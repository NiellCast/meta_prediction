from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # TROQUE para uma chave secreta forte
DATABASE = 'banca.db'


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
    daily_balances = conn.execute("SELECT * FROM daily_balances WHERE user_id = ? ORDER BY date", (user_id,)).fetchall()
    transactions = conn.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date", (user_id,)).fetchall()
    conn.close()
    # Preparando dados para os gráficos
    dates = [record['date'] for record in daily_balances]
    balances = [record['current_balance'] for record in daily_balances]
    deposits = [record['deposits'] if record['deposits'] is not None else 0 for record in daily_balances]
    withdrawals = [record['withdrawals'] if record['withdrawals'] is not None else 0 for record in daily_balances]
    profits = [record['profit'] if record['profit'] is not None else 0 for record in daily_balances]
    return render_template('dashboard.html', daily_balances=daily_balances, transactions=transactions,
                           chart_dates=dates, chart_balances=balances, chart_deposits=deposits,
                           chart_withdrawals=withdrawals, chart_profits=profits)


# Rota para adicionar registro diário
@app.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    user_id = session['user_id']
    date_str = request.form['date']
    current_balance = request.form['current_balance']
    deposits = request.form.get('deposits', 0)
    profit = request.form.get('profit', 0)
    withdrawals = request.form.get('withdrawals', 0)
    win_percentage = request.form.get('win_percentage', 0)
    target = request.form.get('target', 0)
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO daily_balances (user_id, date, current_balance, deposits, profit, withdrawals, win_percentage, target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, date_str, current_balance, deposits, profit, withdrawals, win_percentage, target))
    conn.commit()
    conn.close()
    flash('Registro de saldo diário adicionado com sucesso.', 'success')
    return redirect(url_for('dashboard'))


# Rota para editar registro diário
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
        deposits = request.form.get('deposits', 0)
        profit = request.form.get('profit', 0)
        withdrawals = request.form.get('withdrawals', 0)
        win_percentage = request.form.get('win_percentage', 0)
        target = request.form.get('target', 0)
        conn.execute('''
            UPDATE daily_balances
            SET date = ?, current_balance = ?, deposits = ?, profit = ?, withdrawals = ?, win_percentage = ?, target = ?
            WHERE id = ? AND user_id = ?
        ''', (date_str, current_balance, deposits, profit, withdrawals, win_percentage, target, balance_id, user_id))
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


# Rota para adicionar transação (depósito ou saque)
@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    user_id = session['user_id']
    date_str = request.form['date']
    trans_type = request.form['type']
    amount = request.form['amount']
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
        amount = request.form['amount']
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


# Rota para previsão com Machine Learning
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    user_id = session['user_id']
    target_value = float(request.form['target_value'])
    conn = get_db_connection()
    records = conn.execute("SELECT date, current_balance FROM daily_balances WHERE user_id = ? ORDER BY date",
                           (user_id,)).fetchall()
    conn.close()
    if len(records) < 2:
        flash('Necessário ter pelo menos 2 registros para previsão.', 'warning')
        return redirect(url_for('dashboard'))

    # Prepara os dados utilizando o ordinal da data como feature
    X = []
    y = []
    for record in records:
        try:
            dt = datetime.strptime(record['date'], '%Y-%m-%d')
        except ValueError:
            continue
        X.append([dt.toordinal()])
        y.append(record['current_balance'])
    X = np.array(X)
    y = np.array(y)

    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0]
    intercept = model.intercept_
    if slope == 0:
        flash('Não é possível fazer previsão com dados estáticos.', 'danger')
        return redirect(url_for('dashboard'))

    predicted_ordinal = (target_value - intercept) / slope
    predicted_date = datetime.fromordinal(int(predicted_ordinal))

    flash(f'Previsão: A meta de {target_value} será alcançada por volta de {predicted_date.strftime("%Y-%m-%d")}',
          'info')
    return redirect(url_for('dashboard'))


# Rota para "Zerar Banca" (apaga todos os registros do usuário)
@app.route('/reset', methods=['POST'])
@login_required
def reset():
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM daily_balances WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('Banca resetada com sucesso.', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
