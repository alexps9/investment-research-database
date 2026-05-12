# World Model Evolution 连线规范文档 (Complete Edition)

> 完整覆盖 README.md Part 1-5 的所有论文（~100篇）及其引用关系
> 数据来源：`world_model_complete_data.py`

---

## 一、数据概览

| Lane | 论文数量 | 主要子领域 |
|------|---------|-----------|
| RL-Based WMs | 26 | Dreamer系列, TD-MPC, 多智能体 |
| Observation-Level | 33 | 视频生成, 3D/4D, 交互世界 |
| Latent-Space WMs | 10 | JEPA, DINO特征, Tokenized |
| Object-Centric | 15 | Slot Attention, 结构化动力学 |
| Robotics | 10 | 视觉预测, 4D模型, 物理感知 |
| **总计** | **~100** | **12个子领域** |

---

## 二、Lane 1: RL-Based World Models (26 papers)

### 2.1 RSSM Foundation → Dreamer Evolution (主干)

```
RSSM (2018)
  │
  ├─ influences ── PlaNet (2019)
  │
  └─ builds_on ─── Dreamer V1 (2020)
                    │
                    ├─ builds_on ─── Dreamer V2 (2021)
                    │                 │
                    │                 └─ builds_on ─── Dreamer V3 (2025)
                    │
                    ├─ builds_on ─── DreamSmooth (2024)
                    ├─ builds_on ─── PIGDreamer (2025)
                    ├─ builds_on ─── HarmonyDream (2024)
                    ├─ builds_on ─── DyMoDreamer (2025)
                    │
                    └─ influences ── Hieros (2024)
                                      THICK (2024)
```

**关键引用关系** (验证来源):
- Dreamer V3 paper: "builds upon DreamerV2 algorithm" [arXiv:2301.04104]
- Dreamer V2: "applied to Atari games, utilizing categorical latent states" [arXiv:2010.02193]

### 2.2 TD-MPC Series (分支)

```
TD-MPC (2022)
  │
  ├─ builds_on ─── TD-MPC2 (2024)
  │                 │
  │                 └─ builds_on ─── PWM (2025)
  │
  └─ influences ── IQ-MPC (2025)
```

**关键引用关系**:
- TD-MPC2 GitHub: "TD-MPC2 is out! Visit github.com/nicklashansen/tdmpc2" [官方仓库]
- PWM: builds on TD-MPC2 for multi-task learning

### 2.3 Multi-Agent & Collaborative

```
Dreamer V1
  │
  ├─ influences ── DIMA (2025) [Diffusion-inspired multi-agent]
  └─ builds_on ─── CoWorld (2024) [Collaborative WM]
```

### 2.4 Specialized Variants

| 论文 | 继承自 | 创新点 |
|------|--------|--------|
| REM (2024) | Dreamer | Token-based + parallel prediction |
| cRSSM (2024) | Dreamer V2 | Contextual WM for zero-shot |
| WAKER (2024) | - | Reward-free curricula |
| PCM (2024) | - | Policy-conditioned models |
| MoSim (2025) | Dreamer V3 | Neural motion simulator |

---

## 三、Lane 2: Observation-Level Generative (33 papers)

### 3.1 Language Observations

```
GPT-4 (2023)
  │
  ├─ influences ── LLaMA 3 (2024)
  │
  └─ influences ── LLMCWM (2025) [Causal LLM]
                   RAP (2023) [Reasoning as Planning]
                   ByteSized32 (2024) [Text-based simulator]
```

### 3.2 Video Generation - Diffusion Stream (主干)

```
Video Diffusion Foundation (2022-2023)
  │
  └─ builds_on ─── Sora (2024) [OpenAI]
                    │
                    ├─ builds_on ─── Gen-3 Alpha (2024) [Runway]
                    ├─ builds_on ─── Wan (2025) [Alibaba]
                    ├─ builds_on ─── Cosmos (2025) [NVIDIA]
                    │
                    ├─ influences ── T2V-Turbo (2024)
                    ├─ influences ── SPMEM (2025) [Spatial memory]
                    └─ influences ── VideoCrafter2 (2024)
```

**跨Lane影响**:
- Sora → RoboDreamer (Robotics)
- Sora → Grounding Video Models (Robotics)
- Sora → Vid2World (Interactive)

