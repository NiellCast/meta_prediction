# banca_services.py

from models import db, Saldo, Transacao, Meta
from datetime import datetime, date
from sqlalchemy import func


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

    def process_add_saldo(self, user_id, data_str, saldo_valor):
        """
        Adiciona um novo saldo.
        """
        # Converter data_str para objeto date
        try:
            data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError as e:
            raise ValueError("Formato de data inválido. Use YYYY-MM-DD.") from e

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
            evolucao.append({
                "data": saldo.data.strftime('%d/%m/%Y'),  # Formato dia/mês/ano
                "banca": float(saldo.valor),
                "depositos": self.get_total_depositos(user_id),
                "saques": self.get_total_saques(user_id),
                "lucro": self.get_saldo_calculado(user_id)
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

    def update_saldo(self, user_id: int, saldo_id: int, novo_valor: float):
        """
        Atualiza o valor de um saldo específico.
        """
        saldo = Saldo.query.filter_by(id=saldo_id, user_id=user_id).first()
        if not saldo:
            raise ValueError("Saldo não encontrado.")
        saldo.valor = novo_valor
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

    def update_transacao(self, user_id: int, transacao_id: int, novo_valor: float, novo_tipo: str = None):
        """
        Atualiza o valor e/ou tipo de uma transação específica.
        """
        transacao = Transacao.query.filter_by(id=transacao_id, user_id=user_id).first()
        if not transacao:
            raise ValueError("Transação não encontrada.")
        transacao.valor = novo_valor
        if novo_tipo:
            if novo_tipo not in ['deposito', 'saque']:
                raise ValueError("Tipo de transação inválido.")
            transacao.tipo = novo_tipo
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


# Instanciar o manager
banca_manager = BancaManager()


if __name__ == "__main__":
    print("Este módulo faz parte do sistema. Use-o importando-o em seus scripts.")

# Como rodar os testes:
# 1. Instale o pytest (pip install pytest).
# 2. Certifique-se de que os testes estão no diretório correto.
# 3. Execute o comando 'pytest' no terminal para rodar todos os testes.


# Melhorias aplicadas ao arquivo