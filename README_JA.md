# 🔍 論文盗用検出ツール

> 🌐 **言語 / Language / 語言：**
> [繁體中文](README.md) ・ [English](README_EN.md) ・ [日本語](README_JA.md)

大学院生の論文執筆を支援するための学術類似度比較ツールです。PDF または Word 形式の論文をアップロードすると、複数の学術データベースを自動検索し、類似論文をリスクレベル別に報告します。

---

## ✨ 機能一覧

| 機能 | 説明 |
|------|------|
| 📄 スマートドキュメント解析 | PDF 3 層解析：GROBID ML → フォントサイズ解析 → Regex。主要な会議・学術誌フォーマット全対応 |
| 🔎 マルチソース検索 | Semantic Scholar、arXiv、CrossRef、台湾 NDLTD、Google Scholar、Springer |
| 📚 データベース範囲 | IEEE、ACM、Springer 学術誌・書籍、Elsevier、Nature、arXiv、台湾学位論文 — 2 億件以上 |
| 📊 類似度分析 | TF-IDF コサイン + N-gram フィンガープリント + キーワード重複（3 層） |
| 🔬 段落照合 | Winnowing アルゴリズムで段落単位の照合・並排表示 |
| 🎯 リスク分類 | 高（≥60%）・中（≥35%）・低（<35%） |
| 📈 リアルタイム進捗バー | 結果取得ごとにパーセンテージを更新 |
| 📥 レポート出力 | ワンクリックで CSV ダウンロード |
| 🌐 多言語 UI | 繁體中文 / English / 日本語 切替対応 |
| 🖱️ ワンクリック起動 | `start.bat` をダブルクリックで自動インストール＆ブラウザ起動 |

---

## 🏗️ プロジェクト構成

```
Plagiarism/
├── start.bat                     # ワンクリック起動（Windows）
├── app.py                        # Streamlit メインアプリ
├── requirements.txt              # Python 依存ライブラリ
├── .streamlit/
│   └── config.toml               # 統計・メール確認を無効化
├── src/
│   ├── i18n.py                   # 多言語翻訳辞書（繁中/英/日）
│   ├── document_parser.py        # PDF / DOCX テキスト抽出
│   ├── text_processor.py         # タイトル・要旨・キーワード抽出
│   ├── similarity.py             # 類似度スコア計算
│   ├── fingerprint.py            # Winnowing N-gram フィンガープリント
│   └── searchers/
│       ├── semantic_scholar.py   # Semantic Scholar API（IEEE/ACM 含む）
│       ├── arxiv_searcher.py     # arXiv Atom API
│       ├── crossref_searcher.py  # CrossRef REST API
│       ├── ndltd_searcher.py     # 台湾 NDLTD（スクレイピング）
│       ├── google_scholar.py     # Google Scholar（scholarly ライブラリ）
│       └── springer_searcher.py  # Springer 学術誌・書籍（API または CrossRef フォールバック）
└── README.md / README_EN.md / README_JA.md
```

---

## 🚀 クイックスタート

### 方法 1：ワンクリック起動（推奨・Windows）

`start.bat` をダブルクリックしてください。

- **初回起動時**：必要なパッケージを自動インストール（インターネット接続が必要、約 1〜3 分）
- **毎回の起動**：ブラウザが `http://localhost:8501` で自動的に開きます
- **停止方法**：コマンドプロンプトウィンドウを閉じてください

> **初回起動の注意**：`start.bat` は自動的に `~/.streamlit/credentials.toml` を作成し、Streamlit のメール購読確認をスキップします。メールの入力は不要です。

### 方法 2：手動起動

#### 1. 動作環境
- Python 3.11 以上
- pip

#### 2. パッケージのインストール
```bash
pip install -r requirements.txt
```

#### 3. 起動
```bash
streamlit run app.py
```
ブラウザが `http://localhost:8501` で開きます。

---

## 📖 使い方ガイド

### Step 1：論文のアップロード
「論文ファイルをアップロード」をクリックし、PDF または Word ファイルを選択します。

> ⚠️ **注意**：スキャン版 PDF（画像ベース）はテキストを抽出できません。先に OCR ツールで変換してください。

### Step 2：設定（サイドバー）

| 設定項目 | 説明 |
|----------|------|
| 検索ソース | 比較対象のデータベースを選択（デフォルト：全選択） |
| 取得件数 | 各ソースから取得する件数 |
| 類似度しきい値 | この値未満の結果を非表示（デフォルト：10%） |
| Semantic Scholar API キー | 入力するとレート制限が緩和（任意） |
| Springer Nature API キー | Springer API を直接利用可能に。なければ CrossRef にフォールバック（任意） |

### Step 3：比較開始
**🚀 比較開始** ボタンをクリックします。進捗バーは結果を取得するたびにリアルタイム更新され、現在の検索ソースと全体の進捗率が表示されます。

