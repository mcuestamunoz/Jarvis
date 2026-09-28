---
id: actuadores
nombre: Actuadores
area: Robótica
subarea: Actuadores
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — MIT OCW 2.12 Actuators and Drive Systems; MIT Underactuated (input constraints); PX4 control allocation / ActuatorMotors; MIT Press Autonomous Robots
tags: [spine, lote-4]
---

# Actuadores

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Actuadores
Un **actuador** es un dispositivo o conjunto de dispositivos que transforma una entrada de control y energía disponible en una **acción física** sobre un sistema, normalmente en forma de fuerza, par, desplazamiento o movimiento.

En robótica, los actuadores son los elementos mediante los cuales el sistema ejerce acciones sobre el entorno o modifica su propio movimiento. Entre ellos se encuentran motores eléctricos, servomotores, motores paso a paso, actuadores lineales, actuadores hidráulicos y neumáticos.

En un multicóptero, el sistema de propulsión de cada rotor puede considerarse un conjunto actuador formado, según el nivel de abstracción, por electrónica de potencia + motor + hélice. El motor produce movimiento rotacional; la hélice transforma ese movimiento en fuerzas y momentos aerodinámicos sobre el vehículo.

La literatura de robótica trata los actuadores y sus sistemas de accionamiento como componentes fundamentales del sistema robótico. MIT dedica un capítulo específico a **Actuators and Drive Systems** dentro de su curso *Introduction to Robotics*.

---
## [INTUICION] Actuadores
El controlador calcula una acción deseada. El **control allocation / mixer** transforma esa demanda en comandos compatibles con la geometría y los actuadores disponibles. Los actuadores convierten posteriormente esos comandos en una respuesta física.

Cadena conceptual:

$$
\text{referencia}
\rightarrow
\text{controlador}
\rightarrow
\text{control allocation}
\rightarrow
\text{actuador}
\rightarrow
\text{respuesta física}
$$

En un multicóptero:

```text
controlador
     ↓
control allocation / mixer
     ↓
ESC
     ↓
motor
     ↓
hélice
     ↓
thrust + torque
     ↓
planta
```

PX4 documenta explícitamente esta separación: los controladores producen comandos de thrust y torque, el módulo `control_allocator` los transforma en señales para motores o servos y los drivers de salida llevan esas señales al hardware.

Por tanto, **un comando de control no debe identificarse automáticamente con una magnitud física final**. El resultado depende del actuador, su configuración, sus límites y la carga.

---
## [FUNDAMENTO] Actuadores
### Actuador y planta

Un actuador forma parte de la interfaz entre el sistema de control y la planta física.

Conceptualmente:

$$
u \rightarrow \text{actuador} \rightarrow \text{fuerza/par} \rightarrow \text{planta}
$$

La relación entre la entrada $u$ y la acción física no tiene por qué ser lineal ni instantánea. Puede depender de:

- dinámica del actuador;
- saturación;
- límites eléctricos;
- límites térmicos;
- fricción;
- transmisión;
- carga;
- velocidad;
- condiciones de operación.

Por ello, el modelo de un actuador debe distinguir entre **comando**, **capacidad** y **respuesta física**.

---
### Control allocation

Cuando un sistema tiene varios actuadores, una acción deseada sobre la planta puede tener que repartirse entre ellos.

En un multicóptero, por ejemplo, el controlador puede producir una demanda de thrust y torques:

$$
\mathbf{m}
=
\begin{bmatrix}
\tau_x \\
\tau_y \\
\tau_z \\
T
\end{bmatrix}
$$

y el sistema de control allocation determina las órdenes individuales de los actuadores.

Una representación simplificada es:

$$
\mathbf{u} = \mathbf{P}\mathbf{m}
$$

donde $\mathbf{P}$ representa una matriz de asignación determinada por la geometría y las características de los actuadores.

PX4 documenta esta relación como parte de su arquitectura de **control allocation** y distingue explícitamente la matriz de asignación de los controladores y de las salidas físicas.

