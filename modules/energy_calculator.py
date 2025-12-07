"""
Модуль для розрахунку споживання електроенергії та економії
"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class EnergyCalculator:
    """Калькулятор споживання та економії електроенергії"""
    
    def __init__(self, tariffs: Dict[str, float]):
        """
        Ініціалізація калькулятора
        
        Args:
            tariffs: Словник з тарифами
        """
        self.tariffs = tariffs
        
        # Базове споживання приладів (Вт, годин/день, кількість)
        self.appliance_consumption = {
            "Холодильник": {"power": 150, "hours_per_day": 24, "quantity": 1},
            "Лампи LED": {"power": 10, "hours_per_day": 5, "quantity": 10},
            "Комп'ютер/Ноутбук": {"power": 100, "hours_per_day": 8, "quantity": 1},
            "Телевізор": {"power": 80, "hours_per_day": 4, "quantity": 1},
            "Пральна машина": {"power": 2000, "hours_per_day": 0.5, "quantity": 1},
            "Електрочайник": {"power": 2200, "hours_per_day": 0.1, "quantity": 1},
            "Бойлер": {"power": 2000, "hours_per_day": 2, "quantity": 1}
        }
    
    def calculate_monthly_consumption(self, custom_appliances: Optional[Dict] = None) -> Dict:
        """
        Розрахунок місячного споживання та вартості
        
        Args:
            custom_appliances: Кастомні дані про прилади
            
        Returns:
            Словник з результатами розрахунку
        """
        appliances_data = custom_appliances if custom_appliances is not None else self.appliance_consumption
        
        total_kwh = 0
        total_cost = 0
        day_cost = 0
        night_cost = 0
        
        results = []
        
        # Приймаємо 30 днів у місяці
        DAYS_IN_MONTH = 30
        
        for appliance, data in appliances_data.items():
            power_w = data['power']
            hours_per_day = data['hours_per_day']
            quantity = data['quantity']
            
            if quantity == 0:
                continue
            
            # Споживання за місяць (кВт·год)
            monthly_kwh = (power_w * hours_per_day * DAYS_IN_MONTH * quantity) / 1000
            
            # Спрощений розрахунок вартості (припускаємо, що 70% споживання - денний тариф, 30% - нічний)
            # Денний тариф: 7:00 - 23:00 (16 годин)
            # Нічний тариф: 23:00 - 7:00 (8 годин)
            
            # Якщо годин на день менше 8, припускаємо, що це денне споживання
            if hours_per_day <= 8:
                day_kwh = monthly_kwh
                night_kwh = 0
            else:
                # Складніший розрахунок, але для спрощення візьмемо 70/30
                day_kwh = monthly_kwh * 0.7
                night_kwh = monthly_kwh * 0.3
            
            day_rate = self.tariffs.get('residential_day', 2.64)
            night_rate = self.tariffs.get('residential_night', 1.32)
            
            monthly_day_cost = day_kwh * day_rate
            monthly_night_cost = night_kwh * night_rate
            monthly_cost = monthly_day_cost + monthly_night_cost
            
            total_kwh += monthly_kwh
            total_cost += monthly_cost
            day_cost += monthly_day_cost
            night_cost += monthly_night_cost
            
            results.append({
                'appliance': appliance,
                'power_w': power_w,
                'hours_per_day': hours_per_day,
                'quantity': quantity,
                'monthly_kwh': round(monthly_kwh, 2),
                'monthly_cost': round(monthly_cost, 2)
            })
        
        return {
            'total_kwh': round(total_kwh, 2),
            'total_cost': round(total_cost, 2),
            'day_cost': round(day_cost, 2),
            'night_cost': round(night_cost, 2),
            'appliances': results
        }
    
    def calculate_savings(self, current_kwh: float, 
                         recommendations: list) -> dict:
        """
        Розрахунок потенційної економії
        
        Args:
            current_kwh: Поточне споживання (кВт·год/міс)
            recommendations: Список рекомендацій
            
        Returns:
            Словник з розрахунками економії
        """
        savings_data = []
        total_savings_kwh = 0
        total_savings_cost = 0
        
        for rec in recommendations:
            savings_percent = rec.get('savings_percent', 0) / 100
            savings_kwh = current_kwh * savings_percent
            savings_cost = savings_kwh * self.tariffs.get('residential_day', 2.64)
            
            # Обмеження економії до 100%
            if savings_kwh > current_kwh:
                savings_kwh = current_kwh
                savings_cost = current_kwh * self.tariffs.get('residential_day', 2.64)
            
            roi_months = 0
            if savings_cost > 0:
                roi_months = round(rec.get('investment', 0) / savings_cost, 1)
            
            savings_data.append({
                'recommendation': rec.get('text', ''),
                'savings_percent': rec.get('savings_percent', 0),
                'savings_kwh': round(savings_kwh, 2),
                'savings_cost': round(savings_cost, 2),
                'investment': rec.get('investment', 0),
                'roi_months': roi_months
            })
            
            total_savings_kwh += savings_kwh
            total_savings_cost += savings_cost
        
        # Обмеження загальної економії
        if total_savings_kwh > current_kwh:
            total_savings_kwh = current_kwh
            total_savings_cost = current_kwh * self.tariffs.get('residential_day', 2.64)
        
        return {
            'current_kwh': current_kwh,
            'total_savings_kwh': round(total_savings_kwh, 2),
            'total_savings_cost': round(total_savings_cost, 2),
            'new_kwh': round(current_kwh - total_savings_kwh, 2),
            'savings_percent': round((total_savings_kwh / current_kwh) * 100, 1) if current_kwh > 0 else 0,
            'recommendations': savings_data
        }
    
    def generate_recommendations(self, consumption_data: dict) -> list:
        """
        Генерація рекомендацій щодо економії
        
        Args:
            consumption_data: Дані про споживання
            
        Returns:
            Список рекомендацій
        """
        recommendations = []
        
        # Аналіз споживання приладів
        for appliance in consumption_data.get('appliances', []):
            if appliance['monthly_kwh'] > 50:  # Прилади з високим споживанням
                rec_text = f"Замініть {appliance['appliance']} на енергоефективну модель"
                recommendations.append({
                    'text': rec_text,
                    'savings_percent': 30,
                    'investment': 5000
                })
        
        # Загальні рекомендації
        general_recommendations = [
            {
                'text': "Встановіть LED освітлення замість ламп розжарювання",
                'savings_percent': 5,
                'investment': 1000
            },
            {
                'text': "Використовуйте техніку в нічний час (після 23:00)",
                'savings_percent': 15,
                'investment': 0
            },
            {
                'text': "Встановіть програматор для обігрівача/бойлера",
                'savings_percent': 10,
                'investment': 1500
            },
            {
                'text': "Відключайте прилади від мережі в режимі очікування",
                'savings_percent': 3,
                'investment': 0
            },
            {
                'text': "Встановіть сонячні панелі (3 кВт система)",
                'savings_percent': 40,
                'investment': 80000
            }
        ]
        
        recommendations.extend(general_recommendations)
        return recommendations
    
    def create_consumption_chart(self, consumption_data: dict):
        """
        Створення графіка споживання
        
        Args:
            consumption_data: Дані про споживання
            
        Returns:
            Plotly Figure
        """
        appliances = consumption_data.get('appliances', [])
        
        if not appliances:
            return None
        
        # Підготовка даних для графіка
        names = [app['appliance'] for app in appliances]
        values = [app['monthly_kwh'] for app in appliances]
        costs = [app['monthly_cost'] for app in appliances]
        
        # Створення графіка
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Споживання (кВт·год/міс)', 'Вартість (грн/міс)'),
            specs=[[{'type': 'pie'}, {'type': 'pie'}]]
        )
        
        # Графік споживання
        fig.add_trace(
            go.Pie(
                labels=names,
                values=values,
                hole=0.4,
                textinfo='label+percent',
                marker=dict(colors=px.colors.qualitative.Set3)
            ),
            row=1, col=1
        )
        
        # Графік вартості
        fig.add_trace(
            go.Pie(
                labels=names,
                values=costs,
                hole=0.4,
                textinfo='label+value',
                marker=dict(colors=px.colors.qualitative.Pastel)
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title_text="Аналіз споживання електроенергії",
            showlegend=False,
            height=500
        )
        
        return fig
    
    def create_savings_chart(self, savings_data: dict):
        """
        Створення графіка потенційної економії
        
        Args:
            savings_data: Дані про економію
            
        Returns:
            Plotly Figure
        """
        recommendations = savings_data.get('recommendations', [])
        
        if not recommendations:
            return None
        
        # Підготовка даних
        labels = [rec['recommendation'][:30] + '...' for rec in recommendations]
        savings = [rec['savings_cost'] for rec in recommendations]
        roi = [rec['roi_months'] for rec in recommendations]
        
        # Графік економії
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Щомісячна економія (грн)', 'Термін окупності (місяці)'),
            vertical_spacing=0.15
        )
        
        # Графік економії
        fig.add_trace(
            go.Bar(
                x=labels,
                y=savings,
                marker_color='green',
                text=savings,
                textposition='auto'
            ),
            row=1, col=1
        )
        
        # Графік ROI
        fig.add_trace(
            go.Bar(
                x=labels,
                y=roi,
                marker_color='blue',
                text=[f"{r} міс." for r in roi],
                textposition='auto'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title_text="Потенційна економія електроенергії",
            showlegend=False,
            height=600
        )
        
        fig.update_xaxes(tickangle=45)
        
        return fig
    
    def generate_monthly_report(self, user_data: dict) -> str:
        """
        Генерація місячного звіту
        
        Args:
            user_data: Дані користувача
            
        Returns:
            Текст звіту
        """
        consumption = self.calculate_monthly_consumption()
        savings = self.calculate_savings(
            consumption['total_kwh'],
            self.generate_recommendations(consumption)
        )
        
        report = f"""
        📈 МІСЯЧНИЙ ЗВІТ ПО СПОЖИВАННЮ
        Дата: {datetime.now().strftime('%d.%m.%Y')}
        
        Загальне споживання:
        • Загальне споживання: {consumption['total_kwh']} кВт·год
        • Вартість: {consumption['total_cost']} грн
        • Денна вартість: {consumption['day_cost']} грн
        • Нічна вартість: {consumption['night_cost']} грн
        
        Топ-5 приладів за споживанням:
        """
        
        # Сортування приладів за споживанням
        sorted_appliances = sorted(
            consumption['appliances'],
            key=lambda x: x['monthly_kwh'],
            reverse=True
        )[:5]
        
        for i, appliance in enumerate(sorted_appliances, 1):
            report += f"{i}. {appliance['appliance']}: {appliance['monthly_kwh']} кВт·год ({appliance['monthly_cost']} грн)\n"
        
        report += f"""
        
        Потенційна економія:
        • Можлива економія: {savings['total_savings_kwh']} кВт·год ({savings['savings_percent']}%)
        • Грошова економія: {savings['total_savings_cost']} грн/міс
        • Нове споживання: {savings['new_kwh']} кВт·год
        
        Рекомендації:
        """
        
        for i, rec in enumerate(savings['recommendations'][:3], 1):
            report += f"{i}. {rec['recommendation']}\n   Економія: {rec['savings_cost']} грн/міс, ROI: {rec['roi_months']} міс.\n"
        
        return report


# Глобальний екземпляр калькулятора
energy_calculator = None

def get_energy_calculator():
    """Отримання глобального екземпляру калькулятора"""
    global energy_calculator
    if energy_calculator is None:
        from config import config
        energy_calculator = EnergyCalculator(config.TARIFFS)
    return energy_calculator
