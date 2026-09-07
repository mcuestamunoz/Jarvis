# Investigation Review — Flight Controller Declared Geometry (Geometry axis)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_fc_envelope.md](investigation_contract_geometry_fc_envelope.md)  
**Report:** [investigation_report_geometry_fc_envelope.md](investigation_report_geometry_fc_envelope.md)  
**Parents:** ESC B1 @ **2327** · Board smoke Battery+Motor+ESC ACCEPT · live FC card = `model` only

## Verdict

**PASS WITH NOTES**

Governing question answered. Catalog absence is first-class and correctly drives a **non–Battery-shaped** path. Pixhawk 4 box **44×84×12 mm** is cross-confirmed (PX4 docs + Holybro). Mount/30.5 rejected for lack of source. Default lean **B1 — identity-linked dims table (`pixhawk_4` only), no catalog / no `catalog_ref`** is Buy-ready.

Engineer ★ still required before IC / code.

---

## Checklist

| Criterion | Result |
|---|---|
| A–G present | **Pass** |
| As-is + catalog absence first-class | **Pass** |
| Field bag + live source quotes | **Pass** — box accepted; mount rejected; Mini excluded |
| Honesty / ladder + catalog_ref honesty | **Pass** |
| One default lean | **Pass** — **B1** |
| No `src/` this investigation | **Pass** (per investigator) |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| No `library/fc/` · no `FcSpec` · no `bind_flight_controller_*` | **Confirmed** — `library/` = 6 families only; greps clean |
| Extractor returns `model` only today | **Confirmed** — `aerial.py:538-564` |
| Live project FC = model / `catalog_ref: null` | **Confirmed** — `workspace/autonomía-de-10min-…/state.json` |
| PX4 docs: Weight 15.8g · Dimensions **44x84x12mm** | **Confirmed** — `docs.px4.io/.../pixhawk4.html` this session |
| Holybro: Dimensions **44x84x12mm** · plastic 33.3g / aluminum 49g | **Confirmed** — `holybro.com/products/pixhawk-4` this session |
| Mount pattern on those pages | **Absent** — agree reject for this increment |
| Completeness ignores geometry | **Confirmed** — model confidence only |

---

## Agreement with report core

1. **Skip B0 `library/fc/` foundation** for this increment — correct; would be a side-quest relative to attaching one sourced box.
2. **Accept `length_mm` / `width_mm` / `height_mm` for `pixhawk_4` only** — correct; same box vocab as Battery/ESC.
3. **Reject mount/30.5 without source** — correct; keeps ESC’s “different geometric idea” separation.
4. **Exclude Mini** without inventing dims — correct.
5. **Identity-linked table beside `FLIGHT_CONTROLLER_MAP`, not free-text digit parse** — correct distinction; satisfies contract’s “no free-text mm extractor” intent.
6. **Architectural divergence must stay visible** — agree; do not blur into “catalog bind.”

---

## Notes (must land in IC if Engineer ★ B1)

### N1 — Seed values + axis rule (locked)

| Identity | L / W / H mm | Rule |
|---|---|---|
| `pixhawk_4` | **44 / 84 / 12** | Verbatim `44×84×12` order → `length_mm` / `width_mm` / `height_mm` (sources unlabeled) |

`source_note` (or table fields) must cite both PX4 docs + Holybro agreement. Prefer both URLs in provenance.

### N2 — Reachability / existing projects (honesty, not a blocker)

Dims attach **at extraction time**. Projects that already have `flight_controller` saved with `model` only (e.g. `autonomía-de-10min`) **will not** gain mm until FC is re-declared (or equivalent writer re-run). Smoke path = re-say “Pixhawk 4” (or targeted writer), not catalog rebind. IC / report must say this plainly.

### N3 — `PropertyValue.source` / confidence

Match existing FC `model` / catalog-dim convention: `source="declared"`, confidence inherited from the model match (0.9 for numbered Pixhawk 4). Do **not** invent a new provenance enum in this IC.

### N4 — No catalog_ref / no bind / no library/fc

IC done-criteria: `catalog_ref` stays `None`; no `FcSpec`; no `bind_flight_controller_*`; no Continuity wizard. Implementation report must state the divergence in one sentence.

### N5 — Completeness unchanged

`_flight_controller_completeness` must **not** start requiring dims. Models without table entries stay `model`-only.

### N6 — Do not conflate box with stack/fit

Forbid stack/mount/fit CLI or claim copy from these three fields. Mass/weight out of scope (PX4 15.8g vs Holybro cased weights — flag only, do not seed).

### N7 — Table location

Keep table in `aerial.py` next to `FLIGHT_CONTROLLER_MAP` (or same module constant block). Do **not** open a parallel knowledge subsystem or `library/fc/` “just in case.”

---

## Buy recorded — Engineer ★ B1 (2026-09-07)

| Option | Outcome |
|---|---|
| B0 catalog foundation | Not bought |
| **B1 identity-linked Pixhawk 4 box** | **★ Bought** → [IC](implementation_contract_geometry_fc_envelope_b1.md) |
| B2 / B3 / Defer | Not now |

---

## What Engineer decides next

~~1. ★ Buy B1 → Cursor writes IC → Claude implements~~ **Done — IC open**  
Claude implements IC → Cursor review → optional Board re-declare smoke.
