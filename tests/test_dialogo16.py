"""Regresión de relaciones, condiciones, evidencia y turnos para LCM 1.6."""
import json
from pathlib import Path
import pytest
from src.memory.store import MemoryStore
from src.semantics.dialogue16 import DialogoConceptual, Prop


@pytest.fixture
def contexto(tmp_path):
    m=MemoryStore(str(tmp_path/'mem.json'))
    return DialogoConceptual(m, ruta=tmp_path/'reglas.json')


def test_aprender_hecho_generico(contexto):
    assert 'registrado' in contexto.procesar('Ana acompaña a Luis.')
    assert any(f['s']=='ANA' and f['p']=='ACOMPANAR' and f['o']=='LUIS' for f in contexto.mem.facts)


def test_direccionalidad(contexto):
    contexto.procesar('Ana acompaña a Luis.')
    assert 'Luis' in contexto.procesar('¿A quién acompaña Ana?')
    assert 'no consta' in contexto.procesar('¿A quién acompaña Luis?').lower()


def test_pregunta_quien_sujeto(contexto):
    contexto.procesar('Ana acompaña a Luis.')
    assert 'Ana' in contexto.procesar('¿Quién acompaña a Luis?')


def test_referencia_tercera_persona(contexto):
    contexto.procesar('Ana visita a Luis.')
    assert 'Luis' in contexto.procesar('¿A quién visita ella?')
    assert 'Ana' in contexto.procesar('¿A quién visita él?') or 'no consta' in contexto.procesar('¿A quién visita él?').lower()


def test_referencia_ambigua(contexto):
    contexto.procesar('Ana visita a Carla.')
    assert 'te refieres' in contexto.procesar('¿A quién visita ella?').lower()


def test_regla_condicional(contexto):
    assert 'aprendido' in contexto.procesar('Si X ayuda a Y, entonces Y saluda a X.')
    contexto.procesar('Ana ayuda a Luis.')
    ans=contexto.procesar('¿A quién saluda Luis?')
    assert 'Ana' in ans and 'regla' in ans
    assert 'si x ayuda' in contexto.procesar('¿Por qué?').lower()


def test_premisa_con_dos_variables(contexto):
    contexto.procesar('Si X ayuda a Y y Y saluda a Z, entonces X admira a Z.')
    contexto.procesar('Ana ayuda a Luis.')
    contexto.procesar('Luis saluda a Eva.')
    assert 'Eva' in contexto.procesar('¿A quién admira Ana?')


def test_no_variable_en_conclusion_sin_premisa(contexto):
    ans=contexto.procesar('Si X ayuda a Y, entonces Z saluda a X.')
    assert 'no puedo' in ans.lower()
    assert contexto.reglas==[]


def test_no_inferencia_de_premisas_faltantes(contexto):
    contexto.procesar('Si X ayuda a Y y Y saluda a Z, entonces X admira a Z.')
    contexto.procesar('Ana ayuda a Luis.')
    assert 'no consta' in contexto.procesar('¿A quién admira Ana?').lower()


def test_negacion_no_equivale_desconocimiento(contexto):
    contexto.procesar('Ana no acompaña a Luis.')
    assert 'no:' in contexto.procesar('¿Acompaña Ana a Luis?').lower()
    assert 'no consta' in contexto.procesar('¿Acompaña Ana a Eva?').lower()


def test_regla_negativa_requiere_evidencia_negativa(contexto):
    contexto.procesar('Si X no ayuda a Y, entonces Y saluda a X.')
    assert 'no consta' in contexto.procesar('¿A quién saluda Luis?').lower()
    contexto.procesar('Ana no ayuda a Luis.')
    assert 'Ana' in contexto.procesar('¿A quién saluda Luis?')


def test_contradiccion_inhibe_cierre(contexto):
    contexto.procesar('Si X ayuda a Y, entonces Y saluda a X.')
    contexto.procesar('Ana ayuda a Luis.')
    contexto.procesar('Ana no ayuda a Luis.')
    assert 'no consta' in contexto.procesar('¿A quién saluda Luis?').lower()
    assert 'incompatibles' in contexto.procesar('¿Ayuda Ana a Luis?')


def test_provisional_no_es_hecho(contexto):
    contexto.procesar('Si X ayuda a Y, entonces Y saluda a X.')
    assert 'Ana' in contexto.procesar('Si Ana ayuda a Luis, ¿a quién saluda Luis?')
    assert 'no consta' in contexto.procesar('¿A quién saluda Luis?').lower()
    assert contexto.mem.facts==[]


def test_si_sin_entonces_no_es_hecho(contexto):
    assert 'condición' in contexto.procesar('Si Ana visita a Luis.').lower()
    assert contexto.mem.facts==[]


def test_atribucion_no_es_hecho(contexto):
    assert 'no lo tomaré' in contexto.procesar('Ana cree que Luis ayuda a Carla.')
    assert 'no consta' in contexto.procesar('¿A quién ayuda Luis?').lower()
    assert contexto.mem.facts==[]
    assert len(contexto.atribuciones)==1


@pytest.mark.parametrize('texto', ['Quizá Ana ayuda a Carla.','Ana puede visitar a Luis.',
                                    'Ana dice que Luis visita a Eva.','No sé si Ana ayuda a Luis.'])
def test_posibilidades_no_se_memorizan(contexto,texto):
    contexto.procesar(texto)
    assert contexto.mem.facts==[]


