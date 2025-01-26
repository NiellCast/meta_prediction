# ai_utils.py

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

def calcular_previsao_linear(dados, meta):
    """Realiza a previsão linear com base nos dados fornecidos."""
    if len(dados) < 2:
        return None, "Dados insuficientes para previsão."

    # Preparando os dados para o modelo
    dias = np.arange(len(dados)).reshape(-1, 1)
    valores = np.cumsum([d['valor'] for d in dados])

    modelo = LinearRegression()
    modelo.fit(dias, valores)

    if modelo.coef_[0] == 0:
        return None, "Crescimento zero, meta não pode ser alcançada."

    dias_para_meta = (meta - valores[-1]) / modelo.coef_[0]
    if dias_para_meta < 0:
        return None, "Meta já atingida."

    return int(np.ceil(dias_para_meta)), None

def calcular_previsao_polinomial(dados, meta, grau=2):
    """Realiza a previsão polinomial com base nos dados fornecidos."""
    if len(dados) < 3:
        return None, "Dados insuficientes para previsão polinomial."

    # Preparando os dados para o modelo
    dias = np.arange(len(dados)).reshape(-1, 1)
    valores = np.cumsum([d['valor'] for d in dados])

    modelo = make_pipeline(PolynomialFeatures(grau), LinearRegression())
    modelo.fit(dias, valores)

    dias_para_meta = None
    for dia in range(1, 365):  # Verifica até 1 ano
        pred = modelo.predict([[len(dados) + dia]])
        if pred >= meta:
            dias_para_meta = dia
            break

    if dias_para_meta is None:
        return None, "Meta não pode ser atingida com os dados atuais."

    return dias_para_meta, None
