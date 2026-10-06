"""
Generador de datos ficticios para la prueba de viabilidad.

Todos los nombres y documentos son inventados. No se utiliza ningún dato
personal real, conforme a las condiciones de entrega del desafío.
"""

import random
from datetime import date, timedelta

from .dominio import FabricaRegistroClinico, Paciente

NOMBRES = ["Rosa", "Julián", "Milagros", "Elmer", "Yanet", "Wilder",
           "Marleni", "Hipólito", "Flor", "Edilberto"]
APELLIDOS = ["Vásquez Chuquilín", "Rodríguez Aguilar", "Paredes Sifuentes",
             "Castillo Rubio", "Alvarado Mendoza", "Quispe Tarrillo"]
COMUNIDADES = ["Chagual", "Pias", "Zarumilla", "Huancaspata", "Chilia"]
VACUNAS = ["BCG", "Antipolio", "Pentavalente", "Influenza", "COVID-19"]


def generar_pacientes(cantidad: int, sal: str, semilla: int = 2026) -> list:
    """Crea pacientes ficticios con DNI de 8 dígitos generados al azar."""
    aleatorio = random.Random(semilla)
    pacientes = []
    for indice in range(cantidad):
        dni = f"{aleatorio.randint(10_000_000, 79_999_999)}"
        años_edad = aleatorio.choice([1, 2, 3, 4, 9, 18, 24, 27, 33, 41, 58, 67])
        nacimiento = date.today() - timedelta(days=años_edad * 365 + indice % 300)
        pacientes.append(Paciente(
            nombres=aleatorio.choice(NOMBRES),
            apellidos=aleatorio.choice(APELLIDOS),
            dni=dni,
            sal=sal,
            fecha_nacimiento=nacimiento,
            sexo=aleatorio.choice(["F", "M"]),
            comunidad=aleatorio.choice(COMUNIDADES),
        ))
    return pacientes


def generar_registros(pacientes, cantidad: int, semilla: int = 2026) -> list:
    """
    Crea una colección heterogénea de atenciones de un año de operación.

    La heterogeneidad es intencional: es lo que permite comprobar que el
    polimorfismo y el pipeline funcional trabajan sobre una sola colección.
    Usa FabricaRegistroClinico para no repetir, aquí, un if/elif propio
    por cada tipo de registro clínico.
    """
    aleatorio = random.Random(semilla + 1)
    responsables = ["Téc. Enf. jefe", "Obstetra", "Auxiliar de salud"]
    hoy = date.today()
    registros = []

    for _ in range(cantidad):
        paciente = aleatorio.choice(pacientes)
        fecha_atencion = hoy - timedelta(days=aleatorio.randint(0, 364))
        responsable = aleatorio.choice(responsables)
        tipo = aleatorio.choice(["vacuna", "cred", "gestante"])

        if tipo == "vacuna":
            datos = {"vacuna": aleatorio.choice(VACUNAS),
                     "dosis": aleatorio.randint(1, 3)}
            tipo_fabrica = "vacunacion"
        elif tipo == "cred":
            datos = {"peso_kg": round(aleatorio.uniform(3.0, 18.0), 1),
                     "talla_cm": round(aleatorio.uniform(50.0, 110.0), 1)}
            tipo_fabrica = "cred"
        else:
            datos = {"semanas_gestacion": aleatorio.randint(6, 40),
                     "numero_control": aleatorio.randint(1, 8)}
            tipo_fabrica = "gestante"

        registros.append(FabricaRegistroClinico.crear(
            tipo_fabrica, paciente.dni_seudonimo, fecha_atencion,
            responsable, **datos))

    return registros
