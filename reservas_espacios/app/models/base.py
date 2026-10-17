import sqlite3
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.exceptions import ConflictoHorarioError, EntidadNoEncontradaError, HorarioNoPermitidoError, IntegridadError
from app.models.database import BaseDatos


class Entidad(ABC):
    def __init__(self, id: int | None = None):
        self.id = id

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor) -> None:
        self._id = int(valor) if valor not in (None, "") else None

    def validar(self) -> None:
        pass

    @abstractmethod
    def a_dict(self) -> dict:
        ...

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.a_dict()}>"


T = TypeVar("T", bound=Entidad)


class Repositorio(ABC, Generic[T]):
    tabla: str = ""
    columnas: tuple[str, ...] = ()
    orden: str = "id"
    nombre_entidad: str = "registro"
    mensajes_integridad: dict[str, str] = {}

    def __init__(self, conexion: sqlite3.Connection | None = None):
        self._conexion = conexion

    @property
    def conexion(self) -> sqlite3.Connection:
        return self._conexion if self._conexion is not None else BaseDatos.conexion()

    @abstractmethod
    def _a_entidad(self, fila: sqlite3.Row) -> T:
        ...

    def _a_parametros(self, entidad: T) -> tuple:
        return tuple(getattr(entidad, columna) for columna in self.columnas)

    def listar(self) -> list[T]:
        filas = self.conexion.execute(f"SELECT * FROM {self.tabla} ORDER BY {self.orden}").fetchall()
        return [self._a_entidad(fila) for fila in filas]

    def obtener(self, id_: int | None) -> T:
        fila = self.conexion.execute(f"SELECT * FROM {self.tabla} WHERE id = ?", (id_,)).fetchone()
        if fila is None:
            raise EntidadNoEncontradaError(f"No existe un {self.nombre_entidad} con id {id_}.")
        return self._a_entidad(fila)

    def contar(self) -> int:
        return self.conexion.execute(f"SELECT COUNT(*) FROM {self.tabla}").fetchone()[0]

    def crear(self, entidad: T) -> T:
        entidad.validar()
        columnas = ", ".join(self.columnas)
        marcadores = ", ".join("?" for _ in self.columnas)
        cursor = self._ejecutar(
            f"INSERT INTO {self.tabla} ({columnas}) VALUES ({marcadores})",
            self._a_parametros(entidad),
        )
        entidad.id = cursor.lastrowid
        return entidad

    def actualizar(self, entidad: T) -> T:
        entidad.validar()
        self.obtener(entidad.id)
        asignaciones = ", ".join(f"{columna} = ?" for columna in self.columnas)
        self._ejecutar(
            f"UPDATE {self.tabla} SET {asignaciones} WHERE id = ?",
            (*self._a_parametros(entidad), entidad.id),
        )
        return entidad

    def eliminar(self, id_: int) -> None:
        self.obtener(id_)
        self._ejecutar(f"DELETE FROM {self.tabla} WHERE id = ?", (id_,))

    def _ejecutar(self, sql: str, parametros: tuple) -> sqlite3.Cursor:
        try:
            cursor = self.conexion.execute(sql, parametros)
            self.conexion.commit()
            return cursor
        except sqlite3.IntegrityError as error:
            self.conexion.rollback()
            raise self._traducir_error(error) from error

    def _traducir_error(self, error: sqlite3.IntegrityError) -> Exception:
        detalle = str(error)
        if "CONFLICTO_HORARIO" in detalle:
            return ConflictoHorarioError("El espacio ya tiene una reserva que se cruza con ese rango de horas.")
        if "FUERA_DE_HORARIO" in detalle:
            return HorarioNoPermitidoError("La reserva está fuera del horario permitido o el espacio está deshabilitado.")
        for clave, mensaje in self.mensajes_integridad.items():
            if clave in detalle:
                return IntegridadError(mensaje)
        return IntegridadError(f"La operación viola una restricción de la base de datos ({detalle}).")
