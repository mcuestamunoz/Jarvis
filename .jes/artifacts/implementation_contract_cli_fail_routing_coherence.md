# Implementation Contract — CLI fail-routing coherence

**Project:** Jarvis  
**Date:** 2026-09-03  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** JES / Cursor against this file after Claude reports

**Status:** RATIFIED · **IMPLEMENTED** · **REVIEWED PASS WITH NOTES** (2026-09-03)  
**Report:** [implementation_report_cli_fail_routing_coherence.md](implementation_report_cli_fail_routing_coherence.md)  
**Review:** [implementation_review_cli_fail_routing_coherence.md](implementation_review_cli_fail_routing_coherence.md)

**Type:** Routing / claim-language. **Not** D8. **Not** catalog policy. **Not** ERF / `_derive_overall`. **Not** orchestrator split. **Not** Conversation Engine.

**Parent investigation:** [report](investigation_report_cli_fail_routing_coherence.md) · [review PASS WITH NOTES](investigation_review_cli_fail_routing_coherence.md) · [JES revision R1–R5](investigation_revision_cli_fail_routing_coherence.md)  
**Walk:** [engineer_cli_walk_fail_routing_coherence.md](engineer_cli_walk_fail_routing_coherence.md)  
**★:** [engineer_ratification_cli_fail_routing_coherence.md](engineer_ratification_cli_fail_routing_coherence.md)

**Base:** live tree after Structure A + N1 hotfix, reviewer suite **2143**.

**Catalog sequencing (locked C-A1):** this IC does **not** reopen the motor picker for a D8-admitted bound SKU and does **not** add range-only copy. A later catalog-honesty investigation owns that.

---

## 0. You

- Edit only files in §5.
- Do **not** change `_motor_covers_requirements`, catalog JSON, `MotorSuggestion`, D8 sort key, or `bound_motor_sku_is_underspec`.
- Do **not** add a branch in `_try_start_assisted_motor_help` that reopens the catalog for “admitted by margin but sim thrust fail”.
- Do **not** change simulator pass/fail, thrust formulas, autonomy math, `_derive_overall`, or `ASSEMBLY_READY`.
- Do **not** add a new `status_type` value and do **not** map `sim.status=fail` to `"blocking"`.
- Do **not** split `orchestrator.py`. Do not introduce a Conversation / Decision Engine.
- Do **not** mutate Engineer `workspace/`. Reconstruct in `tmp_path`.
- Full suite green. Zero weakened tests.
- After you finish: write `implementation_report_cli_fail_routing_coherence.md`.

---

## 1. Intent (field fixture)

Walk `workspace/autonomía-de-10-minutos-86f6a0e8effa` (preserve; do not write it):

1. After `PVC 650g` with propeller D known, `ayúdame a elegir` inside the open frame wizard must request **clase en pulgadas**, not mass/material again.
2. `sim.status=fail` must not be rendered as `WARNING` beside Continuity's honest `fail`.
3. Thrust FAIL + autonomy below must never say `el empuje ya es PASS`.
4. Architecture 4/4 + thrust FAIL (autonomy met) must not use `puedes optimizar o simular` as the next action. The evidence footer `Arquitectura 4/4 — completa ✓` may stay.

---

## 2. Locked behavior

### 2.1 Frame next missing datum — `project_closure.py`

Add **one** helper (name free, this name preferred):

```text
frame_next_missing_datum(project_state) ->
  "mass" | "material" | "size_class" | "class_incompatible" | None
```

Compose existing authorities only:

- persisted `components["frame"].properties` for mass/material (same fields `set_frame_material` writes);
- `frame_class_compatibility_state` for class.

Order: missing mass and/or material first; then `missing` → `"size_class"`; then `class_incompatible`; else `None`. Do **not** import `_frame_completeness` from `domains.aerial`.

Add a small question helper in the same module (or next to it) so Acquisition Brief and orchestrator share copy. When datum is `"size_class"` (mass+material already present, D known), locked prompt:

