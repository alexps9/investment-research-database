# ONBOARDING · Insights 模块迭代专用入口

> 给同事 @gigimaster — 你只需要看这一份文档，就能开始针对性优化 Insights 生成部分。不必读 31KB 的 PROJECT.md。

**最近更新**：2026-05-30

---

## § 1. 你接手的范围

✅ **你做**：
- 优化 Insights 段（callout 块）的**生成质量** + prompt
- 三类 Insights：头条 Insights（深度版） / 前沿研究论文 Insights（200-280 字） / 行业应用 Insights（60-100 字）
- 调整 quality gate 规则（`src/hh_research/quality/digest_rules.py`）
- 写 A/B 评估脚本对比 prompt 版本

❌ **你不需要碰**：
- 4 源采集（arxiv / X / OpenAlex / RSS collectors）
- LLM 信号抽取（signal_extractor.py · v7 既有 5-track schema 已稳定）
- 头条筛选 / classifier / selector（v8 大改造中，Haolin 主导）
- TLDR 段（v6.8.5 trial 5-31 落地，Haolin 主导）
- 飞书 wiki 创建 / 卡片推送 / launchd 定时 / Bitable 字段（运维侧）
- 订阅制 / H Link / subscribe listener

如果你的改动需要碰这些"红区"模块，先在飞书群里 sync 一下 Haolin。

---

## § 2. 30 秒理解 Insights 在系统中的位置

```
┌─────────────────────────────────────────────────────────────┐
│  4 源采集（arxiv / X / OpenAlex / RSS）                       │
│         ↓                                                     │
│  Signal 抽取（Sonnet 4.6 · 5-track schema · 并发 10）          │
│         ↓                                                     │
│  Bitable signals 表(持久化)                                    │
│         ↓                                                     │
│  ⭐ Daily Writer(Opus 4.6) · 生成 XML 日报                      │
│      ├─ TL;DR 段(v6.8.5 trial · Haolin 主导)                  │
│      ├─ 头条卡片(v8 classifier · Haolin 主导)                  │
│      ├─ 🟢 头条 Insights callout(你的范围)                      │
│      ├─ 🟢 前沿研究论文 Insights callout(你的范围)              │
│      └─ 🟢 行业应用短卡 Insights callout(你的范围)              │
│         ↓                                                     │
│  Quality Gate(digest_rules.py · v7.0 baseline · 你可调)        │
│         ↓                                                     │
│  飞书 wiki 创建 + 3 通道推送(运维侧 · 不动)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## § 3. 6 个关键文件（看完就能开工）

| 文件 | 作用 | 改动权限 |
|---|---|---|
| `config/prompts/daily_digest.md` | 主 prompt（XML 模板 + v6.8 trial overrides §3 Insights / §6 行业应用 Insights） | ⭐ 你主改 |
| `config/skills/hh-research-researches-insight/` | 论文 Insights 写法 skill（独立封装） | ⭐ 你主改 |
| `config/skills/hh-research-applications-insight/` | 行业应用 Insights 写法 skill | ⭐ 你主改 |
| `config/skills/hh-research-insight-writer/` | 写手 skill（meta） | 视情况 |
| `config/agents/hh-research-insight-reviewer.md` | 审稿 agent（自动 review Insights） | ⭐ 你可调 |
| `src/hh_research/quality/digest_rules.py` | Quality gate（v7.0 baseline · 限字数 / benchmark / 投研黑话词） | ⭐ 你可调 |

---

## § 4. 当前 Prompt 版本树

```
daily_digest.md（v6.8 trial）  ← 当前生产线在用
  ├── v6.8.4（5-27 起 · 30-40 字 TLDR · 即将被 v6.8.5 覆盖，5-31）
  ├── v6.8.5（5-30 design · 40-80 字 TLDR · 仅动 TLDR 节）
  └── v6.7（既有 · 5-24 起 · 事实性约束）

