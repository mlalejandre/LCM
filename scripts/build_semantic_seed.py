"""Construye el núcleo semántico curado del LCM; fuente editable y reproducible.
No deriva sentidos de modelos externos ni fabrica asociaciones etimológicas.
La semántica es una hipótesis inicial; no es un diccionario exhaustivo.
"""
from __future__ import annotations
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm(s):
    return ''.join(x for x in unicodedata.normalize('NFD', s.lower()) if not unicodedata.combining(x)).strip()

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', norm(s)).strip('_')

conceptos=[]
ids=set()
def add(lemma, tipo, familia, subfamilia, definition='', aliases=(), forms=(), parents=(), tags=(), intent=None, evidencia='curado'):
    lemma=lemma.strip()
    # Los seis colores y COLOR usan las MISMAS identidades y rasgos que LCM Vision.
    es_color=tipo=='propiedad' and familia=='visual' and subfamilia=='color' and norm(lemma) in ('rojo','verde','azul','amarillo','blanco','negro')
    es_categoria_color=tipo=='concepto' and lemma=='color' and familia=='visual'
    cid=lemma.upper() if es_color else 'COLOR' if es_categoria_color else f'{tipo}.{slug(lemma)}'
    if cid in ids:
        cid=f'{tipo}.{slug(lemma)}_{slug(subfamilia)}'
    if cid in ids:
        raise ValueError(f'Concepto duplicado: {lemma}/{tipo}/{subfamilia}')
    ids.add(cid)
    family=norm(familia).replace(' ','_')
    sub=norm(subfamilia).replace(' ','_')
    features={f'tipo:{tipo}':1.0, f'familia:{family}':1.15, f'subfamilia:{sub}':1.25, f'identidad:{cid}':0.42}
    for tag in tags: features[f'rasgo:{slug(tag)}']=0.65
    if es_color: features={'categoria:color':1.0,f'identidad:cromatica:{norm(lemma)}':1.0}
    if es_categoria_color: features={'categoria:propiedad':1.0}
    if intent: features[f'operacion:{intent}']=0.85
    conceptos.append({'id':cid,'lema':lemma, 'tipo':tipo,'familia':family,'subfamilia':sub,
      'definicion':definition, 'alias':list(aliases), 'formas':list(forms), 'padres':list(parents),
      'rasgos':features,'operacion':intent,'evidencia':evidencia})
    return cid

