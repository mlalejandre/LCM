"""Examen de 10k+ intervenciones sintéticas, con evaluación por capacidad.
NO mide conversación general ni justifica el 99% de cobertura. Usa un holdout
por plantillas y una semilla distinta de las usadas para crear los conceptos.

Uso: python -m scripts.evaluar_semantica [--n 12000] [--guardar]
"""
from __future__ import annotations
import argparse
import json
import random
import tempfile
from collections import Counter
from pathlib import Path

COLORES=['rojo','verde','azul','amarillo','blanco','negro']
# Las frases de prueba no figuran como ejemplos concretos en el seed conceptual.
VISTAS={
 'crear':['Dibuja un fondo de color {color}.', 'Pinta una superficie {color}.',
          'Crea una imagen {color}, por favor.', 'Diseña un cuadro de tono {color}.',
          'Genera una muestra de color {color}.', 'Ilustra el color {color}.',
          'Representa una muestra {color}.', 'Quiero que dibujes el color {color}.'],
 'mostrar':['Muéstrame una muestra {color}.','Enseña el color {color}.',
           'Muestra un ejemplo visual del color {color}.','Exhibe una imagen {color}.',
           'Presenta el color {color}.','Visualiza el color {color}.',
           'Quiero que muestres el color {color}.', 'Puedes mostrar el color {color}.']}
FUERA=['La mesa azul está en el salón.', 'Ana dibuja el color rojo.', 'No dibujes el color verde.',
       'El agua es azul en algunas fotografías.', '¿De qué color es la imagen?',
       '¿Cuántos cuadrados azules hay?', 'No pintes nada de color amarillo.',
       'La sombra parece azul.', 'Los colores rojo y azul son diferentes.',
       'Me pregunto cómo se llama el color verde.',
       'No quiero que muestres el color azul.', 'Ella crea un cuadro de color rojo.']
DEFINIR=['¿Qué es el color {color}?','Define el color {color}.',
         '¿Qué significa {color}?','Dime qué es el color {color}.']
# Hay frases en las que la semántica de una palabra desconocida es inaccesible:
# el comportamiento correcto no es adivinar, sino solicitar una explicación.
DESCONOCIDAS=['Trazulea una imagen de color {color}.','Bocetiza una imagen de color {color}.',
               'Azuplanea un cuadro {color}.']


def casos(n=12000, seed=20261119):
    rng=random.Random(seed)
    out=[]
    for i in range(n):
        kind=i%7
        color=rng.choice(COLORES)
        if kind in (0,1,2):
            op='crear' if kind!=1 else 'mostrar'
            frase=rng.choice(VISTAS[op]).format(color=color)
            expected=op
        elif kind==3:
            frase=rng.choice(DEFINIR).format(color=color);expected='definicion'
        elif kind==4:
            frase=rng.choice(FUERA);expected='abstencion'
        elif kind==5:
            # Modelo debe pedir aclaración ante un verbo no registrado.
            frase=rng.choice(DESCONOCIDAS).format(color=color);expected='pregunta'
        else:
            frase=rng.choice(VISTAS['mostrar']).format(color=color);expected='mostrar'
        out.append((frase,expected))
    rng.shuffle(out)
    return out


ADVERSARIAS = [
 ('¿Podrías esbozar una forma {color}?','crear','solicitud_condicional'),
 ('Me gustaría que dibujaras una muestra {color}.','crear','subjuntivo_no_visto'),
 ('Si puedes, pinta una imagen {color}.','crear','condicional'),
 ('Hazme el favor de mostrar el color {color}.','mostrar','accion_subordinada'),
 ('Me enseñas qué es el color {color}?','definicion','polisemia_de_ensenar'),
 ('No quiero que crees nada {color}.','abstencion','negacion_compleja'),
 ('No pintes: solo muestra el color {color}.','mostrar','contraste_negacion'),
 ('Me pregunto si podrías dibujar un fondo {color}.','crear','solicitud_indirecta'),
 ('Mira esta imagen {color}.','abstencion','referencia_sin_adjunto'),
 ('El niño dibuja una luna {color}.','abstencion','declaracion_sujeto'),
 ('Necesito comprar pintura {color}.','abstencion','otra_tarea'),
 ('¿Puedes explicar el significado del color {color}?','abstencion','explicacion_no_generacion'),
 ('¿Podrías ponerme una muestra {color}?','mostrar','verbo_de_soporte'),
 ('Sería estupendo contemplar un rectángulo {color}.','abstencion','deseo_sin_comando'),
 ('No me muestres un cuadro {color}.','abstencion','negacion_pronominal'),
 ('Muestra el color {color} y compáralo con el blanco.','abstencion','tarea_compuesta_no_implementada'),
 ('Enséñame los matices del {color}.','abstencion','fuera_de_capacidad'),
 ('Te mostraré un dibujo {color}.','abstencion','futuro_declarativo'),
 ('¿Qué entiendes por {color}?','abstencion','pregunta_conceptual_distinta'),
 ('Desearía visualizar una tarjeta de color {color}.','mostrar','optativo'),
]


