from flask import Flask

from app.controllers import api_controller, espacio_controller, inicio_controller, reserva_controller, usuario_controller


def registrar_blueprints(app: Flask) -> None:
    for modulo in (inicio_controller, espacio_controller, usuario_controller, reserva_controller, api_controller):
        app.register_blueprint(modulo.bp)
