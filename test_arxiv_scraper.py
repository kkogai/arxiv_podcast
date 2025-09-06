"""arxiv新着論文取得機能のテスト"""

import pytest
from unittest.mock import Mock, patch
import requests
from datetime import datetime


class TestArxivScraper:
    """arxiv新着論文取得機能のテストクラス"""
    
    def test_fetch_new_papers_success(self):
        """新着論文リスト取得成功のテスト"""
        # Arrange - 期待する入力と出力を定義
        expected_url = "https://arxiv.org/list/cs.IR/new"
        mock_html_content = """
        <html>
            <div class="list-title">
                <a href="/abs/2509.03236">Test Paper Title 1</a>
            </div>
            <div class="list-title">
                <a href="/abs/2509.03237">Test Paper Title 2</a>
            </div>
        </html>
        """
        
        # Act & Assert - 期待される動作を検証
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html_content
            mock_get.return_value = mock_response
            
            # 実装予定の関数をインポートして呼び出し
            from arxiv_scraper import fetch_arxiv_new_papers
            result = fetch_arxiv_new_papers()
            
            # 期待される結果を検証
            assert isinstance(result, str)
            assert len(result) > 0
            mock_get.assert_called_once_with(expected_url, timeout=30)
    
    def test_fetch_new_papers_network_error(self):
        """ネットワークエラー時のテスト"""
        # Arrange & Act & Assert
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network error")
            
            # 実装：例外が適切に処理されることをテスト
            from arxiv_scraper import fetch_arxiv_new_papers
            with pytest.raises(requests.ConnectionError):
                fetch_arxiv_new_papers()
    
    def test_fetch_new_papers_http_error(self):
        """HTTP エラー時のテスト"""
        # Arrange
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            # 実装：404エラーが適切に処理されることをテスト
            from arxiv_scraper import fetch_arxiv_new_papers
            with pytest.raises(requests.HTTPError):
                fetch_arxiv_new_papers()
    
    def test_parse_paper_urls_from_html(self):
        """HTML から論文URLを抽出するテスト"""
        # Arrange
        sample_html = """
        <div class="list-title">
            <a href="/abs/2509.03236">Paper 1</a>
        </div>
        <div class="list-title">
            <a href="/abs/2509.03237">Paper 2</a>
        </div>
        """
        
        expected_urls = [
            "https://arxiv.org/abs/2509.03236",
            "https://arxiv.org/abs/2509.03237"
        ]
        
        # Act & Assert
        from arxiv_scraper import parse_paper_urls_from_html
        result = parse_paper_urls_from_html(sample_html)
        assert result == expected_urls