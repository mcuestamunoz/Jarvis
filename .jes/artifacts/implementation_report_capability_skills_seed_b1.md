# Implementation Report — Capability Skills product seed (`B1-capability-skills-seed`, T5)

**Project:** Jarvis
**Date:** 2026-09-30
**Implementer:** Claude Code
**Contract:** [`implementation_contract_capability_skills_seed_b1.md`](implementation_contract_capability_skills_seed_b1.md)
**Parents:** T4 `B1-assistant-software-safety-bridge` — ★ **ACCEPT CLOSED @ `v0.6.12`** (commit `5627770`, tag `v0.6.12` present); T2 registry seed; C1 `SkillRecord` schema (shipped empty `skills: []` since `v0.5.0`); Engineer order: Skills seed first, then vehicle HOLD
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**
**Package:** `0.6.13` (bumped in `pyproject.toml`). **No git tag created** — `v0.6.13` is reserved for Engineer ACCEPT per IC §4/§6.

---

## 1. Files changed

**New:**
- `tests/test_capability_skills_seed_b1.py` — T1–T6, plus one extra direct-JSON check

**Modified:**
- `src/jarvis/capabilities/data/default_registry.json` — `skills: []` → the two rows from IC §1 verbatim (`skill.explain_concept`/`skill.project_status`, `version="0.6.13"`, `required_capability_ids` matching T0/T1's existing constants, both `availability="stub"`). Capabilities/providers blocks byte-unchanged
- `src/jarvis/capabilities/schemas.py` — `SkillRecord`'s docstring corrected: no longer claims the registry ships it "without any instances... by default" (now false); describes the two T5 rows instead. No field/validation change
- `src/jarvis/capabilities/registry.py` — module docstring extended: adds a T5 paragraph, and (while already touching this docstring) corrects two stale claims left over from T3/T4 that had never been synced here — the old text still said "`assistant_task.py` does not look up this registry before emitting a `Task`" (false since T3) with no mention of T4 at all. No code change — `registry.py`'s actual logic (`get_capability`/`get_provider`/`skills()`/reject-on-load) is untouched
- `src/jarvis/capabilities/__init__.py` — module docstring extended with a closing paragraph naming T3/T4/T5 (T3/T4 had never been documented here either); `SoftwareCapabilitySafetyGate` was already exported by T4, so no export-list change was needed this Buy
- `pyproject.toml` — `version = "0.6.12"` → `version = "0.6.13"`
- Nine files' own stale version-checkpoint assertions bumped `0.6.12` → `0.6.13` (IC §3: "bump stale `0.6.12` checkpoints forward"): `tests/test_assistant_defer_continuity_b1.py`, `tests/test_assistant_explain_task_b1.py`, `tests/test_assistant_software_safety_bridge_b1.py`, `tests/test_assistant_task_registry_coherence_b1.py`, `tests/test_capability_registry_product_fill_b1.py`, `tests/test_chat_explain_intercept_b1.py`, `tests/test_continuity_explain_topics_expand_b1.py`, `tests/test_fase_c_capability_registry_scaffold_b1.py`, `tests/test_fase_c_intent_safety_stub_b1.py`
- **39 Fase C isolation files** (the T2-era cascade, scripted-and-verified the same way T2 handled its own capabilities/providers cascade — see §2) — their shared `assert registry.skills() == []` sub-assertion (with its T2-explanatory comment) replaced by `assert {skill.id for skill in registry.skills()} == {"skill.explain_concept", "skill.project_status"}` with an updated comment naming both T2 and T5. Full file list: `test_fase_c_altitude_loop_b1.py`, `test_fase_c_attitude_controller_rung_b1.py`, `test_fase_c_attitude_estimation_rung_b1.py`, `test_fase_c_autonomy_executor_b1.py`, `test_fase_c_autonomy_surface_b1.py`, `test_fase_c_control_loop_tick_b1.py`, `test_fase_c_controlled_flight_sim_tip_b1.py`, `test_fase_c_cpp_esc_pwm_stub_b1.py`, `test_fase_c_cpp_flight_control_scaffold_b1.py`, `test_fase_c_cpp_mcu_cross_compile_b1.py`, `test_fase_c_cpp_mcu_freestanding_elf_b1.py`, `test_fase_c_cpp_unit_tests_b1.py`, `test_fase_c_crsf_byte_stream_b1.py`, `test_fase_c_crsf_dual_role_bridge_b1.py`, `test_fase_c_crsf_host_baud_b1.py`, `test_fase_c_crsf_host_serial_b1.py`, `test_fase_c_crsf_link_stub_b1.py`, `test_fase_c_crsf_stream_timeout_failsafe_b1.py`, `test_fase_c_dshot_encode_stub_b1.py`, `test_fase_c_esc_output_hal_b1.py`, `test_fase_c_esc_pwm_stub_rung_b1.py`, `test_fase_c_first_fc_rung_b1.py`, `test_fase_c_icm_register_client_b1.py`, `test_fase_c_imu_filtering_rung_b1.py`, `test_fase_c_mag_yaw_rung_b1.py`, `test_fase_c_mcu_flash_observable_b1.py`, `test_fase_c_mcu_spi_hal_stub_b1.py`, `test_fase_c_mcu_uart_hal_stub_b1.py`, `test_fase_c_mixer_rung_b1.py`, `test_fase_c_position_loop_b1.py`, `test_fase_c_radio_dual_role_b1.py`, `test_fase_c_rate_torque_bridge_b1.py`, `test_fase_c_rc_setpoint_b1.py`, `test_fase_c_safety_real_policy_b1.py`, `test_fase_c_silicon_cited_flash_map_b1.py`, `test_fase_c_sim_6dof_plant_b1.py`, `test_fase_c_spi_scripted_gyro_probe_b1.py`, `test_fase_c_spi_scripted_slave_b1.py`, `test_fase_c_step_failsafe_hold_ticks_b1.py`
- **Three "own" test files** with a dedicated (non-cascade) skills-empty assertion, hand-fixed individually (see §2): `tests/test_capability_registry_product_fill_b1.py` (T2's own T1, function renamed — its old name literally said `..._no_skills`), `tests/test_fase_c_capability_registry_scaffold_b1.py` (C1's own T1), `tests/test_fase_c_intent_safety_stub_b1.py` (C2's own T8)
- `src/jarvis/intelligence/README.md` — header Buys/Package lines updated to `0.6.13`; new short "Skills catalog (T5)" pointer paragraph added (per IC §0.10's exact requested wording), explicitly *not* a full section like T3/T4 got, since this Buy touches nothing in `jarvis.intelligence` itself
- `docs/PLATFORM_CAPABILITY_VISION.md` — §12 Placement line: T4 corrected to ★ ACCEPT CLOSED @ `v0.6.12`, new T5 clause added; §13 gained a new T5 paragraph
- `docs/system_map/CONNECTIONS.md` — **extended the existing T4 note** (corrected its status to ★ ACCEPT CLOSED @ `v0.6.12`) and **added a new paragraph directly below it** for T5, naming the cascade adaptation and cross-referencing this report. **No new `C-xxx`**, per IC §0 row 10
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD block and the T5 cola row updated from "★ AUTHORIZED · Claude" to "IMPLEMENTED · package `0.6.13`, awaiting Cursor review + Engineer ★ ACCEPT", with a link to this report added alongside the IC link

**Not touched (verified — see §5):** `src/jarvis/intelligence/assistant_task.py`, `src/jarvis/capabilities/safety.py`, `src/jarvis/core/orchestrator.py`, `src/jarvis/core/project_continuity.py`, `src/jarvis/capabilities/intent.py`, the `capabilities`/`providers` blocks of `default_registry.json`, `ontology/*.md` (only the pre-existing, unrelated `.obsidian/workspace.json` IDE-state diff remains, as in every prior Buy this session), `library/`, `jarvis.flight_software`, `jarvis.vehicle_profiles`.

---

## 2. Adapting the empty-skills cascade (IC §0 row 9) — scripted and verified, not weakened

**39-file cascade.** Before touching anything, I confirmed the exact shared block via `grep` sampling across several files, then wrote a small Python verification script that read every `tests/*.py` file and counted exact occurrences of the byte-identical 5-line block (4 comment lines + `assert registry.skills() == []`). It reported **39 files with exactly one match** and **3 files containing `skills() == []` but not matching that exact block** (the "own" files below) — confirming the block was uniform before I scripted a replacement, same verify-then-replace discipline T2 used for its own capabilities/providers cascade. The scripted replacement swapped the assertion for the honest new shape (`{skill.id for skill in registry.skills()} == {"skill.explain_concept", "skill.project_status"}`) and updated the comment to name both T2 and T5, leaving every other line in each file untouched. Post-replacement, `grep -rn "skills() == \[\]" tests/` returns nothing anywhere in the repo.

**Three "own" files**, fixed individually since each encoded a slightly different claim:
- `test_capability_registry_product_fill_b1.py::test_t1_load_default_has_exactly_two_available_capabilities_no_skills` — the function *name itself* asserted "no_skills," now false. Renamed to `test_t1_load_default_has_exactly_two_available_capabilities` (dropping the now-false half), removed the `assert registry.skills() == []` line, and added a docstring explaining the split: this test now scopes to exactly what T2 itself changed (`capabilities()`); the new `tests/test_capability_skills_seed_b1.py` is the dedicated authority on `skills()`.
- `test_fase_c_capability_registry_scaffold_b1.py::test_t1_load_default_returns_product_seed` — previously `assert registry.capabilities() != [] / providers() != [] / skills() == []` (proving `load_default()` no longer returns the C1-era all-empty registry). Changed the third assertion to `!= []` too, so the test's own stated purpose ("no longer C1-era empty") stays true and complete rather than half-true.
- `test_fase_c_intent_safety_stub_b1.py::test_t8_capability_registry_default_still_descriptive_only` — the docstring's central claim was "skills stay empty... unchanged since C2," now false. Removed the `assert registry.skills() == []` line and rewrote the docstring to describe what the test still actually guarantees (the registry stays purely descriptive — no dispatcher method), pointing at T5's own test file for the skills shape. The descriptive-only/no-dispatcher assertion itself (the test's real remaining purpose) is untouched.

None of the 42 changed files had any isolation/no-dispatch/no-craft-import assertion weakened — every fix either corrected a now-false claim to the new honest shape or removed a claim that a separately-authorized later Buy (T5, this one) explicitly superseded, matching the same "correction, not weakening" standard applied to two prior Buys' own tests earlier in this series (T3's fix to T2's `test_t6b`, T4's fix to T3's `test_gate_does_not_touch_availability_or_providers`).

---

## 3. Manual verification

Live against the checked-in seed, before writing tests:

```text
skills: [('skill.explain_concept', STUB, ['ontology.explain']),
         ('skill.project_status',  STUB, ['engineering.continuity'])]
caps:      [('ontology.explain', AVAILABLE, 'provider.ontology_explain'),
            ('engineering.continuity', AVAILABLE, 'provider.engineering_continuity')]
providers: [('provider.ontology_explain', SOFTWARE),
            ('provider.engineering_continuity', SOFTWARE)]
```

Capabilities/providers rows are byte-identical to the T2/T3/T4-era seed — confirmed both by this live read and by `git diff` on the seed file showing only the `skills` array changed.

Reject-on-load, re-verified with a hand-built dangling skill:

```text
CapabilityRegistry(capabilities=[<ontology.explain>], skills=[<skill requiring 'unknown.cap'>])
  -> CapabilityRegistryError: skill 's1' requires unknown capability id 'unknown.cap'
```

---

## 4. Tests

`tests/test_capability_skills_seed_b1.py`:

| ID | Assert | Result |
|---|---|---|
| T1 | `load_default().skills()` has exactly the two ids; both `availability == stub` | PASS |
| T2 | Each skill's `required_capability_ids` resolve via `get_capability` (caps still present) | PASS |
| T3 | Capabilities/providers counts and ids unchanged vs T2 seed | PASS |
| T4 | A skill requiring an unknown capability still raises `CapabilityRegistryError` on construction | PASS |
| T5 | `CapabilityRegistry` still has no `execute`/`dispatch`/`run_skill`-shaped public method name | PASS |
| T6 | `pyproject.toml` reads `0.6.13` | PASS |
| (extra) | The checked-in JSON's `skills` array matches IC §1's normative seed verbatim, independent of the loader | PASS |

```text
$ python3 -m pytest tests/test_capability_skills_seed_b1.py -v
7 passed
```

Regression — T0–T4 + Safety + C1/C2 suites together:

```text
$ python3 -m pytest tests/test_capability_skills_seed_b1.py \
    tests/test_assistant_software_safety_bridge_b1.py \
    tests/test_assistant_task_registry_coherence_b1.py \
    tests/test_assistant_explain_task_b1.py \
    tests/test_assistant_defer_continuity_b1.py \
    tests/test_capability_registry_product_fill_b1.py \
    tests/test_fase_c_capability_registry_scaffold_b1.py \
    tests/test_fase_c_intent_safety_stub_b1.py \
    tests/test_fase_c_safety_real_policy_b1.py \
    tests/test_fase_c_safety_sim_policy_b1.py -q
93 passed, 2 failed
```

The 2 failures are the same pre-existing, out-of-scope stale version-checkpoints as before this Buy (`0.5.15`/`0.5.42`) — not `0.6.x`, not touched by this IC's "bump stale `0.6.12` checkpoints" instruction.

Full suite:

```text
$ python3 -m pytest -q
52 failed, 3808 passed, 9 skipped
```

All 52 failures are the identical pre-existing stale-version set as before this Buy (`0.5.1`–`0.5.44`, `0.6.1`–`0.6.5`); 3808 passed is +7 over the T4 baseline (3801), exactly the new T5 test file's count. None of the 39 adapted Fase C files, nor any of the three hand-fixed "own" files, appear among the failures.

---

## 5. Non-edits verification

```text
$ git diff --stat -- src/jarvis/intelligence/assistant_task.py src/jarvis/capabilities/safety.py \
    src/jarvis/core/orchestrator.py src/jarvis/core/project_continuity.py \
    src/jarvis/capabilities/intent.py
(empty)
```

Zero diff on all five — confirming IC §2 ("Do not modify `assistant_task.py`, `safety.py` gate logic, orchestrator, or Continuity ranking") and IC's own Task-path guarantee. The `capabilities`/`providers` blocks of `default_registry.json` are also byte-identical to their T2/T3/T4-era content — only the `skills` array changed, confirmed via direct JSON diff during editing and re-asserted by T3 of this Buy's own test file.

---

## 6. Git-state note: T4 landed mid-session (same pattern as T2/T3 during their successor turns)

At authorization time, `docs/IMPLEMENTATION_TASKS.md` already showed T4 as `✅ ★ ACCEPT CLOSED · tip v0.6.12` and T5 as `★ AUTHORIZED · Claude` — the Engineer/Cursor side had landed and tagged T4 (`v0.6.12`, commit `5627770`) before this turn began, continuing the same concurrent-write pattern seen during the T3 and T4 turns. I built this Buy's docs updates on top of that already-updated state (see §1) rather than re-deriving or overwriting it. No mid-turn HEAD movement was observed this time — `git log`/`git tag` stayed stable throughout this Buy's implementation.

---

## 7. IC acceptance checklist self-check

- [x] Skills seed §1 loaded via `load_default` (verified live, §3; tested T1/T2/extra)
- [x] Skills are `stub`; Task/Safety paths untouched (tested T1; §5 confirms zero diff on `assistant_task.py`/`safety.py`)
- [x] Empty-skills test cascade adapted, not weakened (§2 — 39 scripted-and-verified + 3 hand-fixed, all correction not weakening)
- [x] Tests T1–T6 · report (this document) · docs (README pointer, PLATFORM §13, CONNECTIONS, PRIORIDAD) · package `0.6.13`
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.13`** — pending, not claimed here

**No ACCEPT claim.**
