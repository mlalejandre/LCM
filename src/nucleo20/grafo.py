"""LCM 2.27 · GRAFO de entidades y relaciones.

Cada entidad (una persona, una cosa, un sitio) es un NODO con su ficha: nombre, clase, género y todo lo que se ha dicho de ella. Entre dos
nodos puede haber VARIAS aristas con su tipo («hermana» y «compañera de piso» a la vez). Lo que no se ha dicho se deduce con REGLAS que
son datos, no código por cada pregunta:

  · simétricas:   si A es hermano de B, B lo es de A
  · inversas:     si A es padre de B, B es hijo de A
  · composición:  el padre del padre es el abuelo; el hermano del padre, el tío; el padre de la pareja, el suegro…
  · supuestas:    la pareja de quien es padre o madre se supone el otro progenitor (se dice «que yo sepa»)
  · transitivas:  lo que está en algo que está en otra cosa, está en esa otra cosa (lugares; no solo personas)

El cierre se calcula aplicando las reglas hasta que no sale nada nuevo, y cada arista deducida guarda de dónde sale, para poder explicarlo.
Cuando entre dos nodos no hay una relación con nombre, se da el CAMINO («Sara es la novia de Tomás, y Tomás es el hermano de Álex»).
"""
from __future__ import annotations

import os
import re

from .morfo import sa
from . import nucleo as _N

SIM = set(_N.SIMETRICAS) | {"conviviente", "pareja"}
INV = dict(_N.INVERSAS)
INV.update({"padre": "hijo", "hijo": "padre", "abuelo": "nieto", "nieto": "abuelo", "tio": "sobrino", "sobrino": "tio", "suegro": "yerno", "yerno": "suegro",
            "bisabuelo": "bisnieto", "bisnieto": "bisabuelo", "padrastro": "hijastro", "hijastro": "padrastro", "dueño": "mascota"})
# r1(x, y) y r2(y, z)  =>  r(x, z).   Léase: «el r1 del r2 de z es su r».   Último campo: supuesta.
COMP = [
    ("padre", "padre", "abuelo", False), ("padre", "abuelo", "bisabuelo", False),
    ("hermano", "padre", "tio", False), ("esposo", "tio", "tio", False),
    ("hijo", "tio", "primo", False),
    ("padre", "esposo", "suegro", False),
    ("hermano", "esposo", "cuñado", False), ("esposo", "hermano", "cuñado", False),
    ("hermano", "hermano", "hermano", False), ("hijo", "padre", "hermano", False), ("padre", "hermano", "padre", False),
    ("esposo", "padre", "padre", True),
    ("novio", "hermano", "cuñado", True),
]
# verbos que dicen una relación: (verbo, preposición) -> arista simétrica
VERBO = {("salir", "con"): "novio", ("vivir", "con"): "conviviente", ("convivir", "con"): "conviviente", ("compartir", "con"): "conviviente", ("trabajar", "con"): "compañero", ("estar casado", "con"): "esposo"}
CONVIVE = {"compañero de piso"}
DISP = {"conviviente": "quien vive contigo", "bisnieto": "bisnieto", "hijastro": "hijastro", "mascota": "mascota"}


def _apagado():
    return bool(os.environ.get("LCM_SIN_GRAFO"))


def _g(nuc, e):
    """El género que se SABE de un nodo (el del usuario no se supone: «mi marido» no dice si quien habla es hombre o mujer)."""
    if e == "U":
        return nuc.E.get("U", {}).get("gen") or ""
    return nuc.gen(e)


def base(nuc):
    """Las aristas DICHAS: {(r, x, y): [frase]} con «x es r de y»."""
    A = {}
    for q in nuc.R:
        x, y = nuc.can(q["x"]), nuc.can(q["y"])
        if x != y:
            A.setdefault((q["r"], x, y), [nuc._frase_rel(q["r"], x, y)])
            if sa(q["r"]) in {sa(c) for c in CONVIVE} or re.match(r"^compa[nñ]er[oa] de (?:piso|casa|habitaci[oó]n)$", q["r"].lower()):
                A.setdefault(("conviviente", x, y), [nuc._frase_rel(q["r"], x, y)])
    for f in nuc.F:
        if not f.get("vig", True) or f.get("neg") or not f.get("s"):
            continue
        for c in (f.get("comps") or []):
            r = VERBO.get((f.get("v"), c[0])) if len(c) > 1 else None
            if r and f.get("v") == "compartir" and not re.search(r"\b(?:piso|casa|habitaci[oó]n|apartamento)\b", (f.get("src") or "").lower()):
                r = None                                 # «comparto piso con…» sí; «comparto mesa con…» no dice que vivan juntos
            if r and c[1] and nuc.es_persona(nuc.can(c[1])) is not False:
                x, y = nuc.can(c[1]), nuc.can(f["s"])
                if x != y and (x == "U" or y == "U" or (nuc._persona_por_rol(x) and nuc._persona_por_rol(y))):
                    A.setdefault((r, x, y), [nuc.frase(f)])
    return A


