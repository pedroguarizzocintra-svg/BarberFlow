"""Conexões por requisição e transações de escrita (T02, RNF-03/04)."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import click
from flask.cli import with_appcontext
from flask import current_app, g

def get_db():
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DATABASE"], timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        g.db = db
    return g.db

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@contextmanager
def transaction():
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise

def init_db():
    sql = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(sql)

@click.command("init-db")
@with_appcontext
def init_db_command():
    init_db()
    click.echo("Banco inicializado sem apagar dados.")

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
