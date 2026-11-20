"""LCM 2.2 · conceptos de fábrica del núcleo: taxonomía por capas, propiedades típicas con excepciones, partes,
contrarios y grupos de relaciones. Se leen de conceptos_base.txt (texto editable) y se consultan conversando:
«dime tres frutas», «¿qué animales vuelan?», «¿qué tienen en común un perro y un gato?», «¿vuela un pingüino?»."""
from __future__ import annotations

import os
import re

from . import morfo as M
from .morfo import sa

_KB = None
_PREP = ("en", "por", "de", "con", "bajo", "sobre")


def kb():
    global _KB
    if _KB is not None:
        return _KB
    d = {"isa": {}, "hijos": {}, "forma": {}, "gen": {}, "props": [], "partes": {}, "parte_de": {}, "ant": {}, "grupos": {}, "parte_disp": {}, "efectos": {},
         "alias": {}, "rel": {"funcion": {}, "material": {}, "lugar": {}, "usuario": {}}, "tam": {}, "huecos": {}, "tono": {}, "acciones": {}, "equiv": {}, "equiv_n": {}}
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conceptos_base.txt")
    sec = ""

    def reg(w):
        g = ""
        if w.endswith(("/m", "/f")):
            w, g = w[:-2], w[-1]
        k = sa(w)
        d["forma"].setdefault(k, w)
        if g:
            d["gen"][k] = g
        return k
    try:
        lineas = open(ruta, encoding="utf-8").read().split("\n")
    except OSError:
        lineas = []
    try:                                                 # 2.16: lo aprendido en la escuela de conceptos (cartillas leídas), mismo formato
        lineas += [""] + open(os.path.join(os.path.dirname(ruta), "conceptos_aprendidos.txt"), encoding="utf-8").read().split("\n")
    except OSError:
        pass
    for l in lineas:
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if l.startswith("["):
            sec = l.strip("[]")
            continue
        if sec == "contrarios":
            for par in l.split(","):
                if "/" in par:
                    a, b = [x.strip() for x in par.split("/", 1)]
                    d["forma"].setdefault(sa(a), a); d["forma"].setdefault(sa(b), b)
                    d["ant"].setdefault(sa(a), []).append(sa(b)); d["ant"].setdefault(sa(b), []).append(sa(a))
            continue
        if ":" not in l:
            continue
        cab, resto = l.split(":", 1)
        if sec == "taxonomia":
            c = reg(cab.strip())
            for m in resto.split(","):
                m = m.strip()
                if m:
                    k = reg(m)
                    d["isa"].setdefault(k, []).append(c); d["hijos"].setdefault(c, []).append(k)
        elif sec == "propiedades":
            c = sa(cab.strip())
            for pr in resto.split(";"):
                pr = pr.strip()
                if not pr:
                    continue
                neg = pr.startswith("no ")
                if neg:
                    pr = pr[3:]
                ps = pr.split()
                d["props"].append((c, neg, ps[0], " ".join(ps[1:])))
        elif sec == "partes":
            c = sa(cab.strip())
            for m in resto.split(","):
                m = m.strip()
                if m:
                    k1 = sa(M.singular(m)) if m.endswith("s") else sa(m)
                    d["forma"].setdefault(k1, M.singular(m) if m.endswith("s") else m)
                    d["parte_disp"][(c, k1)] = m
                    d["partes"].setdefault(c, []).append(k1); d["parte_de"].setdefault(k1, []).append(c)
        elif sec == "efectos":
            d["efectos"][sa(cab.strip())] = sa(resto.strip())
            d["forma"].setdefault(sa(resto.strip()), resto.strip())
        elif sec == "grupos":
            d["grupos"][sa(cab.strip())] = [sa(x.strip()) for x in resto.split(",") if x.strip()]
        elif sec == "sinonimos":                         # 2.15: otras palabras para la misma clase («ropa» = prenda)
            for x in resto.split(","):
                if x.strip():
                    d["alias"][sa(x.strip())] = sa(cab.strip())
        elif sec == "tamano":                            # 2.16: tamaño típico en una escala de 1 (diminuto) a 6 (gigantesco); se hereda
            try:
                d["tam"][sa(cab.strip())] = int(resto.strip())
            except ValueError:
                pass
        elif sec == "huecos":                            # 2.17: lo que suele faltar por saber cuando alguien cuenta algo («me voy de viaje» -> ¿adónde?)
            h, _, preg = resto.partition("|")
            d["huecos"].setdefault(sa(cab.strip()), []).append((h.strip(), preg.strip()))
        elif sec == "equivalencias":                     # 2.19: verbos que dicen lo mismo («comer: alimentarse de, ingerir»)
            d["equiv"][cab.strip()] = [x.strip() for x in resto.split(",") if x.strip()]
        elif sec == "equivalencias_nombres":             # 2.19: nombres que dicen lo mismo («comida: alimento»)
            d["equiv_n"][cab.strip()] = [x.strip() for x in resto.split(",") if x.strip()]
        elif sec == "acciones":                          # 2.17: el evento y la acción que es («cena: cenar»): «tengo una cena» = «ceno»
            d["acciones"][sa(cab.strip())] = [sa(x.strip()) for x in resto.split(",") if x.strip()]
        elif sec == "tono":                              # 2.17: cómo se recibe una noticia (logro, bueno, malo, duelo, reto, felicidades)
            for x in resto.split(","):
                if x.strip():
                    d["tono"][sa(x.strip())] = cab.strip()
        elif sec in d["rel"]:                            # 2.15: relaciones entre conceptos (función, material, lugar, usuario)
            vals = d["rel"][sec].setdefault(sa(cab.strip()), [])
            vals.extend(x.strip() for x in resto.split(",") if x.strip() and x.strip() not in vals)
    for w in list(d["alias"]):                           # un alias nunca tapa un concepto que ya existe
        if w in d["isa"] or w in d["hijos"]:
            del d["alias"][w]
    _KB = d
    for w, g in d["gen"].items():
        M.GEN_EXTRA.setdefault(w, g)
    return d


def ancestros(c, con_dist=False):
    """Clases por encima de c en la base de fábrica, de la más cercana a la más general."""
    k = kb()
    out, cola, visto = [], [(c, 0)], {c}
    while cola:
        x, n = cola.pop(0)
        for p in k["isa"].get(x, []):
            if p not in visto:
                visto.add(p); out.append((p, n + 1)); cola.append((p, n + 1))
    return out if con_dist else [p for p, _ in out]


def descendientes(c, max_n=400):
    k = kb()
    out, cola, visto = [], [c], {c}
    while cola and len(out) < max_n:
        x = cola.pop(0)
        for h in k["hijos"].get(x, []):
            if h not in visto:
                visto.add(h); out.append(h); cola.append(h)
    return out


