"""LCM 2.16 · CREAR A PETICIÓN.

Cuando la persona lo pide («escribe un poema sobre el mar», «invéntate un cuento sobre un gato», «dime una palabra que rime con canción»,
«invéntate una adivinanza», «descríbeme un bosque», «dime tres frutas»…), el LCM COMPONE algo nuevo con lo que sabe:
  · el contenido sale de la base de conceptos (qué es, qué partes tiene, para qué sirve, dónde está, qué hace) y de lo que la persona ha contado
  · la rima se calcula por el sonido de la palabra (desde la vocal acentuada), no con una lista
  · la variación la da una semilla que cambia en cada turno: «otro» da uno distinto
No es una orden que guardar como hecho, y solo se activa con una petición (imperativo o «¿puedes…?»): «ayer escribí un poema» es un hecho.
"""
from __future__ import annotations

import re

from . import conceptos as K
from . import morfo as M
from . import relaciones as R
from .morfo import sa

_IMP = (r"(?:escribe(?:me|nos)?|inventa(?:te|me)?|crea(?:me)?|compon(?:me)?|haz(?:me)?|di(?:me|nos)?|cuenta(?:me|nos)?|describe(?:me)?|pon(?:le|me)?|termina(?:me)?|acaba|completa|continua|"
        r"da(?:me)?|recita(?:me)?|imagina(?:te)?|regalame|nombra(?:me)?|enumera(?:me)?|sugiere(?:me)?|propon(?:me)?|improvisa(?:me)?)")
_INF = r"(?:escribir|inventar|crear|componer|hacer|decir|contar|describir|poner|terminar|acabar|completar|continuar|dar|recitar|imaginar|nombrar|enumerar|sugerir|proponer|improvisar)(?:me|te|le|nos)?"
_SUBJ = r"(?:escribas|inventes|crees|compongas|hagas|digas|cuentes|describas|pongas|termines|acabes|completes|continues|des|recites|imagines|nombres|enumeres|sugieras|propongas|improvises)"
_PIDE = re.compile(rf"^(?:(?:por favor|porfa|anda|venga|oye|ahora|y|vale|bueno)\s*,?\s+)*(?:{_IMP}|(?:(?:me|nos)\s+)?(?:puedes|podrias|sabes|sabrias|quieres|te animas a|eres capaz de)\s+{_INF}|"
                   rf"(?:quiero|quisiera|me gustaria|necesito)\s+que\s+(?:me\s+|nos\s+|le\s+)?{_SUBJ})\b\s*(.*)$")
_OTRO = re.compile(r"^(?:(?:y|venga|anda|va|pues)\s+)?(?:otr[oa](?: mas| distint[oa]| diferente)?|un[oa] mas|otra vez|un[oa] distint[oa]|repite(?:lo)?(?: pero distinto)?|hazlo otra vez|mas)(?:\s+por favor)?$")

_EVOCA = ("soñar cantar volar bailar jugar caminar recordar esperar navegar mirar amar abrazar regresar empezar brillar despertar "
          "querer volver aprender ver crecer amanecer correr florecer reír sentir vivir dormir seguir sonreír descubrir partir "
          "corazón canción ilusión emoción razón estación amor color calor flor sabor alegría día melodía compañía fantasía poesía viento momento pensamiento cuento "
          "madrugada mirada almohada nada ternura dulzura aventura locura belleza verano mano hermano temprano luna cuna fortuna sol girasol caracol farol miel papel piel pincel "
          "rosa mariposa hermosa camino destino vecino ventana mañana campana manzana cielo vuelo abuelo consuelo estrella huella botella vida comida despedida "
          "amigo abrigo testigo contigo conmigo casa brasa taza calma palma alma libertad verdad amistad ciudad edad luz cruz voz arroz mar hogar lugar azar final cristal señal").split()
_NOMBRES = {"perro": "Toby Luna Coco Trufa Rayo Canela Thor Nube Chispa Bruno".split(), "gato": "Misu Bigotes Pelusa Simba Nala Tigre Mora Copito Salem Garbanzo".split(),
            "persona": "Lucas Martina Hugo Sofía Leo Julia Mateo Vera Bruno Alba".split(), "_": "Pipo Lila Nico Brisa Tango Momo Kira Zuri Bolo Greta".split()}
