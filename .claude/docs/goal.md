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
具体可以学习：`.claude/docs/knowledge/research.md`了解投资人怎么思考
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

## 七、会议反馈 & Action Items（2026-05-11）

> 来源：团队内部 Demo Review

### 关键反馈

**Angela (产品/方向)**
1. **范式分类需要共识** — 不能只用 AI 生成的分类，需要团队对齐的 taxonomy（可参考 OpenAI 5层：知识→推理→Agentic→Innovator→Organization）
2. **从图里要能看出 insight** — "你看这些图之后我们能发现什么？" 需要明确回答：热度趋势、路线收敛信号、长期方向
3. **多赛道论文怎么显示** — 一个架构同时适用于两个场景时的视觉表达（当前方案：每篇只标主赛道）
4. **对标 EEMTR** — 国外有个网站专门监控大模型发展脉络，每个图有开源/闭源模型的发展方向，后续发给参考
5. **量不够看不到趋势** — 继续补充 related work，数据量上来之后趋势才可见
6. **部署到前端** — 让团队在前端上用，持续给反馈

**Thomas (技术/分析角度)**
1. **颜色混淆问题** — 左侧 Lane 标签颜色和右侧节点赛道颜色不能用同一套色系，会误解为对应关系（已修复：Lane 标签不再用赛道颜色）
2. **看脉络** — 大家基于哪个架构做迭代？一段时间内哪些工作的方向被讨论多？影响力如何累积？
3. **impact 动态信号** — 如果一个节点的圈在某个时序里突然变大，说明它是 rising signal（需要 citation 动态追踪）
4. **citation 深度分析** — 区分"继承性 citation"（在此基础上做延展）vs "对比性 citation"（只是提了一下实验对比）
5. **统一 entity taxonomy** — 所有机构/实验室/人名用同一套命名体系，跟其他团队的 network/signal 数据库打通

**Kai (技术判断)**
1. **Era 分类的分水岭** — 2024 年前后的分界可能是 diffusion 的引入（之前 GAN/其他，之后都用 diffusion 做 world model）

### Action Items

| # | 任务 | 负责 | 优先级 |
|---|------|------|--------|
| 1 | 部署前端，团队可访问 | Tian | P0 |
| 2 | 范式分类 taxonomy 对齐（发文档征求修改） | Tian + 团队 | P0 |
| 3 | Lane 侧边栏颜色去掉（避免与节点赛道色混淆） | Tian | P0 (已修) |
| 4 | 继续补充论文数据量（自动驾驶/游戏 VR） | Tian | P1 |
| 5 | 论文 Panel 完善：点击节点→显示机构、解决的问题、核心 insight | Tian + 叶律 | P1 |
| 6 | 统一 entity taxonomy（与团队 network 数据库对齐） | Tian + Thomas | P1 |
| 7 | Impact 动态追踪（citation 增长速率→节点大小变化） | Tian | P2 |
| 8 | Citation 类型分析（继承性 vs 对比性） | 叶律 | P2 |
| 9 | 参考 EEMTR 网站风格 | Tian | P2 |

---

## 附录：会议原始记录

<details>
<summary>点击展开原始会议纪要（2026-05-11 Demo Review）</summary>

Tian先来。

@Tian QIU  00:11:30
行，我这个是 world model， 先简单的出了一版，按照那个综述来的，这是一个，这是个 big picture， 就是可以看他论文在哪个阶段，哪个话题 topic 讨论比较多，比如说像24年这个产出比较多。左边的分类我是按照那个论文的，按照范式来分的，第一个就是强化学习，第二个就是 observation level 的，剩下就潜空间跟 object centric 的，对，还有就是。

