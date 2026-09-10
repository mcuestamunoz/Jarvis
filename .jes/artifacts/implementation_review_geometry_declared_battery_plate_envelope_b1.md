# Implementation Review — Declared battery envelope + Main Plate L×W B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_declared_battery_plate_envelope_b1.md](implementation_contract_geometry_declared_battery_plate_envelope_b1.md)  
**Report:** [implementation_report_geometry_declared_battery_plate_envelope_b1.md](implementation_report_geometry_declared_battery_plate_envelope_b1.md)  
**Buy:** Engineer ★ **B1-declared-envelope** (battery + plate juntos)

## Verdict

**PASS WITH NOTES**

Parser + writer + IDLE bridge match the IC. No catalog seed. No 230-as-box. Plate box unlocks pose origin (P7). Suite **2583**. Live smoke is the Engineer’s (type real mm).

---

## Checklist

| Criterion | Result |
|---|---|
| P1–P10 | **Pass** — Cursor 10/10 |
| Parser kinds SET / CLEAR / AMBIGUOUS_PLATE / INCOMPLETE / NONE | **Pass** |
| `\brespecto\b` → NONE | **Pass** — P8 |
| Battery needs three numbers | **Pass** — P3 |
| Plate two-number: parser `height_mm is None`; H from `thickness_mm` | **Pass** — P2 (see N1) |
| Writer only `battery` / `is_frame_plate_key` | **Pass** — P6 |
| `thickness_mm` preserved | **Pass** — P2 |
| `source=declared` | **Pass** — P1 |
| No `set_battery_component` on this path | **Pass** — envelope writer only |
| No `wheelbase_mm` / `body_*` in parser or writer | **Pass** |
| `lipo_3s_2200mah` still no L×W×H in seed | **Pass** |
| Rooster plates still no L×W in seed | **Pass** |
| Pose origin after plate SET | **Pass** — P7 |
| IDLE after pose, before FN-005 | **Pass** — `orchestrator.py` |
| Public noun wrappers; no `mounted_on` `_` imports | **Pass** (see N3) |
| `library/` / `ui/` / `workspace/` / visor X | **Pass** — not this Buy |
| Full pytest **2583** | **Pass** — Cursor re-ran |
| Version `0.3.8` | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Confirm copy `Declarado: battery 80 x 34 x 22 mm (source=declared).` | **Confirmed** — live P10 probe |
| Forbidden tokens in that message | **Confirmed** — no cabe / verificado / ensamblado / 230 |
| P10 `cambiar bateria` still lists catalog | **Confirmed** — `battery_suggestions` n=10 (test only asserts status; see N2) |
| Frame `wheelbase_mm` stays 230 after plate 100×100 | **Confirmed** — P2 |
| Refresh keeps declared dims on mute 3S row | **Confirmed** — P9 |

---

## Notes

### N1 — P2 thickness fill is test-side, not orchestrator

P2 asserts parser `height_mm is None`, then the **test** passes `thickness` into the writer. `_try_handle_declared_box_envelope`’s two-number plate apply (read `thickness_mm`, “Alto tomado del thickness_mm citado”) has **no** pytest. Report’s “applied at the orchestrator layer” overstates P2. The apply code matches the IC; smoke will hit it. Not a fail.

### N2 — P10 does not assert `battery_suggestions`

IC asked that `cambiar batería` still open the catalog. The test only checks `status in {interactive, ok}`. Cursor probe: catalog **does** open (10 rows). Optional tighten later.

### N3 — `_normalize_help`

Parser imports `_normalize_help` from `motor_catalog_assist` (same as pose). IC forbade private `_` names on the **mount** module. Pose precedent. Acceptable.

### N4 — Engineer types the millimetres

Fixtures 80/34/22 and 100/100 are not live SoT. 3D plate == 230 only if you type 230 — that remains a smoke fail.

---

## Phase

Implementation **REVIEWED PASS WITH NOTES**. Wait Engineer smoke on `autonomía-de-5min`. Package `0.3.8` · suite **2583**.
