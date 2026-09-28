---
id: c-rate-de-bateria
nombre: C-rate de batería
area: Ingeniería
subarea: Electrónica / energía
nivel: base
estado: solid
jarvis_relevance: [craft, catalog, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: cited — Battery University BU-402 (C-rate); BU-105 (defs); BU-904 (capacity vs discharge); BU-1101 (glossary / coulomb ≠ C-rate)
tags: [spine, lote-4]
---

# C-rate de batería

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] C-rate de batería
El **C-rate** expresa la corriente de carga o descarga de una batería **en relación con su capacidad nominal expresada en Ah**. Un rate de `1C` corresponde a una corriente numéricamente igual a la capacidad en Ah: por ejemplo, una batería de `4 Ah` sometida a `1C` se descarga idealmente a `4 A`.

El C-rate describe una **tasa relativa de carga o descarga**; no es por sí mismo una medida de potencia, energía disponible, masa ni autonomía. La capacidad efectiva obtenida depende de las condiciones de ensayo y de la batería.

---
## [INTUICION] C-rate de batería
“¿A qué ritmo se está cargando o descargando la batería?”

Si la capacidad nominal es $Q$ en Ah y la corriente es $I$ en A, el C-rate se expresa como:

$$
C_{\mathrm{rate}} = \frac{I}{Q}
$$

Así, para una batería de `4 Ah`:

- `1C` → `4 A`
- `0.5C` → `2 A`
- `2C` → `8 A`

Estos valores describen la relación nominal entre corriente y capacidad; **no garantizan que la batería pueda operar continuamente a ese rate**. Los límites de carga/descarga deben proceder de la especificación del fabricante.

---
## [FUNDAMENTO] C-rate de batería
- **Capacidad nominal:** normalmente expresada en Ah o mAh.
- **C-rate de carga:** corriente de carga relativa a la capacidad.
- **C-rate de descarga:** corriente de descarga relativa a la capacidad.
- Los límites de C-rate dependen de la **química, diseño de la celda/pack, temperatura, estado de carga, condiciones de ensayo y especificación del fabricante**.
- El C-rate no determina por sí solo la capacidad realmente extraíble. A tasas de descarga mayores pueden aumentar las pérdidas internas y disminuir la capacidad medida hasta el corte de descarga.
- Deben distinguirse los límites **continuos** de los límites **pico/burst** cuando el fabricante los especifica.

Relacionado: [[Corriente y circuitos]] · [[Potencia eléctrica]] · [[Punto de operación vs capacidad intrínseca]] · [[Batería]].

---
## [EJEMPLO] C-rate de batería
Un pack de `4S 1500 mAh` tiene una capacidad nominal de `1.5 Ah`.

A `1C`:

$$
I = 1 \times 1.5 = 1.5\ \mathrm{A}
$$

A `20C`:

$$
I = 20 \times 1.5 = 30\ \mathrm{A}
$$

El segundo valor **solo puede considerarse una corriente admisible si el fabricante especifica ese C-rate para las condiciones correspondientes**. No debe inferirse simplemente a partir de la capacidad.

---
## [PROCEDIMIENTO] C-rate de batería
1. Leer la capacidad nominal del pack/celda en Ah o mAh.
2. Identificar si el fabricante especifica C-rate de carga, descarga continua y/o descarga pico.
3. Convertir el C-rate a corriente solo dentro de las condiciones especificadas.
4. Separar claramente capacidad nominal, corriente admisible y capacidad realmente medida.
5. No convertir directamente C-rate en autonomía sin un modelo energético y condiciones de descarga definidos.

---
## [USO_PROBLEMAS] C-rate de batería
Selección de baterías, dimensionado de corriente, comprobación de límites de descarga/carga y análisis de condiciones de operación.

---
## [APLICACIONES] C-rate de batería
**Jarvis craft:** explica la relación entre capacidad nominal y corriente de operación.

**Jarvis catalog:** los C-rates de un SKU deben proceder de una fuente identificable del fabricante o de un ensayo documentado; esta nota conceptual no proporciona valores de catálogo.

**Jarvis energy:** el C-rate puede utilizarse como condición de operación de un modelo de batería, pero no sustituye una curva de descarga, modelo de resistencia interna o datos de capacidad medidos cuando estos sean necesarios.

---
## [CONEXIONES] C-rate de batería
- [[Corriente y circuitos]]
- [[Potencia eléctrica]]
- [[Batería]]
- [[Capacidad de batería]]
- [[Punto de operación vs capacidad intrínseca]]
- [[Electrónica de potencia]]
- [[Motores]]

---
## [ERRORES] C-rate de batería
- Inventar el C-rate de un pack a partir únicamente de su capacidad.
- Confundir C-rate con corriente absoluta.
- Confundir C-rate con potencia.
- Confundir C-rate con autonomía en minutos.
- Suponer que `20C` implica automáticamente `20 × capacidad` como corriente continua admisible sin comprobar la especificación del fabricante.
- Tratar la capacidad nominal en Ah como capacidad garantizada independientemente de la corriente de descarga y del criterio de corte.
- Confundir **C-rate** con **culombio (C)**, unidad de carga eléctrica; son conceptos diferentes.

---
## [NOTAS] C-rate de batería
Nodo revisado mediante contraste externo (Engineer + GPT cite).

La definición y relación $C_{\mathrm{rate}} = I / Q$ son coherentes con Battery University. Se refuerza la distinción entre **capacidad nominal**, **corriente relativa** y **capacidad realmente disponible bajo una determinada tasa de descarga**.

---
## [REFERENCIAS] C-rate de batería
- Battery University — BU-402: What Is C-rate? (definición; relación C-rate / capacidad / corriente; efecto de la tasa sobre capacidad medida):
  https://batteryuniversity.com/article/bu-402-what-is-c-rate
- Battery University — BU-105: Battery Definitions and what they mean (capacidad y C-rate):
  https://batteryuniversity.com/article/bu-105-battery-definitions-and-what-they-mean
- Battery University — BU-904: How to Measure Capacity (capacidad medida vs condiciones de descarga):
  https://batteryuniversity.com/article/bu-904-how-to-measure-capacity
- Battery University — BU-1101: Glossary (C-rate vs culombio y otras unidades):
  https://batteryuniversity.com/article/bu-1101-glossary

---
## [ESTADO] C-rate de batería
- comprensión: revisada
- revisión: Engineer + contraste externo (GPT cite) · Cursor land `solid`
- jarvis_lote: spine-lote-4
- estado: solid