def cierre(nuc):
    """Todas las aristas, dichas y deducidas: {(r, x, y): (justificación, supuesta)}."""
    cache = getattr(nuc, "_grafo227", None)
    clave = (len(nuc.R), len(nuc.F), nuc.turno, len(getattr(nuc, "eq", {}) or {}))
    if cache and cache[0] == clave:
        return cache[1]
    G = {k: (j, False) for k, j in base(nuc).items()}

    def pon(r, x, y, j, sup):
        if x == y or (r, x, y) in G:
            return False
        if r == "padre" and sup:
            gx = _g(nuc, x)                              # la pareja se supone progenitor solo si no hay ya uno (dicho) de su mismo género
            dichos = [a for (r2, a, b), (_, s2) in G.items() if r2 == "padre" and b == y and not s2]
            if len(dichos) >= 2 or any(gx and _g(nuc, a) == gx for a in dichos):
                return False
        G[(r, x, y)] = (j, sup)
        return True
    for _ in range(5):
        nuevo = False
        for (r, x, y), (j, s) in list(G.items()):
            if r in SIM:
                nuevo |= pon(r, y, x, j, s)
            if r in INV:
                nuevo |= pon(INV[r], y, x, j, s)
        por_y = {}
        for (r, x, y), v in G.items():
            por_y.setdefault((r, x), []).append((y, v))
        for (r1, x, y), (j1, s1) in list(G.items()):
            for a, b, r, sup in COMP:
                if a != r1:
                    continue
                for z, (j2, s2) in por_y.get((b, y), []):
                    if z != x:
                        nuevo |= pon(r, x, z, j1 + [t for t in j2 if t not in j1], s1 or s2 or sup)
        if not nuevo:
            break
    nuc._grafo227 = (clave, G)
    return G


def _nombre_rel(nuc, r, x):
    g = nuc.gen(x)
    if r in DISP:
        return DISP[r] + ("a" if g == "f" and r in ("bisnieto", "hijastro") else "")
    return nuc._acento(nuc._rel_nombre(r, g))


def _dice(nuc, r, x, y):
    if r == "conviviente":
        return (f"vives con {nuc.disp(y)}" if x == "U" else f"{nuc.disp(x, sujeto=True)} vive contigo" if y == "U" else f"{nuc.disp(x, sujeto=True)} vive con {nuc.disp(y)}")
    try:
        return nuc._frase_rel(r, x, y)
    except Exception:                                    # noqa
        return f"{nuc.disp(x)} es {_nombre_rel(nuc, r, x)} de {nuc.disp(y)}"


def _ent(nuc, txt):
    """El nodo del que habla un trozo de texto («mi jefa», «Clara», «yo», «mí»), o None."""
    t = txt.strip(" ¿?.,")
    n = sa(t.lower())
    if n in ("yo", "mi", "mí", "nosotros"):
        return "U"
    if n in ("tu", "ti", "tú"):
        return "L"
    k = "N:" + n
    if re.fullmatch(r"[a-zñ]+", n) and (k in nuc.E or k in getattr(nuc, "eq", {})):
        return nuc.can(k)
    m = re.match(r"^(?:mi|mis)\s+(.+)$", n)
    if m:
        r = _canon(m.group(1))
        xs = [x for (r2, x, y) in cierre(nuc) if r2 == r and y == "U"]
        if len(set(xs)) == 1:
            return xs[0]
    try:
        e = nuc._sn_ent(t)
        return nuc.can(e) if e else None
    except Exception:                                    # noqa
        return None


