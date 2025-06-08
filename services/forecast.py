from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
from dateutil.relativedelta import relativedelta
from typing import Tuple, Optional

class ForecastService:
    @staticmethod
    def predict_date(balances: list, target: float) -> Tuple[Optional[str], Optional[str]]:
        if target <= 0 or len(balances) < 2:
            return None, None

        X = np.array([[datetime.strptime(b['date'], "%Y-%m-%d").toordinal()] for b in balances])
        y = np.array([b['current_balance'] for b in balances])
        model = LinearRegression().fit(X, y)
        slope, intercept = model.coef_[0], model.intercept_

        if slope <= 0:
            return "Indefinido", "Sem crescimento"

        ord_pred = int((target - intercept) / slope)
        dt_pred = datetime.fromordinal(ord_pred)
        last_dt = datetime.strptime(balances[-1]['date'], "%Y-%m-%d")
        delta = ForecastService._format_time_difference(dt_pred, last_dt)
        return dt_pred.strftime("%d/%m/%Y"), delta

    @staticmethod
    def _format_time_difference(future: datetime, reference: datetime) -> str:
        if future < reference:
            rd = relativedelta(reference, future)
            parts = []
            if rd.months: parts.append(f"{rd.months} mês(es)")
            if rd.days:   parts.append(f"{rd.days} dia(s)")
            return "Atrasado por " + " e ".join(parts)
        rd = relativedelta(future, reference)
        parts = []
        if rd.years:  parts.append(f"{rd.years} ano(s)")
        if rd.months: parts.append(f"{rd.months} mês(es)")
        if rd.days:   parts.append(f"{rd.days} dia(s)")
        return " e ".join(parts) if parts else "0 dias"
