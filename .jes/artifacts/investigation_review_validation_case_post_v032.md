# Investigation Review — Validation Case Post-v0.3.2

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_validation_case_post_v032.md`](investigation_contract_validation_case_post_v032.md)  
**Report:** [`.jes/artifacts/investigation_report_validation_case_post_v032.md`](investigation_report_validation_case_post_v032.md)  
**Base:** tag `v0.3.2` / `checkpoint-deferred-queue-cd` · commit `ca1659c`

## Verdict

**PASS WITH NOTES**

Contract gates met. Baseline re-verified independently. V1–V11 answered with fresh evidence (not mere citation of the deferred-queue report). The core finding holds: **Validation Case physics is already shipped as lookup + honest display**; no live gap on v0.3.2; remaining work is **probe/docs-shaped**, not resolver/calc-shaped. H5 and G24-B correctly remain frozen.

**Defect-first review:** No open findings that block Engineer ★ or IC contract drafting.

---

## Contract checklist (§4)

| Criterion | Result |
|---|---|
| Baseline v0.3.2 with recorded pass counts | **Pass** — **2028/2028**, 7 probes green |
| V1–V11 with code citations / named tests | **Pass** — §3 complete |
| IC-shaped vs data-curation vs docs-only distinguished | **Pass** — options (a–d) table honest |
| Matrix + recommendation present | **Pass** — §5–§6 |
| ★ table complete | **Pass** — §7 |
| No implement / no version bump | **Pass** |
| Does not treat OP seeds as open work | **Pass** |
| Does not collapse Validation Case into H5/G24-B | **Pass** |
| C+D reopening without proof | **Pass** — empty diff on Validation Case files |

---

## Independent verification

```text
pytest tests/                                    → 2028 passed
cli_probe_g24_viable_selection_honest_cta.py     → 6/6 PASS
cli_probe_frankenstein_name_clear.py             → 5/5 PASS
cli_probe_g24_apply_by_index.py                  → 6/6 PASS
cli_probe_p2_2_operating_point_bridge.py         → 6/6 PASS
cli_probe_requirements_closure.py                → 5/5 PASS
cli_probe_battery_catalog_bind_ux.py             → 6/6 PASS
cli_probe_closure_policy_propeller_sku.py        → 4/4 (+ optional)

git diff v0.3.1 v0.3.2 --stat -- component_writers.py calculation_engine.py
  electrical_compatibility.py adapters/cli/main.py library.py
  → (empty)

resolve_operating_point("emax_rs2205s_2300", "hq_5045_bn", 16.0V)
  → exact_operating_point; 432.0 W / 27.0 A / 23560 RPM / 9.7086 N / 0.98

grep validation case in src/ tests/
  → tests/test_phase2_lookup_operating_point.py docstring only

CatalogRef.family                                    → motor | battery | propeller (unchanged)
library/esc/                                         → absent
```

---

## Review highlights

**V7 — C+D isolation by diff, not inference.** Empty diff on all Validation Case-relevant `src/` files is the strongest possible answer. G24C/D footprint confined to explore/identity paths — report claim verified.

**V3/V4 — lookup vs divergence honest.** Live resolver returns ★6 OP-2 numbers verbatim. The one real divergence (rating `motor_power_w` vs resolved `motor_op_power_w`) is already displayed — not a missing feature. Correctly reframes "Validation Case" from vision-doc breadth to **regression narrative + optional data curation**.

**Recommendation discipline.** Primary cut = **probe/regression gate (b)**, optional doc (a). Correctly defers:
- (c) `estado` summary — real but not gap-closing
- (d) battery/ESC test data — Engineer curation, not IC
- H5, G24-B — no new blockers

**IC outline (§8)** is appropriately bounded: zero `src/`/`library.py`/resolver diff as gate; reuses existing fixtures. Matches contract §3 hard constraints.

---

## Notes (non-blocking)

### Note 1 — IC value is regression lock, not gap closure

Engineer should ratify ★1 understanding this: the proposed IC **does not add new physics capability**. It makes an already-true property permanently checkable. That is valid and low-risk — but not the same as closing §12.2's battery/ESC "partial" items (which need data, §3.6).

### Note 2 — Probe sketch step 3 (`estado` lines)

§9 probe sketch includes `estado` line checks. Acceptable as **read-only regression** over existing render paths (no `src/` change required) — align IC contract wording to say "assert via existing `render_startup_context`" so implementer does not add a third summary line (option c).

### Note 3 — Version bump (★6)

Report correctly notes probe/doc-only work may not warrant its own version bump. Engineer ★6: fold into next substantive checkpoint or accept a docs-only patch — either is fine.

---

## Engineer ★ alignment (recommended ratification)

| ★ | Report recommendation | Review |
|---|---|---|
| **★1** | Validation Case (b) [+ optional (a)] | **Ratify** |
| **★2** | Probe gate; not (c) estado; not (d) data in IC | **Ratify** |
| **★3** | Data curation separate Engineer decision | **Ratify** |
| **★4** | H5 defer | **Ratify** |
| **★5** | G24-B freeze | **Ratify** |
| **★6** | Version timing — Engineer's call | **Note only** |

---

## Next step

```text
Investigation PASS WITH NOTES
  ↓
Engineer ★ (especially ★1–★2: probe + optional doc)
  ↓
Cursor: implementation_contract_validation_case_regression_gate.md
  ↓
Claude implements → review → probe → checkpoint (version per ★6)
```

Do **not** draft IC until Engineer ratifies ★1–★2.

---

**End of review.**
