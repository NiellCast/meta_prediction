import os
from data_access import create_tables

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(basedir, 'instance', 'previsao_meta.db')
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def initialize_database():
    """
    Inicializa o banco de dados criando as tabelas necessárias.
    """
    create_tables()

if __name__ == "__main__":
    initialize_database()
    print("Tabelas criadas com sucesso.")
