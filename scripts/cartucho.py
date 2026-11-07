"""Gestion de cartuchos de conocimiento (parche-91).
  python -m scripts.cartucho listar
  python -m scripts.cartucho insertar NOMBRE      (activa un cartucho que ya existe)
  python -m scripts.cartucho retirar NOMBRE       (lo desactiva: olvida SOLO lo suyo; los demas cartuchos y la fabrica siguen)
  python -m scripts.cartucho borrar NOMBRE        (lo retira Y borra su fichero)
Los cambios se notan al arrancar scripts.think (la memoria se recompone al arrancar)."""
import sys

from src.memory import cartuchos


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("listar", "insertar", "retirar", "borrar") or (argv[0] != "listar" and len(argv) < 2):
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "listar":
        filas = cartuchos.listar()
        if not filas:
            print("No hay cartuchos. Crea uno con: python -m scripts.leer_texto TEXTO.txt")
        for nombre, act, n, fuente in filas:
            print(f"  [{'INSERTADO' if act else 'retirado '}] {nombre:24s} {n:4d} hechos   (de {fuente})")
        print("  [fabrica] semilla (siempre presente)")
        return 0
    nombre = argv[1]
    ok = {"insertar": cartuchos.insertar, "retirar": cartuchos.retirar, "borrar": cartuchos.borrar}[cmd](nombre)
    print(("Hecho: " if ok else "Nada que hacer: ") + f"{cmd} {nombre}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