def _canon(palabra):
    w = sa(palabra.strip().lower())
    for cand in (w, w[:-1] if w.endswith("s") else w, w[:-2] if w.endswith("es") else w):
        if cand in {sa(k) for k in _N.REL_CANON}:
            return next(v[0] for k, v in _N.REL_CANON.items() if sa(k) == cand)
        if cand in {sa(c) for c in _N.REL_DISP_BASE} | {"bisnieto", "empleado", "ahijado", "jugador", "conocido", "colega", "pareja", "sobrino", "nieto", "tio", "primo", "yerno", "cuñado", "cunado"}:
            return {"cunado": "cuñado"}.get(cand, next((c for c in _N.REL_DISP_BASE if sa(c) == cand), cand))
    return None


def _ok(txt):
    return {"respuesta": txt, "estado": "ok", "consultar": False, "tipo": "resp"}


def _porque(j, sup):
    j = [x for x in j if x]
    if not j:
        return ""
    return (" Lo supongo porque " if sup else " Lo deduzco porque ") + _N.Nucleo._lista(j) + "."


def _cap(t):
    return t[:1].upper() + t[1:]


def quien(nuc, q):
    """«¿quién es el padre de Clara?», «¿quiénes son mis sobrinos?», «¿quién es mi cuñado?»"""
    m = re.match(r"^¿?\s*(?:y\s+)?qui[eé]n(?:es)?\s+(?:es|son|era|eran)\s+(?:(el|la|los|las)\s+(.+?)\s+de\s+(.+?)|(mi|mis)\s+(.+?))\s*\?$", q.strip(), re.I)
    if not m:
        return None
    art = (m.group(1) or "").lower()
    r = _canon(m.group(2) or m.group(5))
    y = _ent(nuc, m.group(3)) if m.group(3) else "U"
    if not r or not y:
        return None
    G = cierre(nuc)
    gq = "f" if art in ("la", "las") or sa((m.group(2) or m.group(5)).lower()).rstrip("s").endswith("a") else "m" if art else ""
    xs = [(x, G[(r, x, y)]) for (r2, x, y2) in G if r2 == r and y2 == y]
    if gq and r not in ("hijo", "nieto", "sobrino", "primo", "hermano") or gq == "f":
        con = [c for c in xs if _g(nuc, c[0]) == gq]
        sin = [c for c in xs if not _g(nuc, c[0])]
        xs = con or sin
    if not xs:
        return None
    xs.sort(key=lambda c: c[1][1])
    if not xs[0][1][1]:
        xs = [c for c in xs if not c[1][1]] or xs
    sup = any(c[1][1] for c in xs)
    j = []
    for c in xs:
        j += [t for t in c[1][0] if t not in j]
    dichas = all(len(c[1][0]) == 1 and not c[1][1] for c in xs)
    cuerpo = " y ".join(_cap(_dice(nuc, r, c[0], y)) if k == 0 else _dice(nuc, r, c[0], y) for k, c in enumerate(xs))
    return _ok(("Que yo sepa, " + (cuerpo[:1].lower() + cuerpo[1:] if cuerpo.startswith(("Eres ", "El ", "La ", "Tu ")) else cuerpo) if sup else cuerpo) + "." + ("" if dichas else _porque(j, sup))), [c[0] for c in xs]


def camino(nuc, x, y, maximo=3):
    """El camino más corto de aristas DICHAS entre dos nodos: [(r, a, b)] o None."""
    B = base(nuc)
    ady = {}
    for (r, a, b) in B:
        ady.setdefault(a, []).append((r, a, b, b))
        ady.setdefault(b, []).append((INV.get(r, r) if r in INV or r in SIM else r, b, a, a) if (r in INV or r in SIM) else (r, a, b, a))
    cola, visto = [(x, [])], {x}
    while cola:
        n, p = cola.pop(0)
        if n == y:
            return p
        if len(p) >= maximo:
            continue
        for r, a, b, sig in ady.get(n, []):
            if sig not in visto:
                visto.add(sig)
                cola.append((sig, p + [(r, a, b)]))
    return None


