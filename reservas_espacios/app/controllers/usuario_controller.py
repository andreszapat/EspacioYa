from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.exceptions import IntegridadError, ValidacionError
from app.models import RepositorioReservas, RepositorioUsuarios, Usuario

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _desde_formulario(id_: int | None = None) -> Usuario:
    datos = request.form
    return Usuario.crear(
        datos.get("rol"),
        nombre=datos.get("nombre"),
        correo=datos.get("correo"),
        telefono=datos.get("telefono"),
        id=id_,
    )


def _formulario(datos, titulo: str, usuario_id: int | None = None):
    return render_template(
        "usuarios/formulario.html", datos=datos, titulo=titulo, usuario_id=usuario_id, roles=Usuario.roles()
    )


@bp.get("/")
def listar():
    return render_template("usuarios/lista.html", usuarios=RepositorioUsuarios().listar())


@bp.get("/<int:usuario_id>")
def detalle(usuario_id: int):
    usuario = RepositorioUsuarios().obtener(usuario_id)
    reservas = RepositorioReservas().listar_detalle(usuario_id=usuario_id)
    return render_template("usuarios/detalle.html", usuario=usuario, reservas=reservas)


@bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    datos = {"rol": "estudiante"}
    if request.method == "POST":
        datos = request.form
        try:
            usuario = RepositorioUsuarios().crear(_desde_formulario())
            flash(f"Usuario «{usuario.nombre}» registrado como {usuario.etiqueta_rol.lower()}.", "exito")
            return redirect(url_for("usuarios.listar"))
        except (ValidacionError, IntegridadError) as error:
            flash(str(error), "error")
    return _formulario(datos, "Nuevo usuario")


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
def editar(usuario_id: int):
    repositorio = RepositorioUsuarios()
    datos = repositorio.obtener(usuario_id).a_dict()
    if request.method == "POST":
        datos = request.form
        try:
            usuario = repositorio.actualizar(_desde_formulario(usuario_id))
            flash(f"Usuario «{usuario.nombre}» actualizado.", "exito")
            return redirect(url_for("usuarios.listar"))
        except (ValidacionError, IntegridadError) as error:
            flash(str(error), "error")
    return _formulario(datos, "Editar usuario", usuario_id)


@bp.post("/<int:usuario_id>/eliminar")
def eliminar(usuario_id: int):
    try:
        RepositorioUsuarios().eliminar(usuario_id)
        flash("Usuario eliminado.", "exito")
    except IntegridadError as error:
        flash(str(error), "error")
    return redirect(url_for("usuarios.listar"))
