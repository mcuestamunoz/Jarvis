---
id: control-clasico
nombre: Control clásico
area: Ingeniería
subarea: Control
nivel: intermedio
estado: solid
jarvis_relevance: [fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — UMich CTMS PID Controller Design; NASA TM-20230014863; Control Guru windup
tags: [spine, lote-1]
---

# Control clásico

---
## [DEFINICION] Control clásico
El **control clásico** estudia y diseña sistemas de control mediante relaciones entre la referencia, la salida medida, el error y la acción de control, utilizando estructuras como **P**, **PI**, **PD** y **PID**.

En un lazo de realimentación, la referencia $r(t)$ se compara con la salida medida $y(t)$ para obtener un error:

$$
e(t)=r(t)-y(t)
$$

El controlador utiliza ese error para calcular una señal de control $u(t)$ aplicada a la planta.

En sistemas de ingeniería pueden existir varios lazos anidados o en cascada. En vehículos aéreos, por ejemplo, pueden utilizarse lazos relacionados con actitud y velocidad angular, además de lazos externos para variables como altitud o posición.

---
## [INTUICION] Control clásico
Hay un valor deseado (**referencia o setpoint**) y una variable medida o estimada. La diferencia entre ambas constituye el error.

- **P:** genera una acción proporcional al error actual.
- **I:** acumula el error a lo largo del tiempo y puede reducir o eliminar el error estacionario bajo las condiciones apropiadas.
- **D:** responde a la variación temporal del error y puede aportar amortiguamiento y reducir el sobreimpulso en determinados sistemas.

Un controlador **PD** puede interpretarse, de forma intuitiva, como una acción que depende tanto de cuánto se desvía el sistema de la referencia como de cómo está cambiando esa desviación.

Los efectos concretos de P, I y D sobre tiempo de subida, sobreimpulso, tiempo de establecimiento y estabilidad dependen de la planta y de la estructura del lazo; no son reglas universales independientes de la planta.

---
## [FUNDAMENTO] Control clásico
Para un PID continuo en forma paralela:

$$
u(t)
=
K_p e(t)
+
K_i\int_0^t e(\tau)\,d\tau
+
K_d\frac{de(t)}{dt}
$$

donde:

- $K_p$: ganancia proporcional;
- $K_i$: ganancia integral;
- $K_d$: ganancia derivativa.

En el dominio de Laplace, bajo las condiciones habituales para esta representación:

$$
C(s)
=
K_p+\frac{K_i}{s}+K_ds
$$

El término integral puede eliminar el error estacionario ante determinadas referencias/perturbaciones y estructuras de planta, pero también puede introducir oscilación o aumentar el tiempo de establecimiento.

El término derivativo puede aportar amortiguamiento y reducir el sobreimpulso en determinados sistemas, pero su efecto depende de la planta y de la implementación.

La estabilidad y el comportamiento del sistema cerrado dependen conjuntamente del **controlador, la planta, la realimentación, los retardos, las saturaciones y la implementación**. Los valores de $K_p$, $K_i$ y $K_d$ no pueden deducirse de esta nota de forma universal.

Los controladores digitales requieren además considerar discretización, periodo de muestreo y forma de implementación. La derivada de señales medidas puede ser especialmente sensible al ruido, por lo que las implementaciones prácticas suelen incorporar filtrado o estructuras específicas.

En Jarvis, los valores concretos de $K_p/K_d$ del ladder son **parámetros de implementación/simulación**, no constantes físicas universales ni valores automáticamente válidos para un vehículo real.

---
## [EJEMPLO] Control clásico
En un lazo de actitud:

$$
\text{referencia de actitud}
\rightarrow
\text{error}
\rightarrow
\text{controlador}
\rightarrow
\text{comando}
\rightarrow
\text{planta}
\rightarrow
\text{medición/estimación}
\rightarrow
\text{error}
$$

La referencia puede proceder de una orden externa o de un lazo superior. La actitud medida o estimada procede de los sensores y del estimador correspondiente.

Una arquitectura de control puede utilizar un lazo externo que produzca una referencia para un lazo interno de velocidad angular. Esta estructura en cascada es habitual en sistemas de control de vuelo.

El **mixer/control allocation** convierte las acciones de control deseadas en comandos para los actuadores disponibles.

La capa de seguridad es conceptualmente distinta del controlador: que un controlador produzca un comando no implica que exista autorización para ejecutar ese comando sobre hardware.

---
## [PROCEDIMIENTO] Control clásico
1. Definir la variable controlada y su referencia.
2. Definir cómo se obtiene la medición o estimación y en qué marco de referencia está expresada.
3. Definir la planta y las dinámicas relevantes.
4. Elegir la estructura de control adecuada (P, PI, PD, PID u otra).
5. Determinar las restricciones físicas y de actuación, incluidas saturaciones y límites.
6. Seleccionar un método de sintonía apropiado para la planta y los requisitos.
7. Evaluar el comportamiento mediante análisis y/o simulación.
8. Verificar estabilidad, error estacionario, sobreimpulso, tiempo de establecimiento, sensibilidad a perturbaciones y comportamiento ante saturación.
9. Validar los parámetros mediante pruebas apropiadas antes de considerarlos válidos para hardware real.
10. Mantener separadas las funciones de control, seguridad y autorización de actuación.

---
## [USO_PROBLEMAS] Control clásico
Diseño y análisis de:

- lazos de realimentación;
- seguimiento de referencias;
- rechazo de perturbaciones;
- regulación de variables;
- controladores P, PI, PD y PID;
- análisis de estabilidad y respuesta temporal;
- sintonía de controladores;
- sistemas SISO y estructuras de control en cascada.

---
## [APLICACIONES] Control clásico
**Jarvis FS:** marco conceptual para:

- C8: control PD de actitud;
- C38/C39: lazos de altitud/posición en simulación;
- separación entre referencia, estimación, controlador, planta y actuadores;
- explicación de por qué los gains utilizados en simulación son parámetros de diseño y no propiedades físicas universales.

Esta nota no sustituye la especificación ni implementación de `controller.py` / `controller.hpp`.

---
## [CONEXIONES] Control clásico
Hojas del hub:

- [[Control proporcional]]
- [[Control integral]]
- [[Control derivativo]]
- [[Control PID]]
- [[Error de control]]
- [[Realimentación]]
- [[Saturación]]

Spine:

- [[Control]]
- [[Vectores]]
- [[Dinámica]]
- [[Cinemática]]
- [[Control robótico]]
- [[Sensores de movimiento]]
- [[Planta dinámica]]
- [[Estabilidad]]
- [[Marcos de referencia]]

---
## [ERRORES] Control clásico
- Tomar $K_p$, $K_i$ o $K_d$ de esta nota o de un textbook e inyectarlos en FS como si fueran una calibración universal del vehículo.
- Suponer que un PID garantiza estabilidad independientemente de la planta.
- Interpretar "integral elimina el error estacionario" como una garantía universal sin considerar la planta, la referencia, las perturbaciones, la saturación y la implementación.
- Tratar la derivada como una operación ideal sobre una señal medida sin considerar ruido, muestreo y filtrado.
- Ignorar la saturación del actuador y sus efectos sobre el controlador, incluido el posible integrator windup.
- Confundir el controlador con la planta.
- Confundir que el lazo esté implementado o simulado con demostrar que el vehículo vuela correctamente.
- Confundir la generación de un comando con autorización para ejecutar una acción sobre hardware.
- Utilizar gains de simulación como si fueran valores validados experimentalmente.
- Creer que un PID autoriza autonomía o proporciona por sí mismo masa, empuje, potencia u otros parámetros físicos.

---
## [NOTAS] Control clásico
Nodo revisado mediante contraste con referencias académicas y técnicas (Engineer + contraste externo).

La forma PID utilizada corresponde a la formulación continua paralela estándar:

$$
C(s)=K_p+\frac{K_i}{s}+K_ds
$$

Los efectos cualitativos atribuidos a P, I y D son tendencias dependientes de la planta y no leyes independientes del sistema.

El control clásico no implica necesariamente que todo sistema utilice un único PID. Pueden utilizarse controladores P, PI o PD, así como estructuras en cascada y otras técnicas de control. La complejidad debe corresponder a los requisitos del sistema.

Para un sistema físico real, la selección de gains requiere conocimiento de la planta y validación. La simulación puede aportar evidencia de comportamiento, pero no constituye por sí sola una validación experimental del vehículo real.

La separación entre controlador, planta, asignación de control y seguridad es relevante para Jarvis: el controlador calcula acciones dentro del modelo de control; la autorización para actuar sobre hardware pertenece a una capa distinta.

---
## [REFERENCIAS] Control clásico
- University of Michigan — Control Tutorials for MATLAB and Simulink, *Introduction: PID Controller Design*:
  https://ctms.engin.umich.edu/CTMS/?example=Introduction&section=ControlPID
- University of Michigan — Control Tutorials for MATLAB and Simulink, *Aircraft Pitch: PID Controller Design*:
  https://ctms.engin.umich.edu/CTMS/?example=AircraftPitch&section=ControlPID
- University of Michigan — Control Tutorials for MATLAB and Simulink, *Motor Speed: PID Controller Design*:
  https://ctms.engin.umich.edu/CTMS/?example=MotorSpeed&section=ControlPID
- NASA TM-20230014863 — Wu & Litt, *Reinforcement Learning Approach to Flight Control Allocation With Distributed Electric Propulsion* (studies flight-control allocation for the SUSAN aircraft concept):
  https://ntrs.nasa.gov/api/citations/20230014863/downloads/TM-20230014863.pdf
- Control Guru — *Integral (Reset) Windup, Jacketing Logic and the Velocity PI Form*:
  https://controlguru.com/integral-reset-windup-jacketing-logic-and-the-velocity-pi-form/

---
## [ESTADO] Control clásico
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R2 (Cursor)
- jarvis_lote: spine-lote-1
- estado: solid
