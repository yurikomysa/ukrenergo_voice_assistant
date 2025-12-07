"""
Модуль для роботи з синтезом та розпізнаванням мовлення
"""

import azure.cognitiveservices.speech as speechsdk
import streamlit as st
import io
import base64
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import time

class UkrenergoSpeechModule:
    """Модуль обробки мовлення для УкрЕнерго"""
    
    def __init__(self, speech_key: str, region: str = "eastus"):
        """
        Ініціалізація модулю мовлення
        
        Args:
            speech_key: Ключ Azure Speech Services
            region: Регіон Azure
        """
        self.speech_key = speech_key
        self.region = region
        
        # Ініціалізація конфігурації
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=region
        )
        
        # Налаштування для української мови
        self.speech_config.speech_recognition_language = "uk-UA"
        self.speech_config.speech_synthesis_voice_name = "uk-UA-PolinaNeural"
        
        # Налаштування якості синтезу
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
        )
        
        # Кеш для синтезованих аудіо
        self.audio_cache = {}
        
        # Статистика використання
        self.usage_stats = {
            'tts_requests': 0,
            'stt_requests': 0,
            'characters_synthesized': 0,
            'audio_duration': 0
        }
    
    def _create_ssml(self, text: str, rate: int, pitch: int) -> str:
        """Створення SSML для контролю параметрів"""
        rate_str = f"{rate}%" if rate != 0 else "default"
        pitch_str = f"{pitch}%" if pitch != 0 else "default"
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="uk-UA">
            <voice name="{self.speech_config.speech_synthesis_voice_name}">
                <prosody rate="{rate_str}" pitch="{pitch_str}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()
    
    def text_to_speech(self, text: str, voice: str = None, 
                      rate: int = 0, pitch: int = 0) -> Optional[bytes]:
        """
        Синтез мовлення з тексту
        
        Args:
            text: Текст для синтезу
            voice: Голос (за замовчуванням український жіночий)
            rate: Швидкість (-100 до 100)
            pitch: Висота тону (-100 до 100)
            
        Returns:
            Аудіо дані у форматі WAV або None при помилці
        """
        try:
            # Перевірка кешу
            cache_key = f"{text}_{voice}_{rate}_{pitch}"
            if cache_key in self.audio_cache:
                return self.audio_cache[cache_key]
            
            # Налаштування голосу
            if voice:
                self.speech_config.speech_synthesis_voice_name = voice
            
            # Створення синтезатора
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None
            )
            
            # Використання SSML для контролю параметрів
            ssml_text = self._create_ssml(text, rate, pitch)
            
            # Синтез мовлення
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data
                
                # Оновлення статистики
                self.usage_stats['tts_requests'] += 1
                self.usage_stats['characters_synthesized'] += len(text)
                self.usage_stats['audio_duration'] += len(audio_data) / (16000 * 2)  # Приблизно
                
                # Кешування результату
                self.audio_cache[cache_key] = audio_data
                
                return audio_data
            else:
                st.error(f"Помилка синтезу: {result.reason}")
                return None
                
        except Exception as e:
            st.error(f"Помилка TTS: {str(e)}")
            return None
    
    
    
    def speech_to_text(self, audio_data: bytes = None, use_microphone: bool = False) -> Optional[str]:
        """
        Розпізнавання мовлення з байтових даних (без використання файлів!)
        """
        try:
            if use_microphone:
                audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            elif audio_data:
                # Використовуємо PushAudioInputStream без файлів
                stream = speechsdk.audio.PushAudioInputStream()
                audio_config = speechsdk.audio.AudioConfig(stream=stream)
                stream.write(audio_data)
                stream.close()  # Закриваємо потік
            else:
                st.warning("Немає аудіо даних для розпізнавання")
                return None

            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            # Оптимізація для коротких записів
            recognizer.properties.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
                "1000"
            )

            result = recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                self.usage_stats['stt_requests'] += 1
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                st.warning("Мовлення не розпізнано")
                return None
            else:
                error_msg = f"STT помилка: {result.reason}"
                if result.error_details:
                    error_msg += f" — {result.error_details}"
                st.error(error_msg)
                return None

        except Exception as e:
            st.error(f"Помилка STT: {str(e)}")
            return None


    
    def create_audio_player(self, audio_data: bytes, autoplay: bool = False) -> str:
        """
        Створення HTML-коду для аудіо-плеєра Streamlit
        
        Args:
            audio_data: Аудіо дані
            autoplay: Чи відтворювати автоматично
            
        Returns:
            HTML-код
        """
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        autoplay_attr = "autoplay" if autoplay else ""
        
        html_code = f"""
        <audio controls {autoplay_attr} style="width: 100%;">
            <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            Ваш браузер не підтримує аудіо елемент.
        </audio>
        """
        return html_code
    
    def get_available_voices(self, locale: str = "uk-UA") -> List[Dict]:
        """
        Отримання списку доступних голосів
        
        Args:
            locale: Локаль для фільтрації
            
        Returns:
            Список словників з інформацією про голоси
        """
        try:
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None
            )
            
            result = speech_synthesizer.get_voices_async(locale).get()
            
            if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                voices = []
                for voice in result.voices:
                    voices.append({
                        'name': voice.name,
                        'local_name': voice.local_name,
                        'gender': str(voice.gender).split('.')[-1],
                        'locale': voice.locale
                    })
                return voices
            else:
                st.error(f"Помилка отримання голосів: {result.reason}")
                return []
        except Exception as e:
            st.error(f"Помилка отримання голосів: {str(e)}")
            return []
    
    def get_usage_statistics(self) -> Dict:
        """Отримання статистики використання"""
        return self.usage_stats
    
    def generate_announcement_audio(self, announcement_type: str, **kwargs) -> Optional[bytes]:
        """
        Генерація аудіо для стандартних оголошень
        """
        announcements = {
            'welcome': "Ласкаво просимо до голосового асистента УкрЕнерго! Чим можу допомогти?",
            'payment_reminder': f"Нагадуємо про необхідність оплати рахунку до {kwargs.get('date', 'кінця місяця')}. Сума до оплати: {kwargs.get('amount', 'уточніть в рахунку')} гривень.",
            'emergency': f"Увага! {kwargs.get('area', 'Вашому районі')} планові роботи з {kwargs.get('start', '10:00')} до {kwargs.get('end', '16:00')}. Будь ласка, підготуйтеся до тимчасового відключення електроенергії.",
            'tariff_change': f"Інформуємо про зміну тарифів з {kwargs.get('date', 'наступного місяця')}. Денний тариф: {kwargs.get('day_rate', '2.64')} грн/кВт·год, нічний: {kwargs.get('night_rate', '1.32')} грн/кВт·год.",
            'meter_reading': "Нагадуємо про необхідність передачі показників лічильника до 25 числа поточного місяця. Ви можете зробити це через особистий кабінет або чат-бота."
        }
        
        if announcement_type not in announcements:
            return None
        
        text = announcements[announcement_type]
        return self.text_to_speech(text)
    
    def save_audio_to_file(self, audio_data: bytes, 
                          filename: str = "output.wav") -> str:
        """
        Збереження аудіо у файл
        
        Args:
            audio_data: Аудіо дані
            filename: Ім'я файлу
            
        Returns:
            Шлях до збереженого файлу
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_data)
                return f.name
        except Exception as e:
            st.error(f"Помилка збереження файлу: {str(e)}")
            return None


# Глобальний екземпляр модулю мовлення
speech_module = None

def get_speech_module():
    """Отримання глобального екземпляру модулю мовлення"""
    global speech_module
    if speech_module is None:
        from config import config
        speech_module = UkrenergoSpeechModule(
            speech_key=config.AZURE_SPEECH_KEY,
            region=config.AZURE_SPEECH_REGION
        )
    return speech_module
