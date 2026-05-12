# 引用演化图谱：合并可视化方案

> status: propose
> created: 2026-05-07
> complexity: 🟡中等
> scope: 前端可视化（Side Panel 数据流水线见 `tech-assessment-panel-spec.md`）

## 1. 背景与目标

**为什么做**：
现在有两个方向一致但各补其短的 demo：

| Demo | 强在 | 缺在 |
|---|---|---|
| `demo-preview.html` | Tier 聚合 / 引用连线 / 7 模块 Side Panel / Lane Filter | 年粒度时间轴、止于 2024、深色酷炫风违反 Rams |
| `llm_arch_evolution_2023_2026.html` | 季度粒度 / NOW 标记 / α 分级 / 浅色 Rams 风 | 无连线、无 Tier 聚合、Side Panel 信息薄 |

两者都没做 PRD 的三个硬要求：节点大小 ∝ 引用量、泳道必须是"问题"不是"架构"、异质泳道处理。
需要合一份：以 llm_arch 的骨架 + demo-preview 的内容层 + 新泳道分类。

**做完后的效果**（验收标准）：
1. 单页面展示 3 条泳道（序列复杂度&长上下文 / 推理效率 / 参数规模化 MoE），季度粒度时间轴 2023 Q1 → 2026 Q4，带 NOW 标记
2. 节点半径 ∝ `cited_by_count`（log 缩放），而非离散 tier/alpha 档位
3. Tier-1 节点常显标题，Tier-2 悬停显标题；α-HIGH 节点有光晕
4. 引用连线可见：同泳道实线、跨泳道虚线，边上标注 `source_type`
5. 筛选：Lane 切换（All / L1 / L2 / L3），Reasoning toggle 预留位但 MVP 不启用
6. 点击任意节点 → 右侧 Side Panel 展示 7 模块（对接 `tech-assessment-panel-spec.md` 的 `/api/assess/{paper_id}`）
7. 视觉严格 Rams：白/米白底、深灰文本、橙色仅用于活动/NOW/α-HIGH；无渐变、无阴影

**不做的事**（MVP）：
- 架构迭代纵深视图（RWKV V1→V8，PRD §1.3）→ Phase 2
- Planning 模块（问题→解法树，PRD §2.1）→ Phase 2
- 冷门 Trigger 异常检测（PRD §3.3）→ Phase 2
- Impact Score 加权算法（PRD §3.1）→ Phase 2，MVP 只用 `cited_by_count`
- 所有后端数据流水线（见 `tech-assessment-panel-spec.md`）

## 2. 泳道定义（Scheme B：3 lane + Reasoning 暂不放）

### 2.1 设计原则

泳道 = **问题**（"为解决同一问题的不同技术分支"，PRD §附录A）。
泳道内的节点 = 竞争该问题的不同**解法**。
这是从用户视角："我想看 O(n²) 这个问题谁在解"而不是"我想看 SSM 有哪些论文"。

**关键边界**：`SSM` / `Mamba` / `MoE` 是架构名，不是问题名。泳道命名必须是问题导向（"复杂度"/"推理效率"），架构名只在泳道内的节点 tag 层出现。

### 2.2 三条泳道

| # | 泳道名 | 解决的问题（问法视角） | 子分支（A/B/C） |
|---|---|---|---|
| 1 | 序列复杂度 & 长上下文 | "Attention O(n²) 算不动 / 存不下长序列怎么办" | A. 线性化架构 / B. 稀疏 & 长文本扩展 / C. 位置编码 & 记忆 |
| 2 | 推理效率（KV Cache + 工程） | "模型部署起来了，跑得起吗 / 跑得快吗" | A. KV Cache 结构优化 / B. 推理算子工程 / C. 解码策略 |
| 3 | 参数规模化 (MoE) | "参数量再翻 10 倍，训练/推理成本受得了吗" | A. MoE 基础设施 / B. 路由与负载均衡 / C. 工业集成 |

### 2.3 子泳道详细拆分

**Lane 1 — 序列复杂度 & 长上下文**

