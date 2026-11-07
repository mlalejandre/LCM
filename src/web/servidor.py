"""Servidor HTTP local de la interfaz web (solo libreria estandar). Solo escucha en 127.0.0.1; las peticiones que cambian algo exigen la cabecera X-LCM-Web (un sitio externo no puede enviarla
sin permiso CORS) y el Host debe ser local (contra DNS-rebinding)."""
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
MAX_BODY = 12_000_000
HOSTS_OK = {"localhost", "127.0.0.1", "[::1]"}


def crear_servidor(motor, puerto=8765, host="127.0.0.1"):
    class H(BaseHTTPRequestHandler):
        server_version = "LCM-Web/1"

        def log_message(self, *a):                                            # silencioso
            pass

        # ---- salida ----
        def _json(self, obj, code=200):
            b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)

        def _bytes(self, data, ctype, nombre=None):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            if nombre:
                self.send_header("Content-Disposition", f'attachment; filename="{nombre}"')
            self.end_headers()
            self.wfile.write(data)

        def _host_ok(self):
            h = (self.headers.get("Host") or "").rsplit(":", 1)[0] if not (self.headers.get("Host") or "").startswith("[") else "[::1]"
            return h in HOSTS_OK

        # ---- GET ----
        def do_GET(self):
            if not self._host_ok():
                return self._json({"error": "host no permitido"}, 403)
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            r = u.path
            try:
                if r in ("/", "/index.html"):
                    with open(os.path.join(STATIC, "index.html"), "rb") as fh:
                        return self._bytes(fh.read(), "text/html; charset=utf-8")
                if r == "/api/estado":
                    return self._json(motor.estado())
                if r == "/api/sugerencias":
                    from src.web.motor import SUGERENCIAS
                    return self._json(SUGERENCIAS)
                if r == "/api/hechos":
                    return self._json(motor.hechos(q.get("q", ""), q.get("origen", ""), q.get("n", 60), q.get("pag", 0)))
                if r == "/api/conceptos":
                    return self._json(motor.conceptos(q.get("q", ""), q.get("tipo", ""), q.get("origen", ""), q.get("n", 80), q.get("pag", 0)))
                if r == "/api/concepto":
                    return self._json(motor.concepto(q.get("k", "")))
                if r == "/api/grafo":
                    return self._json(motor.grafo(q.get("k") or None, q.get("prof", 1)))
                if r == "/api/diccionario":
                    return self._json(motor.diccionario(q.get("q", "")))
                if r == "/api/reflexion":
                    return self._json(motor.reflexion_informe())
                if r == "/api/cartuchos":
                    return self._json(motor.cartuchos())
                if r == "/api/cartucho/ver":
                    return self._json(motor.cartucho_ver(q.get("n", "")))
                if r == "/api/cartucho/descargar":
                    got = motor.cartucho_descargar(q.get("n", ""))
                    if not got:
                        return self._json({"error": "No existe ese cartucho."}, 404)
                    return self._bytes(got[1], "application/json; charset=utf-8", got[0])
                if r == "/api/memoria/exportar":
                    return self._bytes(motor.exportar_memoria(), "application/json; charset=utf-8", "memoria_personal.json")
            except Exception as e:                                            # noqa
                return self._json({"error": f"Error interno ({type(e).__name__})."}, 500)
            return self._json({"error": "no existe"}, 404)

        # ---- POST ----
        def do_POST(self):
            if not self._host_ok():
                return self._json({"error": "host no permitido"}, 403)
            if self.headers.get("X-LCM-Web") != "1" or "application/json" not in (self.headers.get("Content-Type") or ""):
                return self._json({"error": "petición no permitida"}, 403)
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                n = 0
            if n > MAX_BODY:
                return self._json({"error": "Petición demasiado grande."}, 413)
            try:
                d = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
                if not isinstance(d, dict):
                    raise ValueError
            except ValueError:
                return self._json({"error": "JSON no válido."}, 400)
            r = urllib.parse.urlparse(self.path).path
            try:
                if r == "/api/chat":
                    return self._json(motor.chat(d.get("texto", "")))
                if r == "/api/chat/nueva":
                    return self._json(motor.nueva_conversacion())
                if r == "/api/olvidar":
                    return self._json(motor.olvidar(d.get("s", ""), d.get("p", ""), d.get("o", "")))
                if r == "/api/reflexion":
                    return self._json(motor.reflexionar())
                if r == "/api/cartucho/activar":
                    return self._json(motor.cartucho_activar(d.get("n", ""), bool(d.get("activo"))))
                if r == "/api/cartucho/subir":
                    return self._json(motor.cartucho_subir(d.get("nombre", ""), d.get("contenido"), bool(d.get("sobrescribir"))))
                if r == "/api/cartucho/borrar":
                    return self._json(motor.cartucho_borrar(d.get("n", "")))
                if r == "/api/cartucho/desde_memoria":
                    return self._json(motor.cartucho_desde_memoria(d.get("nombre", ""), str(d.get("descripcion", ""))))
                if r == "/api/cartucho/desde_texto":
                    return self._json(motor.cartucho_desde_texto(d.get("nombre", ""), d.get("texto", ""), str(d.get("descripcion", ""))))
            except Exception as e:                                            # noqa
                return self._json({"error": f"Error interno ({type(e).__name__})."}, 500)
            return self._json({"error": "no existe"}, 404)

    srv = ThreadingHTTPServer((host, puerto), H)
    srv.daemon_threads = True
    return srv
