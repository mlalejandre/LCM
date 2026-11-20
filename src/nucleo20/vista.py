"""LCM 2.3 · lo que el LCM ve, dentro de la conversación.

Cada imagen se convierte en un referente del núcleo (color, forma, color de la figura y del fondo, y lo que la persona
diga que es). Con él se resuelven «esto», «esta imagen», «este color», «la figura», «el fondo» y las preguntas sin sujeto
que siguen a una imagen («¿Es azul?», «¿Qué forma tiene?»), y se cruza con los conceptos de fábrica:
«¿Qué frutas son de este color?», «¿Podría ser un plátano?», «Esto es una fresa», «Luna es de este color».
La visión es por reglas (colores y formas simples): lo que no reconoce, lo dice.
"""
from __future__ import annotations

import re

from . import conceptos as K
from . import morfo as M
from .morfo import sa

NOMBRE = {"ROJO": "rojo", "VERDE": "verde", "AZUL": "azul", "AMARILLO": "amarillo", "BLANCO": "blanco", "NEGRO": "negro", "NARANJA": "naranja",
          "ROSA": "rosa", "MORADO": "morado", "MARRON": "marrón", "GRIS": "gris"}
FORMA = {"CIRCULO": "circulo", "CUADRADO": "cuadrado", "RECTANGULO": "rectangulo", "OVALO": "ovalo", "TRIANGULO": "triangulo", "ESTRELLA": "estrella"}
# 2.10: posiciones dentro de una imagen con varias figuras
POS_IMG = {"sobre": "arriba", "bajo": "abajo", "izquierda": "a la izquierda", "derecha": "a la derecha", "dentro": "dentro"}
REL_TXT = {"sobre": "encima de", "bajo": "debajo de", "izquierda": "a la izquierda de", "derecha": "a la derecha de", "dentro": "dentro de"}
_INVAR = {"naranja", "rosa", "marron", "gris", "azul", "verde", "turquesa", "beige", "violeta"}
_LADOS = {"triangulo": 3, "cuadrado": 4, "rectangulo": 4, "rombo": 4, "pentagono": 5, "hexagono": 6}
_DEIC = r"(?:esto|eso|esta imagen|esa imagen|la imagen|esta foto|la foto|esta figura|la figura|lo que ves|este dibujo|el dibujo|este|esta)"


def color_adj(c, g="m", pl=False):
    c = sa(c)
    if c in _INVAR:
        base = {"marron": "marrón"}.get(c, c)
        return (base + ("es" if base.endswith(("n", "l", "s")) and pl else ("s" if pl else ""))).replace("marrónes", "marrones").replace("griss", "grises").replace("azuls", "azules")
    return M.concuerda(c, g, pl)


def ver(nuc, visto, forma=None, escena=None):
    """Registra la imagen como referente del núcleo y devuelve su descripción."""
    forma = forma or {}
    escena = escena or {}
    n = len(getattr(nuc, "vistas", [])) + 1
    v = {"id": f"V:imagen{n}", "color": sa(NOMBRE.get(visto.get("concepto") or "", "")) or None,
         "forma": FORMA.get(forma.get("forma") or ""), "color_figura": sa(NOMBRE.get(forma.get("color_figura") or "", "")) or None,
         "color_fondo": sa(NOMBRE.get(forma.get("color_fondo") or "", "")) or None, "hay_figura": bool(forma.get("color_figura") or forma.get("relleno")),
         "etiqueta": None, "ent": None, "turno": nuc.turno}
    if v["hay_figura"] and not forma.get("forma"):
        v["forma"] = None
    if len(escena.get("figuras") or []) >= 2:
        v["figuras"] = [{"forma": FORMA.get(f.get("forma") or ""), "color": sa(NOMBRE.get(f.get("color_figura") or "", "")) or None} for f in escena["figuras"]]
        v["rels"] = list(escena.get("relaciones") or [])
        v["hay_figura"], v["forma"], v["color_figura"], v["color"] = True, None, None, None
        v["color_fondo"] = sa(NOMBRE.get(escena.get("fondo") or "", "")) or v.get("color_fondo")
    nuc.vistas = (getattr(nuc, "vistas", []) + [v])[-6:]
    nuc.vista = v
    nuc.foco_vista = True
    nuc._vista_usada = True
    return describe(v)


def color_de(v):
    """Color con el que se identifica la imagen: el de la figura si la hay, si no el de toda la imagen."""
    return v.get("color_figura") or v.get("color")


def nombra_fig(f, art="un"):
    if f.get("forma"):
        base = K.un(f["forma"]) if art == "un" else K.el(f["forma"])
        return base + (" " + color_adj(f["color"], K.genero(f["forma"])) if f.get("color") else "")
    return ("una figura" if art == "un" else "la figura") + (f" {color_adj(f['color'], 'f')}" if f.get("color") else "")


