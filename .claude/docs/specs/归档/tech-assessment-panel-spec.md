# 技术判断面板：从 Demo 到自动化

> status: propose
> created: 2026-04-30
> complexity: 🔴复杂

## 1. 背景与目标

**为什么做**：
demo-preview.html 验证了"技术判断面板"的交互形态——7 个模块让用户 3 分钟理解一条技术路线。
但数据全部写死，老板会问"能自动跑吗"。需要把写死数据替换为三层自动化数据源。

**做完后的效果**（验收标准）：
1. 输入一组论文 ID（或论文名字），系统自动生成技术判断面板
2. 面板 7 个模块中，~65% 内容自动填充（API + 规则），~35% 由 LLM 生成
3. 每条连线标注来源（citation / coupling / llm）
4. 30 篇论文全量跑通，面板内容与 Demo 写死版质量对齐
5. 单篇论文端到端延迟 < 10s（含 LLM 调用）

**不做的事**：
- 不做 SPECTER2 语义向量（Phase C，2500 篇时再做）
- 不做前端三栏布局重构（独立 spec）
- 不改 demo-preview.html（它继续作为演示原型）
- 不做用户输入界面（论文 ID 通过 API 传入）

## 2. 代码现状（Research Findings）

### 2.1 相关入口与链路

当前种子模式链路：
```
seed_papers.py 硬编码 10 个 Work ID + 路径标签
  → OpenAlexClient.fetch_works_by_ids() 批量获取元数据
  → seed_network_service.build_seed_network() 构建图
  → 手工 SEED_CITATIONS 定义引用边
  → 手工 PATH_NAMES 定义社区名称
  → insight_report_service.generate_report() 返回硬编码报告
```

### 2.2 现有实现

| 能力 | 文件 | 状态 |
|------|------|------|
| OpenAlex 论文获取 | `openalex_client.py:fetch_works_by_ids` (L198) | ✅ 可复用 |
| OpenAlex 引用获取 | `openalex_client.py:fetch_references` (L241) | ✅ 可复用 |
| 批量引用获取 | `openalex_client.py:fetch_all_references` (L285) | ✅ 可复用 |
| Abstract 重建 | `openalex_client.py:_parse_work` (L419) | ✅ 已实现 inverted_index 重建 |
| 引用网络构建 | `citation_network.py:build_network` (L49) | ✅ 可复用 |
| Louvain 社区检测 | `citation_network.py:calculate_communities` (L185) | ✅ 可复用 |
| 社区命名（TF-IDF） | `citation_network.py:_generate_community_names` (L289) | ���️ 质量不够，需 LLM 替代 |
| Paper model | `schemas.py:Paper` (L28) | ⚠️ 需扩展 |
| 硬编码报告 | `insight_report_service.py` | ❌ 需重写为动态生成 |
| 种子数据 | `seed_papers.py` | ⚠️ 需扩展到 30 篇 |

### 2.3 发现与风险

1. **OpenAlex 引用数据缺失严重**：arXiv 预印本的 `referenced_works` 经常为空。
   经 Semantic Scholar 验证，30 篇论文中约 40% 能拿到引用数据，60% 缺失。
   → 需要 Semantic Scholar API 作为补充数据源
2. **Louvain 社区命名无语义**：输出"社区 0/1/2"，不知道是"Attention 优化"还是"SSM"。
   现有 `_generate_community_names` 用 TF-IDF 从标题提取关键词，质量不稳定。
   → 需要 LLM 读社区内论文标题生成语义标签
3. **现有 Paper model 缺少 counts_by_year**：计算引用增速需要逐年引用数据，
   OpenAlex 提供但当前 `_parse_work` 没有提取。

## 3. 功能点

### F1：数据源扩展

- [ ] **F1.1 Semantic Scholar 客户端**
  - 输入：arXiv ID 或论文标题
  - 处理：新建 `semantic_scholar_client.py`
    - `search_by_title(title) -> paper_id`：标题搜索拿到 SS paper ID
    - `fetch_references(paper_id) -> List[Reference]`：获取引用列表
    - `fetch_citations(paper_id) -> List[Citation]`：获取被引列表
  - 输出：引用/被引关系，补充 OpenAlex 缺失数据
  - API：`GET /graph/v1/paper/ArXiv:{id}/references?fields=title,year`
  - 限流：100 req/5min（无 API key），1000 req/5min（有 key）

