"""Descarga los corpus de español analizados a mano (Universal Dependencies) a data/ud/. Solo hace falta una vez.
    python -m src.sintaxis.prepara
Después:  python -m src.sintaxis.entrena      (unos 30 minutos en un portátil; deja src/sintaxis/analizador.pt)"""
import os, sys, urllib.request

BASE = "https://raw.githubusercontent.com/UniversalDependencies/{repo}/master/{fichero}"
FICHEROS = [("UD_Spanish-AnCora", "es_ancora-ud-train.conllu"), ("UD_Spanish-AnCora", "es_ancora-ud-dev.conllu"), ("UD_Spanish-AnCora", "es_ancora-ud-test.conllu"),
            ("UD_Spanish-GSD", "es_gsd-ud-train.conllu"), ("UD_Spanish-GSD", "es_gsd-ud-dev.conllu"), ("UD_Spanish-GSD", "es_gsd-ud-test.conllu"),
            ("UD_Spanish-PUD", "es_pud-ud-test.conllu"), ("UD_Spanish-COSER", "es_coser-ud-test.conllu")]


def main():
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "ud")
    os.makedirs(dest, exist_ok=True)
    for repo, f in FICHEROS:
        p = os.path.join(dest, f)
        if os.path.exists(p) and os.path.getsize(p) > 10000:
            print("ya está   ", f)
            continue
        url = BASE.format(repo=repo, fichero=f)
        print("bajando   ", f, "…", end=" ", flush=True)
        try:
            urllib.request.urlretrieve(url, p)
            print(f"{os.path.getsize(p) // 1024} KB")
        except Exception as e:                           # noqa
            print("NO SE PUDO:", e)
            print("   Descárgalo a mano de", url, "y déjalo en data/ud/")
    print("Listo. Ahora: python -m src.sintaxis.entrena")


if __name__ == "__main__":
    main()
