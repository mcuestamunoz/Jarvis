# Engineer smoke — Fit attestation B1

**Date:** 2026-09-10  
**Project:** `autonomía-de-5min`  
**Verdict:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_fit_attestation_b1.md) §6 · [review](implementation_review_geometry_fit_attestation_b1.md) PASS WITH NOTES @ suite **2679**

| Step | Expected | Result |
|---|---|---|
| 1. `sobres` solapan; no `verificación` | screening only | **PASS** |
| 2. `declaro verificado` / Board **Declarar verificado** | human `verificación` copy; `sobres` still “no verificado” | **PASS** |
| 3. Situar-drag selected (card → pane drag) | seal cleared (“sello borrado”) | **PASS** |
| 4. Attest `no_overlap` subject | honest refuse | **PASS** |
| 5. `estado` / readiness | unchanged | **PASS** |

## Field notes closed in same walk

- Nested hit: card-select + pane drag moves that solid; Alt+drag = orbit — [note](engineer_note_situar_nested_hit_select_card.md) **ACCEPT**.

## Out of this Buy

Automatic “encajada” · rename screening · ASSEMBLY_READY from AABB · margin/compose/faces.
