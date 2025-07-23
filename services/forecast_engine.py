"""
Serviço de previsão usando apenas bibliotecas padrão do Python
Implementa regressão linear simples sem dependências externas
"""
from datetime import datetime, timedelta

class ForecastEngine:
    def __init__(self):
        pass
    
    def predict_balance_trend(self, x_values, y_values, days_ahead=30):
        """Prevê tendência de saldo usando regressão linear"""
        if len(x_values) < 2:
            raise ValueError("Dados insuficientes para previsão")
        
        # Calcular regressão linear
        slope, intercept = self.linear_regression(x_values, y_values)
        
        if slope is None:
            raise ValueError("Não foi possível calcular a tendência")
        
        # Gerar previsões
        last_x = max(x_values)
        predictions = []
        
        for i in range(1, days_ahead + 1):
            future_x = last_x + i
            prediction = slope * future_x + intercept
            predictions.append(max(0, prediction))  # Não permitir valores negativos
        
        return {
            'slope': slope,
            'intercept': intercept,
            'predictions': predictions,
            'r_squared': self.calculate_r_squared(x_values, y_values, slope, intercept)
        }
    
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
    
    def calculate_r_squared(self, x_values, y_values, slope, intercept):
        """Calcula o coeficiente de determinação R²"""
        if not y_values:
            return 0
        
        y_mean = sum(y_values) / len(y_values)
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        
        if ss_tot == 0:
            return 1
        
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        
        return max(0, 1 - (ss_res / ss_tot))
    
    def predict_goal_date(self, balances, goal_amount):
        """Prevê quando a meta será alcançada"""
        if len(balances) < 2:
            return None, "Dados insuficientes para previsão"
        
        try:
            # Converter datas para números (dias desde a primeira data)
            dates = [datetime.strptime(b['date'], '%Y-%m-%d') for b in balances]
            amounts = [b['amount'] for b in balances]
            
            start_date = dates[0]
            x_values = [(date - start_date).days for date in dates]
            
            # Calcular regressão linear
            slope, intercept = self.linear_regression(x_values, amounts)
            
            if slope is None or slope <= 0:
                return None, "Tendência não permite alcançar a meta"
            
            # Calcular quando a meta será alcançada
            days_to_goal = (goal_amount - intercept) / slope
            goal_date = start_date + timedelta(days=int(days_to_goal))
            
            # Calcular R² para avaliar qualidade da previsão
            r_squared = self.calculate_r_squared(x_values, amounts, slope, intercept)
            
            confidence = "Alta" if r_squared > 0.8 else "Média" if r_squared > 0.5 else "Baixa"
            
            return goal_date.strftime('%Y-%m-%d'), f"Confiança: {confidence} (R²: {r_squared:.2f})"
            
        except Exception as e:
            return None, f"Erro na previsão: {str(e)}"
    
    def get_weekly_recommendation(self, transactions):
        """Recomenda valor de saque semanal baseado na média de lucro"""
        try:
            # Filtrar apenas depósitos dos últimos 30 dias
            recent_date = datetime.now() - timedelta(days=30)
            
            recent_deposits = [
                t for t in transactions 
                if t['type'] == 'deposit' and 
                datetime.strptime(t['date'], '%Y-%m-%d %H:%M:%S') >= recent_date
            ]
            
            if not recent_deposits:
                return 0, "Sem dados de depósito suficientes"
            
            # Calcular média de depósitos
            total_deposits = sum(t['amount'] for t in recent_deposits)
            avg_daily_deposit = total_deposits / 30
            
            # Recomendar 30% dos depósitos semanais
            weekly_recommendation = avg_daily_deposit * 7 * 0.3
            
            return round(weekly_recommendation, 2), f"Baseado em {len(recent_deposits)} depósitos"
            
        except Exception as e:
            return 0, f"Erro no cálculo: {str(e)}"