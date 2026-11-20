# LCM_VISION_01_GENERATED
"""Entrena un clasificador RGB sintetico (NO un modelo general de vision)."""
import argparse


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--epocas", type=int, default=70)
    p.add_argument("--semilla", type=int, default=42)
    p.add_argument("--salida", default="checkpoints/vision_colors.pt")
    a = p.parse_args(argv)
    if a.epocas < 1 or a.epocas > 500:
        p.error("--epocas debe estar entre 1 y 500")
    from src.vision.color_encoder import entrenar
    val = entrenar(a.salida, epocas=a.epocas, semilla=a.semilla)
    print(f"Validacion sintetica: {val:.1%}. Modelo guardado en {a.salida}.")
    print("Este resultado NO demuestra comprension de imagenes naturales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