def que_es(nuc, q):
    """«¿qué es Jorge de Clara?», «¿qué soy yo de Vera?», «¿qué es Marta de mí?», «¿qué relación tienen Sara y Álex?»"""
    t = q.strip()
    m = re.match(r"^¿?\s*(?:y\s+)?qu[eé]\s+(?:es|son|era)\s+(.+?)\s+de\s+(.+?)\s*\?$", t, re.I)
    m2 = re.match(r"^¿?\s*(?:y\s+)?qu[eé]\s+soy\s+(?:yo\s+)?de\s+(.+?)\s*\?$", t, re.I)
    m3 = re.match(r"^¿?\s*qu[eé]\s+(?:relaci[oó]n|parentesco)\s+(?:tienen?|hay entre|tengo)\s+(.+?)\s+(?:y|con)\s+(.+?)\s*\?$", t, re.I)
    if m2:
        x, y = "U", _ent(nuc, m2.group(1))
    elif m or m3:
        mm = m or m3
        x, y = _ent(nuc, mm.group(1)), _ent(nuc, mm.group(2))
    else:
        return None
    if not x or not y or x == y:
        return None
    G = cierre(nuc)
    rs = [(r, G[(r, x, y)]) for (r, a, b) in G if a == x and b == y]
    if rs:
        firmes = [c for c in rs if not c[1][1]] or rs
        orden = sorted(firmes, key=lambda c: (len(c[1][0]), c[0] == "conviviente"))
        if len(orden) > 1 and any(c[0] == "cuñado" for c in orden) and any(c[0] in ("esposo", "hermano") for c in orden):
            orden = [c for c in orden if c[0] != "cuñado"]
        partes = [_dice(nuc, c[0], x, y) for c in orden]
        txt = _cap(partes[0])
        for p in partes[1:]:
            p2 = re.sub(r"^.*?\b(?:es|eres)\s+", "", p)     # «Marta es tu hermana y tu compañera de piso»
            txt += " y " + (p2 if p2 != p else p)
        j = []
        for c in orden:
            j += [t_ for t_ in c[1][0] if t_ not in j]
        dichas = all(len(c[1][0]) == 1 for c in orden)
        return _ok(txt + "." + ("" if dichas else _porque(j, any(c[1][1] for c in orden))))
    p = camino(nuc, x, y)
    if p and len(p) >= 2:
        return _ok("No tiene nombre, que yo sepa, pero hay relación: " + _N.Nucleo._lista([_dice(nuc, r, a, b) for r, a, b in p]) + ".")
    return None


def cuantos(nuc, q):
    n = sa(q.lower()).strip(" ¿?")
    if re.match(r"^cuant[oa]s (?:somos|vivimos|personas (?:somos|vivimos|hay)) en (?:mi )?casa$", n) or re.match(r"^cuant[oa]s vivimos (?:juntos|aqui)$", n):
        G = cierre(nuc)
        xs = sorted({x for (r, x, y) in G if r == "conviviente" and y == "U"})
        if xs:
            return _ok(f"{_cap(_num(len(xs) + 1))}: {_N.Nucleo._lista(['tú'] + [nuc.disp(x) for x in xs])}.")
    return None


def _num(k):
    from . import morfo as M
    try:
        return M.num_pal(k)
    except Exception:                                    # noqa
        return str(k)


# ---------------------------------------------------------------- lo que está dentro de algo (transitiva)
def dentro(nuc):
    """{cosa: [(sitio, hecho)]} con lo dicho «X está en Y»."""
    D = {}
    for f in nuc.F:
        if f.get("vig", True) and not f.get("neg") and f.get("v") == "estar" and f.get("t") == "pres":
            for c in (f.get("comps") or []):
                if len(c) > 1 and c[0] in ("en", "dentro de") and c[1]:
                    D.setdefault(nuc.can(f["s"]), []).append((nuc.can(c[1]), f))
    return D


def cadena(nuc, x):
    """Los sitios que contienen a x, de dentro afuera: [(sitio, hecho)]."""
    D, out, visto = dentro(nuc), [], {x}
    while x in D and len(out) < 8:
        y, f = D[x][-1]
        if y in visto:
            break
        out.append((y, f)); visto.add(y); x = y
    return out


