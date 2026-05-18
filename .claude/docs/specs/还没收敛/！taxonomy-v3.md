# World Model 技术路线图谱 — 分类框架 v3

> 基于 taxonomy-v2 + 2026.05 新综述讨论后的最终方案
> 核心变化：Lane 1 明确终点是 Embodied；Lane 4 扩展加 Symbolic；新增 integration 属性标签

---

## 设计原则

投资人的核心问题：**"做 embodied world model，是否必须先 scale 一个 foundation video model？"**

图谱主轴 = 实现具身智能的不同 foundation 路径，按对 video generation 的依赖程度从高到低排列。

---

## 前端视觉编码

| 通道 | 编码含义 |
|------|---------|
| 纵轴位置（Lane） | 4 路径：Video→Embodied / Latent / RL / End-to-End |
| 横轴 | 时间 |
| 颜色 | Player（机构） |
| 节点大小 | Impact（连续值，log min-max + override） |
| **节点形状** | **circle = Foundation（提出新架构/新能力），square = Adaptation（在 foundation 上做应用/改进）** |
| 筛选器 | Track（赛道） |
| 连线 | builds_on（adaptation → foundation 的依赖关系） / competes / enables |
| tooltip 标签 | integration（IDM/Single-backbone/MoE/Simulator/Evaluator） |

---

## Lane 1：Video Foundation → Embodied —— "先 scale 视频，再接动作"

- 核心问题：能不能先把视频生成 scale 到足够好，让模型"涌现"物理理解，再 adapt 到机器人？
- 赌什么：Scaling Law — 视频数据喂够多、模型够大，物理直觉会自动涌现，然后可以迁移到 embodied。
- 投资逻辑：当前主流共识路径。Cosmos、GigaWorld、Genie Envisioner 都走这条路。已有商业落地（仿真数据合成）。

### Row 分类（按生成范式）

Adaptation 论文按依赖的 foundation backbone 归入对应 Row，通过 builds_on 连线指向 foundation 节点。

- **Diffusion-based** `diffusion_video`
  - Foundation（○）：Cosmos (NVIDIA, 2025)、Cosmos Predict 2.5 (NVIDIA, 2025)、Wan 2.2 (Alibaba, 2025)、GigaWorld-0 (极佳视界, 2025)、Drive-WM (NVIDIA, 2024)、Vista (NVIDIA, 2024)、DreamGen (NVIDIA, 2025)、IRASim (ByteDance, 2025)、DreamDojo (NVIDIA, 2026)。
  - Adaptation（□）：Vidarc → Wan 2.2 [idm]、Cosmos Policy → Cosmos [single_backbone]、UWM [single_backbone]、UVA [single_backbone]、DreamZero/WAM [single_backbone]、Vid2World → Diffusion WM [simulator]、DiWA [simulator]、WMPO [simulator]、WorldEval [evaluator]、TC-IDM [idm]、VPP [idm]、Gen2Act [idm]、V2A [idm]、Video2Act [idm]、mimic-video [idm]、LVP [idm]、TesserAct (MIT, 2025)、Ctrl-World (2025)、RoboMaster (Kling, 2025)、GE-Act → DiT [moe]、DiT4DiT [moe]、LDA-1B (PKU, 2026) [moe]、Fast-WAM [moe]、GigaBrain-0.5M → Wan 2.2 [simulator+moe]。

- **Autoregressive** `autoregressive_video`
  - Foundation（○）：Genie 2 (DeepMind, 2024)、Genie Envisioner (AgibotTech, 2025) → LTX-Video [domain adaptation]、iVideoGPT (2025)、LWM (UC Berkeley, 2024)、CogVideoX (THU, 2025)。
  - Adaptation（□）：GR-1 → GPT-style video [idm]、VidMan [idm]、Say Dream and Act [idm]、VideoVLA [single_backbone]、GigaWorld-Policy → GigaWorld [single_backbone]、UD-VLA [single_backbone]、Motus (THU, 2025) [moe]、BagelVLA [moe]、STARRY [moe]、World-Env [simulator]、Veo+Gemini (Google, 2025) [evaluator]。