### 3.3 Autoregressive Stream

```
LLaMA 3 (2024) ─── influences ─── Emu3 (2024) [Multimodal AR]
                                    │
                                    └─ LWM (2024) [Million-length video]
```

### 3.4 Interactive / Playable Worlds

```
Sora (2024)
  │
  ├─ influences ── Genie 2 (2024) [DeepMind]
  │                 │
  │                 ├─ influences ── Oasis (2024) [Decart]
  │                 └─ influences ── IRASim (2025) [Fine-grained robot]
  │
  ├─ builds_on ─── TeleWorld (2025)
  └─ influences ── Vid2World (2025)
                   CoLA-World (2025) [Latent actions]
```

### 3.5 3D/4D Generation

```
Text2Room (2023)
  │
  ├─ builds_on ─── 4D-fy (2024)
  │                 │
  │                 ├─ influences ── LiDARCrafter (2025)
  │                 └─ influences ── TesserAct (2025) [Robotics 4D]
  │
  └─ influences ── WonderWorld (2025)

SceneScape (2023) ─── influences ─── WonderJourney (2024)
```

---

## 四、Lane 3: Latent-Space World Models (10 papers)

### 4.1 JEPA Family (主干)

```
LeCun's JEPA Concept
  │
  └─ implements ─── I-JEPA (2023) [CVPR]
                     │
                     ├─ builds_on ─── V-JEPA (2024) [Video]
                     │                  │
                     │                  ├─ builds_on ─── V-JEPA 2 (2025) [Planning]
                     │                  └─ builds_on ─── seq-JEPA (2025) [Sequential]
                     │
                     └─ influences ── MC-JEPA (2023) [Motion & Content]
```

**关键引用关系**:
- V-JEPA 2: "Self-Supervised Video Models Enable Understanding, Prediction and Planning" [arXiv:2506.09985]
- seq-JEPA: "Autoregressive Predictive Learning of Invariant-Equivariant World Models" [NeurIPS 2025]

### 4.2 DINO-based World Models

```
DINOv2 (2023)
  │
  └─ features_for ─── DINO-WM (2024)
                        │
                        ├─ builds_on ─── DINO-World (2025) [Video]
                        └─ builds_on ─── DINO-Foresight (2025) [Future prediction]
```

### 4.3 Structured & Tokenized

```
I-JEPA ─── influences ─── World Models Group Latents (2025)
                            [Group-structured latent space]

Ring Attention ─── enables ─── LWM (2024)
                                  [Million-length video + language]
```

---

## 五、Lane 4: Object-Centric World Models (15 papers)

### 5.1 Slot Attention Evolution (主干)

```
Slot Attention (2020) [NeurIPS]
  │
  ├─ builds_on ─── SlotFormer (2023) [ICLR]
  │                 │
  │                 ├─ builds_on ─── LSlotFormer (2024) [Language-guided]
  │                 ├─ builds_on ─── MEAD (2025) [Exploration]
  │                 │
  │                 └─ influences ── Dyn-O (2025) [Structured]
  │                                  FIOC-WM (2025) [Interactive RL]
  │                                  CarFormer (2024) [Driving]
  │
  └─ influences ─── G-SWM (2020) [Generative imagination]
                    Objects Matter (2025) [RL benefits]
                    FOCUS (2025) [Robotics manipulation]
```

### 5.2 Object-Centric + RL Fusion

```
SlotFormer + Dreamer V1
  │
  └─ fuses_into ─── FIOC-WM (2025) [OC-RL]
                     OWM Meets Policy (2025) [Pixels to Policies]
                     Objects Matter (2025) [RL in complex envs]
```

### 5.3 Compositional & Causal

```
Slot Attention + Causal Learning
  │
  └─ combines ─── Compositional OCL (2024) [Causal + OC]
                   OC Repr Generalize (2025) [Less compute]
```

---

## 六、Lane 5: Robotics World Models (10 papers)

### 6.1 Visual Future Prediction

```
Sora (2024) ─── enables ─── RoboDreamer (2024) [ICML]
                              │
                              ├─ influences ── FlowDreamer (2025)
                              └─ influences ── ViPRA (2025)

Sora ─── enables ─── Grounding Video Models (2025) [ICLR]
```

### 6.2 4D Embodied World Models

