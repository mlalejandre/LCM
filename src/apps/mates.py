"""Aplicaciones de aritmética, exactas (fracciones) y deterministas."""
from __future__ import annotations

from fractions import Fraction as Fr
from math import isqrt

from .registro import App, ErrorApp, registra


class Aprox(Fr):
    """Resultado redondeado (una raíz no exacta): se dice «aproximadamente»."""


def numero(x) -> Fr:
    return x if isinstance(x, Fr) else Fr(str(x))


def formato(x) -> str:
    """Fracción -> texto en castellano: 2,5 · 1024 · 0,333333 (aproximado cuando no es exacto)."""
    x = numero(x)
    if x.denominator == 1:
        return str(x.numerator)
    d = x.denominator
    while d % 2 == 0:
        d //= 2
    while d % 5 == 0:
        d //= 5
    if d == 1 and not isinstance(x, Aprox):               # decimal finito: exacto
        s = f"{float(x):.10f}".rstrip("0").rstrip(".")
    else:
        s = f"{float(x):.6f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def es_exacto(x) -> bool:
    if isinstance(x, Aprox):
        return False
    x = numero(x)
    d = x.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def _suma(*xs):
    return sum((numero(x) for x in xs), Fr(0))


def _resta(a, b):
    return numero(a) - numero(b)


def _producto(*xs):
    r = Fr(1)
    for x in xs:
        r *= numero(x)
    return r


def _cociente(a, b):
    if numero(b) == 0:
        raise ErrorApp("No se puede dividir entre cero.")
    return numero(a) / numero(b)


def _potencia(a, b):
    b = numero(b)
    if b.denominator != 1 or abs(b) > 10000:
        raise ErrorApp("Solo sé elevar a exponentes enteros razonables.")
    if numero(a) == 0 and b < 0:
        raise ErrorApp("No se puede elevar cero a un exponente negativo.")
    return numero(a) ** int(b)


def _raiz(a, n=2):
    a, n = numero(a), int(numero(n))
    if a < 0 and n % 2 == 0:
        raise ErrorApp("Un número negativo no tiene raíz cuadrada real.")
    if a.denominator == 1:
        r = round(abs(a.numerator) ** (1 / n))
        for c in (r - 1, r, r + 1):
            if c >= 0 and c ** n == abs(a.numerator):
                return Fr(c if a >= 0 else -c)
    if n == 2 and a.denominator == 1 and isqrt(a.numerator) ** 2 == a.numerator:
        return Fr(isqrt(a.numerator))
    return Aprox(str(round(float(a) ** (1 / n), 6)))


def _porcentaje(p, x):
    return numero(p) * numero(x) / 100


def _media(*xs):
    return _suma(*xs) / len(xs)


def _diferencia(a, b):
    return abs(numero(a) - numero(b))


registra(App("suma", "aritmetica", _suma, (2, None), "+", 1, nombre_humano="la suma",
             lexico={"operador": ["más", "mas", "+", "sumado a", "sumado con"], "verbo": ["sumar", "suma", "súmale", "sumale", "añade", "añadir", "suman", "sumo", "le sumo", "le añado"],
                     "sustantivo": ["suma", "total"], "pregunta": ["cuánto suman", "cuanto suman"],
                     "problema_mas": ["me dan", "me dio", "me dieron", "me das", "me da", "me diste", "me regalan", "me regala", "me regalas", "me regalaron", "nos dan", "nos dieron", "te dan", "le regalan", "le regalaron", "le dan", "le dieron", "gana", "ganó", "gano", "recibe", "recibo", "recibió", "suben", "subieron", "sube",
                                      "compra", "compro", "compró", "encuentra", "encuentro", "encontró", "añade", "añado", "llegan", "llegaron", "entran", "entraron", "más"]},
             ejemplos=[("¿cuánto es 2 más 5?", "7"), ("la suma de 230 y 420", "650"), ("¿cuánto suman 15, 25 y 35?", "75")]))
registra(App("resta", "aritmetica", _resta, (2, 2), "−", 1, nombre_humano="la resta",
             lexico={"operador": ["menos", "-", "−"], "verbo": ["restar", "resta", "réstale", "restale", "quita", "quitar", "le resto", "le quito", "resto"],
                     "sustantivo": ["resta", "diferencia"],
                     "problema_menos": ["faltaron", "faltan", "se me rompieron", "se rompieron", "se me rompió", "se rompió", "rompí", "se me cayeron", "se cayeron", "se me perdieron", "se perdieron",
                                        "se estropearon", "se escaparon", "devolví", "tiré", "gasta", "gastó", "gasté", "se gastó", "se gasta", "pierde", "perdió", "he perdido", "perdí", "come", "comió", "me comí", "me como", "regala", "regaló",
                                        "regalé", "bajan", "bajaron", "baja", "quita", "quitó", "vende", "vendió", "vendí", "rompe", "rompió", "salen", "salieron", "se van", "se fueron",
                                        "presta", "prestó", "presté", "da", "di", "doy", "menos", "usa", "usó", "usé"]},
             ejemplos=[("¿cuánto es 5 menos 9?", "-4"), ("resta 18 a 50", "32")]))
