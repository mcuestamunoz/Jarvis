---
id: giroscopio
nombre: Giroscopio
area: Robótica
subarea: Sensores de movimiento
nivel: base
estado: solid
jarvis_relevance: [fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — Analog Devices MEMS gyro / ARW / alignment; NASA NTRS 20140002398; TDK ICM-42688-P
tags: [spine, lote-3]
---

# Giroscopio

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Giroscopio
Un **giroscopio**, en el contexto de sensores inerciales MEMS, mide **velocidad angular** respecto a uno o más ejes del sensor. La magnitud medida puede representarse como un vector de velocidad angular $\boldsymbol{\omega}$ expresado en los ejes del sensor.

La integración temporal de la velocidad angular puede utilizarse para obtener información sobre el cambio de orientación. Sin embargo, los errores de bias, ruido y otros errores de medida se acumulan durante la integración y pueden producir **deriva angular**.

Por tanto, un giroscopio proporciona **velocidad angular**, no una medida absoluta directa del ángulo de orientación.

---
## [INTUICION] Giroscopio
El gyro "siente giro", no ángulo absoluto.

En un modelo simplificado, si se conoce la velocidad angular y se integra durante un intervalo de tiempo, puede obtenerse un cambio de orientación aproximado:

$$
\Delta\theta \approx \int_{t_0}^{t_1}\omega(t)\,dt
$$

Para un intervalo discreto suficientemente pequeño:

$$
\Delta\theta \approx \omega\,\Delta t
$$

Pero esta integración acumula los errores de la medición. Un bias aproximadamente constante $b$ produce un error angular que crece aproximadamente con el tiempo:

$$
\theta_{\mathrm{error}}(t) \approx b\,t
$$

Por eso un giroscopio no suele utilizarse por sí solo para proporcionar una orientación absoluta estable durante periodos prolongados. En sistemas de estimación de actitud se combina habitualmente con otras observaciones, como acelerómetro y, cuando resulta apropiado, magnetómetro.

---
## [FUNDAMENTO] Giroscopio
Ideas fundamentales:

- Magnitud medida: **velocidad angular** $\boldsymbol{\omega}$ en los ejes del sensor.
- La integración de $\boldsymbol{\omega}$ proporciona información sobre el cambio de orientación, pero requiere una condición inicial y está sujeta a acumulación de errores.
- Un modelo simplificado de la medición puede expresarse como:

$$
\boldsymbol{\omega}_{m}
=
\boldsymbol{\omega}
+
\mathbf{b}
+
\mathbf{n}
$$

donde $\boldsymbol{\omega}_{m}$ es la medida, $\boldsymbol{\omega}$ la velocidad angular real, $\mathbf{b}$ un término de bias y $\mathbf{n}$ un término de ruido. Este modelo es una simplificación; un modelo real puede incluir términos adicionales como escala, desalineamiento, sensibilidad cruzada y dependencias ambientales.

- El **bias** es especialmente importante porque su integración produce un error angular acumulativo.
- El **angular random walk (ARW)** caracteriza una contribución aleatoria al error de orientación asociada al ruido del giroscopio.
- Otros errores relevantes incluyen error de escala, desalineamiento entre ejes, sensibilidad a aceleraciones y dependencia con temperatura.

### Uso en control

En un vehículo aéreo, el giroscopio puede utilizarse directamente para proporcionar **realimentación de velocidad angular** en un lazo de tasas.

También puede proporcionar una de las principales observaciones para un estimador de actitud. Estas son funciones relacionadas pero conceptualmente distintas:

**gyro → velocidad angular → control de tasas**

y

**gyro + otras observaciones → estimación de actitud**

Los sistemas concretos pueden utilizar arquitecturas diferentes.

---
## [EJEMPLO] Giroscopio
En Jarvis:

```text
IMU simulada
    ↓
velocidad angular
    ↓
estimación / procesamiento
    ↓
attitude
    ↓
control
```

El camino C6 → C7 representa el uso de las mediciones inerciales dentro de la arquitectura de software.

El driver basado en datasheet sobre `ScriptedSpi` (C42) puede modelar el comportamiento de la interfaz y del dispositivo dentro del entorno de software correspondiente.

Esto **no demuestra**:

- que SPI1 esté físicamente conectado;
- que exista comunicación real sobre cobre;
- que el sensor físico esté correctamente instalado;
- que el gyro esté calibrado;
- que sus mediciones sean válidas en vuelo.

Por tanto:

**modelo/driver simulado ≠ comunicación física ≠ calibración ≠ validación de vuelo.**

---
## [PROCEDIMIENTO] Giroscopio
1. Declarar los ejes del sensor y el sentido positivo de $\boldsymbol{\omega}$.
2. Declarar el marco de referencia en el que se expresan las velocidades angulares.
3. Determinar si la medición se utilizará como observación de un estimador, como realimentación de tasas o para ambas funciones.
4. Obtener del datasheet o de ensayos los parámetros relevantes del sensor.
5. Caracterizar bias y su dependencia con temperatura, tiempo y condiciones de funcionamiento cuando sea necesario.
6. Caracterizar ruido y, cuando corresponda, utilizar métricas como noise density o ARW.
7. Considerar escala, desalineamiento y sensibilidad a aceleraciones cuando sean relevantes para la aplicación.
8. No integrar indefinidamente la velocidad angular sin considerar los mecanismos de deriva y las referencias disponibles.
9. Utilizar fusión sensorial o corrección de bias cuando el requisito de orientación lo requiera.
10. Separar explícitamente simulación, probe/`WHO_AM_I`, comunicación física, calibración y validación experimental.

---
## [USO_PROBLEMAS] Giroscopio
- estabilización de actitud;
- control de velocidad angular;
- estimación de orientación;
- navegación inercial;
- fusión sensorial;
- análisis de deriva;
- caracterización de ruido;
- calibración de sensores;
- diseño de filtros y estimadores;
- control de plataformas estabilizadas.

---
## [APLICACIONES] Giroscopio
**Jarvis FS:** fundamento para C6–C7 y C42.

El giroscopio proporciona una medición fundamental para:

**medición de $\boldsymbol{\omega}$ → estimación de estado → control.**

También establece la separación entre:

**modelo/software → interfaz física → calibración → validación experimental.**

Los parámetros concretos de un gyro/SKU no deben incorporarse a esta nota salvo que estén respaldados por su documentación específica.

---
## [CONEXIONES] Giroscopio
- [[Sensores de movimiento]]
- [[IMU]]
- [[Acelerómetro]]
- [[Magnetómetro]]
- [[Velocidad angular]]
- [[Vectores]]
- [[Marcos de referencia]]
- [[Control clásico]]
- [[Control robótico]]
- [[Fusión sensorial]]
- [[Estimación de estado]]
- [[Actitud]]

---
## [ERRORES] Giroscopio
- Tratar la integración del gyro como una medida de actitud absoluta.
- Ignorar el bias al integrar la velocidad angular.
- Suponer que un bias pequeño produce un error pequeño independientemente del tiempo de integración.
- Confundir velocidad angular con ángulo.
- Confundir la realimentación de tasas con la estimación completa de actitud.
- Inventar bias, ruido, escala, rango, ODR o ARW de un SKU sin datasheet.
- Ignorar desalineamiento entre ejes.
- Ignorar sensibilidad a temperatura, vibración o aceleraciones cuando sea relevante.
- Confundir filtrado con calibración.
- Confundir `WHO_AM_I` / probe SPI con calibración del gyro.
- Usar tasas angulares simuladas como evidencia de que el sensor físico funciona correctamente.

---
## [NOTAS] Giroscopio
Nodo revisado mediante contraste con documentación técnica de fabricantes y fuentes NASA (Engineer + contraste externo).

La afirmación central de que el giroscopio MEMS mide **velocidad angular** queda respaldada por Analog Devices. La misma fuente describe cómo la integración de la velocidad angular proporciona información angular y cómo el bias produce deriva proporcional al tiempo.

La distinción entre **bias instability** y **angular random walk (ARW)** es importante. Analog Devices identifica el bias como una fuente de deriva de baja frecuencia y el ARW como una contribución asociada al ruido del sensor durante la integración.

La afirmación de que el giroscopio puede utilizarse para realimentación de tasas también está respaldada por documentación de Analog Devices sobre sistemas de control que utilizan giroscopios MEMS como elementos de feedback de velocidad angular.

NASA documenta, en un sistema de estimación de actitud de UAV, el uso conjunto de gyro, acelerómetro y magnetómetro dentro de un EKF para obtener estimaciones de actitud mediante cuaterniones. Esto respalda la separación entre medición inercial y estimación de actitud.

El desalineamiento de ejes se considera un error relevante en IMU/giroscopios MEMS y debe contemplarse cuando la precisión requerida lo justifique.

Para un dispositivo concreto como el **ICM-42688-P**, TDK especifica un giroscopio de 3 ejes con rangos seleccionables de $\pm15.6$, $\pm31.2$, $\pm62.5$, $\pm125$, $\pm250$, $\pm500$, $\pm1000$ y $\pm2000$ dps, además de una densidad de ruido de giroscopio especificada por el fabricante. Estos valores pertenecen al SKU concreto y no deben convertirse en propiedades genéricas de un giroscopio.

---
## [REFERENCIAS] Giroscopio
- Analog Devices — *Analyzing Frequency Response of Inertial MEMS in Stabilization Systems*:
  https://www.analog.com/en/resources/analog-dialogue/articles/analyzing-frequency-response-of-inertial-mems.html
- Analog Devices — *The Case of the Misguided Gyro*:
  https://www.analog.com/en/resources/analog-dialogue/raqs/raq-issue-139.html
- Analog Devices — *Designing for Low Noise Feedback Control with MEMS Gyroscopes*:
  https://www.analog.com/en/resources/analog-dialogue/articles/low-noise-feedback-control.html
- Analog Devices — *The Basics of MEMS IMU/Gyroscope Alignment*:
  https://www.analog.com/en/resources/analog-dialogue/articles/mems-imu-gyroscope-alignment.html
- NASA Technical Reports Server — *An Application of UAV Attitude Estimation Using a Low-Cost Inertial Navigation System*:
  https://ntrs.nasa.gov/citations/20140002398
- TDK InvenSense — *ICM-42688-P — High-Precision 6-Axis MEMS MotionTracking Device*:
  https://www.invensense.tdk.com/en-us/products/6-axis/icm-42688-p

---
## [ESTADO] Giroscopio
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R3 (Cursor)
- jarvis_lote: spine-lote-3
- estado: solid
