# Investigation Review — IDLE component re-acquisition

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_idle_component_reacquisition.md](investigation_contract_idle_component_reacquisition.md)  
**Report:** [investigation_report_idle_component_reacquisition.md](investigation_report_idle_component_reacquisition.md)  
**Base:** `v0.3.6` + Structure block CLOSED @ suite **2229** (live tree)  
**Engineer mandate:** OK next path = IDLE re-acquisition; coherence secondary

## Verdict

**PASS WITH NOTES**

Buy **B2 frame-first** accepted. B3 deferred correctly. Coherence fork **B0/debt** accepted (arms↔motors naming is structurally a validation claim). G-N4 catalog-path orphan named as **one-line IC policy**, not a new thread — correct.

Ready for Engineer ★ on Buy / phrase set / children-clear policy. **Not** for silent implementation.

---

## Checklist

| Criterion | Result |
|---|---|
| Dual gates (FN-014 complete + `_wants_catalog_help` bound) | **Pass** — `orchestrator.py:1675-1678`, `:114-121`, `:893-909` |
| No frame step in IDLE help-choose chain | **Pass** — motor → propeller → battery only |
| `"ayúdame a elegir frame"` soft-match discards `frame` | **Pass** — `is_help_choose_phrase` soft match is `ayudame`+`elegir` (`motor_catalog_assist.py:72-76`); no component token |
| `"cambiar`/`definir frame"` → iterate | **Pass** — `ITERATE_PATTERNS`; `"frame"` ∉ `_VALID_VARIABLE_DOMAIN` / `_STRUCTURAL_TERMS` |
| Universal bound-swap gap (not frame-only) | **Pass** — Know table + T1 underspec as sole *system*-triggered exception |
| Frankenstein / G-N4 free-text + catalog rebind | **Pass** — `upsert_frame_part` merges; apply path upserts new parts only, never clears absent keys (`orchestrator.py:3077-3080`) |
| Buy B2 vs B3/B4/B5 | **Pass** — frame-first reuses IC-3 offer/apply; B3 wait for field proof; B5 debt |
| No `src/` from this investigation | **Pass** — only report artifact added this turn |
| Non-goals (Structure/MEASURE/cross-check) | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| FN-014 early return when `_next_pending_block is None` | **Confirmed** — `orchestrator.py:1675-1678` before `resolve_acquisition_mention` |
| IDLE help-choose = motor→prop→battery, no frame | **Confirmed** — `orchestrator.py:893-909` |
| `_wants_catalog_help` false when `catalog_ref` set | **Confirmed** — `orchestrator.py:114-121` |
| Soft help-choose matches trailing tokens | **Confirmed** — `"ayúdame a elegir frame"` contains `ayudame`+`elegir` |
| `_apply_component_frame_catalog_pick` does not clear orphans | **Confirmed** — only upserts keys present in `frame_part_specs_from_catalog` |
| `upsert_frame_part` merge semantics | **Confirmed** — docstring + `merged_props.update` (`component_writers.py:188-199`) |
| No `"frame"` iterate variable | **Confirmed** — `_STRUCTURAL_TERMS` has `estructura`/`componentes`, not `frame` |

---

## Notes

### N1 — `"frame Armattan…"` matrix row may be session-contaminated

Report §C says that phrase reopens the **motor** free-text prompt. Engineer field walk (same day, true IDLE after `cancelar`) got the **frame** low-completeness prompt (*"Describe el frame…"*). Likely cause: Fixture A ran phrases sequentially after an underspec motor list left `DEFINE_MISSING` + `expected_keys=["motors"]`.

**Impact:** conclusion unchanged (no SKU-from-display-name bind). IC tests must assert from **clean IDLE**, and B2 should **not** depend on fixing name→SKU as part of the minimum slice (list+pick is enough; name resolution is optional later / B1 residual).

### N2 — B2 must not broaden FN-014 to “any named component”

Report §H correctly says *frame only* and *explicitly named*. IC must keep the exception **narrow**: do not reopen propulsion/energy blocks when `pending_block_key is None` for arbitrary mentions. Prefer a sibling IDLE dispatch for the locked phrase set over a general “satisfied component” reopen of `_continue_block_acquisition` (that helper is gap-oriented, not rebind-oriented).

### N3 — Children-clear policy is mandatory in the B2 IC

§F is right: shipping B2 without an explicit clear/replace rule for `frame_*` when the new SKU’s part set differs (Armattan→TBS, or freeform→SKU) would **productize** frankenstein via the happy path. Engineer ★ should lock one line, e.g.:

> On catalog frame re-pick: replace root; **remove** any `frame_*` child whose key is absent from the new SKU’s `frame_part_specs_from_catalog`; upsert the new set.

(Or the weaker “clear all `parent_key=frame` children then upsert” — same outcome for Fase 1.)

### N4 — Bare `"ayúdame a elegir"` triage is a regression gate

Report correctly treats motor-underspec-first as a **feature**. IC must keep a test that unnamed help-choose still prefers T1 motor re-offer when underspec, and does **not** open frame.

---

## Engineer ★ decisions needed

1. **Buy = B2 frame-first?** (Cursor recommends yes)  
2. **Locked phrases** (minimum): `cambiar frame`, `definir frame`, `ayúdame a elegir frame` — confirm; name→SKU optional out.  
3. **Children policy** on re-pick (N3) — clear absent / clear-all-then-upsert?  
4. **Coherence arms↔motors** — confirm remains debt (Cursor: yes).

After ★ → Cursor drafts Implementation Contract; Claude implements only from that IC.

---

## ★ RATIFIED 2026-09-04

Engineer `procede`. IC: [implementation_contract_idle_frame_rebind_b2.md](implementation_contract_idle_frame_rebind_b2.md).  
Locks: B2 · phrases · clear-all children then upsert · coherence debt · name→SKU out.