- [ ] **F1.2 Paper model 扩展**
  - 输入：OpenAlex API 返回的 `counts_by_year` 字段
  - 处理：`schemas.py:Paper` 新增字段：
    - `counts_by_year: List[dict] = []` — `[{year: 2024, cited_by_count: 150}, ...]`
    - `arxiv_id: Optional[str] = None` — 从 DOI 提取或直接传入
  - 输出：支持引用增速计算
  - 改动：`_parse_work` 提取 `counts_by_year` 和 `arxiv_id`

- [ ] **F1.3 种子数据扩展到 30 篇**
  - 输入：demo-preview.html 的 30 篇论文列表
  - 处理：`seed_papers.py` 扩展，新增 20 篇的 Work ID + 路径标签
    - 需要查 OpenAlex/SS 获取 Work ID（部分已在之前查过）
    - 新增 tier 字段：`tier: Literal[1, 2]`
  - 输出：30 篇完整种子配置

### F2：自动连线服务

- [ ] **F2.1 多源引用获取**
  - 输入：论文 ID 列表
  - 处理：新建 `citation_resolver.py`
    - 先查 OpenAlex `referenced_works`
    - 缺失则查 Semantic Scholar references
    - 返回合并结果，标注来源 `source: 'openalex' | 'semantic_scholar'`
  - 输出：`Dict[paper_id, List[{target_id, source}]]`

- [ ] **F2.2 文献耦合计算**
  - 输入：论文集合的引用列表
  - 处理：复用 `citation_network.py` 的图结构
    - 两篇论文共同引用 K 篇相同参考文献 → 耦合强度 = K
    - K ≥ 3 则建立 coupling 边
  - 输出：`List[{source, target, strength, source_type: 'coupling'}]`

- [ ] **F2.3 LLM 引用判断（fallback）**
  - 输入：两篇论文的 abstract
  - 处理：调用 Claude API
    - Prompt："论文 B 是否在技术上继承或改进了论文 A？回答 JSON: {related: bool, confidence: float, reason: string}"
  - 输出：`{related, confidence, reason}`
  - 触发条件：F2.1 和 F2.2 都没有建立边的论文对（同 lane 内）
  - 成本：~$0.005/对，30 篇同 lane 约 50-80 对 ≈ $0.40

### F3：技术判断面板数据生成

- [ ] **F3.1 标题区（✅ 自动）**
  - 输入：Paper 对象
  - 处理：直接取 title, author_names, publication_year, doi
  - 输出：标题区数据

- [ ] **F3.2 核心玩家（✅ 自动）**
  - 输入：某路径下所有 Paper 对象
  - 处理：
    - 按作者聚合论文数和引用数，排名
    - 按机构聚合，标注 academic/industry
  - 输出：`{core_researchers: [{name, affiliation, paper_count}], active_teams: [string]}`
  - 复用：现有 `Paper.author_names` + `Paper.institutions`

- [ ] **F3.3 当前阶段 — 引用增速（⚠️ 半自动）**
  - 输入：Paper.counts_by_year
  - 处理：
    - 计算最近 12 个月 YoY 增速：`(今年引用 - 去年引用) / 去年引用 * 100%`
    - 规则判断阶段：
      - `增速 > 200% → Growth`
      - `增速 < 30% 且总引用 > 1000 → Mature`
      - `总引用 < 100 → Early/Emerging`
  - 输出：`{stage, growth_rate, period}`

- [ ] **F3.4 技术演进 — 前驱/后续（⚠️ 半自动）**
  - 输入：论文的引用关系（F2 输出）+ 社区信息
  - 处理：
    - 前驱：从 referenced_works 中取同社区 + 高引用的 top 3
    - 后续：从 cited_by 中取同社区的论文，按年份排序
    - 分叉检测：被引论文中出现不同社区 = 分叉信号
  - 输出：`{predecessors: [string], current: string, successors: [string]}`

- [ ] **F3.5 技术定位（❌ LLM）**
  - 输入：论文 abstract + 前驱论文 abstracts + 社区内论文标题列表
  - 处理：Claude API 调用
    ```
    Prompt: 给定论文 B 的摘要和其前驱论文 A 的摘要，请分析：
    1. B 的技术角色（如：范式奠基者/工程优化者/混合架构先驱/...）
    2. B 对标的技术是什么
    3. B 与对标技术的核心差异（一句话）
    4. B 是否构成范式变化（true/false）
    输出 JSON 格式。
    ```
  - 输出：`{role, benchmark, core_diff, is_paradigm_shift}`
  - 同时用于社区命名：LLM 读社区内所有论文标题 → 生成语义标签