_COLOR_NOMBRE = {"negro": "Carbón", "blanco": "Copito", "marron": "Canela", "gris": "Niebla", "naranja": "Mandarina", "amarillo": "Limón", "rojo": "Fresa"}
_AFICIONES = ["mirar las estrellas", "coleccionar hojas secas", "inventar canciones", "contar nubes", "explorar rincones nuevos", "escuchar la lluvia"]
_CHISTES = ["¿Qué le dice una pared a otra pared? Nos vemos en la esquina.", "¿Cuál es el colmo de un jardinero? Que siempre lo dejen plantado.",
            "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!", "¿Por qué los pájaros no usan el móvil? Porque ya tienen tuits.",
            "¿Cuál es el café más peligroso del mundo? El ex-preso.", "¿Qué le dice un semáforo a otro? No me mires, que me estoy cambiando.",
            "¿Cómo se despiden los químicos? Ácido un placer.", "¿Qué le dice el número 1 al número 10? Para ser como yo tienes que ser sincero."]
_FINALES = ["todo empezó a cambiar.", "nadie quiso irse a dormir.", "el día se llenó de sorpresas.", "por fin pudimos respirar tranquilos.", "empezó la mejor parte de la historia.", "el mundo pareció un poco más grande."]
_GENEROS = "un poema, un cuento, una adivinanza, una frase con una palabra, palabras que riman, un título, un nombre, una descripción o un chiste"


# ------------------------------------------------------------------ sonido: de dónde arranca la rima
def clave_rima(w):
    """Desde la vocal acentuada hasta el final («canción» -> «on», «gato» -> «ato», «mar» -> «ar»)."""
    w = w.lower().strip()
    m = list(re.finditer(r"[áéíóú]", w))
    if m:
        return sa(w[m[-1].start():])
    nuc = [x for x in re.finditer(r"[aeo]|[iuü]+[aeo]?[iuü]?|[aeo][iuy]", w)]
    nuc = list(re.finditer(r"(?:[iuü](?=[aeo]))?[aeo](?:[iuy](?![aeo]))?|[iuü]+", w))
    if not nuc:
        return w
    k = nuc[-2] if len(nuc) >= 2 and re.search(r"[aeiouns]$", w) else nuc[-1]
    ini = k.start()
    fuerte = re.search(r"[aeo]", w[k.start():k.end()])
    if fuerte:
        ini = k.start() + fuerte.start()
    return w[ini:]


_RIMARIO = {}


def rimas(w, n=6, semilla=0):
    if not _RIMARIO:
        vistos = set()
        for x in list(_EVOCA) + [f for f in K.kb()["forma"].values() if " " not in f]:
            if sa(x) not in vistos and len(x) > 2:
                vistos.add(sa(x))
                _RIMARIO.setdefault(clave_rima(x), []).append(x)
    c = clave_rima(w)
    cands = [x for x in _RIMARIO.get(c, []) if sa(x) != sa(w.lower())]
    if len(cands) > n:
        i0 = semilla % len(cands)
        cands = (cands[i0:] + cands[:i0])[:n] if semilla else cands[:n]
    return cands


# ------------------------------------------------------------------ lo que se sabe de un concepto
def saber(c):
    k = K.kb()
    d = {"c": c, "clase": (k["isa"].get(c) or [None])[0], "hijos": k["hijos"].get(c, []),
         "partes": [k["parte_disp"].get((c, x), x) for x in k["partes"].get(c, [])],
         "func": R.valores(c, "funcion")[1], "lugar": R.valores(c, "lugar")[1], "mat": R.valores(c, "material")[1],
         "dentro": [K.forma(x, plural=True) if x in k["forma"] else x for x in R.inversa("lugar", c)][:5]}
    props = []
    for cl in [c] + K.ancestros(c)[:2]:
        for (x, neg, v, r) in k["props"]:
            if x == cl and not neg and v not in ("servir",):
                props.append((cl, v, r))
    d["props"] = props
    return d


