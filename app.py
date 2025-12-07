import io
import streamlit as st
from streamlit_option_menu import option_menu
from audiorecorder import audiorecorder
import base64
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import numpy as np
import uuid

# Імпорт власних модулів
from config import config
from modules.speech_module import get_speech_module
from modules.chatbot_module import get_chatbot
from modules.energy_calculator import get_energy_calculator

# Налаштування сторінки
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ініціалізація сесії
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'tts_enabled' not in st.session_state:
    st.session_state.tts_enabled = True
if 'selected_voice' not in st.session_state:
    st.session_state.selected_voice = config.UKRAINIAN_VOICES['female']
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'last_calculation' not in st.session_state:
    st.session_state.last_calculation = None
if 'last_savings' not in st.session_state:
    st.session_state.last_savings = None
if 'audio_recorder_key' not in st.session_state:
    st.session_state.audio_recorder_key = 0
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Головна"

# Завантаження CSS
def load_css():
    """Завантаження кастомних стилів"""
    try:
        with open('assets/styles.css', 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Файл стилів assets/styles.css не знайдено.")

# Завантаження логотипу
def get_logo_base64():
    """Отримання логотипу в base64"""
    try:
        with open('assets/logo.png', 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

# Сторінки додатку
def show_home_page():
    """Головна сторінка"""
    st.title(f"⚡ {config.APP_TITLE}")
    st.markdown(f"### {config.APP_DESCRIPTION}")
    st.markdown("---")
    
    # Логотип
    logo_base64 = get_logo_base64()
    if logo_base64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_base64}" style="max-width: 200px; margin-bottom: 20px;">',
            unsafe_allow_html=True
        )
    else:
        st.header("УкрЕнерго")
    
    # Швидкі дії
    st.markdown("### Швидкі дії")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💬 Чат-бот", use_container_width=True):
            st.session_state.current_page = "Чат-бот"
            st.rerun()
    
    with col2:
        if st.button("🧮 Калькулятор", use_container_width=True):
            st.session_state.current_page = "Калькулятор"
            st.rerun()
    
    with col3:
        if st.button("📢 Оголошення", use_container_width=True):
            st.session_state.current_page = "Оголошення"
            st.rerun()
    
    with col4:
        if st.button("⚙️ Налаштування", use_container_width=True):
            st.session_state.current_page = "Налаштування"
            st.rerun()
    
    # Важлива інформація
    st.markdown("---")
    st.markdown("### ⚠️ Важлива інформація")
    
    with st.expander("📅 Графік обмежень споживання", expanded=False):
        st.info("""
        **Найближчі дні з обмеженням:**
        
        • Понеділок, 10:00-17:00
        • Середа, 09:00-15:00
        • П'ятниця, 11:00-18:00
        
        Рекомендуємо:
        1. Заряджати пристрої заздалегідь
        2. Використовувати генератори (якщо є)
        3. Відключати непотрібні прилади
        """)
    
    with st.expander("📞 Екстрені контакти", expanded=False):
        st.error(f"""
        **При аварійних ситуаціях:**
        
        🔴 **Аварійна служба:** {config.CONTACT_INFO['emergency']}
        🔴 **Гаряча лінія:** {config.CONTACT_INFO['phone']}
        🔴 **Email кризових ситуацій:** emergency@ukrenergo.ua
        
        **Графік роботи:**
        • Понеділок-П'ятниця: 8:00-20:00
        • Субота: 9:00-18:00
        • Неділя: 10:00-16:00
        """)

