"""LCM 2.15 · RELACIONES ENTRE CONCEPTOS.

Además de «X es un Y», la base de fábrica declara relaciones (secciones [funcion], [material], [lugar], [usuario] de conceptos_base.txt).
Aquí no hay una regla por pregunta ni por palabra: hay UN mecanismo para todas las relaciones:
  · herencia: lo que vale para una clase vale para lo que tiene debajo, y manda la clase más cercana (una sierra corta madera aunque sea «herramienta»)
  · sentido directo  (concepto -> valores):   «¿para qué sirve una escoba?», «¿de qué está hecha una botella?», «¿dónde suele estar una cama?»
  · sentido inverso  (valor -> conceptos):    «¿qué sirve para cortar?», «¿qué hay en una cocina?», «¿qué usa un carpintero?»
  · sí/no:                                    «¿una silla sirve para cortar?»
  · con lo que la persona ha contado:         «tengo unas tijeras» -> «¿tengo algo para cortar?»
Cada relación se describe con datos (RELS): cómo se pregunta y cómo se dice. Añadir otra relación es añadir su sección y su descripción.
"""
from __future__ import annotations

import re

from . import conceptos as K
from . import morfo as M
from .morfo import sa

_ART = r"(?:un|una|unos|unas|el|la|los|las)"
_VAC = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "con", "en", "su", "sus", "lo", "se", "me", "te"}


def _clase(t):
    """Clase de fábrica nombrada por un texto sin posesivos («una nevera», «las tijeras»), o None."""
    t = re.sub(rf"^{_ART}\s+", "", t.strip())
    if not t or re.match(r"^(?:mi|mis|tu|tus|su|sus|nuestr[oa]s?|este|esta|ese|esa|aquel)\b", t):
        return None
    c = K._kb_clase(t)
    if c:
        return c
    k = K.kb()
    for cand in (sa(t), sa(M.singular(t))):
        if any(cand in k["rel"][r] for r in k["rel"]) or any(cand in _ens(r) for r in k["rel"]):
            return cand
    return None


_APR = [("funcion", re.compile(rf"^({_ART} [a-zñ]+) (?:tambien )?(?:sirven?|se usan?|se utilizan?|valen?) (?:tambien )?para (.+)$"), "sirve para"),
        ("material", re.compile(rf"^({_ART} [a-zñ]+) (?:esta hech[oa]|estan hech[oa]s|se hacen?|se fabrican?) (?:de|con) (.+)$"), "suele ser de"),
        ("lugar", re.compile(rf"^({_ART} [a-zñ]+) (?:suelen? estar|se guardan?|se suelen? guardar|suelen? encontrarse|se encuentran? normalmente) en (?:el |la |los |las |un |una )?(.+)$"), "suele estar en")]


def aprender(nuc, p, n):
    """«Una pinfa sirve para doblar alambre»: la persona enseña una relación de un concepto. Se guarda como enseñada y se usa como las de fábrica."""
    n = n.strip(" .!")
    for rel, pat, dice in _APR:
        m = pat.match(n)
        if not m:
            continue
        t = re.sub(rf"^{_ART}\s+", "", m.group(1))
        if re.match(r"^(?:mi|mis|tu|tus|su|sus)\b", m.group(1)) or len(t.split()) != 1:
            return None
        c = K._kb_clase(t) or sa(M.singular(t))
        vals = [x.strip() for x in re.split(r"\s*,\s*|\s+y\s+(?=[a-zñ]+(?:ar|er|ir)\b)|\s+o\s+", m.group(2)) if x.strip()]
        if not vals:
            return None
        d = nuc.usuario.setdefault("rel", {}).setdefault(rel, {}).setdefault(c, [])
        for v in vals:
            if v not in d:
                d.append(v)
        ENSENADO.clear(); ENSENADO.update(nuc.usuario.get("rel") or {})
        nuc.ult_just = {"dicho": [p.strip()]}
        art = "una" if (m.group(1).split()[0] in ("una", "la", "las") or (K.genero(c) == "f" if c in K.kb()["forma"] else t.endswith("a"))) else "un"
        return f"Entendido: {_un(c)} {dice} {_lista(vals)}."
    return None