def lugar(nuc, q):
    """«¿las llaves están en la planta baja?» (por la cadena) y «¿en qué habitación están las llaves?»"""
    t = q.strip()
    m = re.match(r"^¿?\s*(?:y\s+)?en\s+qu[eé]\s+([a-záéíóúñ]+)\s+(?:est[aá]n?|se encuentran?)\s+(.+?)\s*\?$", t, re.I)
    if m:
        x = _ent(nuc, m.group(2))
        cad = cadena(nuc, x) if x else []
        if not cad:
            return None
        tipo = sa(m.group(1).lower())
        from . import conceptos as K
        gen = {"habitacion", "cuarto", "sitio", "lugar", "parte", "zona", "sala"}
        for y, f in cad:
            cl = sa((nuc.E.get(y, {}).get("clase") or nuc.disp(y).split()[-1]).lower())
            try:
                anc = {sa(a) for a in K.ancestros(K._kb_clase(cl) or cl)} | {cl}
            except Exception:                            # noqa
                anc = {cl}
            if tipo in anc or (tipo in gen and anc & gen) or tipo in sa(nuc.disp(y).lower()).split():
                return _ok(_cap(_N.Nucleo._lista([nuc.frase(g) for _, g in cad[:cad.index((y, f)) + 1]])) + ".")
        return None
    m = re.match(r"^¿?\s*(?:y\s+)?(.+?)\s+est[aá]n?\s+en\s+(.+?)\s*\?$", t, re.I)
    if m and not re.match(r"^(?:d[oó]nde|qu[eé]|qui[eé]n|c[oó]mo|cu[aá]ndo)\b", m.group(1), re.I):
        x, z = _ent(nuc, m.group(1)), _ent(nuc, m.group(2))
        cad = cadena(nuc, x) if x and z else []
        sitios = [y for y, _ in cad]
        if z in sitios and sitios.index(z) >= 2:         # dos saltos ya los da el núcleo; aquí, la cadena larga
            return _ok("Sí: " + _N.Nucleo._lista([nuc.frase(g) for _, g in cad[:sitios.index(z) + 1]]) + ".")
    return None


def responde(nuc, q, r_nucleo=None):
    """La respuesta del grafo, o None. Si el núcleo ya contestó, solo se le enmienda cuando el grafo sabe algo mejor."""
    if _apagado() or "?" not in q:
        return None
    abst = not (isinstance(r_nucleo, dict) and r_nucleo.get("estado") == "ok")
    txt = (r_nucleo or {}).get("respuesta") or "" if isinstance(r_nucleo, dict) else ""
    try:
        qq = quien(nuc, q)
        if qq:
            r, xs = qq
            if abst or (re.match(r"^Eres\b", txt) and "U" not in xs):
                return r
            return None
        r = que_es(nuc, q)
        if r:
            dice = {sa(w) for w in re.findall(r"\b(?:tu|el|la)\s+(\w+)", r["respuesta"].split(".")[0])}
            if abst or not dice <= {sa(w) for w in re.findall(r"\w+", txt)}:
                return r                                 # el núcleo calló, o no nombró alguna de las relaciones que hay («hermana» y «compañera»)
            return None
        n_ = sa(q.lower()).strip(" ¿?")
        if re.match(r"^(?:y )?con quien(?:es)? vivo$", n_) and (abst or True):
            xs = sorted({x for (r2, x, y) in cierre(nuc) if r2 == "conviviente" and y == "U"})
            if xs and abst:
                return _ok(f"Vives con {_N.Nucleo._lista([nuc.disp(x) for x in xs])}.")
        if abst:
            return cuantos(nuc, q) or lugar(nuc, q)
        if re.match(r"^No\b", txt) or "suele" in txt or re.match(r"^¿?\s*(?:y\s+)?en\s+qu[eé]\s+\w+\s+est", q.strip(), re.I):
            return lugar(nuc, q)
    except Exception:                                    # noqa
        return None
    return None


# ---------------------------------------------------------------- tocayos: dos nodos con el mismo nombre
_ROL = r"([a-záéíóúñ]+(?:\s+de\s+(?:piso|trabajo|clase))?)"


def _roles(nuc, k):
    return [q["r"] for q in nuc.R if nuc.can(q["x"]) == nuc.can(k) and nuc.can(q["y"]) == "U"]


