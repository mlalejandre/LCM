"""Descarga los corpus UD en espanol (Universal Dependencies) a data/ud/. Necesita git y conexion a internet.
Licencias: GSD CC BY-SA 4.0, AnCora CC BY 4.0. NO se redistribuyen con el proyecto: cada persona los descarga.
Uso:  python -m scripts.get_data
"""
import json
import os
import subprocess
import sys

PIN = "reproducibilidad/manifiesto.json"          # si existe, fija el commit exacto de cada corpus (python -m scripts.manifiesto --guardar)

REPOS = {
    "UD_Spanish-GSD": "https://github.com/UniversalDependencies/UD_Spanish-GSD.git",
    "UD_Spanish-AnCora": "https://github.com/UniversalDependencies/UD_Spanish-AnCora.git",
}


def main():
    os.makedirs("data/ud", exist_ok=True)
    for name, url in REPOS.items():
        dest = os.path.join("data", "ud", name)
        if os.path.isdir(dest):
            print(f"[=] Ya existe {dest}")
            continue
        print(f"[+] Descargando {name} ...")
        commit = (json.load(open(PIN, encoding="utf-8")).get("ud", {}).get(name) if os.path.exists(PIN) else None)
        if commit:                                  # version EXACTA con la que se entreno (reproducible)
            steps = [["git", "init", dest], ["git", "-C", dest, "remote", "add", "origin", url],
                     ["git", "-C", dest, "fetch", "--depth", "1", "origin", commit], ["git", "-C", dest, "checkout", "FETCH_HEAD"]]
            r = None
            for cmd in steps:
                r = subprocess.run(cmd)
                if r.returncode != 0:
                    break
            print(f"    fijado al commit {commit[:10]} (reproducibilidad/manifiesto.json)")
        else:
            print("    (sin commit fijado: se baja la ultima version; ejecuta despues  python -m scripts.manifiesto --guardar  para fijarla)")
            r = subprocess.run(["git", "clone", "--depth", "1", url, dest])
        if r.returncode != 0:
            sys.exit(f"[!] Fallo al descargar {name}. Comprueba git/internet o clona a mano en {dest}.")
    print("[OK] Corpus listos en data/ud/")


if __name__ == "__main__":
    main()
