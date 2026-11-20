"""Consultar relaciones, pruebas y vecinos con estructura del LCM.
Uso:
  python -m scripts.consultar_relaciones pájaro animal
  python -m scripts.consultar_relaciones pájaro piar --predicado PUEDE_REALIZAR
  python -m scripts.consultar_relaciones pájaro --vecinos 6
"""
import argparse
import json
from src.semantics.lexicon import Semantica

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('concepto');p.add_argument('otro',nargs='?')
    p.add_argument('--predicado',default=None)
    p.add_argument('--vecinos',type=int,default=0)
    a=p.parse_args()
    sem=Semantica(); g=sem.nucleo
    if g is None:raise SystemExit('El núcleo relacional no está instalado')
    gl=g.glosa(a.concepto)
    print('CONCEPTO:', json.dumps(gl,ensure_ascii=False,indent=2) if gl else 'desconocido o ambiguo')
    if a.otro:
        print('PRUEBA:', json.dumps(g.probar(a.concepto,a.otro,a.predicado),ensure_ascii=False,indent=2))
    else:
        print('ENLACES:',json.dumps(g.vinculaciones(a.concepto,50),ensure_ascii=False,indent=2))
    if a.vecinos:
        print('VECINOS VECTORIALES PROYECTADOS:', json.dumps(g.similitudes_estructurales(a.concepto,max(1,min(30,a.vecinos))),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
