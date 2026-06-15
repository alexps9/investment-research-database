# 两阶段信号提取 + Opus 4.6 Insights 改造 Spec

**Date**: 2026-05-25
**Status**: Proposed · awaiting Monday meeting decision
**Owner**: Haolin GUO
**Reviewer**: leader

---

## 1. 背景

当前一阶段 pipeline 存在以下问题：

1. **LLM 预算分配不合理**：所有 dedup 后的信号（~125/天）无差别用 Sonnet 4.6 跑完整 14 字段抽取，但最终只有 ~40-50 条进 digest（双桶 cap），折叠区信号的深度字段（`method_*` / `core_findings_*`）被浪费
2. **Insights 写作质量不稳定**：daily_writer 单次 LLM call 输出 64K XML，Insights 段偶发写成"事件复述 + 空标签"（5 层次只命中 0-1 层，背离 v6.7 设计意图）
3. **Bitable 可观察性低**：信号被 cap 之后就看不到了，无法 review 哪些信号被丢弃 / 为什么；难以建立 A5 信号 taste eval 数据集
4. **Industry 信号路由依赖白名单 author**：但 @OpenAI 官方账号、Anthropic 官方博客这种"机构来源"不是 researcher 白名单，需要单独 entry

---

## 2. 目标

| # | 目标 | 衡量 |
|---|---|---|
| G1 | LLM 工作流按"信号质量"分档：Haiku 粗筛 → Sonnet 深度 → Opus Insights | 单条信号 LLM 成本下降；高价值信号质量上升 |
| G2 | Insights 质量上一台阶（投研 5 层次更深）| 人工 review 评分提升 |
| G3 | Bitable 渐进式 enrichment，提供可观察性 + eval 基础 | 表里能看到"未深度提取"的全部信号 |
| G4 | 白名单覆盖机构来源（org_account / org_brand）| Industry 信号路由不再依赖人工兜底 |

---

## 3. 总体架构

```
[4 sources collectors (现状不变)]
        ↓
[SQLite dedup (现状不变)]
        ↓
┌──────────────────────────────────────────┐
│ Stage 1: 粗筛  ── Haiku 4.5              │
│  - 提取 6 字段（track / novelty / ...）   │
│  - 写 Bitable signals, stage=initial      │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│ Stage 2: 路由 (代码 + Bitable filter)     │
│  - 白名单一作 arxiv / OpenAlex → 入选     │
│  - 白名单 X 学者含 arxiv 链接 → 入选       │
│  - org_account 推文 → 入选 industry       │
│  - org_brand RSS → 入选 industry          │
│  - novelty>=3 顶尖机构 → 入选             │
│  - 其他 → 留 initial，折叠区显示          │
└──────────────────────────────────────────┘
        ↓ (~50-60 入选信号)
┌──────────────────────────────────────────┐
│ Stage 3: 深度提取 ── Sonnet 4.6 (+ cache) │
│  - 补 8-9 字段（method / cognitive ...）   │
│  - update Bitable, stage=deep             │
└──────────────────────────────────────────┘
        ↓
[Stage 4: RM V4 enrich (现状不变)]
        ↓
┌──────────────────────────────────────────┐
│ Stage 5: Digest 骨架 ── Sonnet 4.6 (1 call) │
│  - 写 TL;DR / 头条 h3 / 摘要 / 方法 / RM   │
│  - Insights 段留 <!--PLACEHOLDER:{sid}-->  │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│ Stage 6: Insights ── Opus 4.6 并行 (~10 calls) │
│  - 仅论文头条 + 前沿研究论文卡片            │
│  - 行业应用 Insights 仍 Sonnet（短锋利）    │
│  - max_tokens=2048 per call                │
│  - ThreadPool 5 并发                       │
└──────────────────────────────────────────┘
        ↓
[Stage 7: 占位替换 + 发布 (现状不变)]
```

---

## 4. 阶段详细规范

### Stage 1: 粗筛 (Haiku 4.5)

**模型**: `us.anthropic.claude-haiku-4-5-...` (待 verify Bedrock model_id)

**抽取字段（6 个）**:
- `track`: 5 选 1
- `novelty_score`: 1-5
- `is_headline_candidate`: bool
- `summary_zh`: ≤ 40 字 short summary
- `first_author`: 一作姓名（不做全作者解析）
- `whitelist_match`: 是否命中白名单（一作 OR 推文作者 OR 机构）

