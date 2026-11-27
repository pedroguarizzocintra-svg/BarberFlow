"""Agenda transacional: RF-07–14, RN-01/02/16/20."""
from datetime import datetime, timedelta, timezone, date, time
from zoneinfo import ZoneInfo
from flask import Blueprint, g, request, render_template, redirect, url_for, flash, abort
from .auth import require_role
from .db import get_db, transaction

bp = Blueprint("agenda", __name__)
LOCAL = ZoneInfo("America/Sao_Paulo")

def now():
    return datetime.now(timezone.utc).replace(microsecond=0)

def stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")

def parse(value):
    d = datetime.fromisoformat(value)
    return (d.replace(tzinfo=LOCAL) if d.tzinfo is None else d).astimezone(timezone.utc)

def local(value):
    return parse(value).astimezone(LOCAL).strftime("%d/%m/%Y %H:%M")

def service_barber(db, service_id, barber_id):
    s = db.execute("SELECT * FROM services WHERE id=? AND active=1",(service_id,)).fetchone()
    b = db.execute("SELECT b.* FROM barbers b JOIN users u ON u.id=b.user_id WHERE b.id=? AND u.active=1 AND u.role='barber'",(barber_id,)).fetchone()
    if not s or not b:
        raise ValueError("Serviço ou profissional indisponível.")
    return s,b

def available(db, barber_id, start, end, skip_appointment=0, skip_offer=0, current=None):
    current = current or now()
    if start <= current or end <= start or start.second or start.microsecond or end.second or end.microsecond:
        return False
    a,b = start.astimezone(LOCAL),end.astimezone(LOCAL)
    if a.date()!=b.date():
        return False
    hours = db.execute("SELECT 1 FROM working_hours WHERE barber_id=? AND weekday=? AND start_time<=? AND end_time>=?",
                       (barber_id,a.weekday(),a.strftime("%H:%M"),b.strftime("%H:%M"))).fetchone()
    if not hours:
        return False
    if db.execute("""SELECT 1 FROM appointments WHERE barber_id=? AND id!=?
        AND status IN ('CONFIRMADO','EM_ATENDIMENTO','CONCLUIDO') AND start_at<? AND end_at>?""",
        (barber_id,skip_appointment,stamp(end),stamp(start))).fetchone():
        return False
    if db.execute("""SELECT 1 FROM offers o JOIN waitlist w ON w.id=o.waitlist_id
        WHERE w.barber_id=? AND o.id!=? AND o.status='PENDENTE' AND o.expires_at>?
        AND o.start_at<? AND o.end_at>?""",(barber_id,skip_offer,stamp(current),stamp(end),stamp(start))).fetchone():
        return False
    return True

def reserve(db, client_id, service_id, barber_id, start, skip_offer=0, current=None, reward_id=None):
    s,b = service_barber(db,service_id,barber_id)
    end = start+timedelta(minutes=s["duration_min"])
    if not available(db,barber_id,start,end,skip_offer=skip_offer,current=current):
        raise ValueError("Horário indisponível ou fora do expediente.")
    aid = db.execute("""INSERT INTO appointments(client_id,barber_id,service_id,start_at,end_at,status,price_cents_snapshot,commission_bps_snapshot)
        VALUES(?,?,?,?,?,'CONFIRMADO',?,?)""",(client_id,barber_id,service_id,stamp(start),stamp(end),s["price_cents"],b["commission_bps"])).lastrowid
    if reward_id is not None:
        from .loyalty import reserve_reward
        reserve_reward(db,client_id,aid,reward_id)
    return aid

def owned(db, appointment_id, client_id):
    row=db.execute("SELECT * FROM appointments WHERE id=? AND client_id=?",(appointment_id,client_id)).fetchone()
    if not row:
        raise PermissionError("Atendimento não pertence ao cliente.")
    if row["status"]!="CONFIRMADO":
        raise ValueError("Atendimento não pode ser alterado.")
    return row

def cancel(db, appointment_id, client_id, current=None):
    from .waitlist import offer_slot
    row=owned(db,appointment_id,client_id)
    db.execute("UPDATE appointments SET status='CANCELADO' WHERE id=?",(appointment_id,))
    db.execute("UPDATE rewards SET status='DISPONIVEL',appointment_id=NULL WHERE appointment_id=? AND status='RESERVADA'",(appointment_id,))
    offer_slot(db,row["service_id"],row["barber_id"],parse(row["start_at"]),parse(row["end_at"]),current=current)

def reschedule(db, appointment_id, client_id, start, current=None):
    from .waitlist import offer_slot
    row=owned(db,appointment_id,client_id)
    service_barber(db,row["service_id"],row["barber_id"])
    end=start+(parse(row["end_at"])-parse(row["start_at"]))
    if not available(db,row["barber_id"],start,end,skip_appointment=appointment_id,current=current):
        raise ValueError("Novo horário indisponível. A reserva anterior foi mantida.")
    if stamp(start)==row["start_at"]:
        return
    db.execute("UPDATE appointments SET start_at=?,end_at=? WHERE id=?",(stamp(start),stamp(end),appointment_id))
    offer_slot(db,row["service_id"],row["barber_id"],parse(row["start_at"]),parse(row["end_at"]),current=current)

