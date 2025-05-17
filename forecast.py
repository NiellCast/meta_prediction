import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import PolynomialFeatures
from dateutil.relativedelta import relativedelta

class ForecastEngine:
    def __init__(self, records):
        """
        records: lista de dicts com keys 'date' (YYYY-MM-DD) e 'current_balance'
        """
        # Prepara X, y
        X, y = [], []
        for r in records:
            dt = datetime.strptime(r['date'], "%Y-%m-%d")
            X.append([dt.toordinal()])
            y.append(r['current_balance'])
        self.X = np.array(X)
        self.y = np.array(y)

        # Modelos
        self.lin = LinearRegression().fit(self.X, self.y)
        self.rf  = RandomForestRegressor(n_estimators=100, random_state=42).fit(self.X, self.y)
        self.gb  = GradientBoostingRegressor(n_estimators=100, random_state=42).fit(self.X, self.y)
        self.poly = PolynomialFeatures(degree=2)

    def ensemble_predict(self, x_ord):
        """
        x_ord: lista de [ordinal] candidatos
        retorna: lista de previsões médias dos 3 modelos
        """
        X_arr = np.array(x_ord)
        lin_p = self.lin.predict(X_arr)
        rf_p  = self.rf.predict(X_arr)
        gb_p  = self.gb.predict(X_arr)
        return (lin_p + rf_p + gb_p) / 3.0

    def predict_date(self, target_value, horizon_days=365):
        """
        Retorna a primeira data futura em que a previsão >= target_value,
        ou None se não alcançar em 'horizon_days'.
        """
        last_ord = int(self.X.max())
        cand = np.arange(last_ord, last_ord + horizon_days + 1).reshape(-1,1)
        preds = self.ensemble_predict(cand)
        # encontra o primeiro índice em que cruza
        idx = np.where(preds >= target_value)[0]
        if len(idx) > 0:
            return datetime.fromordinal(int(cand[idx[0]][0]))
        return None

    @staticmethod
    def format_time_diff(future, reference):
        rd = relativedelta(future, reference)
        parts = []
        if rd.years:
            parts.append(f"{rd.years} ano{'s' if rd.years>1 else ''}")
        if rd.months:
            parts.append(f"{rd.months} mês{'es' if rd.months>1 else ''}")
        if rd.days:
            parts.append(f"{rd.days} dia{'s' if rd.days>1 else ''}")
        return " e ".join(parts) if parts else "0 dias"
