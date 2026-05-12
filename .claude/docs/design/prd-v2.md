# PRD v2 — LLM Systems Evolution Map

> 产品需求文档 v2。基于 v1 的所有设计讨论成果重写。
>
> 日期：2026-05-08

---

## 产品定位

### 一句话

**AI 技术演化地铁图** — 让研究者一眼看出"面对同一个瓶颈，人们产生了哪些不同技术哲学，以及谁赢了"。

### 不是什么

- ❌ 不是论文数据库
- ❌ 不是 citation graph
- ❌ 不是 force-directed graph
- ❌ 不是搜索引擎

### 是什么

- ✅ AI 技术史的可读视觉语言
- ✅ Frontier Attention Flow — 研究注意力迁移图
- ✅ 技术哲学竞争的战场地图
- ✅ 文明演化图谱

### 核心价值

| 价值 | 解释 |
|------|------|
| 全局雷达 | AI frontier 在往哪里迁移 |
| 路线竞争 | 某个问题空间内谁在竞争、谁赢了 |
| 信号发现 | 被忽视但重要的冷门技术 |
| 因果理解 | 为什么这些工作会同时出现 |

---

## 三层视图系统

三个视图回答不同问题，使用不同布局，不强行统一。

| 视图 | 核心 metaphor | 回答的问题 | 布局 | 时间尺度 |
|------|--------------|-----------|------|---------|
| Global View | 文明地图 | AI frontier 在往哪里迁移 | 地铁图 / hierarchical swimlane | 文明时间 |
| Topic View | 技术谱系树 | 某问题空间内部怎么分叉 | lineage tree | 谱系时间 |
| Iteration View | 物种演化轴 | 某路线为什么没死、怎么自我修复 | vertical mutation timeline | 内部工程时间 |
| Arena View | 军备竞赛 | 同时期谁在竞争、谁活下来了 | parallel race tracks | 竞争时间 |

### 四种视图的核心问题

| 视图 | 核心问题 |
|------|---------|
| Global | 为什么时代转向 |
| Topic | 为什么路线分叉 |
| Iteration | 为什么路线持续进化 |
| Arena | 为什么有的路线赢了 |

### 关键原则

1. **不同视图强调不同信息密度** — 全局弱化节点细节，Topic 强化分叉，Iteration 强化 mutation，Arena 强化对比
2. **四种时间尺度** — 每个视图的"时间"含义不同，不共用视觉语言
3. **视图间流转** — Global → Topic → Iteration → Arena（从宏观到微观再到生态）
4. **Iteration 是技术内在逻辑，Arena 是社会生态逻辑** — 先理解技术再理解竞争

---

## 视图 1：Global View（文明地图）

### 用户回答的问题

> "AI community 为什么在这个时期突然转向某个方向？"

### 可观察的模式

- 某阶段讨论 Model Architecture 的人较多
- 某阶段 Pretraining 讨论较多
- 某阶段 Test-time Computing 讨论较多
- 某阶段 RL 讨论较多

### 布局：Hierarchical Swimlane（地铁图）

```
X轴 = 时间（2020 → 2026，按季度）
Y轴 = Bottleneck → Paradigm（可折叠树状泳道）

结构：
  Bottleneck (section header)
    └── Paradigm (row)
          └── Paper (节点)
```

### 信息密度：低节点细节，高趋势感知

| 强调 | 弱化 |
|------|------|
| Era shift | 单篇论文细节 |
| Lane 热度变化 | 具体 arXiv ID |
| Cross-lane linkage | 边的精确关系 |
| 时代重心迁移 | 论文摘要 |

### Era 背景层

全局视图叠加三个 Era 作为时间段背景：

| Era | 时间 | 核心命题 | 视觉特征 |
|-----|------|---------|---------|
| Knowledge Era | 2020-2023 | 更多参数 | 路线清晰，节点稀疏 |
| Reasoning Era | 2024-2025 | 更长推理 | 密度最高，cross-links 激增 |
| Agency Frontier | 2025- | 长期闭环 | 边缘虚化，拓扑未稳定 |

### Lane 活跃度随 Era 变化

