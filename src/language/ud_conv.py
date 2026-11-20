"""Frases CONVERSACIONALES cortas con árbol conocido (LCM 2.1).

Los corpus UD son prensa: de ~22.000 frases de entrenamiento solo ~150 son preguntas y ~1.200 tienen siete palabras o menos.
La Escuela casi no ha visto «¿Dónde vive Pablo?», «Tengo dos gatos», «Me llamo Ana» o «¿Es alta tu hermana?».
Aquí se generan esas estructuras con vocabulario cotidiano y la anotación de UD (mismas convenciones que GSD/AnCora:
atributo como raíz y verbo copulativo `cop`; clíticos `obl`; «estar en» verbo pleno + `obl`).

Dos vocabularios disjuntos: 'train' para afinar y 'eval' para medir con palabras que la Escuela no ha visto en estos marcos.
Una parte de las frases va sin tildes, sin «¿» o en minúsculas, como escribe mucha gente.
"""
from __future__ import annotations

import random
import unicodedata
from typing import List

NOMBRES = """Ana Luis Marta Pablo Sara Carlos Elena Jorge Lucía Diego Nuria Raúl Pedro Juan María José Laura Javier Carmen Antonio Isabel Miguel Rosa Manuel Pilar David Cristina
Daniel Paula Alejandro Andrea Sergio Marina Alberto Silvia Fernando Beatriz Roberto Patricia Ricardo Mónica Álvaro Natalia Adrián Irene Rubén Teresa Víctor Clara Hugo Julia Iván Alicia Óscar
Eva Mario Lorena Enrique Sonia Guillermo Verónica Ignacio Rocío Samuel Aitana Bruno Celia Darío Esteban Fátima Gabriel Helena Joaquín Lidia Marcelo Nerea Ramón Olga Mateo Noelia Gonzalo
Tomás Adriana Emilio Fabián Valeria Inés Marcos Leire Íñigo Vera Toby Luna Rex Nala Coco Kira Thor Lola Pipo Rocky Mar Sol Luz Paz León Ángel Dolores Mercedes Nieves Jesús Andrés
Susana Felipe Agustín Amparo Lourdes Rafael Begoña Ismael Yolanda Emma Leo Noa Martín Abril Bea Nico Maite Koldo Jimena Saúl Elsa Ciro Greta Unai Zoe""".split()
LUGARES = """Madrid Sevilla Valencia Bilbao Granada Toledo Vigo Cádiz Burgos Murcia Oviedo Zaragoza Salamanca Lugo Almería Pamplona Tarragona Huelva Cuenca Gijón Alicante Badajoz Girona
Santander Logroño Ávila Málaga Córdoba Lisboa París Roma Londres Berlín Jaén Teruel Soria Lleida Vitoria Segovia Mérida Ibiza Francia Italia Portugal México Chile Perú""".split()
# (singular, plural, género)
SUST = [x.split("/") for x in """coche/coches/m casa/casas/f libro/libros/m bicicleta/bicicletas/f mesa/mesas/f moto/motos/f piso/pisos/m reloj/relojes/m guitarra/guitarras/f silla/sillas/f
perro/perros/m gato/gatos/m caballo/caballos/m pájaro/pájaros/m pez/peces/m tortuga/tortugas/f conejo/conejos/m loro/loros/m vaca/vacas/f ratón/ratones/m
manzana/manzanas/f pera/peras/f naranja/naranjas/f plátano/plátanos/m tomate/tomates/m patata/patatas/f huevo/huevos/m galleta/galletas/f bocadillo/bocadillos/m
paraguas/paraguas/m mochila/mochilas/f tablet/tablets/f sofá/sofás/m camión/camiones/m bufanda/bufandas/f abrigo/abrigos/m camisa/camisas/f pantalón/pantalones/m zapato/zapatos/m
llave/llaves/f gafa/gafas/f móvil/móviles/m ordenador/ordenadores/m cuaderno/cuadernos/m lápiz/lápices/m carta/cartas/f foto/fotos/f cuadro/cuadros/m flor/flores/f
árbol/árboles/m jardín/jardines/m puerta/puertas/f ventana/ventanas/f cama/camas/f lámpara/lámparas/f cocina/cocinas/f hermano/hermanos/m hermana/hermanas/f hijo/hijos/m
hija/hijas/f primo/primos/m amigo/amigos/m amiga/amigas/f vecino/vecinos/m jefe/jefes/m profesor/profesores/m médico/médicos/m alumno/alumnos/m tío/tíos/m abuelo/abuelos/m
abuela/abuelas/f padre/padres/m madre/madres/f pelota/pelotas/f juguete/juguetes/m película/películas/f canción/canciones/f pulsera/pulseras/f anillo/anillos/m regalo/regalos/m
tren/trenes/m barco/barcos/m avión/aviones/m tienda/tiendas/f huerto/huertos/m examen/exámenes/m reunión/reuniones/f maleta/maletas/f vaso/vasos/m plato/platos/m""".split()]
MASA = [x.split("/") for x in """carne/f verdura/f pescado/m pan/m queso/m fruta/f arroz/m pasta/f chocolate/m sopa/f café/m leche/f té/m agua/f zumo/m vino/m azúcar/m sal/f
música/f fútbol/m cine/m tenis/m pintura/f teatro/m ajedrez/m dinero/m ropa/f medicina/f historia/f yoga/m natación/f""".split()]
LOC_COM = [x.split("/") for x in """hospital/m escuela/f banco/m tienda/f playa/f parque/m biblioteca/f mercado/m oficina/f colegio/m montaña/f piscina/f estación/f museo/m cocina/f
jardín/m garaje/m restaurante/m farmacia/f universidad/f gimnasio/m pueblo/m centro/m cajón/m armario/m salón/m campo/m""".split()]
ADJ = """grande pequeño alto bajo nuevo viejo rápido lento caro barato largo corto limpio sucio fuerte débil rojo azul verde amarillo negro blanco gris marrón joven listo delgado
simpático tímido generoso alegre trabajador amable curioso tranquilo valiente paciente divertido serio sincero ordenado cariñoso inteligente nervioso educado creativo cansado contento
triste enfermo feliz ocupado libre abierto cerrado roto bonito feo ancho estrecho pesado ligero moderno antiguo oscuro claro dulce salado frío caliente lleno vacío""".split()
PROF = """médico profesor abogado ingeniero enfermero cocinero camarero arquitecto maestro veterinario fontanero carpintero bombero panadero peluquero mecánico electricista
periodista dentista estudiante pintor escritor conductor programador""".split()
REL = [x.split("/") for x in "padre/m madre/f hermano/m hermana/f hijo/m hija/f abuelo/m abuela/f tío/m tía/f primo/m prima/f amigo/m amiga/f vecino/m vecina/f jefe/m jefa/f marido/m mujer/f novio/m novia/f".split()]
# verbos transitivos (lema) y con complemento de lugar
V_TR = """comprar vender leer cocinar estudiar pintar tocar escribir cuidar arreglar beber comer escuchar limpiar visitar preparar enseñar dibujar reparar plantar cantar
tomar regar usar lavar encontrar perder buscar traer llevar abrir cerrar mirar cortar guardar necesitar querer tener ver hacer romper alquilar probar""".split()
V_LOC = [("vivir", "en"), ("trabajar", "en"), ("estudiar", "en"), ("viajar", "a"), ("llegar", "a"), ("entrar", "en"), ("salir", "de"), ("volver", "a"), ("pasear", "por"), ("jugar", "en"), ("dormir", "en"), ("comer", "en")]
V_INTR = "dormir correr nadar cantar ladrar volar trabajar llorar sonreír bailar viajar descansar caminar jugar estudiar".split()
V_GUST = "gustar encantar interesar molestar aburrir".split()
NUM = [("dos", 2), ("tres", 3), ("cuatro", 4), ("cinco", 5), ("seis", 6), ("siete", 7), ("ocho", 8), ("diez", 10), ("2", 2), ("3", 3), ("5", 5), ("12", 12)]
TIEMPO = "ayer hoy anoche mañana anteayer ahora siempre".split()
EDADES = ["20", "25", "30", "34", "41", "52", "67", "8", "15", "doce", "veinte", "treinta"]


