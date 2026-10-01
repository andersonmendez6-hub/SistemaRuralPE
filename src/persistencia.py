"""
Persistencia local del establecimiento.

Restricción de diseño atendida: el puesto de salud de Chagual tiene
conectividad intermitente, por lo que el almacenamiento es 100 % local
(archivo JSON en el equipo) y no requiere servidor ni internet.

Patrón de diseño: Singleton. El archivo de datos es un recurso único y
compartido; permitir varias instancias escribiendo a la vez provocaría
pérdida de registros clínicos.
"""

import json
import os
from datetime import date


class RepositorioLocal:
    """Repositorio Singleton sobre un archivo JSON local."""

    _instancia = None

    def __new__(cls, ruta_archivo: str = "datos/pacientes_ficticios.json"):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self, ruta_archivo: str = "datos/pacientes_ficticios.json"):
        if self._inicializado:
            return
        self._ruta_archivo = ruta_archivo
        self._pacientes = []
        self._inicializado = True

    @property
    def ruta_archivo(self) -> str:
        return self._ruta_archivo

    def guardar_pacientes(self, pacientes) -> int:
        """
        Escribe los pacientes seudonimizados en disco.

        Devuelve la cantidad de registros escritos. Maneja explícitamente
        los errores de escritura para no dejar el archivo a medio escribir.
        """
        contenido = {
            "establecimiento": "Puesto de Salud I-1 Nuevo Amanecer",
            "fecha_exportacion": date.today().isoformat(),
            "aviso_legal": ("Datos ficticios. Los identificadores fueron "
                            "seudonimizados conforme a la Ley N.° 29733."),
            "pacientes": [p.a_diccionario() for p in pacientes],
        }
        try:
            carpeta = os.path.dirname(self._ruta_archivo)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            with open(self._ruta_archivo, "w", encoding="utf-8") as archivo:
                json.dump(contenido, archivo, ensure_ascii=False, indent=2)
        except OSError as error:
            raise RuntimeError(
                f"No se pudo guardar el archivo local de pacientes: {error}"
            ) from error
        return len(contenido["pacientes"])

    def cargar_pacientes(self) -> list:
        """Lee el archivo local. Si no existe, devuelve una lista vacía."""
        try:
            with open(self._ruta_archivo, "r", encoding="utf-8") as archivo:
                return json.load(archivo).get("pacientes", [])
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"El archivo local está corrupto y no pudo leerse: {error}"
            ) from error

    @classmethod
    def reiniciar(cls) -> None:
        """Solo para pruebas automatizadas: libera la instancia única."""
        cls._instancia = None
