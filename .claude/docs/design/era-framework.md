# Era Framework — 时代演化层设计

> 定义 AI 能力中心迁移的时代背景层。与 visual-encoding.md / paper-taxonomy.md 配合使用。
>
> 日期：2026-05-08

---

## 核心认知

### 四层 Ontology

```
Layer 0 — Era（时代背景层）     → "整个 AI 系统正在变成什么"
Layer 1 — Bottleneck（压力轴）  → "工程瓶颈是什么"
Layer 2 — Paradigm（技术哲学）  → "用什么信仰解题"
Layer 3 — Paper（具体实现）     → "谁做了什么"
```

### Era 和 Bottleneck 的关系：因果，不是包含

```
Era shift → 暴露新 Bottleneck → 催生新 Paradigm → 产出 Paper
```

Era 不是另一根轴，不是 row。它是：
**"为什么这些 Bottleneck 会在这个时间点同时爆发"的因果解释层。**

---

## 三个 Era 定义

### Era 1 — Knowledge Acquisition Era（知识获取时代）

| 属性 | 值 |
|------|---|
| 时间 | 2020 – 2023 |
| 核心命题 | 让模型"知道更多" |
| 核心信仰 | Capability ∝ Scale |
| 主旋律 | 更多参数 |
| 视觉状态 | **历史已固化** — 路线清晰，节点稀疏但确定 |

#### 主导路线

- **Dense Scaling**: GPT-3 → Chinchilla → LLaMA
- **MoE Scaling**: GShard → Switch → Mixtral
- **Data Engineering**: 数据清洗、去重、配比

#### 催生的 Bottleneck

- compute_scaling → "模型太大训不起"
- sequence_scaling → "context 太短读不完"

#### 时代特征

模型像**压缩互联网**。参数越大越强。

---

### Era 2 — Reasoning / Test-time Era（思维逻辑时代）

| 属性 | 值 |
|------|---|
| 时间 | 2024 – 2025 |
| 核心命题 | 让模型"思考" |
| 核心信仰 | Capability ∝ Test-time Compute |
| 主旋律 | 更长推理 |
| 视觉状态 | **当前主战场** — 密度最高，竞争最激烈 |

#### 关键因果链

```
o1 让推理 token 暴涨
  ↓
Inference 成本爆炸
  ↓
MLA / Speculative / FlashAttn 必须出现
```

**MLA 和 o1 是同一时代产物** — "能力范式变化"倒逼"系统工程变化"。

#### 主导路线

- **Reasoning Scaling**: CoT → ToT → o1 → R1 → Verifier
- **Inference Efficiency**: MLA → GQA → PagedAttention → Speculative Decoding
- **Long Context**: Mamba → Ring Attention → LongRoPE

#### 催生的 Bottleneck

- memory_wall → "推理 token 太多，KV cache 爆了"
- compute_scaling → "test-time compute 分配问题"

#### 时代特征

参数规模不再是唯一变量。**推理过程**成为能力来源。

---

### Era 3 — Agency Frontier（能动与组织时代）

| 属性 | 值 |
|------|---|
| 时间 | 2025 – |
| 核心命题 | 让 AI 持续行动 |
| 核心信仰 | Capability ∝ Memory + Planning + Feedback Loops |
| 主旋律 | 长期闭环行动 |
| 视觉状态 | **边缘未探索区域** — 拓扑未稳定，正在形成 |

#### 核心变化

从"单次推理"变成**"持续闭环"**。

#### 方向性节点（不求完整，标记方向）

| 节点 | 代表方向 |
|------|---------|
| MemGPT | Persistent Memory |
| Voyager | Embodied Agent |
| Generative Agents | Social Simulation |
| World Models | Internal World Model |
| SWE-agent | Code Agent |
| OpenAI Operator | Computer Use |
| Deep Research | Long-horizon Research |
| Toolformer | Tool Use |

#### 催生的 Bottleneck

- memory → "没有长期记忆"
- planning → "没有目标分解能力"
- feedback → "没有验证闭环"

---

## 视觉设计

### Era 作为时间段背景层

Era 映射到 X 轴时间段，作为**最底层背景色**（比 Pressure Wave 更底）：

```
|   Knowledge Era    |   Reasoning Era    |  Agency Frontier  |
|  2020─────2023     |  2024─────2025     |  2025──→          |
|   淡灰 #FAFAFA     |   白色 #FFFFFF      |  边缘虚化          |
```

### 三段视觉差异化

| Era | 视觉特征 | 叙事感 |
|-----|---------|--------|
| Knowledge Era | opacity 正常，路线清晰，节点间距大 | 历史已经固化 |
| Reasoning Era | opacity 100%，密度最高，连线最密 | 当前主战场 |
| Agency Frontier | opacity 降低 (40-60%)，边界虚线，节点稀疏 | 未来正在形成 |