daily_digest.md.v1.bak ~ v6.4.bak    历史快照（如需对照）
extract_signal.md                     信号抽取 prompt（5-track schema · 不属 Insights 范围但你可读）
```

**关键约定**：
- v6.8 trial **§3 Insights 节是你的主战场**（约 200-280 字长卡 + 200-220 字头条版 + 60-100 字短卡）
- v6.8 trial **§4 自然中文 style guide** + **§4.5 符号约束**（约束 Insights 文字风格，不要踩"人机感"禁词）
- v6.8 trial **§5 "注" 注脚机制**（按需加，自披露 / 单方信源 / 数字夸张时加）
- v7.0 **quality gate** = `digest_rules.py` 写死的硬约束：字数 / benchmark 名 / 投研黑话词等

---

## § 5. Insights 三段式（目标读者 / 5 层判断 / 失败标准）

### 5.1 头条 Insights（深度版 · ~250 字）

| 维度 | 定义 |
|---|---|
| 读者 | 跨赛道 PE/VC 投研，本科 CS/AI 基础，30 秒决定要不要继续读完整卡片 |
| 5 层任意命中即合格 | ① 机制 why / ② 格局 shift / ③ 认知 reframe / ④ 节奏 timing / ⑤ 标的 actionable |
| 失败标准 | ① 只复述事件，不能复述判断变化 / ② 80% 字数堆在 why 技术细节 / ③ 投研意涵是空标签（"对 AI agent 有利"） / ④ 与摘要段重复 |

### 5.2 前沿研究论文 Insights（200-280 字长卡）

| 维度 | 定义 |
|---|---|
| 读者 | 关注该赛道的 PM / Analyst，本科 CS/AI 基础，1-2 分钟深读 |
| 状态变化 | 读完能一句话说："这条信号让我对 X 的判断变了：原来 Y，现在 Z" |
| 5 段结构 | 共识锚点（软） + 研究动作 + 结果 + why 段 + 认知改变（独立 `<p>`） |

### 5.3 行业应用 Insights（60-100 字短卡）

| 维度 | 定义 |
|---|---|
| 读者 | 同 5.2，关注产品 / 估值动态 |
| 优先级 | 论文重，行业可略浅（命中 1 层即可） |
| 失败标准 | ① 复述推文内容 / ② 宏大叙事（"AGI 又近一步"） / ③ 没指向具体标的类型 |

更详细的 goal + 写法 spec 见 `docs/specs/2026-05-26-tldr-insights-todos-goals-and-prompts.md`。

---

## § 6. 历史信号样本去哪找

**线上**：飞书 wiki "HH Research Daily" 节点下，所有历史日报。最近案例：
- 5-25 / 5-26 / 5-29 / 5-30 日报（5-26 商业进展子赛道首次启用 · 5-30 GPIC / ViewSuite / Tau Scaling Law 三个高质量论文卡片）

**本地（推荐 · 跑过 pipeline 后）**：
```bash
ls daily-digest/data/digests/         # 既有日报 markdown（已 gitignore 不在 repo 内，需本地跑生成）
```

**Bitable signals 表（拿原始信号反推 prompt 输入）**：

如需直接读 Bitable 原始 signals（每条 signal 含 `extract_json` 全字段），**向 Haolin 索要 Bitable base / table / view ID 与 `.env` 凭证**——本文档不直接列 token，避免凭证扩散。

> 大多数 Insights iteration 不需要直接 Bitable 访问，**已生成的 digest markdown + 飞书 wiki 历史日报已经够用**。

---

## § 7. 本地 iterate 的方法（不跑整 pipeline 也能调）

**最小调用链** — `scripts/regenerate_digest.py` 单日重生成（**当前唯一稳定入口**）：

```bash
# 不重新采集信号，从 Bitable 拉既有 signals 直接喂给 Opus 4.6 → 输出 XML
# 单跑一天成本 ≈ $1.7（Opus 4.6 写日报）

LARK_CLI_NO_PROXY=1 .venv/bin/python scripts/regenerate_digest.py 2026-05-29 \
  --skip-publish     # 不推送，仅生成本地 markdown
