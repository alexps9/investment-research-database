# Taxonomy 重构讨论

> 日期：2026-05-19
> 状态：未收敛，待 Thomas 讨论

---

## 当前问题

四条平行 lane（video_gen / latent_space / rl_based / vla）假设每篇论文属于一个类别，但现实是：

1. **Video + RL 在融合** — DreamDojo/DreamZero = RL 思想 + Video 生成能力；UniSim = Video WM 内跑 RL
2. **VLA 不是同层级** — VLA 是"下游消费者"（怎么行动），不是 world model 哲学（怎么理解世界）；Pi-0.7 已整合轻量 WM 组件
3. **WAM 跨越边界** — World Action Model = "world model 直接输出 action"，同时属于 video_gen/rl_based/vla；3 个月内 3+ 篇独立论文使用 WAM 框架，正在成为共识
4. **融合论文硬塞进任何一条 lane 都不对** — DreamGen、Self Forcing、AR-DiT 等"桥"技术

## 来源：MoE Capital 文章的框架

文章将 world model 分为两条历史线索交汇：
- **Thread A: RL World Models**（学做梦）— Schmidhuber 1990 → Ha 2018 → PlaNet → Dreamer V1-V4
- **Thread B: Video Prediction & Generation**（从观看中学习）— Finn 2016 → R3M/VPT → Sora → Genie

2024-2025 交汇：AR-DiT + Self Forcing 让 Video 变可交互 → DreamGen → DreamDojo → DreamZero

文章核心洞察：RL 社区带来"动作条件化+梦境"概念，Video 社区带来"逼真生成+互联网规模数据"。融合产物在架构上师承视频生成，在精神上传承 RL 世界模型。

## 核心质疑：泳道从一开始就是错的？

泳道的根本假设：每篇论文属于且仅属于一个类别。
现实：论文之间是网状关系，融合论文同时属于多个传统。

## 用户想从图上看到什么

投资人核心问题：**"这个方向收敛了吗？赢家出现了吗？还是还在分叉？"**

具体信号：
- 收敛 = 大家往同一方向跑 → 下注执行力
- 分叉 = 技术路线未定 → 需要等或两边投
- 融合节点 = "新品类诞生" → alpha 窗口

## 替代方案（候选）

### A. 保留时间轴 + 改 lane 关系

Video 和 RL 两行挨着，2024 后去掉分界线（视觉合流）。JEPA 独立。VLA 降级为"应用层"。

优：改动最小，叙事清晰
劣：仍然是泳道思维，只是软化了边界

### B. 河流图（Stream）

Y 位置不固定，研究方向像河流——平行流、分叉、合流。不需要 boundary。

优：自然表达融合
劣：布局不确定性高，难手动编排

### C. 关系驱动（Graph + 时间约束）

X = 时间，Y = 由 builds_on 自然聚类。不预设分类，让结构自己浮现。

优：最诚实，不强加分类
劣：可能变成一团乱麻，失去"一眼看出几个方向"的能力

### D. 地铁图（换乘站）

几条线路可以在某些节点交汇。DreamDojo = "换乘站"，同时在两条线上。

优：保留"方向感" + 允许跨线
劣：视觉上复杂

### E. 取消 Y 分类，颜色表示传统

时间轴上自由散布，颜色 = 继承了哪个传统（蓝=Video，绿=RL，紫=JEPA），融合论文用双色。空间聚类自然发生。

优：最灵活，融合论文天然可表达
劣：失去"区域感"

## VLA 的定位问题

VLA 跟 Video/RL/JEPA 不是同层级：
- Video/RL/JEPA = 怎么理解世界（技术哲学）
- VLA = 怎么行动（应用层）

但 VLA 论文（π0、RT-2、Octo）又确实很重要，不能从图上消失。

选项：
1. 降级为"应用层行"，用不同视觉风格
2. 去掉独立 lane，VLA 论文通过 builds_on 连回 world model 节点
3. 改名为"Action/Policy"，语义重定义

## WAM 的定位

WAM（World Action Model）= world model 直接输出 action
- 本质上跨了 video_gen/rl_based 和 vla
- 代表论文：DreamZero、Fast-WAM、GigaBrain
- 信号强度：3 个月内 3+ 篇独立论文，正在成为共识
- 如果用泳道，WAM 无处安放
- 如果用关系图/河流图，WAM 自然是融合节点

## MoE Capital 的其他参考维度

### 二维定位图（公司层面）
- X: Latent-space ↔ Pixel-space
- Y: Research ↔ Production
- 气泡大小 = 融资额

