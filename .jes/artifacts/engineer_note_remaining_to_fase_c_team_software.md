# Engineer note — Remaining distance to team flight-control software (Fase C)

**Date:** 2026-09-18  
**Authority:** Cursor (docs sync after M3.1 ACCEPT)  
**SoT phase note:** [engineer_note_fase_m_mission_craft_to_control_gate.md](engineer_note_fase_m_mission_craft_to_control_gate.md)

---

## Pregunta

¿Cuánto falta para llegar a **diseño de software de equipo** (control de vuelo / enlace)?

## Respuesta

| Tramo | Queda |
|---|---|
| **Mission craft en Jarvis (Fase M software)** | **0 Buys obligatorios** — H1 · P1 · M1.5–M3.1 **CLOSED** |
| **M7 (gate administrativo)** | **1 paso** — nota de closeout + PRIORIDAD → Fase C + opcional tag **`0.4.2`** |
| **M4 VTX / M5 P2 / M6 polish** | **0** si los dejas en PARK (no bloquean) |
| **Físico / banco** | No es prerrequisito de Fase C |
| **Fase C (el “software de equipo”)** | **Empieza después de M7** — firmware FC, MAVLink/GCS, bind ELRS, PID, planner, app piloto |

```text
[DONE: craft misión] ──► [M7 closeout] ──► [Fase C: diseño software de equipo]
                              ▲
                         AHORA (1 gate)
```

**En una frase:** el software de misión en Jarvis ya está; falta **cerrar formalmente Fase M (M7)** y entonces abrir el arco nuevo de **control/enlace** — ese sí es diseño de software de equipo, todavía no empezado en SoT.
