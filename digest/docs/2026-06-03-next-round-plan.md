# 下一轮改进计划（2026-06-03 提出，供 Codex 审 → 后续执行）

> 背景：6-03 主线首次跑通 P0+P1（frontier=20、dedup 隔离、lark 重试实测顶住飞书抖动、1-1 推送成功），
> 但暴露两个待解问题：① **慢**（08:30→10:18，~1h48min）；② **跨天/跨源事件重复**（NVIDIA GTC：6-02 手工综述已覆盖 Cosmos 3，6-03 又因 NVIDIA 官方新推文 source_id 不同而重报）。

---

## A. 事件级去重（治「跨天/跨源重复」）

**现状根因**：去重只在 `source_id` 级（同一链接不重复，6-03 实测 skipped 0 正常）。但**同一新闻事件**被不同来源（官博 / 多条推文 / RSS）在不同天报道时，每条都是「系统没见过的新 source_id」→ 全部进日报。GTC 这类持续发酵的大事件尤其明显。手工综述（无采集 source_id）更无法与采集信号自动比对。

**方案（二选一或叠加）**：
- **A1 接入 `canonical_event_key`**：v8 schema 的 `Signal.canonical_event_key`（事件聚类键）**已存在但未接入生成链路**（与 v8 headline 模块一样是休眠代码）。接入后同一事件 cluster 只取代表信号 / 折叠为一条。
- **A2 跨天已报道过滤**：digest 生成前，对照「近 N 天（如 3 天）已发布的实体 / 事件关键词」，对重复事件**降权或标注「持续报道」**，而非当全新头条。

**验收**：构造跨天同事件（不同 source_id）回放，确认只报一次或显式标「持续报道」；GTC 类事件不再连续多天占头条。

---

## B. 提速（治「慢」，6-03 实测 ~1h48min）

按收益排序（实测耗时拆解：X 采集 17min + LLM 抽取 267 条 ~35min + 作者富集 ~40min）：

- **B1 作者富集裁剪范围**（省 ~30min）：主线 `daily.py` step5.5 作者/RM 富集现在**对全部白名单 arxiv 逐篇**做；改为**只对头条 + 前沿展示论文**（复用 Task5 的 `select_headlines` / `headline_signal_ids` 抓手）。注意：这是主线发布路径，需保头条/前沿署名质量。
- **B2 LLM 抽取并发**（省 ~20min）：`signal_extractor` 现在 267 条**串行**（~35min）；改为有限并发（如 4–8 路，注意 Bedrock TPM 限流 + 成本）。
- **B3 X 采集收敛**（省 ~10min）：`x_collector` 17min，分页深度 / 超时 / 每账号上限收敛。

**根因放大器**：whitelist 扩到 420 → 单日信号 267 条，是耗时被放大的根本原因；提速同时可考虑 whitelist 分级采集（P0+/P0 全采，P1/P2 降频）。

---

## C. RM 同名消歧 / 白名单作者匹配准确性（6-03 HOIST 实例）

**问题（6-03 实例）**：白名单按**姓名**匹配，把 HOIST 论文（arxiv 2606.00252）的 Shunyu Yao（University of Florida 土木与海岸工程系，`shunyu.yao@ufl.edu`，人形机器人载荷操控）**误匹配**成白名单里的姚顺雨（ReAct/SWE-agent，清华姚班→普林斯顿→OpenAI→现腾讯首席 AI 科学家）——纯同名、研究方向完全不同。结果信号源被标成"OpenAI Shunyu Yao"，差点带着错误机构+错误身份上头条。

**根因**：`bitable_client._build_whitelist_name_index` 只按姓名归一化匹配，无机构 / 领域 / 邮箱消歧；越是高知名度的白名单作者，越容易把同名陌生作者“吸附”成名人。

**方案**：
- **C1 匹配加辅助消歧**：论文作者的 affiliation / email domain / 研究方向，与白名单实体的机构/研究方向比对；不一致 → 不匹配或标 `needs_review`，绝不直接挂“名人+机构”。
- **C2 高知名度作者强验证**：对 P0+/P0 白名单作者（姚顺雨、李飞飞等）匹配时，强制走 `researcher_mapping.verify_coauthor`（anysearch / openalex）核对 affiliation 再确认。
- **C3 论文标题保真**：HOIST 的 digest 标题被 LLM 改写偏离原题（真题 “Humanoid Optimization with Imitation and Sample-efficient Tuning for Manipulating Suspended Loads”）→ 头条/卡片标题应保留 arxiv 原标题或严格基于原文，不臆造。

**验收**：构造同名场景（UFlorida Shunyu Yao vs 腾讯姚顺雨）回放，确认机构不一致时不误匹配 / 标 needs_review；抽查头条作者署名与论文真实 affiliation 一致。

---

## 非目标
- 不回退 / 不动 P0+P1 已交付的稳定性补丁（state / 熔断 / dedup 隔离 / lark 重试 / preflight）。

## 执行方式
- 本文交 Codex 审 → 通过后按 superpowers TDD 执行（从 main 新建分支 / 隔离 worktree，PYTHONPATH=src + 主检出 .venv 模式）。
- A、B、C 可独立成 PR；**A（事件级去重）+ C（RM 同名消歧）用户体验/可信度优先级最高，建议先做**，B（提速）次之。