- **3DGS / NeRF** `3dgs_nerf`
  - Foundation（○）：WonderWorld (2025)、4D-fy (2024)、Kinema4D (2026)。
  - Adaptation（□）：FalconWing (2025)、LiDARCrafter (2025)。

### Integration 属性说明

`integration` 是论文级 tooltip 标签，不影响 Row 布局。论文按 backbone 架构归 Row，按连接方式标 integration。

| Integration | 说明 | 在 Row 中的标记 |
|------|------|------|
| `idm` | 先生成视频，再 inverse dynamics 翻译成动作 | [idm] |
| `single_backbone` | 一个模型同时生成视频和动作 | [single_backbone] |
| `moe` | 视频专家 + 动作专家分离但频繁交互 | [moe] |
| `simulator` | 用 video WM 做仿真环境给 RL 训练 | [simulator] |
| `evaluator` | rollout 打分/排序候选动作 | [evaluator] |
| — | 纯 Foundation，不直接接 policy | 无标记 |

### 归类修正（从综述原始归类中移出 Lane 1）

| 论文 | 综述原归类 | 实际归属 | 原因 |
|------|-----------|---------|------|
| FRAPPE (2026) | Lane 1 MoE | **Lane 2 `latent_policy`** | 不依赖 video generation，对齐 CLIP/DINOv2 特征空间 |
| VLA-MBPO (2026) | Lane 1 Simulator | **Lane 4** | 用多模态大模型 (Bagel) 做 WM，不走视频生成 |
| DayDreamer (2023) | Lane 1 Simulator | **Lane 3 `rssm_based`** | 用 RSSM 不是 video model |

### 关键瓶颈
- 物理一致性：长时间生成会崩
- action faithfulness：visually plausible ≠ action-consistent
- 实时性：生成一帧太慢，难做高频控制

### 收敛信号
- 2024+ Foundation 几乎全在 DiT + Diffusion 架构上迭代
- Integration 方法尚未收敛（IDM/Single-backbone/MoE 都在试）
- MoE 工程上最稳（GE-Act、LDA-1B），有可能胜出
- Single-backbone 论文爆发最快（2025-2026 密集出现）

---

## Lane 2：Latent Prediction —— "不画画，但懂物理和因果"

- 核心问题：能不能在不重建像素的前提下，在特征空间捕捉物理结构与因果？
- 赌什么：Inductive Bias — 光靠数据量不行，必须把物理结构/因果关系作为先验写进架构。
- 投资逻辑：AGI 基础设施 — LeCun 押注方向。如果成了，是所有上层应用的底座。风险高、回报大、周期长。训练成本比 video diffusion 低一个数量级。

### Row 分类（按表征学习方式）

- **JEPA-based** `jepa_based`：I-JEPA (Meta AI, 2023)、V-JEPA 2 (Meta AI, 2025)、V-JEPA 2.1 (Meta, 2026)、seq-JEPA (Meta AI, 2025)、LeWorldModel (2026)。
- **DINO-based** `dino_based`：DINO-WM (NYU/Meta, 2025)、DINO-World (2024)。
- **Slot-based** `slot_based`：SlotAttention (Google, 2020)、SlotFormer (NVIDIA, 2023)、Dyn-O (NeurIPS, 2025)。
- **Latent-space Policy** `latent_policy`：在潜空间做 action-conditioned 预测。FLARE (NVIDIA, 2025)、VLA-JEPA (2026)、JEPA-VLA (2026)、VISTA-WM (2026)、World Guidance/WoG (2026)、DIAL (2026)、AIM (2026)、DexWorldModel (2026)、FRAPPE (2026) [从 Lane 1 MoE 修正归类，实际对齐 CLIP/DINO 特征空间]。

### 关键瓶颈
- 能不能 scale？特征空间的物理是否足够精确？
- 叙事不够性感、demo 不够 impressive（融资劣势）
- 离真实部署还有多远？

### 收敛信号
- Meta 在 JEPA 路线上持续 all-in（I-JEPA → V-JEPA → V-JEPA 2 → V-JEPA 2.1）
- 2026 年 latent policy 论文爆发（FLARE、VLA-JEPA、JEPA-VLA、DIAL、AIM）
- 如果突然 DeepMind/NVIDIA 也开始做 JEPA → 真正的热门信号
- NVIDIA FLARE 已经在做 → 信号已出现

