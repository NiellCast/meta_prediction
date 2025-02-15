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


# Função para formatar valores em moeda BRL (ex.: R$ 1.000,90)
def format_currency(value):
    try:
        value = float(value)
        # Formata no padrão US e depois troca vírgula e ponto
        return "R$ {:,.2f}".format(value).replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return value


app.jinja_env.filters['currency'] = format_currency


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
    daily_balances = conn.execute("SELECT * FROM daily_balances WHERE user_id = ? ORDER BY date", (user_id,)).fetchall()
    # Agrupa as transações por data e tipo
    trans_rows = conn.execute("""
        SELECT date, type, SUM(amount) as total
        FROM transactions
        WHERE user_id = ?
        GROUP BY date, type
    """, (user_id,)).fetchall()
    transactions = conn.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date", (user_id,)).fetchall()

    # Cria um dicionário com os totais de Depósito e Saque por data
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
    # Itera pelos registros de saldo diário em ordem de data para calcular os valores
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
        rec['deposits'] = deposits
        rec['withdrawals'] = withdrawals
        rec['profit'] = profit
        rec['win_percentage'] = win_percentage
        computed_balances.append(rec)
        prev_balance = rec['current_balance']

    # Prepara os dados para os gráficos
    chart_dates = [rec['date'] for rec in computed_balances]
    chart_balances = [rec['current_balance'] for rec in computed_balances]
    chart_deposits = [rec['deposits'] for rec in computed_balances]
    chart_withdrawals = [rec['withdrawals'] for rec in computed_balances]
    chart_profits = [rec['profit'] for rec in computed_balances]

    # Recupera a meta atual do usuário (caso definida)
    meta_row = conn.execute("SELECT target FROM user_meta WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    current_meta = meta_row['target'] if meta_row else None

    # Calcula a previsão da data para atingir a meta, se possível
    predicted_date = None
    if current_meta and len(daily_balances) >= 2:
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
                predicted_ordinal = (current_meta - intercept) / slope
                predicted_date = datetime.fromordinal(int(predicted_ordinal)).strftime("%Y-%m-%d")

    # Obtém o último registro calculado para exibir o resumo da banca
    last_record = computed_balances[-1] if computed_balances else None

    return render_template('dashboard.html', daily_balances=computed_balances, transactions=transactions,
                           chart_dates=chart_dates, chart_balances=chart_balances, chart_deposits=chart_deposits,
                           chart_withdrawals=chart_withdrawals, chart_profits=chart_profits,
                           current_meta=current_meta, predicted_date=predicted_date, last_record=last_record)


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


# Nova rota para atualizar a meta (target) do usuário
@app.route('/update_meta', methods=['POST'])
@login_required
def update_meta():
    user_id = session['user_id']
    new_meta = request.form['meta']
    try:
        new_meta = float(new_meta)
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


if __name__ == '__main__':
    app.run(debug=True)