### 五属性框架（系统评估）
| 属性 | 类型 |
|------|------|
| 因果性 | 硬约束（没有就不是 WM） |
| 交互性 | 硬约束 |
| 持久性 | 连续谱（秒→分钟→小时） |
| 实时性 | 连续谱（7Hz→24FPS→实时） |
| 物理准确性 | 连续谱（visually plausible→r=0.995） |

可能的用法：作为节点 metadata，在 side panel 展示雷达图。

## 更深层的问题：二维平面本身可能不够

一篇论文有多个维度：继承了什么传统（RL/Video/JEPA）、解决什么问题（理解/生成/控制）、服务什么应用（驾驶/机器人/游戏）、成熟度如何。二维平面最多编码 2 个维度（X+Y），颜色/大小/形状很快用完。

可能的突破方向：
- **多视图切换** — 同一批数据不同切面（演化视图/竞争视图/投资视图）
- **叙事驱动（Scrollytelling）** — 引导式故事，维度按叙事需要逐步展开
- **交互式探索** — 按查询动态呈现关系，不把维度固定在轴上

## 价值链视角（来自 MoE Capital "什么是可防御的"）

核心问题：**NVIDIA 全栈开源之后，护城河在哪？**

### 四层机会结构

| 层级 | 押注 | 护城河来源 | 时间跨度 | 风险 |
|------|------|-----------|---------|------|
| 前沿横向 WM | 架构弯道超车（如 OpenAI vs DeepMind） | 算法突破 | 最长 3-5 年 | NVIDIA 持续迭代 |
| 垂直专属 WM | 领域物理 ≠ 通用物理 | 专有数据 + 行业 know-how | 中 2-3 年 | 通用模型可能"够用" |
| 基础设施工具 | 解决成本/效率痛点 | 工程深度 | 短 1-2 年 | 被开源吸收 |
| 产品内置 WM | 机器人做有用的事 | 客户为结果付费 | 中 2-3 年 | 硬件+软件+市场三重 |

代表公司：
- 前沿横向：AMI Labs ($1.03B, JEPA)、Embo ($100M+, Dreamer 谱系)、Dream Labs (DreamGen 路线)
- 垂直专属：外科机器人、仓库操作、食品制备专用 WM
- 基础设施：推理优化、评估平台、sim2real 工具、数据管线
- 产品内置：1X (自建 WM)、Figure/Skild (整合 Cosmos)、Physical Intelligence

### RL 的两种含义（关键澄清）

"RL"在 world model 语境里有两层意思，混淆会导致 taxonomy 错误：

**含义 A：RL 作为核心范式（Dreamer 传统）**

Dreamer 系列的逻辑是：
1. 真实世界交互太贵（机器人摔一次就坏了）
2. 所以先学一个环境模型（world model）
3. 让 agent 在模型里"做梦"——想象出成千上万种情况
4. 在梦里跑 RL（试错、拿奖励、更新策略）
5. 学好了再去真实世界执行

这里 world model 存在的唯一目的就是给 RL 省样本。没有 RL，这个 world model 就没有消费者。这叫 "model-based RL"——世界模型是 RL 的工具。

**含义 B：RL 作为最后一英里调优（大平行假设）**

新范式的逻辑是：
1. 先在海量视频上预训练一个大模型（学物理常识，跟 RL 无关）
2. 微调让它能输出动作（动作条件化）
3. 最后用 RL 信号让动作更精确（就像 RLHF 调 ChatGPT）

这里 world model 的目的是"理解物理世界"，RL 只是末端调优手段，不是核心驱动力。

**为什么 Dreamer 作为独立赛道在消亡：**

Dreamer 的核心贡献——"在想象中训练而非在真实世界试错"——这个 idea 已经被 Video WM 吸收了（DreamDojo 就是在视频世界模型里跑 RL）。但 Video WM 的规模和泛化能力是 Dreamer 做不到的（Dreamer 只有百万参数，每个任务从零开始）。

类比：LSTM 的有用 idea（记忆、门控）被 Transformer 吸收了，LSTM 作为独立路线结束了。同理，Dreamer 的有用 idea（想象训练）被 Video WM 吸收了，"rl_based" 作为独立赛道正在结束。

### "大平行"假设（Jim Fan）

```
World Model = 预训练（学仿真下一个物理状态）
动作微调 = 折叠到真实机器人相关的那一薄片
RL = 最后一英里

类比 LLM：GPT 预训练 → RLHF → 推理（o1）
```

如果大平行成立 → 当前阶段 = 物理 AI 的 GPT-2 → 确定性高，下注规模和执行力

### 关键追踪信号

