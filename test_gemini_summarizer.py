"""Geminiによる論文要約機能のテスト"""

import pytest
from unittest.mock import Mock, patch, mock_open
import os
from datetime import datetime


class TestGeminiSummarizer:
    """Geminiによる論文要約機能のテストクラス"""
    
    def test_summarize_papers_success(self):
        """論文要約成功のテスト"""
        # Arrange
        mock_html_input = "<html>論文リスト</html>"
        mock_system_prompt = "あなたは論文要約のエキスパートです..."
        expected_output = """### 1. Test Paper Title
- **著者**: Test Author
- **URL**: https://arxiv.org/abs/2509.03236
- **推薦理由**: テスト用の論文です
- **概要（3〜4 文で要約）**: テスト概要
- **応用のヒント**: テストヒント"""
        
        # Act & Assert
        with patch('google.genai.Client') as mock_client_class:
            with patch('config.get_gemini_api_key', return_value='test_api_key'):
                with patch('config.get_gemini_model_summary', return_value='gemini-2.0-flash-exp'):
                    mock_client = Mock()
                    mock_client_class.return_value = mock_client
                    
                    mock_response = Mock()
                    mock_response.text = expected_output
                    mock_client.models.generate_content.return_value = mock_response
                    
                    with patch('builtins.open', mock_open(read_data=mock_system_prompt)):
                        from gemini_summarizer import summarize_papers_with_gemini
                        result = summarize_papers_with_gemini(mock_html_input)
                        assert expected_output in result
    
    def test_load_system_prompt_file(self):
        """システムプロンプトファイル読み込みのテスト"""
        # Arrange
        expected_prompt_content = "テスト用システムプロンプト"
        
        # Act & Assert
        with patch('builtins.open', mock_open(read_data=expected_prompt_content)):
            from gemini_summarizer import load_system_prompt
            result = load_system_prompt('prompt/summary.md')
            assert result == expected_prompt_content
    
    def test_save_summary_to_file(self):
        """要約結果のファイル保存テスト"""
        # Arrange
        test_date = "20250906"
        test_summary = "テスト用要約内容"
        expected_file_path = f"data/{test_date}/abstract.md"
        
        # Act & Assert
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs') as mock_makedirs:
                from gemini_summarizer import save_summary_to_file
                save_summary_to_file(test_summary, test_date)
                
                # ディレクトリが作成されることを確認
                mock_makedirs.assert_called_once_with(f"data/{test_date}", exist_ok=True)
                # ファイルが適切なパスで開かれることを確認
                mock_file.assert_called_once_with(expected_file_path, 'w', encoding='utf-8')
    
    def test_gemini_api_error_handling(self):
        """Gemini API エラー処理のテスト"""
        # Arrange
        mock_html_input = "<html>テスト</html>"
        
        # Act & Assert
        with patch('google.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception("API Error")
            
            # 実装：API エラーが適切に処理されることをテスト
            with patch('config.get_gemini_api_key', return_value='test_api_key'):
                with patch('config.get_gemini_model_summary', return_value='gemini-2.0-flash-exp'):
                    from gemini_summarizer import summarize_papers_with_gemini
                    with pytest.raises(Exception):
                        summarize_papers_with_gemini(mock_html_input)
    
    def test_extract_paper_urls_from_summary(self):
        """要約結果から論文URLを抽出するテスト"""
        # Arrange
        mock_summary = """### 1. Test Paper 1
- **URL**: https://arxiv.org/abs/2509.03236

### 2. Test Paper 2  
- **URL**: https://arxiv.org/abs/2509.03237"""
        
        expected_urls = [
            "https://arxiv.org/abs/2509.03236",
            "https://arxiv.org/abs/2509.03237"
        ]
        
        # Act & Assert
        from gemini_summarizer import extract_paper_urls_from_summary
        result = extract_paper_urls_from_summary(mock_summary)
        assert set(result) == set(expected_urls)  # 順序を問わずに比較