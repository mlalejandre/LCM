"""Composición semántica experimental (LCM 1.1).

Distingue estructura lingüística (negación, alcance, petición, argumentos) de
identidad conceptual (Lexicon + vectores ConceptSpace). Los verbos no se
mapean a comandos ni hay una lista de sinónimos de dibujar/mostrar.

ALCANCE: una muestra cromática simple. Se abstiene ante composición no soportada.
No afirma ser un parser sintáctico general ni sustituye a la Escuela del LCM.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import re
from typing import Optional
from .lexicon import tokens, normalizar

# Son pistas de gramática/estructura discursiva, NO equivalencias entre verbos.
MARCADORES_PETICION = frozenset({
    'puedes', 'podrias', 'podria', 'podriamos', 'quiero', 'quisiera',
    'necesito', 'deseo', 'desearia', 'gustaria', 'favor', 'hazme',
    'podriais', 'posible', 'si', 'permite', 'permitiria'
})
NEGADORES = frozenset({'no', 'nunca', 'jamas', 'tampoco', 'sin'})
CONTRASTE = frozenset({'pero', 'sino', 'solo', 'solamente'})
CONECTORES = frozenset({'que', 'de', 'a', 'para', 'con', 'y', 'o', 'lo', 'le', 'me', 'te', 'nos'})
PRONOMBRES_SUJETO = frozenset({'el', 'ella', 'ellos', 'ellas', 'ana', 'pedro', 'nino', 'nina'})
DETERMINANTES = frozenset({'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'este', 'esta'})

@dataclass(frozen=True)
class Predicado:
    indice: int
    forma: str
    concepto: str
    lema: str
    familia: str
    negado: bool
    puntuacion: int  # índice de segmento delimitado por signos
    capacidad: Optional[str]
    similitudes: dict

@dataclass
class Marco:
    original: str
    modalidad_entrada: str
    clase: str  # peticion, declaracion, definicion, negacion, ambigua, no_soportada
    conceptos_color: tuple
    predicados: tuple
    accion: Optional[str] = None
    capacidad: Optional[str] = None
    razon: str = ''

    def dict(self):
        return {
            'tipo': self.clase,
            'modalidad_entrada': self.modalidad_entrada,
            'colores': list(self.conceptos_color),
            'accion': self.accion, 'capacidad': self.capacidad,
            'razon': self.razon,
            'predicados': [asdict(x) for x in self.predicados],
        }


def _segmentos(texto):
    """Cláusulas separadas por signos fuertes, conservando posición."""
    partes = re.split(r'[:;.!?]+', normalizar(texto))
    return [tokens(p) for p in partes if tokens(p)]


def _flexion_regular(lema, forma):
    """Reconocimiento morfológico con terminaciones productivas.

    Esto no asigna significado a una palabra desconocida: solamente permite
    enlazar una flexión con un lema YA registrado en la ontología.
    """
    if not lema.endswith(('ar','er','ir')) or len(lema)<5:
        return False
    raiz = lema[:-2]
    if not forma.startswith(raiz):
        return False
    suf = forma[len(raiz):]
    comunes = {'amos', 'ais', 'an', 'as', 'a', 'es', 'e', 'en', 'o', 'emos', 'eis', 'imos',
               'is', 'ado', 'ido', 'ando', 'iendo', 'ara', 'aras', 'aramos', 'aran',
               'ase', 'ases', 'asemos', 'asen', 'iera', 'ieras', 'ieramos', 'ieran',
               'iese', 'ieses', 'iesemos', 'iesen', 'aste', 'asteis', 'aron',
               'iste', 'isteis', 'ieron', 'aba', 'abas', 'aban', 'abamos',
               'ia', 'ias', 'ian', 'iamos', 'are', 'aras', 'ara', 'areis', 'aran',
               'eria', 'erias', 'eria', 'erian', 'iria', 'irias', 'irian',
               'ares', 'iere', 'ieren', 'ieres', 'ados', 'adas'}
    # Evitar reconocer formas cortísimas con análisis morfológico dudoso.
    return len(forma)>=5 and suf in comunes


def _acciones_para(palabra, lex):
    encontradas = lex.buscar(palabra, tipo='accion')
    if encontradas:
        return encontradas
    # Indice de formas flexionadas de lemas YA conocidos; se invalida si el
    # usuario aprende un concepto nuevo. Evita miles de recorridos del léxico.
    if len(palabra)<5:
        return []
    indice=getattr(lex, '_composicion_morf', None)
    if indice is None or getattr(lex,'_composicion_n',-1)!=len(lex.items):
        indice={}
        finales=('amos', 'ais', 'an', 'as', 'a', 'es', 'e', 'en', 'o', 'emos', 'eis',
                 'imos', 'is', 'ado', 'ido', 'ando', 'iendo', 'ara', 'aras', 'aramos',
                 'aran', 'ase', 'ases', 'asemos', 'asen', 'iera', 'ieras', 'ieramos',
                 'ieran', 'iese', 'ieses', 'iesemos', 'iesen', 'aste', 'asteis',
                 'aron', 'iste', 'isteis', 'ieron', 'aba', 'abas', 'aban', 'abamos',
                 'ia', 'ias', 'ian', 'iamos', 'are', 'areis', 'eria', 'erias',
                 'erian', 'iria', 'irias', 'irian', 'ares', 'iere', 'ieren',
                 'ieres', 'ados', 'adas')
        for c in lex.items.values():
            lema=c['lema']
            if c['tipo']=='accion' and lema.endswith(('ar','er','ir')) and len(lema)>=5:
                for fin in finales:
                    forma=lema[:-2]+fin
                    if len(forma)>=5:
                        indice.setdefault(forma,[]).append(c)
        lex._composicion_morf=indice
        lex._composicion_n=len(lex.items)
    return indice.get(palabra,[])


def _negado(segmento, i):
    # Negación de la proposición o la solicitud completa: "No quiero que...",
    # "No me muestres...", "Sin pintar...". Contraste delimita alcance.
    anterior=segmento[:i]
    if any(w in CONTRASTE for w in anterior):
        anterior=anterior[max(k for k,w in enumerate(anterior) if w in CONTRASTE)+1:]
    return any(w in NEGADORES for w in anterior)


def _es_declarante(segmento, i):
    """Evitar confundir narraciones en 3a persona con órdenes."""
    if not segmento or i<1:
        return False
    # Pronombre + verbo, o artículo + sujeto + verbo al inicio.
    if segmento[0] in ('yo','tu','el','ella','ellos','ellas','nosotros','vosotros') and i<=2:
        return True
    if segmento[0] in DETERMINANTES and i<=4:
        if any(x in segmento[:i] for x in ('nino','nina','persona','hombre','mujer','senor','senora')):
            return True
    # Sujeto nominal libre + verbo finito al inicio (Ana dibuja...).
    # Un verbo en posición inicial suele ser un imperativo; una palabra no
    # gramatical antes del verbo sin marco directivo suele ser sujeto.
    if i==1 and segmento[0] not in MARCADORES_PETICION | CONTRASTE | {'me','te','nos','le','les','por','no','nunca','que'}:
        return True
    return False


def _es_pregunta_definicion(tt, lex):
    pares=list(zip(tt,tt[1:]))
    if ('que','es') in pares or ('que','significa') in pares:
        return True
    if 'significado' in tt and any(w in tt for w in ('explicar','explica','explicame','puedes','que')):
        return True
    if tt:
        # La petición se interpreta por el CONCEPTO DEFINIR, no por una tabla
        # de verbos que ejecutan funciones.
        primeras=_acciones_para(tt[0],lex)
        if any(c['id']=='accion.definir' for c in primeras):
            return True
    return False


def _hay_coordinacion_no_soportada(segments, elegida, lex):
    # Dos predicados en una misma solicitud sobre diferentes operaciones:
    # no ejecutar silenciosamente solo la mitad de la tarea.
    for seg_i,seg in enumerate(segments):
        for i,w in enumerate(seg):
            if w=='y' and i>0 and i<len(seg)-1:
                # ¿El siguiente elemento es un verbo distinto o va en su grupo
                # flexionado? Se comprueba léxico; no se asigna capacidad.
                for x in seg[i+1:i+4]:
                    acciones=_acciones_para(x,lex)
                    if acciones and any(a['id']!=elegida for a in acciones):
                        return True
    return False


def analizar(texto, lex, colores=(), modalidad='texto'):
    segmentos=_segmentos(texto)
    tt=[t for s in segmentos for t in s]
    marc=Marco(texto, modalidad, 'no_soportada', tuple(colores), tuple())
    if not segmentos:
        return marc
    if _es_pregunta_definicion(tt,lex):
        marc.clase='definicion';marc.razon='pregunta sobre significado, no generación'
        return marc
    if len(colores)>1:
        # Describir dos colores no es pedir una imagen. La decisión se hace
        # antes de interpretar la cantidad de argumentos como ambigüedad.
        if tt[0] in DETERMINANTES:
            marc.clase='declaracion';marc.razon='mención de varios colores'
        else:
            marc.clase='ambigua';marc.razon='varios colores posibles'
        return marc
    predicados=[]
    ix_global=0
    for si,seg in enumerate(segmentos):
        for i,w in enumerate(seg):
            # "una muestra": sustantivo, no el verbo mostrar.
            if i and seg[i-1] in DETERMINANTES and w not in ('muestra',):
                # Se deja pasar la revisión de verbos reales; el determinante
                # sirve como pista, no filtro absoluto.
                pass
            if i and seg[i-1] in DETERMINANTES and w=='muestra':
                continue
            opciones=_acciones_para(w,lex)
            for a in opciones:
                cache=getattr(lex,'_composicion_cap',None)
                if cache is None or getattr(lex,'_composicion_cap_n',-1)!=len(lex.items):
                    cache={}; lex._composicion_cap=cache; lex._composicion_cap_n=len(lex.items)
                if a['id'] not in cache:
                    cache[a['id']]=lex.relacionar_accion(a['id'])
                cv=cache[a['id']]
                neg=_negado(seg,i)
                # Una similitud coseno alta por rasgos generales (p. ej.
                # PREGUNTAR~MOSTRAR) no autoriza a ejecutar una capacidad.
                # Se requiere una compatibilidad semántica explícita.
                rasgos=a.get('rasgos',{})
                apta=('rasgo:visual' in rasgos or a.get('operacion') in ('crear','mostrar'))
                capacidad=(cv or {}).get('operacion') if apta else None
                predicados.append(Predicado(ix_global+i,w,a['id'],a['lema'],a['familia'],neg,si,
                                            capacidad, (cv or {}).get('similitudes',{})))
        ix_global+=len(seg)
    marc.predicados=tuple(predicados)
    if not predicados:
        marc.clase='ambigua' if colores else 'no_soportada'
        marc.razon='no se ha resuelto un predicado de acción'
        return marc
    candidatos=[p for p in predicados if p.capacidad in ('crear','mostrar') and not p.negado]
    # Verbo conocido en forma no imperativa tras un sujeto explícito.
    candidatos=[p for p in candidatos if not _es_declarante(segmentos[p.puntuacion],
                p.indice-sum(len(s) for s in segmentos[:p.puntuacion]))]
    if not candidatos:
        marc.clase='negacion' if any(p.negado and p.capacidad for p in predicados) else 'no_soportada'
        marc.razon='sin acción visual afirmativa'
        return marc
    # "Me pregunto si podrías dibujar..." y "Quiero que ...": el acto
    # ejecutable es el subordinado, no el verbo modal o de soporte.
    # Bajo contraste, la última cláusula afirmativa determina el acto pedido.
    afirmativos=[p for p in candidatos if p.forma not in ('hazme','haga')]
    if afirmativos: candidatos=afirmativos
    candidato=candidatos[-1] if any(w in ('solo','solamente','pero','sino') for w in tt) else candidatos[0]
    seg=segmentos[candidato.puntuacion]
    local=candidato.indice-sum(len(s) for s in segmentos[:candidato.puntuacion])
    entrada=tt[:candidato.indice]
    # Forma narrativa futura en primera persona ("Te mostraré...") no
    # equivale a orden. Distinción morfológica, no semántica del verbo.
    if candidato.forma.endswith(('are','ere','ire')) and entrada and entrada[0] in ('te','le','les'):
        marc.clase='declaracion';marc.razon='futuro declarativo'
        return marc
    peticion = (local<=1 or any(x in MARCADORES_PETICION for x in entrada)
                or 'favor' in tt or (tt and tt[0] in ('me','te') and '?' in texto))
    if not peticion:
        marc.clase='declaracion';marc.razon='no hay acto directivo verificable'
        return marc
    if _hay_coordinacion_no_soportada(segmentos, candidato.concepto, lex):
        marc.clase='no_soportada';marc.razon='tarea compuesta que requiere más capacidades'
        return marc
    # Limitar SOLO el actuador de la muestra cromática; no confundir saber
    # qué significa 'matiz' con tener implementada síntesis de gradientes.
    if any(w in tt for w in ('matices','matiz','degradado','degradados','gradiente','gradientes')):
        marc.clase='no_soportada';marc.razon='representación de matices no implementada'
        return marc
    if len(candidatos)>1 and not any(x in CONTRASTE for x in tt):
        # Dos capacidades distintas en una misma solicitud: no adivinar cuál.
        if len({p.capacidad for p in candidatos})>1:
            marc.clase='ambigua';marc.razon='acciones visuales concurrentes'
            return marc
    marc.accion=candidato.concepto;marc.capacidad=candidato.capacidad
    if not colores:
        marc.clase='no_soportada';marc.razon='la operación visual necesita un color conocido'
        return marc
    marc.clase='peticion';marc.razon='accion conceptual y argumento visual resueltos'
    return marc