def genero(c):
    k = kb()
    return k["gen"].get(c) or M.genero_sust(k["forma"].get(c, c))


def forma(c, plural=False):
    w = kb()["forma"].get(c, c)
    if plural:
        ps = w.split()
        ps[0] = M.plural(ps[0])
        if len(ps) > 1 and ps[1] in ("vivo", "inglesa"):
            ps[1] = M.plural(ps[1])
        return " ".join(ps)
    return w


_A_TONICA = {"ave", "aguila", "agua", "arpa", "hacha", "haba", "alga", "haya", "ala", "alma", "hada", "aula", "area", "arma", "hambre"}


def un(c):
    return ("una " if genero(c) == "f" and c not in _A_TONICA else "un ") + forma(c)


def el(c):
    return ("la " if genero(c) == "f" and c not in _A_TONICA else "el ") + forma(c)


def los(c):
    w = forma(c, plural=True)
    return ("las " if genero(c) == "f" else "los ") + w


_MASA = None


def es_masa(c):
    """Nombres que se dicen en singular al generalizar: «la hierba es verde», «el hierro es un metal»."""
    global _MASA
    if _MASA is None:
        _MASA = {"hierba", "nieve", "leche", "carne", "pescado", "pan", "pasta", "agua", "sangre", "miel", "fruta", "verdura"}
        for raiz in ("material", "bebida", "cereal", "lacteo", "fenomeno", "emocion", "deporte", "color", "arte", "asignatura", "sentido"):
            _MASA.update(descendientes(raiz))
    return c in _MASA


def gen1(c):
    return el(c) if es_masa(c) else un(c)


def suj(c):
    return el(c) if es_masa(c) else los(c)


def marcos_fabrica(nuevo):
    """Marcos de clase construidos con las propiedades y partes de fábrica (no se guardan en disco)."""
    k = kb()
    out = []
    for c, neg, verbo, resto in k["props"]:
        refl = verbo.endswith("se") and len(verbo) > 4
        v = sa(verbo[:-2] if refl else verbo)
        f = nuevo(v=v, s="K:" + c, neg=neg, refl=refl, src="fábrica", pl_suj=not es_masa(c), fab=True)
        ps = resto.split()
        if v in ("ser", "estar") and ps and ps[0] in _PREP:
            f["comps"] = [[ps[0], None, " ".join(ps[1:])]]
        elif v in ("ser", "estar") and ps:
            if ps[0] in ("un", "una"):
                cl = sa(" ".join(ps[1:]))
                f["attr"] = [cl]; f["isa"] = [cl]; f["isa_art"] = {cl: "un"}
            else:
                f["attr"] = [M.masc(ps[-1])]; f["grado"] = " ".join(ps[:-1])
        elif ps and ps[0] in _PREP:
            f["comps"] = [[ps[0], None, " ".join(ps[1:])]]
        elif ps:
            f["obj_disp"] = resto
            nucleo = [w for w in ps if M.numero(w) is None and w not in ("el", "la", "los", "las", "un", "una", "de", "y", "en", "poca", "poco", "muy", "bien", "mucho")]
            sus = nucleo[0] if nucleo else ps[-1]
            f["obj_cls"] = sa(M.singular(sus)) if sus.endswith("s") else sa(sus)
            nums = [M.numero(w) for w in ps if M.numero(w) is not None and w not in ("un", "una")]
            f["cuant"] = nums[0] if nums else None
            f["pl_obj"] = True
            resto_ps = ps[ps.index(sus) + 1:] if sus in ps else []
            if resto_ps and resto_ps[0] in _PREP:
                f["comps"] = [[resto_ps[0], None, " ".join(resto_ps[1:])]]
                f["obj_disp"] = " ".join(ps[:ps.index(sus) + 1])
        out.append(f)
    ya = {(f["s"], f.get("obj_cls")) for f in out if f["v"] == "tener"}
    for todo, partes in k["partes"].items():
        for p in partes:
            if ("K:" + todo, p) not in ya:
                out.append(nuevo(v="tener", s="K:" + todo, src="fábrica", pl_suj=True, fab=True, obj_disp=k["parte_disp"][(todo, p)], obj_cls=p, pl_obj=True, parte=True))
    return out


_EJ = re.compile(r"^(?:dime|nombra|nombrame|di|dame|enumera|pon|ponme|cita|citame|sabes|conoces|me dices|me das|puedes (?:decirme|nombrar|darme))\s+(?:(un|una|uno|dos|tres|cuatro|cinco|seis|algun|alguna|algunos|algunas|unos|unas|varios|varias|otro|otra)\s+)?"
                 r"(?:(?:ejemplos?|tipos?|clases?|nombres?)\s+de\s+)?(?:nombres? de )?([a-zñ ]+?)(?:\s+(?:que (?:conozcas|sepas|te sepas)|distint[oa]s|diferentes|por favor))?$")
_EJ2 = re.compile(r"^(?:que|cuales?)\s+(?:(?:tipos?|clases?|ejemplos?)\s+de\s+)?([a-zñ ]+?)\s+(?:conoces|sabes|hay|existen|te sabes|me (?:puedes )?(?:dices|decir|nombrar))$")
_EJ3 = re.compile(r"^(?:un |otro |algun )?ejemplo de ([a-zñ ]+)$")
_COMUN = re.compile(r"^(?:que tienen en comun|en que se parecen|que comparten|en que se diferencian|en que se distinguen|que diferencia hay entre|cual es la diferencia entre|que diferencias hay entre)\s+(.+?)\s+(?:y|e|de)\s+(.+)$")
_CONTR = re.compile(r"^(?:cual es|que es|dime|sabes)?\s*(?:el |lo |un )?(?:contrario|opuesto|antonimo)\s+de\s+([a-zñ]+)$")
_PARTES = re.compile(r"^(?:que partes tiene|cuales son las partes de|de que (?:partes )?(?:se compone|esta hech[oa]|consta)|que tiene)\s+(?:un |una |el |la )?([a-zñ]+)$")
_PARTE_DE = re.compile(r"^de que (?:es|forma) parte (?:un |una |el |la )?([a-zñ]+)$")


ALIAS = {"profesion": "profesional", "profesiones": "profesional", "oficio": "profesional", "oficios": "profesional", "trabajos": "profesional"}


