"""LCM 2.21 · Encadenar dos cosas aprendidas.

«¿Cuánto tarda el recorrido en tren más largo del mundo?» no lo dice ninguna frase. Pero una dice que el Transiberiano ES ese
recorrido y otra, cuánto tarda el Transiberiano. Aquí se da el primer paso: si la pregunta nombra algo por una descripción que lo
aprendido identifica con un nombre («X es el D», «el D se llama X»), se cambia la descripción por el nombre y se pregunta otra vez.
La respuesta dice el paso que ha dado. No depende del tema: trabaja con las frases guardadas, sean las que sean."""
from __future__ import annotations

import re

from . import morfo as M
from .morfo import sa

_VACIAS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "en", "por", "para", "con", "que", "y", "o", "mas", "menos", "muy", "su", "sus", "se", "es", "son", "lo", "donde", "cuando", "como", "cual", "quien", "cuanto", "cuantos", "cuanta", "cuantas"}
_GEN = {"persona", "personas", "cosa", "cosas", "lugar", "sitio", "tipo", "clase", "nombre", "parte"}


def _raiz(w):
    w = sa(w.lower())
    w = sa(M.singular(w)) if len(w) > 3 else w
    return w[:5] if len(w) > 5 else w


def _cont(t):
    return [w for w in re.findall(r"[a-záéíóúñü0-9]+", t.lower()) if sa(w) not in _VACIAS and len(w) > 1]


def _frases(nuc):
    out = []
    for t in (nuc.usuario.get("leido") or []):
        out += t.get("frases") or []
    out += [f["src"] for f in getattr(nuc, "F", []) if f.get("src") and (f.get("leido") or f.get("expo"))]
    return list(dict.fromkeys(out))


def identidades(nuc):
    """[(nombre, descripción)] de lo aprendido: «X es el D», «X es un D», «El D se llama X»."""
    try:
        from . import compuestos as C
        dec = lambda x: C.decodifica(nuc, x)
    except Exception:                                    # noqa
        dec = lambda x: x
    out = []
    for f in _frases(nuc):
        f = dec(f).strip().rstrip(".")
        m = re.match(r"^((?:El|La|Los|Las|Un|Una)\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñü][\wáéíóúñü]*(?:\s+(?:de\s+)?[\wáéíóúñü]+){0,3}?)\s+(?:es|son|era|fue)\s+(el|la|los|las|un|una)\s+(.+)$", f)
        if m and not re.search(r"\b(?:es|son|era|fue)\b", m.group(2)):
            d = re.split(r",|\s+(?:porque|pero|aunque|y por eso|mientras)\s+", m.group(4))[0].strip()
            if len(_cont(d)) >= 2:
                out.append((((m.group(1) or "") + m.group(2)).strip(), d, m.group(3) in ("un", "una")))
        m = re.match(r"^(El|La|Los|Las)\s+(.+?)\s+se\s+llama(?:n|ba|ban)?\s+(.+)$", f)
        if m and len(_cont(m.group(2))) >= 2 and len(m.group(3).split()) <= 3:
            x = m.group(3).strip()
            pl = m.group(1) in ("Los", "Las")
            art = ("las" if pl else "la") if M.genero_sust(sa(M.singular(x.split()[0].lower()) if pl else x.split()[0].lower())) == "f" else ("los" if pl else "el")
            out.append((x if x[:1].isupper() else f"{art} {x}", m.group(2), False))
    return out


