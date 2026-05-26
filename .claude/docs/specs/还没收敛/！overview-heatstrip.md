# Overview Heatstrip（四赛道热度概览）

## Problem

当前 v2 全局视图展开后很长（需要滚动），无法一屏对比四条赛道的宏观活跃度。用户需要一个"仪表盘"级别的入口，一眼看出：
- 哪条赛道 2024-2025 最密集（爆发期）
- 哪条赛道最近断流（衰退）
- 各赛道的 impact 分布差异

## 目标

一屏内展示 4 条赛道的**时间-密度**对比，作为全局导航入口。

## 设计

### 布局

4 条水平 strip，纵向堆叠，每条高度 ~80-100px。全部一屏可见（total ~400px）。

每条 strip 内容：
- 左侧：lane 名称 + subtitle
- 主体：X 轴 = 时间（2019-2026），节点 = 论文圆点
- 圆点大小 = impact（2px/3px/5px 三档）
- 圆点颜色 = lane color，opacity 编码 impact（高 impact 更实）
- **无标题、无标注**——纯密度感知
- Y 轴：该 lane 内所有论文随机散布在 strip 高度内（不分 row）

### 交互

- Hover strip → 显示该 lane 的论文数 + 近一年增长
- 点击 strip → 跳转到 v2 全局视图并筛选该 lane（`filterLane = lane.id`）

### 位置

作为 v2 页面的**默认首屏**：
- 进入 `/world-model-v2` 时先看 Overview
- 页面顶部加一个 tab：`Overview | Detail`
- Overview = 四条 heatstrip
- Detail = 当前的全局散点视图

或者更简单：放在当前视图的**上方**作为一个折叠面板。

## 视觉编码

| 元素 | 编码 |
|------|------|
| 圆点大小 | impact: ≥70→5px, ≥50→3px, <50→2px |
| 圆点 opacity | impact: ≥70→0.8, ≥50→0.5, <50→0.25 |
| 圆点颜色 | lane color（蓝/绿/紫/橙） |
| 背景 | lane color opacity 0.02 |
| strip 间距 | 1px solid #E4E4E7 |

## 约束

- X 轴 = 时间（与 v2 对齐）
- 一屏可见（4 strips total height ≤ 450px）
- 不显示任何文字标题（纯密度图）
- 不做碰撞排布（允许重叠，重叠本身=密度信息）
- 保持 lane 颜色体系

## 验收标准

- [ ] 一屏内可见 4 条赛道全部论文的时间分布
- [ ] 视觉上能明显区分"密集区"和"稀疏区"
- [ ] 点击 strip 可跳转到对应 lane 的详细视图
- [ ] 响应式：窄屏时 strip 高度自适应