**Prompt**: 新建 `config/prompts/extract_signal_initial.md`

**输出**: 写 Bitable signals 表，`extraction_stage=initial`

**失败处理**: 单条失败不阻塞批次，记录到 ops_metrics

### Stage 2: 路由 (代码 + Bitable filter)

入选规则（决定哪些进 Stage 3 深度提取）:

| 信号类型 | 入选规则 | 进入桶 |
|---|---|---|
| arxiv 白名单一作 | 全入 | frontier |
| OpenAlex 白名单 author | 全入 | frontier |
| X 推文：白名单学者 + 含 arxiv 链接 | 全入 | frontier |
| X 推文：白名单学者 + 无 arxiv 链接 | `novelty_score >= 3` | industry |
| X 推文：org_account（@OpenAI 等）| 全入 | industry |
| RSS：org_brand 关键词命中 | 全入 | industry |
| RSS：其他 | `novelty_score >= 3` | industry |
| 闲聊 / 转发 / `novelty_score <= 2` | 不深度提取，仅 initial 进折叠区 | — |

### Stage 3: 深度提取 (Sonnet 4.6)

**模型**: `us.anthropic.claude-sonnet-4-6-...` (现状)

**补抽取字段（9 个，complementary 于 Stage 1）**:
- `cognitive_takeaway_zh` (中性研究内容认知，280 字以内)
- `core_findings_zh` (arxiv only, 2-3 条带数字)
- `method_framework_zh` / `method_detail_zh` / `result_summary_zh` (arxiv only)
- `key_terms` (1-5)
- `entities` (organizations / people / models_or_papers 完整版)
- `signal_source_zh` (完整版含通讯/共一标注)
- `coauthors_raw`: arxiv 全作者列表（供 Stage 4 RM V4 用）

**Prompt**: 新建 `config/prompts/extract_signal_deep.md`

**输出**: update Bitable signals 同 source_id 行，`extraction_stage=deep`，`deep_extracted_at=now()`

**失败处理**: 单条失败不阻塞；记录到 ops_metrics，下次 pipeline 可单独重试（filter `extraction_stage=initial AND should_be_deep=true`）

### Stage 4: RM V4 enrichment (现状不变)

保持现有 `enrich_paper_coauthors_v4` 逻辑：双源 arxiv+OpenAlex + verify_agent + parallel=4。

### Stage 5: Digest 骨架 (Sonnet 4.6)

**输入**: Stage 3 输出的所有 deep 信号（双桶 frontier=40 / industry=50 cap）

**输出**: 完整 XML 骨架包含:
- TL;DR / 内容导览 / 头条 h3（仅标题，无 Insights）
- 各论文的摘要 / 方法与结果 / RM 表
- 行业应用 60-100 字短卡（含 Insights，Sonnet 已胜任，**不外包给 Opus**）
- 折叠区（含 initial 信号，仅 1 行 link）

**Insights 占位**:
```xml
<callout emoji="🎯">
  <!--INSIGHTS_PLACEHOLDER:{source_id}-->
</callout>
```

**Prompt**: 由 `daily_digest.md` 拆出 `digest_skeleton.md`（去掉论文 Insights 段，保留行业应用 Insights）

### Stage 6: Insights 撰写 (Opus 4.6, 并行)

**模型**: `us.anthropic.claude-opus-4-6-...` (待 verify Bedrock 可用性)

**覆盖范围**:
- ✅ 论文头条 5 个
- ✅ 前沿研究论文卡片 ~3-5 个
- ❌ 行业应用卡片（保持 Sonnet）
- 预计 8-10 次 Opus call/天

**配置**:
- `max_tokens=2048` per call（**不是 64K**，Opus 4.6 硬上限是 32K，单 Insights 实际只需 ~400 tokens）
- ThreadPool 5 并发
- Prompt cache：投研框架 + 标的 universe + 5 层次模板（cached prefix）

**Prompt**: 新建 `config/prompts/insights_writer.md`，包含:
- v6.7 Insights 5 层次框架（why / shift / reframe / timing / actionable）
- 5 要素结构（共识锚点 / 研究动作+结果 / 认知改变 / 投研意涵 / Potential To-dos）
- 缩写规则（**英文缩写在前**，与 TL;DR 相反）
- 反例 vs 正例对照（NVIDIA Vera Rubin case）
- 输入格式: `{paper_signal, related_signals_same_topic, whitelist_author_context}`

