# auth_services.py

from models import db, User
from sqlalchemy.exc import IntegrityError


def init_auth(app, db_instance):
    """
    Inicializa a autenticação.
    """
    # Nenhuma inicialização adicional necessária aqui
    pass


def login_user_service(username, password, bcrypt):
    """
    Autentica um usuário.
    """
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.hashed_password, password):
        return user
    return None


def register_user_service(username, email, hashed_password):
    """
    Registra um novo usuário.
    """
    new_user = User(username=username, email=email, hashed_password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return new_user


if __name__ == "__main__":
    print("Este módulo faz parte do sistema. Use-o importando-o em seus scripts.")

# Como rodar os testes:
# 1. Instale o pytest (pip install pytest).
# 2. Certifique-se de que os testes estão no diretório correto.
# 3. Execute o comando 'pytest' no terminal para rodar todos os testes.


# Melhorias aplicadas ao arquivo