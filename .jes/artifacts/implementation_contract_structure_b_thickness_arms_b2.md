# Implementation Contract — Structure B additive enrichment B2 (`thickness_mm` arms-only)

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · CLOSED (suite **2286**)  
**Review:** [implementation_review_structure_b_thickness_arms_b2.md](implementation_review_structure_b_thickness_arms_b2.md)  
**Report:** [implementation_report_structure_b_thickness_arms_b2.md](implementation_report_structure_b_thickness_arms_b2.md)  
**Parents:**
- [investigation_contract_structure_b_additive_enrichment.md](investigation_contract_structure_b_additive_enrichment.md)
- [investigation_report_structure_b_additive_enrichment.md](investigation_report_structure_b_additive_enrichment.md)
- [investigation_review_structure_b_additive_enrichment.md](investigation_review_structure_b_additive_enrichment.md) — **PASS WITH NOTES**

**Type:** Additive declared field on existing parts graph. Display-only.  
**Not** ontology reopen. **Not** mass/Σ physics. **Not** plate thickness. **Not** MEASURE/CAD/FEA.

**Baseline:** Structure B Fase 1 + G-N1 CLOSED @ suite **2229**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B2** | YES — `thickness_mm` descriptive / display-only |
| 2 | N1 plate policy | **(b) arms-only first** — **no** `frame_plate.thickness_mm` in this IC |
| 3 | Mass policy | **M0** — root `mass_kg` sole physics mass; no part mass; no Σ |

**Additional locks:**

- display-only — no physics / ERF / ASSEMBLY_READY impact  
- no mass authority / no sum-of-parts  
- `thickness_mm` **may** project `frame_arm` children (N2)  
- thickness-only BOM `└` lines allowed  
- thickness **non-blocking** for part completeness (N3)  
- keyword/context-gated mm extraction (N4)  
- no plate thickness in this slice  

---

## 1. You

- Do **not** add `mass_kg` / length / geometry / inferred material on parts.
- Do **not** add thickness on `frame_plate` / `frame_cage` / `frame_standoff`.
- Do **not** change `_structure_evidence`, `_frame_completeness`, `_derive_*`, ASSEMBLY_READY.
- Do **not** use thickness to estimate mass/density/inertia.
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 2. Intent

```text
Catalog seed (all rows with sourced arm thickness):
  arm_thickness_mm → FrameSpec
        ↓
  frame_part_specs_from_catalog
        ↓
  components["frame_arm"].properties["thickness_mm"]  (even if no material/count)
        ↓
  BOM:  └ arm — 6mm   (or with material/count if present)

Free-text (G-N1 path): "brazos 6mm" / arm-clause with mm
        ↓
  same property on frame_arm (keyword-gated)
```

Physics mass path unchanged (`structure_mass_override_kg` from root only).

---

## 3. Locked behavior

### 3.1 Seed + `FrameSpec`

- Add optional `arm_thickness_mm: float | None` on `FrameSpec` / loader (`library.py`).
- Update `library/frames/_datos.json` for every row whose **cited** `source_url` states arm thickness (investigation §B1; Cursor verified TBS 6mm, Armattan 4mm; update iFlight/TBS 7" from their cited pages the same way — omit if absent, never invent).
- Extend each row’s `source_note` to mention arm thickness when set.
- **Do not** add `plate_thickness_mm` (or any plate thickness field) in this IC.

### 3.2 Catalog projection — N2

In `frame_part_specs_from_catalog` / `_part` helper:

- Create `frame_arm` when **any** of: `count`, `material`, **`arm_thickness_mm` / thickness** is present.
- Project `thickness_mm` `PropertyValue` (unit `"mm"`, `source="declared"`) onto `frame_arm` only.
- `frame_plate` / cage / standoff: **unchanged** (material/count only as today — no thickness).
- TBS/iFlight with arm thickness but no part materials **must** produce a `frame_arm` child (regression target).

### 3.3 BOM — thickness-only lines

Update `_frame_part_sublines` (`project_closure.py`):

- Read optional `thickness_mm`.
- Render suffix e.g. `6mm` when present.
- **Allow** a line when thickness is present even if count and material are absent  
  (today’s `if not count_bit and not material_bit: continue` must treat thickness as sufficient).
- Example shapes (Spanish/ASCII OK as existing style):

```text
   └ arm — 6mm
   └ arm ×4 — fibra de carbono, 4mm
```

No invented mass/material/count.

### 3.4 Free-text extraction — N4

In `domains/aerial.py` part-clause extraction:

- Optional `thickness_mm` only inside a clause that matched an **arm** part alias (`brazo`/`brazos`/`arm`/…).
- Pattern for value: `\d+(?:[.,]\d+)?\s*mm` (or equivalent), scoped to that clause.
- Must **not** fire on root-only `wheelbase 230mm`, stack `30.5mm`, plate-only phrases, or bare `6mm` without arm keyword.
- Plate clauses: **do not** extract thickness in this IC (arms-only).

### 3.5 Completeness — N3

`_structure_part_completeness` unchanged rule: `"high"` if `count` **or** `material` present.  
Thickness alone may create a child + BOM line, but completeness stays `"low"` until count/material exists **or** keep current rule exactly — **do not** require thickness for `"high"`. Prefer: thickness-only → still `"low"` with missing hint, **or** if existing code would leave empty props incomplete, document the choice in the report; never make thickness mandatory for high.

Clarification locked: thickness is enrichment; absence must never mean “estructura inválida” / Structure PASS fail.

### 3.6 Unchanged

- M0 mass / calc engine  
- Structure PASS * footnote  
- G-N1 root+parts except arm thickness extraction  
- IDLE rebind clear-children  
- Node types / `parent_key`  

---

## 4. Tests (mandatory)

| # | Case |
|---|---|
| T1 | Loader parses `arm_thickness_mm`; omits when absent |
| T2 | `frame_part_specs_from_catalog("tbs_source_one_v5_5in")` → `frame_arm` with `thickness_mm≈6` (even without material) |
| T3 | Armattan → `frame_arm.thickness_mm≈4` (with existing materials) |
| T4 | Free-text arm clause `"brazos 6mm"` → `frame_arm.thickness_mm`; `"wheelbase 230mm"` alone → no arm thickness |
| T5 | BOM sub-line shows thickness; thickness-only arm still renders `└` |
| T6 | Twin: Structure ERF / `_frame_completeness` / `_structure_evidence` identical with vs without thickness present |
| T7 | No `thickness_mm` on `frame_plate` from catalog for any seed row |
| Full suite | Green |

---

## 5. Files (expected)

| File | Change |
|---|---|
| `src/jarvis/knowledge/library.py` | `arm_thickness_mm` on `FrameSpec` |
| `library/frames/_datos.json` | seed + source_note |
| `src/jarvis/core/catalog_bind.py` | project thickness; N2 create gate |
| `src/jarvis/domains/aerial.py` | arm-clause thickness extract |
| `src/jarvis/core/project_closure.py` | BOM sub-line |
| `tests/…` | T1–T7 (new or extend graph tests) |

---

## 6. Explicit non-goals

Per-part mass · arm length · plate thickness · cage/standoff thickness · Σ mass · density-from-thickness · geometry · new node types · PASS widen · ASSEMBLY_READY changes · version bump  

---

## 7. Done criteria

- §2–§3 held  
- T1–T7 + full suite green  
- Report: `.jes/artifacts/implementation_report_structure_b_thickness_arms_b2.md`  
- No forbidden scope  

---

## 8. After implement

Cursor writes **implementation review** only (no ratification artifact).
