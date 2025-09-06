"""ポッドキャスト音声生成機能のテスト"""

import pytest
from unittest.mock import Mock, patch, mock_open
import os
import tempfile
from pathlib import Path


class TestOutputPodcast:
    """ポッドキャスト音声生成機能のテストクラス"""

    def test_load_podcast_script_success(self):
        """台本ファイル読み込み成功のテスト"""
        # Arrange
        test_script = """Please read aloud the following in a podcast interview style:
Speaker 1: こんにちは、今日は新しい論文について話しましょう。
Speaker 2: はい、この論文は推薦システムについて述べています。"""

        # Act & Assert
        with patch('builtins.open', mock_open(read_data=test_script)):
            from output_podcast import load_podcast_script
            result = load_podcast_script("test.md")
            assert result == test_script

    def test_load_podcast_script_file_not_found(self):
        """台本ファイルが見つからない場合のテスト"""
        # Act & Assert
        with patch('builtins.open', side_effect=FileNotFoundError()):
            from output_podcast import load_podcast_script
            with pytest.raises(FileNotFoundError):
                load_podcast_script("nonexistent.md")

    def test_validate_script_format_valid(self):
        """正しいフォーマットの台本検証テスト"""
        # Arrange
        valid_script = """Please read aloud the following in a podcast interview style:
Speaker 1: こんにちは、今日の論文について教えてください。
Speaker 2: この論文は検索システムの改善について述べています。"""

        # Act & Assert
        from output_podcast import validate_script_format
        assert validate_script_format(valid_script) == True

    def test_validate_script_format_invalid_no_header(self):
        """ヘッダーがない台本の検証テスト"""
        # Arrange
        invalid_script = """Speaker 1: こんにちは
Speaker 2: はい"""

        # Act & Assert
        from output_podcast import validate_script_format
        assert validate_script_format(invalid_script) == False

    def test_validate_script_format_invalid_no_speakers(self):
        """話者がない台本の検証テスト"""
        # Arrange
        invalid_script = """Please read aloud the following in a podcast interview style:
ホスト: こんにちは
ゲスト: はい"""

        # Act & Assert
        from output_podcast import validate_script_format
        assert validate_script_format(invalid_script) == False

    def test_find_podcast_scripts(self):
        """台本ファイル検索のテスト"""
        # Arrange & Act & Assert
        with patch('glob.glob') as mock_glob:
            mock_glob.return_value = [
                'data/20241206/2409.12345.md',
                'data/20241206/2409.12346.md', 
                'data/20241206/abstract.md'
            ]
            
            from output_podcast import find_podcast_scripts
            result = find_podcast_scripts('data/20241206')
            
            # abstract.mdは除外される
            expected = [
                ('data/20241206/2409.12345.md', '2409.12345'),
                ('data/20241206/2409.12346.md', '2409.12346')
            ]
            assert result == expected

    def test_create_output_directory(self):
        """出力ディレクトリ作成のテスト"""
        # Arrange & Act & Assert
        with patch('os.makedirs') as mock_makedirs:
            from output_podcast import create_output_directory
            result = create_output_directory('data/20241206')
            
            expected_path = 'data/20241206/audio'
            assert result == expected_path
            mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)

    def test_parse_audio_mime_type_default(self):
        """MIMEタイプ解析のデフォルト値テスト"""
        # Act & Assert
        from output_podcast import parse_audio_mime_type
        result = parse_audio_mime_type('audio/unknown')
        
        assert result['bits_per_sample'] == 16
        assert result['rate'] == 24000

    def test_parse_audio_mime_type_with_parameters(self):
        """MIMEタイプ解析のパラメータ付きテスト"""
        # Act & Assert
        from output_podcast import parse_audio_mime_type
        result = parse_audio_mime_type('audio/L16;rate=48000')
        
        assert result['bits_per_sample'] == 16
        assert result['rate'] == 48000

    def test_save_binary_file(self):
        """バイナリファイル保存のテスト"""
        # Arrange
        test_data = b'\x01\x02\x03\x04'
        test_filename = 'test.wav'
        
        # Act & Assert
        with patch('builtins.open', mock_open()) as mock_file:
            from output_podcast import save_binary_file
            save_binary_file(test_filename, test_data)
            
            mock_file.assert_called_once_with(test_filename, 'wb')
            mock_file().write.assert_called_once_with(test_data)

    def test_generate_audio_from_script_success(self):
        """音声生成成功のテスト"""
        # Arrange
        test_script = """Please read aloud the following in a podcast interview style:
Speaker 1: テスト台本です。
Speaker 2: はい、テストです。"""
        
        # Act & Assert
        with patch('google.genai.Client') as mock_client_class:
            with patch('config.get_gemini_api_key', return_value='test_api_key'):
                with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_api_key'}):
                    mock_client = Mock()
                    mock_client_class.return_value = mock_client
                    
                    # 音声データを含むチャンクをシミュレート
                    mock_chunk = Mock()
                    mock_chunk.candidates = [Mock()]
                    mock_chunk.candidates[0].content = Mock()
                    mock_chunk.candidates[0].content.parts = [Mock()]
                    mock_inline_data = Mock()
                    mock_inline_data.data = b'\x01\x02\x03\x04'
                    mock_inline_data.mime_type = 'audio/wav'
                    mock_chunk.candidates[0].content.parts[0].inline_data = mock_inline_data
                    
                    mock_client.models.generate_content_stream.return_value = [mock_chunk]
                    
                    with patch('output_podcast.save_binary_file'):
                        with patch('mimetypes.guess_extension', return_value='.wav'):
                            from output_podcast import generate_audio_from_script
                            result = generate_audio_from_script(test_script, 'test_output')
                            assert result == True

    def test_generate_audio_from_script_api_error(self):
        """音声生成APIエラーのテスト"""
        # Arrange
        test_script = "Test script"
        
        # Act & Assert
        with patch('google.genai.Client') as mock_client_class:
            with patch('config.get_gemini_api_key', return_value='test_api_key'):
                with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_api_key'}):
                    mock_client = Mock()
                    mock_client_class.return_value = mock_client
                    mock_client.models.generate_content_stream.side_effect = Exception("API Error")
                    
                    from output_podcast import generate_audio_from_script
                    result = generate_audio_from_script(test_script, 'test_output')
                    assert result == False

    def test_convert_to_wav(self):
        """WAV変換のテスト"""
        # Arrange
        test_audio_data = b'\x01\x02\x03\x04' * 100  # ダミーオーディオデータ
        mime_type = 'audio/L16;rate=24000'
        
        # Act
        from output_podcast import convert_to_wav
        result = convert_to_wav(test_audio_data, mime_type)
        
        # Assert
        assert result.startswith(b'RIFF')  # WAVファイルのマジックナンバー
        assert b'WAVE' in result
        assert len(result) > len(test_audio_data)  # ヘッダーが追加されている