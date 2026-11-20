"""Diagnóstico por PROCESO de los fallos del examen grande corregido (2.22, texto pegado).
Para cada pregunta fallada se comprueba con el propio modelo en qué paso se rompe:
  LECTURA        la frase no llegó a ser un hecho del núcleo (solo quedó guardada como texto)
  CONSULTA       el hecho está en el núcleo, pero la pregunta no llega a él (forma de la pregunta)
  RECUPERACION   la frase solo está como texto y la cita no la encuentra o elige otra
  DICCIONARIO    falta el sinónimo en el léxico, o el léxico enlaza dos palabras que aquí no dicen lo mismo
  FABRICA        el conocimiento de fábrica contesta por encima de lo leído
  INTERCONEXION  cada pieza se sabe por separado (se comprueba), pero no se unen: identidad + propiedad, clase + individuo
  RAZONAMIENTO   hace falta un paso lógico sobre algo que sí se sabe: exclusión, negación, implicación
  EXPRESION      lo sabe y lo dice de una forma que no vale
Las comprobaciones automáticas: ¿hay un hecho del núcleo con ese dato?, ¿se acierta la pregunta literal equivalente?, ¿se aciertan
los dos pasos por separado?, ¿qué dice el léxico de la pareja de palabras?
    python -m lab.grande1.diagnostico"""
import gc, json, shutil, sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")
from lab.banco import motor, veredicto
from lab.aprender import grande1b as G
from src.nucleo20.dialogo import Conversador
from src.nucleo20.morfo import sa
from src.nucleo20 import vectores as V

