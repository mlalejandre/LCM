"""Compara analizadores en cinco exámenes: prensa y web (los dos del corpus), escritura descuidada, y dos que NO se parecen al entrenamiento:
PUD (noticias y enciclopedia traducidas) y COSER (español hablado, con muchas preguntas). python -m lab.sintaxis.compara ruta1.pt [ruta2.pt]"""
import json, os, random, sys
import torch
from src.sintaxis.datos import lee_conllu
from src.sintaxis.entrena import predice, UD, descuidada
from src.sintaxis.medir import mide
from src.sintaxis.modelo import Analizador, Vocab


def carga(ruta):
    ck = torch.load(ruta, map_location="cpu")
    V = Vocab(ck["vocab"]["w"], ck["vocab"]["upos"], ck["vocab"]["rels"])
    m = Analizador(len(V.w), len(V.upos), len(V.rels)); m.load_state_dict(ck["modelo"]); m.eval()
    return m, V


if __name__ == "__main__":
    A = lee_conllu(os.path.join(UD, "es_ancora-ud-test.conllu")); G = lee_conllu(os.path.join(UD, "es_gsd-ud-test.conllu"))
    random.seed(3)
    conj = {"prensa y web (corpus)": A + G, "escrito con descuido": [descuidada(f) for f in A + G if len(f) <= 20],
            "PUD (otro origen)": lee_conllu(os.path.join(UD, "es_pud-ud-test.conllu")), "COSER (hablado)": lee_conllu(os.path.join(UD, "es_coser-ud-test.conllu"))}
    conj["COSER solo preguntas"] = [f for f in conj["COSER (hablado)"] if f[-1][0] == "?"]
    res = {}
    for ruta in sys.argv[1:]:
        m, V = carga(ruta)
        print("\n" + ruta)
        for nom, fs in conj.items():
            r = mide(fs, predice(m, V, fs))["todo"]
            res.setdefault(ruta, {})[nom] = r
            print(f"  {nom:24s} frases={r['frases']:5d} categoria={r['categoria']:5.1f} cabeza={r['cabeza']:5.1f} cab+func={r['cabeza_y_funcion']:5.1f} verbo_princ={r['verbo_principal']:5.1f} sujeto={r['sujeto_F1']:5.1f} objeto={r['objeto_F1']:5.1f}")
    json.dump(res, open("reports/sintaxis_comparacion.json", "w"), ensure_ascii=False, indent=1)
