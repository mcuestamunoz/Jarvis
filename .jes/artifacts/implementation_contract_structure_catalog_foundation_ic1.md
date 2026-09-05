# Implementation Contract — Structure Catalog Foundation IC-1 (schema + seed)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · IC-1 **CLOSED**  
**Review:** [implementation_review_structure_catalog_foundation_ic1.md](implementation_review_structure_catalog_foundation_ic1.md)  
**Report:** [implementation_report_structure_catalog_foundation_ic1.md](implementation_report_structure_catalog_foundation_ic1.md)  
**Suite:** **2177**  
**Type:** Catalog groundwork only — **schema + tiny real seed + library readers**.  
**Not** bind. **Not** BOM/`sku_resolved`. **Not** Continuity. **Not** assist. **Not** CAD/layout.

**Parents:**
- [investigation_report_structure_catalog_foundation.md](investigation_report_structure_catalog_foundation.md)
- [investigation_review_structure_catalog_foundation.md](investigation_review_structure_catalog_foundation.md) — **PASS WITH NOTES**
- [engineer_ratification_structure_catalog_foundation.md](engineer_ratification_structure_catalog_foundation.md) — ★ Not yet IC-2/IC-3; Engineer opened **IC-1** via `GENERA EL IC`

**Baseline:** tag **`v0.3.6`** · claim hygiene + control parity + Structure Foundations claim-copy · suite **2171**

**Buy (this IC only):** Bank frame identity data the ESC way — reachable in schema/library, **zero product consumer**.

---

## 0. You

- Edit only files in §5.
- Do **not** add `bind_frame_from_catalog` or any writer/orchestrator/CLI path that sets `frame.catalog_ref`.
- Do **not** change `component_writers.py`, `catalog_bind.py` (except zero touch), `project_closure.py`, `engineering_readiness.py`, `project_continuity.py`, `orchestrator.py`, `render_views.py`.
- Do **not** extend `_bom_sku_resolved` for `"frame"`.
- Do **not** wire `catalog_bound` into Structure PASS / `_derive_subsystem_verdict`.
- Do **not** add `wheelbase`, `arm_count`, tip-clearance, layout params, CAD/FEA.
- Do **not** invent SKUs or fabricate mass/class/material — every seed row must cite a real manufacturer page/datasheet.
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 1. Intent

Make `"frame"` a first-class catalog family **without** changing any engineering claim path:

```text
library/frames/_datos.json
        ↓
ComponentLibrary (get_frame / has_frame / list_frames)
        ↓
CatalogRef.family includes "frame"
        ↓
(no bind, no BOM, no Continuity, no CLI — same posture as ESC today)
```

Structure A free-text declare remains the only live product path for frames.  
This IC does **not** make `structure.catalog_bound` True in any production flow.

---

## 2. Locked behavior

### 2.1 `CatalogRef.family`

In `src/jarvis/schemas/action_schema.py`, extend:

```text
Literal["motor", "battery", "propeller", "esc", "frame"]
```

No other schema changes. `ComponentSpec.catalog_ref` stays optional.

### 2.2 `FrameSpec` + library loaders

In `src/jarvis/knowledge/library.py`, add a frozen dataclass **mirroring `EscSpec` style**:

| Field | Required in loader? | Notes |
|---|---|---|
| `name` | yes (SKU key) | Catalog id |
| `mass_g` | **yes** | Manufacturer-declared empty/frame mass; raise `ValueError` if missing (same pattern as ESC `continuous_current_a`) |
| `size_class_inch` | **yes** | Declared prop/frame class; raise if missing |
| `manufacturer` | optional in loader | Seed rows **must** populate (enforced by tests) |
| `model` | optional in loader | Seed rows **must** populate |
| `material` | optional | Omit if manufacturer does not state it — never invent |
| `part_number` | optional | |
| `source_url` | optional in loader | Seed rows **must** populate |
| `source_note` | optional | Human note of what was read |
| `identity_status` | optional in loader | Seed rows **must** be `"verified"` |

