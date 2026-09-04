# Implementation Contract — Structure A (masa honesta + compatibilidad de clase)

**Project:** Jarvis  
**Date:** 2026-09-03  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** JES / Cursor against this IC after Claude reports

**Status:** RATIFIED (Engineer `ratifico`, 2026-09-03). Implemented by Claude. JES review **PASS WITH NOTES**.

**Type:** Structure level A. **Not** CAD. **Not** geometric fit. **Not** FEA. **Not** control/sensors catalog. **Not** H5. **Not** DSE re-score.

**Checkpoint base:** tag **`v0.3.5`**. Live tree includes DSE apply honesto (review PASS WITH NOTES, suite 2124). Do not revert that.

**Investigation:** [report](investigation_report_structure_a.md) · [review PASS WITH NOTES](investigation_review_structure_a.md)  
**★ (investigation):** [engineer_ratification_structure_a.md](engineer_ratification_structure_a.md) — product model locked; physics lock 2026-09-03 (B, class compatibility)

**Walk leak:** iterate `PVC 200g` registered a material string; `structure_mass_override_kg` stayed **0.65**. Acquisition `"carbono 450g"` already writes mass via `set_frame_material`.

This file **replaces** the draft/hypothesis IC. Do not implement the old FIT PASS / “cabe” wording.

---

## 0. You

- Edit only files in §5.
- Do **not** add a CAD/geometry engine, solids, STL, FEA, wheelbase, arm length, or tip-clearance model.
- Do **not** invent PVC (or any) density to “compute” mass. **Declared grams win.**
- Do **not** change sim `can_fly` / thrust PASS from the class-compatibility gap.
- Do **not** open FC/sensor/ESC catalogs.
- Do **not** mutate Engineer `workspace/`.
- Full suite green. Zero weakened tests.
- After you finish: write `implementation_report_structure_a.md`.

---

## 1. Intent

Structure today is a mass lump (`structure_mass_override_kg`) plus a material label. Architecture can read “structure complete” while iterate ignores a declared 200 g, and while a known propeller diameter has no declared frame class.

This IC does two Structure A operations on the **same** component (shape **B**):

1. **Masa honesta.** If the user declares a frame mass in the same utterance as the material (iterate or component description), that mass reaches `set_frame_material` → `structure_mass_override_kg` and `components["frame"].properties["mass_kg"]`. Calc/sim see it.
2. **Compatibilidad de clase (nivel A), not geometric fit.** When propeller diameter \(D\) is known, the frame must declare `size_class_inch`. Compare as **class screening**:

```text
diameter_in                 size_class_inch
     │                            │
     ├─ PROPULSION (unchanged)    └─ STRUCTURE screening only
     │     OP / pairing / D⁴
     │     if thrust missing
     └─ never from frame class
```

```text
D known + class absent  → GAP-FRAME-SIZE-MISSING + Structure INCOMPLETE
D <= class              → CLASS COMPATIBILITY PASS — LEVEL A / CLASS-BASED
                          (clearance NOT demonstrated)
D > class               → GAP-FRAME-PROP-SIZE + Structure INCOMPLETE
                          (class convention exceeded; physical impossibility NOT demonstrated)
D unknown / no propeller → do not evaluate; structure may close on mass+material
```

**Forbidden copy (internal, gap title, Continuity, CLI):** `STRUCTURAL FIT: VERIFIED`, “la hélice cabe”, “no cabe”, “misfit geométrico”, `Gap.title` containing “does not fit”.  
**Allowed:** CLASS COMPATIBILITY PASS/GAP; user-facing “compatible de clase (nivel A)” / “clase incompatible (nivel A)”.

Do **not** copy `size_class_inch` from the propeller. Do **not** add `+0.25 in` slack. Do **not** convert mm to a class. Do **not** put `size_class_inch` into thrust, power, RPM, \(C_T\), or autonomy.

---

## 2. Locked behavior

### 2.1 Masa — single writer

`set_frame_material` remains the only writer for frame mass + material (already true for acquisition `_apply_inferred_component_spec`).

**Walk leak (confirmed):** `iterate_interactive_session.py` `_extract_material_from_text` (`:1266-1273`) at call sites `:295` and `:412` reduces `"PVC 200g"` to `"pvc"` before `mutation_engine` runs. `apply_material_definition` (`mutation_engine.py:158-172`) then writes a material string only. `_run_declarative_iteration` (`actions/iterate.py:296`) never merges that into `structure_mass_override_kg`.

**Required (do one coherent path, not both parses):**

