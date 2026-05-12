# 技术判断面板 — Task 分解 (v2 + 50篇论文库)

> Epic: 从 Demo 硬编码到自动化生成
> 参考 Spec: tech-assessment-panel-spec.md
> 论文库: 50篇（5个 Lane，每个 Lane 8-12篇）
> 更新: 核心模型是「5 Lane」而非之前的「4 Lane」，Hybrid 架构独立成一个 Lane，且标记为「🔥最重要」

---

## 论文库组织 (50篇，按 Lane + Tier 分组)

### Lane 0: Attention 优化主干 (10篇)
核心逻辑：**不是替代，而是 patch Transformer**

| Tier | 论文名称 | arXiv | 年份 |
|------|--------|-------|------|
| 1 | Attention Is All You Need (Vaswani) | 1706.03762 | 2017 |
| 1 | GPT-3 (Brown et al.) | 2005.14165 | 2020 |
| 1 | FlashAttention (Dao) | 2205.14135 | 2022 |
| 1 | DeepSeek-V3 (MLA) | 2412.19437 | 2024 |
| 2 | FlashAttention-2 | 2307.08691 | 2023 |
| 2 | Ring Attention | 2310.01889 | 2023 |
| 2 | LongRoPE | 2402.13753 | 2024 |
| 2 | YaRN | 2309.00071 | 2023 |
| 2 | StreamingLLM | 2309.17453 | 2023 |
| 2 | Infini-Attention | 2404.07143 | 2024 |

**投研意义**：Transformer 并没有被替代，而是在持续"工程优化"。所有性能改进都是围绕 attention 机制本身的优化，而非架构替代。

---

### Lane 1: SSM / Mamba 系列 (10篇)
核心逻辑：**线性复杂度 + 状态递推**

| Tier | 论文名称 | arXiv | 年份 |
|------|--------|-------|------|
| 1 | Mamba | 2312.00752 | 2023 |
| 1 | Mamba-2 | 2405.21060 | 2024 |
| 1 | Mamba-3 | 2603.15569 | 2026 |
| 1 | S4 | 2111.00396 | 2021 |
| 2 | S5 | 2208.xxxxx | 2022 |
| 2 | H3 | 2310.xxxxx | 2022 |
| 2 | Hyena | 2302.10866 | 2023 |
| 2 | Hyena Hierarchy | 2306.xxxxx | 2023 |
| 2 | ReMamba | 2408.15496 | 2024 |
| 2 | Selective SSM | 2403.xxxxx | 2024 |

**核心 Insight**：Mamba 的关键不是 linear，而是 **selective mechanism**。这是区别于 S4 的核心创新。

---

### Lane 2: Hybrid 架构 (12篇) 🔥**最重要**
核心逻辑：**现实世界主流，从"尝试" → "工业默认方案"**

| Tier | 论文名称 | arXiv | 年份 |
|------|--------|-------|------|
| 1 | Jamba | 2403.19887 | 2024 |
| 1 | Jamba-1.5 | 2408.12570 | 2024 |
| 1 | TransMamba | 2503.24067 | 2025 |
| 1 | Nemotron-H | 2504.03624 | 2025 |
| 1 | HTMNet | 2505.20904 | 2025 |
| 2 | MaTVLM (VLM) | 2503.13440 | 2025 |
| 2 | MaBERT | 2603.03001 | 2026 |
| 2 | Mamba-Transformer Summarization | 2603.01288 | 2026 |
| 2 | MamTra | 2603.12342 | 2026 |
| 2 | Dimba (diffusion) | 2406.01159 | 2024 |
| 2 | Griffin | 2402.xxxxx | 2024 |
| 2 | xLSTM | 2405.xxxxx | 2024 |

**非常重要结论**：Hybrid 已经从"尝试" → "工业默认方案"。Jamba-1.5、Nemotron-H、HTMNet 等来自各大厂的生产级模型，都采用了 Transformer + Mamba 或 RNN + Attention 的混合架构。这是最有投研价值的方向。

---

### Lane 3: Memory / Long Context (10篇)
核心逻辑：**真正 bottleneck，所有架构竞争的本质**

| Tier | 论文名称 | arXiv | 年份 |
|------|--------|-------|------|
| 1 | Transformer-XL | 1901.02860 | 2019 |
| 1 | RETRO | 2112.04426 | 2021 |
| 1 | Memorizing Transformer | 2203.08913 | 2022 |
| 1 | LongNet | 2307.02486 | 2023 |
| 1 | RWKV | 2305.13048 | 2023 |
| 1 | RetNet | 2307.08621 | 2023 |
| 2 | Infini-attention | 2404.07143 | 2024 |
| 2 | StreamingLLM | 2309.17453 | 2023 |
| 2 | Kimi Linear Attention | 2310.xxxxx | 2023 |
| 2 | Long-context Benchmark | 2402.xxxxx | 2024 |

