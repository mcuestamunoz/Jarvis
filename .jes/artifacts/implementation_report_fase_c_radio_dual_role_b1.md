# Implementation Report — Fase C Radio dual-role ingress stub (`B1-fase-c-radio-dual-role`)

**IC:** [`implementation_contract_fase_c_radio_dual_role_b1.md`](implementation_contract_fase_c_radio_dual_role_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** ★ ACCEPT CLOSED @ **`v0.5.3`** (C4+C5 one block; Cursor review PASS — see [review](implementation_review_fase_c_radio_dual_role_b1.md) · [docs truth-sync](engineer_note_docs_truth_sync_fase_c_2026_09_20.md)).

---

## 1. Package path

Added to the existing `src/jarvis/capabilities/` tree (IC §1 lock — no new top-level package):

```text
src/jarvis/capabilities/
├── intent.py          # C2 — unchanged behavior; RadioIntentAdapter docstring cross-references radio.py
├── safety.py           # C2 — gained optional SafetyRequest.authority_signal_id (traceability only)
├── radio.py             # NEW — RadioStubFrame, RadioDualRoleResult, SimulatedRadioIngress, describe_dual_role
└── __init__.py         # exports the new radio public types
```

No `src/jarvis/radio/` or `flight_software/radio/` was created. `flight_control/` and `vehicle_profiles/` (C3) and `flight_software/autonomy/` (C4) are untouched.

---

## 2. Types implemented vs IC §2

| Type | IC ref | Match |
|---|---|---|
| `RadioStubFrame` (`id`, `role`, `intent_text`, `authority_kind`, `authority_payload`, `notes`) | §2.1 | ✅ Pydantic, `extra="forbid"`, no `channels: list[int]` raw RC map. Shape invariants enforced by a `model_validator`: `role="intent"` requires non-empty `intent_text` and forbids `authority_kind`; `role="authority"` requires `authority_kind` and forbids `intent_text`; `role="both"` requires both |
| `RadioDualRoleResult` (`frame_id`, `intent`, `authority`) | §2.2 | ✅ invariants enforced by a `model_validator` on the result itself (defense-in-depth beyond the frame-shape check): at least one of `intent`/`authority` must be set — a degenerate empty result cannot be constructed |
| `SimulatedRadioIngress.ingest(frame) -> RadioDualRoleResult` | §2.3 | ✅ builds `Intent(source=RADIO, ...)` and/or `AuthoritySignal(source="radio", ...)` per `frame.role`; no socket/serial/file I/O anywhere in the class |
| `describe_dual_role(result) -> str` | §2.4 | ✅ pure debug string, no Safety call |
| `RadioIntentAdapter.parse(...)` | §2.5 | ✅ **unchanged** — still raises `NotImplementedError` with `"not_implemented"` in the message. Its docstring now cross-references `SimulatedRadioIngress` so readers don't mistake the two |
| `SafetyRequest.authority_signal_id: str \| None = None` | §2.6 | ✅ added, optional, traceability-only; `RejectAllSafetyGate` still always rejects regardless of this field (T6) |

---

## 3. Integration rules (IC §3) — confirmed unchanged

- C2 `Intent` / `AuthoritySignal` — reused directly, no parallel/duplicate types created.
- C4 autonomy — `radio.py` never imports `jarvis.flight_software.autonomy`; no automatic `submit_command` call from `SimulatedRadioIngress.ingest`.
- C3 `flight_control` — untouched, no import.
- `CapabilityRegistry.load_default()` — untouched, still empty (0/0/0).
- `RejectAllSafetyGate` / `default_safety_gate()` — untouched; still the only shipped factory, still always `reject`, confirmed even with `authority_signal_id` set (T6).

---

## 4. Tests run + counts

New module: `tests/test_fase_c_radio_dual_role_b1.py` — **17 tests**, all passing, covering IC §4 T1–T10 plus seven extra cases (frame-shape invariant edge cases, no-raw-channel-map field check, empty-result rejection, and the debug helper):

```text
test_t1_intent_role_frame_yields_intent_only PASSED
test_t2_authority_role_frame_yields_authority_only PASSED
test_t3_both_role_frame_yields_both_as_distinct_types PASSED
test_t4_radio_intent_adapter_still_not_implemented PASSED
test_t5_no_decode_or_driver_shaped_public_methods_in_radio_module PASSED
test_t6_default_safety_still_rejects_with_authority_signal_id_set PASSED
test_t7_no_cpp_or_cmake_under_capabilities PASSED
test_t8_radio_not_imported_by_orchestrator_or_craft_paths PASSED
test_t9_capability_registry_default_still_empty PASSED
test_t10_pyproject_version_is_0_5_3 PASSED
test_radio_stub_frame_rejects_missing_intent_text_for_intent_role PASSED
test_radio_stub_frame_rejects_missing_authority_kind_for_authority_role PASSED
test_radio_stub_frame_rejects_intent_text_on_authority_only_role PASSED
test_radio_stub_frame_rejects_authority_kind_on_intent_only_role PASSED
test_radio_stub_frame_has_no_raw_channel_map_field PASSED
test_radio_dual_role_result_rejects_empty_result PASSED
test_describe_dual_role_is_pure_and_readable PASSED
```

**T11 (full craft suite green):** `pytest -q` at repo root — **3236 passed, 1 skipped** (baseline before this Buy was 3219 passed, 1 skipped; delta is exactly the 17 new tests, no other file's pass/fail count moved).

**T12 (report confirms dual-role + no live ELRS + no Safety bypass):** see §5 below.

Ten pre-existing tests hardcoded the prior checkpoint version string (`"0.5.2"`) as a version-pin assertion. Since this IC explicitly authorizes and requires the `0.5.3` bump (§0 decision 10, "assumes C4 ACCEPT @ `0.5.2`" — the version bump itself is authorized at implementation time regardless of when the C4 tag is actually cut), those ten assertions were re-pinned to `"0.5.3"`:

- `tests/test_mission_power_w_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_vtx_identity_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`

---

## 5. Honesty / forbidden confirmation (IC §5)

| Rule | Status | Evidence |
|---|---|---|
| CRSF/ELRS binary decode presented as product | ✅ absent | `RadioStubFrame` has no `channels: list[int]` field or any byte-level field; `radio.py`'s module docstring states explicitly it never decodes CRSF/ELRS/SBUS |
| Radio → motors / mixer | ✅ absent | Zero import of `flight_software` (autonomy or flight_control) from `radio.py` |
| Making `RadioIntentAdapter` silently succeed | ✅ unchanged | Still unconditionally raises `NotImplementedError("radio intent ingress is not_implemented in C2")` (T4) |
| Authority implies Safety `allow` | ✅ impossible | `default_safety_gate()` still `RejectAllSafetyGate`, confirmed to reject even with `authority_signal_id` set (T6); no code path reads `AuthoritySignal.kind` to influence a gate decision |
| Collapsing kill/override into `Skill.execute` | ✅ absent | No `Skill`/`execute` symbol referenced anywhere in `radio.py` |
| CLI "stick" simulation wired to Continuity | ✅ absent | Zero references to `capabilities.radio` in `src/jarvis/core/` or `src/jarvis/adapters/` (T8) |
| Dual-role (Intent and/or Authority, never collapsed) | ✅ confirmed | `RadioDualRoleResult.intent` and `.authority` are distinct typed fields (`Intent` vs `AuthoritySignal`); T3 asserts `type(result.intent) is not type(result.authority)` |
| No live ELRS | ✅ confirmed | No serial/USB/SPI/socket I/O anywhere in `SimulatedRadioIngress`; `radio.py` docstring states this explicitly |
| No Safety bypass | ✅ confirmed | `SimulatedRadioIngress.ingest` never calls a `SafetyGate` at all — it only builds data; any Safety check for a resulting `Intent` still goes through `run_intent_through_safety` (C2), unchanged |

---

## 6. Files changed

**New:**
- `src/jarvis/capabilities/radio.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `.jes/artifacts/implementation_report_fase_c_radio_dual_role_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.2` → `0.5.3`
- `src/jarvis/capabilities/__init__.py` — exports `RadioStubFrame`, `RadioDualRoleResult`, `SimulatedRadioIngress`, `describe_dual_role`; package docstring extended to mention C5 and the "authority never implies allow" rule
- `src/jarvis/capabilities/intent.py` — `RadioIntentAdapter`'s docstring now cross-references `SimulatedRadioIngress` (no behavior change)
- `src/jarvis/capabilities/safety.py` — `SafetyRequest` gained the optional `authority_signal_id` field (no behavior change to any gate)
- `docs/ARCHITECTURE.md` — §1b extended with a C5 paragraph (title updated to "C1+C2+C5")
- 10 test files — re-pinned stale `0.5.2` version-checkpoint assertions to `0.5.3` (listed in §4 above)

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/flight_software/*`, `src/jarvis/vehicle_profiles/*`, `.jes/state/engineering_state.json`.

**Process note (honesty-critical):** `docs/IMPLEMENTATION_TASKS.md`, `docs/PLATFORM_CAPABILITY_VISION.md` §13, and `README.md` were left as already corrected by Cursor's own [docs truth-sync](engineer_note_docs_truth_sync_fase_c_2026_09_20.md) pass — that sync caught and fixed an earlier over-eager edit (this session prematurely marked C4 "ACCEPT CLOSED @ tag `v0.5.2`" before any such tag existed in git). Re-editing on top of that correction would have re-introduced the same class of error, so those three files were intentionally left untouched by this report.

---

## 7. Residual — what comes next

- Engineer ★ ACCEPT of C4 → commit + tag `v0.5.2` (still pending, per the truth-sync note).
- Cursor review of this C5 Buy → Engineer ACCEPT → tag `v0.5.3`.
- Further FC rungs, a real (non-`RejectAll`) Safety policy, and native/C++ stacks remain separate future ICs — none of them are authorized by this Buy.

---

## 8. Acceptance self-check against IC §7

- T1–T12: ✅ (T11/T12 are process gates, both satisfied — see §4/§5 above)
- Dual-role types work in sim: ✅ (T1–T3)
- `RadioIntentAdapter` still refuses: ✅ (T4)
- RejectAll unchanged: ✅ (T6)
- No ELRS drivers: ✅ (T5, T7)
- Version `0.5.3`: ✅ (T10)
- No craft coupling: ✅ (T8)
