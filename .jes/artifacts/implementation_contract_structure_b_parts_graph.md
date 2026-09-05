# Implementation Contract — Structure B Parts Graph (Fase 1)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · Fase 1 **CLOSED** pending Engineer ★ (suite **2223**)  
**Review:** [implementation_review_structure_b_parts_graph.md](implementation_review_structure_b_parts_graph.md)  
**Report:** [implementation_report_structure_b_parts_graph_fase1.md](implementation_report_structure_b_parts_graph_fase1.md)  
**Type:** Schema + declared parts graph + BOM display + optional catalog seed projection. **Not** MEASURE. **Not** PASS widen.

**Parents:**
- [investigation_report_structure_b_parts_graph.md](investigation_report_structure_b_parts_graph.md)
- [investigation_review_structure_b_parts_graph.md](investigation_review_structure_b_parts_graph.md) — **PASS WITH NOTES** (N1 BOM filter mandatory)
- [engineer_ratification_structure_b_parts_graph.md](engineer_ratification_structure_b_parts_graph.md) — ★ B = graph; wheelbase in model path; config vocab OK
- Honesty IC: [implementation_contract_structure_honesty_pass_star.md](implementation_contract_structure_honesty_pass_star.md) — **must ship first**

**Baseline:** tag **`v0.3.6`** · suite **2197** (+ honesty IC suite when that lands)

**Buy:** Minimum parts graph — `ComponentSpec.parent_key` + part-type children; richer KNOW/CLAIM; Structure PASS evidence **unchanged**.

---

## 0. You

- Edit only files in §5.
- Do **not** change `_structure_evidence`, `_derive_subsystem_verdict`, `_derive_overall`.
- Do **not** add `arm`/`plate`/`cage`/`standoff` to `BLOCK_TO_COMPONENTS["structure"]` (stays `["frame"]` only).
- Do **not** change `_frame_completeness` (still mass + material on the **frame root** only).
- Do **not** add `mounts_on`, spatial edges, per-instance arm nodes, `hardware` nodes, sum-of-parts mass.
- Do **not** cross-check `arm.count` ↔ `motor_count` or `configuration` ↔ part graph.
- Do **not** invent manufacturer numbers — seed fields only when cited on the row’s `source_url` / existing `source_note`.
- Do **not** bump version.
- Full suite green. Zero weakened tests.
- **Gate:** do not start this IC until honesty IC is REVIEWED PASS (or Engineer explicitly overrides).

---

## 1. Intent

```text
components["frame"]                    ← root (unchanged authority for PASS)
components["frame_arm"]    parent_key="frame"  ← optional part-type node + count
components["frame_plate"]  parent_key="frame"
components["frame_cage"]   parent_key="frame"
components["frame_standoff"] parent_key="frame"
```

BOM shows children **only** as sub-lines under `frame` (Cursor review N1).  
PASS / architecture-progress / ASSEMBLY_READY: **byte-identical** with or without children.

---

## 2. Locked behavior

### 2.1 Schema — `ComponentSpec.parent_key`

In `src/jarvis/schemas/action_schema.py`, add:

```python
parent_key: str | None = None
```

Optional, default `None`. First intra-project parent/child precedent — additive; existing projects deserialize unchanged.

`parent_key` stores the **dict key** of the parent in `design_properties.components` (for Fase 1 always `"frame"` when set).

### 2.2 Locked part keys (Cursor N2)

| Dict key | Part type | Properties (all optional, `source="declared"`) |
|---|---|---|
| `frame_arm` | arm | `count` (int), `material` |
| `frame_plate` | plate | `count` (int), `material` |
| `frame_cage` | cage | `material` (count optional; omit if 1/unspecified) |
| `frame_standoff` | standoff | `count` (int), `material` |

- One node **per type**, not per physical instance (`motor_count` precedent).  
- `suggested_key` for each child = its dict key.  
- `component_type` = `"structure_part"` (or equivalent single literal — pick one and use everywhere).  
- **Out:** `hardware`, per-instance keys (`arm_front_left`, …).

### 2.3 Frame root additive properties

On `components["frame"]` only (extractors + optional catalog projection):