def _verbo(w):
    """«sentarme», «sentarse», «lavarte» -> «sentar», «lavar» (para comparar usos)."""
    w = sa(w)
    m = re.match(r"^(.+(?:ar|er|ir))(?:se|me|te|nos|os|lo|la|los|las|le)$", w)
    return m.group(1) if m else w


def _uso(texto):
    """«cortar el pan» -> («cortar», {«pan»})."""
    ws = [w for w in sa(texto).split() if w]
    if not ws:
        return "", set()
    return _verbo(ws[0]), {sa(M.singular(w)) for w in ws[1:] if w not in _VAC}


def cadena(c):
    return [c] + K.ancestros(c)


ENSENADO = {}        # 2.16: relaciones que ha enseñado la persona en esta conversación (las fija el diálogo en cada turno)


def _ens(rel):
    return (ENSENADO or {}).get(rel, {})


def valores(c, rel, todos=False):
    """Valores de la relación para c: los de la clase más cercana que los tenga -> (clase_que_lo_dice, [valores]).
    todos=True: los de toda la cadena, [(clase, valor)]. Lo que ha enseñado la persona va delante de lo de fábrica."""
    k = K.kb()
    out = []
    for cl in cadena(c):
        vs = list(_ens(rel).get(cl, [])) + [v for v in k["rel"][rel].get(cl, []) if v not in _ens(rel).get(cl, [])]
        if rel == "funcion" and not vs:                    # «servir para…» dicho como propiedad también es función
            vs = [r[5:] for (x, neg, v, r) in k["props"] if x == cl and v == "servir" and r.startswith("para ") and not neg]
        if vs:
            if not todos:
                return cl, vs
            out += [(cl, v) for v in vs]
    return out if todos else (None, [])


def _casa(rel, valor, consulta):
    """0 no casa · 1 casa en general · 2 casa también el complemento («cortar madera» con «cortar madera»)."""
    if rel == "funcion":
        v1, o1 = _uso(valor)
        v2, o2 = _uso(consulta)
        if not v1 or v1 != v2:
            return 0
        if not o2:
            return 2 if not o1 else 1                      # «cortar» a secas: primero lo que corta en general
        if not o1:
            return 1
        return 2 if o1 & o2 else 0
    a, b = sa(M.singular(sa(valor))), sa(M.singular(sa(consulta)))
    if a == b:
        return 2
    cb = K._kb_clase(b)
    ca = K._kb_clase(a)
    if ca and cb and (ca == cb or cb in K.ancestros(ca)):   # «tela vaquera»/«algodón» casan con «tela» si la base lo sabe
        return 1
    return 0


def inversa(rel, consulta):
    """Conceptos cuyo valor PROPIO de la relación casa con la consulta, los más precisos primero."""
    k = K.kb()
    out = []
    fuentes = dict(k["rel"][rel])
    for c_, vs_ in _ens(rel).items():
        fuentes[c_] = list(vs_) + [v for v in fuentes.get(c_, []) if v not in vs_]
    if rel == "funcion":
        for (x, neg, v, r) in k["props"]:
            if v == "servir" and r.startswith("para ") and not neg:
                fuentes.setdefault(x, [])
                fuentes[x] = fuentes[x] + [r[5:]]
    for c, vs in fuentes.items():
        m = max((_casa(rel, v, consulta) * 10 - i for i, v in enumerate(vs)), default=0)
        if m > 0:
            out.append((m, c))
    out.sort(key=lambda x: (-x[0], x[1]))
    return [c for m, c in out]


def _lista(xs):
    xs = list(dict.fromkeys(xs))
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + (" e " if sa(xs[-1]).startswith(("i", "hi")) else " y ") + xs[-1]


def _fem(c):
    return c.endswith(("a", "as", "cion", "dad"))


def _los(c):
    return K.los(c) if c in K.kb()["forma"] else ("las " if _fem(c) else "los ") + (c if c.endswith("s") else M.plural(c))


