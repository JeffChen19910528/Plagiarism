# 🔍 Academic Plagiarism Checker

> 🌐 **Language / 語言 / 言語：**
> [繁體中文](README.md) ・ [English](README_EN.md) ・ [日本語](README_JA.md)

A plagiarism detection tool designed for graduate students. Upload your thesis (PDF or Word), and the system automatically searches multiple academic databases to find similar papers and report them by risk level.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 Smart Document Parsing | Three-tier PDF parsing: GROBID ML → font-size layout → Regex; handles all major conference/journal formats |
| 🔎 Multi-source Search | Semantic Scholar, arXiv, CrossRef, Taiwan NDLTD, Google Scholar, Springer |
| 📚 Database Coverage | IEEE, ACM, Springer journals & books, Elsevier, Nature, arXiv, Taiwan theses — 200M+ papers |
| 📊 Similarity Analysis | TF-IDF cosine + N-gram fingerprint + keyword overlap (3-layer) |
| 🔬 Paragraph Matching | Winnowing algorithm for segment-level matching with side-by-side display |
| 🎯 Risk Levels | High (≥60%), Medium (≥35%), Low (<35%) |
| 📈 Live Progress Bar | Per-result progress updates showing current source and percentage |
| 📥 Export Report | One-click CSV download |
| 🌐 Multi-language UI | Traditional Chinese / English / Japanese |
| 🖱️ One-click Launch | Double-click `start.bat` to auto-install and open browser |

---

## 🏗️ Project Structure

```
Plagiarism/
├── start.bat                     # One-click launcher (Windows)
├── app.py                        # Streamlit main app
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── config.toml               # Disable usage stats & email prompt
├── src/
│   ├── i18n.py                   # Multi-language translations (zh/en/ja)
│   ├── document_parser.py        # PDF / DOCX text extraction
│   ├── text_processor.py         # Title, abstract, keyword extraction
│   ├── similarity.py             # Similarity scoring
│   ├── fingerprint.py            # Winnowing N-gram fingerprint algorithm
│   └── searchers/
│       ├── semantic_scholar.py   # Semantic Scholar API (incl. IEEE/ACM)
│       ├── arxiv_searcher.py     # arXiv Atom API
│       ├── crossref_searcher.py  # CrossRef REST API
│       ├── ndltd_searcher.py     # Taiwan NDLTD (web scraping)
│       ├── google_scholar.py     # Google Scholar (scholarly library)
│       └── springer_searcher.py  # Springer journals & books (API or CrossRef fallback)
└── README.md / README_EN.md / README_JA.md
```

---

## 🚀 Quick Start

### Method 1: One-click Launch (Recommended, Windows)

Double-click `start.bat`.

- **First run**: Automatically detects and installs all required packages (needs internet, ~1–3 min)
- **Every run**: Opens browser at `http://localhost:8501`
- **Stop**: Close the command prompt window

> **First-run note**: `start.bat` auto-creates `~/.streamlit/credentials.toml` to skip Streamlit's email subscription prompt. No email input required.

### Method 2: Manual Launch

#### 1. Requirements
- Python 3.11+
- pip

#### 2. Install packages
```bash
pip install -r requirements.txt
```

#### 3. Start
```bash
streamlit run app.py
```
Browser opens at `http://localhost:8501`.

---

## 📖 Usage Guide

### Step 1: Upload your paper
Click "Upload Paper File" and select your PDF or Word file.

> ⚠️ **Note**: Scanned PDFs (image-based) cannot be parsed. Use an OCR tool first.

### Step 2: Configure settings (sidebar)

| Setting | Description |
|---------|-------------|
| Search Sources | Check databases to compare against (all checked by default) |
| Result Limits | Number of papers to retrieve per source |
| Similarity Threshold | Hide results below this % (default: 10%) |
| Semantic Scholar API Key | Increases rate limits (optional) |
| Springer Nature API Key | Enables direct Springer API queries; falls back to CrossRef without a key (optional) |

### Step 3: Start comparison
Click **🚀 Start Comparison**. The progress bar updates in real time for each result retrieved, showing current source and overall percentage.

