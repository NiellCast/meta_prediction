from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
from sklearn.linear_model import LinearRegression
import numpy as np
from dateutil.relativedelta import relativedelta  # Requer: pip install python-dateutil

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # TROQUE para uma chave secreta forte
DATABASE = 'banca.db'


# Função para formatar valores em moeda BRL (ex.: R$ 1.000,90)
def format_currency(value):
    try:
        value = float(value)
        return "R$ {:,.2f}".format(value).replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return value


app.jinja_env.filters['currency'] = format_currency


# Função para formatar a diferença de tempo entre duas datas em anos, meses e dias
def format_time_difference(future_date, reference_date):
    rd = relativedelta(future_date, reference_date)
    parts = []
    if rd.years:
        parts.append("1 ano" if rd.years == 1 else f"{rd.years} anos")
    if rd.months:
        parts.append("1 mês" if rd.months == 1 else f"{rd.months} meses")
    if rd.days:
        parts.append("1 dia" if rd.days == 1 else f"{rd.days} dias")
    return " e ".join(parts) if parts else "0 dias"


# Função auxiliar para obter o saldo atual do usuário
# Somente considera transações com data > que o último registro diário
def get_current_balance(user_id):
    conn = get_db_connection()
    daily = conn.execute("SELECT * FROM daily_balances WHERE user_id = ? ORDER BY date DESC LIMIT 1",
                         (user_id,)).fetchone()
    if daily:
        base_balance = daily['current_balance']
        base_date = daily['date']
    else:
        base_balance = 0
        base_date = "0000-00-00"
    if base_date != "0000-00-00":
        extra_trans = conn.execute("SELECT * FROM transactions WHERE user_id = ? AND date > ?",
                                   (user_id, base_date)).fetchall()
    else:
        extra_trans = conn.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    extra_deposits = sum(t['amount'] for t in extra_trans if t['type'] == 'deposit')
    extra_withdrawals = sum(t['amount'] for t in extra_trans if t['type'] == 'withdrawal')
    return round(base_balance + extra_deposits - extra_withdrawals, 2)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Tabela de usuários
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    # Tabela para registros diários da banca
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            current_balance REAL NOT NULL,
            deposits REAL,
            profit REAL,
            withdrawals REAL,
            win_percentage REAL,
            target REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Tabela para transações (depósitos ou saques)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Tabela para armazenar a meta (target) do usuário
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_meta (
            user_id INTEGER PRIMARY KEY,
            target REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()


init_db()


# Decorador para proteger rotas que requerem login
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login primeiro.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))


# Rota para registro de usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('Registro realizado com sucesso! Por favor, faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Nome de usuário já existe. Tente outro.', 'danger')
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')


# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('login'))


