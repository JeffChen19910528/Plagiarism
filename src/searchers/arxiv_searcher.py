"""Search arXiv via its public Atom feed API (no key required)."""

import re
import requests
from typing import Generator

BASE_URL = "http://export.arxiv.org/api/query"


def search(query: str, max_results: int = 10) -> Generator[dict, None, None]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[arXiv] Request error: {e}")
        return

    entries = _parse_atom(resp.text)
    for entry in entries:
        if entry.get("abstract"):
            yield entry


def _parse_atom(xml_text: str) -> list[dict]:
    """Minimal Atom parser — avoids feedparser dependency."""
    entries = []
    for block in re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL):
        title = _tag(block, "title")
        abstract = _tag(block, "summary")
        link = _attr(block, "link", "href", 'type="text/html"')
        if not link:
            link = _attr(block, "link", "href")
        year_match = re.search(r"<published>(\d{4})", block)
        year = int(year_match.group(1)) if year_match else None
        authors = re.findall(r"<name>(.*?)</name>", block)
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."

        entries.append({
            "title": title,
            "abstract": abstract,
            "year": year,
            "authors": author_str,
            "url": link,
            "source": "arXiv",
        })
    return entries


def _tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _attr(text: str, tag: str, attr: str, extra_filter: str = "") -> str:
    pattern = rf'<{tag}[^>]*{re.escape(extra_filter)}[^>]*{attr}="([^"]+)"'
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else ""
