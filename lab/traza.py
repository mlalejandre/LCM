"""Depuración: muestra por qué funciones del núcleo pasa un turno y dónde devuelve None.  python -m lab.traza "frase 1" "frase 2" ... (se traza la última)"""
import sys
from lab.banco import motor
m = motor()
for t in sys.argv[1:-1]:
    m.chat(t)
pila = []
def tr(frame, ev, arg):
    fn = frame.f_code.co_filename
    if "nucleo20" not in fn or ev != "call":
        return None
    nombre = frame.f_code.co_name
    if nombre.startswith(("<", "sa", "can", "_acento", "analizar", "formas", "conjugar", "singular", "plural", "numero", "_lem", "masc", "genero", "disp", "gen", "kb")):
        return None
    def loc(frame, ev, arg):
        if ev == "return" and frame.f_code.co_name in ("procesar", "_una", "preguntar", "_interroga", "_si_no", "afirmar", "_interpreta", "responder", "_generica", "_que_hace", "_prop", "_quien", "_tener_q", "_es_un", "_atributo_q", "_graba"):
            print(f"   <- {frame.f_code.co_name}:{frame.f_lineno} {str(arg)[:110]}")
        return loc
    return loc
sys.settrace(tr)
r = m.chat(sys.argv[-1])
sys.settrace(None)
print("RESPUESTA:", str(r)[:200])
