"""Signal scoring & triangulation preprocessing layer (迭代 A').

把「该不该推」从纯 LLM 判断，升级为「先算法做结构化信号工程，再交 LLM」：
  1. Tier 分级加权   —— 谁说的（一手源 > 解读者 > 传播者）
  2. engagement_score —— 多热（点赞/转发 × tier × 原创奖励）
  3. 三角验证          —— 多源印证（同一事件被几个独立来源提到）

借鉴自 twitter-hypothesis-validator/score-tweets.py，但简化为单轮批内分析，
不依赖外部 DB，直接在 main 的本轮信号列表上运行。
"""

import re
from collections import defaultdict

# ── Tier 权重 ──────────────────────────────────────────────
# 一手源 > 一线人物 > 专业解读 > 广泛传播
TIER_WEIGHT = {"tier_1a": 4, "tier_1b": 3, "tier_2": 2, "tier_3": 1}

# Tier 1a：顶级一手源（实验室官方账号 + 顶级决策者本人）。其余白名单推特账号默认 1b。
TIER_1A_HANDLES = {
    "OpenAI", "OpenAIDevs", "AnthropicAI", "GoogleDeepMind", "GoogleAI",
    "googleaidevs", "Meta", "AIatMeta", "MistralAI", "xai",
    "sama", "gdb", "demishassabis", "JeffDean", "ylecun",
    "DrJimFan", "karpathy", "ilyasut",
    "NVIDIAAI", "nvidia",
}


def assign_tier(item: dict) -> str:
    """根据 source_tier + 账号，给信号分配 tier。"""
    st = item.get("source_tier", "twitter")
    if st == "official":          # 公司/实验室官方 RSS = 一手源
        return "tier_1a"
    if st == "media":             # 第三方媒体报道 = 解读层
        return "tier_2"
    if st == "aggregator":        # 聚合/转述号 = 传播层
        return "tier_3"
    # 推特账号：顶级一手源 vs 普通 P0
    if item.get("username") in TIER_1A_HANDLES:
        return "tier_1a"
    return "tier_1b"


def engagement_score(item: dict) -> float:
    """参与度 × tier 权重 × 原创奖励。转发权重高于点赞（传播力强）。"""
    tier_w = TIER_WEIGHT.get(item.get("tier") or assign_tier(item), 1)
    likes = item.get("likes") or 0
    retweets = item.get("retweets") or 0
    raw = likes * 1 + retweets * 3
    # RSS/媒体无互动数据，给一个基线，避免被 engagement 归零
    if raw == 0 and item.get("source_tier") in ("official", "media"):
        raw = 10
    is_rt = item.get("text", "").startswith("RT @")
    originality = 0.3 if is_rt else 1.0
    return raw * tier_w * originality


# ── 三角验证：本轮内跨源聚类 ────────────────────────────────
_STOPWORDS = set(
    "的 了 在 是 我 有 和 就 不 人 都 一 上 也 很 到 说 要 去 你 会 这 那 他 它 们 "
    "the a an and or but in on at to of for with is are was be been have has new "
    "ai model models that this it its will from".split()
)


# 跨语言实体归一：把中文实体/概念词映射到英文 token，让中英文报道同一事件时
# 关键词能重叠、聚到同一簇（解决中英混源无法三角验证/去重的问题）。
_CJK_ALIASES = {
    "谷歌": "google", "英伟达": "nvidia", "微软": "microsoft", "苹果": "apple",
    "亚马逊": "amazon", "英特尔": "intel", "特斯拉": "tesla", "三星": "samsung",
    "阿里": "alibaba", "阿里巴巴": "alibaba", "腾讯": "tencent", "字节": "bytedance",
    "百度": "baidu", "华为": "huawei", "小米": "xiaomi", "月之暗面": "kimi",
    "智谱": "zhipu", "通义": "qwen", "千问": "qwen", "黄仁勋": "huang",
    "实时": "realtime", "翻译": "translation", "语音": "speech", "模型": "model",
    "融资": "funding", "估值": "valuation", "收购": "acquisition", "上市": "ipo",
    "芯片": "chip", "算力": "compute", "数据中心": "datacenter", "机器人": "robot",
    "裁员": "layoff", "发布": "launch", "合作": "partnership", "投资": "invest",
}


