import sqlite3
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def init_app(app):
    from flask.cli import with_appcontext
    import click

    app.teardown_appcontext(close_db)
    @click.command('init-db')
    @with_appcontext
    def init_db_command():
        with current_app.open_resource('schema.sql') as f:
            get_db().executescript(f.read().decode())
        click.echo('Initialized database.')
    app.cli.add_command(init_db_command)
