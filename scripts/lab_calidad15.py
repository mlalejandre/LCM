"""Banco reproducible de operaciones SIN Escuela entrenada.

200 tandas de 10. Mide únicamente capacidades disponibles en la reconstrucción:
reloj, hipótesis temporal, edad desde hechos, definiciones, muestras de color,
aritmética y barrera de citas.  NO mide la comprensión integral en español.

El enrutador ausente se sustituye SOLO EN ESTE PROCESO de evaluación. Nunca
se escribe en memoria de usuario ni se entrena la Escuela con casos de examen.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import random
import re
import tempfile
from collections import Counter
from pathlib import Path

from src.language import intents
from src.memory.store import MemoryStore
from src.web.motor import Motor
from src.semantics.bridge import PuenteSemantico
from src.quality.grounding import normalizar

COLORS=('rojo','verde','azul','amarillo','blanco','negro')
NAMES=('María','Elena','Marta','Juan','Rosa','Carlos','Laura','David','Raúl','Javier','Ana')

class RouterDePrueba:
    def route(self,texto):return 'OTRO',0.
class ParserIncompleto:
    def parse(self,*args,**kw):return []


def prueba(i, rng):
    """Una prueba de cada familia por tanda; los parámetros son aleatorios.
    No se elige la pregunta en función del resultado ni se ocultan fallos.
    """
    familia=i%10
    name=rng.choice(NAMES)
    y=rng.randrange(1920,2011)
    color=rng.choice(COLORS)
    a,b=rng.randint(2,60),rng.randint(2,60)
    reloj=('¿Qué hora es ahora?', '¿Sabes qué hora es?', '¿Me puedes decir qué hora es?')
    samples=('Muéstrame el color {}','Dibuja el color {}','Pinta el color {}',
             'Diseña un cuadro del color {}','Enséñame un ejemplo del color {}')
    if familia==0:return {'tipo':'reloj','q':rng.choice(reloj),'valor':None}
    if familia==1:return {'tipo':'hipotesis','q':f'Si {name} nació en {y}, ¿cuántos años tiene ahora {name}?','valor':(dt.date.today().year-y-1,dt.date.today().year-y)}
    if familia==2:return {'tipo':'edad','q':f'¿Cuántos años tiene {name}?','valor':(dt.date.today().year-y-1,dt.date.today().year-y),'nombre':name,'y':y}
    if familia==3:return {'tipo':'definicion','q':f'¿Qué es el color {color}?','valor':color}
    if familia==4:return {'tipo':'vision','q':rng.choice(samples).format(color),'valor':color.upper()}
    if familia==5:return {'tipo':'suma','q':f'¿Cuánto es {a} más {b}?','valor':a+b}
    if familia==6:return {'tipo':'raiz','q':f'¿Sabes calcular la raíz cuadrada de {a*a}?','valor':a}
    if familia==7:return {'tipo':'cita_ajena','q':f'¿Dónde nació {name}?','valor':name}
    if familia==8:return {'tipo':'concepto','q':'¿Qué es un pájaro?','valor':'ave'}
    if familia==9:return {'tipo':'negacion','q':f'No dibujes nada de color {color}','valor':color}
    raise AssertionError(familia)


def evaluar(caso, salida):
    t=normalizar(salida.get('respuesta','') or '')
    tipo=caso['tipo'];v=caso['valor'];imagen=salida.get('imagen')
    if salida.get('error'):return False
    if tipo=='reloj':
        m=re.search(r'\b([01]\d|2[0-3]):([0-5]\d)\b',salida.get('respuesta',''))
        if not m:return False
        observed=int(m.group(1))*60+int(m.group(2));now=dt.datetime.now().astimezone()
        actual=now.hour*60+now.minute
        return min(abs(observed-actual),1440-abs(observed-actual))<=2
    if tipo in ('hipotesis','edad'):
        return all(re.search(r'(?<!\d)'+str(x)+r'(?!\d)',t) for x in v)
    if tipo=='definicion':return v in t and len(t)>12 and imagen is None
    if tipo=='vision':return bool(imagen and imagen.get('color')==v)
    if tipo in ('suma','raiz'):return re.search(r'(?<!\d)'+str(v)+r'(?!\d)',t) is not None
    if tipo=='cita_ajena':return any(z in t for z in ('no tengo informacion suficientemente relacionada', 'no dispongo de informacion pertinente')) and not imagen
    if tipo=='concepto':return 'ave' in t and not imagen
    if tipo=='negacion':return not imagen and not salida.get('error') and 'no he entendido' not in t
    raise ValueError(tipo)


def correr(n=2000, seed=20261118, salida='reports/calidad15_banco.json'):
    assert n>0 and n%10==0
    rng=random.Random(seed)
    intents._ROUTER=RouterDePrueba()
    resumen={'modo':'Motor.chat real SIN checkpoints ni Escuela, con enrutador incompleto sustituido',
             'n':n,'semilla':seed,'criterio':'9/10 por tanda, revisar siempre primera tanda',
             'limitacion':'Simulación parcial. No demuestra comprensión general ni reemplaza prueba en Mac con school.pt.',
             'tandas':[]}
    with tempfile.TemporaryDirectory(prefix='lcm_calidad15_') as tmp:
        shared=PuenteSemantico(aprendizaje=Path(tmp)/'semantica_test.json')
        primeras=[]
        aprobadas=0
        for tanda in range(n//10):
            casos=[]
            for i in range(10):
                caso=prueba(tanda*10+i,rng)
                m=MemoryStore(str(Path(tmp)/(str(i)+'_m.json')))
                m.today=dt.date.today()
                if caso['tipo']=='edad':
                    m.add_fact((normalizar(caso['nombre']).upper(),'NACER','_'), source=f'{caso["nombre"]} nació en {caso["y"]}',when=str(caso['y']))
                motor=Motor(m,ParserIncompleto(),str(Path(tmp)/'no_cartuchos'))
                shared.pendiente=None
                motor._puente_semantico=shared
                if caso['tipo']=='cita_ajena':
                    class FalsoConversador:
                        def say(self,txt):return 'Según el texto, nació en 2007. En el texto: «Lamine Yamal nació en 2007».'
                    motor.conv=FalsoConversador()
                # Una persona sobre la que sí hay un hecho, otra sin él.
                r=motor.chat(caso['q']);ok=bool(evaluar(caso,r))
                casos.append({'familia':caso['tipo'],'q':caso['q'],'ok':ok,
                              'respuesta':r.get('respuesta') or str(r.get('error',''))})
            okn=sum(x['ok'] for x in casos)
            if tanda==0:primeras=casos
            reg_ok=sum(x['ok'] for x in primeras)>=9
            pasa=okn>=9 and reg_ok
            aprobadas+=pasa
            resumen['tandas'].append({'tanda':tanda+1,'aciertos':okn,'aprobada':pasa,
                                       'regresion_tanda_1':sum(x['ok'] for x in primeras),'casos':casos})
            if (tanda+1)%10==0 or tanda==0:
                print(f'[TANDA {tanda+1:03}] {okn}/10; primera {sum(x["ok"] for x in primeras)}/10; aprobadas acumuladas {aprobadas}',flush=True)
    resumen['aprobadas']=aprobadas
    resumen['aciertos']=sum(x['aciertos'] for x in resumen['tandas'])
    resumen['desglose']={tipo:{'aciertos':sum(x['ok'] for t in resumen['tandas'] for x in t['casos'] if x['familia']==tipo),
                              'n':sum(1 for t in resumen['tandas'] for x in t['casos'] if x['familia']==tipo)}
                          for tipo in sorted({x['familia'] for t in resumen['tandas'] for x in t['casos']})}
    p=Path(salida);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(resumen,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[RESULTADO] {resumen["aciertos"]}/{n}; tandas aprobadas {aprobadas}/{n//10}. Guardado en {p}')
    return resumen

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--n',type=int,default=2000)
    ap.add_argument('--semilla',type=int,default=20261118)
    ap.add_argument('--salida',default='reports/calidad15_banco.json')
    args=ap.parse_args()
    correr(args.n,args.semilla,args.salida)
