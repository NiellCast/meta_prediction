# caminho: dashboard/dashboard.py

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from datetime import datetime
from db import get_db
from db.models import (
    fetch_latest_per_day,
    fetch_all_balances,
    fetch_transactions,
    fetch_balance_on_date,
    fetch_balance_by_id,
    insert_balance,
    update_balance,
    delete_balance,
    fetch_transaction_by_id,
    insert_transaction,
    update_transaction,
    delete_transaction,
    fetch_meta,
    upsert_meta,
    recalc_balance_for_date,
    get_current_balance
)
from services.report import ReportService
from services.forecast_engine import ForecastEngine
from utils import login_required, format_time_difference

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']

    # Sincronização diária automática - corrigida para evitar duplicatas
    txs = fetch_transactions(user_id)
    unique_dates = sorted({t['date'] for t in txs})
    
    for d in unique_dates:
        if not fetch_balance_on_date(user_id, d):
            # Busca o saldo anterior mais próximo
            prev_balances = [b for b in fetch_latest_per_day(user_id) if b['date'] < d]
            prev = prev_balances[-1] if prev_balances else None
            base = prev['current_balance'] if prev else 0.0
            
            # Calcula depósitos e saques do dia
            deps = sum(t['amount'] for t in txs if t['date'] == d and t['type'] == 'deposit')
            wdr = sum(t['amount'] for t in txs if t['date'] == d and t['type'] == 'withdrawal')
            insert_balance(user_id, d, round(base + deps - wdr, 2))
    
    # Recalcula todos os saldos para garantir consistência
    balance_dates = sorted({b['date'] for b in fetch_all_balances(user_id)})
    for d in balance_dates:
        recalc_balance_for_date(user_id, d)

    rows = fetch_latest_per_day(user_id)
    balances = ReportService.calculate_balances(rows)
    current_balance = balances[-1]['current_balance'] if balances else 0.0
    summary = ReportService.summary(balances, current_balance)
    current_meta = fetch_meta(user_id)
    percent_meta = round(current_balance / current_meta * 100, 2) if current_meta and current_meta > 0 else 0.0

    # Previsão de meta
    predicted_date = time_remaining = None
    if current_meta and current_meta > 0 and len(rows) >= 2:
        engine = ForecastEngine(rows)
        if current_balance >= current_meta:
            predicted_date = datetime.today().strftime("%d/%m/%Y")
            time_remaining = "Meta já batida"
        else:
            try:
                dt_pred = engine.predict_date(current_meta, horizon_days=365)
                predicted_date = dt_pred.strftime("%d/%m/%Y")
                last_dt = datetime.strptime(rows[-1]['date'], "%Y-%m-%d")
                time_remaining = format_time_difference(dt_pred, last_dt)
            except Exception as e:
                predicted_date = "Erro na previsão"
                time_remaining = "Dados insuficientes"

    # Dados para gráficos
    chart_dates       = [b['date']            for b in balances]
    chart_balances    = [b['current_balance'] for b in balances]
    chart_deposits    = [b['deposits']        for b in balances]
    chart_withdrawals = [b['withdrawals']     for b in balances]
    chart_profits     = [b['profit']          for b in balances]
    
    # Média móvel de 7 dias corrigida
    chart_mavg = [
        round(sum(chart_balances[max(0,i-6):i+1]) / len(chart_balances[max(0,i-6):i+1]), 2)
        for i in range(len(chart_balances))
    ]

    # Heatmap semanal corrigido
    cols = (len(balances) + 6) // 7
    heat_matrix = [[None]*cols for _ in range(7)]
    for idx, b in enumerate(balances):
        try:
            dt = datetime.strptime(b['date'], "%Y-%m-%d")
            row = dt.weekday()
            col = idx // 7
            if col < cols:
                heat_matrix[row][col] = b['profit']
        except (ValueError, IndexError):
            continue
    
    flat = [abs(x) for row in heat_matrix for x in row if x is not None]
    heat_max = max(flat) if flat else 1.0

    weekly_recommendation = ReportService.weekly_withdrawal_recommendation(balances)

    return render_template('dashboard.html',
        summary=summary,
        display_history=list(reversed(balances)),
        transactions=txs,
        chart_dates=chart_dates,
        chart_balances=chart_balances,
        chart_deposits=chart_deposits,
        chart_withdrawals=chart_withdrawals,
        chart_profits=chart_profits,
        chart_mavg=chart_mavg,
        percent_meta=percent_meta,
        current_meta=current_meta,
        predicted_date=predicted_date,
        time_remaining=time_remaining,
        heat_matrix=heat_matrix,
        heat_max=heat_max,
        weekly_recommendation=weekly_recommendation
    )

