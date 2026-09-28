---
id: control-robotico
nombre: Control robótico
area: Robótica
subarea: Control robótico
nivel: intermedio
estado: solid
jarvis_relevance: [fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — ETH Zürich Quadrotor Control / P&S / PX4Space; NASA NTRS hierarchical control + control allocation; MIT Underactuated Robotics
tags: [spine, lote-2]
---

# Control robótico

---
## [DEFINICION] Control robótico
El **control robótico** aplica teoría de control y modelos de la planta —cinemática y dinámica del robot o vehículo— para hacer que el sistema siga referencias de movimiento, como posición, velocidad, orientación o velocidad angular, mediante actuadores y sensores.

Puede organizarse en varios niveles o lazos, desde controladores de bajo nivel asociados a actuadores, fuerzas, momentos o velocidades, hasta lazos superiores relacionados con posición, trayectoria o navegación. En arquitecturas jerárquicas, los niveles superiores pueden generar referencias para niveles inferiores.

---
## [INTUICION] Control robótico
[[Control clásico]] proporciona estructuras de realimentación como P, PI, PD y PID. El control robótico añade la relación entre:

- **qué variable** se controla en cada lazo;
- **cómo se obtiene o estima** esa variable;
- **qué modelo de planta** describe su evolución;
- **cómo se transforma la acción de control** en acciones sobre los actuadores.

En un multicóptero puede utilizarse una estructura en cascada en la que un lazo externo genera referencias para un lazo interno. Por ejemplo, un controlador de posición puede generar referencias relacionadas con actitud o empuje, mientras un controlador de actitud genera referencias de velocidad angular y un controlador de tasas genera acciones relacionadas con fuerzas/momentos.

La frecuencia de actualización puede ser diferente entre niveles: los lazos internos suelen operar a frecuencias mayores que los lazos externos porque utilizan variables que pueden medirse o estimarse con mayor frecuencia.

---
## [FUNDAMENTO] Control robótico
Ideas centrales:

- **Cascada / jerarquía de lazos:** un lazo externo puede generar una referencia para un lazo interno. La estructura concreta depende de la planta y de las variables disponibles.
- **Estimación ≠ control:** sensores y estimadores proporcionan información sobre el estado del sistema; el controlador utiliza esa información para calcular acciones. La estimación no sustituye al modelo dinámico de la planta ni a los actuadores.
- **Control allocation:** transforma una acción de control deseada en comandos para los actuadores disponibles, teniendo en cuenta su relación con las variables controladas y, cuando corresponde, sus límites físicos. En un multicóptero puede transformar un wrench deseado —fuerza y momentos— en comandos individuales de los rotores.
- **Restricciones de actuadores:** la asignación de control puede incorporar límites de los actuadores y gestionar situaciones de saturación o pérdida de efectividad.
- **Seguridad y autorización:** la generación matemática de una acción de control y la autorización para ejecutar una acción sobre hardware son funciones conceptualmente distintas.

Detalle de PID: ver [[Control clásico]].

Dinámica de planta: ver [[Dinámica]] / [[Dinámica robótica]].

---
## [EJEMPLO] Control robótico
Arquitectura conceptual para un multicóptero:

```text
referencia de posición
        ↓
control de posición
        ↓
referencia de actitud / empuje
        ↓
control de actitud
        ↓
referencia de velocidad angular
        ↓
control de tasas
        ↓
fuerza / momentos deseados
        ↓
control allocation / mixer
        ↓
comandos de actuadores
        ↓
planta
        ↓
sensores / estimador
        └──────────→ realimentación
```

Esta arquitectura es una representación conceptual: la estructura exacta, las variables controladas y las transformaciones dependen del vehículo y de la implementación. ETH Zürich documenta arquitecturas de control de quadrotor con posición → actitud → control allocation → velocidad de actuadores.

En Jarvis FS, la arquitectura C7 → C8 → rate/torque bridge → mixer → ESC stub y los lazos C38/C39 representan actualmente una arquitectura de control en simulación. Su existencia no constituye por sí misma una validación experimental del vehículo.

---
## [PROCEDIMIENTO] Control robótico
1. Definir los grados de libertad y las variables que deben controlarse.
2. Definir las referencias y su origen.
3. Identificar la planta y modelar o acotar las dinámicas relevantes.
4. Definir sensores, estimadores y frecuencia de actualización de cada variable.
5. Declarar los marcos de referencia utilizados.
6. Diseñar la jerarquía de lazos y definir qué referencia genera cada nivel para el siguiente.
7. Seleccionar la estructura de control apropiada para cada lazo.
8. Definir el control allocation entre las acciones de control deseadas y los actuadores.
9. Definir límites, saturaciones y restricciones de los actuadores.
10. Analizar y sintonizar el sistema mediante simulación y métodos apropiados.
11. Validar progresivamente el comportamiento mediante pruebas adecuadas antes de considerar los parámetros válidos para el vehículo real.
12. Mantener separadas las funciones de control, seguridad y autorización de actuación.

---
## [USO_PROBLEMAS] Control robótico
- estabilización de actitud;
- control de velocidad angular;
- seguimiento de posición;
- seguimiento de trayectorias;
- regulación de altitud;
- control de manipuladores;
- control de vehículos aéreos;
- navegación y control de movimiento;
- asignación de acciones entre múltiples actuadores;
- control de sistemas con restricciones de actuación.

---
## [APLICACIONES] Control robótico
**Jarvis:** mapa conceptual del ladder C7–C11 / C36–C40 como arquitectura de **control de movimiento aéreo en simulación**.

La arquitectura sirve para representar las relaciones entre:

- estimación del estado;
- referencias;
- lazos de control;
- dinámica de la planta;
- control allocation;
- actuadores.

No constituye por sí misma una demostración de vuelo, autonomía ni seguridad operacional. La implementación concreta continúa perteneciendo a `flight_software/` y `native/`.

---
## [CONEXIONES] Control robótico
Hojas del hub:

- [[Control de movimiento]]
- [[Control avanzado]]
- [[Control allocation]]
- [[Control en cascada]]
- [[Estimación de estado]]

Spine:

- [[Control clásico]]
- [[Dinámica]]
- [[Cinemática y dinámica]]
- [[Sensores de movimiento]]
- [[Navegación y planificación]]
- [[Actuadores]]
- [[Vectores]]
- [[Momento y rotación]]
- [[Planta dinámica]]

---
## [ERRORES] Control robótico
- Equivaler "hay un lazo funcionando en simulación" con "el vehículo vuela" o "la autonomía está validada".
- Confundir estimación del estado con control de la planta.
- Confundir control allocation con la dinámica de la planta.
- Copiar gains de un textbook o de otro vehículo y tratarlos como calibración válida del vehículo real.
- Diseñar lazos sin declarar los marcos de referencia de las variables utilizadas.
- Ignorar las frecuencias de actualización, retardos, saturaciones y límites de los actuadores.
- Confundir una referencia generada por un lazo externo con una acción directa sobre el actuador.
- Meter planificación, comportamiento de alto nivel o un LLM dentro del `step()` del controlador sin definir y validar explícitamente la arquitectura y sus interfaces.
- Confundir la generación de un comando con la autorización para ejecutar una acción sobre hardware.
- Tratar una asignación matemática de control como evidencia de que los actuadores reales pueden producir la acción solicitada.

---
## [NOTAS] Control robótico
Nodo revisado mediante contraste con literatura técnica y académica (Engineer + contraste externo).

Las arquitecturas jerárquicas y multinivel son habituales en robótica; NASA documenta arquitecturas en las que objetivos de niveles superiores se descomponen progresivamente hasta generar señales para los actuadores.

En quadrotors, ETH Zürich documenta arquitecturas cascadas donde el control de posición genera referencias para el control de actitud y los niveles inferiores generan acciones para los actuadores.

El **control allocation** debe distinguirse del controlador y de la planta. Su función es determinar cómo utilizar los actuadores disponibles para producir las acciones de control requeridas, pudiendo incorporar restricciones y saturaciones.

El control robótico no implica necesariamente PID ni una arquitectura concreta. Pueden utilizarse diferentes leyes de control y diferentes representaciones de estado según el sistema.

---
## [REFERENCIAS] Control robótico
- ETH Zürich — *Robot Dynamics: Rotary Wing UAS — Control of a Quadrotor*:
  https://ethz.ch/content/dam/ethz/special-interest/mavt/robotics-n-intelligent-systems/asl-dam/documents/lectures/robot_dynamics/2015_L8_Quadrotor_Control.pdf
- ETH Zürich — *Quadrotor P&S Exercise Sheet* — arquitectura de control en cascada y tasas de actualización:
  https://www.dfall.ethz.ch/pandsfiles/exercise02/Quadrotor_PandS_ExerciseSheet02_2023-02-22.pdf
- Roque et al. — *PX4Space: PX4 for Spacecraft and Space Robotics* (KTH/ETH; cascaded control + control allocation):
  https://pedroroque.dev/assets/pdf/PX4Space.pdf
  (ETH Research Collection handle: https://www.research-collection.ethz.ch/handle/20.500.11850/698049)
- NASA Technical Reports Server — *Hierarchical control of intelligent machines applied to space station telerobots*:
  https://ntrs.nasa.gov/citations/19890017100
- NASA Technical Reports Server — *Computationally efficient control allocation*:
  https://ntrs.nasa.gov/citations/20080004670
- NASA Technical Reports Server — *Quadratic Programming for Allocating Control Effort*:
  https://ntrs.nasa.gov/citations/20110015070
- MIT — *Underactuated Robotics*, fundamentos de dinámica y relación entre actuadores y ecuaciones de movimiento:
  https://underactuated.mit.edu/intro.html

---
## [ESTADO] Control robótico
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R3 (Cursor)
- jarvis_lote: spine-lote-2
- estado: solid
