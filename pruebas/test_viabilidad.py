"""
Pruebas automatizadas del prototipo (biblioteca estándar: unittest).

Se usa unittest en lugar de pytest para no exigir instalación de paquetes
en los equipos del establecimiento. En la Evaluación Final se migrarán a
pytest, que es la herramienta indicada en el desafío.

Ejecución desde la raíz del proyecto:
    python -m unittest discover -s pruebas -v
"""

import os
import sys
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dominio import ControlCRED, ControlGestante, ControlVacunacion, Cita
from src.reportes import contar_por_tipo, filtrar_por_periodo, total_atenciones
from src.seguridad import enmascarar_dni, seudonimizar_dni, verificar_dni


class PruebaSeguridadDatosPersonales(unittest.TestCase):
    """Verifica el tratamiento de datos personales (Ley N.° 29733)."""

    SAL = "sal_de_prueba"

    def test_seudonimo_no_contiene_el_dni(self):
        seudonimo = seudonimizar_dni("45678912", self.SAL)
        self.assertNotIn("45678912", seudonimo)
        self.assertEqual(len(seudonimo), 16)

    def test_seudonimo_es_determinista_y_verificable(self):
        seudonimo = seudonimizar_dni("45678912", self.SAL)
        self.assertTrue(verificar_dni("45678912", self.SAL, seudonimo))
        self.assertFalse(verificar_dni("45678913", self.SAL, seudonimo))

    def test_dni_invalido_lanza_excepcion(self):
        with self.assertRaises(ValueError):
            seudonimizar_dni("123", self.SAL)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
