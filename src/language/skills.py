"""Habilidades EXACTAS (parche-87): codigo, no lenguaje aprendido. El enrutador (intents.py) decide la operacion; aqui se ejecuta.
Una habilidad nueva se anade una vez y sirve para infinitas formas de pedirla."""
import re
from datetime import date, timedelta
from typing import Optional

from .intents import clean

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
NUMS = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
        "trece": 13, "catorce": 14, "quince": 15, "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50, "cien": 100}

UBICACION = ("No sé dónde estamos físicamente: no tengo sensores ni ubicación. Solo sé que estamos hablando tú y yo en esta conversación. "
             "Si me dices dónde estás, lo recuerdo.")

_DATE = re.compile(r"(?:el\s+)?(?:dia\s+)?(\d{1,2})\s+de\s+(" + "|".join(MONTHS) + r")(?:\s+de\s+(\d{4}))?")


def _num(tok: str) -> Optional[int]:
    return int(tok) if tok.isdigit() else NUMS.get(tok)


def _u(w: str) -> str:
    return {"dia": "día", "dias": "días"}.get(w, w)


def _fmt(d: date, with_year: bool) -> str:
    return f"{d.day} de {MONTHS[d.month - 1]}" + (f" de {d.year}" if with_year else "")


def calc_fecha(text: str, today: date) -> Optional[str]:
    """"Si hoy es 3 de febrero, ¿que dia fue ayer?" -> "Si hoy es 3 de febrero, ayer fue 2 de febrero." None si no se entiende (el pipeline sigue)."""
    t = clean(text)
    m = _DATE.search(t)
    if not m:
        return None
    day, month, year = int(m.group(1)), MONTHS.index(m.group(2)) + 1, m.group(3)
    y = int(year) if year else today.year
    try:
        base = date(y, month, day)
    except ValueError:
        return f"El {day} de {m.group(2)}{' de ' + year if year else ''} no existe en el calendario."
    rest = t[:m.start()] + " " + t[m.end():]
    delta, label = None, ""
    for pat, d_, lab in ((r"\bpasado manana\b", 2, "pasado mañana"), (r"\b(?:anteayer|antes de ayer)\b", -2, "anteayer"), (r"\bayer\b", -1, "ayer"),
                         (r"\bmanana\b", 1, "mañana")):
        if re.search(pat, rest):
            delta, label = d_, lab
            break
    if delta is None:
        mm = re.search(r"\b(?:dentro de|en)\s+(\w+)\s+(dias?|semanas?)\b", rest) or re.search(r"\b(\w+)\s+(dias?|semanas?)\s+(?:despues|mas tarde)\b", rest)
        if mm and _num(mm.group(1)):
            n = _num(mm.group(1)) * (7 if mm.group(2).startswith("semana") else 1)
            delta, label = n, f"dentro de {mm.group(1)} {_u(mm.group(2))}"
        else:
            mm = re.search(r"\bhace\s+(\w+)\s+(dias?|semanas?)\b", rest) or re.search(r"\b(\w+)\s+(dias?|semanas?)\s+(?:antes|atras)\b", rest)
            if mm and _num(mm.group(1)):
                n = _num(mm.group(1)) * (7 if mm.group(2).startswith("semana") else 1)
                delta, label = -n, f"hace {mm.group(1)} {_u(mm.group(2))}"
    if delta is None:
        return None
    try:
        res = base + timedelta(days=delta)
    except OverflowError:
        return None
    wd = bool(re.search(r"dia de la semana|que dia fue|que dia sera|que dia es", rest)) and bool(year or "semana" in rest)
    verb = "fue" if delta < 0 else "será"
    head = f"Si hoy es {_fmt(base, bool(year))}, {label} {verb} "
    out = head + _fmt(res, bool(year))
    if wd:
        out += f" ({WEEKDAYS[res.weekday()]}{'' if year else ', suponiendo el año ' + str(base.year)})"
    return out + "."


# ---------------------------------------------------------------------------------------------- parche-88: aritmetica, dia de la semana, cuenta de dias, fuera de alcance
import ast
import math
import operator

FUERA = ("Eso queda fuera de lo que sé hacer: no tengo acceso a internet ni a datos del exterior (tiempo, noticias, precios, resultados deportivos, música...). "
         "Sí puedo aprender lo que me cuentes, contestar sobre ello, razonar con reglas, calcular fechas y operaciones y decirte la hora.")
_UN = {"cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
       "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiuno": 21,
       "veintiun": 21, "veintidos": 22, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29}
_TENS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90}
_HUND = {"cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300, "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600, "setecientos": 700,
         "ochocientos": 800, "novecientos": 900}
_BIN = [(r"\bdividido\s+(?:entre|por)\b", "/"), (r"\bmultiplicado\s+por\b", "*"), (r"\belevado\s+a(?:l)?\b", "^"), (r"\bmas\b", "+"), (r"\bmenos\b", "-"),
        (r"\bveces\b", "*"), (r"\bpor\b", "*"), (r"\bentre\b", "/"), (r"(?<=\d)\s*x\s*(?=\d)", "*")]


def _words_to_digits(t: str) -> str:
    toks, out, i = t.split(), [], 0
    while i < len(toks):
        w = toks[i]
        if w in _UN or w in _TENS or w in _HUND:
            val, j = 0, i
            while j < len(toks):
                x = toks[j]
                if x in _HUND:
                    val += _HUND[x]
                elif x in _TENS:
                    val += _TENS[x]
                elif x in _UN and (j == i or toks[j - 1] in ("y",) or toks[j - 1] in _HUND):
                    val += _UN[x]
                elif x == "y" and j + 1 < len(toks) and toks[j + 1] in _UN and j > i and toks[j - 1] in _TENS:
                    pass
                else:
                    break
                j += 1
            out.append(str(val))
            i = max(j, i + 1)
        else:
            out.append(w)
            i += 1
    return " ".join(out)


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        a, b = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and (abs(b) > 200 or abs(a) > 10 ** 6):
            raise ValueError("demasiado grande")
        return _OPS[type(node.op)](a, b)
    raise ValueError("no soportado")


