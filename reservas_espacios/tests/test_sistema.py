import os
import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta

from app import create_app
from app.exceptions import (
    ConflictoHorarioError,
    HorarioNoPermitidoError,
    IntegridadError,
    ValidacionError,
)
from app.models import (
    Docente,
    Espacio,
    Estudiante,
    RepositorioEspacios,
    RepositorioReservas,
    RepositorioUsuarios,
    Reserva,
    ServicioReservas,
    Usuario,
)
from config import TestConfig

MANANA = (date.today() + timedelta(days=1)).isoformat()


class BasePrueba(unittest.TestCase):
    def setUp(self):
        descriptor, self.ruta = tempfile.mkstemp(suffix=".db")
        os.close(descriptor)
        configuracion = type("Config", (TestConfig,), {"DATABASE": self.ruta})
        self.app = create_app(configuracion)
        self.cliente = self.app.test_client()
        self.contexto = self.app.app_context()
        self.contexto.push()
        self.espacio = RepositorioEspacios().crear(
            Espacio("Sala A", 10, "Bloque 1", "Tablero", True, "08:00", "18:00")
        )
        self.estudiante = RepositorioUsuarios().crear(Usuario.crear("estudiante", nombre="Ana", correo="ana@u.edu"))
        self.docente = RepositorioUsuarios().crear(Usuario.crear("docente", nombre="Luis", correo="luis@u.edu"))
        self.servicio = ServicioReservas()

    def tearDown(self):
        self.contexto.pop()
        os.remove(self.ruta)

    def reserva(self, inicio="09:00", fin="10:00", usuario=None, fecha=MANANA):
        return Reserva((usuario or self.estudiante).id, self.espacio.id, fecha, inicio, fin, "Estudio")


class PruebasEntidades(BasePrueba):
    def test_espacio_rechaza_capacidad_invalida(self):
        with self.assertRaises(ValidacionError):
            Espacio("Sala", 0, "Bloque")

    def test_espacio_rechaza_horario_invertido(self):
        with self.assertRaises(ValidacionError):
            Espacio("Sala", 5, "Bloque", hora_apertura="18:00", hora_cierre="08:00")

    def test_usuario_correo_invalido(self):
        with self.assertRaises(ValidacionError):
            Usuario.crear("docente", nombre="X", correo="no-es-correo")

    def test_rol_invalido(self):
        with self.assertRaises(ValidacionError):
            Usuario.crear("invitado", nombre="X", correo="x@u.edu")

    def test_polimorfismo_de_roles(self):
        self.assertIsInstance(self.estudiante, Estudiante)
        self.assertIsInstance(self.docente, Docente)
        self.assertLess(self.estudiante.max_horas_reserva, self.docente.max_horas_reserva)

    def test_usuario_es_abstracto(self):
        with self.assertRaises(TypeError):
            Usuario(nombre="X", correo="x@u.edu")

    def test_reserva_fin_antes_de_inicio(self):
        with self.assertRaises(ValidacionError):
            self.reserva("10:00", "09:00")

    def test_duracion(self):
        self.assertEqual(self.reserva("09:00", "10:30").duracion_horas, 1.5)


class PruebasServicio(BasePrueba):
    def test_registro_valido(self):
        reserva = self.servicio.registrar(self.reserva())
        self.assertIsNotNone(reserva.id)

    def test_conflicto_mismo_rango(self):
        self.servicio.registrar(self.reserva("09:00", "10:00"))
        with self.assertRaises(ConflictoHorarioError) as contexto:
            self.servicio.registrar(self.reserva("09:30", "10:30", self.docente))
        self.assertIn("Ana", str(contexto.exception))

    def test_reservas_contiguas_permitidas(self):
        self.servicio.registrar(self.reserva("09:00", "10:00"))
        self.servicio.registrar(self.reserva("10:00", "11:00", self.docente))
        self.assertEqual(RepositorioReservas().contar(), 2)

    def test_fuera_de_horario(self):
        with self.assertRaises(HorarioNoPermitidoError):
            self.servicio.registrar(self.reserva("07:00", "08:30"))

    def test_limite_por_rol(self):
        with self.assertRaises(ValidacionError):
            self.servicio.registrar(self.reserva("09:00", "12:00"))
        self.servicio.registrar(self.reserva("09:00", "12:00", self.docente))

    def test_espacio_deshabilitado(self):
        self.espacio.habilitado = False
        RepositorioEspacios().actualizar(self.espacio)
        with self.assertRaises(ValidacionError):
            self.servicio.registrar(self.reserva())

    def test_fecha_pasada(self):
        ayer = (date.today() - timedelta(days=1)).isoformat()
        with self.assertRaises(ValidacionError):
            self.servicio.registrar(self.reserva(fecha=ayer))

    def test_modificar_sin_chocar_consigo_misma(self):
        reserva = self.servicio.registrar(self.reserva("09:00", "10:00"))
        reserva.hora_fin = "10:30"
        self.servicio.modificar(reserva)
        self.assertEqual(RepositorioReservas().obtener(reserva.id).hora_fin, "10:30")

    def test_disponibilidad(self):
        self.servicio.registrar(self.reserva("09:00", "10:00"))
        tabla = self.servicio.disponibilidad(MANANA)
        estados = {fila["desde"]: fila["celdas"][0]["estado"] for fila in tabla["filas"]}
        self.assertEqual(estados["09:00"], "reservado")
        self.assertEqual(estados["09:30"], "reservado")
        self.assertEqual(estados["10:00"], "libre")


