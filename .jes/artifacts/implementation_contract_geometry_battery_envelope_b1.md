# Implementation Contract — Battery declared envelope (L×W×H) — representar only

**Project:** Jarvis  
**Date:** 2026-09-06  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2316**)  
**Review:** [implementation_review_geometry_battery_envelope_b1.md](implementation_review_geometry_battery_envelope_b1.md)  
**Report:** [implementation_report_geometry_battery_envelope_b1.md](implementation_report_geometry_battery_envelope_b1.md)  
**Parents:**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [investigation_contract_geometry_minimum_physical_object.md](investigation_contract_geometry_minimum_physical_object.md)
- [investigation_report_geometry_minimum_physical_object.md](investigation_report_geometry_minimum_physical_object.md)
- [investigation_review_geometry_minimum_physical_object.md](investigation_review_geometry_minimum_physical_object.md) — **PASS WITH NOTES**

**Type:** Additive declared geometry fields on existing battery catalog + bind projection. Display-only KNOW (`representar`).  
**Not** visualization. **Not** fit/clearance. **Not** Frame geometry. **Not** MEASURE/CAD/FEA.

**Baseline:** tag **`v0.3.8`** · Structure CLOSED suite **2294** · Board B3 closable **2310**

**Output:** `.jes/artifacts/implementation_report_geometry_battery_envelope_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — Battery `length_mm` / `width_mm` / `height_mm` only |
| 2 | Ladder rung | **`representar` only** — text properties on card/BOM path; no glyph |
| 3 | Family scope | **Battery only** — Motor / ESC / Frame / Propeller out |
| 4 | N1 Spektrum values | **138.5 / 47.7 / 40.7** mm — **not** 37×35×75 |
| 5 | N2 axis mapping | **(a)** labeled axes when page labels them; else **verbatim print order** `A×B×C` → `(length, width, height)` + quote in `source_note` |
| 6 | Mass / physics | **M0 unchanged** — dims never drive mass, energy, or ERF |
| 7 | Structure PASS * | **Unchanged** — do not touch footnote or Structure block |

---

## 1. You

- Do **not** add Motor / ESC / Frame envelope fields.
- Do **not** add `diameter_mm`, `envelope_shape`, bounding volume, glyph, 2D/3D preview.
- Do **not** add fit / clearance / “cabe” / compare logic.
- Do **not** add free-text L×W×H extractors in `aerial.py`.
- Do **not** invent dims for rows without a cited source that states them.
- Do **not** change Structure PASS *, ASSEMBLY_READY, calculation_engine energy path, or Board mutation authority.
- Do **not** bump package version unless Engineer asks after review.
- Full suite green. Zero weakened tests.
- Write `implementation_report_geometry_battery_envelope_b1.md` when done.

---

## 2. Intent

```text
library/baterias/_datos.json  (sourced rows only)
  length_mm / width_mm / height_mm
        ↓
  BatterySpec (optional floats)
        ↓
  bind_battery_from_catalog → ComponentSpec.properties
        ↓
  Board card / any generic property consumer
  (spatial_board._fields already generic — no ui/ change required)
