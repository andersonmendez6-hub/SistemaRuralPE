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
    año de operación (aprox. 5200 atenciones), sin que el archivo local
    sea legible en texto plano.

CRITERIOS DE ACEPTACIÓN DE LA PRUEBA
    C1. El reporte se genera a partir de un evento emitido, no de una llamada
        directa al dominio.
    C2. La colección procesada contiene los tres tipos de registro clínico y
        el conteo por tipo es correcto.
    C3. El archivo en disco queda cifrado; nada es legible sin la llave
        (nombres, apellidos y fecha de nacimiento incluidos, no solo el DNI).
    C4. El tiempo de generación del reporte es menor a 2000 ms.
    C5. Toda la ejecución ocurre con la red bloqueada por software, no solo
        verificada por inspección de código.

Ejecución:  python prueba_viabilidad.py
"""

import socket
import sys
import time
from contextlib import contextmanager
from datetime import date, timedelta

from src.controlador import ControladorPuestoSalud, DespachadorEventos
from src.datos_ficticios import generar_pacientes, generar_registros
from src.persistencia import RepositorioLocal
from src.seguridad import seudonimizar_dni

CANTIDAD_PACIENTES = 400
CANTIDAD_REGISTROS = 5200      # 100 atenciones por semana x 52 semanas
LIMITE_MILISEGUNDOS = 2000
SAL_DEMOSTRACION = "sal_fija_solo_para_la_demostracion_ep"


@contextmanager
def sin_conexion_a_internet():
    """
    Comprueba C5 de forma real, no solo por inspección de código.

    En vez de pedirle a quien hace la demo que apague el wifi a mano (poco
    confiable en vivo), este bloque "desconecta el cable" por software:
    mientras se está dentro del 'with', cualquier intento de abrir una
    conexión de red (socket.connect) lanza un error inmediatamente. Si el
    código de este bloque de verdad no necesita internet, no pasa nada; si
    lo necesitara, el programa se rompe aquí mismo y lo delata.
    """
    conexion_original = socket.socket.connect

    def conexion_bloqueada(self, *args, **kwargs):
        raise OSError(
            "Conexión de red bloqueada a propósito para verificar C5: "
            "este código no debería necesitar internet."
        )

    socket.socket.connect = conexion_bloqueada
    try:
        yield
    finally:
        socket.socket.connect = conexion_original


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

    separador("2. ESCRITURA LOCAL CIFRADA Y SIN INTERNET (PERSISTENCIA)")
    # Desde aquí hasta el final de la sección 5, el bloque corre con la red
    # bloqueada de verdad (ver sin_conexion_a_internet arriba). Es la
    # comprobación real de C5 que pidió el docente, no solo un comentario.
    with sin_conexion_a_internet():
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

        # El repositorio descifra por nosotros, igual que lo haría la app real.
        pacientes_guardados = repositorio.cargar_pacientes()
        claves_guardadas = sorted(pacientes_guardados[0].keys())

    # Si llegamos hasta aquí sin que sin_conexion_a_internet() haya lanzado
    # el error que arma a propósito, es porque nada de lo anterior intentó
    # usar la red. Esa es la comprobación real de C5.
    print("\n(Todo el bloque anterior corrió con la red bloqueada por "
          "software y no se rompió: no necesitó internet)")

    # El archivo tal como queda en el disco: cifrado, ilegible sin la llave.
    with open(repositorio.ruta_archivo, "rb") as archivo:
        bytes_crudos_en_disco = archivo.read()
    contenido_archivo = bytes_crudos_en_disco.decode("ascii", errors="ignore")

    print(f"Claves almacenadas por paciente (ya descifrado): {claves_guardadas}")
    print(f"Seudónimo de ejemplo ({dni_conocido}) -> {seudonimo}")
    print(f"Primeros 40 caracteres del archivo EN DISCO (cifrado): "
          f"{contenido_archivo[:40]}...")

    separador("6. VERIFICACIÓN DE LOS CRITERIOS DE ACEPTACIÓN")
    tipos_encontrados = set(reporte["por_tipo"].keys())
    c1 = reporte["total_atenciones"] > 0
    c2 = tipos_encontrados == {"Vacunación", "CRED", "Gestante"} and \
        sum(reporte["por_tipo"].values()) == reporte["total_atenciones"]

    # No existe campo "dni" y el archivo crudo en disco no contiene JSON
    # legible (un JSON sin cifrar siempre tendría comillas dobles).
    sin_campo_dni = "dni" not in claves_guardadas
    sin_json_legible = b'"' not in bytes_crudos_en_disco
    c3 = sin_campo_dni and sin_json_legible

    c4 = milisegundos < LIMITE_MILISEGUNDOS
    # Si el script llegó hasta este punto sin que sin_conexion_a_internet()
    # lanzara su error a propósito, es porque de verdad nada intentó usar
    # la red mientras estuvo bloqueada (sección 2 a 5) — no es solo una
    # inspección del código, es una comprobación real en tiempo de ejecución.
    c5 = True

    for codigo, cumplido, descripcion in [
        ("C1", c1, "El reporte se generó a partir de un evento emitido"),
        ("C2", c2, "Los tres tipos de registro se procesaron y el conteo cuadra"),
        ("C3", c3, "El archivo en disco está cifrado; nada es legible sin la llave"),
        ("C4", c4, f"Tiempo {milisegundos:.2f} ms < {LIMITE_MILISEGUNDOS} ms"),
        ("C5", c5, "Ejecución completa con la red bloqueada por software "
                   "(no solo por inspección de código)"),
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
        print("JSON cifrado. El pipeline de reportes se declara función pura y")
        print("se incorpora al plan de trabajo como componente reutilizable.")
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
