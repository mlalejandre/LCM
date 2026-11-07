"""UN comando para comprobarlo todo (parche-45): tests unitarios + las 6 evaluaciones + diagnostico automatico + comparacion con la
ejecucion anterior. Escribe reports/informe.txt (es lo unico que hace falta pegar/subir) y reports/historial.json.

  python -m scripts.check

Los criterios son los fijados antes de medir en cada test (ver sus docstrings); aqui solo se aplican. Para cada frase fallida se
imprime el ARBOL que lee la escuela, asi no hace falta pedirlo aparte.
"""
import datetime
import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout

import torch

from scripts.eval_frases import evaluate
from scripts.eval_preguntas import add_rule, blocks, make_deduce, ok
from src.language.discourse import parse_text, split_sentences
from src.language.qa import QA
from src.language.school_parser import SchoolParser
from src.language.ud import load_school
from src.memory.store import MemoryStore
import tempfile

FRASES = [("conversacion_80", "data/frases_prueba.tsv", .75), ("largas_ciegas_27", "data/frases_largas_ciegas.tsv", .60)]
PREGUNTAS = [("cantidad_26", "data/cantidad_prueba.tsv", .70), ("cantidad_ciegas_14", "data/cantidad_ciegas.tsv", .60), ("estados_27", "data/estados_prueba.tsv", .70), ("estados_ciegas_18", "data/estados_ciegas.tsv", .60), ("fechas_18", "data/fechas_prueba.tsv", .75), ("herencia_10", "data/herencia_prueba.tsv", .75), ("tiempo_14", "data/tiempo_prueba.tsv", .75), ("conceptos_14", "data/conceptos_prueba.tsv", .75), ("deduccion_12", "data/preguntas_deduccion.tsv", .75), ("preguntas_19", "data/preguntas_prueba.tsv", .70), ("preguntas_ciegas_31", "data/preguntas_ciegas.tsv", .80), ("nuevo_ciego_comparativos_12", "data/comparativos_ciegos.tsv", .0), ("nuevo_ciego_general_13", "data/ciego_general.tsv", .0), ("nuevo_ciego_dificil_26", "data/ciego_dificil.tsv", .0), ("nuevo_ciego_cuatro_14", "data/ciego_cuatro.tsv", .0), ("nuevo_ciego_cinco_13", "data/ciego_cinco.tsv", .0)]      # parche-83: informativo      # parche-82: informativo      # parche-80: informativo      # parche-79: informativo      # parche-78: informativo
DISCURSO = [("discurso_21", "data/discurso_ciego.tsv", .70)]


def tree_lines(parser, sentence):
    try:
        return ["      " + " ".join(f"{i + 1}:{w[0]}/{w[1]}->{w[2]}:{w[3]}" for i, w in enumerate(parser.tree(sentence)))]
    except Exception as exc:                                  # noqa
        return [f"      (sin arbol: {exc})"]


