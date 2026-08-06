# Understanding — motor suggestions UX value

**Date:** 2026-08-05  
**Cycle:** Validar si las sugerencias de motor aportan valor o generan ruido

## What exists

When iterate `define` receives a **propulsion_active** motor with `kv_rating` but **no** `thrust_n`:

1. `IterateInteractiveSession._build_motor_suggestions` → `ComponentLibrary.find_motors_by_kv(kv, tolerance=150)`
2. Wizard stays at step 2 with `motor_suggestions` list
3. User picks `1/2/…` (enrich thrust_n + weight_g) or `no` (advance without thrust)
4. Never auto-applies; catalog-only

Library size today: **6 motors**. Sample coverage:

| KV query | Matches |
|---|---|
| 920 | 2 (SunnySky + generic) |
| 1000 | 3 |
| 2300 / 2400 | 1 (EMAX) |
| 1500 | 0 (silent skip → step 3) |

## How to trigger (real path)

Idle project → iterate define componentes → `"4 motores 920KV"` (no thrust) → expect suggestion prompt.

Already covered by unit tests (`test_motor_kv_suggestion_*`). Gap: **live UX judgment** — useful vs noisy.

## Validation questions

1. Does the prompt appear at the right moment (KV known, thrust missing)?
2. Are catalog options recognizable / relevant to the declared KV?
3. Does picking `1` produce coherent physics (thrust used in calc/sim)?
4. Does `no` feel clean (no zombie suggestions, clear next step)?
5. Empty catalog (KV with 0 matches) — silent skip OK or should say “no encontré motores”?
6. Noise: does it interrupt too often, or offer junk generics (`generic_920kv`)?

## Non-goals this cycle

- Expanding the motor catalog (unless validation proves emptiness is the main failure)
- LLM involvement (feature is deterministic)
- Changing auto-apply policy (must stay user-confirm)

## Exit criteria

Field note + checklist answers; if noise/value clear → either mark roadmap item done, or open a focused Implement cycle with concrete UX/code change.
