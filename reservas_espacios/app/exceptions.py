class ReservasError(Exception):
    codigo_http = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje

    def __str__(self) -> str:
        return self.mensaje


class ValidacionError(ReservasError):
    codigo_http = 400


class HorarioNoPermitidoError(ValidacionError):
    codigo_http = 422


class ConflictoHorarioError(ReservasError):
    codigo_http = 409

    def __init__(self, mensaje: str, conflicto: dict | None = None):
        super().__init__(mensaje)
        self.conflicto = conflicto


class EntidadNoEncontradaError(ReservasError):
    codigo_http = 404


class IntegridadError(ReservasError):
    codigo_http = 409