def _elige(xs, semilla, k=0):
    return xs[(semilla * 7 + k * 13) % len(xs)] if xs else None


def _y(xs):
    xs = list(dict.fromkeys(xs))
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + (" e " if sa(xs[-1]).startswith(("i", "hi")) else " y ") + xs[-1]


def _tema(nuc, resto):
    """«sobre el mar», «para mi hija», «de un gato negro» -> (clase|None, entidad|None, palabra, texto)."""
    m = re.search(r"\b(?:sobre|acerca de|de|del|a|al|para|con)\s+((?:el|la|los|las|un|una|unos|unas|mi|mis|tu|tus|su|sus)\s+)?([a-zñ]+(?:\s+[a-zñ]+)?)\s*$", resto)
    if not m:
        return None, None, "", ""
    det, txt = (m.group(1) or "").strip(), m.group(2).strip()
    w = txt.split()[0]
    ent = None
    if det in ("mi", "mis", "tu", "tus", "su", "sus") or K._kb_clase(w) is None:
        for e in list(nuc.E):
            if e in ("U", "L") or e.startswith("K:"):
                continue
            cl = sa(nuc.E[e].get("clase") or "")
            nombre = sa(nuc.disp(e).lower())
            if (det in ("mi", "mis") and e.endswith("@U") and cl[:4] == sa(M.singular(w))[:4]) or nombre == w or nombre.split()[-1] == w:
                ent = e
                break
    if ent is None and det in ("mi", "mis"):            # «mi hija»: la conoce el núcleo por su nombre
        try:
            t0 = nuc.turno
            r = nuc._procesar_216(f"¿Cómo se llama mi {w}?")
            nuc.turno = t0
            mm = re.search(r"se llama ([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)", (r or {}).get("respuesta", "")) if isinstance(r, dict) and r.get("estado") == "ok" else None
            if mm and ("N:" + sa(mm.group(1).lower())) in nuc.E:
                ent = "N:" + sa(mm.group(1).lower())
        except Exception:                               # noqa
            pass
    c = K._kb_clase(w)
    return c, ent, w, txt


def _semilla(nuc, extra=""):
    return nuc.turno + sum(ord(ch) for ch in extra) + getattr(nuc, "_crea_n", 0) * 5


def _gustos(nuc, e):
    return [f["obj_disp"] for f in nuc.F if f["v"] in ("gustar", "encantar", "adorar", "amar", "apasionar") and f.get("s") and nuc.can(f["s"]) == e and not f.get("neg") and f.get("obj_disp")]


