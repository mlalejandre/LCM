"""PUENTE entre el analizador sintáctico y el núcleo del LCM.

El núcleo entiende bien frases simples con su sujeto («Mi tío Manuel vive en Navarra.»). Aquí cada frase, por compleja que sea, se
parte en ORACIONES según el análisis aprendido, y cada oración se devuelve como una frase simple con su sujeto puesto:

  «Hoy he aprendido que mi tío Manuel es carpintero.»                     -> «Mi tío Manuel es carpintero.»
  «Tengo un amigo que se llama Manuel Pérez que le gustan mucho los gatos.» -> «Tengo un amigo.» «Mi amigo se llama Manuel Pérez.»
                                                                             «A mi amigo le gustan mucho los gatos.»
No decide qué significa nada: solo ordena quién hace qué. Si el análisis no es seguro, devuelve la frase tal cual."""
from __future__ import annotations

import os
import re

from .analiza import palabras
from .datos import frases_de

SEGURO = 0.60
SEGURO_RELATIVA = 0.70
_ORACION = ("conj", "ccomp", "advcl", "acl", "parataxis", "csubj")
# verbos de «me he enterado de que…»: lo que importa es lo que viene detrás. Es léxico, no sintaxis; lista corta y ampliable.
_NOTICIA = ("aprend", "sab", "sé", "enter", "descubr", "dicho", "dij", "dic", "cont", "cuent", "oíd", "oí", "leíd", "leí", "result", "parec", "cre", "pens", "piens", "supon", "supong", "record", "recuerd")


def _une(ws):
    t = " ".join(ws)
    t = re.sub(r"\bde el\b", "del", t); t = re.sub(r"\ba el\b", "al", t)
    t = re.sub(r"\bDe el\b", "Del", t); t = re.sub(r"\bA el\b", "Al", t)
    t = re.sub(r"\s+([,.;:!?)])", r"\1", t); t = re.sub(r"([(¿¡])\s+", r"\1", t)
    return t.strip(" ,;:")


def _es_verbo(ps, p):
    return p["cat"] in ("VERB", "AUX") or any(q["cabeza"] == p["i"] and q["funcion"] == "cop" for q in ps)


def _propias(ps, v, cabezas_oracion):
    """Las palabras de la oración cuyo núcleo es v: su rama, sin las ramas de las otras oraciones que cuelgan de ella."""
    ids = {v["i"]}
    cambio = True
    while cambio:
        cambio = False
        for p in ps:
            if p["cabeza"] in ids and p["i"] not in ids and p["i"] not in cabezas_oracion:
                ids.add(p["i"]); cambio = True
    return [p for p in ps if p["i"] in ids]


def _sn(ps, n, cabezas_oracion):
    """El sintagma de un nombre (con sus determinantes y adjetivos, sin oraciones de relativo)."""
    return [p for p in _propias(ps, n, cabezas_oracion) if p["cat"] != "PUNCT"]


def _referente(ps, n, cabezas_oracion, raiz):
    """Cómo volver a nombrar un antecedente: «un amigo» que TENGO -> «mi amigo»; «un perro» -> «el perro»; «Manuel» -> «Manuel»."""
    sn = _sn(ps, n, cabezas_oracion)
    ws = [p["forma"] for p in sn if not (p["cabeza"] == n["i"] and p["funcion"] == "case")]
    if ws and ws[0].lower() in ("un", "una", "unos", "unas"):
        mio = raiz is not None and n["cabeza"] == raiz["i"] and raiz["forma"].lower() in ("tengo", "tenemos") and n["funcion"] == "obj"
        fem, pl = ws[0].lower() in ("una", "unas"), ws[0].lower() in ("unos", "unas")
        ws[0] = ("mis" if pl else "mi") if mio else (("las" if fem else "los") if pl else ("la" if fem else "el"))
    return ws


