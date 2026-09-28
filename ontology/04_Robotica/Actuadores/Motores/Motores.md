---
id: motores
nombre: Motores
area: Robótica
subarea: Actuadores
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — MIT OCW 2.12 / manipulation.mit.edu; TI drone ESC (slyt692, TIDA-00643, tiducf1); UToronto ECE470
tags: [spine, lote-4]
---

# Motores

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Motores
En robótica, un **motor eléctrico** es un actuador que convierte energía eléctrica en **movimiento mecánico**, normalmente rotatorio. El motor genera par y velocidad angular en su eje; mediante una transmisión, engranaje, rueda, hélice u otro elemento mecánico, ese movimiento puede convertirse en fuerzas y movimientos útiles del sistema.

Los motores eléctricos utilizados como actuadores robóticos incluyen, entre otros, motores DC con escobillas, motores BLDC, motores síncronos, servomotores y motores paso a paso. La elección depende de los requisitos de par, velocidad, precisión, dinámica, control y carga.

En un robot, el motor forma parte de una **cadena de actuación** y no debe confundirse con el actuador completo cuando existen reductoras, transmisiones, electrónica de potencia u otros elementos entre el motor y la carga. MIT señala, por ejemplo, que en robots con motores eléctricos y reductoras la relación simple entre corriente y par del motor no representa necesariamente el par disponible en la articulación debido a fricción, backlash, vibraciones y otras dinámicas de la transmisión.

---
## [INTUICION] Motores
Una cadena conceptual de actuación puede representarse como:

```text
referencia / controlador
          ↓
   electrónica de potencia
          ↓
        motor
          ↓
 transmisión / carga
          ↓
 fuerza / movimiento
```

En un robot manipulador, el controlador puede regular posición, velocidad o par dependiendo de la arquitectura. En un vehículo aéreo, el controlador puede producir demandas de fuerzas/momentos que posteriormente se convierten mediante el sistema de *control allocation* o mixer en comandos individuales de los actuadores.

En un multicóptero:

```text
controlador
     ↓
mixer / allocation
     ↓
ESC
     ↓
BLDC
     ↓
hélice
     ↓
fuerza de empuje + reacción de par
```

Esta cadena es importante porque **el comando aplicado al motor no es automáticamente equivalente a una fuerza o par conocido en la planta**.

Texas Instruments documenta explícitamente arquitecturas de drones en las que el *flight controller* controla los ESC y estos controlan los motores para producir el movimiento y el thrust requeridos.

---
## [FUNDAMENTO] Motores
### Motor como actuador

El motor genera movimiento mecánico caracterizado principalmente por:

- par $\tau$;
- velocidad angular $\omega$;
- potencia mecánica;
- sentido de giro.

La potencia mecánica rotacional es:

$$
P_{\mathrm{mech}} = \tau \omega
$$

La relación entre estas variables depende del motor y de su punto de operación.

En un motor eléctrico de imanes permanentes, bajo un modelo simplificado, el par electromagnético puede relacionarse con la corriente:

$$
\tau_{\mathrm{motor}} = K_t I
$$

MIT utiliza precisamente esta relación como modelo aproximado para motores eléctricos empleados en robots.

Sin embargo, esta relación **no implica que la corriente determine directamente el par disponible en la carga final**. Si existe una reductora o transmisión, aparecen relaciones de transmisión, eficiencia, fricción, backlash y otros efectos dinámicos.

### Electrónica de potencia

Un motor eléctrico normalmente necesita una etapa electrónica de potencia/control adecuada.

Para un BLDC utilizado en drones, el **ESC** controla las corrientes de las fases del motor. TI describe los ESC de drones como sistemas que incluyen etapa de potencia, sensado de corriente y electrónica de control del motor.

Por tanto:

**motor ≠ ESC**

y:

**comando al ESC ≠ par conocido en el eje**.

El comportamiento real depende del motor, ESC, alimentación, control, velocidad y carga.

### Motores y carga

El motor no funciona de forma aislada. El punto de operación se determina por la interacción entre el motor y la carga.

Para una aplicación robótica genérica:

```text
motor
  ↕
carga mecánica
```

Para una aplicación de propulsión:

```text
motor
  ↕
hélice + aire
```

La carga determina qué combinación de velocidad y par se alcanza para unas condiciones determinadas.

MIT señala que el diseño de motores y accionamientos debe considerar explícitamente la interacción entre las características del motor y los requisitos de rendimiento del sistema.

