论文题目：Learning to Model the World: A Survey of World Models in Artificial Intelligence
论文地址：https://www.techrxiv.org/doi/full/10.36227/techrxiv.177274570.09578608/v1

[x] 按建模方式分：4 条技术路线，维度统一（怎么表征世界）— 已实现
[x] 按赛道分：筛选器（Track filter）— 已实现
[x] 颜色 = Player（机构）— 已实现（7家 + Other 灰色）
[x] 时间轴可拖拽伸缩 — 已实现

---
## 前端实现状态

### 视觉编码（已实现）
- **颜色** = Player（机构）：DeepMind #4285F4 / Meta #8B5CF6 / OpenAI #10A37F / NVIDIA #76B900 / Physical Intelligence #E04E39 / UC Berkeley #FDB515 / Wayve #6B21A8 / Other #9CA3AF
- **筛选器** = Track（赛道）：Multimodal Video / Autonomous Driving / Embodied Robotics / Spatial Intelligence / 3D Games/VR
- **位置** = Lane(纵轴) × 时间(横轴)

### 时间轴交互（已实现）
- 年份分割线可拖拽，拖动时**左侧所有年份等比缩放，右侧所有年份等比缩放**
- 用途：2023 年以前论文稀疏，用户压缩早期给后期留更多空间
- 拖拽时视觉反馈：分割线变蓝

---
## 时间维度（横轴）— 从数据倒推，不预设

设计原则：Era 不是主观定义的"时代标签"，而是从 Lane 活跃度数据中倒推出来的阅读辅助线。
做法：按年份统计各 Lane 的论文量 → 找"注意力迁移"的拐点 → 拐点即分水岭。

目前可观察到的事件锚点（待数据验证）：

| 事件锚点 | 年份 | 发生了什么 | 对 Lane 活跃度的影响 |
|---------|------|-----------|-------------------|
| Dreamer/PlaNet 发表 | 2019 | RL-Based WM 成为主流范式 | Lane 2 主导期开始 |
| I-JEPA 发布 | 2023 | 潜空间预测路线正式提出 | Lane 3 开始活跃 |
| Sora 发布 | 2024.02 | 视频生成=世界模拟器叙事确立 | Lane 1 爆发（Diffusion 大规模引入） |
| RT-2 / π0 融资潮 | 2023-2024 | VLA 端到端路线产业化 | Lane 4 独立成势 |

如何验证：用后端论文数据按年份×Lane 画堆叠柱状图，如果能看出明显的"某 Lane 在某年论文量激增 + 另一 Lane 相对减少"，分水岭就从数据里直接读出来。

注意：不同 Lane 视角看到的分水岭不同，产品不强行统一为一套 Era。图上呈现 Lane 活跃度曲线本身，事件锚点作为轻量标注辅助阅读。

---
## 范式维度（纵轴）— 按建模方式分 4 Lane（前端顺序：上→下）

## Lane 1：Video-Generative（视频生成式）—— "直接生成像素级世界"

- 核心问题：能不能生成一个足够真的环境，替代现实世界做训练/测试/内容创作？
- 赌什么：Scaling Law — 视频数据喂够多、模型够大，物理理解会自动涌现。
- 投资逻辑：数字孪生、内容生成平台、仿真 — 替代真实数据收集的成本。已有商业落地。

- 架构分类（一级，按生成范式）→ 前端 row：
  - **Diffusion-based** `diffusion_video`：Sora (OpenAI, 2024)、Gen-3 Alpha (Runway, 2024)、Wan (Alibaba, 2025)、Cosmos (NVIDIA, 2025)、Oasis (2024)、GameNGen (Google, 2024)、Drive-WM (NVIDIA, 2024)、Vista (NVIDIA, 2024)。
  - **Autoregressive** `autoregressive_video`：Emu3 (智源/BAAI, 2024)、LWM (UC Berkeley, 2024)、Genie 2 (DeepMind, 2024)、iVideoGPT (2025)。
  - **3DGS / NeRF** `3dgs_nerf`：Text2Room (2023)、4D-fy (2024)、WonderWorld (2025)、FalconWing (2025)、LiDARCrafter (2025)。Gaussian Splat/NeRF 做 3D 世界建模。

