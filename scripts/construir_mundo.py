"""parche-107: genera cartuchos de CONOCIMIENTO GENERAL a partir del diccionario de conceptos (WordNet + OMW, data/conceptos.json.gz).

    python -m scripts.construir_mundo            # escribe cartuchos/mundo_*.json (no los inserta)
    python -m scripts.construir_mundo --insertar # ademas los inserta

Por cada dominio (animales, plantas, cuerpo, comida, objetos, personas, lugares, materiales, naturaleza, tiempo) elige las palabras espanolas corrientes y escribe
hechos "X es un Y" (siguiendo la cadena de hiperonimos hasta lo abstracto) y "X es parte de Y". Solo para CONSTRUIR usa el listado de frecuencias `wordfreq`
(pip install wordfreq; datos CC BY-SA); los cartuchos resultantes no lo necesitan. Es determinista: misma entrada, mismos cartuchos."""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DOMINIOS = {
    "animales": ([5], 2.6, 900), "plantas": ([20], 2.6, 500), "cuerpo": ([8], 2.6, 400), "comida": ([13], 2.6, 600), "objetos": ([6], 3.0, 1500),
    "personas": ([18], 3.0, 1200), "lugares": ([15, 17], 3.0, 500), "materiales": ([27], 2.8, 500), "naturaleza": ([19], 2.8, 200), "tiempo": ([28], 3.0, 250),
}
DESCRIPCION = {"animales": "Animales y su clasificación", "plantas": "Plantas, flores y árboles", "cuerpo": "Partes del cuerpo", "comida": "Comidas y bebidas", "objetos": "Objetos, edificios y herramientas",
               "personas": "Personas, oficios y parentescos", "lugares": "Lugares y accidentes geográficos", "materiales": "Materiales y sustancias", "naturaleza": "Fenómenos de la naturaleza",
               "tiempo": "Tiempo, días, meses y estaciones"}
OK = re.compile(r"^[a-záéíóúüñ]{3,}$")
EXCLUIR = {"sus", "jorge", "argentina", "virus", "euro", "mierda", "bonito", "mezquita", "salado", "atlas", "son", "mayo", "dios", "internet", "especial", "general", "bien", "gen", "recto", "clara", "maría", "alguien", "gente", "cosa", "peludo", "grano", "variable", "paralelo", "diez", "máster", "radical", "olímpico", "sureño"}
SIN_PLURAL = {"lunes", "martes", "miércoles", "jueves", "viernes", "crisis", "tijeras", "gafas", "vacaciones", "análisis", "pantalones"}


def construir(salida="cartuchos", insertar=False, log=print):
    from wordfreq import top_n_list, zipf_frequency
    from src.language import conceptos as C
    from src.memory import cartuchos
    d = C._load()
    parada = set(top_n_list("es", 250))
    memo = {}

    def mejor(c):
        ws = [w for w in C.nombres(c) if OK.match(w)]
        sc = [(zipf_frequency(w, "es"), w) for w in ws if not (w.endswith("s") and (w[:-1] in ws or w[:-2] in ws))]
        return max(sc) if sc else (0.0, None)

    def lab(c):
        if c not in memo:
            e = C.etiqueta(c)
            if e in C.ETIQUETA_ES.values():
                memo[c] = e
            else:
                z, w = mejor(c)
                memo[c] = w or (e if e and OK.match(e) else None)
        return memo[c]

    def plural(w):
        if not w or not w.endswith("s") or w in SIN_PLURAL or len(w) < 4:
            return False
        sing = [w[:-1]] + ([w[:-2]] if w.endswith("es") else []) + ([w[:-3] + "z"] if w.endswith("ces") else [])
        return any(zipf_frequency(x, "es") >= 2.5 for x in sing)

    def abstracto(l):
        return (not l) or l.lower() in C.ALTO or l.lower() in C.TAXON or l in C.OMITIR or l in EXCLUIR or plural(l) or (l not in C.ETIQUETA_ES.values() and zipf_frequency(l, "es") < 1.2)

    def zipf(c):
        l = lab(c)
        return zipf_frequency(l, "es") if l else 0.0

    res = []
    usados = {}
    for nombre, (lx, umbral, tope) in DOMINIOS.items():
        cand = []
        for c in range(d["n"]):
            if d["pos"][c] != "n" or d["lex"][c] not in lx:
                continue
            l = lab(c)
            if not l or l in EXCLUIR or l in parada or plural(l) or usados.get(l, nombre) != nombre:
                continue
            z = zipf_frequency(l, "es")
            if z < umbral or C.conceptos(l)[:1] != [c] or C.es_genero(c):
                continue
            cand.append((-z, l, c))
        cand.sort()
        cand = cand[:tope]
        hechos, vistos, disp = [], set(), {}

        def hecho(s, p, o):
            k = (s.upper(), p, o.upper())
            if k not in vistos and s.upper() != o.upper():
                vistos.add(k)
                hechos.append({"s": k[0], "p": p, "o": k[2], "n": 1, "source": "mundo", "imp": 1.0, "tick": 0, "archived": False, "neg": False, "when": "", "when_disp": "", "when_abs": None, "q": ""})
                disp.setdefault(k[0], s)
                disp.setdefault(k[2], o)

        for _, l, c in cand:
            usados[l] = nombre
            x, cur, prof, ult = c, l, 0, set()
            while prof < 9:
                ts = [t for t in d["hyp"].get(x, []) if t not in ult]
                if not ts:
                    break
                x = ts[0]
                ult.add(x)
                lx_ = lab(x)
                if lx_ and not abstracto(lx_) and lx_ != cur and C.conceptos(lx_)[:1] != [x]:
                    continue                                                    # el nombre llevaria a otro sentido: se salta al antepasado siguiente
                if abstracto(lx_) or lx_ == cur:
                    if lx_ and lx_.lower() in C.ALTO:
                        break
                    continue
                hecho(cur, "ES", lx_)
                cur, prof = lx_, prof + 1
            for t in d["parte"].get(c, []):
                lt = lab(t)
                if lt and not abstracto(lt) and zipf_frequency(lt, "es") >= 3.0 and lt != l and C.conceptos(lt)[:1] == [t]:
                    hecho(lt, "PARTE_DE", l)
        nom = "mundo_" + nombre
        cont = {"hechos": hechos, "alias": {}, "verb_isa": {}, "defs": {}, "surface": {}, "display": disp, "opposites": []}
        cartuchos.guardar_cartucho(nom, cont, {"fuente": "diccionario de conceptos (WordNet 3.0 + OMW)", "descripcion": DESCRIPCION[nombre], "frases": len(cand), "creado": time.strftime("%Y-%m-%d %H:%M")}, salida)
        ents = {h["s"] for h in hechos} | {h["o"] for h in hechos}
        log(f"{nom}: {len(cand)} palabras, {len(hechos)} hechos, {len(ents)} conceptos")
        res.append((nom, len(hechos), len(ents)))
        if insertar:
            cartuchos.insertar(nom, salida)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="cartuchos")
    ap.add_argument("--insertar", action="store_true")
    a = ap.parse_args()
    construir(a.salida, a.insertar)
