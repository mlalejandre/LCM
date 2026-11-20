"""Evaluación dirigida de invariantes de evidencia LCM 1.3 (NO idioma completo).

Genera escenas e identidades nuevas a partir de semilla reproducible.
Cada familia usa su propio oráculo predefinido. Los objetivos no cambian
según el resultado. Registra por familia los fallos y abstenciones.
"""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
from tempfile import TemporaryDirectory
from src.multimodal.episodic_memory import MemoriaEpisodica, Afirmacion
from src.multimodal.events import ObservacionConceptual

FAMILIAS=('capacidad_no_actual','creencia_no_actual','contradiccion_mismo_instante',
          'cambio_temporal','imagen_sin_color','audio_no_reconocido',
          'imagen_color','hipotesis_no_actual')


def ejecutar(n=256, semilla=1307):
    if n<8 or n>3000:raise ValueError('n entre 8 y 3000')
    rng=random.Random(semilla)
    informe={f:{'aciertos':0,'total':0,'fallos':[]} for f in FAMILIAS}
    # Cada caso usa memoria aislada. No escribe ni toca la memoria real.
    with TemporaryDirectory() as folder:
        for i in range(n):
            f=FAMILIAS[i%len(FAMILIAS)]
            m=MemoriaEpisodica(Path(folder)/f'caso_{i}.json')
            sujeto=f'AVE_{rng.randrange(1,10**9)}'
            escena=f'ESCENA_{i}'
            p='accion.piar' if rng.random()<.5 else 'accion.volar'
            q=lambda modo='actual':m.consultar(sujeto,'REALIZAR',p,escena,estatus=modo)['estado']
            esperado='no_consta'
            if f=='capacidad_no_actual':
                m.afirmar(Afirmacion('concepto.pajaro','PUEDE_REALIZAR',p,escena,
                    estatus='posible',alcance='tipo'))
                obtenido=q()
            elif f=='creencia_no_actual':
                m.afirmar(Afirmacion(sujeto,'REALIZAR',p,escena,estatus='creencia',hablante='ANA'))
                obtenido=q()
            elif f=='contradiccion_mismo_instante':
                m.afirmar(Afirmacion(sujeto,'REALIZAR',p,escena))
                m.afirmar(Afirmacion(sujeto,'REALIZAR',p,escena,polaridad=False,hablante='OTRO'))
                esperado='conflicto';obtenido=q()
            elif f=='cambio_temporal':
                m.afirmar(Afirmacion(sujeto,'REALIZAR',p,escena,instante='2026-11-17T10:00:00+01:00'))
                m.afirmar(Afirmacion(sujeto,'REALIZAR',p,escena,instante='2026-11-17T11:00:00+01:00',polaridad=False))
                esperado='evidencias_distintos_contextos';obtenido=q()
            elif f=='imagen_sin_color':
                o=ObservacionConceptual('imagen',f'IMAGEN_{i}',None,'prueba',
                        'clasificador_color',{}, {})
                m.observar(o,escena)
                obtenido=m.consultar(f'IMAGEN_{i}','TENER_COLOR','VERDE',escena)['estado']
            elif f=='audio_no_reconocido':
                o=ObservacionConceptual('audio',f'AUDIO_{i}',None,'prueba',
                        'acustica_sin_clasificar',{}, {})
                m.observar(o,escena)
                obtenido=m.consultar(f'AUDIO_{i}','ETIQUETA_ACCION','ACCION.PIAR',escena)['estado']
            elif f=='imagen_color':
                colores=('ROJO','VERDE','AZUL','AMARILLO','BLANCO','NEGRO')
                color=rng.choice(colores)
                o=ObservacionConceptual('imagen',f'IMAGEN_{i}',color,'prueba',
                        'clasificador_color',{}, {'color':color})
                m.observar(o,escena)
                esperado='observado_por_clasificador'
                obtenido=m.consultar(f'IMAGEN_{i}','TENER_COLOR',color,escena)['estado']
            else:
                m.afirmar(Afirmacion(sujeto,'REALIZAR',p,escena,estatus='hipotetico'))
                obtenido=q()
            a=informe[f]
            a['total']+=1
            if obtenido==esperado:a['aciertos']+=1
            elif len(a['fallos'])<8:
                a['fallos'].append({'caso':i,'esperado':esperado,'obtenido':obtenido})
    bien=sum(x['aciertos'] for x in informe.values())
    return {'tipo':'evaluación de invariantes de representación, NO comprensión general del español',
            'semilla':semilla,'n':n,'aciertos':bien,'exactitud':round(bien/n,5),
            'familias':informe,'limites':[
                'escenas sintéticas generadas desde reglas del contrato',
                'no evalúa extracción de hechos desde español libre',
                'no evalúa reconocimiento de fotografías complejas ni canto de aves',
                'éxito en estos casos no prueba generalización ni verdad del mundo']}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n',type=int,default=256)
    ap.add_argument('--semilla',type=int,default=1307)
    ap.add_argument('--guardar',action='store_true')
    args=ap.parse_args()
    r=ejecutar(args.n,args.semilla)
    print('LCM episodios:',r['aciertos'],'/',r['n'],f"= {r['exactitud']:.1%}")
    for nombre,v in r['familias'].items():
        print(f'  {nombre}: {v["aciertos"]}/{v["total"]}')
        for f in v['fallos']:print('    ERROR',f)
    print('Aviso:',r['tipo'])
    if args.guardar:
        ruta=Path('reports/episodios_evaluacion.json')
        ruta.parent.mkdir(parents=True,exist_ok=True)
        ruta.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Guardado:',ruta)

if __name__=='__main__':main()
