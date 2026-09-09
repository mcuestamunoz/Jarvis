# Investigation Review — Assembly kit template (novice vs 4-block)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_assembly_kit_template_b0.md](investigation_contract_assembly_kit_template_b0.md)  
**Report:** [investigation_report_assembly_kit_template_b0.md](investigation_report_assembly_kit_template_b0.md)  
**Parents:** [engineer_lock_assembly_kit_template.md](engineer_lock_assembly_kit_template.md)  
**Next steps (ordered):** [engineer_next_assembly_kit_template.md](engineer_next_assembly_kit_template.md)

## Verdict

**PASS WITH NOTES**

Claude’s split **P-energy vs P-kit** is correct. The live 7-key template cannot represent adapters/connectors/harness; those are not “pending,” they are **invisible**. Default lean **B1, narrow, non-PASS-gating** is the right *direction*. It is **not** yet an Implementation Contract: “add three lines to `BLOCK_TO_COMPONENTS`” would **widen** propulsion/energy AND-strict completion (Locked Stance #6). That consumer split is the IC’s first decision.

Engineer ★ required on **Buy shape** before any `src/`.

---

## Checklist

| Criterion | Result |
|---|---|
| 4 blocks → 7 unique keys | **Pass** — `motors` `propellers` `esc` `battery` `frame` `flight_controller` `sensors` |
| Slots = `BLOCK_TO_COMPONENTS` of **declared** blocks only | **Pass** — `_expected_keys_by_column` |
| BOM `missing` = same expected set; extras classifiable; `parent_key` excluded | **Pass** — `build_component_bom` |
| Structure B children exist; not top-level BOM | **Pass** |
| Architecture session fixes the 7-key set at create | **Pass** |
| Default lean named; 40-line list rejected | **Pass** |
| Acquisition via existing DEFINE/Continuity/slots | **Pass as intent** — see N2 (not free) |
| No `src/` / library seed | **Pass** (report only) |
| Plate L×W / scrape / Conversation Engine out | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Append to `propulsion`/`energy` lists → composite `components_ok` requires the new keys | **Confirmed** — `_block_progress_status` composite: `len(non_low) == len(component_keys)` in both `orchestrator.py` and `engineering_readiness.py` |
| `actuation` is `param` → ignores `component_keys` | **Confirmed** — but `actuation` is **not** in `dron` architecture. Copying the param trick onto a new dron block with **no** `param_reason` yields `not_started` forever. **Not** a drop-in for B1. |
| Continuity “Define el componente pendiente: {key}” | **Confirmed** — rank 4 reads BOM `missing[0]` (`project_continuity.py`) |
| DEFINE missing keys | **Confirmed** — orchestrator walks `BLOCK_TO_COMPONENTS[block]` for composite/component blocks. A parallel registry **unwired** to DEFINE would make Continuity ask and DEFINE ignore. |
| B2 “pending if not in seed” already implemented | **Overclaim** — bind projects **curated seed only**. Unseeded HD/VTX plates are **invisible**, not pending children. Seeding those is the plate-L×W **optional text B1**, not a new pending mechanism. |
| Live demo 7 roots + 6 frame children, no adapter/connector | **Plausible**; `/workspace/` is gitignored — Cursor did not re-read `state.json`. Does not change the product finding. |

---

## Notes

### N1 — Central IC gate: visibility ≠ completion

Same dict today feeds: Board slots, BOM expected, Continuity rank 4, DEFINE missing, architecture 4/4, ERF block progress.

B1 must **split** those consumers. Naive append to `propulsion`/`energy` is **forbidden**.

Cursor lean for the IC (Engineer may ★ otherwise):

```text
KIT_TO_COMPONENTS["dron"] = ["power_connector", "signal_harness"]
Board + BOM expected + Continuity missing  →  union(BLOCK_TO, KIT_TO)
architecture / ERF propulsion-energy-structure PASS  →  BLOCK_TO only
DEFINE_MISSING / IDLE “define X”              →  must see KIT_TO too
```

Not a Conversation Engine. One small registry + explicit call sites. Twin tests: P-energy predicates **byte-identical**; kit keys appear as slot + BOM `missing`.

### N2 — “Same DEFINE chain” is not automatic

Claude §C is true **only after** DEFINE’s missing-key helper reads the kit set. IC file list must include that orchestrator path, not only `spatial_board.py` + `project_closure.py`.

### N3 — `prop_adapter` as “conditionally pending”

Today a slot is **unconditional** if the key is expected. Conditional (bore match) is a **later** rule, not B1. First cut: **omit** `prop_adapter`, or include it as always-pending with card text “puede no aplicar.” Do not invent a condition engine in the first IC.

### N4 — ASSEMBLY READY vs hover PASS

BOM `missing` already keeps **NOT ASSEMBLY READY** when expected keys are holes. Putting kit keys on BOM expected is **honest for P-kit** and must **not** change hover/autonomy/Structure/Propulsion PASS. IC twins must name both.

### N5 — Camera / VTX / RX

Engineer’s “controllers, wiring, adapters” is broader than Claude’s three keys. First IC stays **N≤2** (`power_connector`, `signal_harness`). VTX/RX/FPV camera = later ★ (may overlap `sensors`). Mounting hardware stays Structure B / B2 seed, not a fourth architecture key.

---

## Buys (Cursor ranking after review)

| ID | After review | Engineer ★ |
|---|---|---|
| **B1-min** | 2 kit keys + `KIT_TO_COMPONENTS` + DEFINE/Board/BOM wire; **no** PASS widen | **Default next IC** |
| **B3** | Continuity one-liner: architecture ≠ full kit | Same IC footnote **or** doc-only if B1 waits |
| **B2** | Seed Rooster HD + VTX plates (Armattan Included) | **Later**, catalog-only; not the template |
| **B0** | Keep 7 keys, no kit signal | Reject unless Engineer explicitly parks P-kit |
| **B1-naive** | Append to `propulsion` | **Forbidden** |

---

## Phase

Investigation **REVIEWED PASS WITH NOTES**. No implementation until Engineer ★ **B1-min** (or an explicit alternate). Package `0.3.8` · suite **2497**.
