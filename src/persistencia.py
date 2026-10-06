"""
Persistencia local del establecimiento.

Restricción de diseño atendida: el puesto de salud de Chagual tiene
conectividad intermitente, por lo que el almacenamiento es 100 % local
(archivo JSON en el equipo) y no requiere servidor ni internet.

Patrón de diseño: Singleton. El archivo de datos es un recurso único y
compartido; permitir varias instancias escribiendo a la vez provocaría
pérdida de registros clínicos.

Cifrado en reposo: el archivo completo (nombres, apellidos, fecha de
nacimiento, comunidad) se cifra con Fernet (AES simétrico) antes de
guardarse en disco. Antes solo el DNI estaba protegido (seudonimizado);
el resto de los datos del paciente quedaban en texto plano, lo cual fue
observado en la retroalimentación del docente. Ahora NADA del archivo es
legible sin la llave.

Requiere la librería 'cryptography' (no incluida en la biblioteca
estándar): pip install cryptography
"""

import json
import os
from datetime import date

from cryptography.fernet import Fernet, InvalidToken

RUTA_CLAVE_POR_DEFECTO = "datos/clave_cifrado.key"


def obtener_clave(ruta_clave: str = RUTA_CLAVE_POR_DEFECTO) -> bytes:
    """
    Devuelve la llave de cifrado, generando una nueva la primera vez.

    La llave se guarda en un archivo aparte de los datos (igual que la
    llave de una caja fuerte no se guarda pegada a la caja). Para este
    prototipo académico basta con un archivo local; en un sistema en
    producción esa llave se guardaría en un gestor de secretos, no en el
    mismo disco.
    """
    if os.path.exists(ruta_clave):
        with open(ruta_clave, "rb") as archivo:
            return archivo.read()

    nueva_clave = Fernet.generate_key()
    carpeta = os.path.dirname(ruta_clave)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta_clave, "wb") as archivo:
        archivo.write(nueva_clave)
    return nueva_clave


class RepositorioLocal:
    """Repositorio Singleton sobre un archivo JSON local, cifrado en disco."""

    _instancia = None

    def __new__(cls, ruta_archivo: str = "datos/pacientes_ficticios.json",
                ruta_clave: str = RUTA_CLAVE_POR_DEFECTO):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self, ruta_archivo: str = "datos/pacientes_ficticios.json",
                 ruta_clave: str = RUTA_CLAVE_POR_DEFECTO):
        if self._inicializado:
            return
        self._ruta_archivo = ruta_archivo
        self._pacientes = []
        self._fernet = Fernet(obtener_clave(ruta_clave))
        self._inicializado = True

    @property
    def ruta_archivo(self) -> str:
        return self._ruta_archivo

    def guardar_pacientes(self, pacientes) -> int:
        """
        Cifra y escribe los pacientes seudonimizados en disco.

        Devuelve la cantidad de registros escritos. Maneja explícitamente
        los errores de escritura para no dejar el archivo a medio escribir.
        """
        contenido = {
            "establecimiento": "Puesto de Salud I-1 Nuevo Amanecer",
            "fecha_exportacion": date.today().isoformat(),
            "aviso_legal": ("Datos ficticios. Los identificadores fueron "
                            "seudonimizados y el archivo completo está "
                            "cifrado, conforme a la Ley N.° 29733."),
            "pacientes": [p.a_diccionario() for p in pacientes],
        }
        try:
            carpeta = os.path.dirname(self._ruta_archivo)
            if carpeta:
                os.makedirs(carpeta, exist_ok=True)
            texto_json = json.dumps(contenido, ensure_ascii=False, indent=2)
            datos_cifrados = self._fernet.encrypt(texto_json.encode("utf-8"))
            with open(self._ruta_archivo, "wb") as archivo:
                archivo.write(datos_cifrados)
        except OSError as error:
            raise RuntimeError(
                f"No se pudo guardar el archivo local de pacientes: {error}"
            ) from error
        return len(contenido["pacientes"])

    def cargar_pacientes(self) -> list:
        """Lee y descifra el archivo local. Si no existe, devuelve lista vacía."""
        try:
            with open(self._ruta_archivo, "rb") as archivo:
                datos_cifrados = archivo.read()
            texto_json = self._fernet.decrypt(datos_cifrados).decode("utf-8")
            return json.loads(texto_json).get("pacientes", [])
        except FileNotFoundError:
            return []
        except (InvalidToken, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"El archivo local está corrupto, cifrado con otra llave, "
                f"o dañado: {error}"
            ) from error

    @classmethod
    def reiniciar(cls) -> None:
        """Solo para pruebas automatizadas: libera la instancia única."""
        cls._instancia = None
