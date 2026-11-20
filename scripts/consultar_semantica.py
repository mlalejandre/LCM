"""Explorar significados, polisemia y vecinos vectoriales del núcleo semántico.
Uso: python -m scripts.consultar_semantica dibujar
     python -m scripts.consultar_semantica banco --vecinos 8
"""
from __future__ import annotations
import argparse
from src.semantics.lexicon import Semantica


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('palabra',nargs='?',default='')
    p.add_argument('--vecinos',type=int,default=6)
    a=p.parse_args()
    sem=Semantica()
    print('INVENTARIO',sem.informe())
    if a.palabra:
        sentidos=sem.buscar(a.palabra)
        if not sentidos:
            print('Palabra sin sentidos registrados. No se inventa vector para ella.')
            return
        for c in sentidos:
            print('\nSENTIDO',c['id'],'familia:',c['familia'],'subfamilia:',c['subfamilia'])
            print('Definición:',c['definicion'] or '(pendiente de definición revisada)')
            print('Calidad:',c['evidencia'])
            print('Padres:',', '.join(c['padres']) or '(sin relación padre declarada)')
            print('Vecinos coseno:',sem.similares(c['id'],tipo=c['tipo'],limite=max(1,min(30,a.vecinos))))

if __name__=='__main__': main()
