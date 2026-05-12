# World Model 技术路线图 — 需求文档

> 来源：团队会议纪要结构化整理
> 优先级：高于 Transformer 技术路线迭代

---

## 一、项目目标

为投资人提供一份 World Model 领域的**技术路线演进图谱** + **市场信号地图**。

核心问题：
- World Model 的本质是什么？
- 各赛道的范式怎么变？
- 哪些团队/实验室在一线？在解决什么问题？
- 钱去哪了？供需端 gap 在哪？

**对标**: SEMI Analysis（芯片领域）— 比科普深一层，但不是纯技术论文。要有 sharp 观点 + evidence。

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

建模方式分支:
├─ RL-Based (Dreamer, TD-MPC) — 想象力驱动策略学习
├─ 视频生成式 (Sora, Cosmos) — 像素级世界仿真
├─ 潜空间预测 (JEPA, DINO-WM) — 特征空间动力学
├─ 对象中心 (Slot Attention) — 结构化组合表征
└─ VLA 融合 (DriveVLA, RT-2) — 感知-决策闭环
```

关键范式问题（尚未收敛）：
- VLA vs 具身 RL — 路线之争
- AI-native 仿真 vs 传统物理引擎（Isaac Gym）— World Model 做仿真器
- World Model 能否直接输出 action？还是只做环境预测？

### 3.2 Player 维度（横轴 — 谁在做）

| Player | 方向 | 代表作 |
|--------|------|--------|
| Google DeepMind | RL-WM, Game | Dreamer V3, Genie 2 |
| OpenAI | 视频生成 | Sora |
| Meta AI | 潜空间, 开源LLM | V-JEPA 2, LLaMA, DINO |
| NVIDIA | 物理仿真 | Cosmos, Isaac Gym |
| UC Berkeley | MBRL | TD-MPC2 |
| Alibaba | 视频生成 | Wan |
| 智源 | 多模态 | 待访谈 |
| World Labs (李飞飞) | 空间智能 | LRM |

### 3.3 市场维度（钱去哪了）

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

### 4.1 技术路线图谱（本工具输出）

- 按赛道 × 时间展示关键论文/产品节点
- 颜色编码 = Player（一眼看出谁在哪个赛道布局）
- 连线 = 技术演进关系（builds_on / competes / enables）
- 能回答："面对同一问题，不同团队走了什么不同路线？"

### 4.2 信号源/人的 Mapping（配合 Freddy/LIANG Hao）

- 论文 → 一作 → 实验室/团队
- 被投公司 CTO 列表
- 访谈 pipeline（智源等）

### 4.3 投资观点输出

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

## 六、当前进展 & TODO

### 已完成
- [x] 综述论文阅读（Awesome-World-Models, 2026.01）
- [x] 论文图谱 v1（83 篇，5 Lanes，按 Player 着色）
- [x] 连线关系梳理（builds_on, enables, competes）
- [x] 前后端实现（可交互地铁图）

### 待做
- [ ] 补充自动驾驶赛道论文（Part 6 ~20篇）
- [ ] 补充 GUI Agent / Game Simulation 论文（Part 8-9）
- [ ] Player Mapping：论文 → 一作 → 团队/公司
- [ ] 市场数据：融资规模、估值（IT 橘子/青科）
- [ ] 范式收敛判断：VLA vs 具身 RL 路线对比
- [ ] 访谈 pipeline 配合（智源、帕西尼等）
- [ ] 最终 Deliver：内部分享材料（非纯技术，有观点）

---

## 附录：会议原始记录

<details>
<summary>点击展开原始会议纪要</summary>

（原始语音转文字内容保留在 git history 中）

</details>
