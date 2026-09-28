---
id: actuadores
nombre: Actuadores
area: Robótica
subarea: Actuadores
nivel: base
estado: draft
jarvis_relevance: [fs, craft, assistant]
never_invents: [mass_g, power_w, thrust_gf, autonomy_min]
formula_citation: toy/example only
tags: [spine, lote-4]
---

# Actuadores

> **Math (Obsidian):** `$inline$` y bloques `$$`.

---
## [DEFINICION] Actuadores
Un **actuador** es un dispositivo que convierte una señal de control (y energía de alimentación) en una acción física — tipicamente fuerza, par o desplazamiento. En un multicóptero, los motores+hélices son los actuadores de propulsión; servos u otros mecanismos pueden actuar superficies o gimbals.

---
## [INTUICION] Actuadores
El controlador calcula una acción deseada; el **control allocation / mixer** la reparte; los actuadores la materializan dentro de sus límites. Saturar actuadores cambia el comportamiento del lazo — ver [[Control robótico]].

---
## [FUNDAMENTO] Actuadores
Hub:
- [[Motores]]
- [[Transmisión mecánica]]

Sin números de SKU. Límites físicos → datasheet o ensayo.

---
## [EJEMPLO] Actuadores
Jarvis: ESC/motor path en FS; craft monta actuadores desde catálogo.

---
## [PROCEDIMIENTO] Actuadores
1. Definir DoF a actuar.
2. Elegir tipo de actuador.
3. Verificar límites con fuente.
4. Incluir saturación en el diseño de control.

---
## [USO_PROBLEMAS] Actuadores
Diseño de robots, propulsión, manipulación.

---
## [APLICACIONES] Actuadores
**Jarvis:** mapa entre allocation y hardware de propulsión.

---
## [CONEXIONES] Actuadores
- [[Motores]]
- [[Transmisión mecánica]]
- [[Control robótico]]
- [[Electrónica de potencia]]
- [[Motor DC]]

---
## [ERRORES] Actuadores
- Ignorar saturación.
- Inventar thrust/par de un actuador sin OP/cita.

---
## [NOTAS] Actuadores
Borrador Cursor spine-lote-4 (2026-09-28).

---
## [REFERENCIAS] Actuadores
(pendiente cite pass)

---
## [ESTADO] Actuadores
- comprensión: draft agente
- revisión: pendiente Engineer
- jarvis_lote: spine-lote-4
- estado: draft
