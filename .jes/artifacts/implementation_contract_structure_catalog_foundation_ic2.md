# Implementation Contract — Structure Catalog Foundation IC-2 (bind + BOM + diverge)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · IC-2 **CLOSED**  
**Review:** [implementation_review_structure_catalog_foundation_ic2.md](implementation_review_structure_catalog_foundation_ic2.md)  
**Report:** [implementation_report_structure_catalog_foundation_ic2.md](implementation_report_structure_catalog_foundation_ic2.md)  
**Suite:** **2188**  
**Type:** Catalog **bind** for frames — identity + projection + frankenstein clear + BOM resolve.  
**Not** assist / numbered pick UX (IC-3). **Not** CAD/layout. **Not** Structure PASS via `catalog_bound`.

**Parents:**
- [implementation_contract_structure_catalog_foundation_ic1.md](implementation_contract_structure_catalog_foundation_ic1.md) — **CLOSED** (suite **2177**)
- [investigation_report_structure_catalog_foundation.md](investigation_report_structure_catalog_foundation.md) — Not yet for bind as *physics* Buy; Engineer opened IC-2 for **identity/BOM/trazabilidad**
- [engineer_ratification_structure_catalog_foundation.md](engineer_ratification_structure_catalog_foundation.md)

**Baseline:** tag **`v0.3.6`** · IC-1 landed · suite **2177**

**Buy (this IC):** Durable frame SKU identity in project state + honest BOM `[sku]` + diverge clear — **same Structure A physics** as free-text (mass still → `structure_mass_override_kg` unconditionally).

---

## 0. You

- Edit only files in §5.
- Do **not** add CLI assist / `ayúdame a elegir` / acquisition CTA for frames (IC-3).
- Do **not** wire `catalog_bound` into `_derive_subsystem_verdict` / ASSEMBLY_READY.
- Do **not** change LEVEL A screening semantics (`frame_class_compatibility_state` logic).
- Do **not** add `wheelbase` / arm geometry / fit / strength claims.
- Do **not** invent SKUs or expand seed beyond what IC-1 already curated (may *read* existing seed only).
- Do **not** bump version.
- Full suite green. Zero weakened tests.

---

## 1. Intent

```text
IC-1: library/frames + CatalogRef "frame" + get/has/list
IC-2: bind_frame_from_catalog(sku)
        → ComponentSpec with catalog_ref + mass_kg + size_class_inch [+ material]
        → set_frame_material(...) preserves catalog_ref + mirrors structure_mass_override_kg
        → BOM sku_resolved via has_frame
        → invalidate_diverged_catalog_refs clears frame ref if mass OR class diverges
IC-3: (out) assist UX
```

Free-text Structure A path remains valid. Bind is optional identity upgrade.

**Honesty lock:** Bound frame ≠ Structure validated ≠ clearance ≠ load-ready.

---

## 2. Locked behavior

### 2.1 `bind_frame_from_catalog` — `catalog_bind.py`

Add a pure helper mirroring `bind_esc_from_catalog` / `bind_battery_from_catalog`:

```text
bind_frame_from_catalog(sku, *, library=None, base=None) -> ComponentSpec
```

- `library.get_frame(sku)` — KeyError if missing (never fabricate).
- `catalog_ref = CatalogRef(family="frame", sku=sku)`.
- Project **required**:
  - `mass_kg` = `FrameSpec.mass_g / 1000.0` (unit `kg`, `source="declared"`, confidence ≥ 0.9)
  - `size_class_inch` from `FrameSpec.size_class_inch` (unit `in`, `source="declared"`)
- Project **optional**: `material` only if `FrameSpec.material` is not None.
- `suggested_key="frame"`, `component_type="structure"`, `name=sku`, `completeness`/`missing_fields` via existing `_frame_completeness` (or equivalent) over the projected props.
- Support `base=` merge like other binders (preserve unrelated props if any).

No CLI caller required in this IC — **test-callable API** is enough (same early posture as battery/propeller bind before their UX ICs). If a single internal apply helper is needed for tests, keep it deterministic and non-UX.

### 2.2 Writer — preserve identity on bind, clear on free-text replace

Today `set_frame_material` rebuilds `ComponentSpec` **without** `catalog_ref` (always unbound).

**Required:**

1. Extend `set_frame_material` so a bind/apply path can persist `catalog_ref` (and SKU `name`) on the written frame spec.
2. **Free-text / unbound writes** (no catalog_ref supplied): resulting frame must have `catalog_ref is None` (do not silently keep a stale SKU after a free-text overwrite).
3. Mass mirror to `structure_mass_override_kg` stays as today (N1 hotfix: merge-aware). Binding must go through this mirror — **no second mass path**.

Smallest acceptable shape (pick one; document in report):

- Add optional kwargs `catalog_ref=None`, `component_name=None` to `set_frame_material`, **or**
- Thin `apply_frame_component(project_state, spec)` that writes `components["frame"]=spec` (with ref) and updates `structure_mass_override_kg` from `spec.properties["mass_kg"]` using the same merge rules — must not fork mass semantics.

