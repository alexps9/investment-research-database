# World Model Evolution Map — PRD v2

> 基于当前实现的迭代升级。核心变更：颜色编码从 Player 改为赛道(Application Domain)。

---

## 一、核心设计变更：颜色 = 赛道

### 为什么改

| 问题 | 说明 |
|------|------|
| Player 太多 | 8-10个机构，色板分不清 |
| 颜色是最强视觉通道 | pre-attentive，应编码投资人最先关心的维度 |
| 投资人入口是赛道 | "这个市场怎么样" > "这个公司在哪" |
| Player 用标签就够 | 节点本来就有名字，不需额外编码 |

### 新编码方案

| 通道 | 编码 | 回答 |
|------|------|------|
| 位置(泳道) | 范式/技术路线 | "技术路线是什么" |
| 位置(横轴) | 时间 | "演进方向" |
| **颜色** | **赛道 (6种)** | **"钱去哪了"** |
| 形状 | Layer (arch/sys/infer/train/memory) | "改了什么" |
| 大小 | Impact (citations) | "影响力多大" |
| 标签 | Player + 产品名 | "谁在做" |

### 赛道定义 & 色板 (6色)

| 赛道 | ID | 色值 | 代表论文/产品 | 优先级 |
|------|-----|------|--------------|--------|
| 多模态文生/图生视频 | video_gen | #2563EB (蓝) | Sora, Wan, Cosmos, Gen-3 | P0 |
| 自动驾驶 | autonomous_driving | #EA580C (橙) | GAIA-1, DriveVLA, UniWorld | P0 |
| 具身机器人 | robotics | #059669 (绿) | Dreamer, TD-MPC, TesserAct, VLA | P0 |
| 空间智能 | spatial | #7C3AED (紫) | JEPA, World Labs, LRM | P0 |
| 3D游戏/VR | game_vr | #DC2626 (红) | Genie 2, Oasis, GameNGen | P0 |
| 无人机 | drone | #475569 (灰蓝) | — | P2(少看) |

---

## 二、投资人阅读路径

```
1. 扫颜色分布 → "绿色(机器人)集中在 Lane 2 和 3，路线未收敛"
2. 看 Lane 内颜色混合度 → "Lane 1 五颜六色 = 通用基础设施"
3. 细看标签 → "Lane 3 绿色节点是 Dreamer(DeepMind) + TD-MPC(Berkeley)"
4. (交互) 按 Player 高亮 → 一眼看出某机构的全赛道布局
```

---

## 三、新增交互：Player 高亮 Filter

### 功能

侧边栏 Player 列表，点击某 Player：
- 该 Player 所有节点 → 加粗描边 + 发光(box-shadow momentum)
- 其他节点 → opacity 降至 0.2
- 连线只保留该 Player 相关的

### UI 位置

Global View 右侧面板或顶部 toolbar：

```
[Filter by Player]
○ All (default)
● DeepMind    ← 点击后高亮
○ OpenAI
○ Meta AI
○ NVIDIA
○ UC Berkeley
○ Alibaba
○ ...
```

### 视觉效果

| 状态 | 节点样式 |
|------|---------|
| 高亮 | stroke-width: 3px, box-shadow: 0 0 8px {赛道色} |
| 淡化 | opacity: 0.15, 无标签 |
| 默认(无filter) | 正常显示 |

---

## 四、数据模型变更

### Paper 新增字段

```python
class EvolutionPaper(BaseModel):
    # ... 现有字段 ...
    player: str = ""           # 机构/团队: "deepmind", "openai", "meta"...
    application: str = ""      # 赛道: "video_gen", "autonomous_driving", "robotics", "spatial", "game_vr", "infra"
```

### 颜色逻辑变更

```
旧: color = PLAYER_COLORS[paper.player]
新: color = APPLICATION_COLORS[paper.application]
```

### APPLICATION_COLORS

```typescript
const APPLICATION_COLORS: Record<string, string> = {
  video_gen: '#2563EB',
  autonomous_driving: '#EA580C',
  robotics: '#059669',
  spatial: '#7C3AED',
  game_vr: '#DC2626',
  infra: '#475569',
}
```

---

## 五、现有 79 篇论文赛道分配

规则：按论文的**主要应用场景**分配，不是按技术范式。一篇论文只属于一个赛道。

### Lane A: RL-Based World Models (22篇)