# ------------------------------------------------------------------ géneros
def poema(nuc, c, ent, w, sem):
    if ent:
        nombre = nuc.disp(ent)
        nombre = nombre[:1].upper() + nombre[1:]
        gustos = _gustos(nuc, ent)
        l2 = f"que disfruta con {_y(gustos[:2])}," if gustos else "que llena de vida la casa,"
        rs = rimas(gustos[0].split()[-1], semilla=sem) if gustos else rimas("casa", semilla=sem)
        rs = [x for x in rs if x in _EVOCA]
        l4 = f"y el mundo le sabe a {rs[0]}." if rs and not re.search(r"(?:ar|er|ir)$", rs[0]) else "y el día amanece mejor."
        return f"Para {nombre} van estos versos,\n{l2}\ncuando sonríe se nota\n{l4}"
    if not c:
        rs = rimas(w, semilla=sem)
        fin = f"y me dan ganas de {rs[0]}." if rs and re.search(r"(?:ar|er|ir|ír)$", rs[0]) else (f"y me acuerdo de {rs[0]}." if rs else "y me quedo un rato en silencio.")
        return f"Hoy quiero escribir de {w},\nuna palabra que no conocía;\nla digo despacio, {w},\n{fin}"
    s = saber(c)
    el, los = K.el(c), K.los(c)
    primeras = []
    if s["dentro"]:
        primeras.append(f"Entre {_y(s['dentro'][:2])} te encuentro,")
    if s["partes"]:
        primeras.append(f"Con tus {_y(s['partes'][:2])},")
    if s["props"]:
        cl, v, r = s["props"][0]
        primeras.append(K._cap(K._frase_prop(cl, False, v, r)) + ",")
    if s["func"]:
        primeras.append(f"Sirves para {s['func'][0]},")
    if s["clase"]:
        primeras.append(f"Eres {K.un(s['clase'])} y algo más,")
    l1 = _elige(primeras, sem) or f"Te miro despacio, {w},"
    l2 = _elige([f"te canto a ti, {w}.", f"así es {el}.", f"por eso pienso en {el}."], sem, 1)
    l3 = _elige(["Cada vez que te nombro sonrío", "Si no existieras, habría que inventarte", "Te llevo conmigo a todas partes", "Cuando no estás, algo falta"], sem, 2)
    rs = rimas(K.forma(c) if c in K.kb()["forma"] else w, semilla=sem)
    inf = [r for r in rs if re.search(r"(?:ar|er|ir|ír)$", r) and M.analizar(r)]
    if inf:
        l4 = f"y me dan ganas de {_elige(inf, sem)}."
    elif rs:
        r0 = _elige(rs, sem)
        cr = K._kb_clase(r0)
        l4 = f"y me acuerdo de {K.el(cr) if cr else r0}."
    else:
        l4 = "y me quedo aquí, a tu lado."
    return f"{l1}\n{l2}\n{l3}\n{l4}"


def cuento(nuc, c, ent, w, sem):
    k = K.kb()
    if ent:
        prota, nombre, un = nuc.disp(ent), nuc.disp(ent), nuc.disp(ent)
        c = K._kb_clase(sa(nuc.E[ent].get("clase") or "")) or c
        presenta = f"Había una vez {('un' if nuc.gen(ent) != 'f' else 'una')} {nuc.E[ent].get('clase') or 'amigo'} que se llamaba {nombre[:1].upper() + nombre[1:]}"
    else:
        if not c:
            return None
        anc = K.ancestros(c)
        banco = _NOMBRES.get(c) or (_NOMBRES["persona"] if "persona" in anc else _NOMBRES["_"])
        nombre = _elige(banco, sem)
        presenta = f"Había una vez {K.un(c)} que se llamaba {nombre}"
    s = saber(c) if c else {"lugar": [], "props": [], "clase": None}
    anc = K.ancestros(c) if c else []
    lugar = (R._el_lugar(s["lugar"][0]) if s["lugar"] else None) or ("el bosque" if "animal" in anc else "un pueblo pequeño")
    lugar = re.sub(r"^el ", "un ", lugar) if lugar.startswith("el ") and not s["lugar"] else lugar
    t = [f"{presenta} y vivía en {lugar}."]
    afi = _elige(_AFICIONES, sem, 1)
    if s["props"]:
        cl, v, r = s["props"][0]
        t.append(f"Ya se sabe que {K._frase_prop(cl, False, v, r)}, pero lo que más le gustaba a {nombre} era {afi}.")
    else:
        t.append(f"Lo que más le gustaba a {nombre} era {afi}.")
    herm = [x for x in (k["hijos"].get(s["clase"], []) if s.get("clase") else []) if x != c and " " not in x]
    otro = _elige(herm, sem, 2)
    n2 = _elige([x for x in _NOMBRES["_"] if x != nombre], sem, 3)
    cosa = _elige([x for x in k["hijos"].get("juguete", []) + k["hijos"].get("prenda", []) if " " not in x] or ["tesoro"], sem, 4)
    donde = R.valores(cosa, "lugar")[1]
    sitio = R._el_lugar(donde[0]) if donde else "un rincón donde nadie había mirado"
    quien = f"{K.un(otro)} que se llamaba {n2}" if otro else f"un vecino que se llamaba {n2}"
    t.append(f"Un día apareció {quien}, muy triste, porque había perdido {K.un(cosa) if cosa in k['forma'] else 'un ' + cosa}.")
    t.append(f"Buscaron juntos por todas partes y al final {'lo' if K.genero(cosa) != 'f' else 'la'} encontraron en {sitio}.")
    t.append(f"Desde aquel día {nombre} y {n2} fueron inseparables. Y colorín colorado, este cuento se ha acabado.")
    return " ".join(t)


