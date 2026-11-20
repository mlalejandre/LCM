"""Banco de 10 casos por tanda para composición 1.6 (sin School neuronal).

Comprueba derivación y abstención, no fluidez de español libre. Dos semillas
separadas permiten distinguir el examen de desarrollo del de reserva.
"""
from __future__ import annotations
import argparse
import json
import random
import tempfile
from pathlib import Path
from src.memory.store import MemoryStore
from src.semantics.dialogue16 import DialogoConceptual

NOMBRES=['Ana','Luis','Carla','Manuel','Eva','Leo','Rosa','Hugo','Laura','Pablo','Elena','David',
         'Clara','Óscar','Marta','Tomás','Nora','Diego','Lola','Rubén','Irene','Mario']
VERBOS=['ayuda','saluda','visita','acompaña','admira','cuida','observa','escucha','abraza','elogia',
        'respeta','reconoce','anima','apoya']


def caso(semilla,tipo):
    rg=random.Random(semilla)
    a,b,c=rg.sample(NOMBRES,3)
    v,w,x=rg.sample(VERBOS,3)
    # Cada caso crea un motor con hechos y reglas propios, sin fugas entre turnos.
    if tipo==0:
        lineas=[f'Si X {v} a Y, entonces Y {w} a X.',f'{a} {v} a {b}.',f'¿A quién {w} {b}?']
        def ok(r):return a.casefold() in r.casefold() and 'deduce' in r
    elif tipo==1:
        lineas=[f'{a} {v} a {b}.',f'¿A quién {v} {b}?']
        def ok(r):return 'no consta' in r.lower() or 'no invertir' in r.lower()
    elif tipo==2:
        lineas=[f'Si X {v} a Y, entonces Y {w} a X.',f'{a} no {v} a {b}.',f'¿A quién {w} {b}?']
        def ok(r):return 'no consta' in r.lower()
    elif tipo==3:
        lineas=[f'Si X {v} a Y, entonces Y {w} a X.',f'Si X {w} a Y, entonces Y {x} a X.',
                f'{a} {v} a {b}.',f'¿A quién {x} {a}?']
        def ok(r):return b.casefold() in r.casefold() and 'deduce' in r
    elif tipo==4:
        lineas=[f'Si X {v} a Y y Y {w} a Z, entonces X {x} a Z.',
                f'{a} {v} a {b}.',f'{b} {w} a {c}.',f'¿A quién {x} {a}?']
        def ok(r):return c.casefold() in r.casefold() and 'deduce' in r
    elif tipo==5:
        lineas=[f'Si X {v} a Y, entonces Y {w} a X.',f'Si {a} {v} a {b}, ¿a quién {w} {b}?',f'¿A quién {w} {b}?']
        def ok(r):return 'no consta' in r.lower()
    elif tipo==6:
        # Pronombre: dos personas de género morfológico claramente distinto.
        mujeres=[n for n in NOMBRES if n.endswith('a')]
        hombres=[n for n in NOMBRES if not n.endswith('a')]
        a=rg.choice(mujeres);b=rg.choice(hombres)
        lineas=[f'{a} {v} a {b}.',f'¿A quién {v} ella?']
        def ok(r):return b.casefold() in r.casefold()
    elif tipo==7:
        lineas=[f'{a} cree que {b} {v} a {c}.',f'¿A quién {v} {b}?']
        def ok(r):return 'no consta' in r.lower()
    elif tipo==8:
        lineas=[f'{a} {v} a {b}.',f'{a} no {v} a {b}.',f'¿{v.capitalize()} {a} a {b}?']
        def ok(r):return 'incompatibles' in r.lower()
    elif tipo==9:
        lineas=[f'Si X {v} a Y, entonces Y {w} a X.',f'{a} {v} a {b}.',f'¿A quién {w} {b}?']
        def ok(r):return a.casefold() in r.casefold() and 'deduce' in r
    else:raise ValueError(tipo)
    return lineas,ok


def ejecutar(n=2000,semilla=1745,salida=None):
    resultados=[];errores=[]
    with tempfile.TemporaryDirectory(prefix='lcm16_examen_') as tmp:
        base=Path(tmp)
        for i in range(n):
            lineas,check=caso(semilla+i*53,i%10)
            mem=MemoryStore(str(base/f'mem{i}.json'))
            engine=DialogoConceptual(mem,ruta=base/f'rules{i}.json')
            respuestas=[]
            for linea in lineas:
                respuestas.append(engine.procesar(linea))
            # tipo 9 verifica persistencia de reglas y hechos al reiniciar.
            if i%10==9:
                mem2=MemoryStore(str(base/f'mem{i}.json'))
                engine2=DialogoConceptual(mem2,ruta=base/f'rules{i}.json')
                respuestas[-1]=engine2.procesar(lineas[-1])
            ok=bool(respuestas[-1] and check(respuestas[-1]))
            resultados.append(ok)
            if not ok and len(errores)<30:
                errores.append({'caso':i,'lineas':lineas,'respuestas':respuestas})
    tandas=[sum(resultados[i:i+10]) for i in range(0,n,10)]
    informe={'total':n,'aciertos':sum(resultados),'exactitud':round(sum(resultados)/n,5),
             'tandas':len(tandas),'tandas_aprobadas':sum(x>=9 for x in tandas),
             'minimo_tanda':min(tandas), 'aprobado':all(x>=9 for x in tandas),
             'errores_muestra':errores,'semilla':semilla,
             'alcance':'gramática SVO controlada, con entidades/verbos aleatorios; no mide español libre'}
    if salida:
        Path(salida).parent.mkdir(parents=True,exist_ok=True)
        Path(salida).write_text(json.dumps(informe,ensure_ascii=False,indent=2),encoding='utf8')
    print(f'{sum(resultados)}/{n} | tandas >=9/10: {informe["tandas_aprobadas"]}/{len(tandas)} | mínimo {min(tandas)}/10')
    for e in errores[:6]:print('FALLO',e)
    return informe


def main():
    p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=2000);p.add_argument('--semilla',type=int,default=1745)
    p.add_argument('--salida',default='reports/dialogo16_evaluacion.json');args=p.parse_args()
    r=ejecutar(args.n,args.semilla,args.salida)
    raise SystemExit(0 if r['aprobado'] else 1)

if __name__=='__main__':main()
