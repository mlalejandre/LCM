"""LCM 2.26 · El hilo de la conversación: el orden de los pasos y lo que deja de ser verdad.

Tres cosas que una persona da por supuestas al hablar y que no son hechos del mundo, sino de cómo se cuenta:
- quien explica algo con «primero… luego… después… al final» está dando PASOS EN ORDEN, y luego pregunta por ese orden;
- «tengo que A y B» abre tareas, y «ya he A» las va cerrando: lo que falta es la diferencia;
- «ya» marca un cambio: si después de «X está en el taller» se dice «ya lo recogí», a «¿sigue en el taller?» se contesta que ya no.
"""
from __future__ import annotations

import os
import re

from . import morfo as M
from .morfo import sa

_INICIO = ("primero", "lo primero", "para empezar", "en primer lugar")
_FIN = ("por ultimo", "al final", "finalmente", "para terminar", "para acabar")
_MARCA = re.compile(r"^(primero|lo primero|para empezar|en primer lugar|luego|después|despues|a continuación|a continuacion|entonces|más tarde|mas tarde|seguidamente|en segundo lugar|"
                    r"por último|por ultimo|al final|finalmente|para terminar|para acabar)\b,?\s+(?!de\b|que\b)", re.I)


def _lemas(texto):
    out = set()
    from . import lectura as L
    for w in re.findall(r"[a-záéíóúñü]+", texto.lower()):
        if sa(w) in L._VACIAS or len(w) < 3:
            continue
        try:
            an = M.analizar(w) or []
        except Exception:                                # noqa
            an = []
        out |= {sa(a[0]) for a in an if a and a[0]}
        out.add(L._raiz(w))
    return out


def a_ti(texto):
    """«caliento el agua y muelo mi café» dicho a quien lo contó: «calientas el agua y mueles tu café»."""
    from .preguntas import cambia_persona
    ws = texto.split()
    for i, w in enumerate(ws):
        if i > 0 and sa(ws[i - 1].lower()) in ("el", "la", "los", "las", "un", "una", "mi", "mis", "del", "al", "de") \
                and not (i > 1 and sa(ws[i - 1].lower()) in ("la", "los", "las") and sa(ws[i - 2].lower().strip(",")) in ("y", "luego", "despues", "no")):
            continue
        try:
            an = [a for a in (M.analizar(w.lower().strip(",")) or []) if len(a) > 2 and a[1] in ("pres", "pret", "imp", "fut") and a[2] == "1s"]
        except Exception:                                # noqa
            an = []
        verbal = i == 0 or sa(ws[i - 1].lower()) in ("y", "luego", "despues", "no", "me", "lo", "la", "los", "las", "le", "les", "se", "tambien", "ya")
        if an and verbal:
            f = M.conjugar(an[0][0], an[0][1], "2s")
            if f:
                ws[i] = f + ("," if w.endswith(",") else "")
        elif not an and verbal and len(w) > 3 and w.lower().strip(",").endswith("o"):
            f = _tu_irregular(w.lower().strip(","))      # «muelo», «frío»: la morfología no los conoce; se busca el verbo en el léxico
            if f:
                ws[i] = f + ("," if w.endswith(",") else "")
    t = cambia_persona(" ".join(ws))
    return re.sub(r"\bme\b", "te", t)


def _tu_irregular(w):
    try:
        from . import vectores as V
        from .sinonimia import _ALT
        w2s, _ = V._grafo()
    except Exception:                                    # noqa
        return None
    raiz = w[:-1]
    for r in [raiz] + [raiz[::-1].replace(x[::-1], y[::-1], 1)[::-1] for x, y in _ALT if x in raiz]:
        for inf in ("ar", "er", "ir"):
            if sa(r + inf) in w2s and V.vector(sa(r + inf)) is not None and len(r) >= 2:
                return raiz + ("as" if inf == "ar" else "es")
    return None


def apunta_dicho(nuc, texto):
    """Lo dicho en primera persona, tal cual y en orden: de ahí salen las tareas («tengo que…») y lo que ya se hizo."""
    t = texto.strip()
    if "?" in t or len(t) > 240 or "\n" in t:
        return
    D = nuc.usuario.setdefault("dichos226", [])
    D.append(t)
    del D[:-60]


def apunta_paso(nuc, texto):
    """Guarda la frase como un paso si empieza por una marca de orden. «Primero…» abre un procedimiento nuevo."""
    apunta_dicho(nuc, texto)
    t = texto.strip()
    m = _MARCA.match(t)
    if not m or "?" in t or len(t.split()) < 3 or len(t) > 200:
        return False
    marca = sa(m.group(1).lower())
    P = nuc.usuario.setdefault("pasos", [])
    if marca in _INICIO or (P and nuc.turno - P[-1].get("turno", -99) > 6):
        del P[:]
    P.append({"t": t[m.end():].strip().rstrip(".!"), "turno": nuc.turno, "fin": marca in _FIN})
    del P[:-30]
    nuc._paso_ptr = len(P) - 1
    return True


