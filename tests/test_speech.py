"""
Тести для модулю speech_module.py
"""

import unittest
from unittest.mock import MagicMock, patch
from modules.speech_module import UkrenergoSpeechModule

# Мокуємо залежності, які вимагають зовнішніх ресурсів
class MockSpeechConfig:
    def __init__(self, subscription, region):
        pass
    def set_speech_synthesis_output_format(self, format):
        pass
    def set_speech_recognition_language(self, lang):
        pass
    def set_speech_synthesis_voice_name(self, voice):
        pass

class MockSpeechSynthesizer:
    def __init__(self, speech_config, audio_config):
        pass
    def speak_ssml_async(self, ssml):
        mock_result = MagicMock()
        mock_result.reason = 8 # SynthesizingAudioCompleted
        mock_result.audio_data = b'mock_audio_data'
        return MagicMock(get=MagicMock(return_value=mock_result))
    def get_voices_async(self, locale):
        mock_result = MagicMock()
        mock_result.reason = 1 # VoicesListRetrieved
        mock_voice = MagicMock()
        mock_voice.name = "uk-UA-PolinaNeural"
        mock_voice.local_name = "Polina"
        mock_voice.gender = MagicMock(name="Female")
        mock_voice.locale = "uk-UA"
        mock_result.voices = [mock_voice]
        return MagicMock(get=MagicMock(return_value=mock_result))

class MockSpeechRecognizer:
    def __init__(self, speech_config, audio_config):
        pass
    def recognize_once_async(self):
        mock_result = MagicMock()
        mock_result.reason = 1 # RecognizedSpeech
        mock_result.text = "Привіт, як справи?"
        return MagicMock(get=MagicMock(return_value=mock_result))

class MockSpeechSDK:
    SpeechConfig = MockSpeechConfig
    SpeechSynthesizer = MockSpeechSynthesizer
    SpeechRecognizer = MockSpeechRecognizer
    AudioConfig = MagicMock()
    ResultReason = MagicMock(
        SynthesizingAudioCompleted=8,
        RecognizedSpeech=1,
        NoMatch=2
    )

@patch('modules.speech_module.speechsdk', MockSpeechSDK)
@patch('modules.speech_module.st', MagicMock())
class TestUkrenergoSpeechModule(unittest.TestCase):
    
    def setUp(self):
        self.module = UkrenergoSpeechModule(speech_key="test_key", region="test_region")
    
    def test_initialization(self):
        self.assertIsNotNone(self.module.speech_config)
        self.assertEqual(self.module.speech_key, "test_key")
        self.assertEqual(self.module.region, "test_region")
    
    def test_text_to_speech_success(self):
        audio_data = self.module.text_to_speech("Привіт")
        self.assertEqual(audio_data, b'mock_audio_data')
        self.assertEqual(self.module.usage_stats['tts_requests'], 1)
        self.assertIn('Привіт', self.module.audio_cache)
    
    @patch('modules.speech_module.tempfile.NamedTemporaryFile')
    def test_speech_to_text_success(self, mock_tempfile):
        # Мокуємо тимчасовий файл
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_audio.wav"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        with patch('modules.speech_module.Path') as mock_path:
            text = self.module.speech_to_text(b'some_audio_data')
            self.assertEqual(text, "Привіт, як справи?")
            self.assertEqual(self.module.usage_stats['stt_requests'], 1)
            mock_path.return_value.unlink.assert_called_once() # Перевірка видалення файлу
    
    def test_get_available_voices(self):
        voices = self.module.get_available_voices("uk-UA")
        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0]['name'], "uk-UA-PolinaNeural")
        self.assertEqual(voices[0]['local_name'], "Polina")
    
    def test_create_audio_player(self):
        html = self.module.create_audio_player(b'mock_audio_data', autoplay=True)
        self.assertIn('<audio controls autoplay', html)
        self.assertIn('data:audio/wav;base64,bW9ja19hdWRpb19kYXRh', html)

if __name__ == '__main__':
    unittest.main()
