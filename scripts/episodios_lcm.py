"""Herramienta de investigación del registro episódico LCM 1.3.

Ejemplos:
  python -m scripts.episodios_lcm inventario
  python -m scripts.episodios_lcm anotar --sujeto AVE_1 --accion accion.piar --contexto PATIO --creencia ANA
  python -m scripts.episodios_lcm consultar --sujeto AVE_1 --accion accion.piar --contexto PATIO --estatus creencia
  python -m scripts.episodios_lcm analizar-audio grabacion.wav

No implementa reconocimiento acústico de sonidos animales.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from src.multimodal.episodic_memory import Afirmacion, MemoriaEpisodica


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--memoria',default='memory/lcm_episodios.json')
    sub=ap.add_subparsers(dest='accion_cli',required=True)
    sub.add_parser('inventario')
    p=sub.add_parser('anotar')
    p.add_argument('--sujeto',required=True)
    p.add_argument('--accion',required=True)
    p.add_argument('--contexto',required=True)
    p.add_argument('--creencia',help='atribuir la creencia a esta persona')
    p.add_argument('--negado',action='store_true')
    p.add_argument('--instante',help='ISO 8601 con zona horaria')
    p=sub.add_parser('consultar')
    p.add_argument('--sujeto',required=True)
    p.add_argument('--accion',required=True)
    p.add_argument('--contexto',required=True)
    p.add_argument('--estatus',choices=['actual','posible','hipotetico','creencia'],default='actual')
    p.add_argument('--hablante')
    p.add_argument('--instante')
    p=sub.add_parser('analizar-audio')
    p.add_argument('archivo')
    p.add_argument('--etiqueta',help='Etiqueta tras confirmación humana, no predicción')
    p.add_argument('--confirmado',action='store_true')
    p.add_argument('--contexto',default='AUDIO_CARGADO')
    args=ap.parse_args(argv)
    memoria=MemoriaEpisodica(args.memoria)
    if args.accion_cli=='inventario':result=memoria.inventario()
    elif args.accion_cli=='anotar':
        result=memoria.afirmar(Afirmacion(args.sujeto,'REALIZAR',args.accion,args.contexto,
            'creencia' if args.creencia else 'actual',not args.negado,'texto',
            'usuario_afirma', args.creencia or 'USUARIO',args.instante))
    elif args.accion_cli=='consultar':
        result=memoria.consultar(args.sujeto,'REALIZAR',args.accion,
            args.contexto,args.instante,args.estatus,args.hablante)
    else:
        from src.multimodal.audio_features import observacion_audio
        if args.etiqueta and not args.confirmado:
            ap.error('una etiqueta sonora exige --confirmado; no es predicción del LCM')
        path=Path(args.archivo)
        if not path.is_file() or path.stat().st_size>12_000_000:
            ap.error('WAV inexistente o demasiado grande')
        o=observacion_audio(path.read_bytes(),args.etiqueta,args.confirmado)
        result=memoria.observar(o,args.contexto)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