### Motor + transmisión

Si el motor acciona una transmisión, la salida de la transmisión no debe identificarse automáticamente con la salida directa del motor.

Conceptualmente:

$$
\omega_{\mathrm{out}} \neq \omega_{\mathrm{motor}}
$$

y, para una transmisión ideal con relación $N$ definida como reducción:

$$
\omega_{\mathrm{out}} = \frac{\omega_{\mathrm{motor}}}{N}
$$

$$
\tau_{\mathrm{out}} = N\tau_{\mathrm{motor}}
$$

En una transmisión real deben incluirse las pérdidas y otras dinámicas:

$$
\tau_{\mathrm{out}} \approx \eta N\tau_{\mathrm{motor}}
$$

donde $\eta$ representa una eficiencia equivalente bajo las hipótesis del modelo.

Estas relaciones son un **modelo idealizado**, no datos de ningún motor concreto.

### Motor + hélice

En un multicóptero, la hélice convierte el movimiento rotacional del motor en fuerzas aerodinámicas.

Por tanto:

```text
motor
  ↓
RPM / velocidad angular
  ↓
hélice
  ↓
interacción aerodinámica
  ↓
thrust + torque aerodinámico
```

El thrust **no es una propiedad intrínseca del motor aislado**.

Depende, entre otros factores, de:

- hélice;
- velocidad de giro;
- densidad del aire;
- condiciones de operación;
- configuración motor-hélice;
- alimentación;
- características del motor y ESC.

TI dispone de diseños de referencia específicos de controladores BLDC para drones, quadcopters y hélices, y sus pruebas distinguen explícitamente el comportamiento del motor sin hélice del comportamiento con hélice.

Por tanto:

**thrust de un punto de operación ≠ propiedad intrínseca del motor.**

### OP frente a capacidad intrínseca

Un motor puede tener parámetros propios o características de catálogo, pero una magnitud como:

- thrust;
- corriente;
- potencia consumida;
- RPM;

puede corresponder a un **punto de operación concreto**.

Por ejemplo:

```text
Motor X
  +
Hélice Y
  +
Tensión Z
  +
condiciones determinadas
  ↓
OP medido
  ↓
RPM / I / P / thrust
```

Ese resultado no debe convertirse automáticamente en una propiedad universal de `Motor X`.

---
## [EJEMPLO] Motores
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
planta
```

El software puede representar el comando dirigido al actuador, pero no debe afirmar automáticamente que ese comando produce un thrust concreto si no existe un modelo o dato de caracterización que establezca esa relación.

En Jarvis:

- el **tipo de motor** pertenece al conocimiento conceptual;
- el **SKU concreto** pertenece a `library/`;
- sus propiedades físicas requieren fuentes;
- un **OP** requiere condiciones explícitas;
- un resultado de banco debe mantenerse identificado como medición.

---
## [PROCEDIMIENTO] Motores
1. Definir qué movimiento se necesita: posición; velocidad; par; fuerza; thrust.
2. Definir la carga mecánica.
3. Elegir el tipo de motor adecuado.
4. Determinar si existe transmisión entre el motor y la carga.
5. Seleccionar la electrónica de potencia/control correspondiente.
6. Obtener los parámetros del SKU mediante documentación del fabricante o caracterización.
7. Definir el punto de operación de interés: tensión; corriente; velocidad; carga; condiciones ambientales; hélice, si corresponde.
8. Separar: propiedad del motor; límite; capacidad; punto de operación; medición.
9. Para propulsión, utilizar datos del **conjunto motor + hélice** cuando se necesite thrust.
10. No convertir automáticamente una especificación de catálogo en una magnitud física de operación.

---
## [USO_PROBLEMAS] Motores
- selección de actuadores;
- dimensionado de sistemas robóticos;
- control de movimiento;
- selección motor-carga;
- selección de ESC;
- selección de transmisión;
- control de velocidad;
- control de par;
- propulsión;
- análisis motor-hélice;
- estimación de potencia;
- caracterización de puntos de operación.

---
## [APLICACIONES] Motores
**Jarvis:** puente entre [[Control robótico]], [[Actuadores]], electrónica de potencia y catálogo físico `library/`.

La separación fundamental es:

```text
control
  ↓
comando
  ↓
electrónica de potencia
  ↓
motor
  ↓
carga
  ↓
respuesta física
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

