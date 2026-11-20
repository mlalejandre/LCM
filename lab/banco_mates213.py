"""BANCO DE ENTRENAMIENTO DE EXPRESIONES MATEMÁTICAS (ronda 2.13).

Genera frases variadas (plantillas × números al azar con semilla fija, a veces con los números dichos con palabras) y su resultado,
calculado aquí por el corrector con Python, sin pasar por el LCM. Las plantillas se escribieron durante el desarrollo: es un banco
de ENTRENAMIENTO/desarrollo, no una medida ciega (las ciegas son charla50h y examen_ciego13).

python -m lab.banco_mates213 [N] [-v]     (N frases por plantilla; por defecto 3)
"""
import random
import sys
from fractions import Fraction as Fr

from lab.banco import correr, imprime

_U = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince",
      "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco",
      "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_D = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_C = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def palabras(n):
    if n < 30:
        return _U[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _D[d] + ("" if u == 0 else " y " + _U[u])
    if n == 100:
        return "cien"
    if n < 1000:
        c, r = divmod(n, 100)
        return _C[c] + ("" if r == 0 else " " + palabras(r))
    m, r = divmod(n, 1000)
    return ("mil" if m == 1 else palabras(m) + " mil") + ("" if r == 0 else " " + palabras(r))


def fmt(v):
    v = Fr(v)
    if v.denominator == 1:
        return str(v.numerator)
    return f"{float(v):.10f}".rstrip("0").rstrip(".").replace(".", ",")


PLANTILLAS = {
    "suma": [("¿cuánto es {a} más {b}?", lambda a, b: a + b), ("cuanto es el resultado de la suma entre {a} y {b}", lambda a, b: a + b),
             ("cuánto da el resultado de sumar {a} y {b}", lambda a, b: a + b), ("suma {a} y {b}", lambda a, b: a + b),
             ("¿cuánto suman {a} y {b}?", lambda a, b: a + b), ("{a} + {b}", lambda a, b: a + b), ("dime cuánto es {a} más {b}", lambda a, b: a + b),
             ("¿cuál es la suma de {a} y {b}?", lambda a, b: a + b), ("calcula {a} más {b}", lambda a, b: a + b),
             ("¿me puedes decir cuánto es {a} más {b}?", lambda a, b: a + b), ("¿cuánto es {a} sumado a {b}?", lambda a, b: a + b),
             ("haz la suma de {a} y {b}", lambda a, b: a + b), ("¿cuánto suman {a}, {b} y {c}?", lambda a, b, c: a + b + c)],
    "resta": [("¿cuánto es {a} menos {b}?", lambda a, b: a - b), ("resta {b} a {a}", lambda a, b: a - b), ("¿cuánto da {a} menos {b}?", lambda a, b: a - b),
              ("calcula {a} - {b}", lambda a, b: a - b), ("¿cuál es el resultado de restar {b} a {a}?", lambda a, b: a - b),
              ("resta {b} de {a}", lambda a, b: a - b), ("¿cuánto es la resta de {a} menos {b}?", lambda a, b: a - b)],
    "multiplicacion": [("¿cuánto es {a} por {b}?", lambda a, b: a * b), ("multiplica {a} por {b}", lambda a, b: a * b),
                       ("¿cuánto es {a} multiplicado por {b}?", lambda a, b: a * b), ("{a} x {b}", lambda a, b: a * b),
                       ("¿cuál es el producto de {a} y {b}?", lambda a, b: a * b), ("cuanto da el resultado de multiplicar {a} por {b}", lambda a, b: a * b),
                       ("{a} * {b}", lambda a, b: a * b)],
    "division": [("¿cuánto es {p} entre {b}?", lambda p, b: Fr(p, b)), ("divide {p} entre {b}", lambda p, b: Fr(p, b)),
                 ("¿cuánto da {p} dividido entre {b}?", lambda p, b: Fr(p, b)), ("{p} / {b}", lambda p, b: Fr(p, b)),
                 ("¿cuál es el resultado de dividir {p} entre {b}?", lambda p, b: Fr(p, b)), ("¿cuánto es {p} dividido por {b}?", lambda p, b: Fr(p, b))],
    "porcentaje": [("¿cuánto es el {pc} % de {x}?", lambda pc, x: Fr(pc * x, 100)), ("¿cuál es el {pc} por ciento de {x}?", lambda pc, x: Fr(pc * x, 100)),
                   ("calcula el {pc}% de {x}", lambda pc, x: Fr(pc * x, 100))],
    "unarias": [("¿cuánto es el doble de {a}?", lambda a: 2 * a), ("¿cuál es el triple de {a}?", lambda a: 3 * a), ("¿cuánto es la mitad de {e}?", lambda e: Fr(e, 2)),
                ("¿cuál es la raíz cuadrada de {q}?", lambda q: Fr(int(q ** 0.5 + 0.5))), ("¿cuánto es {s} al cuadrado?", lambda s: s * s),
                ("¿cuánto es {s} al cubo?", lambda s: s ** 3), ("¿cuánto es {s} elevado a {t}?", lambda s, t: s ** t)],
    "listas": [("¿cuál es la media de {a}, {b} y {c}?", lambda a, b, c: Fr(a + b + c, 3)), ("¿cuál es el mayor de {a}, {b} y {c}?", lambda a, b, c: max(a, b, c)),
               ("¿cuál es la diferencia entre {a} y {b}?", lambda a, b: abs(a - b))],
    "mixtas": [("¿cuánto es {a} más {b} por {c}?", lambda a, b, c: a + b * c), ("¿cuánto es ({a} más {b}) por {c}?", lambda a, b, c: (a + b) * c),
               ("calcula {a} menos {b} por {c}", lambda a, b, c: a - b * c), ("¿cuánto es {a} por {b} más {c}?", lambda a, b, c: a * b + c),
               ("{a} + {b} * {c}", lambda a, b, c: a + b * c)],
}


def _args(nombre_vars, rnd):
    v = {}
    v["b"] = rnd.randint(2, 60)
    v["a"] = rnd.randint(2, 999)
    v["c"] = rnd.randint(2, 99)
    v["p"] = v["b"] * rnd.randint(2, 40)
    v["pc"] = rnd.choice([5, 10, 15, 20, 25, 30, 40, 50, 75])
    v["x"] = rnd.choice([20, 40, 60, 80, 100, 120, 200, 240, 300, 500, 1000])
    v["e"] = rnd.randint(1, 500) * 2
    v["q"] = rnd.randint(2, 40) ** 2
    v["s"] = rnd.randint(2, 15)
    v["t"] = rnd.randint(2, 6)
    return {k: v[k] for k in nombre_vars}


def generar(n=3, semilla=2113):
    rnd = random.Random(semilla)
    D = []
    for cat, ps in PLANTILLAS.items():
        turnos = []
        for plantilla, f in ps:
            nombres = f.__code__.co_varnames[:f.__code__.co_argcount]
            for k in range(n):
                xs = _args(nombres, rnd)
                v = f(*[xs[x] for x in nombres])
                con_palabras = (k % 3 == 2) and "/" not in plantilla and "*" not in plantilla and "+" not in plantilla and "-" not in plantilla
                fr = plantilla.format(**{x: (palabras(xs[x]) if con_palabras and xs[x] < 100000 else xs[x]) for x in xs})
                esperado = fmt(v)
                if Fr(v).denominator == 1:
                    crit = esperado
                elif len(esperado.split(",")[1]) <= 4:
                    crit = esperado + "|" + esperado.replace(",", ".")
                else:                                     # decimal periódico: basta con las dos primeras cifras decimales
                    crit = esperado[:esperado.index(",") + 3] + "*"
                turnos.append((fr, crit))
        D.append({"id": "bm-" + cat, "cat": cat, "turnos": turnos})
    return D


def medir(n=3, verboso=False, salida="lab/res_banco_mates213.json"):
    return correr(generar(n), verboso=verboso, salida=salida, continua=True)


if __name__ == "__main__":
    n = int(next((a for a in sys.argv[1:] if a.isdigit()), 3))
    f, r = medir(n, "-v" in sys.argv)
    imprime(r, f"BANCO MATES 213 (n por plantilla={n})")
