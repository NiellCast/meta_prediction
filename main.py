# main.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import logging
from functools import wraps
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from auth_services import init_auth, login_user_service, register_user_service
from banca_services import banca_manager
from forms import TransacaoForm, SaldoForm, MetaForm, LoginForm, RegisterForm
from models import db, User, Saldo, Transacao, Meta

from flask_talisman import Talisman  # Para cabeçalhos de segurança

# Inicializar a aplicação Flask corretamente
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta'  # Alterar para uma chave secreta forte em produção

# Configuração do banco de dados (Exemplo usando SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///previsao_meta.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar Extensões
db.init_app(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
talisman = Talisman(app, content_security_policy=None)  # Configuração básica

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)


def login_required(f):
    """
    Decorator para rotas que exigem login.
    Retorna 401 JSON se não estiver logado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({"status": "error", "message": "Faça login primeiro."}), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(required_role):
    """
    Decorator para rotas que exigem um determinado papel de usuário.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return jsonify({"status": "error", "message": "Faça login primeiro."}), 401
            user_id = session.get('user_id')
            user = User.query.get(user_id)
            if not user or user.role != required_role:
                return jsonify({"status": "error", "message": "Acesso não autorizado."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Context Processor para injetar o token CSRF em todos os templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())


# ----------------------------------
# ROTA PRINCIPAL
# ----------------------------------

@app.route('/')
def index():
    """
    Redireciona para /banca se logado, ou para /login se não logado.
    """
    if session.get('logged_in'):
        return redirect(url_for('banca_page'))
    else:
        return redirect(url_for('login_page'))


# ----------------------------------
# LOGIN E REGISTRO
# ----------------------------------

@app.route('/login', methods=['GET'])
def login_page():
    """
    Exibe a página de login.
    """
    if session.get('logged_in'):
        return redirect(url_for('banca_page'))
    return render_template('login.html')  # Certifique-se de ter esse template


@app.route('/login', methods=['POST'])
def login_post():
    """
    Processa o login usando auth_services.
    """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = login_user_service(username, password, bcrypt)
        if user:
            session['logged_in'] = True
            session['user_id'] = user.id
            return jsonify({"status": "success", "message": f"Bem-vindo, {user.username}!"}), 200
        else:
            return jsonify({"status": "error", "message": "Credenciais inválidas"}), 401
    else:
        logging.error(f"Falha na validação do formulário de login: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos fornecidos.", "errors": form.errors}), 400


@app.route('/register', methods=['GET'])
def register_page():
    """
    Exibe a página de registro.
    """
    if session.get('logged_in'):
        return redirect(url_for('banca_page'))
    return render_template('register.html')  # Certifique-se de ter esse template


@app.route('/register', methods=['POST'])
def register_post():
    """
    Processa o registro de um novo usuário.
    """
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        try:
            # Gerar o hash da senha usando Flask-Bcrypt
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Salvar o usuário no banco de dados usando auth_services
            user = register_user_service(username, email, hashed_password)
            session['logged_in'] = True
            session['user_id'] = user.id
            return jsonify({"status": "success", "message": f"Usuário {user.username} registrado com sucesso!"}), 200
        except IntegrityError:
            db.session.rollback()
            logging.error(f"Erro em /register: Nome de usuário ou e-mail já existe.")
            return jsonify({"status": "error", "message": "Nome de usuário ou e-mail já está em uso."}), 400
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro em /register: {e}")
            return jsonify({"status": "error", "message": "Erro ao registrar usuário."}), 400
    else:
        logging.error(f"Falha na validação do formulário de registro: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos fornecidos.", "errors": form.errors}), 400


@app.route('/logout', methods=['POST'])
def logout():
    """
    Faz logout limpando a sessão.
    """
    session.clear()
    return jsonify({"status":"success","message":"Deslogado"}), 200


# ----------------------------------
# ROTAS PRINCIPAIS DE BANCA
# ----------------------------------

@app.route('/banca')
@login_required
def banca_page():
    """
    Exibe a página principal da aplicação (banca.html).
    """
    return render_template('banca.html')  # Certifique-se de ter esse template


# ----------------------------------
# ROTAS DE BANCA - Adicionar Saldo
# ----------------------------------

