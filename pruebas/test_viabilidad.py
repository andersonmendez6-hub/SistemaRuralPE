"""
Pruebas automatizadas del prototipo (biblioteca estándar: unittest).

Se usa unittest y no pytest porque el documento oficial de la Evaluación
Final solo exige "al menos 3 pruebas automatizadas", sin nombrar ninguna
herramienta en particular. unittest viene incluido con Python, así que
estas pruebas corren en cualquier computadora sin necesitar internet para
instalar nada — coherente con la restricción de conectividad del proyecto.

Ejecución desde la raíz del proyecto:
    python -m unittest discover -s pruebas -v
"""

import os
import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controlador import ControladorPuestoSalud, DespachadorEventos
from src.dominio import (Cita, ControlCRED, ControlGestante, ControlVacunacion,
                         Establecimiento, FabricaRegistroClinico, Paciente,
                         PersonalSalud)
from src.persistencia import RepositorioLocal
from src.reportes import (buscar_paciente_por_id, contar_por_tipo,
                          filtrar_por_periodo, total_atenciones)
from src.seguridad import enmascarar_dni, seudonimizar_dni, verificar_dni

SAL = "sal_de_prueba"


class PruebaSeguridadDatosPersonales(unittest.TestCase):
    """Verifica el tratamiento del DNI (Ley N.° 29733)."""

    def test_seudonimo_no_contiene_el_dni(self):
        seudonimo = seudonimizar_dni("45678912", SAL)
        self.assertNotIn("45678912", seudonimo)
        self.assertEqual(len(seudonimo), 16)

    def test_seudonimo_es_determinista_y_verificable(self):
        seudonimo = seudonimizar_dni("45678912", SAL)
        self.assertTrue(verificar_dni("45678912", SAL, seudonimo))
        self.assertFalse(verificar_dni("45678913", SAL, seudonimo))

    def test_dni_invalido_lanza_excepcion(self):
        with self.assertRaises(ValueError):
            seudonimizar_dni("123", SAL)

    def test_enmascarado_solo_muestra_ultimos_tres_digitos(self):
        self.assertEqual(enmascarar_dni("45678912"), "*****912")


class PruebaPipelineFuncional(unittest.TestCase):
    """Verifica que las funciones de reporte sean puras y correctas."""

    def setUp(self):
        hoy = date.today()
        self.registros = [
            ControlVacunacion("id1", hoy, "Obstetra", "BCG", 1),
            ControlCRED("id2", hoy - timedelta(days=10), "Auxiliar", 9.5, 75.0),
            ControlGestante("id3", hoy - timedelta(days=400), "Obstetra", 20, 3),
        ]

    def test_conteo_por_tipo_usa_polimorfismo(self):
        conteo = contar_por_tipo(self.registros)
        self.assertEqual(conteo, {"Vacunación": 1, "CRED": 1, "Gestante": 1})

    def test_filtro_por_periodo_excluye_fuera_de_rango(self):
        hasta = date.today()
        desde = hasta - timedelta(days=364)
        del_periodo = filtrar_por_periodo(self.registros, desde, hasta)
        self.assertEqual(total_atenciones(del_periodo), 2)

    def test_funciones_no_modifican_la_coleccion_original(self):
        copia = list(self.registros)
        contar_por_tipo(self.registros)
        filtrar_por_periodo(self.registros, date(2000, 1, 1), date.today())
        self.assertEqual(self.registros, copia)


class PruebaReglasDeNegocio(unittest.TestCase):
    """Verifica el encapsulamiento y la validación en el dominio."""

    def test_estado_de_cita_invalido_lanza_excepcion(self):
        cita = Cita("id1", date.today(), "Control CRED")
        with self.assertRaises(ValueError):
            cita.estado = "EN_PROCESO"

    def test_estado_de_cita_valido_se_actualiza(self):
        cita = Cita("id1", date.today(), "Control CRED")
        cita.estado = "ATENDIDA"
        self.assertEqual(cita.estado, "ATENDIDA")