- [ ] **F3.6 瓶颈分析（❌ LLM）**
  - 输入：论文 abstract + 前驱论文 abstracts
  - 处理：Claude API 调用
    ```
    Prompt: 论文 B 在解决什么问题？
    1. 当前有哪些技术限制（列出 2-3 个）
    2. 什么是尚未解决的核心问题（一句话）
    输出 JSON 格式。
    ```
  - 输出：`{current_limitations: [string], unsolved: string}`

- [ ] **F3.7 结论（❌ LLM）**
  - 输入：F3.1-F3.6 的所有输出
  - 处理：Claude API 调用
    ```
    Prompt: 基于以下分析，用一句话总结这篇论文在技术路线中的位置。
    不要写投资建议，只写技术判断。
    ```
  - 输出：一句话结论

### F4：API 端点

- [ ] **F4.1 GET /api/assess/{paper_id}**
  - 输入：OpenAlex Work ID 或 arXiv ID
  - 处理：调用 F3.1-F3.7，聚合为完整面板数据
  - 输出：`TechAssessment` 对象（7 个模块）
  - 缓存：结果缓存到内存，相同 paper_id 不重复计算

- [ ] **F4.2 GET /api/assess/lane/{lane_index}**
  - 输入：lane 编号（0-3）
  - 处理：聚合该 lane 所有 tier-1 论文的 assessment
  - 输出：`LaneAssessment` 对象（路径级汇总）

- [ ] **F4.3 GET /api/network/auto**
  - 输入：论文 ID 列表（query param，逗号分隔）
  - 处理：F2.1-F2.3 自动连线 + Louvain 社区检测
  - 输出：`GraphResponse`，每条 link 带 `source_type` 标注

## 4. 业务规则

1. **三层数据源优先级**：API 事实 > 算法推断 > LLM 判断。高层数据不覆盖低层。
2. **LLM 输出标注**：所有 LLM 生成的内容标注 `generated_by: 'llm'`，前端可显示"AI 生成"标记。
3. **连线来源标注**：每条边标注 `source_type: 'citation' | 'coupling' | 'llm'`。
4. **引用数据 fallback**：OpenAlex 为空 → Semantic Scholar → 文献耦合 → LLM 判断。
5. **社区命名**：Louvain 聚类后，LLM 读社区内论文标题生成语义标签（不用 TF-IDF）。
6. **阶段判断规则**：增速 > 200% → Growth；增速 < 30% 且总引用 > 1000 → Mature；总引用 < 100 → Early。
7. **缓存策略**：assessment 结果按 paper_id 缓存，TTL 24h（论文元数据不会频繁变化）。

## 5. 数据变更

| 操作 | 模型/文件 | 字段/结构 | 说明 |
|------|-----------|-----------|------|
| 扩展 | `Paper` (schemas.py) | `counts_by_year: List[dict] = []` | 逐年引用数据 |
| 扩展 | `Paper` (schemas.py) | `arxiv_id: Optional[str] = None` | arXiv ID |
| 扩展 | `SeedPaper` (seed_papers.py) | `tier: Literal[1, 2] = 1` | 论文层级 |
| 扩展 | `Link` (schemas.py) | `source_type: str = 'citation'` | 连线来源标注 |
| 新增 | `TechAssessment` (models/assessment.py) | 7 个模块的聚合模型 | 面板完整数据 |
| 新增 | `LaneAssessment` (models/assessment.py) | 路径级汇总 | lane 面板数据 |

## 6. 接口变更

| 操作 | 接口 | 方法 | 变更内容 |
|------|------|------|----------|
| 新增 | `/api/assess/{paper_id}` | GET | 单篇论文技术判断面板 |
| 新增 | `/api/assess/lane/{lane_index}` | GET | 路径级汇总面板 |
| 新增 | `/api/network/auto` | GET | 自动连线网络（传入 paper_ids） |
| 不变 | `/api/seed-network` | GET | 保留，兼容旧前端 |
| 不变 | `/api/seed-report/{path}` | GET | 保留，兼容旧前端 |
| 不变 | `/api/search` | GET | 不变 |

## 7. 影响范围

### 后端新增文件
| 文件 | 用途 |
|------|------|
| `app/services/semantic_scholar_client.py` | Semantic Scholar API 客户端 |
| `app/services/citation_resolver.py` | 多源引用获取 + 文献耦合 + LLM fallback |
| `app/services/assessment_service.py` | 技术判断面板数据生成（7 模块） |
| `app/services/llm_client.py` | Claude API 调用封装 |
| `app/models/assessment.py` | TechAssessment / LaneAssessment 数据模型 |