**投研意义**：所有架构竞争，本质是 memory competition。上下文长度已经成为模型竞争力的核心指标。

---

### Lane 4: Inference / Reasoning / Test-time Compute (8篇)
核心逻辑：**2025–2026 最重要趋势，推理成本与扩展**

| Tier | 论文名称 | arXiv | 年份 |
|------|--------|-------|------|
| 1 | Tree of Thoughts | 2305.10601 | 2023 |
| 1 | Graph of Thoughts | 2308.09687 | 2023 |
| 1 | Self-Refine | 2303.17651 | 2023 |
| 1 | Reflexion | 2303.11366 | 2023 |
| 1 | R1 (DeepSeek Reasoning) | 2501.xxxxx | 2025 |
| 2 | Tiny Recursive Reasoning | 2602.12078 | 2026 |
| 2 | Test-Time Scaling Law | 2407.xxxxx | 2024 |
| 2 | Attention → Mamba Distillation | 2604.14191 | 2026 |

**核心信号**：从 scaling 参数量转向 scaling test-time compute（推理步数）。DeepSeek-R1 的成功证明了这个方向的可行性。

---

## 数据库设计 — Paper 模型

```python
# backend/app/models/schemas.py

class Paper(BaseModel):
    # 基础信息
    id: str  # OpenAlex Work ID 或 arXiv ID
    title: str
    year: int
    authors: List[str]
    abstract: str
    
    # 新增字段 (来自 OpenAlex)
    counts_by_year: List[Dict[str, int]] = []  # [{year: 2024, cited_by_count: 150}, ...]
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    
    # 论文库分类
    lane: Literal[0, 1, 2, 3, 4]  # 0=Attention, 1=SSM, 2=Hybrid, 3=Memory, 4=Inference
    tier: Literal[1, 2] = 1  # 1=核心, 2=相关
    lane_name: str  # e.g., "Attention 优化主干", "Hybrid 架构 🔥"
    
    # 投研数据
    stage: Literal["Early", "Growth", "Mature"] = "Early"
    growth_rate: float = 0.0  # YoY %
    
    # 连接关系
    references: List[str] = []  # 引用的论文 ID
    cited_by: List[str] = []  # 被引用的论文 ID

class SeedPaper(BaseModel):
    """种子数据 (50篇标准库)"""
    work_id: str
    title: str
    year: int
    lane: int  # 0-4
    tier: Literal[1, 2]
    arxiv_id: str
```

---

## Task 执行顺序 (修订)

### Phase 1: 数据模型 + 种子数据 (串行)

#### Task 1.1: Paper Model 扩展 (5个新字段)
- 目标: 支持 lane/tier/counts_by_year/arxiv_id 等新字段
- 涉及文件: `schemas.py`, `openalex_client.py`
- 依赖: 无
- 验收标准: Paper 对象能正确序列化，新字段从 OpenAlex 提取

#### Task 1.2: SeedPaper 数据库初始化 (50篇)
- 目标: 写入 50 篇论文的元数据，按 lane/tier 组织
- 涉及文件: `backend/app/data/seed_papers_v2.py`
- 依赖: Task 1.1
- 验收标准: 50 篇论文数据完整，work_id 已验证，支持按 lane 和 tier 过滤

**关键任务**：逐篇查询 50 篇论文的 OpenAlex Work ID，并补充到数据库

| 分类 | 需要查询的论文数 | 预期时间 |
|------|---------|----------|
| Attention (10篇) | 10 | 15 min |
| SSM (10篇) | 10 | 15 min |
| Hybrid (12篇) | 12 | 20 min |
| Memory (10篇) | 10 | 15 min |
| Inference (8篇) | 8 | 12 min |
| **总计** | **50** | **~1 hour** |

**查询方法**:
```bash
# 使用 OpenAlex API
curl "https://api.openalex.org/works?search=FlashAttention&per_page=1" | jq

# 或使用 OpenAlex Python 客户端 (已有)
client.search_works(title="Mamba")
```

---

### Phase 2: 数据源集成 (可并行)

#### Task 2.1: Semantic Scholar 客户端
- 目标: 补充 OpenAlex 缺失的引用数据
- 涉及文件: `backend/app/services/semantic_scholar_client.py`
- 依赖: 无
- 验收标准: 能成功搜索和获取论文引用数据，支持 retry 和错误处理

---

### Phase 3: 引用解析层 (串行)

#### Task 3.1: Citation Resolver
- 目标: 实现三层 fallback (OpenAlex → Semantic Scholar → 文献耦合)
- 涉及文件: `backend/app/services/citation_resolver.py`
- 依赖: Task 2.1
- 验收标准: Fallback 逻辑正确，返回结果标注 source_type

---

### Phase 4: 业务逻辑层 (串行)

