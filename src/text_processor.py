"""Extract structured information (title, abstract, keywords) from raw paper text."""

import re
import string
from typing import Optional


# ── Section-header patterns ────────────────────────────────────────────────────

_ABSTRACT_HEADERS = re.compile(
    r"(?i)^(abstract|摘要|summary|概要)\s*[:\-]?\s*$", re.MULTILINE
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


def extract_title(text: str) -> str:
    """Heuristic: first non-empty line that isn't a section header."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:10]:
        # Skip lines that look like page numbers, URLs, or very short tokens
        if len(line) < 10 or re.match(r"^[\d\s]+$", line):
            continue
        if re.match(r"(?i)^(abstract|keywords?|摘要|關鍵字)", line):
            continue
        return line
    return lines[0] if lines else ""


def extract_abstract(text: str) -> str:
    """Return the abstract section, or fall back to the first 600 characters."""
    match = _ABSTRACT_HEADERS.search(text)
    if match:
        after = text[match.end():]
        # Grab text until the next major section header or blank-line cluster
        end = _INTRO_HEADERS.search(after)
        snippet = after[: end.start()] if end else after[:1500]
        return _clean(snippet)

    # Fallback: first 600 chars of text (often includes abstract inline)
    return _clean(text[:600])


def extract_keywords(text: str) -> list[str]:
    """Return keyword list if a keywords section exists."""
    match = _KEYWORD_HEADERS.search(text)
    if not match:
        return []
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    raw = text[match.end(): line_end if line_end != -1 else match.end() + 300]
    # Split on common delimiters
    parts = re.split(r"[;,，；、\|]", raw)
    return [p.strip() for p in parts if 2 < len(p.strip()) < 60]


def extract_body(text: str, max_chars: int = 4000) -> str:
    """Return introduction + body text (stops before References section)."""
    end = _CONCLUSION_HEADERS.search(text)
    body = text[: end.start()] if end else text
    return _clean(body)[:max_chars]


def build_search_query(title: str, keywords: list[str], abstract: str) -> str:
    """Build a compact search string for API queries."""
    parts = [title]
    if keywords:
        parts.extend(keywords[:5])
    else:
        # Pull noun phrases from the abstract as fallback keywords
        words = _extract_important_words(abstract)
        parts.extend(words[:8])
    return " ".join(parts)[:300]


def _extract_important_words(text: str, top_n: int = 10) -> list[str]:
    """Very lightweight keyword extraction without external NLP models."""
    # Remove stopwords inline to avoid requiring NLTK data at first launch
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
    sorted_words = sorted(freq, key=lambda w: freq[w], reverse=True)
    return sorted_words[:top_n]


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()