def descripcion(nuc, c, w):
    if not c:
        return None
    s = saber(c)
    un = K._cap(K.un(c))
    t = []
    if s["clase"]:
        t.append(f"{un} es {K.un(s['clase'])}.")
    if s["partes"]:
        t.append(f"Tiene {_y(s['partes'][:5])}.")
    if s["dentro"]:
        t.append(f"En {K.un(c)} suele haber {_y(s['dentro'][:4])}.")
    if s["func"]:
        t.append(f"Sirve para {_y(s['func'][:2])}.")
    if s["mat"]:
        t.append(f"Suele ser de {_y(s['mat'][:2]).replace(' y ', ' o ')}.")
    if s["lugar"]:
        t.append(f"Suele estar en {R._el_lugar(s['lugar'][0])}.")
    for cl, v, r in s["props"][:3]:
        t.append(K._cap(K._frase_prop(cl, False, v, r)) + ".")
    return " ".join(t) if len(t) >= 2 else None


def frase_con(nuc, w, sem):
    c = K._kb_clase(w)
    if c:
        s = saber(c)
        el = K._cap(K.el(c))
        ops = []
        if s["func"]:
            ops.append(f"Esta mañana he usado {K.el(c)} para {s['func'][0]}.")
        if s["lugar"]:
            ops.append(f"{el} estaba en {R._el_lugar(s['lugar'][0])}, donde siempre.")
        if s["partes"]:
            ops.append(f"{el} tiene {_y(s['partes'][:2])}.")
        if s["props"]:
            cl, v, r = s["props"][0]
            ops.append(f"Todo el mundo sabe que {K._frase_prop(cl, False, v, r)}.")
        ops.append(f"Ayer vi {K.un(c)} y me acordé de ti.")
        fr = _elige(ops, sem)
        return fr if re.search(rf"\b{re.escape(sa(w))}", sa(fr.lower())) else f"Ayer vi {K.un(c)} y me acordé de ti: qué bonita palabra, «{w}»."
    return _elige([f"Hoy he aprendido la palabra «{w}» y no pienso olvidarla.", f"Nadie me había hablado de «{w}» hasta hoy."], sem)


def adivinanza(nuc, sem):
    k = K.kb()
    cands = sorted(c for c in k["partes"] if c in k["forma"] and (k["rel"]["funcion"].get(c) or k["rel"]["lugar"].get(c)) and " " not in c)
    if not cands:
        return None
    c = _elige(cands, sem)
    s = saber(c)
    pistas = [f"tengo {_y(s['partes'][:3])}"]
    if k["rel"]["funcion"].get(c):
        pistas.append(f"sirvo para {k['rel']['funcion'][c][0]}")
    if k["rel"]["lugar"].get(c):
        pistas.append(f"suelo estar en {R._el_lugar(k['rel']['lugar'][c][0])}")
    nuc.usuario["adivinanza"] = {"c": c, "turno": nuc.turno}
    return "Adivina, adivinanza: " + _y(pistas) + ". ¿Qué soy?"


def responde_adivinanza(nuc, n):
    a = nuc.usuario.get("adivinanza")
    if not a or nuc.turno - a["turno"] > 6:
        return None
    c = a["c"]
    if re.match(r"^(?:me rindo|no lo se|no se|ni idea|dimelo|dime la respuesta|cual es(?: la respuesta)?|que es|que eres|que era|la solucion|no caigo)\b", n):
        nuc.usuario.pop("adivinanza", None)
        return f"Era {K.un(c)}."
    m = re.match(r"^(?:es |eres |sera |seras |creo que (?:es|eres) |puede ser )?(?:el |la |un |una |los |las )?([a-zñ ]+)$", n)
    if m and K._kb_clase(m.group(1).strip()):
        if K._kb_clase(m.group(1).strip()) == c:
            nuc.usuario.pop("adivinanza", None)
            return f"¡Sí! Era {K.un(c)}. Muy bien."
        return "No, no es eso. Prueba otra vez, o dime «me rindo»."
    return None


