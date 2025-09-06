# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## システム概要

ArXivの新着論文から自動でポッドキャスト台本を生成し、音声化するTDD開発システムです。Gemini AIを使用して論文要約、重要論文選定、ポッドキャスト台本生成、音声合成を行います。

## 開発コマンド

### 依存関係管理
```bash
# 依存関係インストール
uv sync

# 新しい依存関係追加
uv add <package_name>
```

### テスト実行
```bash
# 全テスト実行（推奨）
uv run pytest -v

# 特定テストファイル実行
uv run pytest test_config.py -v
uv run pytest test_arxiv_scraper.py -v

# 単一テスト実行
uv run pytest test_config.py::test_get_gemini_api_key -v
```

### システム実行

#### ローカル実行
```bash
# 全工程一括実行（台本→音声→MP3）
uv run python main.py

# 台本生成のみ
uv run python main.py --skip-audio

# 高品質MP3で生成
uv run python main.py --bitrate 320k --keep-wav

# 個別実行
uv run python output_podcast.py data/20241206/
uv run python convert_wav_to_mp3.py data/20241206/
```

#### Docker実行
```bash
# Docker Composeで台本生成のみ
docker-compose up arxiv-podcast

# Docker Composeで完全処理
docker-compose --profile full up arxiv-podcast-full

# 直接Docker実行（完全処理）
docker run --rm -v $(pwd)/data:/app/data -e GEMINI_API_KEY=your_key arxiv-podcast python main.py

# 台本生成のみ
docker run --rm -v $(pwd)/data:/app/data -e GEMINI_API_KEY=your_key arxiv-podcast
```

### 環境設定
```bash
# 環境変数設定用ファイルコピー
cp .env.example .env
# その後 .env ファイルを編集してGEMINI_API_KEYを設定
```

## アーキテクチャ

### モジュール構成

- **main.py**: システム全体のメインフロー制御
- **config.py**: 環境変数とGeminiモデル設定管理（4種類のモデル設定）
- **arxiv_scraper.py**: ArXiv新着論文リスト取得
- **gemini_summarizer.py**: Gemini APIによる論文要約と重要論文抽出
- **paper_fetcher.py**: 個別論文HTML取得
- **podcast_generator.py**: ポッドキャスト台本生成
- **file_manager.py**: ファイル・ディレクトリ管理
- **output_podcast.py**: Gemini TTSによる音声生成

### データフロー

1. ArXiv新着論文リスト取得 → HTML解析
2. Gemini要約 → 重要論文選定（abstract.md生成）
3. 個別論文HTML取得 → ポッドキャスト台本生成（.mdファイル生成）
4. TTS音声生成 → WAVファイル出力

### 設定可能なGeminiモデル

- `GEMINI_MODEL_SUMMARY`: 論文要約用（デフォルト: gemini-2.0-flash-exp）
- `GEMINI_MODEL_PODCAST`: ポッドキャスト生成用（デフォルト: gemini-2.0-flash-exp）  
- `GEMINI_MODEL_TTS`: 音声合成用（デフォルト: gemini-2.5-flash-preview-tts）

### プロンプト管理

- **prompt/summary.md**: 論文要約用プロンプトテンプレート
- **prompt/podcast.md**: ポッドキャスト台本生成用プロンプトテンプレート

### 出力構造

```
data/yyyymmdd/
├── abstract.md           # 論文要約と重要論文リスト
└── [arxiv_number].md     # 各論文のポッドキャスト台本
```

## テスト設計

TDD（テスト駆動開発）で開発されており、全7テストファイルで40のテストケースが実装されています。各モジュールに対応するテストファイルが存在し、入出力、エラーハンドリング、外部API連携などを網羅的にテストしています。

## 重要な実装ポイント

- **エラーハンドリング**: 各段階で適切なエラー処理とログ出力
- **モジュラー設計**: 各機能が独立したモジュールとして分離
- **設定の柔軟性**: フェーズ別のGeminiモデル選択が可能
- **ファイル管理**: 日付別ディレクトリでの組織的なファイル管理