def _pos_de(v, i):
    """Dónde está la figura i dentro de la imagen («arriba», «a la izquierda»…), si es una posición extrema clara."""
    rs = [r for (a, r, b) in v.get("rels", []) if a == i]
    for r in ("sobre", "bajo", "izquierda", "derecha"):
        if rs and all(x == r for x in rs) and len(rs) == len(v["figuras"]) - 1:
            return POS_IMG[r]
    return None


def describe(v):
    if v.get("figuras"):
        fs = v["figuras"]
        trozos = []
        for i, f in enumerate(fs):
            pos = _pos_de(v, i)
            trozos.append(nombra_fig(f) + (f" {pos}" if pos else ""))
        num = {2: "dos", 3: "tres", 4: "cuatro"}.get(len(fs), str(len(fs)))
        txt = f"Veo {num} figuras: " + ", ".join(trozos[:-1]) + " y " + trozos[-1]
        if any(not f.get("forma") for f in fs):
            txt += ". De alguna no reconozco la forma"
        return txt + "."
    if v.get("hay_figura"):
        cf, fo = v.get("color_figura"), v.get("color_fondo")
        if v.get("forma"):
            fig = K.un(v["forma"]) + (" " + color_adj(cf, K.genero(v["forma"])) if cf else "")
            return f"Veo {fig}" + (f" sobre fondo {color_adj(fo)}." if fo else ".")
        return ("Veo una figura" + (f" de color {color_adj(cf)}" if cf else "") + (f" sobre fondo {color_adj(fo)}" if fo else "")
                + ", pero no reconozco su forma: solo distingo círculos, óvalos, cuadrados, rectángulos, triángulos y estrellas.")
    if v.get("color"):
        return f"Veo una imagen de color {color_adj(v['color'])}."
    return "No lo sé: no he podido identificar ni el color ni la forma de esta imagen (es mixta o el tono está fuera de los que distingo)."


def _ok(r, tipo="resp"):
    return {"respuesta": r, "estado": "ok", "consultar": False, "tipo": tipo}


def _abst(r):
    return {"respuesta": r, "estado": "abst", "consultar": False, "tipo": "abst"}


def reescribe(nuc, p):
    """«X es de este color» -> «X es rojo» (con el color de la imagen en foco)."""
    v = getattr(nuc, "vista", None)
    if not v or not color_de(v):
        return p
    p = re.sub(r"\b(tienen|tiene)\s+(?:este|ese)\s+(?:mismo\s+)?color\b", lambda m: ("son " if m.group(1) == "tienen" else "es ") + "de este color", p, flags=re.I)
    def _adj(m_):
        prev = p[:m_.start()].split()[-2:]          # «quiero las paredes de ese color» -> «azules»
        if len(prev) == 2 and sa(prev[0].lower()) in ("los", "las", "mis", "tus", "sus", "unos", "unas", "estos", "estas"):
            return color_adj(color_de(v), "f" if sa(prev[0].lower()) in ("las", "unas", "estas") else M.genero_sust(sa(M.singular(prev[1].lower()))), True)
        return color_adj(color_de(v))
    q = re.sub(r"\b(?:de|del)\s+(?:este|ese|el)\s+(?:mismo\s+)?(?:color|tono)(?!\s+(?:que|de)\b)|\bdel color de (?:la|esta|esa) (?:imagen|foto)\b",
               _adj, p, flags=re.I)
    if q != p:
        nuc._vista_usada = True
        nuc.foco_vista = True
    return q


def _clase_kb(txt):
    return K._kb_clase(re.sub(r"^(?:un|una|el|la|los|las)\s+", "", txt.strip()))


def _colores_tipicos(c):
    """Colores que la base de fábrica asigna a la clase c (o a la capa más cercana que los tenga)."""
    k = K.kb()
    for cl in [c] + K.ancestros(c):
        cs = [sa(M.masc(rs.split()[-1])) for x, neg, v, rs in k["props"] if x == cl and not neg and v == "ser" and rs and sa(M.masc(rs.split()[-1])) in NOMBRES_SA]
        if cs:
            return cl, cs
    return None, []


NOMBRES_SA = {sa(x) for x in NOMBRE.values()} | {"dorado", "plateado", "violeta", "beige", "turquesa"}


def responder(nuc, p, n, es_preg):
    """Respuesta sobre la imagen en foco, o None."""
    v = getattr(nuc, "vista", None)
    if v is None:
        return None
    foco = getattr(nuc, "foco_vista", False)
    deic = re.search(rf"\b{_DEIC}\b", n) is not None
    if not (foco or deic):
        return None
    col = color_de(v)
    r = _responde(nuc, v, p, n, es_preg, foco, deic, col)
    if r is not None:
        nuc.foco_vista = True
        nuc._vista_usada = True
    return r