- **1-A. 线性化架构**：用 sub-quadratic 复杂度的新架构替代 Attention
  - 代表：Mamba / Mamba-2 / RWKV (V4-V7) / RetNet / GLA / Linear Transformer / Performer / Hyena / Hybrid (Jamba, Griffin) / DeltaNet / xLSTM
  - 关键问题：能否在保持表达力的同时实现 O(n) 训练 + O(1) 推理
- **1-B. 稀疏 & 长文本扩展**：不换架构，用稀疏/分块/外推手段撑住长序列
  - 代表：Sparse Attention / StreamingLLM / Ring Attention / Infini-Attention / LongNet / SSD
  - 关键问题：如何在不重训基座的前提下把 context 从 4K 推到 1M+
- **1-C. 位置编码 & 记忆**：从位置编码与记忆机制入手延长上下文
  - 代表：RoPE / ALiBi / YaRN / LongRoPE / HMT / RETRO / World-Model 系
  - 关键问题：位置表达能否外推？记忆能否持久化？

**Lane 2 — 推理效率（KV Cache + 工程）**

- **2-A. KV Cache 结构优化**：在 Attention 的 Q/K/V 结构上做减法
  - 代表：MQA (2019) / GQA (2023) / MLA - DeepSeek-V2/V3 / TransMLA
  - 关键问题：能否在不掉点的前提下让 KV 显存占用降一个数量级
- **2-B. 推理算子工程**：IO-aware 底层 kernel 与分布式推理
  - 代表：FlashAttention V1-V4 / PagedAttention (vLLM) / Ring Attention (推理侧) / SpecAttn
  - 关键问题：HBM 带宽和单机显存怎么榨到极限
- **2-C. 解码策略**：改变生成 token 的方式减少前向次数
  - 代表：Speculative Decoding / Medusa / Lookahead Decoding / EAGLE
  - 关键问题：每个 token 能否用"廉价 draft + 一次校验"代替"完整前向"

**Lane 3 — 参数规模化（MoE）**

- **3-A. MoE 基础设施**：稀疏激活的基础范式与算子
  - 代表：GShard (2020) / Switch Transformer (2021) / Megablocks
  - 关键问题：万亿参数但只激活部分专家的训练范式
- **3-B. 路由与负载均衡**：专家路由策略的迭代
  - 代表：Expert Choice MoE / DeepSeek-MoE (fine-grained + shared experts)
  - 关键问题：专家利用率如何稳定，避免塌缩与负载不均
- **3-C. 工业集成**：产品级 MoE 模型
  - 代表：Mixtral 8x7B / DeepSeek-V3 (MLA+MoE) / Jamba (SSM+MoE)
  - 关键问题：MoE 的部署成本、量化、边缘运行可行性

### 2.4 Reasoning 先不放（Phase 2）

CoT / ToT / Self-Refine / o1 / DeepSeek-R1 等推理策略类论文本期不入库。原因：
- 属于**应用层策略**，与 Lane 1-3 的**架构层问题**抽象层级不同
- 混放会让读者误以为它们在同一维度竞争
- 2025 起才是最大 alpha，但也意味着数据稀疏、分类标准还不稳定

Phase 2 再以 `tag: reasoning` 形式引入，配独立筛选 toggle。

### 2.5 一篇论文多泳道归属

优先级规则（论文只出现在一条主泳道，避免重复）：
1. 若核心贡献是 KV Cache 结构 / 推理工程 / 解码策略 → Lane 2
2. 否则若核心是 MoE 路由或稀疏激活 → Lane 3
3. 否则（线性化 / 稀疏扩展 / 位置编码 / 记忆）→ Lane 1
4. 若同时满足（如 DeepSeek-V3 = MLA + MoE）→ 归**主创新**所在 lane（V3 归 Lane 2-A，MLA 是其主创新），tag 加 `moe`，Side Panel 的 Evolution 模块体现跨 lane 关系
5. 若同时满足（如 Jamba = SSM + MoE）→ 归主架构创新 lane（Jamba 归 Lane 1-A，Hybrid SSM 是主创新），tag 加 `moe`

## 3. 视觉规范（Rams 合规）

