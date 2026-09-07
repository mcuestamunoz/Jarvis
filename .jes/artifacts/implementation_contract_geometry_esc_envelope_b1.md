# Implementation Contract — ESC declared envelope (box, reusing Battery vocabulary) — representar only

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2327**)  
**Review:** [implementation_review_geometry_esc_envelope_b1.md](implementation_review_geometry_esc_envelope_b1.md)  
**Report:** [implementation_report_geometry_esc_envelope_b1.md](implementation_report_geometry_esc_envelope_b1.md)  
**Parents:**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [investigation_contract_geometry_esc_envelope.md](investigation_contract_geometry_esc_envelope.md)
- [investigation_report_geometry_esc_envelope.md](investigation_report_geometry_esc_envelope.md)
- [investigation_review_geometry_esc_envelope.md](investigation_review_geometry_esc_envelope.md) — **PASS WITH NOTES**
- Battery B1 CLOSED suite **2316** · Motor B1 CLOSED suite **2323**

**Type:** Additive declared geometry fields on ESC catalog + bind projection. Display-only KNOW (`representar`).  
**Not** visualization. **Not** fit/stack. **Not** Continuity ESC wizard. **Not** mass hygiene. **Not** MEASURE/CAD/FEA.

**Baseline:** package **`0.3.8`** · Motor B1 CLOSED suite **2323**  
**Catalog reality:** `library/esc/_datos.json` has **1** row — seed that row only.

**Output:** `.jes/artifacts/implementation_report_geometry_esc_envelope_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — ESC `length_mm` / `width_mm` / `height_mm` (Battery vocabulary) |
| 2 | Ladder rung | **`representar` only** — text via generic `_fields`; no glyph |
| 3 | Family scope | **ESC only** — Battery/Motor untouched; FC/Frame out |
| 4 | **N1** seed values | **50.0 / 21.6 / 12.0** mm via `part_number` **30901001** (International Version B) — **not** 42.0×21.6×12.0 (Version A) |
| 5 | **N3** `source_url` | **Normalize** to `https://www.hobbywing.com/en/products/xrotor-40a122` (working mirror; leave path/product id unchanged) |
| 6 | **N5** stack | No stack/fit/“cabe” / 30.5 mount copy anywhere |
| 7 | **N2** mass | **Do not** change `mass_g` (26 stays; page 15g = flagged debt only) |
| 8 | **N4** UX | **Do not** build Continuity ESC catalog-pick wizard |
| 9 | Physics / PASS | Dims never drive calc; Structure PASS * unchanged |

---

## 1. You

- Do **not** add Battery/Motor/Frame/FC geometry in this IC.
- Do **not** change `mass_g` (N2).
- Do **not** invent Continuity/orchestrator ESC pick UX (N4).
- Do **not** add fit / stack / mount-pattern / “cabe” logic or CLI copy (N5).
- Do **not** add free-text ESC-mm extractors in `aerial.py`.
- Do **not** bump package version unless Engineer asks after review.
- Full suite green. Zero weakened tests.
- Write `implementation_report_geometry_esc_envelope_b1.md` when done.

---

## 2. Intent

```text
library/esc/_datos.json  (1 row)
  length_mm / width_mm / height_mm
  source_url → www.hobbywing.com mirror (N3)
        ↓
  EscSpec (optional floats)
        ↓
  bind_esc_from_catalog(sku, *, library=None, base=None)
        → project dims like Battery
        ↓
  ComponentSpec.properties → Board _fields (no ui/ change)
```

---

## 3. Locked behavior

### 3.1 Schema — `EscSpec`

In `src/jarvis/knowledge/library.py`:

```text
length_mm: float | None = None
width_mm:  float | None = None
height_mm: float | None = None
```

- Parse in `_esc_from_raw` when present (`float(...)`); absent → `None`.
- Same names as Battery — no ESC-only vocabulary.

### 3.2 Seed — `library/esc/_datos.json`

Update **`hobbywing_xrotor_40a_6s` only**:

| Field | Value |
|---|---|
| `length_mm` | **50.0** |
| `width_mm` | **21.6** |
| `height_mm` | **12.0** |
| `source_url` | **`https://www.hobbywing.com/en/products/xrotor-40a122`** (N3 — replace `a.hobbywing.com`) |
| `mass_g` | **unchanged** (`26`) |

Extend `source_note` with:

- Size quote for part **30901001** / International Version B: `"50.0×21.6×12.0mm"` (verbatim order → L/W/H).
- Explicit: Version A `42.0×21.6×12.0` **not** seeded (different `part_number`).
- Optional one-liner: page weight 15g for this PN differs from seed `mass_g=26` — left unchanged this IC (N2).

Do not add other ESC rows.

### 3.3 Catalog projection — `bind_esc_from_catalog`

In `src/jarvis/core/catalog_bind.py`:

- When `spec.length_mm` / `width_mm` / `height_mm` is not `None`, project:

```text
PropertyValue(value=<float>, unit="mm", confidence=0.9, source="declared")
```

- Mirror Battery’s pattern (no signature change needed).
- Keep existing `current_a` / `mass_g` projection.
- Docstring: keep honesty that Continuity/orchestrator has **no** ESC catalog-pick entry yet (N4) — accurate; do not claim a wizard exists. Optional one-line: still test-callable / script-callable.

### 3.4 Board / UI

- **No** required edits under `ui/` or `workspace/spatial_board.py`.

### 3.5 Completeness / physics / claims

- Completeness: **unchanged** (dims do not gate).
- Calculation engine / electrical_compatibility: **must not** start reading these fields for physics/fit.
- Structure PASS *: **unchanged**.
- No stack/fit sentence in CLI for this IC (N5).

### 3.6 Smoke note (optional in report)

Live projects often have freeform ESC (`"ESC 40A"`) — will **not** show dims until catalog-bound. Optional smoke: `bind_esc_from_catalog("hobbywing_xrotor_40a_6s")` + writer/save → Board shows L×W×H. Unit tests alone suffice for review.

---

## 4. Tests (required)

1. **Loader:** `get_esc("hobbywing_xrotor_40a_6s")` → `(50.0, 21.6, 12.0)`; `source_url` starts with `https://www.hobbywing.com/` (N3).
2. **Mass unchanged:** same SKU still `mass_g == 26` (N2 regression).
3. **Bind:** `bind_esc_from_catalog(...)` properties include the three keys with `unit=="mm"` / `source=="declared"`; existing `current_a` / `mass_g` still present.
4. **Non-regression:** existing ESC bind / foundation tests still pass.

Run full suite; report count in implementation report.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/knowledge/library.py` | `EscSpec` + `_esc_from_raw` |
| `library/esc/_datos.json` | dims + N3 URL + `source_note` |
| `src/jarvis/core/catalog_bind.py` | project dims (+ docstring honesty if needed) |
| `tests/…` | loader + bind coverage §4 |
| `.jes/artifacts/implementation_report_geometry_esc_envelope_b1.md` | write |

**Do not change:** `ui/**`, Battery/Motor schemas, Continuity/orchestrator ESC wizard, `mass_g` value, `aerial.py`, PASS footnote, `calculation_engine.py`.

---

## 6. Explicit non-goals

Fit/clearance/stack 30.5 · CAD/FEA · Board glyph · Continuity ESC catalog-pick UX (N4) · fixing `mass_g` 26→15 (N2) · Battery/Motor/Frame/FC dims · free-text mm extraction · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · weakened tests

---

## 7. Done criteria

- [x] ESC SKU loads/binds with 50.0 / 21.6 / 12.0 mm.
- [x] `source_url` is the `www.hobbywing.com` mirror (N3).
- [x] `mass_g` still 26.
- [x] No stack/fit copy; no wizard; no `ui/` required.
- [x] Full suite green; implementation report written.
- [x] Cursor review PASS before Engineer close.

---

## 8. Role split

```text
Engineer ★ → Buy B1 + N3 in IC (this contract)
Claude     → implement exactly this IC + report
Cursor     → implementation review
Engineer   → optional Board rebind smoke / next focus
```
