import sqlite3

from app.exceptions import ValidacionError
from app.models.base import Entidad, Repositorio
from app.utils import validadores as v


class Espacio(Entidad):
    def __init__(
        self,
        nombre: str,
        capacidad: int,
        ubicacion: str,
        equipamiento: str = "",
        habilitado: bool = True,
        hora_apertura: str = "07:00",
        hora_cierre: str = "21:00",
        id: int | None = None,
    ):
        super().__init__(id)
        self.nombre = nombre
        self.capacidad = capacidad
        self.ubicacion = ubicacion
        self.equipamiento = equipamiento
        self.habilitado = habilitado
        self.hora_apertura = hora_apertura
        self.hora_cierre = hora_cierre
        self.validar()

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor) -> None:
        self._nombre = v.texto(valor, "nombre", maximo=100)

    @property
    def capacidad(self) -> int:
        return self._capacidad

    @capacidad.setter
    def capacidad(self, valor) -> None:
        self._capacidad = v.entero(valor, "capacidad máxima", minimo=1, maximo=5000)

    @property
    def ubicacion(self) -> str:
        return self._ubicacion

    @ubicacion.setter
    def ubicacion(self, valor) -> None:
        self._ubicacion = v.texto(valor, "ubicación física", maximo=150)

    @property
    def equipamiento(self) -> str:
        return self._equipamiento

    @equipamiento.setter
    def equipamiento(self, valor) -> None:
        self._equipamiento = v.texto(valor, "equipamiento", requerido=False, maximo=500)

    @property
    def habilitado(self) -> bool:
        return self._habilitado

    @habilitado.setter
    def habilitado(self, valor) -> None:
        self._habilitado = v.booleano(valor)

    @property
    def hora_apertura(self) -> str:
        return self._hora_apertura

    @hora_apertura.setter
    def hora_apertura(self, valor) -> None:
        self._hora_apertura = v.hora(valor, "hora de apertura")

    @property
    def hora_cierre(self) -> str:
        return self._hora_cierre

    @hora_cierre.setter
    def hora_cierre(self, valor) -> None:
        self._hora_cierre = v.hora(valor, "hora de cierre")

    @property
    def lista_equipamiento(self) -> list[str]:
        return [item.strip() for item in self.equipamiento.split(",") if item.strip()]

    def validar(self) -> None:
        if self.hora_apertura >= self.hora_cierre:
            raise ValidacionError("La hora de apertura debe ser anterior a la hora de cierre.")

    def permite_franja(self, inicio: str, fin: str) -> bool:
        return self.hora_apertura <= inicio < fin <= self.hora_cierre

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "capacidad": self.capacidad,
            "ubicacion": self.ubicacion,
            "equipamiento": self.equipamiento,
            "habilitado": self.habilitado,
            "hora_apertura": self.hora_apertura,
            "hora_cierre": self.hora_cierre,
        }


class RepositorioEspacios(Repositorio[Espacio]):
    tabla = "espacios"
    columnas = ("nombre", "capacidad", "ubicacion", "equipamiento", "habilitado", "hora_apertura", "hora_cierre")
    orden = "nombre COLLATE NOCASE"
    nombre_entidad = "espacio"
    mensajes_integridad = {
        "espacios.nombre": "Ya existe un espacio registrado con ese nombre.",
        "FOREIGN KEY": "No se puede eliminar el espacio porque tiene reservas asociadas. Puede deshabilitarlo.",
    }

    def _a_entidad(self, fila: sqlite3.Row) -> Espacio:
        return Espacio(**dict(fila))

    def listar_habilitados(self) -> list[Espacio]:
        return [espacio for espacio in self.listar() if espacio.habilitado]
