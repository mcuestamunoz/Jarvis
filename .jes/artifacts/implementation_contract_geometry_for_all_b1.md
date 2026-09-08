# Implementation Contract — Geometry-for-all B1 (sourced frame text enrichment)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY FOR IMPLEMENTATION — Engineer ★ Buy **B1** (investigation lean)  
**Parents:**
- [investigation_contract_geometry_for_all_b1.md](investigation_contract_geometry_for_all_b1.md)
- [investigation_report_geometry_for_all_b1.md](investigation_report_geometry_for_all_b1.md) — lean **B1**
- [investigation_review_geometry_for_all_b1.md](investigation_review_geometry_for_all_b1.md) — **PASS WITH NOTES**
- Structure B thickness / plate multiplicity / parts graph — CLOSED precedents
- Catalog-bound refresh B1 — frame **root** refresh picks up new root fields; part children still via `frame_part_specs_from_catalog` on catalog apply

**Type:** Additive **seed + FrameSpec + projection** only. Board shows new **text** fields via existing `_fields` walk.  
**Not** new glyphs. **Not** plate L×W family. **Not** Conn. **Not** fit/pose. **Not** Here3. **Not** mount-hole patterns.

**Baseline:** package **`0.3.8`** · suite **2406**

**Output:** `.jes/artifacts/implementation_report_geometry_for_all_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — narrow per-SKU sourced text |
| 2 | Standoff heights | Seed list (all stated heights; never drop the second) |
| 3 | Body footprint | iFlight only → **frame root** `body_length_mm` / `body_width_mm` = **202 / 202** |
| 4 | Glyphs | **No** new shape; **no** claim that body L×W or height alone creates a glyph |
| 5 | Rows touched | `iflight_xl7_v4_7in` + `tbs_source_one_v5_5in` only; Armattan / TBS 7in **unchanged** (no invention) |
| 6 | Mount holes 30.5/20 | **Out** — pose-reversal flag only |
| 7 | Version | **No** bump |

---

## 1. You

- Do **not** invent dims for Armattan, TBS 7in DC, plates L×W, or cage.
- Do **not** add glyph vocabulary or treat body L×W as a box without height.
- Do **not** open Conn / fit / pose / Here3 identity.
- Do **not** seed mount-hole patterns in this IC.
- Do **not** bump package version.
- Full suite green. Zero weakened tests.
- Write the implementation report when done.

---

## 2. Intent

```text
Seed (cited pages)
  → FrameSpec (+ StandoffSeed list + body_*)
  → bind_frame_from_catalog → frame.root body_* text
  → frame_part_specs_from_catalog → frame_standoff height text
  → Board card fields (generic walk)
```

Product sentence:

> “Cuando la página del frame cita altura de standoffs o body mm, el Board puede mostrarlos como texto declarado — sin inventar el resto ni dibujar un glyph incompleto.”

---

## 3. Locked behavior

### 3.1 Seed (`library/frames/_datos.json`)

**`tbs_source_one_v5_5in`** — add (page: “Standoff Height: 30mm and 22mm”):

```json
"standoffs": [
  {"height_mm": 30},
  {"height_mm": 22}
]
```

Update `source_note` to mention standoff heights 30mm and 22mm (keep existing thickness/wheelbase honesty).

**`iflight_xl7_v4_7in`** — add (page: Body 202×202; Standoff height 25mm×4 + 32mm×4):

```json
"body_length_mm": 202,
"body_width_mm": 202,
"standoffs": [
  {"height_mm": 25, "count": 4},
  {"height_mm": 32, "count": 4}
]
```

Update `source_note` accordingly. **Do not** add mounting-hole fields.

**`armattan_rooster_5in` / `tbs_source_one_v5_1_7in_dc`:** no new numeric fields.

### 3.2 Library schema (`FrameSpec` / loader)

Add (mirroring `PlateSeed` discipline):

```text
StandoffSeed:
  height_mm: float          # required per entry
  count: int | None = None  # only when page states piece count

FrameSpec:
  standoffs: list[StandoffSeed] | None = None
  body_length_mm: float | None = None
  body_width_mm: float | None = None
