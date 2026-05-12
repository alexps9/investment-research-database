# Topic View 连线规范文档

> 从 `topic-view-exploration.html` 提取 + 图片补充的完整连线关系

---

## 一、数据模型

### 1.1 节点属性

```javascript
{
  id: "mamba",           // 唯一标识
  title: "Mamba",        // 显示名称
  year: 2023,            // 年份
  quarter: 4,            // 季度 (1-4)
  paradigm: "linear_ssm", // 范式ID
  lane: "sequence_scaling", // 所属Lane
  layer: "arch",         // 干预层: arch/sys/infer/train/memory
  size: "lg",            // 节点大小: sm/md/lg
  impact: "high"         // 影响力
}
```

### 1.2 连线类型

| 类型 | 语义 | 视觉样式 |
|------|------|----------|
| `builds_on` | 继承演进（同Paradigm内） | 实线 + 箭头 |
| `forks_from` | 从主干分叉（新Paradigm） | 贝塞尔弧线 |
| `enables` | 跨Lane因果/使能 | 虚线 + 箭头 + 标签 |
| `competes_with` | 竞争替代关系 | 虚线（双向） |
| `merges_into` | 融合 | 双线汇入 + 菱形标记 |
| `influences` | 哲学/思想影响 | 淡虚线 |

---

## 二、Lane 1: Context Scaling (sequence_scaling)

### 2.1 Paradigm: Linear / SSM (主干挑战者)

**主干**: RoPE → ALiBi → YaRN → LongRoPE (位置编码，灰色)

**分叉路线** (从 RoPE 2023Q1 分出):

```
RoPE (2023Q1)
  │
  ├─forks_from─┬─ S4 (2023Q1) ────┬─ Mamba (2023Q4) ─┬─ Griffin (2024Q1)
  │            │                   │                  ├─ Jamba (2024Q1)
  │            │                   │                  ├─ Mamba-2 (2024Q2)
  │            │                   │                  └─ xLSTM (2024Q2)
  │            │                   │
  │            └─ RWKV-4 (2023Q2) ──── RWKV-7 (2024Q4)
  │
  └─forks_from── Hyena (2023Q1) ──── RetNet (2023Q3)
                                         │
                                         └─ GLA (2023Q4) ── DeltaNet (2024Q2)
```

**Builds_on 关系**:
- `RetNet → Mamba` (Mamba builds_on RetNet)
- `RWKV-4 → RWKV-7`
- `S4 → Mamba`
- `Mamba → Griffin, Jamba, Mamba-2, xLSTM`
- `GLA → DeltaNet`

### 2.2 Paradigm: Sparse / Chunked (从主干向下分叉)

```
RoPE (2023Q3)
  │
  └─forks_from── StreamingLLM (2023Q3)
         │
         └─ builds_on ── Ring Attention (2023Q4)
         │
         └─ LongNet (2023Q3)
         │
         └─ Infini-Attention (2024Q2) [builds_on StreamingLLM]
```

### 2.3 Paradigm: Memory-Augmented

```
YaRN (2023Q3)
  │
  └─ builds_on ── LongRoPE (2024Q1)

RETRO (2024Q1)
HMT (2024Q1)
MemGPT (2024Q2)
RMT (2024Q4)
```

**跨Lane因果**:
- `FlashAttn-2 → YaRN` (enables 128K)

---

## 三、Lane 2: Memory Wall

### 3.1 Paradigm: KV Compression (从主干向上分叉)

**主干**: FlashAttn → FA-2 → FA-3 → FA-4

```
FlashAttn (2023Q3)
  │
  ├─ builds_on ── FA-2 (2023Q3)
  │                │
  │                └─ builds_on ── FA-3 (2024Q3)
  │                                  │
  │                                  └─ builds_on ── FA-4 (2025Q3)
  │
  └─forks_from── GQA (2023Q2) ──── MLA-DSV2 (2024Q2) ──── MLA-DSV3 (2024Q4) ──── TransMLA (2025Q2)
```

### 3.2 Paradigm: Paging / Offloading (从主干向下分叉)