### Step 4: Review results

- **Summary metrics**: total papers compared, count by risk level
- **Paper list**: title, authors, year, source, link, abstract, matched keywords
- **Similarity scores**:
  - `Combined Score` = TF-IDF × 45% + N-gram fingerprint × 35% + Keyword overlap × 20%
  - `TF-IDF Score`: word-frequency semantic similarity
  - `N-gram Fingerprint`: Winnowing algorithm for exact phrase detection (similar to Turnitin)
  - `Keyword Overlap`: percentage of your keywords found in the candidate paper
- **Paragraph matches**: shows which paragraphs of your paper match the candidate, with color-coded highlighting
  - 🔴 Dark red: high overlap (≥15%)
  - 🟡 Light yellow: medium overlap (7–15%)
  - 🟢 Light green: low overlap (<7%)

### Step 5: Download report
Click **📥 Download CSV Report** for a spreadsheet with all results including matched paragraph details.

---

## 🌐 Switching Language

At the top of the page, select your language from the dropdown:

| Option | Language |
|--------|----------|
| 繁體中文 | Traditional Chinese (default) |
| English | English |
| 日本語 | Japanese |

All UI elements (sidebar, buttons, result labels, CSV column headers) update instantly without reloading.

---

## 🔍 Search Sources

### Semantic Scholar (Recommended)
- **Covers**: IEEE, ACM, Springer, Elsevier, Nature, arXiv — 200M+ papers
- **Cost**: Free; optional API key increases rate limits
- **Apply**: https://www.semanticscholar.org/product/api

### arXiv
- **Covers**: CS, physics, math, EE preprints
- **Cost**: Completely free, no key required

### CrossRef
- **Covers**: Cross-publisher DOI database (journals, conference papers)
- **Cost**: Completely free

### Taiwan NDLTD (Theses)
- **Covers**: Taiwanese master's and doctoral theses (Chinese and English)
- **Cost**: Free (web scraping)
- **Note**: May be temporarily unavailable if the site undergoes maintenance

### Google Scholar
- **Covers**: Multidisciplinary, books, technical reports (Chinese and English)
- **Cost**: Free (via `scholarly` library)
- **Note**: Google rate-limits scraping; if blocked, wait a few minutes or uncheck this source

### Springer (Journals + Books)
- **Covers**: Springer Nature journal articles and book chapters
- **Cost**: Free — without an API key, queries fall back to CrossRef filtered to the Springer DOI prefix `10.1007`
- **API Key (optional)**: Register free at https://dev.springernature.com/ to query the Springer Metadata API directly for richer results
- **Result labels**: Each result's Source field shows `Springer Journal` or `Springer Book`

---

## ⚠️ Risk Levels

| Level | Combined Score | Recommended Action |
|-------|---------------|-------------------|
| 🔴 High Risk | ≥ 60% | Review immediately — check for large text overlap or identical core contributions |
| 🟡 Medium Risk | 35%–59% | Read the candidate carefully — may be legitimate related-work citation |
| 🟢 Low Risk | < 35% | Related topic but low overlap — usually no concern |

> **Important**: High similarity does not always mean plagiarism (e.g., citing related work is normal). Low similarity does not guarantee originality. This tool is for reference only. For final submission verification, use **iThenticate** or **Turnitin**.

---

## 🧩 Technical Architecture

