# Rising Stars — 2026 Q1-Q2

> 数据来源：Google Scholar + HuggingFace Papers + ArXiv（2026.05.18 抓取）
> 筛选标准：参考 `specs/还没收敛/！impact scrolling rubric.md` 的 Rising Signal 定义

---

## Tier 1：引用增速异常（<6个月 50+ citations）

### Do Generative Video Models Understand Physical Principles?
- **会议**: WACV 2026
- **引用**: 78
- **机构**: Google (Motamed, Culp, Swersky et al.)
- **Lane**: video_gen
- **Row**: diffusion_video
- **Rising 原因**: 质疑所有 video world model 的物理推理能力，成为后续评测工作必引
- **建议 impact**: 55

### WorldModelBench: Judging Video Generation Models as World Models
- **会议**: NeurIPS 2026
- **引用**: 60
- **机构**: D Li, Y Fang, Y Chen et al.
- **Lane**: video_gen
- **Row**: diffusion_video
- **Rising 原因**: 定义了 world model 评测标准，benchmark 类论文引用增长快
- **建议 impact**: 50

### Video World Models with Long-term Spatial Memory
- **会议**: NeurIPS 2026
- **引用**: 59
- **机构**: T Wu, S Yang, R Po, Y Xu, Z Liu et al. (Stanford/NVIDIA 系)
- **Lane**: video_gen
- **Row**: diffusion_video
- **Rising 原因**: 几何感知+空间记忆，解决 video WM 一致性问题的新方向
- **建议 impact**: 58

### WISA: World Simulator Assistant for Physics-aware Text-to-Video
- **会议**: NeurIPS 2026
- **引用**: 58
- **机构**: J Wang, A Ma, K Cao et al.
- **Lane**: video_gen
- **Row**: diffusion_video
- **Rising 原因**: 物理感知生成新方向，多团队独立跟进
- **建议 impact**: 52

---

## Tier 2：顶级机构新发（弱信号，引用还低但来源强）

### SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diffusion Transformer
- **日期**: 2026.05.14
- **机构**: NVIDIA
- **HF likes**: 67
- **Lane**: video_gen
- **Row**: diffusion_video
- **Rising 原因**: NVIDIA 首个开源 world model（2.6B参数），分钟级生成，工业界重要信号
- **建议 impact**: 48
- **ArXiv**: 2605.15178

### Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation
- **日期**: 2026.05.14
- **机构**: 清华 Machine Learning Group
- **HF likes**: 84
- **Lane**: video_gen
- **Row**: autoregressive_video
- **Rising 原因**: 1-2步采样实现实时交互 world sim，实用性突破
- **建议 impact**: 42
- **ArXiv**: 2605.15141

### World Action Models: The Next Frontier in Embodied AI (Survey)
- **日期**: 2026.05.12
- **机构**: Mike Zheng Shou 团队
- **Lane**: vla
- **Row**: vla_foundation
- **Rising 原因**: 定义 WAM 新范畴，统一 world model + action generation，方向性论文
- **建议 impact**: 45
- **ArXiv**: 2605.12090

### MotuBrain: An Advanced World Action Model for Robot Control
- **日期**: 2026.04.30
- **机构**: 清华系 (Jun Zhu)
- **Lane**: vla
- **Row**: vla_foundation
- **Rising 原因**: UniDiffuser 做机器人控制 SOTA（95.8% RoboTwin 2.0）
- **建议 impact**: 40
- **ArXiv**: 2604.27792

### HarmoWAM: Adaptive World Action Models
- **日期**: 2026.05.11
- **Lane**: rl_based
- **Row**: mpc_based
- **Rising 原因**: 统一 predictive + reactive control，WAM 方向又一篇独立工作
- **建议 impact**: 35

---

## Tier 3：方向性信号（非单篇论文，是趋势）

### 信号 1: "World Action Model" 概念收敛
- 3个月内 3+ 篇独立论文使用 WAM 框架
- 含义：**"world model 直接输出 action" 正在成为共识**
- 对应 goal.md 的问题："World Model 能否直接输出 action？还是只做环境预测？" → 答案正在收敛为"直接输出"

### 信号 2: 物理评测爆发
- PhyGround (250 prompts, 13 physical laws)
- WorldReasonBench (436 test cases)
- WorldModelBench (NeurIPS 2026)
- 含义：**社区认为 video WM 的物理能力是当前卡点**，大量资源投入评测

### 信号 3: NVIDIA 开源入场
- SANA-WM 是 NVIDIA 首个开源 world model
- 含义：**大厂认为 world model 基础设施化值得投入**，类似当年 LLaMA 对 LLM 的意义

### 信号 4: 实时交互突破
- Causal Forcing++ (1-2步)
- RAVEN (consistency-model GRPO)
- 含义：**从"生成好看视频"转向"实时可交互"**，world model 开始对接下游应用

---

## 待加入 data.json 的论文清单

加入时需要：
- [ ] 确认 lane/row 分类是否准确
- [ ] 确认 impact 分数
- [ ] 标记 `rising: true`
- [ ] Tier 1 的 4 篇建议标为 foundation
- [ ] Tier 2 的 5 篇标为 adaptation 或 foundation（SANA-WM 可能值得 foundation）
