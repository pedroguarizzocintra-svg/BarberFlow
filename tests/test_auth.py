import re
import sqlite3
import pytest
from werkzeug.security import check_password_hash
from src import create_app
from src.db import get_db, init_db, transaction
from src.auth import create_user

def token(client, path):
    page = client.get(path)
    return re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)

def post(client,path,**data):
    return client.post(path,data={"csrf_token":token(client,path),**data})

def login(client,email,password="test-password-123"):
    return post(client,"/login",email=email,password=password)

def test_register_only_client(app,client):
    response=post(client,"/register",name="Cliente",email="CLIENTE@example.test",
                  password="test-password-123",role="admin")
    assert response.status_code == 302
    with app.app_context():
        user=get_db().execute("SELECT * FROM users WHERE email=?",("cliente@example.test",)).fetchone()
        assert user["role"]=="client"
        assert user["password_hash"]!="test-password-123"
        assert check_password_hash(user["password_hash"],"test-password-123")

def test_duplicate_email(app,client):
    with app.app_context():
        create_user("Cliente","cliente@example.test","test-password-123")
    assert post(client,"/register",name="Outro",email="CLIENTE@example.test",password="test-password-123").status_code==400

def test_invalid_credentials(client):
    assert login(client,"admin@example.test","wrong").status_code==401
    assert client.get("/admin").status_code==302

@pytest.mark.parametrize("role,path,denied",[
    ("admin","/admin","/cliente"),("barber","/barbeiro","/admin")])
def test_roles(client,role,path,denied):
    assert login(client,role+"@example.test").status_code==302
    assert client.get(path).status_code==200
    assert client.get(denied).status_code==403

def test_client_cannot_admin(app,client):
    with app.app_context():
        create_user("Cliente","cliente@example.test","test-password-123")
    login(client,"cliente@example.test")
    assert client.get("/cliente").status_code==200
    assert client.get("/admin").status_code==403
    assert client.post("/admin",data={"csrf_token":token(client,"/cliente"),"role":"admin"}).status_code==403

def test_csrf_required(client):
    assert client.post("/login",data={"email":"admin@example.test","password":"test-password-123"}).status_code==400

def test_logout(client):
    login(client,"admin@example.test")
    assert client.post("/logout",data={"csrf_token":token(client,"/admin")}).status_code==302
    assert client.get("/admin").status_code==302

def test_admin_provisions_barber(app,client):
    login(client,"admin@example.test")
    response=post(client,"/admin",name="Novo",email="novo@example.test",password="test-password-123",role="barber")
    assert response.status_code==302
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM barbers b JOIN users u ON u.id=b.user_id WHERE u.email=?",("novo@example.test",)).fetchone()[0]==1

def test_persistence(app):
    with app.app_context():
        create_user("Persistente","persist@example.test","test-password-123")
    new_app=create_app({"TESTING":True,"SECRET_KEY":"another-test-key","DATABASE":app.config["DATABASE"]})
    with new_app.app_context():
        init_db()
        assert get_db().execute("SELECT name FROM users WHERE email=?",("persist@example.test",)).fetchone()[0]=="Persistente"

def test_constraints_and_rollback(app):
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            with transaction() as db:
                db.execute("INSERT INTO supplies(name,quantity,min_quantity) VALUES('válido',1,0)")
                db.execute("INSERT INTO supplies(name,quantity,min_quantity) VALUES('inválido',-1,0)")
        assert get_db().execute("SELECT count(*) FROM supplies").fetchone()[0]==0
        with pytest.raises(sqlite3.IntegrityError):
            with transaction() as db:
                db.execute("INSERT INTO barbers(user_id) VALUES(999999)")
