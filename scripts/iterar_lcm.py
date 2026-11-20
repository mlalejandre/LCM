"""Banco incremental LCM: tandas de 10 + regresión + reparaciones PREAPROBADAS.

Ejemplo: python -m scripts.iterar_lcm --n 2000 --autorreparar
Sin Escuela entrenada se detiene, salvo --sin-escuela (SOLO prueba técnica).
Todas las conversaciones se ejecutan en memoria efímera; nunca escribe la memoria personal.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import random
import re
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from src.quality.grounding import FLAGS, config, normalizar

REPORT = Path('reports/lcm_iteracion14')
COLORS = ('verde', 'rojo', 'azul', 'amarillo', 'blanco', 'negro')
NAMES = ('María', 'Ana', 'Laura', 'Carlos', 'Pedro', 'Luis', 'Rosa', 'Marta', 'Elena', 'David', 'Clara', 'Javier', 'Raúl', 'Miriam')


def caso(i, tag, pregunta, tipo, esperado=None, contexto=None):
    return {'id': f'Q{i:05d}', 'familia': tag, 'pregunta': pregunta, 'tipo': tipo, 'esperado': esperado, 'contexto': contexto or []}


def generar(n, semilla=20261118):
    """Banco de tareas reproducibles y parametrizadas, no diálogo humano irrestricto.

    Se mezclan memoria multi-turno, inferencias limitadas, visión, aritmética,
    conocimiento y casos adversarios. No se ajusta el banco a las respuestas.
    """
    h=dt.date.today().year
    base=[
      ('saludo','hola','contiene','hola',[]),
      ('concepto','¿Qué es un pájaro?','contiene','ave',[]),
      ('reloj','¿Qué hora es ahora?','reloj',None,[]),
      ('reloj','¿Sabes qué hora es?','reloj',None,[]),
      ('reloj','¿Me puedes decir qué hora es?','reloj',None,[]),
      ('hipotesis','Si María nació en 1982, ¿cuántos años tiene ahora María?','intervalo',f'{h-1982-1},{h-1982}',[]),
      ('concepto','¿Qué es el color verde?','contiene','tonalidad',[]),
      ('vision','Muéstrame el color verde','imagen','VERDE',[]),
      ('matematicas','¿Sabes calcular la raíz cuadrada de 9?','numero','3',[]),
      ('edad_memoria','¿Cuántos años tiene María?','intervalo',f'{h-1982-1},{h-1982}',['María nació en 1982.']),
      ('comparacion','¿Qué es más fuerte, un león o un unicornio?','abstencion',None,[]),
      ('relacion_dirigida','Si Manuel acompaña a Carla, ¿a quién está acompañando Carla?','abstencion',None,[]),
    ]
    out=[caso(i+1,*data) for i,data in enumerate(base[:n])]
    rng=random.Random(semilla)
    ciudades=('Toledo','Granada','Burgos','Vigo','Cuenca','León','Zamora','Lugo','Bilbao','Oviedo','Sevilla','Salamanca')
    objetos=('pan','queso','arroz','leche','naranjas','flores','café','manzanas','libros','té','lápices','peras')
    animales=('león','unicornio','lobo','dragón','perro','gato','caballo','grifo','tigre','sirena','oso','elefante')
    plantillas_vision=(
      'Muéstrame el color {c}', 'Enséñame un ejemplo del color {c}',
      'Pinta el color {c}', 'Dibuja una muestra del color {c}',
      'Diseña un cuadro del color {c}', 'Quiero que generes una imagen {c}',
      '¿Podrías representar visualmente el color {c}?',
      'Quisiera ver un ejemplo del color {c}',
      'Crea una imagen de color {c}', 'Por favor, muestra una muestra {c}',
      'Hazme una imagen de color {c}', 'Presenta el color {c}',
    )
    plantillas_def=(
      '¿Qué es el color {c}?','Define el color {c}',
      '¿Qué significa el color {c}?','¿Puedes explicarme qué es el color {c}?',
      'Dime qué es el color {c}','Explícame el significado del color {c}',
    )
    plantillas_reloj=(
      '¿Qué hora es ahora?', '¿Sabes qué hora es?', '¿Me puedes decir la hora?',
      '¿Qué hora tenemos?', '¿Me dices qué hora es?',
      'Dime la hora actual, por favor', '¿Puedes decirme qué hora es ahora?',
      'Quisiera saber qué hora es', '¿Tienes hora?',
      '¿Qué hora es ahora mismo?',
    )
    plantillas_neg=(
      'No dibujes nada de color {c}', 'No me muestres el color {c}',
      'Por favor, no pintes una imagen {c}', 'No quiero que dibujes el color {c}',
      'No generes una imagen de color {c}', 'Evita mostrar el color {c}',
      'No hace falta que crees una imagen {c}',
    )
    mezcla=(('edad_memoria',2),('hipotesis',2),('matematicas',2),('vision',2),
            ('concepto',1),('negacion',1),('reloj',1),('ubicacion',2),
            ('objeto',2),('relacion',2),('comparacion',1),('identidad',1))
    familias=[fam for fam,peso in mezcla for _ in range(peso)]
    vistos={(x['pregunta'],tuple(x['contexto'])) for x in out}
    intentos=0
    while len(out)<n:
        intentos+=1
        if intentos>n*500:
            raise ValueError('Se agotaron combinaciones únicas con las familias disponibles')
        fam=rng.choice(familias)
        nombre=rng.choice(NAMES); otro=rng.choice([x for x in NAMES if x!=nombre])
        ano=rng.randrange(1920,2016)
        color=rng.choice(COLORS)
        x=rng.randint(2,100);y=rng.randint(2,100)
        pref=rng.choice(('', 'Por favor, ','Oye, ','Una pregunta: '))
        if fam=='edad_memoria':
            pregunta=rng.choice((f'¿Cuántos años tiene {nombre}?',f'¿Qué edad tiene ahora {nombre}?',
                                 f'Dime cuántos años tiene {nombre}'))
            c=caso(len(out)+1,fam,pregunta,'intervalo',f'{h-ano-1},{h-ano}',[f'{nombre} nació en {ano}.'])
        elif fam=='hipotesis':
            pregunta=rng.choice((f'Si {nombre} nació en {ano}, ¿cuántos años tiene ahora {nombre}?',
                                 f'Si {nombre} nació en {ano}, ¿qué edad tiene ahora?',
                                 f'Si {nombre} nació en {ano}, ¿cuántos años tendría hoy?'))
            c=caso(len(out)+1,fam,pregunta,'intervalo',f'{h-ano-1},{h-ano}')
        elif fam=='matematicas':
            op=rng.randrange(3)
            if op==0:pregunta=f'¿Cuánto es {x} más {y}?';sol=x+y
            elif op==1:pregunta=f'¿Cuánto es {x} por {y}?';sol=x*y
            else:pregunta=f'¿Cuál es la raíz cuadrada de {x*x}?';sol=x
            c=caso(len(out)+1,fam,pregunta,'numero',str(sol))
        elif fam=='vision':
            plantilla=rng.choice(plantillas_vision)
            pregunta=plantilla.format(c=color)
            if rng.randrange(3)==0:pregunta=pref+pregunta[0].lower()+pregunta[1:]
            c=caso(len(out)+1,fam,pregunta,'imagen',color.upper())
        elif fam=='concepto':
            pregunta=rng.choice(plantillas_def).format(c=color)
            c=caso(len(out)+1,fam,pregunta,'definicion_color',color)
        elif fam=='negacion':
            pregunta=rng.choice(plantillas_neg).format(c=color)
            c=caso(len(out)+1,fam,pregunta,'no_imagen')
        elif fam=='reloj':
            pregunta=rng.choice(plantillas_reloj)
            if rng.randrange(4)==0:pregunta=pref+pregunta
            c=caso(len(out)+1,fam,pregunta,'reloj')
        elif fam=='ubicacion':
            ciudad=rng.choice(ciudades)
            pregunta=rng.choice((f'¿Dónde vive {nombre}?',f'¿En qué ciudad vive {nombre}?',
                                 f'Dime dónde vive {nombre}', f'¿Sabes dónde vive {nombre}?'))
            c=caso(len(out)+1,fam,pregunta,'contiene',ciudad,[f'{nombre} vive en {ciudad}.'])
        elif fam=='objeto':
            objeto=rng.choice(objetos)
            pregunta=rng.choice((f'¿Qué compra {nombre}?', f'Dime qué compró {nombre}',
                                 f'¿Qué es lo que compra {nombre}?'))
            c=caso(len(out)+1,fam,pregunta,'contiene',objeto,[f'{nombre} compra {objeto}.'])
        elif fam=='relacion':
            pregunta=rng.choice((f'¿Quién es el padre de {otro}?', f'¿Sabes quién es el padre de {otro}?'))
            c=caso(len(out)+1,fam,pregunta,'contiene',nombre,[f'{nombre} es el padre de {otro}.'])
        elif fam=='comparacion':
            a,b=rng.sample(animales,2)
            pregunta=rng.choice((f'¿Qué es más fuerte, un {a} o un {b}?',
                                 f'¿Cuál es más pesado, un {a} o un {b}?'))
            c=caso(len(out)+1,fam,pregunta,'abstencion')
        else:
            pregunta=rng.choice(('¿Quién eres?','¿Cómo te llamas?','¿Qué eres tú?',
                                 '¿Podrías decirme quién eres?','Por favor, dime quién eres'))
            c=caso(len(out)+1,fam,pregunta,'contiene','LCM')
        clave=(c['pregunta'],tuple(c['contexto']))
        if clave not in vistos:
            vistos.add(clave);out.append(c)
    return out


def evaluar_respuesta(caso_, respuesta):
    if isinstance(respuesta, dict):
        r = respuesta.get('respuesta', '')
        imagen = respuesta.get('imagen') or {}
        error = respuesta.get('error')
    else:
        r,imagen,error = str(respuesta),{},None
    if error:
        return False, 'error: '+str(error)
    t = normalizar(r)
    esperado = caso_['esperado']
    tipo = caso_['tipo']
    if tipo=='contiene':
        ok=normalizar(esperado) in t and not any(v in t for v in ('no lo se','no tengo informacion','no se nada','no he leido nada','no puedo responder'))
    elif tipo=='definicion_color':
        ok=normalizar(esperado) in t and any(w in t for w in ('color','tonalidad','cromatica','pigmento'))
    elif tipo=='imagen':
        ok=imagen.get('color')==esperado
    elif tipo=='abstencion':
        ok=any(x in t for x in ('no se', 'no puedo', 'no puedo establecer', 'depende', 'no dispongo', 'no consta', 'no es posible', 'no he leido nada', 'no hay datos'))
    elif tipo=='no_imagen':
        ok=not imagen and not (respuesta.get('aprendido') or []) if isinstance(respuesta,dict) else True
    elif tipo=='numero':
        ok=bool(re.search(r'(?<!\d)'+re.escape(esperado)+r'(?!\d)', t))
    elif tipo=='intervalo':
        a,b=esperado.split(',')
        ok=bool(re.search(r'\b'+re.escape(a)+r'\b', t) and re.search(r'\b'+re.escape(b)+r'\b', t))
    elif tipo=='reloj':
        m = re.search(r'\b([01]\d|2[0-3]):([0-5]\d)\b', r)
        if not m: ok=False
        else:
            rmin=int(m.group(1))*60+int(m.group(2))
            local=dt.datetime.now().astimezone()
            ahora=local.hour*60+local.minute
            ok=min(abs(rmin-ahora),1440-abs(rmin-ahora))<=2
    else:
        raise ValueError('Rúbrica no definida: '+tipo)
    return ok, '' if ok else f'No cumple rúbrica {tipo} ({esperado})'


class Evaluador:
    def __init__(self, parser, temporal, memoria_origen=None, carpeta_cartuchos=None):
        from src.memory.store import MemoryStore
        from src.web.motor import Motor
        self.parser, self.temporal = parser, Path(temporal)
        self.Motor,self.MemoryStore = Motor,MemoryStore
        self.base_path=self.temporal/'base.json'
        if memoria_origen:
            from shutil import copyfile
            copyfile(memoria_origen,self.base_path)
            self.base=MemoryStore(str(self.base_path))
        else:
            self.base=MemoryStore(str(self.base_path))
            if parser is not None:
                try:
                    from src.language.semilla import load_seed
                    load_seed(self.base,parser)
                except Exception as e:
                    print('[AVISO] Semilla no disponible:',str(e)[:180])
            # No se cargan cartuchos ni memoria personal ajena por defecto.
        self.base.today=dt.date.today()
        if carpeta_cartuchos:
            from src.memory import cartuchos
            cartuchos.montar(self.base,carpeta_cartuchos)
        self.count=0
        # Solo se comparte un catálogo inmutable; la memoria nunca se comparte.
        from src.semantics.bridge import PuenteSemantico
        self._sem_shared=PuenteSemantico(aprendizaje=self.temporal/'semantica_base_aislada.json')

    def pregunta(self, caso_, flags):
        from src.semantics.bridge import PuenteSemantico
        self.count += 1
        # No se reutiliza memoria mutable entre preguntas independientes.
        memoria=self.MemoryStore(str(self.temporal/f'c{self.count}.json'))
        for k,v in self.base.__dict__.items():
            if k != 'path':
                setattr(memoria,k,copy.deepcopy(v))
        mempath=self.temporal/f'c{self.count}.json'
        memoria.path=str(mempath)
        motor=self.Motor(memoria,self.parser,str(self.temporal/'sin_cartuchos'))
        motor._calidad_flags=dict(flags)
        self._sem_shared.pendiente = None
        motor._puente_semantico=self._sem_shared
        # Enseñanza de conceptos: entorno propio, nunca reutilizar léxico mutable.
        if caso_.get('ensenanza'):
            motor._puente_semantico=PuenteSemantico(aprendizaje=self.temporal/f'learn{self.count}.json')
        try:
            for turno in caso_['contexto']:
                motor.chat(turno)
            start=time.monotonic()
            salida=motor.chat(caso_['pregunta'])
            ms=int((time.monotonic()-start)*1000)
            ok,razon=evaluar_respuesta(caso_,salida)
            return {'id':caso_['id'],'familia':caso_['familia'],'pregunta':caso_['pregunta'],
                    'contexto':caso_['contexto'],'ok':ok,'esperado':caso_['esperado'],
                    'respuesta':salida.get('respuesta') if isinstance(salida,dict) else str(salida),
                    'razon':razon,'ms':ms}
        except Exception as e:
            return {'id':caso_['id'],'familia':caso_['familia'],'pregunta':caso_['pregunta'],
                    'ok':False,'respuesta':'','razon':type(e).__name__+': '+str(e)[:300],'ms':0}


def correr_grupo(ev, casos, flags):
    return [ev.pregunta(c,flags) for c in casos]


def aprobado(r):
    return sum(x['ok'] for x in r) >= max(1, (len(r)*9+9)//10)


def candidato_familia(familia):
    return {'reloj':'reloj','hipotesis':'edad_hipotetica',
            'cita':'citas_ajenas','comparacion':'comparacion_sin_prueba'}.get(familia)


def guardar_json(ruta,obj):
    ruta.parent.mkdir(parents=True,exist_ok=True)
    temp=ruta.with_suffix(ruta.suffix+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(ruta)


def principal(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n',type=int,default=2000,help='número de casos, múltiplo de 10')
    p.add_argument('--semilla',type=int,default=20261118)
    p.add_argument('--autorreparar',action='store_true',help='intentar solamente barreras PREAPROBADAS por familia; nunca reescribe código')
    p.add_argument('--explorar',action='store_true',help='medir todas las tandas aunque fallen; no aprueba ni repara')
    p.add_argument('--sin-escuela',action='store_true',help='solo prueba técnica, NO evalúa el modelo entrenado')
    p.add_argument('--partir-sin-correcciones',action='store_true',help='medir base y activar reparaciones que demuestren mejora')
    p.add_argument('--guardar-config',action='store_true',help='guardar flags validadas para usar desde la web')
    p.add_argument('--memoria',default=None,help='ruta de una memoria origen; se lee pero no se modifica')
    p.add_argument('--cartuchos',default=None,help='carpeta de cartuchos que se monta SOLO en la memoria temporal')
    p.add_argument('--salida',default=str(REPORT))
    args=p.parse_args(argv)
    if args.n<=0 or args.n%10:
        p.error('--n ha de ser múltiplo positivo de 10')
    if not args.sin_escuela:
        from scripts.web import cargar_escuela
        parser=cargar_escuela()
        if parser is None:
            sys.exit('No hay Escuela entrenada: no se presenta una simulación como evaluación integral. Usa --sin-escuela solo para depurar.')
    else:
        class Parser:
            def parse(self,*a,**k): return []
        parser=Parser()
        print('[ATENCIÓN] Sin Escuela real: NO es evaluación de comprensión integral.')
    casos=generar(args.n,args.semilla)
    salida=Path(args.salida)
    salida.mkdir(parents=True,exist_ok=True)
    guardar_json(salida/'banco_casos.json',{'n':len(casos),'semilla':args.semilla,'casos':casos})
    flags = {k:False for k in FLAGS} if args.partir_sin_correcciones else config()
    resumen={'modo':'simulador tecnico' if args.sin_escuela else 'Motor.chat con Escuela real y memoria aislada',
             'n':args.n,'semilla':args.semilla,'flags_iniciales':flags.copy(),'tandas':[],
             'criterio':'9/10; control de regresión de la tanda 1 y todas las tandas previas al activar una reparación',
             'limitacion':'Banco sintético; no demuestra entendimiento humano general'}
    with tempfile.TemporaryDirectory(prefix='lcm_iter14_') as td:
        ev=Evaluador(parser,td,memoria_origen=args.memoria,carpeta_cartuchos=args.cartuchos)
        tandas=[casos[i:i+10] for i in range(0,len(casos),10)]
        primera=None
        for ind,grupo in enumerate(tandas,1):
            res=correr_grupo(ev,grupo,flags)
            intento=[]
            if not args.explorar and not aprobado(res) and args.autorreparar:
                # Candidatos limitados. Se admiten mejoras parciales, porque una
                # tanda puede precisar más de una corrección preaprobada.
                familias=Counter(x['familia'] for x in res if not x['ok'])
                for f,_ in familias.most_common():
                    clave=candidato_familia(f)
                    if not clave or flags[clave]:continue
                    propuestos=dict(flags);propuestos[clave]=True
                    retest=correr_grupo(ev,grupo,propuestos)
                    t={'reparacion':clave,'aciertos_antes':sum(x['ok'] for x in res),
                       'aciertos_despues':sum(x['ok'] for x in retest)}
                    if sum(x['ok'] for x in retest)>sum(x['ok'] for x in res):
                        regression=[]
                        for previo in tandas[:ind-1]:
                            rr=correr_grupo(ev,previo,propuestos)
                            regression.append(sum(x['ok'] for x in rr))
                            if not aprobado(rr):break
                        t['regresiones']=regression
                        if len(regression)==ind-1:
                            flags=propuestos;res=retest;t['estado']='ACEPTADA (mejora validada)'
                        else:t['estado']='RECHAZADA POR REGRESION'
                    else:t['estado']='SIN MEJORA'
                    intento.append(t)
                    if aprobado(res):break
            if ind>1 and not args.explorar and aprobado(res):
                primera=correr_grupo(ev,tandas[0],flags)
            ok=aprobado(res) and (primera is None or aprobado(primera))
            r={'tanda':ind,'aciertos':sum(x['ok'] for x in res),'total':len(res),
               'aprobada':ok,'reparaciones':intento,'revision_tanda_1':sum(x['ok'] for x in primera) if primera else None,
               'casos':res}
            resumen['tandas'].append(r)
            guardar_json(salida/'resumen.json',resumen)
            guardar_json(salida/f'tanda_{ind:04d}.json',r)
            print(f'[TANDA {ind:04d}] {r["aciertos"]}/10 {"APROBADA" if ok else "NO APROBADA"}',flush=True)
            for x in res:
                if not x['ok']:
                    print(f'  FALLA {x["id"]}: {x["pregunta"]} | {str(x["respuesta"])[:160]} | {x["razon"]}',flush=True)
            for t in intento:
                print('  CANDIDATO:',t,flush=True)
            if not ok and not args.explorar:
                print('[DETENIDO] No se avanza sin 9/10 y regresiones. Diagnóstico:',salida/'resumen.json')
                resumen['detenido_en']=ind
                break
        resumen['flags_finales']=flags
        resumen['aprobadas']=sum(x['aprobada'] for x in resumen['tandas'])
        resumen['evaluadas']=sum(x['total'] for x in resumen['tandas'])
        resumen['aciertos']=sum(x['aciertos'] for x in resumen['tandas'])
    guardar_json(salida/'resumen.json',resumen)
    if args.guardar_config and not args.explorar and not args.sin_escuela and 'detenido_en' not in resumen:
        guardar_json(Path('reports/lcm_dialogo14_flags.json'),flags)
        print('[CONFIG] Activadas solo reparaciones validadas:',flags)
    print(f'[FIN] {resumen["aciertos"]}/{resumen["evaluadas"]} casos evaluados; {resumen["aprobadas"]} tandas aprobadas. Informe: {salida / "resumen.json"}',flush=True)
    return 0 if 'detenido_en' not in resumen else 2


if __name__=='__main__':
    raise SystemExit(principal())
