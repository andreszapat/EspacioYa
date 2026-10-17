import sqlite3
from abc import abstractmethod

from app.exceptions import ValidacionError
from app.models.base import Entidad, Repositorio
from app.utils import validadores as v


class Usuario(Entidad):
    ROL: str = ""
    _tipos: dict[str, type["Usuario"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.ROL:
            Usuario._tipos[cls.ROL] = cls

    def __init__(self, nombre: str, correo: str, telefono: str = "", id: int | None = None):
        super().__init__(id)
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @classmethod
    def crear(cls, rol: str, **datos) -> "Usuario":
        tipo = cls._tipos.get(str(rol or "").strip().lower())
        if tipo is None:
            raise ValidacionError("Seleccione un rol válido: estudiante, docente o administrativo.")
        return tipo(**datos)

    @classmethod
    def roles(cls) -> list[dict]:
        return [
            {"valor": rol, "etiqueta": tipo.ETIQUETA, "max_horas": tipo.MAX_HORAS}
            for rol, tipo in cls._tipos.items()
        ]

    @property
    def rol(self) -> str:
        return self.ROL

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor) -> None:
        self._nombre = v.texto(valor, "nombre", maximo=100)

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor) -> None:
        self._correo = v.correo(valor)

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor) -> None:
        self._telefono = v.telefono(valor)

    @property
    @abstractmethod
    def etiqueta_rol(self) -> str:
        ...

    @property
    @abstractmethod
    def max_horas_reserva(self) -> float:
        ...

    def puede_reservar(self, horas: float) -> bool:
        return 0 < horas <= self.max_horas_reserva

    def a_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "correo": self.correo,
            "rol": self.rol,
            "etiqueta_rol": self.etiqueta_rol,
            "telefono": self.telefono,
            "max_horas_reserva": self.max_horas_reserva,
        }


class Estudiante(Usuario):
    ROL = "estudiante"
    ETIQUETA = "Estudiante"
    MAX_HORAS = 2

    @property
    def etiqueta_rol(self) -> str:
        return self.ETIQUETA

    @property
    def max_horas_reserva(self) -> float:
        return self.MAX_HORAS


class Docente(Usuario):
    ROL = "docente"
    ETIQUETA = "Docente"
    MAX_HORAS = 4

    @property
    def etiqueta_rol(self) -> str:
        return self.ETIQUETA

    @property
    def max_horas_reserva(self) -> float:
        return self.MAX_HORAS


class Administrativo(Usuario):
    ROL = "administrativo"
    ETIQUETA = "Administrativo"
    MAX_HORAS = 8

    @property
    def etiqueta_rol(self) -> str:
        return self.ETIQUETA

    @property
    def max_horas_reserva(self) -> float:
        return self.MAX_HORAS


class RepositorioUsuarios(Repositorio[Usuario]):
    tabla = "usuarios"
    columnas = ("nombre", "correo", "rol", "telefono")
    orden = "nombre COLLATE NOCASE"
    nombre_entidad = "usuario"
    mensajes_integridad = {
        "usuarios.correo": "Ya existe un usuario registrado con ese correo electrónico.",
        "FOREIGN KEY": "No se puede eliminar el usuario porque tiene reservas asociadas.",
    }

    def _a_entidad(self, fila: sqlite3.Row) -> Usuario:
        datos = dict(fila)
        return Usuario.crear(datos.pop("rol"), **datos)
