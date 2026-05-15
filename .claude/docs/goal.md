# World Model 技术路线图 — 需求文档

> 来源：团队会议纪要结构化整理
> 优先级：高于 Transformer 技术路线迭代

---

## 一、项目目标

为投资人提供一份 World Model 领域的**技术路线演进图谱** + **市场信号地图**。
不是纯技术，要有 sharp 观点 + evidence，对标 SEMI Analysis（比科普深、有技术投资视角）
   > 原文："deliver 的东西…不能太纯技术…比科普还要在技术深一些，升维一点"

scope：
3D 物理环境 · 仿真
机器人 · 灵巧手 · VLA
自动驾驶 ·具身导航
数字世界 ·虚实双向
空间感知 · 决策


核心问题：
- World Model 的本质是什么？
- 各赛道的范式怎么变？
- 哪些团队/实验室在一线？在解决什么问题？
- 钱去哪了？供需端 gap 在哪？（非必须）

**对标**: SEMI Analysis（芯片领域）— 比科普深一层，但不是纯技术论文。要有 sharp 观点 + evidence。
具体可以学习：`.claude/docs/knowledge/research.md`了解投资人怎么思考

投资关注的
- 成长性：技术是否收敛/还在迭代？哪条路线正在赢？（VLA vs 具身 RL，像素 vs 潜空间）
Topic View：当后来者不是创造新范式，而是在现有范式上打补丁的时候，说明这条 Lane 内部已经选定了事实标准
- 壁垒：谁在做？追赶周期多长？有没有替代路线？
Global View里面看机构在各个赛道的布局，以及为什么是他们做这件事情（哪个有优势：标准？数据？算力？场景先占？）

其他的：稀缺性（供需 gap 在哪？哪个环节缺人/缺钱/缺数据？）
---

## 二、赛道划分（应用环境维度）

| 赛道 | 关键词 | 优先级 |
|------|--------|--------|
| 多模态文生/图生视频 | Sora, Wan, Cosmos, Gen-3 | P0 |
| 自动驾驶 | GAIA-1, DriveVLA, UniWorld | P0 |
| 具身机器人（Robotics） | Dreamer, RoboDreamer, TesserAct, VLA | P0 |
| 空间智能 | 李飞飞 World Labs, LeCun JEPA | P0 |
| 3D 游戏 / VR | Genie 2, Oasis, GameNGen | P0 |
| 无人机 | — | P2（少看） |

---

## 三、分析框架

### 3.1 技术路线维度（纵轴 — 范式）

```
World Model 本质 = 编码 → 潜空间建模 → 解码/预测

建模方式分支:目前没完全收敛

关键范式问题（尚未收敛）：
- VLA vs 具身 RL — 路线之争
- AI-native 仿真 vs 传统物理引擎（Isaac Gym）— World Model 做仿真器
- World Model 能否直接输出 action？还是只做环境预测？

### 3.2 Player 维度（横轴 — 谁在做）


### 3.3 市场维度（钱去哪了）：暂时不用管

- 一级市场投融资：青科、IT 橘子等数据源
- 按赛道看融资规模和估值：
  - 具身机器人本体
  - 灵巧手/关节（帕西尼等）
  - 轮式/足式
  - 自动驾驶
  - 3D 游戏 / VR
- 国外收敛信号 → 国内跟进速度

---

## 四、Deliverable 要求

###技术路线图谱需要能产生insight和信息（本工具输出）

4.1.首页global view能看出的信息：
按范式分lane，可以看到不同时间
- 筛选赛道

- 颜色编码 = Player（一眼看出谁在哪个赛道布局）
Global View里面看机构在各个赛道的布局，以及为什么是他们做这件事情（哪个有优势：标准？数据？算力？场景先占？）

4.1.1 方向热度
.claude/docs/specs/还没收敛/！热门方向.md
1. 哪个方向此刻正在加速 — Diffusion 密集是因为它一直多，还是最近突然涌入？
  2. 多团队独立入场信号 — JEPA 那行 Meta 一直在做，但如果突然 DeepMind、NVIDIA 也开始做 JEPA
  了，这才是真正的热门信号。当前图看不出"谁是新入场的"
  3. 方向之间的竞争/替代 — Diffusion vs JEPA vs Autoregressive，谁在抢人？
  4. 从哪个方向流向哪个方向 — 比如原来做 RL-based 的团队开始转做 Diffusion-based，这是强烈的收敛信号

4.1.2 论文节点热度
.claude/docs/specs/还没收敛/！impact scrolling rubric.md


---
4.2.view lineage能看出的信息
- 连线 = 技术演进关系（builds_on / competes / enables）
- 能回答："面对同一问题，不同团队走了什么不同路线？"


---
未来（先不用管）：
 信号源/人的 Mapping（配合 Freddy/LIANG Hao）

- 论文 → 一作 → 实验室/团队
- 被投公司 CTO 列表
- 访谈 pipeline（智源等）

投资观点输出

- 每个赛道的驱动因素 & 发展路径
- 供需端 gap 分析
- 范式变化预判
- 有 evidence，简洁但有观点

---

## 五、工作方法

1. **Bottom-up**: 顺综述找关键论文 → 跑图谱 → 看整体体系
2. **Top-down**: 从 World Model 本质（编码→建模→解码）出发 → 拆到每个赛道
3. **收敛**: 信息收集 → 抽象框架 → 填充 knowledge → 输出观点

---
