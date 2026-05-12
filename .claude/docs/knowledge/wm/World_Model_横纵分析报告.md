# World Model：技术范式与投资方向

> 研究时间：2026年5月 | 所属领域：AI / 具身智能 / 视频生成 | 研究对象类型：技术范式

## 一句话定义

World Model 是让 AI 在内部模拟世界运转、不需要真实交互就能预测未来状态的技术范式——本质是「编码→潜空间建模→解码/预测」的三段式架构。

## 二、纵向分析：从思想实验到产业爆发

### 2.1 思想根源（1943-2017）

World Model 这个词在 2018 年才正式进入 AI 研究的主流视野，但它背后的思想源头远比这更早。

1943年，英国心理学家 Kenneth Craik 在《The Nature of Explanation》中提出了「心智模型」的概念：人脑通过构建外部世界的内部模型来预测事件、做出决策。这个洞察直接启发了后来认知科学中的 mental simulation 理论。

在强化学习领域，1991年 Richard Sutton 提出 Dyna 架构——智能体不仅从真实经验中学习，还利用一个学到的环境模型生成「模拟经验」来加速学习。这是 model-based RL 的先驱，也是 World Model 在 AI 中最直接的前身。

2017年，DeepMind 发表 Imagination-Augmented Agents，让智能体用神经网络学习的环境模型来「想象」行动后果。这已经非常接近后来 World Model 的完整形态了——但还差最后一步：完全在想象中训练策略。

### 2.2 开山之作（2018）

2018年，David Ha 和 Jürgen Schmidhuber 发表论文「World Models」（arXiv:1803.10122）。

架构很优雅：V（视觉模型，VAE 编码器）+ M（记忆模型，MDN-RNN 预测未来）+ C（控制器，一个简单的线性网络）。智能体先在真实环境中收集数据训练 V 和 M，然后完全在 M 生成的「梦境」中训练 C。

在 VizDoom 和 CarRacing 环境中，这套方法证明了：不需要与真实世界交互，仅在想象中就能学会策略。

为什么是 2018 年？因为 VAE（2013）和 GAN（2014）让潜空间表示成为可能，RNN/LSTM 的序列建模已经成熟，深度 RL 在 Atari/Go 上的成功暴露了 model-free 方法的样本效率问题——World Models 是这些条件汇聚后的自然产物。

### 2.3 Dreamer 时代：从玩具到通用（2019-2023）

Ha & Schmidhuber 点了火，但真正把 World Model 推到 model-based RL 的 SOTA 位置的，是 Danijar Hafner。

**2019 PlaNet**：提出 RSSM（Recurrent State Space Model），将确定性状态和随机性状态结合。解决了纯确定性模型无法表达不确定性、纯随机模型不够稳定的两难。

**2020 Dreamer v1**：在 RSSM 世界模型中用 actor-critic 方法学策略。在 DeepMind Control Suite 上首次让 model-based 方法达到 SOTA 级表现。

**2021 Dreamer v2**：引入离散潜空间（categorical latents）。关键突破——在 Atari 上首次超越 model-free 方法。这证明了世界模型不只是「理论上优雅」，在实际 benchmark 上也能打赢。

**2023 Dreamer v3**：一个统一算法，无需调参即可跨域工作——从 Atari 到 Minecraft 钻石挑战全部搞定。这标志着 RL-based World Model 从「每个任务调一次」走向了真正的通用性。

与此同时，UC Berkeley 的 TD-MPC 系列（2022-2023）走了另一条路：在潜空间中结合 temporal difference learning 和 model predictive control。TD-MPC2（2023）用一个世界模型处理 104 种不同任务。

到 2023 年初，RL-based World Model 这个分支已经很成熟了。但故事才刚开始——因为另一条全新的路线正在酝酿。

### 2.4 范式爆发：四条路线并行（2023-2024）

2023 年是 World Model 从学术走向产业的分水岭。三个事件改变了格局：

**GAIA-1（Wayve，2023年中）**：第一个大规模自动驾驶世界模型。输入视频+文本+动作，预测未来驾驶场景。这是 World Model 从游戏/仿真走向真实世界的第一次大规模尝试。

**UniSim（Google DeepMind，2023年末）**：统一的世界模拟器，通过各种动作类型（相机运动、物体操作、语言指令）进行交互式模拟。展示了世界模型作为通用仿真器的可能性。

