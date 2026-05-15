# Impact Scoring Rubric — Spec

> 来源：Thomas "如果一个时序里这个圈大了非常多，就是 rising signal"
> 优先级：P1
> 状态：待实现
> 参考：`knowledge/product/scoring-methodology-reference.md`

---

## Problem Statement

当前节点大小只有 sm/md/lg 三档，无法表达影响力的连续差异。用户看图时分不清"范式定义者"和"跟进性工作"。更重要的是，一些论文发表时不起眼但后来变得极重要（rising signal），当前没有任何视觉表达。

## Success Metrics

- 节点大小连续映射，一眼能区分 Sora 级别论文和普通跟进论文
- Rising signal（正在获得 momentum 的论文）有独立视觉标识
- Weak signal（顶级机构新发但未被关注）有独立视觉标识
- 同年份论文之间的大小差异合理（不会因为 2024 论文引用少就全部显示很小）

## Non-Goals

- 本期不做热门方向聚类（单独 spec）
- 不做实时刷新（未来需求，先手动触发）
- 不做用户自定义权重 UI

---

## 影响力由什么决定

四个维度，综合反映一篇论文的影响力：

| 维度 | 含义 | 数据源 |
|------|------|--------|
| 引用量 | 被引次数（同年份归一化） | OpenAlex cited_by_count |
| 发表场所 | 社区认可度 | 顶会 oral > poster > arXiv |
| 级联深度 | 技术继承影响力（被引论文又被引 = 深层传播） | builds_on 关系图 |
| 机构影响力 | 信源可信度 | 发表机构等级 |

权重待数据验证后确定（初始假设：引用 > 场所 ≈ 级联 > 机构）。

## Rising Signal 定义

两种情况算 rising：

1. **引用增速异常高** — 短时间内被大量引用/跟进，正在获得 momentum
2. **顶级机构的新论文** — 顶级机构发布但因时间短引用还低（弱信号候选）

判定标准：使用动态百分位阈值（不是固定分数线），让 rising 永远是相对概念。

## 视觉表达

| 信号类型 | 视觉编码 | 设计依据 |
|---------|---------|---------|
| 影响力高低 | 节点半径（连续映射，亚线性避免膨胀） | 大小 = Impact |
| Rising | 节点外圈 glow | momentum 发光（CLAUDE.md 允许） |
| Weak Signal | 节点虚线边框 | 区分确定性 |
| 普通 | 实线边框 | 默认状态 |

半径范围约束：最小可识别（~4px）→ 最大不遮挡（~16px）。

## 验收标准

- [ ] Attention Is All You Need (2017) 在 Transformer 视图中明显最大
- [ ] 2024 年新论文中，Sora / π0 明显大于跟进论文
- [ ] 同年份内百分位归一化生效（不因绝对引用低而全部缩小）
- [ ] Rising 论文有 glow 且数量合理（不超过 20%）
- [ ] 支持 impact_override 手动覆盖异常值
- [ ] 周度刷新机制可手动触发

## Constraints

- 必须兼容现有数据模型（增量加字段，不破坏已有 Paper 结构）
- 不引入外部 ML 模型/embedding，纯规则计算
- 使用已有 OpenAlex 数据源 + builds_on 关系

---

## 附录：Tier 定义（分级标准）

### Venue Tier

| Tier | 示例 |
|------|------|
| T1（顶会 oral/spotlight） | NeurIPS oral, ICML oral, ICLR spotlight |
| T2（顶会 poster） | NeurIPS, ICML, ICLR, CVPR, ICRA poster |
| T3（次级会议/顶刊） | AAAI, CoRL, IROS, Nature Machine Intelligence |
| T4（Workshop / arXiv） | arXiv, workshop papers |
| T5（未发表） | Technical reports, blog posts |

### Institution Tier

| Tier | 示例 |
|------|------|
| T1（顶级 AI Lab） | DeepMind, OpenAI, Meta FAIR, NVIDIA Research |
| T2（顶级高校） | MIT, Stanford, Berkeley, CMU, Tsinghua |
| T3（强校/二线 Lab） | 其他知名高校, Alibaba DAMO, ByteDance |
| T4（一般机构） | 普通高校、小公司 |

---

## 待确认

- [ ] 权重比例跑一次数据再定
- [ ] Rising glow 用赛道同色还是统一橙色？
- [ ] lineage_score 级联深度实现复杂度是否可接受
