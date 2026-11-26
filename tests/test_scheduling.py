"""CT-02/03/04, fluxo integrado e testes de concorrência."""
from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
import pytest
from src.auth import create_user
from src.db import get_db,transaction
from src.scheduling import reserve,cancel,reschedule,available,transition,parse,stamp,LOCAL
from src.waitlist import join,answer,expire_offers
from src.operations import complete

@pytest.fixture
def setup_agenda(app):
    current=datetime(2035,1,1,10,tzinfo=timezone.utc)
    start=datetime(2035,1,2,14,tzinfo=LOCAL).astimezone(timezone.utc)
    with app.app_context():
        ids=[create_user("Cliente "+str(i),f"c{i}@example.test","test-password-123") for i in range(3)]
        db=get_db()
        b=db.execute("SELECT id,user_id FROM barbers").fetchone()
        bid,uid=b["id"],b["user_id"]
        with transaction() as tx:
            sid=tx.execute("INSERT INTO services(name,price_cents,duration_min,loyalty_eligible) VALUES('Corte',5000,40,1)").lastrowid
            tx.execute("INSERT INTO working_hours(barber_id,weekday,start_time,end_time) VALUES(?,?,?,?)",(bid,start.astimezone(LOCAL).weekday(),"09:00","18:00"))
    return ids,bid,uid,sid,current,start

def test_overlap_and_adjacent(app,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    with app.app_context():
        with transaction() as db:
            reserve(db,ids[0],sid,bid,start,current=current)
        with pytest.raises(ValueError), transaction() as db:
            reserve(db,ids[1],sid,bid,start+timedelta(minutes=20),current=current)
        with transaction() as db:
            reserve(db,ids[1],sid,bid,start+timedelta(minutes=40),current=current)
        assert get_db().execute("SELECT count(*) FROM appointments").fetchone()[0]==2

def test_outside_hours(app,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    with app.app_context():
        with pytest.raises(ValueError), transaction() as db:
            reserve(db,ids[0],sid,bid,start+timedelta(hours=4),current=current)

def test_failed_reschedule_preserves_slot(app,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    with app.app_context():
        with transaction() as db:
            aid=reserve(db,ids[0],sid,bid,start,current=current)
            reserve(db,ids[1],sid,bid,start+timedelta(minutes=40),current=current)
        with pytest.raises(ValueError), transaction() as db:
            reschedule(db,aid,ids[0],start+timedelta(minutes=40),current)
        assert get_db().execute("SELECT start_at FROM appointments WHERE id=?",(aid,)).fetchone()[0]==stamp(start)

def test_fifo_decline_accept(app,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    with app.app_context():
        with transaction() as db:
            aid=reserve(db,ids[0],sid,bid,start,current=current)
            w1=join(db,ids[1],sid,bid,start,start+timedelta(hours=1),current)
            w2=join(db,ids[2],sid,bid,start,start+timedelta(hours=1),current)
            cancel(db,aid,ids[0],current)
            o=db.execute("SELECT * FROM offers WHERE status='PENDENTE'").fetchone()
            assert o["waitlist_id"]==w1
            assert not available(db,bid,start,start+timedelta(minutes=40),current=current)
            assert db.execute("SELECT count(*) FROM notifications WHERE user_id=?",(ids[1],)).fetchone()[0]==1
        with pytest.raises(PermissionError), transaction() as db:
            answer(db,o["id"],ids[2],True,current)
        with transaction() as db:
            answer(db,o["id"],ids[1],False,current)
            second=db.execute("SELECT * FROM offers WHERE status='PENDENTE'").fetchone()
            assert second["waitlist_id"]==w2
            new=answer(db,second["id"],ids[2],True,current)
            assert db.execute("SELECT client_id FROM appointments WHERE id=?",(new,)).fetchone()[0]==ids[2]
        with pytest.raises(ValueError),transaction() as db:
            answer(db,second["id"],ids[2],True,current)

def test_expiry_advances(app,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    with app.app_context():
        with transaction() as db:
            aid=reserve(db,ids[0],sid,bid,start,current=current)
            join(db,ids[1],sid,bid,start,start+timedelta(hours=1),current)
            w2=join(db,ids[2],sid,bid,start,start+timedelta(hours=1),current)
            cancel(db,aid,ids[0],current)
            first=db.execute("SELECT id FROM offers").fetchone()[0]
            later=current+timedelta(minutes=15)
            expire_offers(db,later)
            assert db.execute("SELECT status FROM offers WHERE id=?",(first,)).fetchone()[0]=="EXPIRADA"
            assert db.execute("SELECT waitlist_id FROM offers WHERE status='PENDENTE'").fetchone()[0]==w2
        with pytest.raises(ValueError),transaction() as db:
            answer(db,first,ids[1],True,later)

def test_concurrent_reservation(app,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    def attempt(cid):
        with app.app_context():
            try:
                with transaction() as db:
                    reserve(db,cid,sid,bid,start,current=current)
                return True
            except ValueError:
                return False
    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(attempt,ids[:2]))
    assert sorted(results)==[False,True]

def test_completion_and_rollback(app,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    with app.app_context():
        with transaction() as db:
            aid=reserve(db,ids[0],sid,bid,start,current=current)
            supply=db.execute("INSERT INTO supplies(name,quantity,min_quantity) VALUES('Lamina',0,1)").lastrowid
            db.execute("INSERT INTO service_supplies VALUES(?,?,1)",(sid,supply))
            transition(db,aid,uid,"start",start)
        with pytest.raises(ValueError), transaction() as db:
            complete(db,aid,uid,start)
        db=get_db()
        assert db.execute("SELECT status FROM appointments WHERE id=?",(aid,)).fetchone()[0]=="EM_ATENDIMENTO"
        assert db.execute("SELECT count(*) FROM revenues").fetchone()[0]==0
        with transaction() as db:
            db.execute("UPDATE supplies SET quantity=2 WHERE id=?",(supply,))
            complete(db,aid,uid,start)
        assert db.execute("SELECT amount_cents FROM revenues").fetchone()[0]==5000
        assert db.execute("SELECT amount_cents FROM commissions").fetchone()[0]==2000
        assert db.execute("SELECT quantity FROM supplies WHERE id=?",(supply,)).fetchone()[0]==1
        assert db.execute("SELECT count(*) FROM loyalty_credits").fetchone()[0]==1
        with pytest.raises(ValueError),transaction() as db:
            complete(db,aid,uid,start)
        assert db.execute("SELECT count(*) FROM revenues").fetchone()[0]==1

def test_pages_and_roles(app,client,setup_agenda):
    ids,bid,uid,sid,current,start=setup_agenda
    with client.session_transaction() as session:
        session["user_id"]=ids[0]
    assert client.get("/agendamentos").status_code==200
    assert client.get("/fila").status_code==200
    assert client.get("/admin/catalogo").status_code==403
    assert client.get("/barbeiro/agenda").status_code==403
    with client.session_transaction() as session:
        session["user_id"]=uid
    assert client.get("/barbeiro/agenda").status_code==200
    with app.app_context():
        admin=get_db().execute("SELECT id FROM users WHERE role='admin'").fetchone()[0]
    with client.session_transaction() as session:
        session["user_id"]=admin
    assert client.get("/admin/catalogo").status_code==200
