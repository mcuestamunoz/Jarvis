# Investigation Review — Motor thrust is not an intrinsic property

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_catalog_motor_thrust_not_intrinsic.md](investigation_contract_catalog_motor_thrust_not_intrinsic.md)  
**Report:** [investigation_report_catalog_motor_thrust_not_intrinsic.md](investigation_report_catalog_motor_thrust_not_intrinsic.md)  
**Parents:** ESC mass hygiene CLOSED @ **2344** · G5 DSE sync · P2-1 / MOP OP resolution

## Verdict

**PASS WITH NOTES**

Governing questions answered. Engineer claim confirmed: top-level `thrust_n` is not a motor-alone fact. Default lean **B1 (H1 — sync durability + copy hygiene)** is Buy-ready. H2/H3 correctly deferred (schema program).

Engineer ★ implied by `procede con el IC` → IC follows this review.

---

## Checklist

| Criterion | Result |
|---|---|
| A–G present | **Pass** |
| Schema + resolve ladder + surfaces | **Pass** |
| Seed inventory 22 rows + EMAX/SunnySky spotlight | **Pass** |
| H0–H3 + phrase matrix | **Pass** |
| Blast radius / Buy options + default lean | **Pass** — **B1** |
| No `src/`/`tests/` this investigation | **Pass** (per investigator; Cursor status clean for those trees at review time) |
| Out-of-scope held | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `resolve_operating_point(emax, gemfan_5045_hbn, 16.0)` → exact **13.4841** | **Confirmed** live |
| Top-level `thrust_n` 10.042 === fallback OP row (HQ5045 BN shim) | **Confirmed** in seed |
| `resolve_propulsion_parameters` only honors `source=="declared"` thrust | **Confirmed** (`component_resolver.py`) |
| G5 `sync_motors_component_from_params` tags `source="calculated"`; DSE-only call site | **Confirmed** |
| Propeller **catalog** pick re-calls `set_motor_component` (★5) | **Confirmed** (`orchestrator.py` ~2905–2937) |
| `set_motor_component` already mirrors exact/fallback thrust onto component | **Confirmed** — see **N1** |
| That mirror uses `source="declared"` (not `calculated`) | **Confirmed** (`component_writers.py` ~533–536) |
| Freeform propeller registration path does **not** re-call `set_motor_component` | **Confirmed** (~2485) — related gap |

---

## Agreement with report core

1. **FN-007 vs `resolve_operating_point` dual consumer** — correct and load-bearing.
2. **H1 / B1 over H2–H3** — correct; keep required `thrust_n` for design-space ranking.
3. **Reuse G5 tool / calculated tag** — correct direction.
4. **Copy surfaces show unconditioned peak** — confirmed for CLI assist strings.
5. **Do not remove `resolve_operating_point`** — correct.

---

## Notes (must land in IC)

### N1 — Nuance on “never synced” (do not rubber-stamp)

Report §A says catalog-pick path never got G5 sync. **More precise:**

- `set_motor_component` **already writes** resolved exact/fallback thrust onto `properties["thrust_n"]`, but tags it **`source="declared"`**.
- After a successful OP mirror, `resolve_propulsion_parameters` re-derives the **same** OP number (not necessarily 10.042).
- The proven overwrite to **10.042** is when the component still carries **catalog-peak `declared`** thrust while params briefly held a conditioned value — bind-only / incomplete re-resolve paths.
- **IC fix shape:** retarget that existing write to **`source="calculated"`**, and/or call `sync_motors_component_from_params` after OP params write — same gate G5 closed. Do **not** invent a second sync subsystem.
- **Required regression:** motor+propeller(+voltage) → exact OP → run `resolve_propulsion_parameters` / iterate-style apply → `per_motor_max_thrust_n` **stays** at exact OP (e.g. 13.4841), not 10.042.

### N2 — Freeform propeller gap (in or adjacent)

`set_propeller_component` alone does not re-resolve motor OP; catalog propeller pick does (★5). IC **B1 must** cover durability after OP is written. Extending ★5 to freeform propeller registration is **allowed if tiny**; otherwise name as follow-on — do not expand into Continuity redesign.

### N3 — Copy scope (lock phrases lightly)

CLI candidate + chosen lines: must mark catalog peak as unconditioned / “catálogo”. When `propulsion_resolution` is exact/fallback, prefer showing resolved thrust **with** condition (prop SKU / V) if already in params — no invented copy subsystem. BOM `_MEASURABLE` change: **include only if localized**; else defer explicitly in report (prefer include a one-line honesty tail if cheap).

### N4 — Test triage

IC must list inspect/retarget of `10.042` pins (report §E, 5 files). Retarget, don’t weaken. Pre-judge only after reading each fixture.

### N5 — Non-goals

No schema optionalization (H2) · no rename program (H3) · no pose/glyph · no ESC/FC · no hover rewrite · no version bump · no weakening tests.

---

## Disagreements

**None** on Buy direction. **N1** corrects overstatement of “never synced” without rejecting the mechanical diagnosis or B1 lean.

---

## Buy recommendation

| Option | Cursor stance |
|---|---|
| B0 Defer | Reject — live correctness/honesty gap named |
| **B1 sync + copy** | **★ Recommend / ratified for IC** |
| B2 sync-only | Acceptable narrower fallback if copy blows scope mid-IC — prefer full B1 |
| H2/H3 | Defer |

**Next:** IC `implementation_contract_catalog_motor_thrust_not_intrinsic_b1.md` → Claude implements → Cursor reviews.