# Rota principal – Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    # Para cálculos, os registros diários são obtidos em ordem cronológica (ascendente)
    daily_balances = conn.execute("SELECT * FROM daily_balances WHERE user_id = ? ORDER BY date ASC",
                                  (user_id,)).fetchall()
    # Para exibição, os registros de transações são obtidos em ordem decrescente
    transactions = conn.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC",
                                (user_id,)).fetchall()
    # Para cálculos, os registros de transações são obtidos em ordem ascendente
    trans_rows = conn.execute("""
        SELECT date, type, SUM(amount) as total
        FROM transactions
        WHERE user_id = ?
        GROUP BY date, type
    """, (user_id,)).fetchall()
    conn.close()

    # Cálculo dos registros de saldo diário (ascendente)
    trans_dict = {}
    for row in trans_rows:
        d = row['date']
        if d not in trans_dict:
            trans_dict[d] = {'deposit': 0, 'withdrawal': 0}
        if row['type'] == 'deposit':
            trans_dict[d]['deposit'] = row['total']
        elif row['type'] == 'withdrawal':
            trans_dict[d]['withdrawal'] = row['total']

    computed_balances = []
    prev_balance = None
    for record in daily_balances:
        rec = dict(record)
        deposits = trans_dict.get(rec['date'], {}).get('deposit', 0)
        withdrawals = trans_dict.get(rec['date'], {}).get('withdrawal', 0)
        if prev_balance is None:
            profit = 0
        else:
            profit = rec['current_balance'] - (prev_balance + deposits - withdrawals)
        baseline = (prev_balance + deposits - withdrawals) if prev_balance is not None else 0
        win_percentage = (profit / baseline * 100) if baseline != 0 else 0
        rec['deposits'] = round(deposits, 2)
        rec['withdrawals'] = round(withdrawals, 2)
        rec['profit'] = round(profit, 2)
        rec['win_percentage'] = round(win_percentage, 2)
        computed_balances.append(rec)
        prev_balance = rec['current_balance']

    # Para exibir o histórico, invertemos a lista (o registro mais recente primeiro)
    computed_balances_display = computed_balances[::-1]

    # Resumo da Banca: se existir registro diário, utilize o último para base
    if daily_balances:
        last_daily = daily_balances[-1]
        last_daily_date = last_daily['date']
        base_balance = last_daily['current_balance']
        base_deposits = last_daily['deposits'] if last_daily['deposits'] is not None else 0
        base_withdrawals = last_daily['withdrawals'] if last_daily['withdrawals'] is not None else 0
        conn = get_db_connection()
        extra_deposits_row = conn.execute(
            "SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND type = 'deposit' AND date > ?",
            (user_id, last_daily_date)).fetchone()
        extra_withdrawals_row = conn.execute(
            "SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND type = 'withdrawal' AND date > ?",
            (user_id, last_daily_date)).fetchone()
        conn.close()
        extra_deposits = round(extra_deposits_row['total'] if extra_deposits_row['total'] is not None else 0, 2)
        extra_withdrawals = round(extra_withdrawals_row['total'] if extra_withdrawals_row['total'] is not None else 0,
                                  2)
        current_balance_summary = round(base_balance + extra_deposits - extra_withdrawals, 2)
        total_deposits = round(base_deposits + extra_deposits, 2)
        total_withdrawals = round(base_withdrawals + extra_withdrawals, 2)
    else:
        current_balance_summary = get_current_balance(user_id)
        conn = get_db_connection()
        deposits_row = conn.execute(
            "SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND type = 'deposit'",
            (user_id,)).fetchone()
        withdrawals_row = conn.execute(
            "SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND type = 'withdrawal'",
            (user_id,)).fetchone()
        conn.close()
        total_deposits = round(deposits_row['total'] if deposits_row['total'] is not None else 0, 2)
        total_withdrawals = round(withdrawals_row['total'] if withdrawals_row['total'] is not None else 0, 2)
    current_balance_summary = current_balance_summary if current_balance_summary >= total_deposits else total_deposits
    profit_summary = round(current_balance_summary - total_deposits, 2)
    win_percentage_summary = round((profit_summary / total_deposits * 100), 2) if total_deposits > 0 else 0
    summary = {
        'current_balance': current_balance_summary,
        'deposits': total_deposits,
        'withdrawals': total_withdrawals,
        'profit': profit_summary,
        'win_percentage': win_percentage_summary
    }

    # Previsão de meta
    conn = get_db_connection()
    meta_row = conn.execute("SELECT target FROM user_meta WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    current_meta_value = meta_row['target'] if meta_row else None

    predicted_date_str = None
    time_remaining = None
    if current_meta_value and len(daily_balances) >= 2:
        X = []
        y = []
        for record in daily_balances:
            try:
                dt = datetime.strptime(record['date'], '%Y-%m-%d')
            except ValueError:
                continue
            X.append([dt.toordinal()])
            y.append(record['current_balance'])
        if len(X) >= 2:
            X = np.array(X)
            y = np.array(y)
            model = LinearRegression()
            model.fit(X, y)
            slope = model.coef_[0]
            intercept = model.intercept_
            if slope != 0:
                predicted_date_obj = datetime.fromordinal(int((current_meta_value - intercept) / slope))
                predicted_date_str = predicted_date_obj.strftime("%d/%m/%Y")
                # O tempo restante é calculado com base na data do último registro diário
                last_record_date = datetime.strptime(daily_balances[-1]['date'], '%Y-%m-%d')
                time_remaining_calc = format_time_difference(predicted_date_obj, last_record_date)
                if current_balance_summary >= current_meta_value:
                    time_remaining = "A meta já foi batida!"
                else:
                    time_remaining = time_remaining_calc

    last_record = summary

    return render_template('dashboard.html',
                           daily_balances=computed_balances_display,
                           transactions=transactions,
                           chart_dates=[rec['date'] for rec in computed_balances],
                           chart_balances=[rec['current_balance'] for rec in computed_balances],
                           chart_deposits=[rec['deposits'] for rec in computed_balances],
                           chart_withdrawals=[rec['withdrawals'] for rec in computed_balances],
                           chart_profits=[rec['profit'] for rec in computed_balances],
                           current_meta=current_meta_value,
                           predicted_date=predicted_date_str,
                           time_remaining=time_remaining,
                           last_record=last_record)


# Rota para adicionar registro diário – removido o input de Meta
@app.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    user_id = session['user_id']
    date_str = request.form['date']
    current_balance = request.form['current_balance']
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO daily_balances (user_id, date, current_balance)
        VALUES (?, ?, ?)
    ''', (user_id, date_str, current_balance))
    conn.commit()
    conn.close()
    flash('Registro de saldo diário adicionado com sucesso.', 'success')
    return redirect(url_for('dashboard'))


# Rota para editar registro diário – removido o input de Meta
@app.route('/edit_balance/<int:balance_id>', methods=['GET', 'POST'])
@login_required
def edit_balance(balance_id):
    user_id = session['user_id']
    conn = get_db_connection()
    balance = conn.execute("SELECT * FROM daily_balances WHERE id = ? AND user_id = ?",
                           (balance_id, user_id)).fetchone()
    if not balance:
        flash('Registro não encontrado.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        date_str = request.form['date']
        current_balance = request.form['current_balance']
        conn.execute('''
            UPDATE daily_balances
            SET date = ?, current_balance = ?
            WHERE id = ? AND user_id = ?
        ''', (date_str, current_balance, balance_id, user_id))
        conn.commit()
        conn.close()
        flash('Registro atualizado com sucesso.', 'success')
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('edit_balance.html', balance=balance)


# Rota para excluir registro diário
@app.route('/delete_balance/<int:balance_id>', methods=['POST'])
@login_required
def delete_balance(balance_id):
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM daily_balances WHERE id = ? AND user_id = ?", (balance_id, user_id))
    conn.commit()
    conn.close()
    flash('Registro excluído com sucesso.', 'success')
    return redirect(url_for('dashboard'))


# Rota para adicionar transação (Depósito ou Saque)
@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    user_id = session['user_id']
    date_str = request.form['date']
    trans_type = request.form['type']
    try:
        amount = float(request.form['amount'])
    except ValueError:
        flash("Valor inválido.", "danger")
        return redirect(url_for('dashboard'))
    # Se for saque, verifica se o saldo atual é suficiente
    if trans_type == "withdrawal":
        current_balance = get_current_balance(user_id)
        if current_balance < amount:
            flash("Saldo insuficiente para saque.", "danger")
            return redirect(url_for('dashboard'))
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO transactions (user_id, date, type, amount)
        VALUES (?, ?, ?, ?)
    ''', (user_id, date_str, trans_type, amount))
    conn.commit()
    conn.close()
    flash('Transação adicionada com sucesso.', 'success')
    return redirect(url_for('dashboard'))