def colores_que_veo(n):
    if re.match(r"^(?:que|cuales?) (?:colores|formas|figuras) (?:sabes (?:ver|distinguir|reconocer)|distingues|reconoces|ves|puedes (?:ver|distinguir|reconocer))$", n):
        cs = [color_adj(sa(x)) for x in NOMBRE.values()]
        return _ok("Distingo estos colores: " + ", ".join(cs[:-1]) + " y " + cs[-1] + ". Y estas formas simples: círculos, óvalos, cuadrados, rectángulos, triángulos y estrellas. Si hay varias figuras, también te digo cómo están colocadas.")
    return None


def _responde(nuc, v, p, n, es_preg, foco, deic, col):
    n0 = n
    n = re.sub(r"^(?:y|pues|oye|vale|bueno)\s+", "", n)
    if v.get("figuras") and es_preg:
        r = _escena(nuc, v, n)
        if r is not None:
            return r
    if re.match(r"^(?:mira|fijate en|observa)?\s*(?:este|el|esta|la) (?:dibujo|imagen|foto)$|^(?:y )?en (?:este|esta)(?: otro| otra)?(?: dibujo| imagen| foto)?$|^y (?:este|esta)(?: otro| otra)? (?:dibujo|imagen|foto)$|^que (?:hay|ves) en (?:este|el) dibujo$", n) \
            and v["turno"] >= nuc.turno - 1:
        return _ok(describe(v)) if (v.get("color") or v.get("forma") or v.get("figuras")) else _abst(describe(v))
    if es_preg and re.match(r"^cuant[ao]s (?:figuras|formas|cosas|objetos) (?:hay|ves|tiene|aparecen)", n):
        if v.get("figuras"):
            return _ok(describe(v))
        if v.get("hay_figura"):
            return _ok("Veo una sola: " + describe(v)[4:]) if v.get("forma") else _ok("Veo una sola figura" + (f" {color_adj(v['color_figura'], 'f')}" if v.get("color_figura") else "") + ", pero no reconozco su forma.")
        return _ok("Ninguna: la imagen es de un solo color" + (f" ({color_adj(v['color'])})." if v.get("color") else "."))
    if not es_preg and col and not getattr(nuc, "_en_presenta", False):
        nuc._en_presenta = True
        try:
            r = _presenta(nuc, v, p, re.sub(r"^mira\s+", "", n), col)
        finally:
            nuc._en_presenta = False
        if r is not None:
            return r
    # --- qué ves / qué es esto / mira esta imagen
    if re.match(r"^(?:que ves|que hay en (?:la|esta) (?:imagen|foto)|describe(?:me)? (?:la|esta) (?:imagen|foto)|que (?:ves|hay) aqui|mira(?: esta| la)? (?:imagen|foto|esto)|que es esto|que es esta (?:imagen|figura|cosa)|que forma (?:es esta|tiene|ves)|que figura (?:es esta|ves|es)|que forma es)$", n):
        if n.startswith(("que es esto", "que es esta")) and v.get("etiqueta"):
            return _ok(f"Me has dicho que es {K.un(v['etiqueta'])}.")
        if n.startswith(("que forma", "que figura")):
            if v.get("forma"):
                return _ok(f"Es {K.un(v['forma'])}.")
            if v.get("hay_figura"):
                return _abst(describe(v))
            return _abst("No veo ninguna figura: la imagen es de un solo color" + (f" ({color_adj(v['color'])})." if v.get("color") else "."))
        if n.startswith(("que es esto", "que es esta")):
            d = describe(v)
            return _abst("No sé qué es: " + d[0].lower() + d[1:] if not v.get("forma") else d)
        return _ok(describe(v)) if (v.get("color") or v.get("forma")) else _abst(describe(v))
    if n0 in ("y este", "y esta", "y esto", "y ahora", "esta", "este", "esto", "ahora", "y la imagen", "y esta otra", "y este otro", "y esta otra imagen", "y esta otra foto", "y la otra", "y esta foto", "y esta imagen") and (foco or deic) and v["turno"] >= nuc.turno - 1:
        pv = getattr(nuc, "_preg_vista", None)
        if pv and pv[0] == "color_de":
            return _responde(nuc, v, "¿Este es el color de " + pv[1] + "?", "este es el color de " + sa(pv[1]), True, foco, deic, col)
        return _ok(describe(v)) if (v.get("color") or v.get("forma")) else _abst(describe(v))
    # --- color
    if re.match(r"^(?:de que color es|que color (?:es|tiene|ves|predomina|domina|hay)|cual es (?:el|su) color(?: predominante| principal)?|que color es el que predomina)(?: (?:la imagen|esta imagen|esto|este|esta|la foto|esta foto|en la imagen|en la foto))?$", n) and (
            v.get("hay_figura") or not re.search(r"\b(?:este|esta)$", n)):
        if not col:
            return _abst(describe(v))
        if v.get("hay_figura") and v.get("color_fondo"):
            return _ok(f"La figura es {color_adj(col, 'f')} y el fondo {color_adj(v['color_fondo'])}.")
        return _ok(f"Es {color_adj(col)}.")
    if re.match(r"^(?:de que color es|que color tiene) (?:la|esta) figura$", n):
        return _ok(f"La figura es {color_adj(col, 'f')}.") if col else _abst(describe(v))
    if re.match(r"^(?:y )?(?:(?:de que color es|que color tiene) )?el fondo$", n) or n in ("el fondo", "y el fondo"):
        return _ok(f"El fondo es {color_adj(v['color_fondo'])}.") if v.get("color_fondo") else _abst("No lo sé: no distingo un fondo de otro color.")
    m = re.match(rf"^(?:(?:es|esto es|la imagen es|la figura es|el fondo es) )?(?:de color )?([a-zñ]+)$", n)
    if es_preg and m and (sa(M.masc(m.group(1))) in NOMBRES_SA or m.group(1) in NOMBRES_SA) and (n.startswith(("es ", "esto ", "la imagen", "la figura", "el fondo")) or deic):
        c = sa(M.masc(m.group(1))) if sa(M.masc(m.group(1))) in NOMBRES_SA else m.group(1)
        real = v.get("color_fondo") if "fondo" in n else col
        if not real:
            return _abst("No lo sé: no he podido identificar el color.")
        if c == real:
            return _ok(f"Sí, es {color_adj(real)}.")
        return _ok(f"No, es {color_adj(real)}.")
    # --- forma
    m = re.match(r"^(?:es|esto es|la figura es) (?:un|una) ([a-zñ]+)$", n)
    if es_preg and m:
        c = _clase_kb(m.group(1))
        if c and c in ("forma", "poligono") or (c and "forma" in K.ancestros(c)):
            if not v.get("forma"):
                return _abst("No lo sé: no reconozco la forma de esta figura." if v.get("hay_figura") else "No veo ninguna figura en la imagen.")
            fo = v["forma"]
            if c == fo or c in K.ancestros(fo):
                return _ok(f"Sí, es {K.un(fo)}" + (f", y {K.un(fo)} es {K.un(c)}." if c != fo else "."))
            if fo in K.ancestros(c):
                return _abst(f"No lo sé seguro: es {K.un(fo)}.")
            return _ok(f"No, es {K.un(fo)}" + (f"; {K.un(fo)} no es {K.un(c)}." if c in ("poligono",) else "."))
        if c and v.get("etiqueta"):
            et = v["etiqueta"]
            if c == et or c in K.ancestros(et):
                return _ok(f"Sí: me has dicho que es {K.un(et)}" + (f", y {K.un(et)} es {K.un(c)}." if c != et else "."))
            if (K.kb()["isa"].get(c) or K.kb()["hijos"].get(c)) and et in K.kb()["isa"]:
                return _ok(f"No: me has dicho que es {K.un(et)}, y {K.un(et)} no es {K.un(c)}.")
        if c and not v.get("etiqueta"):
            return _podria(v, c, col)
    m = re.match(r"^(?:podria|puede|podra) ser (?:un|una) ([a-zñ]+)$|^(?:esto )?(?:podria|puede) ser (?:un|una) ([a-zñ]+)$|^(?:sera|es esto) (?:un|una) ([a-zñ]+)$", n)
    if m:
        c = _clase_kb(next(g for g in m.groups() if g))
        if c:
            return _podria(v, c, col)
        return _abst("No lo sé: no conozco eso.")
    m = re.match(r"^tiene (\w+) lados$", n)
    if m and es_preg and M.numero(m.group(1)) is not None:
        fo = v.get("forma")
        if not fo:
            return _abst("No lo sé: no reconozco ninguna forma en la imagen.")
        real = _LADOS.get(fo, 0)
        if real == M.numero(m.group(1)):
            return _ok(f"Sí, tiene {M.num_pal(real)} lados: es {K.un(fo)}.")
        return _ok(f"No, tiene {M.num_pal(real)}: es {K.un(fo)}." if real else f"No: es {K.un(fo)}, que no tiene lados rectos.")
    if re.match(r"^cuantos lados tiene(?: (?:esto|la figura|esta figura))?$", n):
        fo = v.get("forma")
        if not fo:
            return _abst("No lo sé: no reconozco ninguna forma en la imagen.")
        if fo in _LADOS:
            return _ok(f"Tiene {M.num_pal(_LADOS[fo])} lados: es {K.un(fo)}." if hasattr(M, "num_pal") else f"Tiene {_LADOS[fo]} lados.")
        return _ok(f"Ninguno: es {K.un(fo)}, que no tiene lados rectos.")
    # --- comparación con un color dicho
    m = re.match(r"^(?:es|esto es|tiene) (?:del mismo color|el mismo color) que (.+)$|^(?:este|esto) es el color de (.+)$|^(?:es|este es) (?:del )?color de (.+)$", n)
    if m:
        txt = next(g for g in m.groups() if g)
        orig = p.strip(" ¿?.!").split()[-len(txt.split()):]
        e = nuc._q_ent(nuc._sn_de(" ".join(orig))) if hasattr(nuc, "_sn_de") else None
        cs = _colores_ent(nuc, e)
        nuc._preg_vista = ("color_de", " ".join(orig))
        if e is None or str(e).startswith("?") or not cs:
            return _abst(f"No lo sé: no me has dicho de qué color es {' '.join(orig)}.")
        if not col:
            return _abst("No lo sé: no he podido identificar el color de la imagen.")
        quien = nuc.disp(e)
        g = nuc.gen(e)
        if col in cs:
            return _ok(f"Sí, {quien} es {color_adj(col, g)}.")
        return _ok(f"No: {quien} es {color_adj(cs[0], g)} y esto es {color_adj(col)}.")
    # --- «Esto es una fresa» / «Esta es Luna»
    m = re.match(r"^(?:esto|esta|este|eso|la imagen|la foto|esta imagen|esta foto) es (?:un|una) ([a-zñ]+)$", n)
    if m and not es_preg:
        c = _clase_kb(m.group(1))
        if not c:
            return None
        v["etiqueta"] = c
        nuc._ent("K:" + c, clase=c, gen=K.genero(c))
        nuc.ult_suj = "K:" + c
        cl, cs = _colores_tipicos(c)
        if col and cs and col not in cs:
            return _ok(f"Entendido, aunque me extraña: {K.suj(cl)} suelen ser {_lista_col(cs, K.genero(cl), True)} y esto es {color_adj(col)}.", "ack")
        return _ok(f"Entendido: es {K.un(c)}" + (f", de color {color_adj(col)}." if col else "."), "ack")
    return None


