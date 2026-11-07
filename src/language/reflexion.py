"""parche-109: REFLEXION. El LCM repasa todos los conceptos que tiene en memoria y descubre los NEXOS que hay entre ellos, sin que nadie se los haya dicho:
  - SE_PARECE_A    conceptos cercanos (mismos antepasados, mismas partes, palabras comunes en su definicion). Motivo: "los dos son tipos de «felino»".
  - RELACIONADO_CON  A aparece en la definicion de B (y no es su tipo): "«bicicleta» se define con «pedal»".
  - PARTE_DE / MIEMBRO_DE / HECHO_DE  lo que el diccionario sabe y la memoria aun no tenia.
  - CONTRARIO_DE   antonimos entre conceptos de la memoria.
Todo sale del diccionario de conceptos y de lo que hay en memoria; cada nexo lleva su motivo ("por") y un peso. El resultado se guarda como cartucho `reflexion`
(se puede retirar sin dejar rastro) y se recalcula cuando cambia la memoria. No hay aleatoriedad: misma memoria, mismos nexos."""
import re
import time
from collections import defaultdict

CARTUCHO = "reflexion"
GENERICOS = {"hombre", "mujer", "persona", "gente", "cosa", "lugar", "parte", "forma", "tipo", "clase", "grupo", "humano", "hembra", "macho", "cuerpo", "área", "superficie", "sustancia", "material", "aire", "agua"}   # aparecen en miles de definiciones: enlazarlos seria ruido
SURFACE = {"SE_PARECE_A": "{s} se parece a {o}", "RELACIONADO_CON": "{s} está relacionado con {o}", "CONTRARIO_DE": "{s} es lo contrario de {o}", "MIEMBRO_DE": "{s} es miembro de {o}", "HECHO_DE": "{s} está hecho de {o}"}


def _C():
    from src.language import conceptos
    return conceptos


def _D():
    from src.language import definiciones
    return definiciones


def _nom(mem, k):
    v = (getattr(mem, "display", {}) or {}).get(k) or str(k).replace("_", " ").lower()
    return re.sub(r"^(?:el|la|los|las|un|una)\s+", "", v.strip(), flags=re.I)


def _resolver(mem, claves):
    """{clave: concepto} para las CLASES de la memoria que tienen sentido claro en el diccionario (coherente con lo que la memoria dice de ellas)."""
    C = _C()
    ids, dudosos = {}, []
    padres = defaultdict(set)
    for f in mem.facts:
        if str(f["p"]).upper() == "ES" and not f.get("neg"):
            padres[f["s"]].add(f["o"])
    for k in sorted(claves):
        nombre = _nom(mem, k)
        if not nombre or not nombre[:1].islower() or len(nombre) < 3:                 # Ana, Madrid, Rex: no son clases del diccionario
            continue
        cs = C.conceptos(nombre)
        if not cs:
            continue
        c = cs[0]
        ok = True
        if padres.get(k):
            asc = set(C.ascendentes(c, 12))
            nombres_asc = {C.nrm(C.etiqueta(x) or "") for x in asc} - {""}
            ok = False
            for p in padres[k]:
                pc = C.conceptos(_nom(mem, p))
                if C.nrm(_nom(mem, p)) in nombres_asc or (pc and (pc[0] in asc or any(x in asc for x in pc[:2]))):
                    ok = True
                    break
        if ok:
            ids[k] = c
        else:
            dudosos.append(k)
    return ids, dudosos


