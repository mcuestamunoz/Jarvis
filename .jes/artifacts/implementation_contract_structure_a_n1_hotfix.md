# Implementation Contract — Structure A N1 hotfix (override mirror from merged props)

**Project:** Jarvis  
**Date:** 2026-09-03  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** JES / Cursor against this IC after Claude reports

**Status:** RATIFIED, IMPLEMENTED, REVIEWED — **PASS WITH NOTE** (suite 2143).

**Type:** Hotfix. Writer-level dual-truth bug found during Structure A review. Not new physics. Not new gaps. Not CAD.

**Parent IC:** [implementation_contract_structure_a.md](implementation_contract_structure_a.md) — review [PASS WITH NOTES](implementation_review_structure_a.md), Note 1 reproduced.

---

## 0. You

- Edit only `src/jarvis/core/component_writers.py` and test files.
- Do **not** change any gap, Continuity, `_block_progress_status`, `_derive_overall`, `extract_frame_properties`, iterate session, or orchestrator code.
- Do **not** invent mass, density, or class from absent data.
- Full suite green. Zero weakened tests.
- After you finish: write `implementation_report_structure_a_n1_hotfix.md`.

---

## 1. Bug

`set_frame_material` mirrors `structure_mass_override_kg` from **the argument** `mass_kg`, not from the **merged** `props["mass_kg"]`. When a caller passes `mass_kg=None` (meaning "this utterance does not mention mass") alongside a new `size_class_inch` or `material`, the writer **deletes** the override even though the merged component still declares a mass.

Reproduced walk:

```text
frame: fibra de carbono 0.65 kg (override = 0.65)
iterate: "pvc 5 pulgadas"          (mass_kg=None, material="pvc", size_class_inch=5.0)
→ components["frame"].mass_kg = 0.65       (merged props preserve existing)
→ structure_mass_override_kg = None        (popped — physics falls back to factor)
→ calc total_mass_kg drops from 1.65 to 1.60
```

Dual truth: component says 0.65 kg, physics uses factor. Same category of bug as the walk leak this IC closed, in the opposite direction.

### Callers affected

| Call site | `mass_kg=None` reachable? |
|---|---|
| `actions/iterate.py:363` (Structure A — new) | **Yes** — `"pvc 5 pulgadas"` has size but no grams |
| `orchestrator._apply_inferred_component_spec` (acquisition) | Only if `extract_frame_properties` finds material + size but no mass — same pattern |
| `component_writers.apply_components_delta` (`:533-538`) | Passes existing `spec.properties["mass_kg"]` — **None only if component truly has no mass**, correct to pop in that case |

---

## 2. Fix

In `set_frame_material`, after building the merged `props` dict and before writing `current_parameters`, derive the override from **`props`** instead of from the argument:

```python
# ── 2. structure_mass_override_kg in current_parameters ───────────────
updated_params = dict(project_state.current_parameters or {})
mass_prop = props.get("mass_kg")
if mass_prop is not None and mass_prop.value is not None:
    updated_params["structure_mass_override_kg"] = float(mass_prop.value)
else:
    updated_params.pop("structure_mass_override_kg", None)
```

This replaces the current argument-based mirror:

```python
if mass_kg is not None:
    updated_params["structure_mass_override_kg"] = mass_kg
else:
    updated_params.pop("structure_mass_override_kg", None)
```

### Behavior change

| Scenario | Before fix | After fix |
|---|---|---|
| `set_frame_material(state, 0.2, "pvc")` | override = 0.2 | override = 0.2 (identical) |
| `set_frame_material(state, None, "pvc", 5.0)` on a state with `mass_kg=0.65` | override **deleted** | override = 0.65 (from merged props) |
| `set_frame_material(state, None, None)` on a state with no `mass_kg` | override deleted | override deleted (identical) |
| `apply_components_delta` re-derive (`:533-538`) with existing `mass_kg=0.45` | override = 0.45 (passes explicit mass) | override = 0.45 (from merged props — identical) |
| `apply_components_delta` re-derive on frame with **no** mass | override deleted | override deleted (identical) |

No caller that passes an explicit `mass_kg` changes behavior. Only the `None`-on-partial-update path is corrected.

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_frame_component.py` | New: `test_set_frame_material_size_only_preserves_existing_mass_override` — state has `mass_kg=0.65` + `structure_mass_override_kg=0.65`; call `set_frame_material(state, None, "pvc", 5.0)`; assert override stays `0.65`, frame `mass_kg` stays `0.65`, `size_class_inch` is `5.0`. |
| same | New: `test_set_frame_material_material_only_preserves_existing_mass_override` — same pattern, call `(state, None, "aluminum")` on a state with declared mass; override must not be popped. |
| same | Existing `test_set_frame_material_mass_only_no_material_key` — must still pass (mass argument is explicit; behavior unchanged). |
| `tests/test_structure_a.py` | New: `test_walk_pvc_5_pulgadas_preserves_existing_mass_override` — fresh project with 0.65 kg frame, iterate `"pvc 5 pulgadas"`, assert override stays 0.65, frame `mass_kg` stays 0.65, `size_class_inch` written, calc `total_mass_kg` unchanged. |
| All existing | No weakened assertions. |

---

## 4. Non-goals

```text
Any gap change
Any Continuity change
Any _block_progress_status change
Any _derive_overall change
Any iterate session change
Any orchestrator change
Any extractor change
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/component_writers.py` | Mirror from merged props |
| `tests/test_frame_component.py` | Writer-level regression |
| `tests/test_structure_a.py` | Walk-level regression |

---

## 6. Acceptance

- `"pvc 5 pulgadas"` on a 0.65 kg frame: override stays 0.65. `size_class_inch` = 5.0. `total_mass_kg` unchanged.
- `"pvc 200g"` still writes 0.2 (explicit mass, no regression).
- `apply_components_delta` re-derive on an existing 0.45 kg frame: override stays 0.45.
- Suite green.

---

## 7. After you finish

Write `.jes/artifacts/implementation_report_structure_a_n1_hotfix.md`. Stop. JES reviews.