def _clave(nuc, texto):
    """Clase de fábrica (o enseñada) que nombra un sintagma simple: «un perro», «los gatos», «perro»."""
    t = re.sub(r"^(?:un|una|unos|unas|el|la|los|las|mi|tu|su)\s+", "", sa(texto).strip(" ?.,"))
    t = ALIAS.get(t, t)
    k = kb()
    for cand in (t, sa(M.singular(t)), " ".join([sa(M.singular(t.split()[0]))] + [sa(M.singular(x)) for x in t.split()[1:]]) if t else t):
        if cand in k["hijos"] or cand in k["isa"] or cand in k["partes"]:
            return cand
    # entidad conocida por el núcleo: su clase
    for eid, d in nuc.E.items():
        if eid.startswith("N:") and eid[2:] == t and d.get("clase"):
            return d["clase"]
    cand = sa(M.singular(t))
    if any(cand in f.get("isa", []) for f in nuc.F) or nuc._semilla_isa(cand):
        return cand
    return None


def responder(nuc, p, n, es_preg):
    """Respuesta conceptual o None."""
    k = kb()
    m = _EJ.match(n) or _EJ2.match(n) or _EJ3.match(n)
    if m:
        cuantos = m.group(1) if m.re is _EJ else ""
        cosa = m.group(m.lastindex).strip()
        c = _clave(nuc, cosa)
        if c and (k["hijos"].get(c) or _ensenados(nuc, c)):
            n_ = {"un": 1, "una": 1, "uno": 1, "otro": 1, "otra": 1, "algun": 1, "alguna": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}.get(cuantos or "", 5 if not cosa.endswith("s") or cuantos in ("", None) else 4)
            if not cuantos and not sa(M.singular(cosa.split()[0])) != cosa.split()[0]:
                n_ = 1
            propios = _ensenados(nuc, c)
            directos = k["hijos"].get(c, [])
            hojas = [x for x in directos if x not in k["hijos"]]
            if len(hojas) < 6:                       # clase abstracta («animal»): se dan ejemplos concretos de las capas de abajo
                sub = [k["hijos"][x] for x in directos if x in k["hijos"]]
                i = 0
                while sub and any(i < len(x) for x in sub) and len(hojas) < 40:
                    hojas.extend(x[i] for x in sub if i < len(x) and x[i] not in k["hijos"] and x[i] not in hojas)
                    i += 1
            hijos = list(dict.fromkeys(propios + (hojas or directos)))
            # se rota con el turno para no repetir siempre los mismos
            pedidos = getattr(nuc, "_ej_dados", {}).get(c, 0)
            if len(hijos) > n_ and pedidos:          # si vuelve a pedir, se dan otros distintos
                r0 = pedidos % len(hijos)
                hijos = (hijos[r0:] + hijos[:r0])
            if not hasattr(nuc, "_ej_dados"):
                nuc._ej_dados = {}
            nuc._ej_dados[c] = pedidos + max(1, n_)
            sel = hijos[:max(1, n_)]
            nuc.ult_just = {"pasos": [f"{un(x)} es {un(c)}" for x in sel[:3]], "fabrica": True}
            if len(sel) == 1:
                return f"Por ejemplo, {un(sel[0])}." if sel[0] in k["forma"] else f"Por ejemplo, {nuc._un(sel[0], M.genero_sust(sel[0]))}."
            return _cap(nuc._lista([forma(x) for x in sel])) + "."
        if m.re is _EJ and re.match(r"^(?:dime|nombra|nombrame|enumera|cita|citame) (?:un|una|dos|tres|cuatro|cinco|seis|algun|alguna|algunos|algunas|unos|unas|varios|varias) [a-zñ]+$", n) and not c \
                and not any(e.startswith(("I:", "G:")) and d.get("clase") == sa(M.singular(cosa)) for e, d in nuc.E.items()):
            return {"respuesta": f"No conozco ningún ejemplo de «{cosa}»: no sé qué es.", "estado": "abst", "consultar": False, "tipo": "abst"}
        pass
    r = _grupo_rel(nuc, n, p)
    if r is not None:
        return r
    r = _generica(nuc, n, es_preg, p)
    if r is not None:
        return r
    m = _COMUN.match(n)
    if m:
        a, b = _clave(nuc, m.group(1)), _clave(nuc, m.group(2))
        if not a or not b:
            return None
        dif = "diferenc" in n or "disting" in n
        aa, bb = [a] + _anc(nuc, a), [b] + _anc(nuc, b)
        comunes = [x for x in aa if x in bb]
        pa, pb = _props(nuc, a), _props(nuc, b)
        if comunes:                                   # la clase común más específica (la que tiene más capas encima)
            comunes.sort(key=lambda x: -len(ancestros(x)) if x in kb()["isa"] else 0)
        if not dif:
            trozos = []
            if comunes:
                c0 = comunes[0]
                dos = "Las dos" if genero(a) == "f" and genero(b) == "f" else "Los dos"
                trozos.append(f"{dos} son {forma(c0, plural=True)}" if a != c0 and b != c0 else f"{_cap(un(a if b == c0 else b))} es {un(c0)}")
            comp = [t for key, (neg, t) in pa.items() if key in pb and pb[key][0] == neg and not neg]      # lo que no hacen ninguno de los dos no es «tener algo en común»
            if comp:
                dos = "las dos" if genero(a) == "f" and genero(b) == "f" else "los dos"
                trozos.append(dos + " " + nuc._lista(comp[:4]) if trozos else _cap(dos) + " " + nuc._lista(comp[:4]))
            from . import relaciones as _R                 # 2.15: también comparten relaciones (para qué sirven, de qué son, dónde están)
            rc = [t for t in _R.comunes(a, b) if t not in comp]
            if rc:
                dos = "las dos" if genero(a) == "f" and genero(b) == "f" else "los dos"
                trozos.append(dos + " " + nuc._lista(rc[:3]) if trozos else _cap(dos) + " " + nuc._lista(rc[:3]))
            if not trozos:
                return {"respuesta": f"No lo sé: no conozco nada que compartan {un(a)} y {un(b)}.", "estado": "abst", "consultar": False, "tipo": "abst"}
            nuc.ult_just = {"pasos": [f"{un(a)} es {un(x)}" for x in aa[1:2]] + [f"{un(b)} es {un(x)}" for x in bb[1:2]], "fabrica": True}
            return _cap("; ".join(trozos)) + "."
        trozos = []
        da, db = [x for x in aa if x not in bb], [x for x in bb if x not in aa]
        if len(da) > 1 or len(db) > 1 or (da and db and (a not in bb and b not in aa) and (aa[1:2] != bb[1:2])):
            ca = next((x for x in da if x != a), None); cb = next((x for x in db if x != b), None)
            if ca and cb:
                trozos.append(f"{un(a)} es {un(ca)} y {un(b)} es {un(cb)}")
        solo_a = [t for key, (neg, t) in pa.items() if key not in pb or pb[key][0] != neg]
        solo_b = [t for key, (neg, t) in pb.items() if key not in pa or pa[key][0] != neg]
        if solo_a:
            trozos.append(f"{los(a)} " + nuc._lista(solo_a[:3]))
        if solo_b:
            trozos.append(f"{los(b)} " + nuc._lista(solo_b[:3]))
        if not trozos:
            return {"respuesta": f"No lo sé: no tengo datos que distingan {un(a)} de {un(b)}.", "estado": "abst", "consultar": False, "tipo": "abst"}
        nuc.ult_just = {"pasos": trozos[:2], "fabrica": True}
        return _cap("; ".join(trozos)) + "."
    m = _CONTR.match(n)
    if m and m.group(1) in k["ant"]:
        x = m.group(1)
        return f"Lo contrario de {forma(x)} es {nuc._lista([forma(y) for y in dict.fromkeys(k['ant'][x])][:2]).replace(' y ', ' o ')}."
    m = _PARTE_DE.match(n)
    if m:
        c = sa(M.singular(m.group(1)))
        if c in k["parte_de"]:
            return f"{_cap(un(c))} es parte de {nuc._lista([un(x) for x in k['parte_de'][c][:3]])}."
        return None
    m = _PARTES.match(n)
    if m and n.startswith(("que partes", "cuales son las partes", "de que")):
        c = sa(M.singular(m.group(1)))
        if c in k["partes"]:
            return f"{_cap(un(c))} tiene {nuc._lista([k['parte_disp'][(c, x)] for x in k['partes'][c]])}."
        return None
    return None


