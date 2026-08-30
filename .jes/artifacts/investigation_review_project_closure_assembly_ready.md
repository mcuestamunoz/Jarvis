# Investigation Review — Project Closure / Assembly Ready

**Date:** 2026-08-30  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_project_closure_assembly_ready.md`](investigation_contract_project_closure_assembly_ready.md)  
**Report:** [`.jes/artifacts/investigation_report_project_closure_assembly_ready.md`](investigation_report_project_closure_assembly_ready.md)  
**Base:** tag `v0.3.0` / `checkpoint-propeller-catalog-bind`

## Verdict

**PASS WITH NOTES**

Report satisfies all 15 contract sections. Headline findings **reproduced independently** by Cursor (live `build_engineering_readiness` on both workspace fixtures). Recommended Option D sequence is well-grounded and should supersede the prior G27→G26→battery ranking in `IMPLEMENTATION_TASKS.md`.

**Defect-first review:** No FAIL findings. Two notes for Engineer before IC drafting.

---

## Contract checklist

| Gate | Result |
|---|---|
| §1.1 Blocker inventory + 2 fixtures | **Pass** — live runs, not static only |
| §1.2 G26 scope box | **Pass** — separates bug vs “never stated constraint” |
| §1.3 G27 role | **Pass** — parallel to battery UX, landmine argument sound |
| §1.4 Battery → calc/energy chain | **Pass** — traces bind API already complete |
| §1.5 “Real component” definitions | **Pass** |
| §1.6–1.7 Family matrix + minimums | **Pass** |
| §1.8 Catalog vs expansion | **Pass** — zero new SKUs required for arc |
| §1.9 Snapshots A/B | **Pass** — honest, no invented PASS |
| §1.10 S0→S1→S2 | **Pass** — independence of transitions proven |
| §1.11 Sequence options | **Pass** — Option D recommended with rationale |
| §1.12 CLI probes | **Pass** |
| ★ decisions (9) | **Pass** — ★3 correctly left to Engineer |
| IC outline | **Pass with note** — see Note 1 |
| No `src/` changes in investigation | **Pass** |
| ★1 no invent components | **Pass** |

---

## Independent verification (Cursor)

Re-ran `build_engineering_readiness` on workspace fixtures:

**`1-324107ef7006`**

```text
overall: NOT_ASSEMBLY_READY
gaps: 0
requirements: INCOMPLETE  ← sole non-PASS
architecture / structure / propulsion / energy / electronics / control / catalog / bom: PASS
parsed_constraints: {}
```

**`crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789`**

```text
overall: NOT_ASSEMBLY_READY
gaps: 6 (all MEDIUM — BOM/arch stubs)
propulsion + catalog: PASS
requirements: INCOMPLETE (parsed_constraints: {})
```

Confirms report §2.2–2.3. **Headline discovery accepted:** for Fixture-2-shaped projects, Requirements closure is the highest-leverage first cut — not battery UX, not BOM work, not catalog expansion.

**Propeller `(SKU sin resolver)` bug** — confirmed in code:

```224:228:src/jarvis/core/project_closure.py
    if family == "motor":
        return default_library.has_motor(sku)
    if family == "battery":
        return default_library.has_battery(sku)
    return False  # no v1 resolve path for other families (★2)
```

`has_propeller` exists in `library.py` but is omitted — valid live finding, display-only (no verdict impact), one-line fix for Cut 3/4.

---

## Assessment of recommended sequence (Option D)

| Cut | Report recommendation | Cursor view |
|---|---|---|
| **1 — Requirements Closure (G26 + ★3)** | Smallest, unblocks Fixture 2 → ASSEMBLY READY | **Ratify ★1** — do this first |
| **2 — Battery Catalog UX + G27** | Same checkpoint window; bind bypasses G27 | **Ratify ★4/★5** — merge into one IC (see Note 1) |
| **3 — Closure policy + BOM honesty** | Propeller `sku_resolved`, family policy docs | **Ratify ★6/★7/★8** — can follow Cut 2 |

**G24 deferred** — accepted. Report correctly scopes it as identity/display debt, not rollup blocker.

**Rejected linear G27→G26→battery** — accepted. Investigation proves path independence.

---

## Notes (non-blocking)

### Note 1 — IC count: §11 says “4 cuts”, §14 lists 3 ICs

Report §11 enumerates G27 as Cut 3 separate from battery UX Cut 2; §14 merges them into **IC 2**. **Recommend Engineer ratify 3 ICs:**

1. Requirements Closure  
2. Battery Catalog UX + G27 Hardening (same checkpoint)  
3. Closure Policy + BOM Honesty  

Not 4 separate checkpoints unless Engineer wants G27 isolated for review granularity.

### Note 2 — ★3 is the gate before IC 1

Both fixtures have `parsed_constraints={}` with `restrictions="no"` — **not** the G26 routing bug alone. Even with G26 fixed, ASSEMBLY READY still requires Engineer choice:

- **(a)** Explicit numeric constraint always required (current de-facto), or  
- **(b)** Explicit “no constraint” counts as satisfied  

IC 1 scope depends on this. **Do not draft IC 1 until ★3 is ratified.**

### Note 3 — Fixture 2 is the demo gate for Cut 1

Use `1-324107ef7006` (or equivalent) as the CLI probe fixture for Cut 1 — cleaner than the post-v0.3.0 dron project which still needs S0→S1 component work.

---

## ★ ratification guidance for Engineer

| ★ | Cursor recommendation |
|---|---|
| ★1 Sequence Option D, Requirements first | **Ratify** |
| ★2 G26: fix write path + `is_derived` defense-in-depth | **Ratify** |
| ★3 No-constraint semantics | **Engineer must decide (a) or (b)** before IC 1 |
| ★4 Battery UX mirrors propeller pattern | **Ratify** |
| ★5 G27 narrow to battery chemistry path | **Ratify** |
| ★6 Propeller `sku_resolved` one-liner | **Ratify** |
| ★7 Family policy matrix | **Ratify** |
| ★8 No expand ACCEPTED_WARNING_TYPES | **Ratify** |
| ★9 G24 deferred | **Ratify** |

---

## Next step

```text
Engineer ★ (especially ★3)
  ↓
Cursor: implementation_contract_requirements_closure.md  (IC 1)
  ↓
Claude implements → review → CLI probe #3 on Fixture 2
  ↓
Then IC 2 (battery + G27) → IC 3 (policy + sku_resolved)
```

Do **not** open battery UX or G27 ICs before ★3 + IC 1 contract.

---

**End of review.**
