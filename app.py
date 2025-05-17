from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
from dateutil.relativedelta import relativedelta
from functools import wraps

import db
from forecast import ForecastEngine

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Troque por uma chave forte em produção

# Expor funções Python no Jinja2
app.jinja_env.globals.update(
    enumerate=enumerate,
    abs=abs,
    range=range
)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def format_currency(value):
    try:
        v = float(value)
        return "R$ {:,.2f}".format(v).replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return value
app.jinja_env.filters['currency'] = format_currency

def format_time_difference(future_date, reference_date):
    rd = relativedelta(future_date, reference_date)
    neg = future_date < reference_date
    years, months, days = abs(rd.years), abs(rd.months), abs(rd.days)
    parts = []
    if years:  parts.append(f"{years} ano{'s' if years>1 else ''}")
    if months: parts.append(f"{months} mês{'es' if months>1 else ''}")
    if days:   parts.append(f"{days} dia{'s' if days>1 else ''}")
    txt = " e ".join(parts) if parts else "0 dias"
    return f"Atrasado por {txt}" if neg else txt

@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username,password = request.form['username'],request.form['password']
        hashed = generate_password_hash(password)
        conn = db.get_db_connection()
        try:
            conn.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,hashed))
            conn.commit()
            flash("Registro realizado com sucesso! Faça login.","success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Nome de usuário já existe.","danger")
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username,password = request.form['username'],request.form['password']
        conn = db.get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?",(username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'],password):
            session['user_id'],session['username'] = user['id'],user['username']
            flash("Login realizado com sucesso!","success")
            return redirect(url_for('dashboard'))
        flash("Credenciais inválidas.","danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da conta.","info")
    return redirect(url_for('login'))

@app.route('/recalculate', methods=['POST'])
@login_required
def recalculate():
    uid = session['user_id']
    conn = db.get_db_connection()
    rows = conn.execute("SELECT id,date,current_balance FROM daily_balances WHERE user_id = ?",(uid,)).fetchall()
    for row in rows:
        d = row['date']
        dep = conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_id=? AND type='deposit' AND date=? AND ajustar_calculo=1",
            (uid,d)
        ).fetchone()[0] or 0
        wd = conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_id=? AND type='withdrawal' AND date=? AND ajustar_calculo=1",
            (uid,d)
        ).fetchone()[0] or 0
        pr = round((row['current_balance'] + wd) - dep,2)
        wp = round((pr/dep*100),2) if dep>0 else 0
        conn.execute(
            "UPDATE daily_balances SET deposits=?,withdrawals=?,profit=?,win_percentage=? WHERE id=?",
            (dep,wd,pr,wp,row['id'])
        )
    conn.commit()
    conn.close()
    flash("Registros recalculados com sucesso.","success")
    return redirect(url_for('dashboard'))

@app.route('/check_daily')
@login_required
def check_daily():
    uid = session['user_id']
    date_s = request.args.get('date')
    conn = db.get_db_connection()
    exists = conn.execute(
        "SELECT 1 FROM daily_balances WHERE user_id=? AND date=?",
        (uid,date_s)
    ).fetchone() is not None
    conn.close()
    return jsonify({"exists":exists})