1. **DreamZero "2× vs VLA" 能否被独立复现** → 验证融合路线是否真的优于纯 VLA
2. **通用 vs 垂直的边界** → 外科接触力和仓库拣选是否需要不同模型
3. **成本曲线** → Genie 3 $100/hr, 谁先降到可商用
4. **NVIDIA 锁定效应** → DreamZero 只能 Blackwell 实时，有没有人突破

### 对产品的核心启示

图可能不应该只追踪"论文/技术"，而是追踪**四层之间的关系变化**：
- 前沿研究产出了什么 → 谁最快工程化 → 谁做出了产品
- 本质是**纵向价值链**（研究→基础设施→产品），不是横向技术分类

这呼应了"泳道从一开始就是错的"——真正的结构是纵向的价值链流动，技术从上层流向下层，而不是在平行赛道里各跑各的。

## 更本质的分类轴：world state 用什么表征

来源：对 world model 核心公式的拆解 — `action + condition → 预测 world state`

分类应该按"world state 的表征方式"，而不是按"怎么用这个模型"：

### 四种表征派系

| 派系 | 表征方式 | 优势 | 劣势 | 代表 |
|------|---------|------|------|------|
| **视频表征** | 直接预测 video，输入输出都是像素 | 端到端，互联网数据直接训练，细节丰富 | 计算量大，细节可能拖累决策 | Sora, Cosmos, Genie, DreamDojo |
| **隐空间表征** | 学一个抽象表示空间做预测 | 紧致高效，偏决策相关的 high level 信息 | 需先构建隐空间，评测困难，跟决策模型对接有障碍 | JEPA, V-JEPA 2, Dreamer/RSSM |
| **显式 3D 表征** | 点云 / 3DGS / occupancy | 可操控物体、空间编辑，一致性好（绝对坐标） | 多阶段（3D→2D），不容易 data driven，需要 3D 标注 | World Labs, BlitzGS |
| **抽象表征** | 几何图/粒子结构 | 模拟高效（矩阵乘法），数据需求少 | 泛化性差，不同物体需专门定义表征 | SlotFormer, 粒子物理模拟 |

### 对当前 taxonomy 的冲击

| 当前 lane | 按表征分应该是 | 问题 |
|-----------|--------------|------|
| video_gen | 视频表征 | ✅ 对应 |
| latent_space | 隐空间表征 | ⚠️ 但 3DGS row 混在 video_gen 里了，slot_based 也混在这 |
| rl_based | 不是表征方式，是用途 | ❌ Dreamer 本质是隐空间表征的一种（task-specific latent） |
| vla | 不是表征方式，是用途 | ❌ 是下游消费者 |

### 关键发现

- **Dreamer/RSSM 本质是隐空间表征** — 学一个 latent state 预测下一步，只是它是 task-specific 的，不像 JEPA 是通用预训练的
- **TD-MPC 也是 latent** — 更 action-centric 的隐空间
- **3D 表征（World Labs）目前不够重要到独立成 lane** — 论文少、stealth 状态、落地路径不清晰、MoE Capital 文章几乎没提
- **抽象表征（Slot/粒子）论文也太少** — 可能合并进隐空间

### Tian 的个人判断

更相信视频表征：端到端，可以直接用互联网视频训练，细节预测本身也是采样不一定拖累决策。

### 可能的新结构（未定论）

```
选项 A：三条 + 应用层
  Lane 1: 视频表征 — 主流，论文最多
  Lane 2: 隐空间表征 — JEPA + Dreamer + DINO-WM + Slot + 3DGS（统称"非像素预测"）
  Lane 3: ？ — 可能不需要第三条
  应用层: VLA / WAM

选项 B：两条主线 + 应用层
  Pixel-space（视频派）vs Latent-space（抽象派：隐空间/3D/图结构）
  对应 MoE Capital landscape 图的 X 轴
  应用层: VLA / WAM

待定：Dreamer 是否值得保留独立位置（作为隐空间的一个 row），还是其思想已被 Video WM 吸收
```

---

## 待讨论

- [ ] 跟 Thomas 确认：投资人更需要"结构清晰的分类"还是"真实的融合关系"
- [ ] 如果去掉泳道，是否还需要某种"区域提示"让人快速定位
- [ ] WAM 是否值得单独高亮为"新品类诞生"的信号
- [ ] 五属性框架要不要做进产品里
- [ ] 是否应该从"技术分类图"转向"价值链流动图"
- [ ] "大平行"假设是否作为产品叙事的核心框架
- [ ] 多视图切换 vs 单一图的取舍——投资人实际使用场景是什么
