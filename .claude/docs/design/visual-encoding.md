# Visual Encoding Spec

> 前端可视化的编码规则。定义 WHAT，不规定 HOW。
>
> 日期：2026-05-10

---

## 1. 核心理念

**AI 技术演化地铁图** — 让研究者一眼看出"面对同一个瓶颈，人们产生了哪些不同技术哲学，以及谁赢了"。

本质结构：`Lane（问题空间）> Paradigm Row（技术路线）> Paper Node（具体工作）`

---

## 2. 编码规则

### 2.1 颜色 = Paradigm（技术哲学）— 严格 5 色

| # | Paradigm | Hex | 信仰 |
|---|----------|-----|------|
| 1 | Attention-native | `#475569` 灰蓝 | Dense attention 没问题，优化实现即可 |
| 2 | Post-Attention | `#2563EB` 蓝 | Attention 不可扩展，必须超越 |
| 3 | Sparse / Long-context | `#0D9488` 青绿 | 稀疏或外推足够 |
| 4 | Conditional Compute | `#DC2626` 红 | 不是所有 token 都值得 full compute |
| 5 | Reasoning Scaling | `#EA580C` 橙 | 能力来自 search + verification |

节点 fill = paradigm 色 @ 50% opacity，stroke = 100%。

**Hybrid 规则：** 主 paradigm = builds_on 目标的 paradigm。次 paradigm 用小 tag 标注。

**验收标准：**
- [ ] 任取一个节点，仅看颜色即可判断其技术哲学归属
- [ ] Hybrid 节点（如 Jamba）的主色与其 builds_on 目标一致

### 2.2 形状 = Layer（解决方案层级）— 严格 5 种

| Layer | 形状 | 含义 |
|-------|------|------|
| `arch` | circle | 改模型结构 |
| `sys` | square | 改 kernel / parallelism |
| `infer` | diamond | 改 decoding / runtime |
| `train` | triangle | 改训练方式 / RL |
| `memory` | hexagon | 改 KV / 位置编码 / 外部记忆 |

**验收标准：**
- [ ] 同一行内可出现不同形状（如 KV Compression 行有 hexagon 也有 square）
- [ ] 用户无需图例即可区分五种形状

### 2.3 大小 = Impact

三档：sm / md / lg。映射 `log(cited_by_count)` 分位。

**验收标准：**
- [ ] 三档大小之间的视觉差异肉眼可辨（相邻档至少 1.5× 面积比）

### 2.4 连线 = 关系类型

| 类型 | 外观 | 方向 | 含义 |
|------|------|------|------|
| `builds_on` | 实线，source paradigm 色 @ 40% | 有箭头 | 技术演进 |
| `competes_with` | 短虚线，中性灰 | 无箭头 | 同问题竞争 |
| `cross_lane_arc` | 长虚线 Bezier 弧，source lane 色 | 有箭头 | 跨问题空间因果 |

**验收标准：**
- [ ] 仅看线型即可区分三种关系，无需颜色辅助
- [ ] builds_on 链可追溯完整演进路径（A→B→C 无断链）

---

## 3. 三级视图导航

核心原则：**复杂度逐级递进，连线只出现在专门回答"为什么分叉"的视图里。**

```
Global View（全景）──→ Topic View（谱系）──→ Iteration View（迭代）
   零连线                 Bezier 分叉弧           mutation 时间轴
```

### 3.1 Global View — 全景总览

**回答问题：** 技术格局是什么样的？

**布局：** 所有 Lane 平铺，每 Lane 下 Row 可折叠/展开为 track。节点按时间排列。

**连线：无。** 不画 builds_on、不画 competes_with、不画 cross_lane_arc。时间顺序 + track 归属本身已暗示演进关系。

**交互：**
- Hover Lane 左侧标签 → 出现 "View Lineage ↗" 按钮
- Hover 展开态下的 track 区域 → 出现 "View Evolution ↗"
- Hover 节点 → Tooltip + 其余行压暗
- 点击节点 → SidePanel（含 "View Evolution ↗" 跳转链接）
- 点击 Row 标签 → 展开/折叠该行的子 track