### 3.1 颜色
| 用途 | 值 |
|---|---|
| 画布底色 | `#FFFFFF` 或 `#F5F5F5` |
| 文本主色 | `#333333` |
| 文本次色 | `#6B6B6B` |
| 分隔线 | `#E5E5E5` |
| 橙色强调 | `#FF4400`（仅用于 NOW 线、α-HIGH 光晕、当前选中节点、Reasoning tag 描边） |
| Lane 颜色（低饱和） | L1 `#185FA5` 蓝 / L2 `#3B6D11` 绿 / L3 `#7C3AED` 紫 |

禁止：渐变、阴影、深色主题。llm_arch 现有浅色 CSS 变量体系直接继承。

### 3.2 布局
- 时间轴水平，季度粒度 `2023 Q1 → 2026 Q4`（共 16 季度），`Q_W = 120px`
- 左端额外 "Before 2023" 聚合列（一列约 200px），显示所有 `is_pre_2023: true` 的基石节点
- 泳道左侧 sticky label 列 `LANE_W = 128px`
- 3 条主泳道之间 4px 细分隔线
- 每条 lane 内部子分支 A/B/C 用 2px 虚线分隔（视觉上弱于 lane 分隔）
- 画布可横向滚动，年份与季度 bar 顶部 sticky

### 3.3 节点
| 属性 | 规则 |
|---|---|
| 半径 | `r = clamp(4, 12, 4 + 2 * log10(cited_by_count + 1))` |
| 填充 | lane 颜色 的 15% 透明度；Reasoning 标签节点额外描边 `#FF4400` 1px |
| 描边 | lane 颜色，Tier-1 粗 1.5px，Tier-2 细 1px |
| α-HIGH 光晕 | `box-shadow: 0 0 0 2px ${laneColor}33` |
| 当前选中 | 描边改橙色 `#FF4400`，半径 +2px |
| 标题显示 | Tier-1 常显；Tier-2 仅悬停/选中时显示 |
| 标签字号 | Tier-1 `11px`；Tier-2 `10px` |

### 3.4 连线
| 类型 | 样式 | 含义 |
|---|---|---|
| 同泳道 | 实线 0.5px，lane 颜色 40% 透明 | predecessor → successor |
| 跨泳道 | 虚线 `4 4` 0.5px 灰色 | 跨 lane 的引用/灵感 |
| coupling 边 | 实线 0.5px 浅灰 | 文献耦合（MVP 可不渲染） |

数据来自 `/api/network/auto` 返回的 link 的 `source_type` 字段。

### 3.5 NOW 线
- 竖线 1px 橙色 60% 透明，穿过所有 lane
- 顶部 "NOW" 标签，10px 橙色
- 位置由 `Date.now()` 映射到季度索引，每次加载计算一次

## 4. 功能点

### F1：泳道与时间轴骨架
- [ ] **F1.1** 定义 `LANES` 常量：3 条 lane 的 id / name / sub-lane (A/B/C) / color
- [ ] **F1.2** 季度时间轴：`2023 Q1 → 2026 Q4`（左端额外 "Before 2023" 聚合列）
- [ ] **F1.3** NOW 线计算与渲染（当前日期映射到季度）
- [ ] **F1.4** Lane 之间 4px 实线分隔；lane 内部 A/B/C 子分支 2px 虚线分隔
- [ ] **F1.5** 年份 sticky bar + 季度 sticky bar

### F2：节点渲染
- [ ] **F2.1** 节点半径按 `cited_by_count` log 缩放，clamp 到 [4, 12]
- [ ] **F2.2** Tier-1 常显标题；Tier-2 悬停/选中显标题
- [ ] **F2.3** α-HIGH 光晕（来自后端 assessment.alpha 字段；MVP 可先硬编码）
- [ ] **F2.4** 同 quarter 节点垂直堆叠（保留 llm_arch 的 `qMap` 逻辑）
- [ ] **F2.5** 选中态样式：橙色描边 + 半径放大

### F3：连线渲染
- [ ] **F3.1** 从 `/api/network/auto` 获取 links
- [ ] **F3.2** 按 `source_type` 区分样式（同泳道实线 / 跨泳道虚线）
- [ ] **F3.3** SVG 层在节点层之下、grid 层之上
- [ ] **F3.4** 选中节点时高亮其入边/出边（opacity 从 0.3 → 0.8）