def _cap(s):
    return s[:1].upper() + s[1:] if s else s


def _ensenados(nuc, c):
    """Miembros de la clase c que ha enseñado la persona («Un colibrí es un pájaro»)."""
    out = []
    for f in nuc.F:
        if f["v"] == "ser" and c in f.get("isa", []) and not f.get("neg") and f.get("vig", True) and str(f["s"]).startswith("K:") and not f.get("fab"):
            out.append(nuc.can(f["s"])[2:])
    return out


def _anc(nuc, c):
    return [x for x, _ in nuc.clases("K:" + c)]


def _props(nuc, c):
    """{clave: (neg, texto)} con las propiedades de c: las de fábrica y las dichas, heredadas por capas (manda la más cercana)."""
    out = {}
    for f in nuc.marcos(s="K:" + c, vig=True, herencia=True):
        if f["v"] == "ser" and f.get("isa"):
            continue
        k = nuc._clave_prop(f) + (f.get("cuant"),)
        if k not in out:
            out[k] = (bool(f.get("neg")), nuc.frase(f, sin_sujeto=True))
    return out


_PERSONAL = {"mi", "mis", "tu", "tus", "su", "sus", "me", "te", "le", "les", "nos", "se", "alguien", "nadie", "quien", "yo", "ella", "ellos", "ellas", "nosotros", "aqui", "alli", "hoy", "ayer", "mañana", "ahora"}
VOCES = ("ladrar", "maullar", "rugir", "mugir", "balar", "relinchar", "croar", "aullar", "gruñir", "cantar", "hablar")
_MODAL = r"(?:puede|pueden|sabe|saben|suele|suelen)"
_ART = r"(un|una|los|las|el|la)"
_GEN_A = re.compile(rf"^(?:(no) )?(?:({_MODAL}) )?([a-zñ]+)(?: (.+?))? {_ART} ([a-zñ]+(?: vivos?)?)$")
_GEN_B = re.compile(rf"^{_ART} ([a-zñ]+(?: vivos?)?) (?:(no) )?(?:({_MODAL}) )?([a-zñ]+)(?: (.+))?$")
_QUE_CL = re.compile(r"^(?:que|cuales?) ([a-zñ]+) (?:(no) )?(?:(pueden?|saben?) )?([a-zñ]+)(?: (.+))?$")
_QUE_ES = re.compile(r"^(?:que|que cosa) (?:es|son) (?:un |una |el |la |los |las )?([a-zñ]+(?: vivos?)?)$|^(?:tu )?(?:sabes|conoces|entiendes) (?:algo|mucho|cosas) (?:de|sobre|acerca de) (?:los |las |el |la )?([a-zñ]+)$|^que sabes (?:de|sobre|acerca de) (?:los |las )([a-zñ]+)$|^sabes (?:que|lo que) (?:es|son) (?:un |una |los |las )?([a-zñ]+)$")
_TIPO_DE = re.compile(r"^(?:que tipo|que clase|que tipo de cosa|que clase de cosa) (?:de (?:cosa|ser|animal|objeto) )?es (?:un |una |el |la )([a-zñ]+)$")


def voz_de(clases):
    """(clase, verbo) de la voz propia de la primera clase de la lista que la tenga («gato» -> maullar)."""
    k = kb()
    for c in clases:
        for cl, ng, v, rs in k["props"]:
            if cl == c and not ng and sa(v) in VOCES and sa(v) not in ("cantar", "hablar"):
                return cl, sa(v)
    return None


def _kb_clase(texto):
    """Clave de una clase de fábrica nombrada por una o dos palabras (singular o plural), o None."""
    k = kb()
    t = sa(texto).strip()
    for cand in (t, sa(M.singular(t)), " ".join(sa(M.singular(x)) for x in t.split())):
        if cand in k["isa"] or cand in k["hijos"]:
            return cand
    for cand in (t, sa(M.singular(t))):
        if cand in k["alias"]:
            return k["alias"][cand]
    return None


def _lema(palabra, modal=False):
    c = M.analizar(palabra)
    if modal:
        c = [x for x in c if x[1] == "inf"]
    else:
        c = [x for x in c if x[1] == "pres" and x[2] in ("3s", "3p")]
    return c[0][0] if c else None


def _estado(c, verbo, resto):
    """(neg, clase_que_lo_dice, texto) de la propiedad de fábrica más cercana a c que casa con verbo+resto, o None."""
    k = kb()
    cadena = [c] + ancestros(c)
    r = _nucleo_resto(resto)
    cop = verbo in ("ser", "estar")
    if cop:
        r = [sa(M.masc(x)) for x in r]
    mejor = None
    for cl, neg, v, rs in k["props"]:
        if cl not in cadena:
            continue
        v0 = sa(v[:-2] if v.endswith("se") and len(v) > 4 else v)
        if v0 != verbo:
            continue
        if cop and (not r or [sa(M.masc(x)) for x in _nucleo_resto(rs)] != r):
            continue
        if not cop and r and not _casa_resto(r, rs):
            continue
        d = cadena.index(cl)
        if mejor is None or d < mejor[0]:
            mejor = (d, neg, cl, v, rs)
    return mejor


_VACIAS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "muy", "mucho", "mucha", "muchos", "muchas", "bien", "y"}


