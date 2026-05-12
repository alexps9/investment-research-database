# 技术判断面板 — Task 分解

> Epic: 从 Demo 硬编码到自动化生成
> 参考 Spec: tech-assessment-panel-spec.md
> 拆分策略: 数据模型 → 数据源 → 处理层 → 业务逻辑 → API 层

---

## 前置条件

- [ ] Claude API key 已配置 (`ANTHROPIC_API_KEY`)
- [ ] Semantic Scholar API 可用（无 key 也支持 30 篇）
- [ ] 30 篇论文的 OpenAlex Work ID 已查询完成

---

## Phase 1: 数据模型和种子数据 (依赖最少)

### Task 1.1: Paper Model 扩展

**目标**: 支持引用增速计算和arXiv ID识别

**涉及文件**:
- `backend/app/models/schemas.py` — 修改 `Paper` 类
- `backend/app/services/openalex_client.py` — 修改 `_parse_work()` 方法

**关键改动**:

```python
# schemas.py: Paper 类新增字段
class Paper(BaseModel):
    # 现有字段...
    counts_by_year: List[Dict[str, int]] = []  # [{year: 2024, cited_by_count: 150}, ...]
    arxiv_id: Optional[str] = None  # 从 DOI 提取或直接传入
```

```python
# openalex_client.py: _parse_work() 新增提取逻辑
def _parse_work(self, work: dict) -> Paper:
    # 现有逻辑...
    # 新增：提取 counts_by_year
    counts_by_year = work.get('counts_by_year', [])
    # 新增：从 primary_location.landing_page_url 提取 arxiv_id
    arxiv_id = self._extract_arxiv_id(work)
    return Paper(..., counts_by_year=counts_by_year, arxiv_id=arxiv_id)

def _extract_arxiv_id(self, work: dict) -> Optional[str]:
    # 从 https://arxiv.org/abs/2205.14135 提取 2205.14135
    # 或从 doi 包含 arXiv: 前缀提取
    pass
```

**依赖**: 无

**验收标准**:
- [ ] Paper.counts_by_year 被正确提取和存储
- [ ] Paper.arxiv_id 从 OpenAlex 元数据中提取成功
- [ ] 现有测试不破裂，新字段能正确序列化

**测试命令**:
```bash
pytest backend/tests/test_schemas.py::test_paper_model_extended -v
pytest backend/tests/test_openalex_client.py::test_parse_work_extracts_counts_by_year -v
```

---

### Task 1.2: SeedPaper 数据扩展到 30 篇

**目标**: 将 10 篇种子论文扩展到 30 篇，按 Lane + Tier 组织

**涉及文件**:
- `backend/app/data/seed_papers.py` — 扩展数据和结构

**关键改动**:

```python
# seed_papers.py: 新增 tier 字段和 lane 信息
from typing import Literal

class SeedPaper(BaseModel):
    work_id: str
    title: str
    year: int
    path: str
    tier: Literal[1, 2] = 1  # 新增
    lane: Literal["attention", "ssm", "rnn_linear", "moe"] = None  # 新增

# 30 篇论文数据
SEED_PAPERS_EXTENDED = [
    # Lane 1: Attention 优化主干
    SeedPaper(work_id="W1706.03762", title="Attention Is All You Need", year=2017, 
              path="attention_evolution", tier=1, lane="attention"),
    SeedPaper(work_id="W2005.14165", title="GPT-3", year=2020, 
              path="attention_evolution", tier=1, lane="attention"),
    # ... 其他 28 篇
]
```

