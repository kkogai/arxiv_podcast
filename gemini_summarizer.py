"""Geminiによる論文要約機能"""

import os
import re
from typing import List

from google import genai
from google.genai import types
from config import get_gemini_api_key, get_gemini_model_summary


def load_system_prompt(file_path: str) -> str:
    """
    システムプロンプトファイルを読み込む
    
    Args:
        file_path (str): プロンプトファイルのパス
        
    Returns:
        str: システムプロンプトの内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def summarize_papers_with_gemini(html_input: str) -> str:
    """
    GeminiでarXiv論文リストを要約する
    
    Args:
        html_input (str): arxiv論文リストのHTML
        
    Returns:
        str: Geminiによる要約結果
        
    Raises:
        Exception: Gemini API呼び出し時のエラー
    """
    try:
        # Geminiクライアントの初期化
        client = genai.Client(
            api_key=get_gemini_api_key(),
        )
        
        # システムプロンプトを読み込み
        system_prompt = load_system_prompt('prompt/summary.md')
        
        # Geminiに送信するコンテンツを準備
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"{system_prompt}\n\n#入力論文リスト\n{html_input}"),
                ],
            ),
        ]
        
        # 生成設定
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
        )
        
        # Gemini APIを呼び出し（.envで指定されたモデルを使用）
        model_name = get_gemini_model_summary()
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )
        
        return response.text
        
    except Exception as e:
        # APIエラーを再発生させる
        raise e


def save_summary_to_file(summary: str, date: str) -> None:
    """
    要約結果をファイルに保存する
    
    Args:
        summary (str): 要約内容
        date (str): 日付文字列
    """
    # ディレクトリを作成
    os.makedirs(f"data/{date}", exist_ok=True)
    
    # ファイルに保存
    file_path = f"data/{date}/abstract.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(summary)


def extract_paper_urls_from_summary(summary: str) -> List[str]:
    """
    要約結果から論文URLを抽出する
    
    Args:
        summary (str): Geminiによる要約結果
        
    Returns:
        List[str]: 論文URLのリスト
    """
    # URLパターンを検索（https://arxiv.org/abs/...）
    url_pattern = r'https://arxiv\.org/abs/[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?'
    urls = re.findall(url_pattern, summary)
    
    # 重複を除去して返す
    return list(set(urls))