def _un(c):
    return K.un(c) if c in K.kb()["forma"] else ("una " if _fem(c) else "un ") + c


# cómo se dice cada relación
def _dice(rel, c, cl, vs, plural=False):
    suj = K._cap(_un(c))
    if rel == "funcion":
        return f"{suj} sirve para {_lista(vs[:3])}."
    if rel == "material":
        return f"{suj} suele ser de {_lista(vs[:3]).replace(' y ', ' o ')}."
    if rel == "lugar":
        return f"{suj} suele estar en {_lista([_el_lugar(v) for v in vs[:3]]).replace(' y ', ' o ')}."
    pron = "las" if K.genero(c) == "f" else "los"
    return f"{K._cap(_los(c))} {pron} usan sobre todo {_lista([_los(sa(v)) for v in vs[:3]])}."


def _el_lugar(v):
    c = K._kb_clase(v)
    if c and sa(K.forma(c)) == sa(v) and K.forma(c) != v and not re.search(r"[áéíóú]", v):
        c = None                                         # «sabana» no es «sábana»: la base guarda las dos con la misma clave
    if c:
        return K.el(c)
    return ("la " if sa(v).endswith("a") else "el ") + v


def _por_herencia(c, cl):
    return "" if cl == c else f" Lo sé porque {_un(c)} es {_un(cl)}."


_P = {
    "funcion_dir": re.compile(rf"^(?:y )?(?:para que (?:sirven?|se usan?|se utilizan?|valen?|es|son)|que (?:se hace|se puede hacer|hago|puedo hacer) con) ({_ART} .+)$"),
    "funcion_sn": re.compile(rf"^(?:y )?({_ART} [a-zñ ]+?) (?:sirven?|se usan?|valen?) para (.+)$"),
    "funcion_inv": re.compile(r"^(?:y )?(?:que (?:cosas? |objetos? |herramientas? |utensilios? |aparatos? |muebles? )?(?:sirven?|se usan?|se utilizan?|valen?|necesito|hace falta|uso|puedo usar) para|con que (?:se|puedo|podemos|se puede)) (.+)$"),
    "funcion_charla": re.compile(r"^(?:y )?(.*?)\b(?:algo|alguna cosa|alguna herramienta|algun aparato) (?:para|con (?:lo )?que|que sirva para) (.+)$"),
    "material_dir": re.compile(rf"^(?:y )?de que (?:(?:material )?(?:esta|estan|suele estar|suelen estar) hech[oa]s?|material (?:es|son)|(?:se hacen?|se fabrican?)) ({_ART} .+)$"),
    "material_sn": re.compile(rf"^(?:y )?({_ART} [a-zñ ]+?) (?:es|son|esta hech[oa]|estan hech[oa]s|se hacen?) de ([a-zñ ]+)$"),
    "material_inv": re.compile(r"^(?:y )?que (?:cosas? |objetos? )?(?:son|esta hech[oa]|estan hech[oa]s|se hacen?|se hace) (?:de|con) ([a-zñ ]+)$"),
    "lugar_dir": re.compile(rf"^(?:y )?(?:donde (?:suelen? estar|suelen? haber|se guardan?|se ponen?|se colocan?|estan? normalmente|se suelen? guardar|se encuentran?|se compran?|hay)|en que (?:sitio|lugar|habitacion) (?:suelen? estar|se guardan?|estan?)) ({_ART} .+)$"),
    "lugar_inv": re.compile(r"^(?:y )?que (?:cosas? |objetos? |muebles? |aparatos? )?(?:hay|suele haber|se encuentra|se guarda|se puede encontrar|encuentras) en (?:un|una|los|las) ([a-zñ ]+)$|^(?:y )?que (?:cosas? )?suele haber en (?:el|la) ([a-zñ ]+)$"),
    "usuario_dir": re.compile(rf"^(?:y )?quien(?:es)? (?:usan?|utilizan?|suelen? usar|suelen? utilizar|trabajan? con|manejan?) ({_ART} .+)$"),
    "usuario_inv": re.compile(r"^(?:y )?que (?:cosas? |herramientas? |instrumentos? |utensilios? )?(?:usan?|utilizan?|necesitan?|suelen? usar) (?:un|una|los|las) ([a-zñ ]+)$"),
}


