"""AnySearch 路径 enrich（封装现有 author_enricher.enrich_author，统一输出 CoauthorInfo）。"""
from __future__ import annotations

from hh_research.extract.author_enricher import enrich_author
from hh_research.storage.schemas import CoauthorInfo
from hh_research.utils.logger import get_logger

log = get_logger("enrich_anysearch")


def enrich_via_anysearch(
    name: str,
    paper_arxiv_id: str | None,
    coauthor_names: list[str] | None = None,
    affiliation_hint: str | None = None,
) -> CoauthorInfo | None:
    """V4 包装：调旧 enrich_author 拿 profile dict → 转为 CoauthorInfo 候选。

    Args:
        name: 作者全名（如 "John Doe"）
        paper_arxiv_id: 论文 arXiv ID（可选，用于缓存 key）
        coauthor_names: 共作者列表（辅助 hint）
        affiliation_hint: affiliation 提示文本

    Returns:
        CoauthorInfo 或 None（若 enrich 失败或无有效结果）
    """
    try:
        profile = enrich_author(
            name,
            paper_arxiv_id,
            coauthor_names or [],
            affiliation_hint,
            cache=True,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("anysearch enrich %s failed: %s", name, e)
        return None

    if not profile or not profile.get("name"):
        return None

    provenance = profile.get("provenance") or {}
    # provenance 中已包含 anysearch:<url> 形式，无需再加前缀
    return CoauthorInfo(
        name=profile.get("name") or name,
        affiliation=profile.get("affiliation"),
        current_status=profile.get("current_status"),
        advisor=profile.get("advisor"),
        github=profile.get("github"),
        scholar_id=profile.get("scholar_id"),
        homepage=profile.get("homepage"),
        email=profile.get("email"),
        provenance=provenance,
    )
