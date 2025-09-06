"""個別論文HTML取得機能"""

import re
from typing import List

import requests


def convert_abs_url_to_html_url(abs_url: str) -> str:
    """
    arxiv abs URLをhtml URLに変換する
    
    Args:
        abs_url (str): abs形式のURL（例：https://arxiv.org/abs/2509.03236）
        
    Returns:
        str: html形式のURL（例：https://arxiv.org/html/2509.03236）
    """
    return abs_url.replace("/abs/", "/html/")


def convert_multiple_abs_urls_to_html_urls(abs_urls: List[str]) -> List[str]:
    """
    複数のabs URLを一括でhtml URLに変換する
    
    Args:
        abs_urls (List[str]): abs URLのリスト
        
    Returns:
        List[str]: html URLのリスト
    """
    return [convert_abs_url_to_html_url(url) for url in abs_urls]


def fetch_paper_html(html_url: str) -> str:
    """
    個別論文のHTMLを取得する
    
    Args:
        html_url (str): 論文のhtml URL
        
    Returns:
        str: 取得したHTML内容
        
    Raises:
        requests.ConnectionError: ネットワークエラー時
        requests.HTTPError: HTTP エラー時
    """
    try:
        response = requests.get(html_url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.ConnectionError:
        raise
    except requests.HTTPError:
        raise


def extract_arxiv_number_from_url(url: str) -> str:
    """
    URLからarxiv番号を抽出する
    
    Args:
        url (str): arxiv URL
        
    Returns:
        str: arxiv番号（例：2509.03236）
    """
    # URL からarxiv番号を抽出する正規表現パターン
    pattern = r'/(?:abs|html)/([0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else:
        raise ValueError(f"Invalid arxiv URL: {url}")


def fetch_multiple_papers_html(html_urls: List[str]) -> List[str]:
    """
    複数論文のHTMLを一括取得する
    
    Args:
        html_urls (List[str]): html URLのリスト
        
    Returns:
        List[str]: 取得したHTML内容のリスト
        
    Note:
        エラーが発生したURLについてはスキップされる
    """
    results = []
    
    for url in html_urls:
        try:
            html_content = fetch_paper_html(url)
            results.append(html_content)
        except (requests.ConnectionError, requests.HTTPError) as e:
            print(f"Error fetching {url}: {e}")
            # エラーが発生した場合は空文字列を追加
            results.append("")
    
    return results