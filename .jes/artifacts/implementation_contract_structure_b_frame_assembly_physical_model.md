# Implementation Contract — Structure B Frame Assembly Physical Model B2 (plate multiplicity)

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · CLOSED (suite **2294**)  
**Review:** [implementation_review_structure_b_frame_assembly_physical_model.md](implementation_review_structure_b_frame_assembly_physical_model.md)  
**Report:** [implementation_report_structure_b_frame_assembly_physical_model.md](implementation_report_structure_b_frame_assembly_physical_model.md)  
**Parents:**
- [investigation_contract_structure_b_frame_assembly_physical_model.md](investigation_contract_structure_b_frame_assembly_physical_model.md)
- [investigation_report_structure_b_frame_assembly_physical_model.md](investigation_report_structure_b_frame_assembly_physical_model.md)
- [investigation_review_structure_b_frame_assembly_physical_model.md](investigation_review_structure_b_frame_assembly_physical_model.md) — **PASS WITH NOTES** · **Engineer Buy locked**

**Type:** Schema + catalog projection + BOM display for **declared plate multiplicity**.  
**Not** free-text multi-plate parsing. **Not** closed role taxonomy. **Not** thickness-only on single `frame_plate`. **Not** MEASURE/CAD/FEA/Σ mass.

**Baseline:** Parts Graph Fase 1 + G-N1 @ **2229** · arms `thickness_mm` B2 @ **2286** · suite **2286** · Fase 1 graph = product (not greenfield).

---

## 0. Engineer Buy (locked 2026-09-05)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B2** | **YES** — ordinal plate siblings + free-text `label` + `plates: list[PlateSeed]` |
| 2 | Closed role taxonomy (`frame_plate_top` / …) | **NO** |
| 3 | Thickness-only on single `frame_plate` | **NO** |
| 4 | **N1** seed inclusion | **(c) curated per SKU** — explicit lists in §3.1; never auto-ingest every carbon piece on a page |
| 5 | **N2** precedence | If `plates` non-empty → **canonical**; scalar `plate_*` = legacy fallback only when `plates` absent/empty |
| 6 | **N3** identity | One node per curated named plate — **do not** merge by equal thickness |
| 7 | **N4** free-text multi-plate | **OUT** — debt only; no opportunistic NL parser in this IC |
| 8 | **N6** completeness hardcode | **Preserve current `_part` behavior**; inconsistency vs `_structure_part_completeness` = **known debt**, do not “fix” incidentally |
| 9 | **N7** key bound | `frame_plate` + `frame_plate_2`…`frame_plate_8` max (**≤8**); reject other `frame_plate_*` shapes |
| 10 | Mass / PASS * | **M0**; Structure PASS * footnote **unchanged** |

---

## 1. You

- Do **not** invent plate roles, cross-SKU equivalences, or scrape-all Included kits.
- Do **not** parse free-text into multiple plate siblings.
- Do **not** add per-part `mass_kg`, dims, hardware, cage/standoff thickness, or Σ→physics.
- Do **not** change `_structure_evidence`, `_frame_completeness`, `_derive_*`, ASSEMBLY_READY, PASS * footnote.
- Do **not** “fix” catalog `completeness="high"` hardcode (N6).
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 2. Intent

```text
CATALOG SEED (_datos.json)
  plates: [ {label, thickness_mm, material?}, … ]   # curated, explicit
        ↓
FrameSpec.plates
        ↓
frame_part_specs_from_catalog
        ↓
components["frame_plate"] , ["frame_plate_2"], …   # ordinal siblings, parent_key="frame"
  properties: label?, thickness_mm?, material?, count?
        ↓
BOM:  └ plate — Bottom, 2.5mm
      └ plate — Top, 2mm
      └ plate — Middle, 2mm
```

No LLM/free-text path into structural architecture in this IC.

---

## 3. Locked behavior

### 3.1 Schema — `PlateSeed` + `FrameSpec.plates`

In `library.py`:

```text
@dataclass(frozen=True)
class PlateSeed:
    label: str | None = None          # verbatim-from-source display string
    thickness_mm: float | None = None
    material: str | None = None
```

- `FrameSpec.plates: list[PlateSeed] | None = None` (additive).
- Keep existing `plate_count` / `plate_material` scalars (legacy fallback).
- Loader: parse `plates` list when present; omit/`None` when absent; never invent entries.
- Soft reject / raise on >8 entries in seed (N7) — do not silently truncate without a test asserting the bound.

### 3.2 Curated seed lists (N1) — lock these exact rows

Update `library/frames/_datos.json` + `source_note` per SKU. **Only** these plates (not Camera / HD Cam / VTX / etc. unless listed here):

| SKU | `plates` (order = ordinal) |
|---|---|
| `tbs_source_one_v5_5in` | (1) label `"Top"`, 2mm · (2) `"Middle"`, 2mm · (3) `"Bottom"`, 2.5mm |
| `tbs_source_one_v5_1_7in_dc` | (1) `"Top/Middle"`, 2mm · (2) `"Bottom"`, 2.5mm |
| `iflight_xl7_v4_7in` | (1) `"upper and lower plate"`, 2mm · (2) `"vertical side plates"`, 1.5mm |
| `armattan_rooster_5in` | (1) `"Main Plate"`, 4mm, material carbon as today · (2) `"Top (LiPo) plate"`, 2mm · (3) `"Small front (top) plate"`, 1.5mm · (4) `"Small rear (top) plate"`, 1.5mm |

