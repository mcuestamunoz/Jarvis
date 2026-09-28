---
id: navegacion-y-planificacion
nombre: Navegación y planificación
area: Robótica
subarea: Navegación y planificación
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — PX4 controller diagrams / EKF2 / trajectory setpoints; Nav2 navigation concepts; MIT Underactuated (estimation, trajopt, sampling planning)
tags: [spine, lote-5]
---

# Navegación y planificación

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Navegación y planificación
La **navegación** comprende los métodos empleados para determinar y mantener una representación del estado y la posición del vehículo respecto a uno o más marcos de referencia, normalmente mediante sensores, odometría, modelos y estimación de estado.

La **planificación** determina una trayectoria, camino, secuencia de estados o conjunto de consignas que permite alcanzar un objetivo respetando las restricciones relevantes del sistema.

En robótica, **localización/estimación, planificación y control son funciones relacionadas pero distintas**. Un sistema de navegación puede integrar estimación de estado, representación del entorno, planificación y control, pero estas funciones no deben confundirse conceptualmente. Nav2, por ejemplo, separa explícitamente *state estimation*, representación del entorno, *planning* y *control*.

En un multicóptero, la navegación no depende necesariamente de un único sensor: puede utilizar GNSS/GPS, IMU, magnetómetro, barómetro, visión, odometría u otras fuentes mediante un estimador. PX4, por ejemplo, utiliza EKF2 para estimar actitud, posición, velocidad, sesgos de IMU y otros estados a partir de múltiples observaciones.

**Medición/observación ≠ estado verdadero.**

---
## [INTUICION] Navegación y planificación
“¿Dónde estoy? ¿Adónde quiero ir? ¿Qué trayectoria o consigna necesito generar? ¿Cómo hago que el vehículo la siga?”

```text
sensores / observaciones
          ↓
   estimación de estado
          ↓
   planificación / trayectoria
          ↓
   setpoints de control
          ↓
 control de posición / actitud
          ↓
       actuadores
          ↓
        planta
```

Esta separación es coherente con arquitecturas robóticas reales. En PX4, por ejemplo, el controlador de posición recibe estimaciones y genera consignas para niveles inferiores; su documentación describe una arquitectura de control multicóptero en cascada.

La planificación no tiene por qué producir directamente comandos de actuador. Puede producir una trayectoria o *setpoints* de posición, velocidad y aceleración que posteriormente son seguidos por controladores de nivel inferior. PX4 documenta explícitamente esta separación mediante su *trajectory generator* y sus *position/velocity controllers*.

---
## [FUNDAMENTO] Navegación y planificación
Hub:

- [[Localización]] — estimar posición o pose a partir de observaciones.
- [[Estimación de estado]] — obtener una representación estimada del estado dinámico del sistema.
- [[Planificación de movimiento]] — determinar caminos o trayectorias hacia un objetivo.
- [[Control robótico]] — hacer que el sistema siga las referencias generadas.

### Navegación / estimación

La navegación requiere una representación explícita del **marco de referencia** y de las transformaciones entre marcos.

En sistemas robóticos como ROS/Nav2 se separan, por ejemplo, los marcos `map`, `odom` y `base_link`, y la localización/SLAM y la odometría proporcionan diferentes relaciones entre ellos.

En aeronaves, PX4 utiliza el marco local NED en numerosos mensajes y controladores; sus mensajes de *position setpoint*, por ejemplo, especifican velocidades locales en NED.

### Planificación

La planificación de movimiento puede formularse como la búsqueda de un camino, una trayectoria temporal o una secuencia de referencias que satisfaga objetivos y restricciones.

No existe un único algoritmo universal de planificación. En robótica se utilizan, entre otros:

- planificación basada en grafos;
- métodos de muestreo;
- optimización de trayectorias;
- planificación basada en modelos dinámicos;
- MPC y otros métodos de planificación/control integrados.

MIT Underactuated Robotics distingue explícitamente planificación basada en muestreo, optimización de trayectorias y planificación con realimentación, mostrando que planificación y control pueden estar estrechamente acoplados en determinadas arquitecturas.

### Navegación ≠ sensor

Un GPS/GNSS proporciona una observación de posición; una IMU proporciona observaciones inerciales; una cámara puede proporcionar información visual. El estado utilizado por el controlador puede ser el resultado de combinar estas observaciones mediante un estimador.

Por ejemplo, PX4 documenta EKF2 como estimador de actitud, posición, velocidad, viento y sesgos de IMU, entre otros estados.

### Mapa conceptual FS

| Rung | Rol conceptual |
|---|---|
| C38 | control de altitud / $z$ → referencia de thrust/colectivo |
| C39 | control de posición $xy$ → referencias de movimiento/actitud |
| C40 | autonomía `HOLD` / `LAND` / `GO_TO` → comportamiento y setpoints |

Estos rungs deben interpretarse como **mapa conceptual de Jarvis**, no como equivalentes universales de componentes de navegación de un autopiloto real.

---
## [EJEMPLO] Navegación y planificación
Jarvis C39:

