"""
Serviço de relatórios e métricas
Versão simplificada usando apenas bibliotecas padrão do Python
"""
import sqlite3
from datetime import datetime, timedelta
import json

class ReportService:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
    
    def get_performance_metrics(self, user_id, days=30):
        """
        Calcula métricas de performance dos últimos N dias
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar dados dos últimos N dias
        cursor.execute('''
            SELECT date, profit, balance 
            FROM daily_balances 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT ?
        ''', (user_id, days))
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return {
                'daily_profit': 0,
                'accumulated_profit': 0,
                'win_rate': 0,
                'total_days': 0,
                'profitable_days': 0
            }
        
        # Calcular métricas
        daily_profit = sum(row[1] for row in data if row[1])
        accumulated_profit = data[0][2] - data[-1][2] if len(data) > 1 else 0
        profitable_days = sum(1 for row in data if row[1] and row[1] > 0)
        total_days = len(data)
        win_rate = (profitable_days / total_days * 100) if total_days > 0 else 0
        
        return {
            'daily_profit': daily_profit,
            'accumulated_profit': accumulated_profit,
            'win_rate': round(win_rate, 2) if win_rate is not None else 0,
            'total_days': total_days,
            'profitable_days': profitable_days
        }
    
    def get_chart_data(self, user_id, days=30):
        """
        Retorna dados formatados para gráficos
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, balance, deposits, withdrawals, profit
            FROM daily_balances 
            WHERE user_id = ? 
            ORDER BY date ASC 
            LIMIT ?
        ''', (user_id, days))
        
        data = cursor.fetchall()
        conn.close()
        
        # Calcular dados para gráfico
        chart_data = []
        try:
            for row in data:
                chart_data.append({
                    'date': row[0],
                    'balance': float(row[1]) if row[1] is not None else 0,
                    'deposits': float(row[2]) if row[2] is not None else 0,
                    'withdrawals': float(row[3]) if row[3] is not None else 0,
                    'profit': float(row[4]) if row[4] is not None else 0
                })
        except (ValueError, TypeError) as e:
            print(f"Erro ao processar dados do gráfico: {e}")
            return []
        
        return chart_data
    
    def get_heatmap_data(self, user_id):
        """
        Gera dados para heatmap de performance (últimas 4 semanas)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar dados dos últimos 28 dias
        cursor.execute('''
            SELECT date, profit
            FROM daily_balances 
            WHERE user_id = ? AND date >= date('now', '-28 days')
            ORDER BY date ASC
        ''', (user_id,))
        
        data = cursor.fetchall()
        conn.close()
        
        # Organizar dados por data
        daily_profits = {row[0]: row[1] for row in data}
        current_date = datetime.now()
        
        # Criar matriz 7x4 (4 semanas)
        heatmap_data = []
        try:
            for week in range(4):
                week_data = []
                for day in range(7):
                    date_key = (current_date - timedelta(days=(3-week)*7 + (6-day))).strftime('%Y-%m-%d')
                    profit = daily_profits.get(date_key, 0)
                    
                    # Classificar performance
                    if profit > 100:
                        intensity = 'high'
                    elif profit > 0:
                        intensity = 'medium'
                    elif profit == 0:
                        intensity = 'neutral'
                    else:
                        intensity = 'low'
                    
                    week_data.append({
                        'date': date_key,
                        'profit': float(profit) if profit is not None else 0,
                        'intensity': intensity
                    })
                heatmap_data.append(week_data)
        except Exception as e:
            print(f"Erro ao gerar heatmap: {e}")
            return []
        
        return heatmap_data
    
    def get_simple_stats(self, user_id):
        """Obtém estatísticas básicas simplificadas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_days,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as profitable_days,
                    AVG(balance) as avg_balance,
                    MAX(balance) as max_balance,
                    MIN(balance) as min_balance,
                    SUM(profit) as total_profit
                FROM daily_balances 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:
                return {
                    'total_days': result[0],
                    'profitable_days': result[1] or 0,
                    'win_rate': round((result[1] or 0) / result[0] * 100, 2),
                    'avg_balance': round(result[2] or 0, 2),
                    'max_balance': round(result[3] or 0, 2),
                    'min_balance': round(result[4] or 0, 2),
                    'total_profit': round(result[5] or 0, 2)
                }
            else:
                return {
                    'total_days': 0,
                    'profitable_days': 0,
                    'win_rate': 0,
                    'avg_balance': 0,
                    'max_balance': 0,
                    'min_balance': 0,
                    'total_profit': 0
                }
                
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return None