**Sora（OpenAI，2024年2月）**：超大规模视频生成模型，OpenAI 直接将其定位为「World Simulator」。技术报告标题就叫「Video generation models as world simulators」。Diffusion Transformer 架构在时空 patch 上训练，展示了惊人的 3D 一致性和物理理解。

Sora 的发布是一个行业转折点。它将「视频生成」和「世界模型」画了等号——虽然这个等号后来被激烈争论（后面会展开），但它确实让 World Model 从一个 RL 社区的小众概念，变成了全球科技产业的焦点词。

到 2024 年底，四条路线已经完全分化：

1. **RL-Based**（Dreamer, TD-MPC）—— 想象力驱动策略学习
2. **视频生成式**（Sora, Cosmos, Wan）—— 像素级世界仿真
3. **潜空间预测**（V-JEPA, DINO-WM）—— 特征空间动力学
4. **VLA 融合**（RT-2, π0, DriveVLA）—— 感知-决策闭环

### 2.5 产业化加速（2024下半年-2025）

2024 年下半年开始，World Model 从论文变成了真金白银。

**V-JEPA（Meta，2024年3月）**：LeCun 路线的正式实现。在特征空间而非像素空间进行预测——不生成视频，只预测高层表征。2025 年初发布 V-JEPA 2，性能大幅提升。

**Genie 2（DeepMind，2024年末）**：从单张图片生成可交互的 3D 世界，支持第一人称视角探索。是「AI 生成可玩游戏」的最强展示。

**World Labs（李飞飞，2024年9月）**：成立即获 2.3 亿美元融资，估值 10 亿美元。专注「空间智能」——从图像生成可导航的 3D 世界。团队包括 Justin Johnson、Ben Mildenhall（NeRF 作者之一）。

**Cosmos（NVIDIA，2025年1月 CES）**：开源世界基础模型，定位为物理 AI 的基础设施。与 Isaac Sim/Omniverse 协同，为机器人和自动驾驶提供合成训练数据。黄仁勋在 CES 和 GTC 重点推介。

**VLA 大爆发（2024-2025）**：Physical Intelligence 的 π0、Google 的 RT-2、开源的 OpenVLA……将视觉-语言-动作统一到一个模型中，世界知识隐式编码在权重里。

到 2025 年中，World Model 已经不是一个学术方向，而是一个数十亿美元级的产业赛道。

## 三、横向分析：六赛道竞争图谱

### 3.1 多模态视频生成

这是商业化最成熟、资本最密集的赛道。

| 玩家 | 技术路线 | 阶段 | 商业化 |
|------|----------|------|--------|
| OpenAI Sora | DiT，时空 patch | 已上线（ChatGPT Plus/Pro） | 付费功能 |
| 阿里 Wan | DiT + 3D VAE + Flow Matching | 已开源（Wan2.1） | 阿里云API + 开源 |
| NVIDIA Cosmos | DiT，面向物理 AI 仿真 | 已开源部分 | 企业客户（卖铲子） |
| Runway Gen-3/4 | 多模态 transformer | 产品成熟 | SaaS订阅，$40亿估值 |
| Google Veo 2 | 扩散+transformer | 已通过 Vertex AI 开放 | Google Cloud API |
| 快手可灵 | 3D VAE + DiT | 产品上线 | API + C端产品 |
| Pika | 侧重易用性 | 2.0已上线 | SaaS订阅，$10亿+估值 |

**格局判断**：技术路线趋同（DiT 成为主流），竞争焦点转向物理一致性、可控性和生态整合。开源（Wan、Cosmos）正在追赶闭源。2025年进入淘汰赛。

### 3.2 自动驾驶

World Model 在自动驾驶中有两个角色：**仿真**（生成训练/测试场景）和**决策**（预测未来辅助规划）。前者已验证价值，后者还在探索。

| 玩家 | 角色 | 路线 | 融资 |
|------|------|------|------|
| Tesla FSD v12+ | 决策（隐式） | 端到端像素到控制 | 上市公司 |
| Wayve GAIA-1 | 仿真+决策 | 显式世界模型 | C轮$10.5亿（软银领投） |
| NVIDIA Cosmos/DriveSim | 仿真 | 平台基础设施 | 内部项目 |
| Waabi | 仿真 | AI-first，可微仿真 | B轮$2亿+ |