- 能力/应用标签（二级，正交于架构）：
  - `可交互`：支持 action→环境响应的闭环（Genie 2, Oasis, GameNGen）
  - `3D/4D 几何一致`：引入几何先验解决物理崩溃（Text2Room, 4D-fy）
  - `具身仿真`：为机器人生成训练环境（TesserAct 2025, Vid2World 2025）

- 关键瓶颈：物理一致性（长时间生成会崩）、可控性（条件精准控制）、交互性。
- 收敛信号：2024+ 几乎全部在 Sora 架构（DiT + Diffusion）上迭代，自回归路线在追赶。

---

## Lane 2：Latent-Space（潜空间预测）—— "不画画，但懂物理和因果"

- 核心问题：能不能在不重建像素的前提下，在特征空间捕捉物理结构与因果？
- 赌什么：Inductive Bias — 光靠数据量不行，必须把物理结构/因果关系作为先验写进架构。
- 投资逻辑：AGI 基础设施 — LeCun 押注方向。如果成了，是所有上层应用的底座。风险高、回报大、周期长。

- 架构分类（一级，按表征学习方式）→ 前端 row：
  - **JEPA-based** `jepa_based`：I-JEPA (Meta AI, 2023)、V-JEPA 2 (Meta AI, 2025)、seq-JEPA (Meta AI, 2025)。
  - **DINO-based** `dino_based`：DINO-WM (NYU/Meta, 2025)、DINO-World (2024)。
  - **Slot-based** `slot_based`：SlotAttention (Google, 2020)、SlotFormer (NVIDIA, 2023)、Dyn-O (NeurIPS, 2025)。

- 能力/应用标签（二级，正交于架构）：
  - `因果推理`：结构化因果关系建模（CausalWorld, CarFormer ECCV 2024）
  - `组合泛化`：未见组合的零样本推理能力

- 关键瓶颈：能不能 scale？特征空间的物理是否足够精确？离部署还有多远？
- 收敛信号：Meta 在 JEPA 路线上持续 all-in（I-JEPA → V-JEPA → V-JEPA 2），但尚未形成行业共识。

---

## Lane 3：RL-Based（想象力规划）—— "在脑子里想 N 步选最优"

- 核心问题：能不能在想象中模拟多条未来轨迹，选最优的那条执行？减少真实交互成本。
- 赌什么：Sample Efficiency — 不需要真实世界试错一万次，在想象中模拟就够学会。
- 投资逻辑：具身智能数据效率 — 在数据稀缺的新任务/新机器人上唯一出路。

- 架构分类（一级，按状态建模方式）→ 前端 row：
  - **RSSM-based** `rssm_based`：PlaNet → Dreamer V1-V3 (Google DeepMind, 2019-2025)、NavMorph (2024)。
  - **MPC-based** `mpc_based`：TD-MPC / TD-MPC2 (UC San Diego, 2022-2024)、PWM (ICLR, 2025)。
  - **Diffusion Planning** `diffusion_planning`：Diffuser (UC Berkeley, 2022)、Decision Diffuser (2023)、PIVOT-R (2024)。用 diffusion 做轨迹规划，不生成像素。

- 能力/应用标签（二级，正交于架构）：
  - `层次化规划`：多时间尺度想象（Hieros 2024, THICK 2024）
  - `具身应用`：面向机器人（RoboDreamer 2024, FlowDreamer 2025, ViPRA 2025）
  - `多智能体`：多体协作想象（DIMA 2025, CoWorld 2024）

- 关键瓶颈：想象力 fidelity、长程规划精度急剧下降（50步+）、Sim2Real gap。
- 收敛信号：DreamerV3 实现跨领域通用性，但正在被 VLA 路线挑战"是否还需要显式 world model"。

