import json
import os
from datetime import datetime, date
from typing import List, Dict, Optional, Any

class Database:
    def __init__(self, db_path: str = 'data.json'):
        self.db_path = db_path
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Carrega dados do arquivo JSON ou cria estrutura inicial"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Estrutura inicial do banco de dados
        return {
            'users': [],
            'balances': [],
            'transactions': [],
            'goals': []
        }
    
    def _save_data(self):
        """Salva dados no arquivo JSON"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
        except IOError as e:
            print(f"Erro ao salvar dados: {e}")
    
    def _get_next_id(self, table: str) -> int:
        """Gera próximo ID para uma tabela"""
        if not self.data[table]:
            return 1
        return max(item.get('id', 0) for item in self.data[table]) + 1

class User:
    def __init__(self, db: Database):
        self.db = db
    
    def create_user(self, username: str, password: str) -> bool:
        """Cria um novo usuário"""
        # Verifica se usuário já existe
        if self.get_user_by_username(username):
            return False
        
        user = {
            'id': self.db._get_next_id('users'),
            'username': username,
            'password': password,  # Em produção, usar hash
            'created_at': datetime.now().isoformat()
        }
        
        self.db.data['users'].append(user)
        self.db._save_data()
        return True
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Busca usuário por nome"""
        for user in self.db.data['users']:
            if user['username'] == username:
                return user
        return None
    
    def validate_user(self, username: str, password: str) -> Optional[Dict]:
        """Valida credenciais do usuário"""
        user = self.get_user_by_username(username)
        if user and user['password'] == password:
            return user
        return None

class Balance:
    def __init__(self, db: Database):
        self.db = db
    
    def add_balance(self, user_id: int, date_str: str, amount: float, 
                   deposits: float = 0, withdrawals: float = 0) -> bool:
        """Adiciona ou atualiza saldo diário"""
        try:
            # Verifica se já existe saldo para esta data
            existing = self.get_balance_by_date(user_id, date_str)
            
            if existing:
                # Atualiza saldo existente
                existing['amount'] = float(amount)
                existing['deposits'] = float(deposits)
                existing['withdrawals'] = float(withdrawals)
                existing['updated_at'] = datetime.now().isoformat()
            else:
                # Cria novo saldo
                balance = {
                    'id': self.db._get_next_id('balances'),
                    'user_id': user_id,
                    'date': date_str,
                    'amount': float(amount),
                    'deposits': float(deposits),
                    'withdrawals': float(withdrawals),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                self.db.data['balances'].append(balance)
            
            self.db._save_data()
            return True
        except (ValueError, TypeError):
            return False
    
    def get_balance_by_date(self, user_id: int, date_str: str) -> Optional[Dict]:
        """Busca saldo por data"""
        for balance in self.db.data['balances']:
            if balance['user_id'] == user_id and balance['date'] == date_str:
                return balance
        return None
    
    def get_balances_by_user(self, user_id: int) -> List[Dict]:
        """Busca todos os saldos de um usuário"""
        balances = [b for b in self.db.data['balances'] if b['user_id'] == user_id]
        return sorted(balances, key=lambda x: x['date'])
    
    def delete_balance(self, balance_id: int, user_id: int) -> bool:
        """Remove um saldo"""
        for i, balance in enumerate(self.db.data['balances']):
            if balance['id'] == balance_id and balance['user_id'] == user_id:
                del self.db.data['balances'][i]
                self.db._save_data()
                return True
        return False
    
    def sync_balance_from_transactions(self, user_id: int, date_str: str):
        """Sincroniza saldo baseado nas transações do dia"""
        transactions = Transaction(self.db).get_transactions_by_date(user_id, date_str)
        
        total_deposits = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
        total_withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'withdrawal')
        
        # Busca saldo anterior para calcular novo saldo
        previous_balance = self.get_previous_balance(user_id, date_str)
        base_amount = previous_balance['amount'] if previous_balance else 0
        
        new_amount = base_amount + total_deposits - total_withdrawals
        
        self.add_balance(user_id, date_str, new_amount, total_deposits, total_withdrawals)
    
    def get_previous_balance(self, user_id: int, date_str: str) -> Optional[Dict]:
        """Busca o saldo do dia anterior"""
        balances = self.get_balances_by_user(user_id)
        previous = None
        
        for balance in balances:
            if balance['date'] < date_str:
                previous = balance
            else:
                break
        
        return previous

