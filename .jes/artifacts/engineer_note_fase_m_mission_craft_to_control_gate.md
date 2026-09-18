# Engineer note — Fase vigilancia / craft-mission software → gate control de vuelo

**Date:** 2026-09-17  
**Authority:** Engineer — listar todo hasta cerrar esta fase y pasar a control de vuelo  
**Live:** `dron-de-vigilancia-doméstico` · mission craft software **CLOSED** (H1 · P1 · M1.5–M3.1) · **M7 GATE AHORA**  
**Package:** `0.4.1` (valorar **`0.4.2`** al cerrar M7)

---

## Fase actual (nombre corto)

**Fase M — Mission craft software (sin calibre / sin banco)** — **software path DONE**  
Objetivo cumplido: vigilancia tiene identidad/masa/montaje/endurance/potencia **declarables** (+ Phoenix catalog mass+W), sin inventar física ni firmware.

**Gate de salida de fase M → Fase C (control de vuelo / diseño software de equipo):**  
**M7** — closeout note + PRIORIDAD flip. M4/M5/M6 = PARK unless Engineer ★. Physical § queda fuera.

---

## §Software-only (trabajar en Jarvis · sin piezas en mano)

| # | ★ / item | Estado | Qué | Depende de |
|---|---|---|---|---|
| **H1** | **`B1-system-definition-b-routing`** | **CLOSED** | B owns turns; `añadir bloques` ≠ custom | smoke ACCEPT 2026-09-17 |
| **M1.5** | **`B1-library-cameras-seed`** | **CLOSED** | Phoenix 2 + fluid path (bind/rebind/refresh/mass) | smoke ACCEPT WITH NOTES 2026-09-18 |
| **M2** | **`B1-mission-continuity-mount-endurance`** | **CLOSED** | Continuity ladder: mount + autonomía objetivo | smoke ACCEPT WITH NOTES 2026-09-18 |
| **M2.1** | **`B1-bom-sku-resolved-cameras`** | **CLOSED** | Display `[sku]` for cameras/FC/sensors | smoke ACCEPT 2026-09-18 |
| **M3** | **`B1-mission-power-w`** | **CLOSED** | Declarar `power_w` misión → presupuesto eléctrico / autonomía (sin claim de vuelo validado) | smoke ACCEPT WITH NOTES 2026-09-18 |
| **M3.1** | **`B1-catalog-camera-power-w`** | **CLOSED** | Phoenix `power_w=1.0` (200mA@5V I×V) → bind + mirror | smoke ACCEPT 2026-09-18 |
| **M4** | **`B1-mission-vtx-identity`** | **✅ CLOSED** | Zeus 800 + fluid path; smoke PASS | [review ACCEPT CLOSED](implementation_review_mission_vtx_identity_b1.md) |
| **M5** | **`payload_kg` P2** (displace) | **PARK / if needed** | Si P1 + warn no basta | Solo ★ |
| **M6** | Guide / USER_GUIDE polish | **CLOSED** | Stale lines cleanup | Engineer: Claude paralelo 2026-09-18 |
| **M7** | Phase M closeout + PRIORIDAD → Fase C | **PRIORIDAD / GATE** | Handoff; tag `0.4.2` | **AHORA** — mínimo craft DONE |

### Ya CLOSED esta fase (no reabrir)

| # | Buy | Nota |
|---|---|---|
| 1–5 | Software closeout queue | Continuity intent · wizard nudge · catalog-pair · hygiene · extended identity |
| P1 | **`B1-mission-mass-energy`** | `mass_g` → AUW + ladder mass; smoke ACCEPT |

---

## §Physical / lab (PARKED — no PRIORIDAD AHORA)

| Item | Por qué park | Cuándo |
|---|---|---|
| **`B1-plate-box`** / placa L×W real | Calibre o cite OEM | Engineer bag |
| Stack attest / geometría chasis | Depende placa real | Tras plate-box |
| **HD-005** craft OP XING-E+Gemfan exacto | Banco / manufacturer combo | Lab |
| ESC H “de verdad” / HD-* siblings | Lab | Never AHORA without bench |
| Path N disk origin | Schema HOLD | No reabrir |
| `library/cameras` physics bags | Cite rows Engineer | Supersedes declared mass |
| Axial hélices↔motores geometry | Facts missing | Parked |

---

## §Fuera de Jarvis SoT / Fase C (después del gate M7)

No son “siguiente Buy” de craft-mission. Abrir solo tras M7 ★:

| Tema | Nota |
|---|---|
| Firmware FC (Betaflight / iNav / PX4…) | Fuera SoT actual |
| MAVLink / GCS / telemetría viva | Fuera o producto nuevo |
| Bind ELRS / radio link commissioning | Campo / herramienta externa |
| Tuning PID / rates / filtros | Vuelo real |
| Mission planner rutas vigilancia | Producto distinto |
| App / UI de piloto | Fuera salvo ★ explícito |

---

## Attack order (recomendado)

```text
1–3. DONE — cameras seed · mount/endurance · power declare + catalog W
4. ★ M7 close Fase M → Fase C (diseño software de equipo / control)
   (M4 VTX / M5 P2 / M6 polish = PARK unless ★)
```

### Cuánto falta hasta “diseño software de equipo” (Fase C)

| Capa | Estado |
|---|---|
| **Mission craft en Jarvis (Fase M software)** | **DONE** — H1, P1, M1.5–M3.1 CLOSED |
| **M7 gate** | **1 paso administrativo** — nota de closeout + PRIORIDAD → Fase C + opcional tag `0.4.2` |
| **M4–M6** | No bloquean el gate (PARK) |
| **Físico / lab** | PARKED — no es prerrequisito de Fase C |
| **Fase C propiamente** | Empieza **después** de M7: firmware FC, MAVLink/GCS, bind ELRS, PID, mission planner, app piloto |

**Respuesta corta:** el camino de software de misión en Jarvis está cerrado. Queda **M7** (cierre formal) y luego el arco nuevo de **control / enlace** — eso es el “diseño de software de equipo”, aún no empezado en SoT.

---

## §Version

| Opción | Cuándo |
|---|---|
| **Quedarse en `0.4.1`** (recomendado **ahora**) | Los ICs de este ciclo bloquearon bump; el trabajo es continuo sobre el mismo checkpoint |
| **`0.4.2`** | Al cerrar **M7** (Fase M done) — tag + release note “mission mass + Continuity ladder + B routing” |
| **`0.5.0`** | Solo si Fase C mete contrato de producto nuevo (control / enlace) en Jarvis |

**Decisión este commit:** **no bump**. Valorar `0.4.2` en M7.
