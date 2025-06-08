# Nome do arquivo completo: db/models.py

import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext
from typing import List, Dict

# ---------------------- CONEXÃO E CONTEXTO ----------------------

def get_db():
    """
    Abre uma conexão com o banco de dados e a mantém em `g`.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """
    Fecha a conexão armazenada em `g`, se existir.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------------------- INICIALIZAÇÃO ----------------------

def init_db():
    """
    Cria todas as tabelas necessárias executando o script schema.sql.
    """
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """
    Comando `flask init-db` para (re)criar o esquema do banco.
    """
    init_db()
    click.echo('Banco de dados inicializado.')

def init_app(app):
    """
    Registra teardown e o comando CLI de inicialização.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    with app.app_context():
        init_db()

# ---------------------- USER MANAGEMENT ----------------------

def create_user(username: str, password: str) -> int:
    """
    Insere um novo usuário no banco. Retorna o id inserido.
    """
    db = get_db()
    cursor = db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password)
    )
    db.commit()
    return cursor.lastrowid

def get_user_by_username(username: str):
    """
    Retorna o usuário correspondente ao username, ou None.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    return dict(row) if row else None

# ---------------------- BALANCES (DAILY) ----------------------

def fetch_all_balances(user_id: int) -> List[Dict]:
    """
    Retorna todos os saldos diários do usuário, em ordem cronológica.
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM daily_balances WHERE user_id=? ORDER BY date ASC, id ASC",
        (user_id,)
    ).fetchall()
    return [dict(r) for r in rows]

def fetch_latest_per_day(user_id: int) -> List[Dict]:
    """
    Retorna um registro por dia (o mais recente daquele dia).
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM daily_balances "
        "WHERE user_id=? AND id IN ("
        "  SELECT MAX(id) FROM daily_balances "
        "  WHERE user_id=? GROUP BY date"
        ") ORDER BY date ASC",
        (user_id, user_id)
    ).fetchall()
    return [dict(r) for r in rows]

def insert_balance(user_id: int, date: str, current_balance: float):
    """
    Insere um novo registro em daily_balances.
    """
    db = get_db()
    db.execute(
        "INSERT INTO daily_balances "
        "(user_id, date, current_balance, deposits, profit, withdrawals, win_percentage) "
        "VALUES (?,?,?,?,0,0,0)",
        (user_id, date, current_balance)
    )
    db.commit()

def update_balance(id: int, **fields):
    """
    Atualiza campos arbitrários em daily_balances.
    Ex: update_balance(42, current_balance=100.0, profit=10.0)
    """
    cols = ','.join(f"{k}=:{k}" for k in fields)
    params = dict(fields, id=id)
    db = get_db()
    db.execute(f"UPDATE daily_balances SET {cols} WHERE id=:id", params)
    db.commit()

def delete_balance(id: int):
    """
    Remove registro de daily_balances.
    """
    db = get_db()
    db.execute("DELETE FROM daily_balances WHERE id=?", (id,))
    db.commit()

# ---------------------- TRANSACTIONS ----------------------

def fetch_transactions(user_id: int) -> List[Dict]:
    """
    Retorna todas as transações do usuário, em ordem cronológica.
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY date ASC",
        (user_id,)
    ).fetchall()
    return [dict(r) for r in rows]

def insert_transaction(user_id: int, date: str, type_: str, amount: float, ajustar: bool = True):
    """
    Insere uma transação.
    """
    db = get_db()
    db.execute(
        "INSERT INTO transactions (user_id, date, type, amount, ajustar_calculo) "
        "VALUES (?,?,?,?,?)",
        (user_id, date, type_, amount, 1 if ajustar else 0)
    )
    db.commit()

def update_transaction(id: int, date: str, type_: str, amount: float):
    """
    Atualiza uma transação existente.
    """
    db = get_db()
    db.execute(
        "UPDATE transactions SET date=?, type=?, amount=? WHERE id=?",
        (date, type_, amount, id)
    )
    db.commit()

def delete_transaction(id: int):
    """
    Remove transação.
    """
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id=?", (id,))
    db.commit()

# ---------------------- TRANSACTION AUX ----------------------

def fetch_transaction_by_id(trans_id: int, user_id: int) -> Dict:
    """
    Retorna transação pelo id e usuário, ou None.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM transactions WHERE id=? AND user_id=?",
        (trans_id, user_id)
    ).fetchone()
    return dict(row) if row else None

