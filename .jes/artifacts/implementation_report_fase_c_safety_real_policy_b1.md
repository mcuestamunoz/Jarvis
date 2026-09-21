# Implementation Report — Fase C Safety-real policy gate (`B1-fase-c-safety-real-policy`)

**IC:** [`implementation_contract_fase_c_safety_real_policy_b1.md`](implementation_contract_fase_c_safety_real_policy_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.15`**. See [review](implementation_review_fase_c_safety_real_policy_b1.md).

---

## 0. Read this first — opt-in policy, honesty summary

This Buy ships the first real (non-RejectAll) Safety gate: **`ArmedAllowlistSafetyGate`** in `src/jarvis/capabilities/safety.py`. It starts **disarmed** and, while disarmed, always rejects. Once explicitly `arm()`ed, it `allow`s **only** `HOLD` and `LAND` (parsed from the `autonomy:{verb}:{id}` shape `submit_command` already builds); any other verb, or a malformed `action_id`, is rejected too. It never reads `authority_signal_id` — Authority stays trace-only (C5), unable to influence this or any gate's decision.

**`default_safety_gate()` is unchanged** — confirmed by `git diff` on `RejectAllSafetyGate`'s class body and `default_safety_gate()`'s own function body: zero lines touched, only new code inserted after them. The shipped product default remains "reject everything," exactly as before this Buy.

**Allow still never means execute.** `submit_command`'s `allow` branch already existed (added in C4, previously unreachable since no shipped gate ever returned `allow`) and already resolved to `execution="not_implemented"` — this Buy did not need to touch `flight_software/autonomy/surface.py` or `types.py` at all to satisfy that lock; it was already correct. `ExecutionState` (`Literal["not_attempted", "not_implemented"]`) still has no `"executed"` member — verified at runtime via `typing.get_args`, not just by grep, in this Buy's own test suite.

---

## 1. Package layout vs IC §1

```text
src/jarvis/capabilities/
  safety.py          # + ArmedAllowlistSafetyGate, + _parse_autonomy_verb (private helper)
                      # RejectAllSafetyGate / default_safety_gate(): byte-unchanged
  __init__.py         # + export ArmedAllowlistSafetyGate; docstring honesty updated
src/jarvis/flight_software/autonomy/
  smoke.py            # + smoke_policy_gate_hold_and_land (thin smoke, IC §0's "optional... preferred")
  __init__.py         # + export smoke_policy_gate_hold_and_land; docstring pointer updated
tests/test_fase_c_safety_real_policy_b1.py   # NEW
```

Matches the IC's normative layout (§1) exactly — no new architectural subsystem, everything stays inside `capabilities/` and the existing `autonomy` surface.

---

## 2. Types / API implemented vs IC §2 behavior table

| Gate | State | Request | `outcome` | Reason | Matches IC §2 |
|---|---|---|---|---|---|
| RejectAll (default) | n/a | any | `reject` | `"not_implemented"` (unchanged, historical) | ✅ |
| ArmedAllowlist | disarmed | any | `reject` | `"disarmed"` | ✅ |
| ArmedAllowlist | armed | HOLD | `allow` | — | ✅ |
| ArmedAllowlist | armed | LAND | `allow` | — | ✅ |
| ArmedAllowlist | armed | TAKEOFF (or other) | `reject` | `"verb_not_allowed"` | ✅ |
| ArmedAllowlist | armed, malformed `action_id` | — | `reject` | `"unparseable_action_id"` | added case, not in the IC's own minimal table but required by "robust parsing" (§0 decision 7) |
| ArmedAllowlist | any + `authority_signal_id` set | — | unchanged from the no-authority case | — | ✅ — `authority_signal_id` is never read by `evaluate()` at all, not merely ignored by a conditional |

`gate_id = "armed_allowlist"` — distinct from `"reject_all"` (§0 decision 6). Reason-string hygiene locked by §0 decision 8: `"disarmed"`, `"verb_not_allowed"`, `"unparseable_action_id"` — none reuse `RejectAllSafetyGate`'s `"not_implemented"`.

**Allow-list is a hardcoded class constant** (`_ALLOWED_VERBS: frozenset[str] = frozenset({"HOLD", "LAND"})`), not a constructor parameter — deliberately, to match the IC's "locked minimum" framing rather than opening an extension point this Buy wasn't asked to design.

**Empirically verified before writing formal tests** (scratch script, full transcript in session):
```text
armed initially: False
disarmed HOLD:            reject / disarmed
armed HOLD:                allow
armed LAND:                allow
armed TAKEOFF:              reject / verb_not_allowed
armed no action_id:          reject / unparseable_action_id
armed HOLD + authority set:   allow   (same outcome as without authority)
re-disarmed HOLD:              reject / disarmed
submit_command armed HOLD:      allow / not_implemented
submit_command armed TAKEOFF:    reject / not_attempted / verb_not_allowed
default gate:                     RejectAllSafetyGate
default HOLD:                      reject / not_attempted / not_implemented
```

---

## 3. Integration rules (IC §3) — confirmed unchanged

- `default_safety_gate()` — still `RejectAllSafetyGate` (§0, byte-diff confirmed).
- `submit_command` — unchanged contract: `allow` → `execution="not_implemented"`; `reject` → `execution="not_attempted"` (no code change needed, already correct since C4).
- Rung regression tests pinning RejectAll — re-verified green directly in this Buy's own test suite (`test_existing_rung_regressions_pinning_reject_all_still_green`, re-running `smoke_hold_and_land()`), plus the full suite (§5).
- Radio / Authority — trace only; `ArmedAllowlistSafetyGate.evaluate()` never reads `authority_signal_id`.
- Craft / Board / CLI / C++ tree — untouched; grep-confirmed no reference to `ArmedAllowlistSafetyGate`/`armed_allowlist` under `src/jarvis/core` or `src/jarvis/adapters`.

---

## 4. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | Gate exists; starts disarmed; `arm`/`disarm` work | ✅ `test_t1_gate_exists_starts_disarmed_arm_disarm_work` |
| T2 | Disarmed → reject with non-`not_implemented` reason | ✅ `test_t2_disarmed_rejects_with_non_not_implemented_reason` |
| T3 | Armed + HOLD and armed + LAND → allow | ✅ `test_t3_armed_hold_and_land_allow` |
| T4 | Armed + TAKEOFF (or other non-list verb) → reject | ✅ `test_t4_armed_non_allowlisted_verb_rejects` (+ `test_t4b_armed_unparseable_action_id_rejects`) |
| T5 | `authority_signal_id` set does not flip allow when disarmed / not-on-list (and doesn't cause allow when it otherwise wouldn't) | ✅ `test_t5_authority_signal_never_flips_allow` |
| T6 | `submit_command(HOLD, policy_gate)` armed → `safety.allow` + `execution="not_implemented"` | ✅ `test_t6_submit_command_armed_hold_allows_but_execution_not_implemented` |
| T7 | `default_safety_gate()` still `RejectAllSafetyGate`; HOLD under default still reject + `not_attempted` | ✅ `test_t7_default_safety_gate_still_reject_all_and_hold_still_rejects` |
| T8 | No `AllowAllSafetyGate` under `src/`; no `execution="executed"` introduced | ✅ `test_t8_no_allow_all_gate_under_src_and_no_executed_state` (real-usage-shape grep + authoritative `typing.get_args(ExecutionState)` check) |
| T9 | Report + docs honesty; no premature `v0.5.15` tag | ✅ §7 below |
| T10 | Python full suite green @ `0.5.15` | ✅ **3403 passed, 1 skipped** (was 3389 — exact +14 delta) |

New Python test module `tests/test_fase_c_safety_real_policy_b1.py` — **14 tests**, all passing:

```text
test_t1_gate_exists_starts_disarmed_arm_disarm_work PASSED
test_t2_disarmed_rejects_with_non_not_implemented_reason PASSED
test_t3_armed_hold_and_land_allow PASSED
test_t4_armed_non_allowlisted_verb_rejects PASSED
test_t4b_armed_unparseable_action_id_rejects PASSED
test_t5_authority_signal_never_flips_allow PASSED
test_t6_submit_command_armed_hold_allows_but_execution_not_implemented PASSED
test_t7_default_safety_gate_still_reject_all_and_hold_still_rejects PASSED
test_t8_no_allow_all_gate_under_src_and_no_executed_state PASSED
test_existing_rung_regressions_pinning_reject_all_still_green PASSED
test_smoke_policy_gate_hold_and_land PASSED
test_capability_registry_default_still_empty PASSED
test_gate_not_coupled_to_esc_sink_or_gpio PASSED
test_t9_pyproject_version_is_0_5_15 PASSED
```

**A honesty-test false-positive caught and fixed during this Buy (disclosed, matching the project's established convention):** the first draft of `test_t8_no_allow_all_gate_under_src_and_no_executed_state` and `test_gate_not_coupled_to_esc_sink_or_gpio` checked bare substrings (`"AllowAllSafetyGate"`, `"executed"`, `"SimulatedEscSink"`/`"GPIO"`/`"PWM"`) anywhere in `src/`'s source text — which false-failed against this Buy's own new honesty-prose docstrings (e.g. "there is no `AllowAllSafetyGate`...", "...does not touch `SimulatedEscSink`/GPIO/PWM...") and the **pre-existing** C2 docstring in `capabilities/__init__.py` that has said "there is no `AllowAllSafetyGate` anywhere in this package" since C2. Fixed by checking real usage shapes only (`"class AllowAllSafetyGate"`, `"AllowAllSafetyGate("`, `'execution="executed"'`) plus an authoritative runtime check via `typing.get_args(ExecutionState)` for the execution-state claim, and by stripping docstring lines before scanning `safety.py` for ESC/GPIO coupling — the same "symbol(" / "class symbol" vs. prose-mention distinction used by every prior Fase C Buy's honesty tests, just freshly re-derived here since this was the first Buy where the *docstrings themselves* needed to name the forbidden terms to disclose their absence.

**T10 (full suite):** `pytest -q` — **3403 passed, 1 skipped** (baseline before this Buy was 3389 passed, 1 skipped; delta is exactly the 14 new tests, no other file's pass/fail count moved).

Twenty-two pre-existing test files hardcoded the prior checkpoint version string (`"0.5.14"`) as a version-pin assertion. Since this IC explicitly requires the `0.5.15` bump (§0 decision 12), all twenty-two were re-pinned to `"0.5.15"`:

- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_fase_c_cpp_esc_pwm_stub_b1.py`
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py`
- `tests/test_fase_c_cpp_mcu_cross_compile_b1.py`
- `tests/test_fase_c_cpp_unit_tests_b1.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_rate_torque_bridge_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_power_w_b1.py`
- `tests/test_mission_vtx_identity_b1.py`

---

## 5. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Flip default to permissive | ✅ absent | `default_safety_gate()` byte-unchanged, still returns `RejectAllSafetyGate()` (§0, §3) |
| `AllowAllSafetyGate` under `src/` | ✅ absent | T8 — no `class AllowAllSafetyGate` / `AllowAllSafetyGate(` anywhere |
| Executor / `"executed"` | ✅ absent | T8 — `typing.get_args(ExecutionState) == {"not_attempted", "not_implemented"}` |
| ESC sink / GPIO / craft wiring | ✅ absent | `test_gate_not_coupled_to_esc_sink_or_gpio` (real-code-only scan of `safety.py`) + craft-isolation grep (§0) |
| "Safe to fly" language | ✅ absent | Not present anywhere in new code, docstrings, or docs updates (§7) |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the real Safety policy scope. No MCU `.elf`, ELRS, craft↔FS, GPIO/ESC, executor, or CLI Intent→autonomy wiring was touched or opened.

---

## 6. Files changed

**New:**
- `tests/test_fase_c_safety_real_policy_b1.py`
- `.jes/artifacts/implementation_report_fase_c_safety_real_policy_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.14` → `0.5.15`
- `src/jarvis/capabilities/safety.py` — added `ArmedAllowlistSafetyGate` + `_parse_autonomy_verb`; module docstring extended; `RejectAllSafetyGate`/`default_safety_gate()` byte-unchanged
- `src/jarvis/capabilities/__init__.py` — export `ArmedAllowlistSafetyGate`; docstring honesty note added
- `src/jarvis/flight_software/autonomy/smoke.py` — added `smoke_policy_gate_hold_and_land`; `smoke_hold_and_land` byte-unchanged
- `src/jarvis/flight_software/autonomy/__init__.py` — export the new smoke function; docstring pointer updated
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C17 sections (see §7)
- 22 test files — re-pinned stale `0.5.14` version-checkpoint assertions to `0.5.15`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `native/flight_control/**` (C++ tree), `src/jarvis/flight_software/autonomy/surface.py` and `types.py` (byte-unchanged — the `allow` → `execution="not_implemented"` contract already existed from C4), `src/jarvis/flight_software/flight_control/esc.py`, `.jes/state/engineering_state.json`.

---

## 7. Docs honesty confirmation (IC §6, §4 T9)

- README / PRIORIDAD / ARCHITECTURE / PLATFORM: ★ ACCEPT CLOSED @ tag **`v0.5.15`**
- Explicit **exists vs. impossible**: **exists** = opt-in armed allow-list + RejectAll default; **impossible** = flying, executed autonomy, hardware Safety.

---

## 8. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — MCU `.elf` (linked, bootable firmware — a separate scope from C16's library-only cross-compile), a real link (ELRS), or craft↔FS wiring. Not decided here.

---

## 9. Acceptance self-check against IC §7

- T1–T10: ✅ (see §4 table)
- Policy allow path proven: ✅ (§2, §4 T3/T6)
- Default RejectAll intact: ✅ (§0, §3, §5, byte-diff confirmed)
- No AllowAll: ✅ (§5, T8)
- No execute: ✅ (§5, T8 — `typing.get_args` proof)
- `0.5.15`: ✅
- Not FAIL conditions: default not made permissive (§0/§3) · no AllowAll shipped (§5) · Authority does not imply allow (§2 T5) · no `"executed"` appears (§5/T8) · no ESC/craft coupling (§5) · no "safe to fly" claim anywhere (§5/§7)
