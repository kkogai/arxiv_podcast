"""Geminiによるポッドキャスト台本生成機能のテスト"""

import pytest
from unittest.mock import Mock, patch, mock_open
import os


class TestPodcastGenerator:
    """Geminiによるポッドキャスト台本生成機能のテストクラス"""
    
    def test_generate_podcast_script_success(self):
        """ポッドキャスト台本生成成功のテスト"""
        # Arrange
        mock_paper_html = """
        <html>
            <h1>New Recommendation System</h1>
            <div class="ltx_abstract">This paper proposes a new recommendation algorithm...</div>
        </html>
        """
        
        expected_script = """Please read aloud the following in a podcast interview style:
Speaker 1: 今日は新しい推薦システムについて話しましょう。
Speaker 2: はい、この論文では従来の協調フィルタリングの課題を解決する新しいアプローチを提案しています。
Speaker 1: 具体的にどのような課題があったのでしょうか？
Speaker 2: 主にコールドスタート問題とスパース性の問題です..."""
        
        # Act & Assert
        with patch('google.genai.Client') as mock_client_class:
            with patch('config.get_gemini_api_key', return_value='test_api_key'):
                with patch('config.get_gemini_model_podcast', return_value='gemini-2.0-flash-exp'):
                    mock_client = Mock()
                    mock_client_class.return_value = mock_client
                    
                    mock_response = Mock()
                    mock_response.text = expected_script
                    mock_client.models.generate_content.return_value = mock_response
                    
                    with patch('builtins.open', mock_open(read_data="システムプロンプト")):
                        from podcast_generator import generate_podcast_script
                        result = generate_podcast_script(mock_paper_html, "2509.03236")
                        assert "Please read aloud the following in a podcast interview style:" in result
                        assert "Speaker 1:" in result
                        assert "Speaker 2:" in result
    
    def test_load_podcast_system_prompt(self):
        """ポッドキャスト用システムプロンプト読み込みのテスト"""
        # Arrange
        expected_prompt = """あなたは、大規模 C2C プラットフォーム（ヤフーオークション、ヤフーフリマ）の検索・推薦システムの改善を担当する、経験豊富なリサーチサイエンティスト兼ポッドキャストホストです。"""
        
        # Act & Assert
        with patch('builtins.open', mock_open(read_data=expected_prompt)):
            from podcast_generator import load_podcast_system_prompt
            result = load_podcast_system_prompt()
            assert "C2C プラットフォーム" in result
    
    def test_save_podcast_script_to_file(self):
        """ポッドキャスト台本のファイル保存テスト"""
        # Arrange
        test_date = "20250906"
        test_arxiv_number = "2509.03236"
        test_script = "Please read aloud the following...\nSpeaker 1: テスト\nSpeaker 2: レスポンス"
        expected_file_path = f"data/{test_date}/{test_arxiv_number}.md"
        
        # Act & Assert
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs') as mock_makedirs:
                from podcast_generator import save_podcast_script
                save_podcast_script(test_script, test_arxiv_number, test_date)
                
                # ディレクトリが作成されることを確認
                mock_makedirs.assert_called_once_with(f"data/{test_date}", exist_ok=True)
                # ファイルが適切なパスで開かれることを確認  
                mock_file.assert_called_once_with(expected_file_path, 'w', encoding='utf-8')
    
    def test_validate_podcast_script_format(self):
        """生成されたポッドキャスト台本のフォーマット検証テスト"""
        # Arrange
        valid_script = """Please read aloud the following in a podcast interview style:
Speaker 1: こんにちは、今日の論文について教えてください。
Speaker 2: この論文は検索システムの改善について述べています。
Speaker 1: どのような問題を解決しようとしているのでしょうか？"""
        
        invalid_script_no_header = """Speaker 1: こんにちは
Speaker 2: はい"""
        
        invalid_script_wrong_format = """Please read aloud the following in a podcast interview style:
ホスト: こんにちは
ゲスト: はい"""
        
        # Act & Assert
        from podcast_generator import validate_podcast_script_format
        assert validate_podcast_script_format(valid_script) == True
        assert validate_podcast_script_format(invalid_script_no_header) == False
        assert validate_podcast_script_format(invalid_script_wrong_format) == False
    
    def test_gemini_api_error_in_podcast_generation(self):
        """ポッドキャスト生成時のGemini APIエラー処理テスト"""
        # Arrange
        mock_paper_html = "<html>Test content</html>"
        
        # Act & Assert
        with patch('google.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception("API rate limit exceeded")
            
            with patch('config.get_gemini_api_key', return_value='test_api_key'):
                with patch('config.get_gemini_model_podcast', return_value='gemini-2.0-flash-exp'):
                    from podcast_generator import generate_podcast_script
                    with pytest.raises(Exception):
                        generate_podcast_script(mock_paper_html, "2509.03236")
    
    def test_extract_key_sections_from_paper_html(self):
        """論文HTMLから重要セクションを抽出するテスト"""
        # Arrange
        paper_html = """
        <html>
            <head><title>Test Paper</title></head>
            <body>
                <h1>Paper Title</h1>
                <div class="ltx_abstract">
                    <p>This paper proposes a new method...</p>
                </div>
                <section id="S1">
                    <h2>1. Introduction</h2>
                    <p>The problem we address is...</p>
                </section>
                <section id="S2">
                    <h2>2. Related Work</h2>
                    <p>Previous approaches have...</p>
                </section>
            </body>
        </html>
        """
        
        # Act & Assert
        from podcast_generator import extract_key_sections_from_paper_html
        result = extract_key_sections_from_paper_html(paper_html)
        assert "abstract" in result or "Abstract" in result
        assert "Introduction" in result or "introduction" in result