Call sites that today call `set_frame_material(...)` without a ref must keep **unbound** behavior (ref cleared / absent).

### 2.3 BOM — `_bom_sku_resolved`

In `project_closure.py`, add:

```text
if family == "frame":
    return default_library.has_frame(sku)
```

So a bound, live SKU renders like other families (`sku_resolved=True` → identity suffix). Missing/removed SKU → False (frankenstein-safe).

Do **not** change claim-copy class suffixes / Continuity situation strings in this IC.

### 2.4 Diverge — `invalidate_diverged_catalog_refs`

Extend with a **frame** branch (motor/battery already exist; propeller/ESC still absent — do **not** expand those here).

When `components["frame"].catalog_ref.family == "frame"`:

1. Resolve live `FrameSpec` via `has_frame`/`get_frame`. If SKU gone → clear `catalog_ref` (and do not invent).
2. Else compare with epsilon (~`1e-6` like motor/battery):
   - component `mass_kg` vs `FrameSpec.mass_g / 1000`
   - component `size_class_inch` vs `FrameSpec.size_class_inch`
3. Optionally also: if `structure_mass_override_kg` is present and diverges from component `mass_kg`, treat as diverge (same frankenstein class as params-vs-property for motor).
4. On diverge: clear `catalog_ref`; set an honest non-SKU `name` (mirror motor’s `_DIVERGED_MOTOR_NAME` pattern with a frame-specific constant, e.g. `"frame (parámetros divergentes)"`). Do **not** delete mass/class properties — only identity.

Existing call sites of `invalidate_diverged_catalog_refs` automatically cover frame once the branch exists — no orchestrator UX work.

### 2.5 Explicitly unchanged

- `_derive_subsystem_verdict` / `catalog_bound` → PASS  
- Continuity “Diseño validado” / claim-copy class tails (already closed)  
- Assist / acquisition brief frame CTA  
- Seed JSON contents (read-only)  
- Calc mass rules (no “mass only if bound” for frame — unlike motor 2A)  

---

## 3. Forbidden

- IC-3 assist / picker / numbered list UX  
- Making Structure PASS require `catalog_bound`  
- Tip clearance / wheelbase / FEA / CAD  
- Silent fuzzy match free-text → SKU  
- Fabricating SKUs  
- Parallel frame writer outside the chosen apply path  

---

## 4. Tests (mandatory)

Prefer extending existing catalog/bind/BOM tests (or thin focused module):

1. `bind_frame_from_catalog(seed_sku)` → `catalog_ref.family=="frame"`, `mass_kg == mass_g/1000`, `size_class_inch` matches seed; material present iff seed has it.  
2. Unknown SKU → KeyError / no fabricate.  
3. Apply bind into a `ProjectState` → `components["frame"].catalog_ref` set + `structure_mass_override_kg` equals projected mass.  
4. Free-text `set_frame_material` after bind (or write without ref) → `catalog_ref is None`.  
5. `_bom_sku_resolved` / BOM identity: bound live SKU → `sku_resolved True`; bound missing SKU → False.  
6. `invalidate_diverged_catalog_refs`: mutate mass away from SKU → ref cleared; mutate `size_class_inch` away → ref cleared; matching values → ref kept.  
7. Regression: Structure A LEVEL A still runs on projected class (compatible vs incompatible smoke with existing helpers — no new gap types).

Full suite green.

---

## 5. Files allowed

| Path | Change |
|---|---|
| `src/jarvis/core/catalog_bind.py` | `bind_frame_from_catalog` + frame diverge branch (+ diverge name constant) |
| `src/jarvis/core/component_writers.py` | Persist/clear `catalog_ref` on frame write; mass mirror unchanged |
| `src/jarvis/core/project_closure.py` | `_bom_sku_resolved` `"frame"` → `has_frame` |
| `tests/…` | Mandatory tests above (catalog foundation / bind / BOM / diverge) |

**Optional one-line doc** in `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` status table: IC-2 bind landed / assist still deferred — only if a single factual row; no doctrine rewrite.

**Not allowed:** `orchestrator.py` assist flows, `acquisition_brief.py` CTA expansion, Continuity claim rewrites, `engineering_readiness.py` verdict changes, `library/frames/_datos.json` expansion.

---

## 6. Done when

1. §2.1–§2.4 complete.  
2. Mandatory tests + full suite green (**2177** + new).  
3. Implementation report states: physics unchanged vs free-text; identity/BOM/diverge only; no assist; no PASS-by-catalog.  
4. Cursor review PASS / PASS WITH NOTES.

---

## 7. Out (later)

| Item | Status |
|---|---|
| **IC-3** assist | Not authorized |
| Propeller/ESC diverge parity | Out of this IC |
| Layout / CAD / FEA | Out |

---

## 8. Engineer gate

**Do not implement until Engineer `procede` on this IC.**  
If no → edit this IC in place (no dual ratification doc).