### F4：筛选与交互
- [ ] **F4.1** Lane Filter：`All / L1 / L2 / L3` 四按钮
- [ ] **F4.2** 预留 Reasoning toggle 位（Phase 2 启用；MVP 隐藏）
- [ ] **F4.3** Filter 状态下非选中 lane 的节点淡出（opacity 0.15），连线一并淡出
- [ ] **F4.4** 点击节点 → 触发 Side Panel 打开 + 请求 `/api/assess/{paper_id}`
- [ ] **F4.5** ESC / 点击空白 → 关闭 Side Panel
- [ ] **F4.6** 节点 hover tooltip：title / authors / year / citations

### F5：Side Panel（7 模块）
- [ ] **F5.1** 布局：固定右侧 420px，页面内嵌（非 fixed overlay，避免遮挡图）
- [ ] **F5.2** 从 demo-preview 移植 7 模块 DOM 结构：标题区 / 技术定位 / 技术演进 / 当前阶段 / 核心玩家 / 瓶颈分析 / 结论
- [ ] **F5.3** 按 Rams 改配色：白底 + 深灰文字 + 细分隔线，去掉深色卡片背景
- [ ] **F5.4** 数据源 = `/api/assess/{paper_id}` 返回的 `TechAssessment` 对象
- [ ] **F5.5** Loading 态 + Error 态（透明错误处理，CLAUDE.md §4 强制）
- [ ] **F5.6** Tier-2 论文走简化面板（标题 + arXiv 链接，同 demo-preview）

### F6：数据对接
- [ ] **F6.1** 页面加载调用 `/api/network/auto?paper_ids=...` 获取节点 + 连线
- [ ] **F6.2** seed_papers.py 扩展到 40-50 篇覆盖 3 条新 lane（旧 seed 按架构分，需按问题重映射）
- [ ] **F6.3** 每个 Paper 需要字段：`id, title, authors, year, quarter, lane, sub_lane, tier, cited_by_count, arxiv_id?, source_url?, is_pre_2023, alpha?`
- [ ] **F6.4** lane / sub_lane / tier 来自 seed_papers.py 人工标注；alpha 初期人工，后期可由后端引用增速规则生成

## 5. 业务规则

1. **泳道即问题**：lane 的 id/name 必须是问题描述而非架构名（违反时 reviewer 必须打回）
2. **Reasoning 先不进库**：CoT / ToT / o1 / R1 等本期不纳入；Phase 2 以 tag 形式引入
3. **节点大小 = 引用量**：禁止用离散 tier 或 alpha 替代连续引用量做半径映射
4. **Rams 视觉红线**：禁止渐变、阴影、深色底；橙色仅用于 NOW / α-HIGH / 选中
5. **Side Panel 数据必走 API**：禁止在前端硬编码 assessment 数据（demo-preview 的 allPapers 内嵌 assessment 只是演示占位）
6. **透明错误**：API 失败时 Side Panel 显示具体错误（paper_id、HTTP 状态、可重试按钮），不隐藏

## 6. 数据模型

### 6.1 前端 Node（TypeScript）
```ts
interface Node {
  id: string;              // OpenAlex Work ID 或 synthetic ID（无 arxiv 时）
  title: string;
  authors: string[];       // 前 3 作者
  year: number;
  quarter: 1 | 2 | 3 | 4;
  lane: 0 | 1 | 2;         // 0=复杂度&长上下文 1=推理效率 2=MoE
  sub_lane: 'A' | 'B' | 'C';
  tier: 1 | 2;
  cited_by_count: number;
  arxiv_id?: string;       // 可空：RWKV-7 / FlashAttn-4 / o1 等
  source_url?: string;     // arxiv_id 缺失时的回退（官方 GitHub / 博客 / 技术报告）
  is_pre_2023: boolean;    // 基石论文，显示在 "Before 2023" 聚合列
  alpha?: 'high' | 'mid' | 'low';
  tags: string[];          // 'long-context' / 'moe' / 'hybrid' / 'kv-cache' 等
}
```

### 6.2 前端 Link
```ts
interface Link {
  source: string;          // node id
  target: string;
  source_type: 'citation' | 'coupling' | 'llm';
  strength?: number;       // 仅 coupling
}
```