def _sa(s):
    s = s.replace("ñ", "\0")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.replace("\0", "ñ")


def _parte(xs, split, k=5):
    """Vocabulario disjunto: uno de cada k elementos queda reservado para 'eval'."""
    return [x for i, x in enumerate(xs) if (i % k == k - 1) == (split == "eval")]


class _B:
    def __init__(self):
        self.w, self.lab = [], {}

    def add(self, label, form, upos, rel, head, lemma=None):
        self.lab[label] = len(self.w) + 1
        self.w.append([form, upos, head, rel, lemma if lemma is not None else form.lower()])
        return self

    def done(self):
        return [(f, u, 0 if h is None else self.lab[h], r, l) for f, u, h, r, l in self.w]


class Conv:
    def __init__(self, split="train", seed=0):
        from src.nucleo20 import morfo as M
        self.M = M
        self.r = random.Random(seed)
        p = lambda xs: _parte(xs, split)
        self.nom, self.lug, self.sust, self.masa, self.loc, self.adj, self.prof, self.rel = p(NOMBRES), p(LUGARES), p(SUST), p(MASA), p(LOC_COM), p(ADJ), p(PROF), REL
        self.vtr, self.vloc, self.vintr = p(V_TR), p(V_LOC) or V_LOC, p(V_INTR)

    # ---- piezas
    def c(self, xs):
        return self.r.choice(xs)

    def verbo(self, lema, t="pres", p="3s"):
        return self.M.conjugar(lema, t, p)

    def fem(self, a):
        if a.endswith("o"):
            return a[:-1] + "a"
        if a.endswith(("dor", "tor")) or a in ("profesor", "pintor", "escritor", "conductor", "programador"):
            return a + "a"
        return a

    def nombre(self, b, lab, rel, head):
        b.add(lab, self.c(self.nom), "PROPN", rel, head)

    def sn(self, b, lab, rel, head, det=None, sust=None, adj=False, pl=False, poss_ok=True):
        """det + sustantivo (+ adjetivo). det: 'el','un','mi','su','num', None=elige."""
        s = sust or self.c(self.sust)
        det = det or self.c(["el", "el", "un", "un", "mi", "su"] if poss_ok else ["el", "un"])
        g = s[2]
        forma = s[1] if pl else s[0]
        if det == "num":
            n, _ = self.c(NUM)
            b.add(lab + "d", n, "NUM", "nummod", lab)
            forma = s[1]
        else:
            df = {"el": {"m": ("el", "los"), "f": ("la", "las")}, "un": {"m": ("un", "unos"), "f": ("una", "unas")}, "mi": {"m": ("mi", "mis"), "f": ("mi", "mis")},
                  "su": {"m": ("su", "sus"), "f": ("su", "sus")}, "tu": {"m": ("tu", "tus"), "f": ("tu", "tus")}}[det][g][1 if pl else 0]
            b.add(lab + "d", df, "DET", "det", lab, {"el": "el", "un": "uno", "mi": "mi", "su": "su", "tu": "tu"}[det])
        b.add(lab, forma, "NOUN", rel, head, s[0])
        if adj:
            a = self.c(self.adj)
            a = self.fem(a) if g == "f" else a
            if pl:
                a = a + ("s" if a[-1] in "aeiouáéó" else "es")
            b.add(lab + "a", a, "ADJ", "amod", lab, self.c([a]) and self._lema_adj(a))
        return s

    def _lema_adj(self, a):
        base = a[:-2] if a.endswith("es") and a[-3] not in "aeiou" else (a[:-1] if a.endswith("s") else a)
        return base[:-1] + "o" if base.endswith("a") and (base[:-1] + "o") in ADJ else base

    def sujeto(self, b, head, lab="s"):
        """Nombre propio (60 %), «el/mi N» (30 %) o «el N de Nombre» (10 %). Devuelve género."""
        x = self.r.random()
        if x < 0.6:
            n = self.c(self.nom)
            b.add(lab, n, "PROPN", "nsubj", head)
            return "f" if _sa(n).endswith("a") else "m"
        s = self.sn(b, lab, "nsubj", head, det=self.c(["el", "mi", "su", "el"]))
        if x > 0.9:
            b.add(lab + "p", "de", "ADP", "case", lab + "n")
            b.add(lab + "n", self.c(self.nom), "PROPN", "nmod", lab)
        return s[2]

    # ---- marcos
    def frase(self):
        r = self.r
        b = _B()
        tipo = r.choice(["svo", "svo", "sloc", "cop_adj", "cop_adj", "cop_n", "estar_adj", "estar_loc", "tener_num", "tener_un", "edad", "neg", "yo", "yo", "gustar", "llamar",
                         "rel", "comp", "pret", "dar", "plural", "pron", "querer",
                         "q_donde", "q_donde", "q_que", "q_que", "q_quien", "q_quien", "q_como", "q_como", "q_cuantos", "q_cuando", "q_sino", "q_sino", "q_sino", "q_color",
                         "q_yo", "q_yo", "q_gustar", "q_rel", "q_y", "q_sv"])
        preg = tipo.startswith("q_")
        if preg:
            b.add("ab", "¿", "PUNCT", "punct", "ROOT")
        getattr(self, "_" + tipo)(b)
        b.add("fin", "?" if preg else ".", "PUNCT", "punct", "ROOT")
        # la raíz se fija por la etiqueta que cada marco deja en b.raiz
        raiz = b.raiz
        for w in b.w:
            if w[2] == "ROOT":
                w[2] = raiz
        out = b.done()
        # mayúscula inicial
        k0 = 1 if preg else 0
        f0 = out[k0][0]
        out[k0] = (f0[:1].upper() + f0[1:],) + out[k0][1:]
        # escritura descuidada
        x = r.random()
        if x < 0.10:                                  # sin signos de apertura ni punto final
            out = self._quita(out, quita_ab=True, quita_fin=not preg)
        elif x < 0.22:                                # sin tildes, en minúsculas, sin «¿»
            out = self._quita(out, quita_ab=True, quita_fin=not preg)
            out = [(_sa(f).lower(), u, h, rl, l) for f, u, h, rl, l in out]
        elif x < 0.30:                                # sin tildes
            out = [(_sa(f), u, h, rl, l) for f, u, h, rl, l in out]
        return out

    @staticmethod
    def _quita(out, quita_ab, quita_fin):
        idx = [i for i, w in enumerate(out) if not ((quita_ab and w[0] == "¿") or (quita_fin and w[0] == "." and i == len(out) - 1))]
        mapa = {old + 1: new + 1 for new, old in enumerate(idx)}
        return [(out[i][0], out[i][1], mapa.get(out[i][2], 0), out[i][3], out[i][4]) for i in idx]

    def _tiempo(self, b, head, p=0.3):
        if self.r.random() < p:
            b.add("t", self.c(TIEMPO), "ADV", "advmod", head)

    def _obj(self, b, head, lab="o"):
        x = self.r.random()
        if x < 0.25:
            m = self.c(self.masa)
            b.add(lab, m[0], "NOUN", "obj", head)
        elif x < 0.4:
            self.sn(b, lab, "obj", head, det="num")
        elif x < 0.5:
            b.add(lab, self.c(self.sust)[1], "NOUN", "obj", head, None)
            b.w[-1][4] = [s for s in self.sust if s[1] == b.w[-1][0]][0][0]
        else:
            self.sn(b, lab, "obj", head, adj=self.r.random() < 0.2)

    def _svo(self, b, t=None):
        self.sujeto(b, "v")
        lema = self.c(self.vtr)
        t = t or self.c(["pres", "pres", "pret", "imp"])
        b.add("v", self.verbo(lema, t), "VERB", "root", None, lema)
        self._obj(b, "v")
        self._tiempo(b, "v", 0.3 if t != "pres" else 0.1)
        b.raiz = "v"

    def _sloc(self, b):
        self.sujeto(b, "v")
        lema, prep = self.c(self.vloc)
        if self.r.random() < 0.2:
            b.add("ah", self.c(["ahora", "ya"]), "ADV", "advmod", "v")
        b.add("v", self.verbo(lema, self.c(["pres", "pres", "imp", "pret"])), "VERB", "root", None, lema)
        self._lugar(b, prep, "v")
        b.raiz = "v"

    def _lugar(self, b, prep, head, lab="l"):
        if self.r.random() < 0.5:
            b.add(lab + "p", prep, "ADP", "case", lab)
            b.add(lab, self.c(self.lug), "PROPN", "obl", head)
        else:
            s = self.c(self.loc)
            b.add(lab + "p", prep, "ADP", "case", lab)
            b.add(lab + "d", self.c([{"m": "el", "f": "la"}[s[1]], {"m": "un", "f": "una"}[s[1]]]), "DET", "det", lab, None)
            b.w[-1][4] = "el" if b.w[-1][0] in ("el", "la") else "uno"
            b.add(lab, s[0], "NOUN", "obl", head)

    def _cop_adj(self, b):
        g = self.sujeto(b, "a")
        b.add("c", self.c(["es", "es", "era", "son"][:3]), "AUX", "cop", "a", "ser")
        if self.r.random() < 0.25:
            b.add("m", self.c(["muy", "bastante", "tan", "poco"]), "ADV", "advmod", "a", None)
            b.w[-1][4] = {"muy": "mucho"}.get(b.w[-1][0], b.w[-1][0])
        a = self.c(self.adj)
        b.add("a", self.fem(a) if g == "f" else a, "ADJ", "root", None, a)
        if self.r.random() < 0.15:
            a2 = self.c(self.adj)
            b.add("y", "y", "CCONJ", "cc", "a2")
            b.add("a2", self.fem(a2) if g == "f" else a2, "ADJ", "conj", "a", a2)
        b.raiz = "a"

    def _cop_n(self, b):
        g = self.sujeto(b, "n")
        b.add("c", "es", "AUX", "cop", "n", "ser")
        if self.r.random() < 0.5:
            pr = self.c(self.prof)
            b.add("n", self.fem(pr) if g == "f" else pr, "NOUN", "root", None, pr)
        else:
            s = self.c(self.sust)
            b.add("nd", {"m": "un", "f": "una"}[s[2]], "DET", "det", "n", "uno")
            b.add("n", s[0], "NOUN", "root", None)
        b.raiz = "n"

    def _estar_adj(self, b):
        g = self.sujeto(b, "a")
        b.add("c", self.c(["está", "está", "estaba"]), "AUX", "cop", "a", "estar")
        if self.r.random() < 0.25:
            b.add("m", "muy", "ADV", "advmod", "a", "mucho")
        a = self.c(self.adj)
        b.add("a", self.fem(a) if g == "f" else a, "ADJ", "root", None, a)
        self._tiempo(b, "a", 0.15)
        b.raiz = "a"

    def _estar_loc(self, b):
        self.sujeto(b, "v")
        b.add("v", self.c(["está", "está", "estaba", "están"][:3]), "VERB", "root", None, "estar")
        self._lugar(b, "en", "v")
        b.raiz = "v"

    def _tener_num(self, b):
        self.sujeto(b, "v")
        b.add("v", self.c(["tiene", "tiene", "tenía"]), "VERB", "root", None, "tener")
        self.sn(b, "o", "obj", "v", det="num")
        b.raiz = "v"

    def _tener_un(self, b):
        self.sujeto(b, "v")
        b.add("v", "tiene", "VERB", "root", None, "tener")
        self.sn(b, "o", "obj", "v", det="un", adj=self.r.random() < 0.3)
        b.raiz = "v"

    def _edad(self, b):
        self.sujeto(b, "v")
        b.add("v", "tiene", "VERB", "root", None, "tener")
        b.add("n", self.c(EDADES), "NUM", "nummod", "o")
        b.add("o", "años", "NOUN", "obj", "v", "año")
        b.raiz = "v"

    def _neg(self, b):
        self.sujeto(b, "v")
        b.add("no", self.c(["no", "no", "nunca", "ya no"][:3]), "ADV", "advmod", "v")
        lema = self.c(self.vtr)
        b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema)
        self._obj(b, "v")
        b.raiz = "v"

    def _yo(self, b):
        x = self.c(["vivo", "tengo", "soy_n", "soy_adj", "estoy", "llamo", "vtr", "vloc", "edad", "gusta"])
        if x == "vivo" or x == "vloc":
            lema, prep = ("vivir", "en") if x == "vivo" else self.c(self.vloc)
            if self.r.random() < 0.2:
                b.add("yo", "yo", "PRON", "nsubj", "v")
            b.add("v", self.verbo(lema, self.c(["pres", "pres", "imp", "pret"]), "1s"), "VERB", "root", None, lema)
            self._lugar(b, prep, "v"); b.raiz = "v"
        elif x == "tengo":
            b.add("v", "tengo", "VERB", "root", None, "tener")
            self.sn(b, "o", "obj", "v", det=self.c(["num", "un", "un"]), adj=self.r.random() < 0.2); b.raiz = "v"
        elif x == "edad":
            b.add("v", "tengo", "VERB", "root", None, "tener")
            b.add("n", self.c(EDADES), "NUM", "nummod", "o"); b.add("o", "años", "NOUN", "obj", "v", "año"); b.raiz = "v"
        elif x == "soy_n":
            b.add("c", "soy", "AUX", "cop", "n", "ser")
            if self.r.random() < 0.5:
                b.add("n", self.c(self.nom), "PROPN", "root", None)
            else:
                pr = self.c(self.prof)
                b.add("n", self.c([pr, self.fem(pr)]), "NOUN", "root", None, pr)
            b.raiz = "n"
        elif x in ("soy_adj", "estoy"):
            b.add("c", "soy" if x == "soy_adj" else "estoy", "AUX", "cop", "a", "ser" if x == "soy_adj" else "estar")
            if self.r.random() < 0.3:
                b.add("m", "muy", "ADV", "advmod", "a", "mucho")
            a = self.c(self.adj)
            b.add("a", self.c([a, self.fem(a)]), "ADJ", "root", None, a); b.raiz = "a"
        elif x == "llamo":
            b.add("me", "me", "PRON", "obl", "v", "yo")
            b.add("v", "llamo", "VERB", "root", None, "llamar")
            b.add("n", self.c(self.nom), "PROPN", "obj", "v"); b.raiz = "v"
        elif x == "gusta":
            b.add("me", "me", "PRON", "obl", "v", "yo")
            lema = self.c(V_GUST)
            b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema)
            m = self.c(self.masa)
            b.add("od", {"m": "el", "f": "la"}[m[1]], "DET", "det", "o", "el"); b.add("o", m[0], "NOUN", "nsubj", "v"); b.raiz = "v"
        else:
            lema = self.c(self.vtr)
            b.add("v", self.verbo(lema, self.c(["pres", "pret"]), "1s"), "VERB", "root", None, lema)
            self._obj(b, "v"); self._tiempo(b, "v", 0.2); b.raiz = "v"

    def _gustar(self, b):
        b.add("ap", "a", "ADP", "case", "e"); b.add("e", self.c(self.nom), "PROPN", "obl", "v")
        if self.r.random() < 0.3:
            b.add("no", "no", "ADV", "advmod", "v")
        b.add("le", "le", "PRON", "obl", "v", "él")
        lema = self.c(V_GUST)
        if self.r.random() < 0.3:
            b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema)
            inf = self.c(self.vintr)
            b.add("o", inf, "VERB", "csubj", "v", inf)
        else:
            b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema)
            m = self.c(self.masa)
            b.add("od", {"m": "el", "f": "la"}[m[1]], "DET", "det", "o", "el"); b.add("o", m[0], "NOUN", "nsubj", "v")
        b.raiz = "v"

    def _llamar(self, b):
        x = self.r.random()
        if x < 0.4:
            self.sn(b, "s", "nsubj", "v", det=self.c(["mi", "el", "su"]))
            if self.r.random() < 0.5:
                b.add("sp", "de", "ADP", "case", "sn"); b.add("sn", self.c(self.nom), "PROPN", "nmod", "s")
        elif x < 0.6:
            b.add("s", self.c(self.nom), "PROPN", "nsubj", "v")
        b.add("se", "se", "PRON", "obl", "v", "él")
        b.add("v", self.c(["llama", "llama", "llamaba"]), "VERB", "root", None, "llamar")
        b.add("n", self.c(self.nom), "PROPN", "obj", "v"); b.raiz = "v"

    def _rel(self, b):
        b.add("s", self.c(self.nom), "PROPN", "nsubj", "n")
        b.add("c", "es", "AUX", "cop", "n", "ser")
        rl = self.c(self.rel)
        if self.r.random() < 0.3:
            b.add("nd", "mi", "DET", "det", "n", "mi"); b.add("n", rl[0], "NOUN", "root", None)
        else:
            if self.r.random() < 0.8:
                b.add("nd", {"m": "el", "f": "la"}[rl[1]], "DET", "det", "n", "el")
            b.add("n", rl[0], "NOUN", "root", None)
            b.add("p", "de", "ADP", "case", "o"); b.add("o", self.c(self.nom), "PROPN", "nmod", "n")
        b.raiz = "n"

    def _comp(self, b):
        g = self.sujeto(b, "a")
        b.add("c", "es", "AUX", "cop", "a", "ser")
        b.add("m", self.c(["más", "más", "menos"]), "ADV", "advmod", "a")
        a = self.c(self.adj)
        b.add("a", self.fem(a) if g == "f" else a, "ADJ", "root", None, a)
        b.add("q", "que", "SCONJ", "case", "o"); b.add("o", self.c(self.nom), "PROPN", "obl", "a"); b.raiz = "a"

    def _pret(self, b):
        self._svo(b, t="pret")

    def _dar(self, b):
        b.add("s", self.c(self.nom), "PROPN", "nsubj", "v")
        b.add("le", "le", "PRON", "obl", "v", "él")
        lema = self.c(["dar", "regalar", "prestar", "enviar", "dejar"])
        b.add("v", self.verbo(lema, "pret"), "VERB", "root", None, lema)
        self.sn(b, "o", "obj", "v", det=self.c(["el", "un"]), poss_ok=False)
        b.add("ap", "a", "ADP", "case", "d"); b.add("d", self.c(self.nom), "PROPN", "obl", "v"); b.raiz = "v"

    def _plural(self, b):
        s = self.c(self.sust)
        b.add("sd", {"m": "los", "f": "las"}[s[2]], "DET", "det", "s", "el"); b.add("s", s[1], "NOUN", "nsubj", "v", s[0])
        if self.r.random() < 0.5:
            lema = self.c(self.vintr)
            b.add("v", self.verbo(lema, "pres", "3p"), "VERB", "root", None, lema); b.raiz = "v"
        else:
            lema = self.c(self.vtr)
            b.add("v", self.verbo(lema, "pres", "3p"), "VERB", "root", None, lema)
            m = self.c(self.masa); b.add("o", m[0], "NOUN", "obj", "v"); b.raiz = "v"

    def _pron(self, b):
        pr = self.c(["Él", "Ella"])
        b.add("s", pr, "PRON", "nsubj", "v", "él")
        if self.r.random() < 0.5:
            lema, prep = self.c(self.vloc)
            b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema); self._lugar(b, prep, "v")
        else:
            lema = self.c(self.vtr)
            b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema); self._obj(b, "v")
        b.raiz = "v"

    def _querer(self, b):
        self.sujeto(b, "v")
        lema = self.c(["querer", "poder", "necesitar", "saber", "preferir"])
        b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema)
        inf = self.c(self.vtr)
        b.add("x", inf, "VERB", "xcomp", "v", inf)
        self._obj(b, "x"); b.raiz = "v"

    # ---- preguntas
    def _suj_post(self, b, head):
        if self.r.random() < 0.65:
            b.add("s", self.c(self.nom), "PROPN", "nsubj", head)
        else:
            self.sn(b, "s", "nsubj", head, det=self.c(["el", "mi", "tu", "su"]))
            if self.r.random() < 0.4:
                b.add("sp", "de", "ADP", "case", "sn"); b.add("sn", self.c(self.nom), "PROPN", "nmod", "s")

    def _q_donde(self, b):
        b.add("w", "dónde", "ADV", "advmod", "v", "dónde")
        if self.r.random() < 0.3:
            b.add("v", self.c(["está", "están", "estaba"][:2][0:1] + ["está"]), "VERB", "root", None, "estar")
        else:
            lema = self.c(self.vloc)[0]
            b.add("v", self.verbo(lema, self.c(["pres", "pres", "imp", "pret"])), "VERB", "root", None, lema)
        self._suj_post(b, "v")
        if self.r.random() < 0.15:
            b.add("t", self.c(["antes", "ahora"]), "ADV", "advmod", "v")
        b.raiz = "v"

    def _q_que(self, b):
        b.add("w", "qué", "PRON", "obj", "v", "qué")
        if self.r.random() < 0.2:
            b.add("no", "no", "ADV", "advmod", "v")
        lema = self.c(self.vtr)
        b.add("v", self.verbo(lema, self.c(["pres", "pret", "pret"])), "VERB", "root", None, lema)
        self._suj_post(b, "v"); self._tiempo(b, "v", 0.2); b.raiz = "v"

    def _q_quien(self, b):
        x = self.r.random()
        if x < 0.4:
            b.add("w", "quién", "PRON", "nsubj", "v", "quién")
            lema = self.c(self.vtr)
            b.add("v", self.verbo(lema, self.c(["pres", "pret"])), "VERB", "root", None, lema); self._obj(b, "v"); b.raiz = "v"
        elif x < 0.6:
            b.add("w", "quién", "PRON", "nsubj", "v", "quién")
            lema, prep = self.c(self.vloc)
            b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema); self._lugar(b, prep, "v"); b.raiz = "v"
        else:
            b.add("w", "quién", "PRON", "root", None, "quién")
            b.add("c", "es", "AUX", "cop", "w", "ser")
            if self.r.random() < 0.3:
                b.add("s", self.c(self.nom), "PROPN", "nsubj", "w")
            else:
                rl = self.c(self.rel)
                b.add("sd", {"m": "el", "f": "la"}[rl[1]], "DET", "det", "s", "el"); b.add("s", rl[0], "NOUN", "nsubj", "w")
                b.add("p", "de", "ADP", "case", "o"); b.add("o", self.c(self.nom), "PROPN", "nmod", "s")
            b.raiz = "w"

    def _q_como(self, b):
        x = self.r.random()
        if x < 0.5:
            b.add("w", "cómo", "PRON", "root", None, "cómo")
            b.add("c", self.c(["es", "está", "está"]), "AUX", "cop", "w", None)
            b.w[-1][4] = "ser" if b.w[-1][0] == "es" else "estar"
            self._suj_post(b, "w"); b.raiz = "w"
        else:
            b.add("w", "cómo", "PRON", "advmod", "v", "cómo")
            b.add("se", "se", "PRON", "obl", "v", "él")
            b.add("v", "llama", "VERB", "root", None, "llamar")
            self._suj_post(b, "v"); b.raiz = "v"

    def _q_cuantos(self, b):
        if self.r.random() < 0.35:
            b.add("w", "cuántos", "DET", "det", "o", "cuánto"); b.add("o", "años", "NOUN", "obj", "v", "año")
        else:
            s = self.c(self.sust)
            b.add("w", {"m": "cuántos", "f": "cuántas"}[s[2]], "DET", "det", "o", "cuánto"); b.add("o", s[1], "NOUN", "obj", "v", s[0])
        b.add("v", "tiene", "VERB", "root", None, "tener")
        self._suj_post(b, "v"); b.raiz = "v"

    def _q_cuando(self, b):
        b.add("w", "cuándo", "ADV", "advmod", "v", "cuándo")
        lema = self.c(self.vtr)
        b.add("v", self.verbo(lema, "pret"), "VERB", "root", None, lema)
        b.add("s", self.c(self.nom), "PROPN", "nsubj", "v")
        self.sn(b, "o", "obj", "v", det="el", poss_ok=False); b.raiz = "v"

    def _q_sino(self, b):
        x = self.c(["vso", "vso", "es_adj", "es_adj2", "esta_adj", "tiene", "vloc", "es_n", "esta_loc"])
        if x == "vso":
            lema = self.c(self.vtr)
            b.add("v", self.verbo(lema, self.c(["pres", "pres", "pret"])), "VERB", "root", None, lema)
            b.add("s", self.c(self.nom), "PROPN", "nsubj", "v"); self._obj(b, "v"); b.raiz = "v"
        elif x == "es_adj":
            b.add("c", "es", "AUX", "cop", "a", "ser")
            n = self.c(self.nom); b.add("s", n, "PROPN", "nsubj", "a")
            a = self.c(self.adj); b.add("a", self.fem(a) if _sa(n).endswith("a") else a, "ADJ", "root", None, a); b.raiz = "a"
        elif x == "es_adj2":
            b.add("c", "es", "AUX", "cop", "a", "ser")
            a = self.c(self.adj)
            s = self.c(self.sust)
            b.add("a", self.fem(a) if s[2] == "f" else a, "ADJ", "root", None, a)
            self.sn(b, "s", "nsubj", "a", det=self.c(["el", "mi", "tu"]), sust=s)
            if self.r.random() < 0.4:
                b.add("sp", "de", "ADP", "case", "sn"); b.add("sn", self.c(self.nom), "PROPN", "nmod", "s")
            b.raiz = "a"
        elif x == "esta_adj":
            b.add("c", "está", "AUX", "cop", "a", "estar")
            n = self.c(self.nom)
            a = self.c(self.adj)
            if self.r.random() < 0.5:
                b.add("s", n, "PROPN", "nsubj", "a"); b.add("a", self.fem(a) if _sa(n).endswith("a") else a, "ADJ", "root", None, a)
            else:
                b.add("a", self.fem(a) if _sa(n).endswith("a") else a, "ADJ", "root", None, a); b.add("s", n, "PROPN", "nsubj", "a")
            b.raiz = "a"
        elif x == "tiene":
            b.add("v", "tiene", "VERB", "root", None, "tener")
            b.add("s", self.c(self.nom), "PROPN", "nsubj", "v")
            self.sn(b, "o", "obj", "v", det=self.c(["un", "num"]), poss_ok=False); b.raiz = "v"
        elif x == "vloc":
            lema, prep = self.c(self.vloc)
            b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema)
            b.add("s", self.c(self.nom), "PROPN", "nsubj", "v"); self._lugar(b, prep, "v"); b.raiz = "v"
        elif x == "es_n":
            b.add("c", "es", "AUX", "cop", "n", "ser")
            b.add("s", self.c(self.nom), "PROPN", "nsubj", "n")
            s = self.c(self.sust)
            b.add("nd", {"m": "un", "f": "una"}[s[2]], "DET", "det", "n", "uno"); b.add("n", s[0], "NOUN", "root", None); b.raiz = "n"
        else:
            b.add("v", "está", "VERB", "root", None, "estar")
            b.add("s", self.c(self.nom), "PROPN", "nsubj", "v"); self._lugar(b, "en", "v"); b.raiz = "v"

    def _q_color(self, b):
        b.add("p", "de", "ADP", "case", "n"); b.add("w", "qué", "DET", "det", "n", "qué"); b.add("n", "color", "NOUN", "root", None)
        b.add("c", "es", "AUX", "cop", "n", "ser")
        self.sn(b, "s", "nsubj", "n", det=self.c(["el", "mi", "tu", "su"]))
        if self.r.random() < 0.5:
            b.add("sp", "de", "ADP", "case", "sn"); b.add("sn", self.c(self.nom), "PROPN", "nmod", "s")
        b.raiz = "n"

    def _q_yo(self, b):
        x = self.c(["donde", "como", "cuantos", "que", "sino"])
        if x == "donde":
            b.add("w", "dónde", "ADV", "advmod", "v", "dónde")
            lema = self.c(["vivir", "trabajar", "estudiar"])
            b.add("v", self.verbo(lema, "pres", "1s"), "VERB", "root", None, lema); b.raiz = "v"
        elif x == "como":
            b.add("w", "cómo", "PRON", "advmod", "v", "cómo"); b.add("me", "me", "PRON", "obl", "v", "yo")
            b.add("v", "llamo", "VERB", "root", None, "llamar"); b.raiz = "v"
        elif x == "cuantos":
            b.add("w", "cuántos", "DET", "det", "o", "cuánto"); b.add("o", "años", "NOUN", "obj", "v", "año")
            b.add("v", "tengo", "VERB", "root", None, "tener"); b.raiz = "v"
        elif x == "que":
            b.add("w", "qué", "PRON", "nsubj", "v", "qué"); b.add("me", "me", "PRON", "obl", "v", "yo")
            b.add("v", "gusta", "VERB", "root", None, "gustar"); b.raiz = "v"
        else:
            lema, prep = self.c(self.vloc)
            b.add("v", self.verbo(lema, "pres", "1s"), "VERB", "root", None, lema); self._lugar(b, prep, "v"); b.raiz = "v"

    def _q_gustar(self, b):
        if self.r.random() < 0.5:
            b.add("w", "qué", "PRON", "nsubj", "v", "qué"); b.add("le", "le", "PRON", "obl", "v", "él")
            b.add("v", self.verbo(self.c(V_GUST), "pres"), "VERB", "root", None, None); b.w[-1][4] = [g for g in V_GUST if self.verbo(g, "pres") == b.w[-1][0]][0]
            b.add("ap", "a", "ADP", "case", "e"); b.add("e", self.c(self.nom), "PROPN", "obl", "v")
        else:
            b.add("le", "le", "PRON", "obl", "v", "él"); b.add("v", "gusta", "VERB", "root", None, "gustar")
            b.add("ap", "a", "ADP", "case", "e"); b.add("e", self.c(self.nom), "PROPN", "obl", "v")
            m = self.c(self.masa); b.add("od", {"m": "el", "f": "la"}[m[1]], "DET", "det", "o", "el"); b.add("o", m[0], "NOUN", "nsubj", "v")
        b.raiz = "v"

    def _q_rel(self, b):
        b.add("c", "es", "AUX", "cop", "n", "ser")
        b.add("s", self.c(self.nom), "PROPN", "nsubj", "n")
        rl = self.c(self.rel)
        b.add("nd", {"m": "el", "f": "la"}[rl[1]], "DET", "det", "n", "el"); b.add("n", rl[0], "NOUN", "root", None)
        b.add("p", "de", "ADP", "case", "o"); b.add("o", self.c(self.nom), "PROPN", "nmod", "n"); b.raiz = "n"

    def _q_y(self, b):
        b.add("y", "y", "CCONJ", "cc", "n")
        if self.r.random() < 0.6:
            b.add("n", self.c(self.nom), "PROPN", "root", None)
        else:
            self.sn(b, "n", "root", None, det=self.c(["el", "mi", "tu"]))
            b.w[-1][2] = None
        b.raiz = "n"

    def _q_sv(self, b):
        b.add("s", self.c(self.nom), "PROPN", "nsubj", "v")
        lema, prep = self.c(self.vloc)
        b.add("v", self.verbo(lema, "pres"), "VERB", "root", None, lema); self._lugar(b, prep, "v"); b.raiz = "v"


def make(n: int, split: str = "train", seed: int = 0) -> List[List[tuple]]:
    g = Conv(split, seed)
    out = []
    while len(out) < n:
        try:
            s = g.frase()
        except (IndexError, KeyError):
            continue
        if 2 <= len(s) <= 14 and sum(1 for w in s if w[2] == 0) == 1:
            out.append(s)
    return out
