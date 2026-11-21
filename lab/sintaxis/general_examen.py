"""EXAMEN DE GENERALIZACIÓN. Siete textos de temas y estilos distintos, escritos por mí, con sus preguntas.
Escrito ANTES de construir el grafo de conceptos y sin ejecutarlo: se mide UNA vez. Ninguno es del sistema solar (ese texto es el de desarrollo).
Criterio: palabras que deben aparecer en la respuesta (a|b = cualquiera; a;b = todas). ABST = debe decir que no lo sabe."""
T = [
 {"id": "abejas", "estilo": "divulgación (biología)", "texto": """
Las abejas son insectos sociales que viven en colonias muy organizadas. Cada colonia tiene una sola reina, miles de obreras y unos cientos de zánganos.
La reina pone los huevos y puede vivir hasta cinco años. Las obreras recogen el néctar de las flores y lo transforman en miel dentro de la colmena.
La miel se almacena en celdas de cera que las propias obreras construyen. Los zánganos no recogen alimento y mueren después de aparearse con la reina.
Cuando una obrera encuentra flores, avisa a sus compañeras con una danza. Las abejas polinizan muchas plantas mientras buscan néctar.
Sin la polinización, muchos árboles frutales no darían fruto. En invierno la colonia se alimenta de la miel almacenada.
""", "preguntas": [
  ("¿Qué son las abejas?", "insectos"), ("¿Dónde viven las abejas?", "colonias"), ("¿Quién pone los huevos?", "reina"),
  ("¿Qué recogen las obreras?", "nectar"), ("¿Dónde se almacena la miel?", "celdas"), ("¿Cuánto puede vivir la reina?", "cinco años"),
  ("¿Con qué avisa una obrera a sus compañeras?", "danza"), ("¿De qué se alimenta la colonia en invierno?", "miel"), ("¿Qué comen las avispas?", "ABST")]},
 {"id": "imprenta", "estilo": "historia", "texto": """
Johannes Gutenberg inventó la imprenta de tipos móviles en la ciudad de Maguncia hacia 1450. Antes de la imprenta, los monjes copiaban los libros a mano en los monasterios.
Un copista tardaba varios meses en terminar un solo libro. La imprenta permitió producir cientos de ejemplares en pocas semanas.
El primer libro impreso por Gutenberg fue una Biblia. Los libros se abarataron y la lectura llegó a más personas.
Las universidades compraron muchos libros impresos durante el siglo XVI. Algunos gobernantes temían la imprenta porque difundía ideas nuevas.
Los impresores fundaron talleres en Venecia, París y Sevilla. La imprenta cambió la manera de transmitir el conocimiento en Europa.
""", "preguntas": [
  ("¿Quién inventó la imprenta?", "gutenberg"), ("¿Dónde inventó Gutenberg la imprenta?", "maguncia"), ("¿Cuándo inventó Gutenberg la imprenta?", "1450"),
  ("¿Quiénes copiaban los libros antes de la imprenta?", "monjes"), ("¿Cuánto tardaba un copista en terminar un libro?", "meses"),
  ("¿Cuál fue el primer libro impreso por Gutenberg?", "biblia"), ("¿Qué compraron las universidades?", "libros"),
  ("¿Dónde fundaron talleres los impresores?", "venecia|paris|sevilla"), ("¿Por qué temían la imprenta algunos gobernantes?", "ideas"), ("¿Quién inventó el telégrafo?", "ABST")]},
 {"id": "valle", "estilo": "geografía (lugar inventado)", "texto": """
El valle de Arnedal se encuentra al norte de la provincia de Tovera. El río Lizana atraviesa el valle de oeste a este y desemboca en el lago Murel.
En el valle viven unas tres mil personas repartidas en seis pueblos. El pueblo más grande es Castrolín, que tiene un mercado cada sábado.
Los habitantes cultivan manzanos y crían ovejas en las laderas. La carretera que une Castrolín con la capital se construyó en 1962.
En invierno la nieve corta a menudo el puerto de Valdeces. El clima del valle es húmedo y los veranos son suaves.
Un antiguo monasterio domina el valle desde la colina de San Telmo. Cada otoño el valle celebra la fiesta de la sidra.
""", "preguntas": [
  ("¿Dónde se encuentra el valle de Arnedal?", "norte|tovera"), ("¿Qué río atraviesa el valle?", "lizana"), ("¿Dónde desemboca el río Lizana?", "murel"),
  ("¿Cuántas personas viven en el valle?", "tres mil"), ("¿Cuál es el pueblo más grande?", "castrolin"), ("¿Qué cultivan los habitantes?", "manzanos"),
  ("¿Cuándo se construyó la carretera?", "1962"), ("¿Qué corta la nieve en invierno?", "puerto|valdeces"), ("¿Qué celebra el valle cada otoño?", "sidra"), ("¿Cuántos hospitales hay en el valle?", "ABST")]},
 {"id": "bici", "estilo": "técnico (cómo funciona)", "texto": """
Una bicicleta eléctrica combina los pedales con un motor alimentado por una batería. El motor ayuda al ciclista solo cuando este pedalea.
Un sensor mide la fuerza del pedaleo y envía la información al controlador. El controlador regula la potencia que el motor entrega a la rueda.
La batería se recarga en un enchufe normal y tarda unas cuatro horas en cargarse. Con una carga completa, la bicicleta recorre unos ochenta kilómetros.
El motor deja de ayudar cuando la bicicleta supera los veinticinco kilómetros por hora. Los frenos de disco detienen la bicicleta incluso con lluvia.
La pantalla del manillar muestra la velocidad y la carga restante. El fabricante recomienda revisar la cadena cada mil kilómetros.
""", "preguntas": [
  ("¿Qué combina una bicicleta eléctrica?", "pedales|motor"), ("¿Qué mide el sensor?", "fuerza"), ("¿Qué regula el controlador?", "potencia"),
  ("¿Dónde se recarga la batería?", "enchufe"), ("¿Cuánto tarda la batería en cargarse?", "cuatro horas"), ("¿Cuántos kilómetros recorre la bicicleta con una carga completa?", "ochenta"),
  ("¿Qué muestra la pantalla del manillar?", "velocidad|carga"), ("¿Qué detienen los frenos de disco?", "bicicleta"), ("¿Qué recomienda el fabricante?", "cadena"), ("¿Cuánto pesa la bicicleta?", "ABST")]},
 {"id": "cuento", "estilo": "narración", "texto": """
Elvira trabajaba de farera en la isla de Corvo desde hacía veinte años. Cada tarde subía los cien escalones del faro y encendía la lámpara.
Una noche de tormenta, un pesquero perdió el rumbo cerca de los arrecifes. Elvira vio las luces del barco y tocó la sirena durante una hora.
El patrón del pesquero, un hombre llamado Anselmo, reconoció la señal y viró hacia el puerto. Los siete marineros llegaron a tierra sin un rasguño.
Al día siguiente Anselmo le regaló a Elvira una caja de sardinas y una brújula antigua. Elvira guardó la brújula en un cajón de su escritorio.
Desde entonces los pescadores saludan al faro cuando salen al mar. El alcalde de la isla le entregó a Elvira una medalla en verano.
""", "preguntas": [
  ("¿De qué trabajaba Elvira?", "farera"), ("¿Dónde trabajaba Elvira?", "corvo|isla|faro"), ("¿Qué encendía Elvira cada tarde?", "lampara"),
  ("¿Qué perdió el pesquero?", "rumbo"), ("¿Qué tocó Elvira durante una hora?", "sirena"), ("¿Quién reconoció la señal?", "anselmo|patron"),
  ("¿Cuántos marineros llegaron a tierra?", "siete"), ("¿Qué le regaló Anselmo a Elvira?", "sardinas|brujula"), ("¿Dónde guardó Elvira la brújula?", "cajon"),
  ("¿Quién le entregó una medalla a Elvira?", "alcalde"), ("¿Cómo se llamaba el perro de Elvira?", "ABST")]},
 {"id": "empresa", "estilo": "nota de prensa (empresa inventada)", "texto": """
La empresa Talvera anunció ayer la apertura de una fábrica de paneles solares en Albacete. La nueva planta empleará a trescientas personas a partir de marzo.
La compañía invertirá cuarenta millones de euros en la construcción. La directora general, Marta Olmedo, presentó el proyecto en el ayuntamiento.
El alcalde agradeció la inversión y prometió mejorar los accesos por carretera. Talvera exporta la mitad de su producción a Portugal y Francia.
La fábrica producirá dos mil paneles al día cuando funcione a pleno rendimiento. Los sindicatos pidieron que los contratos sean indefinidos.
La empresa fue fundada en 2009 por dos ingenieros de Valencia. El año pasado Talvera facturó ciento veinte millones de euros.
""", "preguntas": [
  ("¿Qué anunció la empresa Talvera?", "apertura|fabrica"), ("¿Dónde abrirá Talvera la fábrica?", "albacete"), ("¿A cuántas personas empleará la nueva planta?", "trescientas"),
  ("¿Cuánto invertirá la compañía?", "cuarenta millones"), ("¿Quién presentó el proyecto?", "olmedo|directora"), ("¿Qué prometió el alcalde?", "accesos"),
  ("¿A dónde exporta Talvera su producción?", "portugal|francia"), ("¿Cuántos paneles producirá la fábrica al día?", "dos mil"), ("¿Qué pidieron los sindicatos?", "contratos|indefinidos"),
  ("¿Cuándo fue fundada la empresa?", "2009"), ("¿Quién es el dueño de la fábrica de Lugo?", "ABST")]},
 {"id": "charla", "estilo": "conversación (el usuario cuenta cosas, con descuido)", "texto": """
mi hermana Lola vive en Granada y trabaja en un hospital. El marido de Lola se llama Íñigo y es cocinero en un hotel.
tienen dos hijos que estudian en el mismo colegio. el mayor, que se llama Bruno, toca el violín desde los seis años.
a la pequeña le encantan los caballos y monta todos los sábados. Mis padres visitan a Lola cada verano y se quedan dos semanas.
el año pasado Íñigo abrió un restaurante cerca de la catedral. Lola quiere mudarse a una casa con jardín porque el piso es pequeño.
Bruno ganó un concurso de música en mayo. yo voy a Granada en tren cuando tengo vacaciones.
""", "preguntas": [
  ("donde vive Lola?", "granada"), ("donde trabaja Lola?", "hospital"), ("como se llama el marido de Lola?", "iñigo"), ("que es Íñigo?", "cocinero"),
  ("que toca Bruno?", "violin"), ("que le encanta a la pequeña?", "caballos"), ("quien visita a Lola cada verano?", "padres"),
  ("que abrió Íñigo el año pasado?", "restaurante"), ("que ganó Bruno?", "concurso"), ("a donde quiere mudarse Lola?", "casa"), ("donde vive Bruno ahora?", "ABST")]},
]
