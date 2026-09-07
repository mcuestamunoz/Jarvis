# Investigation Review — Minimum Geometric KNOW for a Physical Catalog Object

**Date:** 2026-09-06  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_minimum_physical_object.md](investigation_contract_geometry_minimum_physical_object.md)  
**Report:** [investigation_report_geometry_minimum_physical_object.md](investigation_report_geometry_minimum_physical_object.md)  
**Parent lock:** [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)  
**Base:** `v0.3.8` · Structure CLOSED **2294** · Board B3 closable **2310**

## Verdict

**PASS WITH NOTES**

Governing question answered. Default lean **B1 — Battery declared envelope (L×W×H), representar only** is sound and Buy-ready after the Notes below land in any IC.

Engineer ★ still required before IC / code.

---

## Checklist

| Criterion | Result |
|---|---|
| A–G present; contract questions covered | **Pass** |
| As-is inventory with `file:line` | **Pass** (minor path nits — N4) |
| Minimum bag reusable, not attribute drip | **Pass** — optional vocab, not per-SKU one-offs |
| First family justified with sources | **Pass** — Battery; Frame correctly excluded |
| Honesty / ladder matrix | **Pass** — stops at `representar` |
| MEASURE / fit / CAD viz / Structure PASS out | **Pass** |
| One default lean | **Pass** — **B1** |
| No `src/` this investigation | **Pass** (per investigator; Cursor did not re-diff tree for that claim) |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `BatterySpec` has no L/W/H today | **Confirmed** — `library.py:92-122` |
| `PropertyValue` + `ComponentSpec.properties` accept arbitrary named scalars | **Confirmed** — `schemas/action_schema.py` (`PropertyValue` / `ComponentSpec`) |
| Board `_fields` / `_format_property` generic + unit | **Confirmed** — `workspace/spatial_board.py:181-202` |
| Structure PASS footnote `sin geometría de chasis` | **Confirmed** — `adapters/cli/main.py:147` |
| `bind_battery_from_catalog` docstring claims no CLI entry | **Confirmed stale** — docstring `catalog_bind.py:91-95`; live callers `orchestrator.py:3002-3033`, `4262-4304` (+ `param_definition_session.py`) |
| CNHL `lipo_4s_1500mah` dims on cited page | **Confirmed** — *"Size (1-5mm difference): 37X35X75mm"* (balticdrones) |
| GNB `lipo_6s_6000mah` dims on cited page | **Confirmed** — *"Dimensions: 141x64x41mm"* (rotorama) |
| Spektrum `lipo_4s_5000mah` publishes L×W×H | **Confirmed existence; numbers wrong in report** — see **N1** |
| Propeller already geometry precedent | **Confirmed** — `PropellerSpec.diameter_in`/`pitch_in` (`library.py:208-213`) |
| MotorSpec / EscSpec: no envelope fields | **Confirmed** |

---

## Agreement with report core

1. **Mechanism exists** — first Geometry increment is seed + `BatterySpec` fields + bind project; Board needs no new code for text rows.
2. **Battery first** — sourced rows, single box shape, live pick path, zero Structure PASS collision. Correct over Frame/Motor/ESC for v1.
3. **Frame excluded** — honesty reason (footnote), not only difficulty. Keep.
4. **Ladder** — B1 = `representar` only. Glyph Buy (contract’s B3) correctly deferred.
5. **B2 bundling rejected for first Buy** — family-grain drip risk is real; Cursor concurs.

---

## Notes (must land in IC if Engineer ★ B1)

### N1 — Spektrum seed numbers (load-bearing)

Report §D claims Spektrum shares the CNHL *"37X35X75mm"* pattern. **False.**

Live Spektrum product page for `SPMX50004S100HT` states:

| Axis | Spec |
|---|---|
| Length | 5.45 in (**138.5 mm**) |
| Width | 1.88 in (**47.7 mm**) |
| Height | 1.6 in (**40.7 mm**) |

Conclusion **“3/3 publish full L×W×H” still holds**; only the Spektrum **values** in the report are wrong. IC seed for `lipo_4s_5000mah` must use **138.5 / 47.7 / 40.7**, not 37/35/75.

### N2 — Axis mapping convention

- Spektrum labels Length/Width/Height explicitly → map 1:1.
- CNHL/GNB publish unordered `A×B×C` strings. IC must lock a rule, e.g.  
  **(a)** verbatim manufacturer order → `(length, width, height)` as printed, or  
  **(b)** report’s semantic rule (longest in-plane = length, etc.) with `source_note` recording the page string.

Cursor lean: **(a) + source_note quote** for softcase packs — avoids inventing which axis is “height” when the page does not say. Spektrum uses labeled axes as authority when present.

### N3 — “Zero schema change” wording

Accurate for **`ComponentSpec` / Board**. **`BatterySpec` + `_datos.json` + `bind_battery_from_catalog` projected dict** *do* change — small additive schema, same class as `arm_thickness_mm`. IC should say that plainly (not “no schema”).

### N4 — Citation path nits (non-blocking)

- `action_schema` lives under `schemas/`, not `core/`.
- `spatial_board.py` lives under `workspace/`. Line numbers cited are correct.

### N5 — Unsourced battery rows

`lipo_4s_10000mah` (common in live projects) has **no** `source_url` today — dims stay absent. IC must not invent mm for those rows; Board simply omits the three fields. Optional follow-on: provenance campaign, not this Buy.

### N6 — Docstring drift

Fixing `bind_battery_from_catalog` docstring is a one-line honesty fix; allowed in the IC diff, not a scope driver.

---

## Buy recorded (awaiting Engineer ★)

| Option | Cursor stance |
|---|---|
| B0 | Unnecessary — evidence enough to Buy schema |
| **B1 Battery L×W×H** | **Recommended** — after N1–N2 in IC |
| B2 multi-family | Later, separate IC |
| B3 glyph/preview | Not now (`visualizar`) |
| Defer | Rejected — sources exist |

**Suggested IC title:** *Battery declared envelope (L×W×H) — representar only.*

---

## What Engineer decides next

1. ★ **Buy B1** → Cursor writes IC (N1–N2 locked) → Claude implements  
2. ★ **Buy B0** first (vocab lock only) — Cursor does not recommend  
3. **Defer / re-scope** family (e.g. Motor first) — would need new evidence write-up  

No code until ★.
