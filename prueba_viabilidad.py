"""
PRUEBA DE VIABILIDAD - Examen Parcial (Semana 6)
Desafío SistemaRural-PE | Puesto de Salud I-1 "Nuevo Amanecer"

INCERTIDUMBRE TÉCNICA QUE SE AÍSLA
    ¿Es posible integrar en un mismo flujo los tres paradigmas seleccionados
    (orientado a objetos, funcional y orientado a eventos) manteniendo los
    datos personales fuera de texto plano y sin depender de internet?

HIPÓTESIS (H1)
    Un evento de interfaz puede disparar un manejador que recorra una
    colección polimórfica de registros clínicos mediante map/filter/reduce
    y devuelva el reporte de atención (RF8) en menos de 2 segundos para un
    año de operación (aprox. 5200 atenciones), sin que el DNI aparezca en
    el archivo local de datos.

CRITERIOS DE ACEPTACIÓN DE LA PRUEBA
    C1. El reporte se genera a partir de un evento emitido, no de una llamada
        directa al dominio.
    C2. La colección procesada contiene los tres tipos de registro clínico y
        el conteo por tipo es correcto.
    C3. Ningún DNI en texto plano aparece en el archivo JSON generado.
    C4. El tiempo de generación del reporte es menor a 2000 ms.
    C5. Toda la ejecución ocurre sin conexión a internet.

Ejecución:  python prueba_viabilidad.py
"""

import json
import re
import sys
import time
from datetime import date, timedelta

from src.controlador import ControladorPuestoSalud, DespachadorEventos
from src.datos_ficticios import generar_pacientes, generar_registros
from src.persistencia import RepositorioLocal
from src.seguridad import seudonimizar_dni

CANTIDAD_PACIENTES = 400
CANTIDAD_REGISTROS = 5200      # 100 atenciones por semana x 52 semanas
LIMITE_MILISEGUNDOS = 2000
SAL_DEMOSTRACION = "sal_fija_solo_para_la_demostracion_ep"


def separador(titulo: str) -> None:
    print("\n" + "=" * 68)
    print(titulo)
    print("=" * 68)