def _tokens(text: str) -> set:
    """抽取关键词集合：英文词(≥3字母) + 中文词(jieba分词≥2字)，去停用词。
    中文实体词额外归一到英文 token，使中英文同一事件可聚类。
    资本/商业动作模板词（融资/估值/funding…）一并剔除，避免不同主体的
    金融新闻因共享这些高频词被误判为同一事件。"""
    import jieba
    low = re.sub(r"https?://\S+", "", text.lower())
    low = re.sub(r"@\w+", "", low)
    drop = _STOPWORDS | _CAPITAL_ACTION_WORDS
    # 英文词
    toks = {t for t in re.findall(r"[a-z]{3,}", low) if t not in drop}
    # 中文用 jieba 分词（比连续汉字正则准得多）
    cn_parts = re.findall(r"[一-鿿]+", low)
    for part in cn_parts:
        for word in jieba.cut(part):
            if len(word) >= 2 and word not in drop:
                toks.add(word)
    # 加入跨语言别名：原文出现中文实体词时，补上其英文等价 token
    # （资本动作类别名不注入——它们已是停用词，注入会重新引入误判）
    for cjk, en in _CJK_ALIASES.items():
        if cjk in text and en not in _CAPITAL_ACTION_WORDS:
            toks.add(en)
    return toks


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# 强实体词：公司/模型/人物的核心专有名词（事件「主体」）。两条信号若共享
# ≥2 个强实体，基本可判为同一事件——不受各源修饰词（breaking/reports…）稀释。
#
# ⚠️ 刻意不含资本动作词（融资/估值/收购/上市/ipo/代工）：这些是事件「类型」
# 而非「主体」。两条不同公司的融资新闻都含「融资+估值」，若它们算强实体，
# 会因 shared_entities>=2 被误判为同一事件 → 整批融资 alert 互相判重全军覆没
# （2026-06-12 Prometheus vs TensorWave vs Cyera 误判即此）。资本动作词已移入
# _CAPITAL_ACTION_WORDS 停用，不参与主体判定。
_STRONG_ENTITIES = {
    "openai", "anthropic", "google", "deepmind", "meta", "microsoft", "nvidia",
    "apple", "intel", "tesla", "spacex", "databricks", "perplexity",
    "mistral", "xai", "amazon", "tsmc", "samsung",
    "gpt", "claude", "gemini", "llama", "grok", "qwen", "kimi", "deepseek",
    "glm", "minimax", "tpu", "gpu", "hbm",
    "通义", "千问", "月之暗面", "智谱", "英伟达", "黄仁勋", "阿里", "字节", "腾讯",
}

# 资本/商业动作词 + 其英文别名：是事件「类型」不是「主体」，从 _tokens 中剔除，
# 不参与 Jaccard 和强实体判定。否则模板化金融新闻（X完成Y亿融资估值Z亿）会
# 因共享这些高频词被误判同一事件。
_CAPITAL_ACTION_WORDS = {
    "融资", "估值", "收购", "并购", "上市", "代工", "投资", "轮", "美元", "亿美元",
    "万美元", "亿元", "万元", "完成", "公司", "旗下", "宣布", "据报道", "据悉",
    "初创", "初创公司", "完成融资", "轮融资",
    "funding", "valuation", "acquisition", "ipo", "invest", "billion", "million",
}


def _same_event(a: set, b: set, threshold: float) -> bool:
    """同一事件判定：Jaccard 达标，或共享 ≥2 个强实体词，
    或共享 ≥1 强实体 + ≥3 公共 token（覆盖跨语言 Jaccard 被稀释的情况）。"""
    if _jaccard(a, b) >= threshold:
        return True
    shared = a & b
    shared_entities = shared & _STRONG_ENTITIES
    if len(shared_entities) >= 2:
        return True
    # 跨语言兜底：CJK alias 注入了核心 token 但脚本特有词膨胀了分母，
    # 导致 Jaccard 不达标；但 1 个实体 + 3 个公共词已是很强的同一事件信号。
    return len(shared_entities) >= 1 and len(shared) >= 3


def _maybe_same_event(a: set, b: set) -> bool:
    """Gray zone: heuristic 不够判 True 但有同一事件嫌疑 — escalate 到 LLM。
    宁缺勿重复，触发条件（满足其一）：
    - 共享 ≥1 个预设强实体（大公司/模型名）；或
    - 共享 ≥2 个任意主体词（非停用、非资本动作词）。
      后者覆盖「主体是预设名单外的专有名词」的情况，例如两条都讲 Prometheus
      （非预设强实体）的融资——剔除模板词后只剩 prometheus 等少量主体词，
      Jaccard 不达标也进不了强实体判定，必须靠这条兜底，否则同一事件重复推送。"""
    if _same_event(a, b, 0.18):
        return False  # heuristic 已经判 True，不需要 escalate
    shared = a & b
    shared_entities = shared & _STRONG_ENTITIES
    if len(shared_entities) >= 1:
        return True
    if len(shared) >= 2:
        return True
    # 共享 1 个「长专有词」也升级：≥5 字母英文词 或 ≥3 字中文词，基本是
    # 公司/产品/人名等具体主体（如 prometheus），不是泛化模板词。两条信号
    # 共享一个这样的专有名词，即便译名差异让其余词对不上，也值得 LLM 看一眼。
    long_proper = {t for t in shared if (t.isascii() and len(t) >= 5) or (not t.isascii() and len(t) >= 3)}
    return len(long_proper) >= 1


