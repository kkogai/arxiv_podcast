"""arxiv論文ポッドキャスト生成システム - メインエントリーポイント"""

import sys
import argparse
import os

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
from output_podcast import (
    find_podcast_scripts,
    load_podcast_script,
    create_output_directory,
    generate_audio_from_script,
)
from convert_wav_to_mp3 import (
    check_ffmpeg_available,
    find_wav_files,
    convert_wav_to_mp3,
    create_mp3_path,
    get_file_size_mb,
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


def generate_audio_and_convert_to_mp3(data_dir: str, bitrate: str = "192k", keep_wav: bool = False) -> bool:
    """
    ポッドキャスト音声生成とMP3変換を実行する
    
    Args:
        data_dir (str): データディレクトリのパス
        bitrate (str): MP3のビットレート
        keep_wav (bool): WAVファイルを保持するか
        
    Returns:
        bool: 処理が成功した場合True
    """
    try:
        # 8. 音声生成処理
        print("8. ポッドキャスト音声を生成中...")
        
        # 台本ファイルを検索
        script_files = find_podcast_scripts(data_dir)
        
        if not script_files:
            print("   台本ファイルが見つかりませんでした。音声生成をスキップします。")
            return False
        
        print(f"   対象台本ファイル: {len(script_files)}件")
        
        # 出力ディレクトリ作成
        output_dir = create_output_directory(data_dir)
        print(f"   音声ファイル出力先: {output_dir}")
        
        successful_audio_count = 0
        
        # 各台本ファイルを処理
        for file_path, arxiv_number in script_files:
            try:
                # 台本読み込み
                script = load_podcast_script(file_path)
                
                # 音声生成
                print(f"   {arxiv_number}: 音声生成中...")
                success = generate_audio_from_script(script, arxiv_number, output_dir)
                
                if success:
                    successful_audio_count += 1
                    print(f"   → {arxiv_number}: 音声生成完了")
                else:
                    print(f"   → {arxiv_number}: 音声生成失敗")
                    
            except Exception as e:
                print(f"   {arxiv_number}: 音声生成エラー ({str(e)})")
                continue
        
        print(f"   音声生成完了: {successful_audio_count}/{len(script_files)} ファイル")
        
        if successful_audio_count == 0:
            print("   音声ファイルが生成されませんでした。MP3変換をスキップします。")
            return False
        
        # 9. MP3変換処理
        print("9. WAVファイルをMP3に変換中...")
        
        # FFmpegの利用可能性チェック
        if not check_ffmpeg_available():
            print("   警告: FFmpegが見つかりません。MP3変換をスキップします。")
            print("   FFmpegをインストールしてください:")
            print("     macOS: brew install ffmpeg")
            print("     Ubuntu: apt install ffmpeg")
            return True  # 音声生成は成功したのでTrueを返す
        
        # WAVファイルを検索
        wav_files = find_wav_files(output_dir)
        
        if not wav_files:
            print("   WAVファイルが見つかりませんでした。")
            return True
        
        print(f"   対象WAVファイル: {len(wav_files)}件")
        print(f"   ビットレート: {bitrate}")
        
        # 変換実行
        successful_mp3_count = 0
        total_wav_size = 0.0
        total_mp3_size = 0.0
        
        for wav_path in wav_files:
            mp3_path = create_mp3_path(wav_path)
            
            # ファイルサイズを記録（変換前）
            wav_size = get_file_size_mb(wav_path)
            total_wav_size += wav_size
            
            if convert_wav_to_mp3(wav_path, mp3_path, bitrate):
                successful_mp3_count += 1
                
                # ファイルサイズを記録（変換後）
                mp3_size = get_file_size_mb(mp3_path)
                total_mp3_size += mp3_size
                
                print(f"   → {os.path.basename(wav_path)}: MP3変換完了")
                
                # 元のWAVファイルを削除（keep_wavが指定されていない場合）
                if not keep_wav:
                    try:
                        os.remove(wav_path)
                        print(f"   → WAVファイルを削除: {os.path.basename(wav_path)}")
                    except OSError as e:
                        print(f"   → WAVファイル削除エラー: {e}")
            else:
                print(f"   → {os.path.basename(wav_path)}: MP3変換失敗")
        
        print(f"   MP3変換完了: {successful_mp3_count}/{len(wav_files)} ファイル")
        
        if successful_mp3_count > 0:
            compression_ratio = (1 - total_mp3_size / total_wav_size) * 100 if total_wav_size > 0 else 0
            print(f"   ファイルサイズ: {total_wav_size:.1f}MB → {total_mp3_size:.1f}MB")
            print(f"   圧縮率: {compression_ratio:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"音声生成・MP3変換エラー: {str(e)}")
        return False


def main() -> None:
    """メイン処理フロー"""
    parser = argparse.ArgumentParser(
        description="ArXiv論文ポッドキャスト生成システム（台本生成→音声生成→MP3変換まで一括実行）"
    )
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="音声生成とMP3変換をスキップして台本生成のみ実行"
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="MP3ビットレート（デフォルト: 192k）"
    )
    parser.add_argument(
        "--keep-wav",
        action="store_true",
        help="MP3変換後もWAVファイルを保持する"
    )
    
    args = parser.parse_args()
    
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
        
        print(f"   台本生成完了: {generated_count}件")
        
        if generated_count == 0:
            print("ポッドキャスト台本が生成されませんでした。処理を終了します。")
            return
        
        # 8-9. 音声生成・MP3変換処理（オプション）
        if not args.skip_audio:
            data_dir_path = f"data/{current_date}"
            audio_success = generate_audio_and_convert_to_mp3(
                data_dir_path, 
                args.bitrate, 
                args.keep_wav
            )
            
            if not audio_success:
                print("音声生成処理でエラーが発生しましたが、台本生成は完了しています。")
        
        # 完了メッセージ
        print("\n=== 処理完了 ===")
        print("生成されたファイル:")
        print(f"  - data/{current_date}/abstract.md (論文要約)")
        print(f"  - {generated_count}件のポッドキャスト台本")
        
        if not args.skip_audio:
            print(f"  - 音声ファイル (data/{current_date}/audio/)")
            if not args.keep_wav:
                print("  - MP3ファイル (WAVファイルは削除されました)")
            else:
                print("  - WAVおよびMP3ファイル")
        else:
            print("\n音声生成を実行するには:")
            print("  uv run python main.py (または)")
            print(f"  uv run python output_podcast.py data/{current_date}/")
            print(f"  uv run python convert_wav_to_mp3.py data/{current_date}/")
        
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