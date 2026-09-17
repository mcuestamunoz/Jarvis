# Implementation Report — Gate SYSTEM_DEFINITION B-path until ComponentRule exists (`B1-system-definition-block-gate`)

**IC:** [implementation_contract_system_definition_block_gate_b1.md](implementation_contract_system_definition_block_gate_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-15
**Baseline:** package `0.4.1` · suite 2929 → **2938** (9 new tests)

---

## Branch taken: investigation B1-min (a), gate only

No `ComponentRule` was added for cameras/lidar/radio/payload_bay/arm/wheels/gearbox. No catalog row. No mass/mm invented. No wizard mission nudge. No Continuity rewrite. No version bump. No `workspace/` mutation (tests-only, per lock #10's default — `dron-de-vigilancia-doméstico` never took the "B" path in its own live smoke, so there was nothing to clean up there either, confirmed by re-reading its live `state.json` components list from the prior investigation: no `cameras`/`lidar`/`radio_module`/`payload_bay` key present).

## The gate

`system_architecture_catalog.block_components_are_resolvable(block, registry=None)` (new, lives next to `BLOCK_TO_COMPONENTS`/`blocks_to_component_keys` per lock #4): returns `True` iff every component key `BLOCK_TO_COMPONENTS[block]` expands to already has a matching `suggested_key` in the registry (default: the live `aerial_registry`, resolved via a **local** import to avoid a cycle — `aerial.py` itself already imports `VEHICLE_TYPE_ALIASES` from this same module at module level, so a module-level import the other way would be circular). A block absent from `BLOCK_TO_COMPONENTS`, or mapping to an empty component list, is vacuously `True` (`all()` over an empty sequence) — that is exactly the pre-existing "unknown/no-alias free-text block" path, left byte-identical.

`ComponentRuleRegistry` gained one new public method, `known_suggested_keys() -> frozenset[str]` (`component_rules.py`), so the gate never reaches into the registry's private `_rules` list — consistent with this codebase's established "never import another module's `_`-prefixed internals" discipline.

**Confirmed live, against the real `aerial_registry`:**

| Block | Resolvable? |
|---|---|
| `propulsion`, `energy`, `structure`, `control` | ✅ True |
| `perception`, `communication`, `payload`, `manipulation`, `actuation`, `transmission` | ❌ False |

Matches the IC's own "7 keys only" claim exactly: `known_suggested_keys()` returns `{motors, propellers, esc, battery, frame, flight_controller, sensors}`.

## Where it's wired (lock #4 — single helper, two call sites)

Both places `system_definition_session.py` turns a recognized `normalize_block_alias(...)` result into an appended block now check the gate first:

- `_handle_choice`'s implicit-B-via-alias branch (typing a block name directly at step 0).
- `_handle_custom_blocks`'s explicit alias branch (step 1, the normal "add blocks one by one" loop).

Both now call a new shared private method, `_refuse_unresolvable_block(self, block, session, ctx)`, so the refuse response (message text + step transition) is defined **once**, not duplicated at both call sites. On refuse: the session stays in SYSTEM_DEFINITION, moves to (or stays at) step 1 so the user can immediately try another block or finish, **never** appends to `custom_blocks`, **never** calls `_build_component_stubs`. Confirmed live: after refusing `"visión artificial"`/`"camara"`/`"comunicación"`/`"payload"`, `saved.design_properties.components` contains **none** of `cameras`/`lidar`/`radio_module`/`payload_bay` — only the base architecture's own 7 keys.

## Refuse message (exact string, lock #5)

```text
Todavía no puedo resolver componentes reales para '{block}' — no lo añado
para no dejar un hueco que nunca podría completar. ¿Otro bloque? (o 'listo'
para terminar)
```

`{block}` is the canonical block name (`perception`, `communication`, etc.) — chosen over echoing the user's own raw text, since the canonical name is what a Cursor/Engineer reader would grep for in `BLOCK_TO_COMPONENTS`, and it's stable across every alias that maps to the same block (`"camara"`/`"visión artificial"`/`"lidar"` all refuse with the identical, single canonical name `'perception'`).

## Step-1 prompt copy (lock #6)

Both places that show the "example blocks" line (`start()`'s unknown-domain branch, and `_handle_choice`'s Option-B branch) were changed from:

```text
Ejemplo(s): 'visión artificial', 'comunicación', 'payload'
```

to:

```text
Ejemplo: 'batería', 'frame', 'control'
```

All three new examples map to `energy`/`structure`/`control` — confirmed resolvable (`block_components_are_resolvable` returns `True` for all three), and confirmed by a dedicated test (`test_step1_prompt_examples_are_all_resolvable`) that none of `cámara`/`comunicación`/`payload` appear in the live prompt text anymore.

## Option A / base architecture — unaffected (lock #7)

`_apply_and_finish`'s Option-A call path uses `ctx["proposed_blocks"]`/`ctx["proposed_component_keys"]` — the base architecture's own blocks (`propulsion`/`energy`/`structure`/`control` for `"dron"`), which are always resolvable (T2) and were never routed through the new gate at all (the gate only guards the alias-acceptance branches, not the pre-computed base-architecture path). Confirmed: Option A on a fresh dron project still produces exactly the same 7-key stub set as before this Buy.

## Existing test inverted (lock #8)

`test_answer_b_then_vision_then_listo` used to assert `"cameras" in saved.design_properties.components` and `"lidar" in ...` — the exact bug this Buy closes. Rewritten in place (not deleted) to assert the refuse message appears and neither key is created, with a docstring explaining the inversion so a future reader never mistakes this for an unexplained behavior flip.

## Files changed

- **`src/jarvis/core/component_rules.py`** — new `ComponentRuleRegistry.known_suggested_keys()`.
- **`src/jarvis/core/system_architecture_catalog.py`** — new `block_components_are_resolvable(block, registry=None)`.
- **`src/jarvis/core/system_definition_session.py`** — both alias-acceptance branches gated; new `_refuse_unresolvable_block` helper; both example-copy lines updated.
- **`tests/test_system_definition_session.py`** — `test_answer_b_then_vision_then_listo` inverted; 9 new tests (T1–T6 plus a registry-injection proof and the prompt-copy check).

No `aerial.py` edit. No catalog/library edit. No version bump.

## Tests

Executed: `python -m pytest -q` → **2938 passed, 1 skipped** (0 failed). Ran `tests/test_system_definition_session.py` alone first (50 passed, was 41) before the full suite.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| T1 | `test_t1_dead_blocks_are_not_resolvable`, `test_t1_helper_respects_injected_registry` |
| T2 | `test_t2_live_blocks_are_resolvable`, `test_t2_unknown_block_is_vacuously_resolvable` |
| T3 | `test_t3_mode_b_camara_refused_no_stub`, `test_answer_b_then_vision_then_listo` (rewritten) |
| T4 | `test_t4_mode_b_comunicacion_and_payload_refused_no_stub` |
| T5 | `test_t5_mode_b_resolvable_alias_still_works`, `test_t5_option_a_still_creates_default_stubs_unaffected` |
| T6 | Full suite green above; `pyproject.toml` still `0.4.1` |

Additional coverage: `test_step1_prompt_examples_are_all_resolvable` (lock #6, not separately IDed in the IC's own table but explicitly required by lock #6's own text).

## Non-goals honored

No `ComponentRule` added for any dead-block key. No `library/cameras`/mass/mm invented anywhere. No wizard "vigilancia" nudge. No Continuity `increase_payload` rewrite. No Conversation Engine. No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation (confirmed via `git status --short -- workspace/`, empty; `dron-de-vigilancia-doméstico`'s live state was re-checked and already had zero dead-block stubs, so no cleanup was needed or performed there).

## Remaining risks / notes for review

- The refuse message's canonical-name choice (`'perception'` rather than echoing `"visión artificial"`) is a small UX judgment call — if Cursor/Engineer prefer echoing the user's own typed phrase instead, that's a one-line change to `_refuse_unresolvable_block`'s f-string, not a structural one.
- `block_components_are_resolvable`'s default registry is hard-locked to `aerial_registry` regardless of the project's actual `vehicle_type` (per the IC's own explicit lock #3 wording) — a ground/robot project naming an actuation/transmission block is refused against the AERIAL registry's own key set, not a ground-domain registry (no such registry is wired into this gate, since `domains/ground.py` was out of this Buy's own investigation scope). This matches the IC exactly but is worth Cursor's explicit confirmation since it means a ground-vehicle custom block could theoretically be refused for the "wrong" reason (aerial registry, not ground) — no ground-domain smoke exists today to have caught this either way.
