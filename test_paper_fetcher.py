"""個別論文HTML取得機能のテスト"""

import pytest
from unittest.mock import Mock, patch
import requests


class TestPaperFetcher:
    """個別論文HTML取得機能のテストクラス"""
    
    def test_convert_abs_url_to_html_url(self):
        """arxiv abs URLをhtml URLに変換するテスト"""
        # Arrange
        abs_url = "https://arxiv.org/abs/2509.03236"
        expected_html_url = "https://arxiv.org/html/2509.03236"
        
        # Act & Assert
        from paper_fetcher import convert_abs_url_to_html_url
        result = convert_abs_url_to_html_url(abs_url)
        assert result == expected_html_url
    
    def test_convert_multiple_urls(self):
        """複数URLの一括変換テスト"""
        # Arrange
        abs_urls = [
            "https://arxiv.org/abs/2509.03236",
            "https://arxiv.org/abs/2509.03237",
            "https://arxiv.org/abs/2509.03238"
        ]
        expected_html_urls = [
            "https://arxiv.org/html/2509.03236",
            "https://arxiv.org/html/2509.03237", 
            "https://arxiv.org/html/2509.03238"
        ]
        
        # Act & Assert
        from paper_fetcher import convert_multiple_abs_urls_to_html_urls
        result = convert_multiple_abs_urls_to_html_urls(abs_urls)
        assert result == expected_html_urls
    
    def test_fetch_paper_html_success(self):
        """個別論文HTML取得成功のテスト"""
        # Arrange
        html_url = "https://arxiv.org/html/2509.03236"
        mock_html_content = """
        <html>
            <head><title>Test Paper</title></head>
            <body>
                <h1>Test Paper Title</h1>
                <div class="ltx_abstract">Abstract content here</div>
                <div class="ltx_para">Paper content here</div>
            </body>
        </html>
        """
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html_content
            mock_get.return_value = mock_response
            
            from paper_fetcher import fetch_paper_html
            result = fetch_paper_html(html_url)
            assert result == mock_html_content
            mock_get.assert_called_once_with(html_url, timeout=30)
    
    def test_fetch_paper_html_not_found(self):
        """論文HTMLが見つからない場合のテスト"""
        # Arrange
        html_url = "https://arxiv.org/html/9999.99999"
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            from paper_fetcher import fetch_paper_html
            with pytest.raises(requests.HTTPError):
                fetch_paper_html(html_url)
    
    def test_fetch_paper_html_network_error(self):
        """ネットワークエラー時のテスト"""
        # Arrange
        html_url = "https://arxiv.org/html/2509.03236"
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Network error")
            
            from paper_fetcher import fetch_paper_html
            with pytest.raises(requests.ConnectionError):
                fetch_paper_html(html_url)
    
    def test_extract_arxiv_number_from_url(self):
        """URLからarxiv番号を抽出するテスト"""
        # Arrange & Act & Assert
        test_cases = [
            ("https://arxiv.org/abs/2509.03236", "2509.03236"),
            ("https://arxiv.org/html/2509.03237", "2509.03237"),
            ("https://arxiv.org/abs/1234.56789v2", "1234.56789"),  # バージョン番号付き
        ]
        
        from paper_fetcher import extract_arxiv_number_from_url
        
        for url, expected_arxiv_number in test_cases:
            result = extract_arxiv_number_from_url(url)
            assert result == expected_arxiv_number
    
    def test_fetch_multiple_papers_batch(self):
        """複数論文の一括取得テスト"""
        # Arrange
        html_urls = [
            "https://arxiv.org/html/2509.03236",
            "https://arxiv.org/html/2509.03237"
        ]
        
        mock_html_responses = [
            "<html>Paper 1 content</html>",
            "<html>Paper 2 content</html>"
        ]
        
        # Act & Assert
        with patch('requests.get') as mock_get:
            mock_responses = []
            for content in mock_html_responses:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = content
                mock_responses.append(mock_response)
            
            mock_get.side_effect = mock_responses
            
            from paper_fetcher import fetch_multiple_papers_html
            result = fetch_multiple_papers_html(html_urls)
            assert len(result) == 2
            assert result[0] == mock_html_responses[0]
            assert result[1] == mock_html_responses[1]