def titulo(nuc, c, w, sem):
    if c:
        el = K.el(c)
        inf = _elige(["volar", "viajar", "cantar", "ser valiente", "ver el mar", "tocar la luna"], sem)
        return _elige([f"«{K._cap(el)} que quería {inf}»", f"«La gran aventura de {el}»".replace(" de el ", " del "), f"«{K._cap(el)} y el secreto del bosque»", f"«El día que {el} aprendió a {inf}»"], sem, 1)
    return f"«La increíble historia de {w}»"


def nombre(nuc, c, resto, sem):
    col = next((v for k_, v in _COLOR_NOMBRE.items() if re.search(rf"\b{k_}[oa]?s?\b", resto)), None)
    banco = _NOMBRES.get(c or "") or (_NOMBRES["persona"] if c and "persona" in K.ancestros(c) else _NOMBRES["_"])
    ns = [col] if col else []
    ns += [x for x in (banco[(sem + i) % len(banco)] for i in range(3)) if x not in ns]
    que = K.un(c) if c else "eso"
    return f"Para {que} se me ocurre {ns[0]}. Si no te convence, también {ns[1]} o {ns[2]}."


def ideas(nuc, resto, sem):
    e = None
    try:
        e = nuc.ref3(persona=True)
    except Exception:                                   # noqa
        pass
    gustos = _gustos(nuc, e) if e else []
    if gustos and re.search(r"regal", resto):
        g = re.sub(r"^(?:el|la|los|las)\s+", "", gustos[0])
        quien = nuc.disp(e)
        return f"Como a {quien} le gustan {gustos[0]}, se me ocurre: un libro sobre {g}, un póster o un puzle de {g}, o una excursión para ver {g} de cerca."
    if re.search(r"regal", resto):
        return "Sin saber qué le gusta, tres ideas que suelen acertar: un libro, un juego de mesa o una tarde haciendo algo juntos. Si me cuentas sus gustos, afino más."
    c, _, w, _ = _tema(nuc, resto)
    if c and c in ("fiesta", "cumpleaños") or re.search(r"fiesta|cumple", resto):
        return "Tres ideas: preparar una lista de canciones para bailar, organizar un juego en el que participen todos y terminar con una merienda sorpresa."
    return f"Tres ideas para empezar: hacer una lista de lo que hace falta, pedir ayuda a alguien de confianza y reservar un rato cada día para {('eso' if not w else w)}."


def continuar(nuc, frag, sem):
    frag = frag.strip(" .:…")
    ws = [K._kb_clase(x) for x in re.findall(r"[a-zñ]+", sa(frag.lower()))]
    for c in [x for x in ws if x]:
        ps = [(v, r) for (x, neg, v, r) in K.kb()["props"] if x == c and not neg and v not in ("ser", "servir", "tener", "estar")]
        if ps:
            v, r = ps[0]
            try:
                return f"{frag[:1].upper() + frag[1:]} {M.conjugar(v, 'pret', '3s')}{' ' + r if r else ''} hasta que se hizo de noche."
            except Exception:                           # noqa
                break
    return f"{frag[:1].upper() + frag[1:]} {_elige(_FINALES, sem)}"


