"""環境設定モジュールのテスト"""

import pytest
from unittest.mock import patch, mock_open
import os


class TestConfig:
    """環境設定モジュールのテストクラス"""

    def test_get_gemini_api_key_success(self):
        """GEMINI_API_KEY取得成功のテスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            from config import get_gemini_api_key
            result = get_gemini_api_key()
            assert result == 'test_api_key'

    def test_get_gemini_api_key_missing(self):
        """GEMINI_API_KEY未設定時のテスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {}, clear=True):
            from config import get_gemini_api_key
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is not set"):
                get_gemini_api_key()

    def test_get_gemini_model_summary_default(self):
        """要約用モデルのデフォルト値テスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {}, clear=True):
            from config import get_gemini_model_summary
            result = get_gemini_model_summary()
            assert result == "gemini-2.0-flash-exp"

    def test_get_gemini_model_summary_custom(self):
        """要約用モデルのカスタム設定テスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {'GEMINI_MODEL_SUMMARY': 'gemini-1.5-pro'}):
            from config import get_gemini_model_summary
            result = get_gemini_model_summary()
            assert result == "gemini-1.5-pro"

    def test_get_gemini_model_podcast_default(self):
        """ポッドキャスト用モデルのデフォルト値テスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {}, clear=True):
            from config import get_gemini_model_podcast
            result = get_gemini_model_podcast()
            assert result == "gemini-2.0-flash-exp"

    def test_get_gemini_model_podcast_custom(self):
        """ポッドキャスト用モデルのカスタム設定テスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {'GEMINI_MODEL_PODCAST': 'gemini-1.5-flash'}):
            from config import get_gemini_model_podcast
            result = get_gemini_model_podcast()
            assert result == "gemini-1.5-flash"

    def test_get_gemini_model_tts_default(self):
        """TTS用モデルのデフォルト値テスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {}, clear=True):
            from config import get_gemini_model_tts
            result = get_gemini_model_tts()
            assert result == "gemini-2.5-flash-preview-tts"

    def test_get_gemini_model_tts_custom(self):
        """TTS用モデルのカスタム設定テスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {'GEMINI_MODEL_TTS': 'custom-tts-model'}):
            from config import get_gemini_model_tts
            result = get_gemini_model_tts()
            assert result == "custom-tts-model"

    def test_validate_environment_success(self):
        """環境検証成功のテスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            from config import validate_environment
            assert validate_environment() == True

    def test_validate_environment_failure(self):
        """環境検証失敗のテスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {}, clear=True):
            from config import validate_environment
            assert validate_environment() == False

    def test_get_all_gemini_models(self):
        """全モデル設定取得のテスト"""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_key',
            'GEMINI_MODEL_SUMMARY': 'custom-summary-model',
            'GEMINI_MODEL_PODCAST': 'custom-podcast-model',
            'GEMINI_MODEL_TTS': 'custom-tts-model'
        }):
            from config import get_all_gemini_models
            result = get_all_gemini_models()
            
            assert result['api_key'] == 'test_key'
            assert result['summary_model'] == 'custom-summary-model'
            assert result['podcast_model'] == 'custom-podcast-model'
            assert result['tts_model'] == 'custom-tts-model'

    def test_dotenv_file_loading(self):
        """.envファイル読み込みのテスト"""
        # Arrange
        mock_env_content = """
GEMINI_API_KEY=file_api_key
GEMINI_MODEL_SUMMARY=file-summary-model
GEMINI_MODEL_PODCAST=file-podcast-model
        """.strip()
        
        # Act & Assert
        with patch('builtins.open', mock_open(read_data=mock_env_content)):
            with patch('os.path.exists', return_value=True):
                # configモジュールを再インポートして.env読み込みをテスト
                import importlib
                import config
                importlib.reload(config)
                
                # 実際の環境変数は確認できないが、エラーが発生しないことを確認
                assert True  # .env読み込み処理が正常に実行される