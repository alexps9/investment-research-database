#!/usr/bin/env python3
"""Retry image insertion for a published wiki digest, without re-calling LLM.

Use case (v7.0 5-28):
  An earlier `regenerate_digest.py --publish` ran successfully but
  `insert_signal_images()` resolved 0/N target block_ids due to URL mismatch
  (signal.url with v1/v2 suffix vs docx href without). The wiki document is
  already published with all anchors injected; we just need to retry image
  insertion with the fixed (fuzzy-matching) code.

Usage:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/retry_insert_images.py \
        --doc "https://my.feishu.cn/wiki/XXX" \
        --date 2026-05-27 \
        --since 2026-05-26T16:00:00Z --until 2026-05-27T16:00:00Z
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.extract.image_extractor import enrich_signal_with_images  # noqa: E402
from hh_research.publish.lark_doc_publisher import insert_signal_images  # noqa: E402
from hh_research.utils.logger import get_logger  # noqa: E402

# Import same signal-reading helpers as regenerate_digest does
sys.path.insert(0, str(Path(__file__).parent))
from regenerate_digest import _read_signals_from_bitable  # type: ignore  # noqa: E402

log = get_logger("retry_insert_images")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True, help="Wiki URL or docx token")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (for log only)")
    ap.add_argument("--since", required=True, help="ISO8601 UTC")
    ap.add_argument("--until", required=True, help="ISO8601 UTC")
    ap.add_argument("--max-per-signal", type=int, default=1)
    args = ap.parse_args()

    since = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
    until = datetime.fromisoformat(args.until.replace("Z", "+00:00"))
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)

    log.info("retry image insertion for doc=%s window %s → %s",
             args.doc[:60], since.isoformat(), until.isoformat())

    # Read signals from Bitable (same window the original digest used)
    signals = _read_signals_from_bitable(
        args.date, cst=False, since_override=since, until_override=until,
    )
    log.info("read %d signals from Bitable", len(signals))

    # Enrich arxiv signals with images (uses fixed enrich_signal_with_images
    # with PyMuPDF fallback)
    n_arxiv = sum(1 for s in signals if s.source == "arxiv")
    log.info("running image enrich on %d arxiv signals ...", n_arxiv)
    for s in signals:
        try:
            enrich_signal_with_images(s, max_images_per_paper=args.max_per_signal)
        except Exception as e:  # noqa: BLE001
            log.warning("image enrich failed for %s: %s", s.source_id, e)
    n_with_imgs = sum(1 for s in signals if s.image_urls)
    log.info("enriched %d/%d signals with images", n_with_imgs, len(signals))

    # Extract docx token from URL
    doc_token = args.doc
    if "feishu.cn" in args.doc:
        # https://my.feishu.cn/wiki/<node_token> 或 /docx/<obj_token>
        # We need obj_token; for wiki URL we need to resolve. But our
        # insert_signal_images accepts whatever `--doc` accepts.
        # lark-cli docs +fetch handles both formats; same for +media-insert.
        # So pass the URL through as-is.
        pass

    # Retry insertion with fixed code (fuzzy match by arxiv id)
    counts = insert_signal_images(
        obj_token=doc_token,
        signals=signals,
        max_per_signal=args.max_per_signal,
    )
    log.info("image insertion final: %s", counts)


if __name__ == "__main__":
    main()
