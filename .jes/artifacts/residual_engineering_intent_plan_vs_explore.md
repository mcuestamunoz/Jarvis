# Residual — Engineering Intent: goal_plan vs explore_design_space

**Date:** 2026-08-10  
**Status:** Deferred (non-blocking)  
**Source cuts:** FN-022 (PASS WITH NOTES); Engineer ratification 2026-08-10  
**Not in scope for:** FN-023 (next-step help → Continuity)

---

## Observation

Two doors for essentially the same engineering intention:

| Phrase | Path today |
|---|---|
| `"Aumentar el empuje"` | `engineering_intent` → deterministic `goal_plan` |
| `"mejorar estabilidad"` / `"Mejorar el margen"` | `explore_design_space` (auto-DSE) |

Same family of intent (improve margin / stability / thrust levers); different first response because pre-existing `EXPLORE_PATTERNS` claim `mejorar`/`optimiza` + goal domain, while `aumentar`/`subir` were intentionally excluded from explore and now hit FN-022’s IDLE gate.

FN-022 acceptance §D allowed “goal plan **or** existing explore path — coherent.” No change required inside FN-022 or FN-023.

---

## Why not fix now

Unifying to plan-first (or explore-first) requires an explicit precedence design among:

- `engineering_intent` / `goal_plan`
- `explore_design_space`
- `iterate`
- `goal_planner` catalogs

Touching `EXPLORE_PATTERNS` / intent_resolver precedence expands scope and risk. Engineer decision: **do not open that discussion inside FN-022 or FN-023.**

---

## Deferred design question

When the user states a bare engineering intention (no numeric mutate, no explicit “explora/optimiza configuraciones”):

1. **Plan-first (preferred candidate):** always `format_goal_plan` + CTA; DSE only on explicit explore vocabulary; **or**
2. **Explore-first:** keep auto-DSE for `mejorar`/`optimiza` + domain; **or**
3. **Split by verb class:** document the two-door model as intentional product behaviour.

Resolve only under a dedicated Engineering Intent coherence cut — after FN-023 / Create→BOM as Engineer prioritizes.

---

## Explicit non-actions

- Do not change FN-022 behaviour to “fix” this residual.
- Do not fold this into FN-023.
- Do not invent Conversation Engine to unify the doors.