@dashboard_bp.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    user_id  = session['user_id']
    date_str = request.form['date']
    try:
        amount = float(request.form['current_balance'])
    except ValueError:
        flash("Valor inválido para saldo atual.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    insert_balance(user_id, date_str, amount)
    recalc_balance_for_date(user_id, date_str)
    flash("Saldo diário adicionado com sucesso.", "success")
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/edit_balance/<int:balance_id>', methods=['GET','POST'])
@login_required
def edit_balance(balance_id):
    user_id = session['user_id']
    bal = fetch_balance_by_id(balance_id, user_id)
    if not bal:
        flash("Registro não encontrado.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        new_date = request.form['date']
        try:
            amount = float(request.form['current_balance'])
        except ValueError:
            flash("Valor inválido para saldo atual.", "danger")
            return redirect(url_for('dashboard.dashboard'))

        update_balance(balance_id, date=new_date, current_balance=amount)
        recalc_balance_for_date(user_id, new_date)
        flash("Saldo diário atualizado.", "success")
        return redirect(url_for('dashboard.dashboard'))

    return render_template('edit_balance.html', balance=bal)

@dashboard_bp.route('/delete_balance/<int:balance_id>', methods=['POST'])
@login_required
def delete_balance(balance_id):
    user_id = session['user_id']
    bal = fetch_balance_by_id(balance_id, user_id)
    if not bal:
        flash("Registro não encontrado.", "danger")
        return redirect(url_for('dashboard.dashboard'))
        
    date_to_recalc = bal['date']
    delete_balance(balance_id)
    recalc_balance_for_date(user_id, date_to_recalc)
    flash("Saldo diário excluído.", "success")
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    user_id  = session['user_id']
    date_str = request.form['date']
    ttype    = request.form['type']
    try:
        amount = float(request.form['amount'])
        if amount <= 0:
            flash("Valor deve ser maior que zero.", "danger")
            return redirect(url_for('dashboard.dashboard'))
    except ValueError:
        flash("Valor inválido.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    insert_transaction(user_id, date_str, ttype, amount)
    
    # Garante que existe um registro de saldo para a data
    if not fetch_balance_on_date(user_id, date_str):
        # Calcula saldo base a partir do dia anterior
        prev_balances = [b for b in fetch_latest_per_day(user_id) if b['date'] < date_str]
        base_balance = prev_balances[-1]['current_balance'] if prev_balances else 0.0
        insert_balance(user_id, date_str, base_balance)
    
    recalc_balance_for_date(user_id, date_str)
    flash("Transação adicionada com sucesso.", "success")
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/edit_transaction/<int:trans_id>', methods=['GET','POST'])
@login_required
def edit_transaction(trans_id):
    user_id = session['user_id']
    tx = fetch_transaction_by_id(trans_id, user_id)
    if not tx:
        flash("Transação não encontrada.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    if request.method == 'POST':
        old_date = tx['date']
        new_date = request.form['date']
        ttype    = request.form['type']
        try:
            amount = float(request.form['amount'])
            if amount <= 0:
                flash("Valor deve ser maior que zero.", "danger")
                return redirect(url_for('dashboard.dashboard'))
        except ValueError:
            flash("Valor inválido.", "danger")
            return redirect(url_for('dashboard.dashboard'))

        update_transaction(trans_id, new_date, ttype, amount)
        
        # Recalcula saldos para ambas as datas (antiga e nova)
        recalc_balance_for_date(user_id, old_date)
        if not fetch_balance_on_date(user_id, new_date):
            prev_balances = [b for b in fetch_latest_per_day(user_id) if b['date'] < new_date]
            base_balance = prev_balances[-1]['current_balance'] if prev_balances else 0.0
            insert_balance(user_id, new_date, base_balance)
        recalc_balance_for_date(user_id, new_date)
        flash("Transação atualizada com sucesso.", "success")
        return redirect(url_for('dashboard.dashboard'))

    return render_template('edit_transaction.html', transaction=tx)

@dashboard_bp.route('/delete_transaction/<int:trans_id>', methods=['POST'])
@login_required
def delete_transaction(trans_id):
    user_id = session['user_id']
    tx = fetch_transaction_by_id(trans_id, user_id)
    if not tx:
        flash("Transação não encontrada.", "danger")
        return redirect(url_for('dashboard.dashboard'))
        
    date_to_recalc = tx['date']
    delete_transaction(trans_id)
    recalc_balance_for_date(user_id, date_to_recalc)
    flash("Transação excluída.", "success")
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/update_meta', methods=['POST'])
@login_required
def update_meta():
    user_id = session['user_id']
    try:
        target = float(request.form.get('meta', 0.0))
    except ValueError:
        flash("Meta inválida.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    upsert_meta(user_id, target)
    flash("Meta atualizada com sucesso.", "success")
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    user_id = session['user_id']
    try:
        target_value = float(request.form['target_value'])
        if target_value <= 0:
            flash("Valor da meta deve ser maior que zero.", "danger")
            return redirect(url_for('dashboard.dashboard'))
    except (ValueError, KeyError):
        flash("Valor da meta inválido.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    rows = fetch_latest_per_day(user_id)
    if len(rows) < 2:
        flash("Necessário ter pelo menos 2 registros para previsão.", "warning")
        return redirect(url_for('dashboard.dashboard'))

    try:
        curr = get_current_balance(user_id)
        if curr >= target_value:
            dt_pred = datetime.today()
            flash(f"Previsão: meta já batida em {dt_pred.strftime('%d/%m/%Y')}", "success")
        else:
            engine = ForecastEngine(rows)
            dt_pred = engine.predict_date(target_value, horizon_days=365)
            last_dt = datetime.strptime(rows[-1]['date'], "%Y-%m-%d")
            delta = format_time_difference(dt_pred, last_dt)
            flash(f"Previsão: meta de {target_value:.2f} será atingida em {dt_pred.strftime('%d/%m/%Y')} ({delta})", "info")
    except Exception as e:
        flash("Erro ao calcular previsão. Verifique se há dados suficientes e consistentes.", "danger")

    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/reset', methods=['POST'])
@login_required
def reset():
    user_id = session['user_id']
    db = get_db()
    db.execute("DELETE FROM daily_balances WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM transactions    WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM user_meta       WHERE user_id=?", (user_id,))
    db.commit()
    flash("Banca resetada com sucesso.", "success")
    return redirect(url_for('dashboard.dashboard'))