```

输出位置：`daily-digest/data/digests/digest_2026-05-29.md`

> **更便宜的单篇 Insights iteration 脚本** 当前**还没有**。如果你需要按"取一条 signal、跑 Opus 输出 Insights 段、不写 Bitable"这种最小循环节奏 iterate，告诉 Haolin，他会单独开 spec 写一个 `scripts/iterate_insight_single.py`。**当前先用 `regenerate_digest.py` 整天跑**，单次成本 ~$1.7 不贵。

---

## § 8. 怎么衡量"优化是否成功"

### 8.1 5 维评分卡（人工 review）

| 维度 | 评分标准（1-5） |
|---|---|
| 判断变化清晰度 | 5 = 一句话能复述判断 / 1 = 只能复述事件 |
| why 段帮助度 | 5 = 让我能跟创业者讨论 / 3 = 让我大致理解类别 / 1 = 占字数无收益 |
| shift / actionable 篇幅 | 5 = 占 ≥ 2/3 / 1 = 占 ≤ 1/3 |
| 投研意涵粒度 | 5 = 点名 + 类标的混合得当 / 1 = 全部空标签 |
| 整体偏好 | 5 = "周一会上想 share 这条" / 1 = "跳过算了" |

### 8.2 A/B 跑法

参考 `docs/specs/2026-05-26-tldr-insights-todos-goals-and-prompts.md` §4 已有的 A/B 设计（5 篇 paper × 2 版 prompt = 10 个 Insights → 飞书 doc 并排展示给 Haolin / leader review）。

### 8.3 自动化 quality gate（已有，不用重写）

`src/hh_research/quality/digest_rules.py` 已经实现了字数 / benchmark / 投研黑话词的硬约束扫描。运行：

```bash
.venv/bin/python scripts/digest_review_agent.py --file daily-digest/data/digests/digest_2026-05-30.md
```

---

## § 9. 推荐第一周做什么

| Day | 任务 |
|---|---|
| Day 1 | 通读本 ONBOARDING + `daily_digest.md` v6.8 trial §3 §6 + `docs/specs/2026-05-25-two-stage-extraction-and-opus-insights.md` + `docs/specs/2026-05-26-tldr-insights-todos-goals-and-prompts.md` |
| Day 2 | 本地跑通 `regenerate_digest.py 2026-05-29 --skip-publish`，看一遍输出 / 关键 case |
| Day 3 | 挑 3 篇 5-25 ~ 5-30 真实 Insights，按 § 8.1 5 维评分卡评分，找出失败 case |
| Day 4 | 拟出 v6.9 改动假设（写在新 spec 文件 `docs/specs/2026-06-XX-insights-v6.9-design.md`） |
| Day 5 | A/B run + sync 给 Haolin（飞书） |

---

## § 10. 哪些规则不要动 / 联系方式

### 不要动的红区

- ⛔ TLDR 章节（v6.8.5 spec 5-31 落地 · Haolin 主导）
- ⛔ 头条筛选 classifier / selector（v8 大改造 · Haolin 主导）
- ⛔ 信号抽取 prompt `extract_signal.md`（5-track schema 已稳定）
- ⛔ 4 源 collectors / Bitable schema / launchd plist / 推送 publisher（运维侧）
- ⛔ 顶层硬约束（v6.7 既有的赛道限额 / 信号路由 / 头条与 section 去重 / 标题层次 · `daily_digest.md` 第 47-198 行）

### 可以改的绿区

- ✅ `daily_digest.md` §3 Insights 写法（v6.8 trial）
- ✅ `daily_digest.md` §6 行业应用 Insights（v6.8 trial）
- ✅ `digest_rules.py` quality gate（添加 / 删除 / 调整 rule，但记得跑 `tests/test_digest_quality_rules.py`）
- ✅ `config/skills/hh-research-{researches,applications}-insight/` 三个 skill 文件
- ✅ `config/agents/hh-research-insight-reviewer.md` 审稿 agent

### 联系方式

- 项目 owner：郭昊霖（Haolin · 飞书优先 · @goalin302）
- Leader：见 GitHub admin @jingruzhao103-bit
- 紧急上线问题：直接 ping Haolin
- 非紧急讨论：在新 spec 文件里写 + 飞书 sync

---

> Welcome aboard 🚀