def show_chatbot_page():
    """Сторінка чат-бота"""
    st.title("💬 Чат-бот підтримки УкрЕнерго")
    st.markdown("---")
    
    # Ініціалізація модулів
    try:
        speech_module = get_speech_module()
        chatbot = get_chatbot()
    except Exception as e:
        st.error(f"Помилка ініціалізації: {str(e)}")
        st.info("Переконайтеся, що ключ Azure встановлено в .env файлі")
        return
    
    # Панель управління
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 💬 Задайте питання голосом або текстом")
    
    with col2:
        tts_enabled = st.checkbox(
            "🔊 Голосова відповідь", 
            value=st.session_state.tts_enabled,
            key="tts_enabled_checkbox",
            help="Увімкнути синтез мовлення для відповідей"
        )
        st.session_state.tts_enabled = tts_enabled

    # Голосовий запис через audiorecorder
    audio = audiorecorder(
        "🎤 Натисніть для запису",
        "🛑 Зупинити запис",
        key=f"recorder_{st.session_state.audio_recorder_key}"
    )

    # Обробка голосового запису
    if len(audio) > 0 and audio.duration_seconds > 0.3:
        # Конвертація до формату, підтримуваного Azure
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        buffer = io.BytesIO()
        audio.export(buffer, format="wav")
        audio_bytes = buffer.getvalue()
        
        if audio_bytes:
            with st.spinner("🎤 Розпізнаю мовлення..."):
                recognized_text = speech_module.speech_to_text(audio_data=audio_bytes)
                if recognized_text:
                    user_input = recognized_text
                    
                    # Додавання повідомлення користувача
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    
                    # Відображення історії чату перед обробкою
                    chat_container = st.container()
                    with chat_container:
                        for message in st.session_state.messages[:-1]:  # Всі крім останнього
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                                if message["role"] == "assistant" and "audio" in message:
                                    audio_html = speech_module.create_audio_player(message["audio"])
                                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Відображення нового повідомлення користувача
                    with st.chat_message("user"):
                        st.markdown(user_input)

                    # Отримання відповіді від чат-бота
                    with st.chat_message("assistant"):
                        with st.spinner("🤔 Думаю..."):
                            response = chatbot.process_message(user_input, st.session_state.user_id)
                            st.markdown(response)
                        
                        # Синтез мовлення для відповіді
                        if st.session_state.tts_enabled:
                            audio_data = speech_module.text_to_speech(
                                response,
                                voice=st.session_state.selected_voice
                            )
                            
                            if audio_data:
                                # Відтворення аудіо
                                audio_html = speech_module.create_audio_player(audio_data, autoplay=True)
                                st.markdown(audio_html, unsafe_allow_html=True)
                                
                                # Додавання відповіді бота з аудіо
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response,
                                    "audio": audio_data
                                })
                            else:
                                # Додавання відповіді бота без аудіо
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response
                                })
                        else:
                            # Додавання відповіді бота без TTS
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response
                            })
                    
                    # Очищення запису
                    st.session_state.audio_recorder_key += 1
                    st.rerun()
                else:
                    st.warning("❌ Не вдалося розпізнати мовлення.")
                    st.session_state.audio_recorder_key += 1
                    st.rerun()

    # Відображення історії чату
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Відтворення аудіо для відповідей бота
                if message["role"] == "assistant" and "audio" in message:
                    audio_html = speech_module.create_audio_player(message["audio"])
                    st.markdown(audio_html, unsafe_allow_html=True)
    
    # Введення повідомлення (текстовий ввід)
    user_input = st.chat_input("Введіть ваше питання...")
    
    # Обробка текстового повідомлення
    if user_input:
        # Додавання повідомлення користувача
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Відображення історії чату перед обробкою
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages[:-1]:  # Всі крім останнього
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if message["role"] == "assistant" and "audio" in message:
                        audio_html = speech_module.create_audio_player(message["audio"])
                        st.markdown(audio_html, unsafe_allow_html=True)
        
        # Відображення нового повідомлення користувача
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Отримання відповіді від чат-бота
        with st.chat_message("assistant"):
            with st.spinner("🤔 Думаю..."):
                response = chatbot.process_message(user_input, st.session_state.user_id)
                st.markdown(response)
            
            # Синтез мовлення для відповіді
            if st.session_state.tts_enabled:
                audio_data = speech_module.text_to_speech(
                    response,
                    voice=st.session_state.selected_voice
                )
                
                if audio_data:
                    # Відтворення аудіо
                    audio_html = speech_module.create_audio_player(audio_data, autoplay=True)
                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Додавання відповіді бота з аудіо
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "audio": audio_data
                    })
                else:
                    # Додавання відповіді бота без аудіо
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response
                    })
            else:
                # Додавання відповіді бота без TTS
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })
        st.rerun()
    
    # Панель з прикладами питань
    st.markdown("---")
    st.markdown("### 💡 Приклади питань, які можна задати:")

    # Функція для обробки прикладних питань
    def process_example_question(question):
        """Обробка прикладної кнопки питання"""
        # Додавання повідомлення користувача
        st.session_state.messages.append({"role": "user", "content": question})
        
        # Відображення історії чату перед обробкою
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages[:-1]:  # Всі крім останнього
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if message["role"] == "assistant" and "audio" in message:
                        audio_html = speech_module.create_audio_player(message["audio"])
                        st.markdown(audio_html, unsafe_allow_html=True)
        
        # Відображення нового повідомлення користувача
        with st.chat_message("user"):
            st.markdown(question)
        
        # Отримання відповіді від чат-бота
        with st.chat_message("assistant"):
            with st.spinner("🤔 Думаю..."):
                response = chatbot.process_message(question, st.session_state.user_id)
                st.markdown(response)
            
            # Синтез мовлення для відповіді
            if st.session_state.tts_enabled:
                audio_data = speech_module.text_to_speech(
                    response,
                    voice=st.session_state.selected_voice
                )
                
                if audio_data:
                    # Відтворення аудіо
                    audio_html = speech_module.create_audio_player(audio_data, autoplay=True)
                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Додавання відповіді бота з аудіо
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "audio": audio_data
                    })
                else:
                    # Додавання відповіді бота без аудіо
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response
                    })
            else:
                # Додавання відповіді бота без TTS
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })
        st.rerun()

    col1, col2 = st.columns(2)
    
    # Кнопки прикладних питань
    with col1:
        if st.button("Як оплатити рахунок?", use_container_width=True):
            process_example_question("Як оплатити рахунок?")
        
        if st.button("Що робити при відключенні світла?", use_container_width=True):
            process_example_question("Що робити при відключенні світла?")
        
        if st.button("Які діють тарифи?", use_container_width=True):
            process_example_question("Які діють тарифи?")
    
    with col2:
        if st.button("Як передати показники лічильника?", use_container_width=True):
            process_example_question("Як передати показники лічильника?")
        
        if st.button("Як підключити нове приміщення?", use_container_width=True):
            process_example_question("Як підключити нове приміщення?")
        
        if st.button("Що таке обмеження споживання?", use_container_width=True):
            process_example_question("Що таке обмеження споживання?")