def _vecinos(ids, k, minimo):
    """k vecinos mas parecidos de cada concepto (coseno de rasgos) con indice invertido; ignora rasgos que tienen casi todos (antepasados muy generales)."""
    C = _C()
    claves = sorted(ids)
    vec = {kk: C.vector(ids[kk]) for kk in claves}
    nor = {kk: sum(x * x for x in v.values()) ** 0.5 for kk, v in vec.items()}
    post = defaultdict(list)
    for kk, v in vec.items():
        for f in v:
            post[f].append(kk)
    tope = max(60, len(claves) // 12)
    out = {}
    for kk in claves:
        acc = defaultdict(float)
        for f, w in vec[kk].items():
            lst = post[f]
            if len(lst) > tope:
                continue
            for o in lst:
                if o != kk:
                    acc[o] += w * vec[o][f]
        rank = sorted(((s / (nor[kk] * nor[o]) if nor[kk] * nor[o] else 0.0, o) for o, s in acc.items()), key=lambda x: (-x[0], x[1]))
        out[kk] = [(round(s, 3), o) for s, o in rank[:k] if s >= minimo]
    return out


def reflexionar(mem, k=3, minimo=0.45, log=None):
    """-> {"hechos": [...], "informe": {...}}. `mem` NO debe llevar montado el cartucho de reflexion (lo hace Motor.reflexionar)."""
    t0 = time.time()
    C, D = _C(), _D()
    if not C.disponible():
        return {"hechos": [], "informe": {"error": "El diccionario de conceptos no está instalado."}}
    claves = {f[x] for f in mem.facts if not f.get("neg") and f.get("cart") != CARTUCHO for x in ("s", "o")}
    ids, dudosos = _resolver(mem, claves)
    inv = {}
    for kk, c in ids.items():
        inv.setdefault(c, kk)
    X = D._load() if D.disponible() else {"ok": False}
    d = C._load()
    existentes = {(f["s"], f["p"], f["o"]) for f in mem.facts if f.get("cart") != CARTUCHO}
    ligados = set()
    for f in mem.facts:
        if f.get("cart") != CARTUCHO and str(f["p"]).upper() in ("ES", "PARTE_DE"):
            ligados.add(frozenset((f["s"], f["o"])))
    hechos, vistos = [], set()

    def nuevo(s, p, o, por, peso, simetrico=False):
        if s == o or (s, p, o) in existentes:
            return
        clave = (min(s, o), p, max(s, o)) if simetrico else (s, p, o)
        if clave in vistos:
            return
        if frozenset((s, o)) in ligados and p in ("SE_PARECE_A", "RELACIONADO_CON"):
            return
        vistos.add(clave)
        hechos.append({"s": s, "p": p, "o": o, "n": 1, "t": 0, "source": "reflexion", "imp": 1.0, "tick": 0, "archived": False, "neg": False, "when": "", "when_disp": "", "when_abs": None, "q": "",
                       "por": por, "peso": round(float(peso), 3)})

    # 1. parecidos
    for kk, lst in _vecinos(ids, k, minimo).items():
        for s, o in lst:
            a, b = ids[kk], ids[o]
            cm = D.comun_es(a, b) if X["ok"] else None
            lab = C.etiqueta(cm) if cm is not None else None
            if (cm is None and X["ok"]) or cm in (a, b):
                continue                                                        # sin un tipo común concreto el parecido es ruido (perro ~ hombre)
            por = f"los dos son tipos de «{lab}»" if lab and lab not in (_nom(mem, kk), _nom(mem, o)) else "comparten antepasados, partes y palabras de su definición"
            nuevo(kk, "SE_PARECE_A", o, por, s, simetrico=True)
    # 2. definicion, partes, miembros, sustancias, contrarios
    entrada = defaultdict(int)
    for kk, c in sorted(ids.items()):
        if X["ok"]:
            arriba = set(C.ascendentes(c))
            n_rel = 0
            for t in X["gl"].get(c, []):
                o = inv.get(t)
                if o and t not in arriba and t != c and not D._alto(t) and n_rel < 3 and entrada[o] < 15 and _nom(mem, o) not in GENERICOS:
                    antes_ = len(hechos)
                    nuevo(kk, "RELACIONADO_CON", o, f"«{_nom(mem, kk)}» se define con «{_nom(mem, o)}»", 0.5)
                    if len(hechos) > antes_:
                        n_rel += 1
                        entrada[o] += 1
        for t in d["parte"].get(c, []):
            o = inv.get(t)
            if o:
                nuevo(o, "PARTE_DE", kk, f"el diccionario dice que «{_nom(mem, o)}» es parte de «{_nom(mem, kk)}»", 0.8)
        for t in d["miembro"].get(c, []):
            o = inv.get(t)
            if o:
                nuevo(o, "MIEMBRO_DE", kk, f"el diccionario dice que «{_nom(mem, o)}» es miembro de «{_nom(mem, kk)}»", 0.8)
        for t in d["sustancia"].get(c, []):
            o = inv.get(t)
            if o:
                nuevo(kk, "HECHO_DE", o, f"el diccionario dice que «{_nom(mem, kk)}» está hecho de «{_nom(mem, o)}»", 0.8)
        for t in d["ant"].get(c, []):
            o = inv.get(t)
            if o:
                nuevo(kk, "CONTRARIO_DE", o, "son antónimos en el diccionario", 0.9, simetrico=True)
    dudas = []
    padres = defaultdict(list)
    for f in mem.facts:
        if str(f["p"]).upper() == "ES" and not f.get("neg") and f.get("cart") != CARTUCHO:
            padres[f["s"]].append(f["o"])
    for kk in dudosos:
        cs = C.conceptos(_nom(mem, kk))
        if cs and padres.get(kk):
            dudas.append({"concepto": _nom(mem, kk), "memoria": "es " + " y ".join(_nom(mem, p) for p in padres[kk][:2]), "diccionario": "es " + (" > ".join(C.cadena(cs[0], 3)) or "?")})
    hechos.sort(key=lambda h: (h["p"], h["s"], h["o"]))
    por_tipo = defaultdict(list)
    for h in hechos:
        por_tipo[h["p"]].append(h)
    grado = defaultdict(int)
    for h in hechos:
        grado[h["s"]] += 1
        grado[h["o"]] += 1
    con = set(grado)
    informe = {"conceptos": len(ids), "sin_sentido_claro": len(dudosos), "nexos": len(hechos), "segundos": round(time.time() - t0, 2), "por_tipo": {p: len(v) for p, v in sorted(por_tipo.items())},
               "ejemplos": {p: [{"s": _nom(mem, h["s"]), "o": _nom(mem, h["o"]), "por": h["por"]} for h in sorted(v, key=lambda x: -x["peso"])[:6]] for p, v in sorted(por_tipo.items())},
               "centrales": [{"concepto": _nom(mem, kk), "nexos": g} for kk, g in sorted(grado.items(), key=lambda x: (-x[1], x[0]))[:10]],
               "aislados": len([kk for kk in ids if kk not in con]), "dudas": dudas[:30], "fecha": time.strftime("%Y-%m-%d %H:%M")}
    if log:
        log(f"[reflexion] {len(ids)} conceptos -> {len(hechos)} nexos en {informe['segundos']} s")
    return {"hechos": hechos, "informe": informe}


def guardar(res, mem, base="cartuchos"):
    """Escribe cartuchos/reflexion.json y lo inserta. Devuelve la ruta."""
    from src.memory import cartuchos
    disp = {}
    for h in res["hechos"]:
        for x in (h["s"], h["o"]):
            disp.setdefault(x, _nom(mem, x))
    cont = {"hechos": [], "nexos": res["hechos"], "nombres": disp, "alias": {}, "verb_isa": {}, "defs": {}, "surface": {}, "display": {}, "opposites": []}
    ruta = cartuchos.guardar_cartucho(CARTUCHO, cont, {"fuente": "reflexión sobre los conceptos de la memoria", "descripcion": "Nexos descubiertos entre conceptos (parecidos, definiciones, partes, contrarios)", "informe": res["informe"]}, base)
    cartuchos.insertar(CARTUCHO, base)
    return ruta
