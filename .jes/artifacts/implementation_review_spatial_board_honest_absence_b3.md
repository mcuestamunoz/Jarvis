# Implementation Review — Spatial board honest absence (B3)

**Date:** 2026-09-05  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_spatial_board_honest_absence_b3.md](implementation_contract_spatial_board_honest_absence_b3.md)  
**Report:** [implementation_report_spatial_board_honest_absence_b3.md](implementation_report_spatial_board_honest_absence_b3.md)  
**★:** [engineer_ratification_spatial_board_product_limits.md](engineer_ratification_spatial_board_product_limits.md)  
**Base:** tag **`v0.3.8`** / `f3deae0`

## Verdict

**PASS WITH NOTES**

B3 does what the IC locked: declared-architecture holes become `kind: "slot"` DTOs; undeclared-block keys (`wheels`) stay invisible; empty `components` + blocks is no longer `[]`; visor untouched. Suite **2310** re-run this review.

Honesty slice can close. Residual product Buy remains **B1** (layout in the project tree). N1 is non-blocking on current writers.

---

## Checklist

| Criterion | Result |
|---|---|
| §5 files only (code/docs/tests) | **Pass** — `spatial_board.py`, `test_spatial_board_projector.py`, `ENTRY_MAP.md`, `README.md`. No `ui/`, `project_closure`, `engineering_readiness`, version. `.jes/state` is pre-existing Cursor cycle pointer, not this implement. |
| Slots = missing expected keys of **declared** blocks, deduped | **Pass** — motors-only 4/4 → slots `propellers`,`esc`,`battery`,`frame`,`flight_controller`,`sensors`; `wheels` absent; motors `component` |
| Empty components + 4 blocks → 7 slots | **Pass** |
| No `system_blocks` → no slots | **Pass** |
| Fixture A: empty FC stays `component`; parts stay `part`; missing three are slots | **Pass** (test + independent reconstruct) |
| All declared columns walked (not only occupied roots) | **Pass** — battery slot `x=360`, frame `680`, FC `1000` with only `motors` present |
| `place_slot` / `_emit` does not index `components[key]` | **Pass** |
| No BOM/ERF/Continuity import | **Pass** — grep + `test_projector_module_does_not_import_*` |
| No new C-xxx; ENTRY_MAP one row | **Pass** |
| README slots ≠ BOM | **Pass** |
| Version unbumped (`0.3.8`) | **Pass** |
| Full suite | **2310 passed** (this review) |

---

## Independent checks (this review)

```text
motors-only + 4/4:
  (motors, component, x=40), (propellers, slot, 40), (esc, slot, 40),
  (battery, slot, 360), (frame, slot, 680),
  (flight_controller, slot, 1000), (sensors, slot, 1000)
  wheels: absent

empty + 4/4: 7 slots, motors not duplicated (energy skip)
esc as spec: one node, kind=component
```

`place()` still requires a spec; slots go through `place_slot` → `_emit` only.

---

## Notes

### N1 — `_emit` does not skip if `key` already emitted

If a `BLOCK_TO_COMPONENTS` key were stored **only** as a child (`parent_key` set), the expected-column pass places it and the parent’s child loop places it again — two nodes, same `id`. Reproduced this review with synthetic `esc` under `frame`.

**Not reachable** with current writers (expected keys are roots; frame parts are not in `BLOCK_TO_COMPONENTS`). Does not fail Fixture A or the dual-esc-as-root test.

If touched later: `if key in emitted: return` at the top of `_emit`, or skip already-emitted children. Not required to close B3.

### N2 — Test module docstring still says “no invented slots”

`tests/test_spatial_board_projector.py:1` is stale relative to B3. Hygiene only.

---

## Close

Spatial board honesty (B3) **CLOSED** pending Engineer ack. Next product IC, when opened: **B1** layout in `workspace/` (`views/spatial_layout.json`).
