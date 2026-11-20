"""Banco reproducible de comprensión discursiva 1.7 (sin Escuela entrenada).

Las familias y su gramática forman parte del desarrollo; no interpretar
estos porcentajes como comprensión de español libre. Cada caso usa memoria
independiente, se registra la respuesta real y no se ocultan fallos.

python -m scripts.evaluar_discurso17 --rondas 100 --semilla 17017 --guardar
"""
from __future__ import annotations
import argparse
import json
import random
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from src.memory.store import MemoryStore
from src.semantics.dialogue16 import DialogoConceptual, clave
from src.semantics.discourse17 import Discurso17

FEM=['Ana','Carla','Eva','Elena','Sara','Marta','Nora','Lucía']
MAS=['Luis','Pablo','Mario','Óscar','David','Tomás','Raúl','Hugo']
LUGARES=['Sevilla','Madrid','Cádiz','Granada','León','Burgos','Lugo','Bilbao']


def evaluar(rondas=100,semilla=17017,guardar=None):
    rng=random.Random(semilla)
    filas=[]
    por=defaultdict(lambda:[0,0])
    for ronda in range(rondas):
        a,b,c=rng.sample(FEM,3)
        l,m=rng.sample(MAS,2)
        ciudad,otra=rng.sample(LUGARES,2)
        preguntas=[
            ('dos_sujetos',[f'{a} ayuda a {l} y {l} saluda a {b}.'],
             lambda d: ('AYUDAR','SALUDAR')==tuple(f['p'] for f in d.nucleo.mem.facts)),
            ('elipsis',[f'{a} ayuda a {l} y saluda a {b}.'],
             lambda d: {f['s'] for f in d.nucleo.mem.facts}=={clave(a)} and len(d.nucleo.mem.facts)==2),
            ('relativa',[f'{a}, que vive en {ciudad}, ayuda a {l}.'],
             lambda d: {f['p'] for f in d.nucleo.mem.facts}=={'VIVIR_EN','AYUDAR'} and len(d.nucleo.mem.facts)==2),
            ('visita_ayer',[f'Ayer {a} visitó a {l}.',f'¿A quién visitó {a} ayer?'],
             lambda d: len(d.eventos)==1 and not d.nucleo.mem.facts and l in d._ultima),
            ('fecha_no_inventada',[f'Ayer {a} visitó a {l}.',f'¿A quién visitó {a} hoy?'],
             lambda d: 'No consta' in d._ultima and not d.nucleo.mem.facts),
            ('contradiccion_fecha',[f'Hoy {a} visita a {l}.',f'Hoy {a} no visita a {l}.',f'¿Visita {a} a {l} hoy?'],
             lambda d: 'incompatibles' in d._ultima and not d.nucleo.mem.facts),
            ('cambio_estado',[f'Antes {a} vivía en {ciudad}, ahora vive en {otra}.',f'¿Dónde vive {a} ahora?'],
             lambda d: otra in d._ultima and len(d.eventos)==2 and not d.nucleo.mem.facts),
            ('atribucion',[f'Según {a}, {l} ayuda a {b}.'],
             lambda d: not d.nucleo.mem.facts and len(d.nucleo.atribuciones)==1),
            ('correferencia',[f'{a} ayuda a {l}.', 'Ella lo saluda.'],
             lambda d: any(f['s']==clave(a) and f['o']==clave(l) and f['p']=='SALUDAR' for f in d.nucleo.mem.facts)),
            ('condicion',[f'Si X ayuda a Y, entonces Y saluda a X.',f'{a} ayuda a {l}.',f'¿A quién saluda {l}?'],
             lambda d: a in d._ultima and 'regla' in d._ultima),
        ]
        # Determinismo de las tandas: una muestra de cada familia, orden mezclado.
        rng.shuffle(preguntas)
        for familia,turnos,oracle in preguntas:
            with tempfile.TemporaryDirectory() as td:
                p=Path(td)
                mem=MemoryStore(str(p/'memory.json'));mem.today=date(2026,11,18)
                nucleo=DialogoConceptual(mem,ruta=p/'rules.json')
                d=Discurso17(nucleo,ruta=p/'discourse.json')
                resultados=[]
                for frase in turnos:
                    resp=d.procesar(frase)
                    if resp is None:resp=nucleo.procesar(frase)
                    resultados.append(resp)
                d._ultima=str(resultados[-1] or '')
                try:acierto=bool(oracle(d))
                except Exception:acierto=False
                filas.append({'ronda':ronda+1,'familia':familia,'turnos':turnos,
                              'respuestas':resultados,'acierto':acierto})
                por[familia][1]+=1
                por[familia][0]+=acierto
    tandas=[]
    for i in range(rondas):
        actual=filas[i*10:(i+1)*10]
        aciertos=sum(f['acierto'] for f in actual)
        tandas.append({'numero':i+1,'aciertos':aciertos,'aprobada':aciertos>=9})
    res={'schema':'lcmeval17-1','semilla':semilla,'rondas':rondas,'casos':len(filas),
         'aciertos':sum(f['acierto'] for f in filas),
         'tandas_aprobadas':sum(t['aprobada'] for t in tandas),
         'minimo_tanda':min(t['aciertos'] for t in tandas) if tandas else 0,
         'familias':{k:{'aciertos':v[0],'total':v[1]} for k,v in sorted(por.items())},
         'tandas':tandas,'fallos':[f for f in filas if not f['acierto']],
         'nota':'Tandas sintéticas limitadas a 10 familias del compositor; no son una prueba de español abierto.'}
    if guardar:
        path=Path(guardar);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
    return res


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rondas',type=int,default=100)
    ap.add_argument('--semilla',type=int,default=17017)
    ap.add_argument('--guardar',nargs='?',const='reports/discurso17_evaluacion.json')
    a=ap.parse_args()
    r=evaluar(a.rondas,a.semilla,a.guardar)
    print(f"LCM 1.7: {r['aciertos']}/{r['casos']} | "+
          f"tandas {r['tandas_aprobadas']}/{r['rondas']} (mínimo {r['minimo_tanda']}/10)")
    for k,v in r['familias'].items():print(f"  {k}: {v['aciertos']}/{v['total']}")
    for f in r['fallos'][:12]:print('FALLO',f['familia'],f['turnos'],f['respuestas'])

if __name__=='__main__':main()
