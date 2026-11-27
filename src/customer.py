"""Histórico, avaliação única e perfil próprio. RF-33–35."""
import sqlite3
from flask import Blueprint,g,request,render_template,redirect,url_for,flash,abort
from .auth import require_role
from .db import get_db,transaction
from .scheduling import stamp,now,local
from .dashboards import money

bp=Blueprint("customer",__name__)

def review(db,uid,aid,rating,comment,current=None):
    a=db.execute("SELECT client_id,status FROM appointments WHERE id=?",(aid,)).fetchone()
    if not a or a["client_id"]!=uid:
        raise PermissionError("Atendimento não pertence ao cliente.")
    if a["status"]!="CONCLUIDO" or rating not in range(1,6) or len(comment)>500:
        raise ValueError("Avaliação inválida. Escolha de 1 a 5 e até 500 caracteres.")
    if db.execute("SELECT 1 FROM reviews WHERE appointment_id=?",(aid,)).fetchone():
        raise ValueError("Atendimento já avaliado.")
    db.execute("INSERT INTO reviews(appointment_id,rating,comment,created_at) VALUES(?,?,?,?)",(aid,rating,comment.strip(),stamp(current or now())))

@bp.route("/historico",methods=["GET","POST"])
@require_role("client")
def history():
    if request.method=="POST":
        try:
            with transaction() as db:
                review(db,g.user["id"],int(request.form["id"]),int(request.form["rating"]),request.form.get("comment",""))
            flash("Obrigado pela avaliação!","success")
        except PermissionError:
            abort(403)
        except (ValueError,KeyError,OverflowError,sqlite3.IntegrityError) as exc:
            flash(str(exc) if isinstance(exc,ValueError) else "Avaliação não registrada.","error")
        return redirect(url_for("customer.history"))
    db=get_db()
    rows=db.execute("""SELECT a.*,s.name AS service,u.name AS barber,r.rating,r.comment FROM appointments a JOIN services s ON s.id=a.service_id
        JOIN barbers b ON b.id=a.barber_id JOIN users u ON u.id=b.user_id LEFT JOIN reviews r ON r.appointment_id=a.id
        WHERE a.client_id=? ORDER BY a.start_at DESC""",(g.user["id"],)).fetchall()
    completed=[a for a in rows if a["status"]=="CONCLUIDO"]
    return render_template("history.html",rows=rows,visits=len(completed),spent=sum(a["paid_cents"] or 0 for a in completed),local=local,money=money)

@bp.route("/perfil",methods=["GET","POST"])
@require_role("client")
def profile():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        if not 1<=len(name)<=100:
            flash("Informe um nome de até 100 caracteres.","error")
        else:
            with transaction() as db:
                db.execute("UPDATE users SET name=? WHERE id=?",(name,g.user["id"]))
            flash("Perfil atualizado.","success")
        return redirect(url_for("customer.profile"))
    return render_template("profile.html")
