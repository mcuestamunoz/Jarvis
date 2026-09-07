# Implementation Contract — Motor declared envelope (stator + overall diameter + shaft) — representar only

**Project:** Jarvis  
**Date:** 2026-09-06  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2323**)  
**Review:** [implementation_review_geometry_motor_envelope_b1.md](implementation_review_geometry_motor_envelope_b1.md)  
**Report:** [implementation_report_geometry_motor_envelope_b1.md](implementation_report_geometry_motor_envelope_b1.md)  
**Parents:**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [investigation_contract_geometry_motor_envelope.md](investigation_contract_geometry_motor_envelope.md)
- [investigation_report_geometry_motor_envelope.md](investigation_report_geometry_motor_envelope.md)
- [investigation_review_geometry_motor_envelope.md](investigation_review_geometry_motor_envelope.md) — **PASS WITH NOTES**
- Battery B1 CLOSED suite **2316** + Board smoke ACCEPT

**Type:** Additive declared geometry fields on motor catalog + bind projection. Display-only KNOW (`representar`).  
**Not** visualization. **Not** fit/clearance/arm-mount. **Not** Battery/ESC/Frame dims. **Not** MEASURE/CAD/FEA.

**Baseline:** package **`0.3.8`** · Geometry Battery B1 CLOSED suite **2316**  
**Catalog reality (locked):** `library/motores/_datos.json` has **22** motor rows; **exactly 2** have `source_url` + `identity_status: verified`. Seed **only** those 2.

**Output:** `.jes/artifacts/implementation_report_geometry_motor_envelope_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — Motor envelope fields below only |
| 2 | Ladder rung | **`representar` only** — text on Board via generic `_fields`; no glyph |
| 3 | Family scope | **Motor only** — Battery untouched; ESC / Frame out |
| 4 | Field bag | `stator_diameter_mm`, `stator_height_mm`, `diameter_mm`, `shaft_diameter_mm` (optional each) |
| 5 | Overall axial height | **OUT** — no `height_mm` / `body_length_mm` / shaft-inclusive overall height (N5 debt) |
| 6 | N3 diameter labels | One property key `diameter_mm`; per-row `source_note` must quote manufacturer label (“Motor Diameter” vs “Rotor Diameter”) |
| 7 | N2 sibling SKUs | Seed **`emax_rs2205s_2300` only** among EMAX rows — **never** invent dims onto unsourced `emax_rs2205_2300` |
| 8 | N4 bind miss | If `get_motor(sku)` fails → project suggestion fields only (today); **no** dims invented |
| 9 | Physics / PASS | Dims never drive thrust/mass/calc; Structure PASS * unchanged |

---

## 1. You

- Do **not** add Battery/ESC/Frame geometry in this IC.
- Do **not** add overall axial `height_mm` / `length_mm` / `body_length_mm`.
- Do **not** widen `MotorSuggestion` TypedDict or change ranking UX in `motor_catalog_assist.py` beyond what bind needs (prefer **zero** edits there).
- Do **not** add fit / mount / bolt-pattern / “cabe” logic.
- Do **not** add free-text motor-mm extractors in `aerial.py`.
- Do **not** invent dims for any of the 20 unsourced motor rows (including `emax_rs2205_2300`).
- Do **not** change Structure PASS *, ASSEMBLY_READY, calculation_engine, or Board mutation authority.
- Do **not** bump package version unless Engineer asks after review.
- Full suite green. Zero weakened tests.
- Write `implementation_report_geometry_motor_envelope_b1.md` when done.

---

## 2. Intent

```text
library/motores/_datos.json  (2 sourced rows only)
  stator_diameter_mm / stator_height_mm / diameter_mm / shaft_diameter_mm?
        ↓
  MotorSpec (optional floats)
        ↓
  bind_motor_from_catalog(suggestion, *, library=None, base=None)
        → lib.get_motor(sku) when present → project dims
        ↓
  ComponentSpec.properties → Board _fields (no ui/ change)