| 论文 | 赛道 | 理由 |
|------|------|------|
| PlaNet | robotics | 从像素学习 latent dynamics 用于连续控制 |
| Dreamer V1/V2/V3 | robotics | 想象力驱动策略学习，核心应用是连续控制/机器人 |
| DreamSmooth | robotics | Dreamer 变体，reward smoothing for control |
| PIGDreamer | robotics | Privileged info guided, safe robot control |
| HarmonyDream | robotics | Task harmonization in WM, control tasks |
| DyMoDreamer | robotics | Dynamic modulation for control |
| TD-MPC / TD-MPC2 / PWM | robotics | Model predictive control for robot tasks |
| IQ-MPC | robotics | Imitation + MPC for robot control |
| Hieros | robotics | Hierarchical imagination for long-horizon control |
| THICK | robotics | Temporal abstraction for planning |
| DIMA | robotics | Multi-agent RL world model |
| CoWorld | robotics | Offline visual RL |
| R2I | robotics | Memory-augmented RL |
| LEQ | robotics | Offline model-based RL |
| PCM | robotics | Policy-conditioned generalization |
| WAKER | robotics | Reward-free curriculum for WM |
| REM | robotics | Token-based parallel prediction |
| cRSSM | robotics | Zero-shot generalization across envs |
| Adaptive WM | robotics | Non-stationary env adaptation |
| MoSim | robotics | Neural motion simulator |

### Lane B: Observation-Level Generative (24篇)

| 论文 | 赛道 | 理由 |
|------|------|------|
| GPT-4 | video_gen | 通用基座，但在此图中关联视频生成路线 |
| LLaMA 3 | video_gen | 同上，多模态基座 |
| LLMCWM | spatial | LLM + causal world model，空间因果推理 |
| RAP | spatial | Reasoning as planning with world model |
| ByteSized32 | game_vr | Text-based world simulator (game) |
| Sora | video_gen | 视频生成 world simulator |
| Gen-3 Alpha | video_gen | 视频生成 |
| Wan (Alibaba) | video_gen | 视频生成 |
| Cosmos (NVIDIA) | video_gen | 视频生成 + 物理仿真 |
| T2V-Turbo | video_gen | 高效视频生成 |
| SPMEM | video_gen | 长期空间记忆视频世界模型 |
| VideoCrafter2 | video_gen | 数据高效视频扩散 |
| Emu3 | video_gen | 自回归多模态视频 |
| LLaVA | video_gen | 视觉语言模型（多模态基础） |
| Genie 2 | game_vr | 交互式游戏世界生成 |
| Oasis | game_vr | Transformer 实时游戏引擎 |
| TeleWorld | video_gen | 长视频自回归生成 |
| Vid2World | video_gen | 视频扩散→交互世界 |
| CoLA-World | video_gen | 潜在动作视频世界模型 |
| Text2Room | spatial | 文本→3D房间（空间智能） |
| 4D-fy | spatial | 文本→4D场景 |
| WonderJourney | spatial | 永续3D场景遍历 |
| SceneScape | spatial | 文本驱动场景一致性生成 |
| WonderWorld | spatial | 单图→交互3D场景 |
| LiDARCrafter | autonomous_driving | LiDAR 4D动态建模 |
| Invisible Stitch | spatial | 深度修复3D场景 |

### Lane C: Latent-Space World Models (10篇)

| 论文 | 赛道 | 理由 |
|------|------|------|
| I-JEPA | spatial | 图像级联合嵌入预测（空间表征） |
| V-JEPA | spatial | 视频时序潜空间预测 |
| V-JEPA 2 | robotics | 融合动作信号，支持机器人规划 |
| seq-JEPA | spatial | 自回归等变预测 |
| MC-JEPA | spatial | 运动+内容分离 |
| DINO-WM | robotics | 预训练视觉特征→零样本规划(robot) |
| DINO-World | robotics | DINO作为视频世界模型基础(robot) |
| DINO-Foresight | robotics | DINO未来预测(robot planning) |
| WM Group Latents | spatial | 群结构潜空间(abstract spatial) |
| LWM | video_gen | 百万长度视频+语言世界模型 |

### Lane D: Object-Centric World Models (14篇)

| 论文 | 赛道 | 理由 |
|------|------|------|
| Slot Attention | spatial | 通用对象发现（空间结构理解） |
| SlotFormer | spatial | 对象级动力学预测 |
| LSlotFormer | robotics | 语言引导机器人操作WM |
| MEAD | robotics | 对象中心探索+操作 |
| Dyn-O | spatial | 结构化对象世界模型 |
| G-SWM | spatial | 生成式对象交互 |
| CarFormer | autonomous_driving | 对象中心自动驾驶 |
| FOCUS | robotics | 机器人操作的对象中心WM |
| FIOC-WM | robotics | 交互式对象中心RL |
| Objects Matter | robotics | 对象中心改善视觉RL |
| OWM Meets Policy | robotics | 对象WM→策略学习 |
| OC Latent Action | robotics | 对象中心潜在动作 |
| Compositional OCL | spatial | 因果+对象组合 |
| OC Repr Generalize | spatial | 组合泛化 |

