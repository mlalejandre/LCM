"""Analizador acústico preparatorio; NO identifica especies, pájaros o palabras.

python -m scripts.analizar_audio_lcm sonido.wav
python -m scripts.analizar_audio_lcm sonido.wav --etiqueta pajaro_piando
La segunda forma crea una observación anotada SOLO en la salida, no cambia la memoria.
"""
import argparse
import json
from pathlib import Path
from src.multimodal.audio_features import observacion_audio

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('wav', type=Path)
    ap.add_argument('--etiqueta', help='Anotación explícita aportada por el usuario')
    args=ap.parse_args()
    obs=observacion_audio(args.wav.read_bytes(),args.etiqueta,bool(args.etiqueta))
    print(json.dumps(obs.serializar(),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