### 6.3 与后端字段对齐
- 后端 `Paper`（`schemas.py`）已有 `cited_by_count`，无需新增
- 后端需补 `lane_id: int (0|1|2)` / `sub_lane: 'A'|'B'|'C'` / `tier: Literal[1, 2]` — 在 `seed_papers.py` 的 `SeedPaper` 上
- 后端需补 `quarter: int` — 从 `publication_date` 推导
- 后端需补 `is_pre_2023: bool` 与 `source_url: Optional[str]`（arxiv_id 缺失时回退）
- Reasoning 相关论文 Phase 2 再考虑，MVP 不入库

## 7. 接口变更

| 操作 | 接口 | 方法 | 变更内容 |
|------|------|------|----------|
| 复用 | `/api/network/auto` | GET | `tech-assessment-panel-spec.md` F4.3 已定义，本 spec 只消费 |
| 复用 | `/api/assess/{paper_id}` | GET | 同上 F4.1 |
| 新增 | `/api/network/lanes` | GET | 返回 4 条 lane 的元数据（id/name/sub/color/layer），让前端不硬编码 |

## 8. 影响范围

### 前端新增文件
| 文件 | 用途 |
|------|------|
| `frontend/src/app/page.tsx` | 整合主页面（如不存在则新建） |
| `frontend/src/components/CitationGraph/index.tsx` | 主图容器 |
| `frontend/src/components/CitationGraph/Lane.tsx` | 单条泳道渲染 |
| `frontend/src/components/CitationGraph/Node.tsx` | 节点组件 |
| `frontend/src/components/CitationGraph/Connections.tsx` | SVG 连线层 |
| `frontend/src/components/CitationGraph/NowLine.tsx` | NOW 标记 |
| `frontend/src/components/CitationGraph/LaneFilter.tsx` | 筛选按钮组 |
| `frontend/src/components/SidePanel/index.tsx` | 7 模块 Side Panel |
| `frontend/src/components/SidePanel/modules/*.tsx` | 7 个子模块 |
| `frontend/src/lib/constants.ts` | `LANES` / `QUARTERS` / 颜色常量 |
| `frontend/src/lib/api.ts` | `fetchNetwork` / `fetchAssessment` |
| `frontend/src/types/index.ts` | Node / Link / TechAssessment 类型 |
| `frontend/src/styles/*.module.css` | 各组件 CSS Modules |

### 前端废弃
- `demo-preview.html` — ���留作演示原型，不再迭代
- `llm_arch_evolution_2023_2026.html` — 同上

### 后端改动
| 文件 | 改动 |
|------|------|
| `app/data/seed_papers.py` | 重映射 lane（按问题），扩展到 40-50 篇，加 `lane_id (0/1/2)` / `sub_lane` / `tier` / `is_pre_2023` / `source_url` |
| `app/models/schemas.py` | `Paper` 加 `quarter: Optional[int]` / `is_pre_2023: bool` / `source_url: Optional[str]` |
| `app/services/openalex_client.py` | `_parse_work` 从 `publication_date` 推 `quarter` |
| `app/api/routes.py` | 新增 `/api/network/lanes` 端点 |

## 9. 风险与关注点

1. **seed 重映射工作量**：旧 seed 按"架构"分 lane（Attention / SSM / RNN / MoE），新 spec 按"问题"分。需要逐篇重标 lane_id + sub_lane，约 40-50 篇人工工作。
2. **一篇论文多 lane 归属**：§2.5 的优先级规则在边界案例（如 DeepSeek-V3 = MLA+MoE、Jamba = SSM+MoE）仍需人工判断 → 在 seed_papers.py 注释里写归属理由。
3. **连线密度**：Lane 1 会成为最密集的泳道（SSM + 稀疏 + 位置编码都在这），连线可能互相遮挡 → MVP 默认不显示全部连线，选中节点时才高亮相关边缓解。
4. **无 arXiv 论文数据获取**：RWKV-7 / FlashAttn-4 / DeepSeek-R1 博客版等无法走 OpenAlex，只能 source_url 占位 + 手工 `cited_by_count` → seed_papers.py 允许 `arxiv_id=None` 且带 `cited_by_count_manual` 字段。
5. **Rams 风格 vs 炫酷需求**：团队分享/老板 demo 时深色版更有冲击力 → 本 spec 明确只做白底 Rams 版；深色版可作为独立 "presentation mode" 放到 Phase 2。

