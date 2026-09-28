---
id: motor-dc
nombre: Motor DC
area: Robótica
subarea: Actuadores / Motores
nivel: base
estado: draft
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-4]
---

# Motor DC

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Motor DC
Un **motor de corriente continua** (en sentido amplio: brushed DC o, en la práctica de drones, **BLDC** controlado por ESC) convierte potencia eléctrica en **par mecánico** en un eje. La relación entre tensión, corriente, RPM y par depende del tipo, del ESC y de la carga (p. ej. hélice).

---
## [INTUICION] Motor DC
Más corriente (dentro de límites) → más par disponible; la carga (hélice + aire) fija el punto de operación junto con la batería/ESC. Un número de catálogo (Kv, corriente máxima) **no** es el thrust en vuelo — el thrust es de un **OP** medido o estimado con honestidad.

---
## [FUNDAMENTO] Motor DC
Ideas (mapa, sin SKU):

- Actuador eléctrico → par / velocidad de eje.
- ESC: electrónica de potencia entre batería y motor ([[Electrónica de potencia]], [[PWM]]).
- Con hélice: el sistema motor+hélice+aire define empuje en un OP — ver [[Punto de operación vs capacidad intrínseca]].
- Límites térmicos y de corriente: no inventar amperios de un pack/motor sin fuente.

---
## [EJEMPLO] Motor DC
Wikilink `[[Motor DC]]` ya colgaba desde [[Motores]] y desde el crosswalk FS conceptual (mixer/actuadores). En Jarvis craft, el SKU concreto vive en `library/`; aquí solo el concepto.

---
## [PROCEDIMIENTO] Motor DC
1. Declarar brushed vs BLDC + tipo de ESC.
2. Declarar carga (hélice, reductora…).
3. Buscar datos citados para el SKU (Kv, I_max, masa…).
4. Separar especificación de catálogo vs medida de banco (OP).

---
## [USO_PROBLEMAS] Motor DC
Selección de propulsión, control de velocidad, pairing motor-hélice.

---
## [APLICACIONES] Motor DC
**Jarvis:** vocabulario para actuadores FS y bind craft. No sustituye filas de `library/motores`.

---
## [CONEXIONES] Motor DC
- [[Motores]]
- [[Actuadores]]
- [[Electrónica de potencia]]
- [[Corriente y circuitos]]
- [[Punto de operación vs capacidad intrínseca]]
- [[Momento y rotación]]

---
## [ERRORES] Motor DC
- Usar Kv como si fuera thrust.
- Inventar corriente/thrust de un modelo concreto sin cita.
- Confundir comando DShot/PWM con par real en vuelo.

---
## [NOTAS] Motor DC
Borrador Cursor spine-lote-4 (2026-09-28). Materializa dangling `[[Motor DC]]`.

---
## [REFERENCIAS] Motor DC
(pendiente cite pass)

---
## [ESTADO] Motor DC
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-4
- estado: draft