def responder(nuc, p, n):
    """Respuesta (texto) a una pregunta sobre relaciones entre conceptos, o None. n: pregunta normalizada, sin acentos ni signos."""
    n = n.strip(" ?¿.!")
    k = K.kb()
    ENSENADO.clear(); ENSENADO.update(nuc.usuario.get("rel") or {})
    fab = lambda pasos: setattr(nuc, "ult_just", {"pasos": pasos, "fabrica": True})   # noqa: E731

    # ---- función
    m = _P["funcion_charla"].match(n)
    if m:
        r = _charla(nuc, m.group(1), m.group(2))
        if r:
            return r
    m = _P["funcion_dir"].match(n)
    if m:
        c = _clase(m.group(1))
        if c:
            cl, vs = valores(c, "funcion")
            if vs:
                fab([f"{_los(cl)} sirven para {vs[0]}"])
                return _dice("funcion", c, cl, vs) + _por_herencia(c, cl)
        return None
    m = _P["funcion_sn"].match(n)
    if m:
        c = _clase(m.group(1))
        if c:
            todos = valores(c, "funcion", todos=True)
            for cl, v in todos:
                if _casa("funcion", v, m.group(2)):
                    fab([f"{_los(cl)} sirven para {v}"])
                    return f"Sí, {_los(c)} sirven para {v}." + ("" if cl == c else f" Lo sé porque {_los(c)} son {K.forma(cl, plural=True)}.")
            propio = k["rel"]["funcion"].get(c)
            if propio and inversa("funcion", m.group(2)):   # se sabe para qué sirve y eso otro lo hacen otras cosas
                fab([f"{_los(c)} sirven para {propio[0]}"])
                return f"No, {_los(c)} sirven para {_lista(propio[:2])}."
        return None
    m = _P["funcion_inv"].match(n)
    if m:
        uso = m.group(1)
        w0 = uso.split()[0]
        if not re.search(r"(?:ar|er|ir)(?:se|me|te|nos|lo|la|los|las)?$", w0):     # «¿con qué se corta el pan?»: la forma conjugada vale por su infinitivo
            uso = " ".join([K._lema(w0) or w0] + uso.split()[1:])
        m = re.match(r"^(.*)$", uso)
        cs = inversa("funcion", m.group(1))
        if cs:
            fab([f"{_los(c)} sirven para {valores(c, 'funcion')[1][0]}" for c in cs[:3]])
            v0 = sa(m.group(1))
            return f"Para {m.group(1)} sirven, por ejemplo, {_lista([_los(c) for c in cs[:5]])}." if len(cs) > 1 else f"Para {m.group(1)} sirve {_un(cs[0])}."
        return None

    # ---- material
    m = _P["material_dir"].match(n)
    if m:
        c = _clase(m.group(1))
        if c:
            cl, vs = valores(c, "material")
            if vs:
                fab([f"{_los(cl)} suelen ser de {vs[0]}"])
                return _dice("material", c, cl, vs) + _por_herencia(c, cl)
        return None
    m = _P["material_inv"].match(n)
    if m and (K._kb_clase(m.group(1)) and "material" in cadena(K._kb_clase(m.group(1))) or any(_casa("material", v, m.group(1)) == 2 for vs in k["rel"]["material"].values() for v in vs)):
        cs = inversa("material", m.group(1))
        if cs:
            fab([f"{_los(c)} suelen ser de {m.group(1)}" for c in cs[:3]])
            return f"Suelen ser de {m.group(1)}, por ejemplo, {_lista([_los(c) for c in cs[:6]])}."
        return None
    m = _P["material_sn"].match(n)
    if m and re.match(r"^(?:un|una|los|las) ", m.group(1)):
        c = _clase(m.group(1))
        mat = K._kb_clase(m.group(2))
        if c and mat and "material" in cadena(mat):
            cl, vs = valores(c, "material")
            if vs:
                fab([f"{_los(cl)} suelen ser de {vs[0]}"])
                if any(_casa("material", v, m.group(2)) for v in vs):
                    return f"Sí, {_los(c)} suelen ser de {m.group(2)}."
                return f"No es lo normal: {_los(c)} suelen ser de {_lista(vs[:3]).replace(' y ', ' o ')}."
        return None

    # ---- lugar habitual
    m = _P["lugar_dir"].match(n)
    if m:
        c = _clase(m.group(1))
        if c:
            cl, vs = valores(c, "lugar")
            if vs:
                fab([f"{_los(cl)} suelen estar en {_el_lugar(vs[0])}"])
                return _dice("lugar", c, cl, vs) + _por_herencia(c, cl)
        return None
    m = _P["lugar_inv"].match(n)
    if m:
        lug = K._kb_clase(m.group(1) or m.group(2)) or sa(M.singular(m.group(1) or m.group(2)))
        cosas = [k["parte_disp"].get((lug, x), x) for x in k["partes"].get(lug, [])]
        dentro = [K.forma(c, plural=True) if c in k["forma"] else c for c in inversa("lugar", lug)]
        todo = list(dict.fromkeys(cosas + [d for d in dentro if sa(M.singular(d)) not in {sa(M.singular(x)) for x in cosas}]))
        if todo:
            fab([f"en {_el_lugar(lug)} suele haber {todo[0]}"])
            return f"En {_un(lug)} suele haber {_lista(todo[:7])}."
        return None

    # ---- usuario
    m = _P["usuario_dir"].match(n)
    if m:
        c = _clase(m.group(1))
        if c and not any(f["v"] in ("usar", "utilizar") and f.get("obj_cls") and c in cadena(f["obj_cls"]) for f in nuc.F):   # si alguien lo ha dicho, manda lo dicho
            cl, vs = valores(c, "usuario")
            if vs:
                fab([f"{_los(cl)} los usan {_los(sa(vs[0]))}"])
                return _dice("usuario", c, cl, vs) + _por_herencia(c, cl)
        return None
    m = _P["usuario_inv"].match(n)
    if m:
        prof = K._kb_clase(m.group(1))
        if prof and "persona" in cadena(prof):
            cs = inversa("usuario", prof)
            if cs:
                fab([f"{_los(prof)} usan {_los(c)}" for c in cs[:3]])
                return f"{K._cap(_un(prof))} suele usar {_lista([_los(c) for c in cs[:6]]).replace('los ', '').replace('las ', '')}."
        return None
    return None


