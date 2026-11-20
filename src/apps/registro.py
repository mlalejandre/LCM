"""Registro común de aplicaciones: lo que el LCM y las aplicaciones comparten (y lo que la prueba de sincronía compara)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable, Optional

VERSION_REGISTRO = "2.13.0"


class ErrorApp(Exception):
    """Error de dominio que la aplicación explica (dividir entre cero, raíz de un negativo…)."""


@dataclass
class App:
    nombre: str                                    # «suma»
    familia: str                                   # «aritmetica», «calendario», «dibujo»
    funcion: Callable
    aridad: tuple = (2, 2)                         # (mínimo, máximo); máximo None = n-aria
    simbolo: str = ""                              # «+»
    precedencia: int = 0                           # para las expresiones: 1 suma/resta, 2 producto/cociente, 3 potencia
    lexico: dict = field(default_factory=dict)     # operador / verbo / sustantivo / prefijo / sufijo / problema_mas / problema_menos…
    concepto: str = "operación matemática"         # clase en la base de fábrica del LCM
    nombre_humano: str = ""                        # «la suma»
    ejemplos: list = field(default_factory=list)   # [(frase, texto esperado en la respuesta)]
    version: str = "1.0"

    def firma(self):
        return {"nombre": self.nombre, "familia": self.familia, "aridad": list(self.aridad), "simbolo": self.simbolo,
                "precedencia": self.precedencia, "lexico": self.lexico, "concepto": self.concepto, "version": self.version,
                "ejemplos": [list(e) for e in self.ejemplos]}


REGISTRO: dict[str, App] = {}


def registra(app: App) -> App:
    if app.nombre in REGISTRO:
        raise ValueError(f"aplicación repetida: {app.nombre}")
    REGISTRO[app.nombre] = app
    return app


def app(nombre: str) -> Optional[App]:
    return REGISTRO.get(nombre)


def de_familia(familia: str):
    return [a for a in REGISTRO.values() if a.familia == familia]


def ejecuta(nombre: str, *args):
    """Única puerta por la que el LCM obtiene un resultado: ejecuta la aplicación y devuelve (valor, traza)."""
    a = REGISTRO[nombre]
    mn, mx = a.aridad
    if len(args) < mn or (mx is not None and len(args) > mx):
        raise ErrorApp(f"«{a.nombre}» necesita {mn}{'' if mx == mn else ' o más'} datos")
    v = a.funcion(*args)
    return v, {"app": a.nombre, "familia": a.familia, "args": list(args), "valor": v, "version": a.version}


def manifiesto() -> dict:
    """Lo que el LCM tiene que conocer de las aplicaciones (con su huella para comprobar la sincronía)."""
    cuerpo = {"version_registro": VERSION_REGISTRO, "apps": {n: REGISTRO[n].firma() for n in sorted(REGISTRO)}}
    huella = hashlib.sha256(json.dumps(cuerpo, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    return dict(cuerpo, huella=huella)
