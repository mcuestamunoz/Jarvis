# Implementation Report — Fase C autonomy command surface (`B1-fase-c-autonomy-surface`)

**IC:** [`implementation_contract_fase_c_autonomy_surface_b1.md`](implementation_contract_fase_c_autonomy_surface_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** ★ ACCEPT CLOSED @ **`v0.5.3`** (C4+C5 one block; no `v0.5.2` tag — see [docs truth-sync](engineer_note_docs_truth_sync_fase_c_2026_09_20.md)).

---

## 1. Package path

Created exactly as locked in IC §1, as a new sibling of `flight_control/` under the existing `flight_software/` tree (C3 forbade this until now):

```text
src/jarvis/flight_software/
├── flight_control/        # C3 — unchanged, no new rung
└── autonomy/               # NEW — C4
    ├── __init__.py         # honest docstring: scaffold; Safety-gated; != live autonomy
    ├── types.py             # AutonomyVerb, AutonomyCommand, AutonomySubmissionResult
    ├── surface.py            # propose_command / submit_command
    └── smoke.py               # smoke_hold_and_land()
```

No `flight_software/autonomy/executor.py` was created. `flight_control/` and `vehicle_profiles/` were not modified beyond a one-line cross-reference in `flight_software/__init__.py`'s package docstring (updated to mention the new `autonomy/` sibling — see §6).

---

## 2. Types implemented vs IC §2

| Type | IC ref | Match |
|---|---|---|
| `AutonomyVerb` (`str` Enum: `TAKEOFF`/`HOLD`/`GO_TO`/`FOLLOW`/`RETURN_HOME`/`LAND`/`PATROL`) | §2.1 | ✅ full C0 starter set |
| `AutonomyCommand` (`id`, `verb`, `intent_id`, `params`, `created_at`) | §2.2 | ✅ Pydantic, `extra="forbid"`; `params: dict[str, str]` default `{}`, opaque data only |
| `AutonomySubmissionResult` (`command_id`, `verb`, `safety`, `execution`) | §2.3 | ✅ `safety: SafetyDecision` embedded (imported from `jarvis.capabilities.safety`); `execution: Literal["not_attempted", "not_implemented"]` — **`"executed"` is not a valid value of this type**, so no shipped path can even construct it |

---

## 3. APIs implemented vs IC §2.4/§2.5

- `propose_command(verb, *, intent_id=None, params=None) -> AutonomyCommand` — pure constructor, does not call Safety.
- `submit_command(command, gate) -> AutonomySubmissionResult` —
  1. builds `SafetyRequest(intent_id=command.intent_id, action_id=f"autonomy:{command.verb.value}:{command.id}")`;
  2. calls `gate.evaluate(request)`;
  3. if `decision.outcome != "allow"` → returns `execution="not_attempted"` (the locked-preferred value, per IC §2.3's "preferred");
  4. the `outcome == "allow"` branch is only reachable with a test-local fake gate (no shipped gate ever returns `allow`) and still returns `execution="not_implemented"`, never `"executed"`.
- **Lock confirmed:** there is no function named `execute_hold`/`run_land`/`dispatch_autonomy` or similar anywhere in `src/` that skips Safety — grep-verified.
- `smoke_hold_and_land(gate=None) -> list[AutonomySubmissionResult]` (IC §2.5, optional, shipped in `src/`) — proposes `HOLD` then `LAND`, submits each through `default_safety_gate()` unless a gate is given, and asserts both results are `reject`/`not_attempted` before returning.

---

## 4. Integration with C1–C3 (IC §3) — confirmed unchanged

- `RejectAllSafetyGate` / `default_safety_gate()` — untouched, still the only shipped factory.
- `flight_control` HAL/IMU — untouched; `autonomy/` never calls `read_imu()` or any `flight_control` symbol as a substitute for "holding."
- `vehicle_profiles` — untouched; no new profile added, no import from `autonomy/`.
- `CapabilityRegistry.load_default()` — untouched, still empty (0/0/0); no `autonomy` capability record added.
- Craft / orchestrator — zero imports of `jarvis.flight_software.autonomy` (or the broader `jarvis.flight_software`) from `src/jarvis/core/` or `src/jarvis/adapters/` — grep-verified with the precise substring `flight_software.autonomy` (a broader ad-hoc `autonomy` grep during verification surfaced only unrelated craft vocabulary — `autonomy_min`/"autonomía objetivo" mission parameters that predate this Buy and are unrelated to this package).

---

## 5. Tests run + counts

New module: `tests/test_fase_c_autonomy_surface_b1.py` — **13 tests**, all passing, covering IC §4 T1–T10 plus three extra cases (smoke-helper contract, extra-field rejection, docstring-amendment presence):

```text
test_t1_propose_hold_command PASSED
test_t2_submit_hold_rejects_under_default_gate PASSED
test_t3_submit_land_rejects_under_default_gate PASSED
test_t4_every_verb_can_be_proposed PASSED
test_t5_no_actuator_shaped_public_methods_under_autonomy PASSED
test_t6_allow_all_gate_absent_and_default_still_reject PASSED
test_t7_local_allow_gate_still_never_executed PASSED
test_t8_capability_registry_default_still_empty PASSED
test_t9_pyproject_version_is_0_5_2 PASSED
test_t10_autonomy_not_imported_by_orchestrator_or_craft_paths PASSED
test_smoke_hold_and_land_uses_default_reject_gate PASSED
test_autonomy_command_rejects_unknown_extra_field PASSED
test_autonomy_package_docstring_carries_python_scaffold_amendment PASSED
```

**T11 (no new `.cpp`/CMake under `flight_software/`/`vehicle_profiles/`):** already covered without duplication — `tests/test_fase_c_first_fc_rung_b1.py::test_no_cpp_or_cmake_tree_created` walks the whole `flight_software/` tree recursively (via `rglob("*")`), so it now also covers the new `autonomy/` subpackage. Re-ran it explicitly after adding `autonomy/`: PASSED.

**T12 (full craft suite green):** `pytest -q` at repo root — **3219 passed, 1 skipped** (baseline before this Buy was 3206 passed, 1 skipped; delta is exactly the 13 new tests, no other file's pass/fail count moved).

**T13 (report confirms H-locks + "surface != live autonomy" + C++ FC honesty):** see §7 below.

Nine pre-existing tests hardcoded the prior checkpoint version string (`"0.5.1"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.2` bump (§0 decision 10), those nine assertions were re-pinned to `"0.5.2"`:

- `tests/test_mission_power_w_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`

---

## 6. Files changed

**New:**
- `src/jarvis/flight_software/autonomy/__init__.py`
- `src/jarvis/flight_software/autonomy/types.py`
- `src/jarvis/flight_software/autonomy/surface.py`
- `src/jarvis/flight_software/autonomy/smoke.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `.jes/artifacts/implementation_report_fase_c_autonomy_surface_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.1` → `0.5.2`
- `src/jarvis/flight_software/__init__.py` — package docstring updated to describe the new `autonomy/` sibling (still "Python scaffold / sim only — production flight_control runtime is C++ (future IC)"); the stale "no autonomy verbs" sentence was corrected to describe the non-operational command surface instead
- `README.md` — header banner, new "What v0.5.2 includes" section, "Next" section reworded to C5
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C4 queue row updated to "landed, awaiting ★ ACCEPT"; suite count 3206 → 3219
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a C4 block; corrected the C3 block's stale "autonomy (C4+)" qualifier now that C4 has landed
- `docs/ARCHITECTURE.md` — new §1d describing `flight_software/autonomy/`
- 9 test files — re-pinned stale `0.5.1` version-checkpoint assertions to `0.5.2` (listed in §5 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/flight_control/*`, `src/jarvis/vehicle_profiles/*` (content), `.jes/state/engineering_state.json`.

---

## 7. Honesty / forbidden confirmation (IC §5)

| Rule | Status | Evidence |
|---|---|---|
| `execution="executed"` on any shipped path | ✅ forbidden and unreachable | `ExecutionState = Literal["not_attempted", "not_implemented"]` — `"executed"` cannot even be constructed as a valid value |
| Default Safety `allow` | ✅ unchanged | `default_safety_gate()` still returns `RejectAllSafetyGate` (T6) |
| Skipping Safety on submit | ✅ impossible | `submit_command` always calls `gate.evaluate(...)` before building any result |
| Calling `SimulatedImuHal` as "holding" | ✅ never happens | `autonomy/` has zero imports from `flight_control` |
| CLI/Board "land now" wiring | ✅ absent | T10 — zero references to `flight_software.autonomy` in `core/`/`adapters/` |
| Marking autonomy capability available | ✅ absent | `CapabilityRegistry.load_default()` unchanged, still empty (T8) |
| C++/CMake tree | ✅ absent | `test_no_cpp_or_cmake_tree_created` (extended coverage, still passes) |
| "Surface != live autonomy" | ✅ stated explicitly | `autonomy/__init__.py` docstring: "This package proposes commands, it does not fly, arm, hold, or land anything"; same phrase repeated in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION |
| C++ FC honesty (continuing C3 amendment) | ✅ carried forward | `autonomy/__init__.py`, `types.py`, `surface.py`, and `smoke.py` all carry "Python scaffold / sim only — production flight_control runtime is C++ (future IC)" |

---

## 8. Residual — what C5 should pick up

- Radio/ELRS Authority + Intent (per C0 attack order, per the IC's own handoff §8).
- A real (non-`RejectAll`) Safety policy remains unauthorized — C4 still ships only the always-reject default.
- No actuator, mixer, or ESC exists anywhere yet — those remain their own future rungs under `flight_control/`.
- Git tag: `v0.5.2` still needs to be cut on Engineer ACCEPT.

---

## 9. Acceptance self-check against IC §7

- T1–T13: ✅ (T12/T13 are process gates, both satisfied — see §5/§7 above)
- HOLD/LAND submit always reject under default gate: ✅ (T2, T3)
- No `executed`: ✅ (type-level impossible)
- No craft coupling: ✅ (T10)
- Version `0.5.2`: ✅ (T9)
- FC rung unchanged: ✅ (`flight_control/` files untouched)
- No C++ tree: ✅ (extended `test_no_cpp_or_cmake_tree_created`)
