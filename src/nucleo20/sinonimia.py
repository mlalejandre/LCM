"""LCM 2.19 · Preguntar con otras palabras.

Si una pregunta no encuentra respuesta, se vuelve a hacer con palabras que dicen lo mismo («¿de qué se alimentan?» = «¿qué comen?»,
«¿dónde habitan?» = «¿dónde viven?», «comida» = «alimento»). Las equivalencias son conocimiento de la lengua y están en la base de
conceptos (sección [equivalencias]); aquí solo se aplica la gramática del cambio (conjugación, «se … de», plural)."""
from __future__ import annotations

import os
import re

from . import conceptos as K
from . import morfo as M
from .morfo import sa


def _tabla():
    eq = K.kb().get("equiv") or {}
    return eq


def _spec(x):
    """«alimentarse de» -> (alimentar, True, 'de'); «comer» -> (comer, False, '')."""
    ws = x.strip().split()
    v = ws[0]
    refl = v.endswith("se") and len(v) > 4
    if refl:
        v = v[:-2]
    return sa(v), refl, (ws[1] if len(ws) > 1 else "")


def _plural(w):
    return w + "s" if w[-1:] in "aeiouáéó" else w + "es"


def alternativas(texto, maximo=6):
    """Otras formas de hacer la misma pregunta."""
    eq = _tabla()
    if not eq or "?" not in texto or os.environ.get("LCM_SIN_TABLA"):       # (interruptor solo para medir cuánto aporta cada pieza)
        return []
    out = []
    ws = re.findall(r"[\wáéíóúñü]+|[^\w\s]", texto)
    for i, w in enumerate(ws):
        wl = w.lower()
        try:
            an = [a for a in (M.analizar(wl) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut")]
        except Exception:                                # noqa
            an = []
        for lema in {a[0] for a in an}:
            a0 = next(a for a in an if a[0] == lema)
            refl_q = i > 0 and ws[i - 1].lower() == "se"
            for propio, otros in eq.items():
                grupo = [propio] + otros
                specs = [_spec(g) for g in grupo]
                mio = [s for s in specs if s[0] == sa(lema) and s[1] == refl_q]
                if not mio:
                    continue
                for dest in specs:
                    if dest == mio[0]:
                        continue
                    forma = M.conjugar(dest[0], a0[1], a0[2])
                    if not forma:
                        continue
                    ws2 = list(ws)
                    if mio[0][1] and not dest[1]:        # «de qué se alimenta» -> «qué come»; «se alimenta de X» -> «come X»
                        ws2[i] = forma
                        del ws2[i - 1]
                        t2 = " ".join(ws2)
                        if mio[0][2]:
                            t2 = re.sub(r"\b" + mio[0][2] + r"\s+(qu[eé])\b", r"\1", t2, count=1, flags=re.I)
                            t2 = re.sub(r"\b" + re.escape(forma) + r"\s+" + mio[0][2] + r"\s+", forma + " ", t2, count=1)
                    elif dest[1] and not mio[0][1]:      # «qué come» -> «de qué se alimenta»
                        ws2[i] = "se " + forma
                        t2 = " ".join(ws2)
                        if dest[2]:
                            if re.search(r"\bqu[eé]\s+se\s+" + re.escape(forma), t2, re.I):
                                t2 = re.sub(r"\b(qu[eé])\s+(se\s+" + re.escape(forma) + ")", dest[2] + r" \1 \2", t2, count=1, flags=re.I)
                            else:
                                t2 = re.sub(r"(se\s+" + re.escape(forma) + r")\s+(?=\w)", r"\1 " + dest[2] + " ", t2, count=1)
                    else:
                        ws2[i] = forma
                        t2 = " ".join(ws2)
                    t2 = re.sub(r"\s+([?.,!])", r"\1", re.sub(r"([¿¡])\s+", r"\1", t2))
                    t2 = re.sub(r"¿(\w)", lambda m: "¿" + m.group(1).upper(), t2)
                    if t2 not in out and sa(t2) != sa(texto):
                        out.append(t2)
        # nombres: «comida» = «alimento»
        base = sa(M.singular(wl)) if len(wl) > 3 else sa(wl)
        pl = wl.endswith("s") and sa(M.singular(wl)) != sa(wl)
        for propio, otros in (K.kb().get("equiv_n") or {}).items():
            grupo = [propio] + otros
            if base in [sa(g) for g in grupo]:
                for g in grupo:
                    if sa(g) == base:
                        continue
                    ws2 = list(ws)
                    ws2[i] = _plural(g) if pl else g
                    if i > 0 and ws2[i - 1].lower() in ("el", "la", "los", "las", "un", "una", "su", "propio", "propia", "mismo", "misma"):
                        fem = M.genero_sust(sa(g)) == "f"
                        k = i - 1
                        while k >= 0 and ws2[k].lower() in ("el", "la", "los", "las", "un", "una", "propio", "propia", "mismo", "misma", "su"):
                            x = ws2[k].lower()
                            ws2[k] = {"el": "la", "la": "el", "los": "las", "las": "los", "un": "una", "una": "un", "propio": "propia", "propia": "propio", "mismo": "misma", "misma": "mismo"}.get(x, x) \
                                if (x in ("la", "las", "una", "propia", "misma")) != fem and x != "su" else ws2[k]
                            k -= 1
                    t2 = re.sub(r"\s+([?.,!])", r"\1", re.sub(r"([¿¡])\s+", r"\1", " ".join(ws2)))
                    if t2 not in out and sa(t2) != sa(texto):
                        out.append(t2)
    for t2 in ([] if os.environ.get("LCM_SIN_LOCUCIONES") else locuciones(texto)):
        if t2 not in out:
            out.append(t2)
    return out[:maximo + 2]


_T_PERS = ("pres", "pret", "imp", "fut")


def ancla(original, rehecha, cita_):
    """¿Trae la frase citada la palabra NUEVA de la pregunta rehecha? Si no, la cita no viene de la equivalencia y no vale
    («¿quién fabrica las colmenas?» -> «¿quién hace…?» no lo contesta «cada colonia vive en una colmena»)."""
    from . import lectura as L
    viejas = {L._raiz(w) for w in L._contenido(original)}
    nuevas = [w for w in re.findall(r"[a-zñ]+", sa(rehecha.lower())) if len(w) > 2 and L._raiz(w) not in viejas and w not in ("que", "del", "los", "las", "una", "uno")]
    if not nuevas:
        return True
    m = re.search(r"«([^»]+)»", cita_ or "")
    frase = m.group(1) if m else (cita_ or "")
    rf = {w[:4] for w in re.findall(r"[a-zñ]+", sa(frase.lower()))}
    if not any(w[:4] in rf for w in nuevas):
        return False
    for w in re.findall(r"[a-záéíóúñü]+", rehecha.lower()):   # y en el mismo tiempo: lo que PASÓ no lo contesta una costumbre («¿quién levantó el puerto?» / «una grúa levanta…»)
        if L._raiz(w) in viejas:
            continue
        for a_ in analiza(w):
            if len(a_) > 2 and a_[1] in ("pres", "pret", "imp") and sa(a_[0]) not in _FUNC:
                if not casa_tiempo([(a_[0], a_[0], 1.0, "pas" if a_[1] in ("pret", "imp") else "pres")], frase):
                    return False
    return True


def _formas_de(w, lema):
    try:
        return [a for a in (M.analizar(w) or []) if len(a) > 2 and a[1] in _T_PERS and sa(a[0]) == sa(lema)]
    except Exception:                                    # noqa
        return []


def locuciones(texto, maximo=4):
    """2.24 · La misma pregunta cambiando una locución por su verbo o al revés («¿qué da vueltas?» = «¿qué gira?»,
    «¿quién se ocupa del faro?» = «¿quién cuida el faro?»). La lista está en la base de conceptos ([locuciones])."""
    loc = K.kb().get("locuciones") or {}
    if not loc or "?" not in texto:
        return []
    ws = re.findall(r"[\wáéíóúñü]+|[^\w\s]", texto)
    low = [sa(w.lower()) for w in ws]
    out = []

    def _sale(ws2):
        t2 = re.sub(r"\s+([?.,!])", r"\1", re.sub(r"([¿¡])\s+", r"\1", " ".join(x for x in ws2 if x)))
        t2 = re.sub(r"\b(de|a) el\b", lambda m_: "del" if m_.group(1) == "de" else "al", t2)
        t2 = re.sub(r"¿(\w)", lambda m_: "¿" + m_.group(1).upper(), t2)
        if t2 not in out and sa(t2.lower()) != sa(texto.lower()):
            out.append(t2)
    for clave, verbos in loc.items():
        partes = clave.split()
        refl = partes[0].endswith("se") and len(partes[0]) > 4
        lema = partes[0][:-2] if refl else partes[0]
        resto = [sa(x) for x in partes[1:]]
        for i in range(1, len(ws)):
            # la locución está en la pregunta -> el verbo solo
            an = _formas_de(ws[i].lower(), lema)
            j = i + 1 + len(resto)
            cola = low[i + 1:j]
            if resto and resto[-1] == "de" and cola[:-1] == resto[:-1] and cola[-1:] == ["del"]:
                cola, del_ = resto, True                 # «se ocupa DEL faro» -> «cuida EL faro»
            else:
                del_ = False
            if an and cola == resto and (not refl or low[i - 1] == "se"):
                for dest in verbos:
                    drefl = dest.endswith("se") and len(dest) > 4
                    f = M.conjugar(dest[:-2] if drefl else dest, an[0][1], an[0][2])
                    if f:
                        _sale(ws[:i - (1 if refl else 0)] + (["se"] if drefl else []) + [f] + (["el"] if del_ else []) + ws[j:])
            # el verbo solo está en la pregunta -> la locución
            for dest in verbos:
                drefl = dest.endswith("se") and len(dest) > 4
                an2 = _formas_de(ws[i].lower(), dest[:-2] if drefl else dest)
                if an2 and (not drefl or low[i - 1] == "se") and (drefl or low[i - 1] != "se" or refl):
                    f = M.conjugar(lema, an2[0][1], an2[0][2])
                    if f:
                        ws2 = ws[:i - (1 if drefl else 0)] + (["se"] if refl else []) + [f] + partes[1:] + ws[i + 1:]
                        _sale(ws2)
    return out[:maximo]


# ---------------------------------------------------------------- 2.20: por el sentido, con los vectores del léxico
UMBRAL = 0.60        # parecido mínimo para dar dos palabras por intercambiables. Calibrado con el propio léxico (lab/iter220/calibra.py): pasan el 69 % de
#                      los verbos sinónimos y el 85 % de los nombres sinónimos; de los que solo son «hermanos» (perro/gato), el 8 % y el 30 %
UMBRAL_ENLACE = 0.50 # con enlace directo en el léxico basta este parecido
UMBRAL_DUDA = 0.35   # por debajo de los umbrales pero por encima de esto: no se da por bueno, se PREGUNTA al usuario
PUENTE_MIN = 2       # idiomas en que tienen que coincidir dos palabras que el léxico español no enlaza
MARGEN = 0.05        # la elegida tiene que destacar sobre la siguiente palabra aprendida de otro sentido
_FUNC = {"ser", "estar", "haber", "tener", "hacer", "poder", "soler", "ir", "decir", "saber", "querer", "deber", "dar", "ver", "pasar", "llamar"}


def _lemas_v(w):
    try:
        r = {a[0] for a in (M.analizar(w) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut", "inf", "part", "ger")}
    except Exception:                                    # noqa
        r = set()
    return r or {a[0] for a in analiza(w)}


_ALT = (("ie", "e"), ("ue", "o"), ("i", "e"), ("ue", "u"), ("ie", "i"), ("uy", "u"), ("qu", "c"), ("gu", "g"), ("c", "z"), ("zc", "c"))
_TERM = (("an", "ar", "pres", "3p"), ("a", "ar", "pres", "3s"), ("en", "er", "pres", "3p"), ("e", "er", "pres", "3s"), ("en", "ir", "pres", "3p"), ("e", "ir", "pres", "3s"),
         ("aron", "ar", "pret", "3p"), ("ó", "ar", "pret", "3s"), ("ieron", "er", "pret", "3p"), ("ió", "er", "pret", "3s"), ("ieron", "ir", "pret", "3p"), ("ió", "ir", "pret", "3s"))


def analiza(w):
    """Análisis verbal de una forma. Si la morfología no la conoce («ingieren», «muelen»), se busca entre los verbos del léxico,
    deshaciendo la terminación regular y el cambio de vocal de la raíz."""
    try:
        an = [a for a in (M.analizar(w) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut", "inf", "part")]
    except Exception:                                    # noqa
        an = []
    if an or len(w) < 5:
        return an
    try:
        from . import vectores as V
        w2s, _ = V._grafo()
    except Exception:                                    # noqa
        return an
    for term, inf, t, p in _TERM:
        if not w.endswith(term):
            continue
        raiz = w[:len(w) - len(term)]
        for r in [raiz] + [raiz[::-1].replace(x[::-1], y[::-1], 1)[::-1] for x, y in _ALT if x in raiz]:
            lema = sa(r + inf)
            if lema in w2s and V.vector(lema) is not None and len(r) >= 2:
                return [(lema, t, p)]
    return an


_DETS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "del", "al", "de", "este", "esta", "ese", "esa", "cada", "mucho", "mucha", "muchos", "muchas"}
_NO_VERBO = {"para", "se", "como", "sobre", "entre", "bajo", "sal", "ve", "haz", "son", "era", "fue", "una", "uno", "cerca", "nada", "vino", "casa", "cara", "lado", "tarde", "modo"}


def vocabulario(nuc):
    """Las palabras de lo que se ha leído o explicado en esta conversación: verbos (por lema) y nombres o adjetivos (en singular)."""
    textos = []
    for t in (nuc.usuario.get("leido") or []):
        textos += t.get("frases") or []
    textos += [f["src"] for f in getattr(nuc, "F", []) if f.get("src")]
    textos += [x["t"] for x in getattr(nuc, "notas", []) if x.get("t")]
    clave = (len(textos), textos[-1] if textos else "")
    cache = getattr(nuc, "_vocab220", None)
    if cache and cache[0] == clave:
        return cache[1], cache[2]
    verbos, nombres, formas_, acentos_ = set(), set(), {}, {}
    for t in dict.fromkeys(textos):
        ant = ""
        for w in re.findall(r"[a-záéíóúñü]+", t.lower()):
            # 2.21: «el pelo», «para», «se»… no son verbos aunque se escriban como uno
            lv = set() if (ant in _DETS or w in _NO_VERBO) else _lemas_v(w)
            if lv and _solo_yo(w):
                lv = set()                               # 2.24: «líquido», «instrumento»: solo serían verbo en primera persona, y el léxico los tiene como nombre o adjetivo
            if lv:
                verbos |= {sa(x) for x in lv}
                for a_ in analiza(w):                    # 2.24: la forma tal como se leyó («muelen», «siembran»): la morfología no sabe todas las irregulares
                    if len(a_) > 2 and a_[1] in ("pres", "pret", "imp", "fut"):
                        formas_.setdefault(sa(a_[0]), {}).setdefault((a_[1], a_[2]), w)
                try:                                     # 2.22: «puesto», «hecho», «vista»: participios que también son nombres
                    if len(w) > 3 and any(len(a_) > 1 and a_[1] == "part" for a_ in (M.analizar(w) or [])):
                        nombres.add(sa(M.singular(w)))
                except Exception:                        # noqa
                    pass
            elif len(w) > 3:
                nombres.add(sa(M.singular(w)))
                acentos_.setdefault(sa(M.singular(w)), M.singular(w))
            ant = w
    nuc._vocab220 = (clave, verbos, nombres)
    nuc._formas224 = formas_
    nuc._acentos224 = acentos_
    return verbos, nombres


def _solo_yo(w):
    """¿Esta palabra solo es verbo leída como «yo …» o «tú …» y además el léxico la conoce tal cual (nombre o adjetivo)?"""
    from . import vectores as V
    try:
        an = [a for a in (M.analizar(w) or []) if len(a) > 2 and not (a[1] == "pret" and a[2] == "3s" and not w.endswith("ó"))]   # «líquido» no es «liquidó»
    except Exception:                                    # noqa
        an = []
    return bool(an) and all(a[1] in ("pres", "pret", "imp", "fut") and a[2] in ("1s", "2s") for a in an) and V.vector(sa(M.singular(w))) is not None


def conjuga(nuc, lema, t, p):
    """2.24: la forma de un verbo APRENDIDO. Si el texto la trae, esa; si trae otra persona del mismo tiempo, se saca de ella
    («muelen» -> «muele»); y si no, la regular."""
    fs = (getattr(nuc, "_formas224", None) or {}).get(sa(lema), {})
    if (t, p) in fs:
        return fs[(t, p)]
    if t == "pres" and p in ("3s", "3p"):
        otra = fs.get((t, "3p" if p == "3s" else "3s"))
        if otra:
            return otra[:-1] if p == "3s" and otra.endswith("n") else otra + "n" if p == "3p" else otra
    return M.conjugar(lema, t, p)


def _base_n(w, nombres=()):
    """Nombre en singular; si así no está en el léxico y en masculino sí («maestra» -> «maestro»), el masculino."""
    from . import vectores as V
    b = sa(M.singular(w))
    if b in nombres or V.vector(b) is not None:
        return b
    for x in ((b[:-1] + "o",) if b.endswith("a") else ()) + ((b[:-1],) if b.endswith("ora") else ()):
        if x in nombres or V.vector(x) is not None:
            return x
    return b


def _afin(lema, c):
    """Cuánto vale `c` como otra manera de decir `lema` (0 a 1). Dos medidas graduales del mismo léxico, y hacen falta las dos:
    - el parecido de los vectores dice qué parte del significado comparten, pero él solo se equivoca: el 33-45 % de los pares con
      parecido >= 0,6 solo están unidos por una cadena de sinónimos («gratificar» -> «encantar» -> «hipnotizar»);
    - el enlace directo en el grafo (comparten un sentido, o una es una manera de la otra) lo confirma, pero él solo tampoco basta:
      «beber» y «usar» comparten un sentido raro.
    Así que solo cuentan las parejas con enlace directo, y entre ellas manda el vector. «Una manera de» (almacenar -> guardar) no es
    simétrica y el vector no la ve: ahí vale la parte de sentidos enlazados."""
    from . import vectores as V
    tipo, peso = V.parentesco(lema, c)
    if not tipo:
        n = 0 if os.environ.get("LCM_SIN_PUENTE") else V.puente(lema, c)
        # 2.22: sin enlace en español, pero las dos comparten palabra en varios idiomas más («transformar» / «convertir»)
        return min(0.75, UMBRAL_ENLACE + 0.05 * (n - PUENTE_MIN)) if n >= PUENTE_MIN else 0.0
    s = V.sim(lema, c)
    if tipo == "modo":
        return max(s, min(1.0, peso + 0.1) if peso >= 0.5 else 0.0)
    return s if s >= UMBRAL_ENLACE else 0.0


_APR = set()          # parejas que el usuario ha enseñado en esta conversación (se cargan al empezar cada búsqueda)


def aprendidos(nuc):
    return nuc.usuario.setdefault("sinonimos", [])


def aprende(nuc, a, b):
    """El usuario enseña que dos palabras dicen lo mismo. Vale desde ese momento igual que un sinónimo del léxico, y también para
    palabras que el léxico no tiene: la nueva hereda el sitio de la conocida."""
    a, b = sa(a.lower()), sa(b.lower())
    if a and b and a != b and [a, b] not in aprendidos(nuc) and [b, a] not in aprendidos(nuc):
        aprendidos(nuc).append([a, b])
        del aprendidos(nuc)[:-200]
    nuc._vocab220 = None


def _carga_apr(nuc):
    _APR.clear()
    for a, b in (nuc.usuario.get("sinonimos") or []):
        _APR.add((a, b)); _APR.add((b, a))


def _mejor(lema, candidatos):
    """La palabra aprendida que más se parece a esta por el sentido, si se parece lo bastante y destaca."""
    from . import vectores as V
    if lema in candidatos:
        return None
    for c in candidatos:
        if (lema, c) in _APR:
            return c, 1.0                                # enseñado por el usuario
    if V.vector(lema) is None:
        return None
    ps = sorted(((_afin(lema, c), c) for c in candidatos if c != lema and c not in _FUNC and V.vector(c) is not None), reverse=True)[:3]
    if not ps or ps[0][0] < UMBRAL_ENLACE or V.antonimos(lema, ps[0][1]):
        return None
    if len(ps) > 1 and ps[1][0] > ps[0][0] - MARGEN and _afin(ps[0][1], ps[1][1]) < UMBRAL_ENLACE:
        return None                                      # dos candidatas de sentido distinto igual de cerca: no se sabe cuál
    return ps[0][1], ps[0][0]


def evidencia(lema, c):
    """2.24 · Qué indicio hay de que `c` diga lo mismo que `lema`: (valor, clase). Clases:
      "S" segura: enseñada por el usuario, o enlace directo que abarca al menos la mitad de los sentidos y con vectores cercanos;
      "F" firme a medias: pasa el umbral de siempre, pero el enlace es de un sentido entre varios («guiar»/«conducir»);
      "D" débil: hay enlace pero no llega («lavar»/«limpiar»), o solo una cadena de sinónimos con vectores cercanos («surgir»/«nacer»),
          o solo coinciden en otros idiomas. Las débiles nunca valen solas: el resto de la pregunta tiene que estar en la frase.
    None si no hay nada."""
    from . import vectores as V
    if (lema, c) in _APR:
        return 1.0, "S"
    if V.vector(lema) is None or V.vector(c) is None or V.antonimos(lema, c):
        return 0.0, None
    a = _afin(lema, c)
    tipo, peso = V.parentesco(lema, c)
    s = V.sim(lema, c)
    if tipo:
        if a >= UMBRAL and peso >= 0.5 and tipo == "igual":
            return a, "S"
        if a >= UMBRAL_ENLACE:
            return a, "F"
        return max(0.2, 0.5 * (s + peso)), "D"
    if a >= UMBRAL_ENLACE:
        return a, ("F" if a >= UMBRAL else "D")          # puentes entre idiomas: con cuatro o más idiomas de acuerdo pasa el umbral
    if s >= UMBRAL and V.dos_pasos(lema, c):
        return 0.5 * s, "D"
    if V.puente(lema, c) == 1 and not os.environ.get("LCM_SIN_PUENTE1") and not os.environ.get("LCM_SIN_PUENTE"):
        return 0.36, "D"                                 # coinciden en un solo idioma más («trabajar» / «funcionar»: ing. work): lo justo para probar, o para preguntar
    return 0.0, None


def candidatas(lema, candidatos, k=3, solo_seguras=False):
    """Las palabras aprendidas que podrían decir lo mismo que `lema`, de más a menos indicio: [(palabra, valor, clase)]."""
    if os.environ.get("LCM_SENTIDO_UNA"):                # (interruptor de medida: la conducta de la 2.23, una sola candidata)
        m = _mejor(lema, candidatos) if lema not in candidatos else None
        return [(m[0], m[1], "S")] if m and not solo_seguras else []
    out = []
    for c in candidatos:
        if c == lema or (c in _FUNC and c != "hacer"):   # «hacer» sí: «fabricar», «elaborar», «construir» son maneras de hacer
            continue
        v, cl = evidencia(lema, c)
        if c == "hacer" and cl:                          # casi todo es una manera de hacer: solo vale de entrada si lo es en TODOS sus sentidos («fabricar»)
            from . import vectores as V
            tipo, peso = V.parentesco(lema, c)
            v, cl = (v, "F") if (tipo == "modo" and peso >= 0.9) else (0.25 * v, "D")
        if solo_seguras and cl == "F" and v >= 0.8:
            cl = "D"                                     # una palabra que SÍ está en lo aprendido solo se cambia por otra con apoyo en la frase
        elif solo_seguras and cl != "S":
            cl = None
        if cl:
            out.append((c, v, cl))
    out.sort(key=lambda x: ({"S": 0, "F": 1, "D": 2}[x[2]], -x[1]))
    if len(out) > 1 and out[0][2] == "F" and out[1][2] == "F" and out[1][1] > out[0][1] - MARGEN and evidencia(out[0][0], out[1][0])[1] not in ("S", "F"):
        out = [(c, v, "D") if cl == "F" else (c, v, cl) for c, v, cl in out]   # dos candidatas de sentido distinto igual de cerca: ninguna vale sin apoyo en la frase
    return out[:k]


def propuestas(nuc, texto, maximo=8):
    """2.24 · La pregunta rehecha con palabras de lo aprendido, UNA palabra cada vez y con VARIAS candidatas por palabra: quién decide
    entre ellas es el texto (la que deja una pregunta que lo aprendido contesta). Devuelve [(pregunta, cambios, clase, valor)].
    También se prueban las palabras que SÍ están en lo aprendido si tienen allí un sinónimo seguro («pacientes» / «enfermos»)."""
    from . import vectores as V
    if "?" not in texto or os.environ.get("LCM_SIN_SENTIDO") or not V.disponible():
        return []
    verbos, nombres = vocabulario(nuc)
    if not verbos and not nombres:
        return []
    _carga_apr(nuc)
    ws = re.findall(r"[\wáéíóúñü]+|[^\w\s]", texto)
    out = []
    for i, w in enumerate(ws):
        wl = w.lower()
        if i == 0 or not wl.isalpha() or len(wl) < 4 or (w[:1].isupper() and i > 1):
            continue
        an = [] if (wl in _NO_VERBO or _solo_yo(wl)) else analiza(wl)
        if an and ws[i - 1].lower() in ("el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "del", "al", "de") \
                and not (i > 1 and ws[i - 2].lower() in ("qué", "que", "quién", "quien", "no", "se", "cuándo", "dónde", "cómo")):
            an = []                                      # tras un determinante es un nombre («las crías»); tras «qué los…» es un verbo con su pronombre
        if an:
            a0 = an[0]
            lema = sa(a0[0])
            if lema in _FUNC:
                continue
            dentro = lema in verbos
            if dentro and os.environ.get("LCM_SENTIDO_FUERA"):
                continue
            for k_, (c, v, cl) in enumerate(candidatas(lema, verbos, solo_seguras=dentro)):
                forma = c if a0[1] == "inf" else conjuga(nuc, c, a0[1], a0[2]) if a0[1] != "part" else None
                if forma:
                    out.append((i, forma, a0[0], c, v, "pas" if a0[1] in ("pret", "imp") else "pres" if a0[1] == "pres" else "", cl, dentro, k_))
            continue
        base = _base_n(wl, nombres)
        if K.kb().get("clases", {}).get(base) and base not in nombres and V.vector(base) is None:
            continue
        dentro = base in nombres or sa(wl) in nombres
        if dentro and os.environ.get("LCM_SENTIDO_FUERA"):
            continue
        pl = wl.endswith("s") and sa(M.singular(wl)) != sa(wl)
        ac_ = getattr(nuc, "_acentos224", None) or {}
        for k_, (c, v, cl) in enumerate(candidatas(base, nombres, solo_seguras=dentro)):
            c_ = ac_.get(c, c)                           # tal como se leyó, con su tilde
            out.append((i, M.plural(c_) if pl else c_, M.singular(wl) if sa(M.singular(wl)) == base else base, c_, v, "", cl, dentro, k_))
    res = []
    orden_cl = {"S": 0, "F": 1, "D": 2}

    def _monta(cs):
        ws2 = list(ws)
        for c in cs:
            i, forma, dest = c[0], c[1], c[3]
            ws2[i] = forma
            if i > 0 and ws2[i - 1].lower() in ("el", "la", "los", "las", "un", "una") and not analiza(ws[i].lower()):
                fem = M.genero_sust(sa(dest)) == "f"
                x = ws2[i - 1].lower()
                if (x in ("la", "las", "una")) != fem:
                    ws2[i - 1] = {"el": "la", "la": "el", "los": "las", "las": "los", "un": "una", "una": "un"}[x]
        t2 = re.sub(r"\s+([?.,!])", r"\1", re.sub(r"([¿¡])\s+", r"\1", " ".join(ws2)))
        t2 = re.sub(r"¿(\w)", lambda m_: "¿" + m_.group(1).upper(), t2)
        return (t2, [(c[2], c[3], round(c[4], 2), c[5]) for c in cs], max((c[6] for c in cs), key=lambda x: orden_cl[x]), min(c[4] for c in cs), max(c[8] for c in cs))
    fuera = [c for c in out if not c[7] and c[8] == 0]
    if len({c[0] for c in fuera}) > 1:                   # dos palabras de la pregunta que no están en lo aprendido: las dos a la vez, cada una con su mejor candidata
        res.append(_monta(sorted(fuera, key=lambda c: c[0])))
    for c in sorted(out, key=lambda c: (c[7], orden_cl[c[6]], -c[4])):
        res.append(_monta([c]))
    return res[:maximo]


def _entera(w):
    w = sa(w.lower())
    return sa(M.singular(w)) if len(w) > 3 else w


def _fondo(nuc):
    """De lo que trata todo lo leído (lo que sale en muchas frases): que la frase lo traiga no prueba nada. Palabras enteras, no raíces:
    «cafeto» y «cafetería» no son lo mismo."""
    from . import lectura as L
    cuenta = {}
    for t in (nuc.usuario.get("leido") or []):
        temas = t.get("temas") or {}
        for f in (t.get("frases") or []):
            for r in {_entera(w) for w in L._contenido(f + " " + (temas.get(f) or ""))}:   # con su tema: «Viven en colonias» también habla de los pingüinos
                cuenta[r] = cuenta.get(r, 0) + 1
        fs = t.get("frases") or []
        if fs:
            for r in {_entera(w) for w in L._contenido(" ".join(fs[0].split()[:4]))}:
                cuenta[r] = cuenta.get(r, 0) + 99
    return {r for r, c in cuenta.items() if c >= 3}


def apoyo(nuc, pregunta, cambios, fuente):
    """¿Trae la frase (o la respuesta con sus fuentes) lo demás que se pregunta? Es la prueba que hace valer un indicio débil.
      "firme":  trae todo lo demás, y es algo más que el tema del texto («¿quiénes mueven las camillas por los pasillos?» con
                «…empujan las camillas por los pasillos»);
      "neutro": no hay nada más que comprobar («¿qué beben los pingüinos?» con «usan sus alas…»: solo coincide el tema);
      "falla":  la pregunta pide algo que la frase no trae («¿qué PAÍS prepara MÁS café?» con «los baristas preparan café»)."""
    from . import lectura as L
    rf = {_entera(w)[:6] for w in L._contenido(fuente or "")}   # seis letras: con cinco, «cafeto» y «cafetería» serían la misma
    dest = {sa(c[1]) for c in cambios}
    fondo = _fondo(nuc)
    rq = set()
    propios = {w.lower() for w in re.findall(r"(?<![¿?¡!.]\s)(?<!^)(?<![¿¡])\b[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+", pregunta)}
    ws_ = re.findall(r"[a-záéíóúñü0-9]+", pregunta.lower())
    for k_, w in enumerate(ws_):
        if sa(w) in L._VACIAS or len(w) < 2:
            continue
        if w in propios:
            continue                                     # 2.25: de quién se habla (un nombre propio) no es apoyo: «Pablo mide…» no contesta «¿cuánto pesa Pablo?»
        if k_ > 0 and sa(ws_[k_ - 1]) in ("que", "cual", "cuales", "cuanto", "cuanta", "cuantos", "cuantas") and k_ <= 2:
            continue                                     # «¿qué PIEZA…?», «¿qué PAÍS…?»: dice de qué tipo es lo que se pide, no algo que la frase tenga que repetir
        if {sa(a_[0]) for a_ in analiza(w)} & dest or _base_n(w) in dest:
            continue                                     # la palabra cambiada, en la forma que sea
        if _entera(w) not in fondo and L._raiz(w) not in L._GEN_Q:   # el tema del texto no hace falta que cada frase lo repita, y que lo traiga no prueba nada
            rq.add(_entera(w)[:6])
    if not rq:
        return "neutro"
    return "firme" if rq <= rf else "falla"


def dos_lecturas(palabra, a, b):
    """Dos palabras aprendidas pueden ser la que se pregunta y cada una lleva a una respuesta distinta: se dan las dos, dicho así."""
    def _limpia(r):
        return re.sub(r"\s*Entiendo «[^»]+» como «[^»]+»\.$", "", (r or "").strip())
    return f"Depende de qué quiera decir «{palabra}». Si es «{a[0]}»: {_limpia(a[1])} Si es «{b[0]}»: {_limpia(b[1])}"


def _casi(lema, candidatos):
    """Candidatas que NO llegan para darlas por buenas, pero se parecen lo bastante para preguntar («vigilar» ~ «cuidar», 0,41).
    Hasta tres: se preguntará por la primera con la que la pregunta tenga respuesta."""
    from . import vectores as V
    if lema in candidatos or V.vector(lema) is None:
        return []
    ps = sorted(((V.sim(lema, c), c) for c in candidatos if c != lema and c not in _FUNC and V.vector(c) is not None and not V.antonimos(lema, c)), reverse=True)[:3]
    return [(c, s_) for s_, c in ps if s_ >= UMBRAL_DUDA and V.parentesco(lema, c)[0]]   # con algún enlace en el léxico, aunque sea débil: sin él, el parecido solo es ruido


def por_sentido(nuc, texto, maximo=4, duda=False):
    """La misma pregunta dicha con las palabras de lo aprendido: cada palabra de la pregunta que no aparece en lo leído se cambia por
    la palabra leída de sentido más cercano. Devuelve [(pregunta, [(palabra, por, parecido)])]. Nada si no hay vectores."""
    from . import vectores as V
    if "?" not in texto or os.environ.get("LCM_SIN_SENTIDO") or not V.disponible():
        return []
    verbos, nombres = vocabulario(nuc)
    if not verbos and not nombres:
        return []
    _carga_apr(nuc)
    ws = re.findall(r"[\wáéíóúñü]+|[^\w\s]", texto)
    cambios = []
    for i, w in enumerate(ws):
        wl = w.lower()
        if i == 0 or not wl.isalpha() or len(wl) < 4 or (w[:1].isupper() and i > 1):
            continue
        an = [] if wl in _NO_VERBO else analiza(wl)
        if an and ws[i - 1].lower() in ("el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus", "del", "al", "de"):
            an = []                                      # 2.21: tras un determinante es un nombre («las crías»), no un verbo
        if an:
            a0 = an[0]
            lema = sa(a0[0])
            if lema in _FUNC or lema in verbos:
                continue
            ms = _casi(lema, verbos) if duda else [x for x in [_mejor(lema, verbos)] if x]
            for m in ms:
                forma = m[0] if a0[1] == "inf" else M.conjugar(m[0], a0[1], a0[2]) if a0[1] != "part" else None
                if forma:
                    cambios.append((i, forma, a0[0], m[0], m[1], "pas" if a0[1] in ("pret", "imp") else "pres" if a0[1] == "pres" else ""))
            continue
        base = sa(M.singular(wl))
        if base in nombres or sa(wl) in nombres or K.kb().get("clases", {}).get(base):
            continue
        m = _mejor(base, nombres) if not duda else None
        if m:
            pl = wl.endswith("s") and base != sa(wl)
            cambios.append((i, M.plural(m[0]) if pl else m[0], base, m[0], m[1], ""))
    if not cambios:
        return []
    out = []

    def _monta(cs):
        ws2 = list(ws)
        for i, forma, _, dest, _s, _t in cs:
            ws2[i] = forma
            if i > 0 and ws2[i - 1].lower() in ("el", "la", "los", "las", "un", "una") and not _lemas_v(ws[i].lower()):
                fem = M.genero_sust(sa(dest)) == "f"
                x = ws2[i - 1].lower()
                if (x in ("la", "las", "una")) != fem:
                    ws2[i - 1] = {"el": "la", "la": "el", "los": "las", "las": "los", "un": "una", "una": "un"}[x]
        t2 = re.sub(r"\s+([?.,!])", r"\1", re.sub(r"([¿¡])\s+", r"\1", " ".join(ws2)))
        return re.sub(r"¿(\w)", lambda m_: "¿" + m_.group(1).upper(), t2), [(c[2], c[3], round(c[4], 2), c[5]) for c in cs]
    if len(cambios) > 1 and not duda:
        out.append(_monta(cambios))
    for c in sorted(cambios, key=lambda c: -c[4]):
        out.append(_monta([c]))
    return out[:maximo]


def aviso(cambios, respuesta):
    """La respuesta y, detrás, con qué palabra se ha entendido la pregunta: quien pregunta puede ver si el parecido era bueno."""
    from . import vectores as V
    def _una(c):                                         # 2.24: si una es un tipo de la otra, se dice así («paciente» no es otra forma de decir «enfermo»: es un enfermo)
        try:
            if len(c) > 3 and c[3] == "" and not c[0].endswith(("ar", "er", "ir")) and V.tipo_de(c[0], c[1]):
                return f"«{c[0]}» como un tipo de «{c[1]}»"
        except Exception:                                # noqa
            pass
        return f"«{c[0]}» como «{c[1]}»"
    nota = "Entiendo " + " y ".join(_una(c) for c in cambios) + "."
    r = (respuesta or "").rstrip()
    return (r if r[-1:] in ".!?»" else r + ".") + " " + nota


def casa_tipo(pregunta, respuesta):
    """2.22: una pregunta rehecha por el sentido tiene que recibir el tipo de dato que pide: «¿cuánto…?» pide una cantidad."""
    q = sa(pregunta.lower())
    if re.match(r"^\W*(?:y\s+)?(?:con |de |en |a )?cuant[oa]s?\b", q):
        from . import lectura as _L
        r = sa((respuesta or "").lower())
        return _L._NUM_RE.search(r) is not None or re.search(r"\b(?:semanas?|meses|anos?|dias?|horas?|minutos?|kilos?|metros?|litros?|euros?)\b", r) is not None
    return True


def casa_tiempo(cambios, respuesta):
    """Una pregunta por algo que PASÓ («¿quién inventó…?») no la contesta una costumbre en presente («se construyen…»), y al revés.
    Solo se exige a los verbos cambiados por el sentido: es donde hay riesgo de casar dos cosas que no son la misma."""
    for c in cambios:
        if len(c) < 4 or not c[3]:
            continue
        ts = set()
        for w in re.findall(r"[a-záéíóúñü]+", (respuesta or "").lower()):
            try:
                ts |= {"pas" if a[1] in ("pret", "imp") else "pres" for a in ((M.analizar(w) or []) + analiza(w)) if len(a) > 2 and sa(a[0]) == sa(c[1]) and a[1] in ("pres", "pret", "imp")}
            except Exception:                            # noqa
                pass
        if not ts or c[3] not in ts:
            return False                                 # 2.22: y la respuesta tiene que usar ese verbo: si no, no es la pregunta rehecha lo que se contesta
    return True


_DECL = re.compile(r"^\W*«?\"?(?:(?:un|una|el|la)\s+)?([a-záéíóúñü]+)»?\"?\s+(?:es lo mismo que|significa lo mismo que|quiere decir lo mismo que|significa|quiere decir|es sin[oó]nimo de|"
                   r"es igual que|es como decir|es otra forma de decir|es otra manera de decir)\s+«?\"?(?:(?:un|una|el|la)\s+)?([a-záéíóúñü]+)»?\"?\W*$", re.I)


def declara(nuc, texto):
    """«Vigilar es lo mismo que cuidar», «un zarpo es lo mismo que un barco»: el usuario enseña un sinónimo. Devuelve la respuesta o None."""
    m = _DECL.match(texto.strip())
    if not m or "?" in texto:
        return None
    a, b = m.group(1).lower(), m.group(2).lower()
    if sa(a) == sa(b) or len(a) < 3 or len(b) < 3:
        return None
    la, lb = (analiza(a) or [(a,)])[0][0], (analiza(b) or [(b,)])[0][0]
    if a.endswith(("ar", "er", "ir")) != b.endswith(("ar", "er", "ir")):
        return None                                      # un verbo y un nombre: eso no es un sinónimo, es otra cosa
    if not a.endswith(("ar", "er", "ir")):
        la, lb = sa(M.singular(a)), sa(M.singular(b))
    aprende(nuc, la, lb)
    return {"respuesta": f"Entendido: «{a}» y «{b}» quieren decir lo mismo. Lo tendré en cuenta cuando me preguntes.", "estado": "ok", "consultar": False, "tipo": "ack"}


def desconocida(nuc, texto):
    """El verbo de la pregunta que no aparece en nada de lo leído o explicado (si es justo uno y hay algo aprendido). Sirve para decir
    por qué no se sabe contestar y para que el usuario pueda enseñar el sinónimo."""
    if "?" not in texto or not (nuc.usuario.get("leido") or []):
        return None
    verbos, _ = vocabulario(nuc)
    if len(verbos) < 3:
        return None
    ws = re.findall(r"[a-záéíóúñü]+", texto.lower())
    fuera = []
    for i, w in enumerate(ws):
        if i == 0 or len(w) < 4 or w in _NO_VERBO or ws[i - 1] in _DETS:
            continue
        an = [a for a in analiza(w) if a[1] in ("pres", "pret", "imp", "fut")]
        if an and sa(an[0][0]) not in verbos and sa(an[0][0]) not in _FUNC and not any(sa(a[0]) in verbos or sa(a[0]) in _FUNC for a in an):
            fuera.append(an[0][0])
    return fuera[0] if len(set(fuera)) == 1 else None


def cita_firme(nuc, pregunta, cambios, cita_):
    """2.22: cuando el cambio de palabra se apoya solo en un indicio débil (los puentes entre idiomas, sin enlace en el léxico español ni
    enseñado por el usuario), la frase citada tiene que traer ella misma todo lo demás que se pregunta; no vale «de eso va el texto»."""
    from . import vectores as V
    from . import lectura as L
    _carga_apr(nuc)
    debil = [c for c in cambios if not V.parentesco(c[0], c[1])[0] and (sa(c[0]), sa(c[1])) not in _APR]
    if not debil:
        return True
    m = re.search(r"«([^»]+)»", cita_ or "")
    rf = {L._raiz(w) for w in L._contenido(m.group(1) if m else (cita_ or ""))}   # sin comillas: es una respuesta del núcleo, vale entera
    rq = {L._raiz(w) for w in L._contenido(pregunta)} - L._GEN_Q
    return rq <= rf
