# SistemaRural-PE — Prototipo multiparadigma (Evaluación Final)

**Desafío:** SistemaRural-PE: diseño de software multiparadigma para la gestión de
establecimientos de salud en zonas rurales del Perú
**Caso aplicado:** Puesto de Salud I-1 "Nuevo Amanecer" — anexo de Chagual, Pataz, La Libertad
**Curso:** Lenguajes de Programación (UAIN1288P) — 2026-2

> Este repositorio parte del prototipo construido para la Evaluación Parcial
> (nota obtenida: 18/20) y se amplía aquí con lo exigido en la Evaluación
> Final: un segundo patrón de diseño, los tres tipos de relación UML, el
> cifrado del archivo local y la comprobación real de que el sistema
> funciona sin internet.

---

## 1. Qué se está probando

**Incertidumbre:** ¿es posible integrar los tres paradigmas seleccionados
(orientado a objetos, funcional y orientado a eventos) en un solo flujo del
sistema, sin exponer datos personales y sin depender de conexión a internet?

**Hipótesis (H1):** un evento de interfaz puede disparar un manejador que recorra
una colección polimórfica de registros clínicos mediante `map`/`filter`/`reduce`
y devuelva el reporte de atención (RF8) en menos de 2 segundos para un año de
operación (~5200 atenciones), sin que el archivo local sea legible sin su llave
de cifrado.

## 2. Requisitos

- Python 3.10 o superior (probado en 3.13).
- **Una sola dependencia externa:** `cryptography`, para el cifrado del archivo
  local. Se instala una sola vez con:
  ```bash
  pip install cryptography
  ```
  El resto del prototipo usa solo la biblioteca estándar de Python — por eso las
  pruebas automatizadas usan `unittest` (incluido con Python) y no `pytest`: el
  documento de la Evaluación Final pide "al menos 3 pruebas automatizadas" sin
  exigir una herramienta en particular, y pedir instalar algo más no tiene
  sentido en un proyecto que precisamente promete funcionar sin internet.
- Tkinter (incluido en la instalación estándar de Python en Windows) solo si se
  desea ejecutar la interfaz gráfica.

## 3. Cómo ejecutar

Desde la carpeta raíz del proyecto:

```bash
# Prueba de viabilidad (consola, no necesita Tkinter)
python prueba_viabilidad.py

# Pruebas automatizadas (27 pruebas, sin instalar nada aparte de cryptography)
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
│   ├── dominio.py           POO: herencia, polimorfismo, Establecimiento y Factory
│   ├── reportes.py          Funcional: map, filter y reduce (funciones puras)
│   ├── controlador.py       Eventos: despachador, listeners y handlers
│   ├── persistencia.py      Repositorio local cifrado (patrón Singleton)
│   ├── seguridad.py         Seudonimización y enmascaramiento (Ley N.° 29733)
│   └── datos_ficticios.py   Generador reproducible de datos de prueba
├── pruebas/
│   └── test_viabilidad.py   27 pruebas automatizadas (unittest)
├── datos/
│   ├── pacientes_ficticios.json   Archivo cifrado (ilegible sin la llave)
│   └── clave_cifrado.key          Llave de cifrado (NUNCA se sube a GitHub)
└── evidencia/
    ├── salida_prueba_viabilidad.txt
    └── salida_pruebas_unitarias.txt
```

> **Importante:** `datos/clave_cifrado.key` es la llave que descifra el archivo
> de pacientes. No debe subirse al repositorio público — agrégala a
> `.gitignore` junto con el resto de la carpeta `datos/`.

## 5. Dónde está cada paradigma y cada patrón de diseño

| Concepto | Archivo | Evidencia concreta |
|---|---|---|
| Orientado a objetos (herencia) | `src/dominio.py` | `Persona → Paciente / PersonalSalud`; `RegistroClinico → ControlVacunacion / ControlCRED / ControlGestante` |
| Orientado a objetos (agregación) | `src/dominio.py` | `Establecimiento` guarda pacientes y personal; existen aunque se desvinculen del establecimiento |
| Orientado a objetos (composición) | `src/dominio.py` | `Establecimiento` guarda sus citas; una cita no tiene sentido fuera de su establecimiento |
| Funcional | `src/reportes.py` | `filtrar_por_periodo`, `buscar_paciente_por_id` (filter); `extraer_tipos` (map); `contar_por_tipo`, `total_atenciones` (reduce) |
| Orientado a eventos | `src/controlador.py`, `app_gui.py` | `DespachadorEventos.suscribir` / `.emitir`; los botones de la GUI solo emiten eventos |
| Patrón Singleton | `src/persistencia.py` | `RepositorioLocal.__new__`: un solo archivo de datos compartido |
| Patrón Factory Method | `src/dominio.py` | `FabricaRegistroClinico.crear(...)`: decide qué subclase de RegistroClinico construir |

## 6. Resultado obtenido (última ejecución)

```
Total atenciones procesadas : 5200
Vacunación 1748 | Gestante 1736 | CRED 1716
Tiempo de generación        : ~3 ms  (límite: 2000 ms)
Criterios C1 a C5            : todos OK
Pruebas automatizadas       : 27/27 OK
VEREDICTO                   : FUNCIONA
```

## 7. Tratamiento de datos personales

- Los DNI **nunca** se almacenan en claro: se convierten en un seudónimo
  irreversible (SHA-256 con sal) antes de llegar a la capa de persistencia.
- En pantalla el documento se muestra enmascarado (`*****912`).
- **Desde la EF:** el archivo local completo —incluyendo nombres, apellidos,
  fecha de nacimiento y comunidad, no solo el DNI— se cifra con Fernet (AES
  simétrico) antes de guardarse en disco. Esto corrige una observación
  puntual del docente en la EP: antes solo el DNI estaba protegido.
- **Desde la EF:** el criterio C5 (funciona sin internet) ya no se declara
  solo por inspección del código; el script bloquea la red por software
  durante la operación central y comprueba que nada se rompe.
- Todos los nombres y documentos del archivo de datos son **ficticios**; no se
  utilizó ningún dato personal real.

## 8. Limitaciones conocidas de esta versión

- No incluye RF6 (control de medicamentos) ni RF7 (referencias), documentados
  pero fuera del alcance del módulo.
- La persistencia es un archivo cifrado, no una base de datos relacional.
- La llave de cifrado se guarda en un archivo local aparte (`datos/clave_cifrado.key`)
  por ser un prototipo académico; en un sistema en producción viviría en un
  gestor de secretos, no en el mismo disco que los datos.
- La sal de seudonimización está fijada en el código solo para que la
  demostración sea reproducible entre ejecuciones.
