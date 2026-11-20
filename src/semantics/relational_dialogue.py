"""Entrada limitada para consultar pruebas relacionales desde el chat.

Las acciones del usuario siguen resolviéndose en el puente conceptual. Este
archivo solo reconoce un patrón interrogativo de relación y exige evidencia:
no inventa un vínculo por similitud entre palabras ni añade comandos verbales.
"""
from __future__ import annotations
import re
from .nucleo_relacional import _nrm


def respuesta_relacional(texto, sem):
    grafo=getattr(sem,'nucleo',None)
    if grafo is None:return None
    t=_nrm(texto).strip()
    m=re.fullmatch(r'que relacion (?:hay|existe) entre (.+?) (?:y|e) (.+)', t)
    if not m:return None
    def limpio(x):
        return re.sub(r'^(?:un|una|unos|unas|el|la|los|las)\s+','',x).strip()
    a,b=limpio(m.group(1)),limpio(m.group(2))
    ia,ib=grafo.resolver(a),grafo.resolver(b)
    if ia is None or ib is None:
        return {'respuesta':'Necesito desambiguar o aprender uno de los conceptos para relacionarlos con fiabilidad.',
                'aprendido':[],'fallo':False,'imagen':None,
                'relacion':{'estado':'no_resuelto','origen':a,'destino':b}}
    r=grafo.probar(ia,ib)
    if r['estado']!='demostrado':
        # La memoria general puede conocer relaciones que no están en este
        # pequeño núcleo: no impedir su consulta ordinaria.
        return None
    s=sem.items[ia]['lema']; o=sem.items[ib]['lema']
    if r['predicado']=='ES_UN':
        traza=' → '.join(sem.items[e['s']]['lema'] for e in r['ruta'])+' → '+o
        respuesta=f'«{s}» es un tipo de «{o}». Relación: {traza}.'
    else:
        rel=r['predicado'].lower().replace('_',' ')
        respuesta=f'«{s}» se relaciona con «{o}» mediante «{rel}» (dato curado).'
    return {'respuesta':respuesta,'aprendido':[],'fallo':False,'imagen':None,
            'relacion':r}
