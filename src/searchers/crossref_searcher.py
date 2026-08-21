"""Search CrossRef API (free, covers broad academic journals)."""

import requests
from typing import Generator

BASE_URL = "https://api.crossref.org/works"
MAILTO = "plagiarism-checker@example.com"  # CrossRef polite pool


def search(query: str, max_results: int = 10, api_key: str = "") -> Generator[dict, None, None]:
    # api_key is unused (CrossRef needs none) but kept so every searcher
    # shares one call signature for src/sources.py's uniform dispatch.
    params = {
        "query": query,
        "rows": max_results,
        "select": "title,abstract,author,published,URL,DOI,container-title",
        "mailto": MAILTO,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[CrossRef] Request error: {e}")
        return

    items = data.get("message", {}).get("items", [])
    for item in items:
        abstract = item.get("abstract") or ""
        if not abstract:
            continue

        # CrossRef wraps abstract in JATS XML tags
        import re
        abstract = re.sub(r"<[^>]+>", " ", abstract).strip()
        if len(abstract) < 30:
            continue

        title_list = item.get("title") or []
        title = title_list[0] if title_list else ""
        url = item.get("URL") or (f"https://doi.org/{item['DOI']}" if item.get("DOI") else "")

        authors_raw = item.get("author") or []
        authors = _format_authors(authors_raw)

        year = _extract_year(item)
        container = (item.get("container-title") or [""])[0]
        source = _detect_source(url, container)

        yield {
            "title": title,
            "abstract": abstract,
            "year": year,
            "authors": authors,
            "url": url,
            "source": source,
        }


def _format_authors(authors_raw: list) -> str:
    names = []
    for a in authors_raw[:3]:
        given = a.get("given", "")
        family = a.get("family", "")
        names.append(f"{given} {family}".strip())
    result = ", ".join(names)
    if len(authors_raw) > 3:
        result += " et al."
    return result


def _extract_year(item: dict) -> int | None:
    for key in ("published", "published-print", "published-online"):
        dp = item.get(key, {}).get("date-parts")
        if dp and dp[0]:
            return dp[0][0]
    return None


def _detect_source(url: str, container: str) -> str:
    url_lower = url.lower()
    if "10.1109" in url_lower or "ieee" in container.lower():
        return "IEEE"
    if "10.1145" in url_lower or "acm" in container.lower():
        return "ACM"
    if "10.1007" in url_lower or "springer" in container.lower():
        return "Springer"
    if "10.1016" in url_lower or "elsevier" in container.lower():
        return "Elsevier"
    return "CrossRef"
