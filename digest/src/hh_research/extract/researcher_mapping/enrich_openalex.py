"""PyAlex / OpenAlex 路径 enrich。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pyalex
from pyalex import Authors, Works

from hh_research.extract.researcher_mapping.match import match_name
from hh_research.utils.logger import get_logger

log = get_logger("enrich_openalex")

try:
    CACHE_DIR = Path("data/cache/author_lookup/openalex")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:  # noqa: BLE001
    CACHE_DIR = Path("data/cache/author_lookup/openalex")

# OpenAlex polite pool: 提供 email 拿到更稳定的限流
_email = os.environ.get("OPENALEX_EMAIL") or os.environ.get("USER_EMAIL")
if _email:
    pyalex.config.email = _email


def _fetch_work(arxiv_id: str) -> dict[str, Any] | None:
    """按 arxiv_id 反查论文 OpenAlex Work；查不到返回 None。

    OpenAlex 不支持 ids.arxiv 过滤字段，改用 arxiv 论文的标准 DOI 格式：
    arxiv id 'YYMM.NNNNN' → DOI '10.48550/arXiv.YYMM.NNNNN'
    """
    arxiv_id_clean = arxiv_id.split("v")[0]  # 去版本号
    doi = f"10.48550/arXiv.{arxiv_id_clean}"
    try:
        # 主路径: pyalex 的 [external_id] 语法
        return dict(Works()[f"doi:{doi}"])
    except Exception as e:  # noqa: BLE001
        # fallback: filter doi（含协议前缀）
        try:
            works = Works().filter(doi=f"https://doi.org/{doi}").get(per_page=1)
            if works:
                return dict(works[0])
        except Exception as e2:  # noqa: BLE001
            log.warning("openalex fetch work for arxiv %s failed: %s | fallback: %s",
                       arxiv_id, e, e2)
    return None


def query_paper_by_arxiv_id(arxiv_id: str, target_name: str) -> dict[str, Any] | None:
    """主路径：按 arxiv_id 反查论文 → 在 authorships 中用姓名匹配定位目标作者。

    返回（命中时）:
        {
            "display_name": str,
            "orcid": str | None,
            "institutions": [{"display_name": str, "ror": str | None}, ...],
            "is_corresponding": bool,
        }
    返回 None 表示论文未收录或无姓名匹配。
    """
    work = _fetch_work(arxiv_id)
    if not work:
        return None
    for authorship in work.get("authorships", []):
        author = authorship.get("author") or {}
        display_name = author.get("display_name") or ""
        if not match_name(target_name, display_name):
            continue
        institutions = [
            {
                "display_name": inst.get("display_name", ""),
                "ror": inst.get("ror"),
            }
            for inst in (authorship.get("institutions") or [])
            if inst.get("display_name")
        ]
        return {
            "display_name": display_name,
            "orcid": author.get("orcid"),
            "institutions": institutions,
            "is_corresponding": authorship.get("is_corresponding", False),
        }
    return None


def query_author_by_name(name: str) -> dict[str, Any] | None:
    """Fallback：直接按姓名搜，取 cited_by_count 排序 top 1。"""
    try:
        results = Authors().search_filter(display_name=name).sort(
            cited_by_count="desc",
        ).get(per_page=1)
        if not results:
            return None
        a = dict(results[0])
        last_inst_list = a.get("last_known_institutions") or []
        return {
            "display_name": a.get("display_name") or "",
            "orcid": a.get("orcid"),
            "institutions": [
                {"display_name": i.get("display_name", ""), "ror": i.get("ror")}
                for i in last_inst_list
                if i.get("display_name")
            ],
            "is_corresponding": False,
        }
    except Exception as e:  # noqa: BLE001
        log.warning("openalex fallback search for %s failed: %s", name, e)
        return None


def _cache_key(arxiv_id: str, name: str) -> Path:
    raw = f"{arxiv_id}:{name.lower().strip()}"
    sha = hashlib.sha1(raw.encode()).hexdigest()
    return CACHE_DIR / f"{sha}.json"


def _to_coauthor(data: dict[str, Any]):
    """OpenAlex query data → CoauthorInfo 候选（仅填 PyAlex 能覆盖的字段）。"""
    from hh_research.storage.schemas import CoauthorInfo  # avoid top-level cycle

    institutions = data.get("institutions") or []
    primary = institutions[0] if institutions else {}
    affiliation = primary.get("display_name") or None
    provenance: dict[str, str] = {}
    if affiliation:
        provenance["affiliation"] = "openalex:" + (primary.get("ror") or "no-ror")
    orcid = data.get("orcid")
    if orcid:
        provenance["orcid"] = "openalex"
    return CoauthorInfo(
        name=data.get("display_name") or "",
        affiliation=affiliation,
        provenance=provenance,
    )


def enrich_via_openalex(arxiv_id: str, name: str):
    """V4 第二路 enrich 主入口：主路径 + fallback + 缓存。"""
    cache_path = _cache_key(arxiv_id, name)
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text())
            return _to_coauthor(data)
        except Exception as e:  # noqa: BLE001
            log.warning("cache read failed %s: %s", cache_path, e)

    data = query_paper_by_arxiv_id(arxiv_id, name)
    if not data:
        data = query_author_by_name(name)
    if not data:
        return None

    try:
        cache_path.write_text(json.dumps(data, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        log.warning("cache write failed %s: %s", cache_path, e)

    return _to_coauthor(data)