```
User uploads PDF/DOCX
        ↓
   ┌──────────────────────────────────────────────────────┐
   │  Three-tier PDF structure parsing (auto-degradation)  │
   │  ① GROBID API (ML — handles all major formats)        │
   │     → Returns TEI XML; extracts title/abstract/body   │
   │  ② pdfplumber font-size analysis (if GROBID fails)    │
   │     → Detects two-column layout; extracts each column │
   │       separately; joins end-of-line hyphenation       │
   │     → Largest font (excl. drop caps) = title          │
   │  ③ Regex heuristics (DOCX or both layers failed)      │
   │     → Detects IEEE inline "Abstract—" and skips       │
   │       journal headers / author-line artefacts         │
   └──────────────────────────────────────────────────────┘
        ↓
   Structured data (title / abstract / keywords / body)
        ↓
   Build search query string
        ↓
   ┌────────────────────────────────────────────────────┐
   │  Search 6 academic databases                        │
   │  Semantic Scholar / arXiv / CrossRef               │
   │  Taiwan NDLTD / Google Scholar / Springer          │
   └────────────────────────────────────────────────────┘
        ↓ (per-result live progress bar)
   ┌────────────────────────────────────────────────────┐
   │  3-layer similarity analysis (per candidate)        │
   │  ① TF-IDF cosine similarity (scikit-learn) × 45%   │
   │  ② Winnowing N-gram fingerprint × 35%               │
   │     - char 8-gram + word 3-gram                     │
   │     - paragraph segmentation → best match per seg   │
   │  ③ Keyword overlap rate × 20%                       │
   └────────────────────────────────────────────────────┘
        ↓
   Sort + Risk classification (High / Medium / Low)
        ↓
   Display report (paragraph match blocks) / Export CSV
```

---

## 🔧 Advanced Configuration

### PDF Parsing Tiers

| Tier | When used | Advantage |
|------|-----------|-----------|
| 🤖 GROBID | Default (auto on PDF upload) | ML-based; handles IEEE / ACM / Springer / Nature / arXiv and more without any configuration |
| 📐 Font-size + layout analysis | GROBID timeout or failure | Runs locally; uses x0-start band density to find the column gutter; extracts left and right columns with `within_bbox`; uses gutter-crossing detection to separate the full-width header (title/authors) from the two-column body; applies 9 pt edge padding so column-edge characters aren't clipped; skips drop caps and running page headers via font-size tiers |
| 🔤 Regex | DOCX or both upper tiers failed | Handles IEEE inline `Abstract—` and detects author-line artefacts |

**Two-column formats tested**: IEEE Transactions (two-column, abstract in columns), ACM SIGCONF-style federated-learning paper — both extract correctly with proper column order and no word merging.

> **GROBID latency note**: Uses the public Hugging Face Space. Cold-start on the first call can take 10–30 s; subsequent calls typically take 3–5 s. To use a self-hosted instance, change `_GROBID_URL` in `document_parser.py`.

### Get a Semantic Scholar API Key
1. Go to https://www.semanticscholar.org/product/api
2. Click "Get API Key" and fill in the form
3. Free plan: 1 req/sec; with key: 10 req/sec

### Get a Springer Nature API Key
1. Register free at https://dev.springernature.com/
2. Create an application to obtain your API key
3. Enter it in the sidebar "Springer Nature API Key" field to query Springer Metadata API directly
4. Without a key, the tool automatically falls back to CrossRef (results still returned, but slightly fewer)

### Customize Risk Thresholds
In `src/similarity.py`, edit the `risk_level` property:
```python
@property
def risk_level(self) -> str:
    if self.combined_score >= 60:   # change this
        return "高風險"
    if self.combined_score >= 35:   # change this
        return "中風險"
    return "低風險"
```

### Tune N-gram Fingerprint Sensitivity
In `src/fingerprint.py`:
```python
CHAR_K   = 8    # char k-gram length (smaller = more sensitive, more false positives)
WORD_K   = 3    # word n-gram length (3 = detect any 3-word match)
WIN_SIZE = 4    # Winnowing window size
```
Recommended:
- Short abstracts: `CHAR_K=6, WORD_K=3`
- Full-text precise: `CHAR_K=12, WORD_K=5`

---

## 📋 System Requirements

| Item | Requirement |
|------|-------------|
| Python | 3.11+ |
| RAM | 4 GB+ recommended |
| Network | Required for API calls |
| OS | Windows / macOS / Linux |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web UI framework |
| pdfplumber | PDF text extraction |
| python-docx | Word document parsing |
| scikit-learn | TF-IDF similarity |
| requests | HTTP API calls (incl. Springer / CrossRef) |
| pandas | Data handling & CSV export |
| jieba | Chinese tokenization (fallback) |
| beautifulsoup4 + lxml | NDLTD HTML parsing |
| scholarly | Google Scholar search |
