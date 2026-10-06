"""
Generación de reportes de atención (RF8) y búsqueda de pacientes.

Paradigma: Programación Funcional.
Todas las funciones de este módulo son puras: no modifican la colección
recibida, no escriben en disco y no dependen de estado global. Esto reduce
el riesgo de alterar accidentalmente datos clínicos sensibles y hace que
cada función sea verificable de forma aislada.
"""

from datetime import date
from functools import reduce


def filtrar_por_periodo(registros, desde: date, hasta: date):
    """filter: devuelve solo las atenciones dentro del rango solicitado."""
    return list(filter(lambda r: desde <= r.fecha_atencion <= hasta, registros))


def extraer_tipos(registros):
    """map + polimorfismo: obtiene la etiqueta de tipo de cada atención."""
    return list(map(lambda r: r.tipo, registros))


def contar_por_tipo(registros) -> dict:
    """
    reduce: consolida el conteo de atenciones por tipo.

    Se construye un diccionario nuevo en cada paso para mantener la pureza
    de la función (no se muta el acumulador recibido).
    """
    def acumular(conteo, tipo):
        return {**conteo, tipo: conteo.get(tipo, 0) + 1}

    return reduce(acumular, extraer_tipos(registros), {})


def total_atenciones(registros) -> int:
    """reduce: total de atenciones del periodo."""
    return reduce(lambda acumulado, _: acumulado + 1, registros, 0)


def resumenes_legibles(registros, limite: int = 5):
    """map: convierte registros en líneas de texto para la jefatura."""
    return list(map(
        lambda r: f"[{r.fecha_atencion.isoformat()}] {r.tipo}: {r.resumen()}",
        registros[:limite]
    ))


def buscar_paciente_por_id(pacientes, id_seudonimo: str):
    """
    filter: localiza un paciente por su identificador seudonimizado.

    Devuelve el objeto Paciente si existe, o None si no hay coincidencia.
    No necesita el DNI real en ningún momento, solo el código ya guardado.
    """
    encontrados = list(filter(lambda p: p.dni_seudonimo == id_seudonimo, pacientes))
    return encontrados[0] if encontrados else None


def pacientes_menores_de(pacientes, edad_limite: int):
    """filter: subconjunto de pacientes por rango etario (apoyo al CRED)."""
    return list(filter(lambda p: p.edad < edad_limite, pacientes))


def generar_reporte_atencion(registros, desde: date, hasta: date) -> dict:
    """
    Composición de las funciones anteriores: el reporte completo de RF8.

    Devuelve un diccionario, no un texto formateado, para que la interfaz
    gráfica decida cómo presentarlo (separación de responsabilidades).
    """
    del_periodo = filtrar_por_periodo(registros, desde, hasta)
    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "total_atenciones": total_atenciones(del_periodo),
        "por_tipo": contar_por_tipo(del_periodo),
        "muestra": resumenes_legibles(del_periodo),
    }
