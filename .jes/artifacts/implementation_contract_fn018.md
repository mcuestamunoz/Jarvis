# Implementation Contract — FN-018

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Acquisition Guided Engineering — Step C (Thin Acquisition Brief)  
**Depends on:** FN-017 (closed), principle ratified  
**Does not implement:** Step D (Guided Engineering subsystem), Conversation Engine, bare `10x4.5` registry (unless trivial)

**Workflow:** Claude Code implements + tests + report → Engineer forwards → Cursor reviews. No commit/push unless Engineer asks.

---

## 1. Intent

Two outcomes in one cut:

**C0 — Harmonize component questions (prerequisite of Brief)**  
Every path that asks the user about a **component key** pending item must use `COMPONENT_PROMPTS[key]` (or the Brief that embeds it) — never `¿Cuál es el valor de propellers?`.

Especially: `_try_reprompt_active_block_declaration` (FN-013) still calls `_question_for_param`.

**C1 — Thin Acquisition Brief**  
When opening or re-prompting a **component-definition** acquisition target, Jarvis shows a short deterministic brief:

```text
Qué estamos definiendo
Qué sabe Jarvis (facts from ProjectState — no LLM)
Por qué importa (1–2 lines, state-aware when cheap)
Qué opciones tengo
Qué necesita de mí  (= COMPONENT_PROMPTS / concrete ask)
```

Example shape (illustrative — implementer may tighten wording; structure mandatory):

```text
Vamos a definir las hélices.

Las hélices convierten la potencia de los motores en empuje.
Para este proyecto: motores ya declarados; gap activo = propellers.
[si hay número útil] Requisito orientativo: ≥ X N/motor (o omitir si no disponible).

Puedes:
  • indicar una hélice, ej. 'hélices 10x4.5'
  • describir material/tipo si lo conoces
  • decir 'ayúdame a definir' para repetir esta guía

¿Cómo quieres definirlas?
Describe las hélices. Ej: '10x4.5' o 'hélices de carbono'
```

**Not** a dialogue manager. **Not** LLM-authored brief. One function composes Core facts → string (or message+question).

---

## 2. Scope

### In scope

| # | Change |
|---|---|
| C0 | FN-013 re-prompt: if `pending[0] ∈ COMPONENT_PROMPTS`, use that prompt (or full Brief) — never `_question_for_param` for component keys |
| C0b | FN-015 component-help path: prefer same Brief builder (or at least same prompt source — already COMPONENT_PROMPTS; upgrade message to Brief if cheap) |
| C1 | New small helper e.g. `build_acquisition_brief(target_key, project_state, *, pending_block_label=...) -> str` (or dict `{message, question}`) in a focused module — prefer `acquisition_target.py` **or** tiny new `acquisition_brief.py` if keeping `acquisition_target` thin |
| C1b | Wire Brief into Phase A `ParamDefinitionSession.start()` when reason is `MISSING_COMPONENT_DEFINITION` and first key is a component |
| C1c | Wire Brief into low-completeness / unclear re-prompt in `_handle_component_description` when `expected_keys` set (replace bare single-line prompt with Brief, or Brief as `message` + short `question`) |
| C1d | Reuse only: `COMPONENT_PROMPTS`, `derive_physical_requirements` (optional fields), existing component presence on `design_properties.components`, block labels. **Do not** re-implement Continuity; optional one-liner from continuity next-step if already cheap |
| Tests | `tests/test_fn018_acquisition_brief.py` |
| Docs | Continuity / IMPLEMENTATION_TASKS short note |

### Out of scope

- Step D subsystem / multi-turn “remember what we explained”  
- Conversation Engine  
- LLM-generated briefs  
- Full consequence narrative after every apply (may keep existing arch-progress hint; do **not** build a new consequence engine)  
- Changing acquisition **target** selection / block priority (battery vs propellers)  
- Rewriting motor catalog assist (already good enough)  
- bare `10x4.5` registry match (deferred unless ≤10 lines + test)

---

## 3. Design

### 3.1 C0 — Single question path for component keys

Shared rule (implement once, call everywhere):

```text
def question_for_acquisition_item(key, suggestions=None) -> str:
  if key in COMPONENT_PROMPTS:
    return COMPONENT_PROMPTS[key]
  return existing _question_for_param(key, suggestions)
```

Use in:

- `ParamDefinitionSession.start()` (already mostly done in FN-017 — keep / route through helper)
- `_try_reprompt_active_block_declaration` **must** use this (C0 acceptance)
- FN-015 component branch (already COMPONENT_PROMPTS — align via helper)

### 3.2 C1 — Brief builder

```text
build_acquisition_brief(key: str, project_state) -> {"message": str, "question": str}
```

Rules:

1. **Target** = `key` from Core (caller passes pending/expected key) — never LLM.  
2. **Static knowledge** blurb per key (small dict next to COMPONENT_PROMPTS — 1–2 sentences max). Start with: `propellers`, `motors`, `battery`, `frame` (others may fall back to question-only).  
3. **What Jarvis knows** — deterministic bullets only if true, e.g. motors already high → “Motores ya declarados.”; omit empty noise.  
4. **Why** — optional one line from `derive_physical_requirements` (e.g. thrust per motor) when present; else omit.  
5. **Options** — fixed short list per key (not a catalog engine). Propellers example as in §1.  
6. **Question** = `COMPONENT_PROMPTS[key]`.  
7. Spanish, concise — no essay. Prefer total brief &lt; ~1200 chars.

If `project_state` unavailable, degrade to `COMPONENT_PROMPTS` only (no crash).

### 3.3 Wiring

| Entry | Behavior |
|---|---|
| `start()` component-definition | Return Brief (`message` + `question`) or combined question string — CLI must show the guidance |
| FN-013 re-prompt | `message` may keep “Seguimos con {label}…” **plus** Brief body **or** Brief replaces generic question |
| `_handle_component_description` low / out-of-scope / generic refuse | Use Brief for expected key |
| FN-015 help on component key | Use Brief (or same message+question) |

Do **not** duplicate Brief text in three hardcoded places — one builder.

### 3.4 Assisted motor params

If `pending[0] ∈ ASSISTED_MOTOR_PARAMS`, keep existing catalog / thrust question path (FN-005/009). Brief is for **component keys** first. Optional: no change to numeric Phase B.

---

## 4. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | Phase A open propellers via declare propulsion | Opening text includes hélices guidance (Brief or COMPONENT_PROMPTS); **not** `¿Cuál es el valor de propellers?` |
| B | Wizard open; `definir propulsión` (FN-013) | Re-prompt question/message uses hélices prompt/Brief — **not** `¿Cuál es el valor de propellers?` |
| C | Unclear input (`5`, `definir hélices`) | Re-prompt is propellers Brief/prompt — not frame material/masa (FN-017 preserved) |
| D | `ayúdame a definir` (FN-015) | Help uses Brief or COMPONENT_PROMPTS for propellers; 0 LLM |
| E | `hélices 10x4.5` | Still saves (FN-017 regression) |
| F | `plastico 450g` | No generic write; Brief/re-prompt (FN-017) |
| G | Frame Phase A | Frame Brief or frame material/masa path still coherent — not propeller text |
| H | FN-016 `atrás` | Still cancels |
| I | No new subsystem name in architecture docs claiming “Guidance Engine” | Thin helper only |

---

## 5. Tests (required)

File: `tests/test_fn018_acquisition_brief.py`

Minimum:

1. `test_phase_a_open_shows_brief_not_valor_de_propellers`  
2. `test_fn013_reprompt_uses_component_prompt_not_generic_valor`  (**C0 — mandatory**)  
3. `test_unclear_input_still_propellers_brief`  
4. `test_fn015_help_uses_brief_or_component_prompt`  
5. `test_helices_still_saves`  
6. `test_generic_still_refused`  
7. `test_frame_brief_or_prompt_not_propellers`  
8. `test_atras_still_cancels`

Also run FN-017 + FN-013/015/016 files. Full suite. Baseline: **1506**.

---

## 6. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/core/acquisition_target.py` and/or new `acquisition_brief.py` | Brief builder + static blurbs + optional `question_for_acquisition_item` |
| `src/jarvis/core/param_definition_session.py` | `start()` returns Brief fields |
| `src/jarvis/core/orchestrator.py` | FN-013, FN-015, `_handle_component_description` wire Brief |
| `tests/test_fn018_acquisition_brief.py` | **Create** |
| `docs/PROJECT_CONTINUITY.md` | FN-018 note |
| `docs/IMPLEMENTATION_TASKS.md` | Mark complete |
| `.jes/artifacts/principle_acquisition_guided_engineering.md` | Update sequence: B done, C in progress (optional one-liner) |

**Forbidden:** Conversation Engine; LLM brief; Continuity redesign; intent_resolver edits unless proven necessary (should not be); Step D.

---

## 7. Implementation report (Claude Code)

1. Diff summary per file  
2. Where Brief builder lives + function signature  
3. Proof C0: FN-013 no longer emits `¿Cuál es el valor de propellers?`  
4. Which entry points call the builder  
5. What state facts are included (and which omitted when missing)  
6. Test commands + counts  
7. Confirmation: no Step D / no Conversation Engine / no LLM brief  
8. Residual risks  

No commit/push unless asked.

---

## 8. Review checklist (Cursor)

- [ ] C0: FN-013 harmonized with COMPONENT_PROMPTS/Brief  
- [ ] Brief deterministic, Core-sourced  
- [ ] FN-017 behaviors preserved  
- [ ] Single builder, not copy-pasted essays  
- [ ] Suite green  
- [ ] No Guidance Engine / Conversation Engine  

**Verdict:** PASS / PASS WITH NOTES / FAIL  

---

## 9. Non-goals reminder

After FN-018 PASS, Step **D** remains blocked until Engineer explicitly authorizes a larger Guided Engineering design. FN-018 only delivers **thin Brief + prompt harmonization**.