def _ok(txt):
    return {"respuesta": txt, "estado": "ok", "consultar": False, "tipo": "resp"}


def _cap(x):
    return x[:1].upper() + x[1:]


def pasos(nuc, q):
    P = nuc.usuario.get("pasos") or []
    if len(P) < 2:
        return None
    qn = re.sub(r"\s+", " ", sa(q.lower()).strip(" ¿?¡!."))
    qn = re.sub(r"^y ", "", qn)
    hago = r"(?:hago|hacemos|hay que hacer|se hace|toca|va|viene)"
    if re.match(r"^(?:que " + hago + r" (?:primero|lo primero|para empezar|al principio)|cual es el primer paso|que es lo primero(?: que hago)?|por donde (?:empiezo|se empieza)|como empiezo)$", qn):
        nuc._paso_ptr = 0
        return _ok(f"Primero {a_ti(P[0]['t'])}.")
    if re.match(r"^(?:que " + hago + r" (?:al final|por ultimo|lo ultimo|para terminar|para acabar)|cual es el ultimo paso|que es lo ultimo(?: que hago)?|como (?:termino|acabo))$", qn):
        nuc._paso_ptr = len(P) - 1
        return _ok(f"Lo último: {a_ti(P[-1]['t'])}.")
    if re.match(r"^cuantos pasos (?:son|hay|tiene|tengo)\b", qn):
        return _ok(f"{_cap(M.num_pal(len(P)) if len(P) < 30 else str(len(P)))} pasos: " + "; ".join(a_ti(p["t"]) for p in P) + ".")
    if re.match(r"^(?:cuales son los pasos|que pasos (?:son|hay|tiene)|repiteme los pasos|como era)\b", qn):
        return _ok("Por orden: " + "; ".join(a_ti(p["t"]) for p in P) + ".")
    m = re.match(r"^que " + hago + r" (despues de|tras|antes de|luego de) (.+)$", qn)
    if m:
        lx = _lemas(m.group(2))
        pts = sorted(((len(lx & _lemas(p["t"])), -k) for k, p in enumerate(P)), reverse=True)
        if not lx or pts[0][0] == 0 or (len(pts) > 1 and pts[1][0] == pts[0][0]):
            return None
        k = -pts[0][1]
        antes = m.group(1).startswith("antes")
        j = k - 1 if antes else k + 1
        if j < 0:
            return _ok(f"Nada: ese es el primer paso ({a_ti(P[k]['t'])}).")
        if j >= len(P):
            return _ok(f"Nada más: ese es el último paso ({a_ti(P[k]['t'])}).")
        nuc._paso_ptr = j
        return _ok(f"{'Antes' if antes else 'Después'} {a_ti(P[j]['t'])}.")
    if re.match(r"^(?:que " + hago + r" (?:despues|luego|a continuacion)|(?:y )?(?:despues|luego)(?: que)?|que viene (?:despues|luego))$", qn):
        j = getattr(nuc, "_paso_ptr", -1) + 1
        if 0 <= j < len(P):
            nuc._paso_ptr = j
            return _ok(f"Después {a_ti(P[j]['t'])}.")
        return _ok("Nada más: ese era el último paso.")
    return None


def _tareas(nuc):
    """[(texto de la tarea, posición en lo dicho)] de lo dicho con «tengo que…»."""
    out = []
    for i, src in enumerate(nuc.usuario.get("dichos226") or []):
        m = re.search(r"\b(?:tengo|tenemos|debo|he de)\s+(?:que\s+)?(.+?)[.!]?$", src, re.I)
        if not m or not re.search(r"\b(?:tengo que|tenemos que|debo|he de)\b", sa(src.lower())) or re.search(r"\bno (?:tengo|tenemos|debo)\b", sa(src.lower())):
            continue
        cuerpo = re.sub(r"\s+(?:hoy|mañana|manana|esta tarde|esta mañana|esta noche|luego|después|despues|antes de [^,]+)$", "", m.group(1).strip(), flags=re.I)
        partes = []
        for trozo in re.split(r",\s*(?:y\s+)?|\s+y\s+|\s+e\s+", cuerpo):
            w0 = sa(trozo.strip().split()[0].lower()) if trozo.strip() else ""
            if re.search(r"(?:ar|er|ir)(?:se|me|lo|la|los|las|le)?$", w0) and len(w0) > 3:
                partes.append(trozo.strip())
            elif partes:
                partes[-1] += " y " + trozo.strip()
        for p in partes:
            if not any(sa(p.lower()) == sa(x[0].lower()) for x in out):
                out.append((p, i))
    return out