_FORMA_ADJ = {"circulo": "redondo", "cuadrado": "cuadrado", "triangulo": "triangular", "rectangulo": "rectangular", "ovalo": "ovalado"}


def _orig(p, k):
    """Las k últimas palabras del texto original (con mayúsculas y tildes)."""
    return " ".join(p.strip(" ¿?.!").split()[-k:])


def sa_orig_lower(p):
    """El texto original en minúsculas, conservando las tildes (para distinguir «está» de «esta»)."""
    return p.lower()


def _presenta(nuc, v, p, n, col):
    """Lo que la persona dice de la imagen, como un dato de la conversación:
       «Este es el color de las cortinas»  -> «Las cortinas son amarillas»
       «Este es el color que le gusta a Rocío» -> «A Rocío le gusta el verde»
       «Esta es la alfombra que he comprado» -> «La alfombra es roja y redonda. He comprado la alfombra»"""
    frases = []
    m = re.match(r"^(?:este|esto|ese) es el color (?:de|del) (.+)$", n)
    if m:
        sn = _orig(p, len(m.group(1).split()))
        if n.split()[-len(m.group(1).split())] == "del" or m.group(0).split()[4] == "del":
            sn = "el " + sn
        art = sa(sn.split()[0])
        pl, g = art in ("los", "las", "mis", "tus", "sus"), ("f" if art in ("la", "las") else ("m" if art in ("el", "los") else M.genero_sust(sa(sn.split()[-1]))))
        frases.append(f"{sn[:1].upper() + sn[1:]} {'son' if pl else 'es'} {color_adj(col, g, pl)}.")
    if not frases and re.match(r"^(?:es (?:este|esta|esto|asi)|(?:este|esta|esto) es|aqui (?:esta|lo tienes|la tienes)|asi es|mira como (?:ha )?(?:quedado|queda))$", n):
        # «(He pintado un cuadro.) Es este» con la foto: lo último que se nombró es lo que se ve
        um = getattr(nuc, "ult_marco", None) or {}
        e_v = um.get("obj") if um.get("obj") and not nuc.es_persona(um["obj"]) else None
        if e_v and um.get("obj_disp"):
            sn = re.sub(r"^(?:un|una|unos|unas)\s+", lambda x: {"un": "el ", "una": "la ", "unos": "los ", "unas": "las "}[x.group(0).strip()], um["obj_disp"])
            from .nucleo import cambia_persona as _cp
            sn = _cp(sn)
            if not re.match(r"^(?:el|la|los|las|mi|mis|tu|tus)\s", sn):
                sn = ("la " if nuc.gen(nuc.can(e_v)) == "f" else "el ") + sn
            g = nuc.gen(nuc.can(e_v)) or "m"; pl = bool(um.get("pl_obj"))
            adj = color_adj(col, g, pl)
            fo = v.get("forma") if v.get("hay_figura") else None
            frases.append(f"{sn[:1].upper() + sn[1:]} {'son' if pl else 'es'} {adj}.")
            if fo in _FORMA_ADJ:                        # la forma en otra frase: «naranja y redondo» no se analiza bien
                frases.append(f"{sn[:1].upper() + sn[1:]} {'son' if pl else 'es'} {M.concuerda(_FORMA_ADJ[fo], g, pl)}.")
    m = None if frases else re.match(r"^(?:esta|este|esto|aqui esta|aqui tienes a) (?:es )?([a-zñ]+)$", n)
    if m:                                               # «Esta es Mimi» (con la foto): Mimi es de ese color
        nom = _orig(p, 1)
        if nom[:1].isupper() and ("N:" + sa(nom.lower())) in nuc.E:
            g_n = nuc.gen("N:" + sa(nom.lower())) or "m"
            frases.append(f"{nom} es {color_adj(col, g_n)}.")
    m = None if frases else re.match(r"^(?:(?:este|esto|ese) )?es (?:el|su) color (?:favorito|preferido) de (.+)$", n)
    if m:
        frases.append(f"El color favorito de {_orig(p, len(m.group(1).split()))} es el {color_adj(col)}.")
    m = None if frases else re.match(r"^(?:(?:este|esto|ese) )?es mi color (?:favorito|preferido)$", n)
    if m:
        frases.append(f"Mi color favorito es el {color_adj(col)}.")
    m = None if frases else re.match(r"^(?:este|esto|ese) es el (?:color )?que (?:le|les) (gusta|encanta)(?: mas)? a (.+)$", n)
    if m:
        frases.append(f"A {_orig(p, len(m.group(2).split()))} le {m.group(1)} el {color_adj(col)}.")
    m = None if frases else re.match(r"^(?:este|esto|ese) es el (?:color )?que (?:me|nos) (gusta|encanta)(?: mas)?(?: a mi)?$", n)
    if m:
        frases.append(f"Me {m.group(1)} el {color_adj(col)}.")
    m = None if frases else re.match(r"^(?:esta|este|esto|estas|estos|aqui tienes|aqui esta|aqui estan) (?:es |son )?(el|la|los|las|mi|mis) ([a-zñ]+(?: (?:nuevo|nueva|nuevos|nuevas))?)(?:,? que (.+))?$", n)
    c_m = K._kb_clase(m.group(2).split()[0]) if m else None
    if m and not (c_m and ("persona" in K.ancestros(c_m) or c_m == "persona")) and m.group(2).split()[0] not in ("imagen", "foto", "figura", "dibujo", "color"):
        nw = len(m.group(2).split()) + 1
        toks = p.strip(" ¿?.!").split()
        k0 = next((i for i, w in enumerate(toks) if sa(w.lower()) == m.group(1)), None)
        if k0 is not None:
            sn = " ".join(toks[k0:k0 + nw])
            pl, g = m.group(1) in ("los", "las", "mis"), ("f" if m.group(1) in ("la", "las") else ("m" if m.group(1) in ("el", "los") else M.genero_sust(m.group(2).split()[0])))
            adj = color_adj(col, g, pl)
            fo = v.get("forma") if v.get("hay_figura") else None
            if fo in _FORMA_ADJ and col not in ("naranja", "rosa", "violeta", "turquesa", "beige", "lila"):
                adj += " y " + M.concuerda(_FORMA_ADJ[fo], g, pl)
            rel0 = (m.group(3) or "").split()
            if m.group(1) in ("el", "la", "los", "las") and any(x[2] in ("1s", "1p") for w in rel0[:3] for x in M.analizar(sa(w)) if x[1] in ("pres", "pret", "imp")):
                sn = ("mis " if pl else "mi ") + " ".join(sn.split()[1:])     # «la alfombra que he comprado»: es mía, no todas las alfombras
            frases.append(f"{sn[:1].upper() + sn[1:]} {'son' if pl else 'es'} {adj}.")
            if m.group(3):
                frases.append(f"{sn[:1].upper() + sn[1:]} que {' '.join(toks[k0 + nw + 1:])}." if False else None)
                rel = " ".join(toks[k0 + nw:])
                rel = re.sub(r"^,?\s*que\s+", "", rel)
                rel = re.sub(r"^(más|menos|mucho|poco|siempre|nunca|ya)\s+(\S+)", r"\2 \1", rel)      # «que más vendo» -> «vendo más»
                if rel:
                    frases[-1] = f"{rel[:1].upper() + rel[1:]} {sn[0].lower() + sn[1:]}."   # «que he comprado» -> «He comprado la alfombra»
    if not frases:
        # «He hecho este cuenco», «Me he comprado esta chaqueta»: la frase tal cual y, además, el color de lo que se enseña
        m = re.search(r"\b(este|esta|estos|estas)\s+([a-zñ]+)\b", n)
        if m and not re.search(r"\b(?:este|esta|estos|estas)\s+" + re.escape(m.group(2)), sa_orig_lower(p)):
            m = None                                    # «mi madre está enferma»: «está» es el verbo, no «esta»
        if m and not re.match(r"^(?:este|esta|esto|estos|estas)\b", n) and any(x[1] in ("pres", "pret", "imp", "fut") for w in n.split()[:4] for x in M.analizar(w)):
            nom = m.group(2)
            c_m = K._kb_clase(nom)
            if not (c_m and ("persona" in K.ancestros(c_m) or c_m == "persona")) and nom not in ("imagen", "foto", "color", "año", "mes", "semana", "dia", "verano", "invierno", "fin"):
                pl = m.group(1) in ("estos", "estas"); g = "f" if m.group(1) in ("esta", "estas") else "m"
                art = ("las " if g == "f" else "los ") if pl else ("la " if g == "f" else "el ")
                toks = p.strip(" ¿?.!").split()
                k0 = next((i for i, w in enumerate(toks) if sa(w.lower()) == m.group(1)), None)
                nom_o = toks[k0 + 1] if k0 is not None and k0 + 1 < len(toks) else nom
                orig = re.sub(r"^(?:[Mm]ira|[Oo]ye)\s*,?\s*", "", p.strip())
                frases = [orig[:1].upper() + orig[1:], f"{art[:1].upper() + art[1:]}{nom_o} {'son' if pl else 'es'} {color_adj(col, g, pl)}."]
    if not frases:
        return None
    hechos = []
    for k_fr, fr in enumerate(frases):
        r = nuc._una(fr) if fr else None
        if r is None or r.get("estado") not in ("ok",) or "no lo he entendido" in sa(r.get("respuesta", "")):
            if k_fr == 0:
                return None
            continue                                    # lo que acompaña («que más vendo») no se ha entendido: queda lo que se ve
        hechos.append(re.sub(r"^(?:Entendido|De acuerdo|Vale|Anotado):\s*", "", r["respuesta"]).rstrip("."))
    v["etiqueta"] = v.get("etiqueta") or "dicho"
    return _ok("Entendido: " + "; ".join(hechos) + ".", "ack")


