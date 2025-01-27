# initialize_db.py

from main import app
from models import db

def create_tables():
    """
    Cria todas as tabelas no banco de dados.
    """
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        create_tables()
        print("Tabelas criadas e aplicação inicializada com sucesso.")


# Melhorias aplicadas ao arquivo