---
id: corriente-y-circuitos
nombre: Corriente y circuitos
area: Física
subarea: Electromagnetismo
nivel: base
estado: draft
jarvis_relevance: [craft, catalog, fs, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-4]
---

# Corriente y circuitos

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Corriente y circuitos
La **corriente eléctrica** es el flujo de carga. Un **circuito** relaciona tensiones, corrientes y elementos (resistencias, fuentes, cargas) bajo leyes de conservación y constitutivas (p. ej. Ohm en el caso resistivo lineal). La **potencia eléctrica** relaciona $P$ con $V$ e $I$ según el contexto del circuito.

---
## [INTUICION] Corriente y circuitos
En un craft: la batería suministra energía; ESC/motores/carga consumen corriente; cables y conectores imponen caídas y límites. Declarar Wh o W “honestos” en Continuity exige entender *qué* se está midiendo o estimando — no inventar amperios de un SKU.

---
## [FUNDAMENTO] Corriente y circuitos
Hojas del hub:
- [[Corriente eléctrica]]
- [[Voltaje]]
- [[Resistencia eléctrica]]
- [[Ley de Ohm]]
- [[Potencia eléctrica]]

Forma toy (no usar como dato de catálogo):

$$
P = V I
$$

(en corriente continua ideal; circuitos reales y RF tienen matices — p. ej. RF mW ≠ DC W de alimentación).

Ver también [[C-rate de batería]] y [[Electrónica de potencia]].

---
## [EJEMPLO] Corriente y circuitos
Jarvis Continuity pide declarar capacidad/energía con honestidad; el *porqué* de corriente y potencia vive aquí. Un VTX con potencia RF citada no autoriza inventar el consumo DC sin fuente.

---
## [PROCEDIMIENTO] Corriente y circuitos
1. Declarar si se habla de DC, promedio, pico o RF.
2. Identificar fuente y carga.
3. Usar datos citados para SKUs.
4. No mezclar RF mW con W de batería sin modelo explícito.

---
## [USO_PROBLEMAS] Corriente y circuitos
Análisis de circuitos, presupuesto de potencia, dimensionado de batería/cables.

---
## [APLICACIONES] Corriente y circuitos
**Jarvis craft/catalog:** vocabulario de honestidad energética. **FS:** ESC/motor como cargas, no números inventados.

---
## [CONEXIONES] Corriente y circuitos
Hojas del hub:
- [[Corriente eléctrica]]
- [[Voltaje]]
- [[Resistencia eléctrica]]
- [[Ley de Ohm]]
- [[Potencia eléctrica]]

Spine:
- [[C-rate de batería]]
- [[Electrónica de potencia]]
- [[Punto de operación vs capacidad intrínseca]]
- [[Motores]]

---
## [ERRORES] Corriente y circuitos
- Igualar potencia RF de un VTX a potencia DC de la batería.
- Inventar A/W de un componente sin cita.
- Usar $P=VI$ fuera de su régimen sin decirlo.

---
## [NOTAS] Corriente y circuitos
Borrador Cursor spine-lote-4 (2026-09-28).

---
## [REFERENCIAS] Corriente y circuitos
(pendiente cite pass)

---
## [ESTADO] Corriente y circuitos
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-4
- estado: draft
