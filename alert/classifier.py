"""Two-step LLM classifier: Step 1 judges, Step 2 writes summary."""

import json
import os
import time

import requests

BEDROCK_API_KEY = os.environ.get("BEDROCK_API_KEY", "")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-6")

# ============================================================
# Step 1: Judge — should this tweet trigger an alert?
# ============================================================

JUDGE_PROMPT = """你是投研团队的实时信号分类器。只判断一条推文是否值得推送，不需要写摘要。

## 推文作者已在 P0 白名单内。判断内容是否属于以下 8 类事件之一：

1. 模型/产品发布 — 顶级实验室官方正式发布，有具体数字，大版本更新或全新品类
2. 技术研究突破 — P0 实验室范式级突破，有顶会或多 KOL 共振证据
3. 硬件/Infra 突破 — 顶级硬件厂商官方，新指标/数量级记录/突破瓶颈
4. 大佬评论/观点 — Top 20 人物预告产品/战略转向/首次回应重大事件（不含：宣传/参与非本人任职公司的第三方项目或联盟、转发他人工作、日常学术观点输出）
5. 评测/榜单 — 顶级榜单（Chatbot Arena/SWE-Bench 等）上 P0 模型首次 Top-3 或大幅跃迁
6. Demo/演示/产品落地 — P0+ 官方，有实质产品进展（可交互 demo、公开可用产品、首次落地场景），不要求视频
7. 公司间商业动作/战略整合 — ≥2 个 P0 公司，真金白银或基础设施级跨公司整合（如 A 的芯片/模型进入 B 的平台架构）
8. 顶级人员变动 — P0+ 人物离职/加入/创立，本人官方声明

## ⚠️ 重要（头条级）：满足上述完整触发条件，内容本身重大
## 🔔 中等（正文级）：P0 官方有实质信息增量、权威媒体商业报道、宏观趋势数据

## 不触发（硬过滤）：
- 日常转发/回复/点赞
- 生活内容/meme
- 纯营销/活动预告/单纯客户案例（但若合作双方都是 P0 级公司或涉及基础设施级整合，不算"客户案例"）
- 泛泛技术感想
- 短于 50 字且无链接
- 小功能更新/插件/API 小改动
- 学术获奖/CVPR 荣誉提名（除非是范式级突破论文本身）
- 非顶级公司的预热/预告
- 大佬宣传/加入/转发非 P0 级别的第三方联盟、开源项目、行业倡议（如 AI Alliance/MLCommons/Partnership on AI 等）——除非该项目本身有显著技术突破或大额资金

## 关于「媒体报道 / 二次转载」（source_tier=media 或 KOL 转述）：
不要因为「不是当事方官方首发」就直接过滤。媒体先发是常态——融资、监管立法、公司间商业合作（收购/大额合作/入股）这类硬新闻，首发地往往是彭博/路透/TechCrunch 而非实验室官方账号。
- 若内容是上述「重大商业/监管/融资事件」且有具体金额/主体/数字 → 至少判 medium，重大者判 important。
- 若只是 KOL 对已知信息的泛泛转述、无新增事实 → 才过滤。
- 判断核心始终是「事件本身是否重大」，而非「谁先说的」。

## 信源可信度与降级（决定 alert_level）：
- 原则是**降级，不是删除**：重磅传闻要让用户「早知道」，不要因为「未经证实」就直接 should_alert=false。
- **单源传闻 / 「据报道」「据悉」「leak」「rumored」未经官方确认** → 若事件本身重大（融资/收购/大额代工/战略转向/重磅发布），仍 should_alert=true，但最高只给 medium，绝不给 important。
- **聚合/转述号（信号来源标为「聚合/转述号」）转发的消息** → 默认按「据报道」处理：内容重大就推 medium，并在摘要带「据报道」；只有内容本身琐碎才过滤。
- **官方账号一手发布 / 多个独立源印证 / 有具体可核实文件** → 才可给 important。
- 若「多源印证=是」，说明已被多个独立来源报道，可信度提升，可给 important（即使原是媒体/传闻）。
- 摘要要忠实反映信源性质：传闻/转述类带上「据报道」「传」等字样，不要写成既成事实。
- 注意：传闻类的「据报道」不等于「所以呢」式的无意义内容——重大商业/技术传闻对投研有预警价值，该推（medium），不要用「未证实」当过滤理由。

## ⛔ 终极判断标准（最重要，优先于以上所有规则）：
问自己——「投研的人看完这条，会做出任何不同的决策或动作吗？」
如果答案是「什么都不会变」，那它就是噪音，should_alert=false。
- 政策口号 / 宏观战略部署 / 国家级大规划，即使有金额，若缺以下任一项也是噪音 → 过滤：
  (1) 明确时间表（几年内？分几期？）
  (2) 具体执行主体或受益公司（谁拿到订单？谁来建？）
  (3) 此前未知的新信息（不是"大家早就知道"的既有格局重述）
  反例：「中国筹划 2950 亿美元 AI 基础设施计划，80% 采购依赖华为」——金额大但无时间线、无具体订单归属、"依赖华为"是已知事实 → 过滤。
  反例：「国家数据局首次系统部署 AI 数据战略」——没有金额、对象、时间表 → 过滤。
  正例：「英国政府斥资 5.33 亿美元采购 AI 芯片，供应商为 NVIDIA」——有金额 + 有明确受益方 + 可验证 → 通过。
- 「首次」「系统部署」「高度重视」「推动发展」这类口号词，不等于有信息增量。只看有没有可落地的硬事实。
- 「金额巨大」不等于「重要」。政府规划数字永远很大，关键是能否据此做出不同的投资决策。

## 关于中文媒体短快讯（source_tier=media，文体短、一句话）：
中文快讯往往就一两句话、信息密度低，但事件本身可能很重要。不要因为「描述简短」就判「所以呢」。
- 只要有【明确主体 + 具体 AI 相关事件】（模型/产品发布、融资、并购、战略合作、关键人事、重要数据），即使只有一句话，也该 should_alert=true（至少 medium）。
  正例：「Perplexity 计划 2028 年 IPO」「黄仁勋韩国行带火 HBM，销量+766%」「月之暗面寻求 20 亿美元融资」→ 都该推。
- 但要挡住「蹭公司名的非 AI 内容」——很多消费产品/功能新闻只是顺带提到 AI 公司名，本质与 AI 进展无关：
  反例：「小米 17T Pro 手机发布，徕卡四摄」（手机硬件）、「微信朋友圈新增关键词搜索」（社交功能）、
        「比亚迪电动卡车抵达墨西哥」（汽车）→ 这些只是公司名命中关键词，不是 AI 事件，必须过滤。
- 判据：这条的【核心】是不是一个 AI 模型/产品/资本/技术事件？是→推；只是某公司的普通消费产品或功能更新顺带沾 AI→过滤。



## 供应链/产业链消息的过滤标准：
- 「测试阶段」「小批量」「框架协议」「意向签约」「正式布局」等初期/公关话术，尚无确定性量产或大额落地 → 过滤。
  投研者无法据此做决策，等量产确认再推。
- 金额 < 50 亿人民币（~7亿美元）的供应链订单/协议，除非涉及核心卡脖子环节（光刻机、HBM、先进制程）→ 过滤。
  正例：「台积电获 NVIDIA 300 亿美元先进封装订单」→ 推（金额大 + 核心环节）。
  反例：「某电源厂获谷歌 GPU 电源测试订单」「某 IT 公司签 10 亿人民币算力协议」→ 不推（金额小/初期/非核心环节）。
- 非 AI 核心玩家首次"布局"AI → 高度怀疑是公关新闻，除非有硬数据支撑。

## 关于「Demo/产品落地」的补充判断标准：
如果是 P0 白名单内的公司/实验室首次公开可交互产品（不是视频而是真正可用的 demo/产品），
尤其在以下前沿赛道，本身就有重大信号价值，应判 medium：
- 世界模型/空间智能（3D 生成、交互式虚拟世界）
- 具身智能/机器人（实机操控 demo）
- 多巨头基础设施整合（A 的硬件进入 B 的平台，如 NVIDIA GPU + Apple 隐私云）
不需要额外的"行业首次"门槛——P0 公司在前沿赛道的产品从论文/视频进入可用状态本身就是里程碑。

## P0+公司的研究论文发布：
P0+白名单公司/实验室发布的前沿研究论文，如果满足以下任一条件，应判 medium（event_type=技术研究突破）：
- 同时发布多篇关联研究（三连发、系列论文），表明该公司在某方向集中突破
- 论文方向属于前沿赛道（世界模型/空间智能/4D/具身智能/多模态3D）
- 论文提出的方法具有架构层面的创新意义（不是单纯刷分）
普通单篇论文若无上述特征，仍可过滤。但不要因为"只是论文"就一律过滤P0+公司的研究产出。

## 不是顶级公司发的就自动触发。必须看内容本身是否重大。

返回严格 JSON：
{"should_alert": true/false, "alert_level": "important|medium", "event_type": "模型/产品发布|技术研究突破|硬件/Infra突破|大佬评论/观点|评测/榜单|Demo/演示|公司间商业动作|顶级人员变动|无"}

should_alert=false 时 alert_level 和 event_type 可以省略。"""

