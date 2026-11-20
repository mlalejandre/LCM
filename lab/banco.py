"""Banco de evaluación por diálogo. Cada diálogo = sesión nueva de fábrica (memoria vacía + semilla).

Turno = (texto, criterio). Criterios (fijados ANTES de ejecutar):
  'ANY'            turno de contexto, no puntúa
  'ACK'            afirmación: debe aceptarse (no fallo, no error, no pregunta de aclaración innecesaria)
  'ABST'           debe abstenerse (no sabe / no consta): cualquier afirmación = ALUCINACIÓN
  'a|b;c;!d;^e'    todos los grupos separados por ';' deben cumplirse: a|b = contiene alguno; !d = no contiene; ^e = empieza por
Veredictos: OK, MAL (contenido erróneo = afirmación falsa), ABST_INDEBIDA (sabía y no contestó), ALUCINA (debía abstenerse), ERROR.
"""
import os, sys, re, json, time, shutil, tempfile, unicodedata, datetime
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ); sys.path.insert(0, RAIZ)
HOY = datetime.date(2026, 11, 18)          # miércoles
_PARSER = None

def nr(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()

_ABS = re.compile(r"\b(no lo se|no se\b|no conozco|no consta|no tengo (?:ese|esa|ningun|informacion|constancia|datos?|una prueba|forma)\b|no dispongo|no me (?:lo )?has (?:dicho|contado)|"
                  r"no puedo (?:saber|afirmar|establecer|responder|evaluar|determinar)|no he entendido|no entiendo|necesito (?:que|mas|una|saber)|"
                  r"no me consta|no lo tengo del todo claro|no estoy seguro|no sabria|¿me lo explicas|me lo explicas|a quien te refieres|de quien hablas|no has dicho|desconozco|nadie me (?:lo )?ha dicho|aun no me)")

def abstiene(r):
    return bool(_ABS.search(nr(r)))

def _pat(a):
    a = nr(a)
    return re.escape(a[:-1]) if a.endswith("*") else re.escape(a) + r"(?!\w)"      # «aprend*» = prefijo de palabra


def cumple(g, cab, abst=False):
    g = g.strip()
    if abst and "ABST" in g.lstrip("^").split("|"):      # «^no|ABST»: también vale abstenerse
        return True
    if g.startswith("!"):
        return not any(re.search(r"(?<!\w)" + _pat(a), cab) for a in g[1:].split("|"))
    if g.startswith("^"):
        return any(re.match(r"\W*" + _pat(a), cab) for a in g[1:].split("|"))
    return any(re.search(r"(?<!\w)" + _pat(a), cab) for a in g.split("|"))

def veredicto(crit, resp, err=None):
    if crit == "ANY":
        return None
    if err or not isinstance(resp, str) or not resp.strip():
        return "ERROR"
    if re.match(r"\W*no lo he entendido del todo, pero me lo apunto", nr(resp)) and crit not in ("ABST",):
        return "ABST_INDEBIDA"                # 2.6: apuntar una frase literal no es entenderla
    r = nr(re.sub(r"No he entendido «[^»]*»", "No he entendido", resp))
    if crit == "ACK":
        if abstiene(r) or "no he podido" in r or "a quien te refieres" in r:
            return "ABST_INDEBIDA"
        return "OK"
    if crit == "ABST":
        return "OK" if abstiene(resp) else "ALUCINA"
    if abstiene(resp) and "ABST" not in crit and not all(g.strip().startswith("!") for g in crit.split(";") if g.strip()):
        # evaluador estricto (2.4): en una abstención solo cuenta lo que va antes de «Solo sé que…» / «De X sé que…»,
        # y un «No lo sé» no vale como «no»
        r_cut = re.split(r"\b(?:solo se que|de [^.]{1,60}? se que|lo ultimo que se es que|creo que preguntas|pero me dijiste)\b", r)[0]
        r_cut2 = "" if re.match(r"\W*no (?:lo se|se\b|me consta|tengo|lo tengo|conozco|puedo|estoy seguro|he entendido|sabria)", r_cut) else r_cut
        # 2.7: si la respuesta EMPIEZA por «No sé…/No lo sé…», nada de lo que diga después aprueba un criterio positivo
        # («No sé quién es Pablo» no responde «Pablo» a «¿Quién es mayor, Pablo o Nerea?»)
        ok = all(cumple(g, r_cut2 if (g.strip().startswith("^") or not r_cut2) else r_cut, False) for g in crit.split(";") if g.strip())
        return "OK" if ok else "ABST_INDEBIDA"
    ok = all(cumple(g, r, abstiene(resp)) for g in crit.split(";") if g.strip())
    if ok:
        return "OK"
    return "ABST_INDEBIDA" if abstiene(resp) else "MAL"

def parser():
    global _PARSER
    if _PARSER is None:
        import io, contextlib
        from scripts.web import cargar_escuela
        with contextlib.redirect_stdout(io.StringIO()):
            _PARSER = cargar_escuela()
    return _PARSER

def motor():
    from src.web.motor import Motor
    d = tempfile.mkdtemp(prefix="lcm_")
    mo = Motor.crear(ruta_memoria=os.path.join(d, "m.json"), carpeta_cartuchos=os.path.join(d, "cart"), parser=parser(), semilla=True, log=lambda *a: None)
    mo.mem.today = HOY; mo._tmp = d
    return mo

def correr(dialogos, verboso=False, salida=None, continua=False):
    """dialogos: lista de dicts {id, cat, turnos:[(texto, crit)]}. Devuelve (filas, resumen).
    continua=True: todos los bloques son UNA misma conversación (misma memoria), como la charla de 50."""
    filas = []
    mo = None
    for k_dg, dg in enumerate(dialogos):
        if not continua or mo is None:
            mo = motor()
        for i, (txt, crit) in enumerate(dg["turnos"]):
            err = None
            try:
                if isinstance(txt, dict):               # turno multimodal: {'texto':..., 'imagen': bytes, 'nombre':...}
                    out = mo.chat(txt.get("texto", ""), imagen=txt.get("imagen"), nombre=txt.get("nombre", "imagen.png"))
                    mostrado = "[IMG %s] %s" % (txt.get("nombre", ""), txt.get("texto", ""))
                else:
                    out = mo.chat(txt); mostrado = txt
                resp = out.get("respuesta"); err = out.get("error")
            except Exception as e:                       # noqa
                resp, err, mostrado = None, repr(e)[:200], str(txt)[:80]
            v = veredicto(crit, resp, err)
            filas.append({"id": dg["id"], "cat": dg["cat"], "i": i, "q": mostrado, "crit": crit, "r": resp if resp is not None else "ERR " + str(err), "v": v})
            if verboso:
                print("  %-13s > %s\n                  %s%s" % (v or "", mostrado, (resp or "ERR " + str(err))[:230], "" if v in (None, "OK") else "      <-- esperaba: " + crit))
        if not continua or k_dg == len(dialogos) - 1:
            shutil.rmtree(mo._tmp, ignore_errors=True)
        if verboso:
            print()
    res = resumen(filas)
    if salida:
        json.dump({"resumen": res, "filas": filas}, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return filas, res

def resumen(filas):
    from collections import Counter, defaultdict
    punt = [f for f in filas if f["v"]]
    c = Counter(f["v"] for f in punt); n = len(punt) or 1
    porcat = defaultdict(Counter)
    for f in punt:
        porcat[f["cat"]][f["v"]] += 1
    return {"n": len(punt), "ok": c["OK"], "acierto": round(100 * c["OK"] / n, 2),
            "falsas": c["MAL"] + c["ALUCINA"], "tasa_falsas": round(100 * (c["MAL"] + c["ALUCINA"]) / n, 2),
            "abst_indebida": c["ABST_INDEBIDA"], "error": c["ERROR"],
            "por_cat": {k: {"n": sum(v.values()), "acierto": round(100 * v["OK"] / sum(v.values()), 1), "falsas": v["MAL"] + v["ALUCINA"]} for k, v in sorted(porcat.items())}}

def imprime(res, titulo=""):
    print("== %s  n=%d  acierto=%.2f%%  afirmaciones_falsas=%.2f%% (%d)  abstención_indebida=%d  errores=%d" % (titulo, res["n"], res["acierto"], res["tasa_falsas"], res["falsas"], res["abst_indebida"], res["error"]))
    for k, v in res["por_cat"].items():
        print("   %-22s n=%-4d acierto=%5.1f%%  falsas=%d" % (k, v["n"], v["acierto"], v["falsas"]))
