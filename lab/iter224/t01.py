"""2.24 T01 · diccionario: preguntas con otras palabras y trampas (solo las sondas que la 2.24 acierta; red de regresión)."""
D = [{'cat': 'aprender-diccionario',
  'id': 'apr224-ddev-la panadería',
  'turnos': [('Te voy a leer un texto sobre la panadería.\n'
              'El pan se elabora con harina, agua, sal y levadura.\n'
              'Los panaderos amasan la mezcla durante veinte minutos.\n'
              'Después dejan reposar la masa en un lugar templado.\n'
              'La masa crece gracias a la levadura.\n'
              'Los panaderos cuecen el pan en un horno de leña.\n'
              'El pan recién hecho es crujiente y huele muy bien.\n'
              'Los panaderos empiezan a trabajar de madrugada.\n'
              'La panadería abre a las siete de la mañana.\n'
              'Los clientes compran el pan temprano.\n'
              'El pan duro se aprovecha para hacer torrijas.',
              ''),
             ('¿con qué se hace el pan?', 'harina'),
             ('¿con qué se fabrica el pan?', 'harina'),
             ('¿quiénes amasan la mezcla?', 'panadero*'),
             ('¿dónde dejan descansar la masa?', 'templado'),
             ('¿gracias a qué aumenta la masa?', 'levadura'),
             ('¿dónde hornean el pan los panaderos?', 'horno'),
             ('¿dónde venden el pan los panaderos?', 'ABST'),
             ('¿cómo es el pan recién elaborado?', 'crujiente'),
             ('¿cuándo comienzan a trabajar los panaderos?', 'madrugada'),
             ('¿cuándo terminan de trabajar los panaderos?', 'ABST'),
             ('¿a qué hora cierra la panadería?', 'ABST'),
             ('¿cuándo adquieren el pan los clientes?', 'temprano'),
             ('¿para qué se tira el pan duro?', 'ABST')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-ddev-el faro',
  'turnos': [('Te voy a leer un texto sobre el faro.\n'
              'Un faro es una torre alta situada en la costa.\n'
              'Su luz guía a los barcos durante la noche.\n'
              'El farero es la persona que cuida el faro.\n'
              'El farero enciende la lámpara al anochecer.\n'
              'La lámpara gira sin parar.\n'
              'Los marineros ven la luz desde muy lejos.\n'
              'Cuando hay niebla, el faro hace sonar una sirena.\n'
              'Los faros antiguos quemaban aceite.\n'
              'Hoy casi todos los faros funcionan con electricidad.\n'
              'El farero sube ciento veinte escalones cada día.',
              ''),
             ('¿dónde está ubicado un faro?', 'costa'),
             ('¿dónde se encuentra un faro?', 'costa'),
             ('¿qué orienta a los barcos durante la noche?', 'luz|faro'),
             ('¿a quién guía la luz del faro?', 'barcos'),
             ('¿quién se ocupa del faro?', 'farero'),
             ('¿cuándo prende la lámpara el farero?', 'anochecer'),
             ('¿cuándo apaga la lámpara el farero?', 'ABST'),
             ('¿qué da vueltas sin parar?', 'lampara'),
             ('¿desde dónde divisan la luz los marineros?', 'lejos'),
             ('¿quiénes observan la luz desde muy lejos?', 'marineros'),
             ('¿qué hace sonar el faro cuando hay bruma?', 'sirena'),
             ('¿qué quemaban los faros viejos?', 'aceite'),
             ('¿qué quemaban los faros modernos?', 'ABST'),
             ('¿con qué marchan hoy casi todos los faros?', 'electricidad')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-ddev-la granja',
  'turnos': [('Te voy a leer un texto sobre la granja.\n'
              'Los granjeros crían vacas, cerdos y gallinas.\n'
              'Las vacas dan leche dos veces al día.\n'
              'Los granjeros ordeñan las vacas al amanecer.\n'
              'Las gallinas ponen huevos en el gallinero.\n'
              'Los cerdos comen pienso y restos de verduras.\n'
              'El granjero guarda el heno en el granero.\n'
              'El perro vigila el rebaño de ovejas.\n'
              'En verano los granjeros recogen el trigo.\n'
              'El tractor arrastra el arado por el campo.\n'
              'Los granjeros venden la leche a una fábrica de quesos.',
              ''),
             ('¿quiénes crían vacas?', 'granjero*'),
             ('¿cuántas veces al día producen leche las vacas?', 'dos'),
             ('¿cuándo ordeñan las vacas los granjeros?', 'amanecer'),
             ('¿dónde depositan los huevos las gallinas?', 'gallinero'),
             ('¿dónde comen las gallinas?', 'ABST'),
             ('¿qué ingieren los cerdos?', 'pienso|restos|verduras'),
             ('¿de qué se alimentan los cerdos?', 'pienso|restos|verduras'),
             ('¿dónde almacena el heno el granjero?', 'granero'),
             ('¿dónde conserva el heno el granjero?', 'granero'),
             ('¿quién cuida el rebaño de ovejas?', 'perro'),
             ('¿quién protege el rebaño de ovejas?', 'perro'),
             ('¿cuándo cosechan el trigo los granjeros?', 'verano'),
             ('¿cuándo siembran el trigo los granjeros?', 'ABST'),
             ('¿qué tira del arado?', 'tractor'),
             ('¿a quién compran la leche los granjeros?', 'ABST'),
             ('¿a quién venden la leche los granjeros?', 'fabrica')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-ddev-el hospital',
  'turnos': [('Te voy a leer un texto sobre el hospital.\n'
              'En el hospital se cura a los enfermos.\n'
              'Los médicos examinan a los pacientes cada mañana.\n'
              'Las enfermeras reparten las medicinas.\n'
              'Los cirujanos operan en el quirófano.\n'
              'Las ambulancias trasladan a los heridos con rapidez.\n'
              'Los visitantes esperan en una sala grande.\n'
              'El hospital nunca cierra.\n'
              'Los celadores empujan las camillas por los pasillos.\n'
              'Los recién nacidos duermen en la planta tercera.',
              ''),
             ('¿dónde se sana a los enfermos?', 'hospital'),
             ('¿dónde se cura a los pacientes?', 'hospital'),
             ('¿cuándo revisan los médicos a los pacientes?', 'manana'),
             ('¿quiénes examinan a los enfermos cada mañana?', 'medicos'),
             ('¿quiénes distribuyen las medicinas?', 'enfermera*'),
             ('¿quiénes reparten los medicamentos?', 'enfermera*'),
             ('¿quiénes fabrican las medicinas?', 'ABST'),
             ('¿dónde operan los cirujanos?', 'quirofano'),
             ('¿qué vehículos transportan a los heridos?', 'ambulancia*'),
             ('¿cómo llevan las ambulancias a los heridos?', 'rapidez|rapid*'),
             ('¿dónde aguardan los visitantes?', 'sala'),
             ('¿quiénes esperan en una sala amplia?', 'visitantes'),
             ('¿quiénes mueven las camillas por los pasillos?', 'celadores'),
             ('¿quiénes limpian los pasillos?', 'ABST'),
             ('¿dónde descansan los recién nacidos?', 'tercera|planta'),
             ('¿dónde comen los recién nacidos?', 'ABST')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-ddev-el río',
  'turnos': [('Te voy a leer un texto sobre el río.\n'
              'El río nace en una montaña muy alta.\n'
              'Sus aguas bajan frías y limpias.\n'
              'El río atraviesa tres pueblos.\n'
              'Los pescadores atrapan truchas en el río.\n'
              'Un puente de piedra une las dos orillas.\n'
              'En primavera el río crece por el deshielo.\n'
              'Los niños se bañan en una poza tranquila.\n'
              'El molino usa la fuerza del agua para moler el grano.\n'
              'El río termina en el mar.',
              ''),
             ('¿dónde nace el río?', 'montana'),
             ('¿cómo descienden las aguas del río?', 'frias|limpias'),
             ('¿cuántos pueblos cruza el río?', 'tres|3'),
             ('¿qué capturan los pescadores en el río?', 'truchas'),
             ('¿qué pescan los pescadores en el río?', 'truchas'),
             ('¿qué cocinan los pescadores?', 'ABST'),
             ('¿qué conecta las dos orillas?', 'puente'),
             ('¿qué junta las dos riberas?', 'puente'),
             ('¿cuándo aumenta el río?', 'primavera'),
             ('¿cuándo se seca el río?', 'ABST'),
             ('¿dónde se bañan los niños?', 'poza'),
             ('¿quiénes se bañan en una poza calmada?', 'ninos'),
             ('¿qué emplea el molino para moler el grano?', 'fuerza|agua'),
             ('¿qué utiliza el molino para triturar el grano?', 'fuerza|agua'),
             ('¿dónde acaba el río?', 'mar'),
             ('¿dónde finaliza el río?', 'mar'),
             ('¿dónde empieza el mar?', 'ABST')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-ddev-la escuela de música',
  'turnos': [('Te voy a leer un texto sobre la escuela de música.\n'
              'En la escuela de música los alumnos aprenden a tocar instrumentos.\n'
              'La profesora enseña solfeo los lunes.\n'
              'Los alumnos practican dos horas cada tarde.\n'
              'El director elige las canciones del concierto.\n'
              'El concierto se celebra en junio.\n'
              'Los padres aplauden al final.\n'
              'El piano pesa mucho y no se mueve nunca.\n'
              'Los violines se guardan en un armario cerrado.\n'
              'La escuela regala una flauta a los nuevos alumnos.',
              ''),
             ('¿qué aprenden los estudiantes en la escuela de música?', 'tocar|instrumentos'),
             ('¿qué estudia la profesora los lunes?', 'ABST'),
             ('¿cuánto ensayan los alumnos cada tarde?', 'dos'),
             ('¿cuánto tiempo practican los alumnos cada tarde?', 'dos'),
             ('¿quién escoge las canciones del concierto?', 'director'),
             ('¿quién selecciona las canciones del concierto?', 'director'),
             ('¿cuándo tiene lugar el concierto?', 'junio'),
             ('¿cuándo silban los padres?', 'ABST'),
             ('¿dónde se almacenan los violines?', 'armario'),
             ('¿dónde se arreglan los violines?', 'ABST'),
             ('¿qué obsequia la escuela a los nuevos alumnos?', 'flauta'),
             ('¿qué da la escuela a los nuevos alumnos?', 'flauta'),
             ('¿qué vende la escuela a los nuevos alumnos?', 'ABST')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-dtest-la biblioteca del barrio',
  'turnos': [('Te voy a leer un texto sobre la biblioteca del barrio.\n'
              'La biblioteca del barrio presta libros a los vecinos.\n'
              'La bibliotecaria coloca los libros en las estanterías.\n'
              'Los niños escuchan cuentos los sábados.\n'
              'Los estudiantes repasan sus apuntes en la sala grande.\n'
              'Un vigilante cierra la puerta a las nueve.\n'
              'Los libros viejos se reparan en el sótano.\n'
              'Los vecinos devuelven los libros en un buzón.\n'
              'El carné de la biblioteca cuesta dos euros.',
              ''),
             ('¿a quién deja libros la biblioteca del barrio?', 'vecinos'),
             ('¿quién ordena los libros en las estanterías?', 'bibliotecaria'),
             ('¿cuándo oyen cuentos los niños?', 'sabados'),
             ('¿qué escuchan los chicos los sábados?', 'cuentos'),
             ('¿cuándo escriben cuentos los niños?', 'ABST'),
             ('¿dónde estudian sus apuntes los estudiantes?', 'sala'),
             ('¿quiénes repasan sus notas en la sala grande?', 'estudiantes'),
             ('¿a qué hora cierra la puerta un guardia?', 'nueve|9'),
             ('¿a qué hora abre la puerta un vigilante?', 'ABST'),
             ('¿dónde se arreglan los libros viejos?', 'sotano'),
             ('¿dónde se reparan los libros antiguos?', 'sotano'),
             ('¿dónde entregan los libros los vecinos?', 'buzon'),
             ('¿dónde compran los libros los vecinos?', 'ABST'),
             ('¿cuánto vale el carné de la biblioteca?', 'dos|2')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-dtest-el taller de coches',
  'turnos': [('Te voy a leer un texto sobre el taller de coches.\n'
              'Los mecánicos arreglan los coches averiados.\n'
              'Una grúa trae los coches que no arrancan.\n'
              'El jefe del taller calcula el precio de cada reparación.\n'
              'Los mecánicos cambian el aceite cada año.\n'
              'Las ruedas gastadas se tiran a un contenedor.\n'
              'El aprendiz limpia las herramientas al terminar.\n'
              'Los clientes aguardan en una sala pequeña.\n'
              'El taller abre a las ocho.',
              ''),
             ('¿quiénes reparan los coches averiados?', 'mecanico*'),
             ('¿quiénes arreglan los automóviles averiados?', 'mecanico*'),
             ('¿quiénes conducen los coches averiados?', 'ABST'),
             ('¿qué lleva al taller los coches que no arrancan?', 'grua'),
             ('¿quién calcula el coste de cada reparación?', 'jefe'),
             ('¿quién paga el precio de cada reparación?', 'ABST'),
             ('¿cada cuánto sustituyen el aceite los mecánicos?', 'ano'),
             ('¿qué reemplazan los mecánicos cada año?', 'aceite'),
             ('¿dónde se fabrican las ruedas?', 'ABST'),
             ('¿cuándo lava las herramientas el aprendiz?', 'terminar'),
             ('¿quién limpia los utensilios al terminar?', 'aprendiz'),
             ('¿dónde esperan los clientes?', 'sala'),
             ('¿dónde trabajan los clientes?', 'ABST')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-dtest-la huerta',
  'turnos': [('Te voy a leer un texto sobre la huerta.\n'
              'Los hortelanos cultivan tomates y lechugas.\n'
              'Riegan la huerta al atardecer.\n'
              'Un espantapájaros asusta a los pájaros.\n'
              'Los tomates maduran en verano.\n'
              'Los hortelanos arrancan las malas hierbas con una azada.\n'
              'La cosecha se guarda en cajas de madera.\n'
              'Los caracoles devoran las hojas tiernas.\n'
              'El pozo proporciona agua todo el año.',
              ''),
             ('¿qué cocinan los hortelanos?', 'ABST'),
             ('¿cuándo mojan la huerta los hortelanos?', 'atardecer'),
             ('¿cuándo riegan la huerta los hortelanos?', 'atardecer'),
             ('¿qué asusta a las aves?', 'espantapajaros'),
             ('¿qué alimenta a los pájaros?', 'ABST'),
             ('¿cuándo se siembran los tomates?', 'ABST'),
             ('¿cuándo maduran los tomates?', 'verano'),
             ('¿con qué quitan las malas hierbas los hortelanos?', 'azada'),
             ('¿con qué herramienta arrancan las malas hierbas?', 'azada'),
             ('¿dónde se almacena la cosecha?', 'cajas'),
             ('¿dónde se mete la cosecha?', 'cajas'),
             ('¿qué comen los caracoles?', 'hojas'),
             ('¿quiénes se comen las hojas tiernas?', 'caracoles'),
             ('¿qué da agua todo el año?', 'pozo'),
             ('¿qué suministra agua todo el año?', 'pozo'),
             ('¿qué gasta agua todo el año?', 'ABST')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-dtest-el teatro',
  'turnos': [('Te voy a leer un texto sobre el teatro.\n'
              'Los actores ensayan la obra por las tardes.\n'
              'La directora corrige a los actores.\n'
              'El público aplaude cuando cae el telón.\n'
              'Los decorados se construyen con madera y cartón.\n'
              'La función comienza a las ocho.\n'
              'El apuntador susurra el texto a los actores.\n'
              'Las entradas se venden en la taquilla.\n'
              'Los trajes se cosen a mano.',
              ''),
             ('¿cuándo escriben la obra los actores?', 'ABST'),
             ('¿quién rectifica a los actores?', 'directora'),
             ('¿a quién corrige la directora?', 'actores'),
             ('¿cuándo aplauden los espectadores?', 'telon'),
             ('¿quién aplaude cuando baja el telón?', 'publico'),
             ('¿con qué se hacen los decorados?', 'madera|carton'),
             ('¿con qué se fabrican los decorados?', 'madera|carton'),
             ('¿a qué hora empieza la función?', 'ocho|8'),
             ('¿a qué hora se inicia la función?', 'ocho|8'),
             ('¿a qué hora acaba la función?', 'ABST'),
             ('¿quién murmura el texto a los actores?', 'apuntador'),
             ('¿quién grita el texto a los actores?', 'ABST')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-dtest-la estación de esquí',
  'turnos': [('Te voy a leer un texto sobre la estación de esquí.\n'
              'Los esquiadores bajan por las pistas nevadas.\n'
              'Un telesilla sube a los esquiadores hasta la cima.\n'
              'Los monitores enseñan a los principiantes.\n'
              'Las máquinas alisan la nieve cada noche.\n'
              'Los socorristas auxilian a los heridos.\n'
              'Los esquiadores alquilan las botas en una tienda.\n'
              'La estación cierra cuando hay ventisca.\n'
              'El refugio ofrece sopa caliente.',
              ''),
             ('¿por dónde descienden los esquiadores?', 'pistas'),
             ('¿por dónde pasean los esquiadores?', 'ABST'),
             ('¿qué lleva a los esquiadores hasta la cumbre?', 'telesilla'),
             ('¿hasta dónde sube el telesilla a los esquiadores?', 'cima'),
             ('¿quiénes instruyen a los principiantes?', 'monitores'),
             ('¿a quiénes enseñan los monitores?', 'principiantes'),
             ('¿quiénes examinan a los principiantes?', 'ABST'),
             ('¿cuándo derriten la nieve las máquinas?', 'ABST'),
             ('¿quiénes socorren a los heridos?', 'socorristas'),
             ('¿dónde venden las botas los esquiadores?', 'ABST'),
             ('¿cuándo cierra la estación?', 'ventisca'),
             ('¿qué pasa en la estación cuando hay ventisca?', 'cierra'),
             ('¿qué sirve el refugio?', 'sopa')]},
 {'cat': 'aprender-diccionario',
  'id': 'apr224-dtest-la imprenta',
  'turnos': [('Te voy a leer un texto sobre la imprenta.\n'
              'La imprenta imprime periódicos cada madrugada.\n'
              'Los operarios vigilan las máquinas.\n'
              'El papel llega en rollos enormes.\n'
              'Una cuchilla corta las hojas.\n'
              'Los camiones distribuyen los periódicos por la ciudad.\n'
              'La tinta se seca en pocos segundos.\n'
              'El corrector revisa los textos antes de imprimir.\n'
              'Los periódicos sobrantes se reciclan.',
              ''),
             ('¿qué imprime la imprenta cada madrugada?', 'periodicos'),
             ('¿cuándo reparte periódicos la imprenta?', 'ABST'),
             ('¿quiénes controlan las máquinas?', 'operarios'),
             ('¿quiénes supervisan las máquinas?', 'operarios'),
             ('¿quiénes fabrican las máquinas?', 'ABST'),
             ('¿cómo viene el papel?', 'rollos'),
             ('¿en qué llega el papel?', 'rollos'),
             ('¿qué recorta las hojas?', 'cuchilla'),
             ('¿qué corta las páginas?', 'cuchilla'),
             ('¿qué reparte los periódicos por la ciudad?', 'camiones'),
             ('¿qué vehículos llevan los periódicos por la ciudad?', 'camiones'),
             ('¿cuánto cuesta la tinta?', 'ABST'),
             ('¿quién comprueba los textos antes de imprimir?', 'corrector'),
             ('¿quién repasa los textos antes de imprimir?', 'corrector'),
             ('¿quién lee los periódicos sobrantes?', 'ABST')]},
 {'cat': 'diccionario-charla',
  'id': 'apr224-charla-1',
  'turnos': [('Lucía tiene una bicicleta.', ''), ('Bici significa bicicleta.', ''), ('¿Tiene Lucía una bici?', '^si')]}]
