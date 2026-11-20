"""Tanda 4: escritura descuidada (sin tildes ni ¿), olvidos, conversación larga con varios temas y vuelta atrás."""
from lab.banco import correr, imprime
D = [
 {"id": "t4-sintildes", "cat": "sin_tildes", "turnos": [
   ("me llamo javier", "javier"), ("vivo en malaga", "ACK"), ("donde vivo?", "malaga"), ("como me llamo?", "javier"), ("mi hermana se llama ines", "ACK"), ("como se llama mi hermana?", "ines"),
   ("ines tiene dos gatos", "ACK"), ("cuantos gatos tiene ines?", "dos|2"), ("quien es ines?", "hermana"), ("que tiene ines?", "gatos")]},
 {"id": "t4-sintildes2", "cat": "sin_tildes", "turnos": [
   ("ana compro un coche ayer", "ACK"), ("que compro ana?", "coche"), ("quien compro un coche?", "ana"), ("cuando compro ana el coche?", "ayer"), ("el coche de ana es rojo", "ACK"),
   ("de que color es el coche de ana?", "roj*"), ("es azul el coche de ana?", "^no"), ("luis esta cansado", "ACK"), ("como esta luis?", "cansad*"), ("esta luis cansado?", "^si")]},
 {"id": "t4-olvido", "cat": "olvido", "turnos": [
   ("Ana vive en Madrid.", "ACK"), ("Luis vive en Vigo.", "ACK"), ("Olvida que Ana vive en Madrid.", "!no he entendido"), ("¿Dónde vive Ana?", "ABST"), ("¿Dónde vive Luis?", "vigo"),
   ("Olvida todo.", "seguro"), ("Sí", "olvidad*|borrad*|hecho"), ("¿Dónde vive Luis?", "ABST"), ("¿Cómo me llamo?", "ABST")]},
 {"id": "t4-larga", "cat": "larga", "turnos": [
   ("Hola, me llamo Carmen.", "carmen"), ("Tengo 34 años y vivo en Bilbao con mi pareja.", "ACK"), ("Mi pareja se llama Íñigo.", "ACK"), ("Íñigo es cocinero y trabaja en un restaurante.", "ACK"),
   ("Tenemos una hija que se llama Leire.", "ACK"), ("Leire tiene cinco años.", "ACK"), ("A Leire le encantan los dinosaurios.", "ACK"), ("¿Cómo se llama mi hija?", "leire"),
   ("¿Cuántos años tiene?", "cinco|5"), ("¿Qué le gusta?", "dinosaurios"), ("¿A qué se dedica mi pareja?", "cociner*"), ("¿Dónde trabaja Íñigo?", "restaurante"), ("¿Quién es Leire?", "hija"),
   ("¿Con quién vivo?", "pareja|inigo"), ("¿Cuántos años tengo?", "34"), ("El año pasado fuimos a Lisboa.", "ACK"), ("¿Adónde fuimos el año pasado?", "lisboa"), ("¿Qué sabes de Íñigo?", "cociner*;restaurante")]},
 {"id": "t4-vuelta", "cat": "vuelta", "turnos": [
   ("Pedro tiene un coche azul.", "ACK"), ("Marta tiene una moto.", "ACK"), ("La moto de Marta es negra.", "ACK"), ("¿De qué color es el coche de Pedro?", "azul"), ("¿Y la moto de Marta?", "negr*"),
   ("¿Quién tiene una moto?", "marta"), ("¿Y un coche?", "pedro"), ("Pedro vendió su coche.", "ACK"), ("¿Tiene Pedro coche?", "^no|^ya no"), ("¿Tiene Marta moto?", "^si")]},
 {"id": "t4-seguimiento", "cat": "seguimiento", "turnos": [
   ("Ana vive en Madrid y Luis vive en Sevilla.", "ACK"), ("¿Dónde vive Ana?", "madrid"), ("¿Y Luis?", "sevilla"), ("Ana tiene 30 años.", "ACK"), ("Luis tiene 28 años.", "ACK"),
   ("¿Cuántos años tiene Ana?", "30"), ("¿Y Luis?", "28"), ("¿Y Pedro?", "ABST"), ("¿Quién es mayor?", "ana"), ("¿Es Luis mayor que Ana?", "^no")]},
 {"id": "t4-negaciones", "cat": "negaciones", "turnos": [
   ("No tengo coche.", "ACK"), ("¿Tengo coche?", "^no"), ("Ana no tiene hermanos.", "ACK"), ("¿Tiene Ana hermanos?", "^no"), ("¿Cuántos hermanos tiene Ana?", "ningun*|no tiene|cero"),
   ("Nunca he estado en París.", "ACK"), ("¿He estado en París?", "^no|nunca"), ("Luis no es médico.", "ACK"), ("¿Es Luis médico?", "^no"), ("¿Qué es Luis?", "ABST")]},
 {"id": "t4-preguntas-lcm", "cat": "lcm", "turnos": [
   ("¿Cómo te llamas?", "lcm"), ("¿Qué eres?", "lcm|modelo"), ("¿Tienes amigos?", "no"), ("¿Cuál es tu color favorito?", "no tengo"), ("¿Dónde vives?", "ordenador"),
   ("¿Me entiendes?", "si"), ("¿Puedes ayudarme?", "claro|si"), ("¿Hablas inglés?", "español"), ("¿Qué día es mañana?", "jueves"), ("¿Qué mes viene después de marzo?", "abril")]},
 {"id": "t4-mixto-modal", "cat": "modal", "turnos": [
   ("Quiero aprender a tocar el piano.", "ACK"), ("¿Qué quiero aprender?", "piano"), ("Tengo que ir al médico mañana.", "ACK"), ("¿Qué tengo que hacer mañana?", "medico"),
   ("Ana puede venir el viernes.", "ACK"), ("¿Puede venir Ana el viernes?", "^si"), ("¿Cuándo puede venir Ana?", "viernes"), ("Luis sabe nadar.", "ACK"), ("¿Sabe nadar Luis?", "^si"), ("¿Sabe nadar Ana?", "ABST")]},
 {"id": "t4-plurales", "cat": "plurales", "turnos": [
   ("Mis padres viven en Zaragoza.", "ACK"), ("¿Dónde viven mis padres?", "zaragoza"), ("Mis hijos se llaman Hugo y Vera.", "ACK"), ("¿Cómo se llaman mis hijos?", "hugo;vera"),
   ("Hugo y Vera van al colegio.", "ACK"), ("¿Quién va al colegio?", "hugo;vera"), ("Los gatos de Ana son negros.", "ACK"), ("¿De qué color son los gatos de Ana?", "negr*"), ("¿Cuántos hijos tengo?", "dos|2")]},
]
if __name__ == "__main__":
    f, r = correr(D, verboso=True, salida="lab/res_tanda04.json"); imprime(r, "TANDA 4")
