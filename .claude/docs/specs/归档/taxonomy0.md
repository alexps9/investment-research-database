论文题目：Learning to Model the World: A Survey of World Models in Artificial Intelligence，论文地址：https://www.techrxiv.org/doi/full/10.36227/techrxiv.177274570.09578608/v1
[] 按范式分：技术往哪收敛， 对应稀缺性 + 成长性。分不同泳道呈现
现有范式：Observation-Level Generative、Latent space、RL以及Object-Centric wms
[] 按赛道分：钱在哪里谁在赢，对应规模 + 壁垒，用不同颜色表征

---
时间/时代维度分类（横轴）
- Era 1：潜动力学与初步控制 (2018-2023)
  - 重心：学习环境的内部表征，捕获潜在结构和不确定性。 
  - 核心事件：RSSM 模型的成熟 、潜空间自监督学习（JEPA）的起步 。
- Era 2：生成式仿真与多模态爆发 (2024-2025)
  - 重心：利用大规模视频预训练构建“世界模拟器”，实现高保真环境仿真。 
  - 核心事件：Sora 定义视频模型为模拟器 、3D/4D 观测在具身领域的应用 。
- Era 3：因果推理与自进化演进 (2025-)
  - 重心：从统计插值转向物理建模，强化长程一致性和物理可解释性。 
  - 核心事件：引入Self-play与Symbolic Knowledge 。
  
范式维度（纵轴）
Lane 1：Observation-Level Generative
- 核心问题：如何直接预测高维观测（像素/视频/3D）以实现可控的写实仿真？ 
- 代表架构与 Player：
  - 扩散模型派 (Diffusion)：Sora (OpenAI, 2024)、Gen-3 Alpha (Runway, 2024)、Wan (Alibaba, 2025)。
  - 自回归派 (Autoregressive)：Emu3 (智源/BAAI, 2024)、LWM (UC Berkeley, 2024)。
- 竞争与改进：为了解决 2D 像素预测导致的物理崩溃，衍生出了引入几何先验的 4D-fy 和 Text2Room 等 3D/4D 建模路径。 
Lane 2：Latent-Space WMs)—— 解决“如何高效规划”
- 核心问题：如何在不重建像素的前提下，在压缩空间内捕捉语义结构与运动逻辑？ 
- 代表架构与 Player：
  - JEPA 系列：I-JEPA (Meta AI, 2023)、V-JEPA 2 (Meta AI, 2025)、seq-JEPA (Meta AI, 2025)。 
  - 特征预训练派：DINO-WM (NYU/Meta, 2025)、DINO-World (arXiv, 2024)。 
- 竞争与改进：作为 Lane 1 的强力竞争对手，这类模型牺牲了图像生成质量，换取了极高的预测与规划效率，更适合端到端的智能体决策。 

- Lane 3：RL-Based WMs—— 解决“如何闭环决策”
- 核心问题：如何通过“想象回滚”优化策略，在减少现实交互的同时提升决策鲁棒性？ 
- 代表架构与 Player：
  - RSSM 体系：Dreamer V1-V3 (Google DeepMind, 2019-2025)。 
  - 高效控制派：TD-MPC2 (UC San Diego, 2024)、PWM (ICLR, 2025)。
- 竞争与改进：通过 DreamerV3 实现了在跨领域任务中的通用性，目前正与 Lane 1 的视频生成能力融合，演进为 VLA (视觉-语言-动作) 架构。 

Lane 4：对象导向模型 (Object-Centric WMs) —— 解决“如何因果推理”
- 核心问题：如何将环境拆解为独立的实体及其交互，以解决像素建模对关键小实体的忽视？ 
- 代表架构与 Player：
  - Slot 机制派：SlotAttention (Google, 2020)、SlotFormer (NVIDIA, 2023)、Dyn-O (NeurIPS, 2025)。 
  - 自动驾驶应用：CarFormer (ECCV, 2024)。 
- 竞争与改进：追求更强的可解释性与组合泛化，是未来“解释原因”而非仅仅“预测内容”的关键路径。 

赛道维度
赛道
代表论文/产品
优先级

多模态文生/图生视频
Sora , Wan , Cosmos, Gen-3 
P0

自动驾驶
GAIA-1 , DriveVLA , UniWorld 
P0

具身机器人
Dreamer , TD-MPC , TesserAct , VLA 
P0

空间智能
JEPA (I-JEPA/V-JEPA), World Labs, LRM
P0

3D 游戏/VR
Genie 2 , Oasis , GameNGen 
P0

无人机
—
P2 (少看)


---
竞争
1. 像素派与特征派的并列竞争： 在 Era 2 中，Lane 1（追求视觉完美）与 Lane 2（追求语义逻辑）处于强烈的并列竞争状态。投资视角下，前者更倾向于赋能内容创作和仿真平台，而后者更倾向于嵌入机器人大脑进行实时决策。 
2. 从“分散模拟”向“统一接口”的收敛：
3. 随着 Era 3 的到来，原本各司其职的泳道正在发生跨泳道融合。
  - Lane 1 + Lane 3：催生了 VLA 模型（如 DriveVLA），将大规模像素预测能力直接转化为驾驶动作。 
  - Lane 2 + Lane 4：正在结合为“结构化潜空间”，试图在高效规划的同时保持对独立物体的精准因果推断。 
  