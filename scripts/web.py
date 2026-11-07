"""Interfaz web del LCM (parche-106): conversa como con un asistente, explora los conceptos de la memoria y sus dependencias, y carga/descarga cartuchos.

  python -m scripts.web                 abre http://127.0.0.1:8765 en tu navegador
  python -m scripts.web --puerto 9000 --no-abrir

Usa la MISMA memoria que scripts.think (memory/lcm_memory.json), la semilla de fabrica y los cartuchos activos. Solo escucha en tu ordenador (127.0.0.1)."""
import argparse
import os
import sys
import threading
import webbrowser


def cargar_escuela():
    import torch
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    if not os.path.exists("checkpoints/school.pt"):
        print("[!] No hay escuela de español (checkpoints/school.pt). Ejecuta: python -m scripts.train_school")
        return None
    from src.language.school_learn import load_overrides
    from src.language.school_parser import SchoolParser
    from src.language.ud import load_school
    model, scripts = load_school(device=device)
    print(f"[escuela] cargada en {device.upper()}")
    return SchoolParser(model, device, scripts, load_overrides())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8765)
    ap.add_argument("--no-abrir", action="store_true")
    ap.add_argument("--reflexionar", action="store_true", help="repasa los conceptos y recalcula los nexos al arrancar (por defecto solo si no hay ninguna reflexion hecha)")
    a = ap.parse_args(argv)
    from src.web.motor import Motor
    from src.web.servidor import crear_servidor
    parser = cargar_escuela()
    if parser is None:
        return 1
    motor = Motor.crear(parser=parser)
    if a.reflexionar or not os.path.exists(os.path.join("cartuchos", "reflexion.json")):
        r = motor.reflexionar()
        i = r.get("informe") or {}
        print(f"[reflexión] {i.get('conceptos', 0)} conceptos repasados -> {i.get('nexos', 0)} nexos nuevos en {i.get('segundos', 0)} s" if r.get("ok") else f"[reflexión] {r.get('error')}")
    st = motor.estado()
    print(f"[memoria] {st['hechos']} hechos ({st['por_origen']}), {st['entidades']} conceptos, {st['cartuchos_activos']} cartuchos activos, diccionario de {st['diccionario']} conceptos")
    srv = crear_servidor(motor, a.puerto)
    url = f"http://127.0.0.1:{a.puerto}"
    print(f"\n  LCM listo en {url}   (Ctrl+C para salir)\n")
    if not a.no_abrir:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with motor.lock:
            motor.mem.save()
        srv.server_close()
        print("\nMemoria guardada. Hasta pronto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
