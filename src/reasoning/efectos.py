"""Efectos de las acciones elementales (parche-59, bloque C): lo que cambia cuando alguien da, vende, compra, abre, rompe, llega...
Recibe los hechos de UNA frase [(s, p, o, o_disp)] y devuelve operaciones:
   ("add", (s, p, o))   hecho nuevo (pasa por la coherencia: si cambia un estado, el viejo pasa a pasado)
   ("lose", (s, p, o))  el hecho deja de valer (pasa a pasado)
"""
from typing import List, Tuple

GAIN = {"comprar", "recibir", "ganar", "encontrar", "conseguir", "coger", "heredar"}                 # el sujeto pasa a tener el objeto
LOSE = {"perder", "tirar"}                                                                         # el sujeto deja de tenerlo
GIVE = {"dar", "regalar", "entregar", "prestar", "vender", "devolver", "ofrecer", "enviar", "mandar", "pasar"}   # el sujeto lo pierde y el destinatario lo gana
STATE = {"abrir": "abierto", "cerrar": "cerrado", "romper": "roto", "encender": "encendido", "apagar": "apagado",
         "terminar": "terminado", "arreglar": "arreglado", "llenar": "lleno", "vaciar": "vacio", "limpiar": "limpio",
         "ensuciar": "sucio", "mojar": "mojado", "secar": "seco"}
ARRIVE = {"ir_a", "llegar_a", "volver_a", "venir_a", "entrar_en", "viajar_a", "regresar_a"}
LEAVE = {"salir_de"}


def _inflect(adj: str, disp: str) -> str:
    d = (disp or "").lower().strip()
    fem = d.startswith(("la ", "una ", "las ", "unas ")) or (d.endswith("a") and not d.startswith(("el ", "un ", "los ")) and not d.endswith("ma"))
    plural = d.startswith(("las ", "los ", "unas ", "unos "))
    if adj.endswith("o"):
        adj = adj[:-1] + ("a" if fem else "o")
    return adj + ("s" if plural else "")


def effects(facts: List[Tuple[str, str, str, str]]) -> List[Tuple[str, Tuple[str, str, str]]]:
    ops = []
    facts = [(s, p.lower(), o, od) for s, p, o, od in facts]          # think da los nombres en MAYUSCULAS
    objs = {}
    for s, p, o, od in facts:
        if "_" not in p:
            objs.setdefault((s, p), (o, od))
    for s, p, o, od in facts:
        verb = p.lower().partition("_")[0] if "_" in p and p.lower() not in ARRIVE | LEAVE else p.lower()
        if p.lower() in ARRIVE:
            ops.append(("add", (s, "estar_en", o)))
            continue
        if p.lower() in LEAVE:
            ops.append(("lose", (s, "estar_en", o)))
            continue
        if "_" in p:                                    # "dar_a luis": se combina con el objeto del mismo verbo
            base, _, prep = p.lower().partition("_")
            if prep == "a" and (s, base) in objs:
                x = objs[(s, base)][0]
                if base in GIVE and base != "devolver":
                    ops.append(("add", (o, "tener", x)))
                elif base == "devolver":
                    ops.append(("add", (o, "tener", x)))
                elif base == "comprar":                 # "compra un coche a Luis": Luis lo pierde
                    ops.append(("lose", (o, "tener", x)))
            continue
        if o in ("", "_"):
            continue
        if verb in GAIN:
            ops.append(("add", (s, "tener", o)))
        elif verb in LOSE or verb in GIVE:
            ops.append(("lose", (s, "tener", o)))
        elif verb in STATE:
            ops.append(("add", (o, "estar", _inflect(STATE[verb], od))))
    return ops
