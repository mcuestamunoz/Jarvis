# Engineer note — Fase vigilancia / craft-mission software → gate control de vuelo

**Date:** 2026-09-17  
**Authority:** Engineer — listar todo hasta cerrar esta fase y pasar a control de vuelo  
**Live:** `dron-de-vigilancia-doméstico` · ASSEMBLY READY · mission mass CLOSED · routing hotfix await smoke  
**Package:** `0.4.1` (no bump este ciclo — ver §Version)

---

## Fase actual (nombre corto)

**Fase M — Mission craft software (sin calibre / sin banco)**  
Objetivo: que vigilancia deje de ser un cartel + empuje genérico y tenga masa/Continuity/montaje/endurance **declarables** en Jarvis, sin inventar física ni firmware.

**Gate de salida de fase M → Fase C (control de vuelo / enlace):**  
Cuando la cola §Software-only esté CLOSED o PARKED-with-reason, y lo físico §Physical quede explícitamente fuera. Entonces PRIORIDAD pasa a control (fuera o nuevo arco Jarvis — decidir en ★).

---

## §Software-only (trabajar en Jarvis · sin piezas en mano)

| # | ★ / item | Estado | Qué | Depende de |
|---|---|---|---|---|
| **H1** | **`B1-system-definition-b-routing`** | Review PASS · **await smoke** | B owns turns; `añadir bloques` ≠ custom | Engineer smoke §3 |
| **M2** | **`B1-mission-continuity-mount-endurance`** (draft when ★) | **COLA** | Continuity ladder: mount cámara/radio/FC (`mounted_on`) + declarar autonomía objetivo (≥ N min) — cierra gaps #9c/#9d del mass Buy | H1 CLOSED |
| **M3** | **`B1-mission-power-w`** (optional follow-on) | **COLA** | Declarar `power_w` misión → presupuesto eléctrico / autonomía (sin claim de vuelo validado) | M2 o paralelo tras H1 |
| **M4** | **VTX identity** (thin) | **COLA / optional** | Identity-only key vídeo enlace (como cameras) o checklist texto | Engineer ★ si quiere familia nombrada |
| **M5** | **`payload_kg` P2** (displace) | **COLA / only if smoke hurts** | Si P1 + warn no basta en vigilancia | Engineer ★ after living with P1 |
| **M6** | Guide / USER_GUIDE polish | **COLA soft** | Hélices→motores stale line (N3 identity review); mount+endurance one-pager | Anytime |
| **M7** | Phase M closeout note + PRIORIDAD → Fase C | **GATE** | Escribir handoff; no más Buys M salvo residual | M2 mínimo; M3–M5 según ★ |

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
1. Smoke ACCEPT H1 (routing)     ← ahora
2. ★ IC M2 mount + endurance     ← cierra Continuity mission story
3. ★ M3 power_w si autonomía sigue inútil sin draw
4. M4 VTX solo si Engineer nombra familia
5. M7 close Fase M → handoff Fase C
   (Physical sigue PARKED en paralelo; no bloquea M7)
```

---

## §Version

| Opción | Cuándo |
|---|---|
| **Quedarse en `0.4.1`** (recomendado **ahora**) | Los ICs de este ciclo bloquearon bump; el trabajo es continuo sobre el mismo checkpoint |
| **`0.4.2`** | Al cerrar **M7** (Fase M done) — tag + release note “mission mass + Continuity ladder + B routing” |
| **`0.5.0`** | Solo si Fase C mete contrato de producto nuevo (control / enlace) en Jarvis |

**Decisión este commit:** **no bump**. Valorar `0.4.2` en M7.