def _nucleo_resto(resto):
    return [sa(M.singular(w)) if w.endswith("s") and len(w) > 3 else sa(w) for w in sa(resto or "").split() if w not in _VACIAS]


_INCLUYE = {"agua": {"mar", "rio", "lago", "oceano", "estanque"}, "naturaleza": {"bosque", "selva", "montaña", "campo", "mar"}}


def _casa_resto(r, rs):
    b = _nucleo_resto(rs)
    b = b + [k for k, v in _INCLUYE.items() if set(b) & v]     # «vivir en el mar» también es «vivir en el agua»
    if not b:
        return False
    nums_r = [x for x in r if M.numero(x) is not None]
    nums_b = [x for x in b if M.numero(x) is not None]
    if nums_r and nums_b and nums_r != nums_b:
        return False
    sr = [x for x in r if M.numero(x) is None]
    sb = [x for x in b if M.numero(x) is None]
    return bool(sr) and all(x in sb for x in sr)


def _frase_prop(c, neg, v, rs, plural=True):
    if es_masa(c):
        refl = v.endswith("se") and len(v) > 4
        v0 = v[:-2] if refl else v
        if v0 in ("ser", "estar") and rs and not rs.startswith(("un ", "una ")):
            ps = rs.split(); ps[-1] = M.concuerda(M.masc(ps[-1]), genero(c), False); rs = " ".join(ps)
        return " ".join(x for x in (el(c), "no" if neg else "", "se" if refl else "", M.conjugar(sa(v0), "pres", "3s"), rs) if x)
    refl = v.endswith("se") and len(v) > 4
    v0 = v[:-2] if refl else v
    vf = M.conjugar(sa(v0), "pres", "3p" if plural else "3s")
    if v0 in ("ser", "estar") and rs and plural and not rs.startswith(("un ", "una ")):
        ps = rs.split()
        ps[-1] = M.concuerda(M.masc(ps[-1]), genero(c), True)
        rs = " ".join(ps)
    elif v0 in ("ser", "estar") and rs.startswith(("un ", "una ")) and plural:
        rs = " ".join(M.plural(x) for x in rs.split()[1:])
    return " ".join(x for x in ((los(c) if plural else un(c)), "no" if neg else "", "se" if refl else "", vf, rs) if x)


def _dichas(nuc, c):
    """Clases que la persona ha dicho de c («Un tenedor es un cubierto»)."""
    out = []
    for f in nuc.F:
        if f["v"] == "ser" and f.get("s") and nuc.can(f["s"]) == "K:" + c and f.get("vig", True) and not f.get("neg"):
            out.extend(f.get("isa", []))
    return list(dict.fromkeys(out))


def _usuario_dijo(nuc, c, verbo):
    """¿Ha dicho la persona algo con ese verbo sobre la clase c o las que tiene encima? Entonces decide el grafo."""
    cadena = {"K:" + c} | {"K:" + x for x, _ in nuc.clases("K:" + c)}
    return any(f.get("s") and nuc.can(f["s"]) in cadena and f["v"] == verbo for f in nuc.F)


def _tiene_propios(nuc, c):
    """¿Hay algo dicho por la persona sobre la clase c o algún ejemplar suyo? Entonces manda el grafo de la conversación."""
    for f in nuc.F:
        s = nuc.can(f["s"]) if f.get("s") else ""
        if s == "K:" + c:
            return True
    return False


def _generica(nuc, n, es_preg, p=""):
    k = kb()
    if es_preg:
        r_ = _es_un(nuc, n, p)
        if r_ is not None:
            return r_
    m = _QUE_ES.match(n)
    if m:
        w_ = next(g_ for g_ in m.groups() if g_)
        if p and re.search(r"(?<=\s)" + re.escape(w_[:1].upper()) + r"\w*", p) and any(k_.startswith("N:") and sa(k_[2:]) == w_ for k_ in nuc.E):
            return None                                  # 2.12: «¿Qué es el Albatros?»: un nombre propio de la charla manda sobre el concepto
        c = _kb_clase(w_)
        if c:
            nuc._ult_clase = c
        if c and k["isa"].get(c):
            p0 = k["isa"][c][0]
            dichas = [x for x in _dichas(nuc, c) if x != p0]
            nuc._ent("K:" + c, clase=c, gen=genero(c))
            nuc.ult_suj = "K:" + c                      # «¿Qué es un tenedor?» «Es un cubierto»: la respuesta habla del tenedor
            if dichas:
                nuc.ult_just = {"dicho": [f["src"] for f in nuc.F if f["v"] == "ser" and nuc.can(f["s"]) == "K:" + c and f.get("isa")]}
                return f"{_cap(gen1(c))} es {nuc._lista([nuc._un(x, M.genero_sust(x)) for x in dichas[:2]])}, como me dijiste; de fábrica sé además que es {un(p0)}."
            extra = [_frase_prop(c, ng, v, rs).split(" ", 2)[2] for cl, ng, v, rs in k["props"] if cl == c and not ng][:2]
            nuc.ult_just = {"pasos": [f"{un(c)} es {un(p0)}"], "fabrica": True}
            return f"{_cap(gen1(c))} es {un(p0)}." + (f" {_cap(suj(c))} {nuc._lista(extra)}." if extra else "")
        return None
    m = _TIPO_DE.match(n)
    if m:
        c = _kb_clase(m.group(1))
        if c and k["isa"].get(c):
            return f"{_cap(gen1(c))} es {un(k['isa'][c][0])}."
        return None
    if not es_preg:
        return None
    m = _QUE_CL.match(n)
    if m and _kb_clase(m.group(1)) and k["hijos"].get(_kb_clase(m.group(1))):
        c = _kb_clase(m.group(1))
        verbo = _lema(m.group(4), bool(m.group(3)))
        orig0 = {sa(w.strip("¿?¡!.,")): w.strip("¿?¡!.,") for w in p.split()[1:]}
        if any(w in _PERSONAL or orig0.get(w) == "él" or (w in orig0 and orig0[w][:1].isupper()) for w in (m.group(5) or "").split()):
            return None
        if verbo in ("tener", "hacer", "llevar", "usar", "necesitar") and not m.group(5):
            return None                                  # «¿Qué forma tiene?»: pregunta por algo concreto, no por una clase
        if verbo and verbo not in ("conocer", "saber", "haber", "existir", "gustar", "preferir", "decir") and (verbo not in ("ser", "estar") or m.group(5)):
            return _cuales(nuc, c, verbo, m.group(5) or "", m.group(1) == sa(M.singular(m.group(1))) and m.group(1) == c.split()[0], neg=bool(m.group(2)))
        return None
    g = None
    m = _GEN_A.match(n)
    if m and _kb_clase(m.group(6)):
        g = dict(neg=m.group(1), modal=m.group(2), verbo=m.group(3), resto=m.group(4) or "", art=m.group(5), cosa=m.group(6), orden="A")
    else:
        m = _GEN_B.match(n)
        if m and _kb_clase(m.group(2)):
            g = dict(neg=m.group(3), modal=m.group(4), verbo=m.group(5), resto=m.group(6) or "", art=m.group(1), cosa=m.group(2), orden="B")
    if not g:
        return None
    c = _kb_clase(g["cosa"])
    rs_ = g["resto"].split()
    orig = {sa(w.strip("¿?¡!.,")): w.strip("¿?¡!.,") for w in p.split()[1:]}
    if any(w in _PERSONAL or orig.get(w) == "él" or (w in orig and orig[w][:1].isupper()) for w in rs_) or (g["orden"] == "A" and g["verbo"] in orig and orig[g["verbo"]][:1].isupper()):
        return None                                  # habla de alguien concreto: lo resuelve el grafo de la conversación
    if g["art"] in ("el", "la") and any(e.startswith(("I:" + c + "@", "N:")) and d.get("clase") == c for e, d in nuc.E.items()):
        return None                                  # «el perro» es un perro concreto de la conversación
    verbo = _lema(g["verbo"], bool(g["modal"]))
    if not verbo or verbo in ("ser", "estar", "llamar", "gustar"):
        return None
    if _usuario_dijo(nuc, c, verbo) or (_tiene_propios(nuc, c) and g["orden"] == "B" and not g["modal"]):
        if g["orden"] == "A" or g["modal"]:
            return nuc._una("¿" + _cap(los(c)) + (" no " if g["neg"] else " ") + M.conjugar(verbo, "pres", "3p") + (" " + g["resto"] if g["resto"] else "") + "?")
        return None
    est = _estado(c, verbo, g["resto"])
    if est is None and verbo in VOCES and not g["resto"]:
        propia = [(cl, v) for cl, ng, v, rs in k["props"] if cl in [c] + ancestros(c) and sa(v) in VOCES and not ng]
        if propia:
            cl, v = propia[0]
            nuc.ult_just = {"pasos": [_frase_prop(cl, False, v, "")], "fabrica": True}
            return f"No, {_frase_prop(c, False, v, '')}."
    if est is None:
        if g["orden"] == "A" or g["modal"]:           # se reordena y decide el grafo (puede haberlo enseñado la persona)
            return nuc._una("¿" + _cap(los(c)) + (" no " if g["neg"] else " ") + M.conjugar(verbo, "pres", "3p") + (" " + g["resto"] if g["resto"] else "") + "?")
        return None
    d, neg, cl, v, rs = est
    pasos = ([f"{un(c)} es {un(x)}" for x in ancestros(c)[:d]][-1:] if d else []) + [_frase_prop(cl, neg, v, rs)]
    nuc.ult_just = {"pasos": pasos, "fabrica": True}
    nuc.ult_suj = None
    return ("No, " if neg else "Sí, ") + _frase_prop(cl if d and cl != c else c, neg, v, rs) + "."