def _charla(nuc, antes, uso):
    """«¿tengo algo para cortar?»: entre lo que la persona ha contado, lo que sirve para eso (por su clase)."""
    antes = antes.strip()
    palabras = [w for w in antes.split() if len(w) > 2 and w not in ("que", "hay", "algun", "alguna")]
    hallados = []
    for f in nuc.F:
        if not f.get("obj_cls") or f.get("neg") or not f.get("vig", True) or f.get("exp"):
            continue
        raiz = sa(f["v"])[:3]
        tener = any(w.startswith(("ten", "tien", "tuv")) for w in palabras)
        if palabras and not any(w.startswith(raiz) for w in palabras) and not (tener and f["v"] in ("comprar", "tener", "recibir", "heredar")):
            continue                                       # lo que se compra o se recibe, se tiene
        quien = sa(nuc.disp(f["s"])) if f.get("s") else ""
        primera = bool(re.match(r"^(?:tengo|tenemos|he|hemos|compre|uso|llevo|guardo)\b", antes))
        if f.get("s") == "U" and not primera and re.search(r"\b(?:mi|mis|su|sus|el|la)\b", antes):
            continue                                       # se pregunta por otra persona
        if f.get("s") not in ("U", None) and quien and quien.replace("tu ", "mi ").replace("tus ", "mis ") not in antes and quien not in antes:
            continue
        for cl, v in valores(f["obj_cls"], "funcion", todos=True):
            if _casa("funcion", v, uso):
                hallados.append((f, cl, v))
                break
    if not hallados:
        if inversa("funcion", uso) and palabras:
            nuc.ult_just = None
            return {"respuesta": f"No me consta: no me has hablado de nada que sirva para {uso}.", "estado": "abst", "consultar": False, "tipo": "abst"}
        return None
    hallados = list({(str(x[0].get("s")), x[0]["obj_cls"]): x for x in hallados}.values())   # una vez cada cosa
    f, cl, v = hallados[-1]
    nuc.ult_just = {"pasos": [nuc.frase(f), f"{_los(cl)} sirven para {v}"]}
    try:
        nuc._pasos_fab.add(f"{_los(cl)} sirven para {v}")
    except Exception:                                  # noqa
        pass
    cosas = _lista([nuc.frase(x[0]) for x in hallados[-3:]])
    return f"Sí: {cosas}, y {_los(cl)} sirven para {v}."


