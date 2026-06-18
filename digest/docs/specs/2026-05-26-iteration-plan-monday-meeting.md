# 周一会议后的 8 要点迭代计划

**Date**: 2026-05-26
**Status**: Draft · 待 Haolin review
**Driver**: Haolin GUO · **Co-design**: Claude

依据：
- [user-persona-v1](./2026-05-26-user-persona-v1.md)
- [two-stage-extraction-and-opus-insights](./2026-05-25-two-stage-extraction-and-opus-insights.md)
- [tldr-insights-todos-goals-and-prompts](./2026-05-26-tldr-insights-todos-goals-and-prompts.md)
- 周一会议产出的 8 要点

---

## 一、8 要点优先级表

| # | 要点 | 优先级 | 影响范围 | 实施时间 |
|---|---|---|---|---|
| 1 | TLDR 看不懂没欲望 | P0 | TLDR prompt 重写 | 本周 |
| 2 | TLDR 桥/translator | P0 | TLDR 加新结构 | 本周 |
| 3 | TLDR 前置突破观点 | P0 | TLDR 加新结构 | 本周 |
| 4 | 头条数量浮动 + 不限前沿研究 | P0 | 头条筛选 + routing | 本周 |
| 5 | Insights 说人话 | P0 | Insights prompt | 本周 |
| 6 | 加粗逻辑重申 | P0 | 加粗规则 | 本周 |
| 7 | 导览升级（目录结构）| P1 | 导览段 | 下周 |
| 8 | 信号源扩展（播客 / 招股书 / 博客）| P2 | collectors | 中长期 |

---

## 二、桥/translator 概念定稿

### 定义

每条 TLDR = **两段式**：
- **第 1 段 · 事件 reframe** — plain 中文 · 完全去英文术语 · 突破观点前置
- **第 2 段 · 桥句** — 一句话告诉读者：对哪类一级市场创业公司意味什么

### 视觉模板

```xml
<li>【{赛道}】<b>{机构 + 团队}</b> —— {事件 reframe}。<br/>
🌉 {桥句：某类创业公司 + 动作}。
（<a href="https://anchor.placeholder/headline_N">↗</a>）</li>
```

### 桥句应用范围

| 信号类型 | 桥句必要性 |
|---|---|
| arxiv 论文 / OpenAlex / X 引用论文 | **必须** |
| 产品发布 / 投融资 / 公司动态 | 可选（事件本身商业化）|
| 顶级实验室博客 / 招股书 | 建议有 |

### 桥句模板

| 模板 | 触发条件 |
|---|---|
| "押注 X 路线的 Y 类创业公司，护城河需要重估" | 论文颠覆了某个方法假设 |
| "Y 类创业公司可能涌出" | 新技术降低了某个赛道的门槛 |
| "Y 类创业公司差异化空间被压缩" | 某大厂自研 stack 整合 |
| "Y 类标的估值前提变动" | 某 benchmark / 成本曲线被打破 |

---

## 三、TLDR v6.8 Prompt 设计

详见独立文件 `prompt_tldr_v6.8.md`（待跑通后落地）。

核心约束：
- **总条数浮动 3-5 条**（基于当日信号质量，不强制 5）
- **完全去英文术语**（VSI-Bench / SPL / token / KV cache / benchmark 名 全禁）
- **赛道标签前置 + 机构名加粗**
- **第 1 段突破观点前置**（用"路径/前提/依赖/替代"型 framing）
- **第 2 段桥句必含**：某类一级市场创业公司 + 动作
- **桥句禁止点名现有 portfolio**
- **桥句禁止空标签**（"对 AI agent 利好"）

---

## 四、头条筛选 v6.8 改造

### 现状（v6.7）
- 固定 5 条头条
- 配额：3 frontier + 2 industry
- 头条候选由 `is_headline_candidate` 字段判定（顶级机构 + novelty=5）

### v6.8 改造
- **数量浮动 3-5**（基于当日信号质量,不强制 5）
- **不限赛道分布**（不必 3 frontier + 2 industry,看当日哪些重要）
- **优先级**：重磅产品发布 / 重要投融资 / 核心实验室关键论文 = 同级
- **差异化新闻汇总**：头条 = 事件 + 投研 insight,不只是新闻摘要

### 头条入选规则（v6.8）

| 信号类型 | 入选条件 |
|---|---|
| arxiv 顶级实验室 | novelty>=4 + 白名单一作 |
| 重磅产品发布 | OpenAI / Anthropic / DeepMind / Meta / xAI / Anthropic 官方账号 + 模型/产品发布关键词 |
| 重要投融资 | 金额 >= $100M 或 顶级 VC 领投 |
| 关键人物动态 | OpenAI / Anthropic 高管 + 战略类陈述 |

---

## 五、Insights 说人话 v6.8 优先级

> "说人话 > 价值 > 简洁"

### 说人话（最高优先级）
- 完全去英文术语（除模型名 / 公司名 / 通用名）
- 不用学术黑话（启发式 / 范式 / 端到端 / 归纳 / 消融）
- 用"路径/前提/依赖/替代/边界"等认知词

