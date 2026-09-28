---
id: imu
nombre: IMU
area: Robótica
subarea: Sensores de movimiento
nivel: base
estado: solid
jarvis_relevance: [fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — NASA GNC / NTRS IMU; NASA-TM-20250008926; TDK ICM-42688-P DS-000347; Analog Devices IMU alignment
tags: [spine, lote-3]
---

# IMU

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] IMU
Una **IMU** (*Inertial Measurement Unit*) es una unidad de medida inercial que integra sensores destinados a medir magnitudes inerciales del movimiento. En su configuración habitual de **6 ejes**, contiene un **acelerómetro triaxial** y un **giroscopio triaxial**. NASA describe una IMU como una unidad que contiene tres acelerómetros ortogonales y tres giróscopos ortogonales.

Algunas unidades pueden incorporar sensores adicionales o integrarse con otros sensores y procesamiento. Por tanto, **un magnetómetro no forma parte necesariamente de una IMU de 6 ejes**. Un producto comercial denominado AHRS puede incluir además magnetómetro, procesamiento de actitud y otros elementos, pero esto debe comprobarse en la documentación del dispositivo concreto.

En una IMU moderna, los sensores están acompañados normalmente por electrónica de acondicionamiento, conversión y comunicación digital. Por ejemplo, el ICM-42688-P integra un acelerómetro de 3 ejes y un giroscopio de 3 ejes y proporciona interfaces I3C, I²C y SPI.

---
## [INTUICION] IMU
Una IMU proporciona al sistema información sobre **cómo se mueve el cuerpo**:

- el acelerómetro proporciona mediciones relacionadas con la aceleración específica;
- el giroscopio proporciona velocidad angular.

El software debe conocer la **orientación de la IMU respecto al vehículo**, las convenciones de ejes y signos y las unidades utilizadas. El montaje físico también introduce posibles errores de alineamiento entre los ejes del sensor y el marco del vehículo.

La IMU no proporciona necesariamente una "actitud verdadera" directamente. Sus mediciones pueden utilizarse para **propagar o estimar el estado** mediante un algoritmo de estimación. NASA describe sistemas de navegación inercial en los que las mediciones del acelerómetro y giroscopio se integran dentro de un modelo cinemático para seguir posición, velocidad y actitud.

Identificar un dispositivo mediante `WHO_AM_I` solamente demuestra que el dispositivo responde con la identidad esperada en la interfaz correspondiente. **No demuestra calibración, alineamiento mecánico ni validación de vuelo.**

---
## [FUNDAMENTO] IMU
Mapa conceptual:

| Bloque | Rol |
|---|---|
| [[Acelerómetro]] | Medición de aceleración específica |
| [[Giroscopio]] | Medición de velocidad angular $\boldsymbol{\omega}$ |
| [[Magnetómetro]] | Medición del campo magnético; puede proporcionar información adicional para heading |
| [[Estimación de estado]] | Combina mediciones y modelo para obtener una estimación del estado |

Una IMU de 6 ejes proporciona tres ejes de acelerómetro y tres ejes de giroscopio.

La representación de las mediciones debe considerar:

- orientación de los ejes del sensor;
- orientación del sensor respecto al vehículo;
- unidades;
- convención de signos;
- frecuencia/tasa de muestreo;
- rango de medida;
- errores y calibración.

La relación entre los ejes de la IMU y los ejes del vehículo puede introducir errores de alineamiento. Analog Devices documenta que tanto el propio sensor como su montaje mecánico contribuyen al error de alineamiento.

### Medición ≠ estimación

La IMU proporciona **mediciones**. Un estimador puede utilizarlas para obtener variables de estado:

```text
IMU
 ↓
mediciones accel + gyro
 ↓
procesamiento / calibración
 ↓
estimador
 ↓
estado estimado
 ↓
control / navegación
```

La estimación puede incorporar otros sensores y modelos. NASA documenta que los sistemas inerciales acumulan errores debido a ruido y bias, por lo que sensores adicionales pueden utilizarse para corregir la deriva acumulada.

