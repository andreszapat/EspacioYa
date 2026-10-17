import re
from datetime import date, datetime

from app.exceptions import ValidacionError

PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PATRON_TELEFONO = re.compile(r"^\+?[\d\s()-]{7,20}$")
VALORES_VERDADEROS = {"1", "true", "on", "si", "sí", "yes"}


def texto(valor, campo: str, requerido: bool = True, maximo: int = 150) -> str:
    limpio = str(valor or "").strip()
    if requerido and not limpio:
        raise ValidacionError(f"El campo «{campo}» es obligatorio.")
    if len(limpio) > maximo:
        raise ValidacionError(f"El campo «{campo}» admite máximo {maximo} caracteres.")
    return limpio


def entero(valor, campo: str, minimo: int | None = None, maximo: int | None = None) -> int:
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        raise ValidacionError(f"El campo «{campo}» debe ser un número entero.") from None
    if minimo is not None and numero < minimo:
        raise ValidacionError(f"El campo «{campo}» debe ser mayor o igual a {minimo}.")
    if maximo is not None and numero > maximo:
        raise ValidacionError(f"El campo «{campo}» debe ser menor o igual a {maximo}.")
    return numero


def hora(valor, campo: str) -> str:
    try:
        return datetime.strptime(str(valor).strip()[:5], "%H:%M").strftime("%H:%M")
    except (TypeError, ValueError):
        raise ValidacionError(f"El campo «{campo}» debe tener el formato HH:MM.") from None


def fecha(valor, campo: str = "fecha") -> str:
    try:
        return date.fromisoformat(str(valor).strip()).isoformat()
    except (TypeError, ValueError):
        raise ValidacionError(f"El campo «{campo}» debe ser una fecha válida (AAAA-MM-DD).") from None


def correo(valor, campo: str = "correo electrónico") -> str:
    limpio = texto(valor, campo, maximo=120).lower()
    if not PATRON_CORREO.match(limpio):
        raise ValidacionError(f"El {campo} «{limpio}» no tiene un formato válido.")
    return limpio


def telefono(valor, campo: str = "teléfono") -> str:
    limpio = texto(valor, campo, requerido=False, maximo=20)
    if limpio and not PATRON_TELEFONO.match(limpio):
        raise ValidacionError(f"El {campo} solo puede contener dígitos, espacios, guiones y el prefijo +.")
    return limpio


def booleano(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, int):
        return valor == 1
    return str(valor or "").strip().lower() in VALORES_VERDADEROS


def a_minutos(valor: str) -> int:
    horas, minutos = valor.split(":")
    return int(horas) * 60 + int(minutos)


def desde_minutos(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"