def _fmt_num(x) -> str:
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e15:
            return str(int(x))
        return f"{x:.6f}".rstrip("0").rstrip(".").replace(".", ",")
    return str(x)


def aritmetica(text: str) -> Optional[str]:
    """"¿Cuanto es siete por ocho?", "2+2", "raiz cuadrada de 81", "el 20% de 150". None si no hay una operacion clara."""
    t = text.lower().replace("¿", " ").replace("?", " ")
    from .lexicon import norm
    t = norm(t)
    t = re.sub(r"(\d+)\s*(?:%|por ciento)\s*de\s*(\d+)", r"\1 pc \2", t)
    t = re.sub(r"[,;:!¡\"«»()]", " ", t)
    t = re.sub(r"(\d)\.(\d{3})", r"\1\2", t)
    t = _words_to_digits(re.sub(r"\s+", " ", t).strip())
    m = re.search(r"(\d+)\s+pc\s+(\d+)", t)
    if m:
        r = int(m.group(1)) * int(m.group(2)) / 100
        return f"El {m.group(1)} % de {m.group(2)} es {_fmt_num(r)}."
    m = re.search(r"raiz(?:\s+cuadrada)?\s+de\s+(\d+)", t)
    if m:
        r = math.sqrt(int(m.group(1)))
        return f"La raíz cuadrada de {m.group(1)} es {_fmt_num(r)}."
    m = re.search(r"\b(suma|multiplica|divide|resta)\s+(\d+)\s+(?:y|por|entre|a)\s+(\d+)", t)
    expr = None
    if m:
        a, b = m.group(2), m.group(3)
        expr = {"suma": f"{a}+{b}", "multiplica": f"{a}*{b}", "divide": f"{a}/{b}", "resta": f"{a}-{b}"}[m.group(1)]
    else:
        u = t
        for pat, sym in _BIN:
            u = re.sub(pat, f" {sym} ", u)
        u = re.sub(r"(?<=\d)\s*([+\-*/^x])\s*(?=\d)", r" \1 ", u)
        m = re.search(r"\d+(?:\s*[+\-*/^]\s*\d+)+", u)
        if m:
            expr = re.sub(r"\s+", "", m.group(0))
    if not expr:
        return None
    try:
        val = _eval(ast.parse(expr.replace("^", "**"), mode="eval"))
    except ZeroDivisionError:
        return "No se puede dividir entre cero."
    except (ValueError, SyntaxError, OverflowError):
        return None
    shown = expr.replace("*", " × ").replace("/", " ÷ ").replace("+", " + ").replace("-", " − ").replace("^", " ^ ")
    return f"{re.sub(chr(32) + '+', chr(32), shown).strip()} = {_fmt_num(val)}."


HOLIDAYS = {"navidad": (12, 25), "nochebuena": (12, 24), "nochevieja": (12, 31), "ano nuevo": (1, 1), "reyes": (1, 6), "san valentin": (2, 14),
            "halloween": (10, 31), "el dia de la hispanidad": (10, 12), "la hispanidad": (10, 12)}


def _target_date(t: str, today: date, future: bool = True) -> Optional[date]:
    m = _DATE.search(t)
    if m:
        y = int(m.group(3)) if m.group(3) else None
        mo, d = MONTHS.index(m.group(2)) + 1, int(m.group(1))
        try:
            if y:
                return date(y, mo, d)
            cand = date(today.year, mo, d)
            if future and cand < today:
                cand = date(today.year + 1, mo, d)
            if not future and cand > today:
                cand = date(today.year - 1, mo, d)
            return cand
        except ValueError:
            return None
    for k, (mo, d) in HOLIDAYS.items():
        if k in t:
            cand = date(today.year, mo, d)
            return cand if (cand >= today or not future) else date(today.year + 1, mo, d)
    return None


def dia_semana(text: str, today: date) -> Optional[str]:
    """"¿Que dia de la semana fue el 1 de enero de 2000?" """
    t = clean(text)
    m = _DATE.search(t)
    if not m:
        return None
    try:
        d = date(int(m.group(3)) if m.group(3) else today.year, MONTHS.index(m.group(2)) + 1, int(m.group(1)))
    except ValueError:
        return f"El {m.group(1)} de {m.group(2)} no existe en el calendario."
    verb = "fue" if d < today else ("es" if d == today else "será")
    sup = "" if m.group(3) else f" (suponiendo el año {d.year})"
    return f"El {_fmt(d, bool(m.group(3)))} {verb} {WEEKDAYS[d.weekday()]}{sup}."


def dias_hasta(text: str, today: date) -> Optional[str]:
    """"¿Cuantos dias faltan para Navidad?" / "¿cuantos dias han pasado desde el 1 de enero de 2020?" """
    t = clean(text)
    past = bool(re.search(r"\b(han pasado|hace|desde|pasaron|llevamos)\b", t)) and not re.search(r"\b(faltan|quedan|falta|queda|hasta)\b", t)
    d = _target_date(t, today, future=not past)
    if d is None:
        return None
    n = (d - today).days
    if n == 0:
        return "Es hoy."
    nombre = _fmt(d, True)
    if n > 0:
        return f"Faltan {n} día{'s' if n != 1 else ''} para el {nombre}."
    return f"Han pasado {-n} día{'s' if n != -1 else ''} desde el {nombre}."
