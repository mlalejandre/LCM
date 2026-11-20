"""LCM 2.19 · Términos de varias palabras.

«La Torre de Hércules», «el zorro volador», «un café solo», «la jalea real» nombran UNA cosa. Si el núcleo los lee palabra a palabra,
lo que se diga del zorro volador se le apunta al zorro, y «Está en La Coruña» ya no sabe de quién habla.
Aquí cada término de varias palabras se convierte en una sola pieza al entrar y vuelve a su forma al salir:
  - nombres propios con enlace («Torre de Hércules»), con artículo propio («La Coruña») o con número («Apolo 11»): en cualquier frase;
  - nombre + adjetivo que nombra una clase («zorro volador», «volcán dormido»): solo cuando se EXPLICA algo general (texto o charla que explica);
    «el coche rojo es de Ana» sigue siendo cosa del núcleo.
También resuelve el apellido suelto («Armstrong») cuando solo hay una persona conocida con ese apellido.
"""
from __future__ import annotations

import re

from . import conceptos as K
from . import morfo as M
from .morfo import sa

_MAY = r"[A-ZÁÉÍÓÚÑ][\wáéíóúñü]+"
_PROPIO = re.compile(r"(?<![\wáéíóúñü])((?:[Ll]a|[Ee]l|[Ll]os|[Ll]as)\s+)?(" + _MAY + r"(?:\s+(?:de|del|de la|de los|de las)\s+" + _MAY + r")+)")
_ART_PROPIO = re.compile(r"(?<=[a-záéíóúñ,;:] )((?:La|El|Los|Las)\s+" + _MAY + r")(?![\wáéíóúñü])")
_CON_NUM = re.compile(r"(?<![\wáéíóúñü])(" + _MAY + r"\s+\d{1,4})(?![\w.,]\d)")
_PRE_ADJ = {"buen", "buena", "gran", "mal", "mala", "mejor", "peor", "primer", "primera", "mismo", "misma", "otro", "otra", "solo", "sola", "unico", "unica", "nuevo", "nueva", "viejo", "vieja",
            "pequeño", "pequeña", "pequeno", "pequena", "propio", "propia", "simple", "pobre", "cierto", "cierta", "verdadero", "verdadera", "ultimo", "ultima", "segundo", "segunda", "tercer", "tercera"}
_NO_ADJ = {"que", "de", "del", "en", "con", "sin", "por", "para", "y", "o", "no", "ni", "se", "le", "les", "lo", "la", "los", "las", "muy", "mas", "menos", "tan", "ya", "tambien", "solo", "siempre", "nunca", "casi",
           "es", "son", "esta", "estan", "hay", "ha", "han", "era", "eran", "fue", "fueron", "tiene", "tienen", "puede", "pueden", "suele", "suelen", "mismo", "misma", "entero", "entera", "todo", "toda"}


def tabla(nuc):
    return nuc.usuario.setdefault("comp", {})


def _plural(w):
    if w.endswith(("a", "e", "i", "o", "u", "á", "é", "ó")):
        return w + "s"
    if w.endswith("s"):
        return w
    if w.endswith("z"):
        return w[:-1] + "ces"
    return re.sub("ón$", "on", re.sub("án$", "an", re.sub("ín$", "in", w))) + "es"


def _alta(nuc, tok, sing, plur=None, propio=False, art="", cabeza=""):
    t = tabla(nuc)
    k = sa(tok.lower())
    if k not in t:
        t[k] = {"tok": tok, "s": sing, "p": plur or "", "propio": propio, "art": art, "cabeza": cabeza}
        if len(t) > 400:
            for viejo in list(t)[:50]:
                del t[viejo]
        return True
    return False


def aprende_propios(nuc, texto):
    """Registra los nombres propios de varias palabras que aparezcan en una afirmación."""
    for m in _PROPIO.finditer(texto):
        art = (m.group(1) or "").strip()
        nombre = m.group(2)
        inicio = m.start() == 0 or texto[:m.start()].rstrip()[-1:] in (".", "!", "?", "¿", "¡", ":")
        if inicio and not art:                           # «Háblame de Clara», «Cerca de Madrid…»: la mayúscula es la del principio de la frase
            w0 = nombre.split()[0].lower()
            try:
                from . import coloquial as _Q
                comun = bool(M.analizar(w0)) or bool(_Q._conocida(sa(w0))) or bool(re.search(r"(?:me|te|le|nos|les|lo|la|los|las|se)$", sa(w0)) and len(w0) > 5)
            except Exception:                            # noqa
                comun = True
            if comun:
                continue
        tok = re.sub(r"\s+", "", nombre)
        _alta(nuc, tok, nombre, propio=True, art=art.lower())
    for m in _ART_PROPIO.finditer(texto):
        nombre = m.group(1)
        _alta(nuc, re.sub(r"\s+", "", nombre), nombre, propio=True)
    for m in _CON_NUM.finditer(texto):
        nombre = m.group(1)
        if sa(nombre.split()[0].lower()) in ("en", "el", "la", "los", "las", "de", "desde", "hasta", "hacia", "año", "ano", "dia", "son", "hay", "con", "tiene", "mide", "pesa", "cuesta", "tengo", "unos", "unas",
                                             "casi", "mas", "menos", "solo", "cada", "sobre", "entre", "llego", "fue", "nacio", "murio"):
            continue
        if m.start() == 0:
            continue
        _alta(nuc, re.sub(r"\s+", "", nombre), nombre, propio=True)