_FRASE_COMUN = {"funcion": "sirven para {}", "material": "suelen ser de {}", "lugar": "suelen estar en {}", "usuario": "los usan {}"}


def comunes(a, b):
    """Lo que dos conceptos comparten por sus relaciones: «sirven para cortar», «suelen ser de metal», «suelen estar en la cocina»."""
    out = []
    for rel in ("funcion", "material", "lugar"):
        _, va = valores(a, rel)
        _, vb = valores(b, rel)
        for x in va:
            y = next((y for y in vb if _casa(rel, x, y) or _casa(rel, y, x)), None)
            if y:
                corto = x if len(x) <= len(y) else y
                if rel == "funcion":
                    corto = _uso(corto)[0] if _uso(x)[1] != _uso(y)[1] else corto
                out.append(_FRASE_COMUN[rel].format(_el_lugar(corto) if rel == "lugar" else corto))
                break
    return out


# ------------------------------------------------------------------ 2.16: tamaño típico y dónde vive
_ESC = {"grande": 1, "pequeno": -1, "pequena": -1, "pequeño": -1, "pequeña": -1, "pesado": 1, "pesada": 1, "ligero": -1, "ligera": -1, "alto": 1, "alta": 1, "bajo": -1, "baja": -1, "largo": 1, "larga": 1, "corto": -1, "corta": -1,
        "mayor": 1, "menor": -1, "chico": -1, "chica": -1}
_T_ALT = re.compile(rf"^(?:y )?(?:que|cual|quien) (?:es|son|pesa|mide|ocupa) mas (?:(grande|peque[nñ][oa]|pesad[oa]|liger[oa]|alt[oa]|baj[oa]|larg[oa]|cort[oa]|chic[oa])s?)?,? ?({_ART} [a-zñ ]+?) o ({_ART} [a-zñ ]+)$")
_T_SN = re.compile(rf"^(?:y )?({_ART} [a-zñ ]+?) (?:es|son) mas (grande|peque[nñ][oa]|pesad[oa]|liger[oa]|alt[oa]|baj[oa]|larg[oa]|cort[oa]|chic[oa])s? que ({_ART} [a-zñ ]+)$")
_VIVE_SN = re.compile(rf"^(?:y )?({_ART} [a-zñ]+) (?:viven?|suelen? vivir|habitan?) en (?:el |la |los |las |un |una )?([a-zñ]+)$")
_VIVE_DIR = re.compile(rf"^(?:y )?donde (?:viven?|suelen? vivir|habitan?) ({_ART} [a-zñ]+)$")
_VIVE_INV = re.compile(r"^(?:y )?que (?:animal|animales|bicho|bichos) (?:viven?|hay|habitan?|suelen? vivir) en (?:el |la |los |las |un |una )?([a-zñ]+)$")


def tam(c):
    k = K.kb()["tam"]
    for cl in cadena(c):
        if cl in k:
            return k[cl], cl
    return None, None


