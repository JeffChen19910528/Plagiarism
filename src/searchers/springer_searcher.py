"""Search Springer Nature for journal articles and book chapters.

Uses the official Springer Metadata API when an API key is provided;
falls back to CrossRef filtered to the Springer DOI prefix (10.1007) otherwise.
Free API keys: https://dev.springernature.com/
"""

import re
import requests
from typing import Generator

_SPRINGER_API_URL = "https://api.springer.com/metadata/json"
_CROSSREF_URL     = "https://api.crossref.org/works"
_CROSSREF_MAILTO  = "plagiarism-checker@example.com"


def search(
    query: str,
    max_results: int = 10,
    api_key: str = "",
) -> Generator[dict, None, None]:
    """Yield combined journal-article and book-chapter results from Springer."""
    half = max(max_results // 2, 1)
    rest = max(max_results - half, 1)
    yield from _search_type(query, half, api_key, "Journal Article", "Springer Journal")
    yield from _search_type(query, rest, api_key, "Book Chapter",    "Springer Book")


def _search_type(
    query: str,
    max_results: int,
    api_key: str,
    content_type: str,
    source_label: str,
) -> Generator[dict, None, None]:
    if api_key:
        yield from _via_springer_api(query, max_results, api_key, content_type, source_label)
    else:
        yield from _via_crossref(query, max_results, content_type, source_label)


# ── Springer Metadata API ──────────────────────────────────────────────────────

def _via_springer_api(
    query: str,
    max_results: int,
    api_key: str,
    content_type: str,
    source_label: str,
) -> Generator[dict, None, None]:
    params = {
        "q":       f'{query} type:"{content_type}"',
        "p":       max_results,
        "api_key": api_key,
    }
    try:
        resp = requests.get(_SPRINGER_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[Springer API] {content_type} error: {e}")
        return

    for record in data.get("records", []):
        abstract = (record.get("abstract") or "").strip()
        if len(abstract) < 30:
            continue

        doi = record.get("doi") or ""
        url_entries = record.get("url") or []
        url = (
            f"https://doi.org/{doi}" if doi
            else (url_entries[0].get("value", "") if url_entries else "")
        )

        creators = record.get("creators") or []
        names = [c.get("creator", "") for c in creators[:3]]
        authors = ", ".join(names)
        if len(creators) > 3:
            authors += " et al."

        pub_date = record.get("publicationDate") or ""
        year = int(pub_date[:4]) if len(pub_date) >= 4 and pub_date[:4].isdigit() else None

        yield {
            "title":    record.get("title") or "",
            "abstract": abstract,
            "year":     year,
            "authors":  authors,
            "url":      url,
            "source":   source_label,
        }


# ── CrossRef fallback (Springer DOI prefix 10.1007) ──────────────────────────

def _via_crossref(
    query: str,
    max_results: int,
    content_type: str,
    source_label: str,
) -> Generator[dict, None, None]:
    crossref_type = "journal-article" if content_type == "Journal Article" else "book-chapter"
    params = {
        "query":  query,
        "rows":   max_results,
        "filter": f"prefix:10.1007,type:{crossref_type}",
        "select": "title,abstract,author,published,URL,DOI,container-title",
        "mailto": _CROSSREF_MAILTO,
    }
    try:
        resp = requests.get(_CROSSREF_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[Springer/CrossRef] {content_type} error: {e}")
        return

    for item in data.get("message", {}).get("items", []):
        abstract = item.get("abstract") or ""
        if not abstract:
            continue
        abstract = re.sub(r"<[^>]+>", " ", abstract).strip()
        if len(abstract) < 30:
            continue

        title_list = item.get("title") or []
        title = title_list[0] if title_list else ""
        doi = item.get("DOI") or ""
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

        authors_raw = item.get("author") or []
        names = []
        for a in authors_raw[:3]:
            given  = a.get("given", "")
            family = a.get("family", "")
            names.append(f"{given} {family}".strip())
        authors = ", ".join(names)
        if len(authors_raw) > 3:
            authors += " et al."

        year = None
        for key in ("published", "published-print", "published-online"):
            dp = item.get(key, {}).get("date-parts")
            if dp and dp[0]:
                year = dp[0][0]
                break

        yield {
            "title":    title,
            "abstract": abstract,
            "year":     year,
            "authors":  authors,
            "url":      url,
            "source":   source_label,
        }