### Step 4：結果の確認

- **サマリー**：比較論文数、リスクレベル別の件数
- **論文一覧**：タイトル、著者、年、ソース、リンク、要旨、一致キーワード
- **類似度スコア**：
  - `総合スコア` = TF-IDF × 45% + N-gram フィンガープリント × 35% + キーワード重複 × 20%
  - `TF-IDF スコア`：単語頻度ベースの意味的類似度
  - `N-gram フィンガープリント`：Winnowing アルゴリズムによる正確なフレーズ検出（Turnitin と同様の原理）
  - `キーワード重複`：あなたのキーワードが候補論文に出現する割合
- **段落照合**：あなたの論文のどの段落が候補論文と一致するかを色分け表示
  - 🔴 濃い赤：高重複（≥15%）
  - 🟡 薄い黄色：中程度の重複（7〜15%）
  - 🟢 薄い緑：低重複（<7%）

### Step 5：レポートのダウンロード
**📥 CSV レポートをダウンロード** をクリックすると、段落照合の詳細を含む全結果のスプレッドシートが取得できます。

---

## 🌐 言語の切り替え方法

ページ最上部のドロップダウンメニューで言語を選択します：

| 選択肢 | 言語 |
|--------|------|
| 繁體中文 | 繁体字中国語（デフォルト） |
| English | 英語 |
| 日本語 | 日本語 |

切り替えると、サイドバー・ボタン・結果ラベル・CSV 列名など、すべての UI テキストがページを再読み込みせずに即時更新されます。

---

## 🔍 検索ソースの説明

### Semantic Scholar（推奨）
- **対象**：IEEE、ACM、Springer、Elsevier、Nature、arXiv など 2 億件以上
- **費用**：無料（API キーで制限緩和可能）
- **申請**：https://www.semanticscholar.org/product/api

### arXiv
- **対象**：CS・物理・数学・電気工学のプレプリント論文
- **費用**：完全無料、キー不要

### CrossRef
- **対象**：クロスパブリッシャー DOI データベース（学術誌・学会論文）
- **費用**：完全無料

### 台湾 NDLTD（修士・博士論文）
- **対象**：台湾の大学の修士・博士論文（中国語・英語）
- **費用**：無料（スクレイピング）
- **注意**：サイトのメンテナンス・改修時に一時的に取得できない場合があります

### Google Scholar
- **対象**：学際的な論文・書籍・技術報告書（日中英ほか）
- **費用**：無料（`scholarly` ライブラリ経由）
- **注意**：Google のレート制限によりブロックされる場合があります。数分待つか、このソースのチェックを外してください

### Springer（学術誌 + 書籍）
- **対象**：Springer Nature の学術誌論文（Journal Article）および書籍章（Book Chapter）
- **費用**：無料 — API キーなしの場合、Springer DOI プレフィックス `10.1007` で CrossRef にフォールバック
- **API キー（任意）**：https://dev.springernature.com/ で無料登録し、Springer Metadata API を直接利用すると結果がより充実
- **結果ラベル**：ソース欄に `Springer Journal` または `Springer Book` と表示

---

## ⚠️ リスクレベルの説明

| レベル | 総合スコア | 推奨対応 |
|--------|-----------|---------|
| 🔴 高リスク | ≥ 60% | 直ちに確認 — 大量のテキスト重複またはコア貢献の重複がないか確認 |
| 🟡 中リスク | 35%〜59% | 候補論文を精読し、正当な関連研究の引用でないか確認 |
| 🟢 低リスク | < 35% | 関連トピックだが重複が少ない — 通常は問題なし |

> **重要**：類似度が高くても盗用とは限りません（関連研究の引用は正常です）。低くても完全な独自性を保証するものではありません。本ツールは参考用です。最終的な提出前確認には **iThenticate** または **Turnitin** をご利用ください。

---

## 🧩 技術アーキテクチャ

