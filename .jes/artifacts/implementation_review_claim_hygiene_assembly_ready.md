# Implementation Review — Claim hygiene under ASSEMBLY READY

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**IC:** [implementation_contract_claim_hygiene_assembly_ready.md](implementation_contract_claim_hygiene_assembly_ready.md)  
**Report:** [implementation_report_claim_hygiene_assembly_ready.md](implementation_report_claim_hygiene_assembly_ready.md)  
**Base:** tag `v0.3.6` / `checkpoint-experimental-prop-energy-closed` · commit `f70b278`  
**Suite (reviewer):** **2160** passed (2150 + 10)

## Verdict

**PASS WITH NOTES**

Margin/quality claim-hygiene slice matches the IC. Continuity no longer says
“Diseño validado” on PASS+risky/`low_margin`; CLI NOTE and humanized `Por qué`
are present; `ASSEMBLY_READY` eligibility is untouched. Ready to close the
**claim hygiene** thread (B4 margin slice). Weak-OP Continuity (N4) remains
follow-up — not blocking.

Engineer may open **control parity** investigation next (agenda plan).

---

## IC checklist

| Criterion | Result |
|---|---|
| §2.1 situation gate + locked string | **Pass** — `margin_claim_weak` + `_MARGIN_WEAK_SITUATION` before plain PASS |
| §2.1 codes exclude `autonomy_below_restriction` | **Pass** |
| §2.2 next-step Corrige… + raw why in Continuity | **Pass** — verified by test (`why == "low_margin"`) |
| §2.3 CLI humanize `Por qué` via WARNING_SHORT | **Pass** — no core→adapters import |
| §2.4 NOTE under ASSEMBLY READY only when weak | **Pass** |
| §2.5 PhaseLayer unchanged | **Pass** |
| Forbidden files untouched | **Pass** — no `simulator.py` / `engineering_readiness` gap/`_derive_overall` / catalogs |
| Mandatory tests | **Pass** — Continuity + CLI + ERF smoke |
| Full suite | **Pass** — **2160** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Predicate: quality risky OR warning set | **Confirmed** — `project_continuity.py:198-203` |
| Branch order: autonomy undemonstrated → margin weak → Diseño validado | **Confirmed** — `:304-320` |
| Locked situation string verbatim | **Confirmed** — `:192-194` |
| Orchestrator exposes single boolean | **Confirmed** — `orchestrator.py` `"margin_claim_weak": margin_claim_weak(simulation)` |
| CLI NOTE exact string | **Confirmed** — `main.py:130-131,160-161` |
| Humanize prefer SHORT | **Confirmed** — `_humanize_next_useful_why` |
| Suite | **Confirmed** — reviewer `pytest -q` → **2160 passed** |

---

## Notes

### N1 — `ctx["margin_claim_weak"]` instead of `ctx["simulation"]` snapshot

IC §2.4 preferred a thin simulation dict. Implementation threads a **precomputed
boolean** from the same Continuity authority. Better than duplicating the
predicate in CLI — accepted as within §2.4 intent (“prefer smaller / same
authority”).

### N2 — PhaseLayer (carry-forward)

Still suppressed when Continuity situation is present. Situation now agrees
in substance; structural dual remains debt (as report).

### N3 — Public helper name

IC sketched `_margin_claim_weak`; shipped `margin_claim_weak` (public, used by
orchestrator). Fine.

### N4 — Weak-OP Continuity (carry-forward)

Not in this IC. Remains named follow-up after control parity or as its own
thread — Engineer choice.

---

## Thread status

**Claim hygiene (margin/quality B4 slice): CLOSED (code + review).**  
Do not re-implement. Next agenda step: **control parity** investigation when
Engineer says so — not automatic.
