# SistemaRural-PE — Prototipo de viabilidad (Examen Parcial, Semana 6)

**Desafío:** SistemaRural-PE: diseño de software multiparadigma para la gestión de
establecimientos de salud en zonas rurales del Perú
**Caso aplicado:** Puesto de Salud I-1 "Nuevo Amanecer" — anexo de Chagual, Pataz, La Libertad
**Curso:** Lenguajes de Programación (UAIN1288P) — 2026-2

> Este repositorio **no** contiene el sistema completo. Contiene el prototipo mínimo
> que aísla y resuelve la principal incertidumbre técnica del proyecto, según el
> alcance definido para la Evaluación Parcial.

---

## 1. Qué se está probando

**Incertidumbre:** ¿es posible integrar los tres paradigmas seleccionados
(orientado a objetos, funcional y orientado a eventos) en un solo flujo del
sistema, sin exponer datos personales en texto plano y sin depender de
conexión a internet?

**Hipótesis (H1):** un evento de interfaz puede disparar un manejador que recorra
una colección polimórfica de registros clínicos mediante `map`/`filter`/`reduce`
y devuelva el reporte de atención (RF8) en menos de 2 segundos para un año de
operación (~5200 atenciones), sin que ningún DNI aparezca en el archivo local.

## 2. Requisitos

- Python 3.10 o superior (probado en 3.12.3).
- **Sin dependencias externas.** Todo el prototipo usa la biblioteca estándar.
- Tkinter (incluido en la instalación estándar de Python en Windows) solo si se
  desea ejecutar la interfaz gráfica.

## 3. Cómo ejecutar

Desde la carpeta raíz del proyecto:

```bash
# Prueba de viabilidad (consola, no necesita Tkinter)
python prueba_viabilidad.py

# Pruebas automatizadas
python -m unittest discover -s pruebas -v

# Interfaz gráfica de demostración (requiere Tkinter)
python app_gui.py
```

## 4. Estructura

```
.
├── prueba_viabilidad.py     Script de la prueba: procedimiento, criterios y veredicto
├── app_gui.py               Interfaz Tkinter (paradigma orientado a eventos)
├── src/
│   ├── dominio.py           POO: herencia, polimorfismo y encapsulamiento
│   ├── reportes.py          Funcional: map, filter y reduce (funciones puras)
│   ├── controlador.py       Eventos: despachador, listeners y handlers
│   ├── persistencia.py      Repositorio local JSON (patrón Singleton)
│   ├── seguridad.py         Seudonimización y enmascaramiento (Ley N.° 29733)
│   └── datos_ficticios.py   Generador reproducible de datos de prueba
├── pruebas/
│   └── test_viabilidad.py   9 pruebas automatizadas (unittest)
├── datos/                          Directorio de salida generado al ejecutar
└── evidencia/
    ├── salida_prueba_viabilidad.txt
    └── salida_pruebas_unitarias.txt
```

## 5. Dónde está cada paradigma

| Paradigma | Archivo | Evidencia concreta |
|---|---|---|
| Orientado a objetos | `src/dominio.py` | `Persona → Paciente / PersonalSalud`; `RegistroClinico → ControlVacunacion / ControlCRED / ControlGestante`; atributos privados y `@property` |
| Funcional | `src/reportes.py` | `filtrar_por_periodo` (filter), `extraer_tipos` (map), `contar_por_tipo` y `total_atenciones` (reduce); funciones puras |
| Orientado a eventos | `src/controlador.py`, `app_gui.py` | `DespachadorEventos.suscribir` / `.emitir`; los botones de la GUI solo emiten eventos |

## 6. Resultado obtenido

```
Total atenciones procesadas : 5200
Vacunación 1748 | Gestante 1736 | CRED 1716
Tiempo de generación        : ~2 ms  (límite: 2000 ms)
Criterios C1 a C5           : todos OK
Pruebas automatizadas       : 9/9 OK
VEREDICTO                   : FUNCIONA
```

## 7. Tratamiento de datos personales

- Los DNI **nunca** se almacenan: se convierten en un seudónimo irreversible
  (SHA-256 con sal) antes de llegar a la capa de persistencia.
- En pantalla el documento se muestra enmascarado (`*****912`).
- Todos los nombres y documentos del archivo de datos son **ficticios**; no se
  utilizó ningún dato personal real.
- En la Evaluación Final se añadirá cifrado del archivo local en reposo y un
  registro de accesos (log de auditoría).

## 8. Limitaciones conocidas de esta versión

- No incluye RF6 (control de medicamentos) ni RF7 (referencias), documentados
  pero fuera del alcance de esta entrega.
- La persistencia es un archivo JSON; en la EF se evaluará migrar a SQLite.
- La sal criptográfica está fijada en el código solo para que la demostración
  sea reproducible; en la EF se generará por establecimiento y se resguardará
  fuera del repositorio.
- El archivo JSON con los pacientes de demostración se genera al ejecutar los
  scripts y no se publica en el repositorio.
