"""parche-130: ¿CUANTO CUESTA CONTESTAR? Mide en TU equipo lo que gasta el LCM: arranque, memoria RAM, tiempo y CPU por respuesta, y lo que cuesta leer un texto.

  python -m scripts.recursos                        lee data/textos/leon.txt (o el primero que haya) y hace unas 15 preguntas
  python -m scripts.recursos --texto mi.txt --preguntas mias.txt --vatios 25 --json salida.json

Usa una memoria TEMPORAL (copia de tus cartuchos): no toca tu memoria. Solo CPU/GPU que ya tengas; no descarga nada.

La energia es una ESTIMACION: segundos de CPU x vatios que supones que gasta tu procesador al trabajar (por defecto 15 W; un vatimetro o la herramienta del
fabricante te dara el dato real). Referencias publicadas para una consulta mediana a un LLM de centro de datos: ~0,24 Wh (Google, mediana de Gemini, 2025),
~0,3 Wh (Epoch AI para GPT-4o, 2025), ~0,34 Wh (OpenAI, 2025). No son comparables 1 a 1: un LLM hace una tarea mucho mas general; el LCM, una mucho mas estrecha."""
import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
import time

PREGUNTAS = ["hola", "¿Qué es un perro?", "¿Para qué sirve un martillo?", "¿Qué día fue hace 4 días?", "¿Cuánto es 15 por 3?",
             "El perro de Ana se llama Rex.", "¿Cómo se llama el perro de Ana?", "Lucía nació el 12 de octubre de 1982.", "¿Qué edad tiene Lucía?",
             "¿Puedes contarme un cuento?", "¿Cuál es la capital de Mongolia?"]
LLM_WH = {"Google (mediana Gemini, 2025)": 0.24, "Epoch AI (GPT-4o, 2025)": 0.30, "OpenAI (media ChatGPT, 2025)": 0.34}


def energia_wh(cpu_s, vatios=15.0):
    """Estimacion: segundos de CPU x vatios / 3600."""
    return float(cpu_s) * float(vatios) / 3600.0


def rss_mb():
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1e6
    except Exception:                                                          # noqa
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return r / (1e6 if sys.platform == "darwin" else 1e3)


def miles(n):
    return f"{int(round(n)):,}".replace(",", ".")


