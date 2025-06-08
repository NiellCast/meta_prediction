# models.py

import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext
from typing import List, Dict


# ---------------------- CONEXÃO E CONTEXTO ----------------------

def get_db():
    """
    Abre uma conexão com o banco de dados e a mantêm em `g`.
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
    # garante existência das tabelas ao iniciar a aplicação
    with app.app_context():
        init_db()


# ---------------------- BALANCES (DAILY) ----------------------

def fetch_all_balances(user_id: int) -> List[Dict]:
    """
    Retorna todos os saldos diários do usuário, em ordem cronológica.
    """
    db = get_db()
    rows = db.execute(
        "SELECT * FROM daily_balances "
        "WHERE user_id=? "
        "ORDER BY date ASC, id ASC",
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
        ") "
        "ORDER BY date ASC",
        (user_id, user_id)
    ).fetchall()
    return [dict(r) for r in rows]

def insert_balance(user_id: int, date: str, current_balance: float):
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
    db = get_db()
    db.execute(
        "INSERT INTO transactions (user_id, date, type, amount, ajustar_calculo) "
        "VALUES (?,?,?,?,?)",
        (user_id, date, type_, amount, 1 if ajustar else 0)
    )
    db.commit()

def update_transaction(id: int, date: str, type_: str, amount: float):
    db = get_db()
    db.execute(
        "UPDATE transactions SET date=?, type=?, amount=? WHERE id=?",
        (date, type_, amount, id)
    )
    db.commit()

def delete_transaction(id: int):
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id=?", (id,))
    db.commit()


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
