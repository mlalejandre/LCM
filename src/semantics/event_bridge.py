"""LCM 1.3: puente sin coerción entre ontología y evidencia episódica.

La similitud vectorial sirve para buscar candidatos, pero nunca certifica
identidad ni prueba que haya ocurrido un suceso.
"""
from __future__ import annotations

from src.multimodal.episodic_memory import Afirmacion


def resolver_rol(semantica, forma, tipo=None):
    """Devuelve ID inequívoco o candidatos para aclaración, sin forzar elección."""
    g=getattr(semantica,'nucleo',None)
    if g is None:
        return {'estado':'sin_nucleo','id':None,'candidatos':[]}
    exact=g.resolver(forma,tipo=tipo)
    if exact is not None:
        return {'estado':'resuelto','id':exact,'candidatos':[]}
    candidatos=[{'id':c['id'],'lema':c['lema']} for c in semantica.buscar(forma,tipo=tipo)]
    return {'estado':'ambiguo' if candidatos else 'desconocido','id':None,
            'candidatos':candidatos}


def capacidad_no_es_suceso(semantica, tipo, accion):
    """Prueba capacidad desde ESQUEMA relacional; NO inventa un evento real."""
    g=getattr(semantica,'nucleo',None)
    if g is None:
        return {'estado':'sin_nucleo','ruta':[]}
    x=g.probar(tipo, accion, 'PUEDE_REALIZAR')
    return {'estado':'capacidad_de_tipo' if x['estado']=='demostrado' else x['estado'],
            'ruta':x.get('ruta',[]), 'autoriza_suceso':False}


def suceso_declarado(memoria, sujeto, verbo, contexto, instante=None,
                     cree=None, negado=False, modalidad='texto'):
    """Entrada de la Escuela/desambiguación una vez confirmados sujeto y verbo.

    No analiza frases automáticamente; exige identidades resueltas, instancia
    concreta y contexto declarado. Para narraciones oídas, es testimonio.
    """
    estatus='creencia' if cree else 'actual'
    a=Afirmacion(sujeto,'REALIZAR',verbo,contexto,estatus=estatus,
        polaridad=not negado,hablante=cree or 'USUARIO',
        modalidad=modalidad,evidencia='usuario_afirma',instante=instante)
    return memoria.afirmar(a)