# Las capacidades se resuelven por el significado de la accion, no por una regex de verbos.
# No se equipara la identidad semantica de dibujar, diseñar, pintar y mostrar.
VERBOS = [
('crear','produccion','generar','Producir algo que no estaba hecho.', 'crear'),
('hacer','produccion','generar','Llevar a cabo una accion o producir un resultado.','crear'),
('generar','produccion','generar','Producir una nueva representacion o resultado.','crear'),
('producir','produccion','generar','Obtener un resultado mediante una actividad.','crear'),
('diseñar','produccion','planificar','Concebir la forma, estructura o disposicion de algo antes de realizarlo.','crear'),
('dibujar','produccion','trazar','Representar visualmente mediante lineas o formas.','crear'),
('pintar','produccion','representar','Aplicar color o producir una representacion pictorica.','crear'),
('ilustrar','produccion','representar','Acompañar o explicar algo con una ilustracion.','crear'),
('representar','produccion','representar','Hacer presente una idea u objeto mediante otra forma.','crear'),
('esbozar','produccion','trazar','Hacer un boceto o primera representacion aproximada.','crear'),
('construir','produccion','construir','Formar algo reuniendo elementos.','crear'),
('componer','produccion','componer','Formar un conjunto mediante la disposicion de partes.','crear'),
('mostrar','comunicacion','presentar','Hacer perceptible o accesible algo a otra persona.','mostrar'),
('enseñar','comunicacion','mostrar','Poner algo a la vista de alguien.','mostrar'),
('presentar','comunicacion','presentar','Dar a conocer o poner algo ante alguien.','mostrar'),
('exhibir','comunicacion','mostrar','Mostrar algo de forma visible.','mostrar'),
('visualizar','comunicacion','mostrar','Hacer visible una representacion de informacion o conceptos.','mostrar'),
('desplegar','comunicacion','mostrar','Mostrar o extender algo que puede verse.','mostrar'),
('compartir','comunicacion','intercambiar','Hacer que otros accedan a un contenido.','mostrar'),
('enseñar','educacion','instruir','Transmitir conocimientos o habilidades para que otro aprenda.',None),
('explicar','comunicacion','informar','Hacer comprensible una idea mediante una exposicion.',None),
('definir','comunicacion','informar','Precisar el significado de un concepto.',None),
('describir','comunicacion','informar','Expresar las caracteristicas de algo.',None),
('narrar','comunicacion','informar','Contar hechos o acontecimientos.',None),
('contar','comunicacion','informar','Relatar acontecimientos o enumerar elementos.',None),
('decir','comunicacion','expresar','Expresar algo mediante lenguaje.',None),
('hablar','comunicacion','expresar','Expresarse oralmente.',None),
('comunicar','comunicacion','expresar','Transmitir informacion a otro.',None),
('escribir','comunicacion','expresar','Representar lenguaje mediante signos escritos.',None),
('leer','comunicacion','comprender','Interpretar signos escritos.',None),
('escuchar','comunicacion','comprender','Prestar atencion a sonidos o palabras.',None),
('preguntar','comunicacion','consultar','Solicitar informacion.',None),
('responder','comunicacion','contestar','Dar contestacion a una pregunta.',None),
('contestar','comunicacion','contestar','Responder a alguien.',None),
('aclarar','comunicacion','informar','Hacer menos ambiguo un significado.',None),
('traducir','comunicacion','transformar','Expresar un contenido en otra lengua.',None),
('resumir','comunicacion','sintetizar','Expresar lo esencial de un contenido.',None),
('corregir','comunicacion','revisar','Modificar algo para eliminar un error.',None),
('reformular','comunicacion','revisar','Expresar nuevamente con otra formulacion.',None),
('conversar','comunicacion','intercambiar','Intercambiar mensajes con otra persona.',None),
('dialogar','comunicacion','intercambiar','Mantener una conversacion.',None),
('saludar','comunicacion','social','Expresar un saludo.',None),
('agradecer','comunicacion','social','Expresar gratitud.',None),
('disculpar','comunicacion','social','Expresar o conceder disculpa.',None),
('pedir','comunicacion','solicitar','Solicitar algo a otra persona.',None),
('solicitar','comunicacion','solicitar','Pedir que se proporcione algo.',None),
('recomendar','comunicacion','aconsejar','Indicar una alternativa considerada conveniente.',None),
('aconsejar','comunicacion','aconsejar','Proponer una conducta o decision.',None),
('prometer','comunicacion','comprometer','Manifestar compromiso futuro.',None),
('negar','comunicacion','afirmar','Rechazar o decir que algo no es cierto.',None),
('afirmar','comunicacion','afirmar','Expresar que algo es verdadero.',None),
('confirmar','comunicacion','afirmar','Ratificar informacion.',None),
('dudar','cognicion','incertidumbre','No tener certeza acerca de una idea.',None),
('creer','cognicion','opinion','Considerar posible o verdadero algo.',None),
('pensar','cognicion','reflexion','Realizar operaciones mentales sobre ideas.',None),
('razonar','cognicion','inferencia','Extraer consecuencias de informacion.',None),
('deducir','cognicion','inferencia','Llegar a una conclusion a partir de premisas.',None),
('inferir','cognicion','inferencia','Obtener una conclusion de evidencias.',None),
('comprender','cognicion','comprension','Captar el significado de algo.',None),
('entender','cognicion','comprension','Comprender algo.',None),
('conocer','cognicion','conocimiento','Tener conocimiento de una cosa.',None),
('saber','cognicion','conocimiento','Poseer una informacion o habilidad.',None),
('aprender','cognicion','aprendizaje','Incorporar nuevos conocimientos o habilidades.',None),
('recordar','cognicion','memoria','Traer a la mente informacion previamente adquirida.',None),
('olvidar','cognicion','memoria','Dejar de recordar algo.',None),
('imaginar','cognicion','representacion','Formar mentalmente una representacion.',None),
('suponer','cognicion','hipotesis','Considerar provisionalmente algo posible.',None),
('comparar','cognicion','analisis','Examinar semejanzas y diferencias.',None),
('analizar','cognicion','analisis','Descomponer algo para estudiar sus partes.',None),
('clasificar','cognicion','clasificacion','Agrupar por caracteristicas.',None),
('identificar','cognicion','reconocimiento','Determinar la identidad o clase.',None),
('reconocer','cognicion','reconocimiento','Advertir que algo corresponde a un concepto conocido.',None),
('decidir','cognicion','decision','Seleccionar una alternativa.',None),
('elegir','cognicion','decision','Escoger entre opciones.',None),
('preferir','cognicion','preferencia','Considerar una alternativa mas deseable.',None),
('querer','volicion','deseo','Desear algo.',None),
('desear','volicion','deseo','Experimentar un deseo.',None),
('necesitar','volicion','necesidad','Requerir algo.',None),
('poder','modalidad','posibilidad','Tener capacidad o posibilidad.',None),
('deber','modalidad','obligacion','Estar obligado o considerarse necesario.',None),
('permitir','modalidad','permiso','Hacer posible que otro haga algo.',None),
('prohibir','modalidad','restriccion','Impedir mediante una norma.',None),
('intentar','volicion','intencion','Procurar conseguir algo.',None),
('lograr','volicion','resultado','Alcanzar una meta.',None),
('fallar','volicion','resultado','No alcanzar el resultado previsto.',None),
('empezar','tiempo','inicio','Iniciar una accion.',None),
('comenzar','tiempo','inicio','Dar inicio a algo.',None),
('terminar','tiempo','fin','Llegar al final.',None),
('acabar','tiempo','fin','Concluir una actividad.',None),
('seguir','tiempo','continuidad','Continuar una actividad.',None),
('continuar','tiempo','continuidad','Proseguir lo empezado.',None),
('parar','tiempo','detencion','Interrumpir una actividad.',None),
('cambiar','cambio','modificacion','Pasar de un estado a otro.',None),
('modificar','cambio','modificacion','Introducir una alteracion.',None),
('transformar','cambio','transformacion','Cambiar de forma o naturaleza.',None),
('mejorar','cambio','mejora','Hacer algo mejor.',None),
('empeorar','cambio','deterioro','Hacer algo peor.',None),
('aumentar','cantidad','incremento','Hacer mayor una magnitud.',None),
('disminuir','cantidad','decremento','Hacer menor una magnitud.',None),
('sumar','cantidad','operacion','Reunir cantidades por adicion.',None),
('restar','cantidad','operacion','Calcular una diferencia.',None),
('multiplicar','cantidad','operacion','Calcular un producto.',None),
('dividir','cantidad','operacion','Separar o repartir en partes.',None),
('contar','cantidad','enumeracion','Determinar un numero de elementos.',None),
('medir','cantidad','medicion','Determinar una magnitud mediante una referencia.',None),
('calcular','cantidad','operacion','Obtener un resultado mediante operaciones.',None),
('mover','espacio','movimiento','Cambiar de posicion.',None),
('girar','espacio','movimiento','Cambiar la orientacion mediante una rotacion.',None),
('subir','espacio','direccion','Desplazarse hacia arriba.',None),
('bajar','espacio','direccion','Desplazarse hacia abajo.',None),
('entrar','espacio','direccion','Pasar al interior.',None),
('salir','espacio','direccion','Pasar al exterior.',None),
('poner','espacio','colocacion','Situar algo en un lugar.',None),
('colocar','espacio','colocacion','Poner en una posicion.',None),
('quitar','espacio','retirada','Retirar algo.',None),
('abrir','manipulacion','apertura','Hacer accesible el interior.',None),
('cerrar','manipulacion','cierre','Impedir el paso o acceso.',None),
('usar','manipulacion','utilizacion','Emplear para un fin.',None),
('guardar','manipulacion','almacenamiento','Conservar algo en un lugar.',None),
('borrar','manipulacion','eliminacion','Quitar informacion o marcas.',None),
('eliminar','manipulacion','eliminacion','Hacer desaparecer o retirar algo.',None),
('buscar','informacion','consulta','Intentar encontrar algo.',None),
('encontrar','informacion','descubrimiento','Localizar algo buscado.',None),
('descubrir','informacion','descubrimiento','Conocer algo antes desconocido.',None),
('ver','percepcion','visual','Percibir con la vista.',None),
('mirar','percepcion','visual','Dirigir la vista hacia algo.',None),
('observar','percepcion','visual','Prestar atencion perceptiva a algo.',None),
('oir','percepcion','auditiva','Percibir sonido.',None),
('sentir','percepcion','sensacion','Experimentar sensaciones o emociones.',None),
('oler','percepcion','olfato','Percibir olores.',None),
('tocar','percepcion','tacto','Percibir por contacto o entrar en contacto.',None),
('gustar','emocion','preferencia','Resultar agradable.',None),
('amar','emocion','afecto','Sentir amor.',None),
('odiar','emocion','rechazo','Sentir odio.',None),
('tener','relacion','posesion','Poseer o disponer de algo.',None),
('poseer','relacion','posesion','Tener algo.',None),
('ser','relacion','identidad','Expresar identidad o clasificacion.',None),
('estar','relacion','estado','Expresar estado o localizacion.',None),
('existir','relacion','existencia','Tener existencia.',None),
('pertenecer','relacion','pertenencia','Formar parte de algo.',None),
('parecer','relacion','semejanza','Tener apariencia o semejanza.',None),
('depender','relacion','dependencia','Estar condicionado por algo.',None),
('significar','relacion','significado','Tener un sentido.',None),
('relacionar','relacion','asociacion','Establecer una vinculacion.',None),
]

