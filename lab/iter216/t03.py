N = "!no lo he entendido"
D = [{"id": "z01", "cat": "razonar", "turnos": [
 ("todos los pingüinos son aves", N), ("Pipo es un pingüino", N), ("¿Pipo es un ave?", "^si"), ("¿Pipo tiene plumas?", "^si"), ("¿Pipo es un pez?", "^no"),
 ("ningún pez tiene pulmones", "!los peces tienen"), ("Nemo es un pez", N), ("¿Nemo tiene pulmones?", "^no"),
 ("Rosa es más rápida que Inés", N), ("Inés es más rápida que Carla", N), ("¿quién es la más rápida?", "rosa"), ("¿quién es la más lenta?", "carla"),
 ("Leo y Max pesan lo mismo", N), ("Leo pesa 70 kilos", N), ("¿cuánto pesa Max?", "70"), ("Ana tiene 41 años", N), ("Ana tiene la misma edad que Bea", N), ("¿cuántos años tiene Bea?", "41")]},
 {"id": "z02", "cat": "razonar", "turnos": [
 ("si nieva, no cojo el coche", N), ("hoy nieva", N), ("¿cojo el coche hoy?", "^no"), ("el mando está en el sofá o en la mesa", N), ("no está en el sofá", N), ("¿dónde está el mando?", "mesa"),
 ("suspendí porque no estudié", N), ("¿por qué suspendí?", "estudi*"), ("primero me vestí, después tomé un café y luego cogí el tren", N), ("¿qué hice después de vestirme?", "cafe"),
 ("¿qué hice antes de coger el tren?", "cafe"), ("¿qué hice primero?", "vest*"), ("¿cogí el tren antes de vestirme?", "^no"),
 ("las gafas están dentro del estuche y el estuche está en la mochila", N), ("¿las gafas están en la mochila?", "^si"), ("¿las gafas están en el coche?", "ABST|^no"),
 ("Pedro es el padre de Ana y Ana es la madre de Luis", N), ("¿quién es el abuelo de Luis?", "pedro"),
 ("tenía 20 euros, gasté 5 y luego me dieron 3", N), ("¿cuánto dinero tengo ahora?", "18"), ("tengo 2 perros y 3 gatos", "!5"), ("¿cuántos perros tengo?", "2|dos")]}]