| Key | Rules |
|---|---|
| `configuration` | Closed vocab match only: `quad_x`, `quad_plus`, `hex`, `deadcat`, `tricopter`. Alias table in `domains/aerial.py` (FC/GPS pattern). **Never** infer from `motor_count` or part graph. Unrecognized → absent. |
| `wheelbase_mm` | Declared float; regex from text (e.g. `230mm` / `230 mm` wheelbase context) and/or catalog. **Never** treat bare mm as `size_class_inch` (existing Structure A rule stands). |

Add `configuration`, `wheelbase_mm`, and `count` to `_MEASURABLE` in `project_closure.py` so declared values are not silently dropped from measurable routing — same posture as `"model"` / `"material"`.

### 2.4 Writers / apply

- Extend or add a small writer helper (prefer `component_writers.py`) to **upsert** a part child: set `parent_key="frame"`, merge properties, set completeness for the **child** independently (child completeness must **not** feed `_frame_completeness` / Structure PASS).
- Free-text: extend `extract_frame_properties` for `configuration` / `wheelbase_mm` on the root; add a dedicated extractor (same file) for part-type phrases that returns which locked key + props (e.g. “4 brazos fibra de carbono”, “standoffs aluminio”). Wire through the **existing** frame/component apply path with the smallest change — do **not** invent a new subsystem or Conversation Engine.
- If text is unrecognized for parts → do not create empty child stubs.

### 2.5 Catalog — `FrameSpec` + seed + bind (bundled per Engineer ★ + report lean)

**FrameSpec** (`library.py`) — additive optional fields (all default `None`):

- `wheelbase_mm: float | None`
- `configuration: str | None` (must be one of the closed vocab values if set)
- `arm_count: int | None`
- `arm_material: str | None`
- `plate_material: str | None`
- `cage_material: str | None`
- `standoff_material: str | None`
- `standoff_count: int | None` (optional)
- `plate_count: int | None` (optional)

Loader: omit / `None` when JSON key absent — never invent.

**Seed** (`library/frames/_datos.json`):

- Enrich rows **only** where the row’s own `source_url` / existing `source_note` already supports the fact.
- **Required evidence case:** `armattan_rooster_5in` — `source_note` already states carbon fiber main plate/arms, titanium cage, aluminum standoffs → set `arm_material` / `plate_material` / `cage_material` / `standoff_material` accordingly (Spanish canonical material names consistent with library aliases where they exist; “titanio” / “aluminio” / “fibra de carbono”).
- `wheelbase_mm`: add only if the cited page states motor-to-motor / wheelbase; update `source_note` to mention the figure. If a row’s page does not state it → leave `null`/absent (TBS rows without material stay honest).
- Do **not** fabricate counts when the page does not state them (Armattan arm count may stay unset unless page states it).

**`bind_frame_from_catalog`:**

- Still returns the **frame root** `ComponentSpec` (API shape preserved).
- Additionally project onto root: `wheelbase_mm`, `configuration` when present on `FrameSpec`.
- New helper (same module or writers): `frame_part_specs_from_catalog(sku) -> dict[str, ComponentSpec]` mapping locked keys → child specs with `parent_key="frame"` and declared materials/counts from `FrameSpec`. Empty dict when no part fields on the SKU.
- Production apply path that already calls `bind_frame_from_catalog` / `set_frame_material(..., catalog_ref=)` (assist IC-3 apply): after writing the root, also upsert returned part children into `design_properties.components`. If no part fields → no children (root-only, today’s behavior).

**Diverge:** existing mass/class/material diverge rules unchanged. Optional: if a later diverge clears frame `catalog_ref`, leave children as declared orphans or clear children with matching catalog provenance — pick the **simpler** honest option and test it (prefer: leave children; do not invent auto-delete unless cheap). Document choice in implementation report.

### 2.6 BOM — Cursor N1 (mandatory)

In `build_component_bom`:

- Specs with `parent_key is not None` must **not** appear in top-level `defined` / `incomplete` / `declarative` / `missing` buckets.
- Orphans (`parent_key` set but parent key absent from `components`): still excluded from top-level buckets; may be omitted from display or shown once as a single honest warning line — **must not crash**. Prefer omit from BOM lines + unit test.

In `format_bom_lines` (needs `project_state`):

