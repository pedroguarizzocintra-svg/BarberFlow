"""Autenticação e RBAC: RF-01/02/03, RNF-01/02/08."""
import re
import sqlite3
from functools import wraps
import click
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db, transaction

bp = Blueprint("auth", __name__)
ROLES = {"client": "Cliente", "barber": "Barbeiro", "admin": "Administrador"}

def validate_identity(name, email, password):
    name = name.strip()
    email = email.strip().lower()
    if not 1 <= len(name) <= 100:
        raise ValueError("Informe um nome de até 100 caracteres.")
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Informe um e-mail válido.")
    if not 10 <= len(password) <= 128:
        raise ValueError("A senha deve conter entre 10 e 128 caracteres.")
    return name, email

def create_user(name, email, password, role="client"):
    name, email = validate_identity(name, email, password)
    if role not in ROLES:
        raise ValueError("Perfil inválido.")
    password_hash = generate_password_hash(password)
    with transaction() as db:
        cur = db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                         (name, email, password_hash, role))
        user_id = cur.lastrowid
        if role == "barber":
            db.execute("INSERT INTO barbers(user_id) VALUES(?)", (user_id,))
    return user_id

@bp.before_app_request
def load_user():
    user_id = session.get("user_id")
    g.user = None if user_id is None else get_db().execute(
        "SELECT id,name,email,role FROM users WHERE id=? AND active=1", (user_id,)).fetchone()
    if user_id is not None and g.user is None:
        session.clear()

def require_role(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))
            if roles and g.user["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def require_owner(owner_id):
    if g.user is None or g.user["id"] != owner_id:
        abort(403)

@bp.route("/register", methods=["GET","POST"])
def register():
    if g.user is not None:
        return redirect(url_for("auth.dashboard"))
    if request.method == "POST":
        try:
            create_user(request.form.get("name",""), request.form.get("email",""),
                        request.form.get("password",""), role="client")
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.IntegrityError:
            flash("Não foi possível cadastrar este e-mail.", "error")
        else:
            flash("Cadastro realizado. Entre com sua conta.", "success")
            return redirect(url_for("auth.login"))
        return render_template("auth.html", mode="register"), 400
    return render_template("auth.html", mode="register")

@bp.route("/login", methods=["GET","POST"])
def login():
    if g.user is not None:
        return redirect(url_for("auth.dashboard"))
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = get_db().execute("SELECT * FROM users WHERE email=? AND active=1", (email,)).fetchone()
        if user is None or len(password) > 128 or not check_password_hash(user["password_hash"], password):
            current_app.logger.warning("event=login_failed result=denied")
            flash("E-mail ou senha inválidos.", "error")
            return render_template("auth.html", mode="login"), 401
        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("auth.dashboard"))
    return render_template("auth.html", mode="login")

@bp.post("/logout")
@require_role()
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@bp.get("/dashboard")
@require_role()
def dashboard():
    return redirect(url_for("auth."+g.user["role"]))

@bp.get("/cliente")
@require_role("client")
def client():
    from .dashboards import context
    return render_template("dashboard.html", role="Cliente", users=None, **context(get_db(),"client"))

@bp.get("/barbeiro")
@require_role("barber")
def barber():
    from .dashboards import context
    return render_template("dashboard.html", role="Barbeiro", users=None, **context(get_db(),"barber"))

@bp.route("/admin", methods=["GET","POST"])
@require_role("admin")
def admin():
    if request.method == "POST":
        role = request.form.get("role","")
        if role not in ("barber","admin"):
            abort(403)
        try:
            uid = create_user(request.form.get("name",""), request.form.get("email",""),
                              request.form.get("password",""), role)
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.IntegrityError:
            flash("Não foi possível cadastrar este e-mail.", "error")
        else:
            current_app.logger.info("event=user_provision actor=%s target=%s result=success", g.user["id"], uid)
            flash("Conta criada.", "success")
        return redirect(url_for("auth.admin"))
    users = get_db().execute("SELECT id,name,email,role FROM users WHERE role IN ('barber','admin') ORDER BY id").fetchall()
    from .dashboards import context
    return render_template("dashboard.html", role="Administrador", users=users, **context(get_db(),"admin"))

@click.command("create-admin")
@click.option("--name", prompt=True)
@click.option("--email", prompt=True)
@click.password_option()
def create_admin_command(name, email, password):
    try:
        create_user(name,email,password,"admin")
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise click.ClickException("Dados inválidos ou e-mail já cadastrado.") from exc
    click.echo("Administrador criado.")

@click.command("seed-demo")
@click.password_option(help="Senha local para as contas fictícias; não use senha real.")
def seed_demo(password):
    accounts = [("Cliente Demo","cliente@example.test","client"),
                ("Barbeiro Demo","barbeiro@example.test","barber"),
                ("Admin Demo","admin@example.test","admin")]
    for name,email,role in accounts:
        if get_db().execute("SELECT id FROM users WHERE email=?",(email,)).fetchone() is None:
            create_user(name,email,password,role)
    click.echo("Contas fictícias disponíveis. Contas existentes não tiveram suas senhas alteradas.")

def init_app(app):
    app.register_blueprint(bp)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(seed_demo)
