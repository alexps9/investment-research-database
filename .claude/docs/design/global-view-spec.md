# Global View 设计规范

> 全局视图的完整设计规范。
>
> 日期：2026-05-09（v3，核心设计哲学重构）

---

## 文档结构说明

本 Spec 分为两类内容：

- **WHAT（行为约束）**：标记为 "Acceptance Criteria" / "Success Metrics" / "Constraints"。实现必须满足，但实现方式不限。
- **参考实现（HOW 建议）**：标记为 "尺寸" / "规格" 的像素级描述。可偏离。

判断标准：换一个渲染技术（SVG → Canvas → WebGL），Spec 的 WHAT 部分仍然有效。

---

## 与其他原型的关系

| 文件 | 定位 |
|------|------|
| `prototypes/llm_systems_evolution_map.html` | 旧版探索原型，保留作技术演进参考 |
| `prototypes/global-view-v2.html` | 当前活跃原型，本 spec 指导 |

---

## 一句话定义

> 全局视图是 **Frontier Pressure Migration Map**。
> 用户打开它的第一秒应该感知到：**"AI 社区的注意力中心在迁移"** — 不是"这里有哪些论文"。

---

## Dominant Cognition（设计哲学核心）

### 视觉语法单一性原则

**Global View 只允许一种 dominant visual grammar：Frontier Pressure Migration。**

所有其他信息层必须视觉降权。如果用户的第一注意力被 lineage edges / paradigm taxonomy / paper details 吸引，则设计失败。

### 认知优先级（严格递降）

| 优先级 | 信息 | 用户应感知为 | 视觉强度 |
|--------|------|------------|---------|
| **P0** | Pressure Migration | "哪个问题正在爆发" | 最强（场 + 脉冲） |
| P1 | Era/时代划分 | "现在处于什么时代" | 中（时间轴标注） |
| P2 | Landmark Papers | "锚点在哪" | 中弱（大节点） |
| P3 | Local Lineage | "局部路线方向" | 弱（同行内短连线） |
| ❌ | 跨行 Lineage / Competition / Philosophy | 不属于 Global View | 默认不显示 |

### 与其他视图的边界

| 信息 | 归属视图 | Global View 中的处理 |
|------|---------|---------------------|
| Frontier pressure migration | **Global** | 主视觉 |
| Lineage fork / competition | Topic | 不显示或 hover reveal |
| Version mutation | Iteration | 不显示 |
| Outcome / adoption | Arena | 不显示 |

**如果 Global View 开始让用户"追 edges"，它就偷偷变成了 Topic View。这是最危险的 drift。**

---

## 用户回答的问题

- "AI frontier 注意力正在往哪个方向迁移？"
- "什么事件触发了这次迁移？"
- "哪个 bottleneck 现在最不可回避？"
- "这些看似无关的工作为什么同时出现？"

**不在本视图回答的问题：**
- "某个路线内部怎么分叉" → Topic View
- "某个架构为什么不断迭代" → Iteration View
- "谁更有竞争力" → Arena View

---

## 全局 Success Metrics

| 指标 | 标准 |
|------|------|
| 首屏感知 | 用户 3 秒内能说出"当前最活跃的压力方向是什么" |
| 迁移感 | 用户能指出"pressure 从 X 迁移到了 Y" |
| 因果感知 | 用户能说出"某事件触发了这波爆发" |
| **不是 taxonomy** | 用户的第一反应不是"这是个分类表" |
| **不是 citation graph** | 用户不会开始"追边" |
| 交互响应 | 点击节点 → Side Panel < 300ms |
| 滚动流畅 | 60fps |

## 全局 Non-Goals（本期不做）

- 实时数据更新（数据为人工标注快照）
- 论文全文搜索 / 用户自定义布局 / 多人协作
- philosophical_lineage 跨 section 曲线
- 时间滑块动画播放
- Lineage fork 可视化（属于 Topic View）
- 能力对比 / 路线命运（属于 Arena View）

---

## 页面结构（从外到内）

