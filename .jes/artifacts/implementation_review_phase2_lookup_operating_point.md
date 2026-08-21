# Implementation Review — Phase 2 P2-1 Lookup Operating Point

**Date:** 2026-08-21  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_phase2_lookup_operating_point.md`](implementation_contract_phase2_lookup_operating_point.md)  
**Report:** [`.jes/artifacts/implementation_report_phase2_lookup_operating_point.md`](implementation_report_phase2_lookup_operating_point.md)  
**★6:** [`.jes/artifacts/phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md)  
**Base:** tag `checkpoint-impl-d` · commit `24fa7ba`

## Verdict

**PASS WITH NOTES**

P2-1 matches the IC and ★6 final locks. Seeds, resolver, bridge, `estado` surface, tests, and probe are in scope. Calc/sim/DSE scoring/BOM/`PropertyValue.source` untouched. The mid-implementation catch (hashable `propulsion_resolution`) is correctly fixed and documented — that is a feature of the delivery, not a residual defect.

**Defect-first review:** No open findings that block checkpoint.

## Checklist

| Gate | Result |
|---|---|
| P2-1 seed: `emax_rs2205s_2300` + `sunnysky_r2205_2500` + props | **Pass** — ★6 numbers; OP-3 rpm=27082 |
| Legacy `emax_rs2205_2300` / `sunnysky_r2305_2500` untouched | **Pass** — no `operating_points`; thrusts 8.0 / 7.5 |
| P2-2 `resolve_operating_point` + `ResolvedOperatingPoint` | **Pass** — exact / fallback / legacy |
| `fallback_only` never → `exact_operating_point` | **Pass** — code + tests |
| Dual exact → max thrust + `v1_max_thrust` | **Pass** — 9.7086 N verified live |
| P2-3 bridge in `set_motor_component` only | **Pass** |
| `propulsion_resolution` hashable (JSON string) | **Pass** — required by DSE cache |
| P2-4 `estado` honest labels | **Pass** — fallback suffix present |
| No calc/sim/BOM/PropertyValue.source / G24–G27 | **Pass** — `git diff` scope |
| P2-5 tests (16) + named regressions | **Pass** — re-ran 45 tests green |
| P2-6 probe claimed 5/5 | **Pass** (report + IC-aligned steps) |
| Report vs code | **Pass** |

## Code review highlights

**Resolver priority is correct.** Exact (non-`fallback_only` + prop match + voltage ε) → fallback → legacy. Unknown SKU → `None`. Known SKU always typed.

**RS2205 vs RS2205S isolation holds.** Live check: legacy resolve → `legacy_estimate` @ 8.0 N; S without prop → `fallback_operating_point` @ 10.042 N; S + `hq_5045_bn` @ 16 V → `exact_operating_point` @ 9.7086 N + `v1_max_thrust`.

**Bridge voltage sourcing is sound.** Battery catalog `nominal_voltage` / `cells×3.7`, else `battery_cell_count` params — no invented pack voltage.

**JSON-string provenance is the right fix.** Nested dict in `current_parameters` breaks `frozenset(params.items())` in Design Explorer candidate eval (errors swallowed → empty catalog DSE). Storing JSON + parse at startup/CLI boundary preserves hashability without touching DSE scoring (IC-forbidden). Flag for every future Phase 2 param: **values in `current_parameters` must remain hashable.**

**CLI honesty:** fallback line appends `(sin hélice de catálogo)`; freeform motors emit no propulsion evidence line.

## Notes (non-blocking)

1. **Document the hashability constraint** in Continuity/ARCHITECTURE or next Phase 2 IC preamble so the next cut does not rediscover it the hard way. Optional one-line ADR — not required to checkpoint P2-1.

2. **Exact `estado` line omits `selection_reason`** (`v1_max_thrust`). Acceptable for v1; optional polish later.

3. **Propeller-bind live UX** still absent — probe uses `bind_propeller_from_catalog` (allowed by IC). Product path remains Phase 2.x.

4. **`v1_max_thrust` ignores current budget** (25 A vs 27 A) — provisional by ★6; do not “fix” in a drive-by.

5. Untracked at review time: tests, probe, investigation/IC/★6/report artifacts — include in the P2-1 commit when Engineer asks (exclude `workspace/`, optional old g21 probe).

## Next step

Engineer: optional short CLI walk → commit (+ tag e.g. `checkpoint-phase2-p2-1` if desired).  
**Version bump still deferred** until Engineer decides (P2-1 end-to-end is now a valid bump candidate, but not automatic).  
Debt queue unchanged: G24–G27 · propeller UX · current-aware OP selection.
