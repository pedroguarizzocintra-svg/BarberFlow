"""Indicadores a partir do banco: RF-31/32, RN-17/18/19."""
from datetime import datetime,time,timedelta
from flask import g
from .scheduling import now,stamp,parse,LOCAL,local
from .finance import totals,selected_period,period
from .inventory import alerts
from .loyalty import balance,available_rewards

def money(cents):
    return "R$ "+f"{cents/100:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def union_minutes(intervals):
    merged=[]
    for start,end in sorted(intervals):
        if end<=start: continue
        if merged and start<=merged[-1][1]:
            merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:
            merged.append((start,end))
    return sum((b-a).total_seconds()/60 for a,b in merged)

def occupancy(db,day):
    low=datetime.combine(day,time.min,LOCAL)
    high=low+timedelta(days=1)
    work=reserved=0
    for barber in db.execute("SELECT b.id FROM barbers b JOIN users u ON u.id=b.user_id WHERE u.active=1"):
        bid=barber["id"]
        hours=[(datetime.combine(day,time.fromisoformat(h["start_time"]),LOCAL),
                datetime.combine(day,time.fromisoformat(h["end_time"]),LOCAL))
               for h in db.execute("SELECT * FROM working_hours WHERE barber_id=? AND weekday=?",(bid,day.weekday()))]
        work+=union_minutes(hours)
        bookings=db.execute("""SELECT start_at,end_at FROM appointments WHERE barber_id=?
            AND status IN ('CONFIRMADO','EM_ATENDIMENTO','CONCLUIDO') AND start_at<? AND end_at>?""",(bid,stamp(high),stamp(low))).fetchall()
        intersections=[]
        for a in bookings:
            for hs,he in hours:
                intersections.append((max(parse(a["start_at"]),hs),min(parse(a["end_at"]),he)))
        reserved+=union_minutes(intersections)
    return round(100*reserved/work,1) if work else 0

def client_metrics(db,uid):
    row=db.execute("SELECT count(*) AS visits,COALESCE(sum(paid_cents),0) AS spent FROM appointments WHERE client_id=? AND status='CONCLUIDO'",(uid,)).fetchone()
    upcoming=db.execute("""SELECT a.*,s.name AS service,u.name AS barber FROM appointments a JOIN services s ON s.id=a.service_id
        JOIN barbers b ON b.id=a.barber_id JOIN users u ON u.id=b.user_id WHERE a.client_id=? AND a.status='CONFIRMADO' AND a.start_at>=? ORDER BY a.start_at LIMIT 5""",(uid,stamp(now()))).fetchall()
    notes=db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 5",(uid,)).fetchall()
    return dict(visits=row["visits"],spent=row["spent"],credits=balance(db,uid),rewards=len(available_rewards(db,uid)),upcoming=upcoming,notes=notes)

def admin_metrics(db,low,high,day):
    summary=totals(db,low,high)
    count=db.execute("SELECT count(*) FROM appointments WHERE status='CONCLUIDO' AND completed_at>=? AND completed_at<?",(low,high)).fetchone()[0]
    summary.update(visits=count,ticket=(summary["revenue"]+count//2)//count if count else 0,occupancy=occupancy(db,day),alerts=alerts(db))
    return summary

def barber_metrics(db,uid,low,high):
    base=" FROM appointments a JOIN barbers b ON b.id=a.barber_id WHERE b.user_id=? AND a.status='CONCLUIDO' AND a.completed_at>=? AND a.completed_at<?"
    count=db.execute("SELECT count(*)"+base,(uid,low,high)).fetchone()[0]
    rating=db.execute("""SELECT AVG(r.rating) FROM reviews r JOIN appointments a ON a.id=r.appointment_id JOIN barbers b ON b.id=a.barber_id
        WHERE b.user_id=? AND a.completed_at>=? AND a.completed_at<?""",(uid,low,high)).fetchone()[0]
    commission=db.execute("""SELECT COALESCE(SUM(c.amount_cents),0) FROM commissions c JOIN appointments a ON a.id=c.appointment_id
        JOIN barbers b ON b.id=a.barber_id WHERE b.user_id=? AND c.created_at>=? AND c.created_at<?""",(uid,low,high)).fetchone()[0]
    agenda=db.execute("""SELECT a.*,s.name AS service,u.name AS client FROM appointments a JOIN barbers b ON b.id=a.barber_id
        JOIN services s ON s.id=a.service_id JOIN users u ON u.id=a.client_id WHERE b.user_id=? AND a.status IN ('CONFIRMADO','EM_ATENDIMENTO')
        ORDER BY a.start_at LIMIT 10""",(uid,)).fetchall()
    return dict(visits=count,rating=rating,commission=commission,agenda=agenda)

def context(db,role):
    if role=="client":
        return dict(metrics=client_metrics(db,g.user["id"]),money=money,local=local)
    start,end,low,high=selected_period()
    metrics=admin_metrics(db,low,high,now().astimezone(LOCAL).date()) if role=="admin" else barber_metrics(db,g.user["id"],low,high)
    return dict(metrics=metrics,start=start,end=end,money=money,local=local)
