"""Compute text similarity between the uploaded paper and candidate papers."""

import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.fingerprint import FingerprintResult, compute_fingerprint


@dataclass
class SimilarityResult:
    title: str
    url: str
    source: str
    year: Optional[int]
    authors: str
    abstract: str
    tfidf_score: float             # 0-100
    keyword_overlap: float         # 0-100
    fingerprint_score: float       # 0-100  (Winnowing n-gram)
    combined_score: float          # weighted combination
    matched_keywords: list[str]
    fingerprint: FingerprintResult = field(default_factory=lambda: FingerprintResult(0.0))

    @property
    def risk_tier(self) -> str:
        """Language-neutral risk bucket: 'high' | 'medium' | 'low'.

        Callers translate this via i18n (t(f"risk_{risk_tier}", lang)) instead
        of relying on a hardcoded display string, so the tier stays valid
        across languages.
        """
        if self.combined_score >= 60:
            return "high"
        if self.combined_score >= 35:
            return "medium"
        return "low"

    @property
    def risk_color(self) -> str:
        return {"high": "🔴", "medium": "🟡", "low": "🟢"}[self.risk_tier]


def compute_tfidf_similarity(source_text: str, candidate_text: str) -> float:
    """Return cosine similarity (0-100) between two texts using TF-IDF."""
    if not source_text.strip() or not candidate_text.strip():
        return 0.0
    try:
        vec = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
            sublinear_tf=True,
        )
        tfidf = vec.fit_transform([source_text, candidate_text])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(float(score) * 100, 1)
    except Exception:
        return 0.0


def compute_keyword_overlap(
    source_text: str, candidate_text: str, keywords: list[str]
) -> tuple[float, list[str]]:
    """Return (overlap_score 0-100, list_of_matched_keywords)."""
    if not keywords:
        return 0.0, []

    cand_lower = candidate_text.lower()
    matched = [kw for kw in keywords if kw.lower() in cand_lower]
    score = (len(matched) / len(keywords)) * 100
    return round(score, 1), matched


def rank_results(results: list["SimilarityResult"]) -> list["SimilarityResult"]:
    return sorted(results, key=lambda r: r.combined_score, reverse=True)


def compute_combined_score(tfidf: float, keyword: float, fingerprint: float) -> float:
    """Weighted score: 45% TF-IDF + 20% keyword + 35% n-gram fingerprint."""
    return round(0.45 * tfidf + 0.20 * keyword + 0.35 * fingerprint, 1)


def build_similarity_result(
    *,
    title: str,
    url: str,
    source: str,
    year: Optional[int],
    authors: str,
    abstract: str,
    source_text: str,
    source_keywords: list[str],
) -> SimilarityResult:
    tfidf          = compute_tfidf_similarity(source_text, abstract)
    keyword_score, matched = compute_keyword_overlap(source_text, abstract, source_keywords)
    fp_result      = compute_fingerprint(source_text, abstract)
    combined       = compute_combined_score(tfidf, keyword_score, fp_result.score)

    return SimilarityResult(
        title=title,
        url=url,
        source=source,
        year=year,
        authors=authors,
        abstract=abstract,
        tfidf_score=tfidf,
        keyword_overlap=keyword_score,
        fingerprint_score=fp_result.score,
        combined_score=combined,
        matched_keywords=matched,
        fingerprint=fp_result,
    )
