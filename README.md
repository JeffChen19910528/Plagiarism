# 🔍 論文抄襲偵測工具

> 🌐 **語言切換 / Language / 言語：**
> [繁體中文](README.md) ・ [English](README_EN.md) ・ [日本語](README_JA.md)

針對研究生論文撰寫設計的學術相似度比對工具。上傳 PDF 或 Word 格式的論文後，系統會自動搜尋多個學術資料庫，找出相似論文並以風險等級呈現比對結果。

---

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 📄 智慧文件解析 | PDF 三層解析：GROBID ML → 字型大小分析 → Regex；支援所有主流會議格式 |
| 🔎 多來源搜尋 | Semantic Scholar、arXiv、CrossRef、碩博士論文網、Google Scholar、Springer |
| 📚 資料庫涵蓋 | IEEE、ACM、Springer 期刊與書籍、Elsevier、Nature、arXiv、台灣碩博士論文等 200M+ 篇 |
| 📊 相似度計算 | TF-IDF 餘弦相似度 + N-gram 指紋比對 + 關鍵字重疊三層分析 |
| 🔬 段落比對 | Winnowing 演算法逐段比對，標示哪幾段與對方論文吻合 |
| 🎯 風險分級 | 高風險（≥60%）、中風險（≥35%）、低風險（<35%） |
| 📥 報告匯出 | 一鍵下載 CSV 比對報告 |
| 🌐 中英文支援 | 支援中文與英文論文 |
| 🖱️ 一鍵啟動 | 雙擊 BAT 檔即可自動安裝套件並開啟瀏覽器 |
| 📈 精細進度條 | 每取得一筆結果即即時更新百分比，顯示目前來源與進度 |
| 🌐 多語系介面 | 支援繁體中文 / English / 日本語 三語切換 |

---

## 🏗️ 專案架構

```
Plagiarism/
├── start.bat                     # 一鍵啟動（Windows）
├── app.py                        # Streamlit 主程式（Web UI）
├── requirements.txt              # Python 套件清單
├── .streamlit/
│   └── config.toml               # 關閉統計與 email 詢問
├── src/
│   ├── document_parser.py        # PDF / DOCX 文字擷取
│   ├── text_processor.py         # 題目、摘要、關鍵字擷取
│   ├── similarity.py             # TF-IDF 相似度計算
│   ├── i18n.py                   # 多語系翻譯字典（繁中/英/日）
│   ├── fingerprint.py            # Winnowing N-gram 指紋比對演算法
│   ├── sources.py                # 搜尋來源註冊表（UI 與比對迴圈的單一資料來源）
│   └── searchers/
│       ├── semantic_scholar.py   # Semantic Scholar API（含 IEEE/ACM）
│       ├── arxiv_searcher.py     # arXiv Atom API
│       ├── crossref_searcher.py  # CrossRef REST API
│       ├── ndltd_searcher.py     # 台灣碩博士論文網（爬蟲）
│       ├── google_scholar.py     # Google Scholar（scholarly 套件）
│       └── springer_searcher.py  # Springer 期刊與書籍（API 或 CrossRef fallback）
└── README.md / README_EN.md / README_JA.md
```

---

## 🚀 快速開始

### 方法一：一鍵啟動（推薦，Windows）

直接雙擊 `start.bat`。

- **首次執行**：自動安裝所有必要套件（需要網路連線，約 1-3 分鐘）
- **每次執行**：自動開啟瀏覽器到 `http://localhost:8501`
- **停止服務**：關閉命令提示字元視窗即可

> **初次啟動說明**：`start.bat` 會自動建立 `~/.streamlit/credentials.toml` 跳過 Streamlit 的 email 訂閱詢問，無需手動輸入任何 email，直接按 Enter 略過即可。

### 方法二：手動啟動

#### 1. 環境需求

- Python 3.11 以上
- pip

#### 2. 安裝套件

```bash
pip install -r requirements.txt
```

#### 3. 啟動工具

```bash
streamlit run app.py
```

啟動後瀏覽器會自動開啟 `http://localhost:8501`。

---

## 📖 使用教學

### Step 1：上傳論文

在主畫面點選「上傳論文檔案」，選取您的 PDF 或 Word 檔案。

> ⚠️ **注意**：若 PDF 為掃描版（圖片），無法擷取文字，請先使用 OCR 工具轉換。

### Step 2：設定搜尋條件（側邊欄）

| 設定項目 | 說明 |
|----------|------|
| 解析方式 | 畫面頂部顯示目前使用的解析器（GROBID／字型分析／Regex） |
| 搜尋來源 | 勾選要比對的資料庫（預設全勾） |
| 搜尋數量 | 每個來源抓取的論文筆數 |
| 相似度門檻 | 低於此值的結果不顯示（預設 10%） |
| Semantic Scholar API Key | 填入可提高速率上限（選填） |
| Springer Nature API Key | 填入可直接查詢 Springer API；無 key 時自動透過 CrossRef 查詢（選填） |