```text
El frame ya tiene material y masa. Declara la clase en pulgadas (ej. 'frame 5 pulgadas'). El empuje lo da la hélice, no el frame.
```

When frame is still missing mass/material **and** D is known, keep the existing Structure A three-part example (`material, masa y clase en pulgadas` / `'fibra de carbono 450g 5 pulgadas'`). When D is unknown, keep today's mass/material examples.

### 2.2 Frame wizard must not close on class-missing

In `_handle_component_description`, `still_missing` for `"frame"` must treat `frame_next_missing_datum in ("size_class", "class_incompatible", "mass", "material")` as still missing, even if `completeness == "high"`.

Then the save path uses `_component_prompt_for_first_missing` / the shared question helper instead of `_set_pending_next_block` + generic `_append_arch_progress_hint`.

### 2.3 Frame probe and Brief must read persisted state

`orchestrator.py:3361-3372` (low-completeness frame branch) must not decide from the current utterance alone. Merge persisted frame properties with the current spec; then call the shared helper. `ayúdame a elegir` with PVC 650g already stored → §2.1 size-class prompt.

`build_acquisition_brief` (`acquisition_brief.py`): for `key=="frame"`, `question` comes from the shared helper, not the static `COMPONENT_PROMPTS["frame"]` when the helper returns a more specific string. Static `COMPONENT_PROMPTS` dict itself may stay as fallback for other keys / no project.

`_component_prompt_for_first_missing` must call the same helper (replace the inline pulgadas string if the helper already covers it).

`build_startup_context` in-progress branch for `"structure"` (`orchestrator.py:4389-4412`) and `_append_arch_progress_hint` in-progress text (`orchestrator.py:3450-3454`) must not say generic `define los parámetros que faltan` when the helper returns `"size_class"` or `"class_incompatible"`. Use the helper's question (or Continuity's existing locked class sentences). Composite-block reason-aware logic stays as-is.

### 2.4 Continuity next step — `project_continuity.py`

Inside rank-2 (`status_type == "warning"` or `sim_status not in ("pass", "", "ok")`):

1. `_underspec_live` — unchanged, still first.
2. `_autonomy_calculated_below_target` **and** `sim.get("can_fly") is True` → existing `_AUTONOMY_BELOW_NEXT_STEP` (verbatim, including `el empuje ya es PASS`).
3. `_autonomy_calculated_below_target` **and** `can_fly` is not True → locked:

```text
La simulación no es PASS: el empuje no alcanza el requisito y la autonomía está por debajo del objetivo. Cambia entradas; repetir simular con los mismos datos no cierra el fallo.
```

4. Else if `can_fly` is not True (thrust fail, autonomy not below) → locked:

```text
La simulación no es PASS: el empuje disponible no cubre el requisito. Cambia motor, hélice o masa; repetir simular no cierra el fallo.
```

5. Else: existing generic. Must **not** copy `proactive_question` when that string contains `puedes optimizar o simular`.

Do not name SKUs. Do not say `ayúdame a elegir` in (3) or (4). `next_useful_why` for (3)/(4): `GAP-SIM-NOT-PASS` or raw `sim.status` — not `autonomy_below_restriction` alone when thrust also failed.

Thrust authority: reuse `sim.can_fly`. Do not re-compare newtons in Continuity.

### 2.5 Architecture evidence vs next action

`build_startup_context` complete branch (`orchestrator.py:4450-4455`): do **not** set `proactive_question` to `Arquitectura completa (…) — puedes optimizar o simular` when `simulation.status` is fail or `can_fly is False`. Architecture progress fields stay; Continuity §2.4 owns the next action.

`_append_arch_progress_hint` (`orchestrator.py:3431-3446`):

- Keep today's full suppression when `_autonomy_objective_undemonstrated` (stale-energy IC).
- When `can_fly is False` (or sim status fail), do **not** append `puedes optimizar o simular`. A line that only says `Arquitectura completa ({progress})` is allowed so `tests/test_fn021_session_hygiene.py` can keep asserting `Arquitectura completa`.

CLI footer `Arquitectura 4/4 — completa ✓` (`main.py:279-282`) stays. That is evidence, not a next action.

