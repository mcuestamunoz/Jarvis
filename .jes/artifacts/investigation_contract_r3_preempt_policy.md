# Investigation Contract — R3 Preempt Policy for DEFINE_MISSING

**Project:** Jarvis  
**Date:** 2026-08-19  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Output:** `.jes/artifacts/investigation_r3_preempt_policy.md`

**Status:** READY FOR CLAUDE

**Type:** Audit + design investigation — preempt policy for `DEFINE_MISSING_PARAMETERS` mode (G8, G11, G7).

**Checkpoint base:** tag `checkpoint-cli-routing-residuals` (`0690895`)

---

## 0. Context

`ITERATE_INTERACTIVE` already has a clean preempt policy via `_should_preempt_iterate_wizard` (C-052). It:

- detects strong action intents (explore, calculate, simulate, etc.),
- detects component descriptions via idle-probe,
- respects ownership (step 2 / motor suggestions / strategy selection),
- clears the session and re-dispatches as IDLE,
- prefixes a notice message.

`DEFINE_MISSING_PARAMETERS` has **no equivalent**. When `param_definition_reason == MISSING_COMPONENT_DEFINITION`, `_handle_component_description` (line 937) intercepts **unconditionally** and returns — the user is trapped. Strong intents like `"reducir payload"`, `"explora opciones"`, `"optimiza autonomía"` are swallowed.

This is **G8** (engineering intent / explore unreachable mid-wizard), **G11** (iterate intent trapped), and **G7** (related preempt gap). All three were registered as "needs R3 preempt-policy design" in the system map.

---

## 1. What Claude must investigate

### 1.1 Current DEFINE_MISSING routing (audit)

Map the full checkpoint chain inside `_handle_user_text_inner` for `mode == DEFINE_MISSING_PARAMETERS`, lines ~830–962. For each gate:

1. What input is intercepted?
2. Does it `return` unconditionally or fall through?
3. What happens to `collected_params` / wizard state?
4. Which intents are **reachable** vs **unreachable** from DEFINE_MISSING?

Produce a table:

| Gate | Input pattern | Returns? | Intent reachable? |
|---|---|---|---|
| soft-interrupt project_status | `"estado"`, `"cómo va"` | YES | ✅ (wizard stays open) |
| soft-interrupt list_materials | `"listar materiales"` | YES | ✅ |
| ... | ... | ... | ... |
| UX-C component intercept (line 937) | **everything else** when MISSING_COMPONENT_DEFINITION | YES | ❌ traps all |

### 1.2 What C-052 does (reference model)

Summarize how `_should_preempt_iterate_wizard` works — its gate logic, ownership concept, what it preserves, what it discards. This is the reference, **not a template to copy verbatim** (DEFINE_MISSING has `collected_params`, not `iteration_draft`).

### 1.3 Danger zones

Identify what can go wrong if we preempt mid-DEFINE_MISSING:

- **`collected_params` loss** — if the user has already declared 2 of 3 components and we `clear_runtime_session()`, those are lost. C-052 can afford to discard `iteration_draft` because iterate is single-variable; DEFINE_MISSING accumulates across multiple wizard turns.
- **`components[]` persistence** — are the declared components already written to `design_properties.components` by the time the wizard is still open, or only on wizard completion? This determines whether clearing is lossy.
- **Re-entry** — can the user resume acquisition after a preempt, or does it restart from scratch?

### 1.4 Design options

Propose **2–3 concrete options** for the preempt policy:

For each option, specify:
- When does preempt fire? (which intents / which inputs)
- What happens to wizard state? (clear, park, preserve)
- What does the user see? (notice message, re-entry instructions)
- What are the risks?
- What tests would be needed?

One option must be **the simplest possible** (even if limited). One must be **the most correct** (even if complex).

### 1.5 G9-A assessment (optional, if quick)

While auditing the routing, note whether `G9-A` (catalog_ref blind spot in `build_startup_context`) is trivially fixable or requires its own investigation. Do not fix it — just assess scope.

---

## 2. Scope boundaries

### In scope
- Audit of DEFINE_MISSING routing chain.
- Reference summary of C-052 (ITERATE preempt).
- Danger-zone analysis for `collected_params` / `components[]` persistence.
- 2–3 design options with trade-offs.
- Optional G9-A scope assessment.

### Out of scope (do not implement)
- Any `src/` changes.
- Any new tests.
- Choosing the final option (that's Engineer's decision).
- G12 retarget paths (related but separate).
- Frame material IDLE intercept (not in R3 set).

---

## 3. Output format

A single investigation artifact: `.jes/artifacts/investigation_r3_preempt_policy.md`

Sections:
1. DEFINE_MISSING routing audit table
2. C-052 reference summary
3. Danger zones (collected_params, components persistence, re-entry)
4. Design options (2–3, with trade-offs)
5. G9-A scope assessment (if quick)
6. Recommendation (investigator's preferred option + reasoning)

---

## 4. Hard constraints for any future IC

These are locked regardless of which option is chosen:

- **No `collected_params` silent loss** — if the user has declared components, they must either be preserved or the user must be warned.
- **Components already written to `design_properties.components`** must not be silently reverted.
- **Soft interrupts (project_status, list_materials, list_motors, analyze)** must remain as-is — they already work correctly mid-wizard.
- **`_handle_component_description`** must still be reachable for its intended purpose (actual component descriptions).
- **Zero weakened tests.**