def _cuales(nuc, c, verbo, resto, singular, neg=False):
    """«¿Qué animales vuelan?», «¿Qué animales no vuelan?»: clases más generales que cumplen, con sus excepciones."""
    k = kb()
    si, exc = [], []

    def baja(x, arriba):
        e = _estado(x, verbo, resto)
        val = None if e is None else ((not e[1]) != neg)
        if val is True and arriba is not True:
            si.append(x)
        if val is False and arriba is True:
            exc.append(x)
        for h in k["hijos"].get(x, []):
            baja(h, val)
    baja(c, None)
    if c in si:
        return None
    if not si:
        return None
    nuc.ult_just = {"pasos": [_frase_prop(x, neg, _estado(x, verbo, resto)[3], _estado(x, verbo, resto)[4]) for x in si[:3]], "fabrica": True}
    if singular and len(si) == 1:
        return f"{_cap(el(si[0]))}."
    txt = "Que yo sepa, " + nuc._lista([los(x) for x in si[:8]])
    dentro = [x for x in exc if any(a in si for a in ancestros(x))]
    if dentro:
        txt += (" (pero sí " if neg else " (pero no ") + nuc._lista([los(x) for x in dentro[:5]]) + ")"
    return txt + (". Hablo solo de las que conozco." if genero(c) == "f" else ". Hablo solo de los que conozco.")


_G = r"(familia|familiares|parientes|conocidos)"
_GR1 = re.compile(rf"^(?:quien(?:es)? (?:son|es|forman?|hay en|componen?)|que|dime quien(?:es)? (?:son|es)) (?:de )?(?:mi|mis) {_G}(?: tengo| conoces)?$|^(?:que|cual es mi) (familia|familiares|parientes)(?: tengo)?$|^quien(?:es)? (?:es|son) de mi (familia)$")
_GR2 = re.compile(rf"^(?:es )?([a-zñ]+) (?:es )?(?:de mi familia|familia mia|pariente mio|parienta mia|familiar mio|un familiar mio|de la familia|un pariente mio|una pariente mia|mi pariente|mi familiar)$")
_GR3 = re.compile(r"^(?:que relacion (?:tengo|tenemos|hay) (?:con|entre) (?:mi y )?([a-zñ]+)|que es ([a-zñ]+) (?:de mi|para mi|mio|mia)|quien es ([a-zñ]+) para mi|que (?:parentesco|relacion) (?:tiene|tengo) (?:con )?([a-zñ]+)(?: conmigo)?)$")
_GR4 = re.compile(r"^(?:tengo|tengo alguna) familia$")


def _de_grupo(nuc, grupo, y="U"):
    """[(x, relación)] de las personas unidas a y por alguna relación del grupo («familia»)."""
    k = kb()
    out, visto = [], set()
    for r in k["grupos"].get(grupo, []):
        try:
            ps = nuc.rels(r, y=y)
        except Exception:                                                      # noqa
            ps = []
        for q in ps:
            x = nuc.can(q["x"])
            if x in visto or x == y or x.startswith(("I:", "G:", "?")) and not nuc.E.get(x, {}).get("clase"):
                continue
            visto.add(x); out.append((x, r))
    return out