**验收标准：**
- [ ] 初始态单屏可总览所有 Lane 和 Row（不含滚动）
- [ ] 展开/折叠有平滑过渡
- [ ] 画面上无任何连线（零 SVG path / line 元素）
- [ ] Hover Lane 标签时 "View Lineage ↗" 可见

### 3.2 Topic View — 技术谱系（分叉）

**回答问题：** 为什么技术路线分叉了？

**入口：** Global View Lane 标签的 "View Lineage ↗"
**退出：** 面包屑 / 返回按钮 → Global View

**布局：** GitGraph 风格树状图。该 Lane 下所有 Row 作为平行轨道，轨道间用 Bezier 弧表示分叉来源。

**连线规则：**
- 同 track 内 builds_on → 实线 + 箭头（paradigm 色 @ 40%）
- 跨 track 分叉弧 → 长虚线 Bezier（source paradigm 色）
- competes_with → 短虚线（中性灰），Hover 时叠加显示

**交互：**
- 点击某条 track → 进入 Iteration View
- Hover 节点 → Tooltip
- 点击节点 → SidePanel

**验收标准：**
- [ ] 只显示该 Lane 下的 Row，其他 Lane 不可见
- [ ] 分叉弧从具体论文节点发出（不是从行首）
- [ ] 面包屑显示路径（如 "Global › Context Scaling"）
- [ ] 连线是此视图的主角 — 分叉关系一目了然

### 3.3 Iteration View — 单路线迭代

**回答问题：** 架构为什么不断变？

**入口：**
- Topic View 中点击具体 track
- Global View 展开态 track 区域的 "View Evolution ↗"
- Global View SidePanel 中的 "View Evolution ↗" 链接

**退出：** 面包屑 / 返回按钮

**布局：** 水平时间轴（与 Global View 方向一致）。只聚焦一条路线。

**核心内容：**
- 该路线所有版本节点按时间排列
- 节点间实线连接（演进链）
- 每个节点下方 mutation 卡片：summary + detail + bottleneck + result

**MVP 范围：** Mamba (→ Mamba-2 → Mamba-3) 和 RWKV (v4 → v5 → v6 → v7)

**验收标准：**
- [ ] 水平时间轴，节点从左到右按时间排列
- [ ] 每个节点有 mutation 卡片（bottleneck + result）
- [ ] 面包屑显示完整路径（如 "Global › Context Scaling › Mamba"）
- [ ] 两个入口（Topic View / Global View）均可达

---

## 4. 布局语义

### X 轴 = 时间

按季度网格（2023 Q1 → 2026 Q4）。三个视图共用水平时间轴方向。NOW 线（`#FF4400`）标注当前时间。

### Y 轴 = 可折叠树状泳道（Global View）

```
Lane（问题空间）
  └── Row（技术路线，可展开为 track）
```

### Pressure Wave（背景带）

水平淡色带，标注产业压力事件。全图不超过 5 条。信息编码，不是装饰。

**验收标准：**
- [ ] X 轴季度刻度等间距
- [ ] NOW 线位置与实际日期一致
- [ ] Pressure Wave 与对应时间段对齐

---

## 5. 设计约束

| ✅ 允许 | ❌ 禁止 |
|---------|---------|
| Gaussian blur 压力场（编码信息） | 装饰性渐变 |
| box-shadow glow（编码活跃度变化） | 装饰性阴影 |
| opacity 变化（编码层级/活跃度） | 超过 1px 的边框 |
| 5 色 + 5 形状编码 | 自动布局算法 |

背景 `#FFFFFF`，面板 `#FAFAFA`，边框 `#E4E4E7` 仅 1px，字体 IBM Plex Sans。

---

## 6. Non-Goals

- 不实现自动聚类/卫星节点（本期）
- 不实现语义搜索或过滤
- 不支持用户自定义颜色/形状映射
- 不做移动端适配
- 不做论文全文展示（仅 metadata + 1-2 句摘要）
- **Global View 不画任何连线**（连线只出现在 Topic View）
- Iteration View 本期只做 Mamba 和 RWKV 两条路线
- Topic View 本期只覆盖 Context Scaling Lane
