from datetime import date

from flask import Blueprint, render_template

from app.models import RepositorioEspacios, RepositorioReservas, RepositorioUsuarios

bp = Blueprint("inicio", __name__)


@bp.get("/")
def index():
    hoy = date.today().isoformat()
    reservas = RepositorioReservas()
    return render_template(
        "inicio.html",
        total_espacios=RepositorioEspacios().contar(),
        total_usuarios=RepositorioUsuarios().contar(),
        reservas_hoy=reservas.listar_detalle(fecha=hoy),
        proximas=reservas.listar_detalle(desde=hoy)[:8],
        hoy=hoy,
    )
