# Implementation Contract — Propeller B0 honesty + B1 cited bag (`gf_5045x3` only)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · CLOSED (suite **2489**) + smoke ACCEPT  
**Parents:**
- Engineer ★ **B0+B1** (2026-09-09)
- [investigation_review_geometry_propeller_envelope_b1.md](investigation_review_geometry_propeller_envelope_b1.md) PASS WITH NOTES
- [engineer_validation_propeller_catalog_2026-09-09.md](engineer_validation_propeller_catalog_2026-09-09.md)
- Claude [investigation_report_geometry_propeller_envelope_b1.md](investigation_report_geometry_propeller_envelope_b1.md)
- Fit stub — **QUEUED**. Plate L×W / `"cabe"` / STEP / nested 40-field schema — **out**

**Type:** Catalog honesty (B0) + optional PropellerSpec bag + one cited seed (B1). Representar **text**.  
**Not** hub 3D. **Not** T-Motor STEP. **Not** SKU splits. **Not** filling the Engineer 🟢 list except `gf_5045x3`.

**Baseline:** package **`0.3.8`** · suite **2480**

**Output:** `.jes/artifacts/implementation_report_geometry_propeller_envelope_b0_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Shape | **B0 + B1** |
| 2 | B0 | Unsourced `mass_g` → **omit** (UNKNOWN). HBN `identity_status` → `partially_verified`. `tmotor_22x6_7` **not** renamed |
| 3 | B1 bag | Optional: `blade_count`, `material`, `hub_diameter_mm`, `hub_thickness_mm`, `mass_tolerance_g`, `shaft_bore_mm`, `source_note` |
| 4 | B1 seed | **`gf_5045x3` only** this IC |
| 5 | 3D | Disk from `diameter_in` **unchanged**. Hub fields never stitch a cylinder |
| 6 | Duplicate Ø mm | **No** catalog `diameter_mm` SoT |
| 7 | Operating / env / STEP | **Out** |
| 8 | Version | **No** bump |

**Product sentence:**

```text
Las hélices sin ficha ya no publican gramos inventados.
gf_5045x3 cita palas / ABS / buje en card. El disco 3D sigue siendo Ø.
```

**Not:**

```text
17 fichas T-Motor · 55 g → 21 g este PR · P22×6.6 rename · STEP en Scene3D
· HBN con masa de Bullnose · 6040 5.2 g sin variante
```

---

## 1. You (Claude)

- Do **not** seed hub/mass/blades on `gemfan_5045_hbn`, `hq_5045_bn`, `gemfan_5030`, `gemfan_6040`, `dal_7040`, any APC, any `tmotor_*`.
- Do **not** rename `tmotor_22x6_7` → `tmotor_22x6_6` or change its `pitch_in`.
- Do **not** copy Lemon/EMAX numbers onto a row whose `source_url` does not state them. **One primary page** per seeded number; re-fetch live; quote in `source_note`. If EMAX listing and Lemon FPV disagree, **STOP**.
- Do **not** add `diameter_mm`, nested schema, RPM, thrust_limit, temps, POPO, `prop_type`, rotation as schema keys.
- Do **not** change `_geometry_from_spec` / `Solid3D` / disk `z`.
- Do **not** invent `motor_power_w`. Do **not** un-QUEUE fit.
- Do **not** mutate live `workspace/` from tests.
- Update `test_gemfan_5045_hbn_verified_identity` to the new honesty (`partially_verified`) — that is a required correction, not a weaken.
- Full pytest green. `ui/` empty diff this cycle.
- Write the implementation report when done.

---

## 2. Intent

```text
B0  helices/_datos.json  — drop unsourced mass_g
    gemfan_5045_hbn.identity_status = partially_verified
        ↓
B1  PropellerSpec optional bag + loader
        ↓
    bind_propeller_from_catalog projects bag when set
        ↓
    gf_5045x3 seed (re-fetched page) → card text
        ↓
    _geometry_from_spec still disk from diameter_in
