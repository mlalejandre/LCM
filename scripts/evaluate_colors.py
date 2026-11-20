# LCM_VISION_01_GENERATED
"""Examen independiente de colores: reglas, mezclas y MLP opcional."""
import argparse
import io
from pathlib import Path


def main(argv=None):
    from PIL import Image
    from src.vision.color_features import analizar_imagen
    from src.vision.color_encoder import evaluar_modelo
    p = argparse.ArgumentParser()
    p.add_argument("--modelo", default="checkpoints/vision_colors.pt")
    a = p.parse_args(argv)
    pruebas = {"ROJO": (230, 30, 30), "VERDE": (20, 165, 65), "AZUL": (25, 60, 230),
               "AMARILLO": (248, 205, 20), "BLANCO": (255, 255, 255), "NEGRO": (0, 0, 0),
               None: (128, 128, 128)}
    bien = total = 0
    for color, rgb in pruebas.items():
        im = Image.new("RGB", (64, 64), rgb)
        buf = io.BytesIO(); im.save(buf, "PNG")
        got = analizar_imagen(buf.getvalue())["concepto"]
        bien += int(got == color); total += 1
        print(f"{str(color):8} -> {str(got):8}")
    mezcla = Image.new("RGB", (100, 100), "red")
    for x in range(50, 100):
        for y in range(100):
            mezcla.putpixel((x, y), (0, 160, 40))
    buf = io.BytesIO(); mezcla.save(buf, "PNG")
    got = analizar_imagen(buf.getvalue())["concepto"]
    bien += int(got is None); total += 1
    print(f"mezcla   -> {got}")
    print(f"Reglas HSV: {bien}/{total} (criterio minimo 8/8)")
    mod = Path(a.modelo)
    if mod.exists():
        from src.vision.color_encoder import cargar
        exactitud = evaluar_modelo(cargar(mod), semilla=981237, n=100)
        print(f"MLP RGB: exactitud sintetica en test independiente {exactitud:.1%}")
        if exactitud < 0.90:
            return 1
    else:
        print("MLP: sin checkpoint; ejecuta python -m scripts.train_colors para evaluarlo.")
    return 0 if bien == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