### Step 3：開始比對

點擊「🚀 開始比對」按鈕，系統依序搜尋各資料庫，進度條會顯示目前進度。

### Step 4：查看結果

比對完成後顯示：

- **摘要統計**：比對總筆數、各風險等級數量
- **詳細列表**：每篇相似論文的題目、作者、年份、來源、連結、摘要與匹配關鍵字
- **相似度指標**：
  - `綜合相似度` = TF-IDF × 45% + N-gram 指紋 × 35% + 關鍵字重疊 × 20%
  - `TF-IDF 相似度`：詞頻語義層面的相似程度
  - `N-gram 指紋`：Winnowing 演算法的字元/詞序列精確比對（類 Turnitin 原理）
  - `關鍵字重疊`：您的關鍵字在對方論文中出現的比例
- **段落比對**：展示您論文中哪幾段與對方文字有 N-gram 吻合，並並排顯示原文與對應片段
  - 🔴 深紅色背景：高度吻合（≥15%）
  - 🟡 淺黃色背景：中度吻合（7-15%）
  - 🟢 淺綠色背景：低度吻合（<7%）

### Step 5：下載報告

點擊「📥 下載 CSV 報告」，取得完整比對結果的 Excel 可讀檔案。

---

## 🔍 搜尋來源說明

### Semantic Scholar（推薦）

- **涵蓋**：IEEE、ACM、Springer、Elsevier、Nature、arXiv 等 200M+ 篇
- **費用**：免費，可申請 API Key 提高速率
- **申請連結**：https://www.semanticscholar.org/product/api

### arXiv

- **涵蓋**：CS、物理、數學、電機等領域預印本論文
- **費用**：完全免費，無需 API Key

### CrossRef

- **涵蓋**：跨出版社 DOI 資料庫（期刊、研討會論文）
- **費用**：完全免費

### 碩博士論文網（台灣 NDLTD）

- **涵蓋**：台灣各大學碩士、博士論文（中英文）
- **費用**：完全免費（爬蟲方式存取）
- **注意**：網站若有維護或改版可能暫時無法取得結果，系統會自動跳過並顯示警告

### Google Scholar

- **涵蓋**：跨學科學術論文、書籍、技術報告，涵蓋中英文
- **費用**：免費（透過 `scholarly` 套件模擬瀏覽器存取）
- **注意**：Google 有速率限制，搜尋過於頻繁時會暫時被封鎖；遇到此情況請稍等幾分鐘後再試，或取消勾選此來源

### Springer（期刊 + 書籍）

- **涵蓋**：Springer Nature 期刊文章（Journal Articles）與書籍章節（Book Chapters）
- **費用**：免費（無 API Key 時透過 CrossRef 過濾 Springer DOI 前綴 `10.1007`）
- **API Key（選填）**：可於 https://dev.springernature.com/ 免費申請，填入後直接查 Springer Metadata API，結果更完整
- **結果標籤**：各論文來源欄位會標示 `Springer Journal` 或 `Springer Book`

---

## ⚠️ 風險等級說明

| 等級 | 綜合相似度 | 建議處理方式 |
|------|-----------|--------------|
| 🔴 高風險 | ≥ 60% | 立即檢視，確認是否有大量文字重疊或核心貢獻相同 |
| 🟡 中風險 | 35% – 59% | 仔細閱讀比對論文，確認是否為合理的相關工作引用 |
| 🟢 低風險 | < 35% | 主題相關但相似度低，通常無需擔心 |

> **重要提醒**：相似度高不一定代表抄襲（例如相關工作引述屬正常）；相似度低也不代表完全原創。本工具為輔助工具，最終判斷仍需人工審核。建議搭配 **iThenticate** 或 **Turnitin** 做最終確認。

---

## 🧩 技術架構

```
使用者上傳 PDF/DOCX
        ↓
   ┌──────────────────────────────────────────────────────┐
   │  三層 PDF 結構解析（自動降級）                          │
   │  ① GROBID API（ML，辨識所有主流會議/期刊格式）          │
   │     → 回傳 TEI XML，精確擷取標題/作者/摘要/正文          │
   │  ② pdfplumber 字型大小分析（GROBID 失敗時）             │
   │     → 偵測兩欄版型並分欄萃取；修復斷字接續               │
   │     → 最大字體（排除 Drop Cap）= 標題；排除頁首 header   │
   │  ③ 正規表示式啟發法（DOCX 或前兩層失敗時）               │
   │     → 偵測 IEEE inline "Abstract—" 等格式              │
   └──────────────────────────────────────────────────────┘
        ↓
   結構資料（題目 / 摘要 / 關鍵字 / 正文）
        ↓
   建構搜尋查詢字串
        ↓
   ┌────────────────────────────────────────────────────┐
   │  搜尋學術資料庫（6 個來源）                          │
   │  Semantic Scholar / arXiv / CrossRef               │
   │  台灣碩博士論文網 / Google Scholar / Springer       │
   └────────────────────────────────────────────────────┘
        ↓
   ┌────────────────────────────────────────────────────┐
   │  三層相似度分析（每篇候選論文）                      │
   │  ① TF-IDF 餘弦相似度（scikit-learn）× 45%          │
   │  ② Winnowing N-gram 指紋比對 × 35%                  │
   │     - 字元 8-gram + 詞 3-gram                       │
   │     - 段落切分 → 逐段找最佳配對片段                  │
   │  ③ 關鍵字重疊率 × 20%                               │
   └────────────────────────────────────────────────────┘
        ↓
   結果排序 + 風險分級（高/中/低）
        ↓
   顯示報告（段落比對色塊）/ 匯出 CSV
```

