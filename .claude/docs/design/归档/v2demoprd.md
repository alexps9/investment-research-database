好，那我直接帮你**收敛成一个“可交互前端 demo 的 PRD”**，完全围绕你现在这张图来设计，去掉所有不必要的后端复杂性。

👉 目标是：**前端能跑 + 能演示 + 能讲清楚价值**

---

# 🧠 技术路径雷达（前端 Demo）PRD v1.0

---

# 一、产品目标（前端版本）

### 🎯 一句话目标

> 构建一个可交互的技术路径可视化界面，让用户能够**探索某一AI技术方向的演进路径、分支结构和关键论文节点**

---

### 🎯 Demo目的（很重要）

* 用于：

  * 内部汇报
  * 展示研究能力
  * 验证产品形态

👉 **不是完整系统，仅为可视化demo**

---

# 二、用户核心行为（只保留最重要的）

用户进入页面后，只做三件事：

---

### 1️⃣ 看技术全局分布

👉 “这个领域有哪些方向？”

---

### 2️⃣ 点一个论文节点

👉 “这个论文做了什么？”

---

### 3️⃣ 看技术路径

👉 “技术是怎么演进的？”

---

---

# 三、页面结构

---

## 🧩 页面 = 2部分

### 左侧（核心）

👉 技术路径雷达图（你现在这张）

---

### 右侧（信息面板）

👉 当前选中论文详情

---

---

# 四、核心模块设计

---

# 🟠 模块1：技术路径雷达图（主画布）

---

## 🎯 目标

展示：

* 技术分支
* 时间演进
* 论文分布

---

## 🧱 数据结构（前端mock）

```json
[
  {
    "id": "paper_1",
    "title": "FlashAttention-2",
    "year": 2023,
    "category": "Attention Optimization",
    "citations": 1200,
    "x": 2023,
    "y": "attention",
    "cluster": "attention",
    "connections": ["paper_0"]
  }
]
```

---

## 📊 可视化规则

---

### 1️⃣ 坐标

* X轴：时间（2023 → 2025）
* Y轴：技术类别（离散）

```text
Attention Optimization
SSM / Mamba
RNN Revival
Scaling / MoE
```

---

---

### 2️⃣ 节点（论文）

* 圆点表示论文
* 属性：

| 属性    | 映射        |
| ----- | --------- |
| size  | citations |
| color | 技术分支      |
| glow  | 高增长（可选）   |

---

---

### 3️⃣ 连线（技术路径）

* 虚线 or 曲线
* 表示：

  * 引用关系
  * 或演进关系

---

👉 Demo阶段可以**写死**

---

---

### 4️⃣ Hover效果

鼠标悬停：

* 显示：

  * 论文名
  * 作者
  * 年份

---

---

### 5️⃣ Click效果（最重要）

👉 点击节点：

* 高亮当前节点
* 右侧panel更新

---

---

# 🟣 模块2：右侧信息面板

---

## 🎯 目标

解释：

👉 “这个论文在干嘛 + 在路径中的位置”

---

---

## 📦 展示内容（精简版）

---

### 1️⃣ 标题区

```text
FlashAttention-2
Tri Dao et al. · 2023 · 1200 citations
```

---

---

### 2️⃣ 一句话摘要（必须）

```text
优化Transformer计算效率，通过IO优化实现加速
```

---

👉 mock数据 or LLM生成

---

---

### 3️⃣ 技术分类（标签）

```text
[Attention Optimization]
```

---

---

### 4️⃣ 阶段（简单版）

```text
Mature / Infra
```

---

👉 demo可写死 or 简单规则

---

---

### ❌ 暂时去掉（很关键）

这些全部删掉：

* ❌ 人才图谱
* ❌ 瓶颈分析
* ❌ 商业价值

👉 这些是后期功能，不是demo

---

---

# 🟡 模块3：筛选/切换（简单）

---

## 🎯 功能

顶部或侧边：

---

