# models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)  # Armazena o hash da senha
    role = db.Column(db.String(20), nullable=False, default='user')  # Adicionado campo de role

    saldos = db.relationship('Saldo', backref='user', lazy=True)
    transacoes = db.relationship('Transacao', backref='user', lazy=True)
    meta = db.relationship('Meta', backref='user', uselist=False)

    def __repr__(self):
        return f"<User {self.username}>"


class Saldo(db.Model):
    __tablename__ = 'saldo'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f"<Saldo {self.valor} em {self.data}>"


class Transacao(db.Model):
    __tablename__ = 'transacao'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'deposito' ou 'saque'
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<Transacao {self.tipo} de {self.valor} em {self.data}>"


class Meta(db.Model):
    __tablename__ = 'meta'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    valor_meta = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f"<Meta {self.valor_meta} para User ID {self.user_id}>"
