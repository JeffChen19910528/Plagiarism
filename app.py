"""Academic Plagiarism Checker — main Streamlit application."""

import pandas as pd
import streamlit as st

from src.document_parser import parse_paper_structured
from src.i18n import LANG_OPTIONS, t
from src.similarity import SimilarityResult, build_similarity_result, rank_results
from src.text_processor import build_search_query
from src.searchers import (
    arxiv_searcher,
    crossref_searcher,
    google_scholar,
    ndltd_searcher,
    semantic_scholar,
    springer_searcher,
)

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Plagiarism Checker",
    page_icon="🔍",
    layout="wide",
)

st.markdown("""
<style>
.risk-high   { color: #d32f2f; font-weight: bold; }
.risk-medium { color: #f57c00; font-weight: bold; }
.risk-low    { color: #388e3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Language selection (top-level, persists in session_state) ─────────────────

if "lang" not in st.session_state:
    st.session_state["lang"] = "zh"

lang_display = {v: k for k, v in LANG_OPTIONS.items()}
selected_lang_name = st.selectbox(
    "🌐 " + t("lang_label", st.session_state["lang"]),
    options=list(LANG_OPTIONS.keys()),
    index=list(LANG_OPTIONS.values()).index(st.session_state["lang"]),
    key="lang_selector",
)
st.session_state["lang"] = LANG_OPTIONS[selected_lang_name]
lang = st.session_state["lang"]


# ── Helper functions ───────────────────────────────────────────────────────────

def render_results(results: list, lang: str) -> None:
    risk_cls_map = {
        t("risk_high", lang):   "risk-high",
        t("risk_medium", lang): "risk-medium",
        t("risk_low", lang):    "risk-low",
    }
    for i, r in enumerate(results, 1):
        risk_cls = risk_cls_map.get(r.risk_level, "risk-low")
        with st.expander(
            t("expander_result", lang,
              icon=r.risk_color, i=i, title=r.title[:90], score=r.combined_score),
            expanded=(r.combined_score >= 60),
        ):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"{t('label_author', lang)} {r.authors or t('unknown', lang)}")
                st.markdown(f"{t('label_year', lang)} {r.year or t('unknown', lang)}")
                if r.url:
                    st.markdown(f"{t('label_link', lang)} [{r.url}]({r.url})")
                st.markdown(f"{t('label_abstract2', lang)} {r.abstract[:400]}…")
                if r.matched_keywords:
                    kws = "`, `".join(r.matched_keywords)
                    st.markdown(f"{t('label_keywords2', lang)} `{kws}`")
            with c2:
                st.markdown(f"{t('label_source', lang)} `{r.source}`")
                st.markdown(
                    f"<span class='{risk_cls}'>"
                    f"{t('label_risk', lang)}{r.risk_level}</span>",
                    unsafe_allow_html=True,
                )
                st.metric(t("metric_combined", lang), f"{r.combined_score:.1f}%")
                st.metric(t("metric_tfidf",    lang), f"{r.tfidf_score:.1f}%")
                st.metric(t("metric_ngram",    lang), f"{r.fingerprint_score:.1f}%")
                st.metric(t("metric_keyword",  lang), f"{r.keyword_overlap:.1f}%")

            # ── Paragraph-level matches ───────────────────────────────────────
            if r.fingerprint.has_matches:
                st.markdown("---")
                st.markdown(t("section_paragraph", lang))
                for seg in r.fingerprint.matched_segments:
                    seg_color = (
                        "#ffebee" if seg.overlap_score >= 15 else
                        "#fff8e1" if seg.overlap_score >= 7  else
                        "#f1f8e9"
                    )
                    st.markdown(
                        f"""<div style="border-left:4px solid #888;padding:8px 12px;
                            margin:6px 0;background:{seg_color};border-radius:4px;
                            font-size:0.9em">
                        <b>{t('para_source', lang, n=seg.paragraph_index+1)}</b>
                        &nbsp;→&nbsp;
                        {t('para_overlap', lang)} <b>{seg.overlap_score:.1f}%</b><br>
                        <span style="color:#555">{seg.source_paragraph}</span><br><br>
                        <b>{t('para_candidate', lang)}</b><br>
                        <span style="color:#1a237e">{seg.candidate_snippet}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )


def to_dataframe(results: list, lang: str) -> pd.DataFrame:
    rows = []
    for r in results:
        seg_summary = "; ".join(
            f"#{s.paragraph_index+1}({s.overlap_score:.1f}%)"
            for s in r.fingerprint.matched_segments
        )
        rows.append({
            t("metric_combined", lang):  r.combined_score,
            t("metric_tfidf",    lang):  r.tfidf_score,
            t("metric_ngram",    lang):  r.fingerprint_score,
            t("metric_keyword",  lang):  r.keyword_overlap,
            "Matched Paragraphs":        seg_summary,
            "Title":                     r.title,
            "Authors":                   r.authors,
            "Year":                      r.year,
            "Source":                    r.source,
            "URL":                       r.url,
            "Abstract":                  r.abstract[:300],
        })
    return pd.DataFrame(rows)


def deduplicate(results: list) -> list:
    seen: set[str] = set()
    unique = []
    for r in results:
        key = r.title.strip().lower()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def _run_search(gen, source_name: str, limit: int, source_text: str,
                keywords: list, results: list, progress_state: dict,
                lang: str) -> None:
    """Iterate a searcher generator, updating the per-result progress bar."""
    for c in gen:
        results.append(build_similarity_result(
            title=c["title"], url=c["url"], source=c["source"],
            year=c["year"], authors=c["authors"], abstract=c["abstract"],
            source_text=source_text, source_keywords=keywords,
        ))
        progress_state["done"] += 1
        pct = min(progress_state["done"] / progress_state["total"], 1.0)
        progress_state["bar"].progress(
            pct,
            text=t("progress_fmt", lang,
                   source=source_name,
                   count=progress_state["done"],
                   pct=pct * 100),
        )


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title(t("sidebar_title", lang))

    st.subheader(t("sidebar_sources", lang))
    use_semantic = st.checkbox(t("src_semantic", lang), value=True)
    use_arxiv    = st.checkbox(t("src_arxiv",    lang), value=True)
    use_crossref = st.checkbox(t("src_crossref", lang), value=True)
    use_ndltd    = st.checkbox(t("src_ndltd",    lang), value=True)
    use_gscholar = st.checkbox(
        t("src_gscholar", lang), value=True,
        help=t("src_gscholar_help", lang),
    )
    use_springer = st.checkbox(
        t("src_springer", lang), value=True,
        help=t("src_springer_help", lang),
    )

    st.subheader(t("sidebar_limits", lang))
    semantic_limit = st.slider(t("limit_semantic", lang), 5, 50, 20)
    arxiv_limit    = st.slider(t("limit_arxiv",    lang), 5, 20, 10)
    crossref_limit = st.slider(t("limit_crossref", lang), 5, 20, 10)
    ndltd_limit    = st.slider(t("limit_ndltd",    lang), 5, 20, 10)
    gscholar_limit = st.slider(t("limit_gscholar", lang), 5, 20, 10)
    springer_limit = st.slider(t("limit_springer", lang), 5, 20, 10)

    st.subheader(t("sidebar_threshold", lang))
    threshold = st.slider(t("threshold_label", lang), 0, 100, 10)

    st.markdown("---")
    st.subheader(t("sidebar_apikey", lang))
    ss_api_key = st.text_input(
        t("apikey_label", lang),
        type="password",
        help=t("apikey_help", lang),
    )
    springer_api_key = st.text_input(
        t("apikey_springer_label", lang),
        type="password",
        help=t("apikey_springer_help", lang),
    )

    st.markdown("---")
    st.caption(t("sidebar_version", lang))

# ── Main UI ────────────────────────────────────────────────────────────────────

st.title(t("app_title",    lang))
st.markdown(t("app_subtitle", lang))

col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        t("upload_label", lang),
        type=["pdf", "docx", "doc"],
        help=t("upload_help", lang),
    )

with col_info:
    st.info(t("info_sources", lang))

if not uploaded_file:
    st.stop()

# ── Parse document ─────────────────────────────────────────────────────────────

with st.spinner(t("spinner_parse", lang)):
    try:
        parsed = parse_paper_structured(uploaded_file)
    except Exception as e:
        st.error(t("err_parse", lang) + str(e))
        st.stop()

raw_text     = parsed["raw_text"]
title        = parsed["title"]
abstract     = parsed["abstract"]
keywords     = parsed["keywords"]
body         = parsed["body"]
parse_source = parsed["parse_source"]

if len(raw_text.strip()) < 100:
    st.error(t("err_short", lang))
    st.stop()

source_text = f"{title} {abstract} {body}"
query       = build_search_query(title, keywords, abstract)

# ── Show parsed info ───────────────────────────────────────────────────────────

