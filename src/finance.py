"""Financeiro e comissões em centavos: RF-28–30, RN-07/17."""
from datetime import date,datetime,time,timedelta,timezone
from flask import Blueprint,g,request,render_template,redirect,url_for,flash
from .auth import require_role
from .db import get_db,transaction
from .catalog import cents
from .scheduling import now,stamp,LOCAL,local
from decimal import InvalidOperation

bp=Blueprint("finance",__name__)

def period(start,end):
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if a>b or (b-a).days>3660:
        raise ValueError("Período inválido.")
    return stamp(datetime.combine(a,time.min,LOCAL)),stamp(datetime.combine(b+timedelta(days=1),time.min,LOCAL))

def totals(db,start,end):
    vals={}
    for key,table,column in [("revenue","revenues","created_at"),("commission","commissions","created_at"),("expense","expenses","occurred_at")]:
        vals[key]=db.execute(f"SELECT COALESCE(SUM(amount_cents),0) FROM {table} WHERE {column}>=? AND {column}<?",(start,end)).fetchone()[0]
    vals["result"]=vals["revenue"]-vals["commission"]-vals["expense"]
    return vals

def add_expense(db,admin_id,description,amount,day):
    description=description.strip()
    if not description or len(description)>250 or amount<=0:
        raise ValueError("Descrição ou valor inválidos.")
    d=date.fromisoformat(day)
    if d>now().astimezone(LOCAL).date():
        raise ValueError("Despesa deve ter data até hoje.")
    db.execute("INSERT INTO expenses(admin_id,description,amount_cents,occurred_at) VALUES(?,?,?,?)",(admin_id,description,amount,stamp(datetime.combine(d,time.min,LOCAL))))

def selected_period():
    today=now().astimezone(LOCAL).date()
    start=request.args.get("start",today.replace(day=1).isoformat())
    end=request.args.get("end",today.isoformat())
    try:
        low,high=period(start,end)
    except (ValueError,OverflowError):
        flash("Período inválido; exibindo mês atual.","error")
        start,end=today.replace(day=1).isoformat(),today.isoformat()
        low,high=period(start,end)
    return start,end,low,high

@bp.route("/admin/financeiro",methods=["GET","POST"])
@require_role("admin")
def admin():
    if request.method=="POST":
        try:
            with transaction() as db:
                add_expense(db,g.user["id"],request.form["description"],cents(request.form["amount"]),request.form["day"])
            flash("Despesa registrada.","success")
        except (ValueError,InvalidOperation,KeyError,OverflowError) as exc:
            flash(str(exc),"error")
        return redirect(url_for("finance.admin"))
    start,end,low,high=selected_period()
    db=get_db()
    expenses=db.execute("SELECT * FROM expenses WHERE occurred_at>=? AND occurred_at<? ORDER BY occurred_at DESC,id DESC",(low,high)).fetchall()
    revenues=db.execute("""SELECT r.*,s.name AS service,u.name AS barber FROM revenues r JOIN appointments a ON a.id=r.appointment_id
        JOIN services s ON s.id=a.service_id JOIN barbers b ON b.id=a.barber_id JOIN users u ON u.id=b.user_id
        WHERE r.created_at>=? AND r.created_at<? ORDER BY r.created_at DESC""",(low,high)).fetchall()
    commissions=db.execute("""SELECT u.name,COALESCE(SUM(c.amount_cents),0) AS amount FROM commissions c JOIN appointments a ON a.id=c.appointment_id
        JOIN barbers b ON b.id=a.barber_id JOIN users u ON u.id=b.user_id WHERE c.created_at>=? AND c.created_at<? GROUP BY b.id,u.name ORDER BY u.name""",(low,high)).fetchall()
    return render_template("finance.html",admin=True,start=start,end=end,summary=totals(db,low,high),expenses=expenses,revenues=revenues,commissions=commissions,local=local,today=now().astimezone(LOCAL).date().isoformat())

@bp.get("/barbeiro/comissoes")
@require_role("barber")
def barber():
    start,end,low,high=selected_period()
    rows=get_db().execute("""SELECT c.*,s.name AS service FROM commissions c JOIN appointments a ON a.id=c.appointment_id
        JOIN barbers b ON b.id=a.barber_id JOIN services s ON s.id=a.service_id
        WHERE b.user_id=? AND c.created_at>=? AND c.created_at<? ORDER BY c.created_at DESC""",(g.user["id"],low,high)).fetchall()
    return render_template("finance.html",admin=False,start=start,end=end,rows=rows,total=sum(r["amount_cents"] for r in rows),local=local)
