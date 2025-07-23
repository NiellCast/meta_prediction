from datetime import datetime
from typing import List, Dict

class ReportService:
    @staticmethod
    def calculate_balances(rows: List[Dict]) -> List[Dict]:
        """
        Calcula lucro diário e % de vitória a partir da lista raw.
        Corrigido para usar dados já calculados do banco.
        """
        balances = []
        for rec in rows:
            # Usa os dados já calculados pelo banco
            balances.append({
                'id': rec['id'],
                'date': rec['date'],
                'current_balance': rec['current_balance'],
                'deposits': rec.get('deposits', 0.0) or 0.0,
                'withdrawals': rec.get('withdrawals', 0.0) or 0.0,
                'profit': rec.get('profit', 0.0) or 0.0,
                'win_percentage': rec.get('win_percentage', 0.0) or 0.0
            })
        return balances

    @staticmethod
    def summary(balances: List[Dict], current_balance: float) -> Dict:
        """
        Calcula resumo geral da banca.
        Corrigido para cálculos mais precisos.
        """
        if not balances:
            return {
                'current_balance': 0.0,
                'deposits': 0.0,
                'withdrawals': 0.0,
                'profit': 0.0,
                'win_percentage': 0.0
            }
            
        total_dep = sum(b['deposits'] for b in balances)
        total_wdr = sum(b['withdrawals'] for b in balances)
        
        # Lucro total = saldo atual + total de saques - total de depósitos
        total_profit = round((current_balance + total_wdr) - total_dep, 2)
        win_pct = round((total_profit / total_dep * 100), 2) if total_dep > 0 else 0.0
        
        return {
            'current_balance': current_balance,
            'deposits': total_dep,
            'withdrawals': total_wdr,
            'profit': total_profit,
            'win_percentage': win_pct
        }

    @staticmethod
    def weekly_withdrawal_recommendation(balances: List[Dict]) -> float:
        """
        Recomendação de saque semanal baseada na média de lucro dos últimos 7 dias.
        """
        if len(balances) < 7:
            return 0.0
        last7 = [b['profit'] for b in balances[-7:]]
        avg_daily = sum(p for p in last7 if p > 0) / 7.0  # Apenas lucros positivos
        return round(max(avg_daily * 7, 0.0), 2)
