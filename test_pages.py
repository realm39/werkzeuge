"""Prüft die GitHub-Pages-Fassung: keine Serverzugriffe, ZIP-Export gültig."""
from playwright.sync_api import sync_playwright
import http.server, socketserver, threading, zipfile, pathlib, sys, re, json, functools
P=F=0
def chk(n,c,i=""):
    global P,F
    if c: P+=1; print("PASS",n)
    else: F+=1; print("FAIL",n,"→",str(i)[:200])

# Statisch ausliefern – genau wie GitHub Pages es täte
H=functools.partial(http.server.SimpleHTTPRequestHandler, directory="docs")
srv=socketserver.TCPServer(("127.0.0.1",8099),H); srv.allow_reuse_address=True
threading.Thread(target=srv.serve_forever,daemon=True).start()
BASIS="http://127.0.0.1:8099"

with sync_playwright() as pw:
    b=pw.chromium.launch(args=["--no-sandbox","--use-fake-ui-for-media-stream",
                               "--use-fake-device-for-media-stream"])
    ctx=b.new_context(viewport={"width":1400,"height":950},permissions=["camera"],
                      accept_downloads=True)
    p=ctx.new_page(); errs=[]; fremd=[]
    p.on("pageerror",lambda e: errs.append(str(e)))
    p.on("request",lambda r: fremd.append(r.url)
         if not r.url.startswith((BASIS,"data:","blob:")) else None)

    print("── Startseite ──")
    p.goto(BASIS+"/"); p.wait_for_timeout(700)
    chk("Startseite lädt", "MasterAgent" in p.title(), p.title())
    chk("Drei Werkzeuge verlinkt", p.locator("a.karte").count()==3)
    for ziel in ["kamera.html","berichtshelfer.html","praesentation.html"]:
        r=p.request.get(f"{BASIS}/{ziel}")
        chk(f"{ziel} erreichbar", r.status==200, r.status)
    chk("Hinweis auf Grenzen", "nicht läuft" in p.locator(".hinweis").inner_text()
        or "nicht" in p.locator(".hinweis h3").inner_text())

    print("── Kamera-Scan (statisch) ──")
    p.goto(BASIS+"/kamera.html"); p.wait_for_timeout(900)
    chk("Seite lädt", "Kamera" in p.title())
    chk("Modusanzeige", "Browser" in p.locator("#modus").inner_text())
    chk("Hinweis ohne Server", "kein Server" in p.locator("#info").inner_text(),
        p.locator("#info").inner_text()[:120])

    p.click("#startBtn"); p.wait_for_timeout(2500)
    chk("Kamera läuft", p.locator("#video").is_visible())
    chk("Messwerte live", any(c.isdigit() for c in p.locator("#chipScharf").inner_text()))

    p.fill("#nameIn","pagestest")
    p.select_option("#fpsIn","8")
    p.click("#scanBtn"); p.wait_for_timeout(3200); p.click("#scanBtn"); p.wait_for_timeout(900)
    anz=int(p.locator("#mAnzahl").inner_text())
    chk("Bilder aufgenommen", anz>=10, anz)
    u=p.locator("#urteil").inner_text()
    chk("Beurteilung im Browser berechnet", "Bewertung" in u and "Ø Schärfe" in u, u[:120])
    print("   ", u.split("\n")[0])

    print("── ZIP-Export ──")
    with p.expect_download() as dl:
        p.click("#zipBtn")
    pfad="/tmp/pages.zip"; dl.value.save_as(pfad)
    chk("ZIP heruntergeladen", pathlib.Path(pfad).stat().st_size>5000,
        pathlib.Path(pfad).stat().st_size)
    z=zipfile.ZipFile(pfad)
    chk("ZIP ist gültig", z.testzip() is None)
    namen=z.namelist()
    chk("START.md enthalten", "START.md" in namen)
    chk("Messwerte enthalten", "messwerte.json" in namen)
    bilder=[n for n in namen if n.startswith("bilder/")]
    chk("Bilder enthalten", len(bilder)==anz, (len(bilder),anz))
    chk("Bilder sind echte JPEGs", z.read(bilder[0])[:2]==b"\xff\xd8")
    start=z.read("START.md").decode()
    chk("Anleitung mit Befehl", "demo.py" in start and "--image_folder" in start)
    chk("Anleitung mit Installation", "huggingface-cli" in start)
    chk("Beurteilung im Paket", "Bewertung" in start, start[-200:])
    mw=json.loads(z.read("messwerte.json"))
    chk("Messwerte vollständig",
        all(k in mw["frames"][0] for k in ("schaerfe","helligkeit","bewegung","t")))

    print("── Agentenverbindung (darf fehlschlagen) ──")
    p.fill("#agentUrl","http://127.0.0.1:1")
    p.click("#agentBtn"); p.wait_for_timeout(5000)
    chk("Fehlversuch wird erklärt", "nicht erreichbar" in p.locator("#agentStatus").inner_text(),
        p.locator("#agentStatus").inner_text())
    chk("Grund wird genannt", "Keine Verbindung" in p.locator("#info").inner_text(),
        p.locator("#info").inner_text()[:140])

    print("── Keine fremden Zugriffe ──")
    extern=[u for u in fremd if not u.startswith("http://127.0.0.1:1")]
    chk("Keine externen Ressourcen", not extern, extern[:3])
    chk("Keine JavaScript-Fehler", not errs, errs[:3])
    b.close()
srv.shutdown()
print(f"\n{P} bestanden, {F} fehlgeschlagen")
sys.exit(1 if F else 0)
