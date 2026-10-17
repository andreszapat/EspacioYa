import os
from pathlib import Path

DIRECTORIO_BASE = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambie-esta-clave-en-produccion")
    DATABASE = os.environ.get("DATABASE", str(DIRECTORIO_BASE / "instance" / "reservas.db"))
    TESTING = False


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "pruebas"
