"""Evaluación externa de alcance con el oráculo anotado en LCM 1.3.

NO convierte el número de estructuras guardadas en exactitud: mide cobertura
aproximada y hechos indebidos para eventos NO asertivos sin Escuela entrenada.
"""
import argparse
import json
import tempfile
from pathlib import Path
from src.memory.store import MemoryStore
from src.semantics.dialogue16 import DialogoConceptual
from src.semantics.discourse17 import Discurso17


def evaluar(oraculo):
    filas=[];indebidos=0;estructuras=0
    for linea in Path(oraculo).read_text(encoding='utf8').splitlines():
        if not linea.strip():continue
        r=json.loads(linea)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);m=MemoryStore(str(p/'m.json'))
            d=DialogoConceptual(m,ruta=p/'r.json')
            e=Discurso17(d,ruta=p/'e.json')
            t=r['texto'];a=e.procesar(t)
            if a is None:a=d.procesar(t)
            n=len(m.facts);almacenadas=n+len(e.eventos)+len(d.atribuciones)+len(d.reglas)
            estructuras+=bool(almacenadas)
            tiene_permiso=bool(r.get('autoriza_afirmar_suceso_actual',False))
            error=not tiene_permiso and n>0
            indebidos+=error
            filas.append({'id':r['id'],'texto':t,'clase':r['clase'],
                          'resuelto':a is not None,'estructuras':almacenadas,'hechos_indebidos':n if error else 0})
    return {'total':len(filas),'estructuras_persistentes':estructuras,'hechos_indebidos':indebidos,'filas':filas,
            'nota':'Examen externo de 40 frases sobre alcance. NO es puntuación de comprensión lingüística.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--oraculo',required=True)
    ap.add_argument('--guardar');a=ap.parse_args()
    r=evaluar(a.oraculo)
    print(f"Oráculo externo: estructuras {r['estructuras_persistentes']}/{r['total']}, hechos indebidos {r['hechos_indebidos']}")
    if a.guardar:Path(a.guardar).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
