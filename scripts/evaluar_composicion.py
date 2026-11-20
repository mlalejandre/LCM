"""Banco independiente de composición: casos nuevos, límites y abstención.

No es una medida de 'comprensión general' ni permite comparar con un LLM.
Se ejecuta aparte de la evaluación que acompañaba a Semántica 1.0.
"""
from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path

# Expectativas elegidas antes de ejecutar el banco. No se entrenan con estos casos.
CASOS=(
    ('Muéstrame una cartulina azul, por favor.','mostrar'),
    ('Quisiera que visualizaras una superficie de color rojo.','mostrar'),
    ('¿Podrías presentar el tono verde?','mostrar'),
    ('Deseo que exhibas una muestra blanca.','mostrar'),
    ('Si puedes, enséñame el color amarillo.','mostrar'),
    ('Hazme el favor de mostrar el color negro.','mostrar'),
    ('Crea una cartulina de color verde.','crear'),
    ('Por favor, dibuja el color azul.','crear'),
    ('¿Podrías esbozar una superficie amarilla?','crear'),
    ('Quiero que ilustres una muestra negra.','crear'),
    ('Me gustaría que dibujaras una muestra roja.','crear'),
    ('Si puedes, pinta un fondo de color blanco.','crear'),
    ('No quiero que pintes ninguna superficie azul.','abstencion'),
    ('No me enseñes el color azul.','abstencion'),
    ('Jamás dibujes un fondo verde.','abstencion'),
    ('No pintes: solo muéstrame el color verde.','mostrar'),
    ('No dibujes: únicamente presenta el color rojo.','abstencion'),
    ('Ana representa una forma amarilla.','abstencion'),
    ('Ella exhibe un cuadro negro.','abstencion'),
    ('El niño pinta una figura verde.','abstencion'),
    ('Te enseñaré el color rojo mañana.','abstencion'),
    ('Los colores rojo y azul son diferentes.','abstencion'),
    ('El pájaro emite sonidos.','abstencion'),
    ('Necesito comprar una pintura roja.','abstencion'),
    ('¿De qué color es esta imagen?','abstencion'),
    ('¿Qué significa el color verde?','definicion'),
    ('Define el color azul.','definicion'),
    ('¿Qué es el color amarillo?','definicion'),
    ('Me enseñas qué es el color negro?','definicion'),
    ('Enséñame los matices del azul.','abstencion'),
    ('Muestra el verde y compáralo con el rojo.','abstencion_o_aclaracion'),
    ('Representa colores rojo y verde.','abstencion_o_aclaracion'),
    ('Tramulea una imagen de color verde.','pregunta'),
    ('Azuplanea una imagen azul.','pregunta'),
)

def clasificar(r):
    if r is None:return 'abstencion'
    if r.get('semantica',{}).get('capacidad'):
        return r['semantica']['capacidad']
    x=r.get('respuesta','').lower()
    if 'no conozco' in x:return 'pregunta'
    if 'ambigua' in x or 'precises' in x:return 'aclaracion'
    if x.startswith(('azul:','rojo:','verde:','amarillo:','blanco:','negro:')):
        return 'definicion'
    return 'otro'

def ejecutar():
    from src.semantics.bridge import PuenteSemantico
    resultados=[]
    with tempfile.TemporaryDirectory() as d:
        sem=PuenteSemantico(aprendizaje=Path(d)/'aprendizaje.json')
        for frase,esperado in CASOS:
            sem.pendiente=None
            obtenido=clasificar(sem.responder(frase))
            valido=(esperado==obtenido or esperado=='abstencion_o_aclaracion' and obtenido in ('abstencion','aclaracion'))
            resultados.append({'frase':frase,'esperado':esperado,'obtenido':obtenido,'ok':valido})
    buenos=sum(r['ok'] for r in resultados)
    return {'n':len(resultados),'aciertos':buenos,'exactitud':round(buenos/len(resultados),4),
            'modo':'banco_dirigido_nuevo_no_prueba_de_generalizacion_abierta',
            'fallos':[r for r in resultados if not r['ok']]}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--guardar',action='store_true')
    args=ap.parse_args()
    rep=ejecutar()
    print('Composición:',rep['aciertos'],'/',rep['n'],f"{rep['exactitud']:.1%}")
    for f in rep['fallos']:print('FALLO',f)
    if args.guardar:
        p=Path('reports/composicion_evaluacion.json');p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Guardado en',p)

if __name__=='__main__':main()
