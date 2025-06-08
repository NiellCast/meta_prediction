# services/forecast_engine.py

from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.ensemble import RandomForestRegressor

class ForecastEngine:
    def __init__(self, records):
        # records: list of dicts with 'date' and 'current_balance'
        self.dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in records]
        self.X = np.array([[d.toordinal()] for d in self.dates])
        self.y = np.array([r['current_balance'] for r in records])
        self.poly = PolynomialFeatures(degree=2)
        self.lin = LinearRegression().fit(self.poly.fit_transform(self.X), self.y)
        self.rf = RandomForestRegressor(n_estimators=100, random_state=42).fit(self.X, self.y)

    def _ensemble(self, x):
        return (self.lin.predict(self.poly.transform(x)) + self.rf.predict(x)) / 2.0

    def predict_date(self, target_value, horizon_days=365):
        last_ord = max(x[0] for x in self.X)
        best_ord, best_diff = last_ord, float('inf')
        for cand in range(last_ord, last_ord + horizon_days + 1):
            diff = abs(self._ensemble([[cand]])[0] - target_value)
            if diff < best_diff:
                best_diff, best_ord = diff, cand
        return datetime.fromordinal(best_ord)