def invento(nuc, sem):
    k = K.kb()
    an = sorted(c for c in k["hijos"].get("mamifero", []) + k["hijos"].get("ave", []) + k["hijos"].get("pajaro", []) if " " not in c and len(c) >= 4 and c in k["forma"])
    if len(an) < 2:
        return None
    a = _elige(an, sem)
    b = _elige([x for x in an if x != a], sem, 3)
    fa, fb = K.forma(a), K.forma(b)
    nom = fa[:max(2, len(fa) // 2)] + fb[len(fb) // 2:]
    pa = next((r for (x, neg, v, r) in k["props"] if x in [a] + K.ancestros(a)[:1] and v == "tener" and not neg), "el cuerpo")
    vb = next(((v, r) for (x, neg, v, r) in k["props"] if x == b and not neg and v not in ("tener", "ser")), None)
    hace = f" y {M.conjugar(vb[0], 'pres', '3s')}{' ' + vb[1] if vb[1] else ''} como {K.los(b)}" if vb else ""
    return f"Me invento el {nom}: es mitad {fa} y mitad {fb}. Tiene {pa} como {K.los(a)}{hace}. No existe, claro: acabo de imaginarlo."


def ejemplos(nuc, n):
    m = re.match(r"^(?:di(?:me|nos)?|dame|nombra(?:me)?|enumera(?:me)?)\s+(un|una|dos|tres|cuatro|cinco|seis|algun|alguna|algunos|algunas|varios|varias|unos|unas|\d+)?\s*(?:ejemplos? de |tipos? de |nombres? de |clases? de )?([a-zñ]+)(?:\s+que\s+(?:no\s+)?([a-zñ]+)(?:\s+(.+))?)?$", n)
    if not m:
        return None
    c = K._kb_clase(m.group(2))
    k = K.kb()
    if not c or not k["hijos"].get(c):
        return None
    cuantos = {"un": 1, "una": 1, "algun": 1, "alguna": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}.get(m.group(1) or "", int(m.group(1)) if (m.group(1) or "").isdigit() else 3)
    todos, cola = [], list(k["hijos"][c])
    while cola:
        x = cola.pop(0)
        if x in k["forma"] and " " not in x and x not in todos:
            if not k["hijos"].get(x):
                todos.append(x)
            cola += k["hijos"].get(x, [])
    if m.group(3):
        v0 = m.group(3)                                    # «que vuele»: el subjuntivo vale por su verbo
        lem = next((a[0] for f_ in (v0, v0[:-1] + "a", v0[:-1] + "e", v0[:-2] + "e", v0[:-2] + "a", v0[:-1]) for a in M.analizar(f_)), None) or v0
        resto = m.group(4) or ""
        neg_q = " que no " in f" {n} "
        ok = []
        for x in todos:
            e = K._estado(x, lem, resto)
            if e is not None and bool(e[1]) == neg_q:
                ok.append(x)
        todos = ok
        if not todos:
            return None
    i0 = (getattr(nuc, "_crea_n", 0) * cuantos) % max(1, len(todos))     # los más típicos primero (orden de la base); «otros» da los siguientes
    elegidos = (todos[i0:] + todos[:i0])[:cuantos]
    nuc.ult_just = {"pasos": [f"{K.un(x)} es {K.un(c)}" for x in elegidos[:3]], "fabrica": True}
    if cuantos == 1:
        return f"{K._cap(K.un(elegidos[0]))}, por ejemplo."
    return K._cap(_y([K.forma(x) for x in elegidos])) + "."


# ------------------------------------------------------------------ entrada
def responder(nuc, texto):
    """Respuesta (texto) si la frase pide crear algo; None si no es una petición de crear."""
    n = re.sub(r"\s+", " ", sa((texto or "").lower()).strip(" ¿?¡!."))
    ra = responde_adivinanza(nuc, n)
    if ra:
        return ra
    if _OTRO.match(n) and getattr(nuc, "_crea_ult", None):
        nuc._crea_n = getattr(nuc, "_crea_n", 0) + 1
        return responder(nuc, nuc._crea_ult)
    m = _PIDE.match(n)
    if not m:
        return None
    resto = m.group(1).strip()
    sem = _semilla(nuc, resto)
    out = None
    if re.search(r"\b(?:palabras?|algo|cosas?) que rimen? con\b|\brim[ae]n? con\b|\brimas? (?:con|para)\b", resto):
        w = (texto.strip(" ¿?¡!.").split()[-1]).strip("«»\"'")
        rs = rimas(w, n=5, semilla=getattr(nuc, "_crea_n", 0))
        out = (f"Con «{w}» riman, por ejemplo: {_y(rs)}." if rs else f"No encuentro ninguna palabra que rime con «{w}» entre las que conozco.")
    elif re.search(r"\bsinonimos?\b|\botras? (?:palabras?|formas?) (?:para|de decir)\b|\bpalabras? parecidas?\b", resto):
        w = (texto.strip(" ¿?¡!.").split()[-1]).strip("«»\"'").lower()
        ss = K.sinonimos_lexico(w)
        out = f"Otras palabras para «{w}», según mi léxico: {_y(ss)}." if ss else f"No tengo anotada otra palabra para «{w}»."
    elif re.search(r"\b(?:frase|oracion)\b.*\bcon\b", resto):
        w = (texto.strip(" ¿?¡!.").split()[-1]).strip("«»\"'").lower()
        out = frase_con(nuc, w, sem)
    elif re.search(r"\b(?:termina|acaba|completa|continua)\b", n) and re.search(r"\bfrase\b|:", texto):
        frag = texto.split(":", 1)[1] if ":" in texto else re.sub(r"^.*?\bfrase\b", "", texto)
        out = continuar(nuc, frag, sem) if frag.strip() else None
    elif re.search(r"\b(?:poema|poesia|versos?|pareado|haiku|cancion|copla|rima)\b", resto):
        c, ent, w, _ = _tema(nuc, resto)
        if not w and not ent:
            c, w = K._kb_clase("mar"), "mar"
            c = _elige([x for x in ("mar", "luna", "lluvia", "bosque", "amistad", "viento") if True], sem)
            w, c = c, K._kb_clase(c)
        out = poema(nuc, c, ent, w, sem)
    elif re.search(r"\b(?:cuento|historia|relato|fabula|aventura)\b", resto) and not re.search(r"\btitulo\b", resto):
        c, ent, w, _ = _tema(nuc, re.sub(r"\b(?:corto|corta|breve|pequeno|pequena|bonito|bonita|largo|infantil)\b", "", resto).strip())
        if not c and not ent:
            c = _elige(["zorro", "gato", "tortuga", "buho", "ardilla"], sem)
            c = K._kb_clase(c) or K._kb_clase("gato")
        out = cuento(nuc, c, ent, w, sem)
    elif re.search(r"\b(?:adivinanza|acertijo)\b", resto):
        out = adivinanza(nuc, sem)
    elif re.search(r"\b(?:chiste|broma)\b", resto):
        out = _elige(_CHISTES, sem)
    elif re.search(r"\btitulo\b", resto):
        c, ent, w, _ = _tema(nuc, resto)
        out = titulo(nuc, c, w or "un día cualquiera", sem)
    elif re.search(r"\bnombres?\b", resto) and re.search(r"\b(?:para|de)\b", resto):
        c, ent, w, _ = _tema(nuc, re.sub(r"\b(?:negro|negra|blanco|blanca|marron|gris|naranja|amarillo|rojo|pequeno|pequena|grande)\b", "", resto).strip())
        out = nombre(nuc, c, resto, sem)
    elif re.search(r"\bideas?\b|\bregal", resto):
        out = ideas(nuc, resto, sem)
    elif re.match(r"^(?:describe(?:me)?|describir(?:me)?|describas)\b", re.sub(r"^.*?(describ\w+)", r"\1", n)) or re.search(r"\bdescripcion\b", resto):
        c, ent, w, _ = _tema(nuc, "de " + resto if not re.search(r"\b(?:de|sobre)\b", resto) else resto)
        out = descripcion(nuc, c, w)
        if out is None and not ent:
            out = f"No sé lo bastante de «{w}» para describirlo: cuéntame cómo es y lo recordaré." if w else None
        if out is None:
            return None
    elif re.search(r"\b(?:animal|criatura|bicho|monstruo|ser)\b", resto) and re.search(r"invent|imagin|crea", n):
        out = invento(nuc, sem)
    else:
        out = ejemplos(nuc, n)
        if out is None:
            if re.match(rf"^(?:{_IMP})\b", n) and re.search(r"invent|imagin|compon|improvis|recita", n):
                out = f"Eso no sé crearlo todavía. Puedo componer {_GENEROS}."
            else:
                return None
    if out is None:
        return None
    nuc._crea_ult = texto
    return out