- After each **frame** top-level line (`defined` / `incomplete` / `declarative`), append display-only sub-lines for children whose `parent_key == "frame"`, in key order `frame_arm`, `frame_plate`, `frame_cage`, `frame_standoff`:

```text
✓ frame: … (high)
   └ arm ×4 — fibra de carbono
   └ plate ×2 — fibra de carbono
   └ cage — titanio
   └ standoff ×4 — aluminio
```

Rules:

- Label = short type (`arm` / `plate` / `cage` / `standoff`), not the dict key.
- Show `×N` only when `count` is present.
- Show `— {material}` only when material present.
- No SKU suffix on part lines in Fase 1 unless child has `catalog_ref` (none expected).

### 2.7 Structure PASS / architecture

Regression (mandatory): with and without children present, `_structure_evidence` fields that feed PASS, `BLOCK_TO_COMPONENTS["structure"]`, and architecture progress for structure are **unchanged**. Children never required for completeness.

### 2.8 Forbidden claim sentences (do not implement helpers that emit these)

```text
"Los 4 brazos sostienen los 4 motores."
"La jaula protege el hardware de impactos."
"Los brazos están correctamente dimensionados para la configuración quad-X."
"El ensamblaje estructural es coherente."
"Standoffs de aluminio — compatibles con el stack declarado."
"El wheelbase permite montar los motores sin interferencia."
```

Display is identity/count/material declaration only.

---

## 3. Tests (mandatory)

| Area | What |
|---|---|
| Schema | `ComponentSpec(parent_key="frame")` round-trip; default `None` |
| Extractors | `configuration` / `wheelbase_mm` from text; unrecognized → absent; never from `motor_count` alone |
| Parts extract | Declared part phrase → correct locked key + props; unrecognized → no stub |
| BOM N1 | Child with `material` does **not** appear as peer `✓ frame_arm:`; appears as `└` under frame |
| BOM orphan | `parent_key="frame"` with no frame → no crash; no peer line |
| PASS regression | Fixture with children: structure verdict / evidence bits identical to root-only twin |
| Catalog | Armattan bind → root + children materials from seed; a TBS row without part fields → root only |
| Wheelbase | When seed has `wheelbase_mm`, root property present after bind |
| Full suite | Green |

Prefer extending `tests/test_catalog_foundation_v1.py`, `tests/test_project_closure_v1.py`, `tests/test_catalog_bind_v1.py` / frame bind tests, new focused `tests/test_frame_parts_graph_v1.py` if cleaner.

---

## 4. Explicit non-goals

- MEASURE / CAD / FEA / clearance / strength  
- Honesty `PASS *` (separate IC — prerequisite)  
- `hardware` / per-instance nodes / `mounts_on`  
- Sum-of-parts mass  
- Widening Structure PASS  
- Version bump  

---

## 5. Files you may edit

| Path | Role |
|---|---|
| `src/jarvis/schemas/action_schema.py` | `parent_key` |
| `src/jarvis/domains/aerial.py` | config/wheelbase/part extractors; alias table |
| `src/jarvis/core/component_writers.py` | upsert part children; frame root props if needed |
| `src/jarvis/core/catalog_bind.py` | root projection + `frame_part_specs_from_catalog` |
| `src/jarvis/core/project_closure.py` | `_MEASURABLE`; BOM filter; sub-lines |
| `src/jarvis/knowledge/library.py` | `FrameSpec` optional fields + loader |
| `library/frames/_datos.json` | sourced enrichment only |
| `src/jarvis/core/orchestrator.py` | **minimal** apply wiring if catalog-assist already writes frame — only to upsert parts after bind |
| `tests/…` | §3 |

Do **not** edit `engineering_readiness.py` evidence/verdict derivation unless a test proves a one-line import-only necessity (default: **zero** edits there).

---

## 6. Done criteria

- §2 locked behaviors present  
- N1: no peer BOM lines for children  
- PASS regression green  
- Seed only sourced facts  
- Full suite green  
- Implementation report: files, behavior, tests, residual (Fase 2 hardware/per-instance explicitly out)

---

## 7. After implementation

Cursor reviews against this IC (especially N1 + PASS regression + seed honesty). On PASS WITH NOTES → Engineer ★ closes Structure B Fase 1 or names follow-ons.