### 1️⃣ 技术分支筛选

```text
[All] [Attention] [SSM] [RNN]
```

---

👉 点击后：

* 只显示对应节点

---

---

### 2️⃣ 时间范围（可选）

```text
2023 - 2025
```

---

---

# 五、交互设计（必须清晰）

---

## 用户操作流

---

### Step 1

打开页面
👉 看到整体技术分布

---

### Step 2

点击某个节点（如 FlashAttention）
👉 右侧显示详情

---

### Step 3

顺着连线看路径
👉 理解技术演进

---

---

# 六、技术实现建议（前端）

---

## 推荐技术栈



---

## 状态管理

```js
selectedNode
filteredCategory
```

---

---

## 数据

👉 完全可以：

* 本地 JSON mock

---

---

# 七、数据规模（控制复杂度）

---

## Demo建议：

* 20~50 篇论文
* 3~5 条主路径
* 3 个分支

---

👉 不要超过100（会炸）

---

---

# 八、成功标准（你交付要达到的）

---

## 🎯 一个合格demo必须：

✔ 能展示技术分布
✔ 能点击节点看信息
✔ 能看到路径关系
✔ 用户能“看懂在发生什么”

---

👉 就够了

---

---

# 九、你现在这个版本的问题（帮你点出来）

---

## ❗问题1：右侧过重

👉 已修正：只保留最基础信息

---

## ❗问题2：想做“分析系统”

👉 已修正：只做“可视化工具”

---

## ❗问题3：没有明确交互核心

👉 已收敛为：

👉 **点 → 看 → 理解路径**

---

---

# 十、你可以直接丢给AI/前端的话

---

👉 直接复制这段：

---

> 帮我做一个前端可视化demo：
>
> 左侧是一个二维散点图：
>
> * X轴是时间（年份）
> * Y轴是技术类别（离散分类）
> * 每个点是论文
> * 点大小表示引用量
> * 点颜色表示技术分支
> * 点之间有连线表示技术演进
>
> 交互：
>
> * hover显示论文信息
> * 点击节点，在右侧展示详情
>
> 右侧展示：
>
> * 标题
> * 作者 + 年份 + citations
> * 一句话摘要
> * 技术分类
> * 阶段（early/growth/mature）
>
> 数据用本地JSON mock即可

---

# 最后一句（很重要）

你现在要做的不是：

❌ 做对

而是：

👉 **做一个“别人一眼能看懂”的东西**

---

如果你下一步要，我可以帮你：

👉 直接生成一份 **mock数据（Transformer路线）+ JSON**
👉 你可以直接喂给前端跑起来

---

# 附录：30 篇核心论文清单（含 arXiv 直达链接）

## Lane 1: Attention 优化主干

| 级别 | 论文名称 | 发表年份 | arXiv ID |
|------|----------|----------|----------|
| Tier 1 | Attention Is All You Need | 2017 | 1706.03762 |
| Tier 1 | GPT-3 (Language Models are Few-Shot Learners) | 2020 | 2005.14165 |
| Tier 1 | FlashAttention | 2022 | 2205.14135 |
| Tier 1 | DeepSeek-V3 Technical Report | 2024 | 2412.19437 |
| Tier 2 | BERT | 2018 | 1810.04805 |
| Tier 2 | Longformer | 2020 | 2004.05150 |
| Tier 2 | RoPE (RoFormer) | 2021 | 2104.09864 |
| Tier 2 | ALiBi (Train Short, Test Long) | 2021 | 2108.12409 |
| Tier 2 | FlashAttention-2 | 2023 | 2307.08691 |
| Tier 2 | Ring Attention | 2024 | 2310.01803 |

## Lane 2: 状态空间模型 (SSM)