FORMAS = {
 'mostrar':['muestra','muestres','muestren','muestras','muestran','muestro','muéstrame','muestrame','muestre','mostrad','mostrarme','muéstralo','muestralo'],
 'enseñar':['enseña','enséñame','ensename','enseñame','enseñe','enséñalo'],
 'dibujar':['dibuja','dibújame','dibujame','dibújalo','dibujalo','dibuje'],
 'pintar':['pinta','píntame','pintame','píntalo','pintalo'],
 'diseñar':['diseña','diséñame','disename','diseñame','diseñe'],
 'crear':['crea','créame','creame','créalo','crealo'],
 'generar':['genera','genérame','generame'],
 'ilustrar':['ilustra','ilústrame','ilustrame'],
 'representar':['representa','represéntame','representame'],
 'visualizar':['visualiza','visualízame','visualizame'],
 'hacer':['haz','hazme','haga','hace','haceme'],
 'ver':['ve','mira','veo','ver'],
 'decir':['di','dime','diga'],
 'poner':['pon','ponme','ponga'],
 'pedir':['pide','pídeme','pideme'],
 'querer':['quiero','quiere','quería','quisiera','quieres'],
 'poder':['puedes','podrías','podrias','puedo','podemos'],
 'ser':['es','son','soy','sea','somos','era','fue'],
 'estar':['está','esta','estoy','están','estan','estamos','estuve'],
 'tener':['tengo','tiene','tienes','tenemos','tienen'],
 'oir':['oye','oigo','oí','oi'],
}
for lemma, family, sub, defn, op in VERBOS:
    special=['visual'] if op else []
    add(lemma,'accion',family,sub,defn,forms=FORMAS.get(lemma,()),tags=special,intent=op)

