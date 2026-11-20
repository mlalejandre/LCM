"""Numerales del castellano -> cifras («doscientos treinta» -> 230, «dos mil quinientos» -> 2500, «tres coma cinco» -> 3,5).
Es lengua, no cálculo: solo reconoce cómo se dice un número."""
from __future__ import annotations

import re

UNID = {"cero": 0, "uno": 1, "una": 1, "un": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
        "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "dieciséis": 16, "diecisiete": 17,
        "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21, "veintiuna": 21, "veintiun": 21, "veintiún": 21, "veintidos": 22,
        "veintidós": 22, "veintitres": 23, "veintitrés": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintiséis": 26,
        "veintisiete": 27, "veintiocho": 28, "veintinueve": 29}
DECENAS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90}
CENTENAS = {"cien": 100, "ciento": 100, "doscientos": 200, "doscientas": 200, "trescientos": 300, "trescientas": 300, "cuatrocientos": 400,
            "cuatrocientas": 400, "quinientos": 500, "quinientas": 500, "seiscientos": 600, "seiscientas": 600, "setecientos": 700,
            "setecientas": 700, "ochocientos": 800, "ochocientas": 800, "novecientos": 900, "novecientas": 900}
_TODAS = set(UNID) | set(DECENAS) | set(CENTENAS) | {"mil", "millon", "millón", "millones", "y"}


def _valor(ws):
    """Lista de palabras numerales -> entero (o None si no forman un número bien dicho)."""
    total, grupo, ult = 0, 0, None
    for w in ws:
        if w in UNID:
            if ult in ("u",) or (ult == "y" and not 1 <= UNID[w] <= 9) or (ult == "d" and True):
                return None
            grupo += UNID[w]; ult = "u"
        elif w in DECENAS:
            if ult in ("u", "d"):
                return None
            grupo += DECENAS[w]; ult = "d"
        elif w in CENTENAS:
            if ult in ("u", "d", "c"):
                return None
            grupo += CENTENAS[w]; ult = "c"
        elif w == "y":
            if ult != "d":
                return None
            ult = "y"
        elif w == "mil":
            total += (grupo or 1) * 1000; grupo = 0; ult = "m"
        elif w in ("millon", "millón", "millones"):
            total = (total + (grupo or 1)) * 1_000_000; grupo = 0; ult = "M"
        else:
            return None
    if ult == "y":
        return None
    return total + grupo


def a_cifras(texto: str, articulos: bool = False) -> str:
    """Cambia cada numeral por sus cifras. «un/una» solo cuentan si articulos=True (en «un perro» son artículo)."""
    # la puntuación pegada («uno,», «quince%», «(cuatrocientos», «nueve)») no debe esconder el numeral
    texto = re.sub(r"(?<=[^\s\d])([,%)])(?!\d)", r" \1", texto)
    texto = re.sub(r"\((?=[^\s\d])", "( ", texto)
    toks = re.split(r"(\s+)", texto)
    pal = [(i, t) for i, t in enumerate(toks) if t and not t.isspace()]
    out = list(toks)
    k = 0
    while k < len(pal):
        i, t = pal[k]
        w = t.lower()
        if w in _TODAS and w != "y" and (articulos or w not in ("un", "una") or (k + 1 < len(pal) and pal[k + 1][1].lower() in ("mil", "millon", "millón"))):
            # tramo más largo que forme un número bien dicho
            mejor = None
            j = k
            while j < len(pal) and pal[j][1].lower() in _TODAS:
                v = _valor([p[1].lower() for p in pal[k:j + 1]])
                if v is not None:
                    mejor = (j, v)
                j += 1
            if mejor is not None:
                j, v = mejor
                # «tres coma cinco»
                if j + 2 < len(pal) and pal[j + 1][1].lower() == "coma":
                    dec = _valor([pal[j + 2][1].lower()])
                    if dec is not None:
                        out[pal[j + 2][0]] = ""; out[pal[j + 1][0]] = ""
                        for q in range(j + 1, j + 3):
                            if pal[q][0] - 1 >= 0:
                                out[pal[q][0] - 1] = ""
                        out[i] = f"{v},{dec}"
                        for q in range(k + 1, j + 1):
                            out[pal[q][0]] = ""
                            out[pal[q][0] - 1] = ""
                        k = j + 3
                        continue
                out[i] = str(v)
                for q in range(k + 1, j + 1):
                    out[pal[q][0]] = ""
                    out[pal[q][0] - 1] = ""
                k = j + 1
                continue
        k += 1
    r = re.sub(r"\s+", " ", "".join(out)).strip()
    r = re.sub(r"\s+([,)])", r"\1", r)
    return re.sub(r"\(\s+", "(", r)
