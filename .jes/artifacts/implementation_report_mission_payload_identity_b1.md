# Implementation Report — Mission payload identity rules (`B1-mission-payload-identity`)

**IC:** `implementation_contract_mission_payload_identity_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-15
**Checkpoint:** package `0.4.1` (unchanged) · suite **2945 passed, 1 skipped** (was 2938 + 1) · UI unaffected (no UI files touched)

---

## 1. Scope delivered

Exactly the locked scope — identity-only `ComponentRule`s for `cameras` and `radio_module`, unlocking SYSTEM_DEFINITION's B-path for `perception`/`communication`. No catalog seeds, no mirrored mass/geometry, no firmware, no version bump, no `workspace/` mutation (tests-only, default per lock #13 — no ★ Path D requested).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/system_architecture_catalog.py` | `BLOCK_TO_COMPONENTS["perception"]` narrowed from `["cameras", "lidar"]` to `["cameras"]`, with a comment documenting the lidar debt (lock #3). `communication` unchanged. |
| `src/jarvis/domains/aerial.py` | Added `CAMERA_MODEL_MAP` (`runcam`/`caddx`/`foxeer`/`gopro`/`insta360`), `extract_camera_properties`, `_camera_completeness`; `RADIO_MODEL_MAP` (`expresslrs`/`elrs`/`crossfire`/`frsky`), `extract_radio_properties`, `_radio_completeness`. Appended two `ComponentRule`s to `aerial_registry` (now 9 rules, was 7). |
| `src/jarvis/core/system_definition_session.py` | Step-1 (Option B) example copy changed from `'batería', 'frame', 'control'` to `'batería', 'frame', 'cámara'` (lock #11, since `cámara` is now resolvable). |
| `tests/test_system_definition_session.py` | Flipped perception/communication tests to accept-path; added a dedicated `B1-mission-payload-identity` test block (T1–T7 below); `payload` refuse test kept as a standalone (`test_t4_mode_b_payload_still_refused_no_stub`). |
| `tests/test_aerial_domain.py`, `tests/test_control_component.py` | Registry-size assertions bumped 7 → 9 (both pre-existing tests literally count `len(aerial_registry)`; this is the expected, intended growth from lock #6, not a weakened test). |

## 3. Behavior changed

- `block_components_are_resolvable("perception")` and `("communication")` now return `True` (were `False`).
- SYSTEM_DEFINITION mode B: `"cámara"` / `"visión artificial"` / `"comunicación"` now **accept** and create a `cameras` / `radio_module` stub instead of refusing. `payload` / `manipulation` / `actuation` / `transmission` are unaffected — still refused (no `ComponentRule` for any of their keys).
- Free-text component inference (`infer_component`, used by the component-description wizard and IDLE catalog/description paths): a phrase naming a recognised camera or radio brand/protocol now resolves to `suggested_key="cameras"`/`"radio_module"` at completeness `medium`; an unrecognised bare `"cámara"`/`"radio"` resolves to the same key at `low` with a hint, instead of falling through to `generic_component`.
- `BLOCK_ALIASES["lidar"] = "perception"` is untouched — a user can still say "lidar" and it still resolves to the `perception` block name, but `perception`'s component-key expansion no longer includes `lidar`, so no `lidar` component key is ever created (lock #3, named debt).

## 4. Empirical verification (before writing tests)

Ran live against the actual `SystemDefinitionSession`/`infer_component` (not mocked):

```
block_components_are_resolvable('perception')    → True
block_components_are_resolvable('communication') → True
payload/manipulation/actuation/transmission      → all False (unchanged)
BLOCK_TO_COMPONENTS['perception']                → ['cameras']

infer_component('cámara RunCam')  → suggested_key=cameras, type=perception, medium, {model: runcam}
infer_component('cámara')         → suggested_key=cameras, low, hint=['modelo de cámara...']
infer_component('radio ELRS')     → suggested_key=radio_module, type=communication, medium, {model: elrs}
infer_component('receptor Crossfire') → suggested_key=radio_module, medium, {model: crossfire}
infer_component('radio')          → suggested_key=radio_module, low, hint=[...]
infer_component('visión artificial') → suggested_key=cameras, low  (keyword opens the rule, no brand recognised)
```

Full SYSTEM_DEFINITION session smoke (mode B): `cámara` → "Bloque 'perception' añadido"; `comunicación` → "Bloque 'communication' añadido"; `payload` → refused with the existing gate message; after `listo`, `design_properties.components` contained `{battery, cameras, esc, flight_controller, frame, motors, propellers, radio_module, sensors}` — no `lidar`, no `payload_bay`.

## 5. Tests

### Added / rewritten (`tests/test_system_definition_session.py`)

| ID | Test | Covers |
|---|---|---|
| T1 | `test_mip_t1_perception_and_communication_are_resolvable` | `block_components_are_resolvable` True for both |
| T2 | `test_t1_dead_blocks_are_not_resolvable` (updated) | payload/manipulation/actuation/transmission still False |
| T3 | `test_mission_payload_identity_camara_accepted_no_lidar_stub`, `test_answer_b_then_vision_then_listo` (rewritten) | Mode B accept path, no lidar stub |
| T4 | `test_mission_payload_identity_comunicacion_accepted`, `test_t4_mode_b_payload_still_refused_no_stub` | communication accepts, payload still refused |
| T5 | `test_mission_payload_identity_camera_freetext_model_reaches_medium`, `test_mission_payload_identity_bare_camara_stays_low_with_hint` | Free-text identity ladder for cameras |
| T6 | `test_mission_payload_identity_radio_freetext_model_reaches_medium`, `test_mission_payload_identity_bare_radio_stays_low_with_hint` | Free-text identity ladder for radio |
| T7 | `test_mission_payload_identity_never_invents_geometry_or_mass` | Digits in the message (`"25mm 15g"`) never become `length_mm`/`mass_g`/etc. |
| — | `test_step1_prompt_examples_are_all_resolvable` (updated) | Example copy now advertises `cámara` (resolvable); `payload` never advertised |

### Updated (pre-existing, unrelated files — registry size only)

- `tests/test_aerial_domain.py::test_aerial_registry_has_four_rules` — `7` → `9`
- `tests/test_control_component.py::test_aerial_registry_has_seven_rules` — `7` → `9`

### Executed

```
python -m pytest tests/test_system_definition_session.py -q  → 57 passed
python -m pytest -q                                           → 2945 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected by this Buy).

## 6. Keyword tuning notes (lock #6)

- **Cameras:** `("camara", "cámara", "camaras", "cámaras", "camera", "fpv", "vision", "visión")`. Kept `vision`/`visión` bare per Engineer's own suggested tuple in the IC, accepting the (Spanish) substring risk against words like `previsión` — not expected to appear in component-declaration phrases in practice.
- **Radio:** `("radio", "elrs", "expresslrs", "crossfire", "telemetria", "telemetría", "telemetry", "emisor", "receptor")`. Deliberately **excluded bare `"rx"`** from the IC's suggested list — `ComponentRule.matches` is a plain substring check (not word-boundary), and a 2-character token risks over-matching inside unrelated words. `"receptor"` covers the Spanish RX use case without that risk; documented inline in `aerial.py`.
- Both rules are appended **after** the existing `sensors` rule in `aerial_registry` (first-match-wins), so a phrase containing `"sensor"` (e.g. "sensor de cámara") still matches the `sensors` rule first — never stolen by the new camera rule, per lock #6's explicit caution.

## 7. Out of scope (unchanged, named debt per IC §4)

`library/cameras` catalog + cited dims/mass · lidar key / perception multi-key · `payload_bay`/`arm`/`wheels`/`gearbox` rules · mirrored mass into energy · wizard "vigilancia" nudge · Continuity intent vs `increase_payload` rewrite · flight-stack software.

## 8. Remaining risks

- None identified beyond the named debt above. The gate's own logic (`block_components_are_resolvable`) was not touched — only its two inputs (`BLOCK_TO_COMPONENTS["perception"]` and `aerial_registry`'s known keys) changed, exactly as the IC intended.
