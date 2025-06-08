# Nome do arquivo completo: utils.py

from functools import wraps
from flask import session, redirect, url_for
from dateutil.relativedelta import relativedelta

def login_required(view):
    """
    Decorator para proteger rotas que requerem usuário autenticado.
    Redireciona para login se não houver 'user_id' na sessão.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped

def format_time_difference(future_date, reference_date):
    """
    Retorna diferença entre future_date e reference_date em formato legível.
    """
    rd = relativedelta(future_date, reference_date)
    years, months, days = abs(rd.years), abs(rd.months), abs(rd.days)
    parts = []
    if years:
        parts.append(f"{years} ano{'s' if years != 1 else ''}")
    if months:
        parts.append(f"{months} mês{'es' if months != 1 else ''}")
    if days:
        parts.append(f"{days} dia{'s' if days != 1 else ''}")
    return " e ".join(parts) if parts else "0 dias"

def format_currency(value):
    """
    Formata valor numérico em real brasileiro (R$), com vírgula decimal.
    """
    try:
        v = float(value)
        return "R$ {:,.2f}".format(v).replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return value

def register_filters(app):
    """
    Registra filtros e globais Jinja no app Flask.
    """
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.globals.update(format_time_difference=format_time_difference)
