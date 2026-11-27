"""Fábrica da aplicação BarberFlow (T01)."""
import os
from pathlib import Path
from flask import Flask, redirect, url_for, g, render_template
from flask_wtf.csrf import CSRFProtect, CSRFError
from . import db, auth, catalog, scheduling, waitlist, loyalty, inventory, finance, customer

csrf = CSRFProtect()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("BARBERFLOW_SECRET"),
        DATABASE=str(Path(app.instance_path) / "barberflow.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("BARBERFLOW_HTTPS") == "1",
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("Defina BARBERFLOW_SECRET antes de iniciar.")
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)
    auth.init_app(app)
    app.register_blueprint(catalog.bp)
    app.register_blueprint(scheduling.bp)
    app.register_blueprint(waitlist.bp)
    app.register_blueprint(loyalty.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(customer.bp)
    @app.get("/")
    def index():
        if g.user is None:
            return redirect(url_for("auth.login"))
        return redirect(url_for("auth.dashboard"))
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("error.html", message="Requisição inválida ou sessão expirada. Tente novamente."), 400
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", message="Você não tem permissão para acessar esta área."), 403
    return app
