from datetime import datetime
from typing import List, Dict

class ReportService:
    @staticmethod
    def calculate_balances(rows: List[Dict]) -> List[Dict]:
        """Calcula lucro diário e % de vitória a partir da lista raw."""
        balances = []
        prev_bal = None
        for rec in rows:
            cur = rec['current_balance']
            dep = rec.get('deposits', 0.0) or 0.0
            wdr = rec.get('withdrawals', 0.0) or 0.0

            if prev_bal is None:
                profit = 0.0
            else:
                profit = round((cur + wdr) - (prev_bal + dep), 2)

            win_pct = round((profit / dep * 100), 2) if dep > 0 else 0.0

            balances.append({
                'id': rec['id'],
                'date': rec['date'],
                'current_balance': cur,
                'deposits': dep,
                'withdrawals': wdr,
                'profit': profit,
                'win_percentage': win_pct
            })
            prev_bal = cur
        return balances

    @staticmethod
    def summary(balances: List[Dict], current_balance: float) -> Dict:
        total_dep = sum(b['deposits'] for b in balances)
        total_wdr = sum(b['withdrawals'] for b in balances)
        profit = round((current_balance + total_wdr) - total_dep, 2)
        win_pct = round((profit / total_dep * 100), 2) if total_dep > 0 else 0.0
        return {
            'current_balance': current_balance,
            'deposits': total_dep,
            'withdrawals': total_wdr,
            'profit': profit,
            'win_percentage': win_pct
        }

    @staticmethod
    def weekly_withdrawal_recommendation(balances: List[Dict]) -> float:
        if len(balances) < 7:
            return 0.0
        last7 = [b['profit'] for b in balances[-7:]]
        avg_daily = sum(last7) / 7.0
        return round(max(avg_daily * 7, 0.0), 2)