**格局判断**：Tesla 凭数据规模和部署量领先（隐式世界模型）；Wayve 是纯 AI 路线领头羊；NVIDIA 作为基础设施通吃。仿真用途已近成熟，决策用途还需 2-3 年验证。

### 3.3 具身机器人

这是 World Model 最被资本追捧的赛道。核心争论：VLA vs 具身 RL。

| 玩家 | 路线 | 阶段 | 融资 |
|------|------|------|------|
| Physical Intelligence π0 | VLA（flow matching + VLM） | Demo/pre-revenue | $4亿，估值$20亿+ |
| Figure AI | 人形机器人 + OpenAI合作 | BMW工厂试点 | B轮$6.75亿，估值$26亿+ |
| Google DeepMind RT-2/Dreamer | VLA + model-based RL | 研究，缩减硬件 | 内部项目 |
| 1X Technologies | 人形NEO + 轮式EVE | EVE少量部署 | $1亿+，OpenAI基金参投 |
| 宇树科技 | 四足+人形，硬件强 | 已量产 | B轮数亿元 |
| 智元机器人 | 软硬一体人形 | 快速迭代 | 累计数十亿元 |

**格局判断**：VLA 正在成为主流共识（π0 是标志），但 World Model/RL 在精细操控方面仍有独特价值。大概率融合：VLA 做高层规划 + World Model 做底层控制。

### 3.4 空间智能

极早期赛道，更像「技术愿景之争」而非商业竞争。

**World Labs（李飞飞）**：从单张图片生成可导航 3D 世界。路线是生成式（NeRF/3DGS + 生成模型）。A轮 $2.3亿，估值 $10亿。

**Meta V-JEPA（LeCun）**：在表征空间预测，不生成像素。路线哲学完全不同——学习世界的结构而非外观。

**核心分歧**：World Labs 认为「能生成可交互 3D 世界 = 理解空间」；LeCun 认为「生成像素是浪费，应在抽象空间理解物理结构」。两条路线可能互补——JEPA 做内部推理，生成式做外部可视化。

**格局判断**：真正的商业价值 2-3 年后才会清晰，可能首先在 AR/VR、建筑设计、影视制作落地。

### 3.5 3D 游戏 / VR

想象力最大但最不成熟的赛道。

| 玩家 | 做了什么 | 进展 |
|------|----------|------|
| DeepMind Genie 2 | 从单张图片生成可交互 3D 世界 | Demo，研究最强 |
| Decart Oasis | 实时生成类 Minecraft 世界 | Demo上线，~20fps | 
| Google GameNGen | 用扩散模型实时模拟 DOOM | 论文，概念验证 |

当前能做到：生成看起来可信的 3D 环境、实时生成简单开放世界、用神经网络替代游戏引擎。

还做不到：AAA 画质、复杂物理交互、长时间一致性、多人交互。

**格局判断**：短期（1-2年）落地场景是快速原型设计和 AI agent 训练环境，而非替代游戏引擎。长期可能引发游戏行业范式变革，但拐点还需 3-5 年。

### 3.6 无人机（简要）

World Model 在无人机中应用分散且早期。当前自主性更多依赖传统 SLAM + 规划算法。在军用（GPS拒止、对抗环境）和复杂室内环境中，学习型世界模型正展现价值。代表公司 Skydio（$22亿估值）、Shield AI（$27亿估值）。预计跟随自动驾驶/机器人领域进展受益。

## 四、横纵交汇洞察

### 4.1 用五问框架定位投资逻辑

| 问题 | 判断 |
|------|------|
| **规模** | 多赛道叠加——视频生成（百亿级）+ 自动驾驶仿真（数百亿级）+ 机器人训练（万亿级远期市场）。付费方：车企、机器人公司、内容创作者、游戏开发商 |
| **壁垒** | 分赛道不同。视频生成壁垒低（路线趋同、开源追赶快）；具身机器人壁垒高（数据稀缺、硬件+软件协同）；平台级壁垒最高（NVIDIA 生态锁定） |
| **稀缺性** | 当前最稀缺的是：真实世界交互数据 > 物理精确仿真能力 > 算力。机器人操作数据的供需 gap 最大（互联网没有，必须自己采集或仿真生成） |
| **成长性** | 持续性需求。只要机器人/自动驾驶要大规模部署，World Model 就是刚需基础设施。不是一次性的 |
| **不确定性** | VLA vs 具身 RL 路线未收敛；像素 vs 潜空间建模未定论；World Model 能否直接输出 action 未验证 |

