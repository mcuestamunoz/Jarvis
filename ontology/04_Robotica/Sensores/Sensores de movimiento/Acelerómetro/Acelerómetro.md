---
id: acelerometro
nombre: Acelerómetro
area: Robótica
subarea: Sensores de movimiento
nivel: base
estado: solid
jarvis_relevance: [fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — Analog Devices accel/gyro ops + AN-1057 + MEMS accel Part 1; NASA NTRS 20140002398; TDK ICM-42688-P
tags: [spine, lote-3]
---

# Acelerómetro

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Acelerómetro
Un **acelerómetro** es un sensor inercial que mide aceleración mediante una respuesta mecánica interna asociada a las fuerzas inerciales. En el contexto de navegación y estimación de estado, la magnitud se describe habitualmente como **fuerza específica** o **aceleración específica**, cuya relación exacta con la aceleración del cuerpo y la gravedad depende de la convención de signos y del marco utilizado.

Por tanto, la salida de un acelerómetro no debe interpretarse automáticamente como la **aceleración lineal del centro de masa** sin declarar el marco de referencia, la convención y el modelo físico utilizado.

En un acelerómetro MEMS, una masa interna se desplaza respecto a la estructura del sensor y esa variación se convierte en una señal eléctrica.

---
## [INTUICION] Acelerómetro
En condiciones estáticas sobre la Tierra, un acelerómetro puede proporcionar información sobre la dirección de la gravedad respecto a sus ejes. Esto permite estimar inclinación cuando la hipótesis dominante es que la aceleración observada procede de la gravedad.

Sin embargo, durante una maniobra, aceleración lineal, vibración o shock, la medición deja de representar únicamente la gravedad. Por ello, utilizar directamente el acelerómetro como inclinómetro durante cualquier movimiento puede producir errores importantes.

El acelerómetro puede proporcionar una referencia gravitacional para un estimador de actitud, mientras que el giroscopio proporciona información sobre la velocidad angular. La combinación de ambas fuentes puede utilizarse en sistemas de estimación de orientación.

---
## [FUNDAMENTO] Acelerómetro
Ideas fundamentales:

- Magnitud de interés: **aceleración específica** $\mathbf{a}_{\mathrm{spec}}$, según la convención del sistema y del fabricante.
- El acelerómetro puede proporcionar información sobre la dirección de la gravedad cuando las aceleraciones no gravitatorias son suficientemente pequeñas.
- Una aceleración lineal adicional puede contaminar la estimación de inclinación. Por ejemplo, una aceleración constante del vehículo puede interpretarse erróneamente como una modificación de la dirección de la gravedad si se utiliza el acelerómetro de forma aislada.
- Errores relevantes de un acelerómetro incluyen **bias/offset, ruido, error de sensibilidad o escala, desalineamiento, sensibilidad cruzada, no linealidad y dependencia con temperatura**.
- **Filtrar ≠ calibrar.** Un filtro puede reducir determinados componentes de ruido, pero no sustituye la caracterización y compensación de errores sistemáticos del sensor.
- La capacidad de utilizar un acelerómetro para estimar inclinación depende de las condiciones dinámicas y del comportamiento del sensor. La vibración y otras aceleraciones pueden degradar significativamente dicha estimación.

### Parámetros de un dispositivo concreto

Los valores de:

- rango de medida;
- densidad de ruido;
- sensibilidad;
- error de sensibilidad;
- offset/bias;
- deriva térmica;
- ancho de banda;
- ODR;
- saturación;

deben proceder del **datasheet o documentación oficial del dispositivo concreto**.

Por ejemplo, el ICM-42688-P especifica acelerómetro de rango seleccionable $\pm2g$, $\pm4g$, $\pm8g$ y $\pm16g$, además de una densidad de ruido de acelerómetro especificada por el fabricante.

Estos valores pertenecen al dispositivo concreto y **no deben convertirse en propiedades genéricas de un acelerómetro**.

---
## [EJEMPLO] Acelerómetro
En Jarvis, las lecturas de aceleración del camino IMU simulado (C3/C6) pueden alimentar la estimación de actitud (C7).

La cadena conceptual es:

```text
acelerómetro
      ↓
medición
      ↓
filtrado / procesamiento
      ↓
estimador de actitud
      ↓
actitud estimada
      ↓
control
```

Esta cadena representa **simulación / interfaz / estimación**, no calibración de un acelerómetro físico.

Una lectura simulada puede demostrar que el software procesa correctamente una señal bajo las hipótesis definidas, pero no demuestra que un acelerómetro físico instalado en el vehículo produzca esas mismas mediciones.

---
## [PROCEDIMIENTO] Acelerómetro
1. Declarar los ejes del sensor y su relación con el marco del vehículo.
2. Declarar la convención utilizada para la aceleración específica y la gravedad.
3. Determinar si la medición se utiliza directamente o como observación de un estimador.
4. Identificar rango, resolución, ruido, bias, sensibilidad, temperatura y otros parámetros relevantes a partir de una fuente válida.
5. Caracterizar o calibrar el sensor cuando el sistema real lo requiera.
6. Aplicar el filtrado apropiado para el objetivo concreto.
7. No utilizar el acelerómetro como referencia gravitacional pura durante maniobras en las que la aceleración no gravitatoria sea significativa.
8. Integrar la información del acelerómetro con otras fuentes cuando sea necesario para estimar el estado.
9. Separar explícitamente simulación, interfaz física, calibración y validación.

---
## [USO_PROBLEMAS] Acelerómetro
- selección de acelerómetros MEMS;
- estimación de inclinación;
- estimación de actitud;
- fusión sensorial;
- navegación inercial;
- detección y análisis de vibraciones;
- diagnóstico de bias;
- calibración de sensores;
- estimación de estado.

---
## [APLICACIONES] Acelerómetro
**Jarvis FS:** vocabulario y fundamento para C6/C7 y para mantener la separación entre:

**medición → procesamiento → estimación → control.**

También establece la distinción entre:

**simulación → interfaz física → calibración → validación experimental.**

Los parámetros concretos de un acelerómetro no deben residir en esta nota salvo que estén respaldados por una fuente específica.

Para el ICM-42688-P, consultar la documentación oficial del dispositivo mediante [[IMU]] / [[Sensores de movimiento]].

---
## [CONEXIONES] Acelerómetro
- [[Sensores de movimiento]]
- [[IMU]]
- [[Giroscopio]]
- [[Magnetómetro]]
- [[Velocidad angular]]
- [[Vectores]]
- [[Marcos de referencia]]
- [[Fusión sensorial]]
- [[Estimación de estado]]
- [[Gravedad]]

---
## [ERRORES] Acelerómetro
- Confundir aceleración específica con aceleración lineal del centro de masa sin declarar convención y marco.
- Interpretar siempre la salida del acelerómetro como el vector gravedad.
- Usar el acelerómetro como inclinómetro durante cualquier maniobra.
- Ignorar aceleraciones lineales, vibraciones o shocks al estimar inclinación.
- Confundir filtrado con calibración.
- Inventar ruido, bias, escala, rango u ODR de un SKU sin una fuente específica.
- Tratar parámetros de un acelerómetro concreto como propiedades universales de todos los acelerómetros.
- Tratar lecturas simuladas como calibración de hardware.
- Confundir una medición de aceleración con una estimación completa de actitud.
- Integrar o transformar una señal sin declarar previamente el marco de referencia y la convención utilizada.

---
## [NOTAS] Acelerómetro
Nodo revisado mediante contraste con documentación técnica de fabricantes y literatura técnica (Engineer + contraste externo).

La afirmación de que el acelerómetro mide **aceleración específica** es adecuada para el contexto de navegación inercial, pero debe mantenerse explícita la dependencia de la convención utilizada. La salida física de un acelerómetro MEMS se obtiene mediante la respuesta de una masa interna a fuerzas inerciales y se expresa normalmente en unidades de aceleración.

La afirmación de que en reposo el acelerómetro proporciona información sobre la gravedad es correcta para aplicaciones de inclinación estática. Sin embargo, la hipótesis deja de ser válida de forma general cuando aparecen aceleraciones adicionales. Analog Devices señala específicamente que aceleraciones constantes, movimiento y aceleraciones centrípetas pueden introducir errores en la estimación de inclinación.

La lista de errores incluye **sensibilidad cruzada y deriva/dependencia térmica**, parámetros relevantes en acelerómetros MEMS documentados por fabricantes.

Para el ICM-42688-P, TDK especifica un acelerómetro de 3 ejes integrado en una IMU de 6 ejes, con rangos seleccionables de $\pm2g$, $\pm4g$, $\pm8g$ y $\pm16g$ y una densidad de ruido especificada por el fabricante. Estos valores son ejemplos de datos de dispositivo y no deben generalizarse.

---
## [REFERENCIAS] Acelerómetro
- Analog Devices — *Accelerometer and Gyroscopes Sensors: Operation, Sensing, and Applications*:
  https://www.analog.com/en/resources/technical-articles/accelerometer-and-gyroscopes-sensors-operation-sensing-and-applications.html
- Analog Devices — *AN-1057: Using an Accelerometer for Inclination Sensing*:
  https://www.analog.com/en/resources/app-notes/an-1057.html
- Analog Devices — *Choosing the Most Suitable MEMS Accelerometer for Your Application—Part 1*:
  https://www.analog.com/en/resources/analog-dialogue/articles/choosing-the-most-suitable-mems-accelerometer-for-your-application-part-1.html
- NASA Technical Reports Server — *An Application of UAV Attitude Estimation Using a Low-Cost Inertial Navigation System*:
  https://ntrs.nasa.gov/citations/20140002398
- TDK InvenSense — *ICM-42688-P*:
  https://www.invensense.tdk.com/en-us/products/6-axis/icm-42688-p
- TDK Product Center — *ICM-42688-P Detailed Information*:
  https://product.tdk.com/en/search/sensor/mortion-inertial/imu/info?part_no=ICM-42688-P

---
## [ESTADO] Acelerómetro
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-3
- estado: solid
