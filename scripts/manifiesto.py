"""Manifiesto de reproducibilidad (parche-60).

  python -m scripts.manifiesto --guardar     # escribe reproducibilidad/manifiesto.json (huellas de TODO el codigo/datos/tests,
                                             # versiones del entorno, commits de los corpus UD y metricas de referencia)
  python -m scripts.manifiesto --verificar   # compara tu copia con el manifiesto: archivos distintos/faltantes/sobrantes
  python -m scripts.manifiesto --verificar --metricas   # ejecuta scripts.check: pasa si cada examen cumple su criterio; compara con la referencia solo como informacion (--estricto: tolerancia 0,03)

Que se vigila: src, scripts, tests, configs, data/*.tsv|txt|json (menos libro*), docs, README, Makefile, requirements, LICENSE y
reports/RESULTADOS.md. NO se vigilan los pesos (checkpoints/*.pt) porque dependen del hardware y de la semilla: de ellos se guarda
la huella solo como informacion. Sirve para saber, con certeza, que dos copias del proyecto tienen el mismo codigo.
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

OUT = "reproducibilidad/manifiesto.json"
TRACK_DIRS = ("src", "scripts", "tests", "configs", "docs", "data", ".github", "reproducibilidad")
TRACK_FILES = ("limpieza.py", "README.md", "LCM_EVOLUCION.md", "Makefile", "requirements.txt", "LICENSE", ".gitignore", "reports/RESULTADOS.md")
TEXT_EXT = (".py", ".tsv", ".txt", ".md", ".json", ".yml", ".yaml", ".cfg", "")
SKIP_PARTS = ("__pycache__", ".pytest_cache", "data/ud/", "data/libro", ".parche_backups", "reproducibilidad/manifiesto.json")


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked(root: str = ".") -> list:
    out = []
    for d in TRACK_DIRS:
        for base, dirs, files in os.walk(os.path.join(root, d)):
            dirs[:] = [x for x in dirs if x not in ("__pycache__", ".pytest_cache")]
            for fn in files:
                rel = os.path.relpath(os.path.join(base, fn), root).replace(os.sep, "/")
                if any(p in rel + ("/" if os.path.isdir(os.path.join(root, rel)) else "") for p in SKIP_PARTS):
                    continue
                if os.path.splitext(fn)[1] not in TEXT_EXT or fn.endswith((".pkl", ".pt", ".pyc")):
                    continue
                out.append(rel)
    out += [f for f in TRACK_FILES if os.path.exists(os.path.join(root, f))]
    return sorted(set(out))


def git_head(path: str):
    try:
        r = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def environment() -> dict:
    env = {"python": sys.version.split()[0], "plataforma": platform.platform(), "semilla_por_defecto": os.environ.get("LCM_SEED", "0")}
    for mod in ("torch", "numpy", "tqdm", "pytest"):
        try:
            env[mod] = __import__(mod).__version__
        except Exception:
            env[mod] = None
    try:
        import torch
        env["dispositivo"] = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    except Exception:
        pass
    return env


def build() -> dict:
    ud = {}
    for name in ("UD_Spanish-GSD", "UD_Spanish-AnCora"):
        head = git_head(os.path.join("data", "ud", name))
        if head:
            ud[name] = head
    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    ud = ud or old.get("ud", {})
    metrics = {}
    if os.path.exists("reports/historial.json"):
        hist = json.load(open("reports/historial.json"))
        if hist:
            metrics = hist[-1]["metrics"]
    ckpt = {}
    for fn in sorted(os.listdir("checkpoints")) if os.path.isdir("checkpoints") else []:
        ckpt[fn] = sha(os.path.join("checkpoints", fn))
    return {"creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "entorno": environment(), "ud": ud, "metricas_referencia": metrics,
            "checkpoints_informativo": ckpt, "archivos": {f: sha(f) for f in tracked()}}


def save():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    m = build()
    json.dump(m, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"[OK] {OUT}: {len(m['archivos'])} archivos, UD: {m['ud'] or 'sin clonar (ejecuta scripts.get_data y repite)'}")
    if m["metricas_referencia"]:
        print(f"     metricas de referencia: {len(m['metricas_referencia'])} (de reports/historial.json)")


def verify(with_metrics: bool, tol: float = 0.03, strict: bool = False) -> int:
    if not os.path.exists(OUT):
        sys.exit(f"[!] Falta {OUT}. Ejecuta primero:  python -m scripts.manifiesto --guardar")
    ref = json.load(open(OUT, encoding="utf-8"))
    now = {f: sha(f) for f in tracked()}
    want = ref["archivos"]
    diff = sorted(f for f in want if f in now and now[f] != want[f])
    missing = sorted(f for f in want if f not in now)
    extra = sorted(f for f in now if f not in want)
    print(f"Archivos vigilados: {len(want)} | distintos: {len(diff)} | faltan: {len(missing)} | sobran: {len(extra)}")
    for tag, lst in (("DISTINTO", diff), ("FALTA", missing), ("SOBRA", extra)):
        for f in lst[:40]:
            print(f"   {tag}: {f}")
    env_now, env_ref = environment(), ref.get("entorno", {})
    for k in ("python", "torch", "numpy"):
        if env_now.get(k) != env_ref.get(k):
            print(f"   (aviso) {k}: manifiesto {env_ref.get(k)} / aqui {env_now.get(k)}  -> las cifras pueden moverse unos puntos")
    ud_now = {n: git_head(os.path.join("data", "ud", n)) for n in ref.get("ud", {})}
    for n, h in ref.get("ud", {}).items():
        if ud_now.get(n) and ud_now[n] != h:
            print(f"   (aviso) {n}: otro commit ({ud_now[n][:10]} en vez de {h[:10]}): la escuela no saldra identica")
    ok = not (diff or missing)
    if with_metrics:
        r = subprocess.run([sys.executable, "-m", "scripts.check"], capture_output=True, text=True)
        if not os.path.exists("reports/historial.json"):
            print("[!] No se pueden comparar metricas: scripts.check no llego a terminar (faltan pesos entrenados?). Ultimas lineas:")
            print("    " + "\n    ".join((r.stderr or r.stdout).strip().splitlines()[-6:]))
            print("    Entrena primero (python -m scripts.reproduce) y repite.")
            return 1
        hist = json.load(open("reports/historial.json"))
        cur, base = hist[-1]["metrics"], ref.get("metricas_referencia", {})
        bad = [(k, base[k], cur.get(k)) for k in base if cur.get(k) is None or cur[k] < base[k] - tol]
        informe = open("reports/informe.txt", encoding="utf-8").read() if os.path.exists("reports/informe.txt") else ""
        resumen = [l for l in informe.splitlines() if l.startswith("RESUMEN:")]
        cumple = bool(resumen) and "TODO CUMPLE" in resumen[-1]
        # Lo que decide es si CADA examen cumple su criterio (fijado antes de medir). La referencia es una sola ejecucion anterior:
        # un reentrenamiento nunca sale al decimal y, en examenes pequenos, una sola pregunta mueve 5-10 puntos. Por eso
        # las diferencias con la referencia se muestran como informacion y solo fallan con --estricto.
        print(f"Criterios de cada examen: {'TODOS CUMPLEN' if cumple else 'HAY EXAMENES QUE NO CUMPLEN (ver reports/informe.txt)'}")
        print(f"Frente a la referencia (una ejecucion anterior): {len(base) - len(bad)}/{len(base)} dentro de {tol:.0%}")
        for k, b, c in bad:
            print(f"   (informativo) {k}: referencia {b:.1%} -> ahora {('%.1f%%' % (c * 100)) if c is not None else 'sin dato'}")
        ok = ok and cumple and (not bad or not strict)
    print("[OK] Reproduccion fiel." if ok else "[!] Hay diferencias (ver arriba).")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--metricas", action="store_true")
    ap.add_argument("--estricto", action="store_true", help="con --metricas: falla tambien si algo baja mas de 3 puntos de la referencia")
    a = ap.parse_args()
    if a.guardar:
        save()
    elif a.verificar:
        sys.exit(verify(a.metricas, strict=a.estricto))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
