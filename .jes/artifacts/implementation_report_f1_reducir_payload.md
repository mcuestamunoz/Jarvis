# Implementation Report — F-1 (Vehicle-Agnostic Payload Direction)

## Summary

`"reducir payload"` no longer resolves to `aumentar_payload`. `goal_planner.detect_goal` now resolves the payload dimension via an explicit **dimension + direction** pattern (`_detect_payload_goal`/`_direction_of`), checked before the existing flat `_GOAL_KEYWORDS` loop — the bare, direction-less tokens `"payload"`/`"carga util"`/`"carga utile"` that caused the inversion were removed from that loop entirely. A new goal, `reducir_payload`, mirrors `aumentar_payload` using the exact same `GOAL_STRATEGIES`/`EXPLORATION_GRIDS`/`HandoffContext` architecture — no parallel planning system. Detection is vehicle-agnostic by construction: `detect_goal`/`is_engineering_intention` take only text, no `vehicle_type` parameter exists to branch on. **Full suite: 1681 passed** (1630 baseline + 51 new), zero regressions.

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/goal_planner.py` | `_detect_payload_goal`/`_direction_of`/`_INCREASE_WORDS`/`_DECREASE_WORDS`/`_PAYLOAD_*` tables (new); `_GOAL_KEYWORDS`'s `aumentar_payload` bare-token entry removed; `detect_goal` calls the new resolver first; new `GOAL_STRATEGIES["reducir_payload"]` (3 strategies); `_prioritize_strategies` new `reducir_payload` branch; `format_goal_plan`'s `goal_labels` gains `"reducir_payload": "Reducir carga útil"`. |
| `src/jarvis/core/design_explorer.py` | `GOAL_LABELS["reducir_payload"]`; new `EXPLORATION_GRIDS["reducir_payload"]` (factors < 1.0 only); `_score_candidate` new `reducir_payload` branch (`-calc.payload_kg`, mirrors `reducir_masa`'s shape). |
| `src/jarvis/core/orchestrator.py` | `_GOAL_EXPLORE_DOMAIN["reducir_payload"] = "payload"`. |
| `tests/test_f1_reducir_payload.py` (new) | 51 tests — see below. |

`intent_resolver.py` — **not touched**. The bare `"explora opciones"` → `HandoffContext` bind path (C-106) already keys off `goal_key in EXPLORATION_GRIDS`, generic over every goal — adding `reducir_payload` to `EXPLORATION_GRIDS` was sufficient for the full Handoff invariant (Goal Plan → HandoffContext → "explora opciones" → DSE) to work with zero `intent_resolver.py` changes, confirmed by test and CLI probe (see below). No catalog/`ComponentSpec`/H5/BOM files touched.

## Root cause

`_GOAL_KEYWORDS["aumentar_payload"]` contained bare, direction-less tokens (`"payload"`, `"carga util"`, `"carga utile"`) matched by plain substring containment in `detect_goal`'s single flat loop. `"reducir payload"` contains `"payload"` as a substring, so it matched the `aumentar_payload` group regardless of the word `"reducir"` sitting right next to it — direction was never encoded, only the dimension.

## Direction-resolution implementation

A small, reusable pattern (`goal_planner.py`):

```python
_INCREASE_WORDS = ("aument", "subir", "sube", "increment", "mejorar", "levantar")
_DECREASE_WORDS = ("reduc", "bajar", "disminu", "menos", "aligerar")

def _direction_of(normalized: str) -> Optional[str]:
    # "increase" | "decrease" | None (absent or both present — ambiguous)