Lane 结构不变，但不同 Era 内 Lane 的视觉活跃度不同：

```
Era1: compute_scaling 最亮 → 其余 opacity 降低
Era2: memory_wall + sequence_scaling 爆发 → cross-links 激增
Era3: memory + RL 开始交织 → feedback loops 出现
```

### 交互

- 点击 Era 标签 → 该时段 dominant lanes 全亮
- 点击 Bottleneck section → 跳转 Topic View
- Hover 节点 → tooltip + 高亮连线
- 时间滑块 → 只显示该时段，活跃度自动计算

---

## 视图 2：Topic View（技术谱系树）

### 用户回答的问题

> "某个问题空间内部，技术路线如何分叉、竞争、融合？"

### 核心不是时间轴，是分叉（fork）

进入 Topic View 后，用户看到的是**技术谱系树**——从一个共同祖先分叉出不同路线。

### 布局：Lineage Tree

```
Transformer (root)
├── Linear Attention
│   ├── Performer
│   ├── Linear Transformer
│   └── DeltaNet → GLA
│
├── RNN Revival
│   ├── RWKV V4 → V5 → V6 → V7
│   ├── RetNet
│   └── xLSTM
│
├── SSM Line
│   ├── S4 → Hyena → Mamba → Mamba-2
│   └── Griffin
│
└── Hybrid
    ├── Jamba (SSM + Attention + MoE)
    └── Zamba
```

### 核心观察维度

| 维度 | 含义 | 示例 |
|------|------|------|
| 技术分叉 (fork) | 同一问题出现几种路线 | Sparse vs SSM vs Linear |
| Tradeoff 演化 | 每条路线的优缺点如何变化 | Linear: O(n) 但 expressivity 弱 |
| Dominance shift | 哪条路线在哪个时期占主导 | 2024 Mamba 爆发，2025 Hybrid 融合 |
| Player Map | 谁在推动哪条路线 | RWKV=BlinkDL, Mamba=CMU/Princeton |

### Tradeoff 可视化

每条路线有一个 tradeoff 雷达或标注：

| 路线 | 优点 | 缺点 |
|------|------|------|
| Linear Attention | O(n) 复杂度 | expressivity 弱 |
| RWKV | cheap inference | retrieval 弱 |
| Mamba | long sequence 强 | hardware ecosystem 弱 |
| Transformer | 生态极强 | O(n²)，KV 膨胀 |

### 信息密度：高细节，强关系

| 强调 | 弱化 |
|------|------|
| 分叉点 | Era 背景 |
| builds_on 链 | 跨 lane 关系 |
| competes_with 对比 | Pressure Wave |
| Player / 机构 | 全局趋势 |

### 交互

- 点击分叉节点 → 展开子树
- Hover 路线 → 高亮整条 lineage + 显示 tradeoff
- 点击具体论文 → Side Panel 详情
- 点击 competes_with → 跳转 Arena View
- 点击某条路线的版本序列 → 跳转 Iteration View

---

## 视图 3：Iteration View（物种演化轴）

### 用户回答的问题

> "这个架构为什么不断变？每次 mutation 在修什么问题？"

### 核心不是 fork，不是 competition，是 refinement

Iteration View 展示的是**单个 organism 的成长**——同一个设计哲学如何不断修补自身。

### 布局：Vertical Mutation Timeline

```
RWKV
│
├── V1 (2021)
│    └─ 初始 RNN-Transformer 混合直觉
│    └─ Problem: 训练不稳定
│
├── V4 (2023 Q1)
│    └─ 引入更稳定 state update
│    └─ Problem: parallelism 不够
│
├── V5 (2023 Q3)
│    └─ parallel training trick
│    └─ Problem: fine-tuning 困难
│
├── V6 (2024 Q1)
│    └─ dynamic state tuning
│    └─ Problem: inference 速度
│
├── V7 (2024 Q3)
│    └─ inference optimization
│    └─ Problem: scaling 天花板
│
└── V8 (2025)
     └─ multi-head + scaling improvements
```

### 核心观察维度

