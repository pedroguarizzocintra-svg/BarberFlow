"""Conclusão integrada, chamada dentro de uma transação BEGIN IMMEDIATE.
RF-13/36, RN-03–07/11/12. Interfaces administrativas dos módulos serão entregues separadamente.
"""
from .scheduling import now,stamp

def complete(db, appointment_id, barber_user, current=None):
    current=current or now()
    a=db.execute("""SELECT a.*,s.loyalty_eligible FROM appointments a JOIN barbers b ON b.id=a.barber_id
       JOIN services s ON s.id=a.service_id WHERE a.id=? AND b.user_id=?""",(appointment_id,barber_user)).fetchone()
    if not a: raise PermissionError("Atendimento não pertence ao profissional.")
    if a["status"]!="EM_ATENDIMENTO": raise ValueError("Apenas atendimento em andamento pode ser concluído.")
    reward=db.execute("SELECT * FROM rewards WHERE appointment_id=? AND status='RESERVADA' AND client_id=?",(appointment_id,a["client_id"])).fetchone()
    paid=0 if reward else a["price_cents_snapshot"]
    items=db.execute("SELECT ss.supply_id,ss.quantity,s.quantity AS stock,s.name FROM service_supplies ss JOIN supplies s ON s.id=ss.supply_id WHERE service_id=?",(a["service_id"],)).fetchall()
    for item in items:
        if item["stock"]<item["quantity"]:
            raise ValueError("Estoque insuficiente: "+item["name"])
    t=stamp(current)
    for item in items:
        db.execute("UPDATE supplies SET quantity=quantity-? WHERE id=?",(item["quantity"],item["supply_id"]))
        db.execute("INSERT INTO stock_movements(supply_id,appointment_id,delta,reason,created_at) VALUES(?,?,?,'ATENDIMENTO',?)",(item["supply_id"],appointment_id,-item["quantity"],t))
    if paid>0:
        db.execute("INSERT INTO revenues(appointment_id,amount_cents,created_at) VALUES(?,?,?)",(appointment_id,paid,t))
    commission=(paid*a["commission_bps_snapshot"]+5000)//10000
    db.execute("INSERT INTO commissions(appointment_id,amount_cents,created_at) VALUES(?,?,?)",(appointment_id,commission,t))
    if reward:
        db.execute("UPDATE rewards SET status='UTILIZADA' WHERE id=?",(reward["id"],))
    elif paid>0 and a["loyalty_eligible"]:
        db.execute("INSERT INTO loyalty_credits(client_id,appointment_id,created_at) VALUES(?,?,?)",(a["client_id"],appointment_id,t))
        credits=db.execute("SELECT id FROM loyalty_credits WHERE client_id=? AND reward_id IS NULL ORDER BY id",(a["client_id"],)).fetchall()
        for i in range(0,len(credits)-9,10):
            rid=db.execute("INSERT INTO rewards(client_id,status,created_at) VALUES(?,'DISPONIVEL',?)",(a["client_id"],t)).lastrowid
            db.executemany("UPDATE loyalty_credits SET reward_id=? WHERE id=?",[(rid,c["id"]) for c in credits[i:i+10]])
    db.execute("UPDATE appointments SET status='CONCLUIDO',paid_cents=?,completed_at=? WHERE id=?",(paid,t,appointment_id))
