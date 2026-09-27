# Implementation Report — Fase C safety-sim policy (`B1-fase-c-safety-sim-policy`)

**IC:** [`implementation_contract_fase_c_safety_sim_policy_b1.md`](implementation_contract_fase_c_safety_sim_policy_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-27
**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.42`** (Engineer 2026-09-27) · Cursor review PASS WITH NOTES.

---

## 0. Read this first — honesty summary

This Buy widens Safety's own armed allow-list to match the three verbs
`SimAutonomyExecutor` (C40) can drive in sim — `HOLD`, `LAND`, and now
`GO_TO` — while `default_safety_gate()` stays `RejectAllSafetyGate` and
`allow` still never means execute.

```text
allow != execute != flying
sim allowlist != copper arm != motors
GO_TO allow != GO_TO in air != SimAutonomyExecutor.tick
```

**Exists:** an opt-in Safety gate that can `allow` `HOLD`/`LAND`/`GO_TO`
once armed. **Impossible:** that `allow` dispatching to any actuator,
calling `SimAutonomyExecutor`, or any real vehicle being "safe to fly."
Nothing in this Buy is any of those, and no shipped path sets
`execution="executed"`.

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/safety.py       # EXTENDED — ArmedAllowlistSafetyGate allow-list widened
src/jarvis/capabilities/__init__.py     # EXTENDED — docstring updated (no new exports; no new symbol)

tests/test_fase_c_safety_sim_policy_b1.py         # NEW — 9 tests
tests/test_fase_c_safety_real_policy_b1.py        # EXTENDED — 2 pre-existing tests disclosed-retargeted for the widened allow-list
```

No `SimAutonomyAllowlistSafetyGate` was added — one gate class, per the
IC's own "prefer one clear gate story" default (§2.1). Python-only, no
C++ twin — Safety has no natural host twin in `native/flight_control/`
(IC §1's own explicit carve-out).

---

## 2. Types / API implemented vs IC §0 / §2

| Item | IC ref | Match |
|---|---|---|
| Allow-list matching C40 verbs when armed | §0.4 | ✅ `ArmedAllowlistSafetyGate._ALLOWED_VERBS` widened to `{HOLD, LAND, GO_TO}` |
| `default_safety_gate()` unchanged | §0.5 | ✅ still returns `RejectAllSafetyGate` — `git diff` shows this line untouched |
| No `AllowAllSafetyGate` | §0.6 | ✅ confirmed absent — `test_t8_no_allow_all_gate_under_src_and_no_executed_state` (C17, unmodified) still passes |
| `submit_command` allow stays `not_implemented` | §0.7 | ✅ re-verified for all three verbs — `test_t4_...` |
| C17 relationship: extend vs new gate | §0.8 | ✅ extended `ArmedAllowlistSafetyGate` — see §2.1 |
| Authority ≠ allow | §0.9 | ✅ re-verified specifically for `GO_TO` — `test_t6_...` |
| C40/plants/loop untouched | §0.11 | ✅ `git diff --stat` empty on every C40/C39/C38/C36/C24 module (§4) |
| Version `0.5.42` | §0.12 | ✅ `pyproject.toml` + 46 checkpoint tests re-pinned |

### 2.1 Disclosed design choices

**One gate, widened — not a second gate class:** the IC offered a
choice: surgically extend `ArmedAllowlistSafetyGate` (C17), or add a
distinct `SimAutonomyAllowlistSafetyGate`. Extending was chosen. C17's
own module docstring already signposted this exact possibility ("this
Buy's locked minimum allow-list — not configurable here; extending it
is a future Buy's decision, not this one's") — this IC is that future
Buy. A second gate class with an overlapping `HOLD`/`LAND` allow-list
would be two competing answers to "which gate do I use for an autonomy
verb," which the IC's own "prefer one clear gate story" explicitly
warns against. `gate_id` stays `"armed_allowlist"`, unchanged — any
caller checking that string is unaffected.

**The one-line change that matters:**
`_ALLOWED_VERBS: frozenset[str] = frozenset({"HOLD", "LAND"})` becomes
`frozenset({"HOLD", "LAND", "GO_TO"})`. Every other line of
`ArmedAllowlistSafetyGate.evaluate(...)` — disarmed check, action-id
parsing, reject reasons, Authority-never-read — is byte-unchanged;
only the set membership check now also matches `GO_TO`.

**Disclosed retarget of two pre-existing C17 tests (not a weakening):**
`tests/test_fase_c_safety_real_policy_b1.py`'s own
`test_t3_armed_hold_and_land_allow` (previously asserting only `HOLD`/
`LAND` allow) now also asserts `GO_TO` allows; its sibling
`test_t4_armed_non_allowlisted_verb_rejects` (previously asserting
`GO_TO` among five rejected verbs) now asserts only the four verbs still
actually rejected (`TAKEOFF`/`FOLLOW`/`RETURN_HOME`/`PATROL`). Both
changes are the direct, intended consequence of the IC's own §0
decision 4 (widen the allow-list) and are explicitly required by §0
decision 8 ("If extending `ArmedAllowlistSafetyGate`, update its
allow-list + tests/docs"). Each retargeted test now carries a docstring
naming this Buy and pointing at its sibling — the same disclosed-
exception convention this session has used for every prior Buy that
had to retarget a pre-existing test's own locked meaning (C37/C38).
Neither test's assertion style, structure, or the rest of the file
changed.

**Honesty false positive avoided while writing new docstrings:** this
Buy's own new prose (in `safety.py` and `capabilities/__init__.py`)
carefully avoids ever writing `execution`/`"executed"` in the adjacent
shape `tests/test_fase_c_safety_real_policy_b1.py`'s own
`test_t8_no_allow_all_gate_under_src_and_no_executed_state` greps for
(whitespace-stripped `execution="executed"`) — a class of false positive
this session already hit once in C40's own report (§2.1 there) and
deliberately checked for again here before landing.

**Not touched by this Buy (IC §0 decisions 9/10/11, confirmed):**
`AuthoritySignal`/Authority-trace-only behavior, ESC-arm/Safety-arm
separation, `SimAutonomyExecutor`, `PositionController`,
`AltitudeController`, `FlightControlLoop`, and every plant module — all
`git diff --stat` empty (§4).

### 2.2 No smoke helper added

The IC's own §0 output 3 calls a smoke "optional." No new
`smoke_*` function was added to `flight_software/autonomy/smoke.py` —
this Buy's own new test module (`test_fase_c_safety_sim_policy_b1.py`)
exercises the widened gate directly (T1-T6), which already covers the
optional smoke's own intent (armed allows `GO_TO` too; default still
rejects) without adding a new exported function whose only caller would
be this Buy's own tests. `smoke_hold_and_land`/
`smoke_policy_gate_hold_and_land` (C4/C17) are untouched — still
exactly `HOLD`+`LAND`, still passing unmodified.

---

## 3. Verified — real test runs

No scratch verification was needed before writing formal tests — this
Buy's own logic is a one-line `frozenset` change plus two disclosed
test retargets, not new numerical/control logic requiring empirical
tuning (unlike C38-C40's own controller work).

```text
$ python -m pytest tests/test_fase_c_safety_real_policy_b1.py \
    tests/test_fase_c_crsf_link_stub_b1.py tests/test_fase_c_crsf_dual_role_bridge_b1.py \
    tests/test_fase_c_autonomy_surface_b1.py -q
59 passed
```

Run immediately after widening the allow-list and before adding the
new test file, to confirm every existing caller of
`ArmedAllowlistSafetyGate` (including the two files that only touch its
disarmed/`TAKEOFF`-reject paths, unaffected by the widening) still
passes.

```text
$ python -m pytest tests/test_fase_c_safety_sim_policy_b1.py -v
9 passed
$ python -m pytest -q
3741 passed, 9 skipped
```

Baseline before this Buy: `3732 passed, 9 skipped`. Delta: **+9
passed** — exactly the new test count, zero regressions (including on
the two disclosed-retargeted C17 tests, which pass under their new,
intended assertions).

```text
$ ctest --test-dir build/flight_control
100% tests passed out of 105
```

Unaffected, as expected — this Buy touches no C++ file (Safety has no
C++ twin), confirmed by an unchanged `105/105` (no delta) against the
baseline this session's own C40 report left at `105/105`.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `default_safety_gate()` / `RejectAllSafetyGate` | Untouched — `git diff --stat` shows this function's own body unmodified |
| `SimAutonomyExecutor` (C40, Python + C++) | Untouched — `git diff --stat` empty |
| `PositionController`/`AltitudeController` (C39/C38) | Untouched — `git diff --stat` empty |
| `FlightControlLoop.step`/`plant.step` | Untouched — `git diff --stat` empty |
| `AuthoritySignal`/Authority-trace-only behavior (C5) | Untouched — never read by the widened gate either |
| `SimulatedEscSink.arm()`/GPIO/PWM | Untouched — no coupling, re-verified by C17's own unmodified `test_gate_not_coupled_to_esc_sink_or_gpio` |
| `native/flight_control/` (any file) | Untouched — `git diff --stat` empty across the whole tree |
| Safety/craft/registry (outside `safety.py`/`capabilities/__init__.py`) | Untouched |

The two disclosed test retargets (§2.1) are the only pre-existing test
changes in this Buy, both explicitly anticipated by the IC's own §0
decision 8.

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_safety_sim_policy_b1.py` — **9 tests**, covering IC
§2's T1-T8 (T8's "suite green" half is the process run in §3; T9 is
this report):

| Test | Covers |
|---|---|
| `test_t1_disarmed_rejects_with_non_not_implemented_reason` | T1 |
| `test_t2_armed_allows_hold_land_go_to` | T2 |
| `test_t3_armed_rejects_other_verbs_with_clear_reason` | T3 |
| `test_t4_submit_command_armed_allow_stays_not_implemented_for_all_three_verbs` | T4 |
| `test_t5_default_safety_gate_still_reject_all` | T5 |
| `test_t6_authority_signal_never_flips_allow_for_go_to` | T6 |
| `test_t7_no_craft_continuity_library_board_edits_and_c40_modules_untouched` | T7 |
| `test_t8_pyproject_version_is_0_5_42` | T8 (version half) |
| `test_t8_full_suite_process_gate_placeholder` | T8 marker |

### 5.2 Python — disclosed retargets in the pre-existing C17 file

`tests/test_fase_c_safety_real_policy_b1.py` — 2 tests retargeted
(§2.1), all other tests in that file (T1, T2, T4b, T5, T6, T7, T8, plus
the smoke/registry/coupling tests) unmodified and still passing under
their original meaning.

---

## 6. Module-boundary / forbidden-symbol grep

```text
$ git diff --stat -- src/jarvis/flight_software/autonomy/sim_executor.py \
    src/jarvis/flight_software/flight_control/position_controller.py \
    src/jarvis/flight_software/flight_control/altitude_controller.py \
    src/jarvis/flight_software/flight_control/loop.py \
    src/jarvis/flight_software/flight_control/plant.py \
    src/jarvis/flight_software/autonomy/surface.py \
    src/jarvis/flight_software/autonomy/types.py \
    native/flight_control/
(empty — every named module and the entire native/ tree byte-unchanged)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
# only pre-existing, external, unrelated diffs (parallel craft-geometry
# track, present before this Buy, not touched by it)
```

No `class AllowAllSafetyGate` or `AllowAllSafetyGate(` anywhere under
`src/` (re-verified by C17's own unmodified `test_t8_...`, which still
passes). No `SafetyGate`/`ArmedAllowlistSafetyGate`/`capabilities.safety`
import or reference in `sim_executor.py`'s real code (docstring prose
naming those symbols to disclose their absence is excluded via the same
comment/docstring-stripping helper every prior Buy's honesty tests use —
`test_t7_...` in this Buy's own new file).

---

## 7. Files changed

**New:**
- `tests/test_fase_c_safety_sim_policy_b1.py`
- `.jes/artifacts/implementation_report_fase_c_safety_sim_policy_b1.md` (this file)

**Modified:**
- `src/jarvis/capabilities/safety.py` (`ArmedAllowlistSafetyGate._ALLOWED_VERBS` widened to include `GO_TO`; module + class docstrings updated)
- `src/jarvis/capabilities/__init__.py` (package docstring updated to disclose the C41 widening)
- `tests/test_fase_c_safety_real_policy_b1.py` (2 tests disclosed-retargeted, §2.1)
- `pyproject.toml` (`0.5.41` → `0.5.42`)
- 46 pre-existing test files re-pinned from `0.5.41` to `0.5.42`
- `README.md`, `docs/ARCHITECTURE.md` (new paragraph after C40), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md` (see §8)

---

## 8. Docs updated (honesty confirmed — not claiming ACCEPT/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.42 includes (LANDED — awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)" section; "Next" pointers retargeted.
- `docs/ARCHITECTURE.md` — new C41 paragraph after the C40 block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C41 block, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C41 table row both changed to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — **not touched**, per the IC's own explicit carve-out (§1: "C++ twin not required unless a natural host twin already exists — it does not for Safety").

No file in this Buy claims `v0.5.42` is tagged, ACCEPT CLOSED,
"executed," "safe to fly," "GO_TO in air," or "Safety certified."
Confirmed via `git tag -l | sort -V | tail -6` at close of this Buy:
`v0.5.35`, `v0.5.37`, `v0.5.38`, `v0.5.39`, `v0.5.40`, `v0.5.41` —
`v0.5.42` does not exist yet.

---

## 9. Residual / next steps

- C42 (ICM register client on `ScriptedSpi`) is next per the IC's own handoff, after Cursor review + Engineer ★ ACCEPT + tag `v0.5.42`. Assistant/placement work stays PARKED until C43.
- The pre-existing MCU-toolchain environment issue (disclosed in C36's own report) remains unfixed, unrelated to this Buy.
- The armed allow-list still only covers `HOLD`/`LAND`/`GO_TO` — the four other `AutonomyVerb` members (`TAKEOFF`/`FOLLOW`/`RETURN_HOME`/`PATROL`) remain rejected under this gate even when armed, matching exactly what `SimAutonomyExecutor` can drive; widening further is a future Buy's decision, same disclaimer C17's own docstring originally carried for this Buy.
- No bridge exists (and none was added) from a Safety `allow` decision to actually invoking `SimAutonomyExecutor.tick` — a caller wanting both a Safety verdict and a sim tick calls the two APIs itself, separately, exactly as before this Buy.

---

## 10. Acceptance self-check vs IC §4 (Acceptance)

- T1-T9: ✅ T1-T8 in Python (9/9 new tests passing, plus 2 disclosed-retargeted C17 tests passing under their new meaning), T9 in this report.
- Allow-list includes `GO_TO`: ✅ `test_t2_armed_allows_hold_land_go_to` + the retargeted C17 test.
- `RejectAll` default: ✅ `default_safety_gate()` body `git diff`-empty; `test_t5_...` re-verifies.
- Allow ≠ execute: ✅ `test_t4_...` — `execution="not_implemented"` for all three verbs, never `"executed"`.
- Version `0.5.42`: ✅ `pyproject.toml` + all 46 checkpoint tests re-pinned.

**PASS** against every criterion in IC §4. **FAIL conditions**
(`"executed"`, default flipped permissive, `AllowAllSafetyGate`, craft
wiring, "we fly") — none present, verified above.