def _grupo_rel(nuc, n, p):
    if not ("?" in p or "¿" in p or n.startswith(("dime", "quien", "que"))):
        return None
    m = _GR1.match(n)
    if m or _GR4.match(n):
        fam = _de_grupo(nuc, "familia")
        if not fam:
            return {"respuesta": "No lo sé: todavía no me has hablado de tu familia.", "estado": "abst", "consultar": False, "tipo": "abst"}
        nuc.ult_just = {"pasos": [nuc._frase_rel(r, x, "U") for x, r in fam[:3]]}
        return "De tu familia conozco a " + nuc._lista([f"{nuc.disp(x)}" if x.startswith(("I:", "G:")) else f"{nuc.disp(x)} (tu {nuc._acento(nuc._rel_nombre(r, nuc.gen(x)))})" for x, r in fam[:8]]) + "."
    mp = re.match(r"^(?:es )?(mi|mis|tu) ([a-zñ]+) (?:es |son )?(?:de mi familia|de la familia|familia mia|mi familia|parte de mi familia|un familiar mio|una familiar mia|pariente mio|parienta mia)$", n)
    if mp:
        cl, g = nuc._canon_rel(sa(M.singular(mp.group(2))) if mp.group(1) == "mis" else mp.group(2))
        nom = mp.group(2)
        if cl in kb()["grupos"].get("familia", []) or cl in ("esposo",):
            return f"Sí: {'tus' if mp.group(1) == 'mis' else 'tu'} {nom} {'son' if mp.group(1) == 'mis' else 'es'} de tu familia."
        if cl in kb()["grupos"].get("conocido", []):
            return f"No: {'una' if g == 'f' else 'un'} {nom} no es de la familia, salvo que además seáis parientes."
        return None
    m = _GR2.match(n)
    if m and ("N:" + m.group(1) in nuc.E or "N:" + m.group(1) in nuc.eq):
        x = nuc.can("N:" + m.group(1))
        fam = [(a, r) for a, r in _de_grupo(nuc, "familia") if a == x]
        if fam:
            nuc.ult_just = {"pasos": [nuc._frase_rel(fam[0][1], x, "U")]}
            return f"Sí, {nuc._frase_rel(fam[0][1], x, 'U')}."
        otros = [(a, r) for a, r in _de_grupo(nuc, "conocido") if a == x]
        if otros:
            return f"Que yo sepa, no: {nuc._frase_rel(otros[0][1], x, 'U')}."
        return {"respuesta": f"No lo sé: no me has dicho qué relación tienes con {nuc.disp(x)}.", "estado": "abst", "consultar": False, "tipo": "abst"}
    m = _GR3.match(n)
    if m:
        nom = next(g for g in m.groups() if g)
        if "N:" + nom in nuc.E or "N:" + nom in nuc.eq:
            x = nuc.can("N:" + nom)
            todas = [(a, r) for g_ in ("familia", "pareja", "conocido") for a, r in _de_grupo(nuc, g_) if a == x]
            if todas:
                nuc.ult_just = {"pasos": [nuc._frase_rel(todas[0][1], x, "U")]}
                return _cap(nuc._frase_rel(todas[0][1], x, "U")) + "."
            return {"respuesta": f"No lo sé: no me has dicho qué relación tienes con {nuc.disp(x)}.", "estado": "abst", "consultar": False, "tipo": "abst"}
    return None



# ====================================================================== 2.12 · «¿Un X es un Y?» con la jerarquía de fábrica
_GRUPOS = {"ser vivo": "vivo", "objeto": "cosa", "material": "cosa", "elemento natural": "cosa", "medicamento": "cosa", "dinero": "cosa", "alimento": "cosa",
           "lugar": "lugar", "evento": "abs", "tiempo": "abs", "enfermedad": "abs", "emocion": "abs", "actitud": "abs", "color": "abs", "forma": "abs",
           "idioma": "abs", "asignatura": "abs", "deporte": "abs", "actividad": "abs", "arte": "abs", "organizacion": "abs", "festividad": "abs",
           "fenomeno": "abs", "medio de comunicacion": "abs", "sentido": "abs", "estacion": "abs",
           # 2.14: raíces nuevas (abstractas, astros, seres imaginarios, sustancias)
           "accion": "abs", "idea": "abs", "informacion": "abs", "cualidad": "abs", "magnitud": "abs", "situacion": "abs", "resultado": "abs",
           "relacion": "abs", "acuerdo": "abs", "norma": "abs", "cargo": "abs", "unidad de medida": "abs", "signo": "abs", "texto": "abs",
           "imagen": "abs", "obra artistica": "abs", "grupo": "abs", "calculo": "abs", "programa": "abs",
           "astro": "astro", "ser imaginario": "imaginario", "sustancia": "cosa", "bebida": "cosa"}
_ES_UN = re.compile(r"^(?:(?:es|son)\s+)?(?:un|una|unos|unas|el|la|los|las)\s+(.+?)\s+(?:es|son|puede ser|pueden ser|tambien es|es tambien)\s+(?:(?:un|una|unos|unas)\s+)?(.+)$")


def _grupos_de(c):
    out = set()
    for a in [c] + list(ancestros(c)):
        if a in _GRUPOS:
            out.add(_GRUPOS[a])
    return out


def _clase_de_texto(t):
    t = t.strip()
    for cand in (t, M.singular(t) if t.endswith("s") else t, " ".join(M.singular(w) for w in t.split())):
        c = _kb_clase(cand)
        if c and (kb()["isa"].get(c) or kb()["hijos"].get(c)):
            return c
    return None


_LEX_ANT = {}


def antonimos_lexico(w):
    """2.14: antónimos de una palabra en el léxico MCR del proyecto (data/lexico_es.json), solo de una palabra y de la misma categoría."""
    if not _LEX_ANT:
        import json, os
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "lexico_es.json")
        try:
            L = json.load(open(ruta, encoding="utf-8"))
        except (OSError, ValueError):
            _LEX_ANT["_"] = {}
            return []
        syn, pos, ant = L["syn"], L["pos"], L["ant"]
        d = {}
        for i, js in ant.items():
            for j in js:
                for a in syn.get(i, []):
                    for b in syn.get(str(j), []):
                        if " " not in a and " " not in b and pos.get(i) == pos.get(str(j)):
                            d.setdefault(sa(a), []).append(b)
        _LEX_ANT["_"] = d
    return list(dict.fromkeys(_LEX_ANT["_"].get(sa(w), [])))


def sinonimos_lexico(w, n=5):
    """2.16: otras palabras para lo mismo, del léxico MCR del proyecto (solo palabras sueltas)."""
    import json, os
    if "_syn" not in _LEX_ANT:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "lexico_es.json")
        d = {}
        try:
            L = json.load(open(ruta, encoding="utf-8"))
            for i, ws in L["syn"].items():
                ws1 = [x for x in ws if " " not in x and "_" not in x]
                for a in ws1:
                    d.setdefault(sa(a), [])
                    d[sa(a)] += [b for b in ws1 if sa(b) != sa(a) and b not in d[sa(a)]]
        except (OSError, ValueError, KeyError):
            pass
        _LEX_ANT["_syn"] = d
    return _LEX_ANT["_syn"].get(sa(w), [])[:n]


