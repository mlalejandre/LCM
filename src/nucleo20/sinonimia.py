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
    return out[:maximo]


# ---------------------------------------------------------------- 2.20: por el sentido, con los vectores del léxico
UMBRAL = 0.60        # parecido mínimo para dar dos palabras por intercambiables. Calibrado con el propio léxico (lab/iter220/calibra.py): pasan el 69 % de
#                      los verbos sinónimos y el 85 % de los nombres sinónimos; de los que solo son «hermanos» (perro/gato), el 8 % y el 30 %
UMBRAL_ENLACE = 0.50 # con enlace directo en el léxico basta este parecido
MARGEN = 0.05        # la elegida tiene que destacar sobre la siguiente palabra aprendida de otro sentido
_FUNC = {"ser", "estar", "haber", "tener", "hacer", "poder", "soler", "ir", "decir", "saber", "querer", "deber", "dar", "ver", "pasar", "llamar"}


def _lemas_v(w):
    try:
        r = {a[0] for a in (M.analizar(w) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut", "inf", "part", "ger")}
    except Exception:                                    # noqa
        r = set()
    return r or {a[0] for a in analiza(w)}


_ALT = (("ie", "e"), ("ue", "o"), ("i", "e"), ("ue", "u"))
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
    verbos, nombres = set(), set()
    for t in dict.fromkeys(textos):
        for w in re.findall(r"[a-záéíóúñü]+", t.lower()):
            lv = _lemas_v(w)
            if lv:
                verbos |= {sa(x) for x in lv}
            elif len(w) > 3:
                nombres.add(sa(M.singular(w)))
    nuc._vocab220 = (clave, verbos, nombres)
    return verbos, nombres


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
        return 0.0
    s = V.sim(lema, c)
    if tipo == "modo":
        return max(s, min(1.0, peso + 0.1) if peso >= 0.5 else 0.0)
    return s if s >= UMBRAL_ENLACE else 0.0


def _mejor(lema, candidatos):
    """La palabra aprendida que más se parece a esta por el sentido, si se parece lo bastante y destaca."""
    from . import vectores as V
    if lema in candidatos or V.vector(lema) is None:
        return None
    ps = sorted(((_afin(lema, c), c) for c in candidatos if c != lema and c not in _FUNC and V.vector(c) is not None), reverse=True)[:3]
    if not ps or ps[0][0] < UMBRAL_ENLACE or V.antonimos(lema, ps[0][1]):
        return None
    if len(ps) > 1 and ps[1][0] > ps[0][0] - MARGEN and _afin(ps[0][1], ps[1][1]) < UMBRAL_ENLACE:
        return None                                      # dos candidatas de sentido distinto igual de cerca: no se sabe cuál
    return ps[0][1], ps[0][0]


def por_sentido(nuc, texto, maximo=4):
    """La misma pregunta dicha con las palabras de lo aprendido: cada palabra de la pregunta que no aparece en lo leído se cambia por
    la palabra leída de sentido más cercano. Devuelve [(pregunta, [(palabra, por, parecido)])]. Nada si no hay vectores."""
    from . import vectores as V
    if "?" not in texto or os.environ.get("LCM_SIN_SENTIDO") or not V.disponible():
        return []
    verbos, nombres = vocabulario(nuc)
    if not verbos and not nombres:
        return []
    ws = re.findall(r"[\wáéíóúñü]+|[^\w\s]", texto)
    cambios = []
    for i, w in enumerate(ws):
        wl = w.lower()
        if i == 0 or not wl.isalpha() or len(wl) < 4 or (w[:1].isupper() and i > 1):
            continue
        an = analiza(wl)
        if an:
            a0 = an[0]
            lema = sa(a0[0])
            if lema in _FUNC or lema in verbos:
                continue
            m = _mejor(lema, verbos)
            if m:
                forma = m[0] if a0[1] == "inf" else M.conjugar(m[0], a0[1], a0[2]) if a0[1] != "part" else None
                if forma:
                    cambios.append((i, forma, a0[0], m[0], m[1], "pas" if a0[1] in ("pret", "imp") else "pres" if a0[1] == "pres" else ""))
            continue
        base = sa(M.singular(wl))
        if base in nombres or sa(wl) in nombres or K.kb().get("clases", {}).get(base):
            continue
        m = _mejor(base, nombres)
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
    if len(cambios) > 1:
        out.append(_monta(cambios))
    for c in sorted(cambios, key=lambda c: -c[4]):
        out.append(_monta([c]))
    return out[:maximo]


def aviso(cambios, respuesta):
    """La respuesta y, detrás, con qué palabra se ha entendido la pregunta: quien pregunta puede ver si el parecido era bueno."""
    nota = "Entiendo " + " y ".join(f"«{c[0]}» como «{c[1]}»" for c in cambios) + "."
    r = (respuesta or "").rstrip()
    return (r if r[-1:] in ".!?»" else r + ".") + " " + nota


def casa_tiempo(cambios, respuesta):
    """Una pregunta por algo que PASÓ («¿quién inventó…?») no la contesta una costumbre en presente («se construyen…»), y al revés.
    Solo se exige a los verbos cambiados por el sentido: es donde hay riesgo de casar dos cosas que no son la misma."""
    for c in cambios:
        if len(c) < 4 or not c[3]:
            continue
        ts = set()
        for w in re.findall(r"[a-záéíóúñü]+", (respuesta or "").lower()):
            try:
                ts |= {"pas" if a[1] in ("pret", "imp") else "pres" for a in (M.analizar(w) or []) if len(a) > 2 and sa(a[0]) == sa(c[1]) and a[1] in ("pres", "pret", "imp")}
            except Exception:                            # noqa
                pass
        if ts and c[3] not in ts:
            return False
    return True
