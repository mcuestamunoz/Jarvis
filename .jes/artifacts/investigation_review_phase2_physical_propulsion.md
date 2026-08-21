# Investigation Review — Phase 2 Physical Propulsion Engine

**Date:** 2026-08-21  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_phase2_physical_propulsion.md`](investigation_contract_phase2_physical_propulsion.md)  
**Report:** [`.jes/artifacts/investigation_report_phase2_physical_propulsion.md`](investigation_report_phase2_physical_propulsion.md)  
**Base:** tag `checkpoint-impl-d` · commit `24fa7ba`

## Verdict

**PASS WITH NOTES**

Investigation complete: all required sections present, zero `src/` / test changes verified. As-is physics audit is accurate and actionable. G26/G27 prerequisite verdict is **code-traced and accepted**. Option A is the correct first-slice recommendation. ★6 (sourced OP numbers) correctly left unfabricated — that remains a **hard gate before any Implementation Contract**.

**Defect-first check:** No findings that invalidate the report.

## Checklist

| Gate | Result |
|---|---|
| §1.1 As-is propulsion physics audit | **Pass** — declared thrust wins; Ct=0.12 heuristic never reads bound prop `ct` |
| §1.2 Catalog inventory vs vision | **Pass** — `operating_points[]` reserved, 0/20 motors populated; no `ESCSpec` |
| §1.3 Operating-point schema | **Pass** — reuses Catalog V1 §4.2 shape; library-resident |
| §1.4 ProjectState / calc / sim / ERF / BOM | **Pass** — populate `per_motor_max_thrust_n`, not replace; Impl D untouched |
| §1.5 G26/G27 dependency verdict | **Pass** — both **NO**; G27 traced to `_parse_value` first-digit regex |
| §1.6 G24 deferral | **Pass** — no elevation evidence |
| §1.7 Design options (≥2) | **Pass** — A recommended; B/C deferred with rationale |
| §1.8–1.10 Model 1 keep / tests / slices | **Pass** |
| ★ numbered for Engineer | **Pass** — ★1–★6 |
| No production fix / no Conversation Engine | **Pass** |

## Code review highlights

**Thrust is context-free today.** Confirmed: catalog bind → Impl C bridge → bare `per_motor_max_thrust_n`; propeller path only if that param is absent, with hardcoded `Ct=0.12`.

**`operating_points[]` is dormant infrastructure.** Confirmed in `library.py` on Motor/Battery/Propeller; live library: **20 motors, 0 with operating_points**. Matches Catalog V1 “zero consumer in A/B.”

**G27 root cause confirmed.** `semantic_intent_adapter._parse_value` uses `re.search(r"-?\d+(?:\.\d+)?", text)` — first number wins (`6` from `6S`). Catalog `bind_battery_from_catalog` path is independent. **NO as Phase 2 calc prerequisite is correct.**

**G26 orthogonal to physics.** `_parse_constraints` reads `restrictions` string only — readiness UX, not OP math. **NO prerequisite accepted.**

**Integration surface is narrow.** Sim/calc consume the thrust scalar; Option A can ship without touching `FeasibilitySimulator` control flow if it writes through the existing bridge.

## Notes (non-blocking for PASS; binding for next step)

1. **★6 is the real gate before IC.** Cursor will **not** invent datasheet thrust/current/voltage numbers. Engineer must approve a small sourced set (or point to datasheets) before `implementation_contract_phase2_*` is written.

2. **Option A probe without propeller-bind UX:** ensure curated table includes at least one **motor(+voltage)-only** row so the first CLI walk can prove OP-hit without waiting for propeller pick UX. Motor+prop rows remain valuable for P2-v2 / probe step 3–4.

3. **G27 remains urgent parallel debt.** It still corrupts Model 1 autonomy when users free-text batteries. Not a Phase 2 gate — still worth a dedicated IC soon after / alongside Phase 2 ★, ranked independently.

4. **Fallback label `estimated` for bare `MotorSpec.thrust_n`:** honest for Phase 2 narrative; IC should state that today’s unlabeled peak remains numerically identical on OP-miss (regression contract).

5. **★5 defer-to-IC:** accepted — do not reopen architecture on provenance *surface* location.

## Cursor stance on ★ (for Engineer ratification)

| ★ | Cursor recommendation |
|---|---|
| ★1 Provenance as OP-only `source_type` (not widen `PropertyValue.source`) | **Ratify (b)** |
| ★2 Option A Lookup OP as first IC | **Ratify** |
| ★3 G26/G27 not Phase 2 prerequisites | **Ratify** |
| ★4 G24 stay deferred | **Ratify** |
| ★5 Provenance surface → IC detail | **Ratify defer** |
| ★6 Curated SKUs + sourced numbers | **Required before IC** — Engineer supplies/approves; Cursor does not invent |

## Engineer ratification (2026-08-21)

Aligned with this review. Locked:

| ★ | Engineer |
|---|---|
| ★1 Provenance as OP-only `source_type` (not widen `PropertyValue.source`) | **RATIFIED** |
| ★2 Option A Lookup OP as first IC | **RATIFIED** |
| ★3 G26/G27 not Phase 2 prerequisites | **RATIFIED** |
| ★4 G24 stay deferred | **RATIFIED** |
| ★5 Provenance surface → IC detail | **RATIFIED** (defer) |
| ★6 Curated SKUs + sourced OP numbers | **OPEN — hard gate** (do not invent; Engineer supplies/approves) |

Also locked by Engineer narrative:
- No parallel Physics Engine; activate dormant `operating_points[]`
- No ESC catalog / full propeller-bind UX / DSE / sim rewrite in P2-1
- No version bump until P2-1 end-to-end
- G26/G27 remain independent debt (not mixed into P2-1)

## Next step

~~Await ★1–★5~~ → **DONE.**  
**Await ★6** (sourced Validation Case dataset) → Cursor drafts `implementation_contract_phase2_lookup_operating_point.md` (P2-1…P2-6 only).  
**Do not implement Phase 2 until that IC exists.**