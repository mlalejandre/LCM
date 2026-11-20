"""LCM 1.5: grounding de respuestas y edades a partir de HECHOS, no de texto recuperado.

Es una capa de validacion y ejecucion sobre operaciones conceptuales ya interpretadas;
no agrega un clasificador de verbos ni altera embeddings. Diseñada para abstenerse
cuando una fuente no es pertinente o una fecha esta incompleta/conflictiva.
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass


def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s).casefold()) if unicodedata.category(c) != 'Mn')


def palabras(s):
    return re.findall(r'[a-zñ0-9]+', norm(s))


# Palabras funcionales y genéricas: no se consideran evidencia de coincidencia.
VACIAS = frozenset('''a al algo algun alguna algunos algunas ante ahora con cual cuales cuando cuanto cuanta cuantos cuantas
como de del desde donde el ella ellos ellas en entre era es esa ese esas esos esto esta estas estos fue ha hay he la las le les lo los
mas me mi mis no nos o para pero por porfavor porque que quien quienes se ser si sin sobre son su sus te tiene tienen tu tus
un una uno unos unas y ya dame dime sabes puedes podria podrias me gustaria favor quiero quisiera decir explicame
hoy ayer manana dia dias ano anos fecha hora minutos momento actual actualmente nombre dato informacion texto segun'''.split())

NOMBRES_NO = frozenset('''Que Como Cual Cuanto Cuantos Cuantas Donde Cuando Dime Me Puedes Podrias Si Por Ahora Esta Un Una
No Sabes Quiero Quisiera Explicame En La El Es Las Los Se Son Ayer Hoy Cuál Cuántos Qué'''.split())


def _nombres_pregunta(s):
    # No se extraen nombres de todas las mayúsculas: solo antropónimos que no son
    # inicio de oración o palabras de cortesía. Usados para verificar evidencia, no NER.
    ps = re.findall(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+', s)
    return {norm(w) for i,w in enumerate(ps) if w[:1].isupper() and w not in NOMBRES_NO
            and (i > 0 or w.isupper()) and norm(w) not in VACIAS}


def _nombres_mencionados_en_respuesta(t, nombres):
    toks = set(palabras(t))
    return nombres <= toks


def tokens_documento(mem, respuesta):
    """Palabras del DOCUMENTO leído al que pertenece cada frase citada («...»).

    Un texto habla de su tema con pronombres y sujetos omitidos («Fue construida...»,
    «Murió en Madrid...»): la entidad consultada debe constar en el documento de la
    cita, no necesariamente en la frase citada. Sin registro del documento -> vacío.
    """
    textos = getattr(mem, 'textos', None) or []
    if not textos or not isinstance(respuesta, str):
        return set()
    citas = {c.strip() for c in re.findall(r'«([^»]+)»', respuesta)}
    if not citas:
        return set()
    docs = {(t.get('d'),) for t in textos if t.get('t', '').strip() in citas}
    toks = set()
    for t in textos:
        if (t.get('d'),) in docs:
            toks.update(palabras(t.get('t', '')))
    return toks


def pertinencia(texto, respuesta, mem=None):
    """(aceptable, motivo) para citas externas.

    Una respuesta sin afirmación externa se deja intacta. Al no haber una
    prueba de alineación, se ABSTIENE, jamás sustituye con otra fuente.
    """
    if not isinstance(respuesta, str):
        return True, 'salida no textual'
    r = norm(respuesta)
    # No tocar respuestas ordinarias ni explicaciones legítimas sin cita.
    if not ('en el texto' in r or 'segun el texto' in r or 'en este documento' in r):
        return True, 'sin recuperación externa'
    nombres = _nombres_pregunta(texto)
    doc = tokens_documento(mem, respuesta)
    visibles = set(palabras(respuesta)) | doc
    # Refutación («No. Según el texto, está en Perú»): el nombre refutado no se repite.
    refuta = norm(respuesta).lstrip().startswith('no') and bool(nombres & visibles) and palabras(respuesta)[:1] == ['no']
    if refuta:
        return True, 'refutación anclada en el documento citado'
    if nombres and not (nombres <= visibles):
        return False, 'la respuesta externa no menciona las entidades consultadas'
    informativas = set(palabras(texto)) - VACIAS
    # Excluir nombres del cálculo de solapamiento, pues ya se verificaron.
    informativas -= nombres
    if nombres and doc and nombres <= doc:
        # La entidad consta en el documento de la cita (correferencia del texto): la
        # paráfrasis de la pregunta («a qué se dedicaba») no tiene por qué repetirse.
        return True, 'entidad consultada presente en el documento citado'
    if len(informativas) >= 2:
        sol = informativas & (set(palabras(respuesta)) | doc)
        if not sol:
            return False, 'la cita no comparte información específica con la consulta'
    return True, 'evidencia superficialmente pertinente (no verificación de verdad)'


def post_respuesta(texto, respuesta, mem=None):
    ok, por_que = pertinencia(texto, respuesta, mem)
    if ok:
        return respuesta
    return ('No tengo información suficientemente relacionada con tu pregunta para responder con seguridad. '
            'La coincidencia recuperada trataba de otra cosa.')


def _persona_edad(texto):
    """Identifica el referente de una pregunta de edad; no interpreta el verbo libre.

    Solo la operación de EDAD activa el calculador. Se evita la resolución
    por posición en el texto que contaminaba María con Lamine Yamal.
    """
    s = norm(texto)
    # Ninguna inferencia de identidad a partir de un nombre distinto.
    if not (('edad' in s or 'anos' in s) and ('?' in texto or '¿' in texto or s.startswith(('dime ', 'calculame ')))):
        return None
    if not any(x in s for x in ('cuantos anos tiene', 'cuantos anos cumple', 'que edad tiene',
                               'dime cuantos anos tiene', 'calcula la edad de', 'que edad tendria')):
        return None
    words = re.findall(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+', texto)
    nombres = [w for w in words if w[:1].isupper() and w not in NOMBRES_NO]
    if len(set(map(norm,nombres))) == 1:
        return norm(nombres[0]).upper()
    return None


def _fechas_nacimiento(mem, sujeto):
    """Leer únicamente NACER positivo sobre el sujeto: hecho memorizado con provenance.

    Una afirmación sobre OTRA persona, aunque venga de un texto muy parecido,
    nunca aporta una fecha a este sujeto.
    """
    fechas=[]
    for f in getattr(mem,'facts',[]):
        if (norm(f.get('s','')).upper() != sujeto or norm(f.get('p','')).upper() not in ('NACER', 'NACIMIENTO')
                or f.get('neg') or f.get('archived')):
            continue
        iv=f.get('when_abs')
        if isinstance(iv,str) and '/' in iv:
            try:
                a,b=iv.split('/',1)
                fechas.append((dt.date.fromisoformat(a),dt.date.fromisoformat(b),'hecho fechado'))
                continue
            except (ValueError,TypeError):
                pass
        # Solo como respaldo cuando el hecho NACER existe y la FUENTE indica año.
        fuente=norm(f.get('source',''))
        m=re.search(r'\bnaci[o]?\s+en\s+((?:18|19|20)\d{2})\b',fuente)
        if m:
            y=int(m.group(1));fechas.append((dt.date(y,1,1),dt.date(y,12,31),'fuente del hecho'))
    return fechas


def edad_hecho(texto, mem, hoy=None):
    """Respuesta o None. 0 hechos => delega al conversador (no inventa un nacimiento)."""
    if mem is None:return None
    sujeto=_persona_edad(texto)
    if not sujeto:return None
    hoy=hoy or getattr(mem,'today',None) or dt.date.today()
    if isinstance(hoy,dt.datetime):hoy=hoy.date()
    fechas=_fechas_nacimiento(mem,sujeto)
    if not fechas:return None
    pares={(a,b) for a,b,_ in fechas}
    if len(pares)>1:
        # Distintas fuentes de fechas compatibles pueden mezclarse si el
        # intervalo exacto está incluido en el aproximado; pero si no, abstenerse.
        as_=[x[0] for x in pares];bs_=[x[1] for x in pares]
        a=max(as_); b=min(bs_)
        if a>b:
            return f'Conozco fechas de nacimiento incompatibles para {sujeto.title()}. Necesito confirmar cuál es correcta.'
    else:a,b=next(iter(pares))
    if a>hoy:
        return f'La fecha de nacimiento de {sujeto.title()} está en el futuro respecto de hoy; necesito verificarla.'
    def edad_en(fecha):
        return hoy.year-fecha.year-((hoy.month,hoy.day)<(fecha.month,fecha.day))
    mayor=edad_en(a);menor=edad_en(b)
    if menor==mayor:
        return f'{sujeto.title()} tiene {menor} años según el hecho de nacimiento guardado.'
    return (f'{sujeto.title()} tiene entre {menor} y {mayor} años. '
            'Sin el día y mes de nacimiento no puedo precisar más.')


def pre_respuesta(texto, mem=None):
    return edad_hecho(texto,mem)

# No hay una intención lexical de «dibujar» para esta operación: se reconoce
# primero el concepto matemático RAÍZ_CUADRADA y se pasa su argumento al
# calculador determinista. No se confunde una afirmación con una pregunta.
_RAIZ_CUADRADA = re.compile(r'\braiz\s+cuadrada\s+de\s+(?:el\s+numero\s+)?(?P<n>-?\d+)\b')


def operacion_matematica(texto):
    if '¿' not in texto and '?' not in texto:
        return None
    s=norm(texto)
    if 'no calcules' in s or 'no resuelvas' in s:
        return None
    m=_RAIZ_CUADRADA.search(s)
    if not m:return None
    # Rechazar oraciones donde la raíz cuadrada sea una premisa para otra tarea.
    posterior=s[m.end():].strip(' ?!.')
    if posterior and posterior not in ('ahora','por favor','exactamente'):
        return None
    n=int(m.group('n'))
    if len(m.group('n'))>12:return 'El número es demasiado grande para esta operación interactiva.'
    if n<0:return 'No tiene raíz cuadrada real. Puedo calcular raíces complejas si se implementa esa capacidad.'
    from math import isqrt
    raiz=isqrt(n)
    if raiz*raiz==n:
        return f'La raíz cuadrada de {n} es {raiz}.'
    return f'La raíz cuadrada de {n} está entre {raiz} y {raiz+1}; no es un entero.'


# Resolver primero la operación matemática si fue solicitada; después la
# consulta de edad almacenada. El cálculo no utiliza datos de textos leídos.
def pre_respuesta(texto, mem=None):
    r=operacion_matematica(texto)
    return r if r is not None else edad_hecho(texto,mem)


def confirmacion_negacion_visual(texto, lex):
    """Reconoce una petición visual negada mediante el MISMO compositor del LCM.

    No modifica el contrato de PuenteSemantico.responder (históricamente None
    en negaciones), no introduce sinónimos de acciones ni registra un hecho.
    """
    from src.semantics.composition import analizar
    from src.semantics.bridge import color_en
    from src.semantics.lexicon import normalizar
    colores=color_en(texto)
    if not colores:return None
    marco=analizar(texto,lex,colores)
    if (marco.clase=='negacion' and marco.predicados
            and any(p.negado and p.concepto.startswith('accion.') for p in marco.predicados)
            and not normalizar(texto).startswith('no se si ')):
        return 'Entendido. No generaré una imagen para esa instrucción.'
    return None