def transition(db, appointment_id, barber_user, action, current=None):
    current=current or now()
    row=db.execute("SELECT a.* FROM appointments a JOIN barbers b ON b.id=a.barber_id WHERE a.id=? AND b.user_id=?",(appointment_id,barber_user)).fetchone()
    if not row:
        raise PermissionError("Atendimento não pertence ao profissional.")
    if row["status"]!="CONFIRMADO" or action not in ("start","absent"):
        raise ValueError("Transição inválida.")
    if action=="absent" and current<parse(row["start_at"]):
        raise ValueError("A ausência só pode ser registrada após o início previsto.")
    if action=="start" and current<parse(row["start_at"]):
        raise ValueError("O atendimento só pode iniciar a partir do horário previsto.")
    if action=="start" and db.execute("SELECT 1 FROM appointments WHERE barber_id=? AND status='EM_ATENDIMENTO'",(row["barber_id"],)).fetchone():
        raise ValueError("Finalize o atendimento em andamento primeiro.")
    db.execute("UPDATE appointments SET status=? WHERE id=?",("EM_ATENDIMENTO" if action=="start" else "AUSENTE",appointment_id))
    if action=="absent":
        db.execute("UPDATE rewards SET status='DISPONIVEL',appointment_id=NULL WHERE appointment_id=? AND status='RESERVADA'",(appointment_id,))

def slots(db, service_id, barber_id, day, current=None):
    s,_=service_barber(db,service_id,barber_id)
    current=current or now()
    result=[]
    for h in db.execute("SELECT * FROM working_hours WHERE barber_id=? AND weekday=? ORDER BY start_time",(barber_id,day.weekday())):
        start=datetime.combine(day,time.fromisoformat(h["start_time"]),LOCAL).astimezone(timezone.utc)
        stop=datetime.combine(day,time.fromisoformat(h["end_time"]),LOCAL).astimezone(timezone.utc)
        while start+timedelta(minutes=s["duration_min"])<=stop:
            if available(db,barber_id,start,start+timedelta(minutes=s["duration_min"]),current=current):
                result.append(stamp(start))
            start+=timedelta(minutes=15)
    return result

def expire():
    from .waitlist import expire_offers
    with transaction() as db:
        expire_offers(db)

def options(db):
    return (db.execute("SELECT * FROM services WHERE active=1 ORDER BY name").fetchall(),
            db.execute("SELECT b.id,u.name FROM barbers b JOIN users u ON u.id=b.user_id WHERE u.active=1 ORDER BY u.name").fetchall())

@bp.route("/agendamentos",methods=["GET","POST"])
@require_role("client")
def appointments():
    expire()
    if request.method=="POST":
        try:
            with transaction() as db:
                from .waitlist import expire_offers
                expire_offers(db)
                action=request.form.get("action")
                if action=="book":
                    reserve(db,g.user["id"],int(request.form["service"]),int(request.form["barber"]),parse(request.form["start"]),reward_id=int(request.form["reward"]) if request.form.get("reward") else None)
                elif action=="cancel":
                    cancel(db,int(request.form["id"]),g.user["id"])
                elif action=="reschedule":
                    reschedule(db,int(request.form["id"]),g.user["id"],parse(request.form["start"]))
                else:
                    raise ValueError("Operação inválida.")
            flash("Agenda atualizada.", "success")
        except PermissionError:
            abort(403)
        except (ValueError,KeyError,OverflowError) as exc:
            flash(str(exc),"error")
        return redirect(url_for("agenda.appointments"))
    db=get_db()
    services,barbers=options(db)
    rows=db.execute("""SELECT a.*,s.name AS service,u.name AS barber,EXISTS(SELECT 1 FROM rewards r WHERE r.appointment_id=a.id AND r.status IN ('RESERVADA','UTILIZADA')) AS has_reward FROM appointments a JOIN services s ON s.id=a.service_id
        JOIN barbers b ON b.id=a.barber_id JOIN users u ON u.id=b.user_id WHERE a.client_id=? ORDER BY a.start_at DESC""",(g.user["id"],)).fetchall()
    times=[]
    selected_service=request.args.get("service",type=int)
    selected_barber=request.args.get("barber",type=int)
    day=request.args.get("day",now().astimezone(LOCAL).date().isoformat())
    if selected_service and selected_barber:
        try:
            times=slots(db,selected_service,selected_barber,date.fromisoformat(day))
        except (ValueError,OverflowError):
            flash("Seleção inválida.","error")
    from .loyalty import available_rewards
    rewards=available_rewards(db,g.user["id"]) if any(s["id"]==selected_service and s["loyalty_eligible"] and s["price_cents"]>0 for s in services) else []
    return render_template("appointments.html",rewards=rewards,services=services,barbers=barbers,rows=rows,times=times,
                           selected_service=selected_service,selected_barber=selected_barber,day=day,local=local)

@bp.route("/barbeiro/agenda",methods=["GET","POST"])
@require_role("barber")
def barber_agenda():
    if request.method=="POST":
        try:
            with transaction() as db:
                if request.form["action"]=="complete":
                    from .operations import complete
                    complete(db,int(request.form["id"]),g.user["id"])
                else:
                    transition(db,int(request.form["id"]),g.user["id"],request.form["action"])
            flash("Atendimento atualizado.","success")
        except PermissionError:
            abort(403)
        except (ValueError,KeyError) as exc:
            flash(str(exc),"error")
        return redirect(url_for("agenda.barber_agenda"))
    rows=get_db().execute("""SELECT a.*,s.name AS service,u.name AS client,EXISTS(SELECT 1 FROM rewards r WHERE r.appointment_id=a.id AND r.status='RESERVADA') AS has_reward FROM appointments a JOIN barbers b ON b.id=a.barber_id
        JOIN services s ON s.id=a.service_id JOIN users u ON u.id=a.client_id WHERE b.user_id=? ORDER BY a.start_at""",(g.user["id"],)).fetchall()
    return render_template("barber_agenda.html",rows=rows,local=local)
