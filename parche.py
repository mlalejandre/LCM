"""parche-80: SONDA (sin cambios de codigo). Los 25 examenes cumplen al 100 % (salvo largas_ciegas_27, error del gold), asi que ya no hay fallos que corregir:
se abre un examen CIEGO mas dificil (26 preguntas: coordinacion, plurales, fechas relativas, comparativos encadenados mezclando mas/menos, parentesco
con regla implicita, generalizacion "todos los X son Y", cambio de trabajo, dativos). Informativo (criterio 0 %). Sus fallos son el trabajo del parche-81.
Honestidad: es un examen escrito por nosotros; algunas preguntas pueden pedir cosas que el sistema aun no promete. Cada fallo se clasifica en el parche siguiente
como (a) error del sistema o (b) pregunta fuera de alcance, y solo (a) se arregla.
Uso:  python -m scripts.ciclo parche-80.py
"""
import datetime, py_compile, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CK = "scripts/check.py"
CK_OLD = '("nuevo_ciego_general_13", "data/ciego_general.tsv", .0)]'
CK_NEW = '("nuevo_ciego_general_13", "data/ciego_general.tsv", .0), ("nuevo_ciego_dificil_26", "data/ciego_dificil.tsv", .0)]      # parche-80: informativo'
ALL_EDITS = [(CK, CK_OLD, CK_NEW, "nuevo_ciego_dificil_26")]
NEW_FILES = {"data/ciego_dificil.tsv": '# Examen CIEGO 3 (parche-80): MAS DIFICIL. Coordinacion, plurales, frases largas, fechas relativas, comparativos con "menos", negacion y cambios. Informativo.\nH: Andrea y Bruno tienen una casa en Valencia.\nP: ¿Quién tiene una casa en Valencia?\tAndrea\nP: ¿Tiene Bruno una casa?\tSI\nP: ¿Dónde tienen una casa Andrea y Bruno?\tValencia\n\nH: Gloria lee novelas y escribe poemas.\nP: ¿Qué escribe Gloria?\tpoemas\nP: ¿Qué lee Gloria?\tnovelas\nP: ¿Escribe Gloria novelas?\tNO\n\nH: Fernando no vive en Madrid sino en Toledo.\nP: ¿Vive Fernando en Madrid?\tNO\nP: ¿Dónde vive Fernando?\tToledo\n\nHOY: 2026-11-07\nH: Ana compró un coche ayer.\nP: ¿Cuándo compró Ana un coche?\t6 de noviembre de 2026\nP: ¿Compró Ana un coche?\tSI\n\nH: Hugo es más viejo que Pedro.\nH: Pedro es menos viejo que Hugo.\nH: Iván es más viejo que Hugo.\nP: ¿Es Iván más viejo que Pedro?\tSI\nP: ¿Es Pedro más viejo que Iván?\tNO\nP: ¿Quién es más viejo que Hugo?\tIván\n\nH: Claudia es la madre de Diego.\nH: Diego es el padre de Estela.\nP: ¿Quién es la madre de Diego?\tClaudia\nP: ¿Es Claudia la abuela de Estela?\tSI\nP: ¿Es Estela la nieta de Claudia?\tSI\n\nH: Todos los gatos son animales.\nH: Félix es un gato.\nP: ¿Es Félix un animal?\tSI\nP: ¿Es un animal Félix?\tSI\n\nH: Mónica está cansada.\nH: Mónica estaba contenta antes.\nP: ¿Está cansada Mónica?\tSI\nP: ¿Cómo está Mónica?\tcansada\n\nH: Rubén regaló un libro a Silvia.\nP: ¿Quién regaló un libro a Silvia?\tRubén\nP: ¿A quién regaló Rubén un libro?\tSilvia\nP: ¿Qué regaló Rubén a Silvia?\tlibro\n\nH: Marina trabajó en Sevilla y ahora trabaja en Bilbao.\nP: ¿Dónde trabaja Marina?\tBilbao\nP: ¿Dónde trabajaba Marina?\tSevilla\n\nH: Los lunes Nico va al gimnasio.\nP: ¿Quién va al gimnasio?\tNico\n'}


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
    print(f"parche-80 instalado. Copias en {bk}" if plan else "parche-80: nada que hacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())