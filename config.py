"""環境設定とモデル設定管理"""

import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


def get_gemini_api_key() -> str:
    """Gemini API keyを取得"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return api_key


def get_gemini_model_summary() -> str:
    """論文要約用Geminiモデルを取得"""
    return os.environ.get("GEMINI_MODEL_SUMMARY", "gemini-2.0-flash-exp")


def get_gemini_model_podcast() -> str:
    """ポッドキャスト生成用Geminiモデルを取得"""
    return os.environ.get("GEMINI_MODEL_PODCAST", "gemini-2.0-flash-exp")


def get_gemini_model_tts() -> str:
    """TTS（音声生成）用Geminiモデルを取得"""
    return os.environ.get("GEMINI_MODEL_TTS", "gemini-2.5-flash-preview-tts")


def validate_environment() -> bool:
    """
    必要な環境変数がすべて設定されているかチェック
    
    Returns:
        bool: 環境が正しく設定されている場合True
    """
    try:
        get_gemini_api_key()
        return True
    except ValueError:
        return False


def get_all_gemini_models() -> dict:
    """すべてのGeminiモデル設定を辞書で返す"""
    return {
        "api_key": get_gemini_api_key(),
        "summary_model": get_gemini_model_summary(),
        "podcast_model": get_gemini_model_podcast(),
        "tts_model": get_gemini_model_tts()
    }