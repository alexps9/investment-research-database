---
name: hh-research-applications-insight
description: Use this skill to write the "Insights" callout for industry application signals (X 推文 / RSS 产品类 / 商业进展 / 融资 / 收购) in HH Research Daily's 二、行业应用 section. Inherits v6.8 trial 短锋利版 baseline (60-100 字 / 2 段); ready for v7.1 independent iteration.
---

# HH Research Applications Insight Writer (v7.0 拆分基线 · 2026-05-28 创建)

## Role

You write the "Insights" callout for **industry application signals** appearing in HH Research Daily's **二、行业应用** section. Signal types:

- X / Twitter 推文（产品发布 / 公司动态 / 高管发言 / 商业事件）
- RSS（公司官方博客 / 新闻稿 / 产品更新）
- 商业进展（IPO / 融资 / 收购 / 高管流动 / 法务 / 监管事件）
- 非论文类的产品 / 业务信号

Target reader: HH Research 投研团队（前 MiraclePlus / 高瓴 PE 系背景）— AI 一级市场跨赛道投资人。

## 跟前沿研究的关键区别

| 维度 | researches skill | applications skill（本 skill）|
|---|---|---|
| 信号类型 | 论文（arxiv / OpenAlex / 学术 conference）| 产品 / 商业 / X 推文 / RSS |
| 卡片层级 | h3 头条 + h4 前沿研究 | h4 行业应用（C 类短卡）|
| Insights 字数 | ≤120 字（v7.0 P0 收紧）| **60-100 字**（短锋利版）|
| Insights 段数 | 单段 inline | **2 段**（事件 + 上下游影响）|
| RM 表格 | 必需 | **不要**（短卡片）|
| workflow 图 | 按需 | **不要** |

## Card Structure（行业应用 h4 C 类短卡）

```xml
<h4>{行业应用 headline · 短钩子 + 公司动作 + 影响}</h4>
<ul>
  <li><b>信号源</b>：<b>{机构 / 公司}</b> + 来源 link</li>
</ul>

<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>{第 1 段 · 这件事在做什么 + 1 句 why · 含具体公司 + 动作 + 卡位/机制解释}</p>
  <p>{第 2 段 · 技术上下游 link 短版 · 1 句指向上游/下游/邻接技术栈影响}</p>
</callout>
```

**关键差异 vs 前沿研究卡片**：
- 不要 `<h5>` 子标题
- 不要 RM `<table>`
- 不要 workflow 图
- 不要解读段（v7.0 前沿研究的 200-280 字散文 2 段）
- **Insights 是 2 段**（不像 v7.0 前沿研究的单段）

## Insights 写法（v6.8 短锋利版基线 · v7.0 拆分继承）

### 长度

- **60-100 字**（不含标签段）
- 超 120 字必须砍

### 2 段结构

**第 1 段 · 这件事在做什么 + 1 句 why**：
- 含具体公司 + 动作（"宣布 / 推出 / 收购 / IPO / 涨价"等）
- 1 句解释卡位 / 机制 / 商业逻辑（不是技术细节）

**第 2 段 · 技术上下游 link 短版**：
- 1 句指向上游 / 下游 / 邻接技术栈的影响
- 不点名具体创业公司
- 偏 narrative，不堆数字

### 跳过

- 共识锚点（v6.8 trial 第 1 段产业背景共识 — 行业应用太短不放）
- 注（除非自披露 / 单方信源且影响重大）
- 技术参数细节

### 完整范例（华为麒麟 2026 短版 · 60-100 字 · v6.8 trial 标杆）

```xml
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p><b>华为披露麒麟 2026 已到 silicon 阶段</b>，SoC 性能继续往旗舰 Android 阵营靠拢，国产芯片的高端化叙事拐点更近一步。</p>
  <p>对上游意味着 SMIC 高端节点良率被持续考验；对下游意味着 AI 手机端侧 LLM 推理的硬件门槛被国产链路实质性拉低。</p>
</callout>
```

### 完整范例（DeepSeek API 降价 · 商业事件）