class PruebasBaseDeDatos(BasePrueba):
    def test_trigger_impide_solape_directo(self):
        self.servicio.registrar(self.reserva("09:00", "10:00"))
        conexion = sqlite3.connect(self.ruta)
        with self.assertRaises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO reservas (usuario_id, espacio_id, fecha, hora_inicio, hora_fin, proposito) "
                "VALUES (?, ?, ?, '09:15', '09:45', 'x')",
                (self.docente.id, self.espacio.id, MANANA),
            )
        conexion.close()

    def test_repositorio_traduce_conflicto(self):
        RepositorioReservas().crear(self.reserva("09:00", "10:00"))
        with self.assertRaises(ConflictoHorarioError):
            RepositorioReservas().crear(self.reserva("09:00", "10:00", self.docente))

    def test_correo_unico(self):
        with self.assertRaises(IntegridadError):
            RepositorioUsuarios().crear(Usuario.crear("docente", nombre="Otra", correo="ana@u.edu"))

    def test_no_elimina_espacio_con_reservas(self):
        self.servicio.registrar(self.reserva())
        with self.assertRaises(IntegridadError):
            RepositorioEspacios().eliminar(self.espacio.id)


class PruebasWeb(BasePrueba):
    def test_paginas_principales(self):
        for ruta in ("/", "/espacios/", "/usuarios/", "/reservas/", "/reservas/calendario", "/reservas/nueva",
                     "/espacios/nuevo", "/usuarios/nuevo", f"/usuarios/{self.estudiante.id}"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.cliente.get(ruta).status_code, 200)

    def test_crud_espacio(self):
        respuesta = self.cliente.post("/espacios/nuevo", data={
            "nombre": "Aula 1", "capacidad": "30", "ubicacion": "B2", "equipamiento": "",
            "habilitado": "on", "hora_apertura": "07:00", "hora_cierre": "20:00",
        })
        self.assertEqual(respuesta.status_code, 302)
        espacio = next(e for e in RepositorioEspacios().listar() if e.nombre == "Aula 1")
        self.cliente.post(f"/espacios/{espacio.id}/editar", data={
            "nombre": "Aula 1B", "capacidad": "35", "ubicacion": "B2",
            "hora_apertura": "07:00", "hora_cierre": "20:00",
        })
        actualizado = RepositorioEspacios().obtener(espacio.id)
        self.assertEqual(actualizado.nombre, "Aula 1B")
        self.assertFalse(actualizado.habilitado)
        self.cliente.post(f"/espacios/{espacio.id}/eliminar")
        self.assertEqual(self.cliente.get(f"/espacios/{espacio.id}/editar").status_code, 404)

    def test_formulario_muestra_conflicto(self):
        self.servicio.registrar(self.reserva("09:00", "10:00"))
        respuesta = self.cliente.post("/reservas/nueva", data={
            "usuario_id": self.docente.id, "espacio_id": self.espacio.id, "fecha": MANANA,
            "hora_inicio": "09:30", "hora_fin": "11:00", "proposito": "Clase",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Conflicto de horario", respuesta.get_data(as_text=True))

    def test_api_ocupacion(self):
        reserva = self.servicio.registrar(self.reserva())
        datos = self.cliente.get(f"/api/ocupacion?espacio_id={self.espacio.id}&fecha={MANANA}").get_json()
        self.assertEqual(datos["reservas"][0]["id"], reserva.id)
        excluida = self.cliente.get(
            f"/api/ocupacion?espacio_id={self.espacio.id}&fecha={MANANA}&excluir={reserva.id}"
        ).get_json()
        self.assertEqual(excluida["reservas"], [])

    def test_api_validar(self):
        self.servicio.registrar(self.reserva())
        respuesta = self.cliente.post("/api/reservas/validar", json={
            "usuario_id": self.docente.id, "espacio_id": self.espacio.id, "fecha": MANANA,
            "hora_inicio": "09:00", "hora_fin": "10:00", "proposito": "x",
        })
        self.assertEqual(respuesta.status_code, 409)
        self.assertFalse(respuesta.get_json()["valida"])

    def test_api_espacio_inexistente(self):
        respuesta = self.cliente.get(f"/api/ocupacion?espacio_id=999&fecha={MANANA}")
        self.assertEqual(respuesta.status_code, 404)
        self.assertIn("error", respuesta.get_json())


if __name__ == "__main__":
    unittest.main()