def _compara(a, b, sentido, palabra):
    (ta, ca), (tb, cb) = tam(a), tam(b)
    if ta is None or tb is None:
        return None
    que = {"pesa": "pesa más", "mide": "mide más"}.get(palabra, "es más " + palabra)
    if ta == tb:
        return None, f"No lo sé seguro: {_un(a)} y {_un(b)} suelen ser de tamaño parecido."
    mayor, menor = (a, b) if ta > tb else (b, a)
    gana = mayor if sentido > 0 else menor
    matiz = "Normalmente, " if abs(ta - tb) == 1 else ""
    por = "" if (ca == a and cb == b) else f" Lo calculo por su clase: {_un(a)} es {_un(ca)}".replace(f"{_un(a)} es {_un(a)}", "").rstrip() if False else ""
    return gana, f"{matiz}{_un(gana)}: {_un(mayor)} suele ser más grande que {_un(menor)}.".replace("Normalmente, un", "Normalmente, un")


def tamano_y_habitat(nuc, n):
    n = n.strip(" ?¿.!")
    fab = lambda pasos: setattr(nuc, "ult_just", {"pasos": pasos, "fabrica": True})   # noqa: E731
    m = _T_ALT.match(n)
    if m:
        a, b = _clase(m.group(2)), _clase(m.group(3))
        if a and b and a in K.kb()["forma"] and b in K.kb()["forma"]:
            adj = sa(m.group(1) or "grande")
            r = _compara(a, b, _ESC.get(adj, 1), adj)
            if r:
                fab([f"tamaño típico de {_un(a)}: {tam(a)[0]} de 10", f"tamaño típico de {_un(b)}: {tam(b)[0]} de 10"])
                txt = r[1]
                if r[0] and adj not in ("grande",):
                    txt = f"{K._cap(_un(r[0]))}. " + txt.split(": ", 1)[-1][:1].upper() + txt.split(": ", 1)[-1][1:]
                return K._cap(txt)
        return None
    m = _T_SN.match(n)
    if m:
        a, b = _clase(m.group(1)), _clase(m.group(3))
        if a and b and a in K.kb()["forma"] and b in K.kb()["forma"]:
            adj = sa(m.group(2))
            r = _compara(a, b, _ESC.get(adj, 1), adj)
            if r:
                fab([f"tamaño típico de {_un(a)}: {tam(a)[0]} de 10", f"tamaño típico de {_un(b)}: {tam(b)[0]} de 10"])
                if r[0] is None:
                    return r[1]
                (ta, _), (tb, _) = tam(a), tam(b)
                mayor, menor = (a, b) if ta > tb else (b, a)
                return f"{'Sí' if r[0] == a else 'No'}: {_un(mayor)} suele ser más grande que {_un(menor)}."
        return None
    m = _VIVE_SN.match(n)
    if m:
        c = _clase(m.group(1))
        if c and c in K.kb()["forma"]:
            cl, vs = valores(c, "lugar")
            if vs:
                fab([f"{_los(cl)} suelen vivir en {_el_lugar(vs[0])}"])
                if any(_casa("lugar", v, m.group(2)) for v in vs) or (sa(m.group(2)) == "agua" and any(sa(v) in ("mar", "rio", "lago", "charca", "estanque", "oceano") for v in vs)):
                    return f"Sí, {_los(c)} viven en {_lista([_el_lugar(v) for v in vs[:2]])}."
                return f"No es lo normal: {_los(c)} suelen vivir en {_lista([_el_lugar(v) for v in vs[:2]])}."
        return None
    m = _VIVE_DIR.match(n)
    if m:
        c = _clase(m.group(1))
        if c and c in K.kb()["forma"] and "animal" in cadena(c):
            cl, vs = valores(c, "lugar")
            if vs:
                fab([f"{_los(cl)} suelen vivir en {_el_lugar(vs[0])}"])
                return f"{K._cap(_los(c))} suelen vivir en {_lista([_el_lugar(v) for v in vs[:3]])}." + ("" if cl == c else f" Lo sé porque {_los(c)} son {K.forma(cl, plural=True)}.")
        return None
    m = _VIVE_INV.match(n)
    if m:
        cs = [c for c in inversa("lugar", m.group(1)) if "animal" in cadena(c)]
        if cs:
            fab([f"{_los(c)} viven en {m.group(1)}" for c in cs[:3]])
            return f"Allí viven, por ejemplo, {_lista([_los(c) for c in cs[:6]])}."
    return None
