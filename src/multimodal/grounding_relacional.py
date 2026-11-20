"""Conectar evidencia multimodal y roles sin atribuir percepciones inexistentes.

No implementa clasificación acústica. La etiqueta se registra sólo cuando el
usuario la ha confirmado expresamente o un futuro reconocedor está validado.
"""
from __future__ import annotations
from src.multimodal.events import ObservacionConceptual


def evento_anotado(grafo, modalidad, entidad, roles, origen='usuario', confirmado=False):
    if modalidad not in ('texto','imagen','audio'):
        raise ValueError('Modalidad no admitida')
    if not confirmado:
        raise ValueError('No se puede atribuir un significado sin evidencia confirmada')
    if not roles or any(k not in ('agente','accion','objeto','color','evento') for k in roles):
        raise ValueError('Roles incompletos o no admitidos')
    asignados={}
    for rol,palabra in roles.items():
        ident=grafo.resolver(palabra)
        if ident is None:
            raise ValueError('Concepto no conocido o polisémico: '+str(palabra))
        asignados[rol]=ident.upper()
    comprobacion='no_evaluada'
    if 'agente' in asignados and 'accion' in asignados:
        prueba=grafo.probar(asignados['agente'].lower(),asignados['accion'].lower(),
                           predicado='PUEDE_REALIZAR')
        comprobacion=('compatible' if prueba['estado']=='demostrado' else 'no_consta')
    return ObservacionConceptual(modalidad,entidad.upper(),
        asignados.get('evento'),origen,'usuario_confirmado',
        {'coherencia_semantica':comprobacion,'nota':'etiqueta enseñada; no predicción perceptiva'},
        asignados)
