"""ディレクトリ構成とファイル保存機能"""

import os
import shutil
from datetime import datetime
from typing import Tuple


def create_date_directory(date_string: str) -> None:
    """
    指定した日付でディレクトリを作成する
    
    Args:
        date_string (str): 日付文字列（例: "20250906"）
    """
    dir_path = f"data/{date_string}"
    os.makedirs(dir_path, exist_ok=True)


def get_current_date_string() -> str:
    """
    現在日付の文字列を取得する
    
    Returns:
        str: YYYYMMDD形式の日付文字列
    """
    return datetime.now().strftime("%Y%m%d")


def ensure_data_directory_exists() -> None:
    """
    dataディレクトリの存在を確認し、なければ作成する
    """
    if not os.path.exists("data"):
        os.makedirs("data", exist_ok=True)


def generate_output_file_paths(date: str, arxiv_number: str) -> Tuple[str, str]:
    """
    出力ファイルのパスを生成する
    
    Args:
        date (str): 日付文字列
        arxiv_number (str): arxiv番号
        
    Returns:
        Tuple[str, str]: (abstract.mdのパス, ポッドキャスト台本のパス)
    """
    abstract_path = f"data/{date}/abstract.md"
    podcast_path = f"data/{date}/{arxiv_number}.md"
    
    return abstract_path, podcast_path


def save_content_to_file(content: str, file_path: str) -> None:
    """
    コンテンツをUTF-8エンコーディングでファイルに保存する
    
    Args:
        content (str): 保存する内容
        file_path (str): 保存先ファイルパス
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def validate_file_path_security(path: str) -> bool:
    """
    ファイルパスがセキュアかどうかを検証する
    
    Args:
        path (str): 検証するファイルパス
        
    Returns:
        bool: セキュアな場合True、そうでなければFalse
    """
    # パスの正規化
    normalized_path = os.path.normpath(path)
    
    # dataディレクトリ内のパスかどうかチェック
    if not normalized_path.startswith('data/'):
        return False
    
    # パストラバーサル攻撃の検出
    if '..' in normalized_path:
        return False
    
    # 絶対パスへの変換を試行してdataディレクトリ外に出ていないかチェック
    try:
        abs_path = os.path.abspath(normalized_path)
        data_dir = os.path.abspath('data')
        
        # data ディレクトリの下にあるかどうか
        return abs_path.startswith(data_dir)
    except Exception:
        return False


def cleanup_old_data_directories(keep_days: int = 7) -> None:
    """
    古いデータディレクトリをクリーンアップする
    
    Args:
        keep_days (int): 保持する日数（デフォルト: 7日）
    """
    if not os.path.exists("data"):
        return
    
    current_date = datetime.now()
    
    for item in os.listdir("data"):
        item_path = os.path.join("data", item)
        
        if not os.path.isdir(item_path):
            continue
        
        # ディレクトリ名が日付形式（YYYYMMDD）かチェック
        if len(item) == 8 and item.isdigit():
            try:
                dir_date = datetime.strptime(item, "%Y%m%d")
                days_diff = (current_date - dir_date).days
                
                if days_diff > keep_days:
                    shutil.rmtree(item_path)
                    
            except ValueError:
                # 日付形式でない場合はスキップ
                continue