# Implementation Contract — Flight Controller declared box (Pixhawk 4 only, identity-linked, no catalog) — representar only

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2332**)  
**Review:** [implementation_review_geometry_fc_envelope_b1.md](implementation_review_geometry_fc_envelope_b1.md)  
**Report:** [implementation_report_geometry_fc_envelope_b1.md](implementation_report_geometry_fc_envelope_b1.md)  
**Parents:**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [investigation_contract_geometry_fc_envelope.md](investigation_contract_geometry_fc_envelope.md)
- [investigation_report_geometry_fc_envelope.md](investigation_report_geometry_fc_envelope.md)
- [investigation_review_geometry_fc_envelope.md](investigation_review_geometry_fc_envelope.md) — **PASS WITH NOTES**
- Battery B1 @ **2316** · Motor B1 @ **2323** · ESC B1 @ **2327**

**Type:** Additive declared geometry on free-text FC identity recognition. Display-only KNOW (`representar`).  
**Not** a catalog family. **Not** `catalog_ref` / bind. **Not** visualization. **Not** fit/stack. **Not** MEASURE/CAD/FEA.

**Baseline:** package **`0.3.8`** · ESC B1 CLOSED suite **2327**

**Architectural divergence (locked honesty):** This Buy is **not** Battery/Motor/ESC-shaped. There is no `library/fc/`, no `FcSpec`, no `bind_flight_controller_*`. Dims attach inside `extract_flight_controller_properties` from a static identity-linked table keyed by the same canonical `model` string already produced today. Implementation report **must** state this in one plain sentence.

**Output:** `.jes/artifacts/implementation_report_geometry_fc_envelope_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — identity-linked `pixhawk_4` box only |
| 2 | Ladder rung | **`representar` only** — text via generic Board `_fields`; no glyph |
| 3 | Mechanism | **Table beside `FLIGHT_CONTROLLER_MAP`** in `aerial.py` — **not** `library/fc/` / `FcSpec` / bind |
| 4 | **N1** values | **44 / 84 / 12** mm — verbatim `44×84×12` → `length_mm` / `width_mm` / `height_mm` |
| 5 | Identity scope | **`pixhawk_4` only** — no Mini, no 6-series, no betaflight backfill |
| 6 | **N4** catalog | **No** `catalog_ref`; **no** `bind_flight_controller_*`; **no** Continuity FC wizard |
| 7 | **N5** completeness | **Unchanged** — dims do **not** gate `_flight_controller_completeness` |
| 8 | **N6** stack/fit/mass | No stack/mount/fit/“cabe” copy; **no** mass/weight field seeded |
| 9 | **N2** reachability | Existing saved FC components gain dims only on **re-declare** (or equivalent re-extract + write) |
| 10 | Physics / PASS | Dims never drive calc; Structure PASS * unchanged |

---

## 1. You

- Do **not** create `library/fc/`, `FcSpec`, loader, or `bind_flight_controller_*`.
- Do **not** set `catalog_ref` on FC components.
- Do **not** touch Battery / Motor / ESC / Frame schema or seeds.
- Do **not** add free-text digit/mm parsing from the user message (table lookup only after model match).
- Do **not** seed `pixhawk_4_mini` or any other model.
- Do **not** add `mount_pattern_mm` / 30.5 / stack height / fit logic or CLI copy.
- Do **not** seed mass/weight (PX4 15.8g vs Holybro cased weights = known disagreement; out of scope).
- Do **not** change `_flight_controller_completeness` to require dims.
- Do **not** bump package version unless Engineer asks after review.
- Full suite green. Zero weakened tests.
- Write `implementation_report_geometry_fc_envelope_b1.md` when done.

---

## 2. Intent

```text
User text "Pixhawk 4"
        ↓
FLIGHT_CONTROLLER_MAP → model = "pixhawk_4"   (already exists)
        ↓
FLIGHT_CONTROLLER_DIMENSIONS["pixhawk_4"]     (new, this IC)
  length_mm=44, width_mm=84, height_mm=12
  + provenance fields (urls / note)
        ↓
extract_flight_controller_properties
  → {model, length_mm, width_mm, height_mm} as PropertyValue
        ↓
existing FC writer path → ComponentSpec.properties
        ↓
Board _fields (no ui/ change)
```

No new subsystem. No catalog bind.

---

## 3. Locked behavior

### 3.1 Table — `FLIGHT_CONTROLLER_DIMENSIONS` (name may vary slightly; keep next to map)

In `src/jarvis/domains/aerial.py`, next to `FLIGHT_CONTROLLER_MAP`:

- Key: canonical model string `"pixhawk_4"` only.
- Required numeric fields: `length_mm=44`, `width_mm=84`, `height_mm=12` (floats OK: `44.0` etc.).
- Provenance on the entry (dict fields, not only comments), minimum:
  - `source_urls`: both  
    - `https://docs.px4.io/main/en/flight_controller/pixhawk4.html`  
    - `https://holybro.com/products/pixhawk-4`
  - `source_note`: quote that both state Dimensions **44x84x12mm**; axis rule = verbatim order → L/W/H; mount pattern **not** claimed; Mini **not** seeded.