**关键数据**:
```
Lane 1: Attention 优化主干 (6篇)
- Tier 1: Attention Is All You Need (2017), GPT-3 (2020), FlashAttention (2022), DeepSeek-V3 (2024)
- Tier 2: BERT (2018), Longformer (2020), RoPE (2021), ALiBi (2021), FlashAttention-2 (2023), Ring Attention (2024)

Lane 2: 状态空间模型 SSM (7篇)
- Tier 1: S4 (2021), Mamba (2023), Jamba (2024)
- Tier 2: HiPPO (2020), H3 (2022), Mamba-2 (2024), Griffin (2024)

Lane 3: 循环与线性架构 (7篇)
- Tier 1: RWKV (2023), xLSTM (2024)
- Tier 2: Linear Transformer (2020), RetNet (2023), TTT Layers (2024), Eagle (2024), HGRN (2023)

Lane 4: 专家混合与规模化 MoE (6篇)
- Tier 1: Switch Transformer (2021), Mixtral 8x7B (2024)
- Tier 2: GShard (2020), DeepSeek-MoE (2024), Expert Choice MoE (2022), Megablocks (2022)
```

**依赖**: Task 1.1 完成（需要 Paper model 支持新字段）

**验收标准**:
- [ ] 30 篇论文数据完整，包含 Work ID / title / year / tier / lane
- [ ] Work ID 已验证可从 OpenAlex 获取
- [ ] 能加载无误，支持按 lane 和 tier 过滤

**测试命令**:
```bash
pytest backend/tests/test_seed_papers.py::test_load_30_papers -v
pytest backend/tests/test_seed_papers.py::test_filter_by_lane_and_tier -v
```

---

## Phase 2: 数据源集成 (新增客户端)

### Task 2.1: Semantic Scholar 客户端

**目标**: 补充 OpenAlex 缺失的引用数据

**涉及文件**:
- `backend/app/services/semantic_scholar_client.py` — 新增文件
- `backend/tests/test_semantic_scholar_client.py` — 新增测试

**关键签名**:

```python
class SemanticScholarClient:
    async def search_by_title(self, title: str) -> Optional[str]:
        """搜索论文，返回 SS paper ID"""
        pass
    
    async def search_by_arxiv_id(self, arxiv_id: str) -> Optional[str]:
        """通过 arXiv ID 搜索论文"""
        pass
    
    async def fetch_references(self, paper_id: str) -> List[Dict]:
        """获取论文引用的参考文献"""
        # 返回 [{paper_id, title, year, ...}, ...]
        pass
    
    async def fetch_citations(self, paper_id: str) -> List[Dict]:
        """获取引用该论文的论文"""
        pass
```

**API限制**:
- 无 key: 100 req/5min
- 有 key: 1000 req/5min
- 30 篇论文 = 30 次请求，在限额内

**依赖**: 无

**验收标准**:
- [ ] 能成功搜索和获取论文引用数据
- [ ] 支持 retry 和错误处理（timeout/rate limit/not found）
- [ ] 单元测试覆盖率 > 80%（包括 mock 测试）

**测试命令**:
```bash
pytest backend/tests/test_semantic_scholar_client.py -v
```

---

## Phase 3: 引用解析层 (多源融合)

### Task 3.1: Citation Resolver (多源引用获取)

**目标**: 实现三层 fallback: OpenAlex → Semantic Scholar → 文献耦合

**涉及文件**:
- `backend/app/services/citation_resolver.py` — 新增文件
- `backend/tests/test_citation_resolver.py` — 新增测试

**关键签名**:

```python
class CitationResolver:
    async def resolve_paper_references(self, paper: Paper) -> List[Reference]:
        """
        多源引用获取 (优先级)
        1. OpenAlex referenced_works
        2. Semantic Scholar API (如果 OpenAlex 为空)
        3. 文献耦合 (计算共同引用)
        返回 [{target_id, source_type: 'openalex'|'semantic_scholar'|'coupling'}, ...]
        """
        pass
    
    async def compute_bibliographic_coupling(
        self, paper1: Paper, paper2: Paper, min_overlap: int = 3
    ) -> Optional[CouplingRelation]:
        """
        两篇论文共同引用 K 篇相同参考文献 → 耦合强度 = K
        K ≥ min_overlap 则建立 coupling 边
        """
        pass
```

**依赖**: Task 2.1 (Semantic Scholar 客户端)