---

## Lane 4：VLA（Vision-Language-Action）—— "感知-理解-行动，端到端一步到位"

- 核心问题：能不能跳过显式 world model，直接从感知到动作端到端闭环？
- 赌什么：Foundation Model Scaling — 足够大的多模态模型会隐式学会世界模型，不需要单独建。
- 投资逻辑：具身智能的产业化路径 — 泛化强、部署快、有大厂资源支撑。2024 后融资最密集的方向。

- 架构分类（一级，按融合方式）→ 前端 row：
  - **LLM/VLM + Action** `vla_llm`：RT-2 (Google DeepMind, 2023)、Octo (UC Berkeley, 2024)。
  - **Diffusion Policy** `vla_diffusion`：π0 (Physical Intelligence, 2024)、Diffusion Policy (Columbia, 2023)、X-Mobility (2025)。
  - **Driving VLA** `vla_driving`：DriveVLA (2024)、UniWorld (2024)、GAIA-1 (Wayve, 2023)、CopilotD4 (NVIDIA, 2024)、Think2Drive (2024)。

- 能力/应用标签（二级，正交于架构）：
  - `语言条件化`：用自然语言指令控制（RT-2, Octo）
  - `长程任务`：多步骤复杂任务执行（π0）
  - `自动驾驶`：端到端驾驶决策（DriveVLA, GAIA-1）

- 关键瓶颈：需要巨量标注数据、黑盒不可解释、安全性验证困难。
- 收敛信号：产业侧快速收敛 — Google/Physical Intelligence/Wayve 全部 all-in，2024 年融资超 $2B。与 Lane 2（具身 RL）形成最核心的路线竞争。

---

## 赛道维度（Track 筛选器，与 Lane 正交）— 已实现为右侧 filter

| Track（前端值） | 代表论文/产品 | 主要 Lane | 优先级 |
|------|-------------|-----------|--------|
| Multimodal Video | Sora, Wan, Cosmos, Gen-3, LWM | Video-Generative | P0 |
| Autonomous Driving | DriveVLA, GAIA-1, UniWorld | VLA + Video-Generative | P0 |
| Embodied Robotics | π0, RT-2, Dreamer, TD-MPC, PlaNet | VLA + RL-Based | P0 |
| Spatial Intelligence | V-JEPA, DINO-WM, SlotAttention | Latent-Space | P0 |
| 3D Games/VR | Genie 2, Oasis, GameNGen | Video-Generative | P0 |
| （无人机不单设 track） | — | — | P2 (少看) |

---

## 核心竞争关系

### 1. 像素派 vs 特征派（Lane 1 vs Lane 3）
- 视频生成式（Sora 路线）：暴力 scale 视频生成来"涌现"物理理解。
- 潜空间预测（JEPA 路线）：先学物理结构再做决策。
- 投资判断：像素派已有商业落地（视频生成、游戏），特征派更可能是 AGI 底座但离钱远。

### 2. VLA vs 具身 RL（Lane 4 vs Lane 2）— 最核心路线之争
- VLA：不需要显式 world model，大模型端到端干。类比 NLP 里 BERT 取代了 parsing tree。
- 具身 RL：显式建模世界→想象→规划。数据效率高但泛化难。
- 现状：产业侧 VLA 在赢（资金密集、大厂 all-in），但数据稀缺场景 RL 仍是唯一出路。
- **这条线现在收敛不了 — 这就是 World Model 领域最核心的路线分歧。**

### 3. 跨 Lane 融合趋势
- Lane 1 + Lane 4：视频生成能力 → 直接驱动动作（DriveVLA 将视频预测转化为驾驶）
- Lane 3 + Lane 2：结构化潜空间 → 高效规划 + 物体级因果推断
- Lane 1 + Lane 2：视频 world model 提供想象环境给 RL agent 训练（Vid2World）
