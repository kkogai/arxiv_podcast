"""Geminiによるポッドキャスト台本生成機能"""

import os
import re

from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from config import get_gemini_api_key, get_gemini_model_podcast


def load_podcast_system_prompt() -> str:
    """
    ポッドキャスト用システムプロンプトファイルを読み込む
    
    Returns:
        str: ポッドキャスト用システムプロンプトの内容
    """
    with open('prompt/podcast.md', 'r', encoding='utf-8') as f:
        return f.read()


def extract_key_sections_from_paper_html(html: str) -> str:
    """
    論文HTMLから重要なセクション（abstract、introduction等）を抽出する
    
    Args:
        html (str): 論文のHTML
        
    Returns:
        str: 抽出された重要セクションのテキスト
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # 重要なセクションを抽出
    sections = []
    
    # タイトル
    title = soup.find('h1')
    if title:
        sections.append(f"Title: {title.get_text(strip=True)}")
    
    # Abstract
    abstract = soup.find(['div', 'section'], class_=re.compile(r'.*abstract.*', re.I))
    if abstract:
        sections.append(f"Abstract: {abstract.get_text(strip=True)}")
    
    # Introduction - テキスト内容にintroductionが含まれる要素を検索
    for element in soup.find_all(['div', 'section', 'h1', 'h2', 'h3']):
        element_text = element.get_text(strip=True)
        if re.search(r'introduction', element_text, re.I):
            # 親要素のセクション全体を取得
            parent_section = element.find_parent(['section', 'div'])
            if parent_section:
                sections.append(f"Introduction: {parent_section.get_text(strip=True)}")
            else:
                sections.append(f"Introduction: {element_text}")
            break
    
    # 他の重要なセクションがある場合は追加
    for section in soup.find_all(['section', 'div'], id=re.compile(r'S[0-9]+')):
        section_text = section.get_text(strip=True)
        if len(section_text) > 100:  # 短すぎるセクションは除外
            sections.append(section_text[:500] + "..." if len(section_text) > 500 else section_text)
    
    return "\n\n".join(sections)


def generate_podcast_script(paper_html: str, arxiv_number: str) -> str:
    """
    論文HTMLからポッドキャスト台本を生成する
    
    Args:
        paper_html (str): 論文のHTML
        arxiv_number (str): arxiv番号
        
    Returns:
        str: 生成されたポッドキャスト台本
        
    Raises:
        Exception: Gemini API呼び出し時のエラー
    """
    try:
        # Geminiクライアントの初期化
        client = genai.Client(
            api_key=get_gemini_api_key(),
        )
        
        # システムプロンプトを読み込み
        system_prompt = load_podcast_system_prompt()
        
        # 論文から重要セクションを抽出
        paper_content = extract_key_sections_from_paper_html(paper_html)
        
        # Geminiに送信するコンテンツを準備
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"{system_prompt}\n\n論文内容：\n{paper_content}"),
                ],
            ),
        ]
        
        # 生成設定
        generate_content_config = types.GenerateContentConfig(
            temperature=0.8,
        )
        
        # Gemini APIを呼び出し（.envで指定されたモデルを使用）
        model_name = get_gemini_model_podcast()
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )
        
        return response.text
        
    except Exception as e:
        # APIエラーを再発生させる
        raise e


def save_podcast_script(script: str, arxiv_number: str, date: str) -> None:
    """
    ポッドキャスト台本をファイルに保存する
    
    Args:
        script (str): ポッドキャスト台本
        arxiv_number (str): arxiv番号
        date (str): 日付文字列
    """
    # ディレクトリを作成
    os.makedirs(f"data/{date}", exist_ok=True)
    
    # ファイルに保存
    file_path = f"data/{date}/{arxiv_number}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(script)


def validate_podcast_script_format(script: str) -> bool:
    """
    生成されたポッドキャスト台本のフォーマットを検証する
    
    Args:
        script (str): ポッドキャスト台本
        
    Returns:
        bool: 正しいフォーマットの場合True
    """
    # 必須のヘッダーが含まれているかチェック
    if "Please read aloud the following in a podcast interview style:" not in script:
        return False
    
    # Speaker 1: と Speaker 2: の両方が含まれているかチェック
    if "Speaker 1:" not in script or "Speaker 2:" not in script:
        return False
    
    # 不適切なフォーマット（ホスト、ゲスト等）がないかチェック
    invalid_patterns = ["ホスト:", "ゲスト:", "Host:", "Guest:"]
    for pattern in invalid_patterns:
        if pattern in script:
            return False
    
    return True