@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    conn = db.get_db_connection()
    daily = conn.execute("""
        SELECT * FROM daily_balances
        WHERE id IN (
            SELECT MAX(id) FROM daily_balances WHERE user_id=? GROUP BY date
        ) ORDER BY date ASC
    """,(uid,)).fetchall()
    txs = conn.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC LIMIT 100",
        (uid,)
    ).fetchall()
    meta_row = conn.execute("SELECT target FROM user_meta WHERE user_id=?",(uid,)).fetchone()
    conn.close()

    current_meta = meta_row['target'] if meta_row else None

    # Processar lucro diário
    computed=[]; prev_cb=None
    for rec in daily:
        r=dict(rec)
        dep=r.get('deposits') or 0
        wd=r.get('withdrawals') or 0
        cb=r['current_balance']
        pr=0.0 if prev_cb is None else round(cb - prev_cb - dep + wd,2)
        wp=round((pr/dep*100),2) if dep>0 else 0
        r.update({'deposits':dep,'withdrawals':wd,'profit':pr,'win_percentage':wp})
        computed.append(r)
        prev_cb=cb

    chart_dates=[r['date'] for r in computed]
    chart_balances=[r['current_balance'] for r in computed]

    last_dep=last_wd=0
    chart_deposits=[]; chart_withdrawals=[]
    for r in computed:
        if r['deposits']>0: last_dep=r['deposits']
        chart_deposits.append(last_dep)
        if r['withdrawals']>0: last_wd=r['withdrawals']
        chart_withdrawals.append(last_wd)

    cum=0; chart_profits=[]
    for r in computed:
        cum+=r['profit']
        chart_profits.append(cum)

    chart_mavg=[]
    for i in range(len(chart_balances)):
        w=chart_balances[max(0,i-6):i+1]
        chart_mavg.append(round(sum(w)/len(w),2))

    heat_matrix=[]; heat_max=0
    if computed:
        base_dt=datetime.strptime(computed[0]['date'],"%Y-%m-%d")
        weeks=max(((datetime.strptime(d['date'],"%Y-%m-%d")-base_dt).days//7) for d in computed)+1
        heat_matrix=[[None]*weeks for _ in range(7)]
        for r in computed:
            dt=datetime.strptime(r['date'],"%Y-%m-%d")
            w=(dt-base_dt).days//7; wd=dt.weekday()
            p=r['profit']
            heat_matrix[wd][w]=p
            heat_max=max(heat_max,abs(p))

    total_dep=sum(t['amount'] for t in txs if t['type']=='deposit')
    total_wd=sum(t['amount'] for t in txs if t['type']=='withdrawal')
    curr_bal=db.get_current_balance(uid)
    profit_sum=round((curr_bal+total_wd)-total_dep,2)
    win_sum=round((profit_sum/total_dep*100),2) if total_dep>0 else 0
    last_record={
        'current_balance':curr_bal,
        'deposits':total_dep,
        'withdrawals':total_wd,
        'profit':profit_sum,
        'win_percentage':win_sum
    }

    percent_meta=round(curr_bal/current_meta*100,2) if current_meta else 0

    predicted_date=None; time_remaining=None
    if current_meta and len(computed)>=2:
        engine=ForecastEngine([{'date':d['date'],'current_balance':d['current_balance']} for d in computed])
        if curr_bal>=current_meta:
            predicted_date=datetime.today().strftime("%d/%m/%Y")
            time_remaining="Meta já batida"
        else:
            dtp=engine.predict_date(current_meta,horizon_days=365)
            if dtp:
                predicted_date=dtp.strftime("%d/%m/%Y")
                last_dt=datetime.strptime(computed[-1]['date'],"%Y-%m-%d")
                time_remaining=format_time_difference(dtp,last_dt)

    return render_template('dashboard.html',
        daily_balances=list(reversed(computed)),
        transactions=txs,
        chart_dates=chart_dates,
        chart_balances=chart_balances,
        chart_deposits=chart_deposits,
        chart_withdrawals=chart_withdrawals,
        chart_profits=chart_profits,
        chart_mavg=chart_mavg,
        heat_matrix=heat_matrix,
        heat_max=heat_max,
        current_meta=current_meta,
        percent_meta=percent_meta,
        predicted_date=predicted_date,
        time_remaining=time_remaining,
        last_record=last_record
    )

@app.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    uid=session['user_id']
    date_str=request.form['date']
    try:
        bal=float(request.form['current_balance'])
    except ValueError:
        flash("Valor inválido para saldo atual.","danger")
        return redirect(url_for('dashboard'))

    conn=db.get_db_connection()
    try:
        existing=conn.execute(
            "SELECT id FROM daily_balances WHERE user_id=? AND date=?",(uid,date_str)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE daily_balances SET current_balance=? WHERE id=?",(bal,existing['id'])
            )
        else:
            conn.execute(
                "INSERT INTO daily_balances(user_id,date,current_balance) VALUES(?,?,?)",
                (uid,date_str,bal)
            )
        conn.commit()
    except:
        conn.rollback()
        flash("Erro ao adicionar saldo diário.","danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/edit_balance/<int:balance_id>', methods=['GET','POST'])
@login_required
def edit_balance(balance_id):
    uid=session['user_id']
    conn=db.get_db_connection()
    rec=conn.execute(
        "SELECT * FROM daily_balances WHERE id=? AND user_id=?",(balance_id,uid)
    ).fetchone()
    if not rec:
        conn.close()
        flash("Registro não encontrado.","danger")
        return redirect(url_for('dashboard'))
    if request.method=='POST':
        date_str=request.form['date']
        try:
            bal=float(request.form['current_balance'])
        except ValueError:
            flash("Valor inválido.","danger")
            return redirect(url_for('dashboard'))
        try:
            conn.execute(
                "UPDATE daily_balances SET date=?,current_balance=? WHERE id=?",
                (date_str,bal,balance_id)
            )
            conn.commit()
        except:
            conn.rollback()
            flash("Erro ao editar registro.","danger")
        finally:
            conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('edit_balance.html',balance=rec)

@app.route('/delete_balance/<int:balance_id>', methods=['POST'])
@login_required
def delete_balance(balance_id):
    uid=session['user_id']
    conn=db.get_db_connection()
    try:
        conn.execute(
            "DELETE FROM daily_balances WHERE id=? AND user_id=?",(balance_id,uid)
        )
        conn.commit()
    except:
        conn.rollback()
        flash("Erro ao excluir registro.","danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    uid=session['user_id']
    date_str=request.form['date']
    ttype=request.form['type']
    try:
        amt=float(request.form['amount'])
    except ValueError:
        flash("Valor inválido.","danger")
        return redirect(url_for('dashboard'))

    conn=db.get_db_connection()
    try:
        conn.execute(
            "INSERT INTO transactions(user_id,date,type,amount,ajustar_calculo) VALUES(?,?,?,?,1)",
            (uid,date_str,ttype,amt)
        )
        conn.commit()
    except:
        conn.rollback()
        flash("Erro ao adicionar transação.","danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/edit_transaction/<int:trans_id>', methods=['GET','POST'])
@login_required
def edit_transaction(trans_id):
    uid=session['user_id']
    conn=db.get_db_connection()
    tx=conn.execute(
        "SELECT * FROM transactions WHERE id=? AND user_id=?",(trans_id,uid)
    ).fetchone()
    if not tx:
        conn.close()
        flash("Transação não encontrada.","danger")
        return redirect(url_for('dashboard'))
    if request.method=='POST':
        date_str=request.form['date']
        ttype=request.form['type']
        try:
            amt=float(request.form['amount'])
        except ValueError:
            flash("Valor inválido.","danger")
            return redirect(url_for('dashboard'))
        try:
            conn.execute(
                "UPDATE transactions SET date=?,type=?,amount=? WHERE id=? AND user_id=?",
                (date_str,ttype,amt,trans_id,uid)
            )
            conn.commit()
        except:
            conn.rollback()
            flash("Erro ao editar transação.","danger")
        finally:
            conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('edit_transaction.html',transaction=tx)

@app.route('/delete_transaction/<int:trans_id>', methods=['POST'])
@login_required
def delete_transaction(trans_id):
    uid=session['user_id']
    conn=db.get_db_connection()
    try:
        conn.execute(
            "DELETE FROM transactions WHERE id=? AND user_id=?",(trans_id,uid)
        )
        conn.commit()
    except:
        conn.rollback()
        flash("Erro ao excluir transação.","danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/update_meta', methods=['POST'])
@login_required
def update_meta():
    uid=session['user_id']
    mstr=request.form['meta']
    try:
        mval=float(mstr) if mstr else 0.0
    except ValueError:
        flash("Meta inválida.","danger")
        return redirect(url_for('dashboard'))

    conn=db.get_db_connection()
    try:
        exists=conn.execute(
            "SELECT 1 FROM user_meta WHERE user_id=?",(uid,)
        ).fetchone()
        if exists:
            conn.execute(
                "UPDATE user_meta SET target=? WHERE user_id=?",(mval,uid)
            )
        else:
            conn.execute(
                "INSERT INTO user_meta(user_id,target) VALUES(?,?)",(uid,mval)
            )
        conn.commit()
    except:
        conn.rollback()
        flash("Erro ao atualizar meta.","danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/reset', methods=['POST'])
@login_required
def reset():
    uid=session['user_id']
    conn=db.get_db_connection()
    try:
        conn.execute("DELETE FROM daily_balances WHERE user_id=?",(uid,))
        conn.execute("DELETE FROM transactions WHERE user_id=?",(uid,))
        conn.execute("DELETE FROM user_meta WHERE user_id=?",(uid,))
        conn.commit()
        flash("Banca resetada com sucesso.","success")
    except:
        conn.rollback()
        flash("Erro ao resetar banca.","danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

if __name__=='__main__':
    app.run(debug=True)