| 级别 | 论文名称 | 发表年份 | arXiv ID |
|------|----------|----------|----------|
| Tier 1 | S4: Structuring State Spaces | 2021 | 2111.00396 |
| Tier 1 | Mamba: Linear-Time Sequence Modeling | 2023 | 2312.00752 |
| Tier 1 | Jamba: A Hybrid Transformer-Mamba Language Model | 2024 | 2403.19887 |
| Tier 2 | HiPPO: Recurrent Memory with Optimal Polynomials | 2020 | 2008.07669 |
| Tier 2 | H3: Hungry Hungry Hippos | 2022 | 2212.14052 |
| Tier 2 | Mamba-2 (Transformers are SSMs) | 2024 | 2405.21060 |
| Tier 2 | Griffin: Mixing Gated LRs with Local Attention | 2024 | 2402.19427 |

## Lane 3: 循环与线性架构 (RNN/Linear)

| 级别 | 论文名称 | 发表年份 | arXiv ID |
|------|----------|----------|----------|
| Tier 1 | RWKV: Reinventing RNNs for LLM | 2023 | 2305.13048 |
| Tier 1 | xLSTM: Extended Long Short-Term Memory | 2024 | 2405.04517 |
| Tier 2 | Linear Transformer (Transformers are RNNs) | 2020 | 2006.16236 |
| Tier 2 | RetNet: Retentive Network for LLM | 2023 | 2307.08621 |
| Tier 2 | TTT Layers (Learning to Learn at Test Time) | 2024 | 2407.04620 |
| Tier 2 | Eagle (RWKV-5) | 2024 | 2401.01460 |
| Tier 2 | HGRN (Hierarchical Gated RNN) | 2023 | 2311.12543 |

## Lane 4: 专家混合与规模化 (MoE)

| 级别 | 论文名称 | 发表年份 | arXiv ID |
|------|----------|----------|----------|
| Tier 1 | Switch Transformer | 2021 | 2101.03961 |
| Tier 1 | Mixtral 8x7B | 2024 | 2401.04088 |
| Tier 2 | GShard: Scaling Giant Models with MoE | 2020 | 2006.16668 |
| Tier 2 | DeepSeek-MoE | 2024 | 2401.06066 |
| Tier 2 | Expert Choice MoE | 2022 | 2202.09368 |
| Tier 2 | Megablocks: Efficient MoE Training | 2022 | 2211.15841 |

## 交互建议：如何呈现跳转？

在右侧面板的论文标题旁放置 ExternalLink 图标，点击后跳转至 arXiv 原文。

```jsx
<div className="flex items-center gap-3">
  <h2 className="text-3xl font-bold text-white">{selectedPaper.title}</h2>
  <a 
    href={`https://arxiv.org/abs/${selectedPaper.arxivId}`}
    target="_blank"
    rel="noopener noreferrer"
    className="text-slate-600 hover:text-blue-400"
  >
    <ExternalLink size={20} />
  </a>
