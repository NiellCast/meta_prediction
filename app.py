# Nome do arquivo completo: app.py

import os
from flask import Flask
from db.models import init_app as init_db_app
from auth.auth import auth_bp
from dashboard.dashboard import dashboard_bp
from utils import register_filters

app = Flask(__name__, instance_relative_config=True)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['DATABASE'] = os.path.join(app.instance_path, 'banca.db')
os.makedirs(app.instance_path, exist_ok=True)

# registra filtros Jinja
register_filters(app)
# inicializa DB e comando CLI
init_db_app(app)
# registra blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

if __name__ == '__main__':
    app.run(debug=True)