1. At the two session call sites, run existing `extract_frame_properties` on the **full** raw/normalized utterance **before** truncating to a bare material name. Carry `mass_kg` (and `size_class_inch` once §2.2 lands) on the draft (`component_patch["frame"]` or equivalent). `draft.value` may still be the canonical material for wizard UX.
2. In `_run_declarative_iteration`, when the material/frame draft carries parsed mass and/or `size_class_inch`, call `set_frame_material` (same pattern as `orchestrator._apply_inferred_component_spec` frame branch: writer + `calculation_engine.build` + simulate + `record_action`). Do **not** leave `structure_mass_override_kg` at the old factor-derived value.
3. Do **not** rely on fixing only `apply_material_definition`. If you keep that function as a string patch, it must not be the only payload after truncation.

- If only material, no mass → keep today’s material path. Do **not** invent density. PVC **has** library density (`1380`); do not write a test that expects “PVC has no physical data”.
- Do **not** resurrect `design_properties.structure.material` as a second source of truth. Canonical is `components["frame"]`.

Walk lock (tmp, not Engineer workspace):

```text
structure_mass_override_kg starts 0.65
user iterate / component text: "PVC 200g"  (or "pvc 200g" / "frame pvc 200g")
→ structure_mass_override_kg == 0.2
→ components["frame"].properties["mass_kg"].value == 0.2
```

`extract_frame_properties` already parses `\d+\s*g` and `pvc` via `MATERIAL_ALIASES`. Reuse it. Do not add a second mass parser.

Acquisition `"carbono 450g"` **unchanged** (already uses `set_frame_material`). Regression test: still 0.45 kg.

### 2.2 Clase en pulgadas — required when prop diameter is known

Thrust, KV, pitch, and morphology stay on the **propeller / motor** path. Do **not** multiply thrust by frame class. Do **not** treat `size_class_inch` as a stand-in for `diameter_in`.

**New property** on `components["frame"]` (name locked): `size_class_inch` (`PropertyValue`, unit `"in"`, source `declared`).

Extract in `extract_frame_properties` when the text has a **class**, without inventing from mass or from the bound prop:

- `5 pulgadas` / `5"` / `5 in` / `5 inch` → `size_class_inch = 5`
- Do **not** convert `250mm` (no silent mm→inch). If only mm is present, ignore size (mass still applies if grams/kg present).
- Do **not** copy `diameter_in` onto the frame.
- `"pvc 200g"` must not invent a class. `"frame 5 pulgadas"` must not invent mass.

Writer: extend `set_frame_material` with optional `size_class_inch: float | None = None` (None = leave existing). Acquisition `_apply_inferred_component_spec` frame branch must pass it when the extractor found it.

**When is \(D\) known?** One helper, e.g. `propeller_diameter_in(project_state) -> float | None` in `project_closure.py`:

1. `components["propellers"].properties["diameter_in"]` if numeric;
2. else `current_parameters["propeller_diameter_in"]`;
3. else, if `components["propellers"].catalog_ref` is a propeller SKU, `library.get_propeller(sku).diameter_in` (bound catalog declaration — do not parse millimetres, do not invent from the SKU **name**).

`set_propeller_component` already bridges (1)→(2). Do not add a fourth source.

**Class-compatibility helper** (name locked in spirit; do not call it fit/misfit):

```text
frame_class_compatibility_state(project_state)
  → not_required | missing | class_compatible | class_incompatible
```

| State | Meaning | Structure block |
|---|---|---|
| `not_required` | \(D\) unknown | Unchanged: complete iff mass + material (`_frame_completeness` today). `"carbono 450g"` still completes structure. |
| `missing` | \(D\) known, no `size_class_inch` | **INCOMPLETE** + `GAP-FRAME-SIZE-MISSING` |
| `class_compatible` | \(D\) known, class set, `D <= class` | Complete if mass+material also present. **CLASS COMPATIBILITY PASS — LEVEL A.** Never VERIFIED. Never “cabe”. |
| `class_incompatible` | \(D\) known, class set, `D > class` | **INCOMPLETE** + `GAP-FRAME-PROP-SIZE`. Do not auto-change the prop. Thrust unchanged. Physical impossibility **not** demonstrated. |

Implement the gate in **both** `_block_progress_status` copies (`orchestrator.py` and `engineering_readiness.py`) via this helper: structure `"complete"` requires existing component-present **and** state in `{not_required, class_compatible}`. Do **not** encode the rule only in `_frame_completeness` — architecture 4/4 does not read that function (`component_presence_tier` treats `medium` as present).

Do **not** drop frame `completeness` to `"low"` just because class is missing (that would lie that a massed frame is a stub). Keep `_frame_completeness` as mass+material for `ComponentSpec.completeness`. Optionally add “clase en pulgadas” to `missing_fields` when `missing`/`class_incompatible` for BOM honesty — 4/4 still uses the shared helper.

