# Implementation Report — Live motor visor via sourced SKU rebind B1

**IC:** [implementation_contract_geometry_motor_visor_rebind_b1.md](implementation_contract_geometry_motor_visor_rebind_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2550 → **2555** (2550 + 5 new)

---

## Files changed

| File | Change |
|---|---|
| `tests/test_geometry_motor_visor_rebind_b1.py` | **New.** P1–P5 exactly per IC §4. |

**No other file was touched.** `src/`, `ui/`, `library/`, `workspace/` all confirmed empty of new changes for this cycle (verified via `git diff --stat` on the specific seam files — the existing diffs on `catalog_bind.py`, `spatial_board.py`, `library.py` predate this IC and belong to earlier closed cycles this session; this cycle made zero edits to any of them). No version bump (`pyproject.toml` still `0.3.8`).

---

## Behavior changed

**None.** Per IC §0.8, `src/` was to be touched only if a P-test proved a seam failure. All five tests (P1–P5) passed on the first run with no code change — the already-shipped `bind_motor_from_catalog` → `set_motor_component` (Bug78) → `_solid_copies`/`_geometry_from_spec` seam already glues together correctly:

- `bind_motor_from_catalog(motor_spec_to_suggestion(default_library.get_motor("emax_rs2205s_2300")))` produces a fresh `ComponentSpec` with `catalog_ref.sku == "emax_rs2205s_2300"` and properties `diameter_mm=27.9`, `height_mm=31.7` (and other dims) copied straight from the library row — no `motor_count`.
- `set_motor_component(project_state, bound_spec, power_w=None)` — Bug78's existing-component fallback pulls `motor_count` from the **prior** `project_state.design_properties.components["motors"]` (the mute-SKU spec) since the freshly bound spec doesn't carry it, and writes the merged spec into the new state.
- `project_spatial_nodes` on the resulting state: `_geometry_from_spec` picks the `disk` branch (`diameter_mm=27.9`) — `height_mm` alone never combines with a missing `length_mm`/`width_mm` into a box/cylinder, confirmed by direct read of `_geometry_from_spec`'s box-requires-full-triple gate. `_solid_copies` draws `N` from the spec's own (now Bug78-preserved) `motor_count`. Rebinding to the mute SKU still yields no geometry/no copies, since that library row still has no `diameter_mm`. Propellers' cross-read of the sibling motors' `motor_count` (Propeller visor copies B1) is unaffected by which motor SKU is bound — only by the count.

---

## Tests added / executed

New: `tests/test_geometry_motor_visor_rebind_b1.py` — 5/5 passing:
- P1: S-SKU rebind with `motor_count=4` → motors disk 27.9, `solidCopies==4`, `catalog_ref.sku` correct, one motors node; propellers still `solidCopies==4`, still disk.
- P2: same with `motor_count=3` → motors `solidCopies==3` (not coerced to 4).
- P3: mute-SKU rebind → motors no geometry/no `solidCopies`; propellers unaffected at 4.
- P4: library census — `emax_rs2205_2300.diameter_mm is None`; `emax_rs2205s_2300.diameter_mm == 27.9`.
- P5: `height_mm` appears as a `31.7 mm` card field; `geometry.shape == "disk"` (never a cylinder).

Full suite: `python -m pytest -q` → **2555 passed**, 0 failed. Pre-existing motor-copies (`test_geometry_motor_count_instances_b1.py`) and propeller-copies (`test_geometry_propeller_visor_copies_b1.py`) suites untouched and still green.

`ui/` not touched — no `npm test`/`typecheck` run needed for this cycle (no `.ts`/`.tsx` edit made).

---

## Non-goals honored

No `diameter_mm`/`height_mm` seeded onto `emax_rs2205_2300` (still `None`, confirmed live via P4). No merge of the two EMAX rows. No cylinder (box branch requires the full L×W×H triple; motor spec never carries `length_mm`/`width_mm`). No millimetre stations, no disk-origin pose change, no `_bom_quantity` change, no `"cabe"` on disks, no invented `max_watts` on the S SKU, no version bump, no `workspace/` mutation.

---

## Remaining risks

- None identified — this cycle only added regression coverage over an already-shipped, already-tested seam; no new code path was introduced.
- Live Engineer smoke (`autonomía-de-5min`/`autonomía-de-10min` via IDLE `cambiar motor`) is unverified by this report — per IC §6/§1 ("Do not mutate `workspace/`"), that step is explicitly the Engineer's own smoke pass, recorded separately in `engineer_smoke_geometry_motor_visor_rebind_b1.md` after Cursor review, not this implementation's responsibility.
- As already accepted by lock #7: rebinding does change live physics numbers (S-row thrust, null `max_watts`) — this is explicitly ACCEPT, not a regression to chase.
