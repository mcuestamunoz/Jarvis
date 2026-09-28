---
id: punto-de-operacion-vs-capacidad-intrinseca
nombre: Punto de operación vs capacidad intrínseca
area: Ingeniería
subarea: Electrónica / propulsión
nivel: intermedio
estado: draft
jarvis_relevance: [craft, catalog, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-4]
---

# Punto de operación vs capacidad intrínseca

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Punto de operación vs capacidad intrínseca
Un **punto de operación (OP)** es un conjunto de condiciones concretas (tensión, corriente, RPM, pitch de hélice, atmósfera, actitud, …) bajo las cuales se mide o estima una magnitud (p. ej. thrust, consumo).

Una **capacidad intrínseca** (o especificación de componente) describe una propiedad del dispositivo según el fabricante o una norma (p. ej. Kv, corriente máxima continua, masa), **no** automáticamente el rendimiento del sistema motor+hélice+aire en vuelo.

**OP ≠ especificación intrínseca del motor solo.** Confundirlos es un error de honestidad de catálogo.

---
## [INTUICION] Punto de operación vs capacidad intrínseca
“Este motor hace X gf” sin decir a qué V, hélice y RPM es un OP disfrazado de propiedad mágica. En Jarvis, HD-005 y debates XING-E / propellers existen precisamente porque falta un OP medido o una cita clara — no porque la ontología pueda inventar la curva.

---
## [FUNDAMENTO] Punto de operación vs capacidad intrínseca
- **Intrínseco / especificación:** datos de ficha con `source_url` / `identity_status` en `library/`.
- **OP:** medición o estimación en condiciones declaradas (thrust-stand, banco, vuelo instrumentado).
- Un OP puede **informar** un bind o un aviso Continuity; no reemplaza la fila citada del SKU ni autoriza fingir match.
- RF mW de un VTX ≠ W DC de alimentación — familia de confusiones relacionada ([[Corriente y circuitos]]).

---
## [EJEMPLO] Punto de operación vs capacidad intrínseca
HD-005: gap de thrust-stand para un combo motor+hélice+4S. La nota ontológica dice *qué habría que medir*; no inventa la curva. Catálogo: OP estimado temporal vs verificado.

---
## [PROCEDIMIENTO] Punto de operación vs capacidad intrínseca
1. Separar “dato de ficha” vs “dato de ensayo/OP”.
2. Declarar condiciones del OP (V, prop, RPM, …).
3. Citar fuente o marcar estimado_temporary.
4. Nunca fingir match de curvas faltantes.

---
## [USO_PROBLEMAS] Punto de operación vs capacidad intrínseca
Honestidad de catálogo, pairing motor-hélice, interpretación de benches, deuda HD-*.

---
## [APLICACIONES] Punto de operación vs capacidad intrínseca
**Jarvis catalog/craft:** lock conceptual para ComponentLibrary / Continuity honesty. No escribe `library/`.

---
## [CONEXIONES] Punto de operación vs capacidad intrínseca
- [[Motores]]
- [[Motor DC]]
- [[Corriente y circuitos]]
- [[C-rate de batería]]
- [[Electrónica de potencia]]
- [[Sensores de movimiento]]

---
## [ERRORES] Punto de operación vs capacidad intrínseca
- Publicar thrust sin OP.
- Tratar Kv como empuje.
- Inventar curva de banco “para cerrar” HD-*.
- Mezclar RF y DC como la misma potencia.

---
## [NOTAS] Punto de operación vs capacidad intrínseca
Borrador Cursor spine-lote-4 (2026-09-28). Nota **nueva** (no existía como hub).

---
## [REFERENCIAS] Punto de operación vs capacidad intrínseca
(pendiente cite pass — candidatos: docs Jarvis HD-005; textbooks de propulsión eléctrica / motor testing)

---
## [ESTADO] Punto de operación vs capacidad intrínseca
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-4
- estado: draft
