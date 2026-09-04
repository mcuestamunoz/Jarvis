# Engineer Ratification — Structure A (investigation)

**Date:** 2026-09-03  
**Authority:** Engineer (investigation before IC; then **ratified in essence** the `diameter_in` split after the repo map)  
**Contract:** [investigation_contract_structure_a.md](investigation_contract_structure_a.md)  
**Draft IC (not work order):** [implementation_contract_structure_a.md](implementation_contract_structure_a.md)  
**Notes (hypotheses):** [engineer_notes_structure_a.md](engineer_notes_structure_a.md)

**Baseline:** tag **`v0.3.5`** plus live tree (DSE apply honesto reviewed, suite 2124).

---

## Ratification status

**LOCKED for investigation of seams.** Product model **ratified in essence**, then **semantic lock** (2026-09-03): screening of **class compatibility**, not proof the prop “fits”. Claude still writes/wrote a report. **No `src/` until a later IC.**

---

## ★ Decisions (locked)

| ★ | Decision |
|---|---|
| **★1** | Investigation next = **seams** (PVC 200g writer, 4/4 dual, gap vs incomplete). **Not** a re-study of OP vs \(D^4\). |
| **★2** | Product shape is **B** (masa + class compatibility). Report may recommend **A then class-compat** only if one IC would be unclean. C/D only with evidence. Physics (2026-09-03): **B**. |
| **★3** | `diameter_in` stays propulsion authority. `size_class_inch` is **class-compatibility screening** (LEVEL A), not geometric fit. Unidirectional: class ↛ thrust. No invented \(C_T\). No copy class from prop. Never VERIFIED, never “cabe”. `D <= class` = CLASS COMPATIBILITY PASS. `D > class` = CLASS COMPATIBILITY GAP (`GAP-FRAME-PROP-SIZE`), not proven physical misfit. No +0.25. No mm→class. |
| **★4** | Missing class or class-incompatible → Structure **INCOMPLETE**. Thrust unchanged. No propeller → structure may close on mass+material. |
| **★5** | **ASSEMBLY_READY / `_derive_overall`:** first IC does **not** add HIGH. Report names whether incomplete already yields “not assembly ready” in practice. Frozen: CAD, H5, Option B, DSE scoring, implementing the draft IC. |

---

## Next

Investigation **reviewed** ([investigation_review_structure_a.md](investigation_review_structure_a.md) — PASS WITH NOTES). IC rewritten: [implementation_contract_structure_a.md](implementation_contract_structure_a.md). Engineer `ratifico` → Claude implements. No extra ★ (B + Gate closed).