with st.expander(t("expander_parsed", lang), expanded=True):
    _source_badge = {
        "GROBID":  ("🤖", t("parse_src_grobid",  lang)),
        "Layout":  ("📐", t("parse_src_layout",  lang)),
        "Regex":   ("🔤", t("parse_src_regex",   lang)),
    }.get(parse_source, ("🔤", parse_source))
    st.caption(
        f"{t('parse_src_label', lang)} {_source_badge[0]} **{_source_badge[1]}**"
    )
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"{t('label_title',    lang)} {title}")
        st.markdown(f"{t('label_abstract', lang)} {abstract[:400]}…")
    with c2:
        if keywords:
            st.markdown(t("label_keywords", lang))
            for kw in keywords:
                st.markdown(f"- {kw}")
        st.markdown(t("label_query", lang))
        st.code(query[:200], language=None)

# ── Search & compare ───────────────────────────────────────────────────────────

if not st.button(t("btn_start", lang), type="primary", use_container_width=True):
    st.stop()

total_limit = sum([
    semantic_limit if use_semantic else 0,
    arxiv_limit    if use_arxiv    else 0,
    crossref_limit if use_crossref else 0,
    ndltd_limit    if use_ndltd    else 0,
    gscholar_limit if use_gscholar else 0,
    springer_limit if use_springer else 0,
])

if total_limit == 0:
    st.warning(t("warn_no_source", lang))
    st.stop()

results: list[SimilarityResult] = []
progress_bar  = st.progress(0.0, text=t("progress_searching", lang))
status_holder = st.empty()

ps = {"bar": progress_bar, "done": 0, "total": max(total_limit, 1)}

if use_semantic:
    status_holder.info(t("status_semantic", lang))
    try:
        _run_search(
            semantic_scholar.search(query, max_results=semantic_limit, api_key=ss_api_key),
            "Semantic Scholar", semantic_limit, source_text, keywords, results, ps, lang,
        )
    except Exception as e:
        st.warning(t("warn_semantic", lang) + str(e))

if use_arxiv:
    status_holder.info(t("status_arxiv", lang))
    try:
        _run_search(
            arxiv_searcher.search(query, max_results=arxiv_limit),
            "arXiv", arxiv_limit, source_text, keywords, results, ps, lang,
        )
    except Exception as e:
        st.warning(t("warn_arxiv", lang) + str(e))

if use_crossref:
    status_holder.info(t("status_crossref", lang))
    try:
        _run_search(
            crossref_searcher.search(query, max_results=crossref_limit),
            "CrossRef", crossref_limit, source_text, keywords, results, ps, lang,
        )
    except Exception as e:
        st.warning(t("warn_crossref", lang) + str(e))

if use_ndltd:
    status_holder.info(t("status_ndltd", lang))
    try:
        _run_search(
            ndltd_searcher.search(query, max_results=ndltd_limit),
            "NDLTD", ndltd_limit, source_text, keywords, results, ps, lang,
        )
    except Exception as e:
        st.warning(t("warn_ndltd", lang) + str(e))

if use_gscholar:
    status_holder.info(t("status_gscholar", lang))
    try:
        _run_search(
            google_scholar.search(query, max_results=gscholar_limit),
            "Google Scholar", gscholar_limit, source_text, keywords, results, ps, lang,
        )
    except Exception as e:
        st.warning(t("warn_gscholar", lang) + str(e))

if use_springer:
    status_holder.info(t("status_springer", lang))
    try:
        _run_search(
            springer_searcher.search(query, max_results=springer_limit, api_key=springer_api_key),
            "Springer", springer_limit, source_text, keywords, results, ps, lang,
        )
    except Exception as e:
        st.warning(t("warn_springer", lang) + str(e))

progress_bar.progress(1.0, text="100%")
status_holder.empty()

# ── Results ────────────────────────────────────────────────────────────────────

ranked   = rank_results(deduplicate(results))
filtered = [r for r in ranked if r.combined_score >= threshold]

st.markdown("---")
st.subheader(t("section_summary", lang))

high   = sum(1 for r in filtered if r.combined_score >= 60)
medium = sum(1 for r in filtered if 35 <= r.combined_score < 60)
low    = sum(1 for r in filtered if r.combined_score < 35)

m1, m2, m3, m4 = st.columns(4)
m1.metric(t("metric_total",  lang), len(filtered))
m2.metric(t("metric_high",   lang), high)
m3.metric(t("metric_medium", lang), medium)
m4.metric(t("metric_low",    lang), low)

if not filtered:
    st.success(t("no_results", lang, threshold=threshold))
else:
    st.subheader(t("section_list", lang))
    render_results(filtered, lang)

    df  = to_dataframe(filtered, lang)
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        t("btn_download", lang),
        data=csv,
        file_name="plagiarism_report.csv",
        mime="text/csv",
    )
