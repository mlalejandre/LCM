"""parche-112: genera cartuchos/razon_base.json, el paquete de reglas de razonamiento general (datos, no codigo).
  python -m scripts.construir_razonamiento
Un cartucho `razon_*` puede traer `reglas` (Horn: si [...] entonces [...]) y `propiedades` (transitiva, simetrica, inversa, subprop, funcional, funcional_inv,
asimetrica, heredable, compara, mundo_cerrado). El mismo motor sirve para cualquier area: basta otro cartucho."""
import json
import os

PROPIEDADES = {
    "ES": {"transitiva": True},
    "PARTE_DE": {"transitiva": True},
    "TENER": {"heredable": True}, "VIVIR_EN": {"heredable": True}, "COMER": {"heredable": True}, "PODER": {"heredable": True},
    "PADRE_DE": {"inversa": "HIJO_DE", "subprop": "ANTEPASADO_DE"},
    "MADRE_DE": {"inversa": "HIJO_DE", "subprop": "ANTEPASADO_DE"},
    "ANTEPASADO_DE": {"transitiva": True, "asimetrica": True},
    "HERMANO_DE": {"simetrica": True}, "HERMANA_DE": {"simetrica": True}, "PRIMO_DE": {"simetrica": True},
    "ESPOSO_DE": {"inversa": "ESPOSA_DE"},
    "ANTES_DE": {"transitiva": True, "inversa": "DESPUES_DE", "asimetrica": True},
    "DESPUES_DE": {"transitiva": True, "asimetrica": True},
}


def R(id_, si, entonces):
    return {"id": id_, "si": si, "entonces": entonces}


REGLAS = [
    R("parte_por_clase", [["?X", "ES", "?Y"], ["?Y", "PARTE_DE", "?Z"]], ["?X", "PARTE_DE", "?Z"]),
    R("abuelo_p", [["?X", "PADRE_DE", "?Y"], ["?Y", "PADRE_DE", "?Z"]], ["?X", "ABUELO_DE", "?Z"]),
    R("abuelo_pm", [["?X", "PADRE_DE", "?Y"], ["?Y", "MADRE_DE", "?Z"]], ["?X", "ABUELO_DE", "?Z"]),
    R("abuela_m", [["?X", "MADRE_DE", "?Y"], ["?Y", "PADRE_DE", "?Z"]], ["?X", "ABUELA_DE", "?Z"]),
    R("abuela_mm", [["?X", "MADRE_DE", "?Y"], ["?Y", "MADRE_DE", "?Z"]], ["?X", "ABUELA_DE", "?Z"]),
    R("hermano_pp", [["?P", "PADRE_DE", "?X"], ["?P", "PADRE_DE", "?Y"], ["?X", "@DISTINTO", "?Y"]], ["?X", "HERMANO_DE", "?Y"]),
    R("tio", [["?X", "HERMANO_DE", "?Y"], ["?Y", "PADRE_DE", "?Z"]], ["?X", "TIO_DE", "?Z"]),
    R("primo", [["?A", "PADRE_DE", "?X"], ["?A", "HERMANO_DE", "?B"], ["?B", "PADRE_DE", "?Z"]], ["?X", "PRIMO_DE", "?Z"]),
]


def main(base="cartuchos"):
    c = {"nombre": "razon_base", "fuente": "parche-112: paquete de reglas de razonamiento general", "hechos": [], "reglas": REGLAS, "propiedades": PROPIEDADES}
    with open(os.path.join(base, "razon_base.json"), "w", encoding="utf-8") as fh:
        json.dump(c, fh, ensure_ascii=False, indent=1)
    print("razon_base:", len(REGLAS), "reglas,", len(PROPIEDADES), "propiedades")


if __name__ == "__main__":
    main()