- `Kv`;
- `mass_g`;
- `power_w`;
- `current_a`;
- `thrust_gf`;
- `autonomy_min`;

para ningún SKU concreto.

Esos datos pertenecen al catálogo y deben estar respaldados por fuentes o ensayos.

---
## [CONEXIONES] Motores
Hojas del hub:

- [[Actuador]]
- [[Motor eléctrico robótica]]
- [[Servo motor]]
- [[Motor paso a paso]]
- [[Motor DC]]
- [[BLDC]]
- [[ESC]]

Spine:

- [[Actuadores]]
- [[Control clásico]]
- [[Control robótico]]
- [[Electrónica de potencia]]
- [[Corriente y circuitos]]
- [[Potencia]]
- [[Torque]]
- [[Momento y rotación]]
- [[C-rate de batería]]
- [[Punto de operación vs capacidad intrínseca]]
- [[Hélice]]
- [[Empuje]]

---
## [ERRORES] Motores
- Tratar el motor como si fuera todo el actuador cuando existe una transmisión.
- Tratar thrust de un OP de banco como una propiedad intrínseca del motor.
- Usar `Kv` como si fuera thrust.
- Usar corriente máxima como si fuera corriente de operación.
- Usar potencia nominal como si fuera potencia consumida durante el vuelo.
- Confundir potencia eléctrica de entrada con potencia mecánica de salida.
- Confundir comando al ESC con par, RPM o thrust directamente conocidos.
- Confundir el motor con el conjunto motor + hélice.
- Ignorar las pérdidas y dinámicas de una transmisión.
- Inventar W, corriente, RPM o thrust de un SKU sin fuente.
- Copiar un dato de una tabla de rendimiento sin conservar las condiciones bajo las que fue medido.
- Utilizar un resultado de banco como si fuera válido para cualquier hélice, tensión o condición atmosférica.

---
## [NOTAS] Motores
Nodo revisado mediante contraste externo (Engineer + GPT cite).

Se refuerza la separación entre **motor**, **actuador completo**, **electrónica de potencia**, **transmisión**, **carga** y **punto de operación**.

La cadena control → mixer → comando → thrust no es físicamente determinista sin modelo intermedio: el controlador produce una orden; la electrónica y el actuador generan una respuesta que depende de la planta, del motor, de la carga y de las condiciones de operación.

La relación simplificada corriente–par está respaldada por MIT para motores eléctricos; MIT también advierte que puede dejar de representar el par de salida de la articulación cuando intervienen transmisiones importantes.

Para drones, TI confirma la arquitectura flight controller → ESC → motores y documenta BLDC/ESC; las pruebas de referencia distinguen motor sin hélice vs con hélice.

---
## [REFERENCIAS] Motores
- MIT OpenCourseWare — *Introduction to Robotics*, Chapter 2 (DC motors, power electronics, robot controls, PWM, BLDC):
  https://ocw.mit.edu/courses/2-12-introduction-to-robotics-fall-2005/resources/chapter2/
- MIT CSAIL — *Let's get you a robot — Position-controlled robots* (manipulation.mit.edu):
  https://manipulation.mit.edu/robot.html
- University of Toronto — *ECE470 Robot Modeling and Control*:
  https://www.control.utoronto.ca/~broucke/ece470s/ECE470.html
- University of Toronto — *ECE470S Robot Modelling and Control* (Maggiore):
  https://www.control.utoronto.ca/people/profs/maggiore/ECE470S.php
- Texas Instruments — *Motor-control considerations for electronic speed control in drones* (slyt692):
  https://www.ti.com/lit/an/slyt692/slyt692.pdf
- Texas Instruments — *TIDA-00643 — High Performance Brushless DC Drone Propeller Controller Reference Design*:
  https://www.ti.com/tool/TIDA-00643
- Texas Instruments — *TIDA-00916 — Sensorless High-Speed FOC Reference Design for Drone ESC*:
  https://www.ti.com/tool/TIDA-00916
- Texas Instruments — *High-Speed Sensorless-FOC Reference Design for Drone ESCs* (tiducf1):
  https://www.ti.com/lit/ug/tiducf1/tiducf1.pdf
- MIT Research Laboratory of Electronics — *Design of Electric Motors, Generators, and Drive Systems*:
  https://www.rle.mit.edu/design-of-electric-motors-generators-and-drive-systems-2/

---
## [ESTADO] Motores
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-4
- estado: solid
