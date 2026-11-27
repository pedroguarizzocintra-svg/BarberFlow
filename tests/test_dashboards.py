"""RF-31–35: indicadores, histórico, avaliações e autorização."""
from datetime import datetime,timedelta,timezone
import re
import pytest
from src.auth import create_user
from src.db import get_db,transaction
from src.scheduling import reserve,transition,LOCAL,stamp
from src.operations import complete
from src.customer import review
from src.dashboards import occupancy,admin_metrics,barber_metrics,client_metrics
from src.finance import period

@pytest.fixture
def scenario(app):
    start=datetime(2035,1,2,9,tzinfo=LOCAL).astimezone(timezone.utc)
    current=start-timedelta(days=1)
    with app.app_context():
        cid=create_user("Cliente","dashboard@example.test","test-password-123")
        other=create_user("Outro","other-dashboard@example.test","test-password-123")
        db=get_db()
        b=db.execute("SELECT id,user_id FROM barbers").fetchone()
        admin=db.execute("SELECT id FROM users WHERE role='admin'").fetchone()[0]
        with transaction() as tx:
            sid=tx.execute("INSERT INTO services(name,price_cents,duration_min,loyalty_eligible) VALUES('Corte',5000,30,1)").lastrowid
            tx.execute("INSERT INTO working_hours(barber_id,weekday,start_time,end_time) VALUES(?,?,?,?)",(b["id"],start.astimezone(LOCAL).weekday(),"09:00","10:00"))
            aid=reserve(tx,cid,sid,b["id"],start,current=current)
            transition(tx,aid,b["user_id"],"start",start)
            complete(tx,aid,b["user_id"],start)
            pending=reserve(tx,other,sid,b["id"],start+timedelta(minutes=30),current=current)
            tx.execute("INSERT INTO supplies(name,quantity,min_quantity) VALUES('Gel',2,2)")
    return cid,other,b["user_id"],admin,aid,pending,start

def test_metrics_real_values(app,scenario):
    cid,other,barber,admin,aid,pending,start=scenario
    with app.app_context():
        db=get_db()
        day=start.astimezone(LOCAL).date()
        low,high=period(day.isoformat(),day.isoformat())
        m=admin_metrics(db,low,high,day)
        assert m["visits"]==1 and m["revenue"]==5000 and m["ticket"]==5000
        assert m["commission"]==2000 and m["result"]==3000
        assert m["occupancy"]==100 and len(m["alerts"])==1
        assert client_metrics(db,cid)["visits"]==1
        assert client_metrics(db,cid)["spent"]==5000
        assert client_metrics(db,other)["spent"]==0
        assert barber_metrics(db,barber,low,high)["rating"] is None
        with transaction() as tx:
            review(tx,cid,aid,5,"Excelente",start)
        assert barber_metrics(db,barber,low,high)["rating"]==5

def test_review_restrictions(app,scenario):
    cid,other,barber,admin,aid,pending,start=scenario
    with app.app_context():
        for owner,target,stars,error in [(other,aid,5,PermissionError),(other,pending,4,ValueError),(cid,aid,6,ValueError)]:
            with pytest.raises(error),transaction() as db:
                review(db,owner,target,stars,"")
        with transaction() as db:
            review(db,cid,aid,4,"Bom")
        with pytest.raises(ValueError),transaction() as db:
            review(db,cid,aid,5,"Duplicado")
        assert get_db().execute("SELECT count(*) FROM reviews").fetchone()[0]==1

def test_dashboard_routes_and_profile(app,client,scenario):
    cid,other,barber,admin,aid,pending,start=scenario
    for uid,allowed,denied in [(cid,["/cliente","/historico","/perfil"],["/admin","/barbeiro"]),(barber,["/barbeiro"],["/historico","/perfil","/admin"]),(admin,["/admin"],["/historico","/perfil","/barbeiro"])]:
        with client.session_transaction() as session:
            session["user_id"]=uid
        for path in allowed: assert client.get(path).status_code==200
        for path in denied: assert client.get(path).status_code==403
    with client.session_transaction() as session:
        session["user_id"]=cid
    page=client.get("/perfil").get_data(as_text=True)
    token=re.search(r'name="csrf_token" value="([^"]+)"',page).group(1)
    assert client.post("/perfil",data={"csrf_token":token,"name":"Novo nome","role":"admin"}).status_code==302
    assert client.post("/historico",data={"csrf_token":token,"id":pending,"rating":5}).status_code==403
    with app.app_context():
        u=get_db().execute("SELECT name,role FROM users WHERE id=?",(cid,)).fetchone()
        assert u["name"]=="Novo nome" and u["role"]=="client"

def test_empty_metrics(app):
    with app.app_context():
        day=datetime(2035,1,2).date()
        low,high=period(day.isoformat(),day.isoformat())
        m=admin_metrics(get_db(),low,high,day)
        assert m["ticket"]==m["occupancy"]==m["visits"]==0