def llm_same_event(text_a: str, text_b: str) -> bool:
    """LLM escalation for uncertain dedup. Biased toward 'same event'
    (宁缺勿重复 — prefer missing one alert over sending duplicates)."""
    from classifier import _call_llm
    prompt = (
        "判断以下两条新闻/信号是否描述同一事件。\n"
        "宁可判为「同一事件」也不要重复推送——只要核心主体和事件性质相同，"
        "即使细节/角度/语言不同，也判为同一事件。\n\n"
        "返回严格 JSON：{\"same\": true/false}"
    )
    user_msg = f"A: {text_a[:300]}\n\nB: {text_b[:300]}"
    result = _call_llm(prompt, user_msg)
    if not result:
        return True  # LLM 失败时默认判同一事件（宁缺勿重复）
    return result.get("same", True)



def triangulate(items: list, threshold: float = 0.18) -> None:
    """对本轮信号按关键词 Jaccard 聚类，标注每条的多源印证情况。

    原地给每个 item 写入：
      - cluster_id   : 所属事件簇
      - source_count : 该事件被多少个不同来源(username)提到
      - verified     : source_count >= 2（多源印证）
    """
    token_sets = [_tokens(it.get("text", "")) for it in items]
    cluster_of = [-1] * len(items)
    clusters = []  # list of member-index lists

    # 高 engagement 的先做簇中心
    order = sorted(range(len(items)), key=lambda i: engagement_score(items[i]), reverse=True)
    for i in order:
        if cluster_of[i] != -1 or not token_sets[i]:
            continue
        cid = len(clusters)
        group = [i]
        cluster_of[i] = cid
        for j in order:
            if cluster_of[j] != -1 or j == i or not token_sets[j]:
                continue
            if _same_event(token_sets[i], token_sets[j], threshold):
                cluster_of[j] = cid
                group.append(j)
            elif _maybe_same_event(token_sets[i], token_sets[j]):
                if llm_same_event(items[i].get("text", "")[:300], items[j].get("text", "")[:300]):
                    cluster_of[j] = cid
                    group.append(j)
        clusters.append(group)

    for cid, group in enumerate(clusters):
        sources = {items[k].get("username", "") for k in group}
        n = len(sources)
        source_list = sorted(s for s in sources if s)
        for k in group:
            items[k]["cluster_id"] = cid
            items[k]["source_count"] = n
            items[k]["verified"] = n >= 2
            items[k]["cluster_sources"] = source_list

    # 无 token 的条目兜底
    for i, it in enumerate(items):
        it.setdefault("cluster_id", -1)
        it.setdefault("source_count", 1)
        it.setdefault("verified", False)
        it.setdefault("cluster_sources", [it.get("username", "")])


def score_signals(items: list) -> list:
    """预处理入口：给每条信号附加 tier / score / 多源印证标记。原地修改并返回。"""
    for it in items:
        it["tier"] = assign_tier(it)
        it["score"] = round(engagement_score(it), 1)
    triangulate(items)
    return items


# Tier 推送优先级：官方一手 > 顶级账号 > 普通 P0 > 媒体 > 聚合转述。
# 同一事件簇里，选优先级最高的做唯一代表推送。
_TIER_RANK = {"tier_1a": 5, "tier_1b": 4, "tier_2": 3, "tier_3": 2}


def dedupe_clusters(items: list) -> list:
    """同一事件簇只保留一条代表，避免多源各推一遍（Thomas 的 pool 去重）。

    代表选取：先按 tier 优先级（官方 > 聚合转述），同级再按 engagement_score。
    被选中的代表已带有全簇的 cluster_sources / verified 标记（来自 triangulate），
    所以推送时仍会显示「✅ 多源证实（所有来源）」。

    返回去重后的代表列表；未聚类（cluster_id=-1）的条目各自独立保留。
    """
    best_by_cluster = {}
    singles = []
    for it in items:
        cid = it.get("cluster_id", -1)
        if cid == -1:
            singles.append(it)
            continue
        cur = best_by_cluster.get(cid)
        if cur is None:
            best_by_cluster[cid] = it
            continue
        # 比优先级：tier rank 高者胜，平局比 engagement
        key_new = (_TIER_RANK.get(it.get("tier"), 0), it.get("score", 0))
        key_cur = (_TIER_RANK.get(cur.get("tier"), 0), cur.get("score", 0))
        if key_new > key_cur:
            best_by_cluster[cid] = it
    return singles + list(best_by_cluster.values())