---

## Lane 3：RL Imagination —— "在脑子里想 N 步选最优"

- 核心问题：能不能在想象中模拟多条未来轨迹，选最优的那条执行？
- 赌什么：Sample Efficiency — 不需要真实世界试错一万次，在想象中模拟就够学会。
- 投资逻辑：数据稀缺场景的唯一出路。新任务/新机器人没有海量演示数据时，只能靠想象力规划。

### Row 分类（按状态建模方式）

- **RSSM-based** `rssm_based`：PlaNet (Google, 2019) → Dreamer V1 (2020) → V2 (2021) → V3 (DeepMind, 2023→2025)、NavMorph (2024)、DayDreamer (2023)。
- **MPC-based** `mpc_based`：TD-MPC (UC San Diego, 2022)、TD-MPC2 (2024)、PWM (ICLR, 2025)。
- **Diffusion Planning** `diffusion_planning`：Diffuser (UC Berkeley, 2022)、Decision Diffuser (2023)、PIVOT-R (2024)。用 diffusion 做轨迹规划，不生成像素。

### 关键瓶颈
- 想象力 fidelity：长程规划精度急剧下降（50步+）
- Sim-to-Real gap：想象中学到的，真实世界不一定适用
- 正在被 VLA "你还需要显式 world model 吗？" 路线挑战

### 收敛信号
- DreamerV3 实现跨领域通用性（单一架构跑多个任务）
- TD-MPC2 在连续控制上 SOTA
- 但产业侧关注度不如 Lane 1 和 Lane 4，资金密度低

---

## Lane 4：End-to-End / Symbolic —— "跳过显式 WM，或在符号层面建模"

- 核心问题：能不能跳过显式 world model，直接从感知到动作端到端闭环？或者在"物体、关系、动作"符号层面做推理？
- 赌什么：Foundation Model Scaling（端到端派）— 足够大的多模态模型会隐式学会世界模型。Compositional Reasoning（符号派）— 长程任务的瓶颈在任务分解而非像素预测。
- 投资逻辑：端到端派是当前融资最密集的方向（π0 $4亿、Figure $6.75亿）。符号派是长程任务的潜在突破口。

### Row 分类

- **LLM/VLM + Action** `vla_llm`：RT-2 (Google DeepMind, 2023)、Octo (UC Berkeley, 2024)、OpenVLA (2024)。
- **Diffusion Policy** `vla_diffusion`：π0 (Physical Intelligence, 2024)、π0.5 (2025)、Diffusion Policy (Columbia, 2023)、X-Mobility (2025)。
- **Unified VLA** `unified_vla`：训练时预测未来画面，部署时只出动作。GR-1 (ByteDance, 2024)、GR-2 (ByteDance, 2024)、UP-VLA (2025)、DreamVLA (2025)、UniVLA (2025)、Genie Envisioner (AgibotTech, 2025)、CoWVLA (2026)、F1 (2025)、RynnVLA-002 (Alibaba, 2025)、InternVLA-A1 (2026)、HALO (2026)、OA-WAM (2026)。
- **Driving VLA** `vla_driving`：DriveVLA (2024)、UniWorld (2024)、GAIA-1 (Wayve, 2023)、Think2Drive (2024)、VLA-MBPO (2026) [从 Lane 1 Simulator 修正归类，用多模态大模型做 WM]。
- **Symbolic World Model** `symbolic`：在"物体、关系、动作"抽象符号层面建模，做任务分解和 compositional reasoning。VisualPredicator (2024)、ExoPredicator (2025)。需要预先定义符号体系，grounding 脆弱，但和 neuro-symbolic 混合可能是长程任务突破口。

### 关键瓶颈
- 需要巨量标注数据（端到端派）
- 黑盒不可解释，安全性验证困难
- 精细操控（<1mm）靠端到端还不够
- 符号 grounding 脆弱（符号派）

