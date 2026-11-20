"""Verificación de alcance, evidencias, composición y no-contaminación 1.7."""
import json
from datetime import date

import pytest

from src.memory.store import MemoryStore
from src.semantics.dialogue16 import DialogoConceptual
from src.semantics.discourse17 import Discurso17


@pytest.fixture
def entorno(tmp_path):
    memoria=MemoryStore(str(tmp_path/'mem.json'))
    memoria.today=date(2026,11,18)
    base=DialogoConceptual(memoria,ruta=tmp_path/'rules.json')
    return Discurso17(base,ruta=tmp_path/'discourse.json')


def test_conjuncion_sujetos_explicitados(entorno):
    assert 'dos proposiciones' in entorno.procesar('Ana ayuda a Luis y Luis saluda a Eva.')
    assert {(f['s'],f['p'],f['o']) for f in entorno.nucleo.mem.facts}=={
        ('ANA','AYUDAR','LUIS'),('LUIS','SALUDAR','EVA')}


def test_conjuncion_elipsis_sujeto(entorno):
    entorno.procesar('Ana ayuda a Luis y saluda a Eva.')
    assert {(f['s'],f['p'],f['o']) for f in entorno.nucleo.mem.facts}=={
        ('ANA','AYUDAR','LUIS'),('ANA','SALUDAR','EVA')}


def test_conjuncion_se_analiza_antes_de_persistir(entorno):
    assert 'no he guardado' in entorno.procesar('Ana ayuda a Luis y saluda al que llegó.').lower()
    assert entorno.nucleo.mem.facts==[]


def test_relativa_interpretable(entorno):
    assert 'relativa' in entorno.procesar('Ana, que vive en Sevilla, ayuda a Luis.').lower()
    assert {(f['s'],f['p'],f['o']) for f in entorno.nucleo.mem.facts}=={
        ('ANA','VIVIR_EN','SEVILLA'),('ANA','AYUDAR','LUIS')}


def test_relativa_sin_roles_no_se_aprende(entorno):
    assert 'no he guardado' in entorno.procesar('Ana, que piensa que Carla le escribió, ayuda a Luis.').lower()
    assert entorno.nucleo.mem.facts==[]


def test_evento_ayer_ni_es_verdad_ahora_ni_premisa(entorno):
    ans=entorno.procesar('Ayer Ana visitó a Luis.')
    assert 'fechado' in ans
    assert entorno.nucleo.mem.facts==[]
    assert 'Luis' in entorno.procesar('¿A quién visitó Ana ayer?')
    assert 'no consta' in entorno.nucleo.procesar('¿A quién visita Ana?').lower()


def test_no_asignar_fecha_incorrecta(entorno):
    entorno.procesar('Ayer Ana visitó a Luis.')
    assert 'no consta' in entorno.procesar('¿A quién visitó Ana hoy?').lower()


def test_tiempo_relativo_anclado_a_fecha(entorno):
    entorno.procesar('Ayer Ana visitó a Luis.')
    assert entorno.eventos[0]['tiempo']=='2026-11-17'


def test_negacion_y_conflicto_mismo_dia(entorno):
    entorno.procesar('Hoy Ana visita a Luis.')
    entorno.procesar('Hoy Ana no visita a Luis.')
    assert 'incompatibles' in entorno.procesar('¿Visita Ana a Luis hoy?').lower()


def test_negacion_fechada_no_invalida_otra_fecha(entorno):
    entorno.procesar('Ayer Ana no visita a Luis.')
    entorno.procesar('Hoy Ana visita a Luis.')
    assert 'Sí' in entorno.procesar('¿Visita Ana a Luis hoy?')
    assert 'No,' in entorno.procesar('¿Visita Ana a Luis ayer?')


def test_estado_cambia_sin_contradiccion(entorno):
    assert 'anterior' in entorno.procesar('Antes Ana vivía en Madrid, ahora vive en Sevilla.')
    assert 'Madrid' in entorno.procesar('¿Dónde vive Ana antes?')
    assert 'Sevilla' in entorno.procesar('¿Dónde vive Ana ahora?')
    assert entorno.nucleo.mem.facts==[]


def test_cambio_otros_sujetos_rechazado(entorno):
    assert 'no he registrado' in entorno.procesar('Antes Ana vivía en Madrid, ahora Carla vive en Sevilla.').lower()
    assert entorno.eventos==[]


def test_segun_no_es_verdad(entorno):
    r=entorno.procesar('Según Ana, Luis ayuda a Eva.')
    assert 'atribuida' in r
    assert not entorno.nucleo.mem.facts
    assert entorno.nucleo.atribuciones[0]['hablante']=='ANA'


@pytest.mark.parametrize('texto',[
    'Parece que Ana ayuda a Luis.', 'Me parece que Ana visita a Carla.',
    'Se rumorea que Ana visita a Luis.', 'Quizá Ana ayuda a Luis y saluda a Carla.',
    'Si Ana ayuda a Luis, Luis saluda a Eva.',
])
def test_no_almacenar_modal_o_condicional(entorno,texto):
    r=entorno.procesar(texto)
    assert entorno.nucleo.mem.facts==[]


def test_episodios_reinicio(tmp_path):
    ruta=tmp_path/'m.json'; er=tmp_path/'d.json'; br=tmp_path/'b.json'
    m=MemoryStore(str(ruta));m.today=date(2026,11,18)
    d=Discurso17(DialogoConceptual(m,ruta=br),ruta=er)
    d.procesar('Ayer Ana visitó a Luis.')
    otra=Discurso17(DialogoConceptual(MemoryStore(str(ruta)),ruta=br),ruta=er)
    otra.nucleo.mem.today=date(2026,11,18)
    assert 'Luis' in otra.procesar('¿A quién visitó Ana ayer?')


