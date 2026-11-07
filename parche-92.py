"""parche-92: EXAMEN DE COMPRENSION del texto + arreglo de "asteroides". Aplica ANTES el parche-91 v2 (cartuchos); este parche no depende de el pero lo complementa.

Tu lectura.txt (16/16 frases, retencion 29/29) es muy buena noticia pero la medida es blanda: "¿Qué sabes de X?" solo comprueba que el dato sale, no que se pueda
USAR. Y se ve que se pierde informacion: "Mercurio es el planeta mas cercano al Sol" -> MERCURIO SER CERCANO (sin "mas" ni "al Sol"); "Venus es el segundo planeta" ->
VENUS SER SEGUNDO; "Jupiter es el planeta mas grande" -> JUPITER SER GRANDE; y "ASTEROID ES ROCA" (el lematizador quita "-es" a "asteroides").
Este parche: (1) "asteroides" -> "asteroide" (las palabras en -oide); (2) data/textos/sistema_solar_examen.tsv: las 16 frases + 25 PREGUNTAS REALES con respuesta esperada
(superlativos, ordinales, "cuantas lunas", "de que estan hechos", sí/no por herencia: "¿Gira la Tierra alrededor del Sol?"), registrado en check.py como examen
INFORMATIVO texto_solar. Su desglose en el informe dice que tipos de pregunta sobre un texto no sabe contestar; el parche-93 arregla esas familias.
Criterio: el test nuevo pasa y nada baja. Uso: python -m scripts.ciclo parche-92.py"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALL_EDITS = [('src/language/extract.py', '            if tree[idx][1] == "NOUN" and f_ != l_ and f_ in (l_ + "s", l_ + "es") and nm_ == f_:\n                return l_\n            return nm_', '            if tree[idx][1] == "NOUN" and f_ != l_ and f_ in (l_ + "s", l_ + "es") and nm_ == f_:\n                return l_ + "e" if (f_ == l_ + "es" and l_.endswith("oid")) else l_      # parche-92: asteroides -> asteroide (no "asteroid")\n            return nm_', 'parche-92: asteroides'), ('scripts/check.py', '("nuevo_ciego_dialogo7", "data/dialogo_ciego_siete.tsv", .0)', '("nuevo_ciego_dialogo7", "data/dialogo_ciego_siete.tsv", .0), ("texto_solar", "data/textos/sistema_solar_examen.tsv", .0)', 'texto_solar')]
NEW_FILES = {'data/textos/sistema_solar_examen.tsv': '# Examen de COMPRENSION del texto del sistema solar (parche-92). Informativo. Las frases son las de data/textos/sistema_solar.txt; las preguntas NO estan en el texto tal cual.\nU: El Sol es una estrella.\t\nU: El Sol está en el centro del Sistema Solar.\t\nU: Los planetas giran alrededor del Sol.\t\nU: Mercurio es el planeta más cercano al Sol.\t\nU: Venus es el segundo planeta.\t\nU: La Tierra es el tercer planeta y tiene una luna.\t\nU: La Luna gira alrededor de la Tierra.\t\nU: Marte es un planeta rojo.\t\nU: Marte tiene dos lunas.\t\nU: Júpiter es el planeta más grande.\t\nU: Júpiter es un gigante gaseoso.\t\nU: Saturno tiene anillos.\t\nU: Urano y Neptuno son planetas helados.\t\nU: Plutón es un planeta enano.\t\nU: Los asteroides son rocas pequeñas.\t\nU: Los cometas están hechos de hielo y polvo.\t\nU: ¿Qué es el Sol?\testrella\nU: ¿Dónde está el Sol?\tcentro\nU: ¿Qué gira alrededor del Sol?\tplanetas\nU: ¿Qué es Mercurio?\tplaneta\nU: ¿Cuál es el planeta más cercano al Sol?\tMercurio\nU: ¿Cuál es el segundo planeta?\tVenus\nU: ¿Cuál es el tercer planeta?\tTierra\nU: ¿Cuántas lunas tiene Marte?\tdos\nU: ¿Qué tiene la Tierra?\tluna\nU: ¿Alrededor de qué gira la Luna?\tTierra\nU: ¿De qué color es Marte?\trojo\nU: ¿Cuál es el planeta más grande?\tJúpiter\nU: ¿Qué es Júpiter?\tgigante\nU: ¿Qué tiene Saturno?\tanillos\nU: ¿Qué planetas son helados?\tUrano\nU: ¿Cómo es Neptuno?\thelado\nU: ¿Qué es Plutón?\tenano\nU: ¿Qué son los asteroides?\trocas\nU: ¿De qué están hechos los cometas?\thielo\nU: ¿Gira la Tierra alrededor del Sol?\tSí\nU: ¿Es la Tierra un planeta?\tSí\nU: ¿Es Plutón un planeta?\tSí\nU: ¿Tiene Marte tres lunas?\tNo\nU: ¿Qué sabes de Saturno?\tanillos\nU: ¿Es Marte un planeta rojo?\tSí\n', 'tests/test_parche92.py': '"""parche-92: el examen de comprension del texto esta bien formado."""\nfrom src.language.ingesta import preparar\n\n\ndef test_examen_solar_bien_formado():\n    frases, _ = preparar(open("data/textos/sistema_solar.txt", encoding="utf-8").read())\n    lines = [l.rstrip("\\n") for l in open("data/textos/sistema_solar_examen.tsv", encoding="utf-8") if l.startswith("U:")]\n    assert [l[3:].split("\\t")[0] for l in lines[:len(frases)]] == frases\n    preguntas = lines[len(frases):]\n    assert len(preguntas) >= 20 and all(l.count("\\t") == 1 and l.split("\\t")[1] for l in preguntas)\n'}

def main(root: Path = ROOT) -> int:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    bk = root / ".parche_backups" / stamp
    texts, changed = {}, set()
    for rel, old, new, marca in ALL_EDITS:                              # comprobar TODO antes de escribir nada
        p = root / rel
        if not p.is_file():
            print(f"FALTA {rel}: no se toca nada."); return 1
        txt = texts[rel] if rel in texts else p.read_text(encoding="utf-8")
        if marca in txt:
            texts[rel] = txt; continue
        if txt.count(old) != 1:
            print(f"ERROR {rel}: un trozo a cambiar aparece {txt.count(old)} veces (debe ser 1): {old[:70]!r}. No se toca nada."); return 1
        texts[rel] = txt.replace(old, new); changed.add(rel)
    plan = [(root / rel, rel, texts[rel]) for rel in sorted(changed)]
    for rel, content in NEW_FILES.items():
        p = root / rel
        if not p.exists() or p.read_text(encoding="utf-8") != content:
            plan.append((p, rel, content))
    for p, rel, txt in plan:
        if p.exists():
            (bk / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, bk / rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
        if rel.endswith(".py"):
            py_compile.compile(str(p), doraise=True)
        print(f"  escrito {rel}")
    print(f"parche-92 instalado. Copias en {bk}" if plan else "parche-92: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

