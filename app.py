#!/usr/bin/env python3
"""
Sistema de Gerenciamento de Banca Esportiva - Versão CLI
Aplicação de linha de comando para gerenciar banca esportiva sem dependências de rede.
"""

import json
import os
import sys
from datetime import datetime, timedelta
import hashlib

# Importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.models import Database
from services.forecast_engine import ForecastEngine
from services.report import ReportService

class BankingCLI:
    def __init__(self):
        self.db = Database()
        self.forecast_engine = ForecastEngine()
        self.report_service = ReportService()
        self.current_user = None
        
    def hash_password(self, password):
        """Hash da senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def clear_screen(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_currency(self, value):
        """Formata valor como moeda brasileira"""
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def print_header(self, title):
        """Imprime cabeçalho formatado"""
        print("\n" + "="*60)
        print(f"  {title.upper()}")
        print("="*60)
    
    def print_menu(self, title, options):
        """Imprime menu formatado"""
        self.print_header(title)
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print(f"  0. Voltar/Sair")
        print("-"*60)
    
    def get_input(self, prompt, input_type=str, required=True):
        """Obtém entrada do usuário com validação"""
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                if not value and required:
                    print("❌ Este campo é obrigatório!")
                    continue
                if input_type == float:
                    return float(value.replace(',', '.'))
                elif input_type == int:
                    return int(value)
                return value
            except ValueError:
                print(f"❌ Valor inválido! Digite um {input_type.__name__} válido.")
    
    def register(self):
        """Registro de novo usuário"""
        self.print_header("REGISTRO DE USUÁRIO")
        
        username = self.get_input("Nome de usuário")
        
        # Verificar se usuário já existe
        if self.db.get_user_by_username(username):
            print("❌ Usuário já existe!")
            return False
        
        password = self.get_input("Senha")
        email = self.get_input("Email")
        
        # Criar usuário
        user_data = {
            'username': username,
            'password': self.hash_password(password),
            'email': email
        }
        
        user_id = self.db.create_user(user_data)
        if user_id:
            print("✅ Usuário registrado com sucesso!")
            return True
        else:
            print("❌ Erro ao registrar usuário!")
            return False
    
    def login(self):
        """Login do usuário"""
        self.print_header("LOGIN")
        
        username = self.get_input("Nome de usuário")
        password = self.get_input("Senha")
        
        user = self.db.get_user_by_username(username)
        if user and user['password'] == self.hash_password(password):
            self.current_user = user
            print(f"✅ Bem-vindo, {username}!")
            return True
        else:
            print("❌ Credenciais inválidas!")
            return False
    
    def show_dashboard(self):
        """Exibe dashboard principal"""
        if not self.current_user:
            return
        
        user_id = self.current_user['id']
        
        # Obter dados
        balances = self.db.get_balances_by_user(user_id)
        transactions = self.db.get_transactions_by_user(user_id)
        goals = self.db.get_goals_by_user(user_id)
        
        self.print_header(f"DASHBOARD - {self.current_user['username']}")
        
        # Saldo atual
        current_balance = balances[-1]['amount'] if balances else 0
        print(f"💰 Saldo Atual: {self.format_currency(current_balance)}")
        
        # Estatísticas
        if balances:
            initial_balance = balances[0]['amount']
            profit_loss = current_balance - initial_balance
            profit_percentage = (profit_loss / initial_balance * 100) if initial_balance > 0 else 0
            
            print(f"📈 Lucro/Prejuízo: {self.format_currency(profit_loss)}")
            print(f"📊 Percentual: {profit_percentage:.2f}%")
        
        # Transações recentes
        if transactions:
            print(f"\n📋 Últimas {min(5, len(transactions))} transações:")
            for transaction in transactions[-5:]:
                date = transaction['date']
                type_symbol = "💰" if transaction['type'] == 'deposit' else "💸"
                print(f"  {type_symbol} {date}: {self.format_currency(transaction['amount'])}")
        
        # Metas
        if goals:
            print(f"\n🎯 Metas ativas: {len(goals)}")
            for goal in goals:
                progress = (current_balance / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
                print(f"  • {goal['description']}: {progress:.1f}% ({self.format_currency(goal['target_amount'])})")
        
        print("-"*60)
    
    def add_balance(self):
        """Adiciona saldo diário"""
        self.print_header("ADICIONAR SALDO DIÁRIO")
        
        amount = self.get_input("Valor do saldo", float)
        date = self.get_input("Data (YYYY-MM-DD) ou Enter para hoje", str, False)
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        balance_data = {
            'user_id': self.current_user['id'],
            'date': date,
            'amount': amount
        }
        
        if self.db.create_balance(balance_data):
            print(f"✅ Saldo de {self.format_currency(amount)} adicionado para {date}!")
        else:
            print("❌ Erro ao adicionar saldo!")
    
    def add_transaction(self):
        """Adiciona transação"""
        self.print_header("ADICIONAR TRANSAÇÃO")
        
        print("Tipo de transação:")
        print("1. Depósito")
        print("2. Saque")
        
        choice = self.get_input("Escolha", int)
        if choice not in [1, 2]:
            print("❌ Opção inválida!")
            return
        
        transaction_type = 'deposit' if choice == 1 else 'withdrawal'
        amount = self.get_input("Valor", float)
        description = self.get_input("Descrição", str, False)
        
        transaction_data = {
            'user_id': self.current_user['id'],
            'type': transaction_type,
            'amount': amount,
            'description': description or f"{'Depósito' if choice == 1 else 'Saque'} via CLI",
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if self.db.create_transaction(transaction_data):
            print(f"✅ {'Depósito' if choice == 1 else 'Saque'} de {self.format_currency(amount)} registrado!")
        else:
            print("❌ Erro ao registrar transação!")
    
    def add_goal(self):
        """Adiciona meta"""
        self.print_header("DEFINIR META")
        
        description = self.get_input("Descrição da meta")
        target_amount = self.get_input("Valor alvo", float)
        target_date = self.get_input("Data alvo (YYYY-MM-DD)", str)
        
        goal_data = {
            'user_id': self.current_user['id'],
            'description': description,
            'target_amount': target_amount,
            'target_date': target_date
        }
        
        if self.db.create_goal(goal_data):
            print(f"✅ Meta '{description}' de {self.format_currency(target_amount)} criada!")
        else:
            print("❌ Erro ao criar meta!")
    
    def show_forecast(self):
        """Exibe previsão"""
        self.print_header("PREVISÃO DE CRESCIMENTO")
        
        user_id = self.current_user['id']
        balances = self.db.get_balances_by_user(user_id)
        
        if len(balances) < 2:
            print("❌ Dados insuficientes para previsão (mínimo 2 registros de saldo)")
            return
        
        # Preparar dados para previsão
        dates = [datetime.strptime(b['date'], '%Y-%m-%d') for b in balances]
        amounts = [b['amount'] for b in balances]
        
        # Converter datas para números (dias desde o primeiro registro)
        base_date = dates[0]
        x_values = [(d - base_date).days for d in dates]
        
        # Fazer previsão
        try:
            forecast_data = self.forecast_engine.predict_balance_trend(x_values, amounts, days_ahead=30)
            
            print(f"📈 Tendência de crescimento:")
            print(f"   Coeficiente angular: {forecast_data['slope']:.4f}")
            print(f"   Intercepto: {self.format_currency(forecast_data['intercept'])}")
            
            print(f"\n🔮 Previsão para 30 dias:")
            for i, prediction in enumerate(forecast_data['predictions'][:7], 1):  # Mostrar apenas 7 dias
                future_date = datetime.now() + timedelta(days=i)
                print(f"   {future_date.strftime('%Y-%m-%d')}: {self.format_currency(prediction)}")
            
        except Exception as e:
            print(f"❌ Erro ao calcular previsão: {e}")
    
    def show_reports(self):
        """Exibe relatórios"""
        self.print_header("RELATÓRIOS")
        
        user_id = self.current_user['id']
        
        try:
            # Relatório de performance
            performance = self.report_service.generate_performance_report(user_id)
            
            print("📊 RELATÓRIO DE PERFORMANCE:")
            print(f"   Saldo inicial: {self.format_currency(performance.get('initial_balance', 0))}")
            print(f"   Saldo atual: {self.format_currency(performance.get('current_balance', 0))}")
            print(f"   Lucro/Prejuízo: {self.format_currency(performance.get('profit_loss', 0))}")
            print(f"   Percentual: {performance.get('profit_percentage', 0):.2f}%")
            
            # Relatório de transações
            transactions_report = self.report_service.generate_transactions_summary(user_id)
            
            print(f"\n💰 RESUMO DE TRANSAÇÕES:")
            print(f"   Total de depósitos: {self.format_currency(transactions_report.get('total_deposits', 0))}")
            print(f"   Total de saques: {self.format_currency(transactions_report.get('total_withdrawals', 0))}")
            print(f"   Número de transações: {transactions_report.get('transaction_count', 0)}")
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatórios: {e}")
    
    def reset_bank(self):
        """Reset da banca"""
        self.print_header("RESET DA BANCA")
        
        print("⚠️  ATENÇÃO: Esta ação irá apagar todos os seus dados!")
        confirm = self.get_input("Digite 'CONFIRMAR' para prosseguir", str, False)
        
        if confirm.upper() == 'CONFIRMAR':
            user_id = self.current_user['id']
            
            # Remover todos os dados do usuário
            self.db.data['balances'] = [b for b in self.db.data['balances'] if b['user_id'] != user_id]
            self.db.data['transactions'] = [t for t in self.db.data['transactions'] if t['user_id'] != user_id]
            self.db.data['goals'] = [g for g in self.db.data['goals'] if g['user_id'] != user_id]
            
            self.db.save_data()
            print("✅ Banca resetada com sucesso!")
        else:
            print("❌ Reset cancelado.")
    
    def main_menu(self):
        """Menu principal após login"""
        while True:
            self.clear_screen()
            self.show_dashboard()
            
            options = [
                "Adicionar Saldo Diário",
                "Adicionar Transação",
                "Definir Meta",
                "Ver Previsões",
                "Ver Relatórios",
                "Reset da Banca",
                "Logout"
            ]
            
            self.print_menu("MENU PRINCIPAL", options)
            
            try:
                choice = int(input("Escolha uma opção: "))
                
                if choice == 0 or choice == 7:  # Logout
                    self.current_user = None
                    break
                elif choice == 1:
                    self.add_balance()
                elif choice == 2:
                    self.add_transaction()
                elif choice == 3:
                    self.add_goal()
                elif choice == 4:
                    self.show_forecast()
                elif choice == 5:
                    self.show_reports()
                elif choice == 6:
                    self.reset_bank()
                else:
                    print("❌ Opção inválida!")
                
                if choice != 0 and choice != 7:
                    input("\nPressione Enter para continuar...")
                    
            except ValueError:
                print("❌ Digite um número válido!")
                input("Pressione Enter para continuar...")
    
    def run(self):
        """Executa a aplicação"""
        while True:
            self.clear_screen()
            
            options = [
                "Login",
                "Registrar novo usuário"
            ]
            
            self.print_menu("SISTEMA DE GERENCIAMENTO DE BANCA ESPORTIVA", options)
            
            try:
                choice = int(input("Escolha uma opção: "))
                
                if choice == 0:  # Sair
                    print("👋 Até logo!")
                    break
                elif choice == 1:  # Login
                    if self.login():
                        input("Pressione Enter para continuar...")
                        self.main_menu()
                elif choice == 2:  # Registro
                    if self.register():
                        input("Pressione Enter para continuar...")
                else:
                    print("❌ Opção inválida!")
                    input("Pressione Enter para continuar...")
                    
            except ValueError:
                print("❌ Digite um número válido!")
                input("Pressione Enter para continuar...")
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break

if __name__ == "__main__":
    app = BankingCLI()
    app.run()