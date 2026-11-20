"""Examen INTEGRAL opcional: usa SchoolParser + Motor + memoria temporal.
Requiere checkpoints/school.pt real. No altera la memoria personal.

Uso: python -m scripts.evaluar_conversaciones_lcm --n 1000

IMPORTANTE: un resultado en este examen tampoco equivale a cobertura del 99%
de conversaciones libres: son ejemplos templados, con entidades reservadas.
"""
from __future__ import annotations
import argparse
import json
import random
import tempfile
from pathlib import Path
from collections import Counter

CIUDADES=('Burgos','Lugo','Zamora','Cuenca','León','Cádiz','Huelva','Teruel')
COLORES=('azul','rojo','verde','amarillo','blanco','negro')
ACCIONES=('Dibuja','Pinta','Muestra','Enséñame','Diseña','Representa')


def principal(n=1000, semilla=241):
    from scripts.web import cargar_escuela
    from src.web.motor import Motor
    if not Path('checkpoints/school.pt').is_file():
        raise RuntimeError('Falta checkpoints/school.pt: prueba integral no ejecutable sin entrenar la Escuela')
    escuela=cargar_escuela()
    if escuela is None: raise RuntimeError('No se pudo cargar la Escuela original')
    rng=random.Random(semilla)
    with tempfile.TemporaryDirectory(prefix='lcm_semantica_eval_') as temp:
        motor=Motor.crear(ruta_memoria=temp+'/evaluacion.json',
                          carpeta_cartuchos=temp+'/cartuchos',parser=escuela,
                          semilla=False, log=lambda *_: None)
        fallos=[];cont=Counter();aciertos=Counter()
        for i in range(n):
            categoria=['vision','memoria','definicion','negacion'][i%4]
            color=rng.choice(COLORES)
            if categoria=='vision':
                mensaje=f'{rng.choice(ACCIONES)} el color {color}.'
                r=motor.chat(mensaje)
                ok=bool(r.get('imagen')) and color in str(r.get('respuesta','')).lower()
            elif categoria=='memoria':
                # Nombres únicos para evitar reutilizar soluciones de la memoria.
                nombre='Alba' if i%2==0 else 'Mario'
                entidad=f'{nombre}_{i}'
                ciudad=rng.choice(CIUDADES)
                motor.chat(f'{entidad} vive en {ciudad}.')
                r=motor.chat(f'¿Dónde vive {entidad}?')
                ok=ciudad.lower() in str(r.get('respuesta','')).lower()
                mensaje=f'¿Dónde vive {entidad}?'
            elif categoria=='definicion':
                mensaje=f'¿Qué es el color {color}?'
                r=motor.chat(mensaje)
                ok=bool(r.get('respuesta')) and color in str(r.get('respuesta','')).lower() and not r.get('error')
            else:
                mensaje=f'No dibujes el color {color}.'
                # No mostrar imagen ni generar acto; la Escuela puede tomarlo
                # como negación textual, esto se registra sin imponer respuesta.
                r=motor.chat(mensaje)
                ok=not r.get('imagen') and not r.get('error')
            cont[categoria]+=1
            if ok: aciertos[categoria]+=1
            elif len(fallos)<120: fallos.append({'grupo':categoria,'texto':mensaje,'resultado':r.get('respuesta'), 'error':r.get('error')})
        resumen={'modo':'evaluacion_integral_real_del_motor_local','n':n,'correctos':sum(aciertos.values()),
                 'exactitud':round(sum(aciertos.values())/n,4),
                 'por_familia':{k:{'total':cont[k],'aciertos':aciertos[k]} for k in sorted(cont)},
                 'fallos':fallos,'nota':'Plantillas sintéticas; no equivale a evaluación de diálogo humano libre'}
        return resumen


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n',type=int,default=1000)
    ap.add_argument('--semilla',type=int,default=241)
    a=ap.parse_args()
    if not 40<=a.n<=20000: ap.error('Número de turnos fuera de rango')
    try: x=principal(a.n,a.semilla)
    except RuntimeError as exc:
        print('[NO EJECUTADO]',exc)
        return 2
    out=Path('reports/semantica_conversaciones_integral.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('LCM integral:',x['correctos'],'/',x['n'],x['exactitud'], 'Informe:',out)
    for k,v in x['por_familia'].items():print(' ',k,v['aciertos'],'/',v['total'])
    return 0

if __name__=='__main__':
    raise SystemExit(main())