```
4D-fy (2024) ─── evolves ─── TesserAct (2025) [4D Embodied]
                               │
                               ├─ builds_on ─── ORV (2025) [Occupancy 4D]
                               └─ influences ── WristWorld (2025) [Wrist views]
```

### 6.3 Physics-Aware Models

```
WonderWorld (2025) ─── influences ─── WISA (2025) [Physics-aware video]
Genie 2 (2024) ─── influences ─── IRASim (2025) [Fine-grained manipulation]
```

---

## 七、跨Lane融合关系 (Era 3 核心)

### 7.1 VLA (Vision-Language-Action) 融合

```
Lane 2 (Sora/Obs-Gen) ────┐
                           ├── merges_into ─── VLA Architecture
Lane 1 (RL-Based WMs) ────┘

CarFormer (OC + Driving)
DriveVLA-W0 (Video + RL + Driving)
```

### 7.2 结构化潜空间 (Structured Latent Space) 融合

```
Lane 3 (V-JEPA 2 / Latent-Space) ────┐
                                      ├── combines ─── Structured Dynamics
Lane 4 (Dyn-O / Object-Centric) ─────┘

World Models Group Latents + SlotFormer concepts
```

### 7.3 完整的 Era 3 闭环

```
Sora (Lane 2: Obs-Gen)
    │
    ├─ enables ─── RoboDreamer ─── enables ─── Robot Actions
    │
    └─ enables ─── Vid2World ──── enables ─── Interactive Worlds
    
Dreamer V3 (Lane 1: RL-Based)
    │
    ├─ enables ─── Objects Matter ─── proves ─── OC improves RL
    │
    └─ enables ─── OWM Meets Policy ─── shows ─── OC + Policy learning

V-JEPA 2 (Lane 3: Latent-Space)
    │
    └─ enables ─── Dyn-O (Lane 4: Object-Centric) ─── enables ─── Causal Reasoning
```

---

## 八、时代演进 (Era Classification)

### Era 1: Latent Dynamics (2018-2023)
**主导论文**: PlaNet, Dreamer V1/V2, Slot Attention, I-JEPA
**核心突破**: 
- RSSM 架构确立
- 想象力驱动的策略学习
- 对象发现机制
- 联合嵌入预测

### Era 2: Generative Simulation (2024-2025)
**主导论文**: Sora, V-JEPA, DINO-WM, SlotFormer, RoboDreamer
**核心突破**:
- 视频扩散模型作为世界模拟器
- 潜空间视频预测
- 预训练视觉特征的世界模型
- 机器人视频生成

### Era 3: Causal Reasoning (2025-2026+)
**主导论文**: V-JEPA 2, Dreamer V3, Dyn-O, OWM Meets Policy
**核心突破**:
- 动作条件预测
- 跨领域通用性
- 结构化对象动力学
- OC + RL 深度融合

---

## 九、引用关系验证表

| 论文 | builds_on | cites | influenced_by | 验证来源 |
|------|-----------|-------|---------------|---------|
| Dreamer V3 | Dreamer V2 | - | - | [Nature 2025] |
| TD-MPC2 | TD-MPC | - | - | [GitHub 官方] |
| V-JEPA | I-JEPA | - | - | [Meta AI Blog] |
| V-JEPA 2 | V-JEPA | - | - | [arXiv:2506.09985] |
| SlotFormer | Slot Attention | - | - | [ICLR 2023] |
| DINO-World | DINO-WM | - | DINOv2 | [arXiv:2507.19468] |
| Sora | Video Diffusion | - | - | [OpenAI Tech Report] |
| RoboDreamer | - | Sora | Dreamer | [ICML 2024] |

---

## 十、数据格式 (JavaScript)