class PruebaFabricaRegistroClinico(unittest.TestCase):
    """Verifica el patrón de diseño Factory Method."""

    def setUp(self):
        self.hoy = date.today()

    def test_fabrica_crea_vacunacion_correctamente(self):
        registro = FabricaRegistroClinico.crear(
            "vacunacion", "id1", self.hoy, "Obstetra", vacuna="BCG", dosis=1)
        self.assertIsInstance(registro, ControlVacunacion)
        self.assertEqual(registro.tipo, "Vacunación")

    def test_fabrica_crea_cred_correctamente(self):
        registro = FabricaRegistroClinico.crear(
            "cred", "id1", self.hoy, "Auxiliar", peso_kg=9.5, talla_cm=75.0)
        self.assertIsInstance(registro, ControlCRED)

    def test_fabrica_crea_gestante_correctamente(self):
        registro = FabricaRegistroClinico.crear(
            "gestante", "id1", self.hoy, "Obstetra",
            semanas_gestacion=20, numero_control=3)
        self.assertIsInstance(registro, ControlGestante)

    def test_fabrica_rechaza_tipo_desconocido(self):
        with self.assertRaises(ValueError):
            FabricaRegistroClinico.crear("tipo_inventado", "id1", self.hoy, "Obstetra")


class PruebaEstablecimiento(unittest.TestCase):
    """Verifica la agregación (pacientes/personal) y composición (citas)."""

    def test_agrega_paciente_y_personal(self):
        establecimiento = Establecimiento("Nuevo Amanecer")
        paciente = Paciente("Rosa", "Vásquez", "45678912", SAL,
                            date(1990, 1, 1), "F", "Chagual")
        trabajador = PersonalSalud("Ana", "Ruiz", "11223344", SAL, "Obstetra")
        establecimiento.agregar_paciente(paciente)
        establecimiento.agregar_personal(trabajador)
        self.assertEqual(len(establecimiento.pacientes), 1)
        self.assertEqual(len(establecimiento.personal), 1)

    def test_programa_cita(self):
        establecimiento = Establecimiento("Nuevo Amanecer")
        cita = Cita("id1", date.today(), "Control CRED")
        establecimiento.programar_cita(cita)
        self.assertEqual(len(establecimiento.citas), 1)


class PruebaBusquedaPaciente(unittest.TestCase):
    """Casos mínimos exigidos por la EF: búsqueda con y sin resultado."""

    def setUp(self):
        self.paciente = Paciente("Rosa", "Vásquez", "45678912", SAL,
                                 date(1990, 1, 1), "F", "Chagual")
        self.pacientes = [self.paciente]

    def test_busqueda_con_resultado(self):
        encontrado = buscar_paciente_por_id(
            self.pacientes, self.paciente.dni_seudonimo)
        self.assertIsNotNone(encontrado)
        self.assertEqual(encontrado.dni_seudonimo, self.paciente.dni_seudonimo)

    def test_busqueda_sin_coincidencias(self):
        resultado = buscar_paciente_por_id(self.pacientes, "id_que_no_existe")
        self.assertIsNone(resultado)


class PruebaPersistenciaCifrada(unittest.TestCase):
    """
    Verifica el Singleton y el cifrado en reposo del archivo local.

    Usa una carpeta temporal propia (tempfile.mkdtemp) para no tocar el
    archivo real del proyecto, y reinicia el Singleton antes y después de
    cada prueba para que una prueba no herede datos de la anterior.
    """

    def setUp(self):
        self.carpeta_temporal = tempfile.mkdtemp()
        RepositorioLocal.reiniciar()
        self.repositorio = RepositorioLocal(
            ruta_archivo=os.path.join(self.carpeta_temporal, "pacientes_prueba.json"),
            ruta_clave=os.path.join(self.carpeta_temporal, "clave_prueba.key"),
        )
        self.paciente = Paciente("Rosa", "Vásquez", "45678912", SAL,
                                 date(1990, 1, 1), "F", "Chagual")

    def tearDown(self):
        RepositorioLocal.reiniciar()
        shutil.rmtree(self.carpeta_temporal, ignore_errors=True)

    def test_singleton_siempre_devuelve_la_misma_instancia(self):
        otro = RepositorioLocal()
        self.assertIs(otro, self.repositorio)

    def test_guardar_y_cargar_recupera_los_mismos_datos(self):
        self.repositorio.guardar_pacientes([self.paciente])
        guardados = self.repositorio.cargar_pacientes()
        self.assertEqual(len(guardados), 1)
        self.assertEqual(guardados[0]["nombres"], "Rosa")
        self.assertEqual(guardados[0]["id"], self.paciente.dni_seudonimo)

    def test_archivo_en_disco_queda_cifrado(self):
        self.repositorio.guardar_pacientes([self.paciente])
        with open(self.repositorio.ruta_archivo, "rb") as archivo:
            crudo = archivo.read()
        # Un archivo cifrado con Fernet nunca contiene comillas dobles;
        # un JSON sin cifrar sí las tendría por todos lados.
        self.assertNotIn(b'"', crudo)

    def test_cargar_pacientes_sin_archivo_devuelve_lista_vacia(self):
        self.assertEqual(self.repositorio.cargar_pacientes(), [])