### 收敛信号
- 产业侧快速收敛：Google/Physical Intelligence/Wayve 全部 all-in 端到端
- 2024 年具身AI融资超 $2B，绝大部分给了这条路线
- Unified VLA 爆发（2025-2026 十余篇），成为 End-to-End 内最活跃子方向
- 与 Lane 3（RL Imagination）形成最核心的路线竞争
- 最终架构大概率分层：VLA 做高层规划 + WM/RL 做底层控制

---

## Track 筛选器（与 Lane 正交）

| Track | 代表 | 说明 |
|-------|------|------|
| Embodied Robotics | π0, Dreamer, TD-MPC, GigaWorld, FLARE | 机械臂/人形机器人 |
| Autonomous Driving | DriveVLA, GAIA-1, Vista, Drive-WM | 自动驾驶 |
| Multimodal Video | Sora, Wan, Gen-3, Emu3 | 纯内容生成（不同客户/估值逻辑） |
| Spatial Intelligence | V-JEPA 2, DINO-WM, SlotAttention | 空间理解 |
| 3D Games/VR | Genie 2, Oasis, GameNGen | 可交互虚拟世界 |

---

## 核心竞争关系

### 1. Lane 1 vs Lane 2+3+4：foundation video model 是不是必经之路？

这是本图谱要回答的首要投资问题。
- Lane 1（Video→Embodied）= 主流共识：先 scale video，再 adapt
- Lane 2（Latent）+ Lane 3（RL）+ Lane 4（End-to-End）= 可以绕过 video foundation 的替代路径
- 判断标准：看 Lane 2/3/4 的效果能不能追上 Lane 1；看 Lane 1 的 adaptation 是否真的比不走视频更好

### 2. Lane 4 vs Lane 3：端到端 vs 显式想象

产业侧最核心的路线之争。
- Lane 4（End-to-End）：大模型暴力 scale，隐式学会世界理解
- Lane 3（RL Imagination）：显式建模→想象→规划，数据效率高
- 现状：产业侧 Lane 4 在赢（资金密集），但数据稀缺场景 Lane 3 仍是唯一出路
- 大概率结局：分层融合（VLA 做高层 + WM 做底层）

### 3. 跨 Lane 融合趋势

- Lane 1 + Lane 4：视频 backbone pretrain → 给 VLA 提供 foundation（π0 的 flow matching 可以理解为视频生成能力的迁移）
- Lane 1 + Lane 3：视频 WM 做仿真环境给 RL agent 训练（Vid2World）
- Lane 2 + Lane 3：潜空间结构 → 高效想象规划（JEPA 做 Dreamer 的 encoder）

---

## Foundation vs Adaptation 判定标准

| 类型 | 形状 | 判定 | 举例 |
|------|------|------|------|
| Foundation | ○ circle | 提出新架构或新能力，被后续论文 builds_on | Cosmos、Genie 2、I-JEPA、Dreamer V3、π0 |
| Adaptation | □ square | 在已有 foundation 上做应用/改进/接入 policy | Vidarc、GR-1、Cosmos Policy、GigaBrain |

灰色地带：Genie Envisioner 在 LTX-Video 上做了完整 domain adaptation（GE-Base + GE-Act + GE-Sim 三件套），本质介于两者之间。归为 Foundation（○）因为它自己也被后续论文引用。

---

## 与 v2 的关键区别总结

| 维度 | v2 | v3 |
|------|-----|-----|
| Lane 1 定义 | "Video-Generative"（太宽泛） | "Video Foundation → Embodied"（明确终点是机器人） |
| Lane 4 定义 | "VLA"（只有端到端） | "End-to-End / Symbolic"（加入符号派） |
| Lane 4 新增 Row | — | unified_vla（爆发最快）、symbolic |
| Foundation/Adaptation | 没有区分 | **形状编码：○ = Foundation, □ = Adaptation**；adaptation 按 backbone 归入对应 Row，builds_on 连向 foundation |
| Integration 论文 | 独立分类表 | 归入对应 Row + tooltip 标签（idm/single_backbone/moe/simulator/evaluator） |
| 论文数量 | ~103 | ~160+（从综述 README 补充） |
| 纯内容生成 | 和具身混在Lane 1 | 降级为Track筛选器，不占泳道 |
| 图谱能回答的核心问题 | 各范式分别在做什么 | foundation video model是不是必经之路 |
