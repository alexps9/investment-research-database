# Paper Taxonomy — 论文分类体系 v2

> 权威定义文件。所有数据源（seed_papers.py / seed-data.ts / 原型）必须遵循此分类。
> 
> 更新日期：2026-05-08

---

## 核心设计原则

分类使用 **两个正交维度** 而非嵌套层级：

```
维度 1 — Lane (压力轴 / 问题空间)    → "这篇论文缓解什么瓶颈"
维度 2 — Layer (解决方案层级)         → "在技术栈的哪一层动手"
```

附加标签：
- `paradigms[]` — 属于什么架构范式（可多个）
- `builds_on[]` — 继承谁
- `competes_with[]` — 对抗/替代谁

这解决了旧分类中 Mamba (arch) 和 FlashAttention (sys) 被强行放在同一抽象层的问题。

---

## 维度 1 — Lane (压力轴)

三条 lane 处于同一抽象层：都是 **Scaling 压力的不同切面**。

| Lane ID | 名称 | 一句话 | 核心问题 |
|---------|------|--------|----------|
| `sequence_scaling` | 序列长度 Scaling | 让模型处理更长文本 | O(N²) attention 怎么打破 |
| `memory_wall` | 显存墙 / 推理效率 | 给定模型能不能 serve | KV cache 占满 + IO 带宽打满 |
| `compute_scaling` | 算力 Scaling | 用更少算力获得更强能力 | 参数/训练/推理三个维度的效率 |

### Lane 边界定义

**sequence_scaling** — 改变模型 **能力** 的上限（输入能有多长）
- Mamba ✓ — 改了模型结构让它能处理无限长
- RoPE ✓ — 改了位置编码让它能外推

**memory_wall** — 改变模型 **部署** 的可行性（给定模型能不能跑起来）
- FlashAttention ✓ — 不改模型能力，让同一模型 serve 更快
- PagedAttention ✓ — 不改模型，解决内存碎片
- Speculative Decoding ✓ — 不改模型，减少延迟
- MLA ✓ — 压缩 KV cache 让 serve 成本下降

**compute_scaling** — 改变 **算力投入的 ROI**
- MoE ✓ — model parameter scaling (稀疏激活降训练/推理成本)
- RL Scaling ✓ — training compute scaling (RLHF → verifier → rubrics)
- Test-time Scaling ✓ — inference compute scaling (CoT / o1 / budget allocation)

---

## 维度 2 — Layer (解决方案层级)

| Layer ID | 含义 | 动什么 | 典型技术 |
|----------|------|--------|----------|
| `arch` | Architecture | 改模型结构 | Mamba, RetNet, MoE routing, Griffin |
| `sys` | Systems | 改 kernel / memory / parallelism | FlashAttention, PagedAttention, MegaBlocks |
| `train` | Training | 改训练方式 / 数据 / RL | RL scaling, RLHF, curriculum, verifier |
| `infer` | Inference | 改 decoding / runtime | Speculative Dec., Medusa, CoT |
| `memory` | Memory | 改 KV / 位置编码 / external memory | MLA, GQA, RoPE, RETRO |

### Layer 判断规则

- 如果 **去掉这个改动模型架构变了** → `arch`
- 如果 **模型不变但 kernel/调度变了** → `sys`
- 如果 **模型不变但 KV 结构/位置信息变了** → `memory`
- 如果 **模型不变但 decoding 策略变了** → `infer`
- 如果 **模型不变但训练 pipeline 变了** → `train`

---

## 二维交叉示例

| 论文 | Lane | Layer | 为什么 |
|------|------|-------|--------|
| Mamba | sequence_scaling | arch | 新架构解决长序列 |
| FlashAttention | memory_wall | sys | IO-aware kernel 解决 serve |
| MLA (DeepSeek-V2) | memory_wall | memory | 压缩 KV cache |
| RoPE | sequence_scaling | memory | 位置编码外推长度 |
| Speculative Decoding | memory_wall | infer | 改 decoding 降延迟 |
| MoE (Switch) | compute_scaling | arch | 稀疏激活降训练成本 |
| DeepSeek-R1 | compute_scaling | train | RL scaling |
| o1 / CoT | compute_scaling | infer | test-time scaling |
| PagedAttention | memory_wall | sys | 内存管理 |
| RWKV | sequence_scaling | arch | RNN 复兴替代 attention |

---

## Paradigm 标签（附加维度）

paradigm 不做轴，作为 tag 附着在论文上，支持多值：

```
paradigms:
  - attention      # 标准 Transformer attention 家族
  - ssm            # State Space Model 家族
  - rnn            # 现代 RNN (RWKV, RetNet, xLSTM)
  - linear-attn    # 线性注意力 (Performer, GLA)
  - moe            # Mixture of Experts
  - hybrid         # 混合架构
  - speculative    # 投机解码家族
  - rl             # 强化学习 / reward / verifier
```