@app.route('/add_saldo', methods=['POST'])
@login_required
def add_saldo():
    """
    Adiciona um novo saldo diário.
    """
    form = SaldoForm()
    if form.validate_on_submit():
        user_id = session['user_id']
        data = form.data.data  # DateField pode ser None
        if data:
            data_str = data.strftime('%Y-%m-%d')
        else:
            data_str = datetime.now().strftime('%Y-%m-%d')  # Data atual
        saldo_valor = float(form.saldo.data)
        try:
            banca_manager.process_add_saldo(user_id, data_str, saldo_valor)
            return jsonify({"status": "success", "message": "Saldo diário salvo com sucesso!"}), 200
        except Exception as e:
            logging.error(f"Erro em /add_saldo: {e}")
            return jsonify({"status": "error", "message": "Erro ao salvar saldo diário."}), 400
    else:
        logging.error(f"Falha na validação do formulário de saldo: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos fornecidos.", "errors": form.errors}), 400


# ----------------------------------
# ROTAS DE BANCA - Obter Saldos
# ----------------------------------

@app.route('/get_saldos', methods=['GET'])
@login_required
def get_saldos_route():
    """
    Retorna os saldos do usuário em formato JSON.
    """
    user_id = session['user_id']
    saldos = banca_manager.get_saldos_ordenados(user_id)
    saldos_list = [{"id": saldo.id, "data": saldo.data.strftime('%d/%m/%Y'), "valor": float(saldo.valor)} for saldo in saldos]
    return jsonify(saldos_list), 200


# ----------------------------------
# ROTAS DE BANCA - Deletar Saldo
# ----------------------------------

@app.route('/delete_saldo/<int:id_>', methods=['DELETE'])
@login_required
def delete_saldo_route(id_):
    """
    Deleta um saldo específico.
    """
    user_id = session['user_id']
    try:
        banca_manager.delete_saldo(user_id, id_)
        return jsonify({"status": "success", "message": "Saldo excluído com sucesso!"}), 200
    except ValueError as ve:
        logging.error(f"Erro em /delete_saldo/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /delete_saldo/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao excluir saldo."}), 400


# ----------------------------------
# ROTAS DE BANCA - Atualizar Saldo
# ----------------------------------

@app.route('/update_saldo/<int:id_>', methods=['POST'])
@login_required
def update_saldo_route(id_):
    """
    Atualiza o valor de um saldo específico.
    """
    user_id = session['user_id']
    novo_valor = request.form.get('novo_valor')
    if not novo_valor:
        return jsonify({"status": "error", "message": "Novo valor não fornecido."}), 400
    try:
        novo_valor_float = float(novo_valor)
        banca_manager.update_saldo(user_id, id_, novo_valor_float)
        return jsonify({"status": "success", "message": "Saldo atualizado com sucesso!"}), 200
    except ValueError as ve:
        logging.error(f"Erro em /update_saldo/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /update_saldo/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao atualizar saldo."}), 400


# ----------------------------------
# ROTAS DE BANCA - Adicionar Transação
# ----------------------------------

@app.route('/add_transacao', methods=['POST'])
@login_required
def add_transacao_route():
    """
    Adiciona uma nova transação.
    """
    form = TransacaoForm()
    if form.validate_on_submit():
        user_id = session['user_id']
        tipo = form.tipo.data
        valor = float(form.valor.data)
        data_transacao = form.data.data  # DateField pode ser None
        if not data_transacao:
            data_transacao = datetime.now().date()  # Data atual
        try:
            banca_manager.process_add_transacao(user_id, tipo, valor, data_transacao)
            return jsonify({"status": "success", "message": "Transação adicionada com sucesso!"}), 200
        except TypeError as te:
            logging.error(f"Erro em /add_transacao: {te}")
            return jsonify({"status": "error", "message": str(te)}), 400
        except Exception as e:
            logging.error(f"Erro em /add_transacao: {e}")
            return jsonify({"status": "error", "message": "Erro ao adicionar transação."}), 400
    else:
        logging.error(f"Falha na validação do formulário de transação: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos fornecidos.", "errors": form.errors}), 400


