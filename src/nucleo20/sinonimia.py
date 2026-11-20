"""LCM 2.19 · Preguntar con otras palabras.

Si una pregunta no encuentra respuesta, se vuelve a hacer con palabras que dicen lo mismo («¿de qué se alimentan?» = «¿qué comen?»,
«¿dónde habitan?» = «¿dónde viven?», «comida» = «alimento»). Las equivalencias son conocimiento de la lengua y están en la base de
conceptos (sección [equivalencias]); aquí solo se aplica la gramática del cambio (conjugación, «se … de», plural)."""
from __future__ import annotations

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
    if not eq or "?" not in texto:
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
