# Implementation Review — Envelope stack rule B1 · B0 hold (`B1-stack-rule`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_geometry_stack_rule_b1.md) · [report](implementation_report_geometry_stack_rule_b1.md)  
**Verdict:** **PASS WITH NOTES** (honest B0 hold — schema conflict, not missing citation)

---

## Checklist

| Gate | Result |
|---|---|
| Stopped before shipping never-confirmable Path N | **Pass** |
| Origin-must-be-box gate cited correctly | **Pass** — Cursor re-checked `component_writers.py` ~337–340 |
| Motors/props → disk, never box via `_geometry_from_spec` | **Pass** — `spatial_board.py` ~278–317; MotorSpec/PropellerSpec lack L×W |
| Envelope declare excludes motors/propellers as subjects | **Pass** — `declared_envelope_declare_assist.py` ~287–288 |
| No writer-gate weaken / no invent plate / no code | **Pass** |
| Path F correctly left data-gated on plate-box | **Pass** |
| Package `0.4.1` · no `src/` footprint | **Pass** |

---

## Notes

| ID | Note |
|---|---|
| **N1** | Cursor’s earlier stack-rule IC offering Path N as “implementable now” was **wrong relative to the pose writer**. Investigation §C described arithmetic that *could* be computed; it did not prove Continuity pose confirm works for disk origins. Hold corrects that. Do not re-★ Path N without an architecture Buy (disk-as-pose-origin or alternate boxed mount). |
| **N2** | Fold N1 into any future layout investigation read — do not edit the closed B0 investigation report unless Engineer asks. |
| **N3** | Only reopen stack-rule for **Path F** after plate-box §0.1 fills and plate is a box. |

---

## Verdict

**PASS WITH NOTES** — B0 hold accepted. Layout cola code path idle until plate caliper/cita. Actionable now: Engineer smokes (mount-assist, Situar, #4*) · wait for frame measure.
