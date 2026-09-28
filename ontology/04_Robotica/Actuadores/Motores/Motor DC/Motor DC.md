---
id: motor-dc
nombre: Motor DC
area: Robótica
subarea: Actuadores / Motores
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — TI BLDC fundamentals / ESC FOC; Analog Devices motor control + TMC2300 Ke/Kt note
tags: [spine, lote-4]
---

# Motor DC

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Motor DC
Un **motor de corriente continua (DC)** convierte energía eléctrica en **energía mecánica**, produciendo par y movimiento de rotación en su eje.

Debe distinguirse entre un **motor DC con escobillas (brushed)** y un **motor DC sin escobillas (BLDC)**. En un motor brushed la conmutación se realiza mecánicamente mediante escobillas y conmutador. En un BLDC la conmutación es electrónica y requiere una electrónica de potencia adecuada, normalmente mediante un inversor/ESC.

En aplicaciones de drones, los motores de propulsión son habitualmente **BLDC**, generalmente de tipo *outrunner*, y trabajan junto con un **ESC** que conmuta las fases del motor.

La relación entre tensión, corriente, velocidad angular y par **no queda determinada por un único parámetro de catálogo**. Depende de las constantes eléctricas y mecánicas del motor, del controlador, de la alimentación y de la carga conectada al eje.

---
## [INTUICION] Motor DC
En un motor eléctrico, la corriente que circula por los devanados produce fuerzas electromagnéticas que generan **par**.

Para un motor de imanes permanentes, en un modelo ideal simplificado:

$$
\tau = K_t I
$$

donde:

- $\tau$ es el par electromagnético;
- $K_t$ es la constante de par;
- $I$ representa la corriente relevante para el modelo.

La relación exacta depende de la definición de corriente y de la topología/control del motor. En un BLDC trifásico, el par electromagnético depende de las corrientes de fase y de las fuerzas contraelectromotrices correspondientes.

Al aumentar la velocidad aparece una **fuerza contraelectromotriz (back-EMF)** que se opone a la tensión aplicada y que aumenta con la velocidad del rotor. Esto limita la corriente disponible y modifica el punto de funcionamiento.

Por tanto:

**más corriente disponible → potencialmente más par**, pero **la corriente por sí sola no determina el thrust** de una hélice.

En un dron:

$$
\text{batería} \rightarrow \text{ESC} \rightarrow \text{motor} \rightarrow \text{hélice} \rightarrow \text{empuje}
$$

El empuje depende del conjunto **motor + hélice + condiciones de operación**, no del motor aislado.

---
## [FUNDAMENTO] Motor DC
### Conversión electromecánica

Un motor eléctrico convierte potencia eléctrica en potencia mecánica, con pérdidas en los elementos eléctricos, magnéticos, mecánicos y térmicos.

La potencia mecánica rotacional se expresa como:

$$
P_{\mathrm{mech}} = \tau \omega
$$

donde:

- $P_{\mathrm{mech}}$ es la potencia mecánica;
- $\tau$ es el par;
- $\omega$ es la velocidad angular.

La potencia eléctrica de entrada, en un modelo simplificado de corriente continua, es:

$$
P_{\mathrm{elec}} = VI
$$

La eficiencia del motor puede expresarse como:

$$
\eta = \frac{P_{\mathrm{mech}}}{P_{\mathrm{elec}}}
$$

siempre que las potencias utilizadas correspondan al mismo punto de operación y sistema de referencia.

### Back-EMF

En un motor en funcionamiento aparece una tensión inducida que se opone a la tensión aplicada. Para un modelo simplificado:

$$
E = K_e \omega
$$

donde $E$ es la back-EMF y $K_e$ la constante correspondiente.

Para un modelo eléctrico simplificado de motor DC:

$$
V = RI + L\frac{dI}{dt} + K_e\omega
$$

