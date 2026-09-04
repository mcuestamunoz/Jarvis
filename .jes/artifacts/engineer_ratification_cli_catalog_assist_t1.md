# Engineer Ratification — CLI catalog-assist T1 (misfit re-offer)

**Date:** 2026-09-01  
**Authority:** Engineer (“ratifico” after investigation review PASS WITH NOTES)  
**Investigation:** [investigation_report_cli_catalog_assist_misfit_propose.md](investigation_report_cli_catalog_assist_misfit_propose.md)  
**Review:** [investigation_review_cli_catalog_assist_misfit_propose.md](investigation_review_cli_catalog_assist_misfit_propose.md) — **PASS WITH NOTES**  
**IC:** [implementation_contract_cli_catalog_assist_t1.md](implementation_contract_cli_catalog_assist_t1.md)  
**Baseline:** tag **`v0.3.5`** / `fc46938` plus live tree (Block Closure + CLI feasibility already in product)

---

## Ratification status

**LOCKED.** First IC = **T1**. Cursor does **not** implement `src/`. Claude implements from the IC only.

T1+2 (named G22 filter relax) and Tier 3 (joint combo) are **not** this IC.

---

## ★ Decisions (locked)

| ★ | Decision |
|---|---|
| **★1** | **T1 only.** Wire existing `bound_sku_underspec` + existing `build_motor_catalog_suggestions` into IDLE/COMPONENT help-choose. No new ranking function. No silent G22 fallback. No catalog JSON. |
| **★2** | **Continuity in T1.** When underspec is live, `next_useful_step` names G22 candidate(s) or the help-choose CTA **even if sim is fail**. Do not rewrite the whole rank table. Do not claim sim PASS or block CERRADO. |
| **★3** | **Watts CTA split in T1.** “No declara vatios” only when the bound SKU’s library `max_watts` is None (`emax_rs2205s_2300`). `catalog_bound_motor_covers_power_w` stays identity for architecture-progress. `sunnysky_r2305_2500` (~220 W) must not use that sentence. |
| **★4** | **GAP title only.** Keep type `GAP-MOTOR-CATALOG-UNRESOLVED`. Vary title on `gap_evidence_fact` prefix. |
| **★5** | **Frozen:** T1+2, Tier 3, G24-B, H5, Catalog Foundation, Option B, Structure, Conversation Engine, `_derive_overall` / `ASSEMBLY_READY`, Block Closure rollup / N1, P26 / P27-A, inventing W. G21 false-rebind test **unchanged**. |

Review notes absorbed: T1 offer may still fail sim (honest); six thrust-only PASS motors are all frankenstein vs `gf_5045x3` — not this IC.

---

## Next

Claude implements [implementation_contract_cli_catalog_assist_t1.md](implementation_contract_cli_catalog_assist_t1.md). Cursor reviews against that IC.
