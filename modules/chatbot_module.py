"""
Модуль чат-бота для УкрЕнерго
"""

import json
import re
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import streamlit as st
from difflib import SequenceMatcher

class UkrenergoChatbot:
    """Інтелектуальний чат-бот для клієнтів УкрЕнерго"""
    
    def __init__(self, faq_file: str = "data/faq.json"):
        """
        Ініціалізація чат-бота
        
        Args:
            faq_file: Шлях до файлу з FAQ
        """
        self.faq_file = faq_file
        self.faq_data = self._load_faq()
        self.conversation_history = []
        self.user_context = {}
        
        # Ініціалізація інтентів
        self.intents = self._initialize_intents()
        
        # Статистика
        self.stats = {
            'total_questions': 0,
            'answered_questions': 0,
            'common_questions': {},
            'response_times': []
        }
    
    def _load_faq(self) -> dict:
        """Завантаження FAQ з файлу"""
        try:
            with open(self.faq_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Створення базового FAQ
            return {
                'categories': {},
                'questions': []
            }
    
    def _initialize_intents(self) -> Dict[str, dict]:
        """Ініціалізація інтентів (намірів)"""
        return {
            'greeting': {
                'patterns': ['привіт', 'добрий день', 'доброго дня', 'вітаю', 'хай'],
                'responses': [
                    'Доброго дня! Ласкаво просимо до голосового асистента УкрЕнерго.',
                    'Вітаємо! Чим можемо допомогти?',
                    'Привіт! Раді вас бачити.'
                ]
            },
            'farewell': {
                'patterns': ['бувай', 'до побачення', 'пакеда', 'дякую', 'спасибі'],
                'responses': [
                    'До побачення! Звертайтеся, якщо будуть питання.',
                    'Раді були допомогти! Гарного дня.',
                    'Дякуємо за звернення!'
                ]
            },
            'payment': {
                'patterns': ['оплата', 'рахунок', 'гроші', 'платіж', 'інвойс', 'квитанція'],
                'responses': ['Я можу допомогти з оплатою рахунків.']
            },
            'emergency': {
                'patterns': ['відключення', 'аварія', 'світла немає', 'чорноби', 'аварійка'],
                'responses': ['Можу допомогти з інформацією про відключення.']
            },
            'tariff': {
                'patterns': ['тариф', 'ціна', 'вартість', 'кВт', 'тарифи'],
                'responses': ['Можу надати інформацію про тарифи.']
            },
            'meter': {
                'patterns': ['лічильник', 'показники', 'пробіг', 'передача', 'лічильника'],
                'responses': ['Допоможу з передачею показників лічильника.']
            },
            'connection': {
                'patterns': ['підключення', 'нова', 'будівля', 'приміщення', 'техумови'],
                'responses': ['Можу надати інформацію про підключення.']
            },
            'document': {
                'patterns': ['документ', 'папір', 'довідка', 'заява', 'запит'],
                'responses': ['Допоможу з документами.']
            },
            'contact': {
                'patterns': ['телефон', 'контакт', 'адреса', 'зв\'язок', 'підтримка'],
                'responses': ['Надам контактну інформацію.']
            }
        }
    
    def process_message(self, message: str, user_id: str = None) -> str:
        """
        Обробка повідомлення від користувача
        
        Args:
            message: Текст повідомлення
            user_id: Ідентифікатор користувача
            
        Returns:
            Відповідь чат-бота
        """
        start_time = datetime.now()
        
        # Логування запиту
        self._log_request(message, user_id)
        
        # Нормалізація тексту
        normalized_message = self._normalize_text(message)
        
        # Визначення наміру
        intent = self._detect_intent(normalized_message)
        
        # Пошук відповіді
        response = self._find_response(normalized_message, intent)
        
        # Збереження в історію
        self._save_to_history(user_id, message, response)
        
        # Оновлення статистики
        self._update_stats(start_time, message, response)
        
        return response
    
    def _normalize_text(self, text: str) -> str:
        """Нормалізація тексту"""
        # Приведення до нижнього регістру
        text = text.lower()
        
        # Видалення зайвих пробілів
        text = ' '.join(text.split())
        
        # Видалення пунктуації
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def _detect_intent(self, text: str) -> str:
        """Визначення наміру користувача"""
        best_intent = 'unknown'
        best_score = 0
        
        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data['patterns']:
                similarity = SequenceMatcher(None, text, pattern).ratio()
                if similarity > best_score and similarity > 0.6:
                    best_score = similarity
                    best_intent = intent_name
        
        return best_intent
    
    def _find_response(self, query: str, intent: str) -> str:
        """Пошук відповіді на запит"""
        # Пошук в FAQ
        faq_response = self._search_faq(query)
        if faq_response:
            return faq_response
        
        # Генерація відповіді за наміром
        if intent in self.intents and intent != 'unknown':
            responses = self.intents[intent]['responses']
            return random.choice(responses)
        
        # Загальна відповідь
        return self._get_fallback_response()
    
    def _search_faq(self, query: str) -> Optional[str]:
        """Пошук відповіді в FAQ"""
        best_match = None
        best_score = 0
        
        for question in self.faq_data.get('questions', []):
            # Перевірка ключових слів
            keywords = question.get('keywords', [])
            keyword_match = any(keyword in query for keyword in keywords)
            
            if keyword_match:
                return question['answer']
            
            # Порівняння з питанням
            question_text = self._normalize_text(question['question'])
            similarity = SequenceMatcher(None, query, question_text).ratio()
            
            if similarity > best_score and similarity > 0.7:
                best_score = similarity
                best_match = question['answer']
        
        return best_match
    
    def _get_fallback_response(self) -> str:
        """Отримання загальної відповіді"""
        fallback_responses = [
            "Вибачте, я не зрозумів ваш запит. Можете переформулювати?",
            "Не впевнений, що правильно зрозумів. Уточніть, будь ласка.",
            "Це питання потребує уточнення. Можете описати детальніше?",
            "Для точної відповіді мені потрібно більше інформації.",
            "Зверніться, будь ласка, до оператора за детальною інформацією."
        ]
        
        return random.choice(fallback_responses)
    
    def _log_request(self, message: str, user_id: str):
        """Логування запиту"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id or 'anonymous',
            'message': message
        }
        
        # Збереження в сесії Streamlit
        if 'chat_logs' not in st.session_state:
            st.session_state.chat_logs = []
        
        st.session_state.chat_logs.append(log_entry)
    
    def _save_to_history(self, user_id: str, message: str, response: str):
        """Збереження в історію розмови"""
        entry = {
            'user_id': user_id,
            'timestamp': datetime.now(),
            'user_message': message,
            'bot_response': response
        }
        self.conversation_history.append(entry)
    
    def _update_stats(self, start_time: datetime, message: str, response: str):
        """Оновлення статистики"""
        self.stats['total_questions'] += 1
        
        if response not in self.intents.get('unknown', {}).get('responses', []):
            self.stats['answered_questions'] += 1
        
        # Час відповіді
        response_time = (datetime.now() - start_time).total_seconds()
        self.stats['response_times'].append(response_time)
        
        # Популярні питання (спрощено)
        normalized_message = self._normalize_text(message)
        if normalized_message in self.stats['common_questions']:
            self.stats['common_questions'][normalized_message] += 1
        else:
            self.stats['common_questions'][normalized_message] = 1
    
    def get_statistics(self) -> Dict:
        """Отримання статистики чат-бота"""
        total = self.stats['total_questions']
        answered = self.stats['answered_questions']
        
        stats = {
            'total_questions': total,
            'answered_questions': answered,
            'answer_rate': (answered / total) * 100 if total > 0 else 0,
            'avg_response_time': sum(self.stats['response_times']) / len(self.stats['response_times']) if self.stats['response_times'] else 0,
            'common_questions': dict(sorted(self.stats['common_questions'].items(), key=lambda item: item[1], reverse=True)[:5])
        }
        return stats
    
    def get_conversation_history(self) -> List[Dict]:
        """Отримання історії розмови"""
        return self.conversation_history
    
    def generate_daily_report(self) -> str:
        """Генерація щоденного звіту"""
        stats = self.get_statistics()
        
        report = f"""
        📊 ЩОДЕННИЙ ЗВІТ ЧАТ-БОТА
        Дата: {datetime.now().strftime('%d.%m.%Y')}
        
        Загальна статистика:
        • Загальна кількість запитів: {stats['total_questions']}
        • Кількість відповідей: {stats['answered_questions']}
        • Відсоток відповідей: {stats['answer_rate']:.1f}%
        • Середній час відповіді: {stats['avg_response_time']:.2f} сек
        
        Топ-5 популярних питань:
        """
        
        for i, (q, count) in enumerate(stats['common_questions'].items(), 1):
            report += f"{i}. {q} ({count} разів)\n"
        
        report += "\nКінець звіту."
        return report

# Глобальний екземпляр чат-бота
chatbot_instance = None

def get_chatbot():
    """Отримання глобального екземпляру чат-бота"""
    global chatbot_instance
    if chatbot_instance is None:
        from config import config
        chatbot_instance = UkrenergoChatbot(
            faq_file=str(config.DATA_DIR / 'faq.json')
        )
    return chatbot_instance
