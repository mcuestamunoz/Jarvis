# Implementation Review — Structure Catalog Foundation IC-3

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**IC:** [implementation_contract_structure_catalog_foundation_ic3.md](implementation_contract_structure_catalog_foundation_ic3.md)  
**Report:** [implementation_report_structure_catalog_foundation_ic3.md](implementation_report_structure_catalog_foundation_ic3.md)  
**★:** [engineer_ratification_structure_catalog_foundation_ic3.md](engineer_ratification_structure_catalog_foundation_ic3.md)  
**Baseline:** IC-1+IC-2 · suite **2188** · reviewer suite **2197**

## Verdict

**PASS WITH NOTES**

IC-3 delivers the product Buy: curated frame list → pick → IC-2 bind in
CLI. Free-text intact. LEVEL A / claim-copy still honest on bound frames.
**Catalog Foundation IC-1→IC-3 CLOSED** as a block (assist included by
Engineer product ★).

---

## IC checklist

| Criterion | Result |
|---|---|
| §2.1 `frame_catalog_assist` battery-shaped, no ranking | **Pass** |
| §2.1 Reuse help-choose / match helpers | **Pass** |
| §2.2 `frame_suggestions` + cross-clear peers | **Pass** |
| §2.3 Offer/apply via bind + `set_frame_material` | **Pass** |
| §2.4 Acquisition brief CTA for frame | **Pass** |
| §2.5 Continuity untouched | **Pass** |
| Forbidden: verdict / seed expand / fuzzy match | **Pass** |
| Mandatory tests §4 | **Pass** — new module + retargeted fail-routing test |
| Full suite | **Pass** — **2197** |
| §6.5 CLI walk | **Pass** — reported by implementer; composes with claim-copy |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `build_frame_catalog_suggestions` / format | **Confirmed** |
| Offer/apply + peer clear | **Confirmed** in orchestrator |
| Brief advertises frame help-choose | **Confirmed** |
| Fail-routing test retargeted, not weakened | **Confirmed** — `"continuar"` keeps persisted-state subject; new test for catalog open |
| `state_manager.py` not in final diff | **Confirmed** — clean / allowlist |
| Suite | **Confirmed** — `pytest -q` → **2197** |

---

## Notes

### N1 — SKU id not always printed on list lines

Formatter shows manufacturer/model + class + mass (+ material). When
identity exists, the **SKU key** is not appended on the line (only used as
fallback if manufacturer/model missing). Mental mapping still works; pick
by number is the path. Optional polish later: append ``(sku)`` — not blocking.

### N2 — `limit=10` on builder

Same battery-shaped cap. IC-1 seed has 4 rows — fine. If seed grows past
10, list truncates silently. Acceptable for now; revisit if seed expands.

### N3 — CLI walk

Implementer walked the recommended path (list → pick → estado `[sku]` +
class-incompatible suffix + NOT ASSEMBLY READY). Cursor did not re-walk
interactively; unit tests + suite + report claim accepted.

---

## Slice / phase

| Item | Status |
|---|---|
| Catalog Foundation **IC-3** | **CLOSED** |
| Catalog Foundation **block** (IC-1→IC-3) | **CLOSED** |
| Ranking / Continuity redesign / CAD | Still out |
