from flask import Blueprint, jsonify, request

from app.exceptions import ReservasError
from app.models import RepositorioEspacios, RepositorioReservas, Reserva, ServicioReservas
from app.utils import validadores as v

bp = Blueprint("api", __name__, url_prefix="/api")

CAMPOS = ("usuario_id", "espacio_id", "fecha", "hora_inicio", "hora_fin", "proposito")


@bp.get("/ocupacion")
def ocupacion():
    espacio = RepositorioEspacios().obtener(request.args.get("espacio_id", type=int))
    fecha = v.fecha(request.args.get("fecha"))
    excluir = request.args.get("excluir", type=int)
    reservas = [
        {clave: r[clave] for clave in ("id", "hora_inicio", "hora_fin", "usuario", "proposito")}
        for r in RepositorioReservas().listar_detalle(fecha=fecha, espacio_id=espacio.id)
        if r["id"] != excluir
    ]
    return jsonify(espacio=espacio.a_dict(), fecha=fecha, reservas=reservas)


@bp.post("/reservas/validar")
def validar():
    datos = request.get_json(silent=True) or {}
    try:
        reserva = Reserva(**{campo: datos.get(campo) for campo in CAMPOS}, id=datos.get("id"))
        ServicioReservas().validar(reserva)
    except ReservasError as error:
        return jsonify(valida=False, mensaje=str(error)), error.codigo_http
    return jsonify(valida=True, mensaje="La franja está disponible.")
