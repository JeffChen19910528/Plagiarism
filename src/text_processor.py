"""Extract structured information (title, abstract, keywords) from raw paper text."""

import re
from typing import Optional


# ── Section-header patterns ────────────────────────────────────────────────────

_ABSTRACT_HEADERS = re.compile(
    r"(?i)^(abstract|摘要|summary|概要)\s*[:\-]?\s*$", re.MULTILINE
)
# IEEE Transactions style: "Abstract—" or "Abstract- " inline at line start
_ABSTRACT_INLINE = re.compile(
    r"(?im)^[^\n]{0,40}?\babstract\b\s*[—–\-:]\s*"
)
_KEYWORD_HEADERS = re.compile(
    r"(?i)^(keywords?|index terms?|關鍵字|關鍵詞)\s*[:\-]?\s*", re.MULTILINE
)
_INTRO_HEADERS = re.compile(
    r"(?i)^(1\.?\s+introduction|1\.?\s+介紹|1\.?\s+緒論|introduction)\s*$",
    re.MULTILINE,
)
_CONCLUSION_HEADERS = re.compile(
    r"(?i)^(\d+\.?\s+)?(conclusion|related work|references|acknowledgment|bibliography|參考文獻|結論)",
    re.MULTILINE,
)

# Lines that are journal/conference page headers — skip when hunting for the title
_JOURNAL_HEADER_RE = re.compile(
    r"(?i)^("
    r"ieee\b|transactions\b|proceedings\s+of|acm\s+(transactions|sigchi|siggraph)|"
    r"springer\b|elsevier\b|nature\b|"
    r"vol\.?\s*\d|volume\s+\d|no\.?\s*\d|"
    r"this\s+(article|paper)\s+(was|is|has\s+been)\s+(published|accepted|submitted)|"
    r"authorized\s+licensed|digital\s+object\s+identifier|doi\s*:|arxiv\s*:|"
    r"©\s*\d{4}|copyright"
    r")",
)

# Lines that look like author affiliations or email addresses
_AFFILIATION_RE = re.compile(
    r"(?i)("
    r"department\s+of|school\s+of|university\s+(of|at)?|institute\s+of|"
    r"laboratory|research\s+(center|group|lab)|faculty\s+of|"
    r"college\s+of|national\s+\w+\s+(university|institute)|"
    r"@[\w.\-]+\.[a-z]{2,}|"          # email address
    r"received\s+\w+\s+\d{1,2}|"      # manuscript dates
    r"revised\s+\w+\s+\d{1,2}|"
    r"accepted\s+\w+\s+\d{1,2}"
    r")",
)


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_title(text: str) -> str:
    """Heuristic: first non-empty line that isn't a journal header or metadata."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:20]:
        if len(line) < 10 or re.match(r"^[\d\s]+$", line):
            continue
        if re.match(r"(?i)^(abstract|keywords?|摘要|關鍵字)", line):
            continue
        if _JOURNAL_HEADER_RE.match(line):
            continue
        if _AFFILIATION_RE.search(line):
            continue
        if "@" in line:
            continue
        # Skip lines that look like "AuthorName1, AuthorName2" (proper nouns, short, no verbs)
        if _looks_like_author_line(line):
            continue
        return line
    return lines[0] if lines else ""


def extract_abstract(text: str) -> str:
    """Return the abstract body, stripped of any leading author/affiliation metadata."""
    # 1. Standalone "Abstract" header (conference / thesis style)
    match = _ABSTRACT_HEADERS.search(text)
    if match:
        after = text[match.end():]
        end = _INTRO_HEADERS.search(after)
        snippet = after[: end.start()] if end else after[:1500]
        return _clean(snippet)

    # 2. Inline "Abstract—" (IEEE Transactions style)
    inline = _ABSTRACT_INLINE.search(text)
    if inline:
        after = text[inline.end():]
        # Cut off at Keywords / Index Terms / Introduction, whichever comes first
        stopper = _first_match(after, _KEYWORD_HEADERS, _INTRO_HEADERS)
        snippet = after[:stopper] if stopper else after[:1500]
        return _clean(snippet)

    # 3. Fallback: skip front-matter (journal header + author block) then take 600 chars
    body_start = _find_content_start(text)
    return _clean(text[body_start: body_start + 600])


def extract_keywords(text: str) -> list[str]:
    """Return keyword list if a keywords section exists."""
    match = _KEYWORD_HEADERS.search(text)
    if not match:
        return []
    line_end = text.find("\n", match.end())
    raw = text[match.end(): line_end if line_end != -1 else match.end() + 300]
    parts = re.split(r"[;,，；、\|]", raw)
    return [p.strip() for p in parts if 2 < len(p.strip()) < 60]


def extract_body(text: str, max_chars: int = 4000) -> str:
    """Return body text starting after front-matter, stopping before References."""
    start = _find_content_start(text)
    end = _CONCLUSION_HEADERS.search(text, start)
    body = text[start: end.start()] if end else text[start:]
    return _clean(body)[:max_chars]


def build_search_query(title: str, keywords: list[str], abstract: str) -> str:
    """Build a compact search string for API queries."""
    parts = [title]
    if keywords:
        parts.extend(keywords[:5])
    else:
        words = _extract_important_words(abstract)
        parts.extend(words[:8])
    return " ".join(parts)[:300]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _looks_like_author_line(line: str) -> bool:
    """Return True if the line looks like an author-name list (e.g. 'John Smith1 and Jane Doe2')."""
    # Must be reasonably short, consist mostly of proper-cased words, digits, and connectors
    if len(line) > 120:
        return False
    # Contains "and" or comma between capitalized tokens, possibly with trailing digits
    return bool(re.match(
        r"^[A-Z][a-z]+(?:[- ][A-Z][a-z]+)*\d*"
        r"(?:\s*(?:and|,)\s*[A-Z][a-z]+(?:[- ][A-Z][a-z]+)*\d*)+\s*$",
        line,
    ))


def _find_content_start(text: str) -> int:
    """Return the character offset where actual paper content begins.

    Skips journal page-header lines, author names, affiliations, and email addresses
    that typically precede the abstract in IEEE-style PDFs.
    """
    lines = text.splitlines(keepends=True)
    offset = 0
    for line in lines[:40]:
        stripped = line.strip()
        if stripped and (
            _JOURNAL_HEADER_RE.match(stripped)
            or _AFFILIATION_RE.search(stripped)
            or "@" in stripped
            or _looks_like_author_line(stripped)
            or re.match(r"^[\d\s,;.\-]+$", stripped)   # digit-only / punctuation lines
        ):
            offset += len(line)
            continue
        # First non-metadata line — stop here
        break
    return offset


def _first_match(text: str, *patterns) -> Optional[int]:
    """Return position of the earliest match among several patterns, or None."""
    positions = [m.start() for p in patterns for m in [p.search(text)] if m]
    return min(positions) if positions else None


def _extract_important_words(text: str, top_n: int = 10) -> list[str]:
    """Very lightweight keyword extraction without external NLP models."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "on", "at", "by", "for", "with", "about",
        "as", "into", "through", "during", "including", "until", "against",
        "among", "throughout", "despite", "towards", "upon", "concerning",
        "this", "that", "these", "those", "it", "its", "we", "our", "their",
        "which", "who", "whom", "and", "or", "but", "if", "then", "than",
        "so", "yet", "nor", "not", "from", "also", "such", "each", "paper",
        "propose", "proposed", "present", "show", "shows", "results", "using",
    }
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=lambda w: freq[w], reverse=True)[:top_n]


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()
