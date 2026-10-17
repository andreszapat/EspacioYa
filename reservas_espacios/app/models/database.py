import sqlite3
from pathlib import Path

from flask import current_app, g

RUTA_ESQUEMA = Path(__file__).resolve().parents[2] / "database" / "schema.sql"


class BaseDatos:
    @staticmethod
    def conectar(ruta: str) -> sqlite3.Connection:
        conexion = sqlite3.connect(ruta)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    @classmethod
    def conexion(cls) -> sqlite3.Connection:
        if "db" not in g:
            g.db = cls.conectar(current_app.config["DATABASE"])
        return g.db

    @staticmethod
    def cerrar(_error=None) -> None:
        conexion = g.pop("db", None)
        if conexion is not None:
            conexion.close()

    @classmethod
    def inicializar(cls, ruta: str) -> None:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        conexion = cls.conectar(ruta)
        try:
            conexion.executescript(RUTA_ESQUEMA.read_text(encoding="utf-8"))
            conexion.commit()
        finally:
            conexion.close()
