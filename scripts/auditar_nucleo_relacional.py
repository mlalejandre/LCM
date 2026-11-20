"""Informe de cobertura estructural sin presentar porcentaje de español comprendido."""
import json
import argparse
from collections import Counter
from pathlib import Path
from src.semantics.lexicon import Semantica

def ejecutar():
    sem=Semantica();g=sem.nucleo
    items=sem.items
    sin_def=sum(not c.get('definicion') or c.get('evidencia')=='agrupacion_inicial' for c in items.values())
    incidencias={x['s'] for x in g.datos['relaciones']} | {x['o'] for x in g.datos['relaciones']}
    comprobaciones=[('pájaro','animal','ES_UN'),('perro','animal','ES_UN'),
      ('cuadrado','figura plana','ES_UN'),('pájaro','piar','PUEDE_REALIZAR'),
      ('perro','piar','PUEDE_REALIZAR'),('pingüino','volar','PUEDE_REALIZAR'),
      ('pío','sonido','ES_UN'),('imagen','audición','SE_PERCIBE_POR')]
    exam=[]
    for a,b,p in comprobaciones:
        out=g.probar(a,b,p)
        exam.append({'consulta':[a,p,b],'estado':out['estado'],'longitud_prueba':len(out['ruta'])})
    return {'schema':'lcm-auditoria-relacional-1.2',
      'tipo':'inventario de conectividad, NO evaluación lingüística independiente',
      'conceptos_totales':len(items),'nuevos':len(g.datos['nuevos']),
      'definiciones_curadas_adicionales':len(g.datos['definiciones']),
      'entradas_sin_definicion_revisada':sin_def,
      'relaciones_explicitadas_adicionales':len(g.datos['relaciones']),
      'nodos_conectados_en_grafo_nuevo':len(incidencias),
      'nodos_aislados_en_grafo_nuevo':len(items)-len(incidencias),
      'evidencia':'curación asistida revisable, sin corpus externo verificado',
      'sondeos':exam}

def main():
    a=argparse.ArgumentParser();a.add_argument('--guardar',action='store_true');args=a.parse_args()
    r=ejecutar(); print(json.dumps(r,ensure_ascii=False,indent=2))
    if args.guardar:
        p=Path('reports/relaciones_12.json');p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
