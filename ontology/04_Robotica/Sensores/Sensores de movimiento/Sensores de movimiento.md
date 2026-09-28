---
id: sensores-de-movimiento
nombre: Sensores de movimiento
area: Robótica
subarea: Sensores
nivel: base
estado: solid
jarvis_relevance: [fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — NASA NTRS attitude/IMU; Analog Devices MEMS FAQs; TDK ICM-42688-P datasheet
tags: [spine, lote-2]
---

# Sensores de movimiento

---
## [DEFINICION] Sensores de movimiento
Los **sensores de movimiento** miden magnitudes relacionadas con el movimiento y la orientación de un cuerpo, como **aceleración específica**, **velocidad angular** y, en sensores complementarios, campo magnético, posición, velocidad o desplazamiento.

En robótica móvil y vehículos aéreos, una **IMU** suele integrar un acelerómetro y un giroscopio de varios ejes. Algunas IMU o unidades de navegación incorporan además magnetómetro u otros sensores.

Estos sensores proporcionan mediciones que pueden utilizarse junto con modelos y algoritmos de estimación para obtener variables de estado como orientación, velocidad o posición. La medición de un sensor no debe confundirse automáticamente con el estado físico verdadero del vehículo.

---
## [INTUICION] Sensores de movimiento
El controlador normalmente no observa directamente todas las variables físicas del vehículo: recibe **mediciones** y/o **estimaciones**.

Un acelerómetro MEMS mide aceleración específica y puede proporcionar información sobre la dirección de la gravedad cuando las aceleraciones no gravitatorias son suficientemente pequeñas. Durante movimiento dinámico, vibraciones o maniobras, esa interpretación deja de ser directamente válida y debe utilizarse un modelo de estimación adecuado.

Un giroscopio mide **velocidad angular**. La integración de esta medición permite obtener cambios de orientación, pero los errores de bias y ruido se acumulan con el tiempo y producen deriva.

El magnetómetro mide el campo magnético y puede aportar una referencia de orientación respecto al campo magnético terrestre, especialmente útil para estimar heading/yaw. Sin embargo, las perturbaciones magnéticas locales pueden degradar esta referencia.

Por ello, la orientación suele estimarse mediante **fusión sensorial**, combinando información de diferentes sensores y un modelo de movimiento.

---
## [FUNDAMENTO] Sensores de movimiento
Mapa conceptual:

| Sensor | Magnitud típica | Notas |
|---|---|---|
| [[Acelerómetro]] | aceleración específica | Puede proporcionar referencia respecto a gravedad en condiciones adecuadas; presenta bias, ruido y sensibilidad a aceleraciones no gravitatorias. |
| [[Giroscopio]] | velocidad angular | La integración permite estimar cambios de orientación, pero el bias y el ruido producen deriva acumulativa. |
| [[IMU]] | acelerómetro + giroscopio | Conjunto inercial; requiere conocer ejes, orientación del sensor y convenciones de marco. |
| [[Magnetómetro]] | campo magnético | Puede proporcionar referencia de heading; sensible a perturbaciones magnéticas. |
| [[Encoder]] | posición/ángulo de eje | Mide desplazamiento o posición angular de un eje; habitual en articulaciones y sistemas con ruedas. |
| [[Velocidad angular]] | $\boldsymbol{\omega}$ | Puede ser medida directamente por un giroscopio o estimada mediante un algoritmo de estado. |

Una IMU de 6 ejes está formada habitualmente por un acelerómetro triaxial y un giroscopio triaxial. Algunas arquitecturas añaden un magnetómetro, pero **un magnetómetro no forma parte necesariamente de una IMU de 6 ejes**.

El filtrado puede reducir determinados componentes de ruido, pero **filtrar no equivale a calibrar** ni sustituye necesariamente un modelo explícito de bias, escala, alineamiento y otros errores del sensor.

En una estimación de actitud, un esquema puede combinar:

- integración de velocidad angular del giroscopio;
- referencia gravitacional procedente del acelerómetro;
- referencia magnética procedente del magnetómetro;
- un modelo dinámico;
- un filtro complementario, EKF u otro estimador.

La elección depende de los requisitos y de las hipótesis sobre el sistema.

---
## [EJEMPLO] Sensores de movimiento
En Jarvis:

`SimulatedImuHal` / filtros (C6) → attitude (C7).

La cadena representa medición simulada → procesamiento/estimación → actitud estimada.

El flujo SPI scripted + probe (C32–C34) y el driver basado en el datasheet del ICM-42688-P sobre `ScriptedSpi` (C42) permiten representar el comportamiento de la interfaz y del dispositivo en el entorno correspondiente, pero **no demuestran que SPI1 esté físicamente conectado ni que exista comunicación real sobre el hardware**.

El ICM-42688-P real soporta interfaces SPI de 3 y 4 hilos y dispone de registros accesibles mediante dicha interfaz.

Por tanto:

**identificación/configuración simulada ≠ comunicación física real ≠ calibración ≠ validación de vuelo.**

Un magnetómetro simulado (C37) puede proporcionar una referencia magnética para el algoritmo de estimación de yaw, pero su existencia en simulación no demuestra que exista una referencia magnética válida en el hardware.

---
## [PROCEDIMIENTO] Sensores de movimiento
1. Declarar qué magnitud se necesita: aceleración específica, velocidad angular, campo magnético, posición, velocidad, etc.
2. Determinar si la magnitud se mide directamente o se estima.
3. Elegir el sensor y la arquitectura de sensado adecuados.
4. Declarar la orientación de los ejes del sensor y su relación con el marco del vehículo.
5. Caracterizar, cuando sea necesario, bias, ruido, escala, alineamiento, saturación y dependencia con temperatura.
6. Obtener estos parámetros de un datasheet, calibración o ensayo; no inventarlos.
7. Aplicar el procesamiento o filtrado apropiado.
8. Si se necesita una variable de estado, definir el estimador y sus fuentes de observación.
9. Validar que las mediciones y estimaciones son coherentes con el rango dinámico y las condiciones de operación.
10. Separar explícitamente simulación, interfaz emulada, comunicación física, calibración y validación experimental.

---
## [USO_PROBLEMAS] Sensores de movimiento
- selección de IMU;
- selección y caracterización de acelerómetros;
- selección y caracterización de giroscopios;
- estimación de actitud;
- fusión sensorial;
- diagnóstico de bias y deriva;
- análisis de ruido;
- calibración de sensores;
- diseño de estimadores;
- diagnóstico de interfaces de sensores;
- navegación inercial.

---
## [APLICACIONES] Sensores de movimiento
**Jarvis FS:** vocabulario y fundamento para C3/C6/C7/C37/C42.

La nota establece la separación entre:

**sensor → medición → filtrado/estimación → estado → control**

y entre:

**simulación → interfaz emulada → hardware físico → calibración → validación.**

Las hojas `[[IMU]]`, `[[Giroscopio]]`, `[[Acelerómetro]]` y `[[Magnetómetro]]` pueden desarrollarse posteriormente como nodos especializados.

---
## [CONEXIONES] Sensores de movimiento
Hojas del hub:

- [[Acelerómetro]]
- [[Giroscopio]]
- [[IMU]]
- [[Magnetómetro]]
- [[Encoder]]
- [[Velocidad angular]]
- [[Estimación de estado]]
- [[Fusión sensorial]]

Spine:

- [[Vectores]]
- [[Control clásico]]
- [[Control robótico]]
- [[Dinámica]]
- [[Magnetismo]]
- [[Navegación y planificación]]
- [[Marcos de referencia]]

---
## [ERRORES] Sensores de movimiento
- Tratar una lectura simulada como calibración de hardware real.
- Confundir aceleración específica medida por un acelerómetro con aceleración lineal del cuerpo sin considerar la contribución gravitatoria y la convención utilizada.
- Tratar el acelerómetro como un inclinómetro válido durante cualquier maniobra dinámica.
- Integrar la velocidad angular de un giroscopio indefinidamente sin considerar bias, ruido y deriva.
- Asumir que una IMU de 6 ejes contiene necesariamente un magnetómetro.
- Tratar el magnetómetro como una referencia de yaw perfecta en presencia de perturbaciones magnéticas.
- Confundir filtrado con calibración.
- Inventar escalas, bias, ruido, saturaciones o parámetros de un sensor concreto sin datasheet o evidencia experimental.
- Confundir `WHO_AM_I` / identificación del dispositivo con calibración.
- Confundir una prueba/probe SPI con comunicación física validada sobre el hardware.
- Confundir mediciones de sensores con el estado verdadero del vehículo.
- Confundir estimación de actitud con medición directa de actitud.

---
## [NOTAS] Sensores de movimiento
Nodo revisado mediante contraste con documentación técnica de fabricantes y fuentes NASA (Engineer + contraste externo).

La afirmación de que "el acelerómetro siente aceleración específica" se conserva porque es conceptualmente correcta para un acelerómetro inercial, pero debe evitarse la simplificación "el acelerómetro mide simplemente aceleración lineal". La salida depende de la convención utilizada y contiene la contribución asociada a la gravedad.

La afirmación "giroscopio + acelerómetro + filtro estiman orientación" es correcta como descripción de alto nivel, pero no debe presentarse como una garantía general. La estimación depende de las condiciones de observabilidad, dinámica, calibración y algoritmo utilizado. NASA documenta esquemas de estimación de actitud mediante EKF utilizando gyro, magnetómetro y acelerómetro.

La afirmación sobre el drift del giroscopio queda respaldada por documentación de Analog Devices: el bias y el ruido integrado producen deriva acumulativa de la estimación angular.

La afirmación sobre `WHO_AM_I` se mantiene como regla de arquitectura de Jarvis: identificar un dispositivo o verificar una interfaz no demuestra calibración ni comportamiento físico del sistema.

Para el ICM-42688-P concreto, cualquier afirmación sobre registros, escalas, rangos, interfaces, ODR, ruido u otros parámetros debe proceder de su datasheet específico y no de una nota genérica.

---
## [REFERENCIAS] Sensores de movimiento
- NASA Technical Reports Server — *Maximum Correntropy Kalman Filter for Orientation Estimation with Application to LiDAR Inertial Odometry*:
  https://ntrs.nasa.gov/citations/20220001452
- NASA Technical Reports Server — *An Application of UAV Attitude Estimation Using a Low-Cost Inertial Navigation System*:
  https://ntrs.nasa.gov/citations/20140002398
- Cullen Matsumoto — *Guidance, Navigation, and Control of Small Satellite Attitude Using Micro-Thrusters*, M.S. thesis, University of Hawaiʻi at Mānoa, December 2016 (hosted on NASA-affiliated SSRI KB; not a NASA-authored report):
  https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/2016-12-ms-matsumoto.pdf
- Analog Devices — *Analyzing Frequency Response of Inertial MEMS in Stabilization Systems*:
  https://www.analog.com/en/resources/analog-dialogue/articles/analyzing-frequency-response-of-inertial-mems.html
- Analog Devices — *The Case of the Misguided Gyro*:
  https://www.analog.com/en/resources/analog-dialogue/raqs/raq-issue-139.html
- Analog Devices — *What are the major error sources for inertial sensors?*:
  https://www.analog.com/en/resources/faqs/faq_what_are_the_major_error_sources_for_inertial.html
- TDK InvenSense — *ICM-42688-P Datasheet* (DS-000347; official download page — prefer current revision):
  https://www.invensense.tdk.com/en-us/download-resource/ds-000347-icm-42688-p-datasheet
  (PDF mirror used in cite-audit: https://www.cdiweb.com/datasheets/invensense/ds-000347-icm-42688-p-v1.2.pdf)
- TDK InvenSense — *ICM-42688-P — High-Precision 6-Axis MEMS MotionTracking Device*:
  https://www.invensense.tdk.com/en-us/inertial-sensors

---
## [ESTADO] Sensores de movimiento
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R1/R2 (Cursor)
- jarvis_lote: spine-lote-2
- estado: solid