#### Task 4.1: Assessment Service (F3.1-F3.4)
- 目标: 实现 7 个模块中的前 4 个（不需要 LLM）
- 涉及文件: `backend/app/models/assessment.py`, `backend/app/services/assessment_service.py`
- 依赖: Task 1.1, Task 3.1
- 验收标准: 4 个模块各自实现正确，端到端跑通 3 篇论文

---

### Phase 5: LLM 模块 (延后，暂不急)

#### Task 5.1: LLM Client + 社区命名
- 目标: Claude API 集成，社区命名/技术定位/瓶颈分析
- 涉及文件: `backend/app/services/llm_client.py`, `backend/app/models/assessment.py`
- 依赖: Task 4.1
- **备注**: 可先实现 Phase 1-4 的完整工作流

---

### Phase 6: API 层 (串行)

#### Task 6.1: Assessment API 端点 (3 个新端点)
- 目标: 暴露 REST 接口，支持自动生成技术判断面板
- 涉及文件: `backend/app/api/routes.py`
- 依赖: Task 4.1
- 验收标准: 3 个端点均能接收请求、调用业务层、返回正确数据

---

### Phase 7: 前端更新 (并行可选)

#### Task 7.1: Demo 前端更新 (修改 demo-preview.html)
- 目标: 将 demo-preview.html 从 30 篇升级到 50 篇，支持 5 Lane 新分类
- 涉及文件: `.claude/docs/design/demo-preview.html`
- 依赖: Task 1.2 (SeedPaper 数据完整)
- 验收标准: Demo 能正确渲染 50 篇论文，Lane 切换正常，右侧面板 Tier-1 展示完整

**关键改动**:
- 从 4 Lane 扩展到 5 Lane（新增 Hybrid 作为独立 Lane）
- 每个 Lane 的色彩编码
- Lane 2 (Hybrid) 特殊标记为 🔥
- allPapers 数组从 30 篇扩展到 50 篇

---

## 前端演进参考

根据 `llm_arch_evolution_2023_2026.html` 的优点：

1. **时间线 + Lane 的清晰分离** — X 轴是时间（Q3 2023 → Q3 2026），Y 轴是 Lane
2. **Alpha 信号体系** — HIGH / MID / LOW 标记投研价值
3. **"NOW" 标记** — 当前时刻（Q2 2026），帮助理解发展阶段
4. **详情面板** — 点击节点展示完整信息

**前端 Task 优先级**：
- 【低】修改 demo-preview.html 的 allPapers 数据
- 【高】在主项目前端集成 Assessment API（Task 6.1 完成后）

---

## 执行里程碑

| 阶段 | Task | 预期周期 | 依赖阻塞 |
|------|------|---------|---------|
| **Week 1** | Task 1.1 + 1.2 + Task 2.1 并行 | 3 天 | OpenAlex Work ID 查询 |
| **Week 1-2** | Task 3.1 + 4.1 串行 | 4 天 | 数据源完整 |
| **Week 2-3** | Task 6.1 + (可选) 5.1 | 3 天 | 业务逻辑完整 |
| **Week 3** | Task 7.1 (Demo 前端更新) | 1 天 | SeedPaper 数据完整 |
| **总计** | 全部完成（不含 LLM） | ~2 周 | — |

---

## 关键决策与风险

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 5 Lane 分类 | 4 Lane(旧) vs 5 Lane(新) | 5 Lane | Hybrid 已成工业标准，需独立突出 |
| Hybrid Lane 标记 | 普通 vs 🔥特殊 | 🔥 | 投研价值最高，需视觉强调 |
| 50 篇数据源 | 硬编码 vs API 动态 | 硬编码 seed_papers.py | 稳定性高，便于版本管理 |
| Demo 更新方式 | 全新前端 vs 修改 HTML | 修改 HTML | 保留原 demo 演示，新增数据 |
| LLM 模块优先级 | 同步 vs 延后 | 延后 | Phase 1-4 不依赖 LLM，可先完成 |

---

## 输入法规范

用户可通过以下方式输入论文：

1. **论文名字** + **arXiv ID** → 系统自动查询 OpenAlex Work ID
2. **arXiv URL** → 解析出 arXiv ID，然后查询
3. **OpenAlex Work ID** → 直接使用

**示例**:
```
输入: "FlashAttention-2" + "2307.08691"
→ 查询 OpenAlex API
→ 找到 Work ID: W4376089890 (假设)
→ 写入 seed_papers.py
```

---

## 待确认

- [ ] 50 篇论文的 OpenAlex Work ID 是否需要我逐篇查询？
- [ ] demo-preview.html 中的 Tier 2 论文详情面板是否简化（只展示基本信息）？
- [ ] Hybrid Lane 是否需要在前端特殊渲染（如背景颜色不同）？
- [ ] 是否需要在 assessment 数据中标注"投研信号" (e.g., "Hybrid 已成工业标准")?

