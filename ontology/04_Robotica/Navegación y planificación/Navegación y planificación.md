---
id: navegacion-y-planificacion
nombre: Navegación y planificación
area: Robótica
subarea: Navegación y planificación
nivel: base
estado: draft
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-5]
---

# Navegación y planificación

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Navegación y planificación
La **navegación** es el conjunto de métodos para estimar y seguir el estado del vehículo en el espacio (posición, velocidad, a veces actitud) respecto a un marco de referencia. La **planificación** elige trayectorias o setpoints compatibles con objetivos y restricciones.

En un multicóptero, navegación ≠ un solo sensor: suele combinar estimadores, modelos y (cuando existen) GPS, visión u odometría. **Medición ≠ estado verdadero.**

---
## [INTUICION] Navegación y planificación
“¿Dónde estoy? ¿A dónde debo ir? ¿Qué consigna mando al control?”

```text
sensores / planta
      ↓
localización / estimación de posición
      ↓
planificación / setpoints
      ↓
control (actitud / altitud / posición)
      ↓
actuadores
```

En Jarvis FS, el lazo de **posición** (C39) produce consignas de inclinación a partir de error xy — la **planta 6-DoF está fuera de `step()`**. Simular posición no valida GPS ni vuelo real.

---
## [FUNDAMENTO] Navegación y planificación
Hub:

- [[Localización]] — estimar pose / posición
- [[Planificación de movimiento]] — generar trayectoria o setpoints

Mapa FS (explain only):

| Rung | Rol conceptual |
|---|---|
| C38 | altitud / z → collective |
| C39 | posición xy → tilt |
| C40 | autonomía HOLD/LAND/GO_TO → setpoints |

Separaciones:

- **navegación estimada ≠ verdad de planta**
- **plan ≠ ejecución segura** (Safety / Authority aparte)
- **sim plant ≠ sensor real**

---
## [EJEMPLO] Navegación y planificación
Jarvis C39:

```text
posición sim (planta)
      ↓
error xy
      ↓
tilt setpoint
      ↓
C24 step / actitud
```

La nota explica el mapa; no afirma que C39 sea un filtro de navegación de vuelo.

---
## [PROCEDIMIENTO] Navegación y planificación
1. Definir marco (ENU/NED, origen).
2. Separar estimación, planificación y control.
3. Declarar qué sensores alimentan la estimación (si aplica).
4. No tratar setpoints de autonomía como “misión validada”.
5. En FS: mantener planta fuera del tick de control cuando así esté diseñado.

---
## [USO_PROBLEMAS] Navegación y planificación
Mapear C38–C40, diseñar localización, interpretar GO_TO/HOLD, evitar confundir sim con navegación real.

---
## [APLICACIONES] Navegación y planificación
**Jarvis FS:** puente conceptual hacia lazo de posición / autonomía.  
**Jarvis craft:** vocabulario de misión vs navegación — sin inventar precisión de GPS.

---
## [CONEXIONES] Navegación y planificación
- [[Localización]]
- [[Planificación de movimiento]]
- [[Control robótico]]
- [[Control clásico]]
- [[IMU]]
- [[Magnetismo]]
- [[Dinámica]]
- [[Vectores]]

---
## [ERRORES] Navegación y planificación
- Confundir setpoint de posición con posición verdadera.
- Tratar planta sim como navegación instrumentada.
- Inventar accuracy GPS/vision sin fuente.
- Mezclar planificación con Safety allow/execute.
- Asumir que C39 “es” un EKF o un GPS stack.

---
## [NOTAS] Navegación y planificación
Borrador Cursor spine-lote-5 (2026-09-28). Sustituye stub de wikilinks. Engineer + GPT cite → Cursor land `solid`.

---
## [REFERENCIAS] Navegación y planificación
(pendiente cite pass — candidatos: PX4 navigation/position control docs; MIT Underactuated / robotics navigation chapters)

---
## [ESTADO] Navegación y planificación
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-5
- estado: draft
