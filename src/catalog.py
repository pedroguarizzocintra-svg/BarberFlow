"""Catálogo e expediente administrativo (RF-04–06)."""
from datetime import time
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, render_template, redirect, url_for, flash
from .auth import require_role
from .db import get_db, transaction
from .scheduling import parse, LOCAL, now, stamp

bp=Blueprint("catalog",__name__)

def cents(raw):
    v=Decimal(raw.replace(",","."))
    if not v.is_finite() or v<0 or v>100000 or v*100!=int(v*100):
        raise ValueError("Valor inválido (até duas casas decimais).")
    return int(v*100)

def save_service(db,form):
    name=form.get("name","").strip()
    description=form.get("description","").strip()
    duration=int(form["duration"])
    price=cents(form["price"])
    image=form.get("image","").strip()
    if not name or len(name)>100 or len(description)>1000 or not 1<=duration<=480:
        raise ValueError("Nome, descrição ou duração inválidos.")
    if image and (not image.startswith("https://") or len(image)>500):
        raise ValueError("Imagem deve ter URL HTTPS válida.")
    fields=(name,description,image or None,price,duration,int(form.get("eligible")=="1"),int(form.get("active")=="1"))
    if form.get("id"):
        result=db.execute("UPDATE services SET name=?,description=?,image_path=?,price_cents=?,duration_min=?,loyalty_eligible=?,active=? WHERE id=?",(*fields,int(form["id"])))
        if not result.rowcount: raise ValueError("Serviço inexistente.")
    else:
        db.execute("INSERT INTO services(name,description,image_path,price_cents,duration_min,loyalty_eligible,active) VALUES(?,?,?,?,?,?,?)",fields)

def save_hours(db,form):
    bid=int(form["barber"])
    weekday=int(form["weekday"])
    start=time.fromisoformat(form["start"])
    end=time.fromisoformat(form["end"])
    if weekday not in range(7) or start>=end or start.second or end.second or start.microsecond or end.microsecond:
        raise ValueError("Expediente inválido.")
    start,end=start.strftime("%H:%M"),end.strftime("%H:%M")
    if not db.execute("SELECT 1 FROM barbers WHERE id=?",(bid,)).fetchone():
        raise ValueError("Barbeiro inexistente.")
    if db.execute("SELECT 1 FROM working_hours WHERE barber_id=? AND weekday=? AND start_time<? AND end_time>?",(bid,weekday,end,start)).fetchone():
        raise ValueError("Expedientes não podem se sobrepor.")
    db.execute("INSERT INTO working_hours(barber_id,weekday,start_time,end_time) VALUES(?,?,?,?)",(bid,weekday,start,end))

def remove_hours(db,hid):
    row=db.execute("SELECT * FROM working_hours WHERE id=?",(hid,)).fetchone()
    if not row: raise ValueError("Expediente inexistente.")
    reservations=db.execute("SELECT start_at,end_at FROM appointments WHERE barber_id=? AND status IN ('CONFIRMADO','EM_ATENDIMENTO') AND end_at>? UNION ALL SELECT o.start_at,o.end_at FROM offers o JOIN waitlist w ON w.id=o.waitlist_id WHERE w.barber_id=? AND o.status='PENDENTE' AND o.expires_at>?",(row["barber_id"],stamp(now()),row["barber_id"],stamp(now()))).fetchall()
    for a in reservations:
        start,end=parse(a["start_at"]).astimezone(LOCAL),parse(a["end_at"]).astimezone(LOCAL)
        if start.weekday()==row["weekday"] and start.strftime("%H:%M")<row["end_time"] and end.strftime("%H:%M")>row["start_time"]:
            raise ValueError("Existem reservas ou ofertas vinculadas ao expediente.")
    db.execute("DELETE FROM working_hours WHERE id=?",(hid,))

@bp.route("/admin/catalogo",methods=["GET","POST"])
@require_role("admin")
def admin():
    if request.method=="POST":
        try:
            with transaction() as db:
                action=request.form.get("action")
                if action=="service": save_service(db,request.form)
                elif action=="hours": save_hours(db,request.form)
                elif action=="remove_hours": remove_hours(db,int(request.form["id"]))
                elif action=="commission":
                    value=cents(request.form["commission"])
                    if value>10000: raise ValueError("Comissão deve ficar entre 0 e 100%.")
                    db.execute("UPDATE barbers SET commission_bps=? WHERE id=?",(value,int(request.form["barber"])))
                else: raise ValueError("Operação inválida.")
            flash("Configuração atualizada.","success")
        except (ValueError,InvalidOperation,KeyError,OverflowError) as exc:
            flash(str(exc),"error")
        return redirect(url_for("catalog.admin"))
    db=get_db()
    return render_template("catalog_admin.html",services=db.execute("SELECT * FROM services ORDER BY id").fetchall(),
        barbers=db.execute("SELECT b.*,u.name FROM barbers b JOIN users u ON u.id=b.user_id ORDER BY u.name").fetchall(),
        hours=db.execute("SELECT h.*,u.name FROM working_hours h JOIN barbers b ON b.id=h.barber_id JOIN users u ON u.id=b.user_id ORDER BY weekday,start_time").fetchall())
