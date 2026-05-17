"""Search Semantic Scholar API (free, covers IEEE/ACM/arXiv/Nature etc.)."""

import time
import requests
from typing import Generator

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,year,authors,externalIds,url,openAccessPdf"


def search(query: str, max_results: int = 20, api_key: str = "") -> Generator[dict, None, None]:
    """Yield paper dicts from Semantic Scholar for the given query."""
    headers = {"x-api-key": api_key} if api_key else {}
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": FIELDS,
    }

    try:
        resp = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[SemanticScholar] Request error: {e}")
        return

    for paper in data.get("data", []):
        abstract = paper.get("abstract") or ""
        if not abstract:
            continue

        authors_list = paper.get("authors") or []
        authors = ", ".join(a.get("name", "") for a in authors_list[:3])
        if len(authors_list) > 3:
            authors += " et al."

        # Prefer open-access PDF link, fall back to S2 URL
        oap = paper.get("openAccessPdf") or {}
        url = oap.get("url") or paper.get("url") or ""
        ext = paper.get("externalIds") or {}
        if not url and ext.get("DOI"):
            url = f"https://doi.org/{ext['DOI']}"

        # Tag the source venue
        source = _detect_source(ext)

        yield {
            "title": paper.get("title") or "",
            "abstract": abstract,
            "year": paper.get("year"),
            "authors": authors,
            "url": url,
            "source": source,
        }


def _detect_source(external_ids: dict) -> str:
    if external_ids.get("DBLP"):
        dblp = external_ids["DBLP"].lower()
        if "conf/ieee" in dblp or "journals/ieee" in dblp:
            return "IEEE"
        if "conf/acm" in dblp or "journals/acm" in dblp:
            return "ACM"
    if external_ids.get("ArXiv"):
        return "arXiv"
    if external_ids.get("PubMed"):
        return "PubMed"
    if external_ids.get("DOI"):
        doi = external_ids["DOI"].lower()
        if "10.1109" in doi:
            return "IEEE"
        if "10.1145" in doi:
            return "ACM"
        if "10.1007" in doi:
            return "Springer"
        if "10.1016" in doi:
            return "Elsevier"
    return "Semantic Scholar"
