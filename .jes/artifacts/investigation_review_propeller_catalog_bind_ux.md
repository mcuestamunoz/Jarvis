# Investigation Review — Propeller Catalog Bind UX

**Date:** 2026-08-21  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_propeller_catalog_bind_ux.md`](investigation_contract_propeller_catalog_bind_ux.md)  
**Report:** [`.jes/artifacts/investigation_report_propeller_catalog_bind_ux.md`](investigation_report_propeller_catalog_bind_ux.md)  
**Base:** tag `checkpoint-phase2-p2-1` · commit `e82b8a1`

## Verdict

**PASS WITH NOTES**

Investigation complete: all required sections present, zero `src/` / test changes. G21 reuse path is correctly identified. Latent motors help-choose starvation bug is real and correctly elevated into this slice. OP re-resolve via explicit `set_motor_component` re-call is the right minimal fix. Voltage-not-required finding for ★6 exact OP is verified and correctly corrects the contract framing.

**Defect-first check:** No findings that invalidate the report.

## Checklist

| Gate | Result |
|---|---|
| §1.1 As-is propeller acquisition | **Pass** |
| §1.2 Suggestion authority (≥2 options) | **Pass** — A recommended; C rejected with proof |
| §1.3 Session / help-choose wiring | **Pass** — starvation bug correctly diagnosed |
| §1.4 OP re-resolve after bind | **Pass** — Option 1 (`set_motor_component` re-call) |
| §1.5 Voltage / walk sequencing | **Pass** — evidence-corrected (no battery needed for ★6) |
| §1.6 Design options A/B/C | **Pass** — A+B recommended; C rejected |
| §1.7–1.8 Tests + slices | **Pass** — Prop-1…Prop-7 |
| ★ numbered | **Pass** — ★1–★7 |
| No production fix / no OP physics change | **Pass** |

## Code review highlights

**Motors help-choose is membership-only.** Confirmed `orchestrator.py:2528` — `if "motors" in expected_keys:` with no incompleteness gate. Adding a propeller block after it without gating would be unreachable in the composite propulsion wizard. ★4 must ship in this slice.

**`match_motor_propeller` already surfaces P2-1 props.** Live check: `emax_rs2205s_2300` matches `hq_5045_bn`, `gf_5045x3`, plus diameter-tolerance neighbors (`gemfan_5030`, `gemfan_6040`). Option C special-casing is unnecessary.

**Exact OP without voltage.** Live: `resolve_operating_point(..., propeller_sku="hq_5045_bn", voltage_v=None)` → `exact_operating_point` @ 9.7086 N + `v1_max_thrust`. ★7 accepted.

**`is_help_choose_phrase` is reusable.** Soft-match on “elegir” already fires for bare `ayúdame a elegir` — not motor-locked despite module name.

## Notes (non-blocking for PASS; binding for IC)

1. **Incompleteness gate definition:** report’s `motors_done` sketch mixes `catalog_ref` and `completeness != "low"`. IC must pick one clear predicate (recommend: still_missing / stub-or-absent for *offer* help-choose; bound `catalog_ref` for *skip* motor branch when preferring propeller upgrade — align with G21 IDLE early-return on `catalog_ref`).

2. **Full-list fallback when no motor bound:** report says Option B as no-motor fallback but also cites G22 “no silent full dump.” IC must specify: if no motor bound → either empty+honest message **or** limited full list with explicit copy — prefer **honest empty / “define motor first”** if motor is expected in same wizard, to avoid dumping 16 props.

3. **New module `propeller_catalog_assist.py`:** accepted (★2). Keep importing shared phrase/match helpers — no duplication.

4. **Schema add `propeller_suggestions`:** additive on `InteractiveSessionState` — in scope for IC (★3).

## Cursor stance on ★ (for Engineer ratification)

| ★ | Cursor recommendation |
|---|---|
| ★1 Suggestion = `match_motor_propeller` filter (drop C) | **Ratify** |
| ★2 New `propeller_catalog_assist.py` | **Ratify** |
| ★3 Add `propeller_suggestions` session field | **Ratify** |
| ★4 Priority-gating fix in this slice | **Ratify (must)** |
| ★5 OP re-resolve = re-call `set_motor_component` | **Ratify** |
| ★6 Scope A+B (wizard + IDLE) | **Ratify** |
| ★7 No battery step needed for ★6 exact walk | **Ratify** |

## Engineer ratification (2026-08-21)

Aligned with this review. **★1–★7 RATIFIED.**

| ★ | Engineer |
|---|---|
| ★1–★3, ★5–★7 | RATIFIED as recommended |
| ★4 priority-gating | RATIFIED as **must-fix in this slice** |

Notes from review folded into IC (incompleteness predicate, no full-catalog dump without motor, new module bounds).

## Next step

~~Await ★~~ → **DONE.**  
IC: [`implementation_contract_propeller_catalog_bind_ux.md`](implementation_contract_propeller_catalog_bind_ux.md) — **READY FOR CLAUDE**.