```
FlashAttn (2023Q3)
  │
  └─forks_from── PagedAttention (2023Q3) ──── SGLang (2023Q4)
                                      │
                                      └─ vLLM-v2 (2024Q3)
```

**跨Lane因果**:
- `PagedAttention → vLLM-v2` (enables)
- `FlashAttn-2 → MLA` (IO解决→KV压缩)
- `MLA-DSV3 → R1` (低成本推理→R1) [跨Lane到Compute]

### 3.3 Paradigm: Quantization

```
AWQ (2023Q2)
  │
  └─ builds_on ── GPTQ (2023Q3)
                   │
                   └─ builds_on ── SmoothQuant (2023Q4)
                                    │
                                    └─ builds_on ── FP8 (2024Q2)
```

**跨Lane因果**:
- `FP8/量化技术 → Real-time Agent Infra` (Era 3)

---

## 四、Lane 3: Compute Scaling

### 4.1 Paradigm: MoE / Routing (主干)

```
GShard (2023Q1)
  │
  └─ builds_on ── Switch Transformer (2023Q1)
                   │
                   ├─ Mixtral-8x7B (2024Q1)
                   │        │
                   │        └─ DBRX (2024Q1)
                   │
                   ├─ DeepSeek-MoE (2024Q1)
                   │        │
                   │        └─ DS-V3-MoE (2024Q4)
                   │                 │
                   │                 └─ Qwen3-MoE (2025Q2)
                   │
                   └─forks_from── Speculative Decoding (2023Q1)
```

### 4.2 Paradigm: Speculative / Draft (从MoE分叉)

```
Switch Transformer (2023Q1)
  │
  └─forks_from── Speculative Decoding (2023Q1) ──── Medusa (2024Q1)
                                              │
                                              ├─ EAGLE (2024Q1)
                                              │     │
                                              │     └─ EAGLE-2 (2024Q2)
                                              │
                                              └─ Lookahead (2024Q2)
```

### 4.3 Paradigm: Reasoning Scaling (从MoE向下分叉)

```
Mixtral (2024Q1)
  │
  └─forks_from── Chain-of-Thought (2023Q1) ──── Tree-of-Thought (2023Q3) ──── o1-preview (2024Q3)
                                                                               │
                                                                               ├─ o1 (2024Q4)
                                                                               │
                                                                               └─ DeepSeek-R1 (2025Q1) ──── s1 (2025Q2)
                                                                                          │
                                                                                          └─ QwQ (2025Q1)
```

**Builds_on**:
- `CoT → ToT → o1-preview`
- `o1-preview → o1, R1, QwQ`
- `R1 → s1`

**新增节点** (图片补充):
- `Verifier Scaling for RL` (2025Q2) [从R1分叉]
  - 逻辑："高质量评价体系是提升RL算力转化率的唯一变量"

---

## 五、跨Lane因果连线 (Critical)

### 5.1 已确认的跨Lane连线

| 起点 | 终点 | 类型 | 标签/语义 |
|------|------|------|-----------|
| FlashAttn-2 | YaRN | enables | "enables 128K" |
| FlashAttn-2 | MLA | enables | "IO解决→KV压缩" |
| MLA-DSV3 | R1 | enables | "低成本推理→R1" |
| MLA-DSV3 | DS-V3-MoE | merge | "MLA+MoE融合" |
| PagedAttn | vLLM-v2 | enables | "" |
| Mamba | Griffin | fork | "hybrid" |
| Mamba | Jamba | merge | "SSM+Attention融合" |
| Mamba | RWKV-7 | fork | "RNN复兴" |
| RetNet | StreamingLLM | fork | "sink token" |
| GQA | PagedAttn | fork | "serving优化" |
| Switch | SpecDec | fork | "条件计算→投机" |
| ToT | o1 | fork | "search scaling" |

### 5.2 图片补充的缺失连线 (Era 3闭环)