**Do not** add `wheelbase`, `arm_count`, `configuration` fields in this IC.

API (mirror ESC):

```text
get_frame(name) -> FrameSpec     # KeyError if missing — never fabricate
has_frame(name) -> bool
list_frames() -> list[FrameSpec]
```

Loader path: `library/frames/_datos.json`. Missing file → empty dict (same as ESC), not crash.

No `find_frames_for_*` in this IC (no consumer).

### 2.3 Seed — `library/frames/_datos.json`

- **≥ 2** and **≤ 6** real SKUs.
- At least **two distinct** `size_class_inch` values (e.g. a 5″-class and a 7″-class product — exact products chosen by implementer from manufacturer sources).
- Every row: `manufacturer`, `model`, `mass_g`, `size_class_inch`, `source_url`, `identity_status: "verified"`, plus `source_note` stating what the page claims.
- **Never invent** mass, class, or material. If a field is unclear on the source page, omit optional fields or drop the SKU.
- Implementation report must list each SKU + URL + the exact numbers copied.

### 2.4 Doc hygiene (minimal)

In `docs/PHYSICAL_COMPONENT_CATALOG_V1.md`, update the deferred line that still says “frame SKU catalog” so it records **IC-1 schema+seed landed / bind still deferred** — one short factual edit. Do **not** rewrite catalog doctrine.

### 2.5 Explicitly unchanged

- Structure A screening / claim-copy BOM & Continuity  
- `set_frame_material` / `structure_mass_override_kg` / calc  
- `invalidate_diverged_catalog_refs`  
- Any assist / acquisition CTA  
- ESC/motor/battery/propeller catalogs  

---

## 3. Forbidden

- `bind_frame_from_catalog`  
- Setting `catalog_ref` on frame from any product path  
- BOM `sku_resolved` for frame  
- Claiming Structure validated / fit / clearance / load from catalog  
- Marketplace-scale seed or scraped unverified rows  
- Parallel catalog architecture outside `ComponentLibrary`  

---

## 4. Tests (mandatory)

Extend `tests/test_catalog_foundation_v1.py` (preferred) or a thin sibling:

1. Seed rows load; `get_frame` returns `FrameSpec` with required physical fields.  
2. `has_frame` true for a seed id; false for a phantom id.  
3. `get_frame(phantom)` → `KeyError` (never fabricate).  
4. Missing `mass_g` or `size_class_inch` in a tmp library JSON → `ValueError` on load/list.  
5. `CatalogRef(family="frame", sku=...)` constructs successfully.  
6. Extend `test_unknown_sku_never_fabricated` (or equivalent) to include `has_frame` / `get_frame`.

**Do not** add bind/orchestrator/BOM tests in this IC.

Full suite green after changes.

---

## 5. Files allowed

| Path | Change |
|---|---|
| `src/jarvis/schemas/action_schema.py` | `CatalogRef.family` += `"frame"` |
| `src/jarvis/knowledge/library.py` | `FrameSpec` + load/get/has/list |
| `library/frames/_datos.json` | **NEW** — curated seed |
| `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` | Deferred-list hygiene only |
| `tests/test_catalog_foundation_v1.py` | Mandatory tests above |

No other paths.

---

## 6. Done when

1. §2.1–§2.4 complete.  
2. Mandatory tests pass; full suite green.  
3. Implementation report lists SKUs + URLs + copied numbers; states **no** bind/BOM/Continuity/behavior change for Structure A.  
4. Cursor review PASS (or PASS WITH NOTES) against this IC.

---

## 7. Out of this IC (later threads only)

| Phase | Status |
|---|---|
| **IC-2** bind + diverge + BOM `sku_resolved` | **Not authorized** (★ Not Buy) |
| **IC-3** assist | **Not authorized** |
| Layout / CAD / FEA | Out |

---

## 8. Engineer gate

**Do not implement until Engineer `procede` on this IC.**  
If no → edit this IC in place (no dual ratification doc).
