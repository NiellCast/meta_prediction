# database.py

from data_access import create_tables

def initialize_database():
    """
    Inicializa o banco de dados criando as tabelas necessárias.
    """
    create_tables()

if __name__ == "__main__":
    initialize_database()
    print("Tabelas criadas com sucesso.")