**失败处理**: graceful degrade — Opus call 挂了 fallback 到 Sonnet 用 `daily_digest.md` 原 prompt 跑一次该 Insights

### Stage 7: 占位填充 + 发布

代码:
```python
for placeholder_match in re.finditer(r'<!--INSIGHTS_PLACEHOLDER:(\w+)-->', skeleton_xml):
    sid = placeholder_match.group(1)
    insights_xml = opus_outputs[sid]
    skeleton_xml = skeleton_xml.replace(placeholder_match.group(0), insights_xml)
```

发布到飞书 wiki 走现有 `lark_doc_publisher` + 后续 anchor / 图片 / IM 通知。

---

## 5. Bitable schema 改造

### 5.1 `signals` 表新增字段

| 字段名 | 类型 | 用途 |
|---|---|---|
| `extraction_stage` | select (`initial` / `deep`) | 区分提取阶段 |
| `deep_extracted_at` | datetime | 深度提取完成时间 |
| `haiku_cost_usd` | number (4 位小数) | Stage 1 单条成本 |
| `sonnet_cost_usd` | number (4 位小数) | Stage 3 单条成本 |
| `opus_insights_cost_usd` | number (4 位小数) | Stage 6 单条成本（仅论文）|
| `should_be_deep` | checkbox | Stage 2 路由判定结果（便于 Bitable filter）|

### 5.2 `whitelist` 表新增字段

| 字段名 | 类型 | 用途 |
|---|---|---|
| `entry_type` | select (`researcher` / `org_account` / `org_brand`) | 区分白名单 entry 类型 |

### 5.3 whitelist 新增约 12-15 个 entries

**org_account**（X 账号，用于 X collector 命中机构推文）:
- @OpenAI, @AnthropicAI, @GoogleDeepMind, @MetaAI, @Microsoft
- @nvidia, @xAI, @MistralAI, @DeepSeek_AI

**org_brand**（关键词，用于 RSS 内容机构匹配）:
- OpenAI, Anthropic, Google DeepMind, Meta AI, Microsoft
- NVIDIA, xAI, Mistral, DeepSeek

现有 347 researcher entries 批量标 `entry_type=researcher`。

---

## 6. Prompt 拆分

| 现有文件 | 拆分为 | 模型 |
|---|---|---|
| `extract_signal.md` (157 行) | `extract_signal_initial.md` (新, ~60 行) | Haiku |
| | `extract_signal_deep.md` (新, ~110 行) | Sonnet |
| `daily_digest.md` (728 行) | `digest_skeleton.md` (新, ~600 行, 去 Insights 段) | Sonnet |
| | `insights_writer.md` (新, ~150 行) | Opus |

`taxonomy.md` 保持不变（被多 prompt include）。

---

## 7. 成本对比

| 方案 | LLM Stage 1 | LLM Stage 3 | LLM Digest 骨架 | LLM Insights | 总/天 | 增量 |
|---|---|---|---|---|---|---|
| **现状** | Sonnet $0.80 (125 all-in) | — | $0.94 | — | **$1.74** | baseline |
| **推荐方案 A** | Haiku $0.05 (125 short) | Sonnet $0.40 (60 deep) | Sonnet $0.50 (骨架, 无 Insights) | Opus $0.60 (10 calls) | **$1.55** | **-$0.19/天**（实际略降）|

实际节省微小（每月 ~$6），主要价值在质量 + 可观察性 + eval 基础。

---

## 8. 实施计划（5 个 Sprint）

### Sprint 1: Bitable schema + whitelist 扩充 (1 day)

- [ ] `signals` 表加 6 个字段
- [ ] `whitelist` 表加 `entry_type` 字段
- [ ] 批量加 12-15 个 `org_account` / `org_brand` entries
- [ ] 现有 347 researcher entries 全标 `entry_type=researcher`
- [ ] 写 schema 文档进 `docs/specs/`

### Sprint 2: Prompt 拆分 (1-2 days)

- [ ] 抽 `extract_signal_initial.md` (Haiku 用)
- [ ] 抽 `extract_signal_deep.md` (Sonnet 用)
- [ ] 抽 `insights_writer.md` (Opus 用)
- [ ] 改 `daily_digest.md` → `digest_skeleton.md` (去论文 Insights 段)
- [ ] 单独测每个 prompt（手动跑 3-5 条样本）

