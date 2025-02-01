import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect, generate_csrf
from sqlalchemy.exc import IntegrityError
from functools import wraps
import logging
from datetime import datetime, date

from models import db, User, Saldo, Transacao, Meta
from auth_services import init_auth, login_user_service, register_user_service
from banca_services import banca_manager
from forms import TransacaoForm, SaldoForm, MetaForm, LoginForm, RegisterForm

from flask_talisman import Talisman

# Inicialização da aplicação
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-padrao-insegura')
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'previsao_meta.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Garante que a pasta instance exista
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

# Inicializa extensões
db.init_app(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
talisman = Talisman(app, content_security_policy=None)

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Decorator para rotas que exigem login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
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

# Injeta o token CSRF em todos os templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

# -------------------------------------------------
# Rotas
# -------------------------------------------------

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('banca_page'))
    else:
        return redirect(url_for('login_page'))

# LOGIN e REGISTRO
@app.route('/login', methods=['GET'])
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('banca_page'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400

    data = request.get_json()
    form = LoginForm(data=data, meta={'csrf': False})
    if form.validate():
        username = form.username.data
        password = form.password.data
        user = login_user_service(username, password, bcrypt)
        if user:
            session['logged_in'] = True
            session['user_id'] = user.id
            logging.info(f"Usuário {username} logado com sucesso.")
            return jsonify({"status": "success", "message": f"Bem-vindo, {user.username}!"}), 200
        else:
            logging.warning(f"Falha no login para usuário {username}.")
            return jsonify({"status": "error", "message": "Credenciais inválidas"}), 401
    else:
        logging.error(f"Erro de validação no login: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos fornecidos.", "errors": form.errors}), 400

@app.route('/register', methods=['GET'])
def register_page():
    if session.get('logged_in'):
        return redirect(url_for('banca_page'))
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400

    data = request.get_json()
    form = RegisterForm(data=data, meta={'csrf': False})
    if form.validate():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        try:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = register_user_service(username, email, hashed_password)
            logging.info(f"Usuário {username} registrado com sucesso.")
            return jsonify({"status": "success", "message": f"Usuário {user.username} registrado com sucesso!"}), 200
        except IntegrityError:
            db.session.rollback()
            logging.error("Erro: Nome de usuário ou e-mail já existe.")
            return jsonify({"status": "error", "message": "Nome de usuário ou e-mail já está em uso."}), 400
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro no registro: {e}")
            return jsonify({"status": "error", "message": "Erro ao registrar usuário."}), 400
    else:
        logging.error(f"Erro de validação no registro: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos fornecidos.", "errors": form.errors}), 400

@app.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    session.clear()
    logging.info(f"Usuário ID {user_id} deslogado.")
    return jsonify({"status": "success", "message": "Deslogado"}), 200

# Dados Gerais
@app.route('/get_dados', methods=['GET'])
@login_required
def get_dados():
    user_id = session['user_id']
    try:
        total_banca = banca_manager.get_valor_total_banca(user_id)
        depositos = banca_manager.get_total_depositos(user_id)
        saques = banca_manager.get_total_saques(user_id)
        lucro = depositos - saques
        meta = banca_manager.get_meta(user_id)
        porcentagem_ganho = (lucro / depositos * 100) if depositos > 0 else 0

        dados = {
            "total_banca": f"{total_banca:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "depositos": f"{depositos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "saques": f"{saques:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "lucro": f"{lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "porcentagem_ganho": f"{porcentagem_ganho:.2f}%",
            "meta": f"{meta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        }
        logging.info(f"Dados carregados para usuário ID {user_id}.")
        return jsonify(dados), 200
    except Exception as e:
        logging.error(f"Erro em /get_dados: {e}")
        return jsonify({"status": "error", "message": "Erro ao obter dados gerais."}), 400

# Evolução da Banca
@app.route('/get_evolucao', methods=['GET'])
@login_required
def get_evolucao_route():
    user_id = session['user_id']
    try:
        evolucao = banca_manager.get_evolucao(user_id)
        logging.info(f"Evolução carregada para usuário ID {user_id}.")
        return jsonify(evolucao), 200
    except Exception as e:
        logging.error(f"Erro em /get_evolucao: {e}")
        return jsonify({"status": "error", "message": "Erro ao obter evolução da banca."}), 400

# Previsão da IA
@app.route('/get_previsao_ia', methods=['GET'])
@login_required
def get_previsao_ia_route():
    user_id = session['user_id']
    try:
        previsao = banca_manager.get_previsao_ia(user_id)
        previsao_formatada = f"{previsao:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        logging.info(f"Previsão IA para usuário ID {user_id}: R$ {previsao_formatada}")
        return jsonify({"previsao": previsao_formatada}), 200
    except Exception as e:
        logging.error(f"Erro em /get_previsao_ia: {e}")
        return jsonify({"status": "error", "message": "Erro ao obter previsão da IA."}), 400

# Página de Banca
@app.route('/banca')
@login_required
def banca_page():
    return render_template('banca.html')

# Rotas de Saldo
@app.route('/add_saldo', methods=['POST'])
@login_required
def add_saldo():
    if not request.is_json:
        logging.warning("Requisição inválida em /add_saldo: Não é JSON.")
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400

    data = request.get_json()
    form = SaldoForm(data=data, meta={'csrf': False})
    if form.validate():
        user_id = session['user_id']
        data_saldo = form.data_saldo.data.strftime('%Y-%m-%d')
        saldo_valor = float(form.saldo.data)
        try:
            banca_manager.process_add_saldo(user_id, data_saldo, saldo_valor)
            logging.info(f"Saldo de R$ {saldo_valor} adicionado para usuário ID {user_id}.")
            return jsonify({"status": "success", "message": "Saldo diário salvo com sucesso!"}), 200
        except Exception as e:
            logging.error(f"Erro em /add_saldo: {e}")
            return jsonify({"status": "error", "message": "Erro ao salvar saldo diário."}), 400
    else:
        logging.error(f"Erro de validação no formulário de saldo: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos.", "errors": form.errors}), 400

@app.route('/get_saldos', methods=['GET'])
@login_required
def get_saldos_route():
    user_id = session['user_id']
    try:
        saldos = banca_manager.get_saldos_ordenados(user_id)
        saldos_list = [{"id": s.id, "data": s.data.strftime('%d/%m/%Y'), "valor": float(s.valor)} for s in saldos]
        logging.info(f"Saldos carregados para usuário ID {user_id}.")
        return jsonify(saldos_list), 200
    except Exception as e:
        logging.error(f"Erro em /get_saldos: {e}")
        return jsonify({"status": "error", "message": "Erro ao obter saldos."}), 400

@app.route('/delete_saldo/<int:id_>', methods=['DELETE'])
@login_required
def delete_saldo_route(id_):
    user_id = session['user_id']
    try:
        banca_manager.delete_saldo(user_id, id_)
        logging.info(f"Saldo ID {id_} excluído para usuário ID {user_id}.")
        return jsonify({"status": "success", "message": "Saldo excluído com sucesso!"}), 200
    except ValueError as ve:
        logging.warning(f"Erro em /delete_saldo/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /delete_saldo/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao excluir saldo."}), 400

@app.route('/update_saldo/<int:id_>', methods=['POST'])
@login_required
def update_saldo_route(id_):
    if not request.is_json:
        logging.warning(f"Requisição inválida em /update_saldo/{id_}: Não é JSON.")
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400

    data = request.get_json()
    novo_valor = data.get('novo_valor')
    nova_data = data.get('nova_data')
    if novo_valor is None or nova_data is None:
        logging.warning(f"Dados incompletos em /update_saldo/{id_}.")
        return jsonify({"status": "error", "message": "Novo valor e nova data não fornecidos."}), 400

    try:
        novo_valor_float = float(novo_valor)
        if novo_valor_float < 0:
            raise ValueError("Valor deve ser positivo.")
        banca_manager.update_saldo(session['user_id'], id_, novo_valor_float, nova_data)
        logging.info(f"Saldo ID {id_} atualizado para R$ {novo_valor_float} e data {nova_data} para usuário ID {session['user_id']}.")
        return jsonify({"status": "success", "message": "Saldo atualizado com sucesso!"}), 200
    except ValueError as ve:
        logging.warning(f"Erro em /update_saldo/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /update_saldo/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao atualizar saldo."}), 400

# Rotas de Transação
@app.route('/add_transacao', methods=['POST'])
@login_required
def add_transacao_route():
    if not request.is_json:
        logging.warning("Requisição inválida em /add_transacao: Não é JSON.")
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400

    data = request.get_json()
    form = TransacaoForm(data=data, meta={'csrf': False})
    if form.validate():
        user_id = session['user_id']
        tipo = form.tipo.data
        valor = float(form.valor.data)
        data_transacao = form.data_transacao.data
        try:
            banca_manager.process_add_transacao(user_id, tipo, valor, data_transacao)
            logging.info(f"Transação '{tipo}' de R$ {valor} adicionada para usuário ID {user_id}.")
            return jsonify({"status": "success", "message": "Transação adicionada com sucesso!"}), 200
        except TypeError as te:
            logging.error(f"Erro em /add_transacao: {te}")
            return jsonify({"status": "error", "message": str(te)}), 400
        except Exception as e:
            logging.error(f"Erro em /add_transacao: {e}")
            return jsonify({"status": "error", "message": "Erro ao adicionar transação."}), 400
    else:
        logging.error(f"Erro de validação no formulário de transação: {form.errors}")
        return jsonify({"status": "error", "message": "Dados inválidos.", "errors": form.errors}), 400

@app.route('/get_transacoes', methods=['GET'])
@login_required
def get_transacoes_route():
    user_id = session['user_id']
    try:
        transacoes = banca_manager.get_transacoes_ordenadas(user_id)
        transacoes_list = [{
            "id": t.id,
            "tipo": t.tipo,
            "valor": float(t.valor),
            "data": t.data.strftime('%d/%m/%Y')
        } for t in transacoes]
        logging.info(f"Transações carregadas para usuário ID {user_id}.")
        return jsonify(transacoes_list), 200
    except Exception as e:
        logging.error(f"Erro em /get_transacoes: {e}")
        return jsonify({"status": "error", "message": "Erro ao obter transações."}), 400

@app.route('/update_transacao/<int:id_>', methods=['POST'])
@login_required
def update_transacao_route(id_):
    if not request.is_json:
        logging.warning(f"Requisição inválida em /update_transacao/{id_}: Não é JSON.")
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400

    data = request.get_json()
    novo_valor = data.get('novo_valor')
    novo_tipo = data.get('novo_tipo')
    nova_data = data.get('nova_data')
    if novo_valor is None or novo_tipo is None or nova_data is None:
        logging.warning(f"Dados incompletos em /update_transacao/{id_}.")
        return jsonify({"status": "error", "message": "Novo valor, tipo e data não fornecidos."}), 400

    try:
        novo_valor_float = float(novo_valor)
        if novo_valor_float <= 0:
            raise ValueError("Valor da transação deve ser positivo.")
        if novo_tipo not in ['deposito', 'saque']:
            raise ValueError("Tipo de transação inválido.")
        banca_manager.update_transacao(session['user_id'], id_, novo_valor_float, novo_tipo, nova_data)
        logging.info(f"Transação ID {id_} atualizada para '{novo_tipo}' de R$ {novo_valor_float} e data {nova_data} para usuário ID {session['user_id']}.")
        return jsonify({"status": "success", "message": "Transação atualizada com sucesso!"}), 200
    except ValueError as ve:
        logging.warning(f"Erro em /update_transacao/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /update_transacao/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao atualizar transação."}), 400

@app.route('/delete_transacao/<int:id_>', methods=['DELETE'])
@login_required
def delete_transacao_route(id_):
    user_id = session['user_id']
    try:
        banca_manager.delete_transacao(user_id, id_)
        logging.info(f"Transação ID {id_} excluída para usuário ID {user_id}.")
        return jsonify({"status": "success", "message": "Transação excluída com sucesso!"}), 200
    except ValueError as ve:
        logging.warning(f"Erro em /delete_transacao/{id_}: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Erro em /delete_transacao/{id_}: {e}")
        return jsonify({"status": "error", "message": "Erro ao excluir transação."}), 400

@app.route('/delete_all_saldos', methods=['POST'])
@login_required
def delete_all_saldos_route():
    user_id = session['user_id']
    data = request.get_json()
    if not data or data.get("confirm") != "yes":
        return jsonify({"status": "error", "message": "Confirmação necessária para deletar todos os saldos."}), 400
    try:
        banca_manager.process_delete_all_saldos(user_id)
        logging.info(f"Banca zerada para usuário ID {user_id}.")
        return jsonify({"status": "success", "message": "Banca zerada com sucesso!"}), 200
    except Exception as e:
        logging.error(f"Erro em /delete_all_saldos: {e}")
        return jsonify({"status": "error", "message": "Erro ao zerar a banca."}), 400

# -------------------------------------------------
# Inicialização e execução
# -------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        init_auth(app, db)
        banca_manager.initialize(app, db)
        logging.info("Banco de dados e serviços inicializados.")
    app.run(host='127.0.0.1', port=5000, debug=True)
