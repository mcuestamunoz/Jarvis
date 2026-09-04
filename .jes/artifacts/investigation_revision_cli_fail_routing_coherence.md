# Investigation Revision — CLI fail-routing coherence (R1–R5 closed)

**Date:** 2026-09-03  
**Author:** JES / Cursor  
**Authority:** Engineer `Procede` (this turn) after [NEEDS REVISION](investigation_review_cli_fail_routing_coherence.md)  
**Parent report:** [investigation_report_cli_fail_routing_coherence.md](investigation_report_cli_fail_routing_coherence.md)

No `src/` edits. Reproductions ran the real orchestrator in `tmp_path`.

This addendum **closes** the review gaps. Claude's PASS findings (FAIL/WARNING, false thrust-PASS, D8 ranking) stand. Where the parent report named the wrong surface, this file replaces that causal claim.

---

## R1 — Active frame wizard (the walk loop)

Reproduced exactly:

```text
mode=define_missing_params
pending_missing_params=['frame']
param_definition_reason=missing_component_definition

sí → Acquisition Brief question = COMPONENT_PROMPTS static
     "Describe el frame del dron (material y masa). Ej: 'fibra de carbono 450g'"
     (propeller D already known; pulgadas prompt not used)

PVC 650g → completeness=high, mass=0.65, material=pvc, no size_class_inch
           frame_class_compatibility_state = missing
           structure block = in_progress
           still_missing == []  (filters completeness=="low" only)
           _set_pending_next_block re-arms the SAME frame wizard
           _append_arch_progress_hint:
             "Siguiente bloque: Estructura (frame) — en progreso, define los parámetros que faltan. (2/4)"

ayúdame a elegir → _handle_component_description low-completeness frame branch
                   spec from the utterance has neither mass nor material
                   ignores persisted PVC 650g
                   "Indica material y masa. Ej: 'fibra de carbono 450g'"
```

### Call-site table (walk surfaces)

| Surface | `file:line` | Fires in the walk? | Asks for class? |
|---|---|---|---|
| `build_acquisition_brief` question | `acquisition_brief.py:66` ← `COMPONENT_PROMPTS` | **Yes** — opening `sí` | No |
| `_handle_component_description` save `still_missing` | `orchestrator.py:3328-3341` | **Yes** — treats high completeness as done | No |
| `_append_arch_progress_hint` in-progress | `orchestrator.py:3447-3454` | **Yes** — exact walk sentence with `Siguiente bloque:` | No |
| `_handle_component_description` low-completeness frame probe | `orchestrator.py:3361-3372` | **Yes** — `ayúdame a elegir` | No |
| `build_startup_context` generic in-progress | `orchestrator.py:4409-4412` | IDLE `estado` only; **not** the wizard loop | No |
| `_component_prompt_for_first_missing` | `orchestrator.py:2272-2294` | **Bypassed** by all four surfaces above | Yes (if reached) |
| Continuity `_frame_class_next_step` | `project_continuity.py:123-159` | Rank-2 sim-fail intercepts first | Yes (if reached) |

Parent §3.1 was right that a generic structure prompt exists, and wrong that `build_startup_context:4397` is the walk's root. The walk loop is the **active wizard**: completeness-high closes the turn, Structure A still leaves the block `in_progress`, the same wizard is re-armed, help-choose has no frame catalog branch, the hand-written probe asks for mass/material again.

### Smallest shared authority

`frame_class_compatibility_state` (`project_closure.py:162-194`) plus persisted `frame.properties` mass/material.

Add **one** helper in `project_closure.py` (not `domains.aerial._frame_completeness`, which is private and class-blind):

```text
frame_next_missing_datum(project_state) ->
  "mass" | "material" | "size_class" | "class_incompatible" | None
```

Mass/material first from persisted properties; then class state. No new subsystem.

---

## R2 — Exact 4/4 `proactive_question`

Reproduced, 4/4 + `sunnysky_r2305_2500`, thrust FAIL, autonomy **met** (10.09 ≥ 10), `warnings=[]`:

```text
status_type = nominal          # FAIL with empty warnings
proactive_question = "Arquitectura completa (4/4) — puedes optimizar o simular."
situation = "Última simulación: fail — el diseño no está cerrado."
next_useful_step = "Arquitectura completa (4/4) — puedes optimizar o simular."
footer = "Arquitectura 4/4 — completa ✓"
_append_arch_progress_hint = "✓ Arquitectura completa (4/4) — puedes optimizar o simular."
```

Exact creation: `orchestrator.py:4450-4455` (complete branch, **not** the in-progress family). Continuity rank-2 else at `project_continuity.py:399-402` copies `proactive_question` because autonomy-below is false and underspec is false.

This is the walk's F4 (`estado` / `simular` **before** the emax swap). After emax, F3 intercepts and next-step becomes the false PASS sentence; the 4/4 line that remains is the **evidence footer**, which is allowed.

### Tests pinning the sentence / behavior

| File | Pin |
|---|---|
| `tests/test_fn021_session_hygiene.py:185` | `"Arquitectura completa" in complete["message"]` after last control component (hint). Does **not** require `puedes optimizar o simular`. |
| `tests/test_cli_stale_energy_recalc.py:51` | pick message must **not** contain `puedes optimizar o simular` when autonomy undemonstrated. |
| `tests/test_project_continuity.py:123,140-141` | fixture *passes* the architecture-complete string as `proactive_question`; asserts next-step for autonomy-below+thrust-PASS does **not** keep it. |
| `tests/test_fn020_completeness_coherence.py:101` | same fixture string as Continuity input; completeness/BOM test, not a next-step pin. |

---

## R3 — Catalog gate: **C-A1**

Parent report recommended C-A **and** a Shape A motor-picker reopen. Those conflict.

**Engineer lock (this revision): C-A1.**

- First routing IC does **not** reopen the motor catalog for a D8-admitted bound SKU.
- First routing IC does **not** add range-only copy, `MotorSuggestion` fields, or D8/sort changes.
- IDLE `ayúdame a elegir` at 4/4 with a D8-covering bound motor may keep resolving to `project_status`, **provided** Continuity's next step is honest after §2.2 of the IC.
- Contextual motor help is a **later** catalog-honesty investigation/IC.
- Frame `ayúdame a elegir` is **not** catalog: it must request `size_class` (R1). That stays in Shape A.

C-B is not chosen: grouping/copy of range-only vs nominal-covering candidates is product policy, even though a caller could derive `thrust_n >= required` without a new field.

---

## R4 — FAIL semantics (no new enum)

Public `status_type` remains `"blocking" | "warning" | "nominal" | "no_data"`.

Do **not** map `sim.status=fail` to `blocking` (`should_auto_start_define_on_load` would open a wizard). Do **not** add `"fail"` in this IC (MCP/`session_manager.py` public contract).

Observed:

| sim.status | warnings | today's status_type | dishonest UI |
|---|---|---|---|
| fail | `[autonomy_below_restriction]` | warning | CLI prints `WARNING` next to Continuity `fail` |
| fail | `[]` | nominal | next-step uses architecture-complete CTA; OK line is already gated on empty situation, so no `OK` |

Continuity **situation** already reads raw `sim.get("status")` (`project_continuity.py:255-256`).

**Derivation contract for this IC:** leave `status_type` hierarchy unchanged. Fix presentation: the CLI `warning` branch must take the same `not continuity.get("situation")` gate as `nominal`/`no_data` (`main.py:241-248` vs `245-248`). When situation already says `Última simulación: fail`, do not print a second `WARNING` line.

`has_warnings` remains `bool(warnings)` at `reasoning_layer.py:63`.

---

## R5 — Citations (remaining)

| Claim | `file:line` |
|---|---|
| `has_warnings` | `reasoning_layer.py:47,63` |
| `_autonomy_objective_undemonstrated` | `project_continuity.py:80-98`; suppression call `orchestrator.py:3439` |
| Continuity situation uses raw status | `project_continuity.py:255-256` |
| Rank-2 generic consumes `proactive_question` | `project_continuity.py:399-402` |
| `_AUTONOMY_BELOW_NEXT_STEP` selected without thrust gate | `project_continuity.py:396-398` + helper `101-112` |

---

## Shape confirmed

**A — local fail-routing coherence**, with catalog **out**. First IC files/functions: see `implementation_contract_cli_fail_routing_coherence.md`.
