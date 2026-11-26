"""Estoque e consumo configurável: RF-24–27."""
from flask import Blueprint,g,request,render_template,redirect,url_for,flash
from .auth import require_role
from .db import get_db,transaction
from .scheduling import now,stamp,local

bp=Blueprint("inventory",__name__)

def number(raw,minimum=0):
    n=int(raw)
    if not minimum<=n<=100000000:
        raise ValueError("Quantidade fora do limite permitido.")
    return n

def save_supply(db,form):
    name=form.get("name","").strip()
    if not name or len(name)>100:
        raise ValueError("Nome de insumo inválido.")
    minimum=number(form["minimum"])
    active=int(form.get("active")=="1")
    if form.get("id"):
        sid=int(form["id"])
        if not active and db.execute("SELECT 1 FROM service_supplies WHERE supply_id=?",(sid,)).fetchone():
            raise ValueError("Remova os vínculos de consumo antes de desativar o insumo.")
        if not db.execute("UPDATE supplies SET name=?,min_quantity=?,active=? WHERE id=?",(name,minimum,active,sid)).rowcount:
            raise ValueError("Insumo inexistente.")
        return sid
    return db.execute("INSERT INTO supplies(name,quantity,min_quantity,active) VALUES(?,0,?,?)",(name,minimum,active)).lastrowid

def move(db,sid,delta,reason,current=None):
    row=db.execute("SELECT * FROM supplies WHERE id=? AND active=1",(sid,)).fetchone()
    reason=reason.strip()
    if not row or delta==0 or abs(delta)>100000000 or not reason or len(reason)>250:
        raise ValueError("Movimentação inválida.")
    if row["quantity"]+delta<0:
        raise ValueError("Estoque insuficiente: "+row["name"])
    db.execute("UPDATE supplies SET quantity=quantity+? WHERE id=?",(delta,sid))
    db.execute("INSERT INTO stock_movements(supply_id,delta,reason,created_at) VALUES(?,?,?,?)",(sid,delta,reason,stamp(current or now())))

def set_consumption(db,service_id,supply_id,quantity):
    if not db.execute("SELECT 1 FROM services WHERE id=?",(service_id,)).fetchone():
        raise ValueError("Serviço inexistente.")
    if not db.execute("SELECT 1 FROM supplies WHERE id=? AND active=1",(supply_id,)).fetchone():
        raise ValueError("Insumo indisponível.")
    if quantity<0 or quantity>100000000:
        raise ValueError("Quantidade inválida.")
    if quantity==0:
        db.execute("DELETE FROM service_supplies WHERE service_id=? AND supply_id=?",(service_id,supply_id))
    else:
        db.execute("""INSERT INTO service_supplies(service_id,supply_id,quantity) VALUES(?,?,?)
            ON CONFLICT(service_id,supply_id) DO UPDATE SET quantity=excluded.quantity""",(service_id,supply_id,quantity))

def alerts(db):
    return db.execute("SELECT * FROM supplies WHERE active=1 AND quantity<=min_quantity ORDER BY name").fetchall()

@bp.route("/admin/estoque",methods=["GET","POST"])
@require_role("admin")
def page():
    if request.method=="POST":
        try:
            with transaction() as db:
                action=request.form.get("action")
                if action=="supply":
                    save_supply(db,request.form)
                elif action=="move":
                    direction=request.form["direction"]
                    if direction not in ("in","out"): raise ValueError("Tipo inválido.")
                    move(db,int(request.form["id"]),number(request.form["quantity"],1)*(1 if direction=="in" else -1),request.form["reason"])
                elif action=="consumption":
                    set_consumption(db,int(request.form["service"]),int(request.form["supply"]),number(request.form["quantity"]))
                else: raise ValueError("Operação inválida.")
            flash("Estoque atualizado.","success")
        except (ValueError,KeyError,OverflowError) as exc:
            flash(str(exc),"error")
        return redirect(url_for("inventory.page"))
    db=get_db()
    return render_template("inventory.html",supplies=db.execute("SELECT * FROM supplies ORDER BY name").fetchall(),
        services=db.execute("SELECT * FROM services ORDER BY name").fetchall(),
        links=db.execute("""SELECT ss.*,s.name AS service,i.name AS supply FROM service_supplies ss JOIN services s ON s.id=ss.service_id JOIN supplies i ON i.id=ss.supply_id ORDER BY s.name,i.name""").fetchall(),
        movements=db.execute("""SELECT m.*,s.name FROM stock_movements m JOIN supplies s ON s.id=m.supply_id ORDER BY m.id DESC""").fetchall(),
        alerts=alerts(db),local=local)
