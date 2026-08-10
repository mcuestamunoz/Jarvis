# Implementation Contract — FN-014

**Project:** Jarvis  
**Date:** 2026-08-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Acquisition Fluency Architecture (Acquisition Target Authority)  
**Depends on:** FN-011, FN-012, FN-013 (closed)  
**Does not implement:** FN-015, FN-016, Conversation Engine  

---

## 1. Intent

When the project has an active architecture gap and the user says an acquisition verb + a **recognized gap term** (block **or** component key belonging to that gap), Jarvis must open deterministic acquisition — **never** the iterate wizard and **never** the LLM.

Field-note case:

```text
IDLE, Continuity: Propulsión en progreso — declara componentes (propellers pendiente)
User: "definir propellers"
Today: ITERATE_INTERACTIVE ("propiedad declarativa…")
Target: DEFINE_MISSING / component acquisition for propellers (same bridge as FN-011/Bug54)
0 LLM
```

---

## 2. Root cause (do not “fix” with more regex only)

Four disconnected vocabularies; `definir` hits `ITERATE_PATTERNS` before any state-aware acquisition for component keys like `propellers` (not in `BLOCK_ALIASES`).

Authority closest to truth: `_next_pending_block` + `_set_pending_next_block` — already used by Bug54 / FN-011 — but not consulted for component-key phrases in IDLE.

---

## 3. Scope

### In scope

| Area | Change |
|---|---|
| New small helper module **or** functions colocated with catalog | Unified term → concept resolution (block ∪ component) |
| [`orchestrator.py`](src/jarvis/core/orchestrator.py) | IDLE (and post-preempt IDLE re-dispatch) acquisition gate using that helper + existing Bug54/FN-011 bridge |
| Tests | New file `tests/test_fn014_acquisition_target_idle.py` (+ keep FN-011 green) |
| Docs | Short note under Guided Propulsion / Continuity that FN-014 closed this IDLE gap |

### Out of scope

- FN-015 (`ayúdame a definir` → analyze inside DEFINE_MISSING)
- FN-016 (`atrás`, float-as-component)
- Rewriting all 13 checkpoints
- Changing `ITERATE_PATTERNS` globally / removing `definir` from iterate
- Conversation Engine
- Auto-jump to a non-active block (`definir batería` while propulsion is the pending block) — must **not** open energy silently
- Changing physics, catalog matching, or Continuity narrative formula

---

## 4. Design

### 4.1 Helper: resolve acquisition target from text + ProjectState

Add a focused helper (preferred location: new `src/jarvis/core/acquisition_target.py`, **or** extend `system_architecture_catalog.py` if kept tiny — prefer dedicated module to avoid bloating the catalog).

```text
resolve_acquisition_mention(user_input, project_state) -> AcquisitionMention | None
```

Where `AcquisitionMention` is a TypedDict / small dataclass:

```text
{
  "kind": "block" | "component",
  "key": str,           # canonical block key OR component suggested_key
  "block_key": str,     # owning block for the mention (for components: block that lists the key
                        # in BLOCK_TO_COMPONENTS and is the active pending block when possible)
}
```

**Resolution order (deterministic):**

1. If `normalize_block_alias(user_input)` → block → `{kind: block, key: block, block_key: block}`.
2. Else if normalized text contains a **known component key** from `BLOCK_TO_COMPONENTS` values (exact token / alias table — see 4.2) → `{kind: component, key: component_key, block_key: owning_block}`.
3. Else `None`.

**Owning block for a component key:** among blocks in `system_priority` that list the key in `BLOCK_TO_COMPONENTS`, prefer the current `_next_pending_block` if it lists the key; else the first such block in priority. Do **not** invent new block membership.

### 4.2 Component term aliases (minimal, explicit)

Add a small map (same module), not a second inference engine:

```text
COMPONENT_TERM_ALIASES = {
  "propellers": "propellers",
  "helices": "propellers",
  "helice": "propellers",
  "hélices": → normalize then "helices",
  "motors": "motors",
  "motores": "motors",
  "motor": "motors",   # careful: only as whole token
  "battery": "battery",
  "bateria": "battery",
  "batería": → normalize,
  "frame": "frame",
  ...
}
```

Use the same `_normalize` style as the catalog (strip accents). Prefer **token / alias lookup**, not broad substring of short tokens (`motor` inside `motorizacion`).

Do **not** call `infer_component()` here — that is for free-text specs (`10x4.5`), not for naming the gap.

### 4.3 Active-gap gate

```text
is_mention_on_active_gap(mention, project_state) -> bool
```

- Compute `pending = _next_pending_block(project_state)` (orchestrator method — helper may take `pending_block_key` as argument to stay pure).
- If no pending block → False.
- If `mention.block_key != pending_block_key` → False (no cross-block jump).
- If `mention.kind == "block"` → True (same as FN-011).
- If `mention.kind == "component"` → True iff that component key is still missing/low on the pending block (same criterion as `_set_pending_next_block` Phase A list) **or**, if Phase B, the mention maps to that block’s param side (optional; FN-014 minimum is Phase A component keys + block name).

**Minimum acceptance for FN-014:** Phase A component keys + block aliases for the active pending block.

### 4.4 Orchestrator wiring (IDLE)

In `_handle_user_text_inner`, **IDLE** path, **after** FN-005 help-choose and **alongside / generalizing** FN-011:

Recommended structure:

1. Keep FN-005 as-is.
2. Replace or wrap FN-011 call with a broader:

```text
_try_start_acquisition_from_mention(user_input) -> dict | None
```

