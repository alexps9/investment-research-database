# Overview Heatstrip（四赛道热度概览）

## Problem

当前 v2 全局视图展开后很长（需要滚动），无法一屏对比四条赛道的宏观活跃度。用户需要一个"仪表盘"级别的入口，一眼看出：
- 哪条赛道 2024-2025 最密集（爆发期）
- 哪条赛道最近断流（衰退）
- 各赛道的 impact 分布差异

## 目标

一屏内展示 4 条赛道的**时间-密度**对比，作为全局导航入口。

## 已实现

### 布局

4 条水平 strip（`OverviewStrips` 组件），纵向堆叠，每条高度 90px。

每条 strip 内容：
- 左侧：lane 名称 + subtitle + 论文数
- 主体：X 轴 = 时间，节点 = 论文圆点
- **Y 轴 = Detail 视图的投影**（非随机）：调用 `computeRowPositions` 计算 Detail 布局，将 Y 归一化到 strip 高度内

### 交互

- 点击 lane 背景 → 跳转到该 lane 的 Detail 视图（`filterLane + setView('global')`）
- 点击大点（foundation） → 切 Detail 并选中该论文（弹出侧边栏）
- 小点不可点击

### 位置

作为 v2 页面的**默认首屏**：
- 进入 `/world-model-v2` 时显示 Overview
- 顶部 tab：`Overview | Detail | Lineage ↗ | Table ↗`

## 视觉编码

| 元素 | 编码 |
|------|------|
| 圆点大小 | impact: ≥70→5px, ≥50→3.5px, <50→2px |
| 圆点 opacity | impact: ≥70→0.75, ≥50→0.45, <50→0.2 |
| 圆点颜色 | lane color（蓝/绿/紫/橙） |
| 背景 | lane color opacity 0.015 |
| strip 间距 | 0.5px solid #E4E4E7 |

## 关键设计决策

| 决策 | 原因 |
|------|------|
| Y 从 Detail 投影，不独立随机 | 保持 Overview→Detail 的空间记忆连续性 |
| 点击大点直接进 Detail+选中 | 减少导航层级，快速定位 |
| 小点不可点击 | 避免 90px strip 内小目标误触 |

## 验收标准

- [x] 一屏内可见 4 条赛道全部论文的时间分布
- [x] 视觉上能明显区分"密集区"和"稀疏区"
- [x] 点击 strip 可跳转到对应 lane 的详细视图
- [x] 点击大点可切 Detail 并选中
- [x] Overview 与 Detail Y 位置一致
- [ ] 响应式：窄屏时 strip 高度自适应
