"""2.33 · EXAMEN LIMPIO de sinónimos y pronombres. Escrito ANTES de tocar el código y sin ejecutarlo; se mide UNA vez en 2.32 y en 2.33.
Cada pregunta lleva su tipo:
  lit  = se pregunta con las mismas palabras del texto (control: no debe bajar)
  sin  = se pregunta con OTRO verbo o nombre de significado parecido («adquirir» por «comprar»)
  pro  = la respuesta está en una oración que usa un pronombre («lo cuida», «ella», «este»)
  abs  = no está en el texto: hay que decir que no se sabe (las trampas usan sinónimos o pronombres para tentar)
Criterio: palabras que deben aparecer (a|b = cualquiera; a;b = todas). ABST = debe decir que no lo sabe."""
T = [
 {"id": "pinguinos", "texto": """
El pingüino emperador vive en la Antártida y soporta temperaturas de cuarenta grados bajo cero. La hembra pone un solo huevo en invierno.
Después se lo entrega al macho y regresa al mar para alimentarse. El macho lo protege entre sus patas durante dos meses sin comer.
Cuando la cría nace, la madre vuelve con comida en el estómago. Ella alimenta al polluelo y el padre se marcha a pescar.
Los pingüinos se agrupan en grandes corros para resistir el viento. Las focas leopardo los cazan cerca de la costa.
""", "preguntas": [
  ("¿Dónde vive el pingüino emperador?", "antartida", "lit"),
  ("¿Qué pone la hembra?", "huevo", "lit"),
  ("¿Dónde habita el pingüino emperador?", "antartida", "sin"),
  ("¿Qué aguanta el pingüino emperador?", "temperaturas|cuarenta", "sin"),
  ("¿Quién protege el huevo?", "macho", "pro"),
  ("¿A quién entrega la hembra el huevo?", "macho", "pro"),
  ("¿Quién alimenta al polluelo?", "madre|hembra|ella", "pro"),
  ("¿Quiénes cazan a los pingüinos?", "focas", "pro"),
  ("¿Quién defiende el huevo?", "macho", "sin"),
  ("¿Qué comen las focas leopardo?", "ABST", "abs"),
 ]},
 {"id": "tienda", "texto": """
Rosa abrió una librería en el centro de Zamora hace diez años. Al principio vendía solo libros de viaje.
Luego compró una pequeña imprenta y empezó a publicar guías de la provincia. Su hermano Pablo la ayuda los fines de semana.
Él se encarga de las cuentas y del almacén. La librería organiza un club de lectura cada jueves.
El ayuntamiento le concedió un premio a Rosa por su labor cultural. Ella lo recogió en el teatro de la ciudad.
""", "preguntas": [
  ("¿Qué abrió Rosa?", "libreria", "lit"),
  ("¿Dónde abrió Rosa la librería?", "zamora|centro", "lit"),
  ("¿Qué adquirió Rosa?", "imprenta", "sin"),
  ("¿Qué empezó a editar Rosa?", "guias", "sin"),
  ("¿Quién ayuda a Rosa?", "pablo|hermano", "pro"),
  ("¿De qué se encarga Pablo?", "cuentas|almacen", "pro"),
  ("¿Dónde recogió Rosa el premio?", "teatro", "pro"),
  ("¿Quién le concedió un premio a Rosa?", "ayuntamiento", "lit"),
  ("¿Quién le otorgó un premio a Rosa?", "ayuntamiento", "sin"),
  ("¿Qué vende Pablo?", "ABST", "abs"),
 ]},
 {"id": "volcan", "texto": """
El volcán Teneguía entró en erupción en la isla de La Palma en 1971. La lava bajó hasta el mar y formó nuevas playas.
Los científicos lo vigilaron durante semanas desde un observatorio cercano. Ellos midieron la temperatura de la lava cada día.
La erupción duró veinticuatro días y no causó víctimas. Un pescador murió por los gases mientras hacía fotos.
Hoy el volcán atrae a muchos turistas que suben a su cráter.
""", "preguntas": [
  ("¿Cuándo entró en erupción el volcán Teneguía?", "1971", "lit"),
  ("¿Qué formó la lava?", "playas", "lit"),
  ("¿Qué creó la lava?", "playas", "sin"),
  ("¿Quiénes vigilaron el volcán?", "cientificos", "pro"),
  ("¿Qué midieron los científicos?", "temperatura", "pro"),
  ("¿Cuánto duró la erupción?", "veinticuatro", "lit"),
  ("¿Qué atrae el volcán?", "turistas", "lit"),
  ("¿Quiénes visitan el cráter?", "turistas", "sin"),
  ("¿Cuántos pescadores salvaron los científicos?", "ABST", "abs"),
 ]},
 {"id": "robot", "texto": """
El robot aspirador limpia el suelo de la casa mientras sus dueños trabajan. Tiene un sensor que detecta los obstáculos.
Cuando encuentra una pared, la esquiva y cambia de dirección. Su batería dura unas dos horas.
Al terminar, vuelve solo a su base y allí se recarga. Los usuarios lo programan desde el teléfono móvil.
El fabricante recomienda vaciar el depósito después de cada uso.
""", "preguntas": [
  ("¿Qué limpia el robot aspirador?", "suelo", "lit"),
  ("¿Qué detecta el sensor?", "obstaculos", "lit"),
  ("¿Qué localiza el sensor?", "obstaculos", "sin"),
  ("¿Qué esquiva el robot?", "pared", "pro"),
  ("¿Cuánto dura la batería?", "dos horas", "lit"),
  ("¿Adónde regresa el robot al terminar?", "base", "sin"),
  ("¿Desde dónde programan los usuarios el robot?", "telefono|movil", "pro"),
  ("¿Qué aconseja el fabricante?", "vaciar|deposito", "sin"),
  ("¿Cuánto cuesta el robot?", "ABST", "abs"),
 ]},
 {"id": "familia", "texto": """
mi primo Óscar vive en Bilbao con su mujer, que se llama Ane. Ella es arquitecta y diseña colegios.
Óscar trabaja en un taller de bicicletas. Lo abrió con un amigo de la universidad hace cuatro años.
tienen una hija pequeña, Lur, que va a una guardería del barrio. Los abuelos la recogen por las tardes.
Ane quiere comprar un piso más grande porque el suyo solo tiene dos habitaciones.
""", "preguntas": [
  ("¿Dónde vive Óscar?", "bilbao", "lit"),
  ("¿Cómo se llama la mujer de Óscar?", "ane", "lit"),
  ("¿Qué diseña Ane?", "colegios", "pro"),
  ("¿Qué proyecta Ane?", "colegios", "sin"),
  ("¿Dónde trabaja Óscar?", "taller", "lit"),
  ("¿Con quién abrió Óscar el taller?", "amigo", "pro"),
  ("¿Quiénes recogen a Lur?", "abuelos", "pro"),
  ("¿Qué quiere adquirir Ane?", "piso", "sin"),
  ("¿Dónde trabaja Lur?", "ABST", "abs"),
 ]},
 {"id": "rio", "texto": """
El río Duero nace en los Picos de Urbión, en la provincia de Soria. Atraviesa la meseta castellana de este a oeste.
En Portugal lo llaman Douro y allí desemboca en el océano Atlántico, junto a la ciudad de Oporto.
Sus orillas acogen viñedos muy antiguos. Los romanos construyeron varios puentes sobre él.
Hoy varias presas lo aprovechan para producir electricidad.
""", "preguntas": [
  ("¿Dónde nace el río Duero?", "urbion|soria", "lit"),
  ("¿Qué atraviesa el Duero?", "meseta", "lit"),
  ("¿Qué cruza el Duero?", "meseta", "sin"),
  ("¿Dónde desemboca el Duero?", "atlantico|oporto", "pro"),
  ("¿Cómo llaman al Duero en Portugal?", "douro", "pro"),
  ("¿Quiénes construyeron puentes sobre el Duero?", "romanos", "pro"),
  ("¿Qué generan las presas?", "electricidad", "sin"),
  ("¿Quiénes edificaron puentes sobre el Duero?", "romanos", "sin"),
  ("¿Cuántos peces viven en el Duero?", "ABST", "abs"),
 ]},
]
