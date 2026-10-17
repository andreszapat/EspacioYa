from collections import defaultdict
from datetime import datetime

from app.exceptions import ConflictoHorarioError, HorarioNoPermitidoError, ValidacionError
from app.models.espacio import RepositorioEspacios
from app.models.reserva import RepositorioReservas, Reserva
from app.models.usuario import RepositorioUsuarios
from app.utils import validadores as v


class ServicioReservas:
    def __init__(
        self,
        reservas: RepositorioReservas | None = None,
        espacios: RepositorioEspacios | None = None,
        usuarios: RepositorioUsuarios | None = None,
        reloj=datetime.now,
    ):
        self._reservas = reservas or RepositorioReservas()
        self._espacios = espacios or RepositorioEspacios()
        self._usuarios = usuarios or RepositorioUsuarios()
        self._reloj = reloj

    def registrar(self, reserva: Reserva) -> Reserva:
        self.validar(reserva)
        return self._reservas.crear(reserva)

    def modificar(self, reserva: Reserva) -> Reserva:
        self._reservas.obtener(reserva.id)
        self.validar(reserva)
        return self._reservas.actualizar(reserva)

    def cancelar(self, reserva_id: int) -> None:
        self._reservas.eliminar(reserva_id)

    def validar(self, reserva: Reserva) -> None:
        reserva.validar()
        espacio = self._espacios.obtener(reserva.espacio_id)
        usuario = self._usuarios.obtener(reserva.usuario_id)

        if not espacio.habilitado:
            raise ValidacionError(f"El espacio «{espacio.nombre}» está deshabilitado y no admite reservas.")

        if not espacio.permite_franja(reserva.hora_inicio, reserva.hora_fin):
            raise HorarioNoPermitidoError(
                f"«{espacio.nombre}» solo puede reservarse entre {espacio.hora_apertura} y {espacio.hora_cierre}."
            )

        if not usuario.puede_reservar(reserva.duracion_horas):
            raise ValidacionError(
                f"Un usuario con rol {usuario.etiqueta_rol.lower()} puede reservar máximo "
                f"{usuario.max_horas_reserva:g} horas seguidas (solicitó {reserva.duracion_horas:g} h)."
            )

        if reserva.es_pasada(self._reloj()):
            raise ValidacionError("No se pueden crear ni modificar reservas en fechas u horas que ya pasaron.")

        conflicto = self._reservas.buscar_conflicto(
            reserva.espacio_id, reserva.fecha, reserva.hora_inicio, reserva.hora_fin, reserva.id
        )
        if conflicto:
            raise ConflictoHorarioError(
                f"Conflicto de horario: «{conflicto['espacio']}» ya está reservado el {conflicto['fecha']} "
                f"de {conflicto['hora_inicio']} a {conflicto['hora_fin']} por {conflicto['usuario']} "
                f"({conflicto['proposito']}). Elija otro rango u otro espacio.",
                conflicto,
            )

    def disponibilidad(self, fecha: str, intervalo_min: int = 30) -> dict:
        fecha = v.fecha(fecha)
        espacios = self._espacios.listar_habilitados()
        if not espacios:
            return {"fecha": fecha, "espacios": [], "filas": [], "total_reservas": 0}

        inicio = min(v.a_minutos(e.hora_apertura) for e in espacios)
        fin = max(v.a_minutos(e.hora_cierre) for e in espacios)
        inicio -= inicio % intervalo_min

        reservas = self._reservas.listar_detalle(fecha=fecha)
        por_espacio: dict[int, list[dict]] = defaultdict(list)
        for reserva in reservas:
            por_espacio[reserva["espacio_id"]].append(reserva)

        etiquetadas: set[int] = set()
        filas = []
        for minuto in range(inicio, fin, intervalo_min):
            desde, hasta = v.desde_minutos(minuto), v.desde_minutos(min(minuto + intervalo_min, fin))
            celdas = []
            for espacio in espacios:
                if not espacio.permite_franja(desde, hasta):
                    celdas.append({"estado": "cerrado"})
                    continue
                ocupante = next(
                    (r for r in por_espacio[espacio.id] if r["hora_inicio"] < hasta and desde < r["hora_fin"]),
                    None,
                )
                if ocupante:
                    primera = ocupante["id"] not in etiquetadas
                    etiquetadas.add(ocupante["id"])
                    celdas.append({"estado": "reservado", "reserva": ocupante, "primera": primera})
                else:
                    celdas.append({"estado": "libre", "espacio_id": espacio.id, "desde": desde, "hasta": hasta})
            filas.append({"desde": desde, "hasta": hasta, "celdas": celdas})

        return {"fecha": fecha, "espacios": espacios, "filas": filas, "total_reservas": len(reservas)}
