"""Registry of academic search sources — single source of truth for the
sidebar UI and the search-and-compare loop in app.py.

Adding a new source means adding one SourceConfig entry (plus its
searcher module and i18n strings) instead of touching four separate
blocks of app.py.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from src.searchers import (
    arxiv_searcher,
    crossref_searcher,
    google_scholar,
    ndltd_searcher,
    semantic_scholar,
    springer_searcher,
)


@dataclass(frozen=True)
class SourceConfig:
    id: str                    # i18n key suffix: src_<id>, limit_<id>, status_<id>, warn_<id>
    display_name: str          # proper noun shown in the progress bar
    search: Callable
    slider_range: tuple[int, int, int]   # (min, max, default)
    has_help: bool = False               # whether src_<id>_help exists in i18n
    api_key_field: Optional[str] = None  # key into the api_keys dict, if this source takes one


SOURCE_CONFIGS: list[SourceConfig] = [
    SourceConfig(
        id="semantic", display_name="Semantic Scholar",
        search=semantic_scholar.search, slider_range=(5, 50, 20),
        api_key_field="semantic",
    ),
    SourceConfig(
        id="arxiv", display_name="arXiv",
        search=arxiv_searcher.search, slider_range=(5, 20, 10),
    ),
    SourceConfig(
        id="crossref", display_name="CrossRef",
        search=crossref_searcher.search, slider_range=(5, 20, 10),
    ),
    SourceConfig(
        id="ndltd", display_name="NDLTD",
        search=ndltd_searcher.search, slider_range=(5, 20, 10),
    ),
    SourceConfig(
        id="gscholar", display_name="Google Scholar",
        search=google_scholar.search, slider_range=(5, 20, 10),
        has_help=True,
    ),
    SourceConfig(
        id="springer", display_name="Springer",
        search=springer_searcher.search, slider_range=(5, 20, 10),
        has_help=True, api_key_field="springer",
    ),
]