Por tanto:

**IMU ≠ estimador ≠ actitud verdadera.**

---
## [EJEMPLO] IMU
En Jarvis:

```text
SimulatedImuHal
      ↓
filtros / procesamiento C6
      ↓
attitude C7
      ↓
control
```

El flujo representa el uso de una IMU dentro de la arquitectura de software.

El camino SPI scripted + probe (C32–C34) y el driver basado en datasheet sobre `ScriptedSpi` (C42) permiten representar interfaces y comportamiento dentro del entorno de software correspondiente.

Esto **no demuestra**:

- que SPI1 esté físicamente conectado;
- que exista comunicación real sobre cobre;
- que el sensor físico esté correctamente montado;
- que la IMU esté calibrada;
- que los ejes estén correctamente alineados con el vehículo;
- que las mediciones sean válidas durante vuelo.

Cadena de honestidad:

**simulación ≠ interfaz emulada ≠ comunicación física ≠ calibración ≠ validación de vuelo.**

---
## [PROCEDIMIENTO] IMU
1. Definir qué variables necesita el sistema: aceleración, velocidad angular, actitud, heading, posición, etc.
2. Determinar si basta una IMU de 6 ejes o si se necesita información adicional procedente de magnetómetro, barómetro, GNSS u otros sensores.
3. Declarar el montaje físico y la transformación entre los ejes de la IMU y los ejes del vehículo.
4. Leer y citar el datasheet del dispositivo elegido.
5. Declarar rangos, unidades, frecuencia de muestreo y otros parámetros únicamente a partir de documentación o caracterización válida.
6. Separar claramente driver/bus, adquisición de datos, calibración, filtrado y estimación.
7. Determinar qué errores de sensor deben modelarse o compensarse.
8. Validar la comunicación con el dispositivo antes de interpretar las mediciones como datos físicos válidos.
9. Validar la calibración y alineación antes de utilizar las mediciones para funciones de control que requieran precisión.
10. No promover `WHO_AM_I`, smoke tests o probes SPI a "IMU calibrada" o "sensor validado en vuelo".

---
## [USO_PROBLEMAS] IMU
- selección de IMU;
- integración en flight controller;
- adquisición de aceleración y velocidad angular;
- estimación de actitud;
- navegación inercial;
- fusión sensorial;
- diagnóstico de bus;
- calibración y alineamiento;
- caracterización de ruido y bias;
- estimación de estado.

---
## [APLICACIONES] IMU
**Jarvis FS:** concepto central para C3/C6/C7/C42.

La IMU proporciona la interfaz conceptual entre:

**sensores físicos → mediciones inerciales → estimación de estado → control.**

La nota también establece la separación entre:

**software simulado → interfaz emulada → interfaz física → calibración → validación experimental.**

Los parámetros específicos de un dispositivo no deben convertirse en propiedades genéricas de la clase IMU.

---
## [CONEXIONES] IMU
- [[Sensores de movimiento]]
- [[Acelerómetro]]
- [[Giroscopio]]
- [[Magnetómetro]]
- [[Velocidad angular]]
- [[Vectores]]
- [[Control robótico]]
- [[Dinámica]]
- [[Marcos de referencia]]
- [[Fusión sensorial]]
- [[Estimación de estado]]
- [[Actitud]]
- [[Navegación inercial]]

---
## [ERRORES] IMU
- Asumir que toda IMU incluye magnetómetro.
- Confundir una IMU de 6 ejes con un AHRS.
- Confundir las mediciones de una IMU con una estimación completa de actitud.
- Confundir aceleración específica con aceleración lineal sin declarar la convención y el modelo utilizados.
- Ignorar la transformación entre los ejes de la IMU y los ejes del vehículo.
- Ignorar errores de alineamiento del sensor o del montaje.
- Inventar `WHO_AM_I`, ODR, rangos, ruido, escalas o registros sin datasheet.
- Tratar la identidad obtenida mediante `WHO_AM_I` como evidencia de calibración.
- Confundir un probe SPI con comunicación física validada.
- Confundir comunicación física con calibración.
- Confundir calibración con validación de vuelo.
- Tratar una salida de IMU simulada como evidencia de que la IMU física funciona correctamente.
- Asumir que filtrar las mediciones elimina automáticamente bias y errores sistemáticos.

