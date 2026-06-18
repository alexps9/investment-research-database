"""Web 日历 digest 索引:单一数据源 web/public/data/digests-index.json 的读写 + 元数据提取。

entry 字段:
  date(唯一键) / title / signal_count / tldr / feishu_wiki_url / source / line / confidence
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path


def load_index(path: Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def write_index_atomic(path: Path, rows: list[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda r: r.get("date", ""), reverse=True)
    payload = json.dumps(ordered, ensure_ascii=False, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".digests-index.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def upsert_entry(path: Path, entry: dict) -> dict:
    if not entry.get("date"):
        raise ValueError("entry must have a non-empty 'date'")
    rows = load_index(path)
    by_date = {r["date"]: r for r in rows if r.get("date")}
    by_date[entry["date"]] = {**by_date.get(entry["date"], {}), **entry}
    write_index_atomic(path, list(by_date.values()))
    return by_date[entry["date"]]


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(s: str) -> str:
    return _TAG_RE.sub(" ", s)


def extract_digest_meta(text: str, *, fallback_title: str, fallback_date: str) -> dict:
    """从 digest 文本(旧 markdown 或 XML/HTML-like)容错提取 title/tldr/signal_count。"""
    title = ""
    tldr = ""

    # title: markdown '# ...' 优先,其次 <title>...</title>
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()
    else:
        m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
        if m:
            title = _strip_tags(m.group(1)).strip()

    # tldr: markdown '## 今日 TL;DR' 段首段;其次 HTML-like '今日 TL;DR' 之后到下个 <h2>
    m = re.search(r"##\s*今日\s*TL;DR\s*\n+([\s\S]*?)(?:\n##|\n═|\Z)", text)
    if m:
        tldr = m.group(1).strip().split("\n\n")[0]
    else:
        m = re.search(r"今日\s*TL;DR.*?(?:</h2>|\n)([\s\S]*?)(?:<h2|\n##|\Z)", text, re.I)
        if m:
            tldr = _strip_tags(m.group(1))
    if not tldr:
        # v7.0 精选格式无 TL;DR 区块：用「Top 3 大新闻」的 h3 标题拼预览
        m = re.search(r"Top 3 大新闻(?:</h1>)?([\s\S]*?)(?:<h1|\Z)", text)
        if m:
            tops = re.findall(r"<h3[^>]*>([\s\S]*?)</h3>", m.group(1))
            tldr = "；".join(_strip_tags(t).strip() for t in tops[:3])
    tldr = re.sub(r"\s+", " ", tldr).strip()[:300]

    # signal_count: markdown '#### ' 优先;其次 HTML <h3>/<h4>
    h4 = len(re.findall(r"^####\s+", text, re.M))
    signal_count = h4 if h4 else len(re.findall(r"<h[34][ >]", text, re.I))

    if not title:
        title = fallback_title or f"HH Research Daily · {fallback_date}"
    return {"title": title, "tldr": tldr, "signal_count": signal_count}
