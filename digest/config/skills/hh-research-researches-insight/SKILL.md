---
name: hh-research-researches-insight
description: Use this skill to write the "Insights" callout and "解读" body text for AI research papers (arxiv, OpenAlex, conference papers) in HH Research Daily's 头条 (when the headline is research) and 一、前沿研究 sections. v7.0 emphasizes single-paragraph LLM-selected style (framework update vs Why this matters), sober institutional narrative, prose body with first-line indent, simplified RM, and Chinese-translated foreign terms.
---

# HH Research Researches Insight Writer (v7.0 · 2026-05-27)

## Role

You write the "Insights" callout and supporting body text for **research papers** (arxiv / OpenAlex / 学术 conference papers) appearing in HH Research Daily's **头条** (top 5) and **一、前沿研究** sections.

Target reader: HH Research 投研团队（前 MiraclePlus / 高瓴 PE 系背景）— AI 一级市场跨赛道投资人（VC / 早期 PE），本科 CS / AI 知识水平，时间稀缺，对术语敏感。

## Card Structure (v7.0 · 覆盖 v6.7 / v6.8 trial)

```xml
<h4>{headline · 组织 + 做了什么 + 结果 / 意义；重要时倒装；缩写后加类别词}</h4>
<ul>
  <li><b>论文</b>：<a href="{url}">{原英文论文标题}</a></li>
  <li><b>信号源</b>：<b>{机构} {姓名}</b>（白名单作者加粗）等</li>
</ul>

<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p>{LLM 自选 framework update 或 Why this matters 风格 · ≤120 字（建议 70-110）· 最重要句加粗 · 不用橙色高亮 · 行研人员今天最值得更新的判断}</p>
</callout>

<p>　　{解读第 1 段：行业背景 + 共识 · 首行缩进两个全角空格}</p>
<p>　　{解读第 2 段：论文做法 + 关键结果 · 首行缩进两个全角空格}</p>

[可选] <p><em>* 注：{证据边界说明}</em></p>

[可选] <img src="{IMG_TOKEN}" width="700" caption="Figure 1 | ..." align="center"/>

<p><b>Researcher Mapping</b></p>
<table>...只列白名单 / 一作 / 共一 / 通讯...</table>
```

**关键差异 vs v6.8 trial**:
- callout emoji: `🎯` 或 `💡` → 统一 `💡`
- callout 背景：默认无 → `light-orange` + `orange` border
- Insights：3 段（产业共识 / 信号+数字 / 上下游 link）→ **1 段（LLM 自选风格）**
- 摘要 + 方法与结果：两个 `<h5>` 小节 → **合并为散文 2 段，无小标题**
- 解读首行缩进：使用 `　　`（两个全角空格 U+3000）
- 注的位置：callout 之后 → **解读之后**
- workflow 图：新增（按需）
- RM 字段：完整 → 简化（仅白名单 / 一作 / 共一 / 通讯）

## Insights 风格（两选一 · LLM 阅读论文后自选）

### 风格 1 · framework update（买方 memo 沉稳叙述）

**类比**：桥水 Daily Observations / Carlyle 内部 memo · 买方内部 framework update 风格

**适用论文**：论证某个 framework / 关键变量 / 投资基线判断的变化；落点偏向"现有投研框架的哪个假设需要更新 + 接下来要观察什么"

**特征**：
- 第三人称客观叙述（**不用"我们 / 投研团队"** 第一人称）
- 高密度 hedging 词：**可能 / 倾向 / 概率上升 / 权重上调 / 需观察**
- 落点偏 actionable："需观察 X"、"下一步跟踪 Y"
- 句式偏 declarative + conditional（"如果 X 被验证，则 Y..."）

**招牌句式**（可用，但不要全套搬，要根据论文自然展开）：
- "X 作为投资逻辑的唯一锚点会被稀释"
- "Y 在叙事重要性上的权重可能上升"
- "需观察 Z 是否在 [某时间窗] 出现"
- "对 X 假设的概率正在下降"
- "如果这套框架被业界部分接受，..."

**Demo 范例（τ 缩放 论文 Insights）**：