### 价值（第二优先级）
- 必须命中 5 层次 ≥ 1 层
- 投研意涵必须指向类标的（不点名 portfolio）

### 简洁（第三优先级）
- 长度 200-280 字
- 但**不能为了简洁牺牲说人话 + 价值**

---

## 六、加粗逻辑 v6.8 重申

沿用 v3 三 Tier（保留 + 在 prompt 里 prominent）：

### Tier 1 强制加粗
- 数字（"+34%" / "$2500" / "72 卡"）
- 公司 / 实验室名**首次**出现
- 模型 / 方法名**首次**出现

### Tier 2 选择性加粗（每段 ≤ 1）
- 表达"判断"的词：贬值 · 重估 · 洗牌 · 护城河 · 窗口期 · 卡点 · 利好 · 差异化

### Tier 3 禁止加粗
- 一般名词 · 形容词 · 已重复公司名 · 文献风词

### 强制范例进 prompt

`<p>业界对推理成本的共识是看模型参数量降本。<b>NVIDIA</b> 这次推翻了这个前提。</p>`
`<p><b>1/10</b> 成本来自 KV cache 跨 <b>72 卡</b> 共享...</p>`

### 上限
- 整篇 ≤ 8 加粗
- 单段 ≤ 3 加粗

---

## 七、内容导览 v6.8 升级（P1）

### 现状（v6.7 / v2 实测）
```
| 一、前沿研究 | 二、行业应用 |
| 基础模型 | 基础模型 (产品) |
| ... | ... |
```
读者只能看到赛道名,看不到该赛道具体有什么内容。

### v6.8 改造（目录结构感）
```
一、前沿研究（5 篇论文）
- 基础模型：VPO 向量化奖励 · Gated DeltaNet-2 长上下文 · ...
- 多模态智能：Cambrian-P 相机位姿罗盘 · ...
- 世界模型：PhysX-Omni 三维统一仿真 · ...
- ai4s：SciCore-Mol 分子科学 · ...

二、行业应用（6 篇）
- 基础模型：DeepSeek -75% 定价 · Greg Brockman Codex iPhone 模拟器 · ...
- AI infra：Microsoft PEEK · Huawei 122TB SSD · ...
- 世界模型：Tesla S/X 停产 → Optimus · Figure 4 周年 · ...
```

读者一眼看到该赛道有什么具体内容,便于跳转。

---

## 八、信号源扩展 v6.8（P2 中长期）

### 新增信号源

| 源 | 内容 | 难度 |
|---|---|---|
| **核心人物播客** | All-In / Lex Fridman / Acquired | RSS / Apple Podcasts API |
| **核心公司招股书** | OpenAI / Anthropic IPO S-1 | 手动 + 自动监控 SEC EDGAR |
| **顶级实验室博客** | Anthropic / OpenAI / DeepMind 官博 | RSS 已部分覆盖,扩展 |

### 用户体验考虑

播客信号呈现 = 短摘要 + **视频跳转链接**（不放完整 transcript）
- 让用户感兴趣可点开听
- 不用 LLM 大段抽 transcript

---

## 九、实施 Sprint 计划

### Sprint 1（本周）· TLDR + 头条 + 加粗（要点 1-4, 6）

- [ ] 写 TLDR v6.8 prompt（含桥/translator）
- [ ] 基于 5.25 v2 跑 TLDR v6.8 输出 → Haolin review
- [ ] 头条筛选规则改 v6.8（数量浮动 + 不限赛道）
- [ ] 加粗逻辑写 prompt 强约束
- [ ] iterate prompt 1-3 轮

### Sprint 2（下周）· Insights + 导览（要点 5, 7）

- [ ] Insights prompt 升级（说人话 priority 提到第一）
- [ ] 导览段改目录结构感
- [ ] 整合到 daily_digest.md v6.8
- [ ] shadow mode 双跑（v6.7 vs v6.8）1 周

### Sprint 3（下周后）· 信号源扩展（要点 8）

- [ ] 调研 podcasts API 接入路径
- [ ] OpenAI / Anthropic IPO 关键信息源（如果未来 IPO）
- [ ] 实验室博客 RSS 扩展

---

## 十、与现有 spec 的关系

| 已有 spec | 本计划如何继承 |
|---|---|
| `user-persona-v1` | 8 要点是画像 → prompt 的落地 |
| `two-stage-extraction-and-opus-insights` | 阶段提取架构保持 · 加桥/translator 逻辑 |
| `tldr-insights-todos-goals-and-prompts` | v6.8 替换 v6.7 段 · A/B 实验跑 3 个版本（baseline / readability / bridge）|

---

## 十一、待 Haolin 决策

- [ ] 桥/translator 概念是否符合您想象的"翻译"？
- [ ] TLDR v6.8 prompt 草稿（见下一节）是否要立即跑 5.25 v2 5 头条对比？
- [ ] 头条数量浮动 3-5 是否合理？还是 3-7？
- [ ] 头条入选规则是否调整？
- [ ] 信号源扩展（要点 8）Sprint 3 还是再延后？