### 2.6 CLI FAIL vs WARNING — `adapters/cli/main.py`

`render_startup_context` `status_type == "warning"` branch (`main.py:241-244`): gate on `not continuity.get("situation")`, matching the `nominal` / `no_data` siblings.

Do not change the public `status_type` enum. Do not print `Última simulación: WARNING` when Continuity situation already named the raw fail.

### 2.7 `ayúdame a elegir`

- **Frame wizard (active `expected_keys` frame):** §2.3. Not a catalog list.
- **IDLE, bound motor D8-admitted:** may still return `project_status`. Honesty of that reprint is §2.4. **No** new motor-catalog reopen in this IC.

---

## 3. Tests (mandatory)

New file `tests/test_cli_fail_routing_coherence.py` (real orchestrator, `_RefuseLLM`, `tmp_path`):

| # | Fixture | Assert |
|---|---|---|
| 1 | Architecture defined, prop D known, open frame wizard, `PVC 650g`, then `ayúdame a elegir` | message names clase/pulgadas; does **not** contain `Indica material y masa` |
| 2 | Same save turn as (1) | follow-up / message does **not** say generic `define los parámetros que faltan` as the only next ask; class is requested |
| 3 | 4/4 + `emax_rs2205_2300` (or equivalent: `sim.status=fail`, `can_fly=False`, `warnings` includes `autonomy_below_restriction`) | Continuity `next_useful_step` does **not** contain `el empuje ya es PASS`; render does **not** contain `Última simulación: WARNING` |
| 4 | 4/4 + thrust FAIL + autonomy **met** (`warnings=[]`, e.g. `sunnysky_r2305_2500` + 10 min met) | `next_useful_step` does **not** contain `puedes optimizar o simular`; situation still names `fail` |
| 5 | Closed BOM + sim **PASS** + autonomy below (existing autonomy-below shape) | `_AUTONOMY_BELOW_NEXT_STEP` / `el empuje ya es PASS` **still** present |
| 6 | `_append_arch_progress_hint` on 4/4 + `can_fly is False` + autonomy met | message does **not** contain `puedes optimizar o simular` |

Regressions that must stay green (do not weaken):

- `tests/test_project_continuity.py` (PASS + autonomy below)
- `tests/test_cli_feasibility_semantics.py`
- `tests/test_cli_stale_energy_recalc.py`
- `tests/test_structure_a.py` / `tests/test_frame_component.py` (N1)
- `tests/test_cli_catalog_assist_t1.py` / `t1_plus_2` / watts-recovery
- `tests/test_fn021_session_hygiene.py` (`Arquitectura completa` still in the completing-control message)

---

## 4. Non-goals

```text
D8 / _motor_covers_requirements / find_motors_for_requirements sort
MotorSuggestion shape / range-only vs nominal groups
_try_start_assisted_motor_help third reopen branch
status_type new enum / FAIL → blocking
_derive_overall / ERF / ASSEMBLY_READY
simulator formulas / mass / OP resolution
orchestrator.py split / Conversation Engine
optimize wizard redesign
P26 / P27-A / H5 / CAD / Option B / Tier 3
Engineer workspace/
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/project_closure.py` | §2.1 helper + question copy |
| `src/jarvis/core/acquisition_brief.py` | §2.3 frame question |
| `src/jarvis/core/orchestrator.py` | §2.2 still_missing, §2.3 probe/startup/hint, §2.5 complete-branch CTA |
| `src/jarvis/core/project_continuity.py` | §2.4 rank-2 guards + two new locked sentences |
| `src/jarvis/adapters/cli/main.py` | §2.6 situation gate on WARNING line |
| `tests/test_cli_fail_routing_coherence.py` | §3 |

Do not touch `knowledge/library.py`, catalog JSON, or `engineering_readiness.py` except read-only if a test needs `build_engineering_readiness`.

---

## 6. After implementation

Write `.jes/artifacts/implementation_report_cli_fail_routing_coherence.md`. Stop. JES reviews. No extra refactors.