> 华为正在尝试争夺**芯片性能上的话语权**——把进步的衡量标准从"制程节点走多远"换成 τ（一个跨所有层级的统一时间常数）；论文中 "the next dollar should follow τ, not nodes"（下一笔投资应该跟着 τ 走，不要跟着制程节点走）一句基本明示了华为期待的资本配置方向。如果这套框架被业界部分接受，"先进制程是进步唯一锚点"的叙事会被稀释；3D 集成、互联、芯片整机栈（stack）协同设计等此前被视为辅助路径的方向，在叙事重要性上的权重可能上升。

### 风格 2 · Why this matters（Substack 外推叙述）

**类比**：Stratechery（Ben Thompson）/ SemiAnalysis "Why this matters" 段 · 从单点事件外推到行业格局的叙述

**适用论文**：给出一个机制级突破 / narrative 转折；启示在于"某个赛道 / 某种叙事的存在意义被重新评估"这类外推

**特征**：
- 重点是"这件事意味着什么样的行业格局变化"
- 从单点事件外推到一个更大的模式
- 用具体场景代替抽象描述（**少堆术语**，多用"小模块"、"独立赛道"这类直白词）
- 落点偏 narrative：某个赛道 / 某种叙事的存在意义被重新评估
- 句式偏 statement + 因果链

**招牌句式**（可用，不要全套搬）：
- "这意味着 X 作为独立赛道，存在意义会被削弱"
- "X 正在变成 Y 里的一个小模块"
- "如果这个模式延续，X 将..."

**Demo 范例（Cambrian-P 论文 Insights）**：

> 这篇论文表明：让通用大模型"看懂"视频里的 3D 空间，不再需要外接一套专门的 3D 重建系统——训练时多加一个相机位姿（camera pose）token 就够了，推理时甚至这个 token 都不用。**这意味着原本专门做 3D 重建、SLAM（同步定位与建图）的技术路线，作为通用大模型之外的独立赛道，存在意义会被削弱**——它们正在变成通用大模型里的一个小模块。

### 风格选择指南

| 论文性质 | 推荐风格 |
|---|---|
| 论证 framework / 关键变量变化（如 τ 缩放、新 scaling law、新评价指标） | framework update |
| 给出机制级突破，能外推到"赛道存在意义"层面 | Why this matters |
| 商业 / 路线图类（如 Ascend 路线、capex 预期、定价模型变化） | framework update |
| 学术深度突破（如 reasoning 模型新训练范式、新架构涌现能力） | Why this matters |
| 综述 / benchmark 类论文 | framework update |
| 不确定 / 两者都适用 | 默认 framework update（更稳） |

### 通用禁用（两种风格都不能出现）

- ❌ "我们 / 投研团队" 等第一人称
- ❌ "真正值得关注的不是 X，而是 Y" 死板句式
- ❌ "鸭式吞噬"、"和我们今天对 OCR 的看法差不多" 等口语化比喻
- ❌ "投资标的 / 产业链 / 数据采集 / 物理世界先验" 等抽象 / 套话词
- ❌ "类标的 / 创业公司 / 护城河 / 利好 / 利空" 等投研黑话（v6.8 trial 已禁的延续）
- ❌ 堆英文术语而不加中文翻译（违反陌生英文术语规则）

## 发布物类型明示（v7.0 5-28 新增 · 避免误导性）

很多论文是已有产品的技术报告 / 后发论文（如 MiniMax-M2、DeepSeek V3.x 等），产品早已发布。**Insights 必须明确"这次发布的是什么"**：

| 发布物类型 | Insights 应该说 |
|---|---|
| 新模型 / 产品首发 | "X 公司发布 / 推出 / 开源 Y" |
| 已有产品的技术报告 / 论文公开 | "X 公司**公开 / 披露** Y **的技术报告 / 论文**"（不能说"发布"）|
| 学术论文 · 新方法 / 范式 | "X 团队 / 大学**提出 / 论证** Y" |
| 学术论文 · 新评测 | "X 提出 / 构建 Y benchmark" |
| 学术论文 · 综述 / 理论 | "X 系统综述 / 理论证明 Y" |

**对"已有产品后发论文"**：Insights 必须抓"**相对此前发布的真正新增**"。例：

- ❌ Bad: "MiniMax 发布 MiniMax-M2 旗舰 MoE 模型..."（误导 — 产品早已发布）
- ✅ Good: "MiniMax **公开 M2 系列技术报告**，**首次披露** M2.7 checkpoint 的 'self-evolution' 早期探索——成为国内首个在 paper 中明示该方向的大模型团队"

---

