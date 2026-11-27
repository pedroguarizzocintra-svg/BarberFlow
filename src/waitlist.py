"""Fila FIFO e oferta exclusiva, RF-15–19."""
from datetime import timedelta
from flask import Blueprint, g, request, render_template, redirect, url_for, flash, abort
from .auth import require_role
from .db import get_db, transaction
from .scheduling import now,stamp,parse,local,available,service_barber,reserve,options

bp=Blueprint("waitlist",__name__)

def join(db,client_id,service_id,barber_id,start,end,current=None):
    current=current or now()
    s,_=service_barber(db,service_id,barber_id)
    if start<=current or end-start<timedelta(minutes=s["duration_min"]):
        raise ValueError("Informe uma janela futura suficiente para o serviço.")
    if db.execute("SELECT 1 FROM waitlist WHERE client_id=? AND service_id=? AND barber_id=? AND window_start=? AND window_end=? AND status='ATIVA'",(client_id,service_id,barber_id,stamp(start),stamp(end))).fetchone():
        raise ValueError("Preferência já cadastrada.")
    return db.execute("""INSERT INTO waitlist(client_id,service_id,barber_id,window_start,window_end,created_at,status)
        VALUES(?,?,?,?,?,?,'ATIVA')""",(client_id,service_id,barber_id,stamp(start),stamp(end),stamp(current))).lastrowid

def offer_slot(db,service_id,barber_id,start,end,current=None):
    current=current or now()
    try:
        s,_=service_barber(db,service_id,barber_id)
    except ValueError:
        return None
    if end-start<timedelta(minutes=s["duration_min"]) or not available(db,barber_id,start,end,current=current):
        return None
    entry=db.execute("""SELECT w.* FROM waitlist w JOIN users u ON u.id=w.client_id
        WHERE w.status='ATIVA' AND u.active=1 AND w.service_id=? AND w.barber_id=?
        AND w.window_start<=? AND w.window_end>=?
        AND NOT EXISTS(SELECT 1 FROM offers o WHERE o.waitlist_id=w.id AND o.start_at=? AND o.end_at=?)
        AND NOT EXISTS(SELECT 1 FROM offers o WHERE o.waitlist_id=w.id AND o.status='PENDENTE')
        ORDER BY w.created_at,w.id LIMIT 1""",(service_id,barber_id,stamp(start),stamp(end),stamp(start),stamp(end))).fetchone()
    if not entry:
        return None
    expires=min(current+timedelta(minutes=15),start)
    oid=db.execute("INSERT INTO offers(waitlist_id,start_at,end_at,expires_at,status) VALUES(?,?,?,?,'PENDENTE')",
        (entry["id"],stamp(start),stamp(end),stamp(expires))).lastrowid
    db.execute("INSERT INTO notifications(user_id,message,created_at) VALUES(?,?,?)",
        (entry["client_id"],"Uma vaga está disponível em "+local(stamp(start))+". Confirme na fila de espera.",stamp(current)))
    return oid

def offer_row(db,oid):
    return db.execute("""SELECT o.*,w.client_id,w.service_id,w.barber_id,w.status AS entry_status FROM offers o JOIN waitlist w ON w.id=o.waitlist_id WHERE o.id=?""",(oid,)).fetchone()

def advance(db,row,current):
    return offer_slot(db,row["service_id"],row["barber_id"],parse(row["start_at"]),parse(row["end_at"]),current)

def expire_offers(db,current=None):
    current=current or now()
    ids=db.execute("SELECT id FROM offers WHERE status='PENDENTE' AND expires_at<=? ORDER BY expires_at,id",(stamp(current),)).fetchall()
    for item in ids:
        row=offer_row(db,item["id"])
        db.execute("UPDATE offers SET status='EXPIRADA' WHERE id=?",(row["id"],))
        advance(db,row,current)

def answer(db,oid,client_id,accept,current=None):
    current=current or now()
    row=offer_row(db,oid)
    if not row or row["client_id"]!=client_id:
        raise PermissionError("Oferta não pertence ao cliente.")
    if row["status"]!="PENDENTE" or row["entry_status"]!="ATIVA" or parse(row["expires_at"])<=current:
        raise ValueError("Oferta não está mais disponível.")
    if accept:
        s,_=service_barber(db,row["service_id"],row["barber_id"])
        if parse(row["start_at"])+timedelta(minutes=s["duration_min"])>parse(row["end_at"]):
            raise ValueError("A duração do serviço mudou; oferta incompatível.")
        aid=reserve(db,client_id,row["service_id"],row["barber_id"],parse(row["start_at"]),skip_offer=oid,current=current)
        db.execute("UPDATE offers SET status='ACEITA',appointment_id=? WHERE id=?",(aid,oid))
        db.execute("UPDATE waitlist SET status='ATENDIDA' WHERE id=?",(row["waitlist_id"],))
        return aid
    db.execute("UPDATE offers SET status='RECUSADA' WHERE id=?",(oid,))
    advance(db,row,current)

def withdraw(db,wid,client_id,current=None):
    current=current or now()
    row=db.execute("SELECT * FROM waitlist WHERE id=? AND client_id=?",(wid,client_id)).fetchone()
    if not row:
        raise PermissionError("Registro não pertence ao cliente.")
    if row["status"]!="ATIVA":
        raise ValueError("Registro não está ativo.")
    db.execute("UPDATE waitlist SET status='RETIRADA' WHERE id=?",(wid,))
    for item in db.execute("SELECT id FROM offers WHERE waitlist_id=? AND status='PENDENTE'",(wid,)).fetchall():
        offer=offer_row(db,item["id"])
        db.execute("UPDATE offers SET status='RECUSADA' WHERE id=?",(item["id"],))
        advance(db,offer,current)

@bp.route("/fila",methods=["GET","POST"])
@require_role("client")
def page():
    with transaction() as db:
        expire_offers(db)
    if request.method=="POST":
        try:
            with transaction() as db:
                expire_offers(db)
                action=request.form.get("action")
                if action=="join":
                    join(db,g.user["id"],int(request.form["service"]),int(request.form["barber"]),parse(request.form["start"]),parse(request.form["end"]))
                elif action in ("accept","decline"):
                    answer(db,int(request.form["id"]),g.user["id"],action=="accept")
                elif action=="withdraw":
                    withdraw(db,int(request.form["id"]),g.user["id"])
                else:
                    raise ValueError("Operação inválida.")
            flash("Fila atualizada.","success")
        except PermissionError:
            abort(403)
        except (ValueError,KeyError,OverflowError) as exc:
            flash(str(exc),"error")
        return redirect(url_for("waitlist.page"))
    db=get_db()
    services,barbers=options(db)
    rows=db.execute("SELECT w.*,s.name AS service,u.name AS barber FROM waitlist w JOIN services s ON s.id=w.service_id JOIN barbers b ON b.id=w.barber_id JOIN users u ON u.id=b.user_id WHERE w.client_id=? ORDER BY w.id DESC",(g.user["id"],)).fetchall()
    offers=db.execute("SELECT o.* FROM offers o JOIN waitlist w ON w.id=o.waitlist_id WHERE w.client_id=? ORDER BY o.id DESC",(g.user["id"],)).fetchall()
    notes=db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC",(g.user["id"],)).fetchall()
    return render_template("waitlist.html",services=services,barbers=barbers,rows=rows,offers=offers,notes=notes,local=local)