```text
posición estimada / posición de planta sim
              ↓
          error XY
              ↓
      referencia de movimiento
              ↓
       control de posición
              ↓
    referencia de actitud/thrust
              ↓
       control de actitud
```

En una implementación real, la cadena exacta depende de la arquitectura de control. PX4, por ejemplo, documenta que el controlador de posición puede producir un vector de thrust y que la aceleración deseada puede transformarse en una referencia de actitud y thrust colectivo.

En Jarvis, la planta simulada puede proporcionar directamente el estado utilizado por C39. Eso **no convierte C39 en un sistema de navegación real**, ni demuestra que GPS, visión, odometría o un estimador físico funcionen en hardware.

---
## [PROCEDIMIENTO] Navegación y planificación
1. Definir el objetivo de navegación y el marco de referencia.
2. Identificar qué observaciones/sensores alimentan la estimación.
3. Separar observaciones, estimación de estado y estado de la planta.
4. Definir la representación de la trayectoria o de los setpoints.
5. Elegir el método de planificación compatible con el vehículo y las restricciones.
6. Pasar las referencias al controlador correspondiente.
7. Verificar saturaciones, límites dinámicos y restricciones de seguridad.
8. Validar progresivamente en simulación, banco y hardware según corresponda.
9. No presentar una trayectoria o setpoint simulado como evidencia de navegación física.
10. No presentar una estimación como estado verdadero sin declarar su modelo, sensores y supuestos.

---
## [USO_PROBLEMAS] Navegación y planificación
Localización, estimación de estado, seguimiento de trayectorias, *waypoints*, *GO_TO*, *HOLD*, planificación de movimiento y coordinación entre navegación y control.

---
## [APLICACIONES] Navegación y planificación
**Jarvis FS:** puente conceptual entre estimación de estado, control de posición y autonomía.

**Jarvis craft:** vocabulario para separar misión, navegación, planificación y control sin inventar precisión de GPS, visión u otros sensores.

---
## [CONEXIONES] Navegación y planificación
- [[Localización]]
- [[Estimación de estado]]
- [[Planificación de movimiento]]
- [[Control robótico]]
- [[Control clásico]]
- [[IMU]]
- [[Magnetismo]]
- [[Dinámica]]
- [[Vectores]]
- [[Marcos de referencia]]

---
## [ERRORES] Navegación y planificación
- Confundir una observación de sensor con el estado verdadero.
- Confundir posición estimada con posición conocida exactamente.
- Confundir planificación con control.
- Confundir un setpoint de posición con una trayectoria ejecutada.
- Tratar una planta simulada como si fuera navegación instrumentada.
- Inventar precisión de GPS/GNSS, visión u odometría sin fuente.
- Asumir que C39 es un EKF, un GPS stack o un sistema de localización.
- Confundir el plan de misión con la autorización de actuación.
- Asumir que todos los sistemas de navegación utilizan la misma arquitectura o los mismos sensores.
- Confundir planificación de trayectoria con control de trayectoria.

---
## [NOTAS] Navegación y planificación
Nodo revisado mediante contraste externo (Engineer + GPT cite).

Se precisan tres puntos:

1. **Navegación no debe definirse únicamente como “estimar y seguir el estado”**: la literatura y arquitecturas robóticas separan estimación/localización, planificación y control, aunque algunos sistemas los integren dentro de un *navigation stack*.
2. **Planificación no equivale necesariamente a generar setpoints directamente**: puede generar caminos, trayectorias o referencias que posteriormente son transformadas por otros módulos.
3. **C39 → tilt** es válido como descripción del diseño conceptual de Jarvis, pero no debe presentarse como arquitectura universal. En PX4, el controlador de posición genera un vector de thrust y este se transforma en referencias de actitud/thrust según la arquitectura concreta.

---
## [REFERENCIAS] Navegación y planificación
- PX4 — Controller Diagrams (arquitectura multicóptero en cascada):
  https://docs.px4.io/main/en/flight_stack/controller_diagrams.html
- PX4 — Modules Reference: Controller:
  https://docs.px4.io/main/en/modules/modules_controller.html
- PX4 — Multicopter Setpoint Tuning (Trajectory Generator):
  https://docs.px4.io/main/en/config_mc/mc_trajectory_tuning.html
- PX4 — Switching State Estimators:
  https://docs.px4.io/main/en/advanced/switching_state_estimators.html
- PX4 — Using PX4's Navigation Filter (EKF2):
  https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html
- PX4 — PositionSetpoint (UORB; NED / local setpoints):
  https://docs.px4.io/main/en/msg_docs/PositionSetpoint.html
- Nav2 — Navigation Concepts:
  https://docs.nav2.org/concepts/
- Nav2 — State Estimation:
  https://docs.nav2.org/rolling/getting_started/navigation_concepts/state_estimation/
- MIT Underactuated Robotics — State Estimation:
  https://underactuated.mit.edu/state_estimation.html
- MIT Underactuated Robotics — Trajectory Optimization:
  https://underactuated.mit.edu/trajopt.html
- MIT Underactuated Robotics — Sampling-based Motion Planning:
  https://underactuated.mit.edu/planning.html

---
## [ESTADO] Navegación y planificación
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-5
- estado: solid