def aprende_clase(nuc, sn):
    """«El zorro volador», «un café solo», «los volcanes extinguidos» como sujeto de una explicación: es el nombre de una clase.
    Devuelve (pieza, cabeza) si lo registra o ya lo conocía, o None."""
    ws = sn.strip().split()
    if len(ws) != 3:
        return None
    det, n, adj = sa(ws[0].lower()), ws[1].lower(), ws[2].lower()
    if det not in ("el", "la", "los", "las", "un", "una", "unos", "unas") or ws[1][:1].isupper() or ws[2][:1].isupper():
        return None
    if sa(n) in _PRE_ADJ or sa(adj) in _NO_ADJ or sa(n) in _NO_ADJ or not n.isalpha() or not adj.isalpha() or len(adj) < 3:
        return None
    if sa(adj).endswith("mente") or re.fullmatch(r"\d+", adj):
        return None
    pl = det in ("los", "las", "unos", "unas")
    n1 = M.singular(n) if pl and len(n) > 3 else n
    a1 = M.singular(adj) if pl and len(adj) > 3 and not sa(adj).endswith(("oides", "is", "us")) else adj
    tok = n1 + a1
    sing = f"{n1} {a1}"
    plur = f"{n} {adj}" if pl else f"{_plural(n1)} {_plural(a1) if not sa(a1).endswith(('oides', 'is', 'us')) else a1}"
    _alta(nuc, tok, sing, plur, cabeza=sa(n1))
    return tok, sa(n1)


def codifica(nuc, texto):
    """Sustituye cada término conocido por su pieza. No registra nada."""
    t = tabla(nuc)
    if not texto:
        return texto
    out = texto
    for k, d in sorted(t.items(), key=lambda kv: -len(kv[1]["s"])):
        if d["propio"]:
            nombre = re.escape(d["s"]).replace(r"\ ", r"\s+")
            if d.get("art"):
                out = re.sub(r"(?<![\wáéíóúñü])(?:(de|a)l\s+|(?:[Ee]l|[Ll]a|[Ll]os|[Ll]as)\s+)?" + nombre + r"(?![\wáéíóúñü])",
                             lambda m: ((m.group(1) + " ") if m.group(1) else "") + d["tok"], out)
            else:
                out = re.sub(r"(?<![\wáéíóúñü])" + nombre + r"(?![\wáéíóúñü])", d["tok"], out)
        else:
            for forma, pieza in ((d.get("p") or "", _plural(d["tok"])), (d["s"], d["tok"])):
                if forma and forma != d["s"] or pieza == d["tok"]:
                    if not forma:
                        continue
                    out = re.sub(r"(?<![\wáéíóúñü])" + re.escape(forma).replace(r"\ ", r"\s+") + r"(?![\wáéíóúñü])", pieza, out, flags=re.I)
    # el apellido suelto de alguien conocido
    try:
        nombres = [d.get("nombre") for e, d in nuc.E.items() if e.startswith("N:") and d.get("nombre") and " " in d.get("nombre")]
    except Exception:                                    # noqa
        nombres = []
    if nombres:
        solos = {sa(d.get("nombre", "").lower()) for d in nuc.E.values() if d.get("nombre")}
        for m in list(re.finditer(r"(?<![\wáéíóúñü])(" + _MAY + r")(?![\wáéíóúñü])", out))[::-1]:
            w = m.group(1)
            if sa(w.lower()) in solos:
                continue
            antes_ = out[:m.start()].rstrip()
            if antes_ and antes_.split()[-1][:1].isupper() and not antes_.endswith((".", "?", "!", "¿", "¡")):
                continue                                 # ya va precedido de su nombre
            cand = [n for n in nombres if n.split()[-1] == w and len(n.split()) == 2]
            if len(cand) == 1:
                out = out[:m.start()] + cand[0] + out[m.end():]
    return out


def decodifica(nuc, texto):
    """Devuelve cada pieza a su forma de varias palabras."""
    t = tabla(nuc)
    if not texto or not t:
        return texto

    def cambia(m):
        w = m.group(0)
        k = sa(w.lower())
        d, pl = t.get(k), False
        if d is None:
            for suf in ("es", "s"):
                if k.endswith(suf) and k[:-len(suf)] in t and not t[k[:-len(suf)]]["propio"]:
                    d, pl = t[k[:-len(suf)]], True
                    break
        if d is None:
            return w
        if d["propio"]:
            return (d["art"] + " " if d.get("art") else "") + d["s"]
        return (d.get("p") or d["s"]) if pl else d["s"]
    out = re.sub(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]+\d{0,4}", cambia, texto)
    out = re.sub(r"\b([Dd])e el\b", r"\1el", out)
    out = re.sub(r"\b([Aa]) el\b", r"\1l", out)
    out = re.sub(r"\b(el|la|los|las) (el|la|los|las) (?=[A-ZÁÉÍÓÚÑ])", r"\2 ", out)        # «la la Torre…»
    out = re.sub(r"(^|[.!?]\s+|¿|¡)([a-záéíóúñü])", lambda m: m.group(1) + m.group(2).upper(), out)
    return out