@Tian QIU  00:12:02
做了一个宏观的 panel， 就是可以看比如 Google 的 DeepMind 他们做了哪些工作，然后再对，比如再来一个 Meta， 对他们在哪些赛道有布局行，然后之后还有一些功能就是可以看它具体的演进，就比如说这目前还是比较手工的，就是说我。知道谁跟谁有引用关系或者什么的来做的，对，然后再有就是单个赛道的展开了，然后展开之后可以看到他单个，比如说这个 Dreamer， 他的V1到V3，就他们每一个迭代他们把哪些瓶颈给攻克了，以及他们达到了什么样的结果？对，这是我目前的一个。

@Angela ZHAO  00:12:56
明白，我觉得这个可以看看。今天也推一下前端嘛？这样的话我觉得大家在前端上给你更多的反馈。

@Angela ZHAO  00:17:01
整体呈现是有那个意思了，但我觉得可能是，比如说你这个标签化到底是什么维度？我觉得需要给它一个对齐，有的时候那个 AI 比较习惯自己有一些分类，但我觉得它需要共识的分类。

@Angela ZHAO  00:17:37
我有个问题，如果一个有一个框架，那个架构它同时适用于两个场景，怎么显示？

@Angela ZHAO  00:19:35
你比如说你看这些图之后我们能发现什么？我给你举个例子，你看过有一篇国外的网站，它专门在监控大模型的发展脉络的，叫什么 EEMTR。

@Angela ZHAO  00:20:13
我觉得挺好。比如说我就问你，你拿开这张图，对吧？它说明了什么问题？我们长期看有什么趋势，或者是你 expect 它后面会是一目了然的是什么？

@Tian QIU  00:20:37
一目了然是哪些范式在收敛，他就在已有的架构上迭代了，而不会有东西去颠覆他这个东西。

@Angela ZHAO  00:20:53
如果是在一个架构上收敛的话，你觉得它会呈现成什么样？

@Tian QIU  00:20:58
比如都在 Dreamer 的基础上优化。大家都是从这引出来的，没有说单独起一个架构。

@Thomas TANG  00:21:27
我想问问这些是 MISI 的吗？就是左边的这个绿色和右边的这个绿色是对等的还是不对等的？

@Thomas TANG  00:23:29
左边的颜色跟右边的颜色是对应的，是不是？就其实你左边和右边是不对应的。左边这个绿色没有意义，不需要有颜色，不然我就会以为右边的都是对应的。

@Thomas TANG  00:25:12
看脉络，就是跟你刚刚画的 linkage 的图是比较像的，大家可能都基于在一段时间内都基于哪一个架构开始做迭代。第二个是看什么样的架构的影响力相对更大。

@Thomas TANG  00:26:32
时间线比较好，era 怎么分可能也是重要的，看在一段时间里什么样的工作方向会被大家讨论的更多，热度更高。

@Thomas TANG  00:27:31
论文有点像比如说 React，一开始发出来可能也不是特别重要，但后来就变得非常非常重要。这样可能更好的可以 identify 说这个人在这个领域里提出了一个比较关键的且被大家搞的比较多的事。如果一个时序里这个圈大了非常多，我们就应该是一个 signal，说明这是一个 rising 的被大家重视热度非常高的工作。

@Thomas TANG  00:29:14
论文之间都有 citation，citation 本身也有可被挖的线索，它到底是一篇继承性的还是一篇对比性的？还是里面有一些重要的工作的 idea 大家是互相借鉴的。

@Thomas TANG  00:31:01
所有的 player 的这些 entity，我们是不是应该统一一个 taxonomy？比如说谷歌 Alphabet 下分要不要分成 DeepMind 和 Google Brain？这样的话这些 entity 就能被对应上，在所有的 research 和 involve 里都应该用同一套 taxonomy。

@Angela ZHAO  00:31:55
同一套话语体系，底层的数据库，你的机构和大家的机构是对应的，如果你这里加了一个实验室，那个底层数据库也要加。

@Angela ZHAO  00:24:47
我觉得可能现在看不到趋势，可能是量不够，你可以再找一下 related work。

</details>