---

## 🔧 進階設定

### PDF 解析層說明

| 解析層 | 使用時機 | 優點 |
|--------|---------|------|
| 🤖 GROBID | 預設（PDF 上傳時自動呼叫） | 支援所有主流格式（IEEE / ACM / Springer / Nature / arXiv 等），不需手動設定 |
| 📐 字型大小 + 版型分析 | GROBID 逾時或失敗 | 純本機執行；以 x0-start 帶狀密度偵測欄間距；用 `within_bbox` 分欄萃取左右欄；利用跨槽字詞偵測自動分離全版標題區（標題／作者）與雙欄內文；加 9 pt 邊緣補正防止欄邊字元被截斷；依字體大小跳過 Drop Cap 與頁首 |
| 🔤 Regex | DOCX 或前兩層均失敗 | 處理 IEEE inline `Abstract—` 等常見格式，搭配作者行偵測避免誤判 |

**已驗證的雙欄格式**：IEEE Transactions（雙欄、摘要在欄中）、ACM SIGCONF 風格論文（聯邦學習）——兩者均能正確分欄萃取，不再有文字交錯或詞語合併問題。

> **GROBID 延遲說明**：使用 Hugging Face 公開空間，冷啟動時首次呼叫約需 10–30 秒；後續請求通常在 3–5 秒內完成。如需更快速度，可自行架設 GROBID Docker 並修改 `document_parser.py` 的 `_GROBID_URL`。

### 取得 Semantic Scholar API Key

1. 前往 https://www.semanticscholar.org/product/api
2. 點選「Get API Key」填寫申請表
3. 免費方案每秒 1 次請求，有 Key 可提升至每秒 10 次

### 取得 Springer Nature API Key

1. 前往 https://dev.springernature.com/ 免費註冊
2. 建立 Application 並取得 API Key
3. 填入側邊欄「Springer Nature API Key」欄位即可直接查詢 Springer Metadata API
4. 未填 Key 時系統自動 fallback 至 CrossRef（仍可取得結果，但資料量略少）

### 自訂風險門檻

在 `src/similarity.py` 修改 `risk_tier` 屬性中的數值：

```python
@property
def risk_tier(self) -> str:
    if self.combined_score >= 60:   # 修改此值
        return "high"
    if self.combined_score >= 35:   # 修改此值
        return "medium"
    return "low"
```

### 調整 N-gram 指紋敏感度

在 `src/fingerprint.py` 最上方修改參數：

```python
CHAR_K   = 8    # 字元 k-gram 長度（越小越敏感，容易誤報；越大越精確）
WORD_K   = 3    # 詞 n-gram 長度（3 = 抓 3 個連續詞的配對）
WIN_SIZE = 4    # Winnowing 視窗大小
```

建議值：
- 短論文 / 摘要比對：`CHAR_K=6, WORD_K=3`
- 全文精確比對：`CHAR_K=12, WORD_K=5`

### 切換介面語言

啟動工具後，頁面最上方有語言選單，點選即可切換：

| 選項 | 語言 |
|------|------|
| 繁體中文 | 中文介面（預設） |
| English | 英文介面 |
| 日本語 | 日文介面 |

切換後所有介面文字（側邊欄、按鈕、結果標籤、下載報告欄位名稱）均即時更新，無需重新整理頁面。

---

## 📋 系統需求

| 項目 | 需求 |
|------|------|
| Python | 3.11+ |
| 記憶體 | 建議 4GB+ |
| 網路 | 需連線至學術 API |
| 作業系統 | Windows / macOS / Linux |

---

## 📦 使用套件

| 套件 | 用途 |
|------|------|
| streamlit | Web UI 框架 |
| pdfplumber | PDF 文字擷取 |
| python-docx | Word 文件解析 |
| scikit-learn | TF-IDF 相似度計算 |
| requests | HTTP API 呼叫（含 Springer / CrossRef） |
| pandas | 資料整理與 CSV 匯出 |
| jieba | 中文斷詞（備用） |
| beautifulsoup4 + lxml | NDLTD 碩博士論文網 HTML 解析 |
| scholarly | Google Scholar 搜尋 |