```

`_detect_payload_goal(normalized)` — checked before the generic `_GOAL_KEYWORDS` loop in `detect_goal`:

1. **Decrease phrases** (`"transportar menos peso"`, `"transportar menos carga"`) — the one case needing context beyond a bare dimension term + direction word, since bare `"menos peso"`/`"bajar peso"` already unambiguously means `reducir_masa` (structural) in the existing keyword table; `"transportar"` framing disambiguates payload from mass.
2. **Increase phrases** — the exact pre-F-1 compound list (`"aumentar carga"`, `"levantar mas"`, `"transportar mas peso"`, ...), kept verbatim so every existing accepted phrase still resolves identically.
3. **Bare dimension terms** (`"payload"`, `"carga util"`, `"carga utile"`, `"capacidad de carga"`) + `_direction_of()`: an explicit decrease word anywhere in the phrase → `reducir_payload`; an explicit increase word, or **no direction word at all** → `aumentar_payload` (preserves the pre-F-1 default for bare `"payload"` alone — never sufficient evidence for *reduction*, but still the conservative default when no direction is stated at all, matching every pre-existing test that relies on it).

This is architecturally a data-driven keyword resolver, not an `if "reducir" in text and "payload" in text` bypass — it reuses the same substring-based matching style `detect_goal` already uses elsewhere, just gated by an explicit direction check for one dimension. Only payload was migrated; `mejorar_autonomia`/`reducir_masa`/`mejorar_estabilidad` keyword groups are byte-for-byte unchanged.

## `reducir_payload` strategy

Same `GOAL_STRATEGIES` shape as every existing goal (`action`/`description`/`lever` dicts), vehicle-agnostic wording (verified by test — no "dron"/"drone"/"hélice" in the copy):

| # | Action | Lever |
|---|---|---|
| 1 | Reducir requisito de carga útil | `payload_kg` |
| 2 | Aligerar estructura si está sobredimensionada | `structure_mass_factor / material` |
| 3 | Reducir actuadores si el payload baja | `motors / motor_count` |

**`_prioritize_strategies`** — new `reducir_payload` branch: when `safety_margin_ratio < 1.15`, the `payload_kg` lever sorts first (contract: "if margin is low, prioritizing payload_kg reduction is appropriate"). **Engineer lock honored**: the actuator/motor lever is *always* sorted last, regardless of margin — `sim_context` (the `last_simulation`-shaped dict `_handle_engineering_intent`/`_handle_analyze` already pass) never carries `motor_count` today, so `sim_context.get("motor_count") is None` is unconditionally true under current wiring; rather than widen `sim_context`'s shape (out of scope — would touch `_handle_engineering_intent`/`_build_analyze_context`), the strategy is simply never promoted, satisfying "do not invent `motor_count` on projects without actuators" exactly. It **stays in `GOAL_STRATEGIES`** (verified by test) so H4's `match_plan_lever` can still bind it when a user names `motors`/`motor_count` explicitly.

## DSE changes

`EXPLORATION_GRIDS["reducir_payload"]` — `payload_kg_factor` values strictly below `1.0` only (`0.85`, `0.7`, `0.5`), plus two combined candidates (`structure_mass_factor_factor` and `motor_count_delta: -1`, both paired with a payload reduction). The `motor_count_delta` candidate is architecture-conditional by the **existing, unmodified** mechanism every other goal's `motor_count_delta` entries already rely on: `_apply_delta` silently omits any candidate whose referenced param is absent from `base_params` — no new invention needed for F-1.

`_score_candidate`: `reducir_payload` → `-calc.payload_kg` (mirrors `reducir_masa`'s exact shape — a pure-reduction goal, unlike `aumentar_payload`'s combined margin×payload metric).

**Verified via CLI-style probe** (real orchestrator, no mocks): a 4.0 kg baseline (viable=✗, margin 0.796) → `"reducir payload"` → Goal Plan → `"explora opciones"` → 2 viable candidates, both strictly below baseline (2.0 kg, 2.8 kg) — `aumentar_payload`'s DSE re-verified unaffected on a separate project (baseline 2.0 kg → candidates including 2.4 kg, i.e. still increasing).

## Tests: focused · regressions · full suite

```
pytest tests/test_f1_reducir_payload.py -v                                          → 51 passed
pytest tests/test_goal_planner.py tests/test_design_explorer.py \
       tests/test_da2_components_delta.py tests/test_fn022_engineering_intent.py \
       tests/test_fn023_next_step_help.py tests/test_fn024_handoff_context_dse.py \
       tests/test_fn025_help_goal_intent.py tests/test_fn026_lever_iterate_preseed.py \
       tests/test_catalog_foundation_v1.py tests/test_catalog_bind_v1.py \
       tests/test_f1_reducir_payload.py -q                                          → 255 passed
