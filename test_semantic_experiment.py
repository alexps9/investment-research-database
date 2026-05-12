"""
MVP2 技术验证脚本 — 独立运行，不影响项目代码
验证风险点：
1. Semantic Scholar batch API 能否通过 DOI 拿到 SPECTER2 embedding
2. OpenAlex 论文的 DOI 映射成功率
3. 相似度分布是否合理，三个假设能否初步验证

用法: python test_semantic_experiment.py
依赖: pip install httpx numpy (项目已有 httpx)
"""

import asyncio
import json
import time
from itertools import combinations
from typing import Optional

import httpx
import numpy as np


# ── 1. 从 OpenAlex 获取 transformer 前 20 篇 ──

async def fetch_openalex_papers(query: str = "transformer", limit: int = 20):
    """复制项目逻辑的简化版，只取核心字段"""
    async with httpx.AsyncClient(timeout=30) as client:
        # 先解析概念 ID
        r = await client.get(
            "https://api.openalex.org/concepts",
            params={"search": query, "per_page": 1},
        )
        r.raise_for_status()
        concepts = r.json().get("results", [])

        if not concepts:
            print(f"[WARN] 未找到概念 '{query}'，用关键词搜索 fallback")
            params = {
                "search": query,
                "filter": "type:article,publication_year:2015-2026",
                "sort": "cited_by_count:desc",
                "per_page": limit,
                "select": "id,title,cited_by_count,publication_year,referenced_works,doi",
            }
        else:
            concept_id = concepts[0]["id"]
            print(f"概念: {concepts[0]['display_name']} ({concept_id})")
            params = {
                "filter": f"concepts.id:{concept_id},type:article,publication_year:2015-2026",
                "sort": "cited_by_count:desc",
                "per_page": limit,
                "select": "id,title,cited_by_count,publication_year,referenced_works,doi",
            }

        r = await client.get("https://api.openalex.org/works", params=params)
        r.raise_for_status()
        results = r.json().get("results", [])

    papers = []
    for w in results:
        papers.append({
            "id": w["id"].split("/")[-1],
            "title": w.get("title", ""),
            "doi": w.get("doi"),
            "cited_by_count": w.get("cited_by_count", 0),
            "year": w.get("publication_year"),
            "reference_ids": [ref.split("/")[-1] for ref in (w.get("referenced_works") or [])],
        })
    return papers


# ── 2. Semantic Scholar batch 获取 SPECTER2 embedding ──

async def fetch_specter2_embeddings(papers: list):
    """
    风险点验证：
    - batch endpoint 是否可用
    - DOI 映射命中率
    - embedding 维度和质量
    """
    # 构建 S2 ID 列表
    s2_ids = []
    id_map = {}  # s2_id -> paper_id
    no_doi = []

    for p in papers:
        doi = p["doi"]
        if doi:
            # OpenAlex DOI 格式: https://doi.org/10.xxx/xxx
            doi_clean = doi.replace("https://doi.org/", "")
            s2_id = f"DOI:{doi_clean}"
            s2_ids.append(s2_id)
            id_map[s2_id] = p["id"]
        else:
            no_doi.append(p["title"])

    print(f"\n=== Semantic Scholar Batch 验证 ===")
    print(f"有 DOI: {len(s2_ids)}/{len(papers)}")
    if no_doi:
        print(f"无 DOI 的论文: {no_doi}")

    # 调用 batch API（S2 embedding 响应慢，需要长超时）
    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(3):
            try:
                r = await client.post(
                    "https://api.semanticscholar.org/graph/v1/paper/batch",
                    params={"fields": "title,embedding"},
                    json={"ids": s2_ids},
                )
                break
            except httpx.ReadTimeout:
                print(f"  [重试 {attempt+1}/3] S2 API 超时，等待 5s...")
                await asyncio.sleep(5)
        else:
            print("[RISK] S2 API 3 次超时，可能需要代理或 API key")
            return {}

    print(f"S2 API 状态码: {r.status_code}")

    if r.status_code == 429:
        print("[RISK] Rate limited! 免费 tier 100 req/5min 可能不够")
        return {}

    if r.status_code != 200:
        print(f"[RISK] API 返回错误: {r.text[:500]}")
        return {}

    results = r.json()
    embeddings = {}
    found = 0
    no_embedding = 0
    not_found = 0

    for i, item in enumerate(results):
        paper_id = id_map[s2_ids[i]]
        if item is None:
            not_found += 1
            continue
        emb = item.get("embedding")
        if emb and emb.get("vector"):
            embeddings[paper_id] = np.array(emb["vector"])
            found += 1
        else:
            no_embedding += 1

    print(f"命中: {found}, 无 embedding: {no_embedding}, 未找到: {not_found}")
    if found > 0:
        dim = len(next(iter(embeddings.values())))
        print(f"Embedding 维度: {dim}")

    return embeddings