**Gaps** (ERF-2 `Gap` pattern). Both **MEDIUM**. Do **not** add them to `_INCOMPATIBLE_CLASS_GAP_TYPES` or `_INCOMPATIBLE_VERDICT_SUBSYSTEMS` (that verdict is for demonstrated conflicts: ESC, discharge, motor↔prop). Do **not** set `can_fly=False`. **`_derive_overall` unchanged** (no new HIGH). Structure `INCOMPLETE` already yields `NOT_ASSEMBLY_READY` via the existing subsystem loop (`engineering_readiness.py:1122-1134`). `GAP-ARCH-BLOCK-INCOMPLETE` will also fire once 4/4 is honest.

Register builders in `build_engineering_readiness` `gaps +=` sequence (`:1159-1172`).

**Missing class** (`missing`):

```text
id / type: GAP-FRAME-SIZE-MISSING
severity: MEDIUM
blocks: ["structure"]
title: "Frame size class missing"
```

Locked Continuity / CLI copy (`next_useful_step` / `next_useful_why` — **not** a long `Gap.title`):

```text
Hay una hélice de {D} in y el frame no declara clase en pulgadas. Declara el tamaño del chasis (ej. 'frame 5 pulgadas'). El empuje lo da la hélice, no el frame; sin clase no hay screening de compatibilidad de clase (nivel A).
```

**Class incompatibility** (`class_incompatible`):

```text
id / type: GAP-FRAME-PROP-SIZE
severity: MEDIUM
blocks: ["structure"]
title: "Propeller diameter exceeds declared frame class"
```

Locked Continuity / CLI copy:

```text
La hélice ({D} in) supera la clase de frame declarada ({C} in). Compatibilidad de clase nivel A: no establecida. Declara un frame de clase mayor o una hélice menor. Esto no cambia el PASS de empuje ni demuestra interferencia geométrica.
```

Do not emit `GAP-FRAME-PROP-SIZE` when class is missing (the missing gap owns that state). Do not emit `GAP-FRAME-SIZE-MISSING` when \(D\) is unknown. Do not emit either on `class_compatible`.

**Continuity:** if `readiness` contains either gap, `next_useful_step` / `next_useful_why` use the locked Spanish copy. Rank after blocking-physics / catalog-assist / energy-assisted ranks, before the generic `sim_status == "pass"` fallback. Do not lose the sentence to a generic “pendiente structure”.

**Frame prompt:** `COMPONENT_PROMPTS["frame"]` in `acquisition_target.py` (orchestrator aliases it). When \(D\) is known, the prompt must mention pulgadas (ej. 5 in). When \(D\) is unknown, keep today’s mass+material example. Do not open a new wizard subsystem. Conditional at `_component_prompt_for_first_missing` is acceptable if the dict stays a static default.

### 2.3 Unchanged

- CalculationEngine mass formula (override vs factor) — only the **write** of override.
- Thrust / OP / G22 / \(D^4\) path / pitch / blades — **not** a function of `size_class_inch`. Red line: no `thrust *=` from class. Do not edit `calculation_engine.py`, `aerodynamics.py`, `resolve_operating_point`, `motor_catalog_assist.py` G22 filters.
- G5, DSE apply honest, Block Closure formula, Option B, T1+2.
- Control/sensors extractors and catalogs.
- `PRODUCT_SCOPE` CAD/FEM out of scope.

---

## 3. Tests (mandatory)

Do not mutate Engineer `workspace/`. Use tmp.

