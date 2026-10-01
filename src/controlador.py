"""
Capa de control orientada a eventos.

Paradigma: Programación Orientada a Eventos.
La interfaz gráfica no conoce el dominio ni los reportes: solo publica
eventos ("registrar_paciente", "generar_reporte") en un despachador, y
este invoca al manejador (handler) correspondiente.

Esta separación permite ejecutar exactamente los mismos manejadores que
dispara un botón de la GUI desde un script de consola, lo que hace que la
prueba de viabilidad pueda verificarse sin abrir una ventana.
"""

from datetime import date

from . import reportes
from .dominio import Paciente
from .persistencia import RepositorioLocal


class DespachadorEventos:
    """Despachador mínimo de eventos (listeners y handlers)."""

    def __init__(self):
        self._manejadores = {}

    def suscribir(self, nombre_evento: str, manejador) -> None:
        self._manejadores.setdefault(nombre_evento, []).append(manejador)

    def emitir(self, nombre_evento: str, **datos):
        """Ejecuta los manejadores suscritos y devuelve sus resultados."""
        if nombre_evento not in self._manejadores:
            raise KeyError(f"No hay manejadores suscritos al evento '{nombre_evento}'.")
        return [manejador(**datos) for manejador in self._manejadores[nombre_evento]]


class ControladorPuestoSalud:
    """Manejadores de la aplicación; son el punto de unión de los 3 paradigmas."""

    def __init__(self, sal: str, repositorio: RepositorioLocal):
        self._sal = sal
        self._repositorio = repositorio
        self._pacientes = []
        self._registros = []

    @property
    def pacientes(self) -> list:
        return list(self._pacientes)

    @property
    def registros(self) -> list:
        return list(self._registros)

    def cargar_datos_en_memoria(self, pacientes, registros) -> None:
        """Carga un conjunto de datos ficticios para la demostración."""
        self._pacientes = list(pacientes)
        self._registros = list(registros)

    # --- Manejadores de eventos (handlers) -------------------------------

    def al_registrar_paciente(self, nombres, apellidos, dni, fecha_nacimiento,
                              sexo, comunidad) -> dict:
        """Handler del botón 'Registrar paciente' (RF1)."""
        try:
            paciente = Paciente(nombres, apellidos, dni, self._sal,
                                fecha_nacimiento, sexo, comunidad)
        except ValueError as error:
            return {"exito": False, "mensaje": str(error)}

        if any(p.dni_seudonimo == paciente.dni_seudonimo for p in self._pacientes):
            return {"exito": False, "mensaje": "El paciente ya está registrado."}

        self._pacientes.append(paciente)
        self._repositorio.guardar_pacientes(self._pacientes)
        return {
            "exito": True,
            "mensaje": f"Paciente {paciente.nombre_completo} registrado.",
            "dni_mostrado": paciente.dni_mascara,
        }

    def al_generar_reporte(self, desde: date, hasta: date) -> dict:
        """Handler del botón 'Generar reporte' (RF8): delega al módulo funcional."""
        return reportes.generar_reporte_atencion(self._registros, desde, hasta)
