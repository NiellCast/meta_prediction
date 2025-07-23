from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Em produção, use uma chave mais segura

# Configuração do banco de dados JSON
DATABASE_FILE = 'data.json'

def init_database():
    """Inicializa o banco de dados JSON se não existir"""
    if not os.path.exists(DATABASE_FILE):
        initial_data = {
            'users': [],
            'balances': [],
            'transactions': [],
            'goals': []
        }
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)

def load_data():
    """Carrega dados do arquivo JSON"""
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        init_database()
        return load_data()

def save_data(data):
    """Salva dados no arquivo JSON"""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def get_next_id(data, table):
    """Gera próximo ID para uma tabela"""
    if not data[table]:
        return 1
    return max(item.get('id', 0) for item in data[table]) + 1

def login_required(f):
    """Decorator para rotas que requerem login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def format_currency(value):
    """Formata valor como moeda brasileira"""
    try:
        return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"

# Filtro para templates
app.jinja_env.filters['currency'] = format_currency

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        data = load_data()
        
        # Verifica se usuário já existe
        for user in data['users']:
            if user['username'] == username:
                flash('Nome de usuário já existe. Tente outro.', 'danger')
                return render_template('register.html')
        
        # Cria novo usuário
        new_user = {
            'id': get_next_id(data, 'users'),
            'username': username,
            'password': generate_password_hash(password),
            'created_at': datetime.now().isoformat()
        }
        
        data['users'].append(new_user)
        save_data(data)
        
        flash('Registro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        data = load_data()
        
        # Busca usuário
        user = None
        for u in data['users']:
            if u['username'] == username:
                user = u
                break
        
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Credenciais inválidas.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    data = load_data()
    
    # Busca dados do usuário
    user_balances = [b for b in data['balances'] if b['user_id'] == user_id]
    user_transactions = [t for t in data['transactions'] if t['user_id'] == user_id]
    user_goal = None
    for g in data['goals']:
        if g['user_id'] == user_id:
            user_goal = g
            break
    
    # Ordena por data
    user_balances.sort(key=lambda x: x['date'])
    user_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # Calcula resumo
    current_balance = user_balances[-1]['amount'] if user_balances else 0
    total_deposits = sum(t['amount'] for t in user_transactions if t['type'] == 'deposit')
    total_withdrawals = sum(t['amount'] for t in user_transactions if t['type'] == 'withdrawal')
    total_profit = current_balance - total_deposits + total_withdrawals
    
    summary = {
        'current_balance': current_balance,
        'deposits': total_deposits,
        'withdrawals': total_withdrawals,
        'profit': total_profit,
        'win_percentage': 0  # Simplificado
    }
    
    # Dados para gráficos
    chart_dates = [b['date'] for b in user_balances]
    chart_balances = [b['amount'] for b in user_balances]
    
    # Meta
    current_meta = user_goal['target_amount'] if user_goal else 0
    percent_meta = (current_balance / current_meta * 100) if current_meta > 0 else 0
    
    return render_template('dashboard.html',
        summary=summary,
        display_history=list(reversed(user_balances)),
        transactions=user_transactions,
        chart_dates=chart_dates,
        chart_balances=chart_balances,
        chart_deposits=[0] * len(chart_dates),  # Simplificado
        chart_withdrawals=[0] * len(chart_dates),  # Simplificado
        chart_profits=[0] * len(chart_dates),  # Simplificado
        chart_mavg=[0] * len(chart_dates),  # Simplificado
        percent_meta=percent_meta,
        current_meta=current_meta,
        predicted_date=None,
        time_remaining=None,
        heat_matrix=[[None for _ in range(4)] for _ in range(7)],  # Simplificado
        heat_max=1,
        weekly_recommendation=0
    )

@app.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    user_id = session['user_id']
    date_str = request.form['date']
    
    try:
        amount = float(request.form['current_balance'])
    except ValueError:
        flash('Valor inválido para saldo atual.', 'danger')
        return redirect(url_for('dashboard'))
    
    data = load_data()
    
    new_balance = {
        'id': get_next_id(data, 'balances'),
        'user_id': user_id,
        'date': date_str,
        'amount': amount,
        'deposits': 0,
        'withdrawals': 0,
        'profit': 0,
        'win_percentage': 0,
        'created_at': datetime.now().isoformat()
    }
    
    data['balances'].append(new_balance)
    save_data(data)
    
    flash('Saldo diário adicionado com sucesso.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    user_id = session['user_id']
    date_str = request.form['date']
    transaction_type = request.form['type']
    
    try:
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Valor deve ser maior que zero.', 'danger')
            return redirect(url_for('dashboard'))
    except ValueError:
        flash('Valor inválido.', 'danger')
        return redirect(url_for('dashboard'))
    
    data = load_data()
    
    new_transaction = {
        'id': get_next_id(data, 'transactions'),
        'user_id': user_id,
        'date': date_str,
        'type': transaction_type,
        'amount': amount,
        'created_at': datetime.now().isoformat()
    }
    
    data['transactions'].append(new_transaction)
    save_data(data)
    
    flash('Transação adicionada com sucesso.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update_meta', methods=['POST'])
@login_required
def update_meta():
    user_id = session['user_id']
    
    try:
        target = float(request.form.get('meta', 0))
    except ValueError:
        flash('Meta inválida.', 'danger')
        return redirect(url_for('dashboard'))
    
    data = load_data()
    
    # Remove meta anterior se existir
    data['goals'] = [g for g in data['goals'] if g['user_id'] != user_id]
    
    # Adiciona nova meta
    new_goal = {
        'id': get_next_id(data, 'goals'),
        'user_id': user_id,
        'target_amount': target,
        'created_at': datetime.now().isoformat()
    }
    
    data['goals'].append(new_goal)
    save_data(data)
    
    flash('Meta atualizada com sucesso.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reset', methods=['POST'])
@login_required
def reset():
    user_id = session['user_id']
    data = load_data()
    
    # Remove todos os dados do usuário
    data['balances'] = [b for b in data['balances'] if b['user_id'] != user_id]
    data['transactions'] = [t for t in data['transactions'] if t['user_id'] != user_id]
    data['goals'] = [g for g in data['goals'] if g['user_id'] != user_id]
    
    save_data(data)
    
    flash('Banca resetada com sucesso.', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)