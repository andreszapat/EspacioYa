import sqlite3
from datetime import datetime

from app.exceptions import ValidacionError
from app.models.base import Entidad, Repositorio
from app.utils import validadores as v

CONSULTA_DETALLE = """
    SELECT r.id, r.usuario_id, r.espacio_id, r.fecha, r.hora_inicio, r.hora_fin, r.proposito,
           u.nombre AS usuario, u.rol AS rol, e.nombre AS espacio, e.ubicacion AS ubicacion
    FROM reservas r
    JOIN usuarios u ON u.id = r.usuario_id
    JOIN espacios e ON e.id = r.espacio_id
"""


class Reserva(Entidad):
    def __init__(
        self,
        usuario_id: int,
        espacio_id: int,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
        proposito: str,
        id: int | None = None,
        **_extra,
    ):
        super().__init__(id)
        self.usuario_id = usuario_id
        self.espacio_id = espacio_id
        self.fecha = fecha
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.proposito = proposito
        self.validar()

    @property
    def usuario_id(self) -> int:
        return self._usuario_id

    @usuario_id.setter
    def usuario_id(self, valor) -> None:
        if valor in (None, ""):
            raise ValidacionError("Debe seleccionar el usuario que realiza la reserva.")
        self._usuario_id = v.entero(valor, "usuario", minimo=1)

    @property
    def espacio_id(self) -> int:
        return self._espacio_id

    @espacio_id.setter
    def espacio_id(self, valor) -> None:
        if valor in (None, ""):
            raise ValidacionError("Debe seleccionar el espacio a reservar.")
        self._espacio_id = v.entero(valor, "espacio", minimo=1)

    @property
    def fecha(self) -> str:
        return self._fecha

    @fecha.setter
    def fecha(self, valor) -> None:
        self._fecha = v.fecha(valor)

    @property
    def hora_inicio(self) -> str:
        return self._hora_inicio

    @hora_inicio.setter
    def hora_inicio(self, valor) -> None:
        self._hora_inicio = v.hora(valor, "hora de inicio")

    @property
    def hora_fin(self) -> str:
        return self._hora_fin

    @hora_fin.setter
    def hora_fin(self, valor) -> None:
        self._hora_fin = v.hora(valor, "hora de fin")

    @property
    def proposito(self) -> str:
        return self._proposito

    @proposito.setter
    def proposito(self, valor) -> None:
        self._proposito = v.texto(valor, "propósito o motivo", maximo=300)

    @property
    def duracion_horas(self) -> float:
        return (v.a_minutos(self.hora_fin) - v.a_minutos(self.hora_inicio)) / 60

    @property
    def inicio(self) -> datetime:
        return datetime.fromisoformat(f"{self.fecha}T{self.hora_inicio}")

    def es_pasada(self, ahora: datetime | None = None) -> bool:
        return self.inicio < (ahora or datetime.now())

    def se_solapa_con(self, inicio: str, fin: str) -> bool:
        return self.hora_inicio < fin and inicio < self.hora_fin

    def validar(self) -> None:
        if self.hora_inicio >= self.hora_fin:
            raise ValidacionError("La hora de fin debe ser posterior a la hora de inicio.")

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "espacio_id": self.espacio_id,
            "fecha": self.fecha,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "proposito": self.proposito,
        }


class RepositorioReservas(Repositorio[Reserva]):
    tabla = "reservas"
    columnas = ("usuario_id", "espacio_id", "fecha", "hora_inicio", "hora_fin", "proposito")
    orden = "fecha, hora_inicio"
    nombre_entidad = "reserva"
    mensajes_integridad = {
        "FOREIGN KEY": "El usuario o el espacio indicado no existe.",
    }

    def _a_entidad(self, fila: sqlite3.Row) -> Reserva:
        return Reserva(**dict(fila))

    def listar_detalle(
        self,
        fecha: str | None = None,
        espacio_id: int | None = None,
        usuario_id: int | None = None,
        desde: str | None = None,
    ) -> list[dict]:
        condiciones, parametros = [], []
        if fecha:
            condiciones.append("r.fecha = ?")
            parametros.append(fecha)
        if desde:
            condiciones.append("r.fecha >= ?")
            parametros.append(desde)
        if espacio_id:
            condiciones.append("r.espacio_id = ?")
            parametros.append(espacio_id)
        if usuario_id:
            condiciones.append("r.usuario_id = ?")
            parametros.append(usuario_id)
        donde = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
        filas = self.conexion.execute(
            f"{CONSULTA_DETALLE} {donde} ORDER BY r.fecha, r.hora_inicio, e.nombre", parametros
        ).fetchall()
        return [dict(fila) for fila in filas]

    def buscar_conflicto(
        self, espacio_id: int, fecha: str, inicio: str, fin: str, excluir_id: int | None = None
    ) -> dict | None:
        fila = self.conexion.execute(
            f"""{CONSULTA_DETALLE}
            WHERE r.espacio_id = ? AND r.fecha = ? AND r.hora_inicio < ? AND ? < r.hora_fin AND r.id IS NOT ?
            ORDER BY r.hora_inicio LIMIT 1""",
            (espacio_id, fecha, fin, inicio, excluir_id),
        ).fetchone()
        return dict(fila) if fila else None
