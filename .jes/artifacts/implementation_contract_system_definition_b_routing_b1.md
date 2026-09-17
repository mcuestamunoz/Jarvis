# Implementation Contract — SYSTEM_DEFINITION B routing vs global intercept (`B1-system-definition-b-routing`)

**Project:** Jarvis  
**Date:** 2026-09-17  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** Implemented · Cursor review **PASS** · await Engineer smoke §3 (or waive)

**Parents:**
- Engineer smoke ACCEPT on **`B1-extended-identity-rules`** (2026-09-17) — throwaway `prueba` · B → payload / manipulador / ruedas / gearbox
- Live observation: mid-B, Continuity footer after `component_description_saved` looked like exit; `añadir bloques` → “bloque custom sin componentes”; `payload` → “Estoy definiendo payload_bay… cancelar si quieres explorar…”
- Root cause (Cursor review): global component intercept runs **before** `SYSTEM_DEFINITION` and **does not** exclude that mode; bare `payload` then hits `_maybe_refuse_different_target` via `aumentar_payload`; step-1 free-text path honestly appends junk strings to `custom_blocks`
- Closeout #5 remains **CLOSED** — this is orchestrator UX/routing, not identity rules

**Type:** While `OrchestratorMode.SYSTEM_DEFINITION` is active, **block-collection owns the turn**. Do not steal block names into component intercept. Do not treat meta “add more blocks” phrases as custom block names. After `listo`, identity declare at IDLE stays unchanged.  
**Not** changing `ComponentRule`s / extractors / completeness ladders.  
**Not** removing free-text custom blocks entirely (unknown real block names may still register as custom without component expansion).  
**Not** Continuity rewrite / mission-mass.  
**Not** version bump. **Not** `workspace/` mutation (tests-only).

**Output:** `.jes/artifacts/implementation_report_system_definition_b_routing_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3044** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-system-definition-b-routing`** — SYSTEM_DEFINITION B owns turns until `listo` / escape |
| 2 | Intercept gate | `_interceptable_component_specs` (and any twin guard) **must return `[]` when `session.mode == SYSTEM_DEFINITION`** — same class of exclusion as `CREATE_PROJECT_INTERACTIVE` / `DEFINE_MISSING_PARAMETERS` / `ITERATE_INTERACTIVE`. Document in the existing mode-guard comment |
| 3 | Step-1 ownership | With lock #2, `payload` / `cámara` / `manipulador` / `ruedas` / `gearbox` in B step 1 go **only** through `SystemDefinitionSession._handle_custom_blocks` → alias → “Bloque '…' añadido” (or refuse if unresolvable) — **never** `component_description_prompt` / `component_description_saved` mid-B |
| 4 | Meta phrases (step 1) | Frozen set (ES+EN; exact tuple in report). At least: `añadir bloques`, `anadir bloques`, `añadir bloque`, `add blocks`, `add block`, `más bloques`, `mas bloques`, `otro bloque`, `otra vez`. Match after normalize (strip/lower); **do not** append to `custom_blocks`; return interactive reprompt: keep asking for a block name or `listo` (copy may reuse the step-1 prompt line) |
| 5 | Step 0 | Unchanged A/B/C. Note: `_OPTION_B` already substring-matches `añadir` — “añadir bloques” at step 0 correctly enters B; do not break that |
| 6 | After `listo` | Session clears as today; IDLE global intercept **unchanged** — free-text `bahía de carga` / `brazo manipulador` / `gearbox 5:1` may still save identity outside B |
| 7 | Continuity footer | No requirement to suppress Continuity on mid-B saves once #2 removes mid-B saves. If any other path still `status=ok` mid-B, do **not** invent a Continuity subsystem — optional thin note in report only |
| 8 | Junk hygiene | Optional (nice): when applying #4, also refuse near-duplicate meta if already in `custom_blocks` from pre-fix sessions — **not required**. Do **not** migrate live `prueba` workspace |
| 9 | Forbidden | Conversation Engine · changing identity extractors · flipping block-gate · version bump · LLM |
| 10 | Live | Default **tests-only** |

**Product sentence:**

```text
En modo B, cuando dices un bloque (payload, ruedas…) Jarvis lo apunta
como bloque y sigue pidiendo más — no te abre un wizard de componente
ni inventa un bloque llamado “añadir bloques”.
```

### 0.1 Enough / not enough

| Enough this Buy | Not this Buy |
|---|---|
| SYSTEM_DEFINITION excluded from global intercept | Redesign Continuity mid-wizard |
| Meta phrases no-op in step 1 | Remove all free-text custom blocks |
| Tests T1–T8 + smoke path green | Identity rule keyword changes |
| | Mission mass / `payload_kg` |

---

## 1. You (Claude)

1. Gate `_interceptable_component_specs` (and docstring / `_should_intercept_component` comment) for `SYSTEM_DEFINITION`.  
2. In `_handle_custom_blocks`, detect meta phrases (lock #4) before alias / free-text append.  
3. Tests T1–T8 via orchestrator `handle_user_text` (not only session.answer in isolation — intercept is the bug).  
4. Report: exact meta tuple + confirm IDLE intercept regression still green.  
5. No version bump. No workspace write.

**STOP if** forced to remove free-text custom blocks entirely or to call LLM for routing.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Fresh create → B → `payload` via **orchestrator** → message contains **añadido** (block), **not** “Estoy definiendo payload_bay” / not `component_description_saved` |
| T2 | Same path → `manipulador` → block añadido (manipulation/arm stub only after `listo`) |
| T3 | `ruedas` → `actuation` añadido (alias path) |
| T4 | `gearbox` → `transmission` añadido |
| T5 | Mid step 1: `añadir bloques` → **no** new entry in `custom_blocks`; message still asks for blocks / `listo`; **not** “bloque custom” |
| T6 | After `listo`, components include `payload_bay` / `arm` / `wheels` / `gearbox` as today |
| T7 | IDLE regression: with system already defined, free-text identity (e.g. `bahía de carga` or existing camera phrase) still reaches component save / intercept as before |
| T8 | Full pytest green; `0.4.1` |

---

## 3. Smoke (Engineer)

Throwaway dron → A/B/C → **B**:

1. `payload` → **Bloque … añadido** (not “Estoy definiendo…”).  
2. `añadir bloques` → reprompt, **no** “bloque custom”.  
3. `manipulador` → `ruedas` → `gearbox` → each **añadido**.  
4. `listo` → `estado` shows the four stubs.  
5. Optional IDLE: `bahía de carga` still declareable if you refine after.

**ACCEPT when:** B stays a block loop until `listo`; meta phrase is harmless; stubs appear after `listo`.

---

## 4. Out of scope

| Item | Note |
|---|---|
| Continuity copy while `system_defined=False` | Residual UX; not this Buy |
| Auto-open component wizard **after** `listo` for new stubs | Optional follow-on |
| `B1-mission-mass-energy` | Next product ★ after this hotfix (or parallel if Engineer ★ both) |
| Identity keyword / `frame_arm` | Untouched |

---

## 5. Done when

- [x] Intercept gate + meta no-op + T1–T8 + report  
- [x] Cursor review PASS — [review](implementation_review_system_definition_b_routing_b1.md)  
- [ ] Engineer smoke ACCEPT (or waive)

---

## 6. Handoff

```text
Engineer → ★ B1-system-definition-b-routing (this IC)
Claude   → implement gate + meta phrases + tests + report
Cursor   → review
Engineer → smoke §3
```