# pregunta fallada -> anotación a mano de lo que NECESITA (no de por qué falla; eso lo decide la comprobación)
#   dato: (palabra del verbo o del asunto, palabra de la respuesta)  -> se busca un hecho del núcleo que tenga las dos
#   lit:  [(pregunta literal o paso, criterio)]                       -> se preguntan al modelo
#   par:  (palabra de la pregunta, palabra del texto)                 -> se mira en el léxico
#   paso: para deducciones y contradicciones, qué paso lógico haría falta
A = {
 "¿cuánto tiempo maman los ballenatos?": dict(dato=("mama", "ano")),
 "¿la ballena azul respira aire?": dict(lit=[("¿las ballenas respiran aire?", "^si|aire"), ("¿la ballena azul es una ballena?", "^si")], paso="herencia: lo que vale para las ballenas vale para la ballena azul"),
 "los ballenatos maman durante tres años": dict(dato=("mama", "ano"), paso="exclusión: un año / tres años"),
 "¿llueve mucho en un desierto?": dict(manual="EXPRESION", nota="cita la frase correcta («casi nunca llueve») sin decir «no»"),
 "¿qué son las dunas?": dict(manual="FABRICA", dato=("duna", "montana")),
 "¿qué transportaba un grupo de camellos que viaja junto?": dict(lit=[("¿cómo se llama un grupo de camellos que viaja junto?", "caravana"), ("¿qué transportaban las caravanas?", "sal|telas")]),
 "¿hay agua en un oasis?": dict(lit=[("¿qué es un oasis?", "agua")], paso="implicación: «zona donde hay agua» -> hay agua"),
 "¿en el Sáhara llueve mucho?": dict(lit=[("¿el Sáhara es un desierto?", "^si"), ("¿llueve mucho en un desierto?", "^no|casi nunca")], paso="herencia + negación: es un desierto y en un desierto casi nunca llueve"),
 "¿mi abuelo vivía en una tienda?": dict(lit=[("¿dónde viven los nómadas?", "tiendas")], manual="EXPRESION", nota="encuentra el dato y contesta «No, …» por el género («las nómadas») y el tiempo verbal"),
 "¿cómo se toca el contrabajo?": dict(dato=("toca", "pie")),
 "¿con qué se golpean los timbales?": dict(manual="FABRICA", dato=("golpe", "maza")),
 "¿con qué se pegan los timbales?": dict(par=("pegar", "golpear"), lit=[("¿con qué se golpean los timbales?", "mazas")]),
 "¿cuánto tardan los ensayos?": dict(par=("tardar", "durar"), lit=[("¿cuánto duran los ensayos?", "tres|3")]),
 "¿cuándo ajustan los músicos sus instrumentos?": dict(par=("ajustar", "afinar"), lit=[("¿cuándo afinan los músicos sus instrumentos?", "antes|concierto")]),
 "¿cómo se toca el instrumento de cuerda más grande de la orquesta?": dict(lit=[("¿cuál es el instrumento de cuerda más grande de la orquesta?", "contrabajo"), ("¿cómo se toca el contrabajo?", "pie")]),
 "¿mi prima usa una batuta?": dict(lit=[("¿con qué marca el ritmo el director?", "batuta")], paso="clase + individuo con un nombre de varias palabras («directora de orquesta») y otro verbo («usa»)"),
 "el contrabajo se toca sentado": dict(dato=("toca", "pie"), paso="exclusión: de pie / sentado"),
 "¿qué lleva el vehículo que lleva a los enfermos al hospital?": dict(lit=[("¿qué es la ambulancia?", "vehiculo"), ("¿qué lleva la ambulancia?", "sirena")]),
 "¿las urgencias cierran por la noche?": dict(lit=[("¿cuándo están abiertas las urgencias?", "noche")], paso="exclusión: abiertas / cierran"),
 "¿quién conduce la ambulancia?": dict(manual="FABRICA", nota="trampa: contesta «los médicos y los enfermeros» de fábrica"),
 "¿cuántos pasajeros lleva un avión grande?": dict(dato=("lleva", "trescientos")),
 "¿dónde se arreglan los aviones?": dict(par=("arreglar", "reparar"), lit=[("¿dónde se reparan los aviones?", "hangar")], malo=("arreglar", "atender")),
 "¿quiénes guían a los aviones?": dict(par=("guiar", "dirigir"), lit=[("¿quiénes dirigen a los aviones?", "controlador*")], malo=("guiar", "conducir")),
 "¿cuántos pasajeros transporta un avión grande?": dict(par=("transportar", "llevar"), lit=[("¿cuántos pasajeros lleva un avión grande?", "trescientos|300")]),
 "¿cuántos aviones hay en el aeropuerto?": dict(manual="RECUPERACION", nota="trampa: cita «…lleva más de trescientos pasajeros»; el número no cuenta aviones"),
 "un avión grande lleva más de mil pasajeros": dict(dato=("lleva", "trescientos"), paso="exclusión: trescientos / mil"),
 "¿qué cortan los castores con los dientes?": dict(dato=("corta", "tronco")),
 "¿para qué usan la cola los castores?": dict(dato=("usa", "timon")),
 "¿para qué emplean la cola los castores?": dict(par=("emplear", "usar"), lit=[("¿para qué usan la cola los castores?", "timon")]),
 "¿los castores saben nadar?": dict(lit=[("¿para qué usan la cola los castores?", "timon")], paso="implicación: «cuando nadan» -> saben nadar"),
 "¿dónde se cocina la paella?": dict(dato=("cocina", "sarten")),
 "¿con qué se come el arroz en Japón?": dict(manual="FABRICA", dato=("come", "palillo")),
 "¿cuándo se planta el arroz?": dict(par=("plantar", "sembrar"), lit=[("¿cuándo se siembra el arroz?", "primavera")]),
 "¿dónde se prepara la paella?": dict(par=("preparar", "cocinar"), lit=[("¿dónde se cocina la paella?", "sarten")]),
 "¿dónde se cocina el plato de arroz más famoso de España?": dict(lit=[("¿cuál es el plato de arroz más famoso de España?", "paella"), ("¿dónde se cocina la paella?", "sarten")]),
 "¿el arroz necesita poca agua?": dict(lit=[("¿qué necesita la planta del arroz?", "agua")], paso="exclusión: mucha / poca"),
 "¿qué hay debajo de los trapecistas?": dict(dato=("debajo", "red")),
 "¿quiénes divierten al público?": dict(par=("divertir", "reir"), lit=[("¿quiénes hacen reír al público?", "payasos")]),
 "¿sobre qué anda el equilibrista?": dict(par=("andar", "caminar"), lit=[("¿sobre qué camina el equilibrista?", "cable")]),
 "¿qué hay debajo del número más peligroso del circo?": dict(manual="EXAMEN", nota="pregunta mal planteada: el texto dice qué hay debajo de los trapecistas, no del «número»"),
 "¿de qué es la tienda donde se hacen las funciones?": dict(lit=[("¿dónde se hacen las funciones?", "carpa"), ("¿qué es la carpa?", "lona")]),
 "¿el circo se queda siempre en la misma ciudad?": dict(lit=[("¿qué es el circo?", "viaja|ciudad")], paso="negación: viaja de ciudad en ciudad -> no se queda siempre en la misma"),
 "¿cuánto cuesta una entrada?": dict(manual="EXPRESION", nota="se abstiene bien («eso queda fuera de lo que sé hacer»); el corrector no lo reconoce"),
 "descríbeme a los payasos": dict(manual="FABRICA", dato=("payaso", "reir")),
 "el circo se queda dos meses en cada ciudad": dict(dato=("queda", "semana"), paso="exclusión: dos semanas / dos meses"),
 "¿cada cuánto hay que dar cuerda a los relojes mecánicos?": dict(dato=("cuerda", "dia"), manual_si_hecho="CONSULTA"),
 "¿qué tiene el reloj de cuco?": dict(dato=("tiene", "pajaro")),
 "¿dónde se usa el cronómetro?": dict(dato=("usa", "carrera")),
 "¿quiénes reparan relojes?": dict(par=("reparar", "arreglar"), lit=[("¿cómo se llaman las personas que arreglan relojes?", "relojero*")]),
 "¿dónde se emplea el cronómetro?": dict(par=("emplear", "usar"), lit=[("¿dónde se usa el cronómetro?", "carreras")]),
 "¿con qué trabajan los relojes de cuarzo?": dict(par=("trabajar", "funcionar"), lit=[("¿con qué funcionan los relojes de cuarzo?", "pila")]),
 "¿qué tiene el reloj más conocido de Suiza?": dict(lit=[("¿cuál es el reloj más conocido de Suiza?", "cuco"), ("¿qué tiene el reloj de cuco?", "pajaro")]),
 "¿dónde se usa el reloj que mide tiempos muy cortos?": dict(lit=[("¿qué es el cronómetro?", "reloj"), ("¿dónde se usa el cronómetro?", "carreras")]),
 "¿un reloj de sol funciona de noche?": dict(lit=[("¿cuándo funcionaban los relojes de sol?", "dia")], paso="exclusión: «solo de día» -> de noche no"),
 "la aguja corta marca los minutos": dict(dato=("marca", "hora"), paso="exclusión: horas / minutos"),
 "¿dónde se vierte la mezcla?": dict(dato=("vierte", "molde")),
 "¿cuánto tarda el jabón en estar listo?": dict(dato=("tarda", "mes")),
 "¿cuánto demora el jabón en estar listo?": dict(par=("demorar", "tardar"), lit=[("¿cuánto tarda el jabón en estar listo?", "mes")]),
 "¿dónde se limpiaba la ropa antiguamente?": dict(par=("limpiar", "lavar"), lit=[("¿dónde se lavaba la ropa antiguamente?", "rio")]),
 "¿qué quema la sustancia que se mezcla con la grasa?": dict(lit=[("¿qué es la sosa?", "sustancia"), ("¿con qué se mezcla la grasa?", "sosa")], nota="además, el segundo paso («quema la piel») está dentro de la definición de la sosa"),
 "el jabón tarda un día en estar listo": dict(dato=("tarda", "mes"), paso="exclusión: un mes / un día"),
}


