"""Dados fictícios, opcionais e não destrutivos para demonstração."""
import click
from .db import get_db,transaction

@click.command("seed-catalog")
def seed_catalog():
    with transaction() as db:
        barber=db.execute("SELECT b.id FROM barbers b JOIN users u ON u.id=b.user_id WHERE u.email='barbeiro@example.test'").fetchone()
        if not barber: raise click.ClickException("Execute seed-demo primeiro.")
        for name,desc,price,duration,eligible in [("Corte tradicional","Corte com acabamento",5000,40,1),("Degradê","Acabamento em degradê",6500,45,1),("Barba","Modelagem e acabamento",3500,30,0)]:
            if not db.execute("SELECT 1 FROM services WHERE name=?",(name,)).fetchone():
                db.execute("INSERT INTO services(name,description,price_cents,duration_min,loyalty_eligible) VALUES(?,?,?,?,?)",(name,desc,price,duration,eligible))
        for weekday in range(6):
            if not db.execute("SELECT 1 FROM working_hours WHERE barber_id=? AND weekday=?",(barber["id"],weekday)).fetchone():
                db.execute("INSERT INTO working_hours(barber_id,weekday,start_time,end_time) VALUES(?,?,?,?)",(barber["id"],weekday,"09:00","18:00"))
        if not db.execute("SELECT 1 FROM supplies WHERE name='Lâmina demo'").fetchone():
            sid=db.execute("INSERT INTO supplies(name,quantity,min_quantity) VALUES('Lâmina demo',0,5)").lastrowid
            from .inventory import move,set_consumption
            move(db,sid,30,"Estoque fictício inicial")
            for s in db.execute("SELECT id FROM services WHERE name IN ('Corte tradicional','Degradê','Barba')").fetchall():
                set_consumption(db,s["id"],sid,1)
    click.echo("Catálogo fictício preparado; registros existentes preservados.")