def _otro(nuc, texto, rol_txt, nombre, resto=""):
    """Abre un NODO NUEVO para «mi <rol>» que se llama igual que alguien ya conocido. Desde la 2.28 es un nodo con su nombre propio
    (N:pedro#2): el nombre deja de ser la identidad."""
    k0 = "N:" + sa(nombre.lower())
    primero = nuc.can(k0)
    r0 = _roles(nuc, k0)
    T = nuc.usuario.setdefault("tocayos", {})
    ops = T.setdefault(sa(nombre.lower()), [])
    if not ops:
        rol0 = _nombre_rel(nuc, r0[0], primero)
        if primero == k0:                                # el primero también deja de ser «el nombre»: pasa a su propio nodo, y N:pedro queda solo como nombre
            nid1 = k0 + "#1"
            nuc.E[nid1] = dict(nuc.E[k0])
            nuc.unir(k0, nid1)
            primero = nid1
        ops.append({"rol": r0[0], "dice": "tu " + rol0, "id": primero})
        nuc.E[primero]["tocayo"] = rol0
    fem = sa(rol_txt.split()[0]).endswith("a")
    antes = set(nuc.E)
    nuc._tocando = True
    try:
        nuc.procesar(f"Tengo {'una' if fem else 'un'} {rol_txt}.")
    finally:
        nuc._tocando = False
    rc = _canon(rol_txt.split()[0]) or sa(rol_txt.split()[0])
    inst = next((e for e in nuc.E if e not in antes and e.startswith("I:")), None) \
        or next((e for e, d in nuc.E.items() if e.startswith("I:") and d.get("dueno") == "U" and sa(d.get("clase") or "") in (sa(rc), sa(rol_txt.split()[0])) and e not in nuc.eq), None)
    nid = f"N:{sa(nombre.lower())}#{len(ops) + 1}"
    nuc._ent(nid, nombre=nombre, clase=(nuc.E.get(inst, {}).get("clase") or rc), dueno="U", gen="f" if fem else (nuc.E.get(inst, {}).get("gen") or "m"))
    nuc.E[nid]["tocayo"] = rol_txt
    if inst:
        nuc.unir(inst, nid)
    else:
        nuc._rel(rc, nid, "U", texto, "f" if fem else "m")
    ops.append({"rol": rc, "dice": "tu " + rol_txt, "id": nid})
    nuc._grafo227 = None
    cola = ""
    if resto.strip(" .,"):
        nuc._tocando = True
        try:
            r2 = nuc.procesar(_cap("mi " + rol_txt + " " + re.sub(r"^\s*(?:y|,)\s*", "", resto).strip()))
            cola = " " + ((r2 or {}).get("respuesta") or "")
        finally:
            nuc._tocando = False
    return _ok(f"Entendido: tu {rol_txt} también se llama {nombre}. Es otra persona, no {ops[0]['dice']}." + cola)


def _ficha(nuc, e):
    """Las palabras de lo que se sabe de un nodo (su ficha), para ver si una frase habla de él."""
    from . import contexto as X
    txt = []
    d = nuc.E.get(e, {})
    marcas = [sa(x.lower())[:5] for x in (d.get("tocayo"), d.get("clase")) if x]
    for f in nuc.F:
        if f.get("vig", True) and (nuc.can(f.get("s") or "") == e or nuc.can(f.get("obj") or "") == e):
            src = f.get("src") or ""
            if marcas and not any(m_ in sa(src.lower()) for m_ in marcas) and not (
                    f.get("turno") is not None and f.get("turno") == d.get("t_nuevo") and not os.environ.get("LCM_SIN_CLASE")):   # 2.31: …o en la misma frase en que se le presentó («Mi primo se llama Raúl Y ES MECÁNICO»)
                continue                                 # solo lo que se dijo NOMBRÁNDOLO: una frase sin sujeto que el núcleo le colgó no es su ficha
            txt.append(src)
    txt.append(nuc.E.get(e, {}).get("tocayo") or "")
    return set(X.lemas(" ".join(txt)))


def _papel_sin_tema(rol):
    """2.31 · «vecino», «hermano», «amigo» dicen la relación, no de qué se habla: no cuentan como tema de la ficha (si no, «¿dónde VIVE Pedro?»
    apuntaba al vecino porque los vecinos «viven al lado»). Un oficio («profesor», «médico») sí es tema."""
    if not rol or os.environ.get("LCM_SIN_CLASE"):
        return set()
    from . import contexto as X
    try:
        from . import conceptos as K
        from . import morfo as M_
        r = sa(M_.singular(rol.lower()))
        if "profesional" in [sa(a_) for a_ in K.ancestros(r)]:
            return set()
    except Exception:                                    # noqa
        pass
    return set(X.lemas(rol)) | {sa(rol.lower())}


