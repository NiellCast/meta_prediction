import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from dateutil.relativedelta import relativedelta

class ForecastEngine:
    def __init__(self, balances, target):
        """
        balances: lista de dicts com 'date' (YYYY-MM-DD) e 'current_balance'
        target: valor da meta a ser alcançado
        """
        self.target = target
        self.X = []
        self.y = []
        for b in balances:
            try:
                dt = datetime.strptime(b['date'], "%Y-%m-%d")
            except ValueError:
                continue
            self.X.append([dt.toordinal()])
            self.y.append(b['current_balance'])
        self.X = np.array(self.X)
        self.y = np.array(self.y)

    def predict(self):
        """
        Retorna uma tupla (predicted_date_str, time_remaining_str):
         - Se slope <= 0: ("Indefinido", "Sem crescimento")
         - Se len(X)<2: (None, None)
         - Caso normal: data prevista e tempo formatado.
        """
        if len(self.X) < 2:
            return None, None

        model = LinearRegression().fit(self.X, self.y)
        slope = model.coef_[0]
        intercept = model.intercept_

        if slope <= 0:
            return "Indefinido", "Sem crescimento"

        ord_pred = int((self.target - intercept) / slope)
        dt_pred = datetime.fromordinal(ord_pred)
        last_dt = datetime.fromordinal(int(self.X[-1][0]))
        time_rem = self._format_time_difference(dt_pred, last_dt)
        return dt_pred.strftime("%d/%m/%Y"), time_rem

    @staticmethod
    def _format_time_difference(future, reference):
        """
        Se future < reference: "A meta deveria ter sido batida há X mês(es) e Y dia(s)"
        Senão: "A e B e C"
        """
        if future < reference:
            rd = relativedelta(reference, future)
            months = f"{rd.months} mês(es)" if rd.months else ""
            days   = f"{rd.days} dia(s)"    if rd.days else ""
            parts = " e ".join(p for p in [months, days] if p)
            return f"A meta deveria ter sido batida há {parts}" if parts else "Atrasado"
        rd = relativedelta(future, reference)
        parts = []
        if rd.years:  parts.append(f"{rd.years} ano(s)")
        if rd.months: parts.append(f"{rd.months} mês(es)")
        if rd.days:   parts.append(f"{rd.days} dia(s)")
        return " e ".join(parts) if parts else "0 dias"