---
### Límites y saturación

Los actuadores tienen límites físicos. Por ejemplo:

- par máximo;
- velocidad máxima;
- fuerza máxima;
- thrust máximo;
- corriente máxima;
- tensión de operación;
- recorrido máximo de un servo.

Estos límites pueden provocar **saturación**.

Si la acción solicitada excede la capacidad disponible:

$$
u_{\mathrm{requested}} > u_{\mathrm{max}}
$$

el actuador no puede producir la acción solicitada.

Los límites de entrada de los actuadores son una restricción explícita de los sistemas dinámicos y de control; MIT Underactuated Robotics los trata como *input constraints*.

En un multicóptero, la saturación de uno o varios motores puede impedir que el sistema produzca simultáneamente el thrust y los torques solicitados. Por ello, la asignación y la gestión de saturaciones forman parte del problema de control del vehículo. PX4 documenta mecanismos relacionados con la saturación de actuadores y la asignación de control.

---
### Actuador ≠ magnitud física final

Una propiedad del actuador no debe confundirse automáticamente con la magnitud que finalmente actúa sobre la planta.

Por ejemplo:

```text
motor
  ↓
velocidad angular
  ↓
hélice
  ↓
fuerza aerodinámica
  ↓
thrust
```

Por tanto:

- un motor no es directamente un thrust;
- una orden al ESC no es directamente una fuerza;
- un límite de corriente no es automáticamente un límite de thrust;
- un comando normalizado no es necesariamente una magnitud física en N o Nm.

En PX4, la interfaz `ActuatorMotors` expresa una **normalised thrust setpoint**, que posteriormente es consumida por los drivers de protocolos ESC como PWM, DSHOT o UAVCAN. Esto demuestra la separación entre el setpoint de control y la actuación física final.

---
## [EJEMPLO] Actuadores
### Jarvis FS

Arquitectura conceptual:

```text
controller
    ↓
control allocation / mixer
    ↓
ESC
    ↓
motor
    ↓
hélice
    ↓
fuerzas + momentos
    ↓
planta 6-DoF
```

El software puede producir y transportar un comando de actuador sin afirmar que dicho comando corresponde a un thrust concreto si no existe un modelo físico o una caracterización que establezca esa relación.

En Jarvis:

- el concepto de actuador pertenece al conocimiento físico;
- el tipo de actuador pertenece a la arquitectura;
- el SKU concreto pertenece a `library/`;
- sus propiedades físicas requieren fuentes;
- la respuesta física requiere un modelo o medición;
- un resultado de banco debe conservar sus condiciones de ensayo.

---
## [PROCEDIMIENTO] Actuadores
1. Definir qué DoF o movimiento debe producirse.
2. Definir la magnitud física requerida:
   - fuerza;
   - par;
   - velocidad;
   - desplazamiento;
   - thrust.
3. Elegir el tipo de actuador adecuado.
4. Definir la cadena de accionamiento:
   - electrónica de potencia;
   - motor;
   - transmisión;
   - elemento terminal;
   - carga.
5. Determinar límites físicos mediante datasheet, modelo o ensayo.
6. Incorporar los límites y saturaciones al diseño de control.
7. Si existen varios actuadores, definir el método de control allocation.
8. Separar:
   - comando;
   - capacidad;
   - respuesta física;
   - medición.
9. Validar la relación comando → respuesta mediante modelo o evidencia experimental.
10. No convertir automáticamente un valor de catálogo en una magnitud de actuación durante la operación.

---
## [USO_PROBLEMAS] Actuadores
- Diseño de robots.
- Selección de actuadores.
- Dimensionado de sistemas de accionamiento.
- Control de movimiento.
- Control de fuerza/par.
- Propulsión.
- Control allocation.
- Análisis de saturación.
- Análisis de límites físicos.
- Modelado de la planta.

---
## [APLICACIONES] Actuadores
**Jarvis:** puente entre [[Control robótico]], [[Control allocation]], electrónica de potencia y hardware físico.

La separación fundamental es:

```text
control
  ↓
comando
  ↓
allocation
  ↓
actuador
  ↓
respuesta física
  ↓
planta
```

Para un multicóptero:

```text
control
  ↓
allocation / mixer
  ↓
ESC
  ↓
BLDC
  ↓
hélice
  ↓
thrust + torque
  ↓
planta 6-DoF
```

La nota conceptual no declara valores de:

- `mass_g`;
- `power_w`;
- `thrust_gf`;
- `autonomy_min`;

para ningún actuador concreto.

Esos datos pertenecen al catálogo físico y deben estar respaldados por fuentes o ensayos.

---
## [CONEXIONES] Actuadores
- [[Motores]]
- [[Transmisión mecánica]]
- [[Control clásico]]
- [[Control robótico]]
- [[Control allocation]]
- [[Electrónica de potencia]]
- [[Motor DC]]
- [[BLDC]]
- [[ESC]]
- [[Momento y rotación]]
- [[Dinámica]]

---
## [ERRORES] Actuadores
- Ignorar los límites físicos del actuador.
- Ignorar saturación durante el diseño del controlador.
- Confundir comando de actuador con fuerza o par físico.
- Confundir motor con actuador completo cuando existen hélice, transmisión o mecanismos intermedios.
- Inventar thrust/par de un actuador sin OP, modelo o ensayo.
- Tratar un valor normalizado de control como una magnitud física en N o Nm sin una transformación definida.
- Confundir capacidad máxima con capacidad disponible en el punto de operación.
- Suponer que todos los actuadores pueden producir cualquier combinación de fuerzas y momentos.
- Confundir control allocation con la dinámica del actuador.

---
## [NOTAS] Actuadores
Nodo revisado mediante contraste externo (Engineer + GPT cite).

Se precisa especialmente:

1. **Actuador ≠ comando de control.**
2. **Actuador ≠ necesariamente motor aislado.**
3. **Motor + hélice** puede tratarse como conjunto actuador de propulsión según el nivel de abstracción.
4. **Control allocation** es una etapa distinta del controlador y de la dinámica física.
5. Los **límites y saturaciones** forman parte del modelo de actuación.
6. Una orden normalizada no debe convertirse en N, Nm o thrust real sin una relación física definida.

Estas distinciones son coherentes con la literatura de actuadores de robótica de MIT y con la arquitectura de control allocation utilizada por PX4.

---
## [REFERENCIAS] Actuadores
- MIT OpenCourseWare — *Introduction to Robotics*, Chapter 2: Actuators and Drive Systems:
  https://ocw.mit.edu/courses/2-12-introduction-to-robotics-fall-2005/pages/lecture-notes/
- MIT Press — Correll, Hayes, Heckman & Roncone, *Introduction to Autonomous Robots: Mechanisms, Sensors, Actuators, and Algorithms*:
  https://mitpressbookstore.mit.edu/book/9780262047555
- MIT Underactuated Robotics — Input and State Constraints (límites de actuadores como restricciones de entrada):
  https://underactuated.mit.edu/intro.html
- PX4 User Guide — Control Allocation (Mixing):
  https://docs.px4.io/main/en/concept/control_allocation.html
- PX4 User Guide — ActuatorMotors (UORB; normalised thrust setpoints):
  https://docs.px4.io/main/en/msg_docs/ActuatorMotors.html
- PX4 Developer Summit 2020 — Overview of multicopter control (sensors to motors; $u = Pm$):
  https://px4.io/wp-content/uploads/2020/10/PX4-Developer-Summit-2020-Overview-of-multicopter-control-from-sensors-to-motors.pdf
- PX4 / Dronecode Forum — mixer / saturación de actuadores:
  https://discuss.px4.io/t/how-mixer-work/3886/5
- MIT CSAIL — Asada, *Introduction to Robotics* (lecture reading PDF):
  https://people.csail.mit.edu/jbarry/spring2011PR2/readings/asado.pdf

---
## [ESTADO] Actuadores
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-4
- estado: solid
