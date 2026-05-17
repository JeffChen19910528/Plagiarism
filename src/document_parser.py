"""PDF / DOCX text extraction with three-tier structured parsing.

Parsing priority for PDF:
  1. GROBID API  — ML-based, handles all academic formats
  2. Font-size layout analysis — pdfplumber char-level font data
  3. Regex heuristics — existing fallback (also used for DOCX)
"""

import io
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Optional

import requests


# ── GROBID ─────────────────────────────────────────────────────────────────────

_GROBID_URL     = "https://kermitt2-grobid.hf.space/api/processFulltextDocument"
_GROBID_TIMEOUT = 30
_TEI_NS         = {"tei": "http://www.tei-c.org/ns/1.0"}


def _grobid_parse(file_bytes: bytes) -> Optional[dict]:
    """Call public GROBID API; return structured dict or None."""
    try:
        resp = requests.post(
            _GROBID_URL,
            files={"input": ("paper.pdf", file_bytes, "application/pdf")},
            data={"consolidateHeader": "0"},
            timeout=_GROBID_TIMEOUT,
        )
    except Exception:
        return None

    if resp.status_code != 200:
        return None

    return _parse_tei(resp.text)


def _parse_tei(xml_text: str) -> Optional[dict]:
    """Extract title / abstract / keywords / body from GROBID TEI XML."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    ns = _TEI_NS

    # ── title ──────────────────────────────────────────────────────────────────
    title = ""
    for selector in (
        ".//tei:titleStmt/tei:title[@type='main']",
        ".//tei:titleStmt/tei:title[@level='a']",
        ".//tei:titleStmt/tei:title",
    ):
        el = root.find(selector, ns)
        if el is not None and el.text:
            title = el.text.strip()
            break

    # ── abstract ───────────────────────────────────────────────────────────────
    paras = root.findall(".//tei:profileDesc/tei:abstract//tei:p", ns)
    abstract = " ".join((p.text or "").strip() for p in paras).strip()
    if not abstract:
        ab = root.find(".//tei:profileDesc/tei:abstract", ns)
        if ab is not None:
            abstract = ET.tostring(ab, method="text", encoding="unicode").strip()

    # ── keywords ───────────────────────────────────────────────────────────────
    kw_els = root.findall(
        ".//tei:profileDesc/tei:textClass/tei:keywords/tei:term", ns
    )
    keywords = [k.text.strip() for k in kw_els if k.text and k.text.strip()]

    # ── body (first 4 000 chars of paragraph text) ────────────────────────────
    body_paras = root.findall(".//tei:text/tei:body//tei:p", ns)
    body = " ".join((p.text or "").strip() for p in body_paras)[:4000]

    if not title and not abstract:
        return None

    raw_text = f"{title}\n\n{abstract}\n\n{body}"
    return {
        "title":    title,
        "abstract": abstract,
        "keywords": keywords,
        "body":     body,
        "raw_text": raw_text,
    }


# ── Font-size layout analysis ──────────────────────────────────────────────────

def _layout_parse(file_bytes: bytes) -> Optional[dict]:
    """Detect title via pdfplumber font-size; use column-aware text for the rest."""
    try:
        import pdfplumber
    except ImportError:
        return None

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                return None

            page1 = pdf.pages[0]
            chars = page1.chars

            # Column-aware full text (handles two-column IEEE/ACM layouts)
            full_text = _extract_text_from_pdf(pdf)

            if not chars or not full_text.strip():
                return None

            title = _detect_title_by_font(chars, page1.height)
            if not title:
                return None

            from src.text_processor import (
                extract_abstract, extract_keywords, extract_body,
            )
            abstract = extract_abstract(full_text)
            keywords = extract_keywords(full_text)
            body     = extract_body(full_text)

            return {
                "title":    title,
                "abstract": abstract,
                "keywords": keywords,
                "body":     body,
                "raw_text": full_text,
            }
    except Exception:
        return None


def _extract_text_from_pdf(pdf) -> str:
    """Extract text from all pages with two-column layout awareness."""
    parts = []
    for page in pdf.pages:
        text = _extract_page_text_smart(page)
        if text:
            parts.append(text)
    return _join_hyphens("\n".join(parts))


def _extract_page_text_smart(page) -> str:
    """Column-aware single-page text extraction.

    Uses within_bbox for each region so pdfplumber reconstructs word spacing
    correctly.  Column detection uses only the body area (below top 25 %) to
    avoid full-width title/author lines masking the gutter.

    Full-width header rows (title / authors / affiliations) are identified by
    finding words whose x-span crosses the gutter (x0 < split_x, x1 > split_x).
    The last such row marks the boundary between the full-width section and the
    two-column body.
    """
    pw, ph = page.width, page.height
    hdr_cut = ph * 0.05    # skip running page header band
    col_cut = ph * 0.25    # use body area only for column-gap detection

    words = page.extract_words(x_tolerance=3, y_tolerance=3)
    if not words:
        return page.extract_text() or ""

    col_words = [w for w in words if w["top"] > col_cut]
    split_x   = _find_column_split(col_words, pw)

    if split_x is None:
        return page.within_bbox((0, hdr_cut, pw, ph)).extract_text() or ""

    # Gutter-crossing words span full width — find the lowest one to locate
    # where the full-width header ends and two-column body begins.
    tol = pw * 0.01
    crossing = [w for w in words if w["x0"] < split_x and w["x1"] > split_x + tol]
    hdr_bottom = max((w["bottom"] for w in crossing), default=hdr_cut)
    hdr_bottom = max(hdr_bottom, hdr_cut)

    parts: list[str] = []
    if hdr_bottom > hdr_cut + 1:
        hdr = page.within_bbox((0, hdr_cut, pw, hdr_bottom)).extract_text() or ""
        if hdr:
            parts.append(hdr)

    # Pad the left bbox so characters that overhang split_x are included.
    # Typical two-column gutter is 10-15 pt; 1.5 % of page width stays within it.
    pad = pw * 0.015   # ~9 pt; right-column x0 starts ≥12 pt past split_x
    left  = page.within_bbox((0,           hdr_bottom, split_x + pad, ph)).extract_text(x_tolerance=1) or ""
    right = page.within_bbox((split_x + pad, hdr_bottom, pw,          ph)).extract_text(x_tolerance=1) or ""
    parts.extend(filter(None, [left, right]))
    return "\n".join(parts)


def _find_column_split(words: list, page_width: float) -> Optional[float]:
    """Return the x-coordinate of the column gap, or None if single-column.

    Counts word STARTS (x0) per band rather than overlap coverage — the gutter
    between two columns has near-zero word starts even though words from both
    columns physically overlap the gutter zone.
    """
    if not words:
        return None

    lo, hi = page_width * 0.30, page_width * 0.70
    bw     = page_width * 0.02          # narrow band matches typical ~12pt gutter
    step   = bw / 2
    bands: list[tuple[float, int]] = []

    x = lo
    while x < hi:
        count = sum(1 for w in words if x <= w["x0"] < x + bw)
        bands.append((x + bw / 2, count))
        x += step

    if not bands:
        return None

    max_count = max(c for _, c in bands)
    min_x, min_count = min(bands, key=lambda t: t[1])

    # Require the gap to be very sparse (< 10 % of busiest band)
    if max_count == 0 or min_count / max_count >= 0.10:
        return None

    return min_x


def _words_to_text(words: list) -> str:
    """Reconstruct text from extract_words() output, grouping by row."""
    if not words:
        return ""

    buckets: dict = defaultdict(list)
    for w in words:
        key = round(w["top"] / 2) * 2
        buckets[key].append(w)

    return "\n".join(
        " ".join(w["text"] for w in sorted(buckets[k], key=lambda w: w["x0"]))
        for k in sorted(buckets)
    )


def _join_hyphens(text: str) -> str:
    """Join words split across lines with a trailing hyphen (column-layout artefact).

    "cross-\\nchan" → "cross-chan"  (preserves compound-word hyphen)
    """
    return re.sub(r"(\w)-\n(\w)", r"\1-\2", text)


def _detect_title_by_font(chars: list, page_height: float) -> str:
    """Return the title by finding the largest-font multi-character lines.

    Two common artefacts are handled:
    * Running page headers (e.g. 'IEEETRANSACTIONS 1') — excluded via an 8 %
      page-height cutoff at the top.
    * Drop caps (e.g. the oversized 'A' that opens the Introduction in IEEE
      Transactions) — excluded by requiring candidate lines to be ≥ 3 characters.

    If the very largest font size belongs only to a drop cap, the algorithm
    automatically falls through to the next-largest size and picks up the title.
    """
    if not chars:
        return ""

    header_cutoff = page_height * 0.05   # running headers sit above ~5 % height
    content_chars = [c for c in chars if c.get("top", 0) > header_cutoff]
    if not content_chars:
        return ""

    # Group into lines by rounded y-coordinate (2 pt tolerance)
    buckets: dict = defaultdict(list)
    for c in content_chars:
        key = round(c.get("top", 0) / 2) * 2
        buckets[key].append(c)

    lines = []
    for top_key in sorted(buckets):
        lc = sorted(buckets[top_key], key=lambda c: c.get("x0", 0))
        sizes = [c.get("size", 0) for c in lc if c.get("size", 0) > 0]
        avg_size = sum(sizes) / len(sizes) if sizes else 10
        # Insert a space whenever the horizontal gap between chars > 20 % of font size
        parts: list[str] = []
        prev_x1: Optional[float] = None
        for c in lc:
            x0 = c.get("x0", 0)
            if prev_x1 is not None and x0 - prev_x1 > avg_size * 0.20:
                parts.append(" ")
            parts.append(c["text"])
            prev_x1 = c.get("x1", x0)
        text = "".join(parts).strip()
        if not text:
            continue
        lines.append({"top": top_key, "text": text, "size": avg_size})

    if not lines:
        return ""

    sorted_lines = sorted(lines, key=lambda l: l["top"])

    # Try each distinct font size from largest to smallest.
    # Drop caps have the largest size but are ≤ 2 chars; the real title comes next.
    unique_sizes = sorted(
        {l["size"] for l in lines if l["size"] > 0}, reverse=True
    )

    for target_size in unique_sizes:
        threshold = target_size * 0.85
        title_parts: list[str] = []
        last_top: Optional[float] = None

        for line in sorted_lines:
            if line["size"] >= threshold:
                text = line["text"].strip()
                if len(text) <= 2:          # drop cap or noise
                    if title_parts:
                        break               # something already collected → stop
                    continue                # not yet started → skip
                if last_top is not None and line["top"] - last_top > 40:
                    break                   # gap too large
                title_parts.append(text)
                last_top = line["top"]
            elif title_parts:
                break

        candidate = " ".join(title_parts).strip()
        if len(candidate) >= 10:
            return candidate               # found a plausible title

    return ""


# ── Plain text extraction (original) ──────────────────────────────────────────

def parse_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return _join_hyphens(_extract_text_from_pdf(pdf))
    except Exception:
        # Last-resort: basic extraction without column handling
        with __import__("pdfplumber").open(io.BytesIO(file_bytes)) as pdf:
            return "\n".join(
                p.extract_text() or "" for p in pdf.pages
            )


def parse_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required: pip install python-docx")

    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_uploaded_file(uploaded_file) -> str:
    """Backward-compatible: return plain text from uploaded file."""
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif name.endswith((".docx", ".doc")):
        return parse_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {Path(name).suffix}")


# ── Main structured entry point ───────────────────────────────────────────────

def parse_paper_structured(uploaded_file) -> dict:
    """Return a structured dict with keys: title, abstract, keywords, body,
    raw_text, parse_source.

    parse_source values: 'GROBID' | 'Layout' | 'Regex'
    """
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    name = getattr(uploaded_file, "name", "").lower()
    is_pdf = name.endswith(".pdf")

    if is_pdf:
        result = _grobid_parse(file_bytes)
        if result:
            return {**result, "parse_source": "GROBID"}

        result = _layout_parse(file_bytes)
        if result:
            return {**result, "parse_source": "Layout"}

    # Regex fallback (also the only path for DOCX)
    from src.text_processor import (
        extract_abstract, extract_body, extract_keywords, extract_title,
    )
    if is_pdf:
        raw_text = parse_pdf(file_bytes)
    else:
        raw_text = parse_docx(file_bytes)

    return {
        "raw_text":     raw_text,
        "title":        extract_title(raw_text),
        "abstract":     extract_abstract(raw_text),
        "keywords":     extract_keywords(raw_text),
        "body":         extract_body(raw_text),
        "parse_source": "Regex",
    }
