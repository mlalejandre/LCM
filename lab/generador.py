"""Generador del banco de evaluación por diálogo (escrito ANTES de ajustar el núcleo con él).

Dos particiones:
  - 'dev'   : vocabulario A y formulaciones básicas. Se usa para analizar fallos y parchear.
  - 'ciego' : vocabulario B (disjunto) y, la mitad de las veces, formulaciones NUEVAS que nunca aparecen
              en dev. Solo se miran sus cifras agregadas; no se leen sus transcripciones para parchear.
Cada diálogo es una sesión nueva de fábrica. Los criterios se generan junto con el diálogo.
"""
import io
import random

V = {
    "dev": dict(
        nombres_f=["Ana", "Marta", "Sara", "Elena", "Lucía", "Nuria"], nombres_m=["Luis", "Pablo", "Carlos", "Jorge", "Diego", "Raúl"],
        lugares=["Madrid", "Sevilla", "Valencia", "Bilbao", "Granada", "Toledo"], mascotas=[("perro", "m"), ("gato", "m")], nombres_masc=["Toby", "Luna", "Rex", "Nala"],
        objetos=[("coche", "m"), ("casa", "f"), ("libro", "m"), ("bicicleta", "f"), ("mesa", "f")],
        adjs=[("grande", "pequeño"), ("alto", "bajo"), ("nuevo", "viejo"), ("rápido", "lento")], colores=["rojo", "azul", "verde"],
        comidas=["carne", "verdura", "pescado", "pan", "queso"], bebidas=["café", "leche", "té"], gustos=["el fútbol", "la música", "el cine"],
        profs=[("médico", "médica"), ("profesor", "profesora")], compras=[("un libro", "libro", "el libro"), ("una bicicleta", "bicicleta", "la bicicleta"), ("un coche", "coche", "el coche")],
        frutas=[("manzanas", "f"), ("peras", "f")], animales=[("gatos", "m"), ("perros", "m")], rasgos=["alto", "rápido", "fuerte"],
        clases=[("perro", "animal", "ladran", "ladra"), ("gato", "animal", "duermen mucho", "duerme mucho")], hab=[("juega al tenis", "tenis"), ("va al gimnasio", "gimnasio")],
        dias=["los lunes", "los martes"], estados=["cansado", "contento"], trabajos=["un hospital", "una escuela"]),
    "ciego": dict(
        nombres_f=["Paula", "Julia", "Silvia", "Teresa", "Carmen", "Irene"], nombres_m=["Hugo", "Iván", "Andrés", "Óscar", "Rubén", "Víctor"],
        lugares=["Vigo", "Cádiz", "Burgos", "Murcia", "Oviedo", "Zaragoza"], mascotas=[("caballo", "m"), ("pájaro", "m")], nombres_masc=["Coco", "Kira", "Thor", "Lola"],
        objetos=[("moto", "f"), ("piso", "m"), ("reloj", "m"), ("guitarra", "f"), ("silla", "f")],
        adjs=[("caro", "barato"), ("largo", "corto"), ("limpio", "sucio"), ("fuerte", "débil")], colores=["amarillo", "negro", "blanco"],
        comidas=["fruta", "arroz", "pasta", "chocolate", "sopa"], bebidas=["zumo", "agua", "vino"], gustos=["el tenis", "la pintura", "el teatro"],
        profs=[("abogado", "abogada"), ("ingeniero", "ingeniera")], compras=[("un reloj", "reloj", "el reloj"), ("una guitarra", "guitarra", "la guitarra"), ("un piso", "piso", "el piso")],
        frutas=[("naranjas", "f"), ("plátanos", "m")], animales=[("caballos", "m"), ("pájaros", "m")], rasgos=["joven", "listo", "delgado"],
        clases=[("caballo", "animal", "corren mucho", "corre mucho"), ("pájaro", "animal", "cantan", "canta")], hab=[("toca la guitarra", "guitarra"), ("va a la piscina", "piscina")],
        dias=["los jueves", "los sábados"], estados=["nervioso", "tranquilo"], trabajos=["un banco", "una tienda"]),
}
NUMS = {2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete", 8: "ocho", 9: "nueve"}
RGB = {"rojo": (220, 38, 38), "azul": (37, 99, 235), "verde": (22, 163, 74), "amarillo": (250, 204, 21), "negro": (10, 10, 10), "blanco": (250, 250, 250)}


def fem(adj):
    return adj[:-1] + "a" if adj.endswith("o") else adj


def rz(adj):
    """criterio que acepta cualquier flexión («rojo/roja/rojos»)."""
    return (adj[:-1] if adj.endswith("o") else adj) + "*"


def png(rgb):
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (32, 32), rgb).save(b, "PNG")
    return b.getvalue()