```

No new type. No Board code unless a test proves a projector hole (unexpected — do not “improve” UI).

---

## 3. Locked behavior

### 3.1 Schema — `BatterySpec`

In `src/jarvis/knowledge/library.py`:

- Add three optional fields on `BatterySpec`:

```text
length_mm: float | None = None
width_mm:  float | None = None
height_mm: float | None = None
```

- Parse in `_battery_from_raw` from JSON when present (`float(...)`); absent → `None`.
- Do **not** require all three together at load time in this IC (if a future source states only two, omit the missing one — today’s three sourced rows all have three). Prefer seeding complete triples when the page states a full box.

### 3.2 Seed — `library/baterias/_datos.json`

Seed **only** the three currently `identity_status: verified` rows with cited dims:

| SKU | `length_mm` | `width_mm` | `height_mm` | Source rule |
|---|---|---|---|---|
| `lipo_4s_1500mah` | **37** | **35** | **75** | CNHL page string `37X35X75mm` → verbatim order (N2a) |
| `lipo_4s_5000mah` | **138.5** | **47.7** | **40.7** | Spektrum labeled Length/Width/Height (N1) |
| `lipo_6s_6000mah` | **141** | **64** | **41** | Rotorama `141x64x41mm` → verbatim order (N2a) |

- Extend each row’s `source_note` with a short verbatim dim quote (and for Spektrum, note labeled axes).
- **All other battery rows** (including `lipo_4s_10000mah`): **omit** the three keys — never invent.
- Do not change energy/mass/identity fields of any row except `source_note` appends for the three seeded SKUs.

### 3.3 Catalog projection — `bind_battery_from_catalog`

In `src/jarvis/core/catalog_bind.py`:

- When `spec.length_mm` / `width_mm` / `height_mm` is not `None`, project:

```text
PropertyValue(value=<float>, unit="mm", confidence=0.9, source="declared")
```

  onto properties keyed exactly `length_mm`, `width_mm`, `height_mm`.

- Rows without dims: projection unchanged from today (no empty keys).
- **N6:** Rewrite the stale docstring — remove “No CLI/UX entry point calls this yet”; state that Continuity / orchestrator battery catalog-pick paths call it. One-paragraph honesty fix only.

### 3.4 Board / UI

- **No** required edits under `ui/spatial-board/` or `workspace/spatial_board.py`.
- Existing `_fields` must already surface the new properties after bind (regression via bind unit test is enough; optional Board projector unit test only if you already have a pattern for property listing).

### 3.5 Completeness / physics / claims

- Battery completeness rules: **unchanged** (dims do not gate `completeness`).
- Calculation engine / hover energy / sag: **unchanged** (must not read these fields).
- Structure footnote / PASS *: **unchanged**.
- No fit sentence anywhere in CLI copy for this IC.

### 3.6 Vocabulary note (future families — do not implement)

Shared optional names `length_mm` / `width_mm` / `height_mm` are the Geometry axis vocabulary for box parts. `diameter_mm` stays **out** of this IC (Motor later). Propeller keeps `diameter_in` / `pitch_in`.

---

## 4. Tests (required)

Add focused tests (new file or extend `tests/test_catalog_bind_v1.py` / catalog foundation — match repo style):

1. **Loader:** `get_battery("lipo_4s_1500mah")` → `(37, 35, 75)`; `lipo_4s_5000mah` → `(138.5, 47.7, 40.7)`; `lipo_6s_6000mah` → `(141, 64, 41)`.
2. **Omit:** `get_battery("lipo_4s_10000mah")` (or any unsourced row) → all three dims `None`.
3. **Bind:** `bind_battery_from_catalog("lipo_4s_1500mah")` properties include the three keys with `unit=="mm"` and `source=="declared"`; `bind_battery_from_catalog("lipo_4s_10000mah")` does **not** include those keys.
4. **Non-regression:** existing bind energy/mass/chemistry assertions for a seeded SKU still pass; Structure / energy calc suites untouched in intent.

Optional: one test that a bound battery’s properties would appear in `project_spatial_nodes` field labels if such a helper test already exists — not mandatory.

Run full suite; report count in implementation report.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/knowledge/library.py` | `BatterySpec` + `_battery_from_raw` |
| `library/baterias/_datos.json` | three seeded rows + `source_note` |
| `src/jarvis/core/catalog_bind.py` | project dims + docstring N6 |
| `tests/…` | loader + bind coverage as §4 |
| `.jes/artifacts/implementation_report_geometry_battery_envelope_b1.md` | write |

**Do not change:** `ui/**`, Structure aerial extractors, `calculation_engine.py`, PASS footnote, Motor/ESC/Frame specs.

---

## 6. Explicit non-goals

Fit/clearance · CAD import/FEA · Board glyph/preview · Motor/ESC/Frame dims · free-text mm extraction · `envelope_shape` · Σ mass→physics · Prop/Energy unlock · System Optimization · Conversation Engine · Board write surface · version bump · inventing dims for unsourced SKUs · fixing unrelated board B1 layout-on-disk.

---

## 7. Done criteria

- [x] Three sourced batteries load and bind with correct mm triples (N1 Spektrum correct).
- [x] Unsourced batteries omit dims.
- [x] Board shows new rows via existing generic path after a real catalog pick (manual smoke OK; unit bind sufficient if smoke not run).
- [x] No Structure / energy / PASS behavior change.
- [x] Full suite green; implementation report written.
- [x] Cursor review PASS before merge narrative / Engineer close.

---

## 8. Role split

```text
Engineer ★ → Buy B1 (this IC)
Claude     → implement exactly this IC + report
Cursor     → implementation review
Engineer   → close / next Buy
```