```
ユーザーが PDF/DOCX をアップロード
        ↓
   ┌──────────────────────────────────────────────────────┐
   │  3 層 PDF 構造解析（自動フォールバック）                 │
   │  ① GROBID API（ML — 主要な全フォーマット対応）           │
   │     → TEI XML を返し、タイトル・要旨・本文を正確抽出      │
   │  ② pdfplumber フォントサイズ解析（GROBID 失敗時）        │
   │     → 2 段組を検出し各カラムを個別抽出；ハイフン修復     │
   │     → 最大フォント（ドロップキャップ除外）= タイトル     │
   │  ③ 正規表現（DOCX または上位 2 層が失敗した場合）         │
   │     → IEEE inline "Abstract—" 等の形式を検出            │
   └──────────────────────────────────────────────────────┘
        ↓
   構造化データ（タイトル / 要旨 / キーワード / 本文）
        ↓
   検索クエリの構築
        ↓
   ┌────────────────────────────────────────────────────┐
   │  6 つの学術データベースを検索                        │
   │  Semantic Scholar / arXiv / CrossRef               │
   │  台湾 NDLTD / Google Scholar / Springer            │
   └────────────────────────────────────────────────────┘
        ↓（取得ごとにリアルタイム進捗バー更新）
   ┌────────────────────────────────────────────────────┐
   │  3 層類似度分析（候補論文ごと）                       │
   │  ① TF-IDF コサイン類似度（scikit-learn）× 45%      │
   │  ② Winnowing N-gram フィンガープリント × 35%         │
   │     - 文字 8-gram + 単語 3-gram                     │
   │     - 段落分割 → 各段落の最適一致を検索               │
   │  ③ キーワード重複率 × 20%                            │
   └────────────────────────────────────────────────────┘
        ↓
   ソート + リスク分類（高 / 中 / 低）
        ↓
   レポート表示（段落照合ブロック）/ CSV エクスポート
```

---

## 🔧 詳細設定

### PDF 解析層の説明

| 解析層 | 使用タイミング | 利点 |
|--------|-------------|------|
| 🤖 GROBID | デフォルト（PDF アップロード時に自動呼び出し） | ML ベース。IEEE / ACM / Springer / Nature / arXiv など全主要フォーマットを設定不要で対応 |
| 📐 フォントサイズ＋レイアウト解析 | GROBID タイムアウト・失敗時 | ローカル実行。x0-start 帯状密度でカラム溝を検出し `within_bbox` で左右カラムを個別抽出；溝越えワード検出で全幅ヘッダー（タイトル／著者）と2段組本文を自動分離；9 pt エッジパディングでカラム端文字の切り捨てを防止；ドロップキャップとページヘッダーを除外 |
| 🔤 正規表現 | DOCX または上位 2 層が両方失敗した場合 | IEEE inline `Abstract—` 形式の検出と著者行アーティファクトの除外 |

**検証済み2段組フォーマット**：IEEE Transactions（2段組・摘要も段組内）、ACM SIGCONF スタイル論文（連合学習）——どちらも正しい段組順序で抽出でき、文字の混在や単語の結合は発生しません。

> **GROBID の遅延について**：Hugging Face の公開スペースを使用しています。コールドスタート時の初回呼び出しは 10〜30 秒かかることがあります。自前で Docker ホストする場合は `document_parser.py` の `_GROBID_URL` を変更してください。

### Semantic Scholar API キーの取得
1. https://www.semanticscholar.org/product/api にアクセス
2. "Get API Key" をクリックしてフォームを記入
3. 無料プラン：1 リクエスト/秒 → キーあり：10 リクエスト/秒

### Springer Nature API キーの取得
1. https://dev.springernature.com/ で無料ユーザー登録
2. アプリケーションを作成して API キーを取得
3. サイドバーの「Springer Nature API キー」欄に入力すると Springer Metadata API を直接利用可能
4. キーなしの場合は CrossRef に自動フォールバック（結果は取得できますが件数は若干少なくなります）

### リスクしきい値のカスタマイズ
`src/similarity.py` の `risk_level` プロパティを編集：
```python
@property
def risk_level(self) -> str:
    if self.combined_score >= 60:   # この値を変更
        return "高風險"
    if self.combined_score >= 35:   # この値を変更
        return "中風險"
    return "低風險"
```

### N-gram フィンガープリントの感度調整
`src/fingerprint.py` の先頭で設定：
```python
CHAR_K   = 8    # 文字 k-gram の長さ（小さいほど敏感だが誤検出が増える）
WORD_K   = 3    # 単語 n-gram の長さ（3 = 3 単語の連続を検出）
WIN_SIZE = 4    # Winnowing ウィンドウサイズ
```
推奨値：
- 短い要旨の比較：`CHAR_K=6, WORD_K=3`
- 全文の精密比較：`CHAR_K=12, WORD_K=5`

---

## 📋 動作環境

| 項目 | 要件 |
|------|------|
| Python | 3.11 以上 |
| メモリ | 4 GB 以上推奨 |
| ネットワーク | API 呼び出しに必要 |
| OS | Windows / macOS / Linux |

---

## 📦 使用ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| streamlit | Web UI フレームワーク |
| pdfplumber | PDF テキスト抽出 |
| python-docx | Word ドキュメント解析 |
| scikit-learn | TF-IDF 類似度計算 |
| requests | HTTP API 呼び出し（Springer / CrossRef 含む） |
| pandas | データ処理・CSV エクスポート |
| jieba | 中国語トークナイザー（フォールバック） |
| beautifulsoup4 + lxml | NDLTD HTML 解析 |
| scholarly | Google Scholar 検索 |
