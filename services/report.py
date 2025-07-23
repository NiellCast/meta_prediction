"""
Serviço de relatórios e métricas
Versão simplificada usando apenas bibliotecas padrão do Python
"""
from datetime import datetime, timedelta

class ReportService:
    def __init__(self):
        pass
    
    def generate_performance_report(self, user_id):
        """Gera relatório de performance básico"""
        # Esta função será chamada com dados já carregados
        # Retorna estrutura básica para compatibilidade
        return {
            'initial_balance': 0,
            'current_balance': 0,
            'profit_loss': 0,
            'profit_percentage': 0,
            'total_days': 0
        }
    
    def generate_transactions_summary(self, user_id):
        """Gera resumo de transações"""
        return {
            'total_deposits': 0,
            'total_withdrawals': 0,
            'transaction_count': 0
        }
    
    @staticmethod
    def calculate_performance_from_data(balances, transactions):
        """Calcula métricas de performance a partir dos dados"""
        if not balances:
            return {
                'initial_balance': 0,
                'current_balance': 0,
                'profit_loss': 0,
                'profit_percentage': 0,
                'total_days': 0
            }
        
        initial_balance = balances[0]['amount']
        current_balance = balances[-1]['amount']
        profit_loss = current_balance - initial_balance
        profit_percentage = (profit_loss / initial_balance * 100) if initial_balance > 0 else 0
        
        return {
            'initial_balance': initial_balance,
            'current_balance': current_balance,
            'profit_loss': profit_loss,
            'profit_percentage': round(profit_percentage, 2),
            'total_days': len(balances)
        }
    
    @staticmethod
    def calculate_transactions_summary(transactions):
        """Calcula resumo das transações"""
        total_deposits = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
        total_withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'withdrawal')
        
        return {
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'transaction_count': len(transactions)
        }
    
    @staticmethod
    def get_chart_data(balances, days=30):
        """Retorna dados formatados para gráficos"""
        if not balances:
            return []
        
        # Limitar aos últimos N dias
        recent_balances = balances[-days:] if len(balances) > days else balances
        
        chart_data = []
        for balance in recent_balances:
            chart_data.append({
                'date': balance['date'],
                'amount': balance['amount'],
                'deposits': balance.get('deposits', 0),
                'withdrawals': balance.get('withdrawals', 0)
            })
        
        return chart_data
    
    @staticmethod
    def calculate_win_rate(balances):
        """Calcula taxa de vitória baseada no crescimento diário"""
        if len(balances) < 2:
            return 0
        
        winning_days = 0
        total_days = len(balances) - 1
        
        for i in range(1, len(balances)):
            if balances[i]['amount'] > balances[i-1]['amount']:
                winning_days += 1
        
        return round((winning_days / total_days * 100), 2) if total_days > 0 else 0
    
    @staticmethod
    def get_weekly_stats(balances):
        """Obtém estatísticas semanais"""
        if not balances:
            return {
                'weekly_growth': 0,
                'best_day': None,
                'worst_day': None
            }
        
        # Calcular crescimento semanal (últimos 7 dias)
        if len(balances) >= 7:
            week_start = balances[-7]['amount']
            week_end = balances[-1]['amount']
            weekly_growth = week_end - week_start
        else:
            weekly_growth = 0
        
        # Encontrar melhor e pior dia
        daily_changes = []
        for i in range(1, len(balances)):
            change = balances[i]['amount'] - balances[i-1]['amount']
            daily_changes.append({
                'date': balances[i]['date'],
                'change': change
            })
        
        if daily_changes:
            best_day = max(daily_changes, key=lambda x: x['change'])
            worst_day = min(daily_changes, key=lambda x: x['change'])
        else:
            best_day = worst_day = None
        
        return {
            'weekly_growth': round(weekly_growth, 2),
            'best_day': best_day,
            'worst_day': worst_day
        }