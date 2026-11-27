"""Controles adicionais de segurança e validação de ponta a ponta."""
import re
from src.db import get_db
from src.auth import create_user

def token(client,path):
    return re.search(r'name="csrf_token" value="([^"]+)"',client.get(path).get_data(as_text=True)).group(1)

def test_security_headers(app,client):
    res=client.get("/login")
    assert res.headers["X-Content-Type-Options"]=="nosniff"
    assert res.headers["X-Frame-Options"]=="DENY"
    assert "frame-ancestors 'none'" in res.headers["Content-Security-Policy"]

def test_log_no_secret(app,client,caplog):
    import logging
    caplog.set_level(logging.INFO)
    t=token(client,"/login")
    secret="password-not-to-be-logged"
    client.post("/login",data={"csrf_token":t,"email":"none@example.test","password":secret})
    assert secret not in caplog.text
    assert "event=mutation" in caplog.text

def test_demo_repeat(app):
    runner=app.test_cli_runner()
    result=runner.invoke(args=["seed-demo","--password","test-password-123"])
    assert result.exit_code==0,result.output
    for _ in range(2):
        result=runner.invoke(args=["seed-catalog"])
        assert result.exit_code==0,result.output
    with app.app_context():
        db=get_db()
        assert db.execute("SELECT count(*) FROM services").fetchone()[0]==3
        assert db.execute("SELECT quantity FROM supplies WHERE name='Lâmina demo'").fetchone()[0]==30

def test_escape_profile(app,client):
    with app.app_context():
        uid=create_user("<script>alert(1)</script>","safe@example.test","test-password-123")
    with client.session_transaction() as session: session["user_id"]=uid
    html=client.get("/cliente").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