def _lista_col(cs, g, pl):
    xs = [color_adj(c, g, pl) for c in cs]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " o " + xs[-1]


def _podria(v, c, col):
    cl, cs = _colores_tipicos(c)
    if not col:
        return _abst("No lo sé: no he podido identificar el color de la imagen.")
    if not cs:
        return _abst(f"No lo sé: no sé de qué color suelen ser {K.suj(c)}.")
    g = K.genero(cl)
    if col in cs:
        return _ok(f"Sí, por el color podría: {K.suj(cl)} {'es' if K.es_masa(cl) else 'son'} {_lista_col(cs, g, not K.es_masa(cl))}. Pero solo veo el color, no su forma real.")
    return _ok(f"No parece: {K.suj(cl)} {'es' if K.es_masa(cl) else 'son'} {_lista_col(cs, g, not K.es_masa(cl))} y esto es {color_adj(col)}.")


def _colores_ent(nuc, e):
    if e is None or isinstance(e, list) or str(e).startswith("?"):
        return []
    out = []
    for f in nuc.marcos(v="ser", s=e, neg=False, herencia=False):
        out.extend(a for a in f.get("attr", []) if a in NOMBRES_SA)
    return out


# ====================================================================== 2.10 · varias figuras: dónde está cada una
_POS_PAL = {"arriba": "sobre", "encima": "sobre", "abajo": "bajo", "debajo": "bajo", "a la izquierda": "izquierda", "izquierda": "izquierda",
            "a la derecha": "derecha", "derecha": "derecha", "dentro": "dentro"}
