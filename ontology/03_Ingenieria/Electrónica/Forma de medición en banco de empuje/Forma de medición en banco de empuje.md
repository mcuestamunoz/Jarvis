---
id: forma-medicion-banco-empuje
nombre: Forma de medición en banco de empuje
area: Ingeniería
subarea: Electrónica / propulsión
nivel: intermedio
estado: solid
jarvis_relevance: [craft, catalog, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — UIUC Propeller Database / Selig pubs; NASA Airvolt + thrust uncertainty NTRS; APC performance (analytic vs measured)
tags: [spine, lote-5]
---

# Forma de medición en banco de empuje

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Forma de medición en banco de empuje
La **forma de medición en banco de empuje** es el conjunto mínimo de **condiciones, magnitudes medidas y metadatos experimentales** necesarios para que un resultado de ensayo de propulsión sea interpretable, reproducible y reutilizable.

No es un valor de thrust. Es una **estructura de evidencia experimental** asociada a un punto o conjunto de puntos de operación (*operating point*, OP).

En ensayos de propulsión eléctrica, las variables relevantes pueden incluir thrust, torque, velocidad de giro, tensión, corriente, temperatura, presión, densidad del aire y velocidad de flujo, según el objetivo y la configuración del ensayo. NASA y los ensayos experimentales de UIUC utilizan conjuntos de instrumentación de este tipo para caracterizar sistemas de propulsión y hélices.

Relacionado: [[Punto de operación vs capacidad intrínseca]].

---
## [INTUICION] Forma de medición en banco de empuje
“Medí 800 gf” sin identificar suficientemente **qué conjunto se ensayó y bajo qué condiciones** no constituye por sí solo un punto de operación reutilizable.

Forma mínima conceptual:

```text
conjunto:
    motor + hélice + ESC + alimentación

condiciones:
    tensión
    corriente
    RPM
    velocidad de flujo / condición estática
    temperatura
    presión / densidad, cuando sean relevantes

resultado:
    thrust
    torque, si se mide
    potencia, si se mide o calcula

metadatos:
    instrumentos
    método de medición
    calibración
    fecha / identificación del ensayo
    incertidumbre o precisión conocida
```

La importancia de registrar las condiciones se observa directamente en bases experimentales como UIUC: sus ensayos identifican RPM, condiciones estáticas o velocidad de flujo y utilizan thrust/torque medidos para obtener los coeficientes de rendimiento.

Por tanto, **“thrust + condiciones”** es una descripción más correcta que exigir una lista rígida idéntica para cualquier banco: las variables necesarias dependen del tipo de ensayo.

---
## [FUNDAMENTO] Forma de medición en banco de empuje
- Un resultado de banco representa el comportamiento del **conjunto ensayado bajo unas condiciones concretas**, no una propiedad universal del motor aislado.
- La hélice tiene un comportamiento dependiente de variables como RPM, diámetro, velocidad de avance y densidad del aire. UIUC, por ejemplo, expresa el rendimiento mediante coeficientes que dependen de estas magnitudes y distingue explícitamente entre ensayos estáticos y con flujo.
- En ensayos experimentales, **thrust y torque pueden medirse mediante células de carga**, mientras que la velocidad de giro y las condiciones del flujo se registran para caracterizar el punto de funcionamiento.
- La potencia mecánica de la hélice puede obtenerse a partir de torque y velocidad angular:

$$
P = 2\pi nQ
$$

donde $n$ es la velocidad de rotación en revoluciones por segundo y $Q$ el torque. Esta relación se utiliza en la metodología experimental de UIUC.

- La calidad del resultado depende también de la **calibración, rigidez, alineamiento, fricción, vibraciones y características del propio banco**. NASA documenta, por ejemplo, cómo errores mecánicos de un banco pueden afectar directamente a la medición de thrust y cómo la calibración de los canales de adquisición forma parte de la validación del sistema.
- La **incertidumbre de medición** no debe confundirse con la repetibilidad del sistema completo. NASA ha publicado análisis específicos de incertidumbre para bancos de thrust, separando fuentes de sesgo y precisión del propio banco de otros factores experimentales.
- Un dato puede ser:
  - **T1 — fabricante:** dato publicado por el fabricante para unas condiciones declaradas.
  - **T2 — ensayo propio:** dato obtenido mediante instrumentación y procedimiento documentados.
  - **estimado:** resultado obtenido mediante un modelo o método de cálculo declarado, sin presentarlo como medición.
- Los datos analíticos también pueden ser válidos si el método está explícitamente identificado. APC, por ejemplo, publica datos de rendimiento calculados mediante métodos basados en teoría de vórtices y distingue esos resultados de datos experimentales.
- No debe mezclarse sin justificación un resultado de un banco que caracteriza **motor + ESC + hélice + alimentación** con una propiedad aislada del ESC o del motor.

---
## [EJEMPLO] Forma de medición en banco de empuje
HD-005 (conceptual): falta un OP suficientemente respaldado para el combo XING-E + Gemfan 51466-3 + 4S.

La nota debe especificar **qué variables y condiciones habría que registrar para obtener un T2**, pero no debe inventar `thrust_gf` ni completar una curva inexistente.

Un resultado experimental válido podría representar, conceptualmente:

```text
motor: SKU identificado
hélice: SKU identificado
ESC: SKU/configuración identificada
batería/alimentación: configuración identificada

V: valor medido
I: valor medido
RPM: valor medido
thrust: valor medido
torque: valor medido, si se dispone
temperatura/presión: valores medidos o declarados
método/instrumentación: identificados
incertidumbre: declarada si está disponible
```

Esto es coherente con la estructura utilizada en campañas experimentales de UIUC y NASA, aunque el conjunto exacto de variables debe adaptarse al ensayo concreto.

---
## [PROCEDIMIENTO] Forma de medición en banco de empuje
1. Identificar los SKUs y la configuración completa del conjunto ensayado.
2. Definir si el ensayo es estático o con flujo y declarar las condiciones correspondientes.
3. Medir y registrar las magnitudes relevantes: thrust, RPM, tensión, corriente, torque y condiciones ambientales según el objetivo del ensayo.
4. Documentar instrumentos, método de adquisición y calibración.
5. Registrar las condiciones suficientes para reproducir o interpretar el punto de operación.
6. Separar claramente dato medido, dato publicado por fabricante y resultado estimado.
7. Registrar incertidumbre o limitaciones de medición cuando estén disponibles.
8. No interpolar ni completar puntos inexistentes sin declarar el modelo utilizado.
9. No convertir automáticamente un resultado de un conjunto ensayado en una propiedad universal del motor.

---
## [USO_PROBLEMAS] Forma de medición en banco de empuje
Diseño de campañas T2, revisión de tablas de fabricante, caracterización motor-hélice, comparación de configuraciones, validación de modelos y evaluación de incertidumbre experimental.

---
## [APLICACIONES] Forma de medición en banco de empuje
**Jarvis catalog/craft:** plantilla conceptual de evidencia para OPs y para decidir si un resultado puede entrar en `library/`.

**Jarvis HD-\*:** permite expresar qué información falta para convertir una afirmación de rendimiento en evidencia utilizable, sin inventar los datos ausentes.

---
## [CONEXIONES] Forma de medición en banco de empuje
- [[Punto de operación vs capacidad intrínseca]]
- [[Motores]]
- [[Motor DC]]
- [[Actuadores]]
- [[Corriente y circuitos]]
- [[C-rate de batería]]
- [[Empuje]]
- [[Hélice]]
- [[RPM]]
- [[Torque]]
- [[Incertidumbre de medición]]

---
## [ERRORES] Forma de medición en banco de empuje
- Publicar thrust sin identificar suficientemente las condiciones del ensayo.
- Usar un OP de otra hélice, tensión, RPM o condición de flujo como si fuera el OP del craft.
- Inventar una curva para cerrar HD-004/HD-005.
- Presentar una estimación como si fuera una medición.
- Ignorar calibración, alineamiento, vibraciones o incertidumbre del banco.
- Confundir potencia mecánica de hélice con potencia eléctrica de entrada.
- Confundir un resultado del conjunto motor+ESC+hélice con una propiedad intrínseca del motor.
- Tratar un único punto de operación como capacidad universal del motor.

---
## [NOTAS] Forma de medición en banco de empuje
Nodo revisado mediante contraste externo (Engineer + GPT cite).

Se corrige una posible sobrerrestricción del borrador: no existe una lista universal e idéntica de variables que deba registrarse en todo ensayo de thrust. Las variables necesarias dependen de si el ensayo es estático, con flujo, orientado a thrust, potencia, eficiencia, caracterización del motor o validación de un modelo.

La estructura propuesta es consistente con metodologías experimentales de UIUC y NASA.

---
## [REFERENCIAS] Forma de medición en banco de empuje
- UIUC — Propeller Database (Selig / Applied Aerodynamics Group):
  https://m-selig.ae.illinois.edu/props/propDB.html
- Dantsker, Caccamo, Deters & Selig — *Performance Testing of APC Electric Fixed-Blade UAV Propellers*, AIAA Aviation 2022 (UIUC PDB Vol. 4 context):
  https://m-selig.ae.illinois.edu/props/volume-4/propDB-volume-4.html
- Brandt & Selig / UIUC — Propeller performance at low Reynolds numbers (PDB Vol. 1 / methodology):
  https://m-selig.ae.illinois.edu/props/volume-1/propDB-volume-1.html
- Shetty & Selig — AIAA 2011-1254 (LRN / VRS props; experimental context):
  https://m-selig.ae.illinois.edu/pubs/ShettySelig-2011-AIAA-2011-1254-LRN-VSR-Props.pdf
- Dantsker, Selig & Mancuso — AIAA 2017-3745 (*A Rolling Rig for Propeller Performance Testing*):
  https://m-selig.ae.illinois.edu/pubs/DantskerSeligMancuso-2017-AIAA-Paper-2017-3745.pdf
- NASA NTRS 20160001339 — Airvolt Aircraft Electric Propulsion Test Stand:
  https://ntrs.nasa.gov/api/citations/20160001339/downloads/20160001339.pdf
- NASA NTRS 20180006103 — *Uncertainty in Inverted Pendulum Thrust Measurements*:
  https://ntrs.nasa.gov/citations/20180006103
- NASA Armstrong — Flight and Ground Experimental Test Capabilities (Airvolt / test stands context):
  https://www.nasa.gov/centers-and-facilities/armstrong/flight-and-ground-experimental-test-capabilities/
- APC Propellers — Performance Data (analytic / vortex methods vs experimental):
  https://www.apcprop.com/technical-information/performance-data/

---
## [ESTADO] Forma de medición en banco de empuje
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid` · cite-audit R2 (Cursor)
- jarvis_lote: spine-lote-5
- estado: solid