---

## 最小论文 Schema

```typescript
type PaperNode = {
  // 身份
  id: string                          // stable slug, e.g. "mamba-2"
  title: string
  arxiv_id?: string                   // e.g. "2312.00752"
  year: number
  quarter: 1 | 2 | 3 | 4

  // 维度 1：问题空间（唯一）
  lane: "sequence_scaling" | "memory_wall" | "compute_scaling"

  // 维度 2：技术层（唯一）
  layer: "arch" | "sys" | "train" | "infer" | "memory"

  // 范式标签（可多个）
  paradigms: string[]
  // e.g. ["ssm"], ["attention", "moe"], ["rnn", "hybrid"]

  // 关系
  builds_on: string[]                 // 继承/演进自哪些 paper id
  competes_with: string[]             // 同时期解决同一问题的竞争者

  // 重要性
  impact: "high" | "mid" | "low"
  cited_by_count?: number
}
```

### Python 对应（seed_papers.py）

```python
Lane = Literal["sequence_scaling", "memory_wall", "compute_scaling"]
Layer = Literal["arch", "sys", "train", "infer", "memory"]

class SeedPaper(BaseModel):
    paper_id: str
    title: str
    arxiv_id: Optional[str]
    year: int
    quarter: Literal[1, 2, 3, 4]

    lane: Lane
    layer: Layer
    paradigms: List[str] = []

    builds_on: List[str] = []
    competes_with: List[str] = []

    impact: Optional[Literal["high", "mid", "low"]]
    cited_by_count: Optional[int]
```

---

## 可视化映射

| 视图 | X轴 | Y轴 | 颜色 | 大小 |
|------|-----|-----|------|------|
| 全局视图 | 时间 | lane (3行) | layer 颜色 | log(citations) |
| 单一主题 | 时间 | paradigm 分行 | layer 颜色 | log(citations) |
| 架构对比 | — | — | paradigm 颜色 | — |

单一主题视图（如选中 sequence_scaling）：
- Y 轴按 paradigm 分行：SSM / RNN / Linear-Attn / Hybrid / Attention
- 同一行内节点按 layer 区分形状或深浅
- 连接线：builds_on 实线，competes_with 虚线

---

## 数据同步架构

```
单一数据源 (Single Source of Truth)
         │
   backend/app/data/seed_papers.py   ← 人工维护
         │
         ├── scripts/sync_papers.py  → frontend/src/lib/citation-graph/seed-data.ts
         └── scripts/sync_papers.py  → prototypes/papers.json (原型共享)
```

### 新论文入库流程

1. 确定 `lane` — 这篇论文缓解什么瓶颈？
2. 确定 `layer` — 在技术栈哪一层动手？
3. 标注 `paradigms[]` — 属于什么架构家族？
4. 填写 `builds_on[]` — 基于哪些前作？
5. 填写 `competes_with[]` — 同期有谁在解决一样的问题？

### 边界 case 决策

| Case | 决策 | 理由 |
|------|------|------|
| DeepSeek-V3 (MLA + MoE + FP8) | lane=compute_scaling, layer=arch | 主要贡献是规模化效率；MLA 是手段 |
| Jamba (SSM + Attention + MoE) | lane=sequence_scaling, layer=arch | 主要创新是 hybrid 架构解决序列问题 |
| FlashAttention | lane=memory_wall, layer=sys | 不改模型能力，解决 serve 的 IO 问题 |
| RoPE | lane=sequence_scaling, layer=memory | 位置编码改变模型处理长度的能力 |
| Speculative Decoding | lane=memory_wall, layer=infer | 减少推理延迟/bandwidth需求 |
| o1 (CoT reasoning) | lane=compute_scaling, layer=infer | test-time compute scaling |

---

## Lane 内典型论文分布

### sequence_scaling

| Layer | 论文 |
|-------|------|
| arch | S4, Mamba, Mamba-2, RWKV, RetNet, Griffin, Jamba, Hyena, xLSTM |
| memory | RoPE, ALiBi, YaRN, LongRoPE, Infini-Attention |
| sys | Ring Attention, LongNet |

### memory_wall

| Layer | 论文 |
|-------|------|
| memory | MQA, GQA, MLA, TransMLA |
| sys | FlashAttention V1-V4, PagedAttention, SGLang |
| infer | Speculative Decoding, Medusa, EAGLE, Lookahead |

### compute_scaling

| Layer | 论文 |
|-------|------|
| arch | GShard, Switch Transformer, MoE routing, DeepSeek-MoE, Mixtral |
| train | RLHF, DeepSeek-R1, verifier/rubrics |
| infer | o1, CoT, test-time budget allocation |
| sys | MegaBlocks |
