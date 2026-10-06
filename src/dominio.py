"""
Modelo de dominio del Puesto de Salud I-1 "Nuevo Amanecer".

Paradigma: Programación Orientada a Objetos.
Aporta la jerarquía Persona -> (Paciente, PersonalSalud) y la jerarquía
RegistroClinico -> (ControlVacunacion, ControlCRED, ControlGestante),
que resuelve por polimorfismo el problema de tratar de forma uniforme
tres tipos de atención con reglas clínicas distintas.

También incluye Establecimiento (agregación de pacientes y personal,
composición de citas) y FabricaRegistroClinico (patrón Factory Method),
agregados para cumplir con los requisitos de la Evaluación Final:
al menos 3 tipos de relación UML y al menos 2 patrones de diseño.
"""

from abc import ABC, abstractmethod
from datetime import date

from .seguridad import enmascarar_dni, seudonimizar_dni


class Persona(ABC):
    """Clase base abstracta. Encapsula los datos identificadores."""

    def __init__(self, nombres: str, apellidos: str, dni: str, sal: str):
        self._nombres = nombres.strip()
        self._apellidos = apellidos.strip()
        # Atributos privados: el DNI en claro NUNCA se guarda como atributo.
        self.__dni_seudonimo = seudonimizar_dni(dni, sal)
        self.__dni_mascara = enmascarar_dni(dni)

    @property
    def nombre_completo(self) -> str:
        return f"{self._nombres} {self._apellidos}"

    @property
    def dni_seudonimo(self) -> str:
        """Único identificador expuesto hacia la capa de persistencia."""
        return self.__dni_seudonimo

    @property
    def dni_mascara(self) -> str:
        """Representación segura para la interfaz gráfica."""
        return self.__dni_mascara

    @abstractmethod
    def descripcion_rol(self) -> str:
        """Cada subclase describe su rol dentro del establecimiento."""


class Paciente(Persona):
    """Persona que recibe atención en el establecimiento (RF1)."""

    def __init__(self, nombres, apellidos, dni, sal, fecha_nacimiento: date,
                 sexo: str, comunidad: str):
        super().__init__(nombres, apellidos, dni, sal)
        self._fecha_nacimiento = fecha_nacimiento
        self._sexo = sexo
        self._comunidad = comunidad

    @property
    def edad(self) -> int:
        hoy = date.today()
        años = hoy.year - self._fecha_nacimiento.year
        if (hoy.month, hoy.day) < (self._fecha_nacimiento.month, self._fecha_nacimiento.day):
            años -= 1
        return años

    @property
    def sexo(self) -> str:
        return self._sexo

    @property
    def comunidad(self) -> str:
        return self._comunidad

    def descripcion_rol(self) -> str:
        return "Paciente del Puesto de Salud I-1 Nuevo Amanecer"

    def a_diccionario(self) -> dict:
        """Serializa el paciente SIN el DNI en texto plano (Ley N.° 29733)."""
        return {
            "id": self.dni_seudonimo,
            "nombres": self._nombres,
            "apellidos": self._apellidos,
            "fecha_nacimiento": self._fecha_nacimiento.isoformat(),
            "sexo": self._sexo,
            "comunidad": self._comunidad,
        }


class PersonalSalud(Persona):
    """Trabajador del establecimiento (técnico, obstetra, auxiliar)."""

    def __init__(self, nombres, apellidos, dni, sal, cargo: str):
        super().__init__(nombres, apellidos, dni, sal)
        self._cargo = cargo

    @property
    def cargo(self) -> str:
        return self._cargo

    def descripcion_rol(self) -> str:
        return f"{self._cargo} del establecimiento"


