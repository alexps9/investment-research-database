# MVP2：语义相似度验证（SPECTER2 + 文献耦合）

## Context

MVP1 用引用关系构建论文知识图谱，假设"互相引用 ≈ 技术相关"。MVP2 要验证这个假设：
- 用 SPECTER2 嵌入（Semantic Scholar 预计算，768 维，不需要本地模型）计算论文语义距离
- 用文献耦合（共同参考文献数）计算方法论相似度
- 对比两种距离与引用关系的相关性，验证 MVP1 的有效性

MVP 范围：取 transformer 搜索结果的前 20 篇论文，快速验证，后端 API + 前端连线粗细体现语义距离。

---

## 技术方案

### 方案一：SPECTER2（语义向量）

**数据来源**：Semantic Scholar API（预计算好，直接调用）

**ID 映射**：OpenAlex ID → Semantic Scholar 通过 DOI 或 arXiv ID 查找
- Paper 对象已有 `doi` 字段
- 批量查询：`POST /graph/v1/paper/batch?fields=title,embedding`
- 支持 `DOI:10.xxx/xxx` 或 `ARXIV:xxxx.xxxxx` 格式

**相似度计算**：余弦相似度 = dot(v1, v2) / (|v1| × |v2|)，值域 [-1, 1]，越高越相似

**Rate limit**：免费 100 req/5min，20 篇论文一次 batch 搞定

### 方案二：文献耦合（方法论向量）

**纯图计算，不需要外部 API**

```python
# 对每对论文 (A, B)
shared_refs = len(refs(A) ∩ refs(B))
jaccard = shared_refs / len(refs(A) ∪ refs(B))  # 归一化
```

NetworkX 直接从已有引用图计算，无需额外数据。

### 验证假设

1. **引用 → 语义**：互相引用的论文对，SPECTER2 相似度均值 > 不引用的论文对
2. **耦合 → 语义**：文献耦合强度与 SPECTER2 相似度的 Pearson 相关系数 > 0.3
3. **社区 → 语义**：同 Louvain 社区论文对的相似度均值 > 跨社区论文对

---

## 实现计划

### 后端变更

#### 1. 新增 service：`backend/app/services/semantic_similarity.py`

```python
class SemanticSimilarityService:
    async def fetch_specter2_embeddings(
        self, papers: List[Paper]
    ) -> Dict[str, List[float]]:
        """
        批量从 Semantic Scholar 获取 SPECTER2 嵌入向量
        映射逻辑：paper.doi → DOI:xxx 或 title search fallback
        返回 {paper_id: embedding_vector}
        """

    def compute_cosine_similarity(
        self, emb1: List[float], emb2: List[float]
    ) -> float:
        """余弦相似度，值域 [-1,1]"""

    def compute_bibliographic_coupling(
        self, papers: List[Paper]
    ) -> Dict[Tuple[str, str], float]:
        """
        文献耦合：共同参考文献 Jaccard 系数
        纯图计算，不需要外部 API
        返回 {(id_a, id_b): jaccard_score}
        """

    def compute_similarity_matrix(
        self,
        embeddings: Dict[str, List[float]],
        coupling: Dict[Tuple[str, str], float],
        alpha: float = 0.7  # SPECTER2 权重，1-alpha = 耦合权重
    ) -> Dict[Tuple[str, str], SimilarityScore]:
        """组合两种相似度"""
```

#### 2. 新增 schema：`SimilarityScore`, `SimilarityEdge`, `SimilarityResponse`

```python
class SimilarityScore(BaseModel):
    specter2: Optional[float]       # SPECTER2 余弦相似度
    bibliographic_coupling: float   # 文献耦合 Jaccard
    combined: float                 # 加权组合

class SimilarityEdge(BaseModel):
    source: str
    target: str
    score: SimilarityScore

class SimilarityResponse(BaseModel):
    edges: List[SimilarityEdge]     # 仅返回 combined > threshold 的边
    verification: VerificationStats # 验证假设的统计结果

class VerificationStats(BaseModel):
    cited_pairs_mean_similarity: float    # 有引用关系的论文对均值
    uncited_pairs_mean_similarity: float  # 无引用关系的论文对均值
    same_community_mean: float
    cross_community_mean: float
    coupling_specter_correlation: float   # Pearson 相关系数
    hypothesis_1_passed: bool   # 引用 → 语义
    hypothesis_2_passed: bool   # 耦合 → 语义
    hypothesis_3_passed: bool   # 社区 → 语义
```

#### 3. 新增路由：`GET /api/similarity`

```
GET /api/similarity?query=transformer&limit=20
```

- `limit` 默认 20（MVP 验证用，SPECTER2 一次 batch 搞定）
- 先调 `/api/search` 逻辑获取论文和引用图
- 再调 `SemanticSimilarityService` 计算
- 返回 `SimilarityResponse`

### 前端变更

#### 4. `frontend/src/types/api.ts`

新增 `SimilarityEdge`、`SimilarityResponse` 类型

#### 5. `frontend/src/components/ForceGraph.tsx`

在**引用聚类视图**下：
- `linkWidth`：从 1 改为按 `score.combined` 映射（0.5 → 2px 细，1.0 → 4px 粗）
- `linkColor`：相似度高的边加橙色色调（`rgba(255, 100, 30, opacity)`）
- 仅当 `similarityEdges` prop 存在时启用，否则保持原有渲染

#### 6. `frontend/src/app/page.tsx`

- 搜索完成后，自动异步调用 `/api/similarity?query=...&limit=20`
- 将结果传给 `ForceGraph`
- 侧栏底部加 `VerificationStats` 面板（简单文字，3 个假设是否通过）

---

## 文件改动清单

| 文件 | 变更类型 |
|------|---------|
| `backend/app/services/semantic_similarity.py` | 新建 |
| `backend/app/models/schemas.py` | 新增 SimilarityScore / SimilarityEdge / SimilarityResponse / VerificationStats |
| `backend/app/api/routes.py` | 新增 GET /api/similarity |
| `backend/requirements.txt` | 新增 numpy, scikit-learn（余弦相似度计算） |
| `backend/tests/test_semantic_similarity.py` | 新建（TDD） |
| `frontend/src/types/api.ts` | 新增类型 |
| `frontend/src/components/ForceGraph.tsx` | 新增 similarityEdges prop，连线粗细/颜色 |
| `frontend/src/app/page.tsx` | 异步调 /api/similarity，传递结果，显示验证统计 |

---

## 关键实现细节

### ID 映射策略（OpenAlex → Semantic Scholar）

```python
def _build_s2_id(paper: Paper) -> Optional[str]:
    if paper.doi:
        return f"DOI:{paper.doi}"
    # fallback: 从 OpenAlex ID 的 arXiv 外链推断（可选）
    return None
# 无法映射的论文：跳过 SPECTER2，只用文献耦合
```

### SPECTER2 Batch 调用

```python
# 一次最多 500 篇，20 篇 MVP 一次即可
POST /graph/v1/paper/batch?fields=title,embedding
{"ids": ["DOI:10.48550/arXiv.1706.03762", ...]}
# embedding.vector 是 768 维 float list
```

### 验证输出示例

```
假设 1（引用 → 语义）：✅ 通过
  - 有引用的论文对平均相似度：0.72
  - 无引用的论文对平均相似度：0.41
  - 差值：+0.31

假设 2（耦合 → 语义）：✅ 通过
  - Pearson r = 0.58（p < 0.01）

假设 3（社区 → 语义）：✅ 通过
  - 同社区均值：0.68，跨社区均值：0.39
```