```
┌─────────────────────────────────────────────────────────────────┐
│ Header (固定)                                                    │
├────────┬────────────────────────────────────────────────────────┤
│        │ Timeline Header (年 + 季度刻度)                         │
│        │ Era Bar ("更多参数" → "更长推理" → "长期闭环")            │
│  Left  ├────────────────────────────────────────────┬───────────┤
│  Rail  │                                            │   Right   │
│        │ Main Canvas                                │   Side    │
│(Bottle-│ (Lanes → Currents → Landmark Nodes)       │   Panel   │
│ neck   │                                            │  (Detail) │
│ labels)│                                            │           │
├────────┴────────────────────────────────────────────┴───────────┤
│ Bottom Legend Bar                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Era Bar（时代标注行） — 新增

位于 Timeline Header 下方，高度约 28-32px。让用户一眼看出**每个时代在解决什么核心命题**。

| Era | 时间范围 | 标注 | 核心命题 |
|-----|---------|------|---------|
| Knowledge Era | 2023 Q1 – 2023 Q4 | "更多参数" | Scaling parameters |
| Reasoning Era | 2024 Q1 – 2025 Q2 | "更长推理" | Scaling inference |
| Agency Frontier | 2025 Q3 → | "长期闭环" | Scaling agency |

Acceptance Criteria:
- [ ] 用户无需滚动即可看到当前处于哪个时代
- [ ] 每个 era 的核心命题用一句话标注，不超过 4 个汉字/2 个英文词
- [ ] Era 之间的转折点清晰可辨

---

## Header（顶部导航栏）

### 尺寸

```
高度: 64px
内边距: 0 32px
背景: #FFFFFF
底部边框: 1px solid #E4E4E7 (zinc-200)
z-index: 30 (sticky)
```

### 内容（从左到右）

| 元素 | 规格 |
|------|------|
| 标题 | "LLM SYSTEMS EVOLUTION MAP"，24px，font-weight: 900，#18181B |
| 副标题 | "后 Transformer 时代的技术演化地图（2023 → 2026）"，12px，#71717A |
| Time Range | "2023 Q1 → 2026 Q1" + 左右箭头，居中 |
| 视图切换 | 3 个按钮：全局视图(active) / 单一主题 / 对比视图 |
| 图例提示 | "形状 = Layer（干预层）| 颜色 = Paradigm（世界观）"，10px，#A1A1AA |

### 视图切换按钮

```
Active:  bg: #EA580C, text: #FFFFFF, font-weight: 600
Inactive: bg: transparent, border: 1px solid #D4D4D8, text: #52525B
圆角: 12px
Padding: 8px 16px
```

---

## Left Rail（左侧 Bottleneck 面板）

### 尺寸

```
宽度: 220px
背景: #FAFAFA
右边框: 1px solid #E4E4E7
```

### 每个 Bottleneck Section

```
左边框: 4px solid [section-color]
Padding: 24px 20px
最小高度: 与 Main Canvas 中对应 section 高度同步
```

### Bottleneck 标签内容

```
┌─────────────────────────┐
│ ① Context Scaling       │  ← 编号 + 标题 (16px bold)
│                         │
│ 处理更长文本（4K → 1M+） │  ← 副标题 (11px #71717A)
│                         │
│ ▾ (折叠按钮)             │
└─────────────────────────┘
```

### Section 颜色

| Bottleneck | 左边框色 | 编号圆底色 |
|------------|---------|-----------|
| Context Scaling | `#2563EB` (blue-600) | `#DBEAFE` |
| Memory Wall | `#059669` (emerald-600) | `#D1FAE5` |
| Compute Allocation | `#EA580C` (orange-600) | `#FFEDD5` |

---

## Timeline Header（时间轴刻度）

### 尺寸

```
高度: 64px
位于 Main Canvas 顶部
背景: #FFFFFF
底部边框: 1px solid #E4E4E7
sticky (z-index: 20)
```

### 刻度结构

```
第一行: 年份 (2023 / 2024 / 2025 / 2026)，16px bold，居中
第二行: Q1 Q2 Q3 Q4 (每年4格)，10px，#A1A1AA，均分
竖向分隔: 年份间 1px solid #E4E4E7，季度间 1px solid #F4F4F5
```

### NOW 线

```
位置: 当前季度对应 X 坐标
样式: 2px dashed #FF4400
标注: "NOW" 文字，10px bold #FF4400，在线顶部
z-index: 10
```

---

## Main Canvas（主画布）

### 整体结构

Main Canvas 由 3 个 Bottleneck Section 纵向排列组成，每个 section 内含多个 Paradigm Row。

```
背景: #FFFFFF
溢出: 水平滚动 (如果时间轴超过视口)
```

### Bottleneck Section

```
section 间距: 16px（用 1px solid #E4E4E7 分割线 + 上下 8px 留白）
section 内部: paradigm rows 紧凑排列
```

### Paradigm Row（核心单位）

每一行就是一条"地铁线路"。

```
高度: 88px
左侧标签区: 180px (paradigm 名称 + 中文副标题)
右侧内容区: 剩余宽度（节点 + 连线）
行内分隔: 1px dashed #F4F4F5 (极淡)
```

#### Paradigm 标签

```
位置: row 左侧，垂直居中
结构:
  ● Linear / SSM (线性/状态空间)
  ^色点  ^英文名         ^中文(10px #A1A1AA)

色点: 8px 圆，fill = paradigm 色
英文名: 13px semibold #3F3F46
中文副标题: 10px #A1A1AA，跟在英文后
```

---

## 节点（Paper Node）

### 形状规格

| Layer | 形状 | 尺寸(md) | 尺寸(lg) | 尺寸(sm) |
|-------|------|---------|---------|---------|
| arch | circle | r=10px | r=14px | r=7px |
| sys | square | 18×18px | 24×24px | 13×13px |
| infer | diamond | 18×18px rotated 45° | 24×24px | 13×13px |
| train | triangle | base=18px h=16px | base=24px h=20px | base=13px h=11px |
| memory | hexagon | 18px inscribed | 24px | 13px |

### 颜色规格

```
Fill: paradigm色 @ 50% opacity
Stroke: paradigm色 @ 100%, 1.5px
Hover: paradigm色 @ 80% fill + scale(1.2) + cursor pointer
Active (clicked): paradigm色 @ 100% fill + 2px stroke
```

### 大小映射

```
size = 'sm' | 'md' | 'lg'

判断标准:
  lg: cited_by_count > 2000 或 impact = "high"
  md: cited_by_count 500-2000
  sm: cited_by_count < 500
```

### 节点标签

```
位置: 节点下方 4px
结构:
  论文名 (11px #3F3F46)
  时间   (9px #A1A1AA)

只有 lg 和 md 节点默认显示标签
sm 节点仅 hover 时显示
```

### 节点定位

```
X 坐标: 根据 paper.year + paper.quarter 映射到时间轴百分比
Y 坐标: 该 paradigm row 的中心线

X 计算公式:
  x% = ((year - 2023) * 4 + (quarter - 1)) / 16 * 100%
  (假设时间范围 2023Q1 到 2026Q4 = 16 个季度)
```

---

## 连接线（Edges）— 极度克制

### 设计原则

**Edge 是 Global View 最危险的元素。** 一旦默认显示大量边，用户会切换为"追边"模式，Pressure migration 的认知会被 topology grammar 杀死。

### 默认可见：仅同行局部 lineage

只显示 **same-paradigm-row 内的相邻 builds_on**（如 Mamba → Mamba-2）。

视觉：极淡（paradigm 色 @ 25%），细线（1px），短箭头。

**禁止默认显示：**
- 跨 paradigm / 跨 Lane 的长距离 lineage
- competes_with 边
- philosophical_lineage 边

### Hover reveal（按需显示）

Hover 某节点时，才显示该节点的：
- builds_on 上下游完整链
- competes_with（虚线，中性灰）

### Acceptance Criteria（Edges）

- [ ] 默认状态下，用户的注意力不会被边吸引（edges 视觉强度弱于 pressure field）
- [ ] 用户不会产生"追边"行为（edges 不形成视觉网络）
- [ ] Hover 时能看到局部关系链

---

## Frontier Pressure Layer（核心信息层）

### Problem Statement

当前地铁图是 object map —— "这里有哪些论文"。
但全局视图真正要展示的是 field dynamics —— **"frontier pressure 在往哪里流动"**。

关键洞察：真正的 frontier pressure 不是"持续热度"，而是**冲击 / 断裂 / 危机**。用户需要感知的是"某个问题突然变得不可回避"——这是 discontinuity，不是 continuous density。

用户需要感知：
- 某个 bottleneck 突然**爆发**（pulse），而不是"一直在那里"
- Frontier pressure 从一个问题空间**迁移**到另一个（surge propagation）
- "Inference suddenly became unavoidable" 的冲击感（shock origin）

### Success Metrics

| 指标 | 标准 |
|------|------|
| 冲击感 | 用户 3 秒内能指出"哪个 Lane 正在爆发"（不是"哪个最热"） |
| 迁移感 | 用户能描述出 pressure 的时间迁移方向（先爆发→后爆发） |
| 节点可读性 | Pressure surge 不得使任何节点标签变得不可辨认（对比度 ≥ 4.5:1） |
| 层级清晰 | 节点始终在视觉层级上高于 pressure field 背景 |
| 非 heatmap | 用户不会将 Pressure Field 描述为"颜色深浅图"或"热力图" |

### Acceptance Criteria

- [ ] 基线状态（weight < 0.3）时，背景几乎不可感知（opacity 0.03-0.08）
- [ ] 冲击状态（weight ≥ 0.7）时，有明显视觉断裂感（不是渐变加深，是"亮起来"）
- [ ] 三个 Lane 的压力场颜色分别使用各自的 Lane 主色
- [ ] Pressure surge 有清晰的"起点"（shock origin）和"扩散方向"
- [ ] 不同 Lane 的 surge 时间错位可被感知（不是同时亮）
- [ ] Pressure field 覆盖整个 Bottleneck Section 高度（所有 paradigm rows）

### Non-Goals

- 不做 pressure field 的 hover 交互
- 不做 pressure 与 paradigm 级别的关联（只挂 Lane）
- 不做动画（压力变化不随时间自动播放）
- 不做 pressure field 的 toggle 开关
- **不做 continuous heatmap**（这是 Pressure 的核心反模式）

### Constraints

- 渲染技术不限（SVG filter / CSS gradient / Canvas 均可），但必须保证 60fps 滚动流畅
- Pressure 数据为人工标注（MVP 阶段），数据格式见下方 interface
- 视觉上必须是 pulse/surge 语言，不是 smooth gradient 语言

---

### 核心 Ontology 原则

**热度场挂在 Lane（问题压力）上，不是 Paradigm（解决方法）上。**

因为：
- Lane 是稳定 partition（问题永远存在）
- Paradigm 会跨 Lane 漂移（Sparse 可以是长上下文也可以是 MoE）
- 用户先感知"什么问题爆发了"，再看"大家用什么办法解决"

正确信息流：
```
Era shift → 某个 bottleneck pressure 增强 → 整个 Lane 的场变亮
  → 内部 paradigm 开始竞争 → landmark papers 出现
```

### 设计原则

1. **Pressure ≠ 论文数量** — raw paper count 有 arxiv flood 污染。Signal 是人工标注的 frontier significance
2. **不是 heatmap** — 是 pulse/surge（冲击事件，不是连续背景色）
3. **场是氛围层，节点是信息层** — 场提供"危机感"，节点提供精确信息。二者不可互相遮挡
4. **场的主体是 bottleneck pressure** — 不是 paradigm popularity
5. **Surge 有生命周期** — onset → peak → decay。不是"一直亮着"。衰减本身就是信息（"这个危机被消化了"）
6. **迁移是核心叙事** — 三个 Lane 的 surge 时间偏移量讲述因果故事

### 视觉层级（从底到顶）

| 层级 | 内容 | 说明 |
|------|------|------|
| z-0 | Era 背景 | 文明阶段色块 |
| z-1 | Frontier Pressure Field | Lane 级 surge 脉冲（核心层） |
| z-2 | Pressure Wave + Shock Origin | 事件解释标注 |
| z-3 | 连接线 | builds_on / competes |
| z-4 | 节点 | Paper nodes |
| z-5 | 标签 / Tooltip | 文字信息 |

### Pressure Field 行为规格

**核心模型：Pulse / Surge（不是 Heatmap）**

Pressure 不是"持续背景色深浅"。它是**冲击事件**：
- 基线时期：几乎不可见（"问题存在但不紧迫"）
- 冲击时期：突然亮起（"问题变得不可回避"）
- 消退时期：快速衰减（"危机被吸收或转移"）

```
┌─────────────────────────────────────────────────────────┐
│ [1] Context Scaling                                      │
│   · · · · · ·╔══SURGE══╗· · · · · · · · · · · · · · ·  │
│              ║ ▓▓▓▓▓▓▓ ║                                │
│   · · · · · ·╚═════════╝· · · · · · · · · · · · · · ·  │
│                                                          │
│ [2] Memory Wall                                          │
│   · · · · · · · · · · · · · ·╔══SURGE══════════╗· · ·  │
│                               ║ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ║       │
│   · · · · · · · · · · · · · ·╚═════════════════╝· · ·  │
│                                                          │
│ [3] Compute Allocation                                   │
│   · · · · · · · · · · · · · · · · ·╔══SURGE════════╗   │
│                              [o1]→  ║ ▓▓▓▓▓▓▓▓▓▓▓▓ ║   │
│   · · · · · · · · · · · · · · · · ·╚═══════════════╝   │
└─────────────────────────────────────────────────────────┘
  2023                    2024                    2025
  
· = dormant（weight < 0.3，opacity 0.03-0.08，几乎不可见）
▓ = surge（weight ≥ 0.7，opacity jump to 0.15-0.25）
[o1] = shock origin marker（标注触发事件）
```

**关键视觉差异（vs Heatmap）：**

| Heatmap 模式（❌ 禁止） | Pulse/Surge 模式（✅ 正确） |
|------------------------|--------------------------|
| 连续渐变，从浅到深 | 基线近乎不可见，surge 突然出现 |
| "哪里颜色深 = 哪里热" | "哪里亮了 = 哪里正在爆发" |
| 视觉感受：统计图 | 视觉感受：雷达上的信号脉冲 |
| 平滑过渡 | 清晰的 onset 和 decay |

**视觉约束：**

| 属性 | 规格 |
|------|------|
| 颜色 | 各 Lane 主色（Context=#2563EB, Memory=#059669, Compute=#EA580C） |
| 基线 opacity | 0.03-0.08（几乎与白色背景融合） |
| Surge opacity | 0.15-0.25（明确可感知但不遮挡节点） |
| Surge onset | 1-2 个季度内从基线跳到 surge（不是 5 个季度慢慢加深） |
| Surge decay | 2-3 个季度从 surge 衰减到基线 |
| 覆盖范围 | section 高度 100%（覆盖该 Lane 内所有 paradigm rows） |
| 与节点关系 | 节点 z-index 永远高于 field，field 不可遮挡节点 |

**Shock Origin Marker：**

每个 Surge 有一个"起因标注"——解释为什么这个 Lane 突然爆发：

| Surge | Shock Origin | 标注 |
|-------|-------------|------|
| Context Scaling surge (2023Q3-2024Q1) | Mamba + 长上下文竞赛 | `[Mamba]` |
| Memory Wall surge (2024Q2-2025Q1) | MLA + 推理成本危机 | `[MLA]` |
| Compute surge (2024Q3-2025Q2) | o1 发布 → reasoning scaling | `[o1]` |

Shock Origin Marker 视觉：9px 灰色文字 + 细箭头指向 surge 起始位置。不抢夺注意力，hover 时可放大。

**迁移叙事（Surge Propagation）：**

三个 Surge 在时间轴上的错位本身就是核心信息：
```
Context → Memory → Compute（左→中→右）
```
这个时间顺序讲述了一个因果故事：长上下文竞赛 → 暴露推理成本 → 催生 reasoning scaling。Surge 的时间偏移量就是"因果传播延迟"。

### Pressure Signal 数据格式

MVP 阶段人工标注每个 Lane 在每个时段的 pressure weight：

```typescript
interface PressureSignal {
  lane: "sequence_scaling" | "memory_wall" | "compute_scaling";
  quarter: string;       // "2024Q2"
  weight: number;        // 0.0 ~ 1.0
  trigger?: string;      // "o1 发布 → inference 成本危机"
}

interface PressureSurge {
  lane: "sequence_scaling" | "memory_wall" | "compute_scaling";
  onset: string;         // "2023Q3" — surge 开始
  peak: string;          // "2023Q4" — surge 峰值
  decay: string;         // "2024Q2" — surge 衰减到基线
  shockOrigin: string;   // "Mamba + 长上下文竞赛"
  peakWeight: number;    // 0.7 ~ 1.0
}
```

Demo 数据（Surge 模型 — 关注 onset/peak/decay，不是均匀分布）：

| Lane | 2023Q1 | Q2 | Q3 | Q4 | 2024Q1 | Q2 | Q3 | Q4 | 2025Q1 | Q2 |
|------|--------|----|----|----|----|----|----|----|----|-----|
| sequence_scaling | 0.1 | 0.1 | **0.7** | **0.9** | 0.6 | 0.3 | 0.1 | 0.1 | 0.05 | 0.05 |
| memory_wall | 0.05 | 0.05 | 0.1 | 0.1 | 0.2 | **0.8** | **0.9** | **0.85** | 0.5 | 0.3 |
| compute_scaling | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 | 0.2 | **0.8** | **1.0** | **0.9** | 0.7 |

注意与 heatmap 模式的数据差异：
- 基线值非常低（0.05-0.1），不是 0.3-0.5
- Surge onset 快速（1-2 季度从 0.1 跳到 0.7+）
- Surge 有明确的 peak 和 decay

Surges:
- sequence_scaling: onset 2023Q3, peak 2023Q4, decay 2024Q2. Shock: "Mamba + 长上下文竞赛"
- memory_wall: onset 2024Q2, peak 2024Q3, decay 2025Q2. Shock: "MLA + 推理成本危机"  
- compute_scaling: onset 2024Q3, peak 2024Q4, decay ongoing. Shock: "o1 → reasoning scaling"

### 用户感知验证

合格的实现应让用户打开全局视图后描述出 **冲击和迁移**（不是"颜色深浅"）：

1. "2023 下半年 Context Scaling 突然爆发了" — 感知到 onset（不是"一直都热"）
2. "然后 2024 年中 Memory Wall 接力爆发" — 感知到 surge propagation
3. "2024 年底 Compute 问题变成最大的" — 感知到最新的 surge
4. "Context Scaling 那波已经过去了" — 感知到 decay（surge 有结束）

**验证红线**：如果用户说"这是一个热力图"或"颜色从浅到深"，则实现失败。正确的反应是"这里有几波脉冲在不同时间爆发"。

### 与节点的关系

- Pressure Field 是背景（场），挂在 Lane（Bottleneck Section）上
- 节点是场中的锚点（landmark），挂在 Paradigm Row 上
- Surge 区域内节点自然密集且大（因为真实数据：危机催生论文）
- 但即使某段时间没有 landmark 论文，Lane 的 surge 依然可以亮起（表示"问题在爆发，解法还没来"）
- Surge 消退后，该区域节点仍可存在但场已暗淡（表示"问题被消化，进入常规演化"）
- Paradigm 颜色和形状在 surge 区域内自然聚类 → 展示"面对同一危机，不同哲学如何同时响应"

---

## Era 背景层

### 位置

最底层（z-index: 0），在 Attention Field 之下。

### 三段划分

| Era | X 范围 | 背景色 | 标注 |
|-----|--------|--------|------|
| Knowledge Era | 2023 Q1 – 2023 Q4 | `#FAFAFA` (极淡灰) | — |
| Reasoning Era | 2024 Q1 – 2025 Q2 | `#FFFFFF` (白，正常) | — |
| Agency Frontier | 2025 Q3 → 右侧边缘 | 从白到透明渐隐 | "Frontier" |

### Era 分割线

```
Knowledge → Reasoning:
  位置: 2023 Q4 / 2024 Q1 之间
  样式: 1px dashed #E4E4E7
  标注: 无（视觉暗示即可）

Reasoning → Agency:
  位置: 2025 Q2 / Q3 之间
  样式: 1px dashed #E4E4E7, opacity 0.5
  标注: "Frontier" 9px #D4D4D8
```

### Agency Frontier 特殊处理

```
该区域内所有节点:
  opacity: 0.5
  stroke: dashed
  标签: 9px italic

该区域连线:
  opacity: 0.3
  全部 dashed

效果: 像地图边缘的未探索区域
```

---

## Lane 活跃度（Era Focus 效果）

### 默认状态

所有 Lane 均匀显示，无 focus。Reasoning Era 区域因节点最密而自然成为视觉重心。

### Era Focus Mode（点击 Era 标签时）

| Era 内 dominant lanes | 视觉 |
|----------------------|------|
| 节点 opacity | 100% |
| 节点大小 | 正常 |
| 连线 opacity | 80% |
| 标签 | 全部显示 |

| Era 内 suppressed lanes | 视觉 |
|------------------------|------|
| 节点 opacity | 40% |
| 节点大小 | 缩小 70% |
| 连线 opacity | 20% |
| 标签 | 仅 lg 显示 |

### Era Focus 数据

```
Knowledge Era (2023):
  dominant: compute_scaling (MoE行)
  suppressed: memory_wall

Reasoning Era (2024-2025):
  dominant: memory_wall + sequence_scaling + compute(reasoning)
  suppressed: 无（全面爆发）

Agency Frontier (2025+):
  dominant: memory_augmented + reasoning_scaling
  suppressed: kernel_optimization, quantization
```

---

## Pressure Wave（事件解释带）

### 与 Pressure Field 的关系

- **Pressure Field** = 视觉层（"看到 surge"）
- **Shock Origin Marker** = 最小标注（"[o1]"）
- **Pressure Wave** = 叙事层（"为什么 surge 发生"）

Wave 是 Shock Origin 的展开形式。如果 Shock Origin 是一个词，Wave 是一句话。

### Problem Statement

Pressure Field 展示"哪里在爆发"，但不解释"为什么爆发"。Pressure Wave 是叠加在 Surge 上的事件标注层，回答："什么外部事件触发了这波冲击？"

### Acceptance Criteria

- [ ] 每条 Wave 跨越对应时间段，视觉上位于节点之下、Era 背景之上
- [ ] Wave 不得遮挡节点或连线（中性淡色背景 + 低对比度文字）
- [ ] 标注文字在 Wave 左上角，简短表述触发事件
- [ ] Demo 中数量不超过 2 条（超过即视觉噪音）

### Non-Goals

- 不做 Wave 的 hover 展开详情
- 不做 Wave 与具体论文的关联高亮

### 视觉约束

| 属性 | 规格 |
|------|------|
| 填充色 | 中性淡灰（如 #F1F5F9），与 Lane 颜色无关 |
| 边框 | 无 |
| 圆角 | 小圆角（视觉柔和） |
| 标注文字 | 9px，低对比度灰色，不抢夺注意力 |

### 准入标准（什么事件值得成为 Wave）

1. **外生驱动**：由市场/硬件/政策事件触发（非某篇论文带动）
2. **多 paradigm 响应**：至少 2 个不同 paradigm 同时产出工作
3. **时间聚集**：3+ 篇论文在 6 个月内发表

### Demo 数据

| 时间范围 | 标注文字 | 触发事件 |
|---------|---------|---------|
| 2023 Q3 – 2024 Q2 | "1M context race" | GPT-4 Turbo 128K 发布 |
| 2024 Q3 – 2025 Q1 | "Inference cost crisis" | LLM API 价格战 + o1 发布 |

---

## Side Panel（右侧详情面板）

### 尺寸

```
宽度: 400px
背景: #FAFAFA
左边框: 1px solid #E4E4E7
内边距: 24px
z-index: 25
动画: 从右侧滑入 (translateX 100% → 0, 250ms ease)
```

### 默认状态

隐藏（节点未被点击时不显示）。

### 内容结构

```
┌──────────────────────────────┐
│ [Context Scaling > Linear/SSM]│  ← 面包屑 (chip 样式)
│                        [×]   │  ← 关闭按钮
│                              │
│ ● Mamba-2                    │  ← 标题 (28px black)
│ 2024 Q2 · 1,892 cites       │  ← 元数据
│ arXiv:2405.21060             │
│                              │
│ ─────────────────────────── │
│                              │
│ 解决的问题                    │  ← section header (10px uppercase)
│ 如何 O(n) 同时实现长序列建模   │  ← content (13px)
│                              │
│ 核心思想                      │
│ Selective SSM + 硬件感知优化   │
│                              │
│ ─────────────────────────── │
│                              │
│ Paradigm  ● Post-Attention   │  ← tag chip
│ Layer     ○ arch (架构)       │  ← tag chip
│ Bottleneck  Context Scaling  │  ← link chip
│                              │
│ ─────────────────────────── │
│                              │
│ Builds on                    │
│ [☆ Mamba (2023 Q4)] [☆ S4]  │  ← 可点击 chips
│                              │
│ Competes with                │
│ [RWKV v6] [RetNet] [LinTfm] │  ← 可点击 chips
│                              │
│ Philosophical Lineage        │
│ [RWKV] [Hyena] [xLSTM]      │  ← 灰色 chips
│                              │
│ ─────────────────────────── │
│                              │
│ 摘要                          │
│ Mamba-2 在 Mamba 基础上引入...│  ← 2-3 句 (12px #525252)
│                              │
│ ─────────────────────────── │
│                              │
│ [arXiv] [Paper] [Code] [Proj]│ ← 链接按钮
└──────────────────────────────┘
```

### 样式细节

```
面包屑: bg #DBEAFE, text #1D4ED8, 10px, border-radius 99px, padding 4px 12px
Section header: 10px uppercase tracking-wider #A1A1AA font-bold
关系 chip: border 1px #D4D4D8, bg #FFFFFF, text #3F3F46, border-radius 99px
链接按钮: border 1px #D4D4D8, bg #FFFFFF, hover bg #F4F4F5
```

---

## Bottom Legend Bar（底部图例栏）

### 尺寸

```
高度: 48px
背景: #FFFFFF
上边框: 1px solid #E4E4E7
内边距: 0 32px
display: flex, align-items: center, justify-content: space-between
```

### 内容（三组）

**组1 — 连接线图例：**
```
──→  builds_on（技术演进）
---  competes_with（竞争关系）
- -  philosophical_lineage（哲学血缘）
```

**组2 — Layer 图例（形状）：**
```
● arch  ■ sys  ◇ infer  △ train  ⬡ memory
```
每个形状 12px，fill #71717A，文字 10px #71717A。

**组3 — 节点大小：**
```
"节点大小 = log(cited_by_count)"
[6px圆] [10px圆] [14px圆]
```

---

## 交互行为规范

### Acceptance Criteria（交互）

- [ ] Hover 节点时，用户能立即识别"哪些节点和它属于同一 paradigm"（同 paradigm 保持高亮，其余暗化）
- [ ] Hover 节点时，出现 tooltip 显示论文名 + 时间 + paradigm
- [ ] Click 节点时，Side Panel 出现并展示该论文详情
- [ ] Click 节点时，该节点的 builds_on 上下游全链清晰可辨
- [ ] 再次 click 空白区域可恢复默认状态
- [ ] 所有交互过渡流畅（无跳变）

### Hover 节点（参考实现）

| 效果 | 时机 |
|------|------|
| 节点放大 | immediate |
| 同 paradigm 节点保持高亮 | immediate |
| 非同 paradigm 节点暗化 | ~150ms ease |
| 该节点 competes_with 边显现 | ~200ms ease |
| tooltip 出现 | ~100ms delay |
| mouseleave → 全部恢复 | ~200ms ease |

### Tooltip

深色背景 tooltip，内容包含：论文名（bold）+ 时间 + paradigm 名。

### Click 节点

| 效果 |
|------|
| Side Panel 滑入 |
| 该节点 builds_on 上下游全链高亮 |
| 其余节点 + 边大幅暗化 |
| competes_with 边以对比色高亮 |
| 再次 click 空白区域 → 恢复，Side Panel 收起 |

### Click Left Rail

| 触发 | 效果 |
|------|------|
| click Bottleneck 标题 | 跳转 Topic View（Phase 2） |
| click 折叠按钮 | section 折叠为单行（Phase 2） |

---

## 数据需求

### 每篇论文数据结构

```typescript
interface PaperNode {
  id: string;                    // "mamba-2"
  title: string;                 // "Mamba-2"
  arxiv_id?: string;             // "2405.21060"
  year: number;                  // 2024
  quarter: 1 | 2 | 3 | 4;

  bottleneck: "sequence_scaling" | "memory_wall" | "compute_scaling";
  paradigm: string;              // "linear_ssm"
  layer: "arch" | "sys" | "infer" | "train" | "memory";

  size: "sm" | "md" | "lg";
  cited_by_count?: number;

  problem: string;               // 解决什么问题（一句话）
  core_idea: string;             // 核心思想（一句话）
  summary?: string;              // 摘要 2-3 句

  builds_on: string[];
  competes_with: string[];
  philosophical_lineage?: string[];

  links?: { arxiv?: string; paper?: string; code?: string; project?: string; };
}
```

### Paradigm Row 配置

```typescript
interface ParadigmRow {
  id: string;              // "linear_ssm"
  name: string;            // "Linear / SSM"
  subtitle: string;        // "线性/状态空间"
  bottleneck: string;      // "sequence_scaling"
  color: string;           // hex
  shape: "circle" | "square" | "diamond" | "triangle" | "hex";
}
```

---

## Demo 原型范围（MVP）

### 论文数量

50-60 篇核心论文，每个 paradigm row 4-6 篇，共 10 行。

### 交互优先级

| 级别 | 交互 |
|------|------|
| P0 | 静态渲染全部节点 + builds_on 连线 + 时间轴 + NOW 线 + 大小差异 |
| P1 | Click → Side Panel 滑入 |
| P1 | Hover → tooltip + 连线高亮 |
| P2 | Era 背景分段 + Pressure Wave |
| P2 | competes_with hover reveal |
| P3 | 折叠/展开 + Filter chips |

### 可省略（Phase 2+）

- Era Focus Mode
- philosophical_lineage 边
- 时间滑块
- 折叠动画

---

## 设计约束（不可违反 — Constitution 级别）

这些是硬约束，任何实现都不得违反：

| 约束 | 规格 | 理由 |
|------|------|------|
| 背景 | 纯白 #FFFFFF | Rams 原则：最大信息密度 |
| 装饰性渐变 | ❌ 禁止 | 无信息编码的视觉元素 |
| 装饰性阴影 | ❌ 禁止 | 同上 |
| 信息编码 opacity 变化 | ✅ 允许 | Pressure Field 的 surge pulse 编码压力冲击 |
| 信息编码发光 | ✅ 允许 | Surge onset 发光编码压力爆发 |
| 强调色 | #FF4400 仅用于 NOW 线和活跃状态 | 控制视觉焦点 |
| 字体 | IBM Plex Sans | 统一性 |
| 最小字号 | 9px | 可读性底线 |
| 边框 | 仅 1px solid ≤ #E4E4E7 | Rams：最少视觉噪音 |
| 布局 | 完全人为编排，❌ 禁止自动布局库 | 叙事控制权 |
| 节点可读性 | 任何背景色不得使节点标签不可辨认 | 信息层级保障 |

### 允许与禁止的边界

| ✅ 允许（编码信息） | ❌ 禁止（无功能装饰） |
|---------|---------|
| Pressure field surge pulse（编码冲击事件） | 装饰性渐变背景 |
| Surge onset 发光（编码"问题爆发"） | 卡片装饰阴影 |
| 节点 opacity 变化（编码活跃度） | 纯美观动画 |
| 5 种几何形状（编码 Layer） | 超过 1px 的边框 |

---

## 现有原型参考

文件：`.claude/docs/design/prototypes/global-view-v2.html`

已实现（v2, 2026-05-09）：
- ✅ Hierarchical swimlane 结构（3 Lane × 10 Paradigm Rows）
- ✅ 节点形状 + 大小差异 + 5 色 paradigm 编码
- ✅ builds_on 连线箭头（含跨 paradigm 虚线）
- ✅ 季度刻度 + NOW 线 + 4 年时间轴（2023-2026）
- ✅ 底部图例栏
- ✅ Paradigm 中文副标题
- ✅ Side Panel 基础版
- ✅ Pressure Field（Lane 级 surge pulse — 待更新为新 spec 的 onset/peak/decay 模型）
- ✅ Pressure Momentum（surge onset 发光 — 待更新）
- ✅ Era 背景分段（Knowledge / Reasoning / Frontier）
- ✅ Pressure Wave 事件解释带 × 2
- ✅ Hover → tooltip + 同 paradigm 高亮 + 其他暗化
- ✅ Left Rail 高度对齐 + 同步滚动
- ✅ 50+ 篇论文数据（对齐 seed_papers.py）

待补（Phase 2）：
- ⬜ Click → builds_on 上下游全链高亮
- ⬜ competes_with hover reveal
- ⬜ Era Focus Mode（点击 Era 标签）
- ⬜ 折叠/展开 section
- ⬜ Agency Frontier 区域虚化效果
- ⬜ Side Panel 完整内容（problem / core_idea / 关系 chips）
