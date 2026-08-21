"""Search Taiwan NDLTD — 國家圖書館碩博士論文知識加值系統 (ndltd.ncl.edu.tw)."""

import re
import requests
from typing import Generator
from urllib.parse import quote

SEARCH_URL = "https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8",
    "Referer": "https://ndltd.ncl.edu.tw/",
}


def search(query: str, max_results: int = 10, api_key: str = "") -> Generator[dict, None, None]:
    """Yield thesis dicts from Taiwan NDLTD.

    api_key is unused (NDLTD needs none) but kept so every searcher shares
    one call signature for src/sources.py's uniform dispatch.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[NDLTD] beautifulsoup4 required: pip install beautifulsoup4 lxml")
        return

    # kinda = keyword in all fields; s param uses CGI query syntax
    params = {
        "o": "dnclcdr",
        "s": f'kinda="{query}".',
        "searchmode": "basic",
        "T": "0",
        "action": "setquery",
    }

    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
        if resp.status_code != 200:
            print(f"[NDLTD] HTTP {resp.status_code}")
            return
    except requests.RequestException as e:
        print(f"[NDLTD] Request error: {e}")
        return

    soup = BeautifulSoup(resp.text, "lxml")
    count = 0

    # Strategy 1: table rows with thesis data (classic CGI interface)
    for row in soup.select("table tr"):
        if count >= max_results:
            break
        result = _parse_row(row)
        if result:
            yield result
            count += 1

    # Strategy 2: div-based result blocks (newer interface)
    if count == 0:
        for block in soup.select("div.result_list_item, div.thesis-item, li.search-result"):
            if count >= max_results:
                break
            result = _parse_block(block)
            if result:
                yield result
                count += 1

    # Strategy 3: fallback — extract any links to thesis detail pages
    if count == 0:
        for link in soup.find_all("a", href=re.compile(r"gs32|etdcgi|thesis")):
            if count >= max_results:
                break
            title = link.get_text(strip=True)
            if len(title) < 10:
                continue
            href = link.get("href", "")
            if not href.startswith("http"):
                href = "https://ndltd.ncl.edu.tw" + href
            yield {
                "title": title,
                "abstract": "",
                "year": None,
                "authors": "",
                "url": href,
                "source": "碩博士論文網",
            }
            count += 1


def _parse_row(row) -> dict | None:
    cells = row.find_all("td")
    if len(cells) < 2:
        return None

    # Look for a cell that has a link long enough to be a title
    title_link = None
    for cell in cells:
        a = cell.find("a")
        if a and len(a.get_text(strip=True)) > 10:
            title_link = a
            break
    if not title_link:
        return None

    title = title_link.get_text(strip=True)
    href  = title_link.get("href", "")
    if not href.startswith("http"):
        href = "https://ndltd.ncl.edu.tw" + href

    # Remaining cells for metadata
    texts = [c.get_text(strip=True) for c in cells]
    year    = _extract_year(texts)
    authors = _extract_author(texts)

    # Abstract from sibling row or detail page (best-effort)
    abstract = _extract_abstract_from_sibling(row)

    return {
        "title": title,
        "abstract": abstract,
        "year": year,
        "authors": authors,
        "url": href,
        "source": "碩博士論文網",
    }


def _parse_block(block) -> dict | None:
    title_el = block.find(["h2", "h3", "h4", "a", "strong"])
    if not title_el:
        return None
    title = title_el.get_text(strip=True)
    if len(title) < 10:
        return None

    href = ""
    a = block.find("a")
    if a:
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://ndltd.ncl.edu.tw" + href

    texts = block.get_text(separator=" ", strip=True)
    year    = _extract_year([texts])
    authors = _extract_author([texts])
    abstract = _extract_abstract_inline(block)

    return {
        "title": title,
        "abstract": abstract,
        "year": year,
        "authors": authors,
        "url": href,
        "source": "碩博士論文網",
    }


def _extract_year(texts: list[str]) -> int | None:
    for t in texts:
        m = re.search(r"\b(19|20)\d{2}\b", t)
        if m:
            return int(m.group())
    return None


def _extract_author(texts: list[str]) -> str:
    for t in texts:
        # Common patterns: "作者：王小明" or just a short name-like token
        m = re.search(r"作者[：:]\s*(\S+)", t)
        if m:
            return m.group(1)
        # Fallback: short Chinese-like string
        m = re.search(r"[一-鿿]{2,4}(?:\s*[一-鿿]{2,4})?", t)
        if m and len(m.group()) <= 12:
            return m.group()
    return ""


def _extract_abstract_from_sibling(row) -> str:
    next_row = row.find_next_sibling("tr")
    if next_row:
        text = next_row.get_text(separator=" ", strip=True)
        if len(text) > 30:
            return text[:500]
    return ""


def _extract_abstract_inline(block) -> str:
    for tag in block.find_all(["p", "div", "span"]):
        text = tag.get_text(strip=True)
        if len(text) > 40:
            return text[:500]
    return ""