### 4.2 四条路线谁会赢？

我的判断是：**不会有唯一赢家，但会形成分层架构。**

- **高层**：VLA / 大语言模型——提供语义理解、任务规划、常识推理
- **中层**：World Model（潜空间预测 or 视频生成式）——提供环境预测、轨迹规划
- **底层**：传统控制器 or RL policy——提供精细运动控制

这跟自动驾驶的 L4 架构演进类似：最终不是某一层独揽全局，而是分层协作。

### 4.3 NVIDIA 是最大确定性赢家

无论哪条路线胜出，都需要 NVIDIA 的算力。而 NVIDIA 同时布局了：
- 硬件（GPU/DPU）
- 物理仿真（Omniverse/Isaac）
- AI 世界模型（Cosmos）
- 资本投资（Wayve、Figure AI 等）

这是「卖铲子」的终极版本。

### 4.4 中国玩家的机会窗口

- **视频生成**：阿里 Wan 开源，快手可灵产品化——在这个赛道中国不落后
- **机器人硬件**：宇树、智元的硬件成本优势明显，且迭代速度快
- **差距在**：底层模型能力（VLA/World Model 大模型训练需要数据+算力）、生态整合

### 4.5 三个剧本

**最可能的剧本**：2025-2027 年各路线并行迭代，VLA + World Model 分层融合成为主流架构。具身机器人在仓储/制造场景小规模落地，视频生成工具成为创作者标配，自动驾驶仿真全面采用 AI 生成。

**最乐观的剧本**：某个团队（可能是 Physical Intelligence 或 DeepMind）突破了通用世界模型——一个模型跨赛道工作，类似 GPT-3 对 NLP 的颠覆。这会引发具身 AI 的「iPhone 时刻」。

**最危险的剧本**：World Model 遇到 scaling 瓶颈（物理推理能力不随规模线性增长），实际应用中 sim-to-real gap 无法弥合，大量投资打水漂。具身机器人回到传统控制+专用仿真的老路。

## 五、核心争论速览

### "视频生成 = World Model" 吗？

OpenAI 说是（Sora = World Simulator）。LeCun 说不是（预测像素 ≠ 理解物理）。核心分歧：生成漂亮视频是在做「理解世界」还是在做「视频插值」？实用派认为够用就行，理论派认为缺乏物理保证。

### VLA vs 具身 RL

VLA（π0, RT-2）：利用互联网预训练知识，语言接口自然，任务泛化强。但推理慢、精细操控弱。

具身 RL + World Model（Dreamer, TD-MPC）：在模型中大量试错，物理理解深，实时规划强。但跨任务泛化难、缺乏语义理解。

趋势：融合。VLA 做高层 + RL/WM 做底层。

### AI 仿真 vs 传统物理引擎

传统引擎（MuJoCo, Isaac Sim）：精确、可控、可解释。但视觉真实感差、场景构建耗时。

AI 仿真（Cosmos, UniSim）：视觉逼真、场景多样。但物理不保证、不可控。

主流观点是融合——传统引擎做骨架，AI 填充外观和多样性。NVIDIA 自己两条腿走路已经说明了问题。

## 六、信息来源

### 关键论文
- Ha & Schmidhuber "World Models" (arXiv:1803.10122, 2018)
- Hafner et al. "Dreamer" 系列 (v1: 1912.01603, v2: 2010.02193, v3: 2301.04104)
- Hansen et al. "TD-MPC2" (arXiv:2310.16828, 2023)
- OpenAI "Video generation models as world simulators" (技术报告, 2024.02)
- LeCun "A Path Towards Autonomous Machine Intelligence" (2022.06)
- Wayve "GAIA-1" (arXiv:2309.17080, 2023)
- Google DeepMind "Genie" 系列 (2024)
- Brohan et al. "RT-2" (arXiv:2307.15818, 2023)

### 融资数据来源
- TechCrunch, The Information, Bloomberg 公开报道
- 标注确信度：高确信（多家媒体交叉验证）/ 中确信（单一来源）/ 暂缺

### 方法论说明
本报告采用横纵分析法（Horizontal-Vertical Analysis），由数字生命卡兹克提出。纵向追踪时间深度，横向追踪同期竞争广度，交汇产出投资判断。
