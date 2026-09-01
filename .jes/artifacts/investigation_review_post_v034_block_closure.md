# Investigation Review — Post-v0.3.4 Block Closure Capability

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_post_v034_block_closure.md`](investigation_contract_post_v034_block_closure.md)  
**Report:** [`.jes/artifacts/investigation_report_post_v034_block_closure.md`](investigation_report_post_v034_block_closure.md)  
**Base:** tag `v0.3.4` / `checkpoint-motor-op-voltage-coherence` · commit `a563fe7`

## Verdict

**PASS WITH NOTES**

All contract gates A–F answered. Mandatory §4 table fully populated with evidence (no `?`). Hypothesis (A) supported with code citations — not assumed. Primary recommendation is bounded and does not pre-decide a new `BLOCK_STATUS` subsystem. Zero `src/` drift from v0.3.4 tag confirmed.

**Ready for Engineer ★** on questions ★1–★6. IC draft may follow ratification; do not implement before ★.

---

## Contract checklist (§7–§8)

| Criterion | Result |
|---|---|
| Baseline verify (suite + probes @ v0.3.4) | **Pass** — §0; `src/` empty vs `a563fe7` |
| Gates A–F answered | **Pass** |
| §4 mandatory table — no inference cells | **Pass** — all six blocks populated |
| ASSEMBLY_READY vs block-closed distinction | **Pass** — Finding B-3 explicit |
| Gate F — Catalog Foundation sequencing | **Pass** — Block Closure first, evidenced |
| One primary recommendation + deferrals | **Pass** — §Primary recommendation |
| No production fix / no version bump | **Pass** |
| Does not reopen closed arcs without proof | **Pass** |

---

## Independent verification (spot-check)

| Claim | Cursor check |
|---|---|
| 8 subsystems share `validated = ctx.sim_status == "pass"` | **Confirmed** — `engineering_readiness.py:904,922,934,946,955,965,973,984` (architecture uses `is_complete AND sim_status`, not a separate physics check per subsystem) |
| `CLOSED` absent from code | **Confirmed** — only docstring references in `catalog_bind.py`, `explore_continuity.py` |
| `parse_floats_from_input` G27-class misparse path | **Confirmed** — `param_definition_session.py:1040-1048` regex `\d+(?:\.\d+)?` extracts first digit from `"6S..."` |
| Gate D: no BLOCKING for B-PROP-ENERGY | **Accepted** — reasoning matches code structure; ESC gap scoped to B-BOM traceability |
| Real end-to-end ASSEMBLY_READY trace | **Not re-run live** — report cites orchestrator path; prior probes use hand-built sim (report discloses this honestly) |

---

## Notes (non-blocking)

### Note 1 — Scratchpad traces not in repo

Reference-case and UX traces ran via fork scratchpad only (per investigator). Acceptable per contract §7 (optional probe/test). **Recommend:** Block Closure IC include committed `tests/test_block_closure_prop_energy.py` + `scripts/cli_probe_block_closure_capability.py` reproducing Gate A compatible/incompatible cases — so the first real end-to-end ASSEMBLY_READY trace is regression-locked.

### Note 2 — Gate E UX matrix uses "assumed" for some backend cells

§4 table is strict; Gate E summary matrix marks B-REQ/B-ARCH/B-BOM backend as "assumed per contract." Minor inconsistency — does not undermine §4.

### Note 3 — `GAP-MOTOR-CATALOG-UNRESOLVED` vocabulary trap

Report Finding (Gate A, motor_count=1 case) is valuable product debt — gap ID mislabels bound-SKU underspec. **Out of scope** for Block Closure IC unless Engineer expands; worth a one-line note in IC non-goals or a separate hygiene item.

### Note 4 — `define_missing_params` divergence route (adjacent to battery bug)

Gate E Path 4: ordinary thrust mutation without `invalidate_diverged_catalog_refs`. Report correctly scopes as **adjacent** to Block Closure IC item 4 — not the same bug as battery re-bind corruption (Path 3). Engineer ★ should decide: same IC or deferred.

### Note 5 — Catalog composition fragility (★6)

Only `sunnysky_r2205_2500` + 14.8V battery aligns to `manufacturer_test` today — well evidenced. Block Closure IC should define closure claims at **tier-aware** levels (manufacturer_test vs fallback-honest), not a single global "closed" boolean.

---

## Engineer ★ — Cursor lean (for ratification, not decided)

| ★ | Lean | Rationale |
|---|---|---|
| **★1** | **Ratify derivable** | COMPATIBLE checks + subsystem verdicts exist; gap is rollup/UX + VALIDATED conflation |
| **★2** | **Ratify PARTIAL closable** | Yes for demonstrated combo + honest refusal; fragile tier/generalization — document in IC |
| **★3** | **Ratify none BLOCKING** | Gate D table consistent with code |
| **★4** | **Ratify Block Closure IC next** | Not H5 / FN-R / Catalog Foundation first |
| **★5** | **Defer Foundation**; if ever needed: ESC schema + 3–5 SKUs only | Gate F |
| **★6** | **Ratify tiered closure** | Accept fallback-honest as lower-confidence mode; do not claim manufacturer_test closure from fallback path |

---

## Recommended IC scope (post-★)

Single bounded arc — **Block Closure B-PROP-ENERGY** (working title):

1. Block-scoped closure derivation (rollup over propulsion + energy + electronics + `electrical_compatibility` facts) — **display/contract layer**, no new physics module  
2. **Prerequisite:** battery SKU re-bind via `define_missing_params` path (Gate E Path 3) — regression test required  
3. VALIDATED field disambiguation or block-closure copy that does not borrow global sim PASS as ESC proof  
4. Optional in same IC or follow-up: `define_missing_params` → `invalidate_diverged_catalog_refs` for param mutations (Path 4)

**Explicit deferrals:** H5 · G24-B · FN-R (except corruption fix above) · Catalog Foundation bulk · C-108 · C-081

---

## Next workflow step

```text
Engineer ★ (★1–★6)
      ↓
implementation_contract_block_closure_prop_energy.md  (draft)
      ↓
implement → review → probe → checkpoint
```

No version bump until IC completes.