# Rota para editar transação
@app.route('/edit_transaction/<int:trans_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(trans_id):
    user_id = session['user_id']
    conn = get_db_connection()
    transaction = conn.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?",
                               (trans_id, user_id)).fetchone()
    if not transaction:
        flash('Transação não encontrada.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        date_str = request.form['date']
        trans_type = request.form['type']
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash("Valor inválido.", "danger")
            return redirect(url_for('dashboard'))
        # Se for saque, verifica se o saldo atual é suficiente
        if trans_type == "withdrawal":
            current_balance = get_current_balance(user_id)
            if current_balance < amount:
                flash("Saldo insuficiente para saque.", "danger")
                return redirect(url_for('dashboard'))
        conn.execute('''
            UPDATE transactions
            SET date = ?, type = ?, amount = ?
            WHERE id = ? AND user_id = ?
        ''', (date_str, trans_type, amount, trans_id, user_id))
        conn.commit()
        conn.close()
        flash('Transação atualizada com sucesso.', 'success')
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('edit_transaction.html', transaction=transaction)


# Rota para excluir transação
@app.route('/delete_transaction/<int:trans_id>', methods=['POST'])
@login_required
def delete_transaction(trans_id):
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (trans_id, user_id))
    conn.commit()
    conn.close()
    flash('Transação excluída com sucesso.', 'success')
    return redirect(url_for('dashboard'))


