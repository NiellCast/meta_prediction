#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import hashlib
import uuid
from datetime import datetime, timedelta
import re

# Import our models
from db.models import Database

class WebHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = Database()
        self.sessions = {}
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_login_page()
        elif path == '/register':
            self.serve_register_page()
        elif path == '/dashboard':
            self.serve_dashboard()
        elif path == '/logout':
            self.handle_logout()
        elif path.startswith('/static/'):
            self.serve_static_file(path)
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = parse_qs(post_data)
        
        # Convert form data to simple dict
        data = {}
        for key, value in form_data.items():
            data[key] = value[0] if value else ''
        
        if path == '/login':
            self.handle_login(data)
        elif path == '/register':
            self.handle_register(data)
        elif path == '/add_balance':
            self.handle_add_balance(data)
        elif path == '/add_transaction':
            self.handle_add_transaction(data)
        elif path == '/set_goal':
            self.handle_set_goal(data)
        elif path == '/reset_balance':
            self.handle_reset_balance()
        else:
            self.send_error(404)
    
    def serve_login_page(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Gerenciador de Banca</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="password"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .link { text-align: center; margin-top: 20px; }
                .error { color: red; margin-bottom: 15px; }
            </style>
        </head>
        <body>
            <h2>Login</h2>
            <form method="post" action="/login">
                <div class="form-group">
                    <label>Usuário:</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Senha:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">Entrar</button>
            </form>
            <div class="link">
                <a href="/register">Criar nova conta</a>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_register_page(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Registro - Gerenciador de Banca</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="password"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #1e7e34; }
                .link { text-align: center; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h2>Criar Conta</h2>
            <form method="post" action="/register">
                <div class="form-group">
                    <label>Usuário:</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Senha:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">Criar Conta</button>
            </form>
            <div class="link">
                <a href="/">Já tem conta? Faça login</a>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_dashboard(self):
        # Check if user is logged in
        session_id = self.get_session_id()
        if not session_id or session_id not in self.sessions:
            self.redirect('/')
            return
        
        user_id = self.sessions[session_id]
        user = self.db.get_user_by_id(user_id)
        if not user:
            self.redirect('/')
            return
        
        # Get user data
        current_balance = self.db.get_current_balance(user_id)
        transactions = self.db.get_recent_transactions(user_id, 10)
        goal = self.db.get_user_goal(user_id)
        
        # Calculate metrics
        total_deposits = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
        total_withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'withdrawal')
        net_result = total_deposits - total_withdrawals
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Gerenciador de Banca</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
                .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
                .metric {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
                .metric h3 {{ margin: 0 0 10px 0; color: #666; }}
                .metric .value {{ font-size: 24px; font-weight: bold; }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; margin-bottom: 5px; }}
                input, select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
                button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
                button:hover {{ background: #0056b3; }}
                .btn-success {{ background: #28a745; }}
                .btn-success:hover {{ background: #1e7e34; }}
                .btn-danger {{ background: #dc3545; }}
                .btn-danger:hover {{ background: #c82333; }}
                .transactions {{ max-height: 300px; overflow-y: auto; }}
                .transaction {{ padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Olá, {user['username']}!</h1>
                <a href="/logout">Sair</a>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>Saldo Atual</h3>
                    <div class="value">R$ {current_balance:.2f}</div>
                </div>
                <div class="metric">
                    <h3>Total Depósitos</h3>
                    <div class="value positive">R$ {total_deposits:.2f}</div>
                </div>
                <div class="metric">
                    <h3>Total Saques</h3>
                    <div class="value negative">R$ {total_withdrawals:.2f}</div>
                </div>
                <div class="metric">
                    <h3>Resultado Líquido</h3>
                    <div class="value {'positive' if net_result >= 0 else 'negative'}">R$ {net_result:.2f}</div>
                </div>
            </div>
            
            <div class="card">
                <h3>Adicionar Saldo Diário</h3>
                <form method="post" action="/add_balance">
                    <div class="form-group">
                        <label>Data:</label>
                        <input type="date" name="date" value="{datetime.now().strftime('%Y-%m-%d')}" required>
                    </div>
                    <div class="form-group">
                        <label>Saldo (R$):</label>
                        <input type="number" name="balance" step="0.01" required>
                    </div>
                    <button type="submit" class="btn-success">Adicionar Saldo</button>
                </form>
            </div>
            
            <div class="card">
                <h3>Nova Transação</h3>
                <form method="post" action="/add_transaction">
                    <div class="form-group">
                        <label>Tipo:</label>
                        <select name="type" required>
                            <option value="deposit">Depósito</option>
                            <option value="withdrawal">Saque</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Valor (R$):</label>
                        <input type="number" name="amount" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Descrição:</label>
                        <input type="text" name="description">
                    </div>
                    <button type="submit">Adicionar Transação</button>
                </form>
            </div>
            
            <div class="card">
                <h3>Definir Meta</h3>
                <form method="post" action="/set_goal">
                    <div class="form-group">
                        <label>Meta de Saldo (R$):</label>
                        <input type="number" name="target_amount" step="0.01" value="{goal['target_amount'] if goal else ''}" required>
                    </div>
                    <div class="form-group">
                        <label>Data Limite:</label>
                        <input type="date" name="target_date" value="{goal['target_date'] if goal else ''}" required>
                    </div>
                    <button type="submit" class="btn-success">Definir Meta</button>
                </form>
            </div>
            
            <div class="card">
                <h3>Transações Recentes</h3>
                <div class="transactions">
                    {''.join([f'<div class="transaction"><span>{t["description"]} ({t["type"]})</span><span class="{"positive" if t["type"] == "deposit" else "negative"}">R$ {t["amount"]:.2f}</span></div>' for t in transactions])}
                </div>
            </div>
            
            <div class="card">
                <form method="post" action="/reset_balance">
                    <button type="submit" class="btn-danger" onclick="return confirm('Tem certeza que deseja resetar a banca?')">Reset da Banca</button>
                </form>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_login(self, data):
        username = data.get('username', '')
        password = data.get('password', '')
        
        user = self.db.authenticate_user(username, password)
        if user:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = user['id']
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/')
            self.end_headers()
        else:
            self.redirect('/')
    
    def handle_register(self, data):
        username = data.get('username', '')
        password = data.get('password', '')
        
        if self.db.create_user(username, password):
            self.redirect('/')
        else:
            self.redirect('/register')
    
    def handle_add_balance(self, data):
        session_id = self.get_session_id()
        if session_id and session_id in self.sessions:
            user_id = self.sessions[session_id]
            date = data.get('date', '')
            balance = float(data.get('balance', 0))
            self.db.add_daily_balance(user_id, date, balance)
        self.redirect('/dashboard')
    
    def handle_add_transaction(self, data):
        session_id = self.get_session_id()
        if session_id and session_id in self.sessions:
            user_id = self.sessions[session_id]
            transaction_type = data.get('type', '')
            amount = float(data.get('amount', 0))
            description = data.get('description', '')
            self.db.add_transaction(user_id, transaction_type, amount, description)
        self.redirect('/dashboard')
    
    def handle_set_goal(self, data):
        session_id = self.get_session_id()
        if session_id and session_id in self.sessions:
            user_id = self.sessions[session_id]
            target_amount = float(data.get('target_amount', 0))
            target_date = data.get('target_date', '')
            self.db.set_user_goal(user_id, target_amount, target_date)
        self.redirect('/dashboard')
    
    def handle_reset_balance(self):
        session_id = self.get_session_id()
        if session_id and session_id in self.sessions:
            user_id = self.sessions[session_id]
            self.db.reset_user_data(user_id)
        self.redirect('/dashboard')
    
    def handle_logout(self):
        session_id = self.get_session_id()
        if session_id and session_id in self.sessions:
            del self.sessions[session_id]
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'session_id=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()
    
    def get_session_id(self):
        cookie_header = self.headers.get('Cookie', '')
        for cookie in cookie_header.split(';'):
            if 'session_id=' in cookie:
                return cookie.split('session_id=')[1].strip()
        return None
    
    def redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()
    
    def serve_static_file(self, path):
        self.send_error(404)

def run_server():
    server_address = ('', 5000)
    httpd = HTTPServer(server_address, WebHandler)
    print("Servidor rodando em http://localhost:5000")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()