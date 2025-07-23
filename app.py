import os
import json
from datetime import datetime, date
from db.models import Database, User, Balance, Transaction, Goal, init_db, reset_db
from auth.auth import Auth
from dashboard.dashboard import Dashboard
from services.report import ReportService
from services.forecast import ForecastService

class SimpleFlask:
    """Simulação simples do Flask usando apenas bibliotecas padrão"""
    
    def __init__(self, name):
        self.name = name
        self.routes = {}
        self.session = {}
        self.request_data = {}
    
    def route(self, path, methods=['GET']):
        def decorator(func):
            self.routes[path] = {'func': func, 'methods': methods}
            return func
        return decorator
    
    def run(self, debug=False, port=5000):
        print(f"Aplicação {self.name} iniciada!")
        print(f"Simulando servidor na porta {port}")
        print("Para testar as funcionalidades, use os métodos da classe diretamente.")
        
        # Demonstração das funcionalidades
        self.demo_functionality()
    
    def demo_functionality(self):
        """Demonstra as funcionalidades do sistema"""
        print("\n=== DEMONSTRAÇÃO DO SISTEMA GERENCIADOR DE BANCA ===\n")
        
        # Inicializa componentes
        db = Database()
        auth = Auth(db)
        dashboard = Dashboard(db)
        
        # Teste de registro de usuário
        print("1. Testando registro de usuário...")
        if auth.register('usuario_teste', 'senha123'):
            print("✅ Usuário registrado com sucesso!")
        else:
            print("❌ Erro no registro (usuário pode já existir)")
        
        # Teste de login
        print("\n2. Testando login...")
        user = auth.login('usuario_teste', 'senha123')
        if user:
            print(f"✅ Login realizado com sucesso! ID: {user['id']}")
            user_id = user['id']
        else:
            print("❌ Erro no login")
            return
        
        # Teste de adição de saldo
        print("\n3. Testando adição de saldos...")
        balance_service = Balance(db)
        dates = ['2024-01-01', '2024-01-02', '2024-01-03']
        amounts = [1000, 1100, 950]
        
        for date_str, amount in zip(dates, amounts):
            if balance_service.add_balance(user_id, date_str, amount):
                print(f"✅ Saldo adicionado: {date_str} - R$ {amount}")
        
        # Teste de transações
        print("\n4. Testando transações...")
        transaction_service = Transaction(db)
        
        transactions = [
            ('2024-01-01', 'deposit', 500, 'Depósito inicial'),
            ('2024-01-02', 'withdrawal', 200, 'Saque para despesas'),
            ('2024-01-03', 'deposit', 300, 'Lucro do dia')
        ]
        
        for date_str, type_, amount, desc in transactions:
            if transaction_service.add_transaction(user_id, date_str, type_, amount, desc):
                print(f"✅ Transação adicionada: {type_} R$ {amount} em {date_str}")
        
        # Teste de meta
        print("\n5. Testando definição de meta...")
        goal_service = Goal(db)
        if goal_service.set_goal(user_id, 5000):
            print("✅ Meta definida: R$ 5.000")
        
        # Teste de relatórios
        print("\n6. Testando geração de relatórios...")
        try:
            report_service = ReportService(db)
            metrics = report_service.get_user_metrics(user_id)
            print(f"✅ Métricas calculadas:")
            print(f"   - Saldo atual: R$ {metrics.get('current_balance', 0):.2f}")
            print(f"   - Lucro total: R$ {metrics.get('total_profit', 0):.2f}")
            print(f"   - Total de depósitos: R$ {metrics.get('total_deposits', 0):.2f}")
            print(f"   - Total de saques: R$ {metrics.get('total_withdrawals', 0):.2f}")
        except Exception as e:
            print(f"❌ Erro nos relatórios: {e}")
        
        # Teste de previsão
        print("\n7. Testando previsão...")
        try:
            forecast_service = ForecastService(db)
            goal = goal_service.get_goal(user_id)
            if goal:
                prediction = forecast_service.predict_goal_date(user_id, goal['target_amount'])
                if prediction:
                    print(f"✅ Previsão para alcançar meta: {prediction}")
                else:
                    print("⚠️ Não foi possível calcular previsão (dados insuficientes)")
        except Exception as e:
            print(f"❌ Erro na previsão: {e}")
        
        print("\n=== DEMONSTRAÇÃO CONCLUÍDA ===")
        print("\nTodas as funcionalidades principais foram testadas!")
        print("Os dados foram salvos em 'data.json'")

# Instância da aplicação
app = SimpleFlask(__name__)

# Inicialização do banco de dados
db = Database()

# Instâncias dos serviços
auth = Auth(db)
dashboard = Dashboard(db)
report_service = ReportService(db)
forecast_service = ForecastService(db)

@app.route('/')
def index():
    return "Sistema Gerenciador de Banca - Funcionando!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Simulação de registro
    return "Página de registro"

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Simulação de login
    return "Página de login"

@app.route('/dashboard')
def dashboard_view():
    # Simulação do dashboard
    return "Dashboard do usuário"

def init_database():
    """Comando para inicializar banco de dados"""
    init_db()

def reset_database():
    """Comando para resetar banco de dados"""
    reset_db()

if __name__ == '__main__':
    import sys
    
    # Verifica se é comando de inicialização
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init-db':
            init_database()
        elif sys.argv[1] == 'reset-db':
            reset_database()
        else:
            print("Comandos disponíveis:")
            print("  python app.py init-db  - Inicializa o banco de dados")
            print("  python app.py reset-db - Reseta o banco de dados")
    else:
        # Executa a aplicação
        app.run(debug=True)