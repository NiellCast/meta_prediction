import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from models import db, User, Saldo, Transacao, Meta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'previsao_meta.db')}"

engine = create_engine( DATABASE_URL, connect_args={"check_same_thread": False}, pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800 )

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def create_tables():
    """ Cria as tabelas do banco (caso não existam). """
    db.create_all()


def insert_saldo(user_id: int, data: str, valor: float):
    session = SessionLocal()
    try:
        saldo = session.query(Saldo).filter(Saldo.user_id == user_id, Saldo.data == data).first()
        if saldo:
            saldo.valor += valor
        else:
            saldo = Saldo(user_id=user_id, data=data, valor=valor)
            session.add(saldo)
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally: session.close()

def get_saldos(user_id: int):
    session = SessionLocal()
    try:
        return session.query(Saldo).filter(Saldo.user_id == user_id).order_by(Saldo.data.asc()).all()
    except Exception as e:
        raise e
    finally: session.close()

def get_saldo_by_id(user_id: int, id_: int):
    session = SessionLocal()
    try:
        return session.query(Saldo).filter(Saldo.user_id == user_id, Saldo.id == id_).first()
    except Exception as e:
        raise e
    finally: session.close()

def update_saldo(user_id: int, id_: int, novo_valor: float):
    session = SessionLocal()
    try:
        saldo = session.query(Saldo).filter(Saldo.user_id == user_id, Saldo.id == id_).first()
        if saldo:
            saldo.valor = novo_valor
            session.commit()
        else:
            raise ValueError(f"Saldo com id={id_} não encontrado para user_id={user_id}.")
    except Exception as e:
        session.rollback()
        raise e
    finally: session.close()

def delete_saldo(user_id: int, id_: int):
    session = SessionLocal()
    try:
        saldo = session.query(Saldo).filter(Saldo.user_id == user_id, Saldo.id == id_).first()
        if saldo:
            session.delete(saldo)
            session.commit()
        else:
            raise ValueError(f"Saldo com id={id_} não encontrado para user_id={user_id}.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def delete_all_saldos(user_id: int):
    session = SessionLocal()
    try:
        session.query(Saldo).filter(Saldo.user_id == user_id).delete()
        session.query(Transacao).filter(Transacao.user_id == user_id).delete()
        session.query(Meta).filter(Meta.user_id == user_id).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def insert_transacao(user_id: int, tipo: str, valor: float, data: str):
    session = SessionLocal()
    try:
        t = Transacao(user_id=user_id, tipo=tipo, valor=valor, data=data)
        session.add(t)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_transacoes(user_id: int):
    session = SessionLocal()
    try:
        return session.query(Transacao).filter(Transacao.user_id == user_id).order_by(Transacao.id.asc()).all()
    except Exception as e:
        raise e
    finally: session.close()

def update_transacao(user_id: int, id_: int, novo_valor: float):
    session = SessionLocal()
    try:
        transacao = session.query(Transacao).filter(Transacao.user_id == user_id, Transacao.id == id_).first()
        if transacao:
            transacao.valor = novo_valor
            session.commit()
        else:
            raise ValueError(f"Transacao com id={id_} não encontrada para user_id={user_id}.")
    except Exception as e:
        session.rollback()
        raise e
    finally: session.close()

def delete_transacao(user_id: int, id_: int):
    session = SessionLocal()
    try:
        transacao = session.query(Transacao).filter(Transacao.user_id == user_id, Transacao.id == id_).first()
        if transacao:
            session.delete(transacao)
            session.commit()
        else:
            raise ValueError(f"Transacao com id={id_} não encontrada para user_id={user_id}.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def calcular_total_banca(user_id: int) -> float:
    session = SessionLocal()
    try:
        total_saldo = session.query(func.sum(Saldo.valor)).filter(Saldo.user_id == user_id).scalar() or 0.0
        total_depositos = session.query(func.sum(Transacao.valor)).filter(Transacao.user_id == user_id, Transacao.tipo == "deposito").scalar() or 0.0
        total_saques = session.query(func.sum(Transacao.valor)).filter(Transacao.user_id == user_id, Transacao.tipo == "saque").scalar() or 0.0
        return float(total_saldo) + float(total_depositos) - float(total_saques)
    except Exception as e:
        raise e
    finally: session.close()

def get_meta(user_id: int) -> float:
    session = SessionLocal()
    try:
        meta = session.query(Meta).filter(Meta.user_id == user_id).first()
        return float(meta.valor_meta) if meta else 0.0
    except Exception as e:
        raise e
    finally: session.close()

def update_meta_value(user_id: int, nova_meta: float):
    session = SessionLocal()
    try:
        meta = session.query(Meta).filter(Meta.user_id == user_id).first()
        if meta:
            meta.valor_meta = nova_meta
        else:
            meta = Meta(user_id=user_id, valor_meta=nova_meta)
            session.add(meta)
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally: session.close()

def total_depositos_no_bd(user_id: int) -> float:
    session = SessionLocal()
    try:
        td = session.query(func.sum(Transacao.valor)).filter(Transacao.user_id == user_id, Transacao.tipo == "deposito").scalar()
        return float(td) if td else 0.0
    except Exception as e:
        raise e
    finally: session.close()

def calcular_total_saques(user_id: int) -> float:
    session = SessionLocal()
    try:
        ts = session.query(func.sum(Transacao.valor)).filter(Transacao.user_id == user_id, Transacao.tipo == "saque").scalar()
        return float(ts) if ts else 0.0
    except Exception as e:
        raise e
    finally: session.close()


def get_evolucao(user_id: int):
    session = SessionLocal()
    try:
        saldos = session.query(Saldo).filter(Saldo.user_id == user_id).order_by(Saldo.data.asc()).all()
        evolucao = []
        for saldo in saldos:
            banca_val = float(saldo.valor)
            depositos = calcular_total_depositos(user_id)
            saques = calcular_total_saques(user_id)
            lucro_val = depositos - saques
            porcentagem_ganho = (lucro_val / depositos * 100) if depositos > 0 else 0

            evolucao.append({
                "data": saldo.data.strftime('%d/%m/%Y'),
                "banca": f"{banca_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "depositos": f"{depositos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "saques": f"{saques:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "lucro": f"{lucro_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "porcentagem_ganho": f"{porcentagem_ganho:.2f}%"
            })
        return evolucao
    except Exception as e:
        raise e
    finally:
        session.close()


banca_manager = BancaManager()