```

---

## 3. Locked behavior

### 3.1 B0 — unsourced mass

In `library/helices/_datos.json`, **remove** the `mass_g` key (do not leave `null` if the loader treats missing as None — missing key is enough) on every row **except** `gf_5045x3`.

Expect these to lose `mass_g` (confirm at implement time):

`gemfan_5030`, `gemfan_6040`, `dal_7040`, `apc_8x4_5`, `apc_10x4_5`, `apc_11x5_5`, `tmotor_12x4`, `tmotor_13x4_4`, `tmotor_15x5`, `tmotor_16x5_4`, `tmotor_17x5_8`, `tmotor_18x6_1`, `tmotor_22x6_7`, `tmotor_24x7_2`.

`gemfan_5045_hbn` and `hq_5045_bn` already have no `mass_g` — leave that.

`diameter_in` / `pitch_in` / `compatible_kv_band` / `tags` **unchanged** except as §3.2–3.3.

After B0, `default_library` census: **exactly one** propeller with `mass_g is not None` → `gf_5045x3` ≈ 4.5.

### 3.2 B0 — HBN identity

`gemfan_5045_hbn`:

```text
identity_status: "partially_verified"
```

Keep Oscar Liang `source_url` (it is identity-of-use, not a physical ficha). Add `source_note` (once the field exists): Oscar Liang test-table label; **no** manufacturer mass/hub/blade count on that page; physical extras UNKNOWN.

Do **not** add `mass_g` / hub / `blade_count` (tags saying `tri-blade` are **not** a seed source).

### 3.3 B0 — `tmotor_22x6_7`

Keep SKU key and `pitch_in` **6.7**. No mass. Add `source_note`: identity debt — current T-Motor catalog shows **P22×6.6**; this row is **not** renamed this Buy.

### 3.4 B1 — `PropellerSpec` (`library.py`)

Add optional fields; parse in `_propeller_from_raw` like other optionals:

```text
blade_count: int | None = None          # integer palas; absent → None
material: str | None = None
hub_diameter_mm: float | None = None
hub_thickness_mm: float | None = None
mass_tolerance_g: float | None = None
shaft_bore_mm: float | None = None
source_note: str | None = None
```

`source_note` is catalog provenance (Motor-like). **Do not** project it as a Board property.

`shaft_bore_mm`: seed **only** if the page names a shaft/bore/hole distinct from hub Ø. Do **not** duplicate `hub_diameter_mm=5` into bore.

### 3.5 B1 — seed `gf_5045x3` only

Keep `part_number` `PMAB5045-3`, `diameter_in` 5, `pitch_in` 4.5, `mass_g` 4.5 unless the primary page contradicts — then **STOP**.

**Primary page rule:** re-fetch live. Prefer the row’s current EMAX shop `source_url` if it states the bag. If that listing does not state hub/blades/material, you may **replace** `source_url` with a propeller page that does (Engineer cited Lemon FPV) **only if** PN/ABS/5×4.5/4.5 g still match. Quote the chosen page in `source_note`. One URL as SoT.

Expected seed **if the primary page states them** (do not invent if absent):

```text
blade_count: 3
material: ABS          # or the page’s exact material string
hub_diameter_mm: 5
hub_thickness_mm: 9.5
identity_status: "verified"   # if still missing; only with a real propeller page
```

`mass_tolerance_g` / `shaft_bore_mm`: omit unless the same page states them.

Pack “2 CW + 2 CCW”: `source_note` only.

### 3.6 Bind

In `bind_propeller_from_catalog`, after existing diameter/pitch/mass:

Project when not `None`:

| key | unit | source |
|---|---|---|
| `blade_count` | none / omit unit or `""` — match existing integer-like properties; if none exist, use `unit=None` / no unit | `declared` |
| `material` | none | `declared` |
| `hub_diameter_mm` | `mm` | `declared` |
| `hub_thickness_mm` | `mm` | `declared` |
| `mass_tolerance_g` | `g` | `declared` |
| `shaft_bore_mm` | `mm` | `declared` |

Same `confidence=0.9` as other optional dims (`mass_g` stays 0.9). Diameter/pitch stay 0.95.

Refresh-from-catalog already calls this bind — no parallel writer.

### 3.7 Projector / visor

`_fields` walks properties — no Board code. `_geometry_from_spec`: **no edit**. Regression: propellers spec with `diameter_in=5` **and** hub mm still `geometry.shape == "disk"` and `diameter_mm == 127` (5×25.4).

---

## 4. Tests

New `tests/test_geometry_propeller_envelope_b0_b1.py`:

| ID | Behavior |
|---|---|
| T1 | `get_propeller("gemfan_5045_hbn").identity_status == "partially_verified"`; `mass_g is None`; no hub/blade_count |
| T2 | `hq_5045_bn` still `partially_verified`; `mass_g is None` |
| T3 | `gf_5045x3`: `mass_g ≈ 4.5`; `blade_count == 3`; hub 5 / 9.5 **if seeded**; `source_note` non-empty |
| T4 | `bind_propeller_from_catalog("gf_5045x3")` projects those card fields; `diameter_in` 5 |
| T5 | bind `gemfan_5030` → **no** `mass_g` key |
| T6 | bind `tmotor_15x5` → **no** `mass_g` key |
| T7 | `project_spatial_nodes` synthetic propellers `{diameter_in: 5, hub_thickness_mm: 9.5}` → disk Ø 127; hub field in `fields` |
| T8 | `tmotor_22x6_7.pitch_in == 6.7`; `mass_g is None`; name/key unchanged |
| T9 | among `list_propellers()`, only `gf_5045x3` has `mass_g is not None` |

Update `tests/test_catalog_foundation_v1.py` `test_gemfan_5045_hbn_verified_identity` → assert `partially_verified` (rename the test). Keep `test_gf_5045x3_curated_identity_and_mass` mass 4.5; extend only if needed without weakening.

Do **not** add UI tests.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `library/helices/_datos.json` | B0 masses; HBN status + notes; `gf_5045x3` bag; T-Motor 22 identity note |
| `src/jarvis/knowledge/library.py` | PropellerSpec bag + loader |
| `src/jarvis/core/catalog_bind.py` | project bag |
| `tests/test_geometry_propeller_envelope_b0_b1.py` | T1–T9 |
| `tests/test_catalog_foundation_v1.py` | HBN identity assertion |
| `ui/` | **empty diff** |
| `.jes/artifacts/implementation_report_geometry_propeller_envelope_b0_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-10min` **propellers** card: still `gemfan_5045_hbn`; still Ø 127 disk; still **no** `mass_g` / hub. (HBN status is catalog-only unless rebound.)

Optional: bind/refresh `gf_5045x3` → card shows palas / ABS / buje; 3D still a **flat disk**.

T-Motor cards in other projects: grams **disappear** until a later cited seed ★ — that is B0 ACCEPT, not a bug.

Record `engineer_smoke_geometry_propeller_envelope_b0_b1.md`.

---

## 7. Done when

- [ ] T1–T9 + foundation HBN test green; full pytest green; UI suite unchanged
- [ ] Exactly one helix `mass_g` in the library (`gf_5045x3`)
- [ ] No 3D / STEP / 22×6.6 rename / version bump
- [ ] Report written

---

## Explicitly not this IC

T-Motor 🟢 masses (12×4, 15×5, …) · `gemfan_6040` 5.2 · `dal_7040` Cyclone 5.7 · APC SKU splits · `tmotor_22x6_6` · L2 hub solid · L4 STEP · motor watts · plate L×W · `"cabe"`