# Rota para atualizar a meta (target) do usuário
@app.route('/update_meta', methods=['POST'])
@login_required
def update_meta():
    user_id = session['user_id']
    new_meta_str = request.form['meta']
    if new_meta_str == "":
        new_meta = 0.0
    else:
        try:
            new_meta = float(new_meta_str)
        except ValueError:
            flash("Meta inválida.", "danger")
            return redirect(url_for('dashboard'))
    conn = get_db_connection()
    meta_row = conn.execute("SELECT target FROM user_meta WHERE user_id = ?", (user_id,)).fetchone()
    if meta_row:
        conn.execute("UPDATE user_meta SET target = ? WHERE user_id = ?", (new_meta, user_id))
    else:
        conn.execute("INSERT INTO user_meta (user_id, target) VALUES (?, ?)", (user_id, new_meta))
    conn.commit()
    conn.close()
    flash("Meta atualizada com sucesso.", "success")
    return redirect(url_for('dashboard'))


# Rota para "Zerar Banca" (apaga todos os registros do usuário e reseta a meta para R$ 0,00)
@app.route('/reset', methods=['POST'])
@login_required
def reset():
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM daily_balances WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.execute("UPDATE user_meta SET target = ? WHERE user_id = ?", (0, user_id))
    conn.commit()
    conn.close()
    flash('Banca resetada com sucesso.', 'success')
    return redirect(url_for('dashboard'))


# Rota para previsão utilizando regressão linear múltipla com features adicionais
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    user_id = session['user_id']
    try:
        target_value = float(request.form['target_value'])
    except ValueError:
        flash("Valor da meta inválido.", "danger")
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    records = conn.execute(
        "SELECT date, current_balance, deposits, withdrawals FROM daily_balances WHERE user_id = ? ORDER BY date",
        (user_id,)).fetchall()
    conn.close()
    if len(records) < 2:
        flash('Necessário ter pelo menos 2 registros para previsão.', 'warning')
        return redirect(url_for('dashboard'))
    X = []
    y = []
    for record in records:
        try:
            dt = datetime.strptime(record['date'], '%Y-%m-%d')
        except ValueError:
            continue
        date_ord = dt.toordinal()
        deposits = record['deposits'] if record['deposits'] is not None else 0
        withdrawals = record['withdrawals'] if record['withdrawals'] is not None else 0
        X.append([date_ord, deposits, withdrawals])
        y.append(record['current_balance'])
    X = np.array(X)
    y = np.array(y)
    model = LinearRegression()
    model.fit(X, y)
    w = model.coef_
    b = model.intercept_
    if w[0] == 0:
        flash('Não é possível fazer previsão com dados estáticos.', 'danger')
        return redirect(url_for('dashboard'))
    # Suponha que os registros futuros terão depósitos e saques iguais à média histórica:
    avg_deposits = np.mean([x[1] for x in X])
    avg_withdrawals = np.mean([x[2] for x in X])
    predicted_date_ord = (target_value - (w[1] * avg_deposits + w[2] * avg_withdrawals + b)) / w[0]
    predicted_date = datetime.fromordinal(int(predicted_date_ord))
    flash(f'Previsão: A meta de {target_value} será alcançada por volta de {predicted_date.strftime("%d/%m/%Y")}',
          'info')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
