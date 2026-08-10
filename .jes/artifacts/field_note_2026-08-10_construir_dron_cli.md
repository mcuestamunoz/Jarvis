# Field Note — New-project CLI session (construir-dron-6ac77f21)

**Date:** 2026-08-10  
**Project:** `workspace/construir-dron-6ac77f21daf5`  
**After:** FN-017 / FN-018  

## Session outcome (honest)

Acquisition Brief + architecture walk **mostly worked** once the user used a registry-valid propeller phrase. End: architecture 4/4, sim PASS (risky), Continuity still lists component gaps.

## What worked

| Step | Result |
|---|---|
| Create wizard (dron, 2.8 kg, 4 motors, helices path, ⌀10, 7500 rpm) | OK |
| Catalog motor pick `#1` | OK (thrust path) |
| `declarar los componentes de propulsión` | Brief hélices (FN-018) ✓ |
| `helices de 10x4.5` | Propellers saved, bloque Propulsión complete ✓ |
| `bateria LiPo 6S 5000mAh, motores…` | Battery saved, Energía complete ✓ |
| `carbono 450g` | Frame ✓ |
| `Pixhawk 4` → `Here3` | Control complete ✓ |
| Architecture 4/4 message | Shown ✓ |

## What blocked / confused

### 1) Bare `10x4.5` loop (FN-019)
Brief advertises `Ej: '10x4.5'` but inference requires keyword (`helice`/`propeller`…).  
`10x4.5` → re-Brief; `ayudame a definir` → re-Brief (by design); `helices de 10x4.5` → success.

### 2) Create already knew helices ⌀/RPM; Phase A still asked to “define propellers”
Create draft stored `helices=10.0" @ 7500 rpm`, then architecture acquisition treated propellers as undeclared component. Dual representation / no handoff from create params → components BOM.

### 3) Continuity vs “Arquitectura 4/4”
Live state:

```text
battery:  completeness=medium  props=[cell_count, battery_capacity_wh]
sensors:  completeness=medium  props=[gps_model]
```

`build_component_bom` classifies **medium** as **incomplete** → Continuity shows `Gap: battery/sensors — incompleto` while UI also says architecture 4/4 complete. Same turn: “gaps de componentes” + “Arquitectura completa”. User hears contradiction.

### 4) Energy next-step copy
After propulsion done: “describe la batería **y motores**” though motors already declared (stale `_BLOCK_COMPONENT_HINTS`).

## Priority recommendation (for Engineer)

| ID | Item | Severity | Notes |
|---|---|---|---|
| FN-019 | Bare `NxP` when pending=propellers + honest example | P0 UX | Contract already drafted; still valid |
| FN-020? | Continuity/BOM: medium vs “complete architecture” messaging | P1 coherence | Don’t call 4/4 “cerrado” while BOM lists gaps — or don’t list medium as gap without saying what’s missing |
| Later | Create helices params → seed/skip propellers component | P1 product | Avoid re-asking what create already captured |
| Polish | Energy hint without “y motores” when motors high | P2 copy | |

**Do not** fold all of this into FN-019. Keep FN-019 narrow (bare size). Capture 2–4 as follow-ups after Engineer ranks them.

## Immediate user workaround

Use `hélices 10x4.5` / `helices de 10x4.5`. Then continue blocks as in this session.
