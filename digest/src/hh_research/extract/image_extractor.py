"""Image extraction for signals (arXiv papers + RSS posts).

Strategies:
  - arXiv (primary):  fetch ar5iv.org HTML rendering and pull first 1-3 figure URLs.
    ar5iv.org is the canonical "arxiv as HTML with figures" service.
  - arXiv (fallback): if ar5iv has no HTML built yet (common for papers < 7-10 days
    old), download the PDF and extract embedded raster images from first pages
    via PyMuPDF (fitz). Images are cached locally under data/img_cache/pdf_extracted/.
  - RSS:              parse the first <img> from the feed entry's HTML content.

Image URLs are stored as remote URLs (ar5iv) or local file:// URLs (PDF cache)
in Signal.image_urls. The publish step uploads them to Feishu via docs +media-insert.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import httpx

from ..storage.schemas import Signal
from ..utils.logger import get_logger

log = get_logger("image_extractor")

UA = {"User-Agent": "Mozilla/5.0 (HH Research Pipeline)"}

AR5IV_BASE = "https://ar5iv.org"
ARXIV_PDF_BASE = "https://arxiv.org/pdf"
PDF_IMG_CACHE_DIR = Path("data/img_cache/pdf_extracted")

# v7.0 5-28 caption-aware selection (plan Task 5):
# Bump cache version to invalidate old low-quality cached figures.
PDF_IMG_CACHE_VERSION = "v2"

# PDF 提取阈值：图片至少这么宽 / 高才认为是 figure（过滤公式 / 装饰 icon）
MIN_IMG_WIDTH = 200
MIN_IMG_HEIGHT = 150

# v7.0 5-28: caption confidence scoring (plan Task 5)
FIGURE_CAPTION_POSITIVE_STRONG = (
    "overview", "architecture", "framework", "pipeline", "workflow",
    "system", "method", "approach", "model", "overall", "schematic",
    "paradigm", "design", "teaser",
    # v7.0 5-28 additions: common Figure 1 captions in AI/ML papers
    "illustration", "proposed", "training",
)

FIGURE_CAPTION_NEGATIVE = (
    "benchmark", "ablation", "comparison", "result", "results",
    "dataset", "table", "histogram", "qualitative", "examples",
    "failure case", "visualization only",
)

# Caption confidence threshold: image is saved only if score ≥ this
# (宁可不插图，也不要错插图)
FIGURE_SCORE_THRESHOLD = 70
FIGURE_SCORE_FIG1_RELAXED = 65  # Figure 1 with no negative keyword


def score_figure_caption(caption: str) -> int:
    """Score a figure caption from 0 (irrelevant) to 100 (high confidence workflow/overview).

    Plan ref: Task 5 Step 4.

    Returns:
        0 if caption is empty
        >=80 for overview/architecture/framework/pipeline/workflow captions
        <50 for benchmark/results captions
        <30 for Table captions
    """
    text = caption.lower().strip()
    if not text:
        return 0
    # Table caption is strongly negative (not even a figure)
    if re.search(r"\btable\b", text):
        return max(0, 20 - 45)  # base 20, but Table is negative anyway
    score = 20
    if any(k in text for k in FIGURE_CAPTION_POSITIVE_STRONG):
        score += 70
    if any(k in text for k in FIGURE_CAPTION_NEGATIVE):
        score -= 45
    if re.search(r"\bfig(?:ure)?\.?\s*1\b", text):
        score += 10
    return max(0, min(100, score))

# Match <img src="..."> with absolute or relative URLs
IMG_TAG_RE = re.compile(r'<img\s+[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
IMG_RE = re.compile(r"https?://[^\s\"'<>)]+\.(?:png|jpg|jpeg|gif|webp|svg)", re.IGNORECASE)

# Feishu/Lark Bitable doesn't render data URLs; skip them
DATA_URL_RE = re.compile(r"^data:", re.IGNORECASE)


def extract_arxiv_paper_images(arxiv_id: str, max_images: int = 3) -> list[str]:
    """Fetch ar5iv.org HTML for an arXiv paper and return first N figure URLs.

    arxiv_id format: '2603.18325' or '2603.18325v1'.
    Returns absolute https:// image URLs (skipping math/equation rendered images).
    """
    # Strip version suffix for ar5iv
    base_id = re.sub(r"v\d+$", "", arxiv_id)
    url = f"{AR5IV_BASE}/abs/{base_id}"

    try:
        with httpx.Client(headers=UA, timeout=20.0, follow_redirects=True) as c:
            resp = c.get(url)
            if resp.status_code != 200:
                log.info("ar5iv: HTTP %d for %s", resp.status_code, arxiv_id)
                return []
            html = resp.text
    except Exception as e:  # noqa: BLE001
        log.warning("ar5iv fetch failed for %s: %s", arxiv_id, e)
        return []

    # Extract <img src="..."> URLs
    candidates: list[str] = []
    for src in IMG_TAG_RE.findall(html):
        if DATA_URL_RE.match(src):
            continue
        # Make absolute
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = f"{AR5IV_BASE}{src}"
        elif not src.startswith(("http://", "https://")):
            # Relative path: ar5iv puts these under /html/<id>/...
            src = f"{AR5IV_BASE}/html/{base_id}/{src}"

        # Filter out math rendering and tiny icons (heuristics)
        sl = src.lower()
        if "ltx_equation" in sl or "math" in sl:
            continue
        if any(skip in sl for skip in ("logo", "icon", "favicon")):
            continue
        # Skip very small images by URL hint (often math or icons)
        if "16x16" in sl or "32x32" in sl:
            continue
        candidates.append(src)
        if len(candidates) >= max_images:
            break

    if not candidates:
        log.info("ar5iv: no images extracted for %s", arxiv_id)
    return candidates


def extract_arxiv_paper_images_pdf_fallback(
    arxiv_id: str,
    max_images: int = 2,
    max_pages: int = 6,
) -> list[str]:
    """PyMuPDF PDF fallback: download arxiv PDF, extract embedded raster images
    from first N pages, save to local cache, return file:// URLs.

    Used when ar5iv has no HTML (common for papers < 7-10 days).

    Returns: list of absolute file paths to cached images (file:// URL form).
    """
    import pymupdf  # lazy import — keep startup fast

    base_id = re.sub(r"v\d+$", "", arxiv_id)
    pdf_url = f"{ARXIV_PDF_BASE}/{base_id}"

    # Cache PDF + extracted images by arxiv_id hash + cache version
    # (v7.0 5-28: cache version bumped to v2 to invalidate old non-caption-aware figures)
    PDF_IMG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_id = base_id.replace("/", "_")
    cache_prefix = PDF_IMG_CACHE_DIR / cache_id

    # Check cache first (only versioned cache files)
    cached = sorted(PDF_IMG_CACHE_DIR.glob(f"{cache_id}_{PDF_IMG_CACHE_VERSION}_*.png"))
    if cached:
        log.info("pdf-fallback: cache hit for %s (%d imgs, version=%s)",
                 arxiv_id, len(cached), PDF_IMG_CACHE_VERSION)
        return [f"file://{p.absolute()}" for p in cached[:max_images]]

    # Download PDF to temp
    pdf_bytes = None
    try:
        with httpx.Client(headers=UA, timeout=30.0, follow_redirects=True) as c:
            resp = c.get(pdf_url)
            if resp.status_code != 200:
                log.info("pdf-fallback: HTTP %d for %s", resp.status_code, arxiv_id)
                return []
            content_type = (resp.headers.get("content-type") or "").lower()
            if "pdf" not in content_type:
                log.info("pdf-fallback: not PDF (%s) for %s", content_type, arxiv_id)
                return []
            pdf_bytes = resp.content
    except Exception as e:  # noqa: BLE001
        log.warning("pdf-fallback download failed for %s: %s", arxiv_id, e)
        return []

    # v7.0 5-28: caption-aware selection (plan Task 5):
    # 1. For each page, extract text blocks with coords + image bboxes
    # 2. Find "Figure N: caption" blocks
    # 3. Pair each image with nearest caption (below or above)
    # 4. Score caption -> only save images with score >= FIGURE_SCORE_THRESHOLD
    # Policy: 宁可不插图，也不要错插图
    extracted: list[Path] = []
    candidates: list[tuple[int, int, str, "pymupdf.Pixmap"]] = []  # (score, fig_num, caption, pix)
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        pages_to_scan = min(max_pages, len(doc))

        for page_idx in range(pages_to_scan):
            page = doc[page_idx]
            text_blocks = page.get_text("blocks")  # [(x0,y0,x1,y1,text,block_no,block_type), ...]

            # Find caption blocks: text starting with "Figure N:" or "Fig. N."
            captions = []  # list of (bbox, fig_num, caption_text)
            for tb in text_blocks:
                if len(tb) < 5:
                    continue
                x0, y0, x1, y1, text = tb[0], tb[1], tb[2], tb[3], tb[4]
                if not isinstance(text, str):
                    continue
                # Match "Figure 1:", "Fig. 2.", "Figure 1 |"
                m = re.match(r"^\s*(?:Figure|Fig\.?)\s+(\d+)[\s:.\|]+(.+)",
                             text.strip(), re.IGNORECASE | re.DOTALL)
                if m:
                    fig_num = int(m.group(1))
                    caption_text = m.group(2).strip().split("\n")[0][:200]
                    captions.append(((x0, y0, x1, y1), fig_num, caption_text))

            # Iterate images and pair with nearest caption
            for img_info in page.get_image_info(xrefs=True):
                xref = img_info.get("xref", 0)
                if not xref:
                    continue
                bbox = img_info.get("bbox", (0, 0, 0, 0))
                img_x0, img_y0, img_x1, img_y1 = bbox
                img_cx = (img_x0 + img_x1) / 2
                img_w = img_x1 - img_x0
                img_h = img_y1 - img_y0

                # Filter very small images (公式 / icon / 装饰)
                if img_w < MIN_IMG_WIDTH * 0.5 or img_h < MIN_IMG_HEIGHT * 0.5:
                    continue

                # Find nearest caption (below preferred; within 80pt vertical)
                best_cap = None
                best_dist = 1e9
                for (cap_box, fig_num, cap_text) in captions:
                    cap_cx = (cap_box[0] + cap_box[2]) / 2
                    if abs(cap_cx - img_cx) > max(img_w, 200):  # horizontal overlap
                        continue
                    cap_y0 = cap_box[1]
                    dy_below = cap_y0 - img_y1  # positive if caption below image
                    dy_above = img_y0 - cap_box[3]
                    dist = dy_below if 0 <= dy_below < 80 else (dy_above if 0 <= dy_above < 40 else 1e9)
                    if dist < best_dist:
                        best_dist = dist
                        best_cap = (fig_num, cap_text)

                # Score caption
                if best_cap:
                    fig_num, cap_text = best_cap
                    score = score_figure_caption(f"Figure {fig_num}: {cap_text}")
                else:
                    fig_num, cap_text = None, ""
                    # No caption found: only allow if image is in page 0-2 and large
                    if page_idx <= 2 and img_w >= MIN_IMG_WIDTH and img_h >= MIN_IMG_HEIGHT:
                        score = 40  # below threshold by default, but Figure 1 bonus may help below
                    else:
                        continue

                # Apply pixmap creation now (lazy: only for non-trivially-rejected candidates)
                try:
                    pix = pymupdf.Pixmap(doc, xref)
                except Exception:  # noqa: BLE001
                    continue
                # Filter small / decorative
                if pix.width < MIN_IMG_WIDTH or pix.height < MIN_IMG_HEIGHT:
                    pix = None
                    continue
                # Wide aspect ratio bonus (workflow 图通常 W > H)
                if img_w > img_h * 1.2:
                    score += 5
                # Figure 1 bonus
                if fig_num == 1:
                    score += 10
                # Convert CMYK if needed
                if pix.n - pix.alpha >= 4:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

                threshold = FIGURE_SCORE_FIG1_RELAXED if fig_num == 1 else FIGURE_SCORE_THRESHOLD
                log.info(
                    "pdf-fallback %s p%d fig%s score=%d (caption=%r) %s",
                    arxiv_id, page_idx, fig_num, score, cap_text[:60],
                    "✓ keep" if score >= threshold else "✗ skip (low confidence)",
                )
                if score < threshold:
                    pix = None
                    continue

                # Save candidate, pick best across pages later
                candidates.append((score, fig_num or 99, cap_text, pix))
                if len(candidates) >= max_images * 3:
                    break  # enough candidates
            if len(candidates) >= max_images * 3:
                break

        # Pick top max_images by score (ties: lower fig_num first)
        candidates.sort(key=lambda x: (-x[0], x[1]))
        for i, (score, fig_num, cap, pix) in enumerate(candidates[:max_images]):
            out_path = PDF_IMG_CACHE_DIR / f"{cache_id}_{PDF_IMG_CACHE_VERSION}_fig{fig_num}_s{score}_{i}.png"
            try:
                pix.save(str(out_path))
                extracted.append(out_path)
            except Exception as e:  # noqa: BLE001
                log.warning("pdf-fallback save img failed: %s", e)

        doc.close()
    except Exception as e:  # noqa: BLE001
        log.warning("pdf-fallback parse failed for %s: %s", arxiv_id, e)
        return []

    if not extracted:
        log.info("pdf-fallback: no high-confidence figures for %s (宁缺毋滥)", arxiv_id)
        return []
    log.info("pdf-fallback: extracted %d figures for %s", len(extracted), arxiv_id)
    return [f"file://{p.absolute()}" for p in extracted]


def extract_rss_post_images(html_content: str, max_images: int = 1) -> list[str]:
    """Parse first N image URLs from a RSS post's HTML content."""
    if not html_content:
        return []
    out: list[str] = []
    for src in IMG_TAG_RE.findall(html_content):
        if DATA_URL_RE.match(src):
            continue
        if not src.startswith(("http://", "https://")):
            continue
        out.append(src)
        if len(out) >= max_images:
            break
    return out


def enrich_signal_with_images(signal: Signal, max_images_per_paper: int = 2) -> Signal:
    """Attach image_urls to a Signal in-place if applicable.

    For arXiv signals: extract paper figures via ar5iv, with PyMuPDF PDF fallback
    (v7.0 5-27: integrated fallback for papers < 7-10 days old where ar5iv has
    no HTML build yet — was previously a separate function only called manually,
    causing v7.0 demo digest to ship without any figure).
    For RSS / X / OpenAlex: image extraction is done at collection time.
    """
    if signal.image_urls:
        return signal  # already populated

    if signal.source == "arxiv":
        # source_id is "arxiv:YYMM.NNNNNvX"
        if signal.source_id.startswith("arxiv:"):
            arxiv_id = signal.source_id.removeprefix("arxiv:")
            urls = extract_arxiv_paper_images(arxiv_id, max_images=max_images_per_paper)
            signal.image_urls = urls
            # v7.0 5-27: ar5iv miss → automatic PyMuPDF PDF fallback
            # (was previously only available via separate enrich_signal_with_pdf_fallback
            # function that callers had to invoke explicitly)
            if not urls:
                log.info("ar5iv miss for %s; trying PyMuPDF PDF fallback", arxiv_id)
                signal = enrich_signal_with_pdf_fallback(
                    signal, max_images_per_paper=max(1, max_images_per_paper - 1)
                )

    return signal


def enrich_signal_with_pdf_fallback(
    signal: Signal, max_images_per_paper: int = 1
) -> Signal:
    """Selective PDF fallback for signals where ar5iv missed.

    Call this AFTER extraction (per-signal HTTP + PDF parse is expensive,
    only worth doing for high-value signals).

    Caller is responsible for filtering by novelty / headline_candidate.
    """
    if signal.image_urls:
        return signal
    if signal.source != "arxiv" or not signal.source_id.startswith("arxiv:"):
        return signal
    arxiv_id = signal.source_id.removeprefix("arxiv:")
    urls = extract_arxiv_paper_images_pdf_fallback(
        arxiv_id, max_images=max_images_per_paper
    )
    if urls:
        signal.image_urls = urls
    return signal
