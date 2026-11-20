"""LCM 2.16 · EL ORDEN DE LAS COSAS.

«Primero desayuné, después me duché y luego salí a correr» es una SECUENCIA: además de tres hechos, hay un antes y un después.
Cada paso se entiende con el núcleo (son hechos normales) y se guarda su posición. Con eso se contesta por el orden:
«¿qué hice después de desayunar?», «¿y antes de salir?», «¿qué hice primero?», «¿me duché antes de salir a correr?».
Un texto leído también es una secuencia: sus frases van en el orden en que pasan las cosas.
"""
from __future__ import annotations

import re

from . import morfo as M
from .morfo import sa

_CON = r"(?:primero|en primer lugar|despues|luego|mas tarde|a continuacion|entonces|por ultimo|al final|finalmente|al rato|acto seguido|seguidamente|en segundo lugar|para terminar)"
_CORTE = re.compile(rf"(?:^|[,.;]\s*|\s+y\s+|\s+)(?:y\s+)?({_CON})\b\s*,?\s*", re.I)
_VERBO_Q = r"(?:hice|hizo|hicimos|hicieron|hiciste|hago|hace|haces|hacemos|hacen|paso|ocurrio|sucedio|vino|toca|hay que hacer|se hace)"


def _raices(texto):
    out = set()
    for w in re.findall(r"[a-zñ]+", sa(texto.lower())):
        if len(w) < 3 or w in ("que", "los", "las", "una", "uno", "del", "con", "por", "para", "muy", "mas"):
            continue
        w = re.sub(r"(?:me|te|se|nos|os|lo|la|los|las|le)$", "", w) if re.search(r"(?:ar|er|ir)(?:me|te|se|nos|os|lo|la|los|las|le)$", w) else w
        an = M.analizar(w)
        base = sa(an[0][0]) if an else w
        out.add(base[:5])
    return out


def es_secuencia(texto):
    if not texto or "?" in texto:
        return False
    t = sa(texto.lower())
    cs = re.findall(rf"\b{_CON}\b", t)
    return len(cs) >= 2 or (len(cs) == 1 and re.match(r"^\s*(?:primero|en primer lugar)\b", t) is not None and ("," in t or " y " in t))


def pasos_de(texto):
    t = texto.strip()
    plano = sa(t)                                        # misma longitud que t: sirve para cortar por posiciones
    cortes = [(m.start(), m.end()) for m in _CORTE.finditer(plano)]
    if not cortes:
        return []
    trozos, ini = [], 0
    for a, b in cortes:
        if t[ini:a].strip(" ,.;"):
            trozos.append(t[ini:a])
        ini = b
    trozos.append(t[ini:])
    out = []
    for x in trozos:
        x = re.sub(r"^\s*y\s+", "", x.strip(" ,.;"))
        if x:
            out.append(x[:1].upper() + x[1:])
    return out


def registrar(nuc, texto, pasos=None, silencioso=False):
    """Entiende cada paso con el núcleo y guarda el orden. Devuelve la respuesta o None si no era una secuencia."""
    from .nucleo import cambia_persona
    pasos = pasos or pasos_de(texto)
    if len(pasos) < 2:
        return None
    seq, dichos = [], []
    for p in pasos:
        n0 = len(nuc.F)
        if not silencioso:
            try:
                nuc._procesar_216(p if p[-1:] in ".!" else p + ".")
            except Exception:                           # noqa
                pass
            nuc.pend = None
        nuevos = nuc.F[n0:] if not silencioso else []
        try:
            txt = nuc.frase(nuevos[0]) if nuevos else cambia_persona(p.rstrip("."))
        except Exception:                               # noqa
            txt = p.rstrip(".")
        seq.append({"raices": sorted(_raices(p)), "texto": txt[:1].lower() + txt[1:] if not txt[:1].isupper() or txt.split()[0].lower() in ("te", "me", "se") or True else txt, "raw": p})
        dichos.append(txt)
    nuc.usuario.setdefault("secuencias", []).append(seq)
    del nuc.usuario["secuencias"][:-5]
    if silencioso:
        return None
    nuc.turno += 1
    nuc.ult_just = {"dicho": [texto.strip()]}
    orden = ["primero", "después", "luego", "más tarde", "después", "luego"]
    partes = [f"{orden[i] if i < len(orden) and i < len(dichos) - 1 else 'por último'} {d[:1].lower() + d[1:] if not re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+ ', d) or d.split()[0].lower() in ('te', 'me', 'se', 'tu', 'tus') else d}" for i, d in enumerate(dichos)]
    if len(partes) >= 1:
        partes[0] = partes[0].replace("por último", "primero", 1) if len(partes) == 1 else partes[0]
    return {"respuesta": "Entendido, por orden: " + ", ".join(partes) + ".", "estado": "ok", "consultar": False, "tipo": "ack"}


