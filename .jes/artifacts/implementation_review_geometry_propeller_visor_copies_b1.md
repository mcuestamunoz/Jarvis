# Implementation Review — Propeller visor copies from motors spec `motor_count` B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_propeller_visor_copies_b1.md](implementation_contract_geometry_propeller_visor_copies_b1.md)  
**Report:** [implementation_report_geometry_propeller_visor_copies_b1.md](implementation_report_geometry_propeller_visor_copies_b1.md)  
**Buy:** Engineer ★ **`B1-copies-prop`** — N hélices in the **row**, not millimetres

## Verdict

**PASS WITH NOTES**

IC locks held. Propeller `solidCopies` is the motors spec’s `motor_count`, never `current_parameters`, never a default 4, never `quad_x`. Geometry gates are independent (live path: props Ø127, motors no Ø). One card still. `expandSolidCopies` unchanged in behavior. Closable after Engineer smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| `_solid_copies(spec, components)` | **Pass** |
| Motors branch own spec + own geometry | **Pass** — P2–P7 of motor-copies still green |
| Propellers: own geometry + sibling motors `motor_count` | **Pass** — P1 live path |
| Never params / never default 4 / never `quad_x` | **Pass** — P5/P6/P9 + source |
| Range `2..16` integer; omit 1 / 3.5 / missing | **Pass** — P4/P7/P8 |
| No motors component → omit | **Pass** — P10 |
| One `id=="propellers"` | **Pass** — P1 |
| Motor-copies P1 amended (not weakened) | **Pass** — both `solidCopies === 3` |
| `_bom_quantity` body untouched | **Pass** — N5 |
| Catalog Ø not seeded | **Pass** — live SKU still no `diameter_mm` |
| `ui/` behavior empty; optional U5 | **Pass** |
| Version `0.3.8` | **Pass** |
| Fit stub QUEUED | **Pass** |
| `workspace/` empty | **Pass** |
| P1–P10 + motor P1–P7 | **Pass** — Cursor 17/17 |
| Full pytest **2550** | **Pass** — Cursor re-ran |
| UI **39** + typecheck | **Pass** — Cursor re-ran |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Count parser shared; motors still self-read | **Confirmed** `spatial_board.py` |
| `_solid_copies` does not read `current_parameters` | **Confirmed** |
| Other keys always omit | **Confirmed** — final `return None` |
| Live 5min: motors no geo, props Ø127 `solidCopies=4`, one node each, SKU `emax_rs2205_2300` | **Confirmed** `project_spatial_nodes_from_path` |
| Live 10min: same, `solidCopies=3` | **Confirmed** |
| `emax_rs2205_2300` still has no library `diameter_mm` | **Confirmed** |
| `expandSolidCopies` loop body unchanged; U3 strip still holds | **Confirmed** |
| `pyproject.toml` version `0.3.8` | **Confirmed** |

---

## Notes

### N1 — Still a row, not “en el espacio”

Smoke must see **N disks in the presentation row**, not an X of 230. Motors remaining invisible is **ACCEPT**.

### N2 — Stale motor-copies module docstring

`tests/test_geometry_motor_count_instances_b1.py` header still says “propellers untouched.” The **P1 test body** is amended correctly. Cosmetic; not a reopen.

### N3 — Two tests named U5

`layoutSolidsRow` already had a U5. The new expand test is also labelled U5. Harmless. Optional IC U5 used `solidCopies: 3` (IC example said 4). Same proof.

### N4 — Report vs SoT wording

The report’s “mirrors `_bom_quantity`” is the **1 propeller per motor** convention. Visor SoT is **spec-only** (P9). BOM stays params-first. Code is the lock.

### N5 — `project_closure.py` leftover

Uncommitted kit-SKU `has_kit_hardware` hunk is **prior cycle**, not this Buy. `_bom_quantity` itself has no diff.

---

## Phase

Implementation **CLOSED**. Engineer smoke **ACCEPT** ([smoke](engineer_smoke_geometry_propeller_visor_copies_b1.md)): 5min Board shows **4** hélices disks, one card, motors still invisible. Package `0.3.8` · suite **2550**. Stations / disk-origin / remaining pieces still later ★.