def mediana(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def medir(f):
    w, c = time.time(), time.process_time()
    r = f()
    return r, (time.time() - w) * 1000, (time.process_time() - c) * 1000


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--texto", help="texto a leer (por defecto data/textos/leon.txt o el primero que haya)")
    ap.add_argument("--preguntas", help="fichero con una pregunta por linea (por defecto unas 15 variadas)")
    ap.add_argument("--vatios", type=float, default=15.0, help="vatios que gasta tu CPU trabajando (estimacion; por defecto 15)")
    ap.add_argument("--hilos", type=int, default=0, help="hilos de torch (0 = los que use por defecto)")
    ap.add_argument("--json", help="guarda el informe en este fichero")
    a = ap.parse_args(argv)
    t_ini = time.time()
    import torch
    if a.hilos:
        torch.set_num_threads(a.hilos)
    rss_torch = rss_mb()
    from src.language.school_learn import load_overrides
    from src.language.school_parser import SchoolParser
    from src.language.ud import load_school
    from src.web.motor import Motor
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists("checkpoints/school.pt"):
        print("[!] No hay escuela de español (checkpoints/school.pt). Ejecuta: python -m scripts.train_school")
        return 1
    tmp = tempfile.mkdtemp()
    cart = os.path.join(tmp, "cartuchos")
    if os.path.isdir("cartuchos"):
        shutil.copytree("cartuchos", cart)
    t0, c0 = time.time(), time.process_time()
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts, load_overrides())
    motor = Motor.crear(ruta_memoria=os.path.join(tmp, "memoria.json"), carpeta_cartuchos=cart, parser=parser, log=lambda *x: None)
    arranque_s, arranque_cpu = time.time() - t0, time.process_time() - c0
    rep = {"dispositivo": device, "parametros_escuela": int(sum(p.numel() for p in model.parameters())),
           "checkpoint_MB": round(os.path.getsize("checkpoints/school.pt") / 1e6, 1), "vatios_supuestos": a.vatios,
           "arranque_s": round(arranque_s, 2), "arranque_cpu_s": round(arranque_cpu, 2), "hechos_de_fabrica": len(motor.mem.facts),
           "ram_tras_importar_torch_MB": round(rss_torch), "ram_tras_arrancar_MB": round(rss_mb())}
    texto = a.texto or next(iter([p for p in ["data/textos/leon.txt"] if os.path.exists(p)] + sorted(glob.glob("data/textos/*.txt"))), None)
    if texto and os.path.exists(texto):
        txt = open(texto, encoding="utf-8").read()
        _, w, c = medir(lambda: motor.aprender(txt))
        rep["lectura"] = {"texto": texto, "caracteres": len(txt), "palabras": len(txt.split()), "segundos": round(w / 1000, 2), "cpu_s": round(c / 1000, 2),
                          "wh_estimados": round(energia_wh(c / 1000, a.vatios), 5), "hechos_totales": len(motor.mem.facts), "ram_MB": round(rss_mb())}
    qs = [l.strip() for l in open(a.preguntas, encoding="utf-8")] if a.preguntas else PREGUNTAS
    qs = [q for q in qs if q]
    filas = []
    for q in qs:
        r, w, c = medir(lambda: motor.chat(q))
        filas.append({"pregunta": q, "ms": round(w), "cpu_ms": round(c), "respuesta": (r.get("respuesta") or r.get("error") or "")[:90].replace("\n", " ")})
    rep["preguntas"] = filas
    ms, cpu = [f["ms"] for f in filas], [f["cpu_ms"] for f in filas]
    rep["resumen"] = {"ms_mediana": mediana(ms), "ms_maximo": max(ms) if ms else 0, "cpu_ms_mediana": mediana(cpu), "cpu_ms_media": round(sum(cpu) / max(1, len(cpu))),
                      "wh_por_respuesta_mediana": round(energia_wh(mediana(cpu) / 1000, a.vatios), 6), "ram_final_MB": round(rss_mb())}
    rep["tiempo_total_s"] = round(time.time() - t_ini, 1)
    # ---- informe --------------------------------------------------------------------------------------------------------------
    print(f"\nLCM — recursos en este equipo ({device.upper()}; sin LLM)")
    print(f"  escuela (analizador): {miles(rep['parametros_escuela'])} parámetros, {rep['checkpoint_MB']} MB en disco")
    print(f"  arranque: {rep['arranque_s']} s ({rep['arranque_cpu_s']} s de CPU), {rep['hechos_de_fabrica']} hechos de fábrica")
    print(f"  RAM: {rep['ram_tras_importar_torch_MB']} MB solo por importar PyTorch, {rep['ram_tras_arrancar_MB']} MB con el LCM listo")
    if "lectura" in rep:
        L = rep["lectura"]
        print(f"  leer {os.path.basename(L['texto'])} ({L['palabras']} palabras): {L['segundos']} s, {L['cpu_s']} s de CPU, ≈ {L['wh_estimados'] * 1000:.1f} mWh; RAM {L['ram_MB']} MB")
    print("\n  pregunta".ljust(48) + "ms".rjust(7) + "CPU ms".rjust(8))
    for f in filas:
        print("  " + f["pregunta"][:44].ljust(46) + str(f["ms"]).rjust(7) + str(f["cpu_ms"]).rjust(8))
    R = rep["resumen"]
    mwh = R["wh_por_respuesta_mediana"] * 1000
    print(f"\n  mediana: {R['ms_mediana']} ms y {R['cpu_ms_mediana']} ms de CPU por respuesta (máximo {R['ms_maximo']} ms); RAM al final {R['ram_final_MB']} MB")
    print(f"  energía estimada por respuesta: ≈ {mwh:.3f} mWh (CPU x {a.vatios:g} W)")
    for n, wh in LLM_WH.items():
        print(f"    frente a {wh} Wh de una consulta mediana a un LLM — {n}: ≈ {miles(wh / max(R['wh_por_respuesta_mediana'], 1e-9))} veces menos")
    print("  (estimación: no es una comparación 1 a 1; mide la energía real con un vatímetro si vas a citarla)")
    if a.json:
        json.dump(rep, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
