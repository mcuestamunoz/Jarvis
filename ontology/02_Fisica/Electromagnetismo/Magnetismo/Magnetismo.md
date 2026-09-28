---
id: magnetismo
nombre: Magnetismo
area: Física
subarea: Electromagnetismo
nivel: base
estado: solid
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — NOAA/NCEI WMM + declination/FAQ; Analog Devices hard/soft iron (EngineerZone); AD AN-1157 (EKF + mag)
tags: [spine, lote-5]
---

# Magnetismo

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Magnetismo
El **magnetismo** es el fenómeno físico asociado a campos magnéticos y a su interacción con corrientes eléctricas, cargas en movimiento y materiales magnéticos.

En robótica aérea, una aplicación relevante es la medida del **campo magnético terrestre** mediante un **magnetómetro**, que puede proporcionar una referencia de orientación respecto al campo geomagnético y, mediante procesamiento y compensación adecuados, contribuir a la estimación del **heading / yaw**.

El magnetómetro no mide directamente el yaw ni proporciona por sí solo una actitud completa. Mide el campo magnético local expresado en los ejes del sensor. La orientación se obtiene a partir de esa observación y del conocimiento de la orientación del sensor respecto al vehículo, normalmente dentro de un estimador o algoritmo de fusión.

La **declinación magnética** es la diferencia angular entre el norte magnético y el norte geográfico, y depende de la localización y del tiempo. NOAA/NCEI mantiene modelos geomagnéticos para describir el campo terrestre y calcular esta magnitud.

---
## [INTUICION] Magnetismo
“¿Cómo está orientado el vehículo respecto al campo magnético terrestre?”

```text
campo magnético terrestre + entorno local
                    ↓
              magnetómetro
                    ↓
        vector B en ejes del sensor
                    ↓
          calibración / compensación
                    ↓
        estimador / fusión sensorial
                    ↓
        heading / yaw estimado
```

El campo medido por el magnetómetro no es necesariamente igual al campo terrestre ideal. Motores, corrientes eléctricas, materiales ferromagnéticos y otros elementos cercanos pueden alterar la magnitud y dirección del campo local.

Los errores asociados a **hard iron** y **soft iron** son fuentes conocidas de error en magnetómetros. Analog Devices documenta que fuentes como imanes permanentes, corrientes de alimentación y materiales ferromagnéticos pueden producir estas perturbaciones y recomienda caracterizar el sensor en el entorno de aplicación.

---
## [FUNDAMENTO] Magnetismo
- El campo magnético se representa mediante un vector $\mathbf{B}$.
- Un magnetómetro mide componentes del campo magnético en los ejes del sensor.
- La medición debe interpretarse teniendo en cuenta el **marco de referencia**, el montaje y la calibración.
- El campo terrestre tiene componentes de dirección e intensidad. NOAA/NCEI describe, entre otras, declinación, inclinación, componentes norte/este, componente vertical e intensidad total.
- La declinación magnética depende de la localización y cambia con el tiempo.
- La lectura del magnetómetro puede contribuir a la estimación de heading/yaw, pero no constituye por sí sola una estimación completa de actitud.
- Las perturbaciones **hard-iron** producen principalmente un desplazamiento del campo medido; las **soft-iron** pueden distorsionar su magnitud y dirección.
- La calibración de un magnetómetro debe realizarse en condiciones representativas del montaje final cuando las perturbaciones del vehículo sean relevantes.
- La fusión con acelerómetros y giróscopos permite combinar las diferentes observaciones en un estimador de orientación. Analog Devices documenta, por ejemplo, la combinación de giroscopios, acelerómetros y magnetómetros dentro de un EKF para estimación de orientación.

Una relación conceptual para el heading magnético horizontal puede expresarse, en un caso idealizado y tras compensar inclinación y errores del sensor, a partir de las componentes horizontales del campo:

$$
\psi_m = \operatorname{atan2}(B_E,B_N)
$$

Esta expresión es **toy/idealizada**: para utilizarla en un sistema real deben considerarse el marco del sensor, la actitud del vehículo, calibración, declinación y perturbaciones magnéticas.

---
## [EJEMPLO] Magnetismo
Jarvis:

```text
C7 attitude
   ↓
C37 magnetometer yaw observation (sim)
   ↓
yaw / heading reference
```

C37 representa una **observación magnética simulada**.

Por tanto:

**simulación ≠ interfaz emulada ≠ sensor físico ≠ calibración ≠ validación de vuelo**

El hecho de que el software procese correctamente un vector magnético simulado no demuestra que un magnetómetro físico montado en el vehículo proporcione un heading válido.