## 10. 测试策略

- **组件测试**：每个 `CitationGraph/*` 和 `SidePanel/*` 子组件 Jest + RTL 单测
  - Node：半径计算、选中态、悬停态
  - Lane：节点堆叠、α-HIGH 光晕
  - Connections：source_type → 样式映射
  - LaneFilter：筛选状态切换
  - SidePanel：7 模块条件渲染、Loading / Error 态
- **集成测试**：`page.tsx` 级 — mock API 返回，验证点击节点 → Side Panel 打开 → 模块数据填充
- **视觉回归**：用 snapshot 锁定 Rams 颜色红线（禁止 gradient / shadow 类出现在 className）
- **覆盖率目标**：新增代码 > 80%（CLAUDE.md §4）

## 11. 技术决策

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 泳道维度 | 按问题 / 按架构 / 混合 | 按问题 (Scheme B) | PRD §附录A 明确要求；横向竞争视角更强；架构名留在 tag 层 |
| 时间粒度 | 年 / 季度 / 月 | 季度 | 季度够显示演进节奏，年太糙，月太碎 |
| 节点大小 | 离散 tier / 离散 alpha / 连续 citation | 连续 citation (log 缩放) | PRD §1.2.2 明确引用量 |
| 配色 | Rams 浅色 / 深色酷炫 / 双主题 | 浅色 Rams only | CLAUDE.md 强制；深色版 Phase 2 |
| 连线渲染 | 始终可见 / 悬停显示 / 选中高亮 | 始终可见 + 选中高亮 | 避免用户探索成本，同时降低噪音 |
| Side Panel 位置 | fixed overlay / 页面内嵌 | 内嵌右侧 420px | 不遮挡图，保留可视对比 |
| 架构迭代视图 | MVP 含 / Phase 2 | Phase 2 | MVP 聚焦横向竞争，纵深视图需要单独设计 |
| 泳道元数据 | 前端硬编码 / 后端 API | 后端 API (`/api/network/lanes`) | 便于后续调整不改前端代码 |
| 深色"演示模式" | 本期做 / Phase 2 | Phase 2 | 避免双主题增加测试面积 |

## 12. 待澄清

- [x] ~~Reasoning 归宿~~ → Phase 2 再以 tag 形式引入，MVP 不纳入（2026-05-07 确认）
- [x] ~~时间起点~~ → 2023 Q1（2026-05-07 确认）
- [ ] seed 候选库（§16）是否是最终清单？需要团队 review 特别是 Lane 1-C 的 World-Model / 记忆系条目
- [ ] `/api/network/lanes` 是否真有必要？如果 lane 定义极少变化，硬编码 `constants.ts` 更简单
- [ ] PMLL / Trellis 这类非正式论文（博客/内部预览）要不要纳入？纳入则破坏"arxiv_id 必填"的数据约束

## 13. 执行日志

