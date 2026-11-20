# LCM_VISION_01_GENERATED
"""Ejecutar desde la raiz: python -m scripts.vision ruta/imagen.png [--guardar]."""
import argparse
import json
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description="LCM Vision 0.1: identificar color dominante")
    p.add_argument("imagen", type=Path)
    p.add_argument("--guardar", action="store_true", help="guarda la observacion en memory/lcm_memory.json")
    p.add_argument("--memoria", default="memory/lcm_memory.json")
    a = p.parse_args(argv)
    from src.vision.color_features import analizar_imagen
    try:
        datos = a.imagen.read_bytes()
        if a.guardar:
            from src.memory.store import MemoryStore
            from src.vision.perception import procesar_imagen
            res = procesar_imagen(MemoryStore(a.memoria), datos, a.imagen.name)
        else:
            res = analizar_imagen(datos)
    except (OSError, ValueError, RuntimeError) as exc:
        p.exit(2, f"ERROR: {exc}\n")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 2 if res.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
