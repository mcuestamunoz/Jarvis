# Investigation Review — Structure Catalog Foundation (Frames)

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_structure_catalog_foundation.md](investigation_contract_structure_catalog_foundation.md) — Engineer 🟢 APPROVED FOR EXECUTION  
**Report:** [investigation_report_structure_catalog_foundation.md](investigation_report_structure_catalog_foundation.md) (Claude Code)  
**★ mandate:** [engineer_ratification_structure_catalog_foundation.md](engineer_ratification_structure_catalog_foundation.md)

## Verdict

**PASS WITH NOTES**

Claude’s report meets the approved Investigation Contract and correctly
uses the contract’s escape hatch: **catalog is not automatically the next
implementation Buy.** The decisive calc-parity finding is independently
confirmed. Recommendation stands: **Not yet for IC-2/IC-3**; **IC-1
(schema+seed) optional groundwork or B0** — Engineer ★ product call.

Implementation remains 🔴 until a separate IC + `procede`.

---

## Checklist

| Criterion | Result |
|---|---|
| Q1–Q10 | **Pass** |
| Q11 decision value (not pretty name) | **Pass** — identity/traceability/error-reduction named; **not** sold as new physics capability |
| Q12 authoritative vs catalog-declared | **Pass** — reuses `source_url` / `source_note` / `identity_status`; notes `identity_status` is documentary, not machine-gated |
| Candidate ≠ required; `wheelbase` Not yet | **Pass** |
| Forbidden claims rejected | **Pass** |
| Reachability described, not fixed | **Pass** |
| Phased IC-1/2/3 with real costs | **Pass** — diverge two-field cost called out honestly |
| May conclude No / not yet | **Pass** — executive finding does |
| No implementation | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `set_frame_material` → `structure_mass_override_kg` | **Confirmed** — `component_writers.py` |
| `CalculationEngine.build` consumes override unconditionally | **Confirmed** — `:196-207`; no catalog_ref gate |
| Motor mass only when SKU-bound | **Confirmed** — `set_motor_component` writes `motor_mass_kg` IFF `catalog_ref.family == "motor"`; calc comment 2A |
| Battery SKU mass vs heuristic | **Confirmed** — catalog path in writers + diverge reverts to 150 Wh/kg |
| `invalidate_diverged_catalog_refs` = motor + battery only | **Confirmed** — no propeller/ESC branches |
| No `"frame"` in `CatalogRef.family` | **Confirmed** |
| `_structure_evidence.catalog_bound` computed; verdict ignores it | **Confirmed** |
| No `library/frames/` | **Confirmed** |
| ESC schema + `bind_esc_from_catalog` exists | **Confirmed** — docstring itself: “No CLI/UX entry point calls this yet” |

---

## Notes

### N1 — ESC “exactly one caller” is nearly right

Production orchestrator/CLI: **no callers** — claim holds. There is also
`scripts/cli_probe_minimum_universe_combo.py` (probe, not product path).
Does not weaken the IC-1 precedent.

### N2 — ESC bind is not a perfect calc-parity twin of frame

`bind_esc_from_catalog` projects `current_a` into a property
`electrical_compatibility` already reads — so *if* ESC bind were wired,
it would change compatibility evidence, not only labels. Frame has **no**
analogous asymmetry: mass/class already fully effective via Structure A.
Claude’s **frame-specific** “binding unlocks no new engineering claim
type” finding is therefore **stronger** than a generic “catalog never
changes physics” slogan — and correctly scoped to frame.

### N3 — Q11 framing: possible vs traceable

Report’s distinction (*more possible* vs *more traceable*) is the right
bar from the amended contract. Procurement/`sku_resolved` would be real
identity capability, but Claude correctly classifies it as traceability
of inputs Structure A already accepts — not a new Structure decision.
Engineer may still ★ IC-1 (or even IC-2) as product priority; the report
does not overclaim a physics Buy.

### N4 — Prior Cursor draft superseded

An earlier same-session draft leaned “Yes if IC-1→IC-2.” Claude’s
evidence-led **Not yet for IC-2** replaces that lean. Review accepts
Claude’s finding; do not treat the superseded draft as authority.

---

## Slice / next

| Item | Status |
|---|---|
| Investigation | **CLOSED** (PASS WITH NOTES) |
| IC-2 / IC-3 Buy | **Not recommended** by report |
| IC-1 schema+seed | **Optional** — or B0 |
| Implementation | 🔴 until Engineer ★ + IC + `procede` |
| Layout / CAD | Still out |

**Awaiting Engineer ★:** bank IC-1 now, B0 defer, or (against lean) still Buy IC-2 for identity/BOM product reasons with eyes open on cost.
