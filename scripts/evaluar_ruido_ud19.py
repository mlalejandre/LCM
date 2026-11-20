"""Prueba de stress de dependencia con perturbaciones CONTROLADAS (no pesos reales)."""
from __future__ import annotations
import argparse
import json
import random
import tempfile
from pathlib import Path
from src.memory.store import MemoryStore
from src.semantics.ud19 import PuenteUD19
from scripts.evaluar_ud19 import cases


def mutar(tree, tipo):
    rows=[tuple(r) for r in tree]
    if tipo=='correcto':return rows
    if tipo=='subj_perdido':return [(f,u,h,'dep' if rel=='nsubj' else rel,l) for f,u,h,rel,l in rows]
    if tipo=='dest_perdido':return [(f,u,h,'dep' if rel=='obl' else rel,l) for f,u,h,rel,l in rows]
    if tipo=='lema_aleatorio':return [(f,u,h,rel,'pintar' if rel=='root' else l) for f,u,h,rel,l in rows]
    if tipo=='entidad_falsa':
        for i,(f,u,h,rel,l) in enumerate(rows):
            if rel=='nsubj' and u=='PROPN':rows[i]=('Ignoradón',u,h,rel,l);break
        return rows
    if tipo=='ciclo':
        for i,(f,u,h,rel,l) in enumerate(rows):
            if rel=='root':rows[i]=(f,u,1,rel,l);break
        return rows
    if tipo=='intercambiar_roles':
        for i,(f,u,h,rel,l) in enumerate(rows):
            if rel=='nsubj':rows[i]=(f,u,h,'obl',l)
            elif rel=='obl':rows[i]=(f,u,h,'nsubj',l)
        return rows
    if tipo=='accion_falsa':
        for i,(f,u,h,rel,l) in enumerate(rows):
            if rel=='root':rows[i]=(f,u,h,rel,'prestar' if l!='prestar' else 'entregar');break
        return rows
    if tipo=='perdida_raiz':return [(f,u,1 if rel=='root' else h,rel,l) for f,u,h,rel,l in rows]
    if tipo=='obj_perdido':return [(f,u,h,'dep' if rel=='obj' else rel,l) for f,u,h,rel,l in rows]
    raise ValueError(tipo)


class EscuelaErrores:
    def __init__(self,texto,tree):self.texto=texto;self.rows=tree
    def tree(self,texto):
        if texto==self.texto:return self.rows
        raise ValueError('sin prediccion')


def ejecutar(n=2000,seed=1919):
    rng=random.Random(seed)
    opciones=['correcto','subj_perdido','dest_perdido','lema_aleatorio','entidad_falsa',
              'ciclo','intercambiar_roles','accion_falsa','perdida_raiz','obj_perdido']
    rows=[]
    sample=cases(seed+1,n*2)
    positives=[c for c in sample if c['esperado'] is not None][:n]
    if len(positives)<n:raise ValueError('faltan positivos')
    with tempfile.TemporaryDirectory() as td:
        for i,c in enumerate(positives):
            mode=opciones[i % len(opciones)]
            dat=mutar(c['arbol'],mode)
            root=Path(td)/str(i);root.mkdir()
            mem=MemoryStore(str(root/'m.json'))
            model=PuenteUD19(mem,EscuelaErrores(c['enunciado'],dat),ruta=root/'ud.json')
            ans=model.procesar(c['enunciado'])
            ev=model.eventos[-1] if model.eventos else None
            gold=(c['esperado'].casefold(),c['enunciado'])
            if mode=='correcto':
                good=bool(ev and ev['destinatario']==c['esperado'].upper().translate(str.maketrans('ÁÉÍÓÚÜ','AEIOUU')))
            else:good=ev is None
            rows.append({'tipo':mode,'correcto':good,'afirmacion':bool(ev),
                         'texto':c['enunciado'],'respuesta':ans})
    grp={}
    for r in rows:
        d=grp.setdefault(r['tipo'],{'n':0,'correcto':0,'afirmaciones':0});d['n']+=1;d['correcto']+=r['correcto'];d['afirmaciones']+=r['afirmacion']
    return {'n':n,'exactitud':sum(x['correcto'] for x in rows)/n,
            'afirmaciones_con_arbol_perturbado':sum(x['afirmacion'] and x['tipo']!='correcto' for x in rows),
            'por_perturbacion':grp,'casos':rows,'nota':'Simulación de errores UD sobre árboles anotados, NO School.pt'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=2000);ap.add_argument('--semilla',type=int,default=1919)
    ap.add_argument('--guardar',default='reports/ud19_perturbaciones.json')
    args=ap.parse_args();result=ejecutar(args.n,args.semilla)
    f=Path(args.guardar);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('Perturbaciones simuladas:',sum(r['correcto'] for r in result['casos']),'/',args.n)
    print('Afirmaciones con arbol alterado:',result['afirmaciones_con_arbol_perturbado'])
    print('Informe:',f)

if __name__=='__main__':main()