**验收标准**:
- [ ] Fallback 逻辑正确，优先级符合规范
- [ ] 文献耦合计算准确
- [ ] 返回结果标注 source_type
- [ ] 单元测试 > 80%

**测试命令**:
```bash
pytest backend/tests/test_citation_resolver.py -v
```

---

## Phase 4: 业务逻辑层 (半自动模块)

### Task 4.1: Assessment Service (F3.1-F3.4 自动模块)

**目标**: 实现技术判断面板的 7 个模块中的前 4 个（不需要 LLM）

**涉及文件**:
- `backend/app/models/assessment.py` — 新增文件，定义 TechAssessment 数据模型
- `backend/app/services/assessment_service.py` — 新增文件
- `backend/tests/test_assessment_service.py` — 新增测试

**数据模型**:

```python
# assessment.py
class TitleSection(BaseModel):
    title: str
    authors: List[str]
    year: int
    doi: str

class CorePlayer(BaseModel):
    name: str
    affiliation: str
    paper_count: int
    citation_count: int

class CurrentStage(BaseModel):
    stage: Literal["Early", "Growth", "Mature"]
    growth_rate: float  # YoY %
    period: str  # "最近12个月"

class TechEvolution(BaseModel):
    predecessors: List[str]  # 论文标题
    current: str
    successors: List[str]

class TechAssessment(BaseModel):
    """7个模块聚合"""
    title_section: TitleSection
    core_players: List[CorePlayer]
    current_stage: CurrentStage
    tech_evolution: TechEvolution
    # F3.5-F3.7 待后续补充
```

**关键签名**:

```python
class AssessmentService:
    async def generate_assessment(self, paper: Paper, lane_papers: List[Paper]) -> TechAssessment:
        """生成完整技术判断面板"""
        pass
    
    def _extract_title_section(self, paper: Paper) -> TitleSection:
        """F3.1: 标题区 (自动)"""
        pass
    
    def _extract_core_players(self, papers: List[Paper]) -> List[CorePlayer]:
        """F3.2: 核心玩家 (自动)"""
        pass
    
    def _analyze_current_stage(self, paper: Paper) -> CurrentStage:
        """F3.3: 当前阶段 (引用增速)"""
        # 使用规则判断: 增速 > 200% → Growth, < 30% 且总引用 > 1000 → Mature, ...
        pass
    
    def _analyze_tech_evolution(
        self, paper: Paper, references: List[Reference], lane_papers: List[Paper]
    ) -> TechEvolution:
        """F3.4: 技术演进 (前驱/后续)"""
        pass
```

**依赖**: Task 1.1, Task 3.1

**验收标准**:
- [ ] 4 个模块各自实现正确，逻辑清晰
- [ ] 规则判断符合 spec（如增速阈值）
- [ ] 单元测试 > 80%
- [ ] 端到端: 选 3 篇论文跑通全流程

**测试命令**:
```bash
pytest backend/tests/test_assessment_service.py -v
pytest backend/tests/test_assessment_service.py::test_end_to_end_three_papers -v
```

---

## Phase 5: LLM 模块 (可选，暂不急)

### Task 5.1: LLM Client 和社区命名

**目标**: Claude API 客户端，用于社区命名、技术定位、瓶颈分析

**涉及文件**:
- `backend/app/services/llm_client.py` — 新增文件
- `backend/app/models/assessment.py` — 扩展 TechAssessment

**关键签名**:

```python
class LLMClient:
    async def generate_community_names(self, papers: List[Paper]) -> List[str]:
        """LLM读社区内论文标题生成语义标签"""
        pass
    
    async def analyze_tech_position(self, paper: Paper, predecessors: List[Paper]) -> TechPosition:
        """F3.5: 技术定位 (LLM)"""
        pass
    
    async def analyze_bottlenecks(self, paper: Paper, predecessors: List[Paper]) -> Bottleneck:
        """F3.6: 瓶颈分析 (LLM)"""
        pass
    
    async def generate_conclusion(self, assessment: PartialAssessment) -> str:
        """F3.7: 结论生成 (LLM)"""
        pass
```

