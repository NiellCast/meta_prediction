"""
Serviço de previsão usando apenas bibliotecas padrão do Python
Implementa regressão linear simples sem dependências externas
"""
import sqlite3
import math
from datetime import datetime, timedelta

class ForecastEngine:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
    
    def get_balance_data(self, user_id):
        """Obtém dados de saldo para análise"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, balance FROM daily_balances 
            WHERE user_id = ? 
            ORDER BY date
        ''', (user_id,))
        
        data = cursor.fetchall()
        conn.close()
        
        return data
    
    def linear_regression(self, x_values, y_values):
        """Implementa regressão linear simples"""
        if len(x_values) < 2:
            return None, None
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        # Calcular coeficientes da regressão linear (y = ax + b)
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return None, None
        
        a = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - a * sum_x) / n
        
        return a, b
    
    def predict_goal_date(self, user_id, goal_amount):
        """Prevê quando a meta será alcançada usando regressão linear"""
        try:
            data = self.get_balance_data(user_id)
            
            if len(data) < 2:
                return None, "Dados insuficientes para previsão"
            
            # Converter datas para números (dias desde a primeira data)
            dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in data]
            balances = [float(row[1]) for row in data]
            
            start_date = dates[0]
            x_values = [(date - start_date).days for date in dates]
            
            # Calcular regressão linear
            slope, intercept = self.linear_regression(x_values, balances)
            
            if slope is None or slope <= 0:
                return None, "Tendência não permite alcançar a meta"
            
            # Calcular quando a meta será alcançada
            days_to_goal = (goal_amount - intercept) / slope
            goal_date = start_date + timedelta(days=int(days_to_goal))
            
            # Calcular R² para avaliar qualidade da previsão
            r_squared = self.calculate_r_squared(x_values, balances, slope, intercept)
            
            confidence = "Alta" if r_squared > 0.8 else "Média" if r_squared > 0.5 else "Baixa"
            
            return goal_date.strftime('%Y-%m-%d'), f"Confiança: {confidence} (R²: {r_squared:.2f})"
            
        except Exception as e:
            return None, f"Erro na previsão: {str(e)}"
    
    def calculate_r_squared(self, x_values, y_values, slope, intercept):
        """Calcula o coeficiente de determinação R²"""
        if not y_values:
            return 0
        
        y_mean = sum(y_values) / len(y_values)
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        
        if ss_tot == 0:
            return 1
        
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        
        return 1 - (ss_res / ss_tot)
    
    def get_weekly_recommendation(self, user_id):
        """Recomenda valor de saque semanal baseado na média de lucro"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obter lucros dos últimos 30 dias
            cursor.execute('''
                SELECT profit FROM daily_balances 
                WHERE user_id = ? AND date >= date('now', '-30 days')
                AND profit > 0
                ORDER BY date DESC
            ''', (user_id,))
            
            profits = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not profits:
                return 0, "Sem dados de lucro suficientes"
            
            # Calcular média de lucro diário
            avg_daily_profit = sum(profits) / len(profits)
            
            # Recomendar 50% do lucro semanal médio
            weekly_recommendation = avg_daily_profit * 7 * 0.5
            
            return round(weekly_recommendation, 2), f"Baseado em {len(profits)} dias de dados"
            
        except Exception as e:
            return 0, f"Erro no cálculo: {str(e)}"