</div>
```

**心理暗示**：这种跳转能告诉你的 Leader，"所有的分析都不是我拍脑门想出来的，每一步都有顶刊论文支撑"

---

# 附录二：论文名称策略（未来扩展）

## 节点命名策略

### 当前做法：社区常用简称

| 节点显示 | 完整论文名 |
|----------|------------|
| BERT | Bidirectional Encoder Representations from Transformers |
| GPT-3 | Language Models are Few-Shot Learners |
| Mamba | Mamba: Linear-Time Sequence Modeling |
| RoPE | RoFormer: Enhanced Position Embedding |

**理由**：符合技术圈习惯，UI 更简洁

### 未来获取方案

| 方案 | 来源 | 难度 | 适用场景 |
|------|------|------|----------|
| **手动映射表** | 维护 `paper_id → 简称` | 低 | MVP/核心论文 (30篇) |
| **LLM 自动提取** | 输入论文标题，提取社区常用名 | 中 | 批量新增论文 |
| **学术数据库** | Semantic Scholar / Google Scholar 爬取 | 高 | 全量数据 |

### MVP 建议

1. **30 篇核心论文** - 手动维护简称映射表
2. **后续扩展** - LLM 自动生成简称（标题太长时自动截取关键词）
3. **数据结构扩展**

```json
{
  "id": "paper_1",
  "title": "FlashAttention",
  "displayName": "FlashAttention",  // 简称
  "fullTitle": "FlashAttention: Fast and Memory-Efficient Attention",  // 全称
  "year": 2023,
  "arxivId": "2205.14135"
}
```

### 技术实现

LLM 提取简称的 Prompt 示例：

```
论文标题：{full_title}
作者：{authors}
请提取这篇论文在社区中最常用的简称（如 BERT、GPT-3、Mamba）。
如果标题本身已经很简洁，返回标题本身。
只返回一个词或短语，不要多余解释。
```

---

# 实现计划：右侧面板重构为"技术判断面板"

> 目标文件：`demo-preview.html`（单文件可交互原型）
> 范围：只改右侧 420px 面板的内容结构，数据全部写死在 allPapers 数组里

## 核心问题

现在的右侧面板 = "情报审计结论"卡片，直接跳到判断，用户不知道怎么得出的。
要改成 = "技术判断面板"，6 个模块，展示结构化思考路径。

## 数据扩展

在 allPapers 每个 tier-1 论文对象上新增字段（写死）：

```js
{
  // 现有字段不变
  id, title, year, lane, tier, author, stage, growth, conclusion, connections, arxivId,

  // 新增字段
  positioning: {
    role: '范式挑战者',        // 技术角色
    benchmark: 'Transformer',  // 对标技术
    coreDiff: '线性复杂度替代 Attention',  // 核心差异
    isParadigmShift: true      // 是否范式变化
  },
  evolution: {
    predecessors: ['S4', 'H3'],           // 前驱论文简称
    current: 'Mamba',                      // 当前节点
    successors: ['Jamba', 'Mamba-2', 'Griffin']  // 后续分叉
  },
  stageDetail: {
    phase: 'Early Adoption',
    period: '2023-2024',
    signals: [
      '引用增速 +320%',
      '工业界开始实验（Together AI / inference stack）'
    ]
  },
  players: {
    coreResearchers: [
      { name: 'Albert Gu', affiliation: 'CMU → Cartesia AI' },
      { name: 'Tri Dao', affiliation: 'Stanford → Together AI' }
    ],
    activeTeams: ['Together AI', 'AI21 Labs', 'Google DeepMind']
  },
  bottlenecks: {
    current: [
      '训练稳定性',
      '长序列优势是否真实（vs attention tricks）',
      '生态缺失（工具链不成熟）'
    ],
    unsolved: '逻辑推理精度在极大规模参数下是否能完全对齐 Transformer'
  }
}
```

Tier-2 论文不需要这些字段，点击 tier-2 只显示基础信息（标题/作者/年份/arXiv 链接）。

## 右侧面板 6 模块结构

点击 tier-1 节点后，右侧面板渲染：

### 模块 1：标题区（保留现有）
- 路径标签 badge
- 论文标题 + arXiv 链接
- 作者 · 年份

### 模块 2：技术定位 (Positioning)
```
技术角色：范式挑战者（SSM 路线）
对标路径：Transformer
核心差异：线性复杂度替代 Attention
```
用结构化描述，不直接写结论。

### 模块 3：技术演进 (Evolution Path)
```
S4 → H3 → [Mamba] → Jamba
                   → Mamba-2
                   → Griffin
```
前驱 → 当前（高亮）→ 后续分叉。用简单的文字 + 箭头，不需要 SVG 图。

### 模块 4：当前阶段 (Stage)
```
阶段：Early Adoption（2023-2024）
信号：
  · 引用增速 +320%
  · 工业界开始实验（Together AI / inference stack）
```
比现在的 "Growth" 一个词更具体，加证据。

### 模块 5：核心玩家 (Key Players)
```
核心研究者：
  · Albert Gu（CMU → Cartesia AI）
  · Tri Dao（Stanford → Together AI）

