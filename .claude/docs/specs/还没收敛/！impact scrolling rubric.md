# Impact Scoring Rubric — Spec

> 来源：Thomas "如果一个时序里这个圈大了非常多，就是 rising signal"
> 优先级：P1
> 状态：**已实现 v1**
> 实现日志：`logs/impact-scoring.md`

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

## 影响力维度

Impact 由以下维度综合决定：

| 维度 | 含义 | 数据源 |
|------|------|--------|
| 引用量 | 学术影响力的硬指标（需压缩幂律分布） | OpenAlex API |
| 发表场所 | 顶会 oral > poster > arXiv | 人工标注 venue_tier |
| 机构影响力 | 发表机构等级 | 人工标注 institution_tier |
| （未来）级联深度 | 被多少后续工作继承 | 依赖 citation analysis |

## Rising Signal 定义

两种情况算 rising：

1. **引用增速异常高** — 短时间内被大量引用/跟进，正在获得 momentum
2. **顶级机构的新论文** — 顶级机构发布但因时间短引用还低（弱信号候选）

判定标准：使用动态百分位阈值（不是固定分数线），让 rising 永远是相对概念。

## 视觉表达

| 信号类型 | 视觉编码 | 设计依据 |
|---------|---------|---------|
| 影响力高低 | 节点半径连续映射 | 大小 = Impact |
| Foundation/Adaptation | opacity 深 vs 浅（同色系） | 视觉层级区分 |
| Rising | box-shadow glow | momentum 发光 |
| Weak Signal | 虚线边框 dashed border | 区分确定性 |
| 普通 | 实心圆、无额外装饰 | 默认状态 |

## Acceptance Criteria

- [ ] 2024 年新论文中，Sora / π0 明显大于跟进论文
- [ ] 同年份内归一化生效（高引用论文不会"碾压"其他所有）
- [ ] Rising 论文有独立视觉标识且数量合理（~10-15%）
- [ ] 支持 impact_override 手动覆盖异常值
- [ ] Foundation vs Adaptation 视觉区分明显
- [ ] 周度刷新机制可手动触发
- [ ] venue_tier / institution_tier 全量标注

## Constraints

- 必须兼容现有数据模型（增量加字段，不破坏已有 Paper 结构）
- 不引入外部 ML 模型/embedding，纯规则计算
- 使用已有 OpenAlex 数据源

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

- [ ] lineage_score 级联深度：等 citation analysis 再加
- [ ] 是否给 Foundation 论文 base bonus（让 foundation/adaptation 分化更明显）
- [ ] 数据范围是否需要随论文增加动态调整
