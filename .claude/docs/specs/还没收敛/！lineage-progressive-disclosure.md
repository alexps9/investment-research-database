# Lineage 渐进式披露设计

## Problem

用户需要理解论文间的引用/竞争/借鉴关系，但信息密度差异大：
- 全局看 4 条技术路线的分叉合流（宏观趋势）
- 单 lane 看具体每篇论文的引用链（微观细节）

一次全部展示 → 信息过载。分层不展示 → 看不到全貌。

## 设计：两级 Lineage 视图

### Level 1: Trunks（全局分叉合流图）

**入口**: v2 页面 ControlBar 的 "Lineage ↗" 按钮

**内容**:
- 4 条 lane 的水平主干线
- 每 lane 只挂路标节点（impact≥50，每 lane 3-8 个）
- 分叉用贝塞尔弧从主干剥离（如 RL 主干 → TD-MPC / Diffuser 分叉）
- 合流用菱形节点，从多条路径汇入（如 DreamZero 汇合 RL + Video）
- 跨 lane 弧线虚线标注

**回答的问题**: "哪些路线在竞争？谁和谁合流了？"

### Level 2: Lane Detail（单 lane 全论文引用图）

**入口**: 在 Level 1 中点击 lane 标签（"Video-Generative →"）

**内容**:
- 该 lane 所有论文（不限 impact）
- 按 row 分行，X 轴 = 时间
- 所有 connections 渲染：inherits（绿实线）/ competes（红虚线）/ borrows（紫点线）
- 低 impact 节点缩小 + 仅 hover 显示标题
- 高 impact 节点始终显示标题

**回答的问题**: "这条路线内部，具体谁引用了谁？"

## 视觉编码

| 元素 | Level 1 (Trunks) | Level 2 (Lane Detail) |
|------|------------------|----------------------|
| 节点大小 | impact 编码 (4/5/7px) | impact 编码 (3/4.5/6px) |
| inherits | 主干实线 (lane color) | 绿实线 |
| competes | 分叉弧 (同色) | 红虚线 |
| borrows | 灰虚线 + 文字标注 | 紫点线 |
| 合流 | 菱形 + subtitle | N/A |
| 标题 | 始终显示 | impact≥60 显示，其余 hover |

## 导航流

```
v2 Global (聚类散点) 
  → [Lineage ↗] → Level 1: Trunks (4-lane 分叉合流)
                     → [点击 lane] → Level 2: Lane Detail (全论文引用)
                     → [← Back] → v2 Global
                   → [← Back to Trunks] → Level 1
```

## 数据来源

- Level 1 节点: 手工策划（TRUNKS 常量内硬编码路标）
- Level 1 合流: 手工策划（CONFLUENCES 常量）
- Level 2 节点: 直接从 `world-model-data.json` 读取该 lane 所有 papers
- Level 2 连线: `paper.connections[]` + `paper.builds_on[]` fallback

## 约束

- X 轴 = 时间（两级都是）
- Level 1 路标数量 ≤ 每 lane 8 个
- Level 2 同 row 内不做碰撞排布（允许重叠，hover 区分）
- 保持 lane 颜色体系

## 已实现

- [x] Level 1: TrunksView（全局分叉合流）
- [x] Level 2: LaneDetailView（单 lane 全论文）
- [x] 导航流：Lineage ↗ → 点 lane → 详情 → Back

## 待优化

- [ ] Level 2 节点碰撞排布（论文多时同 row 重叠）
- [ ] Level 2 跨 lane neighbor 论文显示（如 DreamZero 在 vla 但引用了 rl_based）
- [ ] Level 1 路标数据从 JSON 自动提取（当前硬编码）
- [ ] Hover 高亮关联边（当前只放大节点）
