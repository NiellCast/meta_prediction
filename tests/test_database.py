# tests/test_database.py

import pytest
from data_access import create_tables, insert_saldo, get_saldos, delete_saldo, delete_all_saldos, insert_transacao, calcular_total_banca, update_meta, get_meta

@pytest.fixture
def setup_db():
    """
    Executado antes de cada teste.
    Limpa e recria as tabelas no banco real (não recomendado em produção).
    """
    create_tables()
    delete_all_saldos(user_id=1)  # Supondo user_id=1 para testes
    yield
    delete_all_saldos(user_id=1)

def test_insert_get_saldo(setup_db):
    """
    Verifica se inserir e obter saldos funciona.
    """
    insert_saldo(user_id=1, data="2025-01-01", valor=100.0)
    saldos = get_saldos(user_id=1)
    assert len(saldos) == 1
    assert saldos[0].data.strftime('%Y-%m-%d') == "2025-01-01"  # data
    assert float(saldos[0].valor) == 100.0        # valor

def test_delete_saldo(setup_db):
    """
    Verifica se deletar um saldo específico funciona.
    """
    insert_saldo(user_id=1, data="2025-01-02", valor=50.0)
    saldos = get_saldos(user_id=1)
    assert len(saldos) == 1

    saldo_id = saldos[0].id
    delete_saldo(user_id=1, id_=saldo_id)
    saldos_after_delete = get_saldos(user_id=1)
    assert len(saldos_after_delete) == 0

def test_insert_transacao_calculo_banca(setup_db):
    """
    Verifica se inserir transações altera corretamente o valor total da banca.
    """
    # Começa com 1 saldo
    insert_saldo(user_id=1, data="2025-01-01", valor=100.0)
    # Adiciona um depósito de 200
    insert_transacao(user_id=1, tipo="deposito", valor=200.0, data="2025-01-01")
    assert calcular_total_banca(user_id=1) == 300.0

    # Adiciona um saque de 50
    insert_transacao(user_id=1, tipo="saque", valor=50.0, data="2025-01-01")
    assert calcular_total_banca(user_id=1) == 250.0

def test_meta(setup_db):
    """
    Verifica se a meta pode ser atualizada e lida corretamente.
    """
    update_meta(user_id=1, nova_meta=2000.0)
    assert get_meta(user_id=1) == 2000.0

def test_delete_all_saldos(setup_db):
    """
    Verifica se zerar a banca exclui saldos e transações.
    """
    insert_saldo(user_id=1, data="2025-01-01", valor=500.0)
    insert_transacao(user_id=1, tipo="deposito", valor=300.0, data="2025-01-01")
    assert calcular_total_banca(user_id=1) == 800.0

    delete_all_saldos(user_id=1)
    assert calcular_total_banca(user_id=1) == 0.0