def _un_rel(t):
    w = M.singular(t.strip().split()[-1])
    return ("una " if w.endswith("a") else "un ") + w


def _padres_aprendidos(nuc, x):
    """[(clase, frase)] de lo leído o explicado: «El cartón es un papel grueso», «La lonja es el mercado donde…», «Los murciélagos son los
    únicos mamíferos que…». Solo frases afirmativas cuyo sujeto es exactamente x."""
    out = []
    frases = []
    for t in (getattr(nuc, "usuario", {}).get("leido") or []):
        frases += t.get("frases") or []
    frases += [f["src"] for f in getattr(nuc, "F", []) if f.get("src") and (f.get("leido") or f.get("expo"))]
    try:
        from . import compuestos as _C
        dec = lambda t: _C.decodifica(nuc, t)
    except Exception:                                    # noqa
        dec = lambda t: t
    for fr in dict.fromkeys(frases):
        n = sa(dec(fr).lower()).strip(" .")
        m = re.match(r"^(?:(?:el|la|los|las|un|una)\s+)?([a-zñ]+(?: [a-zñ]+)?)\s+(?:es|son)\s+(?:en realidad\s+)?(?:(?:un|una|el|la|los|las|unos|unas)\s+)?(?:unic[oa]s?\s+|primer[oa]?s?\s+)?([a-zñ]+)\b", n)
        if not m or re.search(r"\bno\s+(?:es|son)\b", n):
            continue
        suj = m.group(1)
        if sa(M.singular(suj)) != x and suj != x and _clase_de_texto(suj) != x:
            continue
        cand = m.group(2)
        padre = _clase_de_texto(cand) or sa(M.singular(cand))
        if padre and padre != x and (_kb_clase(padre) or any(g.get("s") == "K:" + padre for g in getattr(nuc, "F", []))):
            out.append((padre, fr.strip()))
    return out


def _es_un(nuc, n, p=""):
    m = _ES_UN.match(n)
    if not m:
        return None
    x, y = _clase_de_texto(m.group(1)), _clase_de_texto(m.group(2))
    if not x and y:
        # 2.14: las palabras de relación («novio», «hermano», «suegra») no están en la taxonomía (son relaciones), pero son personas
        w = sa(M.singular(m.group(1).strip().split()[-1]))
        rel = {sa(r) for g in kb()["grupos"].values() for r in g}
        if w in rel or (w.endswith("a") and w[:-1] + "o" in rel):
            if y in ("persona", "ser vivo"):
                nuc.ult_just = {"pasos": [f"«{w}» es una relación entre personas"], "fabrica": True}
                return f"Sí, {_un_rel(m.group(1))} es {un(y)}."
            if _grupos_de(y) and "vivo" not in _grupos_de(y):
                return f"No, {_un_rel(m.group(1))} es una persona."
            return None
    if not x or not y or x == y:
        return None
    if "color" in ancestros(y) or y in ("color",) or "forma" in ancestros(y):
        return None                                      # «¿Los plátanos son azules?»: es un adjetivo de color, no una clase
    try:
        # 2.22: lo leído o explicado manda sobre la fábrica: «La lonja es el mercado donde…» -> la lonja es un mercado; y se encadena con
        # lo demás: el vampiro es un murciélago (leído), el murciélago es un mamífero (leído), el mamífero es un animal (fábrica)
        visto, cola, cadena = {x}, [(x, [])], None
        while cola and cadena is None and len(visto) < 12:
            c0, camino = cola.pop(0)
            for padre, frase in _padres_aprendidos(nuc, c0):
                if padre in visto:
                    continue
                visto.add(padre)
                if padre == y or y in ancestros(padre):
                    cadena = camino + [frase]
                    break
                cola.append((padre, camino + [frase]))
        if cadena:
            nuc.ult_just = {"dicho": cadena}
            f0 = cadena[0]
            return f"Sí: según lo que he aprendido, {f0[:1].lower() + f0[1:].rstrip('.')}." + (f" Lo deduzco encadenando {len(cadena)} cosas aprendidas." if len(cadena) > 1 else "")
    except Exception:                                    # noqa
        pass
    if p and any(k_.startswith("N:") and sa(k_[2:]) == x for k_ in nuc.E):
        return None                                      # un nombre propio de la charla no es la clase
    anc = ancestros(x)
    if y in anc:
        cad = [x]
        while cad[-1] != y:                              # la cadena más corta hacia arriba
            sig = next((a for a in kb()["isa"].get(cad[-1], []) if a == y or y in ancestros(a)), None)
            if sig is None or sig in cad:
                break
            cad.append(sig)
        pasos = [f"{un(cad[i])} es {un(cad[i + 1])}" for i in range(len(cad) - 1)]
        nuc.ult_just = {"pasos": pasos, "fabrica": True}
        extra = (" Lo deduzco porque " + nuc._lista(pasos) + ".") if len(pasos) > 1 else ""
        return f"Sí, {un(x)} es {un(y)}.{extra}"
    if x in ancestros(y):
        return f"No siempre: {un(y)} es {un(x)}, pero no al revés."
    gx, gy = _grupos_de(x), _grupos_de(y)
    p0 = kb()["isa"].get(x, [None])[0]
    if gx and gy and not (gx & gy):
        nuc.ult_just = {"pasos": [f"{un(x)} es {un(p0)}"] if p0 else [], "fabrica": True}
        return f"No, {un(x)} es {un(p0)}." if p0 else None
    for raiz in ("ser vivo", "animal", "planta"):        # animal / planta; mamífero / ave / pez…: ramas que no se cruzan
        hijos = set(kb()["hijos"].get(raiz, [])) - {"persona", "profesional"}
        rx = {h for h in hijos if h == x or h in anc}
        ry = {h for h in hijos if h == y or h in ancestros(y)}
        if rx and ry and not (rx & ry) and len(rx) == 1:
            r0 = next(iter(rx))
            nuc.ult_just = {"pasos": [f"{un(x)} es {un(r0)}"], "fabrica": True}
            return f"No, {un(x)} es {un(r0)}, no {un(y)}."
    func = {"recipiente", "utensilio", "herramienta", "aparato", "vajilla", "cubierto", "material de oficina", "objeto de aseo", "accesorio",
            "instrumento de escritura", "producto de limpieza", "material"}
    if p0 and ({x, p0, *anc} & func) and ({y, *ancestros(y)} & func):
        # 2.14: las clases de objetos por su función se solapan (una tetera es utensilio y recipiente): no se niega por ser hermanas
        return f"No lo sé seguro: de fábrica sé que {un(x)} es {un(p0)}, pero no si es {un(y)}."
    return None                                          # 2.14: sin certeza, deciden las reglas de después (hermanas de clase, propiedades…)
