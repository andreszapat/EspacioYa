from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.exceptions import ReservasError, ValidacionError
from app.models import RepositorioEspacios, RepositorioReservas, RepositorioUsuarios, Reserva, ServicioReservas
from app.utils import validadores as v

bp = Blueprint("reservas", __name__, url_prefix="/reservas")

CAMPOS = ("usuario_id", "espacio_id", "fecha", "hora_inicio", "hora_fin", "proposito")


def _desde_formulario(id_: int | None = None) -> Reserva:
    return Reserva(**{campo: request.form.get(campo) for campo in CAMPOS}, id=id_)


def _formulario(datos, titulo: str, reserva_id: int | None = None):
    return render_template(
        "reservas/formulario.html",
        datos=datos,
        titulo=titulo,
        reserva_id=reserva_id,
        usuarios=RepositorioUsuarios().listar(),
        espacios=RepositorioEspacios().listar_habilitados(),
        hoy=date.today().isoformat(),
    )


def _fecha_consulta() -> str:
    try:
        return v.fecha(request.args.get("fecha") or date.today().isoformat())
    except ValidacionError as error:
        flash(str(error), "error")
        return date.today().isoformat()


@bp.get("/")
def listar():
    fecha = request.args.get("fecha") or None
    espacio_id = request.args.get("espacio_id", type=int)
    solo_proximas = request.args.get("todas") is None and not fecha
    reservas = RepositorioReservas().listar_detalle(
        fecha=fecha, espacio_id=espacio_id, desde=date.today().isoformat() if solo_proximas else None
    )
    return render_template(
        "reservas/lista.html",
        reservas=reservas,
        espacios=RepositorioEspacios().listar(),
        filtros={"fecha": fecha or "", "espacio_id": espacio_id, "todas": not solo_proximas},
        hoy=date.today().isoformat(),
    )


@bp.get("/calendario")
def calendario():
    fecha = _fecha_consulta()
    dia = date.fromisoformat(fecha)
    tabla = ServicioReservas().disponibilidad(fecha)
    return render_template(
        "reservas/calendario.html",
        tabla=tabla,
        dia=dia,
        anterior=(dia - timedelta(days=1)).isoformat(),
        siguiente=(dia + timedelta(days=1)).isoformat(),
        hoy=date.today().isoformat(),
    )


@bp.route("/nueva", methods=["GET", "POST"])
def crear():
    datos = {campo: request.args.get(campo, "") for campo in CAMPOS}
    datos["fecha"] = datos["fecha"] or date.today().isoformat()
    if request.method == "POST":
        datos = request.form
        try:
            reserva = ServicioReservas().registrar(_desde_formulario())
            flash(f"Reserva registrada para el {reserva.fecha} de {reserva.hora_inicio} a {reserva.hora_fin}.", "exito")
            return redirect(url_for("reservas.calendario", fecha=reserva.fecha))
        except ReservasError as error:
            flash(str(error), "error")
    return _formulario(datos, "Nueva reserva")


@bp.route("/<int:reserva_id>/editar", methods=["GET", "POST"])
def editar(reserva_id: int):
    datos = RepositorioReservas().obtener(reserva_id).a_dict()
    if request.method == "POST":
        datos = request.form
        try:
            reserva = ServicioReservas().modificar(_desde_formulario(reserva_id))
            flash("Reserva actualizada.", "exito")
            return redirect(url_for("reservas.calendario", fecha=reserva.fecha))
        except ReservasError as error:
            flash(str(error), "error")
    return _formulario(datos, "Editar reserva", reserva_id)


@bp.post("/<int:reserva_id>/eliminar")
def eliminar(reserva_id: int):
    ServicioReservas().cancelar(reserva_id)
    flash("Reserva cancelada.", "exito")
    return redirect(request.form.get("volver") or url_for("reservas.listar"))