| 维度 | 含义 | 示例 |
|------|------|------|
| Problem → Mutation | 每次版本在修什么瓶颈 | V4 修训练稳定性 |
| 设计哲学连续性 | 什么不变 | RWKV 始终坚持"RNN+并行" |
| Refinement 方向 | 在哪些维度持续精炼 | 训练→推理→scaling |
| 外部压力 | 什么逼它变 | Mamba 发布后加速迭代 |

### 核心 narrative：Problem → Mutation

```
遇到瓶颈
  ↓
版本调整（mutation）
  ↓
解决上一个问题，暴露新问题
  ↓
下一次 mutation
```

**技术史不是 "paper magically appears"，而是不断 patch 自己的问题。**

### 适用对象

| 路线 | 版本序列 |
|------|---------|
| RWKV | V1 → V4 → V5 → V6 → V7 → V8 |
| Mamba | Mamba → Mamba-2 → Mamba-3 |
| FlashAttention | V1 → V2 → V3 → V4 |
| MLA | MQA → GQA → MLA(V2) → MLA(V3) → TransMLA |
| vLLM | PagedAttn → vLLM v1 → v2 |

### 信息密度：高工程感，强因果

| 强调 | 弱化 |
|------|------|
| 版本间差异 | 跨路线对比 |
| Problem → Solution | Era 背景 |
| 设计决策理由 | 宏观趋势 |
| 具体 tradeoff 变化 | 其他竞争者 |

### 视觉风格

- 纵向时间轴（从上到下）
- 每个版本节点 = 一个"站"
- 站与站之间标注：mutation reason
- 侧边标注外部压力事件（如"Mamba 发布 → 加速迭代"）
- 类比：iPhone 代际演化图 / Linux kernel changelog

### 交互

- 点击版本节点 → Side Panel 显示该版本详情
- Hover 两个版本之间 → 显示 diff（改了什么、为什么）
- 侧边外部压力标注可点击 → 跳回 Global/Arena 看上下文

---

## 视图 4：Arena View（军备竞赛）

### 用户回答的问题

> "在同一时期，谁更有竞争力？谁活下来了？"

### 核心不是演化，是同期对比

Arena View 本质是**平行赛道视图**——多条技术路线在同一时间轴上的竞争态。

### 布局：Parallel Race Tracks

```
Transformer ────────────●────────●────────●────────●
RWKV        ─────●────●────●────●────●────●────●
Mamba             ─────────●────●────●────●
RetNet             ─────●────●
```

时间同步比较是重点。用户看到的是"同一年谁发了什么"。

### 核心观察维度

| 维度 | 含义 |
|------|------|
| 能力曲线 | 每条路线在不同维度的能力对比 |
| 版本迭代速度 | 谁迭代更快 |
| Production adoption | 谁真正被工业界采用 |
| 路线命运 | 哪条路线被吸收/消亡/统治 |

### 能力对比矩阵

| 维度 | RWKV | Mamba | Transformer |
|------|------|-------|-------------|
| 长上下文 | 强 | 很强 | 中 |
| 推理成本 | 低 | 低 | 高 |
| Ecosystem | 弱 | 中 | 极强 |
| Production adoption | 弱 | 中 | 极强 |
| 训练效率 | 中 | 中 | 强 |

### 路线命运标注

每条路线有一个"命运标签"：

| 路线 | 命运 |
|------|------|
| Sparse Attention | 部分思想被吸收，未成主干 |
| Mamba | 研究热度极高，production adoption 有限 |
| RWKV | 社区驱动，小众但活跃 |
| Transformer | 不断被修补，始终统治 |
| Hybrid | 融合派，2025 后兴起 |

### 信息密度：高对比，强判断

| 强调 | 弱化 |
|------|------|
| 同期对比 | 分叉历史 |
| 能力维度 | builds_on 关系 |
| 采用度 / 命运 | 技术细节 |
| 版本号 | 非竞争论文 |

### 交互

- 选择要对比的路线（多选）
- 时间滑块 → 某年的能力快照
- Hover 节点 → 该版本的关键改进
- 底部 summary → "谁赢了" 结论性标注

