from flask import Flask, jsonify, render_template, request

from app.controllers import registrar_blueprints
from app.exceptions import ReservasError
from app.models import BaseDatos
from config import Config


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    BaseDatos.inicializar(app.config["DATABASE"])
    app.teardown_appcontext(BaseDatos.cerrar)

    registrar_blueprints(app)
    _registrar_manejadores_error(app)
    _registrar_comandos(app)
    _registrar_filtros(app)
    return app


def _responder_error(mensaje: str, codigo: int):
    if request.path.startswith("/api/"):
        return jsonify(error=mensaje), codigo
    return render_template("error.html", mensaje=mensaje, codigo=codigo), codigo


def _registrar_manejadores_error(app: Flask) -> None:
    @app.errorhandler(ReservasError)
    def error_de_negocio(error: ReservasError):
        return _responder_error(str(error), error.codigo_http)

    @app.errorhandler(404)
    def no_encontrado(_error):
        return _responder_error("La página solicitada no existe.", 404)

    @app.errorhandler(405)
    def metodo_no_permitido(_error):
        return _responder_error("Método HTTP no permitido para esta ruta.", 405)

    @app.errorhandler(500)
    def error_interno(_error):
        return _responder_error("Ocurrió un error inesperado. Intente nuevamente.", 500)


def _registrar_comandos(app: Flask) -> None:
    @app.cli.command("seed")
    def seed():
        from app.datos_demo import cargar_datos_demo

        resumen = cargar_datos_demo()
        print(f"Datos de ejemplo cargados: {resumen}")


def _registrar_filtros(app: Flask) -> None:
    from datetime import date

    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]

    @app.template_filter("fecha_larga")
    def fecha_larga(valor) -> str:
        dia = valor if isinstance(valor, date) else date.fromisoformat(str(valor))
        return f"{dias[dia.weekday()]} {dia.day} de {meses[dia.month - 1]} de {dia.year}"