### Lane E: Robotics World Models (9篇)

| 论文 | 赛道 | 理由 |
|------|------|------|
| RoboDreamer | robotics | 机器人组合想象 |
| Grounding Video | robotics | 视频→机器人动作 |
| ViPRA | robotics | 视频预测机器人动作 |
| FlowDreamer | robotics | 光流+深度机器人操作 |
| TesserAct | robotics | 4D具身世界模型 |
| ORV | robotics | 4D占据栅格机器人视频 |
| WristWorld | robotics | 腕视角4D生成 |
| IRASim | robotics | 精细机器人操作仿真 |
| WISA | robotics | 物理感知视频世界模型 |

### 赛道统计

| 赛道 | 论文数 | 占比 |
|------|--------|------|
| robotics (具身机器人) | ~45 | 57% |
| video_gen (多模态视频) | ~15 | 19% |
| spatial (空间智能) | ~14 | 18% |
| game_vr (游戏/VR) | 3 | 4% |
| autonomous_driving (自动驾驶) | 2 | 3% |
| drone (无人机) | 0 | 0% |

**注意**：当前数据中自动驾驶和游戏/VR 论文严重不足，需从综述 Part 6/8 补充。

---

## 六、实现优先级

| 优先级 | 任务 | 工作量 |
|--------|------|--------|
| P0 | 数据模型加 `application` + `player` 字段 | 0.5h |
| P0 | 79篇论文标注赛道(按上表) | 1h |
| P0 | 前端颜色逻辑从 PLAYER_COLORS 改为 APPLICATION_COLORS | 0.5h |
| P0 | 节点标签改为 "论文名 — Player" 格式 | 0.5h |
| P0 | 图例更新(6色赛道色板) | 0.5h |
| P1 | Player 高亮 filter 侧边栏 | 2h |
| P1 | 高亮动效(glow + fade others) | 1h |
| P1 | 补充自动驾驶论文(综述 Part 6, ~15篇) | 2h |
| P1 | 补充游戏/VR论文(综述 Part 8, ~8篇) | 1h |
| P2 | 赛道分布统计面板 | 2h |
| P2 | 无人机赛道论文(少量) | 1h |

---

## 七、待补充论文（从综述获取）

### 自动驾驶 (Part 6) — 目标 ~15篇

| 论文 | 年份 | 子方向 |
|------|------|--------|
| GAIA-1 | 2023 | Action-Conditioned Imagination |
| UniWorld | 2023 | Predictive Modeling |
| OccWorld | 2024 | 3D Occupancy |
| DriveDreamer | 2024 | Real-world driving |
| Vista | 2024 | Generalizable driving |
| Drive-WM | 2024 | Multiview forecasting |
| DriveWorld | 2024 | 4D pre-trained |
| Think2Drive | 2024 | RL + latent WM |
| Copilot4D | 2024 | Discrete diffusion |
| DriveDreamer-2 | 2025 | LLM-enhanced |
| AdaWM | 2025 | Adaptive planning |
| DriveVLA-W0 | 2025 | VLA + world model |
| Doe-1 | 2024 | Closed-loop |
| InfinityDrive | 2024 | Long-horizon |
| NeMo | 2024 | Neural volumetric |

### 游戏/VR (Part 8) — 目标 ~8篇

| 论文 | 年份 | 子方向 |
|------|------|--------|
| GameNGen | 2025 | Diffusion 实时游戏引擎 |
| Genie 2 | 2024 | 交互式世界生成(已有) |
| Oasis | 2024 | Transformer游戏引擎(已有) |
| AnimeGamer | 2025 | 动漫生活模拟 |
| Matrix-Game | 2025 | 交互式世界基础模型 |
| Matrix-Game 2.0 | 2025 | 实时流式交互 |
| HunyuanWorld | 2025 | 3D沉浸式世界 |
| GameFactory | 2025 | 生成式交互视频 |

## 八、向后兼容

- `player` 字段保留在数据中，用于标签显示和 filter
- `PLAYER_COLORS` 映射表移除，不再用于节点着色
- 现有 Lane/Row 结构不变（编码范式，不是赛道）
- 现有 builds_on / iterations 不变

---

## 九、验收标准

1. Global View 一眼能分辨 5-6 种赛道颜色
2. 同一 Lane 内可见颜色混合（说明该范式是通用的）
3. 节点标签显示 "论文名 — Player"
4. Player filter 点击后 < 200ms 响应
5. 高亮节点有 glow 效果（信息编码 momentum，非装饰）
6. 淡化节点不干扰阅读高亮节点