活跃团队：
  · Together AI · AI21 Labs · Google DeepMind
```

### 模块 6：瓶颈分析 (Bottleneck)
```
当前限制：
  · 训练稳定性
  · 长序列优势是否真实
  · 生态缺失（工具链不成熟）

未解决：逻辑推理精度在极大规模参数下能否对齐 Transformer
```

### 模块 7：结论（降权，放最后）
```
结论：属于"潜在范式替代路径"，当前仍处实验期，值得跟踪但未进入主流。
```
一句话，不是投资建议。

### arXiv 按钮（保留现有）

## 改动范围

只改 demo-preview.html 一个文件：
1. allPapers 数组：给 tier-1 论文加新字段
2. 右侧面板 JSX：从现在的 4 块改为 7 块
3. 不改左侧画布、不改布局、不改交互逻辑

## 验收标准

- 点击 Mamba → 右侧显示 7 个模块，能看到"怎么得出结论的"
- 点击 tier-2 → 只显示基础信息
- 所有 tier-1 论文（约 8 篇）都有完整的 7 模块数据
- 用户 3 分钟内能理解一条技术路线

---

# 自动化方案：当老板问"这能自动跑吗"

## 问题

Demo 里 7 个模块的数据是写死的。老板一定会问：给一个新论文 ID，系统能自动生成这些吗？

## 诚实回答：7 个模块分三档

### ✅ 完全可自动化（API 直接拿）

| 模块 | 数据源 | 实现方式 |
|------|--------|---------|
| 标题区（标题/作者/年份） | OpenAlex `works/{id}` | 直接取 |
| 核心玩家（研究者+机构） | OpenAlex `authorships[].author` + `institutions` | 聚合排序 |
| 当前阶段 — 引用增速部分 | OpenAlex `counts_by_year` | 计算 YoY 增速 |
| 技术演进 — 前驱论文 | OpenAlex `referenced_works` | 取引用列表 |
| 技术演进 — 后续论文 | OpenAlex `cited_by_api_url` | 反查被引 |

这些占面板内容的 **~40%**，纯 API 调用，零 AI 成本。

### ⚠️ 可半自动化（算法 + 规则）

| 模块 | 方法 | 说明 |
|------|------|------|
| 当前阶段 — 阶段判断 | 引用增速规则 | `增速 > 200% → Growth`，`增速 < 30% 且引用 > 1000 → Mature`，`引用 < 100 → Early` |
| 技术演进 — 关键前驱筛选 | 引用数 + 同社区过滤 | 从 referenced_works 中取同社区 + 高引用的 top 3 |
| 技术演进 — 后续分叉 | 被引论文社区检测 | 被引论文中出现新社区 = 分叉信号 |

这些占面板内容的 **~25%**。

> **纠正：技术定位 — 所属路径** 之前归在这一档是错的。
> Louvain 输出无语义的社区编号（0/1/2），不知道"社区 0 = Attention 优化"。
> 真实链路：Louvain 聚类 → 人工或 LLM 给社区打语义标签 → 才有"所属路径"。
> 所以归入下面 ❌ LLM 层。

### ❌ 需要 LLM（必须读懂论文）

| 模块 | 为什么不能自动 | LLM 方案 |
|------|--------------|---------|
| 技术定位 — 所属路径 | Louvain 只给编号，不给语义 | LLM 读社区内论文标题 → 命名"Attention 优化" |
| 技术定位 — 角色/对标/核心差异 | "范式挑战者"是人类判断 | Claude 读 abstract → 结构化输出 |
| 瓶颈分析 — 当前限制/未解决 | 需要理解论文在解决什么问题 | Claude 读 abstract + 对比前驱 → 提取瓶颈 |
| 结论 — 一句话判断 | 综合以上所有信息的总结 | Claude 汇总前 6 个模块 → 生成结论 |
| 当前阶段 — 工业信号 | "Together AI 在用" 这种信息不在论文里 | 暂时不做，或 LLM 从 abstract 推测 |

这些占面板内容的 **~30%**，是真正需要 AI 的部分。

## 实现路线：三步走

### Step 1：Demo 写死版（现在）

就是 demo-preview.html，30 篇论文全部手写。目的：**验证面板结构和交互是否对**。

老板看到的是最终形态，不需要知道数据是写死的。

### Step 2：半自动版（1-2 天）

接入 OpenAlex API，自动填充 ✅ 和 ⚠️ 部分：

```
输入：论文 ID（如 W4389326242）
  ↓
