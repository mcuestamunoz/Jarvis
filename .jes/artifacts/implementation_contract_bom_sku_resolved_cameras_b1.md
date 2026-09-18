# Implementation Contract — BOM `sku_resolved` for cameras (+ FC/sensors) (`B1-bom-sku-resolved-cameras`)

**Project:** Jarvis  
**Date:** 2026-09-18  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke (or waive)

**Status:** **CLOSED** 2026-09-18 — Cursor implemented · Engineer smoke ACCEPT (vigilancia shows `[runcam_phoenix_2]`)

**Parents:**
- Smoke ACCEPT WITH NOTES on [`B1-library-cameras-seed`](implementation_review_library_cameras_seed_b1.md): bound Phoenix 2 showed **`runcam_phoenix_2 (SKU sin resolver)`** despite `completeness=high` + live row in `library/cameras/`
- Same class as historical propeller miss — [`_bom_sku_resolved`](../../src/jarvis/core/project_closure.py) only re-checks motor/battery/propeller/esc/frame/kit_hardware; falls through to `False` for other families
- `ComponentLibrary` already has `has_camera` / `has_fc` / `has_sensor`

**Type:** Display-only: extend `_bom_sku_resolved` so bound SKUs that exist in the library show **`[sku]`**, not **`(SKU sin resolver)`**.  
**Not** new catalog rows · not bind/rebind logic · not mass/power · not Continuity · not version bump · not Conversation Engine · not workspace mutate.

**Output:** `.jes/artifacts/implementation_report_bom_sku_resolved_cameras_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3100** · UI ≥**105** (or current green at ★)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-bom-sku-resolved-cameras`** |
| 2 | Seam | Only `project_closure._bom_sku_resolved` (+ tests). No new modules |
| 3 | Cameras | `family == "cameras"` → `default_library.has_camera(sku)` |
| 4 | Same miss (this Buy) | Also wire **`flight_controller` → `has_fc`** and **`sensors` → `has_sensor`** if those family strings are what `CatalogRef.family` uses today — report exact Literal values. Do **not** invent new family names |
| 5 | Unchanged | `catalog_ref is None` → no suffix; missing library row → still `(SKU sin resolver)` (Scenario C honesty) |
| 6 | Forbidden | Touching gap builders / ERF / bind paths “while here” · version bump · LLM · inventing resolve via `.name` shape |
| 7 | Live | Default tests-only; optional: reopen vigilancia → `estado` shows `[runcam_phoenix_2]` |

**Product sentence:**

```text
Si la cámara está bound al Phoenix 2 del catálogo, el estado muestra
[runcam_phoenix_2] — no miente con “SKU sin resolver”.
```

---

## 1. You (Claude)

1. Add the three family branches (or cameras-only if FC/sensors Literal differs — STOP and ask if unclear).  
2. Tests: bound camera → `sku_resolved` True / BOM suffix `[runcam_phoenix_2]`; unbound / wrong sku → marker or empty per existing rules.  
3. Short report. No guide rewrite required (optional one-line under cameras seed if desired).  
4. No version bump.

**STOP if** tempted to resolve from `.name` without `catalog_ref` + `has_*`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Bound `runcam_phoenix_2` + `catalog_ref.family=cameras` → `_bom_sku_resolved` True |
| T2 | `format_bom_lines` / estado-style suffix → `[runcam_phoenix_2]` not `(SKU sin resolver)` |
| T3 | Unknown sku + cameras family → False / sin resolver |
| T4 | `catalog_ref is None` → no `[sku]` suffix |
| T5 | Regression: motor/esc/frame still resolve; package `0.4.1`; suite green |

---

## 3. Smoke (Engineer)

On vigilancia (already bound Phoenix 2):

1. `estado` → cameras line shows **`[runcam_phoenix_2]`**, not `(SKU sin resolver)`.  
2. Optional: `actualiza la cámara` still ok.

**ACCEPT when:** display matches bound truth.

---

## 4. Out of scope

| Item | Note |
|---|---|
| M3 `power_w` | Separate Buy |
| More camera SKUs | Not this |
| Changing completeness / catalog_ref writers | Not this |

---

## 5. Done when

- [x] Engineer ★ (authorized Cursor implement)  
- [x] Branches + T1–T5 + report  
- [x] Cursor self-check PASS — [review](implementation_review_bom_sku_resolved_cameras_b1.md)  
- [x] Engineer smoke ACCEPT (vigilancia 2026-09-18) — `cameras: runcam_phoenix_2 [runcam_phoenix_2]`

---

## 6. Handoff

```text
Engineer → ★ B1-bom-sku-resolved-cameras (this micro-IC)
Claude   → implement
Cursor   → review
Engineer → smoke estado on vigilancia
```
