from datetime import date, timedelta

from app.exceptions import ReservasError
from app.models import Espacio, RepositorioEspacios, RepositorioUsuarios, Reserva, ServicioReservas, Usuario

ESPACIOS = [
    dict(nombre="Sala de Juntas A", capacidad=12, ubicacion="Bloque 1, piso 2", equipamiento="Televisor, videoconferencia, tablero"),
    dict(nombre="Aula 301", capacidad=40, ubicacion="Bloque 3, piso 3", equipamiento="Video beam, sonido, aire acondicionado"),
    dict(nombre="Laboratorio de Cómputo 2", capacidad=30, ubicacion="Bloque 5, piso 1", equipamiento="30 computadores, video beam", hora_apertura="08:00", hora_cierre="18:00"),
    dict(nombre="Auditorio Principal", capacidad=200, ubicacion="Edificio central", equipamiento="Sonido, micrófonos, proyector", hora_apertura="08:00", hora_cierre="20:00"),
    dict(nombre="Sala de Estudio 4", capacidad=6, ubicacion="Biblioteca, piso 2", equipamiento="Tablero", habilitado=False),
]

USUARIOS = [
    ("estudiante", dict(nombre="Laura Gómez", correo="laura.gomez@universidad.edu.co", telefono="3001234567")),
    ("estudiante", dict(nombre="Andrés Rojas", correo="andres.rojas@universidad.edu.co", telefono="3109876543")),
    ("docente", dict(nombre="Camilo Charry", correo="camilo.charry@universidad.edu.co", telefono="3154567890")),
    ("docente", dict(nombre="María Fernanda López", correo="mf.lopez@universidad.edu.co")),
    ("administrativo", dict(nombre="Jorge Martínez", correo="jorge.martinez@universidad.edu.co", telefono="6012345678")),
]


def cargar_datos_demo() -> dict:
    repo_espacios, repo_usuarios = RepositorioEspacios(), RepositorioUsuarios()
    if repo_espacios.contar() or repo_usuarios.contar():
        return {"mensaje": "la base de datos ya tenía información; no se cargó nada"}

    espacios = [repo_espacios.crear(Espacio(**datos)) for datos in ESPACIOS]
    usuarios = [repo_usuarios.crear(Usuario.crear(rol, **datos)) for rol, datos in USUARIOS]

    manana = date.today() + timedelta(days=1)
    pasado = date.today() + timedelta(days=2)
    planes = [
        (usuarios[2], espacios[1], manana, "08:00", "10:00", "Clase de Lenguajes de Programación"),
        (usuarios[0], espacios[0], manana, "10:00", "12:00", "Reunión del equipo del mini-proyecto"),
        (usuarios[3], espacios[2], manana, "14:00", "17:00", "Taller de Flask y SQLite"),
        (usuarios[4], espacios[3], manana, "09:00", "13:00", "Inducción de nuevos estudiantes"),
        (usuarios[1], espacios[0], pasado, "15:00", "16:30", "Asesoría de proyecto"),
        (usuarios[2], espacios[1], pasado, "07:00", "09:00", "Parcial de Programación"),
    ]
    servicio, creadas = ServicioReservas(), 0
    for usuario, espacio, dia, inicio, fin, motivo in planes:
        try:
            servicio.registrar(Reserva(usuario.id, espacio.id, dia.isoformat(), inicio, fin, motivo))
            creadas += 1
        except ReservasError:
            continue
    return {"espacios": len(espacios), "usuarios": len(usuarios), "reservas": creadas}