# Conceptos núcleo conversacionales, desambiguados por sentido.
GENERAL = {
 'comunicacion.mensaje':('mensaje','comunicacion','contenido','Contenido transmitido entre interlocutores.'),
 'comunicacion.pregunta':('pregunta','comunicacion','consulta','Enunciado que solicita informacion.'),
 'comunicacion.respuesta':('respuesta','comunicacion','contestacion','Enunciado que contesta a una pregunta.'),
 'comunicacion.conversacion':('conversación','comunicacion','intercambio','Intercambio sucesivo de intervenciones.'),
 'comunicacion.dialogo':('diálogo','comunicacion','intercambio','Conversacion entre participantes.'),
 'comunicacion.explicacion':('explicación','comunicacion','informacion','Texto que hace comprensible una idea.'),
 'comunicacion.definicion':('definición','comunicacion','informacion','Descripcion del significado de un concepto.'),
 'comunicacion.significado':('significado','comunicacion','sentido','Contenido semantico de una palabra o signo.'),
 'comunicacion.concepto':('concepto','cognicion','representacion','Representacion abstracta de una idea o entidad.'),
 'comunicacion.palabra':('palabra','lenguaje','unidad','Unidad de lenguaje con forma y posible significado.'),
 'comunicacion.verbo':('verbo','lenguaje','gramatica','Clase gramatical que puede expresar acciones, procesos o estados.'),
 'comunicacion.frase':('frase','lenguaje','unidad','Secuencia de palabras organizada.'),
 'comunicacion.oracion':('oración','lenguaje','unidad','Unidad gramatical con estructura predicativa.'),
 'comunicacion.texto':('texto','lenguaje','contenido','Secuencia coherente de enunciados.'),
 'comunicacion.parrafo':('párrafo','lenguaje','unidad','Conjunto de oraciones con continuidad tematica.'),
 'comunicacion.contexto':('contexto','lenguaje','interpretacion','Informacion circundante relevante para interpretar algo.'),
 'comunicacion.sinonimo':('sinónimo','lenguaje','relacion','Palabra o expresion de significado cercano al de otra.'),
 'comunicacion.antonimo':('antónimo','lenguaje','relacion','Palabra de significado opuesto o contrastante.'),
 'comunicacion.ejemplo':('ejemplo','comunicacion','ilustracion','Caso concreto que ayuda a comprender una idea.'),
 'comunicacion.error':('error','evaluacion','fallo','Resultado que no corresponde a lo esperado.'),
 'comunicacion.correccion':('corrección','evaluacion','revision','Cambio realizado para eliminar un error.'),
 'comunicacion.prueba':('prueba','evaluacion','comprobacion','Procedimiento que contrasta una afirmacion con evidencias.'),
 'comunicacion.dato':('dato','informacion','representacion','Valor o registro susceptible de procesamiento.'),
 'comunicacion.hecho':('hecho','informacion','evidencia','Acontecimiento o proposicion considerada verdadera segun evidencia.'),
 'comunicacion.opinion':('opinión','cognicion','juicio','Valoracion o creencia que no equivale necesariamente a hecho.'),
 'comunicacion.hipotesis':('hipótesis','cognicion','suposicion','Explicacion provisional que requiere contraste.'),
 'comunicacion.certeza':('certeza','cognicion','confianza','Conviccion de conocer algo con seguridad.'),
 'comunicacion.incertidumbre':('incertidumbre','cognicion','confianza','Ausencia de certeza suficiente.'),
 'comunicacion.memoria':('memoria','cognicion','registro','Capacidad o soporte que conserva informacion.'),
 'comunicacion.aprendizaje':('aprendizaje','cognicion','proceso','Proceso de adquirir conocimiento o habilidad.'),
 'comunicacion.lenguaje':('lenguaje','lenguaje','sistema','Sistema de signos usado para comunicar.'),
 'comunicacion.idioma':('idioma','lenguaje','sistema','Lengua compartida por una comunidad.'),
 'comunicacion.intencion':('intención','cognicion','proposito','Objetivo que una persona busca con una accion.'),
 'comunicacion.solicitud':('solicitud','comunicacion','peticion','Peticion dirigida a otra persona.'),
 'comunicacion.orden':('orden','comunicacion','instruccion','Instruccion para realizar una accion.'),
 'comunicacion.capacidad':('capacidad','modalidad','habilidad','Posibilidad o habilidad de llevar a cabo una accion.'),
 'comunicacion.funcion':('función','informatica','operacion','Operacion ejecutable con entradas y resultados.'),
 'comunicacion.operacion':('operación','informatica','accion','Transformacion definida sobre datos o estado.'),
 'comunicacion.usuario':('usuario','persona','rol','Persona que utiliza un sistema.'),
 'comunicacion.asistente':('asistente','persona','rol','Sistema o persona que ayuda en una tarea.'),
 'comunicacion.modelo':('modelo','informatica','representacion','Representacion formal de un proceso o estructura.'),
 'comunicacion.vector':('vector','matematica','objeto','Elemento con componentes en un espacio vectorial.'),
 'comunicacion.imagen':('imagen','visual','representacion','Representacion visual formada por elementos o pixeles.'),
 'comunicacion.color':('color','visual','propiedad','Propiedad perceptiva relacionada con la luz visible.'),
 'comunicacion.forma':('forma','visual','propiedad','Configuracion espacial o contorno de una entidad.'),
 'comunicacion.figura':('figura','visual','objeto','Forma o representacion de un objeto.'),
 'comunicacion.cuadro':('cuadro','visual','representacion','Obra pictorica o superficie enmarcada.'),
 'comunicacion.muestra':('muestra','visual','ejemplo','Ejemplo material o visual de una propiedad.'),
}
for key,(lemma,fam,sub,definition) in GENERAL.items():
    add(lemma,'concepto',fam,sub,definition)