def hay_hecho(c, clave, resp):
    for f in c.F:
        try:
            t = sa(c.frase(f).lower())
        except Exception:                                # noqa
            continue
        if clave in t and resp in t and not f.get("efecto"):
            return c.frase(f)
    return None


def lexico(a, b):
    tipo, peso = V.parentesco(a, b)
    return {"enlace": tipo, "peso": round(peso, 2), "vectores": round(V.sim(a, b), 2), "idiomas": V.puente(a, b)}


def main():
    ver = next((a for a in sys.argv[1:] if a.isdigit()), "222")      # python -m lab.grande1.diagnostico 223
    fallos = [f for f in json.load(open(f"lab/grande1/resb_{ver}_texto.json"))["filas"] if f["t"] != "-" and f["v"] and f["v"] != "OK"]
    por_tema = defaultdict(list)
    for f in fallos:
        por_tema[f["tema"]].append(f)
    out = []
    for tema in G.TEMAS:
        fs = por_tema.get(tema["nombre"], [])
        if not fs:
            continue
        mo = motor()
        mo.chat(tema["intro"] + "\n" + "\n".join(f for f, _ in tema["frases"]))
        c = mo._n20                                      # el núcleo de ESTE motor (no uno cualquiera que siga en memoria)
        for f in fs:
            a = A.get(f["q"])
            d = {"tema": tema["nombre"], "t": f["t"], "q": f["q"], "r": (f["r"] or "")[:140]}
            if a is None:
                d["proceso"] = "SIN_ANOTAR"; out.append(d); continue
            hecho = hay_hecho(c, *a["dato"]) if a.get("dato") else None
            d["hecho_en_nucleo"] = hecho
            pasos = []
            for q2, crit in a.get("lit", []):
                r2 = mo.chat(q2).get("respuesta")
                pasos.append({"q": q2, "ok": veredicto(crit, r2) == "OK", "r": (r2 or "")[:90]})
            d["pasos"] = pasos
            if a.get("par"):
                d["lexico"] = lexico(*a["par"])
            if a.get("malo"):
                d["lexico_malo"] = dict(lexico(*a["malo"]), pareja=a["malo"])
            todos = all(p["ok"] for p in pasos) if pasos else None
            if a.get("manual") and not (hecho and a.get("manual_si_hecho")):
                proc = a["manual"]
            elif f["t"] == "P":
                if not todos:
                    proc = "LECTURA" if not pasos[0]["ok"] else "RECUPERACION"
                    d["nota"] = "la pregunta literal equivalente también falla: el problema no es la palabra"
                elif a.get("malo"):
                    proc = "DICCIONARIO"; d["nota"] = "el léxico enlaza la palabra con otra del texto que aquí no dice lo mismo"
                else:
                    lx = d["lexico"]
                    proc = "DICCIONARIO" if not (lx["enlace"] or lx["idiomas"] >= 2) else "DICCIONARIO"
                    d["nota"] = "falta el enlace en el léxico" if not (lx["enlace"] or lx["idiomas"] >= 2) else "hay enlace, pero débil o con un sentido minoritario: no pasa el umbral"
            elif f["t"] == "M":
                proc = "INTERCONEXION" if todos else "LECTURA"
                d["nota"] = "los dos pasos se aciertan por separado" if todos else "uno de los dos pasos falla ya por separado: " + next(p["q"] for p in pasos if not p["ok"])
            elif f["t"] in ("D", "C"):
                proc = ("RAZONAMIENTO" if "herencia" not in a.get("paso", "") and "clase" not in a.get("paso", "") else "INTERCONEXION") if todos else "LECTURA"
                d["nota"] = a.get("paso", "") if todos else "la premisa ya falla preguntada directamente: " + next(p["q"] for p in pasos if not p["ok"])
            elif f["t"] == "K":
                entendida = not sa(f["r"].lower()).startswith("no lo he entendido")
                proc = "RAZONAMIENTO" if (hecho and entendida) else "LECTURA"
                d["nota"] = a.get("paso", "") if proc == "RAZONAMIENTO" else ("no entiende la afirmación" if not entendida else "lo leído solo quedó como texto y el contraste por texto no salta: " + a.get("paso", ""))
            else:                                        # literales
                if hecho:
                    proc = a.get("manual_si_hecho") or "CONSULTA"
                    d["nota"] = "el hecho está en el núcleo; la pregunta no llega a él"
                else:
                    proc = "LECTURA"
                    d["nota"] = "la frase no llegó a ser un hecho del núcleo y la cita tampoco la encuentra"
            if a.get("nota"):
                d["nota"] = (d.get("nota", "") + " " + a["nota"]).strip()
            d["proceso"] = proc
            out.append(d)
        shutil.rmtree(mo._tmp, ignore_errors=True)
    # un fallo que depende de un paso que ya falla solo hereda la causa de ese paso (si ese paso está diagnosticado)
    causa = {d["q"]: d["proceso"] for d in out}
    for d in out:
        malos = [p["q"] for p in d.get("pasos", []) if not p["ok"]]
        if malos and d["proceso"] == "LECTURA" and causa.get(malos[0]) not in (None, "LECTURA"):
            d["proceso"] = causa[malos[0]]
            d["nota"] = d.get("nota", "") + f" (ese paso falla por {causa[malos[0]]})"
    cuenta = Counter(d["proceso"] for d in out)
    cruz = defaultdict(Counter)
    for d in out:
        cruz[d["proceso"]][d["t"]] += 1
    json.dump({"n_fallos": len(out), "por_proceso": dict(cuenta), "proceso_por_tipo": {k: dict(v) for k, v in cruz.items()}, "detalle": out},
              open(f"lab/grande1/diagnostico_{ver}.json", "w"), indent=1, ensure_ascii=False)
    print(len(out), dict(cuenta.most_common()))
    for p, _ in cuenta.most_common():
        print("\n##", p, dict(cruz[p]))
        for d in out:
            if d["proceso"] == p:
                print("  ", d["t"], "|", d["q"][:62], "|", d.get("nota", "")[:110], "|", d.get("lexico", ""))


if __name__ == "__main__":
    main()
