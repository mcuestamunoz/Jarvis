# Implementation Report — Fase C capability schema + registry stub (`B1-fase-c-capability-registry-scaffold`)

**IC:** [`implementation_contract_fase_c_capability_registry_scaffold_b1.md`](implementation_contract_fase_c_capability_registry_scaffold_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-20
**Status:** Implemented, full suite green. Awaiting Cursor review + Engineer ACCEPT (tag `v0.5.0` on ACCEPT, per IC §9).

---

## 1. Package path chosen

`src/jarvis/capabilities/` (locked preference from IC §0.3):

```text
src/jarvis/capabilities/
├── __init__.py          # public exports
├── schemas.py            # CapabilityRecord, ProviderRecord, SkillRecord + enums
├── registry.py            # CapabilityRegistry + CapabilityRegistryError
└── data/
    └── default_registry.json   # {"capabilities": [], "providers": [], "skills": []}
```

No `flight_software/`, `vehicle_profiles/`, or any FC/runtime tree was created. Nothing outside `src/jarvis/capabilities/` and the docs/version files listed below was touched — Continuity, orchestrator IDLE, Board, and `library/` are all unchanged.

---

## 2. Schema field list vs IC

### `CapabilityRecord` (IC §1.1) — implemented exactly as specified

| Field | Type | Match |
|---|---|---|
| `id` | `str` | ✅ |
| `version` | `str` | ✅ |
| `provider_id` | `str \| None` | ✅ default `None` |
| `availability` | `CapabilityAvailability` enum | ✅ `stub` / `not_implemented` only — no `available`/`ready` |
| `requirements` | `list[str]` | ✅ default `[]` |
| `health` | `CapabilityHealth` enum | ✅ `unknown` only, default `unknown` |

`model_config = ConfigDict(extra="forbid")` — rejects any field not in this list, so no future accidental `execute`-shaped addition slips in unnoticed by tests.

### `ProviderRecord` (IC §1.2) — implemented exactly as specified

| Field | Type | Match |
|---|---|---|
| `id` | `str` | ✅ |
| `kind` | `Literal`-equivalent enum `ProviderKind` (`vehicle` \| `device`) | ✅ |
| `offered_capability_ids` | `list[str]` | ✅ default `[]`, empty OK |
| `health` | `CapabilityHealth` | ✅ `unknown` only |

### `SkillRecord` (IC §1.3) — shipped, zero instances loaded by default

| Field | Type | Match |
|---|---|---|
| `id` | `str` | ✅ |
| `version` | `str` | ✅ |
| `required_capability_ids` | `list[str]` | ✅ default `[]` |
| `availability` | same restricted enum as Capability | ✅ |

### Validation rules (IC §1.4) — all four implemented in `CapabilityRegistry.__init__`

1. Unknown `kind` → reject — enforced by Pydantic enum validation on `ProviderRecord.kind` (T5).
2. Duplicate ids on load → reject — `_reject_duplicate_ids()` runs separately for capabilities/providers/skills, raises `CapabilityRegistryError` (T3, T3b).
3. Dangling capability-id references (`offered_capability_ids` / `required_capability_ids`) → reject on load (locked policy) — checked against the loaded capability id set before the registry is considered constructed (T4, T4b).
4. No field named `execute`/`dispatch`/`command_esc` anywhere — confirmed by `model_fields` audit in `test_t9b_no_execute_or_dispatch_field_on_records`.

---

## 3. Registry API (IC §2) — implemented verbatim

```text
CapabilityRegistry
  .capabilities() -> list[CapabilityRecord]
  .providers() -> list[ProviderRecord]
  .skills() -> list[SkillRecord]
  .get_capability(id) -> CapabilityRecord | None
  .get_provider(id) -> ProviderRecord | None
  .providers_offering(capability_id) -> list[ProviderRecord]
  .load_default() -> CapabilityRegistry
```

Plus one addition not in the IC's normative list but explicitly allowed by §2's "Optional: load from a checked-in JSON" note: `CapabilityRegistry.from_dict(data)`, a `@classmethod` used internally by `load_default()` to parse the checked-in seed. It is not part of the locked API surface, is pure parsing (no I/O beyond the one file read `load_default()` already does), and does not add any execution capability.

No I/O to hardware, no threads, no asyncio loops anywhere in the module.

---

## 4. Confirmation: default registry empty; no execution path

- **H1 (default empty):** `CapabilityRegistry.load_default()` reads `src/jarvis/capabilities/data/default_registry.json`, which is checked in as literally `{"capabilities": [], "providers": [], "skills": []}`. `test_t1_load_default_is_empty` and `test_default_seed_file_is_honestly_empty` both assert this directly.
- **H2 (no product path claims flight/actuation available):** the `availability` enum (`CapabilityAvailability`) has exactly two members, `stub` and `not_implemented` — there is no `available`/`ready` value to assign in C1, so no record constructed against this schema can claim readiness. `test_t8_availability_enum_rejects_available` pins the enum's exact membership and confirms constructing a record with `availability="available"` or `"ready"` raises `pydantic.ValidationError`.
- **H3 (fixtures ≠ product default):** the test module's `_capability()`/`_provider()` helpers and the dangling-reference/duplicate-id tests construct in-memory records purely to exercise validation — none of them is wired into `load_default()` or any other product-facing path. `load_default()` only ever reads the checked-in empty JSON.
- **H4 (no orchestrator "runs a skill" hook):** the orchestrator, CLI, and MCP adapters were not touched by this Buy — `grep -rn "capabilities" src/jarvis/core/orchestrator.py` returns nothing. `jarvis.capabilities` is not imported anywhere outside its own package and its own test module.
- **H5 (docs say scaffold ≠ shipped):** stated explicitly in `README.md` ("What v0.5.0 includes"), `docs/ARCHITECTURE.md` (new §1b), and `docs/PLATFORM_CAPABILITY_VISION.md` §13.
- **No execution path:** `test_t9_no_public_method_executes_or_dispatches` audits every public `CapabilityRegistry` method name against `execute`/`dispatch`/`command_esc`/`actuat`/`run_skill` substrings; `test_t9b_no_execute_or_dispatch_field_on_records` does the same for every schema field name.

---

## 5. Tests run + counts

New module: `tests/test_fase_c_capability_registry_scaffold_b1.py` — **15 tests**, all passing, covering T1–T10 (plus two extra cases: T3b/T4b for provider vs skill symmetry, T8b for `health`, and a direct seed-file honesty check):

```text
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t1_load_default_is_empty PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t2_valid_capability_and_provider_are_accepted PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t3_duplicate_capability_id_is_rejected PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t3b_duplicate_provider_and_skill_ids_are_rejected PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t4_provider_offering_unknown_capability_is_rejected PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t4b_skill_requiring_unknown_capability_is_rejected PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t5_provider_kind_rejects_unknown_value PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t6_providers_offering_returns_expected_subset PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t7_missing_get_returns_none PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t8_availability_enum_rejects_available PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t8b_health_enum_only_offers_unknown PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t9_no_public_method_executes_or_dispatches PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t9b_no_execute_or_dispatch_field_on_records PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_t10_pyproject_version_is_0_5_0 PASSED
tests/test_fase_c_capability_registry_scaffold_b1.py::test_default_seed_file_is_honestly_empty PASSED
```

**T11 (full craft suite green):** `pytest -q` at repo root — **3181 passed, 1 skipped** (baseline was 3166 passed, 1 skipped before this Buy; delta is exactly the 15 new tests, no other file's pass/fail count moved).

Six pre-existing tests hardcoded the prior checkpoint version string (`"0.4.3"`) as a "this Buy doesn't bump the package version" pin, from earlier Buys that were explicitly forbidden from bumping. Since this IC explicitly authorizes and requires the `0.5.0` bump (§0 decision 10), those six assertions were updated to `"0.5.0"` — not weakened, just re-pinned to the new correct checkpoint, matching the same pattern used for the 0.4.1→0.4.2 bump earlier in Fase M:

- `tests/test_mission_power_w_b1.py::test_t10_package_checkpoint_version`
- `tests/test_geometry_prop_adapter_visor_x_b1.py::test_p6_library_and_version_untouched`
- `tests/test_library_cameras_seed_b1.py::test_t8_package_checkpoint_version`
- `tests/test_mission_vtx_identity_b1.py::test_t12_package_checkpoint_version`
- `tests/test_catalog_camera_power_w_b1.py::test_t8_package_checkpoint_version`
- `tests/test_bom_sku_resolved_cameras_b1.py::test_t5_package_checkpoint`

**T12 (report):** this document.

---

## 6. Version

`pyproject.toml` → `version = "0.5.0"`. `README.md` header banner updated to `v0.5.0` with a new "What v0.5.0 includes" section (scaffold blurb, honesty summary, explicit "not yet git-tagged" note). **Git tag `v0.5.0` not created by this report** — per IC §0 decision 10 / §9, the tag lands on Engineer ACCEPT (may be the same closeout commit or a follow-up, Engineer's call).

---

## 7. Files changed

**New:**
- `src/jarvis/capabilities/__init__.py`
- `src/jarvis/capabilities/schemas.py`
- `src/jarvis/capabilities/registry.py`
- `src/jarvis/capabilities/data/default_registry.json`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.4.3` → `0.5.0`
- `README.md` — header banner, new "What v0.5.0 includes" section, "Next" section reworded to C2
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C1 queue row updated to "landed, awaiting ★ ACCEPT"
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 pointer updated to landed state + report link
- `docs/ARCHITECTURE.md` — new §1b describing the `capabilities/` scaffold
- `tests/test_mission_power_w_b1.py`, `tests/test_geometry_prop_adapter_visor_x_b1.py`, `tests/test_library_cameras_seed_b1.py`, `tests/test_mission_vtx_identity_b1.py`, `tests/test_catalog_camera_power_w_b1.py`, `tests/test_bom_sku_resolved_cameras_b1.py` — re-pinned stale `0.4.3` version-checkpoint assertions to `0.5.0`

---

## 8. Residual — what C2 should pick up

- Intent/Safety gate stub (non-operational) per IC §6 out-of-scope table.
- A first non-empty *fixture-shaped* seed is explicitly NOT this Buy's job — C1 locked "empty registry + schemas + tests" as the product default; any future seed with real capability rows needs its own IC and must keep flight-related ids `not_implemented` or omitted per H2/H3.
- `flight_software/`, HAL/mixer/ESC, live Vehicle/Device runtime binding to workspace, and any Intent→actuator path remain untouched and unauthorized until their own ICs (C3+/C4/C5 per IC §6).
- Git tag `v0.5.0` still needs to be cut on Engineer ACCEPT.

---

## 9. Acceptance self-check against IC §8

- T1–T12: ✅ (T11/T12 are process gates, both satisfied — see §5 above)
- H1–H5: ✅ (see §4 above)
- No `flight_software/` created: ✅ (`find src -iname "flight_software" -o -iname "vehicle_profiles"` → empty)
- No craft regression: ✅ (3181 passed vs prior 3166 passed, delta = new tests only, 1 skipped unchanged)
- Version `0.5.0`: ✅
