# Implementation Contract — Rooster Included plates B2 (HD Cam + Rear VTX text)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED — REVIEWED PASS WITH NOTES @ **2514** — Engineer smoke **ACCEPT**  
**Parents:**
- Engineer ★ after kit B1-min **CLOSED** — [next steps](engineer_next_assembly_kit_template.md) §3 A
- [investigation_review_geometry_plate_lw_sourced_b1.md](investigation_review_geometry_plate_lw_sourced_b1.md) **PASS WITH NOTES** — optional text Buy (N1: Armattan **Included**, not Wayback GetFPV)
- [investigation_review_assembly_kit_template_b0.md](investigation_review_assembly_kit_template_b0.md) — B2 = seed children, **not** the kit template
- Plate L×W **B0** — **holds**. Fit / `"cabe"` / STEP / Conversation Engine / GetFPV scrape — **out**
- Kit B1-min **CLOSED** — do **not** add `vtx` / `receiver` / camera kit keys

**Type:** Catalog **seed + one root scalar**. Existing `PlateSeed` / `frame_part_specs_from_catalog` / BOM `└` already ship.  
**Not** a new architecture key. **Not** a 3D box. **Not** kit `KIT_TO_COMPONENTS`. **Not** nylon/bolts ingest.

**Baseline:** package **`0.3.8`** · suite **2508**

**Output:** `.jes/artifacts/implementation_report_geometry_rooster_included_plates_b2.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Shape | **B2 text seed** — two extra `plates[]` on `armattan_rooster_5in` + `max_stack_height_mm` **22** on the **frame root** |
| 2 | Source | Live manufacturer **Included** + specs table: `https://armattanquads.com/products/rooster-1` |
| 3 | 3D | **No** box. Do **not** write `length_mm` / `width_mm` / `height_mm`. `max_stack_height_mm` is **not** `height_mm` |
| 4 | Other SKUs | **Unchanged** (TBS / iFlight) |
| 5 | Kit keys | **No** `vtx` / camera / `prop_adapter` |
| 6 | Version | **No** bump |

**Product sentence:**

```text
Tras re-pick del Rooster, el BOM muestra también la placa HD Cam (1.5 mm)
y las Rear VTX (2 mm). El chasis sigue sin caja 3D. Stack máximo 22 mm
es texto en la card del frame, no un sólido.
```

**Not:**

```text
inventar L×W · scrapear tornillos/nylon · KIT_TO vtx
· alias max_stack → height_mm · cilindro · "cabe"
```

---

## 1. You (Claude)

- Re-fetch **Armattan live**. If Included no longer lists those two carbon lines, or thicknesses differ, **STOP**.
- If the page now states plate or airframe **L×W**, **STOP** and report — this IC does **not** seed a box.
- Do **not** reorder the existing four `plates[]`. **Append** the two new rows.
- Do **not** split “Rear VTX plates (Standard and TBS)” into two siblings (one Included line → one `PlateSeed`).
- Do **not** seed nylon standoffs, bolt counts, LiPo strap, camera foam, 28.5 mm cam mount, 30.5 mm stack mount.
- Do **not** touch `_geometry_from_spec` except a **test** that the new field is not a box.
- Do **not** change `_frame_completeness`, Structure PASS, `BLOCK_TO_COMPONENTS`, `KIT_TO_COMPONENTS`.
- `ui/` empty. Full pytest green. Report every existing assertion you update (plate counts). Write the report when done.

---

## 2. Intent

```text
library/frames/_datos.json  armattan_rooster_5in
  plates[]  += HD Cam 1.5 · Rear VTX 2.0
  max_stack_height_mm = 22
        ↓
FrameSpec.plates / FrameSpec.max_stack_height_mm
        ↓
frame_part_specs_from_catalog → frame_plate_5, frame_plate_6
bind_frame_from_catalog      → root max_stack_height_mm  (never height_mm)
        ↓
BOM └ plate — …   card text
_geometry_from_spec(frame) still None  (no L×W×H)
```

Live demo: **`refresh_component_from_catalog("frame")` updates the root only.** New plate children appear only on catalog **re-pick** (existing IDLE frame rebind: clear `frame_*` + `upsert_frame_part`). Smoke must re-pick Rooster, not only refresh.

---

## 3. Locked behavior

### 3.1 Re-fetch (2026-09-09 Cursor live — confirm)

| Quote | Seed |
|---|---|
| Carbon: `1x 1.5mm HD Cam plate` | `{"label": "HD Cam plate", "thickness_mm": 1.5}` |
| Carbon: `1x 2mm Rear VTX plates (Standard and TBS)` | `{"label": "Rear VTX plates (Standard and TBS)", "thickness_mm": 2}` |
| Specs: `Max Stack Height` **22mm** | root `max_stack_height_mm`: **22** |

Do **not** copy thickness into `label` (existing Main/LiPo pattern). Omit `material` on the new rows (same as Top/front/rear).

Keep the current four, **this order**:

```json
{"label": "Main Plate", "thickness_mm": 4, "material": "fibra de carbono"},
{"label": "Top (LiPo) plate", "thickness_mm": 2},
{"label": "Small front (top) plate", "thickness_mm": 1.5},
{"label": "Small rear (top) plate", "thickness_mm": 1.5},
{"label": "HD Cam plate", "thickness_mm": 1.5},
{"label": "Rear VTX plates (Standard and TBS)", "thickness_mm": 2}
```

`source_url` unchanged. Extend `source_note`: Included carbon now also cites HD Cam 1.5 mm and Rear VTX plates 2 mm (Standard and TBS); specs table Max Stack Height 22 mm; **still no L×W**; still not the full hardware bag (nylon/bolts out).

### 3.2 Schema — `FrameSpec.max_stack_height_mm`

Additive `float | None = None` on `FrameSpec`, parsed like `body_length_mm`.

`bind_frame_from_catalog`: if set, project

```text
properties["max_stack_height_mm"] = PropertyValue(value=22, unit="mm", source="declared")
```

**Forbidden:** alias to `height_mm`, `body_*`, or standoff `height_mm`. Other frames stay `None` / no property.

`_frame_completeness`: **unchanged** (still mass + material).

### 3.3 Projection of plates

No new bind logic if `plates[]` already walks every entry (it does). After seed:

| Key | Label | thickness_mm |
|---|---|---|
| `frame_plate` | Main Plate | 4 |
| `frame_plate_2` | Top (LiPo) plate | 2 |
| `frame_plate_3` | Small front (top) plate | 1.5 |
| `frame_plate_4` | Small rear (top) plate | 1.5 |
| `frame_plate_5` | HD Cam plate | 1.5 |
| `frame_plate_6` | Rear VTX plates (Standard and TBS) | 2 |

Arm + cage + standoff unchanged. Six plates ≤ `FRAME_PLATE_MAX_SIBLINGS` 8.

N6 completeness hardcode on catalog parts: **do not “fix.”**

### 3.4 Twin — 3D / PASS

- `_geometry_from_spec` on bound Rooster root: **still `None`**.
- Same spec plus only `max_stack_height_mm`: still **`None`**.
- Hover / Structure PASS * / architecture 4/4 / kit keys: **byte-identical**.

---

## 4. Tests (required)

New file `tests/test_geometry_rooster_included_plates_b2.py`:

| ID | Assert |
|---|---|
| T1 | Loader: `get_frame("armattan_rooster_5in").plates` length **6**; last two labels/thicknesses as §3.1; first four **unchanged** |
| T2 | `max_stack_height_mm == 22`; other three frame SKUs `None` |
| T3 | `frame_part_specs_from_catalog` has `frame_plate_5` / `frame_plate_6` as §3.3; parent_key `frame` |
| T4 | `bind_frame_from_catalog` root has `max_stack_height_mm` 22; **no** `height_mm` / `length_mm` / `width_mm` / `body_*` |
| T5 | `_geometry_from_spec(bind_frame_from_catalog(...)) is None` |
| T6 | Synthetic `ComponentSpec` with **only** `max_stack_height_mm` → `_geometry_from_spec` is `None` |

**Update** (required, not weaken) — they currently lock **four** plates:

- `tests/test_frame_parts_graph_v1.py` — `test_frame_part_specs_from_catalog_armattan_has_arm_four_plates_cage_standoff` → six plates + same arm/cage/standoff; **rename** if the name lies.
- `tests/test_idle_frame_rebind_b2.py` — Armattan `frame_*` sorted list includes `frame_plate_5`, `frame_plate_6`.
- `tests/test_geometry_for_all_b1.py` — T5 no-body-footprint and T5b standoff-no-height **stay**. T7 may still stop at `frame_plate_4`; do not delete those asserts.

Do not weaken N3 (TBS equal-thickness siblings).

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `library/frames/_datos.json` | `armattan_rooster_5in` only — plates + `max_stack_height_mm` + `source_note` |
| `src/jarvis/knowledge/library.py` | `FrameSpec.max_stack_height_mm` + loader |
| `src/jarvis/core/catalog_bind.py` | root projection only |
| `tests/test_geometry_rooster_included_plates_b2.py` | T1–T6 |
| named existing tests | plate-count updates |
| `ui/` | **empty** |
| `engineering_readiness.py` / `KIT_TO_*` | **empty** |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-10min` already bound to Rooster:

1. IDLE **re-pick** `armattan_rooster_5in` (not refresh-only).
2. `estado`: two new `└ plate` lines — HD Cam 1.5 mm, Rear VTX 2 mm.
3. Frame card: `max_stack_height_mm` 22 mm (or equivalent Board field).
4. **No** new 3D solid for the frame.
5. Architecture still **4/4**. Kit XT60/harness unchanged.

Record `engineer_smoke_geometry_rooster_included_plates_b2.md`.

---

## 7. Done when

- [ ] T1–T6 + updated plate-count tests green; full pytest green  
- [ ] No L×W / `height_mm` on Rooster root  
- [ ] No other SKU edits; no version bump; no kit keys  
- [ ] Report lists existing-test updates  
- [ ] Report written  

---

## Explicitly not this IC

Plate L×W · Engineer-declared box · nylon/bolts · `vtx` kit key · `"cabe"` · GetFPV crawler · Conversation Engine · propeller B2 (already REVIEWED)
