# ERF-2 Implementation Report — Dependency Hardening

**Contract:** [`implementation_contract_erf2.md`](implementation_contract_erf2.md)
**Design (ratified):** [`design_erf2_dependency_hardening.md`](design_erf2_dependency_hardening.md)
**Checkpoint base:** tag `checkpoint-erf1` (`63c427b`)
**Status:** Implemented, all four slices, tests added, full suite green. **Not committed** (per contract §"Do not commit or push unless asked").

---

## Slices completed

- [x] 1 Compatibility authority
- [x] 2 ESC in architecture
- [x] 3 Readiness extension
- [x] 4 CLI surface

(Slice 5 — Continuity handoff — explicitly deferred per ★9, not implemented.)

---

## Files changed

| File | Slice(s) | What |
|---|---|---|
| `src/jarvis/core/electrical_compatibility.py` | 1 | **New module.** `evaluate_electrical_compatibility` + four deterministic checks (`esc_presence`, `esc_vs_motor`, `battery_discharge`, `prop_motor`) per §5–§6. No imports of `engineering_readiness`/`project_continuity`/`orchestrator`/LLM. |
| `src/jarvis/core/system_architecture_catalog.py` | 2 | `BLOCK_TO_COMPONENTS["propulsion"]` gained `"esc"` (★5). |
| `src/jarvis/core/engineering_readiness.py` | 3 | `SUBSYSTEM_KEYS` → nine (added `electronics`). `_COMPONENT_SUBSYSTEM_MAP["esc"]` moved `"propulsion"` → `"electronics"`. Four new gap builders (`_esc_undefined_gap`, `_esc_undersized_gap`, `_battery_discharge_exceeded_gap`, `_prop_motor_mismatch_gap`) wired into `build_engineering_readiness`. New `_electronics_evidence` builder. `_derive_subsystem_verdict` gained an INCOMPATIBLE-class check (checked before the generic HIGH/MEDIUM path) for the three genuinely-incompatible gap types. |
| `src/jarvis/adapters/cli/main.py` | 4 | `_READINESS_SUBSYSTEM_LABELS`/`_READINESS_SUBSYSTEM_ORDER` extended to nine entries including `"Electronics"`. No new rendering logic — `INCOMPATIBLE` already displays verbatim since it was always a valid `SubsystemReadiness.verdict` literal. |
| `tests/test_electrical_compatibility.py` | 1 | New — 14 tests covering the full §9 Slice 1 matrix (per-motor lock, boundary, topology guard, missing-evidence guards, battery exceeded/within-limit/unverifiable, prop-motor mismatch/compatible/unverifiable via a `match_motor_propeller` spy). |
| `tests/test_erf2_architecture.py` | 2 | New — 3 tests: esc in `BLOCK_TO_COMPONENTS`, BOM lists esc missing/not-missing. |
| `tests/test_engineering_readiness_erf2_gaps.py` | 3 | New — 7 tests: all four ERF-2 gap types (trigger + mutual exclusion + sim-PASS-does-not-suppress), ERF-1 gaps still compose, clean-compatibility regression guard. |
| `tests/test_engineering_readiness_erf2_subsystems.py` | 3 | New — 5 tests: nine keys exactly, electronics evidence/verdict separation, unverifiable-not-incompatible guard, mutual exclusion, compatible-no-gap guard. |
| `tests/test_engineering_readiness_cli.py` | 4 (+ 5 updated ERF-1 assertions) | Extended — 2 new tests (`test_cli_shows_electronics_line`, `test_cli_shows_incompatible_label`); 3 existing ERF-1 assertions updated from eight to nine subsystem keys (anticipated by the contract's own "40 ERF-1 tests updated where subsystem count changes" note). |
| `tests/test_engineering_readiness_subsystems.py` | (ERF-1, affected) | 2 renamed/updated assertions (`test_readiness_emits_exactly_eight_subsystems` → `..._nine_subsystems`, `test_no_electronics_subsystem_lines` → `..._no_integration_or_communications...`) + 2 fixtures gained an `esc` component so they stay genuinely gap-free post-★5. |
| **16 pre-existing test files** (architecture/FN-011/013/015/016/017/018/019/020/021/023/block_progress/propulsion_composite_wizard_flow) | (Slice 2 ripple, see below) | Fixtures updated to include an `esc` component wherever the test's own intent was "propulsion block is complete/component-satisfied" — see next section. |

---

## Behavior changed

- **Slices 1–2:** `electrical_compatibility.py` is new and unused elsewhere; `esc` in `BLOCK_TO_COMPONENTS["propulsion"]` is the one observable production-behavior change — BOM/architecture-progress now treat `esc` as a real propulsion component, so `propulsion` block completion now genuinely requires motors + propellers + esc (previously motors + propellers only).
- **Slice 3:** new gaps (`GAP-ESC-UNDEFINED`, `GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH`) + `electronics` subsystem line + `INCOMPATIBLE` verdict, all additive to `build_engineering_readiness`'s existing output shape.
- **Slice 4:** CLI now shows nine subsystem lines instead of eight; `INCOMPATIBLE` renders verbatim in the verdict column when present.

---

## The Slice 2 ripple (unanticipated scope, resolved)

Adding `esc` to `BLOCK_TO_COMPONENTS["propulsion"]` initially broke **62 tests across 14 files** — far beyond the contract's own Slice 2 file estimate (`system_architecture_catalog.py`, `test_architecture_progress.py`, `test_fn020_completeness_coherence.py "if affected"`). The root cause: `propulsion` is a **composite** block (`BLOCK_TYPE["propulsion"] = "composite"`), and its completion predicate requires *all* component keys non-stub — dozens of pre-ERF-2 test fixtures across the FN-011 through FN-023 field-note regression suites, `test_architecture_progress.py`, `test_block_progress.py`, and `test_propulsion_composite_wizard_flow.py` construct a "propulsion complete" or "propulsion in progress, only propellers pending" scenario by declaring exactly `{motors, propellers}` — a completely reasonable assumption before this cut, now a stale one.

I fixed every one of these **by adding an `esc` component to the affected fixture** (not by weakening any assertion) — in every case this restores the test's own original intent (e.g. "propellers is the only remaining propulsion gap" stays true by declaring `esc` alongside `motors` from the start, rather than leaving it as a second, unintended pending item). Two representative fix patterns:

1. **"Propulsion complete" fixtures** (`test_architecture_progress.py`, `test_block_progress.py`, `test_propulsion_composite_wizard_flow.py`): added `"esc": _medium_stub()` (or equivalent) alongside the existing `motors`/`propellers` stubs.
2. **"Propellers is the only pending gap" fixtures** (FN-015 through FN-019, FN-011/013 `components_done=True` branches, FN-023): declared `esc` **from the start** (in both the "pending" and "done" branches) so the file's own actual target (propellers) stays the only thing under test, not co-mingled with an unrelated esc gap.

All 62 originally-failing tests pass again with these fixture updates; no assertion was loosened, no test was deleted. This is the same category of change as the CLI-polish and ERF-1 sessions' test updates — fixtures updated to reflect an intentional, contract-mandated architecture change, not weakened to force a pass.

---

## Tests

```
python -m pytest tests/test_electrical_compatibility.py tests/test_engineering_readiness*.py tests/test_erf2_architecture.py -q
41 passed
```

Regression guards explicitly re-run:

```
python -m pytest tests/test_catalog_foundation_v1.py -q
25 passed
```

Full suite:

```
python -m pytest -q
1844 passed
```
(baseline 1827 at `checkpoint-erf1` + 41 new ERF-2 tests + 2 new CLI tests + net renames in ERF-1 test files = 1844. No failures, no skips.)

---

## Design decisions / interpretation notes

1. **`_topology_determinable`, `_esc_vs_motor`'s mutual exclusion, and the current-priority helpers are implemented exactly per IC §5** (not the simpler design-doc §5.2 sketch) — the IC is the binding document; the design doc predates it and is background context only. Where they differ (e.g. §5.2's declared-`max_current_a`-property step, `_nominal_pack_voltage_v`'s three-tier priority), I followed the IC.
2. **INCOMPATIBLE-class check runs before the generic HIGH-severity path** in `_derive_subsystem_verdict` (see code comment) — all three INCOMPATIBLE-class gap types are severity `HIGH` like ordinary gaps; without this ordering they'd read as `INCOMPLETE` instead of `INCOMPATIBLE`, defeating ★3's whole point.
3. **`_derive_overall` needed no code change** — ERF-1's existing rollup (`any HIGH-severity gap → NOT_ASSEMBLY_READY`, plus the per-subsystem PASS/accepted-WARNING loop) already implements the IC's §4.3 "any INCOMPATIBLE → NOT_ASSEMBLY_READY" rule for free, since all three INCOMPATIBLE-class gaps are HIGH severity and INCOMPATIBLE is never a "PASS" nor an accepted-WARNING verdict.
4. **`electronics.catalog_bound` is honestly `False` in virtually every MVP scenario** — no ESC catalog exists (★7), so `_catalog_ref_set(project_state, "esc")` can only be `True` if some future path binds a `catalog_ref` on an ESC component, which nothing in this cut does. This is intentional, not a bug — matches §8.1's own "likely false in MVP; keep honest."

---

## Risks / follow-ups

- **Slice 5 (Continuity handoff)** — deferred per ★9. A user running the CLI today sees ERF-2 gaps/INCOMPATIBLE verdicts in the `ENGINEERING READINESS` block, but `Situación`/`Siguiente paso` (Continuity's own narration) does not yet mention ESC/battery/prop-motor issues by name — only the readiness block does.
- **H5 ESC catalog** — not implemented (explicitly out of scope, ★7). `_esc_current_a`/`electronics.catalog_bound` only ever read a user-declared `current_a` property, never a SKU.
- **ERF-1 Slice 4b** — still not implemented (unrelated, explicitly out of scope here too).
- **Proposed System Map caveat** (not applied — report only):
  > **Electrical Compatibility (ERF-2, added 2026-08-19):** `src/jarvis/core/electrical_compatibility.py` is a new pure fact authority (ESC presence, ESC-vs-motor current, battery discharge limit, motor↔propeller catalog pairing) — MVP topology lock is 1-motor↔1-ESC-channel, no series/parallel/custom wiring inference. `engineering_readiness.py` composes its facts into four new gap types and a ninth `electronics` subsystem line; `INCOMPATIBLE` is only ever emitted when topology + numeric evidence are both deterministically established (never from missing/heuristic evidence). `BLOCK_TO_COMPONENTS["propulsion"]` now includes `"esc"` — any code or test that assumed propulsion's component set was `{motors, propellers}` needs updating (see implementation_report_erf2.md "The Slice 2 ripple" for the full list of fixtures already migrated).