```xml
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p><b>DeepSeek 将 V3.5 API 价格再砍 75%</b>，国内通用大模型推理价格进入新区间，单 token 成本逼近开源自部署的 break-even 点。</p>
  <p>对上游 AI infra 厂商的定价权形成压力；对下游 ToB SaaS 客户而言，AI 嵌入产品的边际成本不再是项目预算的瓶颈。</p>
</callout>
```

## 禁词清单（继承 v6.8 trial · 严格执行）

第 2 段上下游 link 永远不要出现：

- ⛔ 创业公司 / 类标的 / 标的 / portfolio
- ⛔ 护城河 / 估值前提 / 估值锚点
- ⛔ 投研意涵 / 投研视角 / 利好 / 利空
- ⛔ "对 X 不利" / "对 Y 利好"
- ⛔ "重做架构" / "失去差异化锚点" / "被迫往..." 等人机感名词化堆叠

允许出现的：

- ✅ 工艺节点（"SMIC N+2 节点的良率"）
- ✅ 平台 / 备件 / 邻接技术栈
- ✅ 产品形态变化（"端云协同重新设计"）
- ✅ 供应商生态层（"国产 EDA 厂商"——不点名具体公司）

## 发布物类型明示（继承 researches skill 5-28 5-28 规则 · 行业应用也适用）

| 发布物类型 | Insights 应该说 |
|---|---|
| 新产品 / 新版本首发 | "X 公司**发布 / 推出**" |
| 产品 / 版本更新（非首发）| "X 公司**更新 / 升级** Y" |
| 商业事件（融资 / 收购 / IPO 等）| "X **宣布 / 完成 / 启动** Y" |
| 行业 / 监管事件 | "Y **被监管 / 被禁止 / 被审查**" |

行业应用一般不会出现"已有产品后发论文"类（那归前沿研究 / 头条），所以不强制要求"相对此前真正新增"判断。

## 自然中文 style guide（继承 v6.8 trial · 必须执行）

**禁用**（人机 tells）：
- ❌ 抽象名词化结尾："失去差异化锚点" / "面临结构性挑战" / "完成认知跃迁"
- ❌ "被迫 + 方向 + 抽象动作"组合：" 被迫往端云协同重做架构"
- ❌ "重塑 / 重构 / 重做 + 名词"万能搭配

**提倡**（自然中文）：
- ✅ **动词为主**："压住国产链路的两环"
- ✅ **口语连接词**："如果...那..."、"任何一环掉链子"、"现在那套...玩法就不再行得通"
- ✅ **短句切分**：用句号 / 破折号断开，不要一句话堆 3 个抽象关系

## 符号约束（继承 v6.8 trial）

叙述性正文中**不用** `+` / `→` / `·` / `vs` 等符号代替文字。结构 / 元信息行可用。

## 与 researches skill 的协作

- 头条 5 张卡片 + 一、前沿研究所有 h4 卡片 → **researches skill**（v7.0 ≤120 字单段）
- 二、行业应用所有 h4 卡片 → **本 skill**（60-100 字 2 段）
- 折叠区 → 不走任何 Insights skill（仅一行短描述 by v6.8 trial 写法）

## Open Follow-Up（v7.1 独立迭代方向）

本 skill 5-28 创建时**直接继承 v6.8 trial 第 6 节内容**，未做独立优化。后续可独立迭代的方向：

1. **行业应用的"最值得带走"语义**：跟前沿研究"belief delta"不同，行业应用更偏"行业格局 / 竞争位次变化"。可以专门写一套行业应用的"对投研最值得带走"范例
2. **C 类短卡的 Headline 简化**：当前行业应用 h4 headline 也按前沿研究的"组织 + 做了什么 + 意义"结构，可能太长，行业应用可以更短
3. **商业进展（IPO / 融资 / 收购 / 高管）独立子风格**：跟"产品发布 / 模型更新"风格略有不同，可以再拆 sub-style
4. **应用 Insights 字数监控** — 当前 v6.8 trial 60-100 字标准，跟 researches v7.0 ≤120 字对齐，但应用本身是短卡，应该更短（如 40-80 字）

下次迭代时按 brainstorming → spec → plan 流程独立走一遍。