```

Loader parses `standoffs` / body_* ; reject malformed lists. Empty list → treat as None (no child height projection).

### 3.3 Root projection (`bind_frame_from_catalog`)

When set, project onto **frame** root properties (same pattern as `wheelbase_mm`):

- `body_length_mm`, `body_width_mm` — `PropertyValue` float, unit `"mm"`, source declared.

Do **not** change `_frame_completeness` gates (still mass+material). Body fields are additive display/KNOW only.

### 3.4 Standoff part projection (`frame_part_specs_from_catalog`)

Extend standoff `_part` path:

1. If `spec.standoffs` is non-empty **or** existing material/count would create the child → emit `FRAME_STANDOFF_KEY`.
2. Preserve existing `standoff_count` / `standoff_material` scalar projection when present.
3. Heights: build Board text without dropping values:
   - **One** entry → `height_mm` = float (e.g. `30.0`).
   - **Two+** entries → `height_mm` = **string** `"30 / 22"` (heights in seed order, `" / "` joined). `PropertyValue.value` allows `str`. Unit `"mm"`.
4. Optional: if every seed entry has `count`, you may set `count` to the **sum** only when that sum is explicitly recoverable from the page groups (iFlight 4+4=8). If scalars already set `standoff_count`, do not overwrite with a conflicting invented total — prefer leaving scalar count as-is and not summing unless scalar was absent. **Safest lock:** do **not** auto-sum counts in this IC; `count` on each `StandoffSeed` is stored for seed fidelity / future use, but Board projection of height string is enough. (iFlight `count` on seed entries is still required in JSON for honesty of the quote.)

5. Creating a standoff child from **heights alone** (TBS/iFlight have no `standoff_material` today) **is required** — otherwise the new data never appears on a card.

### 3.5 Glyph / Board

- No projector / glyph code changes expected.
- Assert: frame with only `body_*` (no full L×W×H triple) → **no** box glyph.
- Assert: `frame_standoff` with `height_mm` only → **no** disk/box glyph.

### 3.6 Refresh / already-bound projects

- `refresh_component_from_catalog(..., "frame")` updates **root** (body_* appear after this IC + refresh).
- Standoff **child** heights appear when catalog apply re-runs `frame_part_specs_from_catalog` + upsert (existing pick/rebind path). Do **not** silently rewrite all frame children inside refresh unless you find an existing helper already used on re-pick — prefer reuse; if none, document in report that standoff text requires frame catalog re-pick / apply, and keep refresh root-only (honest N4 parallel to ESC mass).
- Demo Armattan: **no** Board change expected from seed alone.

---

## 4. Tests (required)

New or extend existing frame catalog / spatial board tests:

| # | Case |
|---|---|
| T1 | Loader: TBS 5in `standoffs` → two heights 30, 22; iFlight body 202/202 + standoffs 25/32 with counts |
| T2 | `bind_frame_from_catalog("iflight_xl7_v4_7in")` → root has body_length/width 202 |
| T3 | `frame_part_specs_from_catalog` TBS → `frame_standoff.properties["height_mm"].value == "30 / 22"` (or equivalent locked join) |
| T4 | iFlight parts → standoff height string includes both 25 and 32 |
| T5 | Armattan unchanged: no body_*; standoff still material-only (no height) |
| T6 | Projector: body-only frame → `geometry` absent; standoff height-only → `geometry` absent |
| T7 | Non-regression: existing plate/arm thickness projections still pass |

Full suite green; report count.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `library/frames/_datos.json` | TBS 5in + iFlight enrichment + source_note |
| `src/jarvis/knowledge/library.py` | `StandoffSeed`, FrameSpec fields, parse |
| `src/jarvis/core/catalog_bind.py` | root body_* + standoff height projection |
| `tests/…` | T1–T7 |
| `.jes/artifacts/implementation_report_geometry_for_all_b1.md` | write |

**Do not change:** Board/UI glyph code · Conn Continuity · sensors · pose · version · other seeds

---

## 6. Explicit non-goals

Plate footprint family · cage dims · Armattan invention · new glyphs · mount-hole seeding · Here3 · Conn · fit/pose · version bump · weakened tests

---

## 7. Done criteria

- [ ] Seeds + source_notes cite the live page facts  
- [ ] Both standoff heights survive projection (no scalar drop)  
- [ ] iFlight body on **frame root**  
- [ ] No false glyphs  
- [ ] Tests T1–T7; full suite green  
- [ ] Report written  
- [ ] Cursor review  

---

## 8. Stop conditions

Stop and ask before: projecting body dims onto a plate key, adding a 2D footprint glyph, seeding mount holes, or auto-mutating demo Armattan state.