### Agency Frontier 特殊视觉处理

```
- 背景：从白色渐变到 transparent（唯一允许的"渐变"：fade out）
- 节点：opacity 50%，无 stroke，只有 fill
- 连线：虚线，opacity 30%
- 边界：右侧无硬边，自然消散
- 标注："Frontier — topology unstable" 淡灰文字
- 效果：像地图边缘的"未探索区域"
```

### Era 分割线

```
Knowledge → Reasoning 分割线：
  位置：2023 Q4（GPT-4 Turbo 发布）
  视觉：竖向淡色虚线 + "Paradigm Shift" 标注

Reasoning → Agency 分割线：
  位置：2025 Q2（Operator/Deep Research 发布）
  视觉：竖向更淡虚线 + "Emerging" 标注
  特征：线条本身也是 fadeout 的
```

---

## 叙事效果

整个地图从左到右呈现：

```
← 确定                              不确定 →
← 密集                              稀疏 →
← 清晰                              模糊 →
```

**像文明正在向右扩张。**

### 用户体验

1. **点击 "Knowledge Era"** → 左侧 Dense/MoE 路线全亮
2. **点击 "Reasoning Era"** → CoT + o1 + MLA + FlashAttn + Speculative 全亮
   - 用户突然意识到：这些不是独立论文，而是同一个时代问题的不同侧面
3. **hover "Agency Frontier"** → 稀疏节点微微亮起，拓扑不确定感
   - 用户感受到：这是正在书写的历史

---

## 与现有 Ontology 的融合

```
Era（背景时间段）
  ├── 因果触发 → Bottleneck（Y轴 section header）
  │                 └── Paradigm（Y轴 row）
  │                       └── Paper（节点）
  └── 解释 → Pressure Wave（为什么这些工作同时出现）
```

### Era 不替代 Bottleneck

| 概念 | 作用 | 例子 |
|------|------|------|
| Era | 解释"时代精神是什么" | "现在是 Reasoning Era" |
| Bottleneck | 解释"具体卡在哪" | "推理太贵" |
| Pressure Wave | 解释"为什么这半年集中爆发" | "o1 发布后 inference cost crisis" |

三者分工明确，层级递进。

---

## 实现优先级

| 特性 | 难度 | 建议 |
|------|------|------|
| Era 背景色分段 | ★☆☆ | P1 — 纯 CSS |
| Era 分割线 | ★☆☆ | P1 — 竖线 + 标注 |
| Agency Frontier fade-out | ★★☆ | P2 — opacity + clip |
| Era 点击高亮 | ★★★ | P2 — 需要节点-Era 映射关系 |
| Era 标题悬浮 | ★☆☆ | P1 — fixed header |

---

## 关键约束

1. **Era 最多 3-5 个** — 它是"时代精神"，不是技术类别，否则会失控
2. **Era 3 节点不求完整** — 只放"方向性节点"，标记方向即可
3. **Era 不是 Y 轴** — 它是 X 轴时间段的语义标注
4. **因果方向明确** — Era shift → Bottleneck exposure → Paradigm creation

---

## 全局视图的灵魂：Frontier Attention Flow

### 核心问题

全局视图不应该只是"展示所有 topic"。它应该展示：

**AI frontier 的注意力中心如何迁移。**

用户要感知的不是"这里有 50 篇论文"，而是：
- 某阶段大家都在讨论 Model Architecture
- 某阶段大家都在讨论 Pretraining
- 某阶段 Test-time Computing 爆发
- 某阶段 RL 讨论激增

### 设计决策：不改 Y 轴，给 Lane 加"时代热度"

Y 轴 = Bottleneck → Paradigm 结构保持不变（稳定骨架）。

变化的是：**每个 Lane 在不同 Era 内的视觉活跃度。**

---

## Era Focus 数据模型

```yaml
era_focus:
  knowledge_era:
    time: "2020-2023"
    dominant_lanes:
      - compute_scaling  # Lane 3-A 参数规模
    suppressed_lanes:
      - memory_wall      # 还不是瓶颈
    dominant_paradigms:
      - dense_scaling
      - moe
    optimization_target: pre-training
    graph_shape: "linear chains, few cross-links"
    external_trigger: "GPT-3 scaling law discovery"

  reasoning_era:
    time: "2024-2025"
    dominant_lanes:
      - sequence_scaling  # Lane 1-A/B 爆发
      - memory_wall       # Lane 2 推理效率
      - compute_scaling   # Lane 3-B test-time
    suppressed_lanes:
      - compute_scaling   # Lane 3-A pretraining 退潮
    dominant_paradigms:
      - test_time_scaling
      - conditional_compute
      - post_attention
    optimization_target: inference / test-time compute
    graph_shape: "cross-links 激增, density explosion"
    external_trigger: "o1 发布 / API 价格战"

  agency_frontier:
    time: "2025-"
    dominant_lanes:
      - sequence_scaling  # Lane 1-C 记忆
      - compute_scaling   # Lane 3-C RL/Verifier
    emerging_paradigms:
      - persistent_memory
      - feedback_loops
      - tool_use
    optimization_target: memory + planning + feedback
    graph_shape: "feedback loops, cross-lane fusion"
    external_trigger: "Operator / Deep Research / SWE-agent"
```