| Task | 状态 | 实际改动文件 | 备注 |
|------|------|-------------|------|
| F1 泳道与时间轴骨架 | 待开始 | CitationGraph/* | — |
| F2 节点渲染 | 待开始 | Node.tsx | — |
| F3 连线渲染 | 待开始 | Connections.tsx | — |
| F4 筛选与交互 | 待开始 | LaneFilter.tsx, page.tsx | — |
| F5 Side Panel 7 模块 | 待开始 | SidePanel/* | 依赖后端 `/api/assess` 完成 |
| F6 数据对接 + seed 重映射 | 待开始 | seed_papers.py, api.ts | — |

## 14. 审查结论

（待 reviewer 审查后填写）

## 15. 确认记录（HARD-GATE）

- **确认时间**：
- **确认人**：

## 16. Seed 论文候选库

> 2023 Q1 起；Scheme B lane 划分 + 思维导图论文清单。共约 50 篇。
> 列：arXiv / 季度 / tier / sub_lane / tags / 归属理由
> 归属有歧义时依照 §2.5 优先级规则，主创新所在 lane 优先。

### Lane 1 — 序列复杂度 & 长上下文

#### 1-A：线性化架构（用 sub-quadratic 新架构替代 Attention）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2006.16236 | Linear Transformer | pre-2023 | 2 | `linear` | 基石 |
| 2009.14794 | Performer | pre-2023 | 2 | `linear` | 基石 |
| 2008.07669 | HiPPO | pre-2023 | 2 | `ssm`,`theory` | SSM 理论基石 |
| 2111.00396 | S4 | pre-2023 | 1 | `ssm` | SSM 范式奠基 |
| 2212.14052 | H3 | pre-2023 | 2 | `ssm`,`hybrid` | — |
| 2302.10866 | Hyena | 2023 Q1 | 2 | `ssm`,`convolution` | — |
| 2305.13048 | RWKV (V4) | 2023 Q2 | 1 | `rnn`,`linear` | 开源社区范式代表 |
| 2307.08621 | RetNet | 2023 Q3 | 1 | `linear`,`microsoft` | Microsoft |
| 2312.00752 | Mamba | 2023 Q4 | 1 | `ssm`,`selective` | Attention 挑战者 |
| 2312.06635 | GLA (Gated Linear Attention) | 2023 Q4 | 2 | `linear`,`gated` | — |
| 2402.19427 | Griffin | 2024 Q1 | 2 | `ssm`,`hybrid`,`deepmind` | DeepMind |
| 2403.19887 | Jamba | 2024 Q1 | 1 | `ssm`,`hybrid`,`moe` | 工业级 hybrid（MoE 是副创新） |
| 2405.21060 | Mamba-2 | 2024 Q2 | 1 | `ssm`,`theory` | SSD 理论统一 |
| 2406.06484 | DeltaNet | 2024 Q2 | 2 | `linear`,`delta-rule` | — |
| 2405.04517 | xLSTM | 2024 Q2 | 2 | `rnn`,`linear` | RNN 复兴 |
| — | RWKV-7 | 2024 Q4 | 2 | `rnn`,`linear` | ⚠️ 无正式 arXiv，`source_url` 指 GitHub/博客 |

#### 1-B：稀疏 & 长文本扩展（不换架构，用稀疏/分块/外推撑长序列）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2104.07364 | Sparse Attention (Child-tuning) | pre-2023 | 2 | `sparse` | 基石 |
| 2309.17453 | StreamingLLM | 2023 Q3 | 2 | `streaming`,`long-context` | Attention sink |
| 2310.01889 | Ring Attention | 2023 Q4 | 2 | `distributed`,`long-context` | 训练侧分布式 |
| 2404.07143 | Infini-Attention | 2024 Q2 | 1 | `long-context`,`memory` | — |
| 2307.02486 | LongNet | 2023 Q3 | 2 | `long-context`,`sparse` | 1B token |

#### 1-C：位置编码 & 记忆（从位置表达与外挂记忆入手）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2104.09864 | RoPE | pre-2023 | 1 | `rope`,`position` | 位置编码基石 |
| 2108.12409 | ALiBi | pre-2023 | 2 | `position`,`linear-bias` | — |
| 2309.00071 | YaRN | 2023 Q3 | 2 | `rope`,`long-context` | 外推 |
| 2402.13753 | LongRoPE | 2024 Q1 | 2 | `rope`,`long-context` | Microsoft，2M token |
| 2403.03844 | HMT | 2024 Q1 | 2 | `memory`,`hierarchical` | 层级化记忆 |
| 2112.04426 | RETRO | pre-2023 | 2 | `retrieval`,`memory` | DeepMind 检索增强 |

### Lane 2 — 推理效率（KV Cache + 工程）

#### 2-A：KV Cache 结构优化（Q/K/V 结构做减法）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 1911.02150 | MQA (Multi-Query Attention) | pre-2023 | 2 | `kv-cache` | 基石 |
| 2305.13245 | GQA (Grouped-Query Attention) | 2023 Q2 | 1 | `kv-cache` | Llama2 采用 |
| 2405.04434 | DeepSeek-V2 (MLA 原出处) | 2024 Q2 | 1 | `kv-cache`,`mla` | MLA 首次提出 |
| 2412.19437 | DeepSeek-V3 | 2024 Q4 | 1 | `kv-cache`,`mla`,`moe` | MLA+MoE 工业集成（归 2-A，主创新是 MLA） |
| 2501.10091 | TransMLA | 2025 Q1 | 2 | `mla`,`migration` | MLA 迁移研究 |

#### 2-B：推理算子工程（IO-aware kernel + 分布式推理）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2205.14135 | FlashAttention | pre-2023 | 1 | `flash`,`kernel` | 基石 |
| 2307.08691 | FlashAttention-2 | 2023 Q3 | 2 | `flash` | — |
| 2407.02064 | FlashAttention-3 | 2024 Q3 | 1 | `flash`,`hopper` | H100 |
| — | FlashAttention-4 | 2025+ | 2 | `flash` | ⚠️ 仅演讲/GitHub，`source_url` 占位 |
| 2309.06180 | PagedAttention (vLLM) | 2023 Q3 | 1 | `paged`,`serving` | 推理系统代表 |
| 2410.04005 | SpecAttn | 2024 Q4 | 2 | `speculative`,`kernel` | — |

#### 2-C：解码策略（改变前向次数）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2302.01318 | Speculative Decoding | 2023 Q1 | 1 | `speculative` | Google 提出 |
| 2401.10774 | Medusa | 2024 Q1 | 2 | `speculative`,`multi-head` | — |
| 2402.02057 | Lookahead Decoding | 2024 Q1 | 2 | `speculative`,`parallel` | — |
| 2401.15077 | EAGLE | 2024 Q1 | 2 | `speculative` | — |

### Lane 3 — 参数规模化（MoE）

#### 3-A：MoE 基础设施（稀疏激活的基础范式与算子）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2006.16668 | GShard | pre-2023 | 2 | `moe`,`google` | 基石 |
| 2101.03961 | Switch Transformer | pre-2023 | 1 | `moe` | 范式 |
| 2211.15841 | Megablocks | pre-2023 | 2 | `moe`,`kernel` | 块稀疏算子 |

#### 3-B：路由与负载均衡（专家路由策略）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2202.09368 | Expert Choice MoE | pre-2023 | 2 | `moe`,`routing` | token→expert 反转 |
| 2401.06066 | DeepSeek-MoE | 2024 Q1 | 2 | `moe`,`routing` | fine-grained + shared experts |

#### 3-C：工业集成（产品级 MoE 模型）
| arXiv | 论文 | Q | tier | tags | 备注 |
|---|---|---|---|---|---|
| 2401.04088 | Mixtral 8x7B | 2024 Q1 | 1 | `moe`,`open-source` | 商业拐点 |
| 2412.19437 | DeepSeek-V3 | 2024 Q4 | — | — | ⚠️ 见 Lane 2-A，本 lane 不重复渲染，仅 tag 体现跨 lane |

### Phase 2 预留（不进本期）

**Reasoning 策略类**（2025 起最大 alpha，但抽象层级与架构问题不同）：
- 2305.10601 Tree of Thoughts
- 2303.17651 Self-Refine
- 2303.11366 Reflexion
- 2308.09687 Graph of Thoughts
- 2501.12948 DeepSeek-R1（基于 V3，届时引入时加跨 lane 引用）
- o1（无 arXiv，OpenAI blog）

**World Model / 多模态记忆**（PRD 提及的 Demo 2 优先方向，但与 LLM 架构 lane 抽象层级不同，独立 spec 展开）：
- 2311.16118 Sparse World Models
- 2412.01506 Trellis

### 待澄清清单
1. ~~**无 arxiv 论文怎么处理**~~ → 纳入。`arxiv_id` 可空，用 `source_url` 回退至官方 GitHub / 技术博客（2026-05-07 确认）
2. ~~**pre-2023 根节点是否显示**~~ → 画布最左端加 "Before 2023" 聚合列，节点 `is_pre_2023: true`（2026-05-07 确认）
3. ~~**Reasoning 论文处理**~~ → Phase 2 以 tag 形式引入，MVP 不入库（2026-05-07 确认）
4. ~~**DeepSeek-V3 归属**~~ → Lane 2-A（主创新是 MLA），tags 含 `moe`；Lane 3 仅占位说明，不重复渲染（2026-05-07 确认）
5. ~~**Jamba 归属**~~ → Lane 1-A（主创新是 Hybrid SSM），tags 含 `moe`（2026-05-07 确认）