# ----------------------------------
# ROTAS DE BANCA - Obter Transações
# ----------------------------------

@app.route('/get_transacoes', methods=['GET'])
@login_required
def get_transacoes_route():
    """
    Retorna as transações do usuário em formato JSON.
    """
    user_id = session['user_id']
    transacoes = banca_manager.get_transacoes_ordenadas(user_id)
    transacoes_list = [{
        "id": trans.id,
        "tipo": trans.tipo,
        "valor": float(trans.valor),
        "data": trans.data.strftime('%d/%m/%Y')  # Formatação de data
    } for trans in transacoes]
    return jsonify(transacoes_list), 200


# ----------------------------------
# ROTAS DE BANCA - Atualizar Meta
# ----------------------------------

@app.route('/update_meta', methods=['POST'])
@login_required
def update_meta_route():
    """
    Atualiza a meta do usuário.
    """
    form = MetaForm()
    if form.validate_on_submit():
        user_id = session['user_id']
        nova_meta = float(form.nova_meta.data)
        try:
            banca_manager.process_update_meta(user_id, nova_meta)
            return jsonify({
                "status": "success",
                "message": "Meta atualizada com sucesso!",
                "meta": f"{nova_meta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            }), 200
        except Exception as e:
            logging.error(f"Erro em /update_meta: {e}")
            return jsonify({"status": "error", "message": "Erro ao atualizar meta."}), 400
    else:
        logging.error(f"Falha na validação do formulário de meta: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos fornecidos.", "errors": form.errors}), 400


# ----------------------------------
# ROTAS DE BANCA - Deletar Todas as Saldos
# ----------------------------------

@app.route('/delete_all_saldos', methods=['POST'])
@login_required
def delete_all_saldos_route():
    """
    Deleta todos os saldos e transações do usuário e reseta a meta.
    """
    user_id = session['user_id']
    try:
        banca_manager.process_delete_all_saldos(user_id)
        return jsonify({"status": "success", "message": "Banca zerada com sucesso!"}), 200
    except Exception as e:
        logging.error(f"Erro em /delete_all_saldos: {e}")
        return jsonify({"status": "error", "message": "Erro ao zerar a banca."}), 400


# ----------------------------------
# ROTAS DE BANCA - Atualizar Transação
# ----------------------------------

@app.route('/update_transacao/<int:id_>', methods=['POST'])
@login_required
def update_transacao_route(id_):
    """
    Atualiza o valor e/ou tipo de uma transação específica.
    """
    user_id = session['user_id']
    novo_valor = request.form.get('novo_valor')
    novo_tipo = request.form.get('novo_tipo')  # Opcional
    if not novo_valor:
        return jsonify({"status": "error", "message": "Novo valor não fornecido."}), 400
    try:
        novo_valor_float = float(novo_valor)
        if novo_valor_float <= 0:
            raise ValueError("O valor da transação deve ser positivo.")
        banca_manager.update_transacao(user_id, id_, novo_valor_float, novo_tipo)
        return jsonify({"status": "success", "message": "Transação atualizada com sucesso!"}), 200
    except ValueError as ve:
        logging.error(f"Erro em /update_transacao/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /update_transacao/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao atualizar transação."}), 400


# ----------------------------------
# ROTAS DE BANCA - Deletar Transação
# ----------------------------------

@app.route('/delete_transacao/<int:id_>', methods=['DELETE'])
@login_required
def delete_transacao_route(id_):
    """
    Deleta uma transação específica.
    """
    user_id = session['user_id']
    try:
        banca_manager.delete_transacao(user_id, id_)
        return jsonify({"status": "success", "message": "Transação excluída com sucesso!"}), 200
    except ValueError as ve:
        logging.error(f"Erro em /delete_transacao/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /delete_transacao/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao excluir transação."}), 400


# ----------------------------------
# INICIALIZAÇÃO
# ----------------------------------

@app.before_request
def initialize():
    """
    Inicializa o banco de dados e outras configurações antes de cada pedido.
    """
    if not hasattr(app, 'initialized'):
        init_auth(app, db)
        banca_manager.initialize(app, db)
        app.initialized = True


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)


# Melhorias aplicadas ao arquivo