def test_forma_perifrastica(contexto):
    contexto.procesar('Manuel acompaña a Carla.')
    assert 'Carla' in contexto.procesar('¿A quién está acompañando Manuel?')
    assert 'no consta' in contexto.procesar('¿Carla a quién está acompañando?').lower()


def test_memoria_reinicio(tmp_path):
    ruta=tmp_path/'mem.json'; reglas=tmp_path/'reglas.json'
    m=MemoryStore(str(ruta)); d=DialogoConceptual(m,ruta=reglas)
    d.procesar('Si X ayuda a Y, entonces Y saluda a X.')
    d.procesar('Ana ayuda a Luis.')
    m2=MemoryStore(str(ruta));d2=DialogoConceptual(m2,ruta=reglas)
    assert 'Ana' in d2.procesar('¿A quién saluda Luis?')


def test_regla_sin_duplicados(contexto):
    for _ in range(5):contexto.procesar('Si X ayuda a Y, entonces Y saluda a X.')
    assert len(contexto.reglas)==1


def test_edad_nacimiento_ruta_memory(contexto):
    contexto.procesar('María nació en 1982.')
    assert any(f['s']=='MARIA' and f['p']=='NACER' and f['source'].startswith('María nació') for f in contexto.mem.facts)
    assert any('1982' in f.get('when','') for f in contexto.mem.facts)


def test_no_inferir_relaciones_por_similitud(contexto):
    contexto.procesar('Ana ayuda a Luis.')
    assert 'no consta' in contexto.procesar('¿A quién admira Ana?').lower()


def test_no_invertir_hipotesis(contexto):
    ans=contexto.procesar('Si Manuel acompaña a Carla, Carla a quién está acompañando?')
    assert 'no consta' in ans.lower()
    assert contexto.mem.facts==[]


def test_pregunta_factual_fuera_de_ambito(contexto):
    assert contexto.procesar('¿Qué es el concepto de verde?') is None
    assert contexto.procesar('¿Qué hora es?') is None


def test_escuela_prioritaria_si_devuelve_roles(tmp_path):
    class Escuela:
        def parse(self,texto):
            return [{'s':'Rosa','p':'confiar_en','o':'Mario','neg':False}]
    m=MemoryStore(str(tmp_path/'mem.json'))
    d=DialogoConceptual(m,Escuela(),tmp_path/'r.json')
    assert 'registrado' in d.procesar('Rosa confía en Mario.')
    assert any(f['p']=='CONFIAR_EN' for f in m.facts)


def test_invalidez_de_memoria_reglas_no_se_sobrescribe(tmp_path):
    p=tmp_path/'reglas.json';p.write_text('{"schema":"desconocido"}')
    with pytest.raises(ValueError):DialogoConceptual(MemoryStore(str(tmp_path/'m.json')),ruta=p)
    assert 'desconocido' in p.read_text()


def test_condicion_dos_premisas_orden_independiente(contexto):
    contexto.procesar('Si X ayuda a Y y Y saluda a Z, entonces X admira a Z.')
    contexto.procesar('Luis saluda a Eva.')
    contexto.procesar('Ana ayuda a Luis.')
    assert 'Eva' in contexto.procesar('¿A quién admira Ana?')


def test_ciclo_acotado(contexto):
    contexto.procesar('Si X ayuda a Y, entonces Y ayuda a X.')
    contexto.procesar('Ana ayuda a Luis.')
    assert 'Ana' in contexto.procesar('¿A quién ayuda Luis?')


def test_examen_seed_diferente(tmp_path):
    # Prueba rápida de 20 tandas generadas (el banco completo está en scripts/).
    from scripts.evaluar_dialogo16 import ejecutar
    a=ejecutar(n=200,semilla=884839,salida=tmp_path/'eval.json')
    assert a['tandas_aprobadas']==20 and a['minimo_tanda']>=9


def test_motor_real_chat_sin_checkpoint(tmp_path):
    from src.web.motor import Motor
    class ParserMinimo:
        def parse(self, *args, **kwargs):return []
    mem=MemoryStore(str(tmp_path/'memory.json'))
    motor=Motor(mem,ParserMinimo(),carpeta_cartuchos=str(tmp_path/'c'))
    for texto in ('Si X ayuda a Y, entonces Y saluda a X.', 'Ana ayuda a Luis.'):
        assert 'respuesta' in motor.chat(texto)
    res=motor.chat('¿A quién saluda Luis?')
    assert 'Ana' in res['respuesta'] and res['composicion16']['modulo']=='alcance_y_reglas'


def test_no_guardar_imperativo_audio(contexto):
    assert contexto.procesar('Escucha esta grabación.') is None
    assert contexto.mem.facts==[]


def test_no_guardar_peticion_mostrar(contexto):
    assert contexto.procesar('Muestra este dibujo.') is None
    assert contexto.mem.facts==[]


def test_parser_no_puede_inventar_otra_persona(tmp_path):
    class EscuelaErrada:
        def parse(self,texto):
            return [{'s':'Lamine','p':'ayudar','o':'Luis','neg':False}]
    m=MemoryStore(str(tmp_path/'memoria.json'))
    d=DialogoConceptual(m,EscuelaErrada(),tmp_path/'r.json')
    d.procesar('Ana ayuda a Luis.')
    assert any(f['s']=='ANA' and f['o']=='LUIS' for f in m.facts)
    assert all(f['s']!='LAMINE' for f in m.facts)