```javascript
const PAPERS = [
  // RL-Based
  {id:'planet', title:'PlaNet', year:2019, lane:'rl_wm', row:'rssm'},
  {id:'dreamer_v1', title:'Dreamer', year:2020, lane:'rl_wm', row:'dreamer', builds_on:['planet']},
  {id:'dreamer_v2', title:'DreamerV2', year:2021, lane:'rl_wm', row:'dreamer', builds_on:['dreamer_v1']},
  {id:'dreamer_v3', title:'DreamerV3', year:2025, lane:'rl_wm', row:'dreamer', builds_on:['dreamer_v2']},
  {id:'tdmpc', title:'TD-MPC', year:2022, lane:'rl_wm', row:'tdmpc'},
  {id:'tdmpc2', title:'TD-MPC2', year:2024, lane:'rl_wm', row:'tdmpc', builds_on:['tdmpc']},
  {id:'pwm', title:'PWM', year:2025, lane:'rl_wm', row:'tdmpc', builds_on:['tdmpc2']},
  
  // Observation-Level
  {id:'sora', title:'Sora', year:2024, lane:'obs_gen', row:'video_gen'},
  {id:'gen3', title:'Gen-3 Alpha', year:2024, lane:'obs_gen', row:'video_gen', builds_on:['sora']},
  {id:'wan', title:'Wan', year:2025, lane:'obs_gen', row:'video_gen', builds_on:['sora']},
  {id:'cosmos', title:'Cosmos', year:2025, lane:'obs_gen', row:'video_gen', builds_on:['sora']},
  {id:'genie2', title:'Genie 2', year:2024, lane:'obs_gen', row:'interactive', influenced_by:['sora']},
  
  // Latent-Space
  {id:'i_jepa', title:'I-JEPA', year:2023, lane:'latent_wm', row:'jepa'},
  {id:'v_jepa', title:'V-JEPA', year:2024, lane:'latent_wm', row:'jepa', builds_on:['i_jepa']},
  {id:'v_jepa_2', title:'V-JEPA 2', year:2025, lane:'latent_wm', row:'jepa', builds_on:['v_jepa']},
  {id:'dino_wm', title:'DINO-WM', year:2024, lane:'latent_wm', row:'dino'},
  {id:'dino_world', title:'DINO-World', year:2025, lane:'latent_wm', row:'dino', builds_on:['dino_wm']},
  
  // Object-Centric
  {id:'slot_attention', title:'Slot Attention', year:2020, lane:'obj_centric', row:'slot'},
  {id:'slotformer', title:'SlotFormer', year:2023, lane:'obj_centric', row:'slot', builds_on:['slot_attention']},
  {id:'dyn_o', title:'Dyn-O', year:2025, lane:'obj_centric', row:'structured', builds_on:['slotformer']},
  
  // Robotics
  {id:'robodreamer', title:'RoboDreamer', year:2024, lane:'robotics', row:'visual_pred', influenced_by:['sora']},
  {id:'tesseract', title:'TesserAct', year:2025, lane:'robotics', row:'4d', influenced_by:['4dfy']},
];

const CROSS_ARCS = [
  // Era 2 Competition
  {from:'sora', to:'v_jepa', type:'competes_with', label:'像素派 vs 特征派'},
  
  // Era 3 Fusion
  {from:'sora', to:'robodreamer', type:'enables', label:'视频→机器人'},
  {from:'dreamer_v1', to:'objects_matter', type:'enables', label:'RL+OC'},
  {from:'v_jepa_2', to:'dyn_o', type:'enables', label:'潜空间+对象结构'},
  {from:'slotformer', to:'carformer', type:'enables', label:'OC→驾驶'},
];
```

---

## 附录：新增论文列表 (相对于初始版本)

### 新增 RL-Based (15篇)
- DreamSmooth, PIGDreamer, HarmonyDream, DyMoDreamer
- TD-MPC (原版), IQ-MPC
- Hieros, THICK
- R2I, LEQ, WAKER, PCM, REM, cRSSM, Adaptive WM, MoSim

### 新增 Observation-Level (13篇)
- GPT-4, LLaMA 3, LLMCWM, RAP, Surge, ByteSized32
- T2V-Turbo, SPMEM, VideoCrafter2
- Oasis, Vid2World, CoLA-World
- WonderJourney, SceneScape, Invisible Stitch

### 新增 Robotics (10篇)
- RoboDreamer, Grounding Video, ViPRA, FlowDreamer
- TesserAct, ORV, WristWorld
- IRASim, WISA

### 引用关系验证状态
- ✅ 已验证: Dreamer系列, TD-MPC系列, JEPA系列, Slot系列, DINO系列
- ⚠️ 推断: 部分跨Lane影响基于技术逻辑
- 📚 来源: arXiv, OpenReview, 官方GitHub, 会议论文
