"""CT-05–11: integração de fidelidade, estoque e financeiro."""
from datetime import datetime,timedelta,timezone
import pytest
from src.auth import create_user
from src.db import get_db,transaction
from src.scheduling import reserve,cancel,transition,LOCAL
from src.operations import complete
from src.loyalty import balance,available_rewards
from src.inventory import save_supply,move,set_consumption,alerts
from src.finance import totals,period,add_expense

@pytest.fixture
def business(app):
    current=datetime(2035,1,1,10,tzinfo=timezone.utc)
    start=datetime(2035,1,2,9,tzinfo=LOCAL).astimezone(timezone.utc)
    with app.app_context():
        client=create_user("Cliente","customer@example.test","test-password-123")
        other=create_user("Outro","other@example.test","test-password-123")
        b=get_db().execute("SELECT id,user_id FROM barbers").fetchone()
        bid,uid=b["id"],b["user_id"]
        admin=get_db().execute("SELECT id FROM users WHERE role='admin'").fetchone()[0]
        with transaction() as db:
            sid=db.execute("INSERT INTO services(name,price_cents,duration_min,loyalty_eligible) VALUES('Corte',5000,20,1)").lastrowid
            db.execute("INSERT INTO working_hours(barber_id,weekday,start_time,end_time) VALUES(?,?,?,?)",(bid,start.astimezone(LOCAL).weekday(),"09:00","18:00"))
    return client,other,bid,uid,admin,sid,current,start

def test_ten_cuts_and_free_redemption(app,business):
    cid,other,bid,uid,admin,sid,current,start=business
    with app.app_context():
        with transaction() as db:
            stock=save_supply(db,{"name":"Lâmina","minimum":"2","active":"1"})
            move(db,stock,13,"Compra",current)
            set_consumption(db,sid,stock,1)
            for i in range(10):
                at=start+timedelta(minutes=20*i)
                aid=reserve(db,cid,sid,bid,at,current=current)
                transition(db,aid,uid,"start",at)
                complete(db,aid,uid,at)
                if i==8:
                    assert balance(db,cid)==9
            assert balance(db,cid)==0
            rid=available_rewards(db,cid)[0]["id"]
            assert len(available_rewards(db,cid))==1
        with pytest.raises(ValueError),transaction() as db:
            reserve(db,other,sid,bid,start+timedelta(minutes=200),current=current,reward_id=rid)
        with transaction() as db:
            at=start+timedelta(minutes=200)
            aid=reserve(db,cid,sid,bid,at,current=current,reward_id=rid)
            assert not available_rewards(db,cid)
            cancel(db,aid,cid,current)
            assert available_rewards(db,cid)[0]["id"]==rid
            aid=reserve(db,cid,sid,bid,at,current=current,reward_id=rid)
            transition(db,aid,uid,"absent",at)
            assert available_rewards(db,cid)[0]["id"]==rid
            aid=reserve(db,cid,sid,bid,at,current=current,reward_id=rid)
            transition(db,aid,uid,"start",at)
            complete(db,aid,uid,at)
            assert db.execute("SELECT status FROM rewards WHERE id=?",(rid,)).fetchone()[0]=="UTILIZADA"
            assert db.execute("SELECT count(*) FROM loyalty_credits").fetchone()[0]==10
            assert db.execute("SELECT count(*) FROM revenues").fetchone()[0]==10
            assert db.execute("SELECT amount_cents FROM commissions WHERE appointment_id=?",(aid,)).fetchone()[0]==0
            assert db.execute("SELECT paid_cents FROM appointments WHERE id=?",(aid,)).fetchone()[0]==0
            assert alerts(db)[0]["quantity"]==2
        with pytest.raises(ValueError),transaction() as db:
            reserve(db,cid,sid,bid,start+timedelta(minutes=240),current=current,reward_id=rid)

def test_stock_history_and_negative_block(app,business):
    cid,other,bid,uid,admin,sid,current,start=business
    with app.app_context():
        with transaction() as db:
            supply=save_supply(db,{"name":"Gel","minimum":"2","active":"1"})
            move(db,supply,3,"Entrada",current)
            set_consumption(db,sid,supply,1)
        with pytest.raises(ValueError),transaction() as db:
            move(db,supply,-4,"Saída",current)
        db=get_db()
        assert db.execute("SELECT quantity FROM supplies WHERE id=?",(supply,)).fetchone()[0]==3
        assert db.execute("SELECT count(*) FROM stock_movements").fetchone()[0]==1
        with transaction() as db:
            move(db,supply,-1,"Ajuste",current)
            assert alerts(db)[0]["id"]==supply

def test_finance_totals_and_period(app,business):
    cid,other,bid,uid,admin,sid,current,start=business
    with app.app_context():
        with transaction() as db:
            for i in range(2):
                at=start+timedelta(minutes=20*i)
                aid=reserve(db,cid,sid,bid,at,current=current)
                transition(db,aid,uid,"start",at)
                complete(db,aid,uid,at)
            low,high=period("2035-01-02","2035-01-02")
            db.execute("INSERT INTO expenses(admin_id,description,amount_cents,occurred_at) VALUES(?,?,?,?)",(admin,"Limpeza",1000,low))
            assert totals(db,low,high)=={"revenue":10000,"commission":4000,"expense":1000,"result":5000}
            low,high=period("2035-01-03","2035-01-03")
            assert totals(db,low,high)["result"]==0
            add_expense(db,admin,"Material",100,"2025-01-01")
        with pytest.raises(ValueError),transaction() as db:
            add_expense(db,admin,"Inválida",0,"2025-01-01")

def test_business_pages_permissions(app,client,business):
    cid,other,bid,uid,admin,sid,current,start=business
    for who,allowed,denied in [(cid,["/recompensas","/agendamentos"],["/admin/estoque","/admin/financeiro","/barbeiro/comissoes"]),(admin,["/admin/estoque","/admin/financeiro"],["/recompensas","/barbeiro/comissoes"]),(uid,["/barbeiro/comissoes"],["/admin/financeiro","/admin/estoque","/recompensas"])]:
        with client.session_transaction() as session:
            session["user_id"]=who
        for path in allowed: assert client.get(path).status_code==200
        for path in denied: assert client.get(path).status_code==403
