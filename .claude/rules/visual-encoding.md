---
paths:
  - "frontend/src/**"
  - ".claude/docs/design/**"
  - ".claude/docs/specs/**"
---

# 视觉设计规范

## Rams 原则正确解读

核心是**每个视觉元素必须编码信息**，不是"尽量少视觉元素"。

- 无功能的装饰 → 删除
- 编码信息的视觉手段（blur 压力场、glow momentum、形状编码）→ 保留

## 颜色体系

| 用途 | 色值 |
|------|------|
| 背景 | #FFFFFF |
| 面板背景 | #FAFAFA |
| 文本 | #18181B / #3F3F46 / #71717A / #A1A1AA |
| 边框 | #E4E4E7（仅 1px） |
| NOW 线 | #FF4400 |
| Paradigm 5色 | 灰蓝 #475569 / 蓝 #2563EB / 青绿 #0D9488 / 红 #DC2626 / 橙 #EA580C |
| Lane 3色 | 蓝 #2563EB / 绿 #059669 / 橙 #EA580C |

## 允许与禁止

| 允许 | 禁止 |
|------|------|
| Gaussian blur 压力场（信息编码） | 装饰性渐变 |
| box-shadow momentum 发光（信息编码） | 装饰性阴影 |
| 5种几何形状编码 Layer | 自动布局 |
| opacity 变化编码活跃度 | 超过 1px 的边框 |

## 节点编码

- **颜色** = Paradigm（5 色，世界观）
- **形状** = Layer（circle/square/diamond/triangle/hexagon）
- **大小** = Impact（log citations → sm/md/lg）
- **连线** = 关系（实线 builds_on / 短虚线 competes / 长虚线 lineage）