def test_memoria_desconocida_no_se_sobrescribe(tmp_path):
    p=tmp_path/'d.json';p.write_text('{"schema":"desconocida","eventos":[]}')
    d=DialogoConceptual(MemoryStore(str(tmp_path/'m.json')),ruta=tmp_path/'r.json')
    with pytest.raises(ValueError):Discurso17(d,p)
    assert 'desconocida' in p.read_text()


def test_motor_real(tmp_path):
    from src.web.motor import Motor
    class Stub:
        def parse(self,*a,**kw):return []
    m=MemoryStore(str(tmp_path/'mem.json'));m.today=date(2026,11,18)
    motor=Motor(m,Stub(),carpeta_cartuchos=str(tmp_path/'cartuchos'))
    assert 'dos proposiciones' in motor.chat('Ana ayuda a Luis y Luis saluda a Eva.')['respuesta']
    assert 'Eva' in motor.chat('¿A quién saluda Luis?')['respuesta']
    assert 'fechado' in motor.chat('Ayer Ana visitó a Luis.')['respuesta']
    assert 'Luis' in motor.chat('¿A quién visitó Ana ayer?')['respuesta']
    assert 'Hoy' not in motor.chat('¿A quién visitó Ana hoy?')['respuesta']


def test_no_interferir_flujo_normal(entorno):
    assert entorno.procesar('Si X ayuda a Y, entonces Y saluda a X.') is None
    assert entorno.procesar('¿Qué es un color?') is None
    assert entorno.procesar('Ana ayuda a Luis.') is None


def test_pronombre_clitico_con_referente_unico(entorno):
    assert 'registrado' in entorno.nucleo.procesar('Ana ayuda a Luis.')
    assert 'pronombre' in entorno.procesar('Ella lo saluda.').lower()
    assert 'Luis' in entorno.nucleo.procesar('¿A quién saluda Ana?')


def test_pronombre_clitico_ambiguo_no_se_guarda(entorno):
    entorno.nucleo.procesar('Ana acompaña a Carla.')
    n=len(entorno.nucleo.mem.facts)
    assert 'antecedente' in entorno.procesar('Ella la saluda.').lower() or 'inequívoca' in entorno.procesar('Ella la saluda.').lower()
    assert len(entorno.nucleo.mem.facts)==n


def test_pronombre_sin_contexto_no_se_guarda(entorno):
    assert 'antecedente' in entorno.procesar('Ella lo saluda.').lower()
    assert entorno.nucleo.mem.facts==[]


def test_enunciado_de_especie_es_mencion_no_tipo(entorno):
    assert 'acontecimiento' in entorno.procesar('Un pájaro está piando en el jardín.')
    assert not entorno.nucleo.mem.facts
    assert entorno.eventos[0]['s'].startswith('MENCION_')
    assert entorno.eventos[0]['p']=='PIAR_EN'
    assert entorno.eventos[0]['o']=='JARDIN'


def test_negacion_progresiva_no_es_hecho_universal(entorno):
    assert 'acontecimiento' in entorno.procesar('Ese pájaro no está piando.')
    assert entorno.eventos[0]['neg'] is True
    assert entorno.nucleo.mem.facts==[]


def test_imperfecto_ayer_intransitivo(entorno):
    assert 'fechado' in entorno.procesar('El pájaro piaba ayer.')
    assert entorno.eventos[0]['p']=='PIAR'
    assert entorno.eventos[0]['tiempo']=='2026-11-17'
    assert entorno.nucleo.mem.facts==[]


def test_ladro_ayer_negado(entorno):
    assert 'fechado' in entorno.procesar('El perro no ladró ayer.')
    assert entorno.eventos[0]['p']=='LADRAR'
    assert entorno.eventos[0]['neg']


def test_especie_potencial_no_evento(entorno):
    assert entorno.procesar('Un pájaro puede piar.') is None
    assert entorno.eventos==[]


def test_regla_dos_premisas_tras_frase_coordinada(entorno):
    assert 'aprendido' in entorno.nucleo.procesar('Si X ayuda a Y y Y saluda a Z, entonces X admira a Z.')
    assert 'dos proposiciones' in entorno.procesar('Ana ayuda a Luis y Luis saluda a Eva.')
    assert 'Eva' in entorno.nucleo.procesar('¿A quién admira Ana?')


def test_evento_fechado_no_activa_condicional_atemporal(entorno):
    entorno.nucleo.procesar('Si X visita a Y, entonces Y saluda a X.')
    entorno.procesar('Ayer Ana visitó a Luis.')
    assert 'no consta' in entorno.nucleo.procesar('¿A quién saluda Luis?').lower()


def test_nueva_conversacion_no_recicla_referente(tmp_path):
    from src.web.motor import Motor
    class Escuela:
        def parse(self,*a,**kw):return []
    m=MemoryStore(str(tmp_path/'m.json'))
    motor=Motor(m,Escuela(),carpeta_cartuchos=str(tmp_path/'cartuchos'))
    motor.chat('Ana ayuda a Luis.')
    motor.nueva_conversacion()
    antes=len(m.facts)
    r=motor.chat('Ella lo saluda.')['respuesta'].lower()
    assert 'antecedente' in r or 'a quién' in r
    assert len(m.facts)==antes