---
## [PROCEDIMIENTO] Magnetismo
1. Determinar si se necesita una referencia magnética de heading.
2. Declarar el marco de coordenadas y la orientación del magnetómetro respecto al vehículo.
3. Identificar las fuentes de perturbación magnética próximas al sensor.
4. Caracterizar y compensar errores de hard iron y soft iron cuando corresponda.
5. Separar campo magnético medido, heading magnético y heading referido al norte geográfico.
6. Aplicar la declinación magnética cuando sea necesario transformar entre norte magnético y norte verdadero.
7. Integrar la observación magnética dentro del estimador/fusión correspondiente.
8. Validar la medición en el montaje físico final; una prueba del sensor aislado no garantiza el comportamiento del sistema instalado.
9. En Jarvis FS, mantener explícitamente separados los datos simulados de la validación sobre hardware.

---
## [USO_PROBLEMAS] Magnetismo
Heading, estimación de orientación, fusión sensorial, diagnóstico de interferencias magnéticas, calibración de magnetómetros y navegación basada en referencias geomagnéticas.

---
## [APLICACIONES] Magnetismo
**Jarvis FS:** fundamento físico para C37 y para la utilización de una observación magnética como referencia de yaw.

**Jarvis craft:** vocabulario para magnetómetros, interferencias magnéticas, calibración y declinación.

**Jarvis honesty:** un magnetómetro simulado o una lectura correcta del bus no constituye evidencia de que el heading físico del vehículo sea válido.

---
## [CONEXIONES] Magnetismo
- [[Campo magnético]]
- [[Fuerza magnética]]
- [[Inducción electromagnética]]
- [[Ley de Faraday]]
- [[Magnetómetro]]
- [[IMU]]
- [[Giroscopio]]
- [[Acelerómetro]]
- [[Sensores de movimiento]]
- [[Vectores]]
- [[Marcos de referencia]]
- [[Fusión sensorial]]
- [[Control robótico]]
- [[Navegación y planificación]]

---
## [ERRORES] Magnetismo
- Tratar la lectura del magnetómetro como yaw verdadero.
- Asumir que el magnetómetro mide directamente el norte geográfico.
- Confundir norte magnético con norte geográfico sin considerar la declinación.
- Ignorar la dependencia espacial y temporal del campo magnético terrestre.
- Ignorar perturbaciones producidas por motores, corrientes, cableado o materiales ferromagnéticos.
- Confundir errores hard-iron con soft-iron.
- Inventar parámetros de calibración sin mediciones o fuente.
- Considerar una calibración realizada lejos del montaje definitivo como garantía del comportamiento final.
- Confundir un magnetómetro simulado con un magnetómetro físico validado.
- Confundir `WHO_AM_I` / comunicación SPI o I²C correcta con una medición magnética válida.

---
## [NOTAS] Magnetismo
Nodo revisado mediante contraste externo (Engineer + GPT cite).

Correcciones principales respecto al borrador:

- Se precisa que el magnetómetro **mide el campo magnético**, no “mide yaw”.
- Se separan **heading magnético** y **norte geográfico** mediante el concepto de declinación.
- Se refuerza que hard-iron y soft-iron son errores dependientes de la aplicación y del entorno físico.
- Se añade que la calibración debe considerar el montaje y entorno final.
- Se evita presentar $\operatorname{atan2}$ como solución universal para yaw; se mantiene como relación idealizada.
- La distinción **simulación ≠ hardware ≠ calibración ≠ validación** es regla arquitectónica de Jarvis (honestidad), no una ley física.

---
## [REFERENCIAS] Magnetismo
- NOAA / NCEI — World Magnetic Model (WMM):
  https://www.ncei.noaa.gov/products/world-magnetic-model
- NOAA / NCEI — Magnetic Declination:
  https://www.ncei.noaa.gov/products/magnetic-declination
- NOAA / NCEI — Geomagnetism Frequently Asked Questions:
  https://www.ncei.noaa.gov/products/geomagnetism-frequently-asked-questions
- Analog Devices EngineerZone — Hard & Soft Iron Correction for Magnetometer Measurements:
  https://ez.analog.com/mems/a/documents/do19172/faq-hard-soft-iron-correction-for-magnetometer-measurements
- Analog Devices — AN-1157: Tuning the Extended Kalman Filter in the ADIS16480 (gyro + accel + mag en EKF):
  https://www.analog.com/media/en/technical-documentation/application-notes/AN-1157.pdf

---
## [ESTADO] Magnetismo
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-5
- estado: solid
