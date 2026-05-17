"""Search Google Scholar via the `scholarly` library (no API key required)."""

import time
from typing import Generator


def search(query: str, max_results: int = 10) -> Generator[dict, None, None]:
    """Yield paper dicts from Google Scholar.

    Note: scholarly scrapes Google Scholar and may be rate-limited.
    If it fails, a warning is printed and the generator returns empty.
    """
    try:
        from scholarly import scholarly as _scholarly
    except ImportError:
        print("[GoogleScholar] scholarly required: pip install scholarly")
        return

    try:
        search_gen = _scholarly.search_pubs(query)
        count = 0
        while count < max_results:
            try:
                pub = next(search_gen)
            except StopIteration:
                break

            bib      = pub.get("bib", {})
            title    = bib.get("title", "").strip()
            abstract = bib.get("abstract", "").strip()

            if not title or len(title) < 5:
                continue

            # Google Scholar often omits abstract — still include for title matching
            if not abstract:
                abstract = title  # use title as minimal text for similarity

            authors_raw = bib.get("author", [])
            if isinstance(authors_raw, list):
                authors = ", ".join(str(a) for a in authors_raw[:3])
                if len(authors_raw) > 3:
                    authors += " et al."
            else:
                authors = str(authors_raw)

            year = bib.get("pub_year")
            try:
                year = int(year) if year else None
            except (ValueError, TypeError):
                year = None

            url = (
                pub.get("pub_url")
                or pub.get("eprint_url")
                or ""
            )

            yield {
                "title": title,
                "abstract": abstract,
                "year": year,
                "authors": authors,
                "url": url,
                "source": "Google Scholar",
            }
            count += 1

            # Brief pause to reduce chance of being blocked
            time.sleep(0.5)

    except Exception as e:
        err = str(e)
        if "MaxTriesExceeded" in err or "CaptchaError" in err or "bot" in err.lower():
            print("[GoogleScholar] Rate limited or CAPTCHA triggered. Try again later.")
        else:
            print(f"[GoogleScholar] Error: {e}")