class PruebaControlador(unittest.TestCase):
    """Verifica los manejadores de eventos y su conexión con los otros módulos."""

    def setUp(self):
        self.carpeta_temporal = tempfile.mkdtemp()
        RepositorioLocal.reiniciar()
        repositorio = RepositorioLocal(
            ruta_archivo=os.path.join(self.carpeta_temporal, "pacientes_prueba.json"),
            ruta_clave=os.path.join(self.carpeta_temporal, "clave_prueba.key"),
        )
        self.controlador = ControladorPuestoSalud(SAL, repositorio)

    def tearDown(self):
        RepositorioLocal.reiniciar()
        shutil.rmtree(self.carpeta_temporal, ignore_errors=True)

    def test_al_registrar_paciente_exitoso(self):
        respuesta = self.controlador.al_registrar_paciente(
            nombres="Rosa", apellidos="Vásquez", dni="45678912",
            fecha_nacimiento=date(1990, 1, 1), sexo="F", comunidad="Chagual")
        self.assertTrue(respuesta["exito"])
        self.assertEqual(len(self.controlador.pacientes), 1)

    def test_al_registrar_paciente_rechaza_dni_invalido(self):
        respuesta = self.controlador.al_registrar_paciente(
            nombres="Prueba", apellidos="Inválida", dni="123",
            fecha_nacimiento=date(1990, 1, 1), sexo="F", comunidad="Chagual")
        self.assertFalse(respuesta["exito"])

    def test_al_registrar_paciente_rechaza_duplicado(self):
        datos = dict(nombres="Rosa", apellidos="Vásquez", dni="45678912",
                     fecha_nacimiento=date(1990, 1, 1), sexo="F", comunidad="Chagual")
        self.controlador.al_registrar_paciente(**datos)
        segunda_vez = self.controlador.al_registrar_paciente(**datos)
        self.assertFalse(segunda_vez["exito"])
        self.assertIn("ya está registrado", segunda_vez["mensaje"])

    def test_al_generar_reporte_delega_a_reportes(self):
        hoy = date.today()
        self.controlador.cargar_datos_en_memoria(
            [], [ControlVacunacion("id1", hoy, "Obstetra", "BCG", 1)])
        reporte = self.controlador.al_generar_reporte(
            desde=hoy - timedelta(days=1), hasta=hoy)
        self.assertEqual(reporte["total_atenciones"], 1)
        self.assertIn("por_tipo", reporte)


class PruebaDespachadorEventos(unittest.TestCase):
    """Verifica el paradigma orientado a eventos de forma aislada."""

    def test_despachador_ejecuta_el_manejador_suscrito(self):
        despachador = DespachadorEventos()
        resultados = []
        despachador.suscribir("saludo", lambda nombre: resultados.append(f"Hola {nombre}"))
        despachador.emitir("saludo", nombre="Rosa")
        self.assertEqual(resultados, ["Hola Rosa"])

    def test_despachador_lanza_error_si_nadie_esta_suscrito(self):
        despachador = DespachadorEventos()
        with self.assertRaises(KeyError):
            despachador.emitir("evento_sin_manejador")


if __name__ == "__main__":
    unittest.main(verbosity=2)