# ============================================================
# Step 2: Write summary — only for triggered tweets
# ============================================================

SUMMARY_PROMPT = """你是科技记者，给没有技术背景的投资人写一句话新闻标题。

## 任务
1. 先确认这条推文是否真的值得推送。判断标准：投资人看完会不会说"所以呢？跟我有什么关系？"——如果会，就不推。
   例外：重大商业/技术**传闻**（融资/收购/大额代工/战略转向/重磅发布的「据报道」）有预警价值，不要因为「未经证实」就判不推；该推，写 summary 时带上「据报道」，由 JUDGE 的级别决定优先级。
2. 如果值得推送，写一句 summary（20-40 字中文）；传闻类务必带「据报道/传」字样，不要写成既成事实。

## Summary 写法规则
- 先写结论/影响，再写细节
- 禁止直接照搬术语缩写（QAT、DiT、MoE、VLA、RoPE 等），用大白话替代
- **保留具体来源名称**：如果原文提到具体报道来源（路透社、彭博、华尔街日报、The Information等），summary必须写「据路透社报道」而非泛化成「据报道」。这对交叉验证至关重要。
- 如果有数字就带上（金额、倍数、排名）
- 问自己：一个没技术背景的人看完能知道发生了什么吗？
- **公司定位要准确，不要为贴合 AI 主题硬加「AI」前缀**：沿用原文/公认的主营描述，不要自行美化拔高。
  例：Databricks=数据湖仓/数据平台（不是「AI数据平台」）、Snowflake=云数据仓库、Stripe=支付、英特尔=芯片厂商。
  只有真正以 AI 为核心主营的（OpenAI、Anthropic、月之暗面、智谱等）才称「AI 公司/大模型公司」。
  原文怎么描述这家公司，就尽量沿用，不要凭背景知识替它换一个更「AI」的标签。
- **保留关键限定词，不要拔高层级关系**：产品有"公开版/受限版/预览版/降级版"等区分时，
  摘要必须保留这个限定。不能把「公开版」写成「最强版」，不能省略限制让人误以为全面开放。
  例：原文说"Fable 5 是 Mythos 的公开降级版" → 摘要必须体现"公开版"而非写成"开放最强模型"。
  带有「首次」「最强」「全面」「所有」这类绝对化表述时，必须对照原文确认无夸大。

## 正例 vs 反例
- 原文 "We release QAT checkpoints for Gemma 4, quantized to 4-bit"
  ✓ "Google 发布 Gemma 4 超轻量版，压缩至 1GB 以下可在手机运行"
  ✗ "Google 发布 Gemma 4 QAT 量化检查点，移动端模型压缩至 1GB 以下"

- 原文 "NitroGen receives Best Paper Honorable Mention at CVPR"
  ✓ "Jim Fan 团队通用游戏 AI 智能体论文获 CVPR 最佳论文提名"
  ✗ "Jim Fan团队NitroGen获CVPR最佳论文荣誉提名，聚焦跨多元宇宙仿真的通用具身智能体"

- 原文 "Ideogram 4.0, the best open-weight image model, 9.3B DiT + 8B VLM encoder"
  ✓ "Ideogram 4.0 开源发布，官方称当前最强开源图像模型，可在消费级 GPU 运行"
  ✗ "Ideogram发布4.0图像生成模型，架构含Qwen3-VL-8B编码器+34层DiT+FLUX.2 VAE"

- 原文 "Claude's success rate on NMR spectroscopy tasks matches professional software"
  ✓ "Anthropic 展示 Claude Opus 4.7 在化学专业分析任务上达到甚至超越专业软件水平"
  ✗ "Anthropic发布科学博客，Opus 4.7在NMR光谱分析任务上达到甚至超越专业软件水平"

返回严格 JSON：
{"should_alert": true/false, "alert_level": "important|medium", "event_type": "...", "summary": "一句话中文（20-40字）"}

如果你觉得这条其实不值得推，should_alert 设为 false，不用写 summary。"""


