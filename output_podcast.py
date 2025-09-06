"""ポッドキャスト音声生成システム

生成されたポッドキャスト台本から音声ファイルを作成します。
Gemini TTS（Text-to-Speech）を使用して多話者対応の音声を生成。
"""

import argparse
import glob
import mimetypes
import os
import struct
import sys
from typing import List, Tuple

from google import genai
from google.genai import types
from config import get_gemini_api_key, get_gemini_model_tts


def save_binary_file(file_name: str, data: bytes) -> None:
    """
    バイナリファイルを保存する
    
    Args:
        file_name (str): 保存するファイル名
        data (bytes): 保存するバイナリデータ
    """
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"音声ファイルを保存しました: {file_name}")


def load_podcast_script(file_path: str) -> str:
    """
    ポッドキャスト台本ファイルを読み込む
    
    Args:
        file_path (str): 台本ファイルのパス
        
    Returns:
        str: 台本の内容
        
    Raises:
        FileNotFoundError: ファイルが見つからない場合
        UnicodeDecodeError: ファイルの読み込みに失敗した場合
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"台本ファイルが見つかりません: {file_path}")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"ファイルの読み込みに失敗しました: {file_path}")


def validate_script_format(script: str) -> bool:
    """
    台本がTTS用の正しいフォーマットかチェックする
    
    Args:
        script (str): 台本内容
        
    Returns:
        bool: 正しいフォーマットの場合True
    """
    if "Please read aloud the following in a podcast interview style:" not in script:
        return False
    
    if "Speaker 1:" not in script or "Speaker 2:" not in script:
        return False
        
    return True


def generate_audio_from_script(script: str, output_filename: str, output_dir: str = None) -> bool:
    """
    台本から音声ファイルを生成する
    
    Args:
        script (str): ポッドキャスト台本
        output_filename (str): 出力ファイル名（拡張子なし）
        output_dir (str, optional): 出力ディレクトリ（指定しない場合は現在のディレクトリ）
        
    Returns:
        bool: 成功した場合True
    """
    try:
        # Geminiクライアントの初期化
        client = genai.Client(
            api_key=get_gemini_api_key(),
        )

        # TTS用設定
        model = get_gemini_model_tts()
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=script),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.8,
            response_modalities=[
                "audio",
            ],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker="Speaker 1",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name="Zephyr"  # 男性の声
                                )
                            ),
                        ),
                        types.SpeakerVoiceConfig(
                            speaker="Speaker 2",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name="Puck"  # 別の男性の声
                                )
                            ),
                        ),
                    ]
                ),
            ),
        )

        print(f"音声生成中: {output_filename}")
        file_index = 0
        
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
                
            if (chunk.candidates[0].content.parts[0].inline_data and 
                chunk.candidates[0].content.parts[0].inline_data.data):
                
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                
                if file_extension is None:
                    file_extension = ".wav"
                    data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
                
                if output_dir:
                    final_filename = os.path.join(output_dir, f"{output_filename}_{file_index:03d}{file_extension}")
                else:
                    final_filename = f"{output_filename}_{file_index:03d}{file_extension}"
                save_binary_file(final_filename, data_buffer)
                file_index += 1
            else:
                # テキスト出力がある場合は表示（デバッグ用）
                if hasattr(chunk, 'text') and chunk.text:
                    print(f"[デバッグ] {chunk.text}")
        
        return file_index > 0
        
    except Exception as e:
        print(f"音声生成エラー: {str(e)}")
        return False


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """
    オーディオデータをWAVファイル形式に変換する
    
    Args:
        audio_data (bytes): 元のオーディオデータ
        mime_type (str): MIMEタイプ
        
    Returns:
        bytes: WAVフォーマットのデータ
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data


def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    """
    オーディオMIMEタイプからパラメータを解析する
    
    Args:
        mime_type (str): オーディオMIMEタイプ文字列
        
    Returns:
        dict[str, int]: bits_per_sampleとrateを含む辞書
    """
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def find_podcast_scripts(data_dir: str) -> List[Tuple[str, str]]:
    """
    指定されたディレクトリからポッドキャスト台本ファイルを検索する
    
    Args:
        data_dir (str): データディレクトリのパス
        
    Returns:
        List[Tuple[str, str]]: (ファイルパス, arxiv番号)のリスト
    """
    script_files = []
    
    # .mdファイルを検索（abstract.md以外）
    pattern = os.path.join(data_dir, "*.md")
    for file_path in glob.glob(pattern):
        filename = os.path.basename(file_path)
        if filename != "abstract.md":
            # ファイル名からarxiv番号を抽出
            arxiv_number = filename.replace('.md', '')
            script_files.append((file_path, arxiv_number))
    
    return sorted(script_files)  # ソートして順序を安定させる


def create_output_directory(data_dir: str) -> str:
    """
    音声ファイル用の出力ディレクトリを作成する
    
    Args:
        data_dir (str): データディレクトリのパス
        
    Returns:
        str: 出力ディレクトリのパス
    """
    output_dir = os.path.join(data_dir, "audio")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="ポッドキャスト台本から音声ファイルを生成"
    )
    parser.add_argument(
        "data_dir",
        help="台本ファイルが含まれるデータディレクトリ（例: data/20241206/）"
    )
    parser.add_argument(
        "--output-dir",
        help="音声ファイルの出力ディレクトリ（デフォルト: data_dir/audio）"
    )
    
    args = parser.parse_args()
    
    # データディレクトリの存在確認
    if not os.path.exists(args.data_dir):
        print(f"エラー: データディレクトリが見つかりません: {args.data_dir}")
        sys.exit(1)
    
    # 台本ファイルを検索
    print(f"台本ファイルを検索中: {args.data_dir}")
    script_files = find_podcast_scripts(args.data_dir)
    
    if not script_files:
        print("台本ファイルが見つかりませんでした。")
        print("main.pyを実行してポッドキャスト台本を生成してください。")
        sys.exit(1)
    
    print(f"見つかった台本ファイル: {len(script_files)}件")
    
    # 出力ディレクトリ作成
    output_dir = args.output_dir or create_output_directory(args.data_dir)
    print(f"音声ファイル出力先: {output_dir}")
    
    successful_count = 0
    failed_count = 0
    
    # 各台本ファイルを処理
    for file_path, arxiv_number in script_files:
        print(f"\n処理中: {arxiv_number}")
        
        try:
            # 台本読み込み
            script = load_podcast_script(file_path)
            
            # フォーマット検証
            if not validate_script_format(script):
                print(f"スキップ: 不正なフォーマット - {arxiv_number}")
                failed_count += 1
                continue
            
            # 音声生成
            output_filename = os.path.join(output_dir, f"podcast_{arxiv_number}")
            
            if generate_audio_from_script(script, output_filename):
                print(f"完了: {arxiv_number}")
                successful_count += 1
            else:
                print(f"失敗: {arxiv_number}")
                failed_count += 1
                
        except Exception as e:
            print(f"エラー: {arxiv_number} - {str(e)}")
            failed_count += 1
    
    # 結果表示
    print("\n=== 音声生成完了 ===")
    print(f"成功: {successful_count}件")
    print(f"失敗: {failed_count}件")
    print(f"出力ディレクトリ: {output_dir}")
    
    if successful_count > 0:
        print("\n生成された音声ファイルを確認してください。")
    elif failed_count > 0:
        print("\n全ての処理が失敗しました。GEMINI_API_KEYを確認してください。")


if __name__ == "__main__":
    main()