_INV_IMG = {"sobre": "bajo", "bajo": "sobre", "izquierda": "derecha", "derecha": "izquierda"}


def _fig_por_nombre(v, txt):
    """Índices de las figuras que casan con «el cuadrado», «la figura roja», «la estrella amarilla»."""
    ws = sa(txt).split()
    out = []
    for i, f in enumerate(v["figuras"]):
        ok = False
        for w in ws:
            if f.get("forma") and (w == f["forma"] or sa(M.singular(w)) == f["forma"]):
                ok = True
        cols = [w for w in ws if sa(M.masc(w)) in NOMBRES_SA or w in NOMBRES_SA]
        if cols:
            c = sa(M.masc(cols[0])) if sa(M.masc(cols[0])) in NOMBRES_SA else cols[0]
            ok = (ok or "figura" in ws or not any(w in FORMA.values() for w in ws)) and f.get("color") == c
        if ok:
            out.append(i)
    return out


def _fig_en_pos(v, rel):
    """La figura que está en esa posición respecto de todas las demás («la de arriba»)."""
    cands = [i for i in range(len(v["figuras"])) if sum(1 for (a, r, b) in v["rels"] if a == i and r == rel) == len(v["figuras"]) - 1]
    return cands[0] if len(cands) == 1 else None


def _escena(nuc, v, n):
    n = re.sub(rf"^(?:en |mira )?{_DEIC}\s*[,:]?\s*", "", n).strip(" ,:")
    n = re.sub(r"\s+(?:en|de) (?:este|el|la|esta) (?:dibujo|imagen|foto)$", "", n)
    pos_re = r"(arriba|encima|abajo|debajo|a la izquierda|a la derecha|dentro)"
    if re.match(r"^cuantas (?:figuras|formas|cosas) (?:hay|ves|tiene)", n):
        return _ok(describe(v))
    # «¿qué figura está encima?», «¿qué hay abajo?»
    m = re.match(rf"^(?:que|cual) (?:figura|forma|cosa)? ?(?:esta|hay|ves|tienes|es la que esta)(?: (?:mas|mas hacia))? {pos_re}$", n) or re.match(rf"^que hay {pos_re}$", n)
    if m:
        rel = _POS_PAL[m.group(1)]
        i = _fig_en_pos(v, rel)
        if i is None:
            return _abst(f"No lo sé: no hay una sola figura {POS_IMG.get(rel, rel)}. " + describe(v))
        return _ok(_cap1(f"{nombra_fig(v['figuras'][i], 'el')} está {POS_IMG[rel]}."))
    # «¿qué hay debajo del cuadrado?»
    m = re.match(rf"^(?:que|cual) (?:figura |forma )?(?:hay|esta|ves) (encima|debajo|a la izquierda|a la derecha|dentro|al lado) (?:de|del) (.+)$", n)
    if m:
        rel = _POS_PAL.get(m.group(1), "junto")
        if not _habla_de_figuras(m.group(2)):
            return None                                   # «¿qué hay debajo de la cama?»: no es una figura del dibujo
        js = _fig_por_nombre(v, m.group(2))
        if len(js) != 1:
            return _abst(f"No sé a qué figura te refieres. " + describe(v))
        j = js[0]
        if rel == "junto":
            ys = [a for (a, r, b) in v["rels"] if b == j and r in ("izquierda", "derecha")]
        else:
            ys = [a for (a, r, b) in v["rels"] if b == j and r == rel]
        if not ys:
            return _ok(f"No, {REL_TXT.get(rel, 'al lado de')} {nombra_fig(v['figuras'][j], 'el')} no hay ninguna figura.".replace("de el ", "del "))
        return _ok(_cap1(f"{REL_TXT.get(rel, 'al lado de')} {nombra_fig(v['figuras'][j], 'el')} está {nombra_fig(v['figuras'][ys[0]])}.".replace("de el ", "del ")))
    # «¿de qué color es la figura de arriba?», «¿qué forma tiene la de la izquierda?»
    m = re.match(rf"^(?:de que color es|que color tiene|que forma tiene|que (?:figura|forma) es) (?:la figura|la forma|la|lo) (?:de )?(arriba|abajo|la izquierda|la derecha|encima|debajo)$", n)
    if m:
        pal = m.group(1).replace("la ", "a la ")
        rel = _POS_PAL.get(pal, _POS_PAL.get(m.group(1)))
        i = _fig_en_pos(v, rel)
        if i is None:
            return _abst("No lo sé: " + describe(v)[0].lower() + describe(v)[1:])
        f = v["figuras"][i]
        if "color" in n:
            return _ok(f"La figura de {POS_IMG[rel].replace('a la ', 'la ')} es {color_adj(f['color'], 'f')}.") if f.get("color") else _abst("No reconozco su color.")
        return _ok(_cap1(f"Es {nombra_fig(f)}.")) if f.get("forma") else _abst("No reconozco su forma.")
    # «¿el cuadrado está encima del triángulo?»
    m = re.match(rf"^(?:el|la) (.+?) esta (encima|debajo|a la izquierda|a la derecha|dentro) (?:de|del) (.+)$", n)
    if m and _habla_de_figuras(m.group(1)) and _habla_de_figuras(m.group(3)):
        a_, b_ = _fig_por_nombre(v, m.group(1)), _fig_por_nombre(v, m.group(3))
        if len(a_) == 1 and len(b_) == 1:
            rel = _POS_PAL[m.group(2)]
            if (a_[0], rel, b_[0]) in v["rels"]:
                return _ok("Sí.")
            real = [r for (a, r, b) in v["rels"] if a == a_[0] and b == b_[0]]
            return _ok(f"No: {nombra_fig(v['figuras'][a_[0]], 'el')} está {REL_TXT[real[0]]} {nombra_fig(v['figuras'][b_[0]], 'el')}.".replace("de el ", "del ")) if real else _abst("No lo sé.")
    return None


def _habla_de_figuras(txt):
    """¿Nombra una figura o un color (lo que hay en un dibujo), y no una cosa cualquiera?"""
    ws = [sa(M.singular(w)) if w.endswith("s") else w for w in sa(txt).split()]
    return any(w in FORMA.values() or w in ("figura", "forma") or sa(M.masc(w)) in NOMBRES_SA or w in NOMBRES_SA for w in ws)


def _cap1(t):
    return t[:1].upper() + t[1:]