def casos_adversarios(n=4000,seed=20261120):
    rng=random.Random(seed)
    out=[]
    for _ in range(n):
        pattern,esperado,familia=rng.choice(ADVERSARIAS)
        out.append((pattern.format(color=rng.choice(COLORES)),esperado,familia))
    return out


def adversario(n=4000,seed=20261120):
    from src.semantics.bridge import PuenteSemantico
    with tempfile.TemporaryDirectory() as d:
        sem=PuenteSemantico(aprendizaje=Path(d)/'aprendizaje.json')
        familias=Counter();errores=Counter();fallos=[]
        for frase,expected,familia in casos_adversarios(n,seed):
            sem.pendiente=None
            result=clasificar(sem.responder(frase))
            familias[familia]+=1
            if expected!=result:
                errores[familia]+=1
                if len(fallos)<50: fallos.append({'familia':familia,'frase':frase,'esperado':expected,'obtenido':result})
        good=n-sum(errores.values())
        return {'modo':'desafio_de_plantillas_adversarias_no_lcm_completo','n':n,'correctos':good,
                'exactitud':round(good/n,5),'por_familia':[{'familia':f,'n':familias[f],
                'aciertos':familias[f]-errores[f]} for f in sorted(familias)],'fallos':fallos}

def clasificar(resultado):
    if resultado is None:return 'abstencion'
    if resultado.get('semantica'):return resultado['semantica']['capacidad']
    if 'no conozco' in resultado.get('respuesta','').lower():return 'pregunta'
    if resultado.get('respuesta','').startswith(('Azul:','Rojo:','Verde:','Blanco:','Negro:','Amarillo:')):return 'definicion'
    return 'otro'


def ejecutar(n=12000, seed=20261119):
    from src.semantics.bridge import PuenteSemantico
    with tempfile.TemporaryDirectory() as d:
        sem=PuenteSemantico(aprendizaje=Path(d)/'aprendizaje.json')
        matriz=Counter();fallos=[];total=0
        for frase,esperado in casos(n,seed):
            # Preguntas independientes: no heredar un diálogo de aclaración.
            sem.pendiente=None
            got=clasificar(sem.responder(frase))
            matriz[(esperado,got)]+=1;total+=1
            if got!=esperado and len(fallos)<60:
                fallos.append({'frase':frase,'esperado':esperado,'obtenido':got})
        buenos=sum(v for (esp,got),v in matriz.items() if esp==got)
        informe={'modo':'simulacion_del_puente_semantico_no_conversacion_integral_del_lcm',
                 'advertencia':'Las plantillas son sintéticas y los resultados NO equivalen a cobertura del español real.',
                 'n':total,'correctos':buenos,'exactitud':round(buenos/total,5),
                 'matriz':[{ 'esperado':e,'obtenido':g,'n':v} for (e,g),v in sorted(matriz.items())],
                 'fallos':fallos,'inventario':sem.lex.informe()}
        return informe


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n',type=int,default=12000)
    ap.add_argument('--semilla',type=int,default=20261119)
    ap.add_argument('--guardar',action='store_true')
    ap.add_argument('--desafio',type=int,default=4000)
    a=ap.parse_args()
    if not 100<=a.n<=100000: ap.error('--n debe estar entre 100 y 100000')
    reporte=ejecutar(a.n,a.semilla)
    print(f'Simulación léxico-semántica: {reporte["correctos"]}/{reporte["n"]} = {reporte["exactitud"]:.2%}')
    print('Esto NO evalúa la conversación integral ni demuestra cobertura del 99% del español.')
    rep_adv=adversario(a.desafio,a.semilla+1)
    reporte['adversario']=rep_adv
    print(f'Desafío adversario: {rep_adv["correctos"]}/{rep_adv["n"]} = {rep_adv["exactitud"]:.2%}')
    for fila in rep_adv['por_familia']:
        if fila['aciertos']!=fila['n']: print('  DIFICULTAD:',fila)
    print('Inventario:',reporte['inventario'])
    for f in reporte['fallos'][:20]: print('  FALLO:',f)
    if a.guardar:
        p=Path('reports/semantica_evaluacion.json');p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(reporte,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Guardado en',p)

if __name__=='__main__': main()
