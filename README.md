# ArXiv論文ポッドキャスト生成システム

ArXivの新着論文から自動でポッドキャスト台本を生成するTDD開発システム

## 🚀 使用方法

### 1. 環境設定

#### 方法A: .envファイルで設定（推奨）
```bash
# .envファイルをコピー
cp .env.example .env

# .envファイルを編集
vim .env
```

```env
# Gemini API設定
GEMINI_API_KEY=your_gemini_api_key_here

# Geminiモデル設定（フェーズ別）
GEMINI_MODEL_SUMMARY=gemini-2.0-flash-exp    # 論文要約用
GEMINI_MODEL_PODCAST=gemini-2.0-flash-exp    # ポッドキャスト生成用
```

#### 方法B: 環境変数で設定
```bash
export GEMINI_API_KEY='your_gemini_api_key'
export GEMINI_MODEL_SUMMARY='gemini-2.0-flash-exp'
export GEMINI_MODEL_PODCAST='gemini-2.0-flash-exp'
```

### 2. 依存関係インストール
```bash
uv sync
```

### 3. システム実行
```bash
uv run python main.py
```

### 4. 音声生成（システム完了後）
```bash
uv run python output_podcast.py data/20241206/
```

## 📁 システム構成

```
arxiv_podcast/
├── main.py                    # メインエントリーポイント
├── config.py                  # 環境設定管理
├── arxiv_scraper.py          # arxiv新着論文取得
├── gemini_summarizer.py      # Gemini論文要約
├── paper_fetcher.py          # 個別論文HTML取得
├── podcast_generator.py      # ポッドキャスト台本生成
├── file_manager.py           # ファイル管理
├── .env.example              # 環境変数設定サンプル
├── prompt/
│   ├── summary.md            # 論文要約プロンプト
│   └── podcast.md            # ポッドキャスト生成プロンプト
├── output_podcast.py         # 音声生成
├── data/yyyymmdd/            # 出力データ
│   ├── abstract.md           # 論文要約
│   └── [arxiv_number].md     # ポッドキャスト台本
└── test_*.py                 # テストファイル群（40テスト）
```

## 🔧 利用可能なモデル

以下のGeminiモデルを各フェーズで選択可能：

- `gemini-2.0-flash-exp` - 最新の高性能モデル（デフォルト）
- `gemini-1.5-pro` - プロ版モデル
- `gemini-1.5-flash` - 高速モデル

フェーズ別にモデルを設定することで、用途に応じて最適化できます：
- **論文要約**: 複雑な学術論文を理解できる高性能モデル
- **ポッドキャスト生成**: 自然な対話を生成できるモデル

## 🎯 システムフロー

1. **arxiv新着論文取得** - cs.IR/newから論文リスト取得
2. **Gemini論文要約** - 重要論文を要約・選定
3. **個別論文取得** - 選定論文のHTML取得
4. **ポッドキャスト台本生成** - 対話形式台本作成
5. **音声生成** - TTS対応フォーマットで音声化

## 🛠️ 開発情報

- **開発手法**: TDD（テスト駆動開発）
- **テスト数**: 40テストケース（100%成功）
- **言語**: Python 3.11+
- **主要依存**: google-genai, requests, beautifulsoup4, python-dotenv

## 📊 テスト実行

```bash
# 全テスト実行
uv run pytest -v

# 特定モジュールのテスト
uv run pytest test_config.py -v
```

## 🎙️ 実行例

```bash
# 1. 論文取得と台本生成
uv run python main.py

# 出力例:
# === arxiv論文ポッドキャスト生成システム ===
# 1. 環境設定をチェック中...
# 使用モデル - 要約: gemini-2.0-flash-exp, ポッドキャスト: gemini-2.0-flash-exp
# 2. ディレクトリを準備中...
# 作業ディレクトリ: data/20241206
# 3. arxiv新着論文リストを取得中...
# 15件の論文を発見
# 4. Geminiで論文を要約中...
# 要約を data/20241206/abstract.md に保存
# 5. 重要論文を特定中...
# 3件の重要論文を特定
# 6. 個別論文のHTML取得中...
# 7. ポッドキャスト台本を生成中...
# 論文 1 (arxiv:2409.12345): 台本生成中...
# → data/20241206/2409.12345.md に保存完了
# 論文 2 (arxiv:2409.12346): 台本生成中...
# → data/20241206/2409.12346.md に保存完了
# 
# === 処理完了 ===
# 生成されたファイル:
#   - data/20241206/abstract.md (論文要約)
#   - 2件のポッドキャスト台本
# 
# 次に output_podcast.py を使用してポッドキャストを生成してください。

# 2. 音声ファイル生成
uv run python output_podcast.py data/20241206/
```