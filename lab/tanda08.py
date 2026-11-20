"""Tanda 8 (desarrollo): negativas, cuantificadores negativos y resistencia a inventar."""
from lab.banco import correr, imprime
D = [
 {"id": "t8-neg1", "cat": "negacion", "turnos": [
   ("Ana no tiene coche.", "ACK"), ("¿Tiene Ana coche?", "^no"), ("¿Ana tiene coche?", "^no"), ("¿Qué no tiene Ana?", "coche"), ("Luis tiene coche.", "ACK"),
   ("¿Quién no tiene coche?", "ana;!luis"), ("¿Quién tiene coche?", "luis;!ana"), ("¿Tiene Ana moto?", "ABST")]},
 {"id": "t8-neg2", "cat": "negacion", "turnos": [
   ("No me gusta el pescado.", "ACK"), ("Me gusta la carne.", "ACK"), ("¿Me gusta el pescado?", "^no"), ("¿Qué no me gusta?", "pescado;!carne"), ("¿Qué me gusta?", "carne;!pescado"),
   ("¿Me gusta la fruta?", "ABST"), ("Tampoco me gusta el queso.", "ACK"), ("¿Me gusta el queso?", "^no"), ("¿Qué cosas no me gustan?", "pescado;queso")]},
 {"id": "t8-neg3", "cat": "negacion", "turnos": [
   ("Marta no vive en Sevilla.", "ACK"), ("¿Vive Marta en Sevilla?", "^no"), ("¿Dónde vive Marta?", "ABST"), ("Marta vive en Cádiz.", "ACK"), ("¿Dónde vive Marta?", "cadiz"),
   ("¿No vive Marta en Cádiz?", "^si;cadiz"), ("¿No vive Marta en Sevilla?", "^no"), ("¿Marta vive en Huelva?", "^no;cadiz")]},
 {"id": "t8-nunca", "cat": "negacion", "turnos": [
   ("Nunca he estado en Roma.", "ACK"), ("¿He estado en Roma?", "^no|nunca"), ("Mi hermano nunca come carne.", "ACK"), ("¿Mi hermano come carne?", "^no|nunca"),
   ("Jamás bebo café.", "ACK"), ("¿Bebo café?", "^no|nunca|jamas"), ("¿Bebo té?", "ABST")]},
 {"id": "t8-nadie", "cat": "cuantificador", "turnos": [
   ("Nadie de mi familia fuma.", "ACK"), ("¿Fuma alguien de mi familia?", "^no|nadie"), ("No tengo hermanos.", "ACK"), ("¿Tengo hermanos?", "^no"), ("¿Cuántos hermanos tengo?", "ningun*|cero|no tienes"),
   ("¿Cómo se llama mi hermano?", "no tienes|ningun*|ABST"), ("No tengo ninguna mascota.", "ACK"), ("¿Tengo mascotas?", "^no"), ("¿Tengo perro?", "^no|ABST")]},
 {"id": "t8-nini", "cat": "cuantificador", "turnos": [
   ("Pedro no tiene ni coche ni moto.", "ACK"), ("¿Tiene Pedro coche?", "^no"), ("¿Tiene Pedro moto?", "^no"), ("¿Tiene Pedro bicicleta?", "ABST"),
   ("No bebo ni vino ni cerveza.", "ACK"), ("¿Bebo cerveza?", "^no"), ("¿Bebo vino?", "^no"), ("¿Bebo agua?", "ABST")]},
 {"id": "t8-yano", "cat": "negacion", "turnos": [
   ("Trabajo en un banco.", "ACK"), ("Ya no trabajo en el banco.", "ACK"), ("¿Trabajo en un banco?", "^no|ya no"), ("¿Trabajaba en un banco?", "^si|antes"), ("¿Dónde trabajo ahora?", "ABST"),
   ("Ahora trabajo en una librería.", "ACK"), ("¿Dónde trabajo?", "libreria;!banco")]},
 {"id": "t8-ser", "cat": "negacion", "turnos": [
   ("Julia no es médica.", "ACK"), ("¿Julia es médica?", "^no"), ("¿Qué es Julia?", "ABST|no es medic*"), ("Julia es enfermera.", "ACK"), ("¿Es Julia médica?", "^no"),
   ("¿Julia es enfermera?", "^si"), ("Julia no está casada.", "ACK"), ("¿Está casada Julia?", "^no"), ("¿Julia está soltera?", "^si|ABST")]},
 {"id": "t8-anti1", "cat": "antialucinacion", "turnos": [
   ("Mi primo Óscar vive en Vigo.", "ACK"), ("¿Dónde trabaja Óscar?", "ABST"), ("¿Cuántos años tiene Óscar?", "ABST"), ("¿Óscar está casado?", "ABST"), ("¿Cómo se llama la mujer de Óscar?", "ABST"),
   ("¿Óscar vive en Vigo?", "^si"), ("¿Quién es Óscar?", "primo"), ("¿Óscar tiene hijos?", "ABST"), ("¿Dónde vive la hermana de Óscar?", "ABST")]},
 {"id": "t8-anti2", "cat": "antialucinacion", "turnos": [
   ("¿Cómo se llama mi perro?", "ABST"), ("¿Dónde vivo?", "ABST"), ("¿Cuál es mi color favorito?", "ABST"), ("Mi color favorito es el verde.", "ACK"), ("¿Cuál es mi color favorito?", "verde"),
   ("¿Cuál es el color favorito de mi madre?", "ABST"), ("¿Mi color favorito es el rojo?", "^no;verde"), ("¿Qué día nací?", "ABST")]},
 {"id": "t8-color", "cat": "negacion", "turnos": [
   ("La mesa de Sara es verde.", "ACK"), ("¿Es la mesa de Sara azul?", "^no;verde"), ("¿Es verde la mesa de Sara?", "^si"), ("¿La mesa de Sara es roja?", "^no;verde"),
   ("El coche de Iván no es rojo.", "ACK"), ("¿El coche de Iván es rojo?", "^no"), ("¿De qué color es el coche de Iván?", "ABST|no es rojo")]},
 {"id": "t8-corrige", "cat": "negacion", "turnos": [
   ("Mi hermana se llama Lucía.", "ACK"), ("No, perdona, no se llama Lucía, se llama Luisa.", "luisa"), ("¿Cómo se llama mi hermana?", "luisa;!lucia"), ("¿Mi hermana se llama Lucía?", "^no;luisa"),
   ("Eso no es verdad.", "ANY"), ("No tengo ningún hermano.", "ACK"), ("¿Tengo algún hermano?", "^no")]},
 {"id": "t8-concepto-neg", "cat": "negacion", "turnos": [
   ("¿Un perro no es un animal?", "^si|es un animal"), ("¿Qué animales no vuelan?", "ANY"), ("¿Un coche no tiene ruedas?", "^si|tiene* cuatro ruedas"), ("Mi perro no tiene cola.", "ACK"),
   ("¿Mi perro tiene cola?", "^no"), ("¿Mi perro tiene cuatro patas?", "^si"), ("¿Los perros mueven la cola?", "^si")]},
]
if __name__ == "__main__":
    f, r = correr(D, verboso=True)
    imprime(r, "TANDA 8")