### 后端修改文件
| 文件 | 改动 |
|------|------|
| `app/models/schemas.py` | Paper 新增 counts_by_year, arxiv_id；Link 新增 source_type |
| `app/services/openalex_client.py` | `_parse_work` 提取 counts_by_year 和 arxiv_id |
| `app/data/seed_papers.py` | 扩展到 30 篇，新增 tier 字段 |
| `app/api/routes.py` | 新增 3 个端点 |

### 不动的文件
- `citation_network.py` — Louvain 逻辑不变，直接复用
- `insight_report_service.py` — 保留兼容旧端点
- 前端所有文件 — 本 spec 只做后端

## 8. 风险与关注点

1. **Semantic Scholar 限流**：无 key 100 req/5min。30 篇论文获取引用需要 30 次请求，在限额内。扩展到 100+ 篇需要申请 API key。
2. **LLM 调用延迟**：Claude API 单次 ~2-5s。F3.5+F3.6+F3.7 串行 = ~10s/篇。可并行化 F3.5 和 F3.6 降到 ~7s。
3. **LLM 输出不稳定**：同一 prompt 多次调用可能输出不同结论。缓存 + temperature=0 缓解。
4. **Abstract 缺失**：部分论文无摘要（OpenAlex `abstract_inverted_index` 为 null）。LLM 模块 fallback 到只用标题。
5. **成本**：30 篇 × 3 次 LLM 调用 ≈ $0.30-0.50。可控。2500 篇 ≈ $25-40。

## 8.5 测试策略

- **测试范围**：
  - Semantic Scholar 客户端：mock HTTP 测试 + 集成测试（真实 API，标记 @integration）
  - citation_resolver：mock 测试三层 fallback 逻辑
  - assessment_service：mock LLM 输出，验证 7 模块聚合逻辑
  - 3 个新 API 端点：请求/响应测试
  - 端到端：选 3 篇论文（Mamba/FlashAttention/Mixtral）跑全链路
- **覆盖率目标**：新增代码 > 80%
- **独立 Test Spec**：否

## 9. 待澄清

- [ ] Claude API key 从哪里来？环境变量 `ANTHROPIC_API_KEY`？
- [ ] Semantic Scholar API key 是否需要申请？30 篇无 key 够用，100+ 需要。
- [ ] LLM 输出语言：中文还是英文？Demo 是中文，但 abstract 是英文。
  → 建议：LLM 输出中文（面向中文用户），输入保持英文 abstract。

## 10. 技术决策

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 引用数据补充 | 只用 OpenAlex / 加 SS / 加 LLM | OpenAlex + SS + LLM 三层 | OpenAlex 缺失率 60%，必须补充 |
| 社区命名 | TF-IDF / LLM | LLM | TF-IDF 质量不稳定，LLM 一次调用解决 |
| LLM 选择 | Claude / GPT-4 / 本地模型 | Claude (Haiku) | 成本低、速度快、结构化输出好 |
| 缓存 | 内存 / Redis / 文件 | 内存 dict | 30 篇数据量小，不需要 Redis |
| 连线 source_type | 只标注 / 不标注 | 标注 | 让用户判断可���度 |
| 并行策略 | 串行 / 并行 LLM 调用 | 并行 F3.5+F3.6，串行 F3.7 | F3.7 依赖前两者输出 |

## 11. 执行日志

| Task | 状态 | 实际改动文件 | 备注 |
|------|------|-------------|------|
| F1.1 Semantic Scholar 客户端 | 待开始 | `semantic_scholar_client.py` | — |
| F1.2 Paper model 扩展 | 待开始 | `schemas.py`, `openalex_client.py` | — |
| F1.3 种子数据扩展 30 篇 | 待开始 | `seed_papers.py` | 需查 Work ID |
| F2.1 多源引用获取 | 待开始 | `citation_resolver.py` | — |
| F2.2 文献耦合计算 | 待开始 | `citation_resolver.py` | — |
| F2.3 LLM 引用判断 | 待开始 | `citation_resolver.py`, `llm_client.py` | — |
| F3.1-F3.4 自动模块 | 待开始 | `assessment_service.py` | — |
| F3.5-F3.7 LLM 模块 | 待开始 | `assessment_service.py`, `llm_client.py` | — |
| F4.1-F4.3 API 端点 | 待开始 | `routes.py` | — |

## 12. 审查结论

（待 reviewer 审查后填写）

## 13. 确认记录（HARD-GATE）

- **确认时间**：
- **确认人**：
