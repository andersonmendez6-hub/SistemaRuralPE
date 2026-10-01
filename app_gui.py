"""
Interfaz gráfica del prototipo (paradigma orientado a eventos).

Esta ventana NO contiene lógica de negocio: cada botón solo emite un
evento en el despachador, que a su vez invoca al manejador del
controlador. Es el mismo camino que recorre la prueba de viabilidad en
consola, por lo que la GUI no introduce lógica nueva que deba probarse
por separado.

Requiere Tkinter (incluido en la instalación estándar de Python en
Windows). Ejecución:  python app_gui.py
"""

import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, scrolledtext

from src.controlador import ControladorPuestoSalud, DespachadorEventos
from src.datos_ficticios import generar_pacientes, generar_registros
from src.persistencia import RepositorioLocal

SAL_DEMOSTRACION = "sal_fija_solo_para_la_demostracion_ep"


class VentanaPrincipal(tk.Tk):
    """Ventana principal del Puesto de Salud I-1 Nuevo Amanecer."""

    def __init__(self, despachador: DespachadorEventos):
        super().__init__()
        self._despachador = despachador
        self.title("SistemaRural-PE | Puesto de Salud I-1 Nuevo Amanecer")
        self.geometry("720x520")
        self._construir_formulario()
        self._construir_area_reporte()

    def _construir_formulario(self) -> None:
        marco = tk.LabelFrame(self, text="Registro de paciente (RF1)", padx=8, pady=8)
        marco.pack(fill="x", padx=10, pady=10)

        self._campos = {}
        etiquetas = [("nombres", "Nombres"), ("apellidos", "Apellidos"),
                     ("dni", "DNI (8 dígitos)"), ("comunidad", "Comunidad")]
        for fila, (clave, texto) in enumerate(etiquetas):
            tk.Label(marco, text=texto).grid(row=fila, column=0, sticky="w")
            entrada = tk.Entry(marco, width=38)
            entrada.grid(row=fila, column=1, padx=6, pady=2)
            self._campos[clave] = entrada

        # Listener: el clic del botón se traduce en un evento del despachador.
        tk.Button(marco, text="Registrar paciente",
                  command=self._al_hacer_clic_registrar).grid(row=4, column=1,
                                                              sticky="e", pady=6)

    def _construir_area_reporte(self) -> None:
        marco = tk.LabelFrame(self, text="Reporte de atenciones (RF8)",
                              padx=8, pady=8)
        marco.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Button(marco, text="Generar reporte del último año",
                  command=self._al_hacer_clic_reporte).pack(anchor="w", pady=4)

        self._salida = scrolledtext.ScrolledText(marco, height=14)
        self._salida.pack(fill="both", expand=True)

    # --- Listeners de la interfaz ---------------------------------------

    def _al_hacer_clic_registrar(self) -> None:
        try:
            respuesta = self._despachador.emitir(
                "registrar_paciente",
                nombres=self._campos["nombres"].get(),
                apellidos=self._campos["apellidos"].get(),
                dni=self._campos["dni"].get(),
                fecha_nacimiento=date(1995, 5, 20),
                sexo="F",
                comunidad=self._campos["comunidad"].get(),
            )[0]
        except Exception as error:  # la GUI nunca debe cerrarse por un error
            messagebox.showerror("Error inesperado", str(error))
            return

        if respuesta["exito"]:
            messagebox.showinfo(
                "Registro correcto",
                f"{respuesta['mensaje']}\nDNI almacenado de forma seudonimizada.\n"
                f"Se muestra en pantalla como: {respuesta['dni_mostrado']}")
        else:
            messagebox.showwarning("No se pudo registrar", respuesta["mensaje"])

    def _al_hacer_clic_reporte(self) -> None:
        hasta = date.today()
        desde = hasta - timedelta(days=364)
        reporte = self._despachador.emitir("generar_reporte",
                                           desde=desde, hasta=hasta)[0]
        self._salida.delete("1.0", tk.END)
        self._salida.insert(tk.END, f"Periodo: {reporte['desde']} a {reporte['hasta']}\n")
        self._salida.insert(tk.END, f"Total de atenciones: {reporte['total_atenciones']}\n\n")
        for tipo, cantidad in sorted(reporte["por_tipo"].items()):
            self._salida.insert(tk.END, f"  {tipo:<12}: {cantidad}\n")
        self._salida.insert(tk.END, "\nÚltimas atenciones registradas:\n")
        for linea in reporte["muestra"]:
            self._salida.insert(tk.END, f"  {linea}\n")


def main() -> None:
    RepositorioLocal.reiniciar()
    repositorio = RepositorioLocal("datos/pacientes_ficticios.json")
    pacientes = generar_pacientes(400, SAL_DEMOSTRACION)
    registros = generar_registros(pacientes, 5200)

    controlador = ControladorPuestoSalud(SAL_DEMOSTRACION, repositorio)
    controlador.cargar_datos_en_memoria(pacientes, registros)

    despachador = DespachadorEventos()
    despachador.suscribir("registrar_paciente", controlador.al_registrar_paciente)
    despachador.suscribir("generar_reporte", controlador.al_generar_reporte)

    VentanaPrincipal(despachador).mainloop()


if __name__ == "__main__":
    main()