La ecuación muestra que la corriente depende de la tensión aplicada, la resistencia, la inductancia y la velocidad del motor. En un BLDC trifásico la formulación exacta se realiza por fases y depende de la conmutación y de la forma de la back-EMF.

### Relación entre par y corriente

En unidades SI, para un modelo ideal de motor de imanes permanentes, la constante de par y la constante de back-EMF están relacionadas numéricamente cuando se utilizan las unidades compatibles:

$$
K_t = K_e
$$

Esta equivalencia debe utilizarse con cuidado porque las hojas de datos pueden definir las constantes respecto a diferentes magnitudes eléctricas (fase, línea-línea, RMS, pico, etc.).

### BLDC y ESC

Un BLDC no utiliza escobillas ni conmutador mecánico. La corriente de las fases debe ser conmutada electrónicamente.

El ESC contiene la electrónica de potencia necesaria para aplicar las tensiones/corrientes apropiadas a las fases del motor. Dependiendo de la arquitectura puede utilizar conmutación trapezoidal, sinusoidal o técnicas como FOC.

Por tanto:

**ESC ≠ motor**

y

**PWM/DShot ≠ par directamente medido**.

El comando enviado al ESC es una entrada de control; el par resultante depende del motor, del ESC, de la alimentación, de la velocidad y de la carga.

### Motor + hélice

En un multicóptero, el motor normalmente acciona una hélice.

El punto de operación resulta de la interacción entre:

- motor;
- ESC;
- batería;
- hélice;
- velocidad de giro;
- condiciones atmosféricas;
- carga aerodinámica.

Por ello, un valor de **Kv**, una corriente máxima o una potencia nominal de catálogo **no constituyen por sí mismos un valor de thrust**.

El thrust debe proceder de una medición, una curva de fabricante válida o un modelo aerodinámico explícitamente justificado.

---
## [EJEMPLO] Motor DC
En Jarvis, el concepto `[[Motor DC]]` representa el actuador electromecánico.

Para un multicóptero:

```text
Battery
   ↓
ESC
   ↓
BLDC
   ↓
Propeller
   ↓
Aerodynamic thrust
```

El software de control puede producir una orden destinada al ESC, pero esa orden no debe interpretarse automáticamente como:

- un par conocido;
- una RPM conocida;
- una potencia conocida;
- un thrust conocido.

Esas magnitudes requieren un modelo o datos de caracterización apropiados.

En Jarvis, el **SKU concreto** y sus propiedades físicas pertenecen a `library/` y deben estar respaldados por fuentes o mediciones.

---
## [PROCEDIMIENTO] Motor DC
1. Declarar el tipo de motor: **brushed DC, BLDC u otro**.
2. Si es BLDC, declarar el tipo de control/conmutación y el ESC utilizado.
3. Declarar la carga conectada al eje: hélice, reductora, rueda, etc.
4. Obtener del fabricante los parámetros relevantes del SKU: Kv; resistencia; corriente; masa; tensión/rango; potencia; constantes de motor; curvas de rendimiento cuando estén disponibles.
5. Distinguir claramente entre: especificación de catálogo; límite; condición nominal; punto de operación; medición de banco.
6. Para un sistema motor-hélice, utilizar datos de rendimiento del conjunto cuando se necesite thrust o potencia operacional.
7. No convertir directamente Kv, corriente máxima o potencia nominal en thrust.
8. Si se utiliza un modelo matemático, declarar sus hipótesis y el alcance de validez.

---
## [USO_PROBLEMAS] Motor DC
- selección de actuadores;
- dimensionado de sistemas de propulsión;
- control de velocidad;
- control de par;
- selección de ESC;
- análisis motor-hélice;
- estimación de potencia;
- caracterización de puntos de operación;
- diseño de sistemas robóticos.

---
## [APLICACIONES] Motor DC
**Jarvis:** vocabulario base para el subsistema de actuadores y para la cadena:

```text
control
  ↓
ESC
  ↓
motor
  ↓
hélice / carga
  ↓
fuerza y momento
  ↓
planta
```

La nota no sustituye las filas de `library/motores`, `library/esc` ni los datos de ensayo de banco.

En el modelo de Jarvis debe mantenerse la separación entre:

**propiedad intrínseca del motor → capacidad del sistema → punto de operación → magnitud medida.**

---
## [CONEXIONES] Motor DC
- [[Motores]]
- [[Actuadores]]
- [[BLDC]]
- [[ESC]]
- [[Electrónica de potencia]]
- [[Corriente y circuitos]]
- [[Potencia]]
- [[Velocidad angular]]
- [[Torque]]
- [[Momento y rotación]]
- [[Punto de operación vs capacidad intrínseca]]
- [[Hélice]]
- [[Empuje]]

---
## [ERRORES] Motor DC
- Usar **Kv como si fuera thrust**.
- Usar corriente máxima como si fuera corriente de operación.
- Usar potencia nominal como si fuera potencia consumida durante el vuelo.
- Confundir potencia eléctrica de entrada con potencia mecánica de salida.
- Confundir comando PWM/DShot con par o RPM directamente conocidos.
- Confundir el motor aislado con el sistema motor + hélice.
- Inventar corriente, potencia, RPM o thrust de un SKU sin fuente.
- Aplicar una constante de par o back-EMF sin comprobar cómo está definida por el fabricante.
- Ignorar la back-EMF al analizar el funcionamiento a velocidad elevada.
- Asumir que un motor puede entregar indefinidamente su corriente o potencia máxima.
- Tratar un punto de operación medido como si fuera una propiedad intrínseca del motor.

---
## [NOTAS] Motor DC
Nodo revisado mediante contraste externo (Engineer + GPT cite).

La distinción entre **motor DC brushed**, **BLDC**, **ESC**, **motor aislado** y **sistema de propulsión motor-hélice** debe mantenerse.

La **back-EMF** explica por qué la relación entre tensión, corriente y velocidad no puede reducirse a "más corriente = más velocidad" ni a un único parámetro como Kv.

**Kv no es thrust**: Kv está relacionado con la constante de back-EMF/velocidad; el thrust depende además de la hélice y del punto de operación. Jarvis debe evitar derivar thrust directamente de Kv sin un modelo de propulsión validado.

---
## [REFERENCIAS] Motor DC
- Texas Instruments — *BLDC Motor Fundamentals*:
  https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/38/5086.00885a.pdf
- Texas Instruments — *Commutation / Electromagnetic Torque Ripple in BLDC Motors*:
  https://www.ti.com/document-viewer/lit/html/SSZTBM0
- Texas Instruments — *Understanding BLDC Motor Control*:
  https://www.ti.com/document-viewer/lit/html/SSZTBP2
- Texas Instruments — *High-Speed Sensorless-FOC Reference Design for Drone ESCs*:
  https://www.ti.com/lit/ug/tiducf1/tiducf1.pdf
- Analog Devices — *Guide to Industrial Motor Control System*:
  https://www.analog.com/en/resources/technical-articles/guide-to-industrial-motor-control-system--maxim-integrated.html
- Analog Devices — *Brushless DC Motors Introduction for Next-Generation Missile Actuation Systems*:
  https://www.analog.com/en/resources/technical-articles/brushless-dc-motors-introduction-for-next-generation-missile-actuation-systems-outline.html
- Analog Devices — *High Efficiency, Low Cost, Sensorless Motor Control*:
  https://www.analog.com/media/en/technical-documentation/technical-articles/63171300ADI_Tech_Paper.pdf
- Analog Devices — *TMC2300 Datasheet — Understanding the Back EMF Constant of a Motor*:
  https://www.analog.com/media/en/technical-documentation/data-sheets/TMC2300_datasheet_rev1.08.pdf

---
## [ESTADO] Motor DC
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-4
- estado: solid
