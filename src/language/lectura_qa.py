"""parche-117: preguntas sobre lo aprendido leyendo textos ("quien creo a X", "quien fue el creador de X", "que exhibe X", "que come el leon").
Se usa solo cuando la comprension normal no contesta. Sin listas de dominio: la forma verbal se enlaza con los predicados que hay en memoria
por su raiz y su terminacion, y los nombres de agente (creador, descubridor, escritor...) con el verbo del que salen."""
from __future__ import annotations

import re
from typing import List, Optional

from .irregulares import IRREG
from .lexicon import norm

_ART = r"(?:el|la|los|las|un|una|al|del)"
_FIN = {"ar": ["o", "as", "a", "amos", "an", "e", "es", "en", "aba", "abas", "aban", "o", "aste", "amos", "aron", "ando", "ado", "ada", "ados", "adas", "are", "ara"],
        "er": ["o", "es", "e", "emos", "en", "ia", "ias", "ian", "i", "iste", "io", "imos", "ieron", "iendo", "ido", "ida", "idos", "idas", "a", "an"],
        "ir": ["o", "es", "e", "imos", "en", "ia", "ias", "ian", "i", "iste", "io", "ieron", "iendo", "ido", "ida", "idos", "idas", "a", "an"]}


def _predicados(qa) -> List[str]:
    return sorted({f["p"] for f in qa.m.facts if not f.get("neg")})


def _verbos(qa, forma: str) -> List[str]:
    """Predicados de la memoria que pueden ser la forma conjugada dada."""
    f = norm(forma)
    out = []
    irr = IRREG.get(f) or IRREG.get(forma.lower())
    for p in _predicados(qa):
        base = p.lower().split("_")[0]
        if len(base) < 4 or base[-2:] not in _FIN:
            continue
        if irr and norm(irr) == norm(base):
            out.append(p)
            continue
        st = base[:-2]
        for stem in {st, st[:-1] + {"c": "qu", "g": "gu", "z": "c"}.get(st[-1:], st[-1:])}:
            if f.startswith(stem) and f[len(stem):] in _FIN[base[-2:]] + [""]:
                out.append(p)
                break
    return out


def _verbo_de_agente(qa, nombre: str) -> List[str]:
    """creador -> crear, descubridor -> descubrir, escritor -> escribir, fundador -> fundar."""
    n = norm(nombre)
    m = re.fullmatch(r"(.{3,}?)(?:ad|ed|id)?(?:or|ora|ores|oras)", n)
    if not m:
        return []
    raiz = m.group(1)
    res = []
    for p in _predicados(qa):
        base = norm(p.lower().split("_")[0])
        if base[-2:] in _FIN and (base[:-2].startswith(raiz[:max(3, len(raiz) - 1)]) or raiz.startswith(base[:-2][:max(3, len(base) - 3)])):
            res.append(p)
    return res


def _entidad(qa, texto: str) -> Optional[str]:
    t = re.sub(r"^" + _ART + r"\s+", "", texto.strip(), flags=re.I)
    clave = re.sub(r"\s+", "_", norm(t)).upper()
    if not clave:
        return None
    for k in (clave, clave + "S", clave[:-1] if clave.endswith("S") else clave, clave[:-2] if clave.endswith("ES") else clave):
        if any(f["s"] == k or f["o"] == k for f in qa.m.facts):
            return k
    al = getattr(qa.m, "alias", {}).get(clave)
    return al or None


def responder(qa, pregunta: str) -> Optional[str]:
    q = re.sub(r"[¿?¡!]", " ", pregunta).strip()
    q = re.sub(r"\s+", " ", q)
    low = q.lower()
    hits = []
    m = re.fullmatch(r"(?:y )?(quien|quienes|quién)\s+(?:fue|es|era|son|fueron)\s+" + _ART + r"\s+(\w+(?:dor|dora|tor|tora|dores|tores))\s+(?:de|del)\s+(.+)", low)
    if m:
        ent = _entidad(qa, m.group(3))
        for p in _verbo_de_agente(qa, m.group(2)):
            if ent:
                hits += qa.lookup(None, p, ent)
    if not hits:
        m = re.fullmatch(r"(?:y )?(?:quien|quienes|quién)\s+(\w+)\s+(?:a la |a los |a las |al |a |el |la |los |las )?(.+)", low)
        if m:
            ent = _entidad(qa, m.group(2))
            for p in (_verbos(qa, m.group(1)) if ent else []):
                hits += qa.lookup(None, p, ent)
    if not hits:
        m = re.fullmatch(r"(?:y )?(?:qu[eé]|a qu[eé]|con qu[eé])\s+(\w+)\s+(.+)", low)
        if m:
            ent = _entidad(qa, m.group(2))
            for p in (_verbos(qa, m.group(1)) if ent else []):
                hits += qa.lookup(ent, p, None)
    hits = list(dict.fromkeys(hits))
    if not hits:
        return None
    return " ".join(dict.fromkeys(qa.say(f) + "." for f in hits))[:600]