class Transaction:
    def __init__(self, db: Database):
        self.db = db
    
    def add_transaction(self, user_id: int, date_str: str, type_: str, 
                       amount: float, description: str = '') -> bool:
        """Adiciona uma nova transação"""
        try:
            transaction = {
                'id': self.db._get_next_id('transactions'),
                'user_id': user_id,
                'date': date_str,
                'type': type_,  # 'deposit' ou 'withdrawal'
                'amount': float(amount),
                'description': description,
                'created_at': datetime.now().isoformat()
            }
            
            self.db.data['transactions'].append(transaction)
            self.db._save_data()
            
            # Atualiza saldo automaticamente
            Balance(self.db).sync_balance_from_transactions(user_id, date_str)
            
            return True
        except (ValueError, TypeError):
            return False
    
    def get_transactions_by_user(self, user_id: int) -> List[Dict]:
        """Busca todas as transações de um usuário"""
        transactions = [t for t in self.db.data['transactions'] if t['user_id'] == user_id]
        return sorted(transactions, key=lambda x: (x['date'], x['created_at']), reverse=True)
    
    def get_transactions_by_date(self, user_id: int, date_str: str) -> List[Dict]:
        """Busca transações por data"""
        return [t for t in self.db.data['transactions'] 
                if t['user_id'] == user_id and t['date'] == date_str]
    
    def update_transaction(self, transaction_id: int, user_id: int, 
                          date_str: str, type_: str, amount: float, 
                          description: str = '') -> bool:
        """Atualiza uma transação"""
        try:
            for transaction in self.db.data['transactions']:
                if transaction['id'] == transaction_id and transaction['user_id'] == user_id:
                    old_date = transaction['date']
                    
                    transaction['date'] = date_str
                    transaction['type'] = type_
                    transaction['amount'] = float(amount)
                    transaction['description'] = description
                    transaction['updated_at'] = datetime.now().isoformat()
                    
                    self.db._save_data()
                    
                    # Recalcula saldos das datas afetadas
                    Balance(self.db).sync_balance_from_transactions(user_id, old_date)
                    if old_date != date_str:
                        Balance(self.db).sync_balance_from_transactions(user_id, date_str)
                    
                    return True
            return False
        except (ValueError, TypeError):
            return False
    
    def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Remove uma transação"""
        for i, transaction in enumerate(self.db.data['transactions']):
            if transaction['id'] == transaction_id and transaction['user_id'] == user_id:
                date_str = transaction['date']
                del self.db.data['transactions'][i]
                self.db._save_data()
                
                # Recalcula saldo da data afetada
                Balance(self.db).sync_balance_from_transactions(user_id, date_str)
                
                return True
        return False

class Goal:
    def __init__(self, db: Database):
        self.db = db
    
    def set_goal(self, user_id: int, target_amount: float) -> bool:
        """Define ou atualiza meta do usuário"""
        try:
            # Remove meta anterior se existir
            self.db.data['goals'] = [g for g in self.db.data['goals'] if g['user_id'] != user_id]
            
            goal = {
                'id': self.db._get_next_id('goals'),
                'user_id': user_id,
                'target_amount': float(target_amount),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.db.data['goals'].append(goal)
            self.db._save_data()
            return True
        except (ValueError, TypeError):
            return False
    
    def get_goal(self, user_id: int) -> Optional[Dict]:
        """Busca meta do usuário"""
        for goal in self.db.data['goals']:
            if goal['user_id'] == user_id:
                return goal
        return None
    
    def delete_goal(self, user_id: int) -> bool:
        """Remove meta do usuário"""
        initial_count = len(self.db.data['goals'])
        self.db.data['goals'] = [g for g in self.db.data['goals'] if g['user_id'] != user_id]
        
        if len(self.db.data['goals']) < initial_count:
            self.db._save_data()
            return True
        return False

def init_db():
    """Inicializa o banco de dados"""
    db = Database()
    print("Banco de dados inicializado com sucesso!")
    return db

def reset_db():
    """Reseta o banco de dados"""
    if os.path.exists('data.json'):
        os.remove('data.json')
    db = Database()
    print("Banco de dados resetado com sucesso!")
    return db