pytest -q (full suite)                                                              → 1681 passed (1630 baseline + 51 new)
```

Coverage highlights (mapped to contract §5):
- Required outcomes table (9 phrases) — parametrized, all pass.
- Existing positive-intent regression (8 phrases, including every `TestDetectGoal` case in `test_goal_planner.py`) — unchanged.
- Numeric deferral (`"reducir payload a 2kg"` → `None`).
- **Vehicle-agnostic**: a pure parametrization crossing 3 payload phrases × 3 `vehicle_type` labels (`dron`/`robot`/`ground`) calling `detect_goal` identically (the parameter is explicitly unused — `detect_goal`'s signature has no `vehicle_type` slot to branch on), **plus** a full orchestrator-level test creating real `dron`/`robot`/`rover` projects and confirming `"reducir payload"` produces `goal_key == "reducir_payload"` for all three end to end.
- `GOAL_STRATEGIES["reducir_payload"]` structure, levers, and vehicle-agnostic wording (no "dron"/"drone"/"hélice" substring anywhere in the strategy copy).
- `_prioritize_strategies`: low margin → payload first; motor lever *never* first, *always* last, regardless of margin (3 margin values tested); motor lever confirmed still present in the catalog (not removed); no-sim_context default order unchanged.
- DSE: `reducir_payload` candidates never exceed baseline `payload_kg`; viable candidates strictly below baseline; `aumentar_payload` DSE regression (still produces increasing candidates); `EXPLORATION_GRIDS`/`GOAL_LABELS` membership; all-goals smoke loop (now 5 goals, generic, no hardcoded count).
- **Handoff invariant** (Goal Plan → HandoffContext → `"explora opciones"` → DSE, exactly the diagram in contract §"HANDOFF CONSTRAINT"): `reducir_payload` plan creates an active `HandoffContext`; bare `"explora opciones"` binds through it and returns only lower-payload viable candidates; `dse_capability` consumed correctly; `aumentar_payload`'s own bind path re-verified unaffected by the new goal's addition.
- H4 (`match_plan_lever`) resolves `payload_kg` correctly for a `reducir_payload` `HandoffContext` — tested directly (see note below on why not via natural language).
- FN-022/FN-025 regression smoke (bare `"aumentar el empuje"` still `mejorar_estabilidad`; `"ayudame a reducir payload"` correctly routes to `engineering_intent` with `goal_key="reducir_payload"`, exercising FN-025's help+goal gate for the new goal too).

**One test note, not a defect**: `"cambia payload_kg"` cannot be used to exercise H4's natural-language lever-preseed path, because `"payload_kg"` contains the substring `"payload"` — the pre-existing FN-022 goal-detection gate (unrelated to F-1, checked *before* the iterate dispatch) reclaims any phrase containing a goal-keyword dimension word before it ever reaches `match_plan_lever`. This is the exact same pre-existing limitation FN-026's own report documented for the `"thrust"`/`"empuje"` lever (worked around there via the DSE route instead of natural language). The test instead calls `match_plan_lever` directly against a real `reducir_payload` `HandoffContext`, which is what H4 preseeding actually invokes — full coverage of the mechanism, without fighting an unrelated, pre-existing routing quirk.

## CLI probe result

Simulated via direct orchestrator calls (no mocks, real `CalculationEngine`/`FeasibilitySimulator`/`DesignExplorer`), mirroring the contract's CLI VALIDATION section exactly:

```text
reducir payload   → "Plan estratégico — Reducir carga útil:" — 3 strategies,
                    payload_kg lever listed first (action-order default)
                    → "explora opciones" → 2 viable candidates (2.0 kg, 2.8 kg),
                      both below the 4.0 kg baseline — no increase leaked in

aumentar payload  → "Plan estratégico — Aumentar carga útil:" — unchanged
                    3-strategy plan (structure/thrust/hélices), pre-F-1 wording
                    verbatim
```

Non-drone intent-level check (optional per contract, included anyway — cheap and strengthens confidence): `"reducir payload"` on freshly created `dron`/`robot`/`rover` projects all produced `goal_key == "reducir_payload"` identically.

## Findings / remaining risks

- `_prioritize_strategies`'s `reducir_payload` motor-deprioritization is currently a *permanent* no-op-toward-promotion under today's wiring (since `sim_context` never carries `motor_count`) — technically correct per the Engineer lock's literal instruction, but if a future contract widens `sim_context` to include `motor_count` (e.g., for `aumentar_payload`'s existing thrust-first rule to also become architecture-aware), `reducir_payload`'s branch will automatically start promoting the actuator lever once that data is present, with no further code change needed — the conditional is already written for that future, not just today's constant case.
- `_INCREASE_WORDS`/`_DECREASE_WORDS` are intentionally a small, non-exhaustive set (only words needed to satisfy the required table plus the pre-existing compound phrases) — per contract, this is deliberately not a general synonym/NLP layer; future dimensions (F-1b: autonomy, thrust, mass) will need their own review of which direction words apply to their own phrasing before reusing `_direction_of`.
- No change was made to how `"optimiza para reducir payload"`-style **explicit** DSE-goal phrases resolve (untested/unexplored) — `EXPLORE_PATTERNS` requires a "mejor"/"configuracion" keyword alongside the explore verb, which such a phrase wouldn't contain either before or after F-1; the only exercised/working path to `reducir_payload`'s DSE is the Handoff-bound bare `"explora opciones"`, which was proven end to end.