---

## Era Phase Signature（时代相变特征）

每个 Era 的图拓扑有不同的"形态特征"，像物理学中的相变：

### Era 1 — Scale Phase

```
图像特征：
  - 节点：大而稀疏，间距宽
  - 边：线性链（A→B→C），few cross-links
  - 活跃 lane：compute_scaling 最亮
  - 其余 lane：opacity 50-70%
  - 整体感：扩建机器
```

### Era 2 — Inference Phase

```
图像特征：
  - 节点：密集爆发，同期多论文并行
  - 边：cross-lane links 激增（MLA↔o1↔Speculative 互联）
  - 活跃 lane：memory_wall + sequence_scaling + compute(test-time) 全亮
  - 整体感：计算资源危机 → 多路径竞争
```

### Era 3 — Closed-loop Phase

```
图像特征：
  - 节点：稀疏但出现反馈环
  - 边：graph 出现 cycles（memory → action → feedback → memory）
  - 活跃 lane：memory + RL 开始交织
  - 跨 lane：fusion links（不再是单向演进，是闭环）
  - 整体感：系统开始持续运行
```

---

## Lane 活跃度视觉映射

| 视觉属性 | 活跃 Lane | 抑制 Lane |
|---------|----------|----------|
| 节点 opacity | 100% | 40-60% |
| 节点大小 | 正常 (log citations) | 缩小 70% |
| 连线 opacity | 80% | 20% |
| 连线粗细 | 1.5px | 0.8px |
| Label | 全部显示 | 仅 high-impact 显示 |
| Paradigm row 背景 | 微色 (#FAFBFC) | 无 |

### 活跃度不是 binary，是连续的

```
每个 lane 在每个 era 有一个 attention_weight: 0.0 → 1.0

视觉公式：
  node_opacity = 0.4 + 0.6 * attention_weight
  node_scale = 0.7 + 0.3 * attention_weight
  edge_opacity = 0.2 + 0.6 * attention_weight
```

---

## 全局视图交互：Era 作为 Lens

### 默认状态

所有 Era 均匀显示，无 focus。用户看到完整地图。
但因为 Era 2 本身节点最密，自然视觉重心在中段。

### 点击 Era 标签

进入"Era Focus Mode"：
- 该 Era 时段内的 dominant lanes 全亮
- 其余 lanes 对应时段内 opacity 降低
- cross-era 的 builds_on 链保持可见（保证上下文）
- 底部显示 Era 概要卡片："核心命题 / 主导范式 / 外部触发"

### 拖动时间滑块

用户可以拖动一个 time range selector：
- 只显示该时间段内的节点
- Lane 活跃度根据该时段自动计算
- 效果：**用户亲眼看到注意力中心在迁移**

---

## 核心叙事效果

用户在全局视图中看到的不是"所有论文平铺"，而是：

```
2020-2023: compute_scaling lane 最亮，大节点（GPT-3, Chinchilla, Mixtral）
            其他 lane 存在但安静

2024:      突然 memory_wall + sequence_scaling 爆发
            cross-links 激增
            用户感知到："发生了什么？"
            → Era 标注告诉他："Reasoning Era — o1 让推理成本爆炸"

2025:      右侧开始模糊
            memory + RL lane 开始出现 feedback loops
            但拓扑不稳定
            → "这就是现在正在发生的事"
```

**图的拓扑形态本身在讲故事。**

不需要文字解释。Lane 结构不变，但它们的"亮度"和"互联密度"在不同时段完全不同。

这就是"Frontier Attention Flow"——用 topology 相变来表达时代迁移。

---

## 与已有设计的关系总结

| 层级 | 视觉载体 | 回答的问题 |
|------|---------|-----------|
| Era | X轴背景段 + Lane 活跃度 | "时代精神是什么" |
| Bottleneck | Y轴 section header | "卡在哪" |
| Paradigm | Y轴 row | "用什么信仰解题" |
| Pressure Wave | 背景带 | "为什么这半年集中爆发" |
| Paper | 节点 | "谁做了什么" |
| Philosophical Lineage | 跨 lane 虚线 | "看似无关的工作为什么本质相同" |

六个概念，六种视觉载体，分工无重叠。
