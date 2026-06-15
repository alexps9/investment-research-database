"""字段级合并 anysearch 和 openalex 候选。

冲突取舍：
- affiliation: openalex 优先（学术权威源）
- 其他字段: anysearch 唯一，openalex 不覆盖
"""
from __future__ import annotations

from hh_research.extract.researcher_mapping.match import match_affiliation
from hh_research.storage.schemas import CoauthorInfo


def _pick(a_val, b_val, prefer: str):
    """两个候选值二选一。prefer in {'a', 'b'}。"""
    if a_val is None and b_val is None:
        return None
    if a_val is None:
        return b_val
    if b_val is None:
        return a_val
    return a_val if prefer == "a" else b_val


def _agree_affiliation(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return match_affiliation(a, [b]) or match_affiliation(b, [a])


def merge_candidates(
    anysearch: CoauthorInfo | None,
    openalex: CoauthorInfo | None,
) -> CoauthorInfo:
    """字段级合并。返回 CoauthorInfo 含 enrich_sources 记录每字段来源。"""
    if anysearch is None and openalex is None:
        raise ValueError("both candidates are None — caller should not call merge")

    name = (openalex.name if openalex and openalex.name else (anysearch.name if anysearch else ""))

    sources: dict[str, list[str]] = {}

    # affiliation：双源优先级取舍 + 冲突标注
    a_aff = anysearch.affiliation if anysearch else None
    b_aff = openalex.affiliation if openalex else None
    if a_aff and b_aff:
        if _agree_affiliation(a_aff, b_aff):
            affiliation = b_aff
            sources["affiliation"] = ["anysearch", "openalex"]
        else:
            affiliation = b_aff  # openalex 优先
            sources["affiliation"] = ["anysearch", "openalex(conflict)"]
    else:
        affiliation = _pick(a_aff, b_aff, "a")
        if affiliation:
            if a_aff:
                sources["affiliation"] = ["anysearch"]
            else:
                sources["affiliation"] = ["openalex"]

    def _from_anysearch(field: str, value):
        if value is not None:
            sources.setdefault(field, ["anysearch"])
        return value

    github = _from_anysearch("github", anysearch.github if anysearch else None)
    scholar_id = _from_anysearch("scholar_id", anysearch.scholar_id if anysearch else None)
    homepage = _from_anysearch("homepage", anysearch.homepage if anysearch else None)
    email = _from_anysearch("email", anysearch.email if anysearch else None)
    advisor = _from_anysearch("advisor", anysearch.advisor if anysearch else None)
    current_status = _from_anysearch("current_status",
                                     anysearch.current_status if anysearch else None)

    provenance: dict[str, str] = {}
    if anysearch:
        provenance.update(anysearch.provenance)
    if openalex:
        for k, v in openalex.provenance.items():
            provenance.setdefault(k, v)

    return CoauthorInfo(
        name=name,
        role=(anysearch.role if anysearch else (openalex.role if openalex else "合作")),
        is_whitelist=(anysearch.is_whitelist if anysearch else False)
        or (openalex.is_whitelist if openalex else False),
        whitelist_record_id=(anysearch.whitelist_record_id if anysearch else None)
        or (openalex.whitelist_record_id if openalex else None),
        affiliation=affiliation,
        current_status=current_status,
        advisor=advisor,
        github=github,
        scholar_id=scholar_id,
        homepage=homepage,
        email=email,
        expected_graduation=(anysearch.expected_graduation if anysearch else None),
        provenance=provenance,
        enrich_sources=sources,
    )
