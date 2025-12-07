"""
Тести для модулю chatbot_module.py
"""

import unittest
from unittest.mock import MagicMock, patch
from modules.chatbot_module import UkrenergoChatbot
import json
import os

# Створення фіктивного файлу FAQ
FAQ_CONTENT = {
  "categories": {
    "payments": "Оплата та рахунки",
    "emergency": "Аварії та відключення"
  },
  "questions": [
    {
      "id": 1,
      "question": "Як оплатити рахунок?",
      "answer": "Ви можете оплатити рахунок через Приват24.",
      "category": "payments",
      "keywords": ["оплата", "рахунок"]
    },
    {
      "id": 2,
      "question": "Що робити при відключенні?",
      "answer": "При аварійному відключенні зателефонуйте на гарячу лінію 104.",
      "category": "emergency",
      "keywords": ["відключення", "аварія"]
    }
  ]
}

class TestUkrenergoChatbot(unittest.TestCase):
    
    def setUp(self):
        # Створення тимчасового файлу FAQ
        self.faq_file = "test_faq.json"
        with open(self.faq_file, 'w', encoding='utf-8') as f:
            json.dump(FAQ_CONTENT, f, ensure_ascii=False)
        
        # Мокуємо Streamlit session_state
        with patch('modules.chatbot_module.st') as mock_st:
            mock_st.session_state = {}
            self.chatbot = UkrenergoChatbot(faq_file=self.faq_file)
    
    def tearDown(self):
        # Видалення тимчасового файлу
        os.remove(self.faq_file)
    
    def test_load_faq(self):
        self.assertEqual(len(self.chatbot.faq_data['questions']), 2)
        self.assertEqual(self.chatbot.faq_data['questions'][0]['question'], "Як оплатити рахунок?")
    
    def test_normalize_text(self):
        text = "Привіт, як справи? (Тест)"
        normalized = self.chatbot._normalize_text(text)
        self.assertEqual(normalized, "привіт як справи тест")
    
    def test_detect_intent_greeting(self):
        intent = self.chatbot._detect_intent("Привіт, бот")
        self.assertEqual(intent, 'greeting')
    
    def test_detect_intent_payment(self):
        intent = self.chatbot._detect_intent("Хочу оплатити рахунок")
        self.assertEqual(intent, 'payment')
    
    def test_detect_intent_unknown(self):
        intent = self.chatbot._detect_intent("Яка погода сьогодні?")
        self.assertEqual(intent, 'unknown')
    
    def test_search_faq_by_keyword(self):
        response = self.chatbot._search_faq("Мені потрібна інформація про аварію")
        self.assertIn("гарячу лінію 104", response)
    
    def test_search_faq_by_question(self):
        response = self.chatbot._search_faq("як оплатити рахунок")
        self.assertIn("Приват24", response)
    
    def test_process_message_faq(self):
        response = self.chatbot.process_message("Що робити при відключенні?")
        self.assertIn("гарячу лінію 104", response)
        self.assertEqual(self.chatbot.stats['total_questions'], 1)
        self.assertEqual(self.chatbot.stats['answered_questions'], 1)
    
    def test_process_message_intent(self):
        response = self.chatbot.process_message("Привіт")
        self.assertIn("Доброго дня", response)
        self.assertEqual(self.chatbot.stats['total_questions'], 1)
        self.assertEqual(self.chatbot.stats['answered_questions'], 1)
    
    def test_process_message_fallback(self):
        response = self.chatbot.process_message("Яка сьогодні температура?")
        self.assertIn("Вибачте", response)
        self.assertEqual(self.chatbot.stats['total_questions'], 1)
        self.assertEqual(self.chatbot.stats['answered_questions'], 0)
    
    def test_get_statistics(self):
        self.chatbot.process_message("Привіт")
        self.chatbot.process_message("як оплатити рахунок")
        self.chatbot.process_message("Яка сьогодні температура?")
        
        stats = self.chatbot.get_statistics()
        self.assertEqual(stats['total_questions'], 3)
        self.assertEqual(stats['answered_questions'], 2)
        self.assertAlmostEqual(stats['answer_rate'], 66.666, places=2)
        self.assertGreater(stats['avg_response_time'], 0)
        self.assertIn('привіт', stats['common_questions'])

if __name__ == '__main__':
    unittest.main()
