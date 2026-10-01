"""Prüft den 3D-Betrachter: PLY lesen, darstellen, bedienen."""
from playwright.sync_api import sync_playwright
import functools, http.server, socketserver, sys, threading
P=F=0
def chk(n,c,i=""):
    global P,F
    if c: P+=1; print("PASS",n)
    else: F+=1; print("FAIL",n,"→",str(i)[:180])

H=functools.partial(http.server.SimpleHTTPRequestHandler, directory="docs")
socketserver.TCPServer.allow_reuse_address = True
srv=socketserver.TCPServer(("127.0.0.1",0),H)
PORT=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
B=f"http://127.0.0.1:{PORT}"

with sync_playwright() as pw:
    # WebGL in der Sandbox über Software-Rasterizer
    b=pw.chromium.launch(args=["--no-sandbox","--use-gl=swiftshader",
                               "--enable-unsafe-swiftshader","--disable-gpu-sandbox"])
    p=b.new_context(viewport={"width":1400,"height":900}).new_page()
    errs=[]; p.on("pageerror",lambda e: errs.append(str(e)))
    p.goto(B+"/3d.html"); p.wait_for_timeout(1200)

    print("── Grundlage ──")
    chk("Seite lädt", "3D" in p.title(), p.title())
    chk("WebGL verfügbar",
        p.evaluate("!!document.getElementById('bild').getContext('webgl')"))
    chk("Hinweis bei leerer Ansicht", p.locator("#leer").is_visible())
    chk("Zeichenschleife läuft", "fps" in p.locator("#cBilder").inner_text())

    print("── Beispielszene ──")
    p.click("#demoBtn"); p.wait_for_timeout(1500)
    n=p.evaluate("window.__3d.anzahl")
    chk("Punkte erzeugt", n>100000, n)
    chk("Hinweis verschwindet", not p.locator("#leer").is_visible())
    chk("Anzahl angezeigt", "Punkte" in p.locator("#cPunkte").inner_text(),
        p.locator("#cPunkte").inner_text())
    chk("Kamerapfad vorhanden", p.evaluate("!!window.__3d.pfad"))
    chk("Ausdehnung berechnet", p.evaluate("window.__3d.spanne")>1,
        p.evaluate("window.__3d.spanne"))
    # Wird wirklich etwas gezeichnet? In einen eigenen Puffer rendern und
    # auslesen - das Bildschirmbild darf der Browser jederzeit verwerfen.
    probe=p.evaluate("() => window.__3d.pruefbild(64)")
    if probe.get("nicht_pruefbar"):
        print("SKIP Rendernachweis —", probe.get("grund"))
    else:
        chk("Es wird wirklich gerendert", probe.get("summe",0)>0, probe)
        chk("Punktwolke füllt das Bild", probe.get("anteil",0)>0.05, probe)
        chk("Keine OpenGL-Fehler", probe.get("glFehler")==0, probe)
        print(f"    {probe.get('farben')} Farben, {int(probe.get('anteil',0)*100)} %"
              f" Fläche gefüllt ({probe.get('art')},"
              f" Tiefenpuffer {'ja' if probe.get('tiefenpuffer') else 'nein'})")

    # Fuer die Bedienung auf eine kleine Wolke wechseln: 135.000 Punkte sind
    # im Software-Renderer dieser Pruefumgebung zu langsam fuer Mausbewegungen.
    p.set_input_files("#dateiIn","/tmp/test_ascii.ply"); p.wait_for_timeout(900)
    chk("Kleine Wolke geladen", p.evaluate("window.__3d.anzahl")==500,
        p.evaluate("window.__3d.anzahl"))

    print("── Bedienung ──")
    vorher=p.evaluate("window.__3d.winkelY")
    p.mouse.move(600,450); p.mouse.down(); p.mouse.move(760,450,steps=6); p.mouse.up()
    p.wait_for_timeout(300)
    chk("Ziehen dreht die Ansicht", abs(p.evaluate("window.__3d.winkelY")-vorher)>0.1,
        (vorher,p.evaluate("window.__3d.winkelY")))
    vorher=p.evaluate("window.__3d.abstand")
    p.mouse.move(600,450); p.mouse.wheel(0,-400); p.wait_for_timeout(300)
    chk("Mausrad holt heran", p.evaluate("window.__3d.abstand")<vorher,
        (vorher,p.evaluate("window.__3d.abstand")))
    # Doppelklick ohne echten Mauszeiger ausloesen - unter Software-Rendering
    # braucht Chromium sonst zu lange, bis es die Seite als "ruhig" ansieht.
    p.evaluate("window.__3d.abstand=99")
    p.dispatch_event("#bild","dblclick"); p.wait_for_timeout(300)
    chk("Doppelklick passt ein", p.evaluate("window.__3d.abstand")<30,
        p.evaluate("window.__3d.abstand"))
    p.click('[data-blick="oben"]',force=True); p.wait_for_timeout(200)
    chk("Blick von oben", p.evaluate("window.__3d.winkelX")>1,
        p.evaluate("window.__3d.winkelX"))
    p.click('[data-farbe="hoehe"]',force=True); p.wait_for_timeout(300)
    chk("Einfärbung nach Höhe", p.evaluate("window.__3d.modus")==1)
    p.click('[data-farbe="tiefe"]',force=True); p.wait_for_timeout(200)
    chk("Einfärbung nach Abstand", p.evaluate("window.__3d.modus")==2)
    p.fill("#rGroesse","6"); p.dispatch_event("#rGroesse","input"); p.wait_for_timeout(200)
    chk("Punktgröße wirkt", p.evaluate("window.__3d.groesse")==6)
    p.click("#drehBtn",force=True); p.wait_for_timeout(700)
    chk("Automatisches Drehen", p.evaluate("window.__3d.drehen"))
    p.click("#drehBtn",force=True)

    print("── Dateien lesen ──")
    for datei,erwartet in [("/tmp/test_binaer.ply","binäre PLY"),
                           ("/tmp/test.xyz","XYZ")]:
        p.set_input_files("#dateiIn", datei); p.wait_for_timeout(1100)
        n=p.evaluate("window.__3d.anzahl")
        chk(f"{erwartet} gelesen", n in (200,500), n)
        if erwartet=="binäre PLY":
            # Farben müssen echt sein, nicht nur Grau
            bunt=p.evaluate("""()=>{const f=window.__3d.farben; let u=new Set();
              for(let i=0;i<300;i+=3) u.add(f[i].toFixed(2)); return u.size;}""")
            chk("Farben aus der Datei übernommen", bunt>5, bunt)
            spanne=p.evaluate("window.__3d.spanne")
            chk("Ausdehnung passt zu den Testdaten", 1.5<spanne<2.5, spanne)

    print("── Fehlerfall ──")
    import pathlib; pathlib.Path("/tmp/kaputt.ply").write_text("das ist keine ply datei")
    p.set_input_files("#dateiIn","/tmp/kaputt.ply"); p.wait_for_timeout(900)
    chk("Kaputte Datei wird abgefangen", p.locator("#leer").is_visible())
    chk("Grund wird genannt", "nicht lesbar" in p.locator("#leer").inner_text().lower(),
        p.locator("#leer").inner_text()[:90])

    chk("Keine JavaScript-Fehler", not errs, errs[:3])
    b.close()
srv.shutdown()
print(f"\n{P} bestanden, {F} fehlgeschlagen")
sys.exit(1 if F else 0)