OpenAlex API → 标题/作者/年份/机构/引用数/引用列表/被引列表
  ↓
引用增速计算 → 阶段判断（Growth/Mature/Early）
  ↓
Louvain 社区检测 → 所属路径
  ↓
引用列表 + 社区过滤 → 关键前驱/后续分叉
  ↓
输出：面板 70% 内容自动填充，❌ 部分留空或显示"待分析"
```

这一步用的全是你已有的代码：`openalex_client.py` + `citation_network.py`。

### Step 3：全自动版（3-5 天）

接入 LLM 填充 ❌ 部分：

```
输入：论文 abstract + 前驱论文 abstracts
  ↓
Prompt 1（技术定位）：
  "对比论文 B 和其前驱 A，B 的技术角色是什么？对标什么？核心差异是什么？"
  → 结构化 JSON 输出
  ↓
Prompt 2（瓶颈分析）：
  "论文 B 在解决什么问题？当前还有什么限制？什么是未解决的？"
  → 结构化 JSON 输出
  ↓
Prompt 3（结论）：
  "基于以上分析，用一句话总结这篇论文在技术路线中的位置。"
  → 一句话
```

每篇论文 3 次 Claude API 调用，成本约 $0.01/篇。30 篇 = $0.30。

### 关于 SPECTER2 + 文献耦合：Phase C 的事，不是现在

v1-thoughts 里想的 SPECTER2 语义向量 + 文献耦合，本质是解决"发现没互相引用但技术相关的论文"。
在 30 篇手选论文的 Demo 里，你已经知道谁和谁相关了——引用关系 + 手工标注就够。
SPECTER2 的 ROI 在 **2500 篇全量数据**时才体现（自动发现隐性关联），属于 Phase C 的锦上添花，不是 Demo 的核心。

## 给老板的话术

> "面板里的信息分三层：
> 第一层是学术数据库的结构化事实——作者、机构、引用关系、引用增速——OpenAlex API 直接拿。
> 第二层是图算法的推断——社区聚类、演进路径筛选、阶段判断规则——这是我们的分析引擎。
> 第三层是 LLM 的结构化判断——技术定位、瓶颈分析、路径命名——Claude 读 abstract 后输出。
> 三层叠加，就是'技术认知压缩器'。
> 其中第一层和第二层完全自动化，第三层每篇论文成本不到一分钱。"

> 如果被追问"社区命名怎么自动化"：
> "Louvain 算法自动把论文聚成社区，然后 LLM 读社区内论文标题，自动生成语义标签。
> 比如它会发现社区里全是 FlashAttention、Ring Attention、MLA 这些论文，就自动命名为'Attention 优化'。
> 不需要人工打标签。"

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| LLM 判断不准 | 结论可能误导 | 标注"AI 生成"，提供 arXiv 原文链接让用户验证 |
| OpenAlex 引用数据缺失 | arXiv 预印本经常没有 referenced_works | 用 Semantic Scholar API 补充（它对 arXiv 覆盖更好） |
| SPECTER2 嵌入获取慢 | 批量计算耗时 | Semantic Scholar 已预计算，直接调 API |
| 成本 | LLM 调用费用 | 30 篇 ~$0.30，2500 篇 ~$25，可控 |

---

# 连线策略：论文之间的边怎么来

## 现状

Demo 里的 `connections` 数组是手写的。经 Semantic Scholar API 验证，大部分连线有真实引用支撑：

| 连线 | 真实引用？ | 说明 |
|------|----------|------|
| Transformer → GPT-3 | ✅ | GPT-3 引用 Transformer |
| Transformer → FlashAttention | ✅ | FlashAttention 引用 Transformer |
| GPT-3 → FlashAttention | ✅ | FlashAttention 引用 GPT-3 |
| FlashAttention → DeepSeek-V3 | ❓ | SS 无数据（论文太新） |
| HiPPO → S4 | ✅ | S4 引用 HiPPO |
| S4 → Mamba | ❓ | SS 无数据（Mamba 引用未被收录） |
| H3 → Mamba | ❓ | 同上 |
| Mamba → Jamba | ✅ | Jamba 引用 Mamba |
| Transformer → Jamba | ✅ | Jamba 引用 Transformer |
| S4 → Griffin | ✅ | Griffin 引用 S4 全称版 |
| Transformer → RWKV | ✅ | RWKV 引用 Transformer |
| Linear Transformer → RWKV | ✅ | RWKV 引用 "Transformers are RNNs" |
| GShard → Mixtral | ✅ | Mixtral 引用 GShard |
| Megablocks → Mixtral | ✅ | Mixtral 引用 Megablocks |
| Switch → Mixtral | ❌ | Mixtral 不引用 Switch（引用更早的 Sparsely-Gated MoE 2017） |

结论：手写连线基本准确，只有 Switch→Mixtral 一条是错的（应改为 Sparsely-Gated MoE → Mixtral）。

## 真实场景：输入论文 ID 或论文名字，怎么自动连线

### 数据源优先级

```
1. Semantic Scholar API（对 arXiv 覆盖最好）
   GET /graph/v1/paper/ArXiv:{arxiv_id}/references → 它引用了谁
   GET /graph/v1/paper/ArXiv:{arxiv_id}/citations  → 谁引用了它