def main():
    out, metrics, ok_all = [], {}, True
    log = lambda s="": out.append(s)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], capture_output=True, text=True)
    log("TESTS UNITARIOS: " + (r.stdout.strip().splitlines() or ["?"])[-1])
    ok_all &= r.returncode == 0
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model, scripts = load_school(device=device)
    parser = SchoolParser(model, device, scripts)

    for name, path, limit in FRASES:
        ex, rl, pr, rc, rows = evaluate(parser, path=path)
        metrics[name] = round(rl, 4)
        good = rl >= limit
        ok_all &= good
        log(f"\n{name}: {rl:.1%} relajado / {ex:.1%} exacto, precision {pr:.1%}, cobertura {rc:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if good else 'NO CUMPLE'})")
        for sent, g, p, okk in rows:
            if not okk:
                log(f"   FALLO {sent}\n      esperado {sorted(g)}\n      obtenido {sorted(p)}")
                for l in tree_lines(parser, sent):
                    log(l)

    for name, path, limit in PREGUNTAS:
        total = good_n = 0
        bad = []
        for b in blocks(path):
            with tempfile.TemporaryDirectory() as d:
                mem = MemoryStore(os.path.join(d, "m.json"))
                from datetime import date as _date
                mem.today = parser.today = _date.fromisoformat(b["HOY"]) if b.get("HOY") else None
                for sent in b["H"]:
                    for t in parser.parse(sent) or []:
                        tr = (t["s"], t["p"], t["o"])
                        mem.add_fact(tr, source=sent, neg=t["neg"], when=t.get("when", ""), when_disp=t.get("when_disp", ""), quant=t.get("q", ""))
                        mem.note_surface(tr, t.get("template"), t.get("s_disp"), t.get("o_disp"))
                for rule in b.get("R", []):
                    add_rule(mem, parser, rule)
                qa = QA(mem, parser.parse, make_deduce(mem))
                for q, exp in b["P"]:
                    ans = qa.answer(q)
                    total += 1
                    if ok(ans, exp):
                        good_n += 1
                    else:
                        bad.append((q, exp, ans))
        rate = good_n / max(total, 1)
        metrics[name] = round(rate, 4)
        good = rate >= limit
        ok_all &= good
        log(f"\n{name}: {good_n}/{total} = {rate:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if good else 'NO CUMPLE'})")
        for q, exp, ans in bad:
            log(f"   FALLO {q} esperado={exp} obtenido={ans}")

    from scripts.eval_frases import key, load_gold
    for name, path, limit in DISCURSO:
        gold = load_gold(path)
        n = good_n = 0
        for text, g in gold:
            n += 1
            pred = {(t["s"], key(t["p"]), t["o"], t["neg"]) for t in parse_text(parser, text)}
            gk = {(s, key(p), o, ng) for s, p, o, ng in g}
            if pred == gk:
                good_n += 1
            else:
                log(f"   FALLO {text}\n      esperado {sorted(gk)}\n      obtenido {sorted(pred)}")
                for s in split_sentences(text):
                    for l in tree_lines(parser, s):
                        log(l)
        rate = good_n / max(n, 1)
        metrics[name] = round(rate, 4)
        good = rate >= limit
        ok_all &= good
        log(f"\n{name}: {good_n}/{n} = {rate:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if good else 'NO CUMPLE'})")

    from scripts.eval_dialogo import run as run_dialogo
    g, t, bad = run_dialogo("data/dialogo_prueba.tsv")
    rate = g / max(t, 1)
    metrics["dialogo_%d" % t] = round(rate, 4)
    ok_all &= rate >= .75
    log(f"\ndialogo_{t}: {g}/{t} = {rate:.1%}  (criterio >= 75%: {'CUMPLE' if rate >= .75 else 'NO CUMPLE'})")
    for turn, exp, ans in bad:
        log(f"   FALLO {turn} esperado={exp} obtenido={ans}")

    g, t, bad = run_dialogo("data/dialogo_ciego.tsv")
    rate = g / max(t, 1)
    metrics["dialogo_ciego_%d" % t] = round(rate, 4)
    ok_all &= rate >= .60
    log(f"\ndialogo_ciego_{t}: {g}/{t} = {rate:.1%}  (criterio >= 60%: {'CUMPLE' if rate >= .60 else 'NO CUMPLE'})")
    for turn, exp, ans in bad:
        log(f"   FALLO {turn} esperado={exp} obtenido={ans}")

    for name, path, limit in (("coherencia", "data/coherencia_prueba.tsv", .70), ("coherencia_ciega", "data/coherencia_ciega.tsv", .60),
                             ("definiciones", "data/definiciones_prueba.tsv", .70), ("definiciones_ciegas", "data/definiciones_ciegas.tsv", .60),
                             ("nucleo", "data/nucleo_prueba.tsv", .70), ("nucleo_ciego", "data/nucleo_ciego.tsv", .60), ("nuevo_ciego_dialogo", "data/dialogo_ciego_seis.tsv", .0), ("nuevo_ciego_dialogo7", "data/dialogo_ciego_siete.tsv", .0)):      # parche-85: informativo      # parche-84: informativo
        g, t, bad = run_dialogo(path)
        rate = g / max(t, 1)
        metrics[f"{name}_{t}"] = round(rate, 4)
        ok_all &= rate >= limit
        log(f"\n{name}_{t}: {g}/{t} = {rate:.1%}  (criterio >= {limit:.0%}: {'CUMPLE' if rate >= limit else 'NO CUMPLE'})")
        for turn, exp, ans in bad:
            log(f"   FALLO {turn} esperado={exp} obtenido={ans}")

    hist_path = "reports/historial.json"
    hist = json.load(open(hist_path)) if os.path.exists(hist_path) else []
    if hist:
        prev = hist[-1]["metrics"]
        log("\nCAMBIOS respecto a la ejecucion anterior (" + hist[-1]["fecha"] + "):")
        for k, v in metrics.items():
            if k in prev and abs(v - prev[k]) > 1e-9:
                log(f"   {k}: {prev[k]:.1%} -> {v:.1%}  {'MEJORA' if v > prev[k] else 'EMPEORA'}")
        if all(abs(v - prev.get(k, v)) < 1e-9 for k, v in metrics.items()):
            log("   (sin cambios)")
    hist.append({"fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "metrics": metrics})
    os.makedirs("reports", exist_ok=True)
    json.dump(hist, open(hist_path, "w"), indent=1)
    log(f"\nRESUMEN: {'TODO CUMPLE' if ok_all else 'HAY CRITERIOS QUE NO SE CUMPLEN'}  " + json.dumps(metrics))
    text = "\n".join(out)
    open("reports/informe.txt", "w", encoding="utf-8").write(text)
    print(text)
    print("\n[Informe guardado en reports/informe.txt: pegame ese fichero entero]")


if __name__ == "__main__":
    main()
