"""Reproduce los examenes SIN la escuela, con los arboles grabados por scripts.grabar_arboles (parche-75).

    python -m scripts.replay [--arboles reports/arboles.json] [--tests]

Sustituye solo la prediccion cruda de la escuela por la grabada; el resto (arreglos de la escuela, lemas irregulares, extractor, preguntas,
memoria, dialogo, coherencia, efectos) se ejecuta de verdad. Sirve para probar un cambio simbolico contra TODOS los examenes en segundos,
sin reentrenar. No sirve para medir la escuela: si cambia la escuela hay que volver a grabar.
No toca reports/informe.txt ni reports/historial.json (los restaura); escribe reports/replay_informe.txt.
Si falta alguna frase en la grabacion, la lista al final (hay que volver a grabar con --extra).
"""
import argparse
import json
import os
import sys
import types


def _stubs():
    """Si no hay torch (p. ej. en un servidor), se simulan los modulos pesados que los examenes importan pero no usan."""
    try:
        import torch  # noqa
        return False
    except ImportError:
        pass

    def stub(name, **attrs):
        m = types.ModuleType(name)
        m.__dict__.update(attrs)
        sys.modules[name] = m

    class _X:
        pass

    stub("torch", cuda=types.SimpleNamespace(is_available=lambda: False),
         backends=types.SimpleNamespace(mps=types.SimpleNamespace(is_available=lambda: False)))
    stub("src.language.ear", Ear=_X, EarParser=_X)
    stub("src.reasoning.engine", ReasoningEngine=_X)
    stub("src.language.ud", School=_X, predict_trees=lambda *a, **k: None, load_school=lambda device="cpu": (None, []))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arboles", default="reports/arboles.json")
    ap.add_argument("--tests", action="store_true", help="correr tambien pytest (necesita torch)")
    args = ap.parse_args()
    sys.argv = [sys.argv[0]]
    sys.path.insert(0, os.getcwd())
    _stubs()
    import importlib
    ud = sys.modules.get("src.language.ud") or importlib.import_module("src.language.ud")
    ud.load_school = lambda device="cpu": (None, [])
    rec = json.load(open(args.arboles, encoding="utf-8"))["arboles"]
    missing = []

    import src.language.school_parser as sp

    def lookup(model, batch, device, scripts):
        out = []
        for forms in batch:
            k = "\x1f".join(forms)
            if k in rec:
                out.append([tuple(x) for x in rec[k]])
            else:
                if k not in missing:
                    missing.append(k)
                out.append([("X", 0 if i == 0 else 1, "root" if i == 0 else "dep", f.lower()) for i, f in enumerate(forms)])
        return out

    def init(self, model=None, device="cpu", scripts=(), overrides=None):
        self.model, self.device, self.scripts = None, device, []
        self.overrides = {**sp.IRREG, **(overrides or {})}

    sp.predict_trees = lookup
    sp.SchoolParser.__init__ = init

    saved = {f: (open(f, "rb").read() if os.path.exists(f) else None) for f in ("reports/informe.txt", "reports/historial.json")}
    from scripts import check
    if not args.tests:
        check.subprocess = types.SimpleNamespace(run=lambda *a, **k: types.SimpleNamespace(stdout="TESTS UNITARIOS: omitidos en replay (usa --tests)\n", returncode=0))
    try:
        check.main()
        os.makedirs("reports", exist_ok=True)
        open("reports/replay_informe.txt", "wb").write(open("reports/informe.txt", "rb").read())
    finally:
        for f, data in saved.items():
            if data is None:
                if os.path.exists(f):
                    os.remove(f)
            else:
                open(f, "wb").write(data)
    print(f"\n[replay] informe en reports/replay_informe.txt | frases sin arbol grabado: {len(missing)}")
    for k in missing[:30]:
        print("   FALTA:", k.replace("\x1f", " "))


if __name__ == "__main__":
    main()
