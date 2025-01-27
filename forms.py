# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])


class SaldoForm(FlaskForm):
    data = DateField('Data', format='%Y-%m-%d', validators=[Optional()])  # Campo opcional
    saldo = DecimalField('Saldo', places=2, validators=[DataRequired(), NumberRange(min=0)])


class TransacaoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('deposito', 'Depósito'), ('saque', 'Saque')], validators=[DataRequired()])
    valor = DecimalField('Valor', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    data = DateField('Data', format='%Y-%m-%d', validators=[Optional()])  # Campo opcional


class MetaForm(FlaskForm):
    nova_meta = DecimalField('Nova Meta', places=2, validators=[DataRequired(), NumberRange(min=0.01)])


if __name__ == "__main__":
    print("Este módulo faz parte do sistema. Use-o importando-o em seus scripts.")

# Como rodar os testes:
# 1. Instale o pytest (pip install pytest).
# 2. Certifique-se de que os testes estão no diretório correto.
# 3. Execute o comando 'pytest' no terminal para rodar todos os testes.


# Melhorias aplicadas ao arquivo