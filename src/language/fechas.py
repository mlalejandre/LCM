"""Fechas ABSOLUTAS (parche-53). Idea del usuario: toda expresion temporal relativa ("ayer", "el lunes", "el ano pasado")
se convierte, al aprender el hecho, en una fecha absoluta anclada a "hoy" (la fecha de la conversacion). Asi "ayer" dicho
el 6 de noviembre sigue valiendo 5 de noviembre aunque pasen los meses, y se pueden ordenar los hechos sin confusion.

Un tiempo se guarda como intervalo ISO "AAAA-MM-DD/AAAA-MM-DD" (un dia: inicio = fin).
Convenios (documentados): un dia de la semana sin mas ("el lunes") es el ultimo que ya paso; "proximo" mira al futuro;
un mes suelto es el mas reciente que ya empezo; las estaciones usan fechas del hemisferio norte.
"""
import re
from datetime import date, timedelta
from typing import Optional, Tuple

from src.language.lexicon import norm

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
WEEKDAYS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
SEASONS = {"primavera": ((3, 21), (6, 20)), "verano": ((6, 21), (9, 22)), "otono": ((9, 23), (12, 20)), "invierno": ((12, 21), (3, 20))}
FUTURE = {"proximo", "proxima", "siguiente"}
_ABS = re.compile(r"\b(?:el\s+|del\s+|de\s+)?(\d{1,2})\s+de\s+(" + "|".join(MONTHS) + r")(?:\s+de\s+(\d{4}))?", re.I)


def _iv(a: date, b: date) -> str:
    return f"{a.isoformat()}/{b.isoformat()}"


def parse_iv(iv: str) -> Tuple[date, date]:
    a, _, b = iv.partition("/")
    return date.fromisoformat(a), date.fromisoformat(b or a)


def resolve(key: str, today: date) -> Optional[str]:
    """Clave normalizada de extract.when_of -> intervalo ISO anclado a today, o None si no se puede fijar."""
    if not key:
        return None
    if key.startswith("abs:"):
        return key[4:]
    parts = key.split("_")
    w, mods = parts[0], set(parts[1:])
    fut = bool(mods & FUTURE)
    day = {"hoy": 0, "ayer": -1, "anteayer": -2, "anoche": -1, "manana": 1}.get(w)
    if day is not None and not mods:
        d = today + timedelta(days=day)
        return _iv(d, d)
    if w in WEEKDAYS:
        k = WEEKDAYS.index(w)
        delta = (k - today.weekday()) % 7
        d = today + timedelta(days=delta or 7) if fut else today - timedelta(days=(today.weekday() - k) % 7 or 7)
        return _iv(d, d)
    if w in MONTHS:
        m = MONTHS.index(w) + 1
        y = today.year + (1 if fut and m <= today.month else 0) if fut else (today.year if m <= today.month else today.year - 1)
        end = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
        return _iv(date(y, m, 1), end)
    if re.fullmatch(r"\d{4}", w):
        return _iv(date(int(w), 1, 1), date(int(w), 12, 31))
    if w == "ano" and mods:
        y = today.year + (1 if fut else -1)
        return _iv(date(y, 1, 1), date(y, 12, 31))
    if w == "mes" and mods:
        y, m = today.year, today.month + (1 if fut else -1)
        y, m = y + (m > 12) - (m < 1), (m - 1) % 12 + 1
        return _iv(date(y, m, 1), date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
    if w == "semana" and mods:
        mon = today - timedelta(days=today.weekday()) + timedelta(days=7 if fut else -7)
        return _iv(mon, mon + timedelta(days=6))
    if w in SEASONS:
        (m1, d1), (m2, d2) = SEASONS[w]
        for y in (today.year, today.year - 1, today.year - 2):
            a = date(y, m1, d1)
            b = date(y + (m2 < m1), m2, d2)
            if a <= today:
                return _iv(a, b)
    return None


def month_name(m: int) -> str:
    return MONTHS[m - 1]


def fmt(iv: str) -> str:
    """Intervalo ISO -> texto en espanol: "5 de noviembre de 2026", "octubre de 2026", "2020"."""
    a, b = parse_iv(iv)
    if a == b:
        return f"{a.day} de {month_name(a.month)} de {a.year}"
    if a.day == 1 and (b + timedelta(days=1)).day == 1 and a.month == b.month and a.year == b.year:
        return f"{month_name(a.month)} de {a.year}"
    if a == date(a.year, 1, 1) and b == date(a.year, 12, 31):
        return str(a.year)
    return f"del {a.day} de {month_name(a.month)} de {a.year} al {b.day} de {month_name(b.month)} de {b.year}"


def extract_abs(text: str, today: date):
    """Quita de la frase una fecha escrita ("el 5 de noviembre [de 2025]") -> (frase limpia, intervalo, como se escribio) o (texto, None, "").
    Sin ano, vale el ano del ancla; si eso cae en el futuro, el ano anterior (convenio del pasado)."""
    m = _ABS.search(text)
    if not m:
        return text, None, ""
    d, mo, y = int(m.group(1)), MONTHS.index(m.group(2).lower()) + 1, m.group(3)
    try:
        dt = date(int(y), mo, d) if y else date(today.year, mo, d)
        if not y and dt > today:
            dt = date(today.year - 1, mo, d)
    except ValueError:
        return text, None, ""
    clean = (text[:m.start()] + text[m.end():]).replace("  ", " ")
    clean = re.sub(r"\s+([.?!,])", r"\1", clean).strip()
    return clean, _iv(dt, dt), m.group(0).strip()


def before(iv: str, ref: str) -> bool:
    return parse_iv(iv)[1] < parse_iv(ref)[0]


def after(iv: str, ref: str) -> bool:
    return parse_iv(iv)[0] > parse_iv(ref)[1]


def contains(iv: str, ref: str) -> bool:
    a, b = parse_iv(iv)
    c, d = parse_iv(ref)
    return a <= c and d <= b or c <= a and b <= d