---

## 四层 Ontology

```
Layer 0 — Era（时代背景）    → "AI 系统正在变成什么"
Layer 1 — Bottleneck（压力轴）→ "工程瓶颈是什么"
Layer 2 — Paradigm（技术哲学）→ "用什么信仰解题"
Layer 3 — Paper（具体实现）   → "谁做了什么"
```

因果关系：**Era shift → 暴露新 Bottleneck → 催生新 Paradigm → 产出 Paper**

---

## 论文分类体系

### Bottleneck（压力轴）— Y 轴 section

| Bottleneck | 一句话 | 核心问题 |
|------------|--------|----------|
| sequence_scaling | 让模型处理更长文本 | O(N²) 怎么打破 |
| memory_wall | 给定模型能不能 serve | KV cache + IO 带宽 |
| compute_scaling | 用更少算力获得更强能力 | 参数/训练/推理效率 |

### Paradigm（技术哲学）— Y 轴 row

#### sequence_scaling 内

| Paradigm | 代表 | 关键问题 |
|----------|------|---------|
| Linear / SSM | Mamba, RWKV, RetNet, GLA, xLSTM | 保持表达力 + O(n) |
| Sparse / Chunked | Ring Attn, Infini-Attn, LongNet, StreamingLLM | 不重训推到 1M+ |
| Memory-Augmented | RoPE, ALiBi, YaRN, HMT, RETRO | 位置外推 + 记忆持久化 |
| Kernel Optimization | FlashAttn V1-V4 | IO-aware kernel |

#### memory_wall 内

| Paradigm | 代表 | 关键问题 |
|----------|------|---------|
| KV Compression | MQA, GQA, MLA, TransMLA | KV 显存降一个数量级 |
| Paging / Offloading | PagedAttn, vLLM, PyramidKV | HBM 带宽极限 |
| Quantization | AWQ, GPTQ, SmoothQuant, FP8 | 精度 vs 速度 |
| Decoding Strategy | Speculative Dec., Medusa, EAGLE | 减少前向次数 |

#### compute_scaling 内

| Paradigm | 代表 | 关键问题 |
|----------|------|---------|
| MoE / Routing | GShard, Switch, Mixtral, DS-MoE, DS-V3 | 稀疏激活 + 负载均衡 |
| Reasoning Scaling | CoT, ToT, o1, R1, Verifier | test-time compute 分配 |

### Layer（解决方案层级）— 形状编码

| Layer | 形状 | 含义 |
|-------|------|------|
| arch | 圆形 | 改模型结构 |
| sys | 方形 | 改 kernel / parallelism |
| infer | 菱形 | 改 decoding / runtime |
| train | 三角 | 改训练方式 / RL |
| memory | 六边形 | 改 KV / 位置编码 / 外部记忆 |

---

## 视觉编码（详见 visual-encoding.md）

| 维度 | 编码 | 值域 |
|------|------|------|
| 颜色 | Paradigm（世界观） | 5 色：灰蓝/蓝/青绿/红/橙 |
| 形状 | Layer（干预层） | 5 形：圆/方/菱/三角/六边形 |
| 大小 | Impact (citations) | log(cited_by_count) |
| 连线 | 关系 | 实线=builds_on / 短虚线=competes / 长虚线=lineage |

---

## Side Panel（论文详情）

点击任一节点后右侧展开：

```
面包屑:     Context Scaling > Linear / SSM
标题:       Mamba-2
元数据:     2024 Q2 · 1,892 cites · arXiv:2405.21060

解决的问题:  如何 O(n) 复杂度做长序列建模
核心思想:    Selective SSM + 硬件感知优化

Paradigm:   ● Post-Attention / SSM
Layer:      ○ arch（架构）
Bottleneck: Context Scaling

关系:
  Builds on:    Mamba (2023 Q4), S4 (2022)
  Competes with: RWKV v6, RetNet, Linear Transformer
  Phil. Lineage: Hyena, xLSTM

摘要:  2-3 句话

链接:  arXiv | Paper | Code | Project
```

---

## 视图间流转