def _hecha(nuc, tarea, i0):
    """¿Se dijo después que eso ya se hizo? («ya he regado las plantas», «pagué el alquiler»): mismo verbo y, si la tarea lo tiene, mismo objeto."""
    ws = tarea.split()
    inf = re.sub(r"(?:se|me|lo|la|los|las|le)$", "", sa(ws[0].lower()))
    from . import lectura as L
    objs = {L._raiz(w) for w in L._contenido(" ".join(ws[1:]))}
    for src in (nuc.usuario.get("dichos226") or [])[i0 + 1:]:
        n_ = sa(src.lower())
        if re.search(r"\b(?:tengo que|tenemos que|debo|no he|todavia no|aun no)\b", n_):
            continue
        hecho = False
        for w in re.findall(r"[a-záéíóúñü]+", src.lower()):
            try:
                an = M.analizar(w) or []
            except Exception:                            # noqa
                an = []
            if any(sa(a[0]) == inf and len(a) > 1 and (a[1] == "part" or (a[1] == "pret" and len(a) > 2 and a[2] in ("1s", "1p"))) for a in an):
                hecho = True
        if hecho and (not objs or objs & {L._raiz(w) for w in L._contenido(src)}):
            return True
    return False


def pendientes(nuc, q):
    qn = sa(q.lower()).strip(" ¿?¡!.")
    ts = _tareas(nuc)
    if not ts:
        return None
    if re.match(r"^(?:y )?que (?:tengo|tenemos) que hacer(?: hoy| manana| ahora)?$", qn) and all(not _hecha(nuc, t, i) for t, i in ts):
        return _ok(f"Tienes que {nuc._lista([a_ti(t) for t, i in ts])}.")
    if not re.search(r"\b(?:que|algo|mucho) (?:mas )?(?:me |nos )?(?:falta|queda)\b|\b(?:me|nos) (?:falta|queda) (?:algo|mucho|alguna cosa)\b|\bque (?:tengo|tenemos) pendiente\b|\bque tareas (?:me quedan|tengo)\b", qn):
        return None
    faltan = [a_ti(t) for t, i in ts if not _hecha(nuc, t, i)]
    hechas = [a_ti(t) for t, i in ts if _hecha(nuc, t, i)]
    if faltan:
        return _ok(f"Te falta {nuc._lista(faltan)}.")
    return _ok(f"Nada, que yo sepa: ya hiciste todo lo que me dijiste ({nuc._lista(hechas)}).")


def sigue(nuc, q):
    """«¿sigue en el taller mi coche?», «¿sigo resfriado?»: lo último que se dijo con «ya» sobre eso manda."""
    m = re.match(r"^¿?\s*(?:y\s+)?(sigo|sigues|sigue|siguen|seguimos|todav[ií]a|a[uú]n)\b(.*?)\??$", q.strip(), re.I)
    if not m or "?" not in q:
        return None
    from . import lectura as L
    yo = sa(m.group(1).lower()) in ("sigo", "seguimos")
    rq = {L._raiz(w) for w in L._contenido(m.group(2))} - {"sigo", "sigue", "segui", "todav", "aun"}
    if not rq:
        return None
    mejor = None
    for i, f in enumerate(nuc.F):
        if f.get("neg") or f.get("t") != "pres" or not f.get("s"):
            continue
        if yo and f["s"] != "U":
            continue
        rf = {L._raiz(w) for w in L._contenido((f.get("src") or "") + " " + nuc.frase(f))}
        if rq <= rf or (len(rq) >= 3 and len(rq - rf) == 1):
            rango = (f.get("v") != "tener", i)           # «el taller tiene el coche» es un hecho derivado: antes el que se dijo
            if mejor is None or rango >= mejor[0]:
                mejor = (rango, i, f)
    if mejor is None:
        return None
    _, i0, f0 = mejor
    e0 = {nuc.can(f0["s"])} | ({nuc.can(f0["obj"])} if f0.get("obj") else set())
    if not f0.get("vig", True):                          # el propio núcleo ya lo dio por superado («estoy enfadado» -> «ya estoy tranquilo»)
        ahora = [g for g in nuc.F[i0 + 1:] if g.get("vig", True) and g.get("s") and nuc.can(g["s"]) == nuc.can(f0["s"]) and g.get("v") == f0.get("v")]
        return _ok("No, ya no" + (f": ahora {nuc.frase(ahora[-1])}." if ahora else "."))
    luego = []
    for g in nuc.F[i0 + 1:]:
        if not g.get("vig", True) or (g.get("src") or "") == (f0.get("src") or ""):
            continue
        ents = {nuc.can(x) for x in [g.get("s"), g.get("obj")] + [c[1] for c in (g.get("comps") or []) if len(c) > 1] if x}
        if ents & e0 and re.search(r"\bya\b", sa((g.get("src") or "").lower())) and not re.search(r"\bya no\b", sa((g.get("src") or "").lower())) and g.get("v") != "tener":
            luego.append(g)
    if luego:
        return _ok(f"No, ya no: {nuc.frase(luego[-1])}.")
    return _ok(f"Que yo sepa, sí: {nuc.frase(f0)}.")


def responde(nuc, q):
    if os.environ.get("LCM_SIN_HILO"):
        return None
    for f in (pasos, pendientes, sigue):
        try:
            r = f(nuc, q)
        except Exception:                                # noqa
            r = None
        if r is not None:
            return r
    return None