---
## [NOTAS] IMU
Nodo revisado mediante contraste con documentación NASA, documentación oficial TDK y documentación técnica de Analog Devices (Engineer + contraste externo).

La definición de IMU como combinación de acelerómetro y giroscopio triaxiales en una unidad de 6 ejes es correcta y queda respaldada tanto por NASA como por la documentación del ICM-42688-P.

La distinción entre **IMU**, **AHRS** y **estimador** debe mantenerse. Una IMU proporciona mediciones inerciales; un AHRS puede incorporar procesamiento adicional para estimar orientación; un estimador de estado puede combinar las mediciones de la IMU con otras observaciones y modelos.

La afirmación de que la IMU requiere conocer su orientación respecto al vehículo es especialmente importante para Jarvis. Los errores de alineamiento del propio sensor y los producidos por su montaje pueden afectar directamente a la transformación entre el marco del sensor y el marco del sistema.

Para el **ICM-42688-P**, la documentación oficial confirma que es una IMU de 6 ejes formada por un acelerómetro y un giroscopio de tres ejes, con interfaces I3C, I²C y SPI. El fabricante especifica además rangos seleccionables para ambos sensores y sus características de ruido.

La documentación NASA también respalda la regla de arquitectura de Jarvis de que las mediciones inerciales no deben tratarse como un estado perfecto: ruido y bias provocan deriva de las soluciones inerciales durante periodos prolongados y hacen necesaria, cuando corresponde, la utilización de observaciones adicionales.

---
## [REFERENCIAS] IMU
- NASA — *Guidance, Navigation and Control — Small Spacecraft Systems Virtual Institute*:
  https://www.nasa.gov/smallsat-institute/sst-soa/guidance-navigation-and-control/
- NASA Technical Reports Server — *Onboard Navigation Systems Characteristics* (NASA-TM-79944 / JSC-14675, citation 19790012950; §2.0 "Inertial Measurement Unit"):
  https://ntrs.nasa.gov/api/citations/19790012950/downloads/19790012950.pdf
- NASA Technical Memorandum NASA-TM-20250008926 — Graupe, Karlgaard, Dutta, *Using Doppler Tracking to Aid Trajectory Reconstruction for Atmospheric Entry, Descent, and Landing* (IMU/Doppler fusion context):
  https://ntrs.nasa.gov/api/citations/20250008926/downloads/NASA-TM-20250008926.pdf
- NASA Planetary Data System — *Mars Exploration Rover Inertial Measurement Unit*:
  https://pds.nasa.gov/ds-view/pds/viewContext.jsp?identifier=urn%3Anasa%3Apds%3Acontext%3Ainstrument%3Aimu.mer2&version=1.2
- TDK InvenSense — *ICM-42688-P — High-Precision 6-Axis MEMS MotionTracking Device*:
  https://www.invensense.tdk.com/en-us/products/6-axis/icm-42688-p
- TDK InvenSense — *ICM-42688-P Datasheet* (DS-000347):
  Official download page: https://www.invensense.tdk.com/en-us/download-resource/ds-000347-icm-42688-p-datasheet
  PDF mirror (cite-audit verified): https://www.cdiweb.com/datasheets/invensense/ds-000347-icm-42688-p-v1.2.pdf
- TDK Product Center — *ICM-42688-P Detailed Information*:
  https://product.tdk.com/en/search/sensor/mortion-inertial/imu/info?part_no=ICM-42688-P
- Analog Devices — *The Basics of MEMS IMU/Gyroscope Alignment*:
  https://www.analog.com/en/resources/analog-dialogue/articles/mems-imu-gyroscope-alignment.html

---
## [ESTADO] IMU
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R1/R2 + TM title (Cursor)
- jarvis_lote: spine-lote-3
- estado: solid
