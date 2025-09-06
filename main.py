"""arxiv論文ポッドキャスト生成システム - メインエントリーポイント"""

import sys

from arxiv_scraper import fetch_arxiv_new_papers, parse_paper_urls_from_html
from config import get_all_gemini_models, validate_environment
from file_manager import (
    create_date_directory,
    ensure_data_directory_exists,
    get_current_date_string,
)
from gemini_summarizer import (
    extract_paper_urls_from_summary,
    save_summary_to_file,
    summarize_papers_with_gemini,
)
from paper_fetcher import (
    convert_multiple_abs_urls_to_html_urls,
    extract_arxiv_number_from_url,
    fetch_multiple_papers_html,
)
from podcast_generator import (
    generate_podcast_script,
    save_podcast_script,
    validate_podcast_script_format,
)


def check_environment() -> bool:
    """
    必要な環境変数が設定されているかチェックする
    
    Returns:
        bool: 環境が正しく設定されている場合True
    """
    if not validate_environment():
        print("エラー: GEMINI_API_KEY環境変数が設定されていません")
        print(".envファイルを作成するか、環境変数を設定してください:")
        print("export GEMINI_API_KEY='your_api_key'")
        return False
    
    # 使用するモデル情報を表示
    models = get_all_gemini_models()
    print(f"使用モデル - 要約: {models['summary_model']}, ポッドキャスト: {models['podcast_model']}")
    
    return True


def main() -> None:
    """メイン処理フロー"""
    try:
        print("=== arxiv論文ポッドキャスト生成システム ===")
        
        # 1. 環境チェック
        print("1. 環境設定をチェック中...")
        if not check_environment():
            sys.exit(1)
        
        # 2. ディレクトリ準備
        print("2. ディレクトリを準備中...")
        ensure_data_directory_exists()
        current_date = get_current_date_string()
        create_date_directory(current_date)
        print(f"   作業ディレクトリ: data/{current_date}")
        
        # 3. arxiv新着論文リスト取得
        print("3. arxiv新着論文リストを取得中...")
        html_content = fetch_arxiv_new_papers()
        paper_urls = parse_paper_urls_from_html(html_content)
        print(f"   {len(paper_urls)}件の論文を発見")
        
        # 4. Geminiで論文要約
        print("4. Geminiで論文を要約中...")
        summary = summarize_papers_with_gemini(html_content)
        save_summary_to_file(summary, current_date)
        print(f"   要約を data/{current_date}/abstract.md に保存")
        
        # 5. 要約から重要な論文URLを抽出
        print("5. 重要論文を特定中...")
        important_paper_urls = extract_paper_urls_from_summary(summary)
        print(f"   {len(important_paper_urls)}件の重要論文を特定")
        
        if not important_paper_urls:
            print("重要な論文が見つかりませんでした。処理を終了します。")
            return
        
        # 6. 個別論文HTML取得
        print("6. 個別論文のHTML取得中...")
        html_urls = convert_multiple_abs_urls_to_html_urls(important_paper_urls)
        paper_htmls = fetch_multiple_papers_html(html_urls)
        
        # 7. 各論文のポッドキャスト台本生成
        print("7. ポッドキャスト台本を生成中...")
        generated_count = 0
        
        for i, (url, paper_html) in enumerate(zip(important_paper_urls, paper_htmls)):
            if not paper_html:  # HTMLが取得できなかった場合はスキップ
                print(f"   論文 {i+1}: HTML取得に失敗、スキップ")
                continue
                
            try:
                arxiv_number = extract_arxiv_number_from_url(url)
                print(f"   論文 {i+1} (arxiv:{arxiv_number}): 台本生成中...")
                
                script = generate_podcast_script(paper_html, arxiv_number)
                
                # フォーマット検証
                if validate_podcast_script_format(script):
                    save_podcast_script(script, arxiv_number, current_date)
                    print(f"   → data/{current_date}/{arxiv_number}.md に保存完了")
                    generated_count += 1
                else:
                    print("   → 台本フォーマットが不正、スキップ")
                    
            except Exception as e:
                print(f"   論文 {i+1}: エラーが発生、スキップ ({str(e)})")
                continue
        
        # 8. 完了メッセージ
        print("\n=== 処理完了 ===")
        print("生成されたファイル:")
        print(f"  - data/{current_date}/abstract.md (論文要約)")
        print(f"  - {generated_count}件のポッドキャスト台本")
        print("\n次に output_podcast.py を使用してポッドキャストを生成してください。")
        
    except KeyboardInterrupt:
        print("\n処理が中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()