### Sprint 3: Pipeline 代码改造 (3-5 days)

- [ ] `claude_client.py` 加 `HAIKU_MODEL_ID` / `OPUS_MODEL_ID` + verify Bedrock 可用性
- [ ] `signal_extractor.py` 拆 `extract_initial()` / `extract_deep()`
- [ ] 新建 `routing.py` 模块（按入选规则路由信号）
- [ ] `daily_writer.py` 改两阶段：先 Sonnet 骨架 + 后 Opus Insights 替换
- [ ] 占位匹配 + 替换的 unit test
- [ ] `pipeline.daily` 整合新流程
- [ ] graceful degrade（Opus 挂了 fallback Sonnet）
- [ ] Bitable 写入逻辑改：Stage 1 insert + Stage 3 update（同 source_id）

### Sprint 4: Shadow Mode 验证 (1 week)

- [ ] 同时跑现状一阶段 + 新两阶段（互不写库）
- [ ] **Haiku vs Sonnet 一致率**（`track` / `novelty_score` / `is_headline_candidate`）目标 ≥ 95%
- [ ] **Sonnet vs Opus Insights 质量**（人工评分 1-5 评估 5 层次命中数）
- [ ] 监控成本 / 墙钟 / 失败率
- [ ] 输出 shadow report 决定是否切换

### Sprint 5: 切换 + 监控 (1 day + 1 week)

- [ ] 切到新流程
- [ ] 监控 7 天稳定性 / 成本 / 用户反馈
- [ ] 根据反馈调整 routing 规则 / Insights prompt

---

## 9. 风险 + 缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| Opus 4.6 Bedrock 不可用 | 低 | 高 | 早 verify (Sprint 3 第 1 天)；fallback Sonnet |
| Haiku 准确性不够 | 中 | 中 | shadow mode 1 周验证；不达标用 Sonnet 跑 Stage 1（多 ~$0.50/天）|
| 占位替换失败 | 中 | 中 | 显眼占位串 `<!--INSIGHTS_PLACEHOLDER:{sid}-->` + unit test 验证占位完整性 |
| 墙钟变长 | 高 | 低 | 并行 Opus calls；主线时间 BJT 8:30 → 9:00 推迟（与 C1 arxiv bug 同时修）|
| Bitable 多写一次（insert + update）| 中 | 低 | retry 1 次（已加）|
| Stage 间数据不一致 | 低 | 中 | `extraction_stage` 字段标记，Stage 1 失败时下次重跑只跑失败的（Bitable filter `stage=null`）|
| Insights 上下文丢失 | 中 | 中 | Sonnet 骨架在 Stage 5 已生成"摘要 + 方法 + 结果"，Opus Stage 6 输入要附带这些，避免 Opus 重写一份 |

---

## 10. 与周一 sync 议题的关系

| 周一议题 | 本方案对接 |
|---|---|
| A1 整体 pipeline | 本方案是主要优化 |
| A3 Insights goal | Opus 写作能力支撑读者画像（本科 CS/AI），插槽 prompt = `insights_writer.md` |
| A4 信号提取设计 | 本方案落地，新 schema（6 字段 initial + 9 字段 deep）|
| A5 信号 taste eval | Stage 1/3 shadow 跑产生 golden set（Haiku vs Sonnet 对比）|
| C7 publisher 检测脆弱 | Sonnet 骨架更稳定（output 短，无 Insights 长段干扰）|
| TODO-10 Insights 改写 | 本方案是实施载体 |

---

## 11. 周一会议待决项

- [ ] 接受净成本 -$0.19/天（实际略降）
- [ ] 接受墙钟多 1-1.5 min（4.5 min → 5.5-6 min）
- [ ] verify Opus 4.6 Bedrock 在 us-east-1 可用（Sprint 3 起跑前必查）
- [ ] Shadow mode 周期：1 周 vs 2 周
- [ ] Sprint 1-5 执行 owner 和时间窗口
- [ ] 是否同时修 C1 arxiv 窗口边界 bug（主线 BJT 8:30 → 9:00）

---

## 12. 附录: 不在本方案范围

- HLink G1 visibility (C5) — 独立 ops 问题
- 11:00 G0 早预览 cron — 独立 task #10
- TODO-05 Alert 实时推送系统 — 独立系统
- C2 anchor marker 被吞 — 独立 prompt 调整
