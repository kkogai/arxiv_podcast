"""arxiv新着論文取得機能"""

from typing import List

import requests
from bs4 import BeautifulSoup


def fetch_arxiv_new_papers() -> str:
    """
    arxivの新着論文一覧ページからHTMLを取得する
    
    Returns:
        str: 取得したHTML内容
        
    Raises:
        requests.ConnectionError: ネットワークエラー時
        requests.HTTPError: HTTP エラー時
    """
    url = "https://arxiv.org/list/cs.IR/new"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.ConnectionError:
        raise
    except requests.HTTPError:
        raise


def parse_paper_urls_from_html(html: str) -> List[str]:
    """
    HTMLから論文のabsページURLを抽出する
    
    Args:
        html (str): arxiv新着論文ページのHTML
        
    Returns:
        List[str]: 論文のabs URLのリスト
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # list-title クラスのdiv要素内のaタグを検索
    paper_urls = []
    
    for div in soup.find_all('div', class_='list-title'):
        a_tag = div.find('a')
        if a_tag and a_tag.get('href'):
            href = a_tag.get('href')
            # 相対URL（/abs/...）を絶対URLに変換
            if href.startswith('/abs/'):
                full_url = f"https://arxiv.org{href}"
                paper_urls.append(full_url)
    
    return paper_urls