| 起点 | 终点 | 类型 | 标签/语义 | Era |
|------|------|------|-----------|-----|
| LongRoPE / Mamba-2 | Persistent Memory | enables | "长上下文→持久化记忆" | 3 |
| Mamba-2 | Persistent Memory | enables | "线性复杂度→记忆架构" | 3 |
| Persistent Memory | Agent RL | enables | "记忆→ACI行动" | 3 |
| R1 | Verifier Scaling | fork | "推理→评价体系" | 3 |
| Verifier Scaling | Agent RL | enables | "评价→行动优化" | 3 |
| TransMLA | Real-time Agent Infra | enables | "极低延迟→实时行动" | 3 |
| FlashAttn-4 | Real-time Agent Infra | enables | "效率→实时闭环" | 3 |

---

## 六、时代划分 (Era)

### Era 1: Knowledge Acquisition (2023)
**背景色**: 淡灰 #FAFAFA
**主导Lane**: sequence_scaling
**Pressure Wave**: "1M context race"
- 触发：GPT-4 Turbo 128K 发布
- 响应：RoPE, YaRN, LongRoPE, Mamba

### Era 2: Logical Reasoning (2024)
**背景色**: 纯白 #FFFFFF
**主导Lane**: memory_wall
**Pressure Wave**: "Inference cost crisis"
- 触发：LLM API价格战 + o1发布
- 响应：MLA, FlashAttn-2/3, o1-preview

### Era 3: Unified Action / AGI (2025+)
**背景色**: 渐隐到透明
**主导Lane**: compute_scaling
**Pressure Wave**: "Test-time scaling"
- 触发：DeepSeek-R1 低成本推理
- 响应：Verifier Scaling, Agent RL, Persistent Memory

**Era 3 Extension (2027+)**:
**标题**: "The Test-Time Computing Shift"
**核心理念**: 
- Low-Rank MLA compression frees HBM bandwidth
- Allow longer CoT reasoning Tokens

---

## 七、节点密度统计

| Lane | 已有关键节点 | 需新增节点 |
|------|-------------|-----------|
| sequence_scaling | 18 | Persistent Memory (1-C) |
| memory_wall | 16 | TransMLA标注, Real-time Agent Infra依赖 |
| compute_scaling | 14 | Verifier Scaling, Agent RL, s1 |
| **总计** | **48** | **35+** |

---

## 八、渲染优先级

### P0 (必须实现)
1. ✅ 三Lane主干线
2. ✅ Paradigm分叉弧线
3. ✅ builds_on行内箭头
4. ✅ 跨Lane enables虚线

### P1 (重要)
5. 时代背景色带 (Era 1/2/3)
6. Pressure Wave标注
7. NOW线

### P2 (增强)
8. 线宽编码dominance (河流风格)
9. Momentum高亮 (爆发感)
10. 融合节点菱形标记

---

## 九、数据格式示例

```javascript
const PAPERS = [
  // ... 已有节点
  
  // Era 3 新增节点
  {id:'persistent_mem', title:'Persistent Memory', year:2025, quarter:2, 
   paradigm:'memory_aug', lane:'sequence_scaling', layer:'memory', size:'lg'},
   
  {id:'agent_rl', title:'Agent RL', year:2025, quarter:3, 
   paradigm:'reasoning', lane:'compute_scaling', layer:'train', size:'lg'},
   
  {id:'verifier_scaling', title:'Verifier Scaling', year:2025, quarter:2, 
   paradigm:'reasoning', lane:'compute_scaling', layer:'train', size:'md'},
];

const CROSS_ARCS = [
  // ... 已有连线
  
  // Era 3 闭环
  {from:'mamba2', to:'persistent_mem', type:'enables', label:'线性→记忆'},
  {from:'longrope', to:'persistent_mem', type:'enables', label:'长上下文→记忆'},
  {from:'persistent_mem', to:'agent_rl', type:'enables', label:'记忆→ACI'},
  {from:'r1', to:'verifier_scaling', type:'fork', label:'推理→评价'},
  {from:'verifier_scaling', to:'agent_rl', type:'enables', label:'评价→行动'},
  {from:'transmla', to:'agent_rl', type:'enables', label:'实时→行动'},
];
```
