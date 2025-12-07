"""
Конфігураційний файл для голосового асистента УкрЕнерго
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

class Config:
    """Конфігурація додатку"""
    
    # Azure Speech Services
    AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
    AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', 'eastus')
    
    # Українські голоси
    UKRAINIAN_VOICES = {
        'female': 'uk-UA-PolinaNeural',
        'male': 'uk-UA-OstapNeural'
    }
    
    # Шляхи
    BASE_DIR = Path(__file__).parent
    ASSETS_DIR = BASE_DIR / 'assets'
    DATA_DIR = BASE_DIR / 'data'
    
    # Налаштування додатку
    APP_TITLE = "Голосовий асистент УкрЕнерго"
    APP_DESCRIPTION = "Інтелектуальний помічник для клієнтів енергетичної компанії"
    
    # Мови
    SUPPORTED_LANGUAGES = {
        'uk': 'Українська',
        'en': 'English',
        'ru': 'Русский'
    }
    
    # Налаштування TTS
    TTS_SETTINGS = {
        'rate': 0,      # -100 до 100
        'pitch': 0,     # -100 до 100
        'volume': 100   # 0 до 100
    }
    
    # Налаштування чат-бота
    CHATBOT_SETTINGS = {
        'max_history': 10,
        'response_delay': 0.5,
        'typing_animation': True
    }
    
    # Контактна інформація
    CONTACT_INFO = {
        'phone': '0 800 500 425',
        'email': 'support@ukrenergo.ua',
        'website': 'https://www.ukrenergo.ua',
        'emergency': '104'
    }
    
    # Тарифи (гривень за кВт·год)
    TARIFFS = {
        'residential_day': 2.64,
        'residential_night': 1.32,
        'commercial': 4.20,
        'industrial': 3.85
    }
    
    @classmethod
    def validate(cls):
        """Перевірка конфігурації"""
        if not cls.AZURE_SPEECH_KEY:
            raise ValueError("AZURE_SPEECH_KEY не встановлено в .env файлі")
        
        # Створення необхідних директорій
        cls.ASSETS_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        
        return True

# Ініціалізація конфігурації
config = Config()
