"""V4 主入口：编排 enrich → merge → verify。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from hh_research.extract.author_enricher import (
    _clean_url,
    detect_co_first_authors,
    fetch_arxiv_html,
)
from hh_research.extract.researcher_mapping.enrich_anysearch import enrich_via_anysearch
from hh_research.extract.researcher_mapping.enrich_openalex import enrich_via_openalex
from hh_research.extract.researcher_mapping.merge import merge_candidates
from hh_research.extract.researcher_mapping.verify_agent import verify_coauthor
from hh_research.storage.schemas import CoauthorInfo, WhitelistEntry
from hh_research.utils.logger import get_logger

log = get_logger("rm_v4_orchestrator")


def select_authors_for_rm(
    authors: list[str],
    roles: dict[str, str],
    whitelist_match: dict[str, WhitelistEntry],
) -> list[tuple[str, str]]:
    """新筛选规则：白名单 ∪ 一作 ∪ 共一 ∪ 通讯（去重，无上限）。

    Returns: [(name, role), ...] 按论文署名顺序
    """
    selected: list[tuple[str, str]] = []
    seen: set[str] = set()
    for i, name in enumerate(authors):
        role = roles.get(name, "合作")
        keep = (
            name in whitelist_match
            or i == 0  # 一作
            or role in ("一作", "共一", "通讯")
        )
        if i == 0 and role == "合作":
            role = "一作"
        if keep and name not in seen:
            selected.append((name, role))
            seen.add(name)
    return selected


def _enrich_one(
    name: str,
    role: str,
    arxiv_id: str,
    co_hints: list[str],
    whitelist_match: dict[str, WhitelistEntry],
) -> CoauthorInfo | None:
    """对单位作者跑：双路 enrich → merge → verify。"""
    wl = whitelist_match.get(name)
    if wl:
        # 白名单作者：从 Bitable whitelist 直接拼候选
        # Bitable URL 字段常包成 markdown 形式 [url](url)，用 _clean_url 剥
        gh_clean = _clean_url(wl.github_url)
        scholar_clean = _clean_url(wl.scholar_url)
        home_clean = _clean_url(wl.personal_url)
        anysearch_cand = CoauthorInfo(
            name=name,
            role=role,
            is_whitelist=True,
            whitelist_record_id=wl.record_id,
            affiliation=wl.organization,
            current_status=(wl.bio[:80] if wl.bio else None),
            github=gh_clean,
            scholar_id=(scholar_clean.rsplit("user=", 1)[-1].split("&")[0]
                       if scholar_clean and "user=" in scholar_clean else None),
            homepage=home_clean,
            provenance={
                "affiliation": "bitable:whitelist",
                "github": "bitable:whitelist" if gh_clean else "",
                "homepage": "bitable:whitelist" if home_clean else "",
            },
        )
        openalex_cand = enrich_via_openalex(arxiv_id, name)
    else:
        anysearch_cand = enrich_via_anysearch(name, arxiv_id, co_hints)
        openalex_cand = enrich_via_openalex(arxiv_id, name)

    if anysearch_cand is None and openalex_cand is None:
        return CoauthorInfo(name=name, role=role)

    merged = merge_candidates(anysearch_cand, openalex_cand)
    merged.role = role
    if wl:
        merged.is_whitelist = True
        merged.whitelist_record_id = wl.record_id

    verified = verify_coauthor(merged)
    return verified


def enrich_paper_coauthors_v4(
    arxiv_id: str,
    authors: list[str],
    whitelist_match: dict[str, WhitelistEntry] | None = None,
    parallel_workers: int = 4,
) -> list[CoauthorInfo]:
    """V4 主入口（替代 V3.2 author_enricher.enrich_paper_coauthors）。"""
    if not authors:
        return []
    whitelist_match = whitelist_match or {}

    html = fetch_arxiv_html(arxiv_id)
    roles = detect_co_first_authors(html, authors)

    selected = select_authors_for_rm(authors, roles, whitelist_match)
    if not selected:
        return []

    log.info("rm_v4: paper %s selected %d authors (wl=%d)",
             arxiv_id, len(selected),
             sum(1 for n, _ in selected if n in whitelist_match))

    co_hints = [n for n, _ in selected[:3]]

    out: list[CoauthorInfo | None] = [None] * len(selected)
    with ThreadPoolExecutor(max_workers=parallel_workers) as ex:
        futs = {
            ex.submit(_enrich_one, name, role, arxiv_id,
                     [h for h in co_hints if h != name], whitelist_match): pos
            for pos, (name, role) in enumerate(selected)
        }
        for fut in as_completed(futs):
            pos = futs[fut]
            try:
                out[pos] = fut.result()
            except Exception as e:  # noqa: BLE001
                log.warning("enrich_one (pos=%d) failed: %s", pos, e)
                out[pos] = None

    # 过滤被审查 agent 整位剔除（None）
    return [c for c in out if c is not None]
