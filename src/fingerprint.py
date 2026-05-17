"""N-gram fingerprint similarity using the Winnowing algorithm.

Winnowing is the same underlying technique used by MOSS and similar to
what Turnitin applies internally.  It works in three steps:
  1. Normalize text → character k-grams → hash each k-gram
  2. Slide a window of size w; keep the minimum hash per window
  3. The resulting set of hashes is the document "fingerprint"

Two documents share a fingerprint hash only when they share the exact
same k-character sequence, so even paraphrased sentences with identical
phrases will be caught.
"""

import re
import unicodedata
from dataclasses import dataclass, field

# Winnowing parameters
# Smaller k catches more overlaps in short texts (abstracts ~300 words).
# Larger k is more precise but misses paraphrased phrases.
CHAR_K   = 8    # k-gram length (chars): 8-char sequences (e.g. "federate")
WORD_K   = 3    # word n-gram length: 3-word sequences
WIN_SIZE = 4    # sliding window size for hash selection


@dataclass
class MatchedSegment:
    source_paragraph: str      # paragraph from the uploaded paper
    candidate_snippet: str     # matching text from the candidate paper
    overlap_score: float       # Jaccard similarity of this pair (0-100)
    paragraph_index: int       # 0-based index in source paragraphs


@dataclass
class FingerprintResult:
    score: float                              # overall fingerprint similarity 0-100
    matched_segments: list[MatchedSegment] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return len(self.matched_segments) > 0


# ── Public API ─────────────────────────────────────────────────────────────────

def compute_fingerprint(source_text: str, candidate_text: str) -> FingerprintResult:
    """Return fingerprint similarity between source and candidate texts."""
    src_fp   = _fingerprint(source_text)
    cand_fp  = _fingerprint(candidate_text)
    score    = _jaccard(src_fp, cand_fp) * 100

    segments = _find_matching_segments(source_text, candidate_text)
    return FingerprintResult(score=round(score, 1), matched_segments=segments)


# ── Winnowing internals ────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s一-鿿]", "", text)  # keep CJK + alphanumeric
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _char_kgrams(text: str, k: int = CHAR_K) -> list[str]:
    n = _normalize(text)
    return [n[i: i + k] for i in range(len(n) - k + 1)]


def _word_ngrams(text: str, n: int = WORD_K) -> list[str]:
    words = _normalize(text).split()
    return [" ".join(words[i: i + n]) for i in range(len(words) - n + 1)]


def _hash_list(items: list[str]) -> list[int]:
    return [hash(s) & 0xFFFF_FFFF for s in items]


def _winnow(hashes: list[int], w: int = WIN_SIZE) -> set[int]:
    """Select the minimum hash in each sliding window."""
    if len(hashes) < w:
        return set(hashes)
    fp: set[int] = set()
    for i in range(len(hashes) - w + 1):
        fp.add(min(hashes[i: i + w]))
    return fp


def _fingerprint(text: str) -> set[int]:
    """Combined char k-gram + word n-gram fingerprint."""
    char_fp = _winnow(_hash_list(_char_kgrams(text)))
    word_fp = _winnow(_hash_list(_word_ngrams(text)))
    return char_fp | word_fp


def _jaccard(fp1: set[int], fp2: set[int]) -> float:
    if not fp1 or not fp2:
        return 0.0
    inter = len(fp1 & fp2)
    union = len(fp1 | fp2)
    return inter / union if union else 0.0


# ── Paragraph-level matching ───────────────────────────────────────────────────

def _split_paragraphs(text: str, min_chars: int = 40) -> list[str]:
    """Split text into meaningful paragraphs."""
    # Split on blank lines or sentence-ending punctuation followed by newline
    parts = re.split(r"\n{2,}|(?<=[。！？\.!?])\n", text)
    result = []
    buf = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        buf = (buf + " " + part).strip() if buf else part
        if len(buf) >= min_chars:
            result.append(buf)
            buf = ""
    if buf and len(buf) >= min_chars:
        result.append(buf)
    return result


def _sentence_windows(text: str, window: int = 3) -> list[str]:
    """Sliding windows of `window` sentences for the candidate text."""
    # Tokenize into sentences
    sents = re.split(r"(?<=[。！？\.!?])\s+", text.strip())
    sents = [s.strip() for s in sents if len(s.strip()) > 10]
    if len(sents) <= window:
        return [text]
    return [" ".join(sents[i: i + window]) for i in range(len(sents) - window + 1)]


def _find_matching_segments(
    source_text: str,
    candidate_text: str,
    min_score: float = 0.01,   # minimum Jaccard to report (lower = more sensitive)
    top_n: int = 5,             # max matched paragraphs to return
) -> list[MatchedSegment]:
    """For each source paragraph, find the best-matching snippet in candidate."""
    source_paras = _split_paragraphs(source_text)
    cand_windows = _sentence_windows(candidate_text)

    # Pre-compute candidate fingerprints
    cand_fps = [_fingerprint(w) for w in cand_windows]

    matches: list[MatchedSegment] = []

    for idx, para in enumerate(source_paras):
        src_fp = _fingerprint(para)
        if not src_fp:
            continue

        best_score = 0.0
        best_snippet = ""
        for cand_win, cand_fp in zip(cand_windows, cand_fps):
            j = _jaccard(src_fp, cand_fp)
            if j > best_score:
                best_score = j
                best_snippet = cand_win

        if best_score >= min_score:
            matches.append(MatchedSegment(
                source_paragraph=para[:300],
                candidate_snippet=best_snippet[:300],
                overlap_score=round(best_score * 100, 1),
                paragraph_index=idx,
            ))

    # Return top matches sorted by score
    matches.sort(key=lambda m: m.overlap_score, reverse=True)
    return matches[:top_n]