# Color y geometría vinculados a percepción, sin forzar los verbos a ser comandos.
for word, desc in [
 ('rojo','Tonalidad cromatica asociada aproximadamente a longitudes de onda largas.'),
 ('azul','Tonalidad cromatica asociada aproximadamente a longitudes de onda cortas.'),
 ('verde','Tonalidad cromatica entre azul y amarillo en varios espacios perceptivos.'),
 ('amarillo','Tonalidad cromatica amarilla.'),
 ('negro','Ausencia o reduccion fuerte de luz visible en una superficie.'),
 ('blanco','Alta reflexion difusa del espectro visible, con apariencia blanca.'),
 ('naranja','Tonalidad intermedia entre rojo y amarillo.'),
 ('morado','Tonalidad violacea o purpura.'),
 ('violeta','Tonalidad violacea.'),
 ('gris','Color acromatico intermedio entre negro y blanco.'),
 ('rosa','Tonalidad rosada.'),
 ('marrón','Tonalidad parda o marron.'),
 ('celeste','Azul claro.'),
 ('turquesa','Tonalidad entre azul y verde.')]:
    add(word,'propiedad','visual','color',desc,tags=['visual','cromatico'])
for w in 'círculo cuadrado rectángulo triángulo óvalo esfera cubo cono cilindro línea punto ángulo curva segmento contorno vértice borde centro diagonal'.split():
    add(w,'concepto','visual','geometria',f'Concepto geometrico asociado a {w}.', tags=['visual','geometria'])

