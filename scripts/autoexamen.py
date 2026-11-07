"""Autoexamen (parche-89): genera cada vez un examen de dialogo NUEVO a partir de plantillas con nombres/cosas/ciudades al azar y VARIAS formas de
preguntar lo mismo, lo pasa por la conversacion real y agrupa los fallos por plantilla. Es el bucle 'generar -> intentar -> agrupar fallos' sin que
tengas que escribir preguntas: los fallos de reports/informe.txt dicen QUE FAMILIA de pregunta no se cubre.
Uso:  python -m scripts.autoexamen [--semilla 101] [--n 10]     (check.py lo ejecuta con semilla fija como examen informativo)"""
import argparse
import random
from collections import defaultdict

FEM = ["Ana", "Marta", "Rosa", "Elena", "Sara", "Clara", "Irene", "Lucia", "Nora", "Julia", "Paula", "Carla"]
MAS = ["Pedro", "Luis", "Juan", "Carlos", "Pablo", "Raul", "Hugo", "Mario", "Tomas", "Diego", "Andres", "Ivan"]
COSAS = ["pan", "leche", "flores", "naranjas", "cafe", "manzanas", "queso", "arroz"]
CIUDADES = ["Madrid", "Sevilla", "Lugo", "Bilbao", "Cuenca", "Valencia", "Cadiz", "Leon", "Burgos", "Granada"]
PROFES = [("profesora", "profesor"), ("medica", "medico"), ("abogada", "abogado"), ("pintora", "pintor"), ("ingeniera", "ingeniero"), ("cantante", "cantante")]


def _blocks(rng, n):
    """Devuelve lista de (tag, [(turno, esperado)])."""
    out = []
    for _ in range(n):
        f = rng.sample(FEM, 3)
        m = rng.sample(MAS, 2)
        c = rng.sample(CIUDADES, 2)
        t = rng.choice(COSAS)
        pf, pm = rng.choice(PROFES)
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        out.append(("compra_que", [(f"{f[0]} compra {t}.", ""), (rng.choice([f"¿Qué compra {f[0]}?", f"¿Qué es lo que compra {f[0]}?", f"Dime qué compra {f[0]}"]), t)]))
        out.append(("compra_quien", [(f"{m[0]} compra {t}.", ""), (rng.choice([f"¿Quién compra {t}?", f"¿Quién es el que compra {t}?"]), m[0])]))
        out.append(("compra_si", [(f"{f[1]} compra {t}.", ""), (rng.choice([f"¿Compra {f[1]} {t}?", f"¿{f[1]} compra {t}?"]), "Sí")]))
        out.append(("vive_donde", [(f"{m[1]} vive en {c[0]}.", ""), (rng.choice([f"¿Dónde vive {m[1]}?", f"¿En qué ciudad vive {m[1]}?", f"¿Sabes dónde vive {m[1]}?"]), c[0])]))
        out.append(("vive_quien", [(f"{f[2]} vive en {c[1]}.", ""), (rng.choice([f"¿Quién vive en {c[1]}?", f"¿Quién es la que vive en {c[1]}?"]), f[2])]))
        out.append(("correccion", [(f"{m[0]} vive en {c[0]}.", ""), (f"No, {m[0]} vive en {c[1]}.", ""), (f"¿Dónde vive {m[0]}?", c[1]), (f"¿Dónde vivía {m[0]}?", c[0])]))
        out.append(("profesion_que", [(f"{f[0]} es {pf}.", ""), (rng.choice([f"¿Qué es {f[0]}?", f"¿A qué se dedica {f[0]}?", f"¿De qué trabaja {f[0]}?"]), pf)]))
        out.append(("profesion_quien", [(f"{m[1]} es {pm}.", ""), (rng.choice([f"¿Quién es {pm}?", f"¿Quién es el {pm}?"]), m[1])]))
        out.append(("padre", [(f"{m[0]} es el padre de {f[1]}.", ""), (rng.choice([f"¿Quién es el padre de {f[1]}?", f"¿Quién es el papá de {f[1]}?"]), m[0])]))
        out.append(("nombre", [(rng.choice([f"Me llamo {m[1]}.", f"Soy {m[1]}."]), ""), (rng.choice(["¿Cómo me llamo?", "¿Sabes cómo me llamo?", "¿Cuál es mi nombre?"]), m[1])]))
        if rng.random() < 0.5:
            q = (f"¿Es {f[0]} más alta que {f[2]}?", "Sí")
        else:
            q = (f"¿Quién es más alta, {f[0]} o {f[2]}?", f[0])
        out.append(("comparar", [(f"{f[0]} es más alta que {f[1]}.", ""), (f"{f[1]} es más alta que {f[2]}.", ""), q]))
        out.append(("aritmetica", [(rng.choice([f"¿Cuánto es {a} por {b}?", f"{a} x {b}", f"¿Cuánto da {a} por {b}?"]), str(a * b))]))
    return out


def generar(n=10, semilla=101):
    """-> (texto del examen en formato de dialogo, {turno: tag})."""
    rng = random.Random(semilla)
    lines, tags = [f"# Autoexamen generado (semilla {semilla}, {n} rondas): NO editar a mano, se regenera."], {}
    for tag, turns in _blocks(rng, n):
        for turn, exp in turns:
            lines.append(f"U: {turn}\t{exp}")
            if exp:
                tags[turn] = tag
        lines.append("")
    return "\n".join(lines) + "\n", tags


def ejecutar(n=10, semilla=101, path="data/autoexamen.tsv"):
    from scripts.eval_dialogo import run as run_dialogo
    text, tags = generar(n, semilla)
    open(path, "w", encoding="utf-8").write(text)
    g, t, bad = run_dialogo(path)
    por = defaultdict(lambda: [0, 0])
    for line in text.splitlines():
        if line.startswith("U:") and "\t" in line:
            turn, _, exp = line[2:].strip().partition("\t")
            if exp.strip():
                por[tags.get(turn.strip(), "?")][1] += 1
    for turn, exp, ans in bad:
        por[tags.get(turn, "?")][0] += 1
    resumen = {k: (v[1] - v[0], v[1]) for k, v in sorted(por.items())}
    return g, t, bad, resumen, tags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semilla", type=int, default=101)
    ap.add_argument("--n", type=int, default=10)
    a = ap.parse_args()
    g, t, bad, resumen, tags = ejecutar(a.n, a.semilla)
    print(f"autoexamen: {g}/{t} = {g / max(t, 1):.1%}")
    for k, (ok, tot) in resumen.items():
        print(f"  {k:16s} {ok}/{tot}")
    for turn, exp, ans in bad[:60]:
        print(f"   FALLO [{tags.get(turn, '?')}] {turn!r} esperado={exp} obtenido={ans[:90]!r}")


if __name__ == "__main__":
    main()