def show_calculator_page():
    """Сторінка калькулятора споживання"""
    st.title("🧮 Калькулятор споживання електроенергії")
    st.markdown("---")
    
    try:
        calculator = get_energy_calculator()
    except Exception as e:
        st.error(f"Помилка ініціалізації калькулятора: {str(e)}")
        return
    
    # Вкладки
    tab1, tab2, tab3 = st.tabs(["📊 Розрахунок споживання", "💰 Економія", "📈 Звіт"])
    
    with tab1:
        st.markdown("### Оцінка споживання електроенергії")
        
        # Налаштування приладів
        st.markdown("#### Налаштуйте параметри ваших приладів:")
        
        appliances_data = calculator.appliance_consumption.copy()
        
        # Створення колонок для приладів
        cols = st.columns(3)
        col_index = 0
        
        # Використання st.session_state для збереження стану форми
        if 'appliance_state' not in st.session_state:
            st.session_state.appliance_state = appliances_data
        
        for appliance, data in appliances_data.items():
            with cols[col_index]:
                st.markdown(f"**{appliance}**")
                
                # Кількість
                quantity = st.number_input(
                    f"Кількість ({appliance})",
                    min_value=0,
                    max_value=10,
                    value=int(st.session_state.appliance_state.get(appliance, {}).get('quantity', data['quantity'])),
                    key=f"qty_{appliance}"
                )
                
                # Години роботи
                hours = st.slider(
                    f"Годин на день ({appliance})",
                    min_value=0.0,
                    max_value=24.0,
                    value=float(st.session_state.appliance_state.get(appliance, {}).get('hours_per_day', data['hours_per_day'])),
                    step=0.5,
                    key=f"hours_{appliance}"
                )
                
                # Потужність
                power_options = sorted(list(set([data['power'], data['power']//2, data['power']*2])))
                power = st.selectbox(
                    f"Потужність, Вт ({appliance})",
                    options=power_options,
                    index=power_options.index(data['power']),
                    key=f"power_{appliance}"
                )
                
                # Оновлення даних
                st.session_state.appliance_state[appliance] = {
                    'power': power,
                    'hours_per_day': hours,
                    'quantity': quantity
                }
            
            col_index = (col_index + 1) % 3
        
        # Кнопка розрахунку
        if st.button("🧮 Розрахувати споживання", type="primary", use_container_width=True):
            with st.spinner("Розраховую..."):
                # Розрахунок споживання
                consumption = calculator.calculate_monthly_consumption(st.session_state.appliance_state)
                
                # Відображення результатів
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Загальне споживання", f"{consumption['total_kwh']} кВт·год")
                
                with col2:
                    st.metric("Загальна вартість", f"{consumption['total_cost']} грн")
                
                with col3:
                    st.metric("Денна вартість", f"{consumption['day_cost']} грн")
                
                with col4:
                    st.metric("Нічна вартість", f"{consumption['night_cost']} грн")
                
                # Графік споживання
                chart = calculator.create_consumption_chart(consumption)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                
                # Таблиця деталей
                st.markdown("#### Деталізація по приладах:")
                
                df = pd.DataFrame(consumption['appliances'])
                st.dataframe(
                    df,
                    column_config={
                        "appliance": "Прилад",
                        "power_w": "Потужність (Вт)",
                        "hours_per_day": "Годин/день",
                        "quantity": "Кількість",
                        "monthly_kwh": "кВт·год/міс",
                        "monthly_cost": "грн/міс"
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Збереження результатів
                st.session_state.last_calculation = consumption
    
    with tab2:
        st.markdown("### Розрахунок потенційної економії")
        
        if st.session_state.last_calculation is None:
            st.info("Спочатку виконайте розрахунок споживання у вкладці 'Розрахунок споживання'")
        else:
            consumption = st.session_state.last_calculation
            
            # Генерація рекомендацій
            recommendations = calculator.generate_recommendations(consumption)
            
            # Розрахунок економії
            savings = calculator.calculate_savings(consumption['total_kwh'], recommendations)
            
            # Відображення результатів
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Потенційна економія", f"{savings['total_savings_cost']} грн/міс")
            
            with col2:
                st.metric("Економія кВт·год", f"{savings['total_savings_kwh']} кВт·год")
            
            with col3:
                st.metric("Відсоток економії", f"{savings['savings_percent']}%")
            
            # Графік економії
            chart = calculator.create_savings_chart(savings)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            # Таблиця рекомендацій
            st.markdown("#### Деталізація рекомендацій:")
            
            df_savings = pd.DataFrame(savings['recommendations'])
            st.dataframe(
                df_savings,
                column_config={
                    "recommendation": "Рекомендація",
                    "savings_percent": "Економія (%)",
                    "savings_kwh": "Економія (кВт·год/міс)",
                    "savings_cost": "Економія (грн/міс)",
                    "investment": "Інвестиції (грн)",
                    "roi_months": "Окупність (міс)"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Збереження результатів
            st.session_state.last_savings = savings
            
    with tab3:
        st.markdown("### Місячний звіт")
        
        if st.session_state.last_calculation is None:
            st.info("Спочатку виконайте розрахунок споживання у вкладці 'Розрахунок споживання'")
        else:
            # Генерація звіту
            report = calculator.generate_monthly_report(st.session_state.last_calculation)
            
            st.text_area("Звіт", report, height=500)
            
            # Кнопка завантаження
            st.download_button(
                label="⬇️ Завантажити звіт (TXT)",
                data=report,
                file_name=f"ukrenergo_monthly_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

def show_announcements_page():
    """Сторінка оголошень"""
    st.title("📢 Генератор голосових оголошень")
    st.markdown("---")
    
    try:
        speech_module = get_speech_module()
    except Exception as e:
        st.error(f"Помилка ініціалізації: {str(e)}")
        return
    
    # Генерація стандартних оголошень
    st.markdown("### 1. Стандартні оголошення")
    
    announcement_type = st.selectbox(
        "Оберіть тип оголошення:",
        ["welcome", "payment_reminder", "emergency", "tariff_change", "meter_reading"],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    # Тексти для стандартних оголошень
    announcement_texts = {
        "welcome": "Ласкаво просимо до УкрЕнерго! Ваш надійний партнер у сфері електропостачання. Завжди раді допомогти!",
        "payment_reminder": "",
        "emergency": "",
        "tariff_change": "",
        "meter_reading": "Шановні клієнти, нагадуємо про необхідність передати показники лічильника до 25 числа поточного місяця. Дякуємо за співпрацю!"
    }
    
    # Динамічні параметри для оголошень
    kwargs = {}
    announcement_text = announcement_texts.get(announcement_type, "")
    
    if announcement_type == "payment_reminder":
        date = st.date_input("Дата оплати:", datetime.now().date())
        amount = st.number_input("Сума до оплати (грн):", min_value=0.0, value=150.50)
        announcement_text = f"Шановні клієнти, нагадуємо про необхідність оплатити рахунок за електроенергію до {date.strftime('%d.%m.%Y')}. Сума до оплати: {amount} гривень. Дякуємо!"
        kwargs = {"date": date.strftime('%d.%m.%Y'), "amount": str(amount)}
    elif announcement_type == "emergency":
        area = st.text_input("Район/Область:", "Київська область")
        start = st.time_input("Початок робіт:", datetime.now().time())
        end = st.time_input("Кінець робіт:", datetime.now().time())
        announcement_text = f"Увага! У {area} заплановані аварійні роботи на лініях електропередач з {start.strftime('%H:%M')} до {end.strftime('%H:%M')}. Можливі тимчасові перебої з електропостачанням. Приносимо вибачення за незручності."
        kwargs = {"area": area, "start": start.strftime('%H:%M'), "end": end.strftime('%H:%M')}
    elif announcement_type == "tariff_change":
        date = st.date_input("Дата зміни тарифів:", datetime.now().date())
        day_rate = st.number_input("Новий денний тариф:", min_value=0.0, value=2.64)
        night_rate = st.number_input("Новий нічний тариф:", min_value=0.0, value=1.32)
        announcement_text = f"Шановні клієнти, повідомляємо про зміну тарифів на електроенергію з {date.strftime('%d.%m.%Y')}. Новий денний тариф: {day_rate} гривень за кіловат-годину, нічний тариф: {night_rate} гривень за кіловат-годину."
        kwargs = {"date": date.strftime('%d.%m.%Y'), "day_rate": str(day_rate), "night_rate": str(night_rate)}
    
    # Показати текст оголошення
    if announcement_text:
        st.text_area("Текст оголошення:", announcement_text, height=100, key="announcement_text_preview")
        
    if st.button("🔊 Згенерувати та озвучити стандартне оголошення", use_container_width=True):
        if announcement_text:
            with st.spinner("Генерую аудіо..."):
                # ВИПРАВЛЕНО: використовуємо text_to_speech замість generate_announcement
                audio_data = speech_module.text_to_speech(
                    announcement_text,
                    voice=st.session_state.selected_voice
                )
                
                if audio_data:
                    audio_html = speech_module.create_audio_player(audio_data, autoplay=True)
                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Кнопка завантаження
                    st.download_button(
                        label="⬇️ Завантажити аудіо (WAV)",
                        data=audio_data,
                        file_name=f"{announcement_type}_announcement_{datetime.now().strftime('%H%M%S')}.wav",
                        mime="audio/wav",
                        use_container_width=True
                    )
                else:
                    st.error("Не вдалося згенерувати аудіо.")
        else:
            st.warning("Оберіть тип оголошення та заповніть необхідні поля.")
    
    st.markdown("---")
    
    # Генерація кастомного оголошення
    st.markdown("### 2. Кастомне оголошення")
    
    custom_text = st.text_area(
        "Введіть текст для озвучення:",
        "Шановні клієнти, у зв'язку з погодними умовами можливі тимчасові перебої в електропостачанні. Приносимо вибачення за незручності."
    )
    
    if st.button("🔊 Згенерувати та озвучити кастомне оголошення", type="primary", use_container_width=True):
        if custom_text:
            with st.spinner("Генерую аудіо..."):
                audio_data = speech_module.text_to_speech(
                    custom_text,
                    voice=st.session_state.selected_voice
                )
                
                if audio_data:
                    audio_html = speech_module.create_audio_player(audio_data, autoplay=True)
                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Кнопка завантаження
                    st.download_button(
                        label="⬇️ Завантажити аудіо (WAV)",
                        data=audio_data,
                        file_name=f"custom_announcement_{datetime.now().strftime('%H%M%S')}.wav",
                        mime="audio/wav",
                        use_container_width=True
                    )
                else:
                    st.error("Не вдалося згенерувати аудіо.")
        else:
            st.warning("Введіть текст оголошення")

def show_analytics_page():
    """Сторінка аналітики"""
    st.title("📈 Аналітика та звіти")
    st.markdown("---")
    
    try:
        chatbot = get_chatbot()
        speech_module = get_speech_module()
    except Exception as e:
        st.error(f"Помилка ініціалізації: {str(e)}")
        return
    
    # Вкладки
    tab1, tab2, tab3 = st.tabs(["📊 Статистика", "📝 Звіти", "📁 Експорт"])
    
    with tab1:
        st.markdown("### Статистика роботи системи")
        
        # Статистика чат-бота
        bot_stats = chatbot.get_statistics()
        speech_stats = speech_module.get_usage_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Загальна кількість запитів", bot_stats.get('total_questions', 0))
        
        with col2:
            st.metric("Відсоток відповідей", f"{bot_stats.get('answer_rate', 0):.1f}%")
        
        with col3:
            st.metric("TTS запитів", speech_stats.get('tts_requests', 0))
        
        with col4:
            st.metric("STT запитів", speech_stats.get('stt_requests', 0))
        
        # Графіки
        st.markdown("---")
        st.markdown("#### Графіки активності")
        
        # Створення тестових даних для демонстрації
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        questions = np.random.randint(10, 50, size=len(dates))
        response_times = np.random.uniform(0.5, 2.5, size=len(dates))
        
        df = pd.DataFrame({
            'Дата': dates,
            'Запити': questions,
            'Час відповіді (сек)': response_times
        })
        
        # Графік запитів
        fig1 = px.line(
            df, 
            x='Дата', 
            y='Запити',
            title='Кількість запитів по дням'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Графік часу відповіді
        fig2 = px.bar(
            df,
            x='Дата',
            y='Час відповіді (сек)',
            title='Середній час відповіді'
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Топ популярних питань
        st.markdown("---")
        st.markdown("#### Популярні питання")
        
        # Створення тестових даних
        popular_questions = [
            {"question": q, "count": c} for q, c in bot_stats.get('common_questions', {}).items()
        ]
        if not popular_questions:
            popular_questions = [
                {"question": "Як оплатити рахунок?", "count": 45},
                {"question": "Що робити при відключенні?", "count": 38},
                {"question": "Які діють тарифи?", "count": 32},
                {"question": "Як передати показники?", "count": 28},
                {"question": "Графік обмежень?", "count": 25}
            ]
        
        df_popular = pd.DataFrame(popular_questions)
        fig3 = px.bar(
            df_popular,
            x='count',
            y='question',
            orientation='h',
            title='Найпопулярніші питання'
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab2:
        st.markdown("### Генерація звітів")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Тип звіту",
                ["Щоденний", "Тижневий", "Місячний", "Квартальний"]
            )
        
        with col2:
            date_range = st.date_input(
                "Період",
                value=(datetime.now().date(), datetime.now().date())
            )
        
        if st.button("📄 Згенерувати звіт", type="primary", use_container_width=True):
            with st.spinner("Генерую звіт..."):
                # Генерація звіту чат-бота
                bot_report = chatbot.generate_daily_report()
                
                # Відображення звіту
                st.markdown("#### Звіт чат-бота:")
                st.text_area("Звіт", bot_report, height=300)
                
                # Кнопка озвучення
                if st.button("🔊 Озвучити звіт", use_container_width=True):
                    audio_data = speech_module.text_to_speech(
                        bot_report[:1000] + "... (звіт скорочено)",
                        voice=st.session_state.selected_voice
                    )
                    
                    if audio_data:
                        audio_html = speech_module.create_audio_player(audio_data, autoplay=True)
                        st.markdown(audio_html, unsafe_allow_html=True)
                    else:
                        st.error("Не вдалося згенерувати аудіо.")
    
    with tab3:
        st.markdown("### Експорт даних")
        
        export_options = st.multiselect(
            "Оберіть дані для експорту:",
            ["Історія чату", "Статистика", "Аудіофайли", "Звіти"],
            default=["Історія чату"]
        )
        
        export_format = st.radio(
            "Формат експорту:",
            ["JSON", "CSV", "TXT"]
        )
        
        if st.button("📤 Експортувати дані", type="primary", use_container_width=True):
            with st.spinner("Готую дані для експорту..."):
                export_data = {}
                
                if "Історія чату" in export_options:
                    export_data['chat_history'] = chatbot.get_conversation_history()
                
                if "Статистика" in export_options:
                    export_data['statistics'] = {
                        'bot': chatbot.get_statistics(),
                        'speech': speech_module.get_usage_statistics()
                    }
                
                if export_format == "JSON":
                    data_str = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
                    mime_type = "application/json"
                    file_ext = "json"
                elif export_format == "CSV":
                    # Спрощений експорт у CSV
                    data_str = "Категорія,Значення\n"
                    for key, value in export_data.get('statistics', {}).get('bot', {}).items():
                        if isinstance(value, (int, float, str)):
                            data_str += f"{key},{value}\n"
                    mime_type = "text/csv"
                    file_ext = "csv"
                else:
                    data_str = str(export_data)
                    mime_type = "text/plain"
                    file_ext = "txt"
                
                st.download_button(
                    label=f"⬇️ Завантажити ({export_format})",
                    data=data_str,
                    file_name=f"ukrenergo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
                    mime=mime_type,
                    use_container_width=True
                )

def show_settings_page():
    """Сторінка налаштувань"""
    st.title("⚙️ Налаштування системи")
    st.markdown("---")
    
    try:
        speech_module = get_speech_module()
    except Exception as e:
        st.error(f"Помилка ініціалізації: {str(e)}")
        return
    
    # Налаштування голосу
    st.markdown("### 🎵 Налаштування голосу")
    
    col1, col2 = st.columns(2)
    
    with col1:
        voices = speech_module.get_available_voices("uk-UA")
        
        if voices:
            voice_options = {v['local_name']: v['name'] for v in voices}
            
            current_voice_name = next((k for k, v in voice_options.items() if v == st.session_state.selected_voice), list(voice_options.keys())[0])
            
            selected_voice_name = st.selectbox(
                "Оберіть голос:",
                options=list(voice_options.keys()),
                index=list(voice_options.keys()).index(current_voice_name)
            )
            
            selected_voice = voice_options[selected_voice_name]
            st.session_state.selected_voice = selected_voice
            
            for voice in voices:
                if voice['name'] == selected_voice:
                    st.markdown(f"**Гендер:** {voice['gender']}")
                    st.markdown(f"**Мова:** {voice['locale']}")
        
        test_text = st.text_input(
            "Текст для тесту:",
            value="Це тестовий голос українською мовою."
        )
        
        if st.button("▶️ Протестувати голос", use_container_width=True):
            audio_data = speech_module.text_to_speech(
                test_text,
                voice=st.session_state.selected_voice
            )
            
            if audio_data:
                audio_html = speech_module.create_audio_player(audio_data, autoplay=True)
                st.markdown(audio_html, unsafe_allow_html=True)
            else:
                st.error("Не вдалося згенерувати аудіо.")
    
    with col2:
        rate = st.slider("Швидкість:", min_value=-50, max_value=50, value=0)
        pitch = st.slider("Висота тону:", min_value=-50, max_value=50, value=0)
        volume = st.slider("Гучність:", min_value=50, max_value=150, value=100)
        
        if st.button("💾 Зберегти налаштування", type="primary", use_container_width=True):
            st.success("Налаштування збережено!")

    st.markdown("---")
    st.markdown("### ⚙️ Налаштування додатку")
    
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox("Мова інтерфейсу:", options=list(config.SUPPORTED_LANGUAGES.values()), index=0)
        auto_play = st.checkbox("Автоматично відтворювати аудіо-відповіді", value=True)
        save_audio = st.checkbox("Зберігати аудіо-відповіді на сервері", value=False)
        debug_mode = st.checkbox("Режим налагодження (показувати технічну інформацію)", value=False)
        if debug_mode:
            st.json(st.session_state)
    
    with col2:
        theme = st.selectbox("Тема оформлення:", options=["Світла", "Темна", "Системна"], index=0)
        font_size = st.slider("Розмір шрифту:", min_value=12, max_value=20, value=14)
        
        if st.button("🗑️ Скинути всі налаштування", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Налаштування скинуто. Перезавантажте сторінку.")

# Головна функція
def main():
    """Головна функція додатку"""
    load_css()
    
    # Бічна панель
    with st.sidebar:
        try:
            st.image("assets/logo.png", width=100)
        except:
            st.title("⚡ УкрЕнерго")
        st.title(config.APP_TITLE)
        
        # Меню - ПРОСТИЙ ВАРІАНТ: використовуємо st.radio для надійності
        menu_options = ["Головна", "Чат-бот", "Калькулятор", "Оголошення", "Аналітика", "Налаштування"]
        
        selected_page = st.radio(
            "Навігація",
            menu_options,
            index=menu_options.index(st.session_state.current_page),
            label_visibility="collapsed"
        )
        
        # Оновлюємо поточну сторінку
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()
        
        # Інформація про версію
        st.markdown("---")
        st.markdown(f"**Версія:** 1.0.0")
        st.markdown(f"**Розробник:** УкрЕнерго AI")
        st.markdown(f"**Контакти:** {config.CONTACT_INFO['email']}")
    
    # Відображення обраної сторінки
    if st.session_state.current_page == "Головна":
        show_home_page()
    elif st.session_state.current_page == "Чат-бот":
        show_chatbot_page()
    elif st.session_state.current_page == "Калькулятор":
        show_calculator_page()
    elif st.session_state.current_page == "Оголошення":
        show_announcements_page()
    elif st.session_state.current_page == "Аналітика":
        show_analytics_page()
    elif st.session_state.current_page == "Налаштування":
        show_settings_page()

if __name__ == "__main__":
    main()