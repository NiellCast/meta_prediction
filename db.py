import sqlite3

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
    # Tabela para registros diários da banca (removida coluna target)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            current_balance REAL NOT NULL,
            deposits REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            withdrawals REAL DEFAULT 0,
            win_percentage REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Tabela para transações
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            ajustar_calculo INTEGER DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Tabela para armazenar a meta do usuário
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_meta (
            user_id INTEGER PRIMARY KEY,
            target REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_current_balance(user_id):
    conn = get_db_connection()
    daily = conn.execute('''
        SELECT * FROM daily_balances
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 1
    ''', (user_id,)).fetchone()
    if daily:
        base_balance = daily['current_balance']
        base_date = daily['date']
    else:
        base_balance = 0
        base_date = "0000-00-00"
    if base_date != "0000-00-00":
        extra_trans = conn.execute('''
            SELECT * FROM transactions
            WHERE user_id = ? AND date > ?
        ''', (user_id, base_date)).fetchall()
    else:
        extra_trans = conn.execute('''
            SELECT * FROM transactions WHERE user_id = ?
        ''', (user_id,)).fetchall()
    conn.close()
    extra_deposits = sum(t['amount'] for t in extra_trans if t['type'] == 'deposit')
    extra_withdrawals = sum(t['amount'] for t in extra_trans if t['type'] == 'withdrawal')
    return round(base_balance + extra_deposits - extra_withdrawals, 2)

# Inicializa o DB automaticamente
init_db()
