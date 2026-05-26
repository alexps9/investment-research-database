# Citation 深度分析 — 继承性/对比性/借鉴性

> 来源：Thomas "citation 本身也有可被挖的线索，它到底是一篇继承性的还是一篇对比性的？还是里面有一些重要的工作的 idea 大家是互相借鉴的"
> 优先级：P2（依赖论文数量积累）
> 状态：Phase 1/1.5 已完成，Phase 2+ 待做

---

## Problem Statement

当前图谱只有节点位置，没有连线。投资人无法看出：
- 某个方向是否已收敛（全是继承 → 收敛）
- 是否还有替代路线在竞争（competes 关系多 → 未收敛）
- 跨 lane 融合趋势（borrows 跨域 → 融合前兆）

## Success Metrics

- 用户能从图上一眼判断"这条赛道收敛了没有"
- Foundation 之间的演化脉络清晰（谁继承谁、谁和谁竞争）
- Adaptation 能看出依赖哪个 Foundation
- 新论文进来后，能在 1 天内确定它和已有论文的关系（自动化覆盖 > 70%）

## Non-Goals

- 不做全量引用网络（只看命中我们库的论文间关系）
- 不做情感分析（不判断"正面引用/负面引用"）
- 不做实时流式处理（批量定期跑即可）

---

## 三种关系类型

| 类型 | 含义 | 投资信号 |
|------|------|---------|
| **inherits** | 直接继承架构/方法，在其基础上改进 | 路线收敛，标准确立 |
| **competes** | 解决同一问题的替代方案 | 路线未定，需等胜出者 |
| **borrows** | 跨领域借鉴某个 idea（非整体架构） | 融合趋势，新方向酝酿 |

## 数据模型

每篇论文增加 `connections` 字段：

```json
{
  "id": "cosmos_policy",
  "connections": [
    { "target": "cosmos", "type": "inherits" },
    { "target": "pi0", "type": "borrows" }
  ]
}
```

工作量分层：
- L1：所有 adaptation 标 `inherits` 指向对应 foundation（~130 篇，每篇 <1min）
- L2：foundation 之间标 competes/borrows（~30-40 对，需判断）
- L3：新论文的关系自动化补全

## 前端呈现原则

- **默认不画线，交互触发**（全局视图线太多会乱）
- Hover foundation → 高亮其 adaptation 群
- 点击 foundation → 展开 lineage 面板，显示三种关系
- 可选"演化视图" toggle → 只显示 foundation 之间连线（~30 条）

连线视觉编码：
- 实线 ─── inherits（继承）
- 短虚线 - - competes（竞争）
- 点线 ··· borrows（借鉴）

## Acceptance Criteria

- [x] JSON 数据中有 builds_on / connections 字段
- [x] 前端 hover foundation 时，其 adaptation 群高亮
- [x] Side Panel 显示关系类型（video_gen lane 已完成）
- [ ] 演化视图中 foundation 间连线可区分三种类型（全 lane）
- [ ] 新论文进来时，脚本能自动建议候选关系（人确认即可）
- [ ] lineage_depth 可作为因子输入 impact_score

## Constraints

- 只处理已在我们库中的论文之间的关系（不做全网 citation graph）
- 不引入付费 API 作为硬依赖（付费可加速但免费路径必须可走通）
- 连线数据兼容现有 JSON 结构（增量加字段）
- 前端连线不能破坏现有布局的可读性

---

## 待确认

- [ ] borrows 跨 lane 时前端怎么画线（曲线？还是只在面板里文字展示）
- [ ] lineage_depth 权重多少合适（等数据积累后调）
- [ ] L1 标注是否需要用户逐个确认，还是批量自动标（adaptation → 对应 foundation）
