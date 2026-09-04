# Engineer Ratification — CLI feasibility vs readiness semantics

**Date:** 2026-09-01  
**Authority:** Engineer (“haz el implementation” after investigation review PASS WITH NOTES)  
**Investigation:** [investigation_report_cli_feasibility_semantics.md](investigation_report_cli_feasibility_semantics.md)  
**Review:** [investigation_review_cli_feasibility_semantics.md](investigation_review_cli_feasibility_semantics.md)  
**IC:** [implementation_contract_cli_feasibility_semantics.md](implementation_contract_cli_feasibility_semantics.md)  
**Baseline:** tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`** (`fc46938`) · live tree (P27-B / Option A ESTIMATIVO already in product)

---

## Ratification status

**LOCKED.** Option A (presentation + ranking) may ship.

C1 stands: **do not** change ERF §11 / `_energy_evidence` / `ASSEMBLY_READY`.  
P26 / P27-A remain frozen. HD-001/002/003 unchanged. Cursor does **not** implement; Claude implements from the IC only.

---

## ★ Decisions (locked)

| ★ | Decision |
|---|---|
| **★1** | Presentation + ranking only. `ASSEMBLY_READY` formula untouched. Continuity may say “candidato inicial” while ERF still prints ASSEMBLY READY. |
| **★2** | Never ask the user to invent `motor_power_w` when motors are catalog-bound (`catalog_bound_motor_covers_power_w`). Do not write W into catalog. Do not reopen P27-A / P26. |
| **★3** | No persisted fidelity ladder. Map claims onto existing sim/calc/continuity/reasoning fields. |
| **★4** | Fallback CLI suffix is copy-only. Resolver HOLD / `fallback_only` / voltage epsilon untouched. Keep motor-only “sin hélice de catálogo”; do not use that phrase when BOM propeller `catalog_ref` is set. |
| **★5** | Named negatives for missing autonomy must **not** use Phase 2.5 “fuera del rango del dataset” (that is hover-unverifiable, not this fixture’s honest absence). Do not invent minutes. Do not relabel L1. |

Review notes absorbed: honesty-note gating; orchestrator `:4115` gate; `test_estado_renders_honest_evidence_label` second case.

---

## Next

Claude implements [implementation_contract_cli_feasibility_semantics.md](implementation_contract_cli_feasibility_semantics.md). Cursor reviews against that IC.