```

---

## 3. Locked behavior

### 3.1 Catalog reality (do not “fix” by inventing)

At implement time, confirm row count in `_datos.json` (expect **22**). Seed **2 of 22**:

| SKU | Seedable? | Why |
|---|---|---|
| `emax_rs2205s_2300` | **YES** | verified + source_url |
| `sunnysky_r2205_2500` | **YES** | verified + source_url |
| `emax_rs2205_2300` | **NO** | no source_url — distinct SKU (thrust 8 N vs sourced ~10 N) |
| All other motors | **NO** | no citable page |

### 3.2 Schema — `MotorSpec`

In `src/jarvis/knowledge/library.py`:

```text
stator_diameter_mm: float | None = None
stator_height_mm:   float | None = None
diameter_mm:        float | None = None   # overall radial (bell/rotor)
shaft_diameter_mm:  float | None = None
```

- Parse in `_motor_from_raw` when present (`float(...)`); absent → `None`.
- Fields independently optional (SunnySky omits shaft).

### 3.3 Seed — `library/motores/_datos.json`

| SKU | `stator_diameter_mm` | `stator_height_mm` | `diameter_mm` | `shaft_diameter_mm` |
|---|---|---|---|---|
| `emax_rs2205s_2300` | **22** | **5** | **27.9** | **3** |
| `sunnysky_r2205_2500` | **22** | **5** | **27.4** | omit |

Extend each row’s `source_note` with verbatim quotes, including manufacturer diameter **label**:

- EMAX: Stator Diameter 22mm · Stator Height 5mm · Shaft Diameter 3mm · **Motor Diameter** 27.9mm · (note Motor Height 31.7mm / 15mm extended prop shaft **not seeded** — N5).
- SunnySky: Stator Diameter 22mm · Stator Thickness 5mm → `stator_height_mm` · **Rotor Diameter** 27.4mm · (note Body Length 18mm **not seeded** — N5).

Do not change thrust/kv/mass/identity fields except `source_note` appends for these two rows.

### 3.4 Catalog projection — `bind_motor_from_catalog`

In `src/jarvis/core/catalog_bind.py`:

- Keep existing signature shape for callers: still accepts `MotorSuggestion` (+ optional `base`).
- Add optional `library: ComponentLibrary | None = None` (default `None` → `default_library`), mirroring Battery/Propeller/ESC.
- After building the existing `projected` dict from the suggestion:
  1. `sku = str(suggestion["name"])` (already present).
  2. **N4:** `try` `spec = lib.get_motor(sku)` except missing/KeyError/ValueError → skip dim projection (suggestion-only path unchanged).
  3. When present, for each of the four fields if `spec.<field> is not None`, project:

```text
PropertyValue(value=<float>, unit="mm", confidence=0.9, source="declared")
```

- Do **not** put dims on `MotorSuggestion`.
- Prefer **no** edits to `motor_catalog_assist.py`.

### 3.5 Board / UI

- **No** required edits under `ui/` or `workspace/spatial_board.py`.
- Existing `_fields` surfaces new properties automatically.

### 3.6 Completeness / physics / claims

- Motor completeness: **unchanged** (dims do not gate completeness).
- Calculation engine / thrust / energy: **must not** read these fields.
- Structure PASS *: **unchanged**.
- No fit/mount sentence in CLI copy for this IC.

### 3.7 Smoke note (for Engineer / implementer report — not a code requirement)

After implement, Board card for current project SKU `emax_rs2205_2300` will **still lack** dims (N2). Optional smoke: rebind to `emax_rs2205s_2300` (or bind SunnySky) and confirm Board shows stator/diameter/(shaft). Document in implementation report if smoke run; unit tests alone are enough for Cursor review.

---

## 4. Tests (required)

Extend catalog foundation / bind tests (match repo style):

1. **Loader:** `get_motor("emax_rs2205s_2300")` → stator 22/5, diameter 27.9, shaft 3; `get_motor("sunnysky_r2205_2500")` → 22/5/27.4 and `shaft_diameter_mm is None`.
2. **Omit:** `get_motor("emax_rs2205_2300")` → all four geometry fields `None`.
3. **Bind happy path:** build a minimal `MotorSuggestion` with `name="emax_rs2205s_2300"` (+ required TypedDict fields from library or fixtures) → `bind_motor_from_catalog(...)` properties include the four keys with `unit=="mm"` / `source=="declared"` (SunnySky bind omits shaft key entirely).
4. **Bind omit:** suggestion `name="emax_rs2205_2300"` → no geometry keys in properties.
5. **N4:** suggestion with a non-existent `name` (and valid-looking other fields) → no crash; no geometry keys; existing thrust/kv/weight still project from the dict.
6. **Non-regression:** existing motor bind / catalog-assist tests still pass.

Run full suite; report count in implementation report.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/knowledge/library.py` | `MotorSpec` + `_motor_from_raw` |
| `library/motores/_datos.json` | two seeded rows + `source_note` |
| `src/jarvis/core/catalog_bind.py` | `library` param + dim projection + N4 |
| `tests/…` | loader + bind coverage §4 |
| `.jes/artifacts/implementation_report_geometry_motor_envelope_b1.md` | write |

**Do not change:** `ui/**`, Battery schema, ESC/Frame specs, `aerial.py` extractors, `calculation_engine.py`, PASS footnote, `MotorSuggestion` TypedDict (unless a test fixture forces a tiny touch — prefer zero).

---

## 6. Explicit non-goals

Fit/clearance/arm-mount · CAD/FEA · Board glyph · Battery/ESC/Frame dims · free-text mm extraction · overall axial height fields (N5) · inventing dims on `emax_rs2205_2300` or any unsourced row · widening suggestion ranking UX · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · weakened tests

---

## 7. Done criteria

- [x] Two sourced motors load/bind with locked mm values; unsourced `emax_rs2205_2300` omits dims.
- [x] `bind_motor_from_catalog` projects dims via library lookup; N4 miss is safe.
- [x] No overall height field anywhere in this slice.
- [x] No Structure / energy / PASS behavior change; no `ui/` change required.
- [x] Full suite green; implementation report written.
- [x] Cursor review PASS before Engineer close.

---

## 8. Role split

```text
Engineer ★ → Buy B1 (this IC)
Claude     → implement exactly this IC + report
Cursor     → implementation review
Engineer   → smoke optional (rebind to …s_2300) / next Buy
```
