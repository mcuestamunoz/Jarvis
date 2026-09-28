---
id: c-rate-de-bateria
nombre: C-rate de batería
area: Ingeniería
subarea: Electrónica / energía
nivel: base
estado: draft
jarvis_relevance: [craft, catalog, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-4]
---

# C-rate de batería

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] C-rate de batería
El **C-rate** expresa una corriente de carga o descarga **relativa a la capacidad nominal** de la batería. Un rate de $1\mathrm{C}$ corresponde, por definición de ese uso, a una corriente numéricamente igual a la capacidad en Ah (p. ej. 1 C sobre 4 Ah → 4 A), bajo las convenciones del fabricante.

Es una magnitud de **uso / especificación de celda o pack**, no un permiso para inventar Wh, masa o autonomía de un SKU concreto en Jarvis.

---
## [INTUICION] C-rate de batería
“¿A qué ritmo vacío el pack?” Si la capacidad es $Q$ (Ah) y la corriente es $I$ (A), el C-rate de descarga es del orden:

$$
\mathrm{C\text{-}rate} \approx \frac{I}{Q}
$$

(usando las mismas convenciones de capacidad del fabricante; packs reales tienen límites de burst vs continuo, temperatura, etc.).

---
## [FUNDAMENTO] C-rate de batería
- Capacidad nominal $Q$ (Ah o mAh) — dato de ficha / ensayo.
- Corriente de descarga / carga relativa a $Q$.
- Límites: continuo vs pico; degradación; sag — no inventar curvas.
- Continuity puede pedir declarar capacidad honestamente; **esta nota explica el concepto**, no rellena `battery_capacity_wh` desde prosa.

Relacionado: [[Corriente y circuitos]] · [[Punto de operación vs capacidad intrínseca]].

---
## [EJEMPLO] C-rate de batería
Un pack 4S 1500 mAh con descarga 1 C ≈ 1.5 A; a 20 C (si el fabricante lo especifica) ≈ 30 A — **solo si** esa cifra está citada en la ficha. Jarvis no inventa el 20 C.

---
## [PROCEDIMIENTO] C-rate de batería
1. Leer capacidad y rates del datasheet/pack label.
2. Separar continuo vs burst.
3. Declarar en craft solo lo respaldado.
4. No convertir C-rate en autonomía sin modelo energético citado.

---
## [USO_PROBLEMAS] C-rate de batería
Selección de baterías, presupuesto de corriente, seguridad de descarga.

---
## [APLICACIONES] C-rate de batería
**Jarvis craft:** explicación del *porqué* detrás de declarar capacidad/C-rate con honestidad. Catálogo: filas de `library/baterias` con cita — no esta nota.

---
## [CONEXIONES] C-rate de batería
- [[Corriente y circuitos]]
- [[Potencia eléctrica]]
- [[Punto de operación vs capacidad intrínseca]]
- [[Electrónica de potencia]]
- [[Motores]]

---
## [ERRORES] C-rate de batería
- Inventar C-rate o Ah de un pack sin ficha.
- Usar un ejemplo numérico de esta nota como dato de proyecto.
- Confundir C-rate con autonomía en minutos.

---
## [NOTAS] C-rate de batería
Borrador Cursor spine-lote-4 (2026-09-28). Nota **nueva**.

---
## [REFERENCIAS] C-rate de batería
(pendiente cite pass — candidatos: documentación fabricante de LiPo; textbooks de baterías)

---
## [ESTADO] C-rate de batería
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-4
- estado: draft