def simples(frase):
    """Una frase -> lista de frases simples para el núcleo. Si no se puede con seguridad, [frase]."""
    f = frase.strip()
    if not f or "?" in f or "¿" in f or len(f) > 400:
        return [f]
    try:
        ps = palabras(f)
    except Exception:                                    # noqa
        return [f]
    raiz = next((p for p in ps if p["cabeza"] == 0), None)
    if raiz is None or not _es_verbo(ps, raiz):
        return [f]
    nucleos = [p for p in ps if p["i"] == raiz["i"] or (p["funcion"] in _ORACION and _es_verbo(ps, p))]
    if len(nucleos) < 2:
        return [f]
    if min(p["seguro"] for p in nucleos) < SEGURO:
        return [f]                                       # el propio modelo no lo ve claro: no se toca
    cab = {p["i"] for p in nucleos}
    por_i = {p["i"]: p for p in ps}
    out = []
    sujeto_de = {}
    for v in sorted(nucleos, key=lambda p: (p["i"] != raiz["i"], p["i"])):
        prop = [p for p in _propias(ps, v, cab) if p["cat"] != "PUNCT"]
        hijos = [p for p in prop if p["cabeza"] == v["i"]]
        suj = next((h for h in hijos if h["funcion"] == "nsubj"), None)
        marca = [h for h in hijos if h["funcion"] in ("mark", "cc") or (h["cat"] in ("SCONJ", "CCONJ"))]
        quitar = {h["i"] for h in marca}
        pre = []
        if v["funcion"] == "acl":                        # relativa: el «que» se cambia por aquello de lo que se habla
            ant = por_i.get(v["cabeza"])
            rel = next((h for h in hijos if h["forma"].lower() in ("que", "quien", "cual") and h["cat"] in ("PRON", "SCONJ")), None)
            if ant is None or ant["cat"] not in ("NOUN", "PROPN", "PRON"):
                continue
            if v["seguro"] < SEGURO_RELATIVA:
                continue                                 # no está claro de quién se dice (¿«cuerpo» o «sistema»?): mejor no afirmar nada
            ref = _referente(ps, ant, cab, raiz)
            if rel is not None:
                quitar.add(rel["i"])
                quitar |= {p["i"] for p in prop if p["cabeza"] == rel["i"]}       # «al que», «a la que»
            dativo = any(h["forma"].lower() in ("le", "les") for h in hijos)
            otro_suj = any(h["funcion"] in ("nsubj", "csubj") and h is not rel for h in hijos) or any(p["cabeza"] == v["i"] and p["funcion"] == "csubj" for p in ps)
            pre = (["A"] if dativo and (otro_suj or rel is None or rel["funcion"] != "nsubj" or v["forma"].lower().startswith(("gust", "encant", "interes", "apetec", "duel", "dol", "molest"))) else []) + ref
            sujeto_de[v["i"]] = ref
        elif suj is None and v["funcion"] in ("conj", "advcl") and sujeto_de.get(v["cabeza"]):
            dativo = any(h["forma"].lower() in ("le", "les") for h in hijos) and v["forma"].lower().startswith(("gust", "encant", "interes", "apetec", "duel", "dol", "molest"))
            sj = list(sujeto_de[v["cabeza"]])
            if dativo and sj and sj[0] in ("Mi", "El", "La", "Los", "Las", "Mis", "Un", "Una"):
                sj[0] = sj[0].lower()
            pre = (["A"] if dativo else []) + sj         # «…y le gusta cazar»: el mismo de antes
            sujeto_de[v["i"]] = sujeto_de[v["cabeza"]]
        if suj is not None:
            sujeto_de[v["i"]] = [p["forma"] for p in _sn(ps, suj, cab)]
        if v["i"] == raiz["i"]:
            cc = next((p for p in nucleos if p["cabeza"] == v["i"] and p["funcion"] == "ccomp"), None)
            if cc is not None and suj is None and any(h["forma"].lower().startswith(_NOTICIA) or v["forma"].lower().startswith(_NOTICIA) for h in [v] + [h for h in hijos if h["funcion"] == "aux"]):
                continue                                 # «he aprendido que…», «me han dicho que…»: se queda lo aprendido
        if v["funcion"] == "csubj" or (v["funcion"] == "ccomp" and por_i[v["cabeza"]]["i"] != raiz["i"]):
            continue
        ws = pre + [p["forma"] for p in prop if p["i"] not in quitar]
        if v["funcion"] == "ccomp" and not any(o for o in out) and False:
            pass
        # los infinitivos que cuelgan («gusta cazar jabalíes») se quedan dentro de su oración
        t = _une(ws)
        if len(t.split()) >= 2:
            out.append(t[:1].upper() + t[1:] + ".")
    # el sujeto de la principal, para las que lo heredan
    return out or [f]


def partes(texto):
    """Texto -> lista de frases simples (para que el núcleo las entienda de una en una)."""
    if os.environ.get("LCM_SIN_SINTAXIS"):
        return [texto]
    out = []
    for f in frases_de(texto):
        ss = simples(f)
        # «Tengo un amigo.» + «Mi amigo se llama X.»: la segunda ya dice que existe; la primera sobra
        if len(ss) >= 2 and re.match(r"^Tengo (?:un|una) [a-záéíóúñ]+\.$", ss[0]) and re.match(r"^Mi [a-záéíóúñ]+ se llama ", ss[1]):
            ss = ss[1:]
        out += ss
    return out or [texto]


def reescribe(texto):
    """Texto de una o varias frases -> el mismo contenido en frases simples."""
    if os.environ.get("LCM_SIN_SINTAXIS"):
        return texto
    out = []
    for f in frases_de(texto):
        out += simples(f)
    return " ".join(out)


if __name__ == "__main__":
    import sys
    for f in frases_de(" ".join(sys.argv[1:])):
        print("«" + f + "»")
        for s in simples(f):
            print("    ->", s)
