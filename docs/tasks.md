# arxiv論文ポッドキャスト生成システム - タスクリスト

## 全体フロー
1. https://arxiv.org/list/cs.IR/new からHTMLをダウンロード
2. gemini-2.5-proにて、prompt/summary.mdをシステムプロンプトとして、1で取得したHTMLをユーザー入力として処理
3. その出力をdata/yyyymmdd/abstract.mdに保存
4. 3の内容にある論文のURLを https://arxiv.org/abs/2509.03236 から https://arxiv.org/html/2509.03236 に変換してHTMLをダウンロード
5. gemini-2.5-proにて、prompt/podcast.mdをシステムプロンプトとして、4の内容を入力
6. この出力結果をdata/yyyymmdd/[arxiv number].mdで保存
7. data/yyyymmdd/[arxiv number].mdをoutput_podcast.pyに入力しポッドキャストを作成

## 実装タスク（TDD順序）

### Phase 1: arxiv新着論文取得機能
- [ ] `fetch_arxiv_new_papers()` - arxivの新着論文一覧を取得
- [ ] `parse_paper_urls_from_html(html)` - HTMLから論文URLを抽出
- [ ] ネットワークエラー・HTTPエラー処理の実装

**テストファイル**: `test_arxiv_scraper.py`

### Phase 2: ファイル管理機能
- [ ] `create_date_directory(date_string)` - 日付ベースのディレクトリ作成
- [ ] `get_current_date_string()` - 現在日付の文字列取得
- [ ] `ensure_data_directory_exists()` - dataディレクトリの存在確認・作成
- [ ] `generate_output_file_paths(date, arxiv_number)` - 出力ファイルパス生成
- [ ] `save_content_to_file(content, file_path)` - UTF-8でファイル保存
- [ ] `validate_file_path_security(path)` - ファイルパスセキュリティ検証
- [ ] `cleanup_old_data_directories(keep_days)` - 古いデータのクリーンアップ

**テストファイル**: `test_file_manager.py`

### Phase 3: Gemini論文要約機能
- [ ] `load_system_prompt(file_path)` - システムプロンプトファイル読み込み
- [ ] `summarize_papers_with_gemini(html_input)` - Geminiで論文要約
- [ ] `save_summary_to_file(summary, date)` - 要約結果をファイル保存
- [ ] `extract_paper_urls_from_summary(summary)` - 要約結果から論文URL抽出
- [ ] Gemini APIエラー処理の実装

**テストファイル**: `test_gemini_summarizer.py`

### Phase 4: 個別論文HTML取得機能
- [ ] `convert_abs_url_to_html_url(abs_url)` - abs URLをhtml URLに変換
- [ ] `convert_multiple_abs_urls_to_html_urls(abs_urls)` - 複数URLの一括変換
- [ ] `fetch_paper_html(html_url)` - 個別論文HTML取得
- [ ] `extract_arxiv_number_from_url(url)` - URLからarxiv番号抽出
- [ ] `fetch_multiple_papers_html(html_urls)` - 複数論文の一括取得
- [ ] ネットワークエラー・404エラー処理の実装

**テストファイル**: `test_paper_fetcher.py`

### Phase 5: Geminiポッドキャスト台本生成機能
- [ ] `load_podcast_system_prompt()` - ポッドキャスト用システムプロンプト読み込み
- [ ] `generate_podcast_script(paper_html, arxiv_number)` - ポッドキャスト台本生成
- [ ] `save_podcast_script(script, arxiv_number, date)` - 台本をファイル保存
- [ ] `validate_podcast_script_format(script)` - 台本フォーマット検証
- [ ] `extract_key_sections_from_paper_html(html)` - 論文HTMLから重要セクション抽出
- [ ] Gemini APIエラー処理の実装

**テストファイル**: `test_podcast_generator.py`

### Phase 6: メイン統合処理
- [ ] `main()` - 全体の処理フローを統合
- [ ] コマンドライン引数処理
- [ ] 環境変数（GEMINI_API_KEY）の設定確認
- [ ] ログ出力の実装
- [ ] エラーハンドリングの統合

## 環境設定
- [x] プロジェクト初期化
- [x] 依存関係設定（pyproject.toml）
- [x] テストファイル作成（30テストケース）
- [ ] 環境変数設定ガイドの作成
- [ ] README.mdの更新

## 確認済みファイル
- `prompt/summary.md` - 論文要約用システムプロンプト
- `prompt/podcast.md` - ポッドキャスト生成用システムプロンプト
- `output_podcast.py` - 音声生成機能（既存）

## 想定ディレクトリ構造
```
arxiv_podcast/
├── data/
│   └── 20250906/
│       ├── abstract.md        # 論文要約結果
│       ├── 2509.03236.md      # ポッドキャスト台本1
│       └── 2509.03237.md      # ポッドキャスト台本2
├── prompt/
│   ├── summary.md             # 論文要約用プロンプト
│   └── podcast.md             # ポッドキャスト用プロンプト
├── test_*.py                  # テストファイル群
├── main.py                    # メインエントリーポイント
└── output_podcast.py          # 音声生成機能
```

## 開発メモ
- TDD（テスト駆動開発）でRed-Green-Refactorサイクルを適用
- 全30テストケースが実行可能
- Gemini 2.5 Proを使用
- UTF-8エンコーディングでファイル保存
- セキュリティを考慮したファイルパス検証
- エラーハンドリングの充実