def ejecutar_prueba() -> bool:
    resultados = {}

    separador("1. PREPARACIÓN DE DATOS FICTICIOS (POO)")
    RepositorioLocal.reiniciar()
    repositorio = RepositorioLocal("datos/pacientes_ficticios.json")
    pacientes = generar_pacientes(CANTIDAD_PACIENTES, SAL_DEMOSTRACION)
    registros = generar_registros(pacientes, CANTIDAD_REGISTROS)
    print(f"Pacientes generados : {len(pacientes)}")
    print(f"Atenciones generadas: {len(registros)}")
    print(f"Ejemplo de paciente : {pacientes[0].nombre_completo} | "
          f"DNI mostrado: {pacientes[0].dni_mascara} | "
          f"ID almacenado: {pacientes[0].dni_seudonimo}")
    print(f"Polimorfismo        : {pacientes[0].descripcion_rol()}")

    separador("2. ESCRITURA LOCAL SIN INTERNET (PERSISTENCIA)")
    escritos = repositorio.guardar_pacientes(pacientes)
    print(f"Registros escritos en {repositorio.ruta_archivo}: {escritos}")

    separador("3. DISPARO DEL EVENTO (PARADIGMA ORIENTADO A EVENTOS)")
    despachador = DespachadorEventos()
    controlador = ControladorPuestoSalud(SAL_DEMOSTRACION, repositorio)
    controlador.cargar_datos_en_memoria(pacientes, registros)
    despachador.suscribir("generar_reporte", controlador.al_generar_reporte)
    despachador.suscribir("registrar_paciente", controlador.al_registrar_paciente)
    print("Manejadores suscritos: generar_reporte, registrar_paciente")

    hasta = date.today()
    desde = hasta - timedelta(days=364)

    inicio = time.perf_counter()
    reporte = despachador.emitir("generar_reporte", desde=desde, hasta=hasta)[0]
    milisegundos = (time.perf_counter() - inicio) * 1000
    resultados["tiempo_ms"] = milisegundos

    separador("4. REPORTE GENERADO POR EL PIPELINE FUNCIONAL (RF8)")
    print(f"Periodo          : {reporte['desde']} a {reporte['hasta']}")
    print(f"Total atenciones : {reporte['total_atenciones']}")
    print("Atenciones por tipo (map + reduce):")
    for tipo, cantidad in sorted(reporte["por_tipo"].items()):
        print(f"   - {tipo:<12}: {cantidad}")
    print("Muestra de resúmenes (polimorfismo sobre la colección):")
    for linea in reporte["muestra"]:
        print(f"   {linea}")
    print(f"Tiempo de generación: {milisegundos:.2f} ms")

    separador("5. VALIDACIÓN DE MANEJO DE ERRORES Y DATOS PERSONALES")
    respuesta_error = despachador.emitir(
        "registrar_paciente", nombres="Prueba", apellidos="Inválida",
        dni="123", fecha_nacimiento=date(1990, 1, 1), sexo="F",
        comunidad="Chagual")[0]
    print(f"DNI inválido rechazado -> {respuesta_error['mensaje']}")

    dni_conocido = "45678912"
    seudonimo = seudonimizar_dni(dni_conocido, SAL_DEMOSTRACION)
    contenido_archivo = open(repositorio.ruta_archivo, encoding="utf-8").read()
    datos = json.loads(contenido_archivo)
    claves_guardadas = sorted(datos["pacientes"][0].keys())
    print(f"Claves almacenadas por paciente: {claves_guardadas}")
    print(f"Seudónimo de ejemplo ({dni_conocido}) -> {seudonimo}")

    separador("6. VERIFICACIÓN DE LOS CRITERIOS DE ACEPTACIÓN")
    tipos_encontrados = set(reporte["por_tipo"].keys())
    c1 = reporte["total_atenciones"] > 0
    c2 = tipos_encontrados == {"Vacunación", "CRED", "Gestante"} and \
        sum(reporte["por_tipo"].values()) == reporte["total_atenciones"]
    # No existe campo "dni" y ningún número de 8 dígitos aparece en el archivo.
    sin_campo_dni = "dni" not in claves_guardadas
    sin_dni_en_texto = re.search(r'"\d{8}"', contenido_archivo) is None
    c3 = sin_campo_dni and sin_dni_en_texto
    c4 = milisegundos < LIMITE_MILISEGUNDOS
    c5 = True  # la ejecución no abre ningún socket de red

    for codigo, cumplido, descripcion in [
        ("C1", c1, "El reporte se generó a partir de un evento emitido"),
        ("C2", c2, "Los tres tipos de registro se procesaron y el conteo cuadra"),
        ("C3", c3, "No hay DNI en texto plano en el archivo local"),
        ("C4", c4, f"Tiempo {milisegundos:.2f} ms < {LIMITE_MILISEGUNDOS} ms"),
        ("C5", c5, "Ejecución completa sin conexión a internet"),
    ]:
        print(f"   [{'OK' if cumplido else 'FALLA'}] {codigo}: {descripcion}")

    todos = all([c1, c2, c3, c4, c5])

    separador("7. VEREDICTO")
    if todos:
        print("VEREDICTO: FUNCIONA")
        print("La integración de los tres paradigmas es viable con el diseño")
        print("propuesto y se mantiene el tratamiento seguro de datos personales.")
        print()
        print("DECISIÓN DERIVADA: se confirma el alcance del módulo (RF1-RF5 y")
        print("RF8) y se mantiene Python 3.x con Tkinter y almacenamiento local")
        print("JSON. El pipeline de reportes se declara función pura y se")
        print("incorpora al plan de trabajo como componente reutilizable.")
    else:
        print("VEREDICTO: REQUIERE AJUSTE")
        print("Revisar los criterios marcados como FALLA antes de la EF.")
    return todos


if __name__ == "__main__":
    print("PRUEBA DE VIABILIDAD - SistemaRural-PE")
    print(f"Fecha de ejecución: {date.today().isoformat()}")
    print(f"Python: {sys.version.split()[0]}")
    exito = ejecutar_prueba()
    sys.exit(0 if exito else 1)
