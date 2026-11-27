"""Validação reproduzível: 30 requisições, 1000 registros, Chromium 360/1280."""
import json,math,platform,statistics,tempfile,threading,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from werkzeug.serving import make_server
from src import create_app
from src.db import init_db,get_db,transaction
from src.auth import create_user
from src.scheduling import stamp,LOCAL
from playwright.sync_api import sync_playwright

def main():
    out=Path("evidence");out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        app=create_app({"TESTING":True,"SECRET_KEY":"local-test-only","DATABASE":str(Path(directory)/"test.sqlite3")})
        with app.app_context():
            init_db()
            ids={role:create_user(role.title(),role+"@example.test","validation-password",role) for role in ("client","barber","admin")}
            with transaction() as db:
                bid=db.execute("SELECT id FROM barbers").fetchone()[0]
                sid=db.execute("INSERT INTO services(name,price_cents,duration_min,loyalty_eligible) VALUES('Corte teste',5000,30,1)").lastrowid
                base=datetime.now(timezone.utc).replace(second=0,microsecond=0)-timedelta(days=50)
                rows=[]
                for i in range(1000):
                    a=base+timedelta(minutes=30*i);b=a+timedelta(minutes=30)
                    rows.append((ids["client"],bid,sid,stamp(a),stamp(b),"CONCLUIDO",5000,4000,5000,stamp(b)))
                db.executemany("INSERT INTO appointments(client_id,barber_id,service_id,start_at,end_at,status,price_cents_snapshot,commission_bps_snapshot,paid_cents,completed_at) VALUES(?,?,?,?,?,?,?,?,?,?)",rows)
                for a in db.execute("SELECT id,completed_at FROM appointments").fetchall():
                    db.execute("INSERT INTO revenues(appointment_id,amount_cents,created_at) VALUES(?,5000,?)",(a["id"],a["completed_at"]))
                    db.execute("INSERT INTO commissions(appointment_id,amount_cents,created_at) VALUES(?,2000,?)",(a["id"],a["completed_at"]))
        results={"python":platform.python_version(),"platform":platform.platform(),"appointments":1000,"requests":30,"endpoint":"/admin","viewport_checks":[]}
        client=app.test_client()
        with client.session_transaction() as session: session["user_id"]=ids["admin"]
        assert client.get("/admin").status_code==200
        samples=[]
        for _ in range(30):
            t=time.perf_counter();res=client.get("/admin");samples.append((time.perf_counter()-t)*1000)
            assert res.status_code==200
        results["p95_ms"]=round(sorted(samples)[math.ceil(.95*len(samples))-1],2)
        results["median_ms"]=round(statistics.median(samples),2)
        results["samples_ms"]=[round(x,2) for x in samples]
        assert results["p95_ms"]<=2000,results
        server=make_server("127.0.0.1",0,app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url=f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch()
                for width in (360,1280):
                    for role,paths in [("client",["/cliente","/agendamentos","/fila","/recompensas","/historico","/perfil"]),("barber",["/barbeiro","/barbeiro/agenda","/barbeiro/comissoes"]),("admin",["/admin","/admin/catalogo","/admin/estoque","/admin/financeiro"])]:
                        page=browser.new_page(viewport={"width":width,"height":900})
                        page.goto(url+"/login")
                        page.locator('input[name="email"]').fill(role+"@example.test")
                        page.locator('input[name="password"]').fill("validation-password")
                        page.locator('form button').first.click()
                        page.wait_for_url(lambda u:"/login" not in u)
                        for path in paths:
                            res=page.goto(url+path)
                            assert res.status==200,(role,path,res.status)
                            overflow=page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                            results["viewport_checks"].append({"role":role,"path":path,"width":width,"overflow":overflow})
                            if path in ("/cliente","/barbeiro","/admin"):
                                page.screenshot(path=str(out/f"{role}-{width}.png"))
                            assert not overflow,(role,path,width)
                        page.close()
                browser.close()
        finally:
            server.shutdown();thread.join()
        (out/"validation.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
        print("VALIDATION",json.dumps(results))
if __name__=="__main__":main()
