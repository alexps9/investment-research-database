# Topic View Spec

> 日期：2026-05-09

---

## 一句话

展示**递归分叉**：从共同祖先出发，路线不断分裂出子路线，子路线内部还会继续分裂。

---

## 核心问题

"技术路线如何分叉、竞争、融合？"

---

## 与其他视图的边界

- Global View 回答"哪个问题在爆发" → Topic View 不做 pressure
- Iteration View 回答"版本为什么迭代" → Topic View 不展开版本细节
- Arena View 回答"谁赢了" → Topic View 不做能力评分

Topic View 只回答：**为什么路线分叉，以及分叉的结构是什么。**

---

## 关键洞察：递归分叉

分叉不只发生一次。当路线内部出现核心争议时，会继续分裂：

```
Transformer (root)
├── Linear / SSM
│   ├── SSM-only (Mamba, Mamba-2, Mamba-3)
│   ├── Hybrid SSM (Jamba, Griffin, Zamba)
│   └── Linear Attention (DeltaNet, GLA)
│
├── Sparse / Chunked
│   ├── 位置外推派 (RoPE, ALiBi, YaRN, LongRoPE)
│   └── 分块/环形派 (Ring Attn, LongNet, Infini-Attn)
│
├── MoE / Routing
│   ├── 路由派 (GShard, Switch, Mixtral)
│   ├── Shared Expert 派 (DeepSeek-MoE, DS-V3)
│   └── Fine-grained Expert 派 (...)
│
└── Reasoning Scaling
    ├── Search 派 (ToT, MCTS, Tree-search)
    ├── Verifier 派 (R1, Rubric, Reward modeling)
    └── Latent Reasoning 派 (Quiet-STaR, Recurrent depth)
```

**二次分叉的触发条件**：原路线内部出现了不可调和的设计哲学争议。

---

## 布局

参考图片风格（HRes Technical Trajectory）：

- X 轴 = 时间（季度）
- Y 轴 = 分叉层级（从粗到细）
- 从左侧共同祖先出发，向右展开
- 一级分叉 = 粗线（主路线）
- 二级分叉 = 细线（子路线）
- 节点 = 论文（形状编码 Layer，颜色编码 Paradigm）
- 虚线 = competes_with / 融合关系

布局是**人为编排**的，不是自动计算的。

---

## 视觉编码

继承 Global View 的规则：
- 颜色 = Paradigm（5色）
- 形状 = Layer（circle/square/diamond/triangle/hexagon）
- 大小 = Impact
- 实线 = builds_on
- 短虚线 = competes_with

新增：
- **线宽** = 路线活跃度（dominant 粗 / declining 细）
- **分叉标记** = 分叉点用特殊视觉突出（如加粗节点 + 分叉注释）
- **子路线缩进** = 二级分叉在 Y 轴上缩进，视觉层级清晰

---

## Tradeoff 标注

每条路线旁标注核心 tradeoff（1优1缺）：

| 路线 | ✓ 优 | ✗ 缺 |
|------|------|------|
| SSM-only | O(n) inference | expressivity 上限 |
| Hybrid SSM | 兼顾两家 | 复杂度叠加 |
| Search 派 | 可验证的推理 | 计算成本爆炸 |
| Verifier 派 | 可规模化训练 | reward hacking |
| Latent 派 | 无额外 token | 不可解释 |

---

## 交互

| 动作 | 效果 |
|------|------|
| 从 Global View 点击 bottleneck | 进入该 bottleneck 的 Topic View |
| Hover 路线 | 整条路线高亮，其余暗化，显示 tradeoff |
| Click 节点 | Side Panel 显示论文详情 |
| Click 版本序列 | 跳转 Iteration View |
| Click competes_with 边 | 跳转 Arena View |

---

## 入口数据

```typescript
interface TopicTree {
  root: string;                    // "transformer"
  branches: Branch[];
}

interface Branch {
  id: string;
  name: string;                    // "Linear / SSM"
  paradigm: string;
  papers: string[];                // lineage order
  tradeoff: { pros: string[]; cons: string[]; };
  sub_branches?: Branch[];         // 递归！二级分叉
  players?: string[];
}
```

---

## Acceptance Criteria

- [ ] 用户 3 秒内感知"从一个祖先分出了 N 条路线"
- [ ] 用户能看到二级分叉（路线内部还有子路线）
- [ ] 每条路线的 tradeoff 一目了然
- [ ] 时间方向清晰（左早右晚）
- [ ] competes_with 关系可感知
- [ ] 不退化成"纯列表"或"纯时间线"

---

## 约束

- 白底 #FFFFFF，无装饰渐变/阴影
- IBM Plex Sans
- 人为编排布局，禁止自动布局
- 节点编码与 Global View 一致
