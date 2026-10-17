import datetime
import os
import socket
import sys
import threading
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "app.log")
PUERTO = int(os.environ.get("PUERTO_RESERVAS", "5050"))
NOMBRE_VENTANA = "Sistema de Reservas de Espacios"
URL = f"http://127.0.0.1:{PUERTO}/"

ICONO = os.path.join(BASE_DIR, "reservas.ico")
APP_ID = "LenguajesProgramacion.ReservasEspacios.1"

os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def _log(mensaje):
    marca = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as archivo:
            archivo.write(f"[{marca}] {mensaje}\n")
    except OSError:
        pass


def _puerto_libre(puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", puerto)) != 0


def _esperar_servidor(timeout=20):
    inicio = time.time()
    while time.time() - inicio < timeout:
        if not _puerto_libre(PUERTO):
            return True
        time.sleep(0.2)
    return False


def _mostrar_error(titulo, mensaje):
    try:
        import tkinter as tk
        from tkinter import messagebox

        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror(titulo, mensaje)
        raiz.destroy()
    except Exception:
        _log(f"{titulo}: {mensaje}")


def _crear_servidor():
    from werkzeug.serving import make_server

    from app import create_app
    from app.models import RepositorioEspacios
    from app.datos_demo import cargar_datos_demo

    aplicacion = create_app()
    with aplicacion.app_context():
        if RepositorioEspacios().contar() == 0:
            _log(f"Base de datos vacía; cargando datos de ejemplo: {cargar_datos_demo()}")
    return make_server("127.0.0.1", PUERTO, aplicacion, threaded=True)


def _aplicar_icono(ventana):
    if sys.platform != "win32":
        return
    try:
        from System import Action
        from System.Drawing import Icon

        formulario = ventana.native
        formulario.Invoke(Action(lambda: setattr(formulario, "Icon", Icon(ICONO))))
    except Exception as error:
        _log(f"No se pudo aplicar el icono a la ventana: {error!r}")


def _ventana_sin_webview(servidor):
    import tkinter as tk

    webbrowser.open(URL)
    raiz = tk.Tk()
    raiz.title(NOMBRE_VENTANA)
    raiz.resizable(False, False)
    tk.Label(raiz, text=f"La aplicación está abierta en el navegador:\n{URL}\n\nCierra esta ventana para detenerla.",
             padx=24, pady=16, justify="center").pack()
    tk.Button(raiz, text="Abrir de nuevo", command=lambda: webbrowser.open(URL), width=16).pack(pady=(0, 6))
    tk.Button(raiz, text="Cerrar aplicación", command=raiz.destroy, width=16).pack(pady=(0, 16))
    raiz.mainloop()
    servidor.shutdown()


def main():
    if not _puerto_libre(PUERTO):
        _mostrar_error(
            "Puerto ocupado",
            f"El puerto {PUERTO} ya está en uso. Es posible que la aplicación ya esté abierta.\n"
            "Ciérrala (o revisa procesos 'pythonw' en el Administrador de tareas) e inténtalo de nuevo.",
        )
        sys.exit(1)

    try:
        servidor = _crear_servidor()
    except Exception as error:
        _log(f"No se pudo iniciar el servidor: {error!r}")
        _mostrar_error("Error al iniciar", f"No se pudo iniciar la aplicación.\nRevisa {LOG_PATH}")
        sys.exit(1)

    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    if not _esperar_servidor():
        _mostrar_error("Error al iniciar", f"El servidor no respondió.\nRevisa {LOG_PATH}")
        os._exit(1)
    _log(f"Servidor iniciado en {URL}")

    try:
        import webview
    except ImportError:
        _log("pywebview no disponible; se abre el navegador")
        _ventana_sin_webview(servidor)
        os._exit(0)

    ventana = webview.create_window(NOMBRE_VENTANA, url=URL, maximized=True, min_size=(1024, 600))
    ventana.events.closing += servidor.shutdown
    ventana.events.shown += lambda: _aplicar_icono(ventana)
    try:
        webview.start(icon=ICONO)
    except Exception as error:
        _log(f"pywebview falló ({error!r}); se abre el navegador")
        _ventana_sin_webview(servidor)
    servidor.shutdown()
    os._exit(0)


if __name__ == "__main__":
    main()
