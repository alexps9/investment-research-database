
---

## 📋 目录
1. [产品概述](#产品概述)
2. [核心需求](#核心需求)
3. [功能模块](#功能模块)
4. [可视化设计](#可视化设计)
5. [数据架构](#数据架构)
6. [优先级与里程碑](#优先级与里程碑)
7. [评估机制](#评估机制)

---

## 产品概述

### 目标
构建一个学术论文分析工具，通过可视化展示特定领域（如 Transformer、World Model）论文的演化关系，帮助研究者理解技术发展脉络和不同流派的竞争关系。

### 核心价值
- **全局雷达视角**: 展示为解决同一问题的不同技术分支的横向竞争
- **局部放大镜视角**: 展示单一技术架构的纵深迭代过程
- **信号发现**: 通过影响力算法发现被忽视但重要的冷门技术

---

## 核心需求

### 1. 需求降级（Phase 1 优先）

#### 1.1 引用量替代影响力分析
- **当前**: 使用复杂的 impact 分析决定节点大小
- **调整**: 先用**引用量（Citation）**完全替代 impact 分析
- **理由**: 简化实现，快速验证核心逻辑

#### 1.2 定义问题导向的论文筛选
- 不再依赖海量扫描，改为**规划驱动（Planning）**
- 通过组内讨论定义当前范式（Paradigm）的优缺点
- 以此作为论文筛选的 criteria

**示例**:
```
Transformer 范式问题:
├─ Attention 计算量大 (平方级)
│  └─ 解决方案: Linear Attention, Sparse Attention, Speculative Sampling
├─ 残差更新过慢
│  └─ 解决方案: Adaptive Residual, Fast Weight
└─ 参数更新效率低
   └─ 解决方案: 浅层更新策略
```

---

### 2. 论文沉淀逻辑：从海量扫描到规划驱动

#### 2.1 Planning 模块
**定义**: 在寻找论文前，通过组内讨论或 Agent 交互，定义当前范式的优缺点

**工作流**:
1. 识别范式的关键问题（如 Attention 计算量）
2. 列举解决该问题的不同策略（Linear, Sparse, Speculative）
3. 以此作为论文搜索的优先级标准

#### 2.2 海量扫描作为补充
- 虽然噪音大，但可从论文热点反推当前研究趋势
- 用于发现 Planning 模块遗漏的新方向

---

### 3. 核心关注方向

#### 3.1 Transformer 优化（Demo 1）
重点追踪 Transformer 架构的优化方向

#### 3.2 World Model 赛道（Demo 2 - 优先）
**覆盖范围**:
- 多模态学习
- 具身智能（Embodied AI）
- 机器人与自动驾驶
- 3D 游戏与虚拟环境
- 李飞飞等顶尖实验室的研究路径

**信息来源**: 利用访谈（导师、研究员、被投公司）的一手认知，具象化为子问题注入 Planning 模块

---

### 4. 信源边界扩张

#### 4.1 多元信息源
| 信源 | 优势 | 用途 |
|------|------|------|
| arXiv 论文 | 权威、完整 | 核心学术信号 |
| 大厂 Tech Blog | 及时、前沿 | 工程实践信号 |
| 研究者个人 Blog | 深度思考 | 观点与洞见 |
| X (Twitter) 长文 | 实时讨论 | 社区反应、小道消息 |
| Hugging Face | 开源实现 | 社区采纳度 |
| GitHub | 代码与 Stars | 开发者关注度 |

#### 4.2 信源优先级
- **Backbone**: 论文 + Tech Blog
- **补充**: X、Hugging Face、GitHub
- **未来**: 券商 Report、分析文章

---

## 功能模块

### 1. 可视化图谱（核心）

#### 1.1 双轴展示逻辑
```
纵轴: 技术分支/分野
  ├─ Linear Attention
  ├─ Sparse Attention
  ├─ Speculative Sampling
  └─ ...

横轴: 严格的时间轴
  └─ 按发表时间排序
```

#### 1.2 节点设计
- **单位**: 每个论文 = 一个节点（圆点）
- **大小**: 按引用量缩放（气泡图）
- **重要论文**: 视觉突出（闪烁、更大）
- **聚合处理**: 同一主题的衍生论文
  - 根源论文：大节点，标注名称
  - 衍生论文：小节点，鼠标悬停显示全名

#### 1.3 架构迭代展示（如 RWKV V1→V8）
- 展示单一架构的版本演进时间脉络
- 同期对比其他竞争架构的进展
- 理解：局部放大镜视角

---

### 2. 单篇论文深度分析（Side Panel）

#### 2.1 侧边栏信息结构
点击节点后，右侧栏展示：

| 模块 | 内容 | 数据源 |
|------|------|--------|
| **核心差异** | 论文解决的问题、技术创新点 | LLM 从摘要提取 |
| **技术角色** | 该论文在技术树中的位置 | LLM 分类 |
| **当前阶段** | 早期/成熟期 | 引用增速 YoY |
| **核心 Players** | 相关研究者、机构 | 人脉图谱联动 |
| **瓶颈分析** | 当前技术的限制与挑战 | Claude API 分析 |

#### 2.2 多篇论文聚合
- 若同一主题有多篇论文，展示根源论文详情
- 衍生论文以列表形式展示

---

### 3. 影响力评估算法

#### 3.1 影响力分数公式（初版）
```
Impact Score = w1 * Citation + w2 * GitHub_Stars + w3 * Community_Feedback
```

**权重分配**:
- Citation: 60% (最可靠)
- GitHub Stars: 20% (考虑刷单风险，权重降低)
- Community Feedback: 20% (社区认可度)

#### 3.2 "预三家"权重加成
- Google、OpenAI、Anthropic 发出的工作：+权重系数
- 理由：这些机构的工作通常具有更高的影响力

#### 3.3 冷门技术发现（Trigger 机制）
**场景**: 某篇论文在算法中 impact 很高，但未被公众号推荐

**触发逻辑**:
1. 识别 impact 异常升高的论文
2. 标记为"信号"，提醒团队关注
3. 自动推送到 Insight 产品进行深度分析

**历史校验**:
- 用历史上公认有影响力的论文（Attention Is All You Need, React 等）校验算法准确性

---

### 4. 反馈机制
- 点击率、阅读时长、转发等行为数据
- 用于优化推送算法

---

## 可视化设计

### 1. 全局视图（All Topics）
展示所有技术分支在时间轴上的演进

**可观察的模式**:
- 某阶段讨论 Model Architecture 的人较多
- 某阶段 Pretraining 讨论较多
- 某阶段 Test-time Computing 讨论较多
- 某阶段 RL 讨论较多

### 2. 单一主题视图（Single Topic）
聚焦某个技术分支（如 Linear Attention）

**可观察的内容**:
- 技术演进路线的分野
- 不同流派的主要 Players
- 时间脉络与竞争关系

### 3. 架构对比视图
展示同期不同架构的竞争情况

**示例**: RWKV V1-V8 vs Mamba vs Transformer 的并行演进

---

## 数据架构

### 1. 后端多维表格（底层）
```
多维表格结构:
├─ 赛道 (Track)
├─ 研究方向 (Research Direction)
├─ 一级节点 (Primary Node)
├─ 二级节点 (Secondary Node)
├─ 三级节点 (Tertiary Node)
├─ Players (大厂、研究所)
├─ Talent (研究者、团队)
├─ 从属关系 (Affiliation)
└─ 优先级 (P1/P2/P3)
```

### 2. 信号源管理
- 信源增删改查
- 信源分类（论文、Blog、Twitter、Report）
- 信源优先级评分

### 3. 日历日报
- 每日抓取的信息内容
- 与多维表格关联
- 形成时间序列数据

---

## 优先级与里程碑

### Phase 1: MVP（本周交付）

#### 交付物
1. **可视化研究图谱** (Visualized Research Graph)
   - 支持 Transformer 和 World Model 两个主题
   - 双轴展示（时间 + 技术分支）
   - 节点聚合与分层


#### 负责人
- 图谱可视化: Tian QIU



### Phase 2: 深度分析（后续迭代）

#### 功能
1. 单篇论文 Insight 生成（Agent）
2. 影响力算法精细化
3. 信号实时推送优化
4. 人脉图谱联动

#### 负责人
- Insight Agent: 叶绿
- 人脉图谱: Freddy
- 算法优化: Thomas TANG

---

## 评估机制

### 1. 图谱准确性评估

#### 1.1 历史校验
用公认有影响力的论文验证算法：
- Attention Is All You Need
- React (Yao et al.)
- Mamba
- 等

#### 1.2 语义聚类评估
- 论文是否被正确分类到对应分支
- 节点大小是否合理反映影响力


---

## 附录

### A. 技术分支 vs 架构迭代

| 维度 | 技术分支 | 架构迭代 |
|------|---------|---------|
| 定义 | 为解决同一问题的不同策略 | 同一技术物种的生长过程 |
| 视角 | 全局雷达（横向竞争） | 局部放大镜（纵深演进） |
| 示例 | Linear vs Speculative Sampling | RWKV V1→V8 |
| 关键问题 | 哪些流派在竞争？谁在跟？ | 如何从 V1 演进到 V8？ |

### B. 关键术语

- **Planning**: 在搜索论文前定义范式问题与解决方案
- **Paradigm**: 当前技术范式（如 Transformer）
- **Trigger**: 影响力异常升高的冷门技术发现机制
- **Dogfooding**: 团队内部使用自己的产品进行反馈迭代
- **Rubric**: 评估标准与打分规则

---
c.论文分类
[] 定义每个泳道为解决不同问题（架构的优缺点及相关改进尝试，如解决 attention 计算量大、优化残差、加快参数更新等方向）

Lane1:序列复杂度 & 长上下文
1-A. 线性化架构：用 sub-quadratic 复杂度的新架构替代 Attention（SSM/线性注意力/rnn复兴）
- 代表：Mamba / Mamba-2 / RWKV (V4-V7) / RetNet / GLA / Linear Transformer / Performer / Hyena / Hybrid (Jamba, Griffin) / DeltaNet / xLSTM
- 关键问题：能否在保持表达力的同时实现 O(n) 训练 + O(1) 推理
1-B. 稀疏 & 长文本扩展：不换架构，用稀疏/分块/外推手段撑住长序列
- 代表：Sparse Attention / StreamingLLM / Ring Attention / Infini-Attention / LongNet / SSD
- 关键问题：如何在不重训基座的前提下把 context 从 4K 推到 1M+
1-C. 位置编码 & 记忆：从位置编码与记忆机制入手延长上下文
- 代表：RoPE / ALiBi / YaRN / LongRoPE / HMT / RETRO / World-Model 系
- 关键问题：位置表达能否外推？记忆能否持久化？

Lane 2 — 推理效率（KV Cache + 工程）
- 2-A. KV Cache 结构优化：在 Attention 的 Q/K/V 结构上做减法
  - 代表：MQA (2019) / GQA (2023) / MLA - DeepSeek-V2/V3 / TransMLA
  - 关键问题：能否在不掉点的前提下让 KV 显存占用降一个数量级
- 2-B. 推理算子工程：IO-aware 底层 kernel 与分布式推理
  - 代表：FlashAttention V1-V4 / PagedAttention (vLLM) / Ring Attention (推理侧) / SpecAttn
  - 关键问题：HBM 带宽和单机显存怎么榨到极限
- 2-C. 解码策略：改变生成 token 的方式减少前向次数
  - 代表：Speculative Decoding / Medusa / Lookahead Decoding / EAGLE
  - 关键问题：每个 token 能否用"廉价 draft + 一次校验"代替"完整前向"

Lane 3 — 参数规模化（MoE）
- 3-A. MoE 基础设施：稀疏激活的基础范式与算子
  - 代表：GShard (2020) / Switch Transformer (2021) / Megablocks
  - 关键问题：万亿参数但只激活部分专家的训练范式
- 3-B. 路由与负载均衡：专家路由策略的迭代
  - 代表：Expert Choice MoE / DeepSeek-MoE (fine-grained + shared experts)
  - 关键问题：专家利用率如何稳定，避免塌缩与负载不均
- 3-C. 工业集成：产品级 MoE 模型
  - 代表：Mixtral 8x7B / DeepSeek-V3 (MLA+MoE) / Jamba (SSM+MoE)
  - 关键问题：MoE 的部署成本、量化、边缘运行可行性
  
 Reasoning 先不放（Phase 2）
CoT / ToT / Self-Refine / o1 / DeepSeek-R1 等推理策略类论文本期不入库。原因：
- 属于应用层策略，与 Lane 1-3 的架构层问题抽象层级不同