# Dominios del español habitual: pertenencia a categorías conservadora y auditada.
# Cada item se considera un concepto individual, no sinónimo del resto del grupo.
DOMINIOS={
'persona/familia':'''persona gente individuo niño niña bebé adulto anciano joven hombre mujer madre padre hijo hija hermano hermana primo prima tío tía abuelo abuela nieto nieta pareja esposo esposa marido mujer padrastro madrastra familiar pariente sobrino sobrina gemelo amigo amiga compañero compañera vecino vecina conocido desconocido huésped invitado anfitrión''',
'persona/profesiones':'''profesor profesora maestro maestra médico médica enfermero enfermera abogado abogada juez policía bombero bombera ingeniero ingeniera científico científica mecánico mecánica cocinero cocinera camarero camarera artista músico cantante actor actriz escritor escritora periodista conductor conductora electricista agricultor agricultora vendedor vendedora estudiante aprendiz director directora empleado empleada jefe jefa propietario propietaria cliente paciente''',
'persona/roles_sociales':'''ciudadano ciudadana extranjero extranjera turista viajero viajera comprador compradora encargado responsable participante testigo víctima voluntario voluntaria líder seguidor seguidora miembro grupo equipo comunidad asociación organización público audiencia población sociedad''',
'emocion/afecto':'''amor cariño afecto ternura alegría felicidad entusiasmo satisfacción calma tranquilidad orgullo gratitud confianza esperanza ilusión compasión simpatía amistad solidaridad respeto admiración pasión nostalgia melancolía pena tristeza miedo ansiedad nerviosismo ira enfado rabia odio disgusto frustración vergüenza culpa sorpresa asombro curiosidad aburrimiento indiferencia alivio preocupación estrés soledad decepción celos envidia''',
'emocion/calidad':'''feliz triste alegre contento preocupado preocupado ansioso tranquilo nervioso enfadado furioso satisfecho insatisfecho amable simpático antipático cordial hostil respetuoso generoso egoísta honesto sincero tímido valiente prudente impaciente paciente optimista pesimista''',
'estado/salud':'''salud enfermedad dolor fiebre tos resfriado gripe infección herida lesión cansancio fatiga sueño hambre sed sediento somnoliento mareo náusea alergia medicina medicamento tratamiento terapia médico hospital clínica farmacia vacuna recuperación descanso ejercicio alimentación dieta peso altura temperatura presión pulso respiración músculo hueso piel sangre corazón cerebro ojo oído mano pie brazo pierna cabeza espalda estómago garganta nariz boca diente lengua''',
'objeto/casa':'''casa hogar piso apartamento habitación dormitorio cocina baño salón pasillo jardín balcón terraza tejado techo pared suelo escalera entrada salida puerta ventana cerradura llave timbre lámpara bombilla mesa silla sofá sillón cama colchón almohada manta sábana armario cajón estantería escritorio escritorio perchero espejo alfombra cortina cuadro florero reloj teléfono televisor mando enchufe cable grifo lavabo ducha bañera inodoro''',
'objeto/ropa':'''ropa camiseta camisa pantalón falda vestido abrigo chaqueta jersey sudadera calcetín zapato zapatilla bota sandalia gorro sombrero bufanda guante cinturón bolso cartera mochila maleta collar pulsera anillo pendiente gafas paraguas pijama uniforme''',
'objeto/herramientas':'''herramienta martillo destornillador tornillo clavo llave alicate tijera cuchillo sierra taladro cepillo brocha regla lápiz bolígrafo pluma goma cuaderno folio papel cartón pegamento cinta cuerda aguja hilo pincel lienzo pintura''',
'objeto/tecnologia':'''ordenador computadora portátil móvil tableta pantalla teclado ratón impresora cámara altavoz auriculares micrófono wifi internet red página web sitio navegador enlace correo mensaje aplicación programa sistema dispositivo archivo carpeta documento código contraseña cuenta usuario servidor cliente base datos algoritmo modelo entrenamiento procesador memoria almacenamiento disco batería cargador sensor motor robot inteligencia artificial''',
'objeto/transporte':'''vehículo coche automóvil bicicleta motocicleta moto autobús autocar tren tranvía metro taxi camión furgoneta barco buque bote velero avión helicóptero patinete carretera calle avenida camino autopista puente túnel estación aeropuerto puerto aparcamiento garaje gasolinera señal semáforo''',
'objeto/educacion':'''escuela colegio instituto universidad clase curso lección asignatura examen ejercicio tarea deberes pregunta respuesta libro biblioteca diccionario enciclopedia artículo capítulo página párrafo frase palabra letra número nota apuntes profesor alumno estudiante diploma título conocimiento estudio investigación experimento teoría hipótesis método''',
'objeto/alimentacion':'''comida alimento plato desayuno almuerzo merienda cena pan leche agua café té zumo jugo arroz pasta pizza sopa ensalada carne pescado huevo queso yogur mantequilla aceite sal azúcar miel harina chocolate galleta fruta manzana naranja pera plátano fresa uva limón sandía melón melocotón verdura tomate patata cebolla zanahoria lechuga pepino pimiento ajo garbanzo lenteja judía pollo ternera cerdo jamón pescado atún salmón panadería restaurante cafetería cocina horno sartén olla cuchara tenedor cuchillo vaso taza botella nevera frigorífico''',
'naturaleza/animales':'''animal perro gato caballo vaca oveja cerdo gallina gallo pato ganso conejo ratón rata elefante jirafa león tigre oso lobo zorro mono gorila ballena delfín tiburón pez pulpo cangrejo tortuga serpiente lagarto rana sapo mariposa abeja hormiga mosquito mosca araña pájaro ave águila paloma loro búho pingüino pez insecto mamífero reptil anfibio vertebrado invertebrado mascota''',
'naturaleza/plantas':'''planta árbol flor hoja tallo raíz semilla fruto madera bosque selva pradera hierba césped rama tronco arbusto rosal pino roble olivo manzano palmera trigo maíz arroz vid rosa margarita tulipán girasol cactus hongo seta tierra suelo barro arcilla piedra roca arena polvo''',
'naturaleza/fenomenos':'''naturaleza aire agua fuego tierra lluvia nieve granizo viento tormenta nube niebla sol luna estrella planeta cielo universo galaxia cometa meteorito arcoíris rayo trueno relámpago invierno primavera verano otoño estación día noche amanecer atardecer temperatura calor frío humedad sequía clima tiempo atmósfera océano mar río lago cascada montaña valle colina volcán terremoto isla continente playa costa bosque desierto''',
'ubicacion/lugares':'''lugar espacio habitación edificio casa ciudad pueblo barrio municipio provincia región comunidad país nación capital frontera territorio mapa dirección calle plaza parque jardín tienda supermercado mercado centro comercio oficina banco hospital farmacia escuela universidad restaurante hotel museo teatro cine estadio gimnasio piscina iglesia biblioteca estación aeropuerto playa montaña río bosque campo granja fábrica taller empresa trabajo''',
'ubicacion/orientacion':'''izquierda derecha arriba abajo encima debajo delante detrás dentro fuera interior exterior norte sur este oeste centro medio lado esquina borde cerca lejos alrededor enfrente atrás adelante primero último junto separado paralelo perpendicular vertical horizontal diagonal distancia recorrido trayecto ruta destino origen''',
'tiempo/momentos':'''tiempo momento instante segundo minuto hora día semana mes año década siglo mañana tarde noche madrugada mediodía medianoche lunes martes miércoles jueves viernes sábado domingo enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre ayer hoy mañana pasado presente futuro ahora después antes luego temprano tarde pronto siempre nunca a veces frecuentemente recientemente inmediato duración periodo plazo fecha calendario agenda cita horario''',
'cantidad/numeros':'''cantidad número cifra unidad decena centena millar millón mitad doble triple tercio cuarto quinto sexto séptimo octavo noveno décimo porcentaje total parte suma diferencia producto cociente resultado media promedio máximo mínimo límite aproximación exactitud precisión medida escala tamaño longitud anchura altura volumen superficie peso masa velocidad distancia tiempo precio coste valor presupuesto descuento''',
'cantidad/comparacion':'''más menos mayor menor igual diferente semejante similar distinto superior inferior mejor peor suficiente insuficiente mucho poco bastante demasiado todo nada alguno ninguno varios muchos pocos ambos cada cualquier mismo otro nuevo antiguo siguiente anterior primero último pequeño grande mediano enorme diminuto largo corto alto bajo ancho estrecho grueso delgado pesado ligero rápido lento''',
'valoracion/cualidades':'''bueno malo correcto incorrecto verdadero falso posible imposible probable improbable seguro inseguro fácil difícil simple complejo claro oscuro bonito feo útil inútil importante irrelevante necesario opcional obligatorio libre público privado abierto cerrado vacío lleno limpio sucio nuevo viejo moderno antiguo eficaz eficiente fiable robusto débil fuerte flexible rígido estable inestable compatible incompatible completo incompleto disponible ausente presente''',
'color/luz':'''color luz sombra brillo claridad oscuridad tono tonalidad saturación contraste transparencia opacidad reflejo reflejar colorido pigmento pintura azul rojo verde amarillo blanco negro naranja morado violeta gris rosa marrón celeste turquesa cian magenta dorado plateado beige crema''',
'relacion/espacio':'''parte todo conjunto elemento miembro relación vínculo conexión unión separación pertenencia inclusión contenedor contenido adyacencia proximidad distancia dirección posición lugar ubicación ubicación origen destino límite frontera región área superficie objeto entidad sujeto predicado propiedad atributo clase categoría tipo instancia ejemplo caso excepción norma regla consecuencia premisa conclusión causa efecto condición consecuencia''',
'actividad/ocio':'''juego deporte fútbol baloncesto tenis natación carrera senderismo ciclismo lectura escritura música canción concierto película serie televisión cine teatro danza baile dibujo pintura fotografía arte museo viaje vacaciones excursión fiesta reunión celebración cumpleaños aniversario pasatiempo afición colección videojuego ajedrez carta novela cuento poesía poema receta cocina paseo descanso entretenimiento''',
'actividad/trabajo':'''trabajo empleo profesión oficio proyecto plan objetivo meta tarea actividad proceso etapa paso acción decisión reunión entrevista cita presentación documento informe análisis resultado entrega fecha plazo equipo responsable jefe empleado cliente proveedor contrato acuerdo salario nómina impuesto factura pago cobro presupuesto dinero compra venta precio pedido oferta demanda mercado negocio empresa industria servicio producto calidad riesgo seguridad problema solución oportunidad estrategia prioridad recurso tiempo productividad''',
'actividad/economia':'''dinero moneda billete tarjeta banco cuenta ahorro inversión préstamo deuda interés impuesto gasto ingreso sueldo salario precio tarifa coste beneficio pérdida ganancia presupuesto crédito débito transferencia compra venta alquiler hipoteca propiedad patrimonio capital mercado oferta demanda factura recibo contrato comercio tienda supermercado negocio empresa economía inflación''',
'actividad/sociedad':'''sociedad gobierno estado nación ciudadanía ley norma derecho deber responsabilidad libertad igualdad justicia delito sanción juez tribunal juicio contrato acuerdo permiso prohibición obligación elección voto parlamento ayuntamiento municipio democracia participación comunidad vecino familia amistad respeto seguridad privacidad información protección confianza cooperación conflicto paz guerra negociación''',
'informatica/estructura':'''software hardware algoritmo estructura dato información variable constante función parámetro argumento resultado excepción error fallo registro tabla fila columna índice consulta filtro ordenación lista tupla conjunto diccionario mapa grafo nodo arista relación vector matriz tensor punto dimensión espacio distancia similitud coseno embedding representación característica rasgo etiqueta categoría clase objeto instancia método constructor módulo paquete librería dependencia versión archivo carpeta ruta directorio memoria disco almacenamiento caché servidor cliente petición respuesta interfaz botón formulario campo página imagen píxel resolución formato pantalla dispositivo red protocolo puerto token modelo aprendizaje entrenamiento validación prueba evaluación métrica exactitud precisión cobertura confianza incertidumbre abstención''',
}