Behavior:

```text
mention = resolve_acquisition_mention(...)
if mention is None: return None
if not is_mention_on_active_gap(...): return None
# Same bridge as FN-011 — DO NOT invent a second bridge:
self._set_pending_next_block()
session = get_runtime_session()
if not session.pending_define_missing: return None
return start_define_missing_params(session.pending_missing_params, reason=...)
```

Notes:

- When user said `definir propellers` and Phase A pending is `["motors","propellers"]` or `["propellers"]`, `_set_pending_next_block` already loads the right missing component keys — **do not** shrink the pending list unless already only propellers; starting the full Phase A list is OK (same as FN-011).
- Prefer **one** code path shared with FN-011 (refactor FN-011 to call this helper) so block-only phrases keep working without duplication.

### 4.5 Interaction with iterate

- Do **not** remove `definir` from `ITERATE_PATTERNS`.
- Acquisition gate must run in IDLE **before** mode owners are irrelevant; it already runs before iterate starts. Critical: when input would have become iterate at checkpoint 12, it must have been claimed in IDLE by this gate.
- Legitimate iterate: `definir material a carbono` / `aumentar payload` — no component/block gap mention on active gap → unchanged.

### 4.6 Wrong-block mention

`definir batería` / `definir energy` while pending block is `propulsion`:

- `is_mention_on_active_gap` → False → return None.
- Must **not** open energy acquisition.
- Fall-through may still hit iterate or define_params (Bug41 energy patterns). **Contract requirement:** if fall-through would open energy via `DEFINE_PARAMS_PATTERNS` while propulsion is still the active `_next_pending_block`, **suppress** that jump for this cut: treat as non-acquisition (return a short deterministic message **or** fall through to project_status with Continuity — pick **one** and test it).

**Preferred (minimal):** return interactive/ok message without mutating session:

```text
"Ahora toca Propulsión (motores + hélices). Cuando esté completa, podremos definir energía/batería."
0 LLM, mode stays IDLE
```

Only if `mention` resolved to a **different** block than pending. If mention is None, existing routing unchanged.

---

## 5. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | IDLE, propellers pending, `"definir propellers"` | `define_missing_params`, pending includes `propellers`, **0 LLM**, **not** ITERATE |
| B | Same, `"definir propulsión"` / `"definir propulsion"` | Same as today FN-011 (regression) |
| C | Same, `"ayúdame a declarar propulsión"` | FN-011 regression green |
| D | Same, `"definir batería"` | Does **not** open energy wizard; IDLE + clear message (or Continuity); 0 LLM |
| E | IDLE, no architecture / no pending block, `"definir propellers"` | No false acquisition; existing behavior OK |
| F | `"definir material"` / iterate-style without gap term | Still opens iterate (or existing path) — **not** acquisition |
| G | `"ayúdame a elegir el motor"` | FN-005 regression unchanged |
| H | Suite: FN-011 tests still pass |

---

## 6. Tests (required)

File: `tests/test_fn014_acquisition_target_idle.py`

Reuse the project fixture pattern from `tests/test_fn011_propulsion_declare_routing.py` (motors declared, propellers pending, system_defined).

Use `_RefuseLLM` (assert no interpret/analyze/generate).

Minimum tests:

1. `test_definir_propellers_opens_component_acquisition_no_llm`
2. `test_definir_propulsion_still_opens_acquisition` (regression)
3. `test_definir_bateria_does_not_jump_while_propulsion_pending`
4. `test_definir_material_still_iterate_or_non_acquisition` (must not claim acquisition)
5. `test_ayudame_elegir_motor_unaffected` (FN-005)

Also run: `tests/test_fn011_propulsion_declare_routing.py`, `tests/test_fn013_active_block_declare_routing.py`.

Report focused + related + full suite counts in the implementation report.

---

## 7. Files allowed to change

| File | Allowed |
|---|---|
| `src/jarvis/core/acquisition_target.py` | **Create** (preferred) |
| `src/jarvis/core/orchestrator.py` | Wire gate; refactor FN-011 to shared helper |
| `src/jarvis/core/system_architecture_catalog.py` | Only if aliases must live here — prefer not |
| `tests/test_fn014_acquisition_target_idle.py` | **Create** |
| `docs/PROJECT_CONTINUITY.md` | Short FN-014 closed note |
| `docs/IMPLEMENTATION_TASKS.md` | Mark FN-014 under prioridad |

**Forbidden without new contract:** `intent_resolver.py` large pattern expansion as the *only* fix; `iterate_interactive_session.py` whitelist hacks; LLM prompts; calculation engine.

---

## 8. Implementation report (Claude Code must return)

1. Diff summary per file  
2. How `propellers` is resolved (alias table)  
3. How active-gap check reuses `_next_pending_block` / `_set_pending_next_block`  
4. Behavior chosen for wrong-block (`definir batería`)  
5. Test commands + pass counts  
6. Explicit confirmation: no FN-015/016 scope creep  
7. Residual risks  

---

## 9. Review checklist (Cursor)

- [ ] Shared bridge with FN-011 (no second acquisition starter)  
- [ ] Component keys work without being BLOCK_ALIASES  
- [ ] No silent cross-block jump  
- [ ] Iterate legítimo intacto  
- [ ] 0 LLM on A–D, G  
- [ ] Tests match contract table  

**Verdict scale:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Non-goals reminder

This cut does **not** finish Acquisition Fluency Architecture. It only installs the IDLE gate + unified mention vocabulary for the **active** gap. FN-015/016 remain next contracts.