| File | What |
|---|---|
| `tests/test_structure_a.py` **new** | Iterate or `handle_user_text` on the **walk path** (iterate session material, not only acquisition): `"pvc 200g"` / `"PVC 200g"`. After save: `structure_mass_override_kg == 0.2`, frame `mass_kg == 0.2`. Cover **both** session call sites if cheap (awaiting-material turn **and** strategy-embedded). |
| same | Acquisition regression: `"carbono 450g"` still `0.45` kg. |
| same | Material-only `"pvc"` with no grams: override **not** silently set to an invented mass. Do **not** assert “PVC has no density”. |
| same | `"pvc 200g"` does not invent `size_class_inch`. `"frame 5 pulgadas"` (no grams) does not invent `mass_kg`. |
| same | Frame `size_class_inch=5` + prop `diameter_in=7` → `GAP-FRAME-PROP-SIZE`; structure **not** complete; thrust **identical** to the same fixture without the class property. Copy / Continuity / title must not contain cabe / verificado / “does not fit”. |
| same | Prop 5 in + class 5 in → no `GAP-FRAME-PROP-SIZE`, no `GAP-FRAME-SIZE-MISSING`; structure complete if mass+material; any user-visible class line is LEVEL A / “compatible de clase”, never VERIFIED. |
| same | Prop 5 in + **no** class → `GAP-FRAME-SIZE-MISSING`; structure block **not** complete; **no** `GAP-FRAME-PROP-SIZE`. Class **not** copied from 5. |
| same | `"carbono 450g"` **without** a propeller diameter → structure still complete. No `GAP-FRAME-SIZE-MISSING`. |
| `tests/test_frame_component.py` and/or `tests/test_g10_materials_frame.py` | Frame completeness without prop still mass+material; with prop, size required as §2.2. Do **not** reference `tests/test_fase2_uxc.py` (does not exist). |
| `tests/test_engineering_readiness_gaps.py` | New types are MEDIUM; **not** in `_INCOMPATIBLE_CLASS_GAP_TYPES`; structure incomplete / gap present → overall `NOT_ASSEMBLY_READY` (intended). `_derive_overall` source **unchanged**. |

---

## 4. Non-goals

```text
CAD / FEM / STL / piece design / topology / tip clearance / arm length
Wheelbase / 250mm → inch class fabrication
Invent PVC density or any density
+0.25 in slack
Copy size_class_inch from propeller
STRUCTURAL FIT: VERIFIED / “la hélice cabe” / geometric misfit demonstrated
HIGH gap / `_derive_overall` edit / `_INCOMPATIBLE_CLASS_GAP_TYPES` membership
Control / sensor / ESC catalog
DSE grids / scoring
Option B / Block PARCIAL / Tier 3
Failing sim on class incompatibility
New domain module
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/iterate_interactive_session.py` | Primary mass leak: parse full text at `:294-296` and `:409-419` before `_extract_material_from_text` truncation |
| `src/jarvis/actions/iterate.py` | `_run_declarative_iteration`: `set_frame_material` + recalc when draft carries mass/class |
| `src/jarvis/core/mutation_engine.py` | Only if needed so DEFINE does not drop a surviving rich payload; **not** the primary leak |
| `src/jarvis/core/component_writers.py` | Optional `size_class_inch` on `set_frame_material` |
| `src/jarvis/domains/aerial.py` | Extract `size_class_inch`; mass regex **unchanged** except not colliding with inches |
| `src/jarvis/core/project_closure.py` | `propeller_diameter_in` + `frame_class_compatibility_state` (shared) |
| `src/jarvis/core/orchestrator.py` | `_block_progress_status` structure AND-condition; `_apply_inferred_component_spec` pass class; prompt when \(D\) known |
| `src/jarvis/core/engineering_readiness.py` | Same AND-condition; two MEDIUM gap builders; `gaps +=` |
| `src/jarvis/core/project_continuity.py` | Locked Spanish copy for the two gaps |
| `src/jarvis/core/acquisition_target.py` | `COMPONENT_PROMPTS["frame"]` default; pulgadas when \(D\) known via orchestrator conditional if the dict stays static |
| `tests/test_structure_a.py` | New |
| `tests/test_frame_component.py` / `tests/test_g10_materials_frame.py` | Completeness without prop |
| `tests/test_engineering_readiness_gaps.py` | MEDIUM + rollup |
| `docs/IMPLEMENTATION_TASKS.md` | Sync after report |
| `.jes/state/engineering_state.json` | Sync after report |

Do **not** edit: `calculation_engine.py`, `tools/aerodynamics.py`, `knowledge/library.py` (`resolve_operating_point`), `motor_catalog_assist.py` G22 filters, `_derive_overall`.

---

## 6. Acceptance

- `PVC 200g` (iterate walk path) → override **0.2 kg**, not 0.65.
- `"carbono 450g"` still 0.45.
- 7 in prop on 5 in class → `GAP-FRAME-PROP-SIZE` + structure **incomplete**; sim thrust PASS unchanged; copy = class incompatibility LEVEL A, not “no cabe”.
- 5 in prop, no class → `GAP-FRAME-SIZE-MISSING`, structure **not** complete, class **not** copied from the prop.
- 5 in prop + 5 in class → CLASS COMPATIBILITY PASS LEVEL A (no VERIFIED / cabe).
- `"carbono 450g"` without prop → still complete.
- Thrust numbers identical with vs without `size_class_inch` on the same prop/motor fixture.
- Suite green.

---

## 7. After you finish

Write `.jes/artifacts/implementation_report_structure_a.md`. Stop. JES reviews.
