"""main.py のテスト"""

import pytest
from unittest.mock import patch, MagicMock, call
import tempfile
import os

from main import check_environment, generate_audio_and_convert_to_mp3


class TestCheckEnvironment:
    """check_environment 関数のテスト"""
    
    def test_check_environment_success(self):
        """環境設定が正常な場合のテスト"""
        with patch('main.validate_environment', return_value=True), \
             patch('main.get_all_gemini_models', return_value={
                 'summary_model': 'gemini-2.0-flash-exp',
                 'podcast_model': 'gemini-2.0-flash-exp'
             }):
            
            result = check_environment()
            assert result is True
    
    def test_check_environment_missing_api_key(self):
        """API keyが設定されていない場合のテスト"""
        with patch('main.validate_environment', return_value=False):
            result = check_environment()
            assert result is False


class TestGenerateAudioAndConvertToMp3:
    """generate_audio_and_convert_to_mp3 関数のテスト"""
    
    def test_generate_audio_and_convert_success(self):
        """音声生成とMP3変換の成功テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # モックデータ設定
            mock_script_files = [
                (os.path.join(temp_dir, "script1.md"), "2024.01.001"),
                (os.path.join(temp_dir, "script2.md"), "2024.01.002")
            ]
            
            mock_wav_files = [
                os.path.join(temp_dir, "audio", "podcast_2024.01.001_000.wav"),
                os.path.join(temp_dir, "audio", "podcast_2024.01.002_000.wav")
            ]
            
            # モック設定
            with patch('main.find_podcast_scripts', return_value=mock_script_files), \
                 patch('main.create_output_directory', return_value=os.path.join(temp_dir, "audio")), \
                 patch('main.load_podcast_script', return_value="test script"), \
                 patch('main.generate_audio_from_script', return_value=True), \
                 patch('main.check_ffmpeg_available', return_value=True), \
                 patch('main.find_wav_files', return_value=mock_wav_files), \
                 patch('main.convert_wav_to_mp3', return_value=True), \
                 patch('main.create_mp3_path') as mock_create_mp3_path, \
                 patch('main.get_file_size_mb', return_value=10.0), \
                 patch('os.remove') as mock_remove:
                
                # MP3パスのモック設定
                mock_create_mp3_path.side_effect = lambda x: x.replace('.wav', '.mp3')
                
                result = generate_audio_and_convert_to_mp3(temp_dir)
                
                # 結果検証
                assert result is True
                
                # WAVファイル削除が2回呼ばれることを確認（keep_wav=Falseの場合）
                assert mock_remove.call_count == 2
    
    def test_generate_audio_and_convert_no_script_files(self):
        """台本ファイルが見つからない場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('main.find_podcast_scripts', return_value=[]):
                result = generate_audio_and_convert_to_mp3(temp_dir)
                assert result is False
    
    def test_generate_audio_and_convert_no_ffmpeg(self):
        """FFmpegが利用できない場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_script_files = [
                (os.path.join(temp_dir, "script1.md"), "2024.01.001")
            ]
            
            with patch('main.find_podcast_scripts', return_value=mock_script_files), \
                 patch('main.create_output_directory', return_value=os.path.join(temp_dir, "audio")), \
                 patch('main.load_podcast_script', return_value="test script"), \
                 patch('main.generate_audio_from_script', return_value=True), \
                 patch('main.check_ffmpeg_available', return_value=False):
                
                result = generate_audio_and_convert_to_mp3(temp_dir)
                
                # 音声生成は成功するが、FFmpegがないためMP3変換は警告のみでTrueを返す
                assert result is True
    
    def test_generate_audio_and_convert_keep_wav(self):
        """WAVファイルを保持する場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_script_files = [
                (os.path.join(temp_dir, "script1.md"), "2024.01.001")
            ]
            
            mock_wav_files = [
                os.path.join(temp_dir, "audio", "podcast_2024.01.001_000.wav")
            ]
            
            with patch('main.find_podcast_scripts', return_value=mock_script_files), \
                 patch('main.create_output_directory', return_value=os.path.join(temp_dir, "audio")), \
                 patch('main.load_podcast_script', return_value="test script"), \
                 patch('main.generate_audio_from_script', return_value=True), \
                 patch('main.check_ffmpeg_available', return_value=True), \
                 patch('main.find_wav_files', return_value=mock_wav_files), \
                 patch('main.convert_wav_to_mp3', return_value=True), \
                 patch('main.create_mp3_path', return_value="/path/to/output.mp3"), \
                 patch('main.get_file_size_mb', return_value=10.0), \
                 patch('os.remove') as mock_remove:
                
                result = generate_audio_and_convert_to_mp3(temp_dir, keep_wav=True)
                
                # 結果検証
                assert result is True
                
                # WAVファイル削除が呼ばれないことを確認（keep_wav=Trueの場合）
                mock_remove.assert_not_called()
    
    def test_generate_audio_and_convert_audio_generation_failure(self):
        """音声生成に失敗した場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_script_files = [
                (os.path.join(temp_dir, "script1.md"), "2024.01.001")
            ]
            
            with patch('main.find_podcast_scripts', return_value=mock_script_files), \
                 patch('main.create_output_directory', return_value=os.path.join(temp_dir, "audio")), \
                 patch('main.load_podcast_script', return_value="test script"), \
                 patch('main.generate_audio_from_script', return_value=False):  # 音声生成失敗
                
                result = generate_audio_and_convert_to_mp3(temp_dir)
                
                # 音声生成に失敗した場合はFalseを返す
                assert result is False
    
    def test_generate_audio_and_convert_custom_bitrate(self):
        """カスタムビットレートの場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_script_files = [
                (os.path.join(temp_dir, "script1.md"), "2024.01.001")
            ]
            
            mock_wav_files = [
                os.path.join(temp_dir, "audio", "podcast_2024.01.001_000.wav")
            ]
            
            with patch('main.find_podcast_scripts', return_value=mock_script_files), \
                 patch('main.create_output_directory', return_value=os.path.join(temp_dir, "audio")), \
                 patch('main.load_podcast_script', return_value="test script"), \
                 patch('main.generate_audio_from_script', return_value=True), \
                 patch('main.check_ffmpeg_available', return_value=True), \
                 patch('main.find_wav_files', return_value=mock_wav_files), \
                 patch('main.convert_wav_to_mp3', return_value=True) as mock_convert, \
                 patch('main.create_mp3_path', return_value="/path/to/output.mp3"), \
                 patch('main.get_file_size_mb', return_value=10.0), \
                 patch('os.remove'):
                
                result = generate_audio_and_convert_to_mp3(temp_dir, bitrate="320k")
                
                # 結果検証
                assert result is True
                
                # カスタムビットレートで変換が呼ばれることを確認
                mock_convert.assert_called_with(mock_wav_files[0], "/path/to/output.mp3", "320k")
    
    def test_generate_audio_and_convert_exception_handling(self):
        """例外処理のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('main.find_podcast_scripts', side_effect=Exception("Test error")):
                result = generate_audio_and_convert_to_mp3(temp_dir)
                assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])