def _busca(seqs, frase):
    r = _raices(frase)
    if not r:
        return None
    mejor = None
    for seq in reversed(seqs):
        for i, paso in enumerate(seq):
            n = len(r & set(paso["raices"]))
            if n and (mejor is None or n > mejor[0]):
                mejor = (n, seq, i)
        if mejor:
            break
    return mejor


def _dice(paso):
    t = paso["texto"].rstrip(".")
    return t[:1].upper() + t[1:]


def responder(nuc, p, n):
    seqs = nuc.usuario.get("secuencias") or []
    if not seqs or "?" not in p:
        return None
    n = n.strip(" ?¿.!")
    seq = seqs[-1]
    fab = lambda i: setattr(nuc, "ult_just", {"dicho": [x["raw"] for x in seq[max(0, i - 1):i + 2]]})   # noqa: E731
    m = re.match(rf"^(?:y )?que (?:fue lo |es lo )?(?:{_VERBO_Q}|primero que hice|primero que hizo)? ?(?:[a-zñ]+ )?(?:justo |inmediatamente )?(despues de|tras|antes de|luego de) (.+)$", n)
    if m:
        h = _busca(seqs, m.group(2))
        if not h:
            return None
        _, seq, i = h
        j = i + 1 if m.group(1) in ("despues de", "tras", "luego de") else i - 1
        if j < 0:
            return f"Nada, que yo sepa: eso fue lo primero. Después, {seq[i + 1]['texto']}." if i + 1 < len(seq) else None
        if j >= len(seq):
            return "Nada más, que yo sepa: eso fue lo último que me contaste."
        nuc.ult_just = {"dicho": [seq[min(i, j)]["raw"], seq[max(i, j)]["raw"]]}
        nuc._seq_pos = (len(seqs) - 1 - list(reversed(seqs)).index(seq), j)
        return _dice(seq[j]) + "."
    m = re.match(rf"^(?:y )?que (?:fue lo |es lo )?(?:(primero|ultimo) que (?:hice|hizo|hicimos|hicieron|paso)|(?:{_VERBO_Q}) (?:[a-zñ]+ )?(primero|al principio|en primer lugar|al final|por ultimo|lo ultimo|en ultimo lugar|finalmente|en segundo lugar|lo segundo))$", n)
    if m:
        k = m.group(1) or m.group(2)
        j = 0 if k in ("primero", "al principio", "en primer lugar") else (1 if k in ("en segundo lugar", "lo segundo") else len(seq) - 1)
        if j >= len(seq):
            return None
        fab(j)
        nuc._seq_pos = (len(seqs) - 1, j)
        return _dice(seq[j]) + "."
    if re.match(r"^(?:y )?(?:despues|luego|a continuacion|y despues de eso|que mas)$", n) and getattr(nuc, "_seq_pos", None):
        si, j = nuc._seq_pos
        if si < len(seqs) and j + 1 < len(seqs[si]):
            nuc._seq_pos = (si, j + 1)
            return _dice(seqs[si][j + 1]) + "."
        return "Nada más, que yo sepa."
    m = re.match(r"^(.+?) (antes|despues) (?:de|que) (.+)$", n)
    if m and not re.match(r"^(?:que|quien|como|cuando|donde)\b", n):
        a, b = _busca(seqs, m.group(1)), _busca(seqs, m.group(3))
        if a and b and a[1] is b[1] and a[2] != b[2]:
            antes = a[2] < b[2]
            ok = antes if m.group(2) == "antes" else not antes
            nuc.ult_just = {"dicho": [a[1][min(a[2], b[2])]["raw"], a[1][max(a[2], b[2])]["raw"]]}
            return f"{'Sí' if ok else 'No'}: primero {a[1][min(a[2], b[2])]['texto'].rstrip('.')} y después {a[1][max(a[2], b[2])]['texto'].rstrip('.')}."
    return None
