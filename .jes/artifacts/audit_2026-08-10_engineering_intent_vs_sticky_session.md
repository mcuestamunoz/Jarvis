# Audit — Post-architecture "Aumentar el empuje" + next-step help

**Date:** 2026-08-10  
**Project evidence:** `workspace/dron-03c60670c9a8` (+ runtime_snapshot)  
**Context:** Engineer assessment after FN-019 validated CLI session  

## Verdict in one line

Two distinct issues. **Do not merge into one FN.** Hygiene first; Engineering Intent second. No Conversation Engine.

---

## A) `"Aumentar el empuje"` → controladora — ROOT CAUSE (confirmed)

### What the Core would do if IDLE

| Probe | Result |
|---|---|
| `IntentResolver.resolve_intent("Aumentar el empuje")` | **`iterate`** |
| `detect_goal(...)` | **`None`** (no keyword for bare “empuje”) |
| `infer_components(...)` | `generic_component` only |
| `_next_pending_block(state)` | **`None`** (arch 4/4) |

So the phrase is **not** being classified as flight_controller. Intent wants **iterate**.

### What actually happened

Live snapshot after simulate:

```json
mode: "define_missing_params"
pending_param_definitions: ["propellers"]           // stale
pending_missing_params: ["flight_controller", "sensors"]  // stale, already declared
param_definition_reason: "missing_component_definition"
```

DEFINE_MISSING branch runs **before** iterate. UX-C → `_handle_component_description` with `expected_keys = [flight_controller, sensors]` → low/unclear input → `_COMPONENT_PROMPTS["flight_controller"]`.

### Why session stayed zombie

On last component save (`still_missing` empty):

```text
_set_pending_next_block()
  → _next_pending_block() is None  (architecture complete)
  → return   // NO clear_runtime_session()
```

Mode + stale pending fields remain. Simulate does not clear them either.

**Category:** session / Acquisition Target Authority leak after arch close.  
**Not:** missing Engineering Intent layer (that layer never got the turn).

---

## B) `"ayúdame con el siguiente paso"` → battery talk — ROOT CAUSE

| Probe | Result |
|---|---|
| intent | **`analyze`** → LLM |
| Continuity next (at that moment) | declare propulsion / propellers |
| FN-015 | does **not** match (needs definir/valor/poner) |

LLM invents `battery_capacity_wh` while pending gap was propellers.

**Category:** next-step help ignores Acquisition Target / Continuity.  
**Related to A** (authority), different phrase class — can be a small follow-up after hygiene, or scoped with Continuity `project_status` / pending help.

---

## C) goal_planner + DSE capacity (parallel check)

| Capability | Status for this user intent |
|---|---|
| `detect_goal("Aumentar el empuje")` | **None** — no “empuje”/“thrust” keyword in `_GOAL_KEYWORDS` |
| Closest goals | `mejorar_estabilidad` (margin) / `aumentar_payload` strategies include lever `per_motor_max_thrust_n / motors` |
| `EXPLORATION_GRIDS["mejorar_estabilidad"]` | Exists (motor_count, thrust factors, safety_factor) |
| `explore_design_space` intent | Needs explore verb **and** goal keyword — bare “aumentar empuje” → **iterate**, not explore |
| Iterate path | Correct *if* IDLE — would open iterate wizard for thrust mutation, **not** the multi-candidate DSE narrative |

**Conclusion:** Pieces for “increase thrust / improve margin” **exist** (goal catalog levers + DSE grids + iterate), but:

1. Sticky DEFINE_MISSING blocks them today.  
2. Phrase does not map to `detect_goal` / `explore_design_space` yet.  
3. Desired UX (options A/B/C + trade-offs) is closer to **goal_plan + DSE** than to raw iterate — that is a **second cut**, not a reason to skip hygiene.

---

## Recommended sequence (aligned with Engineer)

**Hard constraint (Engineer, 2026-08-10):** everything in this track must stay **generic**.
No thrust-only hacks, no one-off phrase tables for a single symptom, no
architecture that only works for “aumentar el empuje”. Acquisition hygiene,
next-step help, and Engineering Intent→goal/DSE must all be reusable across
intents, blocks, and goals.

```text
1. FN-021 — Session hygiene (micro, generic)
   When acquisition finishes and there is no next architecture block
   (_next_pending_block is None): clear_runtime_session() → IDLE.
   Same rule for any last block/component completion — not control-specific.
   Optionally: simulate/calculate clear or refuse stale DEFINE_MISSING.
   Prove with the field phrase, but implement as general arch-complete cleanup.

2. Then Engineering Intent cut (NOT Conversation Engine) — generic bridge:
   engineering-intent language → existing goal_planner keys + format_goal_plan
   and/or explore_design_space grids. Extend keyword/strategy catalogs
   symmetrically; no single-goal special case as the design center.

3. Deferred: next-step help phrases → Continuity / Acquisition Target Authority
   (generic: help follows current pending target or Continuity next step,
   never LLM inventing a different gap). Separate FN if needed.

4. Still later: Create→BOM handoff. Step D Guided Engineering subsystem — blocked.
```

## Explicit non-recommendations

- Do **not** treat this session as FN-019 failure.  
- Do **not** start EngineeringConversationEngine.  
- Do **not** jump to DSE UX before clearing sticky DEFINE_MISSING — would mask whether iterate/DSE actually receive the turn.

## Pass criteria for FN-021 (if authorized)

- After last architecture component save: `mode == IDLE`, pending_* empty.  
- Replay: arch complete + `"Aumentar el empuje"` → not flight_controller prompt; intent path iterate or documented goal/DSE.  
- FN-019/020 regressions green.