Do **not** invent entries for other keys in `FLIGHT_CONTROLLER_MAP`.

### 3.2 Extractor — `extract_flight_controller_properties`

After a successful model match:

1. Attach `model` exactly as today (`source="declared"`, confidence 0.9/0.7 rule unchanged).
2. If `found_model` is in the dimensions table, also attach:

```text
length_mm / width_mm / height_mm
PropertyValue(value=<float>, unit="mm", confidence=<same as model match>, source="declared")
```

3. If `found_model` is **not** in the table → return `model` only (today’s behavior).
4. **Never** parse millimetre digits from the user string for this feature.

Update the function docstring to state: dims are identity-linked from a sourced table for recognized models only; not catalog-bound; not free-text mm extraction.

### 3.3 Completeness / writers / Board

- `_flight_controller_completeness`: **unchanged** (N5).
- Existing `set_control_component` / description handlers: **no** special-case required if they already persist the extractor’s full `properties` dict — verify; if a writer strips unknown keys, fix only enough to persist the three dim keys (do not redesign control writers).
- Board / `ui/` / `spatial_board.py`: **no** required edits (generic `_fields`).

### 3.4 Honesty constraints

- `catalog_ref` remains `None` for FC under this IC.
- No CLI/claim copy that says “fits stack,” “30.5,” “cabe,” or “from catalog.”
- Implementation report must include one sentence: **no catalog, no `catalog_ref`, declared-by-recognized-identity only.**

### 3.5 Smoke note (report)

Live project `autonomía-de-10min` already has FC with `model` only — will **not** show dims until re-declare “Pixhawk 4” (N2). Unit tests alone suffice for review; optional Board re-declare smoke after PASS.

---

## 4. Tests (required)

Prefer extending `tests/test_control_component.py` (or adjacent FC tests):

1. **Pixhawk 4 dims:** `extract_flight_controller_properties("pixhawk 4")` → `model=="pixhawk_4"` and `(length_mm, width_mm, height_mm) == (44, 84, 12)` (float-approx OK), each `unit=="mm"`, `source=="declared"`, confidence ≈ 0.9.
2. **Non-seeded model:** e.g. `"pixhawk 4 mini"` → `model=="pixhawk_4_mini"` and **no** `length_mm`/`width_mm`/`height_mm` keys.
3. **Generic pixhawk:** `"controladora pixhawk"` → `model=="pixhawk"` and **no** dim keys.
4. **Completeness unchanged:** high completeness still from model confidence alone; props with only `model` (no dims) still grade as today.
5. **Persist path (one integration):** declaring FC “Pixhawk 4” via existing control/description path writes the three dim properties onto `components["flight_controller"]` (or equivalent writer used by that path).

Update any existing Pixhawk-4 extract tests that assert “only model” if they would falsely fail — extend assertions rather than weaken.

Run full suite; report count in implementation report.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/domains/aerial.py` | dimensions table + extractor attach + docstring |
| `tests/test_control_component.py` (and/or adjacent) | §4 coverage |
| `.jes/artifacts/implementation_report_geometry_fc_envelope_b1.md` | write |

**Touch only if needed to persist props:** control writer / orchestrator path that currently drops unknown property keys — document in report if touched.

**Do not change:** `library/**`, `library.py` FC family (none), `catalog_bind.py` FC bind (none), Battery/Motor/ESC, `ui/**`, PASS footnote, `calculation_engine.py`, version.

---

## 6. Explicit non-goals

`library/fc/` foundation · `FcSpec` / bind / `catalog_ref` · Continuity FC wizard · mount/30.5/stack · Mini or other models · mass/weight · free-text mm digit parse · Board glyph · fit/clearance · Battery/Motor/ESC/Frame edits · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · weakened tests

---

## 7. Done criteria

- [x] `extract_flight_controller_properties("pixhawk 4")` yields 44 / 84 / 12 mm alongside `model`.
- [x] Other mapped FC models stay dims-less.
- [x] Completeness unchanged; no catalog/bind/`catalog_ref`.
- [x] No stack/fit/mass seeding; no `ui/` required.
- [x] Full suite green; implementation report written (incl. divergence sentence + N2 re-declare note).
- [x] Cursor review PASS before Engineer close.

---

## 8. Role split

```text
Engineer ★ → Buy B1 (this contract)
Claude     → implement exactly this IC + report
Cursor     → implementation review
Engineer   → optional Board re-declare smoke / next focus
```