def probabilidades(nuc, t, forma, ops):
    """La probabilidad de cada tocayo: de quién se venía hablando (caché) y con la ficha de quién casa la frase."""
    from . import contexto as X
    fichas = [_ficha(nuc, o["id"]) - {sa(forma.lower()), "tener"} - _papel_sin_tema(o.get("rol")) for o in ops]
    todas = set().union(*fichas) if fichas else set()
    # 2.30: también de lo que se venía hablando («se ha roto una tubería»), pero no las palabras con que se habló de ellos mismos: eso ya lo cuenta la recencia
    for o in ops:
        todas |= set(X.lemas(o["dice"])) | {sa(o["rol"])}
    raices = {x[:5] for x in todas}
    ids = {o["id"] for o in ops}
    turnos_suyos = {x[0] for x in X._cache(nuc) if x[1] == "e" and nuc.can(x[2]) in ids}   # los turnos en que se habló de alguno de ellos no cuentan como «tema»
    tn = nuc.turno
    frase = {}
    for x in X._cache(nuc):
        if x[1] == "w" and x[0] not in turnos_suyos and tn - x[0] <= X.VENTANA and x[2] not in todas and x[2][:5] not in raices:
            frase[x[2]] = max(frase.get(x[2], 0.0), min(1.0, 0.84 * X.OLVIDO ** max(0, tn - x[0])))
    frase.update({l: 1.0 for l in X.lemas(re.sub(r"\b" + forma + r"\b", " ", t))})
    for vago in ("dedicar", "llamar", sa(forma.lower())):
        frase.pop(vago, None)
    rec = [X.peso_entidad(nuc, o["id"]) for o in ops]
    tem = [1.5 * X.casa(frase, f_) for f_ in fichas]
    nuc._pt_tema230 = tem
    puntos = [r_ + t_ for r_, t_ in zip(rec, tem)]
    return X.reparte(puntos), puntos


def _probable(nuc, t, forma, ops):
    from . import contexto as X
    if X.apagado():
        return None
    ps, puntos = probabilidades(nuc, t, forma, ops)
    k = max(range(len(ops)), key=lambda i: ps[i])
    umbral = X.SEGURO if "?" in t else X.SEGURO_DICHO
    nuc._ult_prob229 = (forma, [round(p, 2) for p in ps])
    tem = getattr(nuc, "_pt_tema230", None) or [0.0] * len(ops)
    claro = puntos[k] >= 0.5 or tem[k] >= 0.25           # o se habló de él hace nada, o la frase casa con su ficha: un recuerdo lejano no basta
    return ops[k] if ps[k] >= umbral and claro else None


