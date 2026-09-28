---
id: motores
nombre: Motores
area: Robótica
subarea: Actuadores
nivel: base
estado: draft
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-4]
---

# Motores

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Motores
En robótica y vehículos, un **motor** (eléctrico) es un **actuador** que convierte energía eléctrica en movimiento rotatorio (o lineal, según el tipo). Produce **par** y, a través de la mecánica (hélices, ruedas, transmisiones), puede producir fuerzas de propulsión o movimiento de juntas.

---
## [INTUICION] Motores
El controlador pide fuerzas/momentos; el **mixer/allocation** reparte esa demanda a comandos por motor; el ESC convierte el comando en corriente/PWM/DShot hacia el motor; el motor + hélice (u otra carga) produce thrust/par. La nota de teoría no declara Kv, thrust ni W de un SKU — eso es `library/` con cita.

---
## [FUNDAMENTO] Motores
Mapa de tipos (hojas del hub):

- [[Motor DC]] — corriente continua / brushless tip en multicópteros (concepto)
- [[Servo motor]]
- [[Motor paso a paso]]
- [[Motor eléctrico robótica]]

Relaciones: [[Actuadores]] · [[Electrónica de potencia]] · [[Punto de operación vs capacidad intrínseca]] · [[Momento y rotación]]

**OP ≠ intrínseco:** el empuje medido en un punto de operación no es una propiedad intrínseca del motor solo — ver nota dedicada.

---
## [EJEMPLO] Motores
Jarvis FS: mixer → ESC stub / DShot encode — comandos a actuadores en sim. Craft: bind de motores desde catálogo citado. Ninguno de los dos inventa curvas de thrust.

---
## [PROCEDIMIENTO] Motores
1. Definir qué movimiento se necesita (par, RPM, thrust).
2. Elegir tipo de motor y carga (hélice, reductora…).
3. Declarar OP de interés (V, I, RPM, pitch…) con fuente.
4. No copiar un número de apunte como dato de SKU.

---
## [USO_PROBLEMAS] Motores
Selección de actuadores, dimensionado, control de movimiento, propulsión.

---
## [APLICACIONES] Motores
**Jarvis:** puente entre [[Control robótico]] (allocation) y catálogo craft. HD-005 / OP debates viven en honestidad de catálogo + [[Punto de operación vs capacidad intrínseca]].

---
## [CONEXIONES] Motores
Hojas del hub:
- [[Actuador]]
- [[Motor eléctrico robótica]]
- [[Servo motor]]
- [[Motor paso a paso]]
- [[Motor DC]]

Spine:
- [[Actuadores]]
- [[Control robótico]]
- [[Electrónica de potencia]]
- [[Corriente y circuitos]]
- [[C-rate de batería]]
- [[Punto de operación vs capacidad intrínseca]]

---
## [ERRORES] Motores
- Tratar thrust de un OP de banco como Kv/“capacidad intrínseca” del motor.
- Inventar W/thrust de un SKU sin `source_url` / ensayo.
- Confundir comando ESC con dinámica de la planta.

---
## [NOTAS] Motores
Borrador Cursor spine-lote-4 (2026-09-28). Engineer + GPT cite → `solid`.

---
## [REFERENCIAS] Motores
(pendiente cite pass)

---
## [ESTADO] Motores
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-4
- estado: draft
