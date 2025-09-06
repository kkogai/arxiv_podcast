"""WAVファイルをMP3に変換するスクリプト

生成されたポッドキャストWAVファイルをMP3形式に変換します。
FFmpegを使用して高品質な変換を行います。
"""

import argparse
import glob
import os
import subprocess
import sys
from typing import List


def check_ffmpeg_available() -> bool:
    """
    FFmpegが利用可能かチェックする
    
    Returns:
        bool: FFmpegが利用可能な場合True
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            capture_output=True, 
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def convert_wav_to_mp3(wav_path: str, mp3_path: str, bitrate: str = "192k") -> bool:
    """
    WAVファイルをMP3に変換する
    
    Args:
        wav_path (str): 入力WAVファイルのパス
        mp3_path (str): 出力MP3ファイルのパス  
        bitrate (str): MP3のビットレート（デフォルト: 192k）
        
    Returns:
        bool: 変換に成功した場合True
        
    Raises:
        FileNotFoundError: 入力ファイルが見つからない場合
        subprocess.CalledProcessError: FFmpeg実行に失敗した場合
    """
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAVファイルが見つかりません: {wav_path}")
    
    try:
        # FFmpegでWAVからMP3に変換
        command = [
            'ffmpeg',
            '-i', wav_path,          # 入力ファイル
            '-codec:a', 'libmp3lame', # MP3エンコーダー
            '-b:a', bitrate,         # ビットレート
            '-q:a', '2',             # 品質設定（高品質）
            '-y',                    # 出力ファイルを上書き
            mp3_path                 # 出力ファイル
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5分でタイムアウト
        )
        
        if result.returncode == 0:
            print(f"変換完了: {os.path.basename(wav_path)} -> {os.path.basename(mp3_path)}")
            return True
        else:
            print(f"変換エラー: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"変換タイムアウト: {wav_path}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg実行エラー: {e}")
        return False


def find_wav_files(audio_dir: str) -> List[str]:
    """
    指定されたディレクトリからWAVファイルを検索する
    
    Args:
        audio_dir (str): オーディオディレクトリのパス
        
    Returns:
        List[str]: WAVファイルパスのリスト
        
    Raises:
        FileNotFoundError: ディレクトリが見つからない場合
    """
    if not os.path.exists(audio_dir):
        raise FileNotFoundError(f"オーディオディレクトリが見つかりません: {audio_dir}")
    
    if not os.path.isdir(audio_dir):
        raise NotADirectoryError(f"指定されたパスはディレクトリではありません: {audio_dir}")
    
    # podcast_*.wavファイルを検索
    pattern = os.path.join(audio_dir, "podcast_*.wav")
    wav_files = glob.glob(pattern)
    
    return sorted(wav_files)


def create_mp3_path(wav_path: str, output_dir: str = None) -> str:
    """
    WAVファイルパスからMP3ファイルパスを生成する
    
    Args:
        wav_path (str): WAVファイルのパス
        output_dir (str): 出力ディレクトリ（Noneの場合WAVと同じディレクトリ）
        
    Returns:
        str: MP3ファイルのパス
    """
    wav_dir = os.path.dirname(wav_path)
    wav_filename = os.path.basename(wav_path)
    
    # 拡張子を.mp3に変更
    mp3_filename = wav_filename.replace('.wav', '.mp3')
    
    # 出力ディレクトリが指定されている場合は使用、そうでなければWAVと同じディレクトリ
    target_dir = output_dir if output_dir else wav_dir
    
    return os.path.join(target_dir, mp3_filename)


def get_file_size_mb(file_path: str) -> float:
    """
    ファイルサイズをMB単位で取得する
    
    Args:
        file_path (str): ファイルパス
        
    Returns:
        float: ファイルサイズ（MB）
    """
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    return 0.0


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="ポッドキャストWAVファイルをMP3に変換"
    )
    parser.add_argument(
        "data_dir",
        help="WAVファイルが含まれるデータディレクトリ（例: data/20241206/）"
    )
    parser.add_argument(
        "--output-dir",
        help="MP3ファイルの出力ディレクトリ（デフォルト: data_dir/audio）"
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="MP3ビットレート（デフォルト: 192k）"
    )
    parser.add_argument(
        "--keep-wav",
        action="store_true",
        help="変換後もWAVファイルを保持する"
    )
    
    args = parser.parse_args()
    
    # データディレクトリの存在確認
    if not os.path.exists(args.data_dir):
        print(f"エラー: データディレクトリが見つかりません: {args.data_dir}")
        sys.exit(1)
    
    # オーディオディレクトリのパス
    audio_dir = os.path.join(args.data_dir, "audio")
    
    # FFmpegの利用可能性チェック
    if not check_ffmpeg_available():
        print("エラー: FFmpegが見つかりません")
        print("FFmpegをインストールしてください:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: apt install ffmpeg")
        print("  Windows: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    try:
        # WAVファイルを検索
        wav_files = find_wav_files(audio_dir)
        
        if not wav_files:
            print(f"WAVファイルが見つかりません: {audio_dir}")
            print("まず output_podcast.py を実行してWAVファイルを生成してください")
            sys.exit(1)
        
        print("=== WAV→MP3変換開始 ===")
        print(f"対象ファイル数: {len(wav_files)}")
        print(f"ビットレート: {args.bitrate}")
        
        # 出力ディレクトリ設定
        output_dir = args.output_dir if args.output_dir else None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            print(f"出力ディレクトリ: {output_dir}")
        
        # 変換実行
        success_count = 0
        total_wav_size = 0.0
        total_mp3_size = 0.0
        
        for wav_path in wav_files:
            mp3_path = create_mp3_path(wav_path, output_dir)
            
            # ファイルサイズを記録（変換前）
            wav_size = get_file_size_mb(wav_path)
            total_wav_size += wav_size
            
            if convert_wav_to_mp3(wav_path, mp3_path, args.bitrate):
                success_count += 1
                
                # ファイルサイズを記録（変換後）
                mp3_size = get_file_size_mb(mp3_path)
                total_mp3_size += mp3_size
                
                # 元のWAVファイルを削除（--keep-wavが指定されていない場合）
                if not args.keep_wav:
                    try:
                        os.remove(wav_path)
                        print(f"  WAVファイルを削除: {os.path.basename(wav_path)}")
                    except OSError as e:
                        print(f"  WAVファイル削除エラー: {e}")
        
        # 結果表示
        print("\n=== 変換完了 ===")
        print(f"成功: {success_count}/{len(wav_files)} ファイル")
        
        if success_count > 0:
            compression_ratio = (1 - total_mp3_size / total_wav_size) * 100 if total_wav_size > 0 else 0
            print(f"ファイルサイズ: {total_wav_size:.1f}MB → {total_mp3_size:.1f}MB")
            print(f"圧縮率: {compression_ratio:.1f}%")
        
    except KeyboardInterrupt:
        print("\n変換が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()