- Material on Armattan plate[0]: use existing carbon wording (`fibra de carbono`) when setting `PlateSeed.material`; other Armattan plates may omit material if not separately stated (do not invent).
- After adding `plates`, Armattan may keep scalar `plate_material` for legacy rows elsewhere, but **projection ignores scalars** when `plates` non-empty (N2).
- `source_note` must state that plate list is **curated** (not full Included kit).

### 3.3 Catalog projection — N2 / N3 / N7

In `frame_part_specs_from_catalog`:

1. If `spec.plates` is non-`None` and `len(plates) > 0`:
   - Emit **only** from `plates` (ignore `plate_count` / `plate_material` for child emission).
   - Key `i=0` → `frame_plate`; `i≥1` → `frame_plate_{i+1}` (so index 1 → `frame_plate_2`).
   - Cap at 8; refuse/assert beyond.
   - Each child: `parent_key="frame"`, `component_type="structure_part"`.
   - Props: `thickness_mm` / `material` / optional `count` when set; **`label`** as `PropertyValue` (str, `source="declared"`) when label non-empty.
   - Create child when **any** of label / thickness / material / count is present (mirror arm thickness gate).
2. Else (no `plates`): legacy path unchanged — `_part(FRAME_PLATE_KEY, …, plate_count, plate_material)` only.
3. Arms / cage / standoff: **unchanged**.
4. **N6:** keep existing `_part` `completeness="high"` hardcode; do not switch plate siblings to `_structure_part_completeness` in this IC.

### 3.4 BOM — ordinal plates + label

Update `_frame_part_sublines`:

- Iterate arm → **all present plate siblings in ordinal order** → cage → standoff.
- Plate key recognition: `frame_plate` or `frame_plate_2`…`frame_plate_8` only (helper preferred).
- Display base word remains `"plate"`; when `label` present, include it, e.g.:

```text
   └ plate — Bottom, 2.5mm
   └ plate — Top, 2mm
   └ plate — Middle, 2mm
   └ plate — Main Plate, 4mm
```

(Exact punctuation may match existing `material_bit`/`thickness_bit` style; label before thickness when both exist. Prefer: `plate — {label}, {thickness}` or `plate — {label}` if no thickness.)

- Thickness-only / label-only lines allowed (same gate family as arms B2).
- Do **not** invent role names in the label column — render seed `label` verbatim.

### 3.5 Free-text — N4 OUT

- **No** changes to multi-plate free-text extraction / ordinal key emission from chat.
- Existing single-key plate clause behavior stays.
- Do **not** add plate-clause `thickness_mm` extraction in this IC (prior arms-only thickness lock stands for free-text).
- Name debt in implementation report: free-text multi-plate / plate thickness NL = OUT.

### 3.6 Unchanged

- M0 / calc engine / Structure PASS * / architecture progress  
- IDLE `clear_frame_part_children` (already `parent_key`-based — must clear ordinal siblings on rebind; add regression if missing)  
- Node *type* set (`structure_part` only)  
- Arm thickness B2 behavior  

---

## 4. Tests (mandatory)

| # | Case |
|---|---|
| T1 | Loader parses `plates`; omits when absent; >8 rejected or hard-fails as locked |
| T2 | TBS 5" catalog → three plate keys with Top/Middle/Bottom thicknesses 2 / 2 / 2.5 |
| T3 | Armattan → four plate siblings; Main 4mm; LiPo 2mm; front/rear 1.5mm; cage/standoff still present |
| T4 | N2: when `plates` set, scalar `plate_material` alone does **not** create a fifth/conflicting plate path (projection from `plates` only) |
| T5 | N3: Top and Middle both 2mm remain **two** nodes |
| T6 | BOM renders distinct `└ plate` lines with labels |
| T7 | Twin: `_frame_completeness` / `_structure_evidence` / ERF Structure verdict byte-identical with vs without plate siblings |
| T8 | Rebind Armattan→TBS clears `frame_plate_2`… (no stale siblings) |
| T9 | Free-text multi-plate phrase does **not** gain new ordinal behavior (no accidental parser) |
| Full suite | Green |

---

## 5. Files (expected)

| File | Change |
|---|---|
| `src/jarvis/knowledge/library.py` | `PlateSeed`; `FrameSpec.plates`; loader + bound |
| `library/frames/_datos.json` | curated `plates` + `source_note` for all four SKUs |
| `src/jarvis/core/catalog_bind.py` | project ordinal plates; N2 precedence |
| `src/jarvis/core/project_closure.py` | BOM iterate plate siblings + label |
| `src/jarvis/domains/aerial.py` | optional tiny `is_frame_plate_key` / key helpers if needed — **no** free-text multi-plate |
| `tests/…` | T1–T9 (new or extend) |

Optional doc touch (same PR OK): Vision debt line naming free-text multi-plate OUT + completeness hardcode debt — only if already editing Vision; not required for green.

---

## 6. Explicit non-goals

Closed role enum · free-text multi-plate · auto-ingest full Included lists · per-part mass · dims · hardware · Σ thickness / Σ mass · cage/standoff multiplicity · MEASURE/CAD/FEA · PASS * wording change · completeness hardcode fix · version bump  

---

## 7. Done criteria

- §0–§3 held  
- T1–T9 + full suite green  
- Report: `.jes/artifacts/implementation_report_structure_b_frame_assembly_physical_model.md`  
- No forbidden scope  

---

## 8. After implement

Cursor writes **implementation review** only (no `engineer_ratification_*`).
