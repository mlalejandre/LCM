"""Tanda 7 (desarrollo): conceptos de fábrica, capas de abstracción, excepciones y su mezcla con lo que cuenta la persona."""
from lab.banco import correr, imprime
D = [
 {"id": "t7-taxo1", "cat": "taxonomia", "turnos": [
   ("¿Un gato es un animal?", "^si"), ("¿Es un gato un mamífero?", "^si"), ("¿Un gato es una planta?", "^no"), ("¿Una sardina es un pez?", "^si"), ("¿Es una sardina un mamífero?", "^no;pez"),
   ("¿Qué es una trucha?", "pez"), ("¿Un roble es un árbol?", "^si"), ("¿Un roble es una planta?", "^si"), ("¿Un roble es un animal?", "^no"), ("¿Qué es un violín?", "instrumento")]},
 {"id": "t7-taxo2", "cat": "taxonomia", "turnos": [
   ("¿Una silla es un mueble?", "^si"), ("¿Es una silla un vehículo?", "^no;mueble"), ("¿Una camisa es una prenda?", "^si"), ("¿El hierro es un metal?", "^si"), ("¿Es el fútbol un deporte?", "^si"),
   ("¿Una pera es una verdura?", "^no;fruta"), ("¿Qué es una lechuga?", "verdura"), ("¿Un martillo es una herramienta?", "^si"), ("¿Qué tipo de cosa es un tenedor?", "utensilio"), ("¿Un plimbo es un animal?", "ABST")]},
 {"id": "t7-ejemplos", "cat": "ejemplos", "turnos": [
   ("Dime tres animales.", "ANY"), ("Nombra dos frutas.", "ANY"), ("¿Qué deportes conoces?", "futbol|tenis|baloncesto|natacion"), ("Dime un color.", "rojo|azul|verde|amarillo|blanco|negro"),
   ("Dime otro.", "ANY"), ("Ponme un ejemplo de mueble.", "silla|mesa|cama|sofa|armario"), ("¿Qué instrumentos conoces?", "guitarra|piano|violin"), ("Dime cuatro verduras.", "tomate|lechuga;!manzana;!pera"),
   ("Dime tres plimbos.", "ABST")]},
 {"id": "t7-props1", "cat": "propiedades", "turnos": [
   ("¿Los perros ladran?", "^si"), ("¿Ladra un gato?", "^no;maull*|maúll*"), ("¿Los gatos maúllan?", "^si"), ("¿Vuelan los pájaros?", "^si"), ("¿Vuela un pingüino?", "^no"),
   ("¿Un pingüino es un ave?", "^si"), ("¿Los peces nadan?", "^si"), ("¿Tienen plumas los peces?", "^no"), ("¿Los peces tienen escamas?", "^si"), ("¿Un caballo vuela?", "^no")]},
 {"id": "t7-props2", "cat": "propiedades", "turnos": [
   ("¿Cuántas ruedas tiene una bicicleta?", "dos|2"), ("¿Cuántas ruedas tiene un coche?", "cuatro|4"), ("¿Tiene motor una bicicleta?", "^no"), ("¿Una moto tiene motor?", "^si"),
   ("¿Cuántas patas tiene un insecto?", "seis|6"), ("¿Cuántas patas tiene una araña?", "ocho|8"), ("¿Una araña es un insecto?", "^no;aracnido"), ("¿Los aviones vuelan?", "^si"),
   ("¿Vuela un barco?", "ABST|^no"), ("¿Un barco flota?", "^si"), ("¿Cuántas ruedas tiene un plimbo?", "ABST")]},
 {"id": "t7-props3", "cat": "propiedades", "turnos": [
   ("¿Qué animales vuelan?", "aves|pajaros;!perros"), ("¿Qué animal maúlla?", "gato"), ("¿Qué animal da leche?", "vaca"), ("¿Qué come una vaca?", "hierba"), ("¿Dónde viven los peces?", "agua"),
   ("¿Qué hace una abeja?", "miel|vuela*|pica*"), ("¿Una mesa respira?", "^no"), ("¿Una planta habla?", "^no"), ("¿Las personas hablan?", "^si"), ("¿Un perro habla?", "^no")]},
 # 2.14: en «una silla y un perro», «los dos tienen patas» es correcto (criterio corregido a mano)
 {"id": "t7-comun", "cat": "abstraccion", "turnos": [
   ("¿Qué tienen en común un perro y un gato?", "mamifero*|animal*"), ("¿Qué tienen en común una manzana y una pera?", "fruta*"), ("¿En qué se parecen un coche y un tren?", "vehiculo*"),
   ("¿En qué se diferencian un perro y un pez?", "mamifero|pez|ladra*|nada*|pelo|escamas"), ("¿Qué tienen en común una rosa y un pino?", "planta*"),
   ("¿Qué tienen en común una silla y un perro?", "ABST|cosa*|objeto*|patas"), ("¿Qué tienen en común un perro y un roble?", "seres vivos|ser vivo"), ("¿Qué tienen en común un plimbo y un gato?", "ABST")]},
 {"id": "t7-partes", "cat": "partes", "turnos": [
   ("¿Qué partes tiene un árbol?", "tronco;ramas;hojas"), ("¿Tiene ramas un árbol?", "^si"), ("¿Qué partes tiene una bicicleta?", "ruedas;pedales"), ("¿De qué forma parte un pétalo?", "flor"),
   ("¿Cuál es el contrario de caro?", "barato"), ("¿Qué es lo contrario de subir?", "bajar"), ("¿Cuál es el opuesto de limpio?", "sucio"), ("¿Cuál es el contrario de plimbo?", "ABST")]},
 {"id": "t7-mezcla1", "cat": "mezcla", "turnos": [
   ("Tengo una gata que se llama Nala.", "ACK"), ("¿Nala es un animal?", "^si"), ("¿Nala es un mamífero?", "^si"), ("¿Nala ladra?", "^no|ABST"), ("¿Nala tiene cuatro patas?", "^si"),
   ("¿Nala vuela?", "^no"), ("¿Nala es una planta?", "^no"), ("¿De qué color es Nala?", "ABST"), ("Nala es negra.", "ACK"), ("¿De qué color es mi gata?", "negr*")]},
 {"id": "t7-mezcla2", "cat": "mezcla", "turnos": [
   ("Mi vecino tiene un loro llamado Paco.", "ACK"), ("¿Paco es un ave?", "^si"), ("¿Paco tiene plumas?", "^si"), ("¿Paco vuela?", "^si"), ("Paco no vuela porque tiene un ala rota.", "ACK"),
   ("¿Paco vuela?", "^no"), ("¿Por qué no vuela Paco?", "ala"), ("¿Los loros vuelan?", "^si"), ("¿Quién es el dueño de Paco?", "vecino")]},
 {"id": "t7-mezcla3", "cat": "mezcla", "turnos": [
   ("Ayer comí una manzana y un trozo de queso.", "ACK"), ("¿Comí fruta ayer?", "^si|manzana"), ("¿Comí verdura ayer?", "ABST|^no"), ("Mi hermano toca el violín.", "ACK"),
   ("¿Mi hermano toca algún instrumento?", "^si|violin"), ("¿Qué instrumento toca mi hermano?", "violin"), ("Mi padre es carpintero.", "ACK"), ("¿Cuál es la profesión de mi padre?", "carpintero"),
   ("¿Mi padre es médico?", "^no")]},
 {"id": "t7-excep", "cat": "excepciones", "turnos": [
   ("Los plimbos son animales.", "ACK"), ("Los plimbos vuelan.", "ACK"), ("Un zurco es un plimbo.", "ACK"), ("¿Un zurco vuela?", "^si"), ("Los zurcos no vuelan.", "ACK"),
   ("¿Un zurco vuela?", "^no"), ("¿Los plimbos vuelan?", "^si"), ("¿Un zurco es un animal?", "^si"), ("Dime un plimbo.", "zurco")]},
 {"id": "t7-ensena", "cat": "excepciones", "turnos": [
   ("Un kiwi es un pájaro.", "ACK"), ("Los kiwis no vuelan.", "ACK"), ("¿Vuela un kiwi?", "^no"), ("¿Vuelan los pájaros?", "^si"), ("¿Un kiwi tiene plumas?", "^si"),
   ("¿Por qué?", "ave*|pajaro*|fabrica"), ("¿Un gorrión vuela?", "^si")]},
 {"id": "t7-explica", "cat": "abstraccion", "turnos": [
   ("¿Un delfín es un pez?", "^no;mamifero"), ("¿Por qué?", "mamifero|fabrica"), ("¿Los delfines nadan?", "^si"), ("¿Un delfín tiene pelo?", "^no"), ("¿Un murciélago vuela?", "^si"),
   ("¿Un murciélago es un ave?", "^no;mamifero"), ("¿Quién te ha enseñado eso?", "fabrica|ANY")]},
]
if __name__ == "__main__":
    f, r = correr(D, verboso=True)
    imprime(r, "TANDA 7")
