# Engineer note — M7 closeout: Fase M DONE → Fase C open

**Date:** 2026-09-18  
**Authority:** Engineer ★ “cerramos”  
**Package:** **`0.4.2`** / tag **`v0.4.2`**  
**SoT phase note (historical):** [engineer_note_fase_m_mission_craft_to_control_gate.md](engineer_note_fase_m_mission_craft_to_control_gate.md)

---

## Decisión de tag

| Opción | Cuándo | Significado |
|---|---|---|
| **`0.4.2` ahora (elegido)** | Al **cerrar M7** | Checkpoint **Fase M done** — mission craft software en Jarvis cerrado |
| `0.4.2` al primer commit de Fase C | **No** | Mezclaría “M cerrado” con “C empezado”; el tip de C aún no tiene Buy |
| **`0.5.0`** | Primer Buy de Fase C que meta **contrato de producto nuevo** (control / enlace) en Jarvis | Salto de fase de producto |

---

## Qué se cierra (Fase M — mission craft software)

Objetivo cumplido: vigilancia puede declarar identidad / masa / montaje / autonomía objetivo / potencia / VTX **sin inventar física ni firmware**.

| # | Buy | Gate |
|---|---|---|
| H1 | `B1-system-definition-b-routing` | ACCEPT |
| P1 | `B1-mission-mass-energy` | ACCEPT |
| M1.5 | `B1-library-cameras-seed` (Phoenix 2) | ACCEPT WITH NOTES |
| M2 | `B1-mission-continuity-mount-endurance` | ACCEPT WITH NOTES |
| M2.1 | `B1-bom-sku-resolved-cameras` | ACCEPT |
| M3 | `B1-mission-power-w` | ACCEPT WITH NOTES |
| M3.1 | `B1-catalog-camera-power-w` | ACCEPT |
| M4 | `B1-mission-vtx-identity` (Zeus 800) | ACCEPT CLOSED |
| M6 | USER_GUIDE polish | CLOSED |
| **M7** | **this note + PRIORIDAD flip + tag** | **CLOSED** |

Software closeout queue 1–5 (intent, nudge, catalog-pair, hygiene, extended identity) ya CLOSED antes de este arco.

**No reabrir** salvo regresión o ★ Engineer.

---

## Qué queda PARK (no bloquea Fase C)

| Item | Nota |
|---|---|
| M5 `payload_kg` P2 | Solo si P1 duele |
| `B1-plate-box` / geometría chasis real | Calibre / cite |
| HD-* / craft OP exacto | Banco — never AHORA without lab |
| Path N disk origin | Schema HOLD |
| Más SKUs cámara / radio catalog W / VTX DC W | Cite rows |
| Autonomía 8 min no demostrada en smoke | Restricción de misión honesta — no gate de fase |

---

## PRIORIDAD tras M7

**Fase C — diseño software de equipo / control de vuelo** — **await Engineer ★** para el primer Buy.

Temas candidatos (fuera SoT craft hasta ★):

- Firmware FC (Betaflight / iNav / PX4…)
- MAVLink / GCS / telemetría
- Bind ELRS / radio commissioning
- PID / rates / filtros
- Mission planner vigilancia
- App / UI piloto

Ninguno está abierto. Distancia: [engineer_note_remaining_to_fase_c_team_software.md](engineer_note_remaining_to_fase_c_team_software.md).

---

## Release note (`v0.4.2`)

Mission craft software checkpoint:

- Continuity mission intent + wizard nudge + B routing
- Mission mass → AUW; mount + endurance ladder; `power_w` declare + Phoenix catalog W
- Cameras seed (Phoenix 2) + VTX seed (Zeus 800) fluid catalog paths
- BOM `[sku]` for cameras/FC/sensors; guide craft-montage sync

Suite at close: **3165** · UI **105** · package **`0.4.2`**.