def tocayos(nuc, texto):
    """Antes de entender la frase: ¿habla de un nombre que llevan dos personas? Devuelve None, {"respuesta": …} o {"texto": frase rehecha}.
    Si no se sabe a cuál se refiere, SE PREGUNTA."""
    if _apagado() or os.environ.get("LCM_SIN_TOCAYOS") or not texto or getattr(nuc, "_tocando", False) or "\n" in texto or len(texto) > 200:
        return None
    T = nuc.usuario.setdefault("tocayos", {})
    t = texto.strip()
    pend = getattr(nuc, "_toc_pend", None)
    nuc._toc_pend = None
    if pend and nuc.turno - pend["turno"] <= 1 and len(t.split()) <= (3 if pend["tipo"] == "cual" else 6):
        n = sa(t.lower()).strip(" .!¡¿?,")
        if pend["tipo"] == "cual":
            for op in T.get(pend["nombre"], []):
                if re.search(r"\b" + re.escape(sa(op["dice"].split(" ", 1)[1])) + r"\b", n):
                    return {"texto": pend["texto"], "foco": {"N:" + pend["nombre"]: op["id"]}}
        elif pend["tipo"] == "mismo":
            if re.match(r"^(?:si|el mismo|la misma|es el mismo|es la misma|claro|eso es)\b", n):
                nuc._tocando = True
                try:
                    return nuc.procesar(pend["texto"])
                finally:
                    nuc._tocando = False
            if re.match(r"^(?:no|otro|otra|es otro|es otra|otra persona|distint[oa])\b", n):
                return _otro(nuc, pend["texto"], pend["rol"], pend["forma"], pend["resto"])
    m = re.match(r"^(?:[Yy]\s+)?(?:[Mm]i|[Ee]l|[Ll]a)\s+" + _ROL + r"\s+(tambi[eé]n\s+)?se\s+llama\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b(.*)$", t)
    if m and "?" not in t and len(m.group(1).split()[0]) > 2 and sa(m.group(1).split()[0]) not in ("nombre", "apellido", "mote", "perro", "gato", "perra", "gata", "calle", "pueblo", "ciudad"):
        rol_txt, tam, nombre, resto = m.group(1), m.group(2), m.group(3), m.group(4)
        k = "N:" + sa(nombre.lower())
        if k in nuc.E or k in getattr(nuc, "eq", {}):
            r0 = _roles(nuc, k)
            rc = _canon(rol_txt.split()[0]) or sa(rol_txt.split()[0])   # cualquier papel vale («mi dentista»), no solo los de familia
            if r0 and rc not in r0 and not any(o["rol"] == rc for o in T.get(sa(nombre.lower()), [])):
                if tam:
                    return _otro(nuc, t, rol_txt, nombre, resto)
                nuc._toc_pend = {"tipo": "mismo", "turno": nuc.turno, "texto": t, "rol": rol_txt, "forma": nombre, "resto": resto, "nombre": sa(nombre.lower())}
                return {"respuesta": f"Ya conozco a un {nombre}: tu {_nombre_rel(nuc, r0[0], nuc.can(k))}. ¿Tu {rol_txt} es el mismo {nombre} o es otra persona?",
                        "estado": "ok", "consultar": False, "tipo": "pregunta"}
        return None
    for nom, ops in T.items():
        if len(ops) < 2:
            continue
        mm = re.search(r"\b(" + nom[:1].upper() + r"\w*)\b", t)
        if not mm or sa(mm.group(1).lower()) != nom:
            continue
        forma = mm.group(1)
        if re.match(r"^¿?\s*cu[aá]nt[oa]s\s+" + forma, t, re.I):
            continue
        for op in ops:                                   # «mi vecino Pedro», «el vecino Pedro», «Pedro, el vecino»: dicho cuál
            rol = re.escape(op["dice"].split(" ", 1)[1])
            pat = r"(?:\b(?:mi|el|la|tu)\s+" + rol + r"\s+" + forma + r"\b|\b" + forma + r",?\s+(?:mi|el|la)\s+" + rol + r"\b)"
            if re.search(pat, t, re.I):
                return {"texto": re.sub(pat, forma, t, count=1, flags=re.I), "foco": {"N:" + nom: op["id"]}}
        el = _probable(nuc, t, forma, ops)               # 2.29: ¿de cuál se venía hablando? Si está claro, no se pregunta
        if el is not None and not os.environ.get("LCM_SIN_CLASE"):
            try:                                         # 2.31: a este lo ha elegido el modelo, no lo ha nombrado el usuario: en la caché cuenta la mitad
                nuc._ded231 = (getattr(nuc, "_ded231", None) or set()) | {nuc.can(el["id"])}
            except Exception:                            # noqa
                pass
        if el is not None:
            return {"texto": t, "foco": {"N:" + nom: el["id"]}}
        nuc._toc_pend = {"tipo": "cual", "turno": nuc.turno, "texto": t, "forma": forma, "nombre": nom}
        return {"respuesta": f"¿Qué {forma}: {' o '.join(o['dice'] for o in ops)}?", "estado": "ok", "consultar": False, "tipo": "pregunta"}
    m = re.match(r"^¿?\s*cu[aá]nt[oa]s\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+?)s?\s+(?:conozco|hay|tengo)\s*\?$", t)
    if m and len(T.get(sa(m.group(1).lower()), [])) >= 2:
        ops = T[sa(m.group(1).lower())]
        return _ok(f"{_cap(_num(len(ops)))}: {_N.Nucleo._lista([o['dice'] for o in ops])}.")
    return None


def pule(txt):
    """«Tu vecino Pedro es tu vecino» -> «Pedro es tu vecino»: con tocayos el nodo se nombra con su papel, y a veces sobra."""
    return re.sub(r"\b[Tt]u ([a-záéíóúñ]+(?: de [a-záéíóúñ]+)?) ([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+) es tu \1\b", r"\2 es tu \1", txt)
