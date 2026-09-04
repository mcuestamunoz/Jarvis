# Engineer Ratification — Block Closure B-PROP-ENERGY

**Date:** 2026-09-01  
**Authority:** Engineer (“ratifico” after CLI feasibility IC closed)  
**Investigation:** [investigation_report_post_v034_block_closure.md](investigation_report_post_v034_block_closure.md)  
**Review:** [investigation_review_post_v034_block_closure.md](investigation_review_post_v034_block_closure.md) — **PASS WITH NOTES**  
**IC:** [implementation_contract_block_closure_prop_energy.md](implementation_contract_block_closure_prop_energy.md)  
**Baseline:** tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`** (`fc46938`) plus live tree (P27-B / Option A / CLI feasibility semantics already in product). Investigation itself was run on `v0.3.4` / `a563fe7`; do not revert later slices.

---

## Ratification status

**LOCKED.** Hypothesis (A): block closure is **derivable**. No `BLOCK_STATUS` subsystem. No Catalog Foundation first. No H5.

Cursor does **not** implement `src/`. Claude implements from the IC only. Cursor reviews against that IC.

P26 / P27-A remain frozen. HD-001/002/003 unchanged. CLI feasibility copy stays. `ASSEMBLY_READY` / `_derive_overall` / the eight `validated = sim_status == "pass"` assignments stay.

---

## ★ Decisions (locked)

| ★ | Decision |
|---|---|
| **★1** | **Derivable.** Closure is a named rollup over existing subsystem verdicts + the four `electrical_compatibility` facts + catalog_ref identity. Not a new physics engine, not a new `BLOCK_STATUS` authority, not a rewrite of ERF §11. |
| **★2** | **PARTIAL closable today.** Gate A combo (`sunnysky_r2205_2500` + `gf_5045x3` + `lipo_4s_1500mah` + freeform ESC, `motor_count=2`) may be declared block-closed with honest COMPATIBLE + SIM_PASS. Incompatible `motor_count=4` must refuse. Closability is catalog-fragile — document the combo; do not pretend every SKU reaches `manufacturer_test`. |
| **★3** | **None of Gate D is BLOCKING** for B-PROP-ENERGY. H5 / battery real-test data / OP density / G24-C / FN-R / C-108 / G1 / C-081 stay deferred. ESC catalog remains B-BOM traceability only. |
| **★4** | **This IC is next** (one bounded arc). Catalog Foundation investigation is **not** first. FN-R / H5 / C-108 are not this slice. Battery SKU re-bind corruption (Gate E Path 3) is **in** this IC as prerequisite, not a later polish. |
| **★5** | **Do not start Catalog Foundation.** If it is ever opened later: +1 ESC schema class and 3–5 SKUs only — not motor/prop/battery expansion. Not this IC. |
| **★6** | **Tiered closure.** Accept fallback-honest as a **lower-confidence closed** mode. Never claim `manufacturer_test` closure from a fallback/legacy OP. Copy must name the tier. |

### Scope lock (review Note 4)

Gate E Path 4 (`define_missing_params` thrust mutation without `invalidate_diverged_catalog_refs`) is **deferred**. Document it as a known gap in the IC non-goals. Same IC would be a mega-slice.

`GAP-MOTOR-CATALOG-UNRESOLVED` vocabulary trap (bound SKU underspec) is **out of scope**.

---

## What “closed” means for this block (product)

A user can stop working on **motor + propeller + battery + ESC electrical stack** when:

- propulsion / energy / electronics subsystem verdicts are PASS,
- the four electrical checks do not refuse (freeform ESC current is allowed),
- motor / propeller / battery are catalog-bound,
- latest sim is PASS,

**and** the CLI says so **without** equating that to `PROJECT STATUS: ASSEMBLY READY`.

Frame / FC / structure gaps may still keep the project `NOT_ASSEMBLY_READY`. That dual is **required** (Finding B-3).

Electronics `evidence.validated` (global sim PASS) is **not** ESC proof. The rollup must read `electrical_compatibility`, not borrow that boolean.

---

## Next

Claude implements [implementation_contract_block_closure_prop_energy.md](implementation_contract_block_closure_prop_energy.md). Cursor reviews against that IC. Then an Engineer **CLI walk Combo A / PRODUCT_SCOPE** — interconnection gate, not optional. Tests do not replace it.
