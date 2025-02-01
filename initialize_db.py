from main import app
from models import db

def create_tables():
    """
    Cria todas as tabelas no banco de dados.
    """
    with app.app_context():
        db.create_all()
        print("Tabelas criadas com sucesso.")

if __name__ == "__main__":
    create_tables()
