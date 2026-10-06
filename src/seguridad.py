"""
Módulo de seguridad de datos personales.

Responsabilidad única (SRP): proteger los identificadores directos de los
pacientes antes de que lleguen a la capa de persistencia, conforme a la
Ley N.° 29733 de Protección de Datos Personales.

Decisión de diseño: se usa únicamente la biblioteca estándar de Python
(hashlib, hmac, secrets) para que este módulo en particular pueda
ejecutarse sin instalar dependencias externas ni requerir conexión a
internet. El cifrado del archivo completo (que sí usa una dependencia
externa) vive aparte, en persistencia.py.
"""

import hashlib
import hmac
import secrets

# Longitud del seudónimo almacenado. 16 caracteres hexadecimales (64 bits)
# son suficientes para evitar colisiones en un establecimiento I-1.
LONGITUD_SEUDONIMO = 16


def generar_sal() -> str:
    """Genera una sal aleatoria criptográficamente segura (clave del puesto)."""
    return secrets.token_hex(16)


def seudonimizar_dni(dni: str, sal: str) -> str:
    """
    Convierte un DNI en un seudónimo irreversible mediante SHA-256 con sal.

    El seudónimo es determinista: el mismo DNI con la misma sal produce
    siempre el mismo valor, lo que permite detectar duplicados de paciente
    sin almacenar nunca el DNI en texto plano.
    """
    if not isinstance(dni, str) or len(dni.strip()) != 8 or not dni.strip().isdigit():
        raise ValueError("El DNI debe ser una cadena de 8 dígitos numéricos.")

    digest = hashlib.sha256((sal + dni.strip()).encode("utf-8")).hexdigest()
    return digest[:LONGITUD_SEUDONIMO]


def verificar_dni(dni: str, sal: str, seudonimo_guardado: str) -> bool:
    """
    Comprueba si un DNI ingresado corresponde a un seudónimo ya almacenado.

    Usa comparación en tiempo constante (hmac.compare_digest) para no filtrar
    información por diferencias de tiempo de respuesta.
    """
    try:
        candidato = seudonimizar_dni(dni, sal)
    except ValueError:
        return False
    return hmac.compare_digest(candidato, seudonimo_guardado)


def enmascarar_dni(dni: str) -> str:
    """
    Devuelve el DNI enmascarado para mostrarlo en pantalla (p. ej. *****678).

    El personal de salud necesita confirmar visualmente la identidad del
    paciente sin que el documento completo quede expuesto en la interfaz.
    """
    dni = str(dni).strip()
    if len(dni) < 3:
        return "*" * len(dni)
    return "*" * (len(dni) - 3) + dni[-3:]