class RegistroClinico(ABC):
    """
    Clase base abstracta de toda atención registrada (RF3, RF4, RF5).

    El polimorfismo permite que el módulo de reportes recorra una sola
    colección heterogénea de registros sin condicionales por tipo.

    No hereda de Persona: una atención no es un tipo de persona, es un
    dato asociado a una persona (guarda su id, no la hereda).
    """

    def __init__(self, id_paciente: str, fecha_atencion: date, responsable: str):
        self._id_paciente = id_paciente
        self._fecha_atencion = fecha_atencion
        self._responsable = responsable

    @property
    def id_paciente(self) -> str:
        return self._id_paciente

    @property
    def fecha_atencion(self) -> date:
        return self._fecha_atencion

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Etiqueta del tipo de atención usada en los reportes."""

    @abstractmethod
    def resumen(self) -> str:
        """Descripción legible de la atención para el reporte de jefatura."""


class ControlVacunacion(RegistroClinico):
    """RF3: control de vacunación e inmunizaciones."""

    def __init__(self, id_paciente, fecha_atencion, responsable, vacuna: str, dosis: int):
        super().__init__(id_paciente, fecha_atencion, responsable)
        self._vacuna = vacuna
        self._dosis = dosis

    @property
    def tipo(self) -> str:
        return "Vacunación"

    def resumen(self) -> str:
        return f"Vacuna {self._vacuna}, dosis {self._dosis}"


class ControlCRED(RegistroClinico):
    """RF4: control de crecimiento y desarrollo de niños menores de 5 años."""

    def __init__(self, id_paciente, fecha_atencion, responsable,
                 peso_kg: float, talla_cm: float):
        super().__init__(id_paciente, fecha_atencion, responsable)
        self._peso_kg = peso_kg
        self._talla_cm = talla_cm

    @property
    def tipo(self) -> str:
        return "CRED"

    def resumen(self) -> str:
        return f"Peso {self._peso_kg} kg, talla {self._talla_cm} cm"


class ControlGestante(RegistroClinico):
    """RF5: atención y seguimiento de gestantes."""

    def __init__(self, id_paciente, fecha_atencion, responsable,
                 semanas_gestacion: int, numero_control: int):
        super().__init__(id_paciente, fecha_atencion, responsable)
        self._semanas_gestacion = semanas_gestacion
        self._numero_control = numero_control

    @property
    def tipo(self) -> str:
        return "Gestante"

    def resumen(self) -> str:
        return (f"Control N.° {self._numero_control}, "
                f"{self._semanas_gestacion} semanas de gestación")


class Cita:
    """RF2: programación y control de citas médicas."""

    ESTADOS_VALIDOS = ("PENDIENTE", "ATENDIDA", "CANCELADA")

    def __init__(self, id_paciente: str, fecha: date, motivo: str,
                 estado: str = "PENDIENTE"):
        self._id_paciente = id_paciente
        self._fecha = fecha
        self._motivo = motivo
        self.estado = estado  # pasa por el setter para validar

    @property
    def id_paciente(self) -> str:
        return self._id_paciente

    @property
    def fecha(self) -> date:
        return self._fecha

    @property
    def motivo(self) -> str:
        return self._motivo

    @property
    def estado(self) -> str:
        return self._estado

    @estado.setter
    def estado(self, nuevo_estado: str) -> None:
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado de cita no válido: {nuevo_estado}. "
                f"Valores permitidos: {', '.join(self.ESTADOS_VALIDOS)}"
            )
        self._estado = nuevo_estado


class FabricaRegistroClinico:
    """
    Patrón de diseño: Factory Method.

    Encapsula en un único lugar la decisión de qué subclase de
    RegistroClinico construir. Quien pide un registro nuevo (por ejemplo,
    datos_ficticios.py) no necesita conocer las tres subclases concretas
    ni repetir su propio if/elif para elegir cuál instanciar: se lo pide
    a la fábrica por nombre.
    """

    TIPOS_VALIDOS = ("vacunacion", "cred", "gestante")

    @staticmethod
    def crear(tipo: str, id_paciente: str, fecha_atencion: date,
              responsable: str, **datos) -> RegistroClinico:
        tipo = tipo.strip().lower()

        if tipo == "vacunacion":
            return ControlVacunacion(id_paciente, fecha_atencion, responsable,
                                     datos["vacuna"], datos["dosis"])
        if tipo == "cred":
            return ControlCRED(id_paciente, fecha_atencion, responsable,
                               datos["peso_kg"], datos["talla_cm"])
        if tipo == "gestante":
            return ControlGestante(id_paciente, fecha_atencion, responsable,
                                   datos["semanas_gestacion"], datos["numero_control"])

        raise ValueError(
            f"Tipo de registro clínico no reconocido: '{tipo}'. "
            f"Valores permitidos: {', '.join(FabricaRegistroClinico.TIPOS_VALIDOS)}"
        )


class Establecimiento:
    """
    Puesto de Salud I-1 "Nuevo Amanecer".

    Agrega pacientes y personal de salud: ambos existen y tienen sentido
    como personas aunque se les deje de asociar a este establecimiento en
    particular (agregación, propiedad débil).

    Compone las citas: una Cita solo tiene sentido como parte de la
    operación diaria de ESTE establecimiento — si el establecimiento
    dejara de operar, sus citas programadas dejan de tener sentido
    (composición, propiedad fuerte).
    """

    def __init__(self, nombre: str):
        self._nombre = nombre
        self._pacientes = []    # agregación
        self._personal = []     # agregación
        self._citas = []        # composición

    @property
    def nombre(self) -> str:
        return self._nombre

    def agregar_paciente(self, paciente: Paciente) -> None:
        self._pacientes.append(paciente)

    def agregar_personal(self, trabajador: PersonalSalud) -> None:
        self._personal.append(trabajador)

    def programar_cita(self, cita: Cita) -> None:
        self._citas.append(cita)

    @property
    def pacientes(self) -> list:
        return list(self._pacientes)

    @property
    def personal(self) -> list:
        return list(self._personal)

    @property
    def citas(self) -> list:
        return list(self._citas)

    def resumen(self) -> str:
        return (f"{self._nombre}: {len(self._pacientes)} pacientes, "
                f"{len(self._personal)} personal de salud, "
                f"{len(self._citas)} citas programadas")
