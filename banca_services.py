from models import db, Saldo, Transacao, Meta
from datetime import datetime, date
from sqlalchemy import func
import random  # Para simular a previsão da IA

class BancaManager:
    def initialize(self, app, db_instance):
        """
        Inicializa o manager com o contexto da aplicação.
        """
        self.app = app
        self.db = db_instance

    def process_update_meta(self, user_id, nova_meta):
        """
        Atualiza a meta do usuário.
        """
        meta = Meta.query.filter_by(user_id=user_id).first()
        if meta:
            meta.valor_meta = nova_meta
        else:
            meta = Meta(user_id=user_id, valor_meta=nova_meta)
            db.session.add(meta)
        db.session.commit()

    def process_add_transacao(self, user_id, tipo, valor, data_transacao):
        """
        Adiciona uma nova transação.
        """
        if not isinstance(data_transacao, date):
            raise TypeError("data_transacao deve ser um objeto date.")
        transacao = Transacao(user_id=user_id, tipo=tipo, valor=valor, data=data_transacao)
        db.session.add(transacao)
        db.session.commit()

    def process_add_saldo(self, user_id, data_saldo, saldo_valor):
        """
        Adiciona um novo saldo.
        """
        # Converter data_str para objeto date
        try:
            data_obj = datetime.strptime(data_saldo, '%Y-%m-%d').date()
        except ValueError as e:
            raise ValueError("Formato de data inválido. Use YYYY-MM-DD.") from e

        saldo = Saldo.query.filter_by(user_id=user_id, data=data_obj).first()
        if saldo:
            saldo.valor += saldo_valor  # Atualiza o saldo existente
        else:
            saldo = Saldo(user_id=user_id, data=data_obj, valor=saldo_valor)
            db.session.add(saldo)
        db.session.commit()

    def process_delete_all_saldos(self, user_id):
        """
        Exclui todos os saldos e transações de um usuário e reseta a meta.
        """
        Transacao.query.filter_by(user_id=user_id).delete()
        Saldo.query.filter_by(user_id=user_id).delete()
        Meta.query.filter_by(user_id=user_id).delete()
        db.session.commit()

    def get_saldos_ordenados(self, user_id):
        """
        Retorna os saldos ordenados por data.
        """
        return Saldo.query.filter_by(user_id=user_id).order_by(Saldo.data).all()

    def get_transacoes_ordenadas(self, user_id):
        """
        Retorna as transações ordenadas por data.
        """
        return Transacao.query.filter_by(user_id=user_id).order_by(Transacao.data).all()

    def get_saldo_calculado(self, user_id):
        """
        Calcula o saldo atual com base nas transações.
        """
        depositos = db.session.query(func.sum(Transacao.valor)).filter_by(user_id=user_id, tipo='deposito').scalar() or 0
        saques = db.session.query(func.sum(Transacao.valor)).filter_by(user_id=user_id, tipo='saque').scalar() or 0
        saldo = depositos - saques
        return saldo

    def get_valor_total_banca(self, user_id):
        """
        Calcula o valor total da banca.
        """
        return self.get_saldo_calculado(user_id)

    def get_evolucao(self, user_id: int):
        """
        Obtém a evolução da banca ao longo do tempo.
        """
        saldos = Saldo.query.filter_by(user_id=user_id).order_by(Saldo.data.asc()).all()
        evolucao = []
        for saldo in saldos:
            banca_val = float(saldo.valor)
            depositos = self.get_total_depositos(user_id)
            saques = self.get_total_saques(user_id)
            lucro_val = banca_val - saques
            porcentagem_ganho = (lucro_val / depositos * 100) if depositos > 0 else 0

            evolucao.append({
                "data": saldo.data.strftime('%d/%m/%Y'),  # Formato dia/mês/ano
                "banca": f"{banca_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "depositos": f"{depositos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "saques": f"{saques:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "lucro": f"{lucro_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "porcentagem_ganho": f"{porcentagem_ganho:.2f}%"
            })
        return evolucao

    def get_total_depositos(self, user_id: int) -> float:
        """
        Calcula o total de depósitos do usuário.
        """
        total = db.session.query(func.sum(Transacao.valor)).filter_by(user_id=user_id, tipo='deposito').scalar() or 0.0
        return float(total)

    def get_total_saques(self, user_id: int) -> float:
        """
        Calcula o total de saques do usuário.
        """
        total = db.session.query(func.sum(Transacao.valor)).filter_by(user_id=user_id, tipo='saque').scalar() or 0.0
        return float(total)

    def get_meta(self, user_id: int) -> float:
        """
        Obtém a meta do usuário.
        """
        meta = Meta.query.filter_by(user_id=user_id).first()
        return float(meta.valor_meta) if meta else 0.0

    # ------------------------------
    # Implementação das Novas Funções
    # ------------------------------

    def update_saldo(self, user_id: int, saldo_id: int, novo_valor: float, nova_data: str):
        """
        Atualiza o valor e a data de um saldo específico.
        """
        saldo = Saldo.query.filter_by(id=saldo_id, user_id=user_id).first()
        if not saldo:
            raise ValueError("Saldo não encontrado.")
        try:
            data_obj = datetime.strptime(nova_data, '%Y-%m-%d').date()
        except ValueError as e:
            raise ValueError("Formato de data inválido. Use YYYY-MM-DD.") from e
        saldo.valor = novo_valor
        saldo.data = data_obj
        db.session.commit()

    def delete_saldo(self, user_id: int, saldo_id: int):
        """
        Deleta um saldo específico.
        """
        saldo = Saldo.query.filter_by(id=saldo_id, user_id=user_id).first()
        if not saldo:
            raise ValueError("Saldo não encontrado.")
        db.session.delete(saldo)
        db.session.commit()

    def update_transacao(self, user_id: int, transacao_id: int, novo_valor: float, novo_tipo: str, nova_data: str):
        """
        Atualiza o valor, tipo e data de uma transação específica.
        """
        transacao = Transacao.query.filter_by(id=transacao_id, user_id=user_id).first()
        if not transacao:
            raise ValueError("Transação não encontrada.")
        if novo_tipo not in ['deposito', 'saque']:
            raise ValueError("Tipo de transação inválido.")
        try:
            data_obj = datetime.strptime(nova_data, '%Y-%m-%d').date()
        except ValueError as e:
            raise ValueError("Formato de data inválido. Use YYYY-MM-DD.") from e
        transacao.valor = novo_valor
        transacao.tipo = novo_tipo
        transacao.data = data_obj
        db.session.commit()

    def delete_transacao(self, user_id: int, transacao_id: int):
        """
        Deleta uma transação específica.
        """
        transacao = Transacao.query.filter_by(id=transacao_id, user_id=user_id).first()
        if not transacao:
            raise ValueError("Transação não encontrada.")
        db.session.delete(transacao)
        db.session.commit()

    def get_previsao_ia(self, user_id: int) -> float:
        """
        Gera uma previsão da IA para o próximo mês.
        (Simulação: gera um valor aleatório baseado no saldo atual)
        """
        saldo_atual = self.get_saldo_calculado(user_id)
        # Simulação simples: previsão é saldo atual + um valor aleatório entre -10% a +10%
        variacao = random.uniform(-0.1, 0.1)
        previsao = saldo_atual + (saldo_atual * variacao)
        return round(previsao, 2)

banca_manager = BancaManager()