def reformula(nuc, texto, maximo=3):
    """[(pregunta con el nombre en lugar de la descripción, nombre, descripción)]"""
    if "?" not in texto or re.match(r"^\W*(?:y\s+)?(?:cu[aá]l(?:es)? (?:es|son|era|fue)|qui[eé]n(?:es)? (?:es|son|era|fue)|c[oó]mo se (?:le |les )?llaman?|qu[eé] (?:es|son))\b", texto.strip(), re.I):
        return []                                        # eso es preguntar por el nombre o por la definición: no hay nada que encadenar
    ws = re.findall(r"[\wáéíóúñü]+|[^\w\s]", texto)
    rq = [(_raiz(w) if sa(w.lower()) not in _VACIAS and w.isalnum() else None) for w in ws]
    presentes = {r for r in rq if r}
    out = []
    for nombre, desc, indef in identidades(nuc):
        rd = [_raiz(w) for w in _cont(desc)]
        claves = [r for r in rd if r not in {_raiz(g) for g in _GEN}]
        if len(claves) < 2 or _raiz(nombre.split()[-1]) in presentes:
            continue
        com = [r for r in claves if r in presentes]
        if len(com) < 2 or len(com) < (0.7 if indef else 0.99) * len(claves):
            continue
        idx = [i for i, r in enumerate(rq) if r in set(rd)]
        if not idx:
            continue
        a, b = idx[0], idx[-1]
        if b - a > len(rd) + 4:
            continue
        while a > 0 and sa(ws[a - 1].lower()) in ("el", "la", "los", "las", "un", "una", "del", "al"):
            a -= 1
        pre = ws[a].lower() if a < idx[0] else ""
        nom = nombre[:1].lower() + nombre[1:] if nombre.split()[0] in ("El", "La", "Los", "Las", "Un", "Una") else nombre
        if pre in ("del", "al"):
            nom = pre[:-1] + " " + nom if not re.match(r"^el\s", nom) else pre + nom[2:]
        if a == 0 or (b - a + 1) >= len([w for w in ws if w.isalnum()]) - 1:
            continue                                     # la pregunta entera ES la descripción: eso es preguntar por el nombre, no encadenar
        ws2 = ws[:a] + [nom] + ws[b + 1:]
        t2 = re.sub(r"\s+([?.,!])", r"\1", re.sub(r"([¿¡])\s+", r"\1", " ".join(ws2)))
        t2 = re.sub(r"\bde el\b", "del", re.sub(r"\ba el\b", "al", t2))
        if sa(t2.lower()) != sa(texto.lower()) and t2 not in [x[0] for x in out]:
            out.append((t2, nombre, desc))
            # el nombre puede ser un caso de algo más general que también se conoce («aceite de oliva virgen extra» -> «aceite de oliva»)
            pal = nom.split()
            otras = " ".join(sa(x.lower()) for x in _frases(nuc))
            for k in range(len(pal) - 1, 1, -1):
                corto = " ".join(pal[:k])
                if sa(pal[k - 1].lower()) in _VACIAS or len(_cont(corto)) < 1:
                    continue
                if len(re.findall(r"\b" + re.escape(sa(corto.lower())) + r"\b(?!\s+" + re.escape(sa(pal[k].lower())) + r")", otras)) >= 1:
                    t3 = re.sub(r"\s+([?.,!])", r"\1", re.sub(r"([¿¡])\s+", r"\1", " ".join(ws[:a] + [corto] + ws[b + 1:])))
                    out.append((t3, nombre, desc))
                    break
    return out[:maximo]


def aviso(respuesta, nombre, desc):
    r = (respuesta or "").rstrip()
    n = nombre[:1].lower() + nombre[1:] if nombre.split()[0] in ("El", "La", "Los", "Las", "Un", "Una") else nombre
    return (r if r[-1:] in ".!?»" else r + ".") + f" Lo junto con otra cosa que aprendí: {n} es «{desc}»."


def fuentes(nuc, nombre, desc):
    """Las frases que dicen que `nombre` es `desc`: no valen como respuesta al segundo paso (eso sería contestar con la propia identidad)."""
    try:
        from . import compuestos as C
        dec = lambda x: C.decodifica(nuc, x)
    except Exception:                                    # noqa
        dec = lambda x: x
    n, d = sa(nombre.lower()), sa(desc.lower())
    return {f.strip().rstrip(".") for f in _frases(nuc) if n.split()[-1] in sa(dec(f).lower()) and d in sa(dec(f).lower())}
