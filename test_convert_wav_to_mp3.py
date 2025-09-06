"""convert_wav_to_mp3.py のテスト"""

import os
import tempfile
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from convert_wav_to_mp3 import (
    check_ffmpeg_available,
    convert_wav_to_mp3,
    find_wav_files,
    create_mp3_path,
    get_file_size_mb
)


class TestCheckFFmpegAvailable:
    """check_ffmpeg_available 関数のテスト"""
    
    def test_ffmpeg_available_success(self):
        """FFmpegが利用可能な場合のテスト"""
        with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = check_ffmpeg_available()
            assert result is True
            mock_run.assert_called_once_with(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
    
    def test_ffmpeg_not_available_file_not_found(self):
        """FFmpegが見つからない場合のテスト"""
        with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = check_ffmpeg_available()
            assert result is False
    
    def test_ffmpeg_not_available_timeout(self):
        """FFmpegがタイムアウトする場合のテスト"""
        with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=['ffmpeg'], timeout=10)
            
            result = check_ffmpeg_available()
            assert result is False
    
    def test_ffmpeg_not_available_error_code(self):
        """FFmpegがエラーコードを返す場合のテスト"""
        with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result
            
            result = check_ffmpeg_available()
            assert result is False


class TestConvertWavToMp3:
    """convert_wav_to_mp3 関数のテスト"""
    
    def test_convert_success(self):
        """WAVからMP3への変換成功テスト"""
        with tempfile.NamedTemporaryFile(suffix='.wav') as wav_file, \
             tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
            
            wav_path = wav_file.name
            mp3_path = mp3_file.name
            
            with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result
                
                result = convert_wav_to_mp3(wav_path, mp3_path)
                assert result is True
                
                # FFmpegの正しいコマンドが呼ばれることを確認
                expected_command = [
                    'ffmpeg',
                    '-i', wav_path,
                    '-codec:a', 'libmp3lame',
                    '-b:a', '192k',
                    '-q:a', '2',
                    '-y',
                    mp3_path
                ]
                mock_run.assert_called_once_with(
                    expected_command,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            # クリーンアップ
            try:
                os.unlink(mp3_path)
            except OSError:
                pass
    
    def test_convert_custom_bitrate(self):
        """カスタムビットレートでの変換テスト"""
        with tempfile.NamedTemporaryFile(suffix='.wav') as wav_file, \
             tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
            
            wav_path = wav_file.name
            mp3_path = mp3_file.name
            custom_bitrate = "320k"
            
            with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result
                
                result = convert_wav_to_mp3(wav_path, mp3_path, custom_bitrate)
                assert result is True
                
                # カスタムビットレートが使用されることを確認
                call_args = mock_run.call_args[0][0]
                assert '-b:a' in call_args
                bitrate_index = call_args.index('-b:a') + 1
                assert call_args[bitrate_index] == custom_bitrate
            
            # クリーンアップ
            try:
                os.unlink(mp3_path)
            except OSError:
                pass
    
    def test_convert_input_file_not_found(self):
        """入力ファイルが見つからない場合のテスト"""
        non_existent_wav = "/tmp/non_existent.wav"
        mp3_path = "/tmp/output.mp3"
        
        with pytest.raises(FileNotFoundError):
            convert_wav_to_mp3(non_existent_wav, mp3_path)
    
    def test_convert_ffmpeg_error(self):
        """FFmpegがエラーを返す場合のテスト"""
        with tempfile.NamedTemporaryFile(suffix='.wav') as wav_file, \
             tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
            
            wav_path = wav_file.name
            mp3_path = mp3_file.name
            
            with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stderr = "FFmpeg error message"
                mock_run.return_value = mock_result
                
                result = convert_wav_to_mp3(wav_path, mp3_path)
                assert result is False
            
            # クリーンアップ
            try:
                os.unlink(mp3_path)
            except OSError:
                pass
    
    def test_convert_timeout(self):
        """FFmpegがタイムアウトする場合のテスト"""
        with tempfile.NamedTemporaryFile(suffix='.wav') as wav_file, \
             tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
            
            wav_path = wav_file.name
            mp3_path = mp3_file.name
            
            with patch('convert_wav_to_mp3.subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(cmd=['ffmpeg'], timeout=300)
                
                result = convert_wav_to_mp3(wav_path, mp3_path)
                assert result is False
            
            # クリーンアップ
            try:
                os.unlink(mp3_path)
            except OSError:
                pass


class TestFindWavFiles:
    """find_wav_files 関数のテスト"""
    
    def test_find_wav_files_success(self):
        """WAVファイル検索成功テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # テストファイルを作成
            wav_files = [
                "podcast_2024.01.001_000.wav",
                "podcast_2024.01.002_000.wav", 
                "other_file.txt"
            ]
            
            for filename in wav_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w') as f:
                    f.write("test")
            
            result = find_wav_files(temp_dir)
            
            # podcast_*.wavのみが返されることを確認
            assert len(result) == 2
            assert all(f.endswith('.wav') and 'podcast_' in f for f in result)
            assert all(os.path.basename(f) in wav_files[:2] for f in result)
    
    def test_find_wav_files_directory_not_found(self):
        """ディレクトリが見つからない場合のテスト"""
        non_existent_dir = "/tmp/non_existent_directory"
        
        with pytest.raises(FileNotFoundError):
            find_wav_files(non_existent_dir)
    
    def test_find_wav_files_not_directory(self):
        """指定されたパスがディレクトリでない場合のテスト"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(NotADirectoryError):
                find_wav_files(temp_file.name)
    
    def test_find_wav_files_empty_directory(self):
        """WAVファイルが見つからない場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = find_wav_files(temp_dir)
            assert result == []


class TestCreateMp3Path:
    """create_mp3_path 関数のテスト"""
    
    def test_create_mp3_path_same_directory(self):
        """同じディレクトリにMP3を作成する場合のテスト"""
        wav_path = "/path/to/audio/podcast_2024.01.001_000.wav"
        expected_mp3_path = "/path/to/audio/podcast_2024.01.001_000.mp3"
        
        result = create_mp3_path(wav_path)
        assert result == expected_mp3_path
    
    def test_create_mp3_path_custom_output_dir(self):
        """カスタム出力ディレクトリを指定した場合のテスト"""
        wav_path = "/path/to/audio/podcast_2024.01.001_000.wav"
        output_dir = "/different/output/dir"
        expected_mp3_path = "/different/output/dir/podcast_2024.01.001_000.mp3"
        
        result = create_mp3_path(wav_path, output_dir)
        assert result == expected_mp3_path
    
    def test_create_mp3_path_filename_only(self):
        """ファイル名のみの場合のテスト"""
        wav_path = "podcast_2024.01.001_000.wav"
        expected_mp3_path = "podcast_2024.01.001_000.mp3"
        
        result = create_mp3_path(wav_path)
        assert result == expected_mp3_path


class TestGetFileSizeMb:
    """get_file_size_mb 関数のテスト"""
    
    def test_get_file_size_mb_existing_file(self):
        """存在するファイルのサイズ取得テスト"""
        with tempfile.NamedTemporaryFile() as temp_file:
            # 1024バイト（約1KB）のデータを書き込み
            test_data = b'x' * 1024
            temp_file.write(test_data)
            temp_file.flush()
            
            result = get_file_size_mb(temp_file.name)
            expected_size = 1024 / (1024 * 1024)  # MB換算
            
            assert abs(result - expected_size) < 0.001  # 小数点以下の誤差を許容
    
    def test_get_file_size_mb_non_existent_file(self):
        """存在しないファイルの場合のテスト"""
        non_existent_file = "/tmp/non_existent_file.txt"
        
        result = get_file_size_mb(non_existent_file)
        assert result == 0.0
    
    def test_get_file_size_mb_empty_file(self):
        """空ファイルの場合のテスト"""
        with tempfile.NamedTemporaryFile() as temp_file:
            result = get_file_size_mb(temp_file.name)
            assert result == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])