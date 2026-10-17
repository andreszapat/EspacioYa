from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.exceptions import IntegridadError, ValidacionError
from app.models import Espacio, RepositorioEspacios

bp = Blueprint("espacios", __name__, url_prefix="/espacios")

VALORES_INICIALES = {"habilitado": True, "hora_apertura": "07:00", "hora_cierre": "21:00", "capacidad": 20}


def _desde_formulario(id_: int | None = None) -> Espacio:
    datos = request.form
    return Espacio(
        nombre=datos.get("nombre"),
        capacidad=datos.get("capacidad"),
        ubicacion=datos.get("ubicacion"),
        equipamiento=datos.get("equipamiento"),
        habilitado="habilitado" in datos,
        hora_apertura=datos.get("hora_apertura"),
        hora_cierre=datos.get("hora_cierre"),
        id=id_,
    )


@bp.get("/")
def listar():
    return render_template("espacios/lista.html", espacios=RepositorioEspacios().listar())


@bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    datos = VALORES_INICIALES
    if request.method == "POST":
        datos = request.form
        try:
            espacio = RepositorioEspacios().crear(_desde_formulario())
            flash(f"Espacio «{espacio.nombre}» registrado correctamente.", "exito")
            return redirect(url_for("espacios.listar"))
        except (ValidacionError, IntegridadError) as error:
            flash(str(error), "error")
    return render_template("espacios/formulario.html", datos=datos, titulo="Nuevo espacio")


@bp.route("/<int:espacio_id>/editar", methods=["GET", "POST"])
def editar(espacio_id: int):
    repositorio = RepositorioEspacios()
    datos = repositorio.obtener(espacio_id).a_dict()
    if request.method == "POST":
        datos = request.form
        try:
            espacio = repositorio.actualizar(_desde_formulario(espacio_id))
            flash(f"Espacio «{espacio.nombre}» actualizado.", "exito")
            return redirect(url_for("espacios.listar"))
        except (ValidacionError, IntegridadError) as error:
            flash(str(error), "error")
    return render_template("espacios/formulario.html", datos=datos, titulo="Editar espacio", espacio_id=espacio_id)


@bp.post("/<int:espacio_id>/eliminar")
def eliminar(espacio_id: int):
    try:
        RepositorioEspacios().eliminar(espacio_id)
        flash("Espacio eliminado.", "exito")
    except IntegridadError as error:
        flash(str(error), "error")
    return redirect(url_for("espacios.listar"))
