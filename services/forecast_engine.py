# services/forecast_engine.py

from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.ensemble import RandomForestRegressor

class ForecastEngine:
    def __init__(self, records):
        """
        Inicializa o motor de previsão.
        Corrigido para lidar melhor com dados inconsistentes.
        """
        if not records or len(records) < 2:
            raise ValueError("Necessário pelo menos 2 registros para previsão")
            
        self.dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in records]
        self.X = np.array([[d.toordinal()] for d in self.dates])
        self.y = np.array([r['current_balance'] for r in records])
        
        # Verifica se há variação nos dados
        if np.std(self.y) == 0:
            raise ValueError("Dados sem variação suficiente para previsão")
            
        self.poly = PolynomialFeatures(degree=2)
        
        try:
            X_poly = self.poly.fit_transform(self.X)
            self.lin = LinearRegression().fit(X_poly, self.y)
            self.rf = RandomForestRegressor(n_estimators=50, random_state=42).fit(self.X, self.y)
        except Exception as e:
            # Fallback para regressão linear simples
            self.lin = LinearRegression().fit(self.X, self.y)
            self.rf = None

    def _ensemble(self, x):
        """
        Combina predições de múltiplos modelos.
        """
        try:
            if self.rf is not None:
                lin_pred = self.lin.predict(self.poly.transform(x))
                rf_pred = self.rf.predict(x)
                return (lin_pred + rf_pred) / 2.0
            else:
                return self.lin.predict(x)
        except:
            # Fallback para predição linear simples
            return self.lin.predict(x)

    def predict_date(self, target_value, horizon_days=365):
        """
        Prediz a data em que o saldo atingirá o valor alvo.
        Corrigido para ser mais robusto.
        """
        last_ord = max(x[0] for x in self.X)
        best_ord, best_diff = last_ord, float('inf')
        
        for cand in range(last_ord, last_ord + horizon_days + 1):
            try:
                pred_value = self._ensemble([[cand]])
                if hasattr(pred_value, '__len__'):
                    pred_value = pred_value[0]
                diff = abs(pred_value - target_value)
            except:
                continue
                
            if diff < best_diff:
                best_diff, best_ord = diff, cand
                
        return datetime.fromordinal(best_ord)