```
Global View（文明地图）
  │
  ├── 点击 Bottleneck section
  │         ↓
  │   Topic View（技术谱系树）
  │         │
  │         ├── 点击某条路线的版本序列
  │         │         ↓
  │         │   Iteration View（物种演化轴）
  │         │
  │         ├── 点击 competes_with 关系
  │         │         ↓
  │         │   Arena View（军备竞赛）
  │         │
  │         └── 点击论文节点
  │                   ↓
  │               Side Panel（详情）
  │
  └── 点击 Era 标签
            ↓
      Era Focus Mode（该时代 dominant lanes 高亮）
```

### 逻辑递进

```
为什么时代转向（Global）
  → 为什么路线分叉（Topic）
    → 为什么路线持续进化（Iteration）
      → 为什么有的路线赢了（Arena）
```

从宏观到微观，从技术内在逻辑到社会生态逻辑。

---

## 技术栈决策

| 层级 | 选择 | 理由 |
|------|------|------|
| 布局引擎 | D3.js 手动布局 / 纯 SVG + React | 需要完全控制位置，拒绝自动布局 |
| 前端框架 | Next.js 14 + React 18 | App Router, 现有基础 |
| 后端 | FastAPI + NetworkX | 图分析 + API |
| 数据源 | OpenAlex API + 人工标注 | citations 自动获取，taxonomy 人工 |
| ~~react-force-graph~~ | ❌ 放弃 | 自动布局破坏叙事 |

---

## 实现分期

### Phase 1：Global Narrative（MVP）

建立 Era + Bottleneck + Paradigm 的全局骨架。

| 交付物 | 说明 |
|--------|------|
| 全局视图 HTML 原型 | Hierarchical swimlane |
| 50-60 篇核心论文 | seed_papers.py |
| Side Panel | 点击节点显示详情 |
| Era 背景分段 + NOW 线 | 三段视觉差异 |
| builds_on 连线 | 技术路线骨架 |

### Phase 2：Topic Lineage

建立 fork + tradeoff + philosophical split。

| 交付物 | 说明 |
|--------|------|
| Topic View | Lineage tree 布局 |
| 分叉可视化 | 从共同祖先展开子路线 |
| Tradeoff 标注 | 每条路线的优缺点 |
| Player Map | 机构/研究者标注 |

### Phase 3：Iteration View

建立 mutation + self-repair + refinement history。

| 交付物 | 说明 |
|--------|------|
| Iteration View | Vertical mutation timeline |
| Problem → Mutation 标注 | 每个版本在修什么 |
| 外部压力标注 | 什么事件逼它演化 |
| 版本 diff | Hover 两版本显示差异 |

### Phase 4：Arena + Ecosystem

建立 dominance + adoption + ecosystem。

| 交付物 | 说明 |
|--------|------|
| Arena View | Parallel race tracks |
| 能力对比矩阵 | 多维度打分 |
| 路线命运标注 | 吸收/消亡/统治 |
| 后端 API | OpenAlex 集成 |
| Era Focus 交互 | Lane 活跃度动态变化 |
| 信号发现 | Impact 异常检测 |

### 为什么这个顺序

```
Phase 1 (Global)  — 宏观框架，让人"震撼"
Phase 2 (Topic)   — 技术分叉，让人"理解"
Phase 3 (Iteration) — 内部演化，让人"沉浸"（工程感最强）
Phase 4 (Arena)   — 生态竞争，让人"判断"（需要最多外部数据）
```

Iteration 先于 Arena 的原因：
- Iteration 属于技术内在逻辑，数据需求小（版本序列 + diff）
- Arena 属于社会生态逻辑，需要 adoption/ecosystem 等外部数据
- 用户必须先理解"路线为什么存在"，才能理解"谁赢了"

---

## 设计约束

- Dieter Rams 10 原则严格遵守
- 背景纯白 #FFFFFF，无渐变无阴影
- 强调色 #FF4400 仅用于 NOW 线和活跃状态
- 字体 IBM Plex Sans
- 最大信息密度，最少视觉噪音
- 完全人为编排布局（curated topology），不用自动布局
