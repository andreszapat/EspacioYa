# Sistema de Reservas de Espacios

Aplicación web en **Python 3 + Flask + SQLite** para gestionar salas, aulas y espacios compartidos: registro de espacios y usuarios, creación de reservas con control de horarios, prevención de reservas duplicadas y un calendario visual de disponibilidad.

Mini-Proyecto I · Lenguajes de Programación · 2026B

## Funcionalidades

| Requisito | Dónde está |
|---|---|
| CRUD de espacios (nombre, capacidad, ubicación, equipamiento, estado, horario) | `app/models/espacio.py`, `app/controllers/espacio_controller.py` |
| CRUD de usuarios (nombre, correo, rol, contacto) | `app/models/usuario.py`, `app/controllers/usuario_controller.py` |
| Registro de reservas (usuario + espacio + fecha + horas + propósito) | `app/models/reserva.py`, `app/controllers/reserva_controller.py` |
| Control de horarios de apertura/cierre por espacio | `Espacio.permite_franja`, `ServicioReservas.validar`, trigger `trg_reservas_horario_*` |
| Evitar reservas duplicadas con notificación del conflicto | `ServicioReservas.validar`, `RepositorioReservas.buscar_conflicto`, trigger `trg_reservas_sin_solape_*` |
| Validación en servidor **y** en la interfaz | `app/models/*` + `app/static/js/reservas.js` (consulta `/api/ocupacion`) |
| Calendario visual por día y franja horaria | `/reservas/calendario` → `ServicioReservas.disponibilidad` |

## Instalación en Windows (app de escritorio)

Doble clic en `instalar.bat`: crea el entorno virtual `.venv`, instala las dependencias, carga datos de ejemplo y crea el acceso directo **Reservas de Espacios** en el Escritorio. La app se abre en una ventana propia (pywebview) en el puerto 5050.

## Instalación manual

```bash
git clone <url-del-repositorio>
cd reservas_espacios
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app run seed               # opcional: carga datos de ejemplo
flask --app run run --debug
```

Abrir http://127.0.0.1:5000

La base de datos se crea automáticamente en `instance/reservas.db` a partir de `database/schema.sql`.

## Pruebas

```bash
python -m unittest discover -s tests -t .
```

27 pruebas cubren entidades, reglas de negocio, triggers de la base de datos, controladores y API.

## Estructura

```
reservas_espacios/
├── run.py                       Punto de entrada
├── config.py                    Configuración (normal y pruebas)
├── database/schema.sql          Tablas, restricciones CHECK/UNIQUE/FK y triggers
├── app/
│   ├── __init__.py              Fábrica de la aplicación y manejo global de errores
│   ├── exceptions.py            Jerarquía de excepciones del dominio
│   ├── datos_demo.py            Datos de ejemplo (comando `flask seed`)
│   ├── models/                  MODELO
│   │   ├── base.py              Entidad y Repositorio genérico (abstractos)
│   │   ├── database.py          Conexión SQLite
│   │   ├── espacio.py           Espacio + RepositorioEspacios
│   │   ├── usuario.py           Usuario → Estudiante, Docente, Administrativo
│   │   ├── reserva.py           Reserva + RepositorioReservas
│   │   └── servicio_reservas.py Reglas de negocio y disponibilidad
│   ├── controllers/             CONTROLADOR (Blueprints de Flask)
│   ├── templates/               VISTA (Jinja2 + HTML)
│   ├── static/                  CSS y JavaScript de validación
│   └── utils/validadores.py     Validación de datos de entrada
├── tests/                       Pruebas automatizadas
├── desktop.py                   Lanzador de escritorio (ventana nativa)
└── instalar.bat                 Instalador para Windows
```

## Reglas de negocio

- Una reserva debe estar dentro del horario de apertura y cierre del espacio.
- Dos reservas del mismo espacio y día no pueden cruzarse (reservas contiguas, como 9–10 y 10–11, sí se permiten).
- No se reserva en espacios deshabilitados ni en fechas/horas pasadas.
- Duración máxima por rol: estudiante 2 h, docente 4 h, administrativo 8 h.
- Un espacio o usuario con reservas no puede eliminarse (se recomienda deshabilitar el espacio).

## Equipo

| Integrante | Módulo principal |
|---|---|
| Integrante 1 | Espacios (modelo, controlador, vistas) |
| Integrante 2 | Usuarios y jerarquía de roles |
| Integrante 3 | Reservas y servicio de validación |
| Integrante 4 | Calendario de disponibilidad, CSS y JavaScript |
| Integrante 5 | Base de datos, pruebas y documentación |
