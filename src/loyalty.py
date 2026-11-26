"""Fidelidade RF-20–23, RN-03/04/15."""
from flask import Blueprint,g,render_template
from .auth import require_role
from .db import get_db
from .scheduling import local

bp=Blueprint("loyalty",__name__)

def reserve_reward(db,client_id,appointment_id,reward_id):
    a=db.execute("""SELECT a.*,s.loyalty_eligible FROM appointments a JOIN services s ON s.id=a.service_id
        WHERE a.id=? AND a.client_id=?""",(appointment_id,client_id)).fetchone()
    if not a or a["status"]!="CONFIRMADO" or not a["loyalty_eligible"] or a["price_cents_snapshot"]<=0:
        raise ValueError("Recompensa válida apenas para corte elegível pago.")
    r=db.execute("SELECT * FROM rewards WHERE id=? AND client_id=? AND status='DISPONIVEL' AND appointment_id IS NULL",(reward_id,client_id)).fetchone()
    if not r:
        raise ValueError("Recompensa indisponível.")
    if db.execute("SELECT 1 FROM rewards WHERE appointment_id=?",(appointment_id,)).fetchone():
        raise ValueError("Atendimento já possui uma recompensa.")
    db.execute("UPDATE rewards SET status='RESERVADA',appointment_id=? WHERE id=?",(appointment_id,reward_id))

def balance(db,client_id):
    return db.execute("SELECT count(*) FROM loyalty_credits WHERE client_id=? AND reward_id IS NULL",(client_id,)).fetchone()[0]

def available_rewards(db,client_id):
    return db.execute("SELECT id FROM rewards WHERE client_id=? AND status='DISPONIVEL' AND appointment_id IS NULL ORDER BY id",(client_id,)).fetchall()

@bp.get("/recompensas")
@require_role("client")
def page():
    db=get_db()
    uid=g.user["id"]
    return render_template("loyalty.html",credits=balance(db,uid),
        rewards=db.execute("SELECT * FROM rewards WHERE client_id=? ORDER BY id DESC",(uid,)).fetchall(),
        visits=db.execute("""SELECT a.*,s.name AS service FROM appointments a JOIN services s ON s.id=a.service_id
             WHERE a.client_id=? AND a.status='CONCLUIDO' ORDER BY completed_at DESC""",(uid,)).fetchall(),local=local)