# Determinantes, preposiciones y conectores se distinguen como unidades de lengua:
FUNCIONALES = {
 'interrogativo':'''qué quién quiénes cuál cuáles cómo cuándo dónde por qué para qué cuánto cuánta cuántos cuántas adónde de dónde con quién''',
 'conector_causal':'''porque pues dado que ya que debido a puesto que''',
 'conector_condicional':'''si siempre que a menos que salvo que con tal de que''',
 'conector_contrastivo':'''pero aunque sin embargo no obstante en cambio a pesar de''',
 'conector_consecutivo':'''entonces por tanto por eso así que en consecuencia''',
 'conector_aditivo':'''y además también asimismo incluso igualmente''',
 'negacion':'''no tampoco nunca jamás ni ninguna ningún nadie nada''',
 'afirmacion':'''sí ciertamente efectivamente desde luego afirmativamente''',
 'modalidad':'''quizás quizá tal vez probablemente posiblemente seguramente ciertamente''',
 'cuantificador':'''todo todos toda todas cada alguno alguna ninguno ninguna mucho mucha poco poca bastante demasiado varios varias ambos ambas''',
 'preposicion':'''a ante bajo con contra de desde durante en entre hacia hasta mediante para por según sin sobre tras''',
 'pronombre':'''yo tú él ella ello nosotros nosotras vosotros vosotras ustedes ellos ellas me te se nos os lo la le los las les mí ti conmigo contigo suyo suya mío mía tuyo tuya''',
 'determinante':'''el la los las un una unos unas este esta estos estas ese esa esos esas aquel aquella aquellos aquellas mi mis tu tus su sus nuestro nuestra nuestros nuestras''',
}
# Las expresiones compuestas se incorporan explícitamente, no se segmentan como 'palabras' sueltas.
for fam, words in FUNCIONALES.items():
    strings = []
    if fam=='interrogativo':
        strings=['qué','quién','quiénes','cuál','cuáles','cómo','cuándo','dónde','por qué','para qué','cuánto','cuánta','cuántos','cuántas','adónde','de dónde','con quién']
    elif fam=='conector_causal': strings=['porque','pues','dado que','ya que','debido a','puesto que']
    elif fam=='conector_condicional': strings=['si','siempre que','a menos que','salvo que','con tal de que']
    elif fam=='conector_contrastivo': strings=['pero','aunque','sin embargo','no obstante','en cambio','a pesar de']
    elif fam=='conector_consecutivo': strings=['entonces','por tanto','por eso','así que','en consecuencia']
    elif fam=='conector_aditivo': strings=['y','además','también','asimismo','incluso','igualmente']
    else: strings=words.split()
    for w in strings:
        add(w,'funcional','gramatica',fam, f'Unidad funcional de lengua: {fam.replace("_", " ")}.',evidencia='rol_gramatical')

