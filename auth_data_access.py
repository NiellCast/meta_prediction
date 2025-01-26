# app/auth_data_access.py

import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from models import db, User  # Importando User do models.py

# Configuração do banco de dados
DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(__file__), '../previsao_meta.db')}"

engine_auth = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

SessionLocalAuth = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine_auth))

def create_users_table():
    """
    Cria as tabelas do banco (caso não existam).
    """
    db.create_all()

def create_user(username: str, email: str, password: str):
    """
    Cria um novo usuário com senha hasheada.
    """
    session = SessionLocalAuth()
    try:
        hashed_pw = generate_password_hash(password, method='bcrypt')
        new_user = User(username=username, email=email, hashed_password=hashed_pw)
        session.add(new_user)
        session.commit()
        return new_user
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_user_by_username(username: str):
    """
    Busca um usuário pelo username.
    """
    session = SessionLocalAuth()
    try:
        return session.query(User).filter(User.username == username).first()
    except Exception as e:
        raise e
    finally:
        session.close()

def verify_password(user: User, plain_password: str) -> bool:
    """
    Verifica se a senha fornecida corresponde à senha hasheada do usuário.
    """
    return check_password_hash(user.hashed_password, plain_password)
