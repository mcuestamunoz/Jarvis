# Implementation Review — Catalog v1 Connection Audit

**Date:** 2026-08-12  
**Reviewer:** Cursor (JES)  
**Contract:** `.jes/artifacts/implementation_contract_catalog_v1_audit.md`  
**Report:** `.jes/artifacts/catalog_v1_connection_audit.md`  

## Verdict

**PASS WITH NOTES**

The audit is high quality, evidence-backed, and correctly reframes Catalog v1 around a real architectural gap: **SKU identity does not survive into persisted state**. Spot-checks confirm the headline claims against code. One contract section (§G) is missing as a dedicated table — content is partially recoverable from §§1.5/E; Claude should add §G or Cursor will lock scope in the Design doc.

**Zero product code** — accepted. Ready to proceed to **Design CLOSED** (`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`), not yet to Impl A coding.

---

## Checklist

| Gate | Result |
|---|---|
| Vision stress-test A | **Pass** — ALIGNED/GAP/CONFLICT/OVERSCOPE used well |
| Connection table + mermaid | **Pass** — as-is / proposed-after-B clear |
| Dual-truth hazards C | **Pass** — authority rules actionable |
| System Map impact D | **Pass** — 5–8 new edges estimate; H5 coupling named without scope creep |
| Design outline E + 5 Engineer Qs | **Pass** |
| Misses F | **Pass** — material KeyError is a real independent bug |
| §G Impl A IN/OUT table | **Note** — **missing as labeled section**; recommendations exist in §1.5/E |
| No `src/` edits | **Pass** |

### Spot-checks (reviewer)

1. **SKU discard on iterate pick** — confirmed: `iterate_interactive_session.py` ~1410 copies only `thrust_n` / `weight_g`; message uses `s['name']` narratively only.  
2. **DEFINE_MISSING path richer but still not identity** — `_make_motor_spec_from_catalog` sets `ComponentSpec.name` to the suggestion name and copies power/thrust/kv/weight, but there is still no `catalog_ref` / `source="catalog"`; `name` is not a durable SKU contract (can collide with display names). Finding stands.  
3. **Motor mass inert** — calc mass path is structure + battery heuristic; `weight_g` unused — confirmed by report’s calc reading.  
4. **Material ES/EN mismatch** — `MATERIAL_MAP` → `carbon_fiber` vs library `fibra de carbono` — confirmed pattern; treat as live bug independent of Catalog.

---

## Headline findings — Cursor position

| Finding | Cursor decision for Design |
|---|---|
| Identity lost after catalog pick | **Accept.** Central gap. |
| “Put binding in Foundation” | **Partial accept.** Impl A ships the **schema field** (`catalog_ref` or equivalent) as additive/optional, unused by writers. **Full Bind write path (pick → fill field → writers)** stays **Impl B**. Do not collapse A+B into one coding cut. |
| B before C hard dependency | **Accept.** Catalog DSE forbidden until Bind writes identity. |
| Motor/battery mass “from zero” | **Accept.** Battery catalog = new family; motor mass = new physics consumer, not enrichment. |
| Mass-in-calc blast radius | **Accept recommendation:** opt-in **only when SKU-bound**; never rewrite free-text-declared motors’ physics in the first Bind cut. |
| Material KeyError | **Accept as independent bug.** Prefer a **tiny separate fix FN** (alias map) — do not block Catalog Design; do not silently “keep materials as healthy.” |
| Continuity catalog_gap as H5 precedent | **Accept for H5 design later.** Do not implement H5 now. |

---

## Notes (non-blocking)

1. **Missing §G:** Ask Claude for a short addendum table, or Cursor will synthesize IN/OUT when writing Design. Prefer the former for contract hygiene.  
2. **Motor count in report (18 vs ~20):** Cosmetics; includes/excludes generics — not material.  
3. **PROPOSED-CAT-\*** correctly unallocated — good.  
4. **Two call sites** (assist vs orchestrator Continuity) — Design must pick: generalize assist module vs siblings (Engineer Q5).

---

## Engineer decisions needed (from §E — Cursor recommendations)

Answer these to unlock Design CLOSED. Cursor’s **default if Engineer agrees in silence later** is marked ★:

1. **Identity field shape** ★ → `catalog_ref: {family: str, sku: str} | None` (not bare string — BOM/DSE/Create→BOM will need family). Optional `bound_at` later, not required for v1.  
2. **Motor mass in calc** ★ → SKU-bound only (audit recommendation). No heuristic mass for free-text motors in Bind v1.  
3. **Material mismatch** ★ → Separate micro-fix (alias → Spanish library keys), not folded into Catalog Foundation.  
4. **Battery chemistry** ★ → Schema allows chemistry string; seed LiPo-first; `mass_g`/`energy_wh` required on SKU so Wh/kg is derived, not a second global constant.  
5. **Assist module shape** ★ → Sibling modules OK for v1 speed (`battery_catalog_assist`, `propeller_catalog_assist`) **or** thin shared helpers under `knowledge/` + keep `motor_catalog_assist` — avoid a giant parameterized rewrite in Impl A. Prefer **extend `ComponentLibrary` + keep motor assist; add thin battery/prop loaders first**; generalize assist only if Continuity gaps for other families ship in the same cut (recommend: Continuity gaps for battery/prop **out of Impl A**).

---

## Recommended Impl A / B split (locked for Design)

```text
Impl A — Foundation
  • library/baterias, helices (+ enrich motores schema, optional operating_points unused)
  • ComponentLibrary loaders + get/find/match (deterministic)
  • ComponentSpec.catalog_ref field (optional, unused by writers)
  • Honest not-found / gap at library API level
  • No calc change, no DSE change, no Continuity redesign, no Bind write path

Impl B — Bind
  • Pick/confirm writes catalog_ref + full projected properties
  • Fix iterate discard bug; align DEFINE_MISSING path to same identity contract
  • Writers: motor_mass_kg mirror when SKU-bound; battery mass overrides 150 Wh/kg when SKU-bound
  • BOM/Continuity can distinguish catalog-bound vs declared-only
  • Invalidation rule when DSE continuous apply diverges from SKU (§C)

Impl C — Catalog DSE   (strictly after B)
Impl D — Create→BOM / SKU BOM
```

---

## Queue

```text
Audit PASS WITH NOTES
        ↓
Engineer answers Q1–Q5 (or accepts ★ defaults)
        ↓
Cursor: docs/PHYSICAL_COMPONENT_CATALOG_V1.md (Design CLOSED)
        ↓
Cursor: Implementation Contract — Catalog Foundation (Impl A)
        ↓
Claude implements Foundation only
```

**Do not** send the previously drafted full Foundation IC until Design CLOSED incorporates this review.
