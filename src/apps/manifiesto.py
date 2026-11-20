"""Escribe src/apps/manifiesto.json: lo que el LCM y las aplicaciones han acordado (léxico, versiones, ejemplos) con su huella.
Uso: python -m src.apps.manifiesto   (tras añadir o cambiar una aplicación; la prueba de sincronía lo exige)."""
import json
import os

from . import registro as R

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifiesto.json")


def escribe():
    m = R.manifiesto()
    with open(RUTA, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
    return m


def leido():
    with open(RUTA, encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    m = escribe()
    print(f"manifiesto {m['version_registro']} · {len(m['apps'])} aplicaciones · huella {m['huella']}")