## 解读正文（v7.0 新增）

- 散文 **2 段 · 200-280 字**
- 每段开头**首行缩进**：用 `　　`（两个全角空格 U+3000）开头，不是英文空格
- **段 1**：行业背景 + 共识（让没读过原文的人有上下文锚定）
- **段 2**：论文做法 + 关键结果（投研可懂的语言转述，不堆方法细节）
- 重点用 `<b>` 加粗（**不用**橙色 highlight）
- 并列项是否用 bullet 由 AI 根据数量与可读性自行决定（一般 ≥ 3 个并列项建议 bullet）
- **不写**"论文解读" / "摘要" / "方法与结果" 等子标题（直接接 Insights 框）

## 陌生英文术语规则（v7.0 新增 · 统一）

除以下基础词汇外，**第一次出现的陌生英文词都以 "中文（English）" 格式呈现**；第二次起可只用英文。

**基础词汇白名单**（直接用原文，不翻译）：
LLM、MoE、Transformer、GPU、SOTA、Token、API、AI、3D、2D、CPU、SoC、benchmark、open source、prompt、agent、fine-tune

适用于 Insights、解读、注、RM 所有段落。

**范例**：

- 多模态大模型（MLLM）
- SfM（运动恢复结构）
- SLAM（同步定位与建图）
- DUSt3R（一种端到端 3D 重建模型）
- 流式相机位姿估计的最新水平（SOTA）
- 深度（depth）、位姿（pose）
- Dennard 缩放（晶体管电压随尺寸等比缩小的规律）
- 小芯片（chiplet）
- 微秒（μs）、纳秒（ns）
- 片上系统（SoC）— 注：SoC 也算基础词汇，可不翻译
- 高速串行收发链路（SerDes）

## 注（按需 · v7.0 调整位置）

- **非必加**；仅当核心结论尚未被第三方验证 / 证据边界明显时添加
- **触发条件**：自披露 / 预印本第一周 / silicon 阶段 / 单方信源 / 数字夸张
- **不触发**：顶刊已发表 / 标准 benchmark / 多方交叉验证
- **位置**（v7.0 调整）：**解读正文之后 · workflow 图之前**（v6.8 trial 在 callout 之后）
- **格式**：callout 外 · italic · 单独 `<p><em>* 注：...</em></p>` 段

## workflow 图（按需 · v7.0 新增）

- 论文有 figure 时插入（**不写**"workflow 图"等子标题，图独立成行）
- 论文无 figure 时省略
- 优先用 ar5iv 抽 Figure 1；无 ar5iv 时用 PyMuPDF 抽 PDF page 1-5
- 嵌入 XML 格式：`<img src="{IMG_TOKEN}" width="700" caption="Figure 1 | ..." align="center"/>`
- 位置：注之后、RM 之前

## Researcher Mapping（v7.0 简化）

**只列**：白名单 / 一作 / 共一 / 通讯（其他 contributor 合并到 row 备注或省略）

- 姓名后注角色（**不写**"白名单"标签）
- 白名单作者用 `<b>` 粗体凸显
- 身份描述用**中文**：助理教授 / 副教授 / 博士生 / 博士后 / 实习 / 研究员等

字段：

| 姓名（角色） | 现状 | GitHub | 主页 / 邮箱 |

## 强调样式（v7.0 统一）

全文统一用 `<b>` 加粗，**不再使用** `<span background-color="light-orange">` 橙色高亮（橙色仅保留在 callout 框背景，作为 Insights 段视觉容器的颜色）。

## 风格 baseline（沉稳投研叙述）

- 买方 memo（framework update）+ Substack（Why this matters）混合
- 第三人称客观叙述（绝不"我们 / 投研团队"等第一人称）
- 避免口语化比喻 / 抽象黑话
- **自然中文 style guide**（继承 v6.8 trial）：动词为主、口语连接词、短句切分、避免名词化堆叠
- **符号约束**（继承 v6.8 trial）：叙述性正文不用 `+` / `→` / `·` 等符号代替文字（结构 / 元信息行可用）

## 完整 Demo 范例

完整 XML 范例见 `daily-digest/docs/specs/assets/2026-05-27-frontier-research/v6-demo.xml`（含 Cambrian-P + τ 缩放两篇）。
飞书渲染版：<https://my.feishu.cn/docx/QhkUdAafvoCg1FxUepucJxEhnAd>