**依赖**: Task 4.1, Task 1.1

**备注**: 此 Task 延后执行，先完成 Phase 1-4

---

## Phase 6: API 层 (最上层)

### Task 6.1: Assessment API 端点

**目标**: 暴露 3 个新 API 端点，实现自动生成技术判断面板

**涉及文件**:
- `backend/app/api/routes.py` — 修改/新增

**关键端点**:

```python
# GET /api/assess/{paper_id}?mode=auto
# 输入: OpenAlex Work ID 或 arXiv ID
# 输出: TechAssessment (7个模块)
async def assess_paper(paper_id: str, mode: str = "auto"):
    pass

# GET /api/assess/lane/{lane_index}
# 输入: lane 编号 (0-3)
# 输出: lane 中所有 tier-1 论文的 assessment 汇总
async def assess_lane(lane_index: int):
    pass

# GET /api/network/auto?paper_ids=W1706.03762,W2205.14135
# 输入: 论文 ID 列表 (逗号分隔)
# 输出: GraphResponse (nodes + links, 每条link标注source_type)
async def auto_network(paper_ids: str):
    pass
```

**依赖**: Task 4.1, Task 1.2

**验收标准**:
- [ ] 3 个端点均能接收请求、调用业务层、返回正确数据结构
- [ ] 支持缓存策略 (TTL 24h)
- [ ] 端到端测试覆盖主要用例
- [ ] API 文档清晰

**测试命令**:
```bash
pytest backend/tests/test_api_assess.py -v
```

---

## 执行顺序和并行性

```
Phase 1 (串行)
  ├─ Task 1.1: Paper Model 扩展 ✓
  └─ Task 1.2: SeedPaper 数据 (依赖 1.1)

Phase 2 (可并行)
  └─ Task 2.1: Semantic Scholar 客户端 ✓

Phase 3 (串行)
  └─ Task 3.1: Citation Resolver (依赖 2.1)

Phase 4 (串行)
  └─ Task 4.1: Assessment Service (依赖 1.1, 3.1)

Phase 5 (延后)
  └─ Task 5.1: LLM 模块 (依赖 4.1) — 暂不急

Phase 6 (串行)
  └─ Task 6.1: API 端点 (依赖 4.1, 1.2)
```

**并行执行推荐**:
- Task 1.1 和 1.2 串行 (1.2 依赖 1.1)
- Task 1.x 完成后，Task 2.1 可独立开始
- Task 1.x + 2.1 并行完成后，Task 3.1 开始
- 最终串行到 Phase 6

**预期周期**: ~2-3 周 (不含 LLM 模块)

---

## 输入论文数据注册

**用户输入样式**: 论文名字、arXiv ID、发表年份

**需要补充的信息**: OpenAlex Work ID

**查询方式**:
1. arXiv 预印本: `https://arxiv.org/search/?query={id}&searchtype=all` 获取完整元数据
2. OpenAlex 搜索: `https://api.openalex.org/works?search={title}`
3. Semantic Scholar 搜索: `https://www.semanticscholar.org/search?q={title}`

**建议**: Task 1.2 执行时，逐篇查询 Work ID 并补充到 `seed_papers.py`

---

## 知识库参考

| 文件 | 用途 |
|------|------|
| tech-assessment-panel-spec.md | 完整需求规范 |
| citation_network.py | Louvain 社区检测逻辑（可复用） |
| openalex_client.py | OpenAlex API 调用模式（参考） |
| seed_network_service.py | 现有 seed 网络构建（参考） |

---

## 待确认事项

- [ ] Anthropic API key 位置确认
- [ ] 是否需要 Semantic Scholar API key
- [ ] LLM 输出语言偏好（中文/英文）
- [ ] 30 篇论文的 OpenAlex Work ID 是否已查齐