registra(App("multiplicacion", "aritmetica", _producto, (2, None), "×", 2, nombre_humano="la multiplicación",
             lexico={"operador": ["por", "x", "×", "*", "multiplicado por"], "verbo": ["multiplicar", "multiplica", "multiplícalo", "multiplicalo"], "sustantivo": ["producto", "multiplicación"]},
             ejemplos=[("¿cuánto es 12 por 15?", "180"), ("multiplica 25 por 4", "100")]))
registra(App("division", "aritmetica", _cociente, (2, 2), "÷", 2, nombre_humano="la división",
             lexico={"operador": ["entre", "dividido entre", "dividido por", "/", "÷", ":"], "verbo": ["dividir", "divide", "divídelo", "dividelo", "reparte", "repartir"],
                     "sustantivo": ["cociente", "división"], "problema_reparto": ["reparte", "repartimos", "repartir", "repartió", "reparto", "para", "entre", "a cada uno", "cada uno"]},
             ejemplos=[("divide 144 entre 12", "12"), ("¿cuánto es 10 entre 4?", "2,5")]))
registra(App("potencia", "aritmetica", _potencia, (2, 2), "^", 3, nombre_humano="la potencia",
             lexico={"operador": ["elevado a", "elevado al", "^", "**"], "sufijo": {"al cuadrado": 2, "al cubo": 3}, "sustantivo": ["potencia"]},
             ejemplos=[("¿cuánto es 7 al cuadrado?", "49"), ("¿cuánto es 2 elevado a 10?", "1024")]))
registra(App("raiz", "aritmetica", _raiz, (1, 2), "√", 4, nombre_humano="la raíz",
             lexico={"prefijo": ["la raíz cuadrada de", "la raiz cuadrada de", "raíz cuadrada de", "raiz cuadrada de", "la raíz de", "la raiz de", "raíz de", "raiz de"],
                     "sustantivo": ["raíz", "raíz cuadrada"]},
             ejemplos=[("¿cuál es la raíz cuadrada de 225?", "15"), ("¿cuánto es la raíz de 49?", "7")]))
registra(App("porcentaje", "aritmetica", _porcentaje, (2, 2), "%", 4, nombre_humano="el porcentaje",
             lexico={"patron": ["el N % de X", "el N por ciento de X"], "sustantivo": ["porcentaje", "tanto por ciento"]},
             ejemplos=[("¿cuánto es el 15 % de 80?", "12"), ("¿cuánto es el 25 por ciento de 200?", "50")]))
registra(App("media", "aritmetica", _media, (1, None), "media", 4, nombre_humano="la media",
             lexico={"prefijo": ["la media de", "la media entre", "el promedio de", "la media aritmética de", "el valor medio de"], "sustantivo": ["media", "promedio"]},
             ejemplos=[("¿cuál es la media de 4, 8 y 12?", "8")]))
registra(App("doble", "aritmetica", lambda x: numero(x) * 2, (1, 1), "2×", 4, nombre_humano="el doble", lexico={"prefijo": ["el doble de", "doble de"]},
             ejemplos=[("¿cuánto es el doble de 37?", "74")]))
registra(App("triple", "aritmetica", lambda x: numero(x) * 3, (1, 1), "3×", 4, nombre_humano="el triple", lexico={"prefijo": ["el triple de", "triple de"]},
             ejemplos=[("¿cuál es el triple de 15?", "45")]))
registra(App("mitad", "aritmetica", lambda x: numero(x) / 2, (1, 1), "½", 4, nombre_humano="la mitad", lexico={"prefijo": ["la mitad de", "mitad de"]},
             ejemplos=[("¿cuánto es la mitad de 90?", "45")]))
registra(App("diferencia", "aritmetica", _diferencia, (2, 2), "|−|", 1, nombre_humano="la diferencia",
             lexico={"prefijo": ["la diferencia entre", "la diferencia de"], "pregunta": ["cuánto se llevan", "cuántos años nos llevamos", "cuántos años se llevan"]},
             ejemplos=[("¿cuál es la diferencia entre 12 y 9?", "3")]))
registra(App("maximo", "aritmetica", lambda *xs: max(numero(x) for x in xs), (2, None), "máx", 4, nombre_humano="el mayor",
             lexico={"prefijo": ["el mayor de", "el máximo de", "el número mayor de"]}, ejemplos=[("¿cuál es el mayor de 3, 9 y 4?", "9")]))
registra(App("minimo", "aritmetica", lambda *xs: min(numero(x) for x in xs), (2, None), "mín", 4, nombre_humano="el menor",
             lexico={"prefijo": ["el menor de", "el mínimo de", "el número menor de"]}, ejemplos=[("¿cuál es el menor de 3, 9 y 4?", "3")]))