# ── 3. 计算相似度 & 验证假设 ──

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_bibliographic_coupling(papers: list) -> dict:
    """文献耦合 Jaccard"""
    ref_sets = {p["id"]: set(p["reference_ids"]) for p in papers}
    paper_ids = [p["id"] for p in papers]
    coupling = {}
    for a, b in combinations(paper_ids, 2):
        ra, rb = ref_sets[a], ref_sets[b]
        union = ra | rb
        if union:
            coupling[(a, b)] = len(ra & rb) / len(union)
        else:
            coupling[(a, b)] = 0.0
    return coupling


def build_citation_pairs(papers: list) -> set:
    """构建论文集内的引用对"""
    paper_ids = {p["id"] for p in papers}
    cited = set()
    for p in papers:
        for ref in p["reference_ids"]:
            if ref in paper_ids:
                pair = tuple(sorted([p["id"], ref]))
                cited.add(pair)
    return cited


def verify_hypotheses(papers, embeddings, coupling, citation_pairs):
    print("\n=== 假设验证 ===")
    paper_ids = [p["id"] for p in papers if p["id"] in embeddings]

    # 所有有 embedding 的论文对
    all_pairs = list(combinations(paper_ids, 2))
    sims = {(a, b): cosine_sim(embeddings[a], embeddings[b]) for a, b in all_pairs}

    # 假设 1：引用 → 语义
    cited_sims = [sims[pair] for pair in all_pairs if tuple(sorted(pair)) in citation_pairs]
    uncited_sims = [sims[pair] for pair in all_pairs if tuple(sorted(pair)) not in citation_pairs]

    if cited_sims and uncited_sims:
        cited_mean = np.mean(cited_sims)
        uncited_mean = np.mean(uncited_sims)
        h1_pass = cited_mean > uncited_mean
        print(f"\n假设 1（引用 → 语义）: {'✅' if h1_pass else '❌'}")
        print(f"  有引用对均值: {cited_mean:.3f} ({len(cited_sims)} 对)")
        print(f"  无引用对均值: {uncited_mean:.3f} ({len(uncited_sims)} 对)")
        print(f"  差值: {cited_mean - uncited_mean:+.3f}")
    else:
        print(f"\n假设 1: 跳过 (cited_sims={len(cited_sims)}, uncited_sims={len(uncited_sims)})")

    # 假设 2：耦合 → 语义 (Pearson)
    coupling_vals = []
    specter_vals = []
    for pair in all_pairs:
        key = tuple(sorted(pair))
        if key in coupling:
            coupling_vals.append(coupling[key])
            specter_vals.append(sims[pair])

    if len(coupling_vals) > 2:
        r = np.corrcoef(coupling_vals, specter_vals)[0, 1]
        h2_pass = r > 0.3
        print(f"\n假设 2（耦合 → 语义）: {'✅' if h2_pass else '❌'}")
        print(f"  Pearson r = {r:.3f}")
    else:
        print(f"\n假设 2: 数据不足")

    # 相似度分布
    all_sim_vals = list(sims.values())
    print(f"\n=== 相似度分布 ===")
    print(f"  min={np.min(all_sim_vals):.3f}  max={np.max(all_sim_vals):.3f}")
    print(f"  mean={np.mean(all_sim_vals):.3f}  std={np.std(all_sim_vals):.3f}")
    print(f"  中位数={np.median(all_sim_vals):.3f}")

    # 文献耦合分布
    coupling_all = list(coupling.values())
    nonzero = [v for v in coupling_all if v > 0]
    print(f"\n=== 文献耦合分布 ===")
    print(f"  非零对: {len(nonzero)}/{len(coupling_all)}")
    if nonzero:
        print(f"  非零 mean={np.mean(nonzero):.4f}  max={np.max(nonzero):.4f}")


# ── 主流程 ──

async def main():
    print("=" * 60)
    print("MVP2 技术验证 — Semantic Scholar SPECTER2 + 文献耦合")
    print("=" * 60)

    # Step 1
    print("\n[1/3] 从 OpenAlex 获取 transformer 前 20 篇...")
    papers = await fetch_openalex_papers("transformer", limit=20)
    print(f"获取 {len(papers)} 篇论文")
    for p in papers[:5]:
        doi_status = "✅" if p["doi"] else "❌"
        print(f"  {doi_status} [{p['year']}] {p['title'][:60]}... (cited: {p['cited_by_count']})")
    print(f"  ... 共 {len(papers)} 篇")

    # Step 2
    print("\n[2/3] 获取 SPECTER2 embeddings...")
    embeddings = await fetch_specter2_embeddings(papers)

    if len(embeddings) < 3:
        print("\n[ABORT] embedding 数量不足，无法验证假设")
        print("可能原因: S2 API 不可用 / DOI 映射失败 / embedding 未计算")
        return

    # Step 3
    print("\n[3/3] 计算文献耦合 & 验证假设...")
    coupling = compute_bibliographic_coupling(papers)
    citation_pairs = build_citation_pairs(papers)
    print(f"论文集内引用对: {len(citation_pairs)}")

    verify_hypotheses(papers, embeddings, coupling, citation_pairs)

    print("\n" + "=" * 60)
    print("验证完成。风险总结见上方输出。")
    print("用完后可删除此文件: rm test_semantic_experiment.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