for cat, words in DOMINIOS.items():
    fam,sub=cat.split('/',1)
    for word in words.split():
        normalized=norm(word)
        # Se conserva un ID diferente para sentidos en dominios diferentes.
        add(word,'concepto',fam,sub,'',evidencia='agrupacion_inicial')

# Algunos sentidos que NO deben fusionarse con un solo embedding por coincidencia textual.
for lemma, fam, sub, definition in [
 ('banco','finanzas','institucion','Entidad que presta servicios financieros.'),
 ('banco','objetos','asiento','Asiento alargado para varias personas.'),
 ('carta','comunicacion','documento','Mensaje escrito dirigido a alguien.'),
 ('carta','ocio','juego','Pieza de una baraja.'),
 ('planta','naturaleza','organismo','Ser vivo vegetal.'),
 ('planta','arquitectura','nivel','Nivel horizontal de un edificio.'),
 ('cola','animales','parte','Apéndice posterior de algunos animales.'),
 ('cola','organizacion','fila','Fila de personas o elementos que esperan.'),
 ('cola','materiales','adhesivo','Sustancia utilizada para pegar.'),
 ('llama','animales','mamifero','Mamifero sudamericano usado como animal de carga.'),
 ('llama','fuego','combustion','Parte visible luminosa de una combustion.'),
 ('copa','objetos','recipiente','Recipiente con pie destinado a beber.'),
 ('copa','naturaleza','arbol','Conjunto de ramas y hojas superiores de un arbol.'),
 ('cura','medicina','tratamiento','Acto o proceso de tratar una dolencia.'),
 ('cura','persona','religion','Sacerdote de una comunidad religiosa.'),
 ('ratón','animales','roedor','Pequeño mamifero roedor.'),
 ('ratón','tecnologia','dispositivo','Dispositivo apuntador de ordenador.')]:
    add(lemma, 'sentido', fam, sub, definition, evidencia='desambiguado')

# Agrupar nodos del mismo dominio no equivale a afirmar que sean sinonimos.
# Las relaciones de sinonimia sólo se guardan para un conjunto pequeño validado.
SINONIMOS=[('mostrar','exhibir'),('responder','contestar'),('comenzar','empezar'),('entender','comprender'),('producir','generar'),('seguir','continuar'),('preguntar','consultar'),('coche','automóvil'),('ordenador','computadora')]
RELACIONES=[{'s':c['id'],'p':'SER','o':'COLOR','evidencia':'catalogo_vision'} for c in conceptos if c['id'] in ('ROJO','VERDE','AZUL','AMARILLO','NEGRO','BLANCO')]
by_lemma={}
for c in conceptos:
    by_lemma.setdefault(norm(c['lema']),[]).append(c)
for a,b in SINONIMOS:
    x=by_lemma.get(norm(a),[])
    y=by_lemma.get(norm(b),[])
    if len(x)==1 and len(y)==1:
        RELACIONES.append({'s':x[0]['id'],'p':'RELACIONADO_ESTRECHAMENTE_CON','o':y[0]['id'],'evidencia':'revisado'})
for c in conceptos:
    if c['tipo']=='accion' and c['operacion'] and c['subfamilia'] in ('trazar','representar','planificar','generar','componer','construir'):
        c['padres'].append('accion.crear') if c['id']!='accion.crear' else None
    elif c['tipo']=='accion' and c['operacion']=='mostrar' and c['id']!='accion.mostrar':
        c['padres'].append('accion.mostrar')

# Identificar duplicados por lema no es un error: hay polisemia explícita.
out={'schema':'lcm-semantica-1.0','autor':'base curada y expandida con LLM, requiere validación',
     'version':'2026-11-17','conceptos':conceptos,'relaciones':RELACIONES,
     'nota':'Los agrupamientos genericos son hipótesis de dominio, no definiciones fiables ni sentidos validados individualmente.'}
target=ROOT/'data'/'semantica'/'conceptos_es.json'
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('conceptos',len(conceptos),'lemas',len(by_lemma),'polisemias',sum(len(v)>1 for v in by_lemma.values()),'relaciones',len(RELACIONES),'bytes',target.stat().st_size)
