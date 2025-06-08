# Nome do arquivo completo: auth/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from db.models import create_user, get_user_by_username

auth_bp = Blueprint('auth', __name__, url_prefix='')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        try:
            create_user(username, password)
            flash("Registro realizado com sucesso! Faça login.", "success")
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash("Nome de usuário já existe. Tente outro.", "danger")
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        passwd = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], passwd):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('dashboard.dashboard'))
        flash("Credenciais inválidas.", "danger")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da conta.", "info")
    return redirect(url_for('auth.login'))