2. OpenAlex API（覆盖更广，但 arXiv 预印本引用经常为空）
   GET /works/{id}?select=referenced_works → 它引用了谁
   GET /works?filter=cites:{id}           → 谁引用了它

3. 如果只有论文名字（没有 ID）
   论文名字 → Semantic Scholar /paper/search?query=xxx → 拿到 paperId
           → OpenAlex /works?search=xxx → 拿到 Work ID
           → 回到上面的流程
```

### 核心问题：引用数据缺失

实测发现：Semantic Scholar 对 2023 年底之后的 arXiv 论文（Mamba、xLSTM、DeepSeek-V3）引用数据经常为空。
这不是 API 的 bug，是这些论文太新，引用关系还没被解析入库。

### 缺失时的 fallback 策略

```
层次 1：引用数据存在 → 直接用（最可靠）
  ↓ 缺失
层次 2：文献耦合 → 两篇论文共同引用 K 篇相同参考文献，K ≥ 3 则连线
  ↓ 仍然不够
层次 3：LLM 判断 → 给 Claude 两篇论文的 abstract，问"B 是否技术上继承了 A"
  输出：yes/no + 置信度 + 一句话理由
  成本：~$0.005/对
  30 篇论文同 lane 内约 50-80 对，成本 < $0.50
```

### 连线质量保证

每条连线标注来源：
- `source: 'citation'` — 有真实引用关系（最可信）
- `source: 'coupling'` — 文献耦合推断（中等可信）
- `source: 'llm'` — LLM 判断（需人工验证）

前端可以用不同线型区分：实线 = citation，虚线 = coupling/llm。

### 给老板的话术

> "连线有三个来源：第一是学术数据库里的真实引用关系，这是事实；
> 第二是文献耦合——两篇论文引用了大量相同的参考文献，说明方法论趋同；
> 第三是 AI 判断——当前两个来源都缺失时，LLM 读摘要判断是否有技术继承关系。
> 每条线都标注了来源，用户可以自己判断可信度。"
