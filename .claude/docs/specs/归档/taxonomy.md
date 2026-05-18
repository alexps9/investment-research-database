---
status: backlog
created: 2026-05-11
complexity: 🔴复杂（需团队共识）
---

# World Model 分类体系 — Taxonomy 收敛

## 一句话

确定 Global View 的 Lane 分类方案，降低投资人认知成本，同时保持技术准确性。

---

## 问题来源

> Angela："你这个标签化到底是什么维度？我觉得需要给它一个对齐，AI 比较习惯自己有一些分类，但它需要共识的分类"
> Kai："24年前基本上都是没有用 diffusion，最近都是用 diffusion 去做了"

现状：4 Lane 按建模方法分（RL / Observation-Level / Latent-Space / Object-Centric），技术准确但投资人看不懂名字。

---

## 候选方案

### 方案 A：保持 4 Lane，换 label（最小改动）

| 现 Lane | 新 label | 一句话 |
|---------|---------|--------|
| RL-Based WMs | 想象力规划 | 在脑子里模拟 → 选最优路径 |
| Obs-Level Generative | 视频仿真 | 生成逼真像素级世界 |
| Latent-Space WMs | 物理直觉 | 不生成画面，但"懂"物理规律 |
| Object-Centric WMs | 结构推理 | 把世界拆成物体 + 因果关系 |

- 优点：零数据迁移，只改前端显示
- 缺点：4 个 Lane 还是多，"物理直觉"和"结构推理"对投资人区分度不够

### 方案 B：3 Lane 按用途分（推荐）

```
仿真器型（Simulator）    → 生成逼真环境给你用
规划器型（Planner）      → 在想象中做决策
理解器型（Understanding）→ 学世界的底层规律
```

| Lane | 核心问题 | 代表 | 投资逻辑 |
|------|---------|------|---------|
| 仿真器 | 能不能替代真实世界做训练？ | Sora, Cosmos, Genie 2, GAIA-1 | 数字孪生、内容生成、仿真平台 |
| 规划器 | 能不能在脑子里想 N 步选最优？ | Dreamer V1-V3, TD-MPC2, RoboDreamer | 机器人 sample efficiency、具身智能 |
| 理解器 | 能不能真懂物理和因果？ | V-JEPA, DINO-WM, Slot Attention, SlotFormer | AGI 基础设施、LeCun 路线 |

**与现 4 Lane 的映射：**
```
Lane A (RL-Based)       → 规划器
Lane B (Obs-Level Gen)  → 仿真器
Lane C (Latent-Space)   → 理解器
Lane D (Object-Centric) → 理解器（合并）
```

**互斥性检验：**

| 论文 | 归类 | 歧义？ |
|------|------|:------:|
| Sora | 仿真器 | ❌ |
| Dreamer V3 | 规划器 | ❌ |
| V-JEPA 2 | 理解器 | ❌ |
| Cosmos | 仿真器 | ❌ |
| RoboDreamer | 规划器 | ⚠️ 也用视频生成，但核心目的是规划 |
| DINO-WM | 理解器 | ⚠️ 也被用来做规划，但核心贡献是表征学习 |

判断标准：**这篇论文的核心贡献在解决什么问题？** 按主要贡献归类，次要功能用 tag 标注。

- 优点：3 个词投资人秒懂、直接对应投资问题（"这条线在赌什么"）
- 缺点：C+D 合并丢失了 Latent vs Object-Centric 的区分度
- 补偿方案：在 Topic View 展开时细分（理解器 → 特征预测派 vs 物体发现派）

### 方案 C：按功能阶段分（来自综述 Figure）

```
Simulation → Planning → Decision-Making
```

- 结论：**不推荐**。这是 pipeline 分解，不是互斥分类。Dreamer 同时做了三个阶段，放不进一个格子。

---

## 赛道维度（颜色编码，与 Lane 正交）

| 赛道 | 代表 | 优先级 |
|------|------|--------|
| 多模态视频生成 | Sora, Wan, Cosmos, Gen-3 | P0 |
| 自动驾驶 | GAIA-1, DriveVLA, UniWorld | P0 |
| 具身机器人 | Dreamer, TD-MPC, TesserAct, VLA | P0 |
| 空间智能 | JEPA, World Labs, LRM | P0 |
| 3D 游戏/VR | Genie 2, Oasis, GameNGen | P0 |
| 无人机 | — | P2 |

---

## Era 维度（横轴时间）

| Era | 时间 | 特征 | 分水岭事件 |
|-----|------|------|-----------|
| 潜动力学 | 2018-2023 | 学习环境内部表征 | RSSM 成熟、JEPA 起步 |
| 生成式仿真 | 2024-2025 | 大规模视频预训练做世界仿真 | Sora 发布（diffusion 引入） |
| 因果推理 | 2025- | 物理建模、长程一致性 | 待观察 |

> Kai 判断：分水岭是 diffusion 的引入（2024 前后）。Era 划分应倒推而非预设（Thomas 反馈）。

---

## 跨 Lane 融合趋势

- **仿真器 + 规划器 → VLA**：将视频生成能力转化为动作（DriveVLA）
- **理解器内部分化 → 结构化潜空间**：高效规划 + 物体级因果推断

---

## 待团队收敛的决策

1. 选方案 A（换 label）还是方案 B（3 Lane）？
2. 如果选 B，边界 case 的判断标准大家认不认（"按主要贡献归类"）？
3. Era 划分是预设还是倒推？暂时先用 Kai 的 diffusion 分水岭，后续数据量大了再校准？