# ---------------------- USER META ----------------------

def fetch_meta(user_id: int) -> float:
    """
    Retorna a meta do usuário ou 0.0 se não existir.
    """
    db = get_db()
    row = db.execute(
        "SELECT target FROM user_meta WHERE user_id=?",
        (user_id,)
    ).fetchone()
    return row['target'] if row else 0.0

def upsert_meta(user_id: int, target: float):
    """
    Insere ou atualiza a meta do usuário.
    """
    db = get_db()
    if db.execute("SELECT 1 FROM user_meta WHERE user_id=?", (user_id,)).fetchone():
        db.execute("UPDATE user_meta SET target=? WHERE user_id=?", (target, user_id))
    else:
        db.execute("INSERT INTO user_meta (user_id,target) VALUES (?,?)", (user_id, target))
    db.commit()

# ---------------------- SALDO DIÁRIO AUXILIARES ----------------------

def fetch_balance_on_date(user_id: int, date: str) -> Dict:
    """
    Retorna registro de daily_balance para aquele usuário e data, ou None.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM daily_balances WHERE user_id=? AND date=?",
        (user_id, date)
    ).fetchone()
    return dict(row) if row else None

def fetch_balance_by_id(balance_id: int, user_id: int) -> Dict:
    """
    Retorna um registro de daily_balances pelo id e usuário.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM daily_balances WHERE id=? AND user_id=?",
        (balance_id, user_id)
    ).fetchone()
    return dict(row) if row else None

def recalc_balance_for_date(user_id: int, date: str):
    """
    Recalcula deposits, withdrawals, profit e win_percentage para a data dada.
    """
    db = get_db()
    bal = fetch_balance_on_date(user_id, date)
    if not bal:
        return
    dep = db.execute(
        "SELECT SUM(amount) as total FROM transactions WHERE user_id=? AND type='deposit' AND date=? AND ajustar_calculo=1",
        (user_id, date)
    ).fetchone()['total'] or 0.0
    wdr = db.execute(
        "SELECT SUM(amount) as total FROM transactions WHERE user_id=? AND type='withdrawal' AND date=? AND ajustar_calculo=1",
        (user_id, date)
    ).fetchone()['total'] or 0.0
    prev = db.execute(
        "SELECT current_balance FROM daily_balances WHERE user_id=? AND date<? ORDER BY date DESC, id DESC LIMIT 1",
        (user_id, date)
    ).fetchone()
    prev_bal = prev['current_balance'] if prev else 0.0
    profit = round((bal['current_balance'] + wdr) - (prev_bal + dep), 2)
    win_pct = round((profit / dep * 100), 2) if dep > 0 else 0.0
    db.execute(
        "UPDATE daily_balances SET deposits=?, withdrawals=?, profit=?, win_percentage=? WHERE id=?",
        (dep, wdr, profit, win_pct, bal['id'])
    )
    db.commit()

def get_current_balance(user_id: int) -> float:
    """
    Retorna o saldo atual considerando último registro diário e transações posteriores.
    """
    db = get_db()
    last = db.execute(
        "SELECT current_balance, date FROM daily_balances WHERE user_id=? ORDER BY date DESC, id DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    if not last:
        return 0.0
    base_balance, base_date = last['current_balance'], last['date']
    rows = db.execute(
        "SELECT type, amount FROM transactions WHERE user_id=? AND date>?",
        (user_id, base_date)
    ).fetchall()
    dep = sum(r['amount'] for r in rows if r['type']=='deposit')
    wdr = sum(r['amount'] for r in rows if r['type']=='withdrawal')
    return round(base_balance + dep - wdr, 2)