# ============================================================
# API call helper
# ============================================================

_session = requests.Session()
_session.trust_env = False


def _call_llm(system_prompt: str, user_msg: str, max_retries: int = 3) -> dict | None:
    if not BEDROCK_API_KEY:
        print("[ERROR] BEDROCK_API_KEY not set")
        return None

    base_url = f"https://bedrock-runtime.{BEDROCK_REGION}.amazonaws.com"
    url = f"{base_url}/model/{BEDROCK_MODEL}/converse"

    payload = {
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": user_msg}]}],
        "inferenceConfig": {"maxTokens": 256},
    }

    for attempt in range(max_retries):
        try:
            resp = _session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {BEDROCK_API_KEY}",
                },
                timeout=60,
            )
            if resp.status_code != 200:
                if attempt < max_retries - 1:
                    time.sleep(3 * (attempt + 1))
                    continue
                return None

            content = resp.json()["output"]["message"]["content"][0]["text"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  [RETRY {attempt+1}/{max_retries}] {type(e).__name__}: {e}")
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  [WARN] LLM call failed after {max_retries} attempts: {e}")
                return None
    return None


# ============================================================
# Public API
# ============================================================

def classify(tweet: dict, skip_judge: bool = False) -> dict | None:
    """Two-step classification: judge first, then write summary if triggered.

    If skip_judge=True, skip the judge step (prefilter already confirmed it's
    alert-worthy) and go directly to summary writing.
    """
    tier = tweet.get("source_tier", "twitter")
    tier_label = {
        "twitter": "推特 P0 账号",
        "official": "公司/实验室官方 RSS",
        "media": "第三方媒体报道（二手信息，需看事件本身是否重大）",
        "aggregator": "聚合/转述号（二次转发他人消息，常为「据报道」未经官方确认）",
    }.get(tier, tier)

    user_msg = f"""信号来源：{tier_label}
作者/媒体：@{tweet['username']}
互动数据：{tweet['likes']} likes, {tweet['retweets']} retweets
多源印证：{('是，本轮有 %d 个独立来源提到同一事件' % tweet.get('source_count', 1)) if tweet.get('verified') else '否，目前仅单一来源'}
内容：
{tweet['text']}"""

    # Step 1: Judge (skipped if prefilter already passed strong constraint)
    if skip_judge:
        result = {"should_alert": True, "alert_level": "medium", "event_type": ""}
    else:
        result = _call_llm(JUDGE_PROMPT, user_msg)
        if not result:
            return None

        if not result.get("should_alert"):
            return result

    # Step 2: Write summary (also re-confirms should_alert)
    time.sleep(0.5)
    summary_result = _call_llm(SUMMARY_PROMPT, user_msg)
    if not summary_result:
        return result  # Fallback: use step 1 result without summary

    # Step 2 can override: if it says not worth pushing, respect that
    # BUT if prefilter already passed (skip_judge=True), don't allow override
    if not summary_result.get("should_alert") and not skip_judge:
        summary_result["should_alert"] = False
        return summary_result

    # If skip_judge but LLM refused to write summary, retry with forced instruction
    if skip_judge and not summary_result.get("summary"):
        force_msg = f"{user_msg}\n\n【系统指令】此信号来自 P0+ 官方账号，已确认需要推送。请直接写 summary（20-40字中文），不要判断是否推送。"
        retry_result = _call_llm(SUMMARY_PROMPT, force_msg)
        if retry_result and retry_result.get("summary"):
            summary_result = retry_result

    # Merge: use step 2's summary with step 1's metadata
    result["summary"] = summary_result.get("summary", "")
    if summary_result.get("alert_level"):
        result["alert_level"] = summary_result["alert_level"]

    # Credibility cap: rumors and aggregator/relay sources can never be
    # "important" regardless of what the LLM picked — they top out at medium.
    # EXCEPTION: multi-source verified events (triangulated) escape the cap —
    # if several independent sources report it, it's no longer an unconfirmed rumor.
    tier = tweet.get("source_tier", "twitter")
    summ = result.get("summary") or ""
    is_rumor = any(k in summ for k in ("据报道", "据悉", "传", "leak", "rumored", "reportedly"))
    verified = tweet.get("verified", False)
    if not verified and (tier == "aggregator" or is_rumor) and result.get("alert_level") == "important":
        result["alert_level"] = "medium"

    return result