class Gen:
    def __init__(self, split, semilla):
        self.split, self.v, self.r = split, V[split], random.Random(semilla)
        self.ciego = split == "ciego"

    # --- utilidades
    def f(self, basicas, nuevas=()):
        """Elige formulación: en dev solo básicas; en ciego, la mitad de las veces una nueva."""
        if self.ciego and nuevas and self.r.random() < 0.5:
            return self.r.choice(list(nuevas)), True
        return self.r.choice(list(basicas)), False

    def persona(self, n=1, sexo=None):
        pool = [(x, "f") for x in self.v["nombres_f"]] + [(x, "m") for x in self.v["nombres_m"]]
        if sexo:
            pool = [p for p in pool if p[1] == sexo]
        return self.r.sample(pool, n)

    def de(self, que, quien):
        art = "la" if que[1] == "f" else "el"
        return f"{art} {que[0]} de {quien}"

    # --- categorías -------------------------------------------------------
    def atributos(self):
        (p, _), = self.persona()
        obj = self.r.choice(self.v["objetos"]); a, anti = self.r.choice(self.v["adjs"]); col, col2 = self.r.sample(self.v["colores"], 2)
        g = obj[1]; A = fem(a) if g == "f" else a; ANTI = fem(anti) if g == "f" else anti; C = fem(col) if g == "f" else col; C2 = fem(col2) if g == "f" else col2
        mio = self.r.random() < 0.4
        X = f"mi {obj[0]}" if mio else self.de(obj, p)
        Xc = X[0].upper() + X[1:]
        t = [(f"{Xc} es {A}.", "ACK")]
        q, _ = self.f([f"¿Cómo es {X}?"], [f"¿Qué sabes de {X}?", f"¿{Xc} cómo es?"]); t.append((q, rz(a)))
        q, _ = self.f([f"¿Es {X} {A}?"], [f"¿{Xc} es {A}?", f"¿Es {A} {X}?"]); t.append((q, "^si"))
        q, _ = self.f([f"¿Es {X} {ANTI}?"], [f"¿{Xc} es {ANTI}?", f"¿Es {ANTI} {X}?"]); t.append((q, "^no;" + rz(a)))
        q, _ = self.f([f"¿De qué color es {X}?"], [f"¿Qué color tiene {X}?", f"¿Cuál es el color de {X}?"]); t.append((q, "ABST"))
        t.append((f"{Xc} es {C}.", "ACK"))
        q, _ = self.f([f"¿De qué color es {X}?"], [f"¿Qué color tiene {X}?", f"¿Cuál es el color de {X}?"]); t.append((q, rz(col)))
        t.append((f"¿Es {X} {C2}?", "^no;" + rz(col)))
        t.append((f"¿Es {X} {C}?", "^si"))
        return t

    def familia(self):
        (ab, sab), (pa, spa), (hi, shi), (tio, stio) = self.persona(4)
        r_ab = "madre" if sab == "f" else "padre"; r_pa = "madre" if spa == "f" else "padre"
        abu = "abuela" if sab == "f" else "abuelo"; hijo = "hija" if spa == "f" else "hijo"; nieto = "nieta" if shi == "f" else "nieto"
        herm = "hermana" if stio == "f" else "hermano"; tio_w = "tía" if stio == "f" else "tío"
        art = lambda w: "la" if w.endswith("a") else "el"
        s1, _ = self.f([f"{ab} es {art(r_ab)} {r_ab} de {pa}."], [f"{art(r_ab).capitalize()} {r_ab} de {pa} es {ab}.", f"{art(r_ab).capitalize()} {r_ab} de {pa} se llama {ab}."])
        t = [(s1, "ACK"), (f"{pa} es {art(r_pa)} {r_pa} de {hi}.", "ACK")]
        q, _ = self.f([f"¿Quién es {art(r_ab)} {r_ab} de {pa}?"], [f"¿Cómo se llama {art(r_ab)} {r_ab} de {pa}?", f"¿Sabes quién es {art(r_ab)} {r_ab} de {pa}?"]); t.append((q, ab))
        q, _ = self.f([f"¿Quién es {art(abu)} {abu} de {hi}?"], [f"¿Cómo se llama {art(abu)} {abu} de {hi}?"]); t.append((q, ab))
        t.append((f"¿Es {ab} {abu} de {hi}?", "^si"))
        q, _ = self.f(["¿Por qué?"], ["¿Cómo lo sabes?", "¿Y eso por qué?"]); t.append((q, pa + ";" + r_pa + "|" + r_ab))
        q, _ = self.f([f"¿Quién es {art(hijo)} {hijo} de {ab}?"], [f"¿Cómo se llama {art(hijo)} {hijo} de {ab}?"]); t.append((q, pa))
        t.append((f"¿Quién es {art(nieto)} {nieto} de {ab}?", hi))
        t.append((f"{tio} es {art(herm)} {herm} de {pa}.", "ACK"))
        q, _ = self.f([f"¿Quién es {art(tio_w)} {tio_w} de {hi}?"], [f"¿Cómo se llama {art(tio_w)} {tio_w} de {hi}?"]); t.append((q, tio))
        t.append((f"¿Quién es el padre de {ab}?", "ABST"))
        t.append((f"¿Es {hi} {r_ab} de {ab}?", "!^si"))
        return t

    def lugar(self):
        (p, s), (p2, _) = self.persona(2); l1, l2, l3 = self.r.sample(self.v["lugares"], 3); tr = self.r.choice(self.v["trabajos"])
        s1, _ = self.f([f"{p} vive en {l1}."], [f"{p} reside en {l1}.", f"{p} está viviendo en {l1}."])
        t = [(s1, "ACK")]
        qd = lambda: self.f([f"¿Dónde vive {p}?"], [f"¿En qué ciudad vive {p}?", f"¿Sabes dónde vive {p}?", f"¿{p} dónde vive?"])[0]
        t.append((qd(), l1))
        s2, _ = self.f([f"Ahora {p} vive en {l2}."], [f"{p} se ha mudado a {l2}.", f"{p} ya no vive en {l1}, ahora vive en {l2}."])
        t.append((s2, "ACK"))
        t.append((qd(), l2 + ";!" + l1))
        q, _ = self.f([f"¿Dónde vivía {p} antes?"], [f"¿Dónde vivía antes {p}?", f"¿En qué ciudad vivía {p} antes?"]); t.append((q, l1))
        t.append((f"¿Vive {p} en {l3}?", "^no;" + l2))
        t.append((f"¿Vive {p} en {l2}?", "^si"))
        t.append((f"¿Dónde trabaja {p}?", "ABST"))
        t.append((f"{p} trabaja en {tr}.", "ACK"))
        q, _ = self.f([f"¿Dónde trabaja {p}?"], [f"¿En qué lugar trabaja {p}?", f"¿Sabes dónde trabaja {p}?"]); t.append((q, tr.split()[1]))
        t.append((f"¿Dónde vive {p2}?", "ABST"))
        q, _ = self.f([f"¿Quién vive en {l2}?"], [f"¿Quién reside en {l2}?"]); t.append((q, p))
        return t

    def cantidad(self):
        (p, _), = self.persona(); (a1, _), (a2, _) = self.v["animales"]; n1, n2, n3 = self.r.sample(list(NUMS), 3)
        fr, _g = self.r.choice(self.v["frutas"]); nf = self.r.choice(list(NUMS))
        t = [(f"{p} tiene {NUMS[n1]} {a1}.", "ACK")]
        q, _ = self.f([f"¿Cuántos {a1} tiene {p}?"], [f"¿{p} cuántos {a1} tiene?", f"¿Sabes cuántos {a1} tiene {p}?"]); t.append((q, f"{NUMS[n1]}|{n1}"))
        t.append((f"{p} tiene {NUMS[n2]} {a2}.", "ACK"))
        q, _ = self.f([f"¿Qué tiene {p}?"], [f"¿Qué cosas tiene {p}?"]); t.append((q, a1 + ";" + a2))
        t.append((f"¿Cuántos animales tiene {p}?", f"{n1 + n2}|" + {4: "cuatro", 5: "cinco", 6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince", 16: "dieciséis", 17: "diecisiete"}.get(n1 + n2, str(n1 + n2))))
        t.append((f"¿Tiene {p} {NUMS[n1]} {a1}?", "^si"))
        t.append((f"¿Cuántas {fr} tiene {p}?" if _g == "f" else f"¿Cuántos {fr} tiene {p}?", "ABST"))
        t.append((f"{p} tiene {NUMS[nf]} {fr}.", "ACK"))
        t.append((f"¿Cuántas {fr} tiene {p}?" if _g == "f" else f"¿Cuántos {fr} tiene {p}?", f"{NUMS[nf]}|{nf}"))
        s, _ = self.f([f"Ahora {p} tiene {NUMS[n3]} {a1}."], [f"{p} ya tiene {NUMS[n3]} {a1}."]); t.append((s, "ACK"))
        t.append((f"¿Cuántos {a1} tiene {p}?", f"{NUMS[n3]}|{n3};!{NUMS[n1]}"))
        return t

    def negacion(self):
        (p, _), = self.persona(); c1, c2, c3 = self.r.sample(self.v["comidas"], 3); b1, b2 = self.r.sample(self.v["bebidas"], 2)
        t = [(f"{p} no come {c1}.", "ACK"), (f"¿Come {p} {c1}?", "^no")]
        t.append((f"{p} come {c2}.", "ACK"))
        q, _ = self.f([f"¿Qué come {p}?"], [f"¿{p} qué come?", f"¿Qué cosas come {p}?"]); t.append((q, c2 + ";!come " + c1))
        q, _ = self.f([f"¿Qué no come {p}?"], [f"¿{p} qué no come?"]); t.append((q, c1))
        t.append((f"¿Come {p} {c3}?", "ABST"))
        t.append((f"{p} bebe {b1}.", "ACK"))
        t.append((f"¿Bebe {p} {b1}?", "^si"))
        s, _ = self.f([f"{p} ya no bebe {b1}."], [f"Ahora {p} no bebe {b1}."]); t.append((s, "ACK"))
        t.append((f"¿Bebe {p} {b1}?", "^no|^ya no"))
        t.append((f"¿Bebe {p} {b2}?", "ABST"))
        return t

    def correferencia(self):
        (p, s), = self.persona(); m = self.r.choice(self.v["mascotas"]); nm = self.r.choice(self.v["nombres_masc"]); l = self.r.choice(self.v["lugares"]); a, anti = self.r.choice(self.v["adjs"])
        pron = "Ella" if s == "f" else "Él"
        t = [(f"{p} tiene un {m[0]}.", "ACK")]
        t.append((f"¿Cómo se llama el {m[0]} de {p}?", "ABST"))
        s1, _ = self.f(["Se llama {n}."], ["Su nombre es {n}.", "El animal se llama {n}."]); t.append((s1.format(n=nm), "ACK"))
        q, _ = self.f([f"¿Cómo se llama el {m[0]} de {p}?"], [f"¿Cuál es el nombre del {m[0]} de {p}?", f"¿Qué nombre tiene el {m[0]} de {p}?"]); t.append((q, nm))
        t.append((f"{pron} vive en {l}.", "ACK"))
        t.append((f"¿Dónde vive {p}?", l))
        t.append((f"Su {m[0]} es {a}.", "ACK"))
        q, _ = self.f([f"¿Cómo es {nm}?"], [f"¿Cómo es el {m[0]} de {p}?"]); t.append((q, rz(a)))
        t.append((f"¿Es {nm} {anti}?", "^no"))
        q, _ = self.f([f"¿Quién tiene un {m[0]}?"], [f"¿De quién es {nm}?", f"¿Quién es el dueño de {nm}?"]); t.append((q, p))
        t.append((f"¿Tiene {p} un {m[0]}?", "^si"))
        return t

    def acciones(self):
        (p, _), (p2, _) = self.persona(2); (un, cl, el) = self.r.choice(self.v["compras"]); cuando, clave = self.r.choice([("ayer", "ayer"), ("el lunes", "lunes"), ("esta mañana", "mañana")])
        v, vq = self.r.choice([("compró", "compró"), ("encontró", "encontró")])
        t = [(f"{p} {v} {un} {cuando}.", "ACK")]
        q, _ = self.f([f"¿Qué {vq} {p}?"], [f"¿{p} qué {vq}?", f"¿Qué {vq} {p} {cuando}?"]); t.append((q, cl))
        q, _ = self.f([f"¿Quién {vq} {un}?"], [f"¿Quién {vq} {el}?", f"¿Sabes quién {vq} {un}?"]); t.append((q, p))
        q, _ = self.f([f"¿Cuándo {vq} {p} {el}?"], [f"¿Cuándo {vq} {el} {p}?", f"¿Qué día {vq} {p} {el}?"]); t.append((q, clave))
        t.append((f"¿Tiene {p} {un}?", "^si"))
        d, _ = self.f([f"{p} le dio {el} a {p2}."], [f"{p} le regaló {el} a {p2}.", f"{p} le ha dado {el} a {p2}."]); t.append((d, "ACK"))
        q, _ = self.f([f"¿Quién tiene {el}?"], [f"¿Quién tiene ahora {el}?"]); t.append((q, p2 + ";!" + p + " tiene"))
        t.append((f"¿Tiene {p} {el}?", "^no|^ya no"))
        t.append((f"¿Tiene {p2} {el}?", "^si"))
        t.append((f"¿Qué {vq} {p2}?", "ABST"))
        return t

    def usuario(self):
        (yo, s), = self.persona(); l, l2 = self.r.sample(self.v["lugares"], 2); ed = self.r.randint(19, 68); m = self.r.choice(self.v["mascotas"]); nm = self.r.choice(self.v["nombres_masc"])
        g = self.r.choice(self.v["gustos"]); g2 = self.r.choice([x for x in self.v["gustos"] if x != g]); pm, pf = self.r.choice(self.v["profs"]); prof = pf if s == "f" else pm
        s1, _ = self.f([f"Me llamo {yo}."], [f"Mi nombre es {yo}.", f"Soy {yo}."]); t = [(s1, yo)]
        t.append((f"Vivo en {l}.", "ACK")); t.append((f"Tengo {ed} años.", "ACK"))
        q, _ = self.f(["¿Cómo me llamo?"], ["¿Cuál es mi nombre?", "¿Sabes cómo me llamo?", "¿Recuerdas mi nombre?"]); t.append((q, yo))
        q, _ = self.f(["¿Dónde vivo?"], ["¿En qué ciudad vivo?", "¿Sabes dónde vivo?"]); t.append((q, l))
        q, _ = self.f(["¿Cuántos años tengo?"], ["¿Qué edad tengo?", "¿Cuál es mi edad?"]); t.append((q, str(ed)))
        t.append((f"Tengo un {m[0]}.", "ACK")); t.append((f"Mi {m[0]} se llama {nm}.", "ACK"))
        q, _ = self.f([f"¿Cómo se llama mi {m[0]}?"], [f"¿Cuál es el nombre de mi {m[0]}?"]); t.append((q, nm))
        t.append((f"Me gusta {g}.", "ACK"))
        q, _ = self.f(["¿Qué me gusta?"], ["¿Sabes qué me gusta?", "¿Recuerdas qué me gusta?"]); t.append((q, g.split()[1]))
        t.append((f"¿Me gusta {g2}?", "ABST"))
        t.append((f"¿Vivo en {l2}?", "^no;" + l))
        t.append((f"Soy {prof}.", "ACK"))
        q, _ = self.f(["¿A qué me dedico?"], ["¿Cuál es mi profesión?", "¿En qué trabajo?"]); t.append((q, pm + "|" + pf))
        q, _ = self.f(["¿Qué sabes de mí?"], ["¿Qué recuerdas de mí?", "Cuéntame lo que sabes de mí."]); t.append((q, yo + ";" + l))
        return t

    def gustos(self):
        (p, _), (p2, _) = self.persona(2); g1, g2, g3 = self.v["gustos"][:3]; self.r.shuffle(x := [g1, g2, g3]); g1, g2, g3 = x
        n = lambda g: g.split()[1]
        t = [(f"A {p} le gusta {g1}.", "ACK"), (f"A {p} no le gusta {g2}.", "ACK")]
        q, _ = self.f([f"¿Qué le gusta a {p}?"], [f"¿A {p} qué le gusta?", f"¿Sabes qué le gusta a {p}?"]); t.append((q, n(g1) + ";!gusta " + g2))
        t.append((f"¿Le gusta a {p} {g2}?", "^no"))
        t.append((f"¿Le gusta a {p} {g1}?", "^si"))
        s, _ = self.f([f"A {p2} le encanta {g3}."], [f"A {p2} le gusta mucho {g3}."]); t.append((s, "ACK"))
        q, _ = self.f([f"¿A quién le gusta {g1}?"], [f"¿Quién disfruta de {g1}?"] if False else [f"¿A quién le gusta {g1}?"]); t.append((q, p + ";!" + p2))
        t.append((f"¿Le gusta a {p2} {g1}?", "ABST"))
        t.append((f"¿Qué le gusta a {p2}?", n(g3)))
        q, _ = self.f([f"¿Qué no le gusta a {p}?"], [f"¿A {p} qué no le gusta?"]); t.append((q, n(g2)))
        return t

    def comparativos(self):
        (a, sa_), (b, sb), (c, sc) = self.persona(3); r = self.r.choice(self.v["rasgos"]); e1, e2 = self.r.sample(range(20, 70), 2)
        R = lambda s: fem(r) if s == "f" else r
        t = [(f"{a} es más {R(sa_)} que {b}.", "ACK"), (f"{b} es más {R(sb)} que {c}.", "ACK")]
        t.append((f"¿Es {a} más {R(sa_)} que {b}?", "^si"))
        t.append((f"¿Es {c} más {R(sc)} que {a}?", "^no"))
        q, _ = self.f([f"¿Quién es más {r}, {a} o {c}?"], [f"¿Quién es más {r}: {c} o {a}?", f"Entre {a} y {c}, ¿quién es más {r}?"]); t.append((q, "^" + a + "|" + a + " es"))
        t.append((f"¿Es {a} más {R(sa_)} que {c}?", "^si"))
        t.append((f"{a} tiene {e1} años.", "ACK")); t.append((f"{c} tiene {e2} años.", "ACK"))
        may = a if e1 > e2 else c
        q, _ = self.f([f"¿Quién es mayor, {a} o {c}?"], [f"¿Quién tiene más años, {a} o {c}?", f"¿Quién es mayor: {c} o {a}?"]); t.append((q, may + ";!" + (c if may == a else a) + " es mayor"))
        q, _ = self.f([f"¿Cuántos años tiene {c}?"], [f"¿Qué edad tiene {c}?", f"¿Cuál es la edad de {c}?"]); t.append((q, str(e2)))
        t.append((f"¿Cuántos años tiene {b}?", "ABST"))
        return t

    def clases(self):
        cl, sup, vpl, vsg = self.r.choice(self.v["clases"]); otra = [c for c in self.v["clases"] if c[0] != cl][0][0]; nm = self.r.choice(self.v["nombres_masc"]); (p, _), = self.persona()
        t = [(f"{nm} es un {cl}.", "ACK")]
        t.append((f"¿Es {nm} un {cl}?", "^si"))
        q, _ = self.f([f"¿Es {nm} un {sup}?"], [f"¿{nm} es un {sup}?"]); t.append((q, "^si"))
        t.append((f"¿Es {nm} un {otra}?", "^no"))
        q, _ = self.f([f"¿Qué es {nm}?"], [f"¿Qué tipo de animal es {nm}?", f"¿{nm} qué es?"]); t.append((q, cl))
        t.append((f"Los {cl}s {vpl}.", "ACK"))
        vq = vsg.split()[0].capitalize()
        t.append((f"¿{vq} {nm}{' ' + ' '.join(vsg.split()[1:]) if len(vsg.split()) > 1 else ''}?", "^si"))
        t.append((f"{nm} es de {p}.", "ACK"))
        q, _ = self.f([f"¿De quién es {nm}?"], [f"¿Quién es el dueño de {nm}?"]); t.append((q, p))
        t.append((f"¿Es {p} un {cl}?", "!^si"))
        return t

    def correcciones(self):
        (p, _), = self.persona(); l1, l2 = self.r.sample(self.v["lugares"], 2); obj = self.r.choice(self.v["objetos"]); c1, c2 = self.r.sample(self.v["colores"], 2); e1 = self.r.randint(20, 60); e2 = e1 + self.r.randint(1, 5)
        C1 = fem(c1) if obj[1] == "f" else c1; C2 = fem(c2) if obj[1] == "f" else c2
        t = [(f"{p} vive en {l1}.", "ACK")]
        s, _ = self.f([f"No, {p} vive en {l2}."], [f"Perdón, {p} vive en {l2}.", f"Me he equivocado, {p} vive en {l2}."]); t.append((s, "ACK"))
        t.append((f"¿Dónde vive {p}?", l2 + ";!" + l1))
        t.append((f"Mi {obj[0]} es {C1}.", "ACK"))
        s, _ = self.f([f"No, mi {obj[0]} es {C2}."], [f"Perdón, es {C2}.", f"Me he equivocado, mi {obj[0]} es {C2}."]); t.append((s, "ACK"))
        t.append((f"¿De qué color es mi {obj[0]}?", rz(c2) + ";!" + rz(c1)))
        t.append((f"{p} tiene {e1} años.", "ACK"))
        s, _ = self.f([f"No, {p} tiene {e2} años."], [f"Perdón, {p} tiene {e2} años."]); t.append((s, "ACK"))
        t.append((f"¿Cuántos años tiene {p}?", f"{e2};!{e1}"))
        return t

    def desconocido(self):
        (a, _), (b, sb), (c, _) = self.persona(3); l = self.r.choice(self.v["lugares"]); m = self.r.choice(self.v["mascotas"]); obj = self.r.choice(self.v["objetos"])
        t = [(f"{a} vive en {l}.", "ACK")]
        for q in self.r.sample([f"¿Dónde vive {b}?", f"¿Cuántos años tiene {a}?", f"¿Quién es la madre de {a}?", f"¿Cómo se llama el {m[0]} de {a}?", f"¿De qué color es {self.de(obj, a)}?",
                                f"¿Dónde trabaja {a}?", f"¿Quién es {c}?", f"¿Qué le gusta a {a}?", f"¿Tiene {a} un {m[0]}?", f"¿Es {a} {self.v['profs'][0][0]}?", f"¿Cuántos hermanos tiene {a}?",
                                f"¿Vive {b} en {l}?", f"¿Qué compró {a} ayer?", "¿Cómo me llamo?", "¿Dónde vivo?", f"¿Con quién vive {a}?"], 9):
            t.append((q, "ABST"))
        t.append((f"¿Dónde vive {a}?", l))
        return t

    def social(self):
        (yo, s), = self.persona(); est = self.r.choice(["triste", "cansado", "nervioso", "contento", "feliz", "preocupado"]); E = fem(est) if s == "f" else est
        neg = est in ("triste", "cansado", "nervioso", "preocupado")
        t = []
        q, _ = self.f(["Hola"], ["Hola, buenos días", "Buenas tardes", "Hola, ¿qué tal?"]); t.append((q, "hola|buenos dias|buenas|bien"))
        t.append((f"Me llamo {yo}.", yo))
        q, _ = self.f(["¿Cómo estás?"], ["¿Qué tal estás?", "¿Cómo te encuentras?"]); t.append((q, "bien"))
        s1, _ = self.f([f"Estoy {E}."], [f"Hoy estoy muy {E}.", f"Me siento {E}."]); t.append((s1, ("siento|vaya|lamento" if neg else "alegr*|que bien") + ";!no he entendido"))
        q, _ = self.f(["¿Tienes hambre?"], ["¿Tú tienes sed?", "¿Tienes sueño?"]); t.append((q, "^no;!^no lo se"))
        q, _ = self.f(["¿Eres una persona?"], ["¿Eres humano?", "¿Eres un robot?"]); t.append((q, "lcm|programa|modelo;!no conozco"))
        q, _ = self.f(["¿Qué opinas del fútbol?"], ["¿Qué piensas de la música?", "¿Te gusta el cine?"]); t.append((q, "no tengo;!no he entendido;!no conozco"))
        q, _ = self.f(["¿Cómo estoy?"], ["¿Cómo me siento?", "¿Cómo me encuentro hoy?"]); t.append((q, rz(est)))
        q, _ = self.f(["Vale, perfecto."], ["Genial, gracias.", "Ah, vale."]); t.append((q, "!no he entendido;!no conozco;!entendido:"))
        q, _ = self.f(["Gracias"], ["Muchas gracias", "Gracias por todo"]); t.append((q, "de nada|un placer|para eso|gusto|no hay de que"))
        q, _ = self.f(["Adiós"], ["Hasta luego", "Hasta mañana"]); t.append((q, "adios|hasta|nos vemos"))
        return t

    def fabrica(self):
        base = [("¿Es un perro un animal?", "^si"), ("¿De qué color es el cielo?", "azul"), ("¿Cuántos lados tiene un triángulo?", "tres|3"), ("¿Es un gato un mamífero?", "^si"),
                ("¿De qué color es la hierba?", "verde"), ("¿Es una rosa una planta?", "^si"), ("¿Es un roble un árbol?", "^si"), ("¿Para qué sirve un cuchillo?", "cortar"),
                ("¿Es una manzana una fruta?", "^si"), ("¿Es enero un mes?", "^si"), ("¿Es un coche un vehículo?", "^si"), ("¿Es un gato un pájaro?", "^no")]
        otra = [("¿Es un caballo un animal?", "^si"), ("¿De qué color es la nieve?", "blanc*"), ("¿Cuántos lados tiene un cuadrado?", "cuatro|4"), ("¿Es un pino una planta?", "^si"),
                ("¿De qué color es el sol?", "amarillo"), ("¿Es una silla un mueble?", "^si"), ("¿Para qué sirve una cama?", "dormir"), ("¿Es una bicicleta un vehículo?", "^si"),
                ("¿Es una manzana un alimento?", "^si"), ("¿Es el lunes un día?", "^si"), ("¿Tiene un pájaro alas?", "^si"), ("¿Es un perro un pez?", "^no"), ("¿Es una mesa un animal?", "^no")]
        pool = otra if self.ciego else base
        t = [(q, c) for q, c in self.r.sample(pool, 7)]
        t.append((self.r.choice(["¿Qué es un zorbliano?", "¿Qué es un plimbo?", "¿De qué color es un blixo?"]) if not self.ciego else self.r.choice(["¿Qué es un fremolín?", "¿De qué color es un dratal?"]), "ABST"))
        return t

    def colores_img(self):
        c1, c2 = self.r.sample(self.v["colores"], 2); c3 = [c for c in self.v["colores"] if c not in (c1, c2)][0]
        q, _ = self.f(["¿De qué color es esta imagen?"], ["¿Qué color ves?", "¿Qué color es este?"])
        t = [({"texto": q, "imagen": png(RGB[c1]), "nombre": "a.png"}, c1)]
        t.append(("¿De qué color es?", c1))
        t.append(({"texto": "", "imagen": png(RGB[c2]), "nombre": "b.png"}, c2))
        t.append(("¿De qué color es?", c2 + ";!" + c1))
        t.append(({"texto": f"¿Es {c3}?", "imagen": png(RGB[c2]), "nombre": "c.png"}, "!^si"))
        return t

    def habitos(self):
        (p, _), = self.persona(); (h, clave), = self.r.sample(self.v["hab"], 1); d = self.r.choice(self.v["dias"]); an = self.r.randint(1960, 2005); l = self.r.choice(self.v["lugares"])
        t = [(f"{p} {h} {d}.", "ACK")]
        q, _ = self.f([f"¿Cuándo {h.replace(' a la ', ' a la ').replace('va al', 'va al')} {p}?"], [f"¿Qué días {h} {p}?"]); t.append((q, d.split()[1]))
        q, _ = self.f([f"¿Qué hace {p} {d}?"], [f"¿{p} qué hace {d}?"]); t.append((q, clave))
        t.append((f"{p} nació en {an}.", "ACK"))
        q, _ = self.f([f"¿Cuántos años tiene {p}?"], [f"¿Qué edad tiene {p}?"]); t.append((q, f"{2026 - an}|{2025 - an}"))
        t.append((f"{p} nació en {l}.", "ACK"))
        q, _ = self.f([f"¿Dónde nació {p}?"], [f"¿En qué ciudad nació {p}?"]); t.append((q, l))
        q, _ = self.f([f"¿Cuándo nació {p}?"], [f"¿En qué año nació {p}?"]); t.append((q, str(an)))
        return t

    def mixta(self):
        """Conversación larga con varios temas intercalados (memoria y referentes)."""
        (yo, s), (a, sa_), (b, sb) = self.persona(3); l1, l2 = self.r.sample(self.v["lugares"], 2); m = self.r.choice(self.v["mascotas"]); nm = self.r.choice(self.v["nombres_masc"])
        g = self.r.choice(self.v["gustos"]); n1 = self.r.choice(list(NUMS)); (an, _) = self.r.choice(self.v["animales"]); rel = "hermana" if sa_ == "f" else "hermano"
        pron = "Ella" if sa_ == "f" else "Él"
        t = [(f"Me llamo {yo}.", yo), (f"{a} es mi {rel}.", "ACK"), (f"{pron} vive en {l1}.", "ACK"), (f"Yo vivo en {l2}.", "ACK")]
        t.append((f"¿Dónde vive mi {rel}?", l1 + ";!" + l2)); t.append(("¿Dónde vivo?", l2 + ";!" + l1))
        t.append((f"{a} tiene un {m[0]}.", "ACK")); t.append((f"Se llama {nm}.", "ACK"))
        t.append((f"A {b} le gusta {g}.", "ACK")); t.append((f"{b} tiene {NUMS[n1]} {an}.", "ACK"))
        t.append((f"¿Quién es mi {rel}?", a)); t.append((f"¿Cómo se llama el {m[0]} de mi {rel}?", nm))
        t.append((f"¿Cuántos {an} tiene {b}?", f"{NUMS[n1]}|{n1}")); t.append((f"¿Qué le gusta a {b}?", g.split()[1]))
        t.append((f"¿Tiene {b} un {m[0]}?", "!^si" if m[0] + "s" != an else "ANY")); t.append(("¿Cómo me llamo?", yo))
        t.append((f"¿Dónde vive {b}?", "ABST")); t.append((f"¿Quién vive en {l1}?", a))
        return t


LEX = {
    "dev": dict(svo=[("lee", "leyó", "el periódico", "periódico"), ("cocina", "cocinó", "pasta", "pasta"), ("estudia", "estudió", "medicina", "medicina"), ("pinta", "pintó", "cuadros", "cuadros"),
                     ("toca", "tocó", "el piano", "piano"), ("escribe", "escribió", "cartas", "cartas"), ("vende", "vendió", "zapatos", "zapatos"), ("conduce", "condujo", "un camión", "camión"),
                     ("cuida", "cuidó", "el jardín", "jardín"), ("colecciona", "coleccionó", "sellos", "sellos"), ("arregla", "arregló", "relojes", "relojes"), ("bebe", "bebió", "leche", "leche"),
                     ("come", "comió", "pescado", "pescado"), ("escucha", "escuchó", "la radio", "radio"), ("limpia", "limpió", "la cocina", "cocina")],
               adjs=["simpático", "tímido", "generoso", "alegre", "trabajador", "amable", "curioso", "tranquilo", "valiente", "paciente"],
               lugares=["la playa", "el parque", "la biblioteca", "el mercado", "la oficina", "el colegio"]),
    "ciego": dict(svo=[("visita", "visitó", "museos", "museos"), ("prepara", "preparó", "la cena", "cena"), ("enseña", "enseñó", "matemáticas", "matemáticas"), ("dibuja", "dibujó", "paisajes", "paisajes"),
                       ("repara", "reparó", "ordenadores", "ordenadores"), ("planta", "plantó", "tomates", "tomates"), ("canta", "cantó", "ópera", "ópera"), ("compra", "compró", "flores", "flores"),
                       ("hornea", "horneó", "pan", "pan"), ("graba", "grabó", "vídeos", "vídeos"), ("construye", "construyó", "casas", "casas"), ("toma", "tomó", "café", "café"),
                       ("riega", "regó", "las plantas", "plantas"), ("usa", "usó", "el ordenador", "ordenador"), ("lava", "lavó", "la ropa", "ropa")],
                  adjs=["divertido", "serio", "sincero", "optimista", "ordenado", "cariñoso", "inteligente", "nervioso", "educado", "creativo"],
                  lugares=["la montaña", "el teatro", "la piscina", "el hospital", "la estación", "el museo"]),
}


def _lexico(self):
    L = LEX[self.split]
    (p, s), (p2, s2) = self.persona(2); (v, vp, o, clave), (v2, vp2, o2, clave2) = self.r.sample(L["svo"], 2); a = self.r.choice(L["adjs"]); lug = self.r.choice(L["lugares"])
    A = fem(a) if s == "f" else a
    A = A if not (s == "f" and a == "trabajador") else "trabajadora"
    t = [(f"{p} {v} {o}.", "ACK")]
    q, _ = self.f([f"¿Qué {v} {p}?"], [f"¿{p} qué {v}?", f"¿Sabes qué {v} {p}?"]); t.append((q, clave))
    q, _ = self.f([f"¿Quién {v} {o}?"], [f"¿Sabes quién {v} {o}?"]); t.append((q, p))
    t.append((f"¿{v.capitalize()} {p} {o}?", "^si"))
    t.append((f"{p} es {A}.", "ACK"))
    q, _ = self.f([f"¿Cómo es {p}?"], [f"¿{p} cómo es?", f"¿Qué sabes de {p}?"]); t.append((q, rz(a) if a.endswith("o") else a + "*"))
    t.append((f"{p2} {vp2} {o2} ayer.", "ACK"))
    q, _ = self.f([f"¿Qué {vp2} {p2} ayer?"], [f"¿Qué {vp2} ayer {p2}?", f"¿{p2} qué {vp2} ayer?"]); t.append((q, clave2))
    t.append((f"¿Quién {vp2} {o2}?", p2 + ";!" + p + " " + vp2))
    t.append((f"{p} está en {lug}.", "ACK"))
    q, _ = self.f([f"¿Dónde está {p}?"], [f"¿En qué lugar está {p}?", f"¿Sabes dónde está {p}?"]); t.append((q, lug.split()[1]))
    t.append((f"¿{v2.capitalize()} {p} {o2}?", "ABST"))
    t.append((f"¿Dónde está {p2}?", "ABST"))
    return t


Gen.lexico = _lexico

CATS = ["lexico", "atributos", "familia", "lugar", "cantidad", "negacion", "correferencia", "acciones", "usuario", "gustos", "comparativos", "clases", "correcciones", "desconocido", "social", "fabrica",
        "colores_img", "habitos", "mixta"]


def generar(split, n_por_cat=10, semilla=1, cats=None):
    out = []
    for ci, cat in enumerate(cats or CATS):
        for k in range(n_por_cat):
            g = Gen(split, hash((split, cat, k, semilla)) % (2 ** 31) if False else (semilla * 1000003 + ci * 10007 + k * 101 + (0 if split == "dev" else 7)))
            out.append({"id": f"{split}-{cat}-{semilla}-{k}", "cat": cat, "turnos": getattr(g, cat)()})
    return out


if __name__ == "__main__":
    import sys, json
    from lab.banco import correr, imprime
    split = sys.argv[1] if len(sys.argv) > 1 else "dev"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    sem = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    cats = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    verb = "-v" in sys.argv
    D = generar(split, n, sem, cats)
    filas, res = correr(D, verboso=False, salida=f"lab/res_{split}_{sem}.json")
    if verb or split == "dev":
        vistos = set()
        for f in filas:
            if f["v"] not in (None, "OK"):
                clave = (f["cat"], f["crit"][:12], f["v"], f["q"].split()[0:2] and " ".join(f["q"].split()[:2]))
                if clave in vistos and not verb:
                    continue
                vistos.add(clave)
                print("  %-13s [%s] > %s\n        %s      <-- %s" % (f["v"], f["id"], f["q"], str(f["r"])[:200], f["crit"]))
    imprime(res, f"{split.upper()} semilla={sem}")
