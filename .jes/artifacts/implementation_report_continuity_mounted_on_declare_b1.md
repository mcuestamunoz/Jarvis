# Implementation Report — Continuity Declare `mounted_on` B1 (CLI / IDLE)

**IC:** [implementation_contract_continuity_mounted_on_declare_b1.md](implementation_contract_continuity_mounted_on_declare_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · suite 2364

---

## Files changed

- `src/jarvis/core/mounted_on_declare_assist.py` (**new**) — **§3.1**: pure parser mirroring `catalog_rebind_assist`'s thinness — no LLM, no state mutation, accent-stripped normalization via the existing `motor_catalog_assist._normalize_help`. Exports `MountDeclareResult` (frozen dataclass: `kind: str`, `component_key`, `target_key`, `candidates`) and `parse_mounted_on_declare(user_input, components) -> MountDeclareResult`.
  - **Gate phrases**: `_CLEAR_RE` (`quita(r) (el) montaje`, `sin montaje`, `desmonta(r)`); SET gate is `_SET_DIRECT_RE` (`montad[ao]s? en`, `montar en`) **or** (`_SET_VERB_RE` = `monta el/la/los/las` **and** a later `\ben\b`) **or** (`_FIJA_RE` = `fija(r)` **and** a later `\ben\b`) — this conjunction is exactly what keeps a bare "por que no puedo montar" at `NONE` (T6): it has no "en" following "montar"/"monta + article", so no SET pattern fires.
  - **Subject resolution** (`_resolve_subject`, §3.2 table, fixed priority order flight_controller > esc > motors > battery > sensors > propellers): matches the canonical key regardless of whether it's actually declared in the project — that check is deliberately left to the orchestrator (§3.4/T8), matching the IC's "return a clear error path from orchestrator (not silent NONE)" instruction.
  - **Target resolution** (`_resolve_target`, §3.3 table): exact declared-key match first, then a unique frame-plate `label` substring match, then `frame_arm`/`frame_cage`/`frame_standoff`/`frame`+`chasis` (only if that key is actually present), then the bare `placa`/`plate` rule (0 plates → unresolved, 1 plate → that key, 2+ plates → `AMBIGUOUS_TARGET` with `(key, label)` candidates sorted by key, per the locked plate rule steps 1-5). **Only searches the text after the first `\ben\b`** — a fix made during implementation (see "Fix" note below) so a subject noun that happens to also be a declared component key can never resolve as its own target (e.g. "esc montado en frame_plate" — see new regression test).
  - An unresolved target with no plate ambiguity involved (e.g. "monta el fc en algo que no existe") also returns `AMBIGUOUS_TARGET`, but with an **empty** `candidates` tuple — the IC's own `Kind` table only lists 4 kinds, so this reuses `AMBIGUOUS_TARGET` for "recognized as a mount phrase but nothing matches" rather than inventing a 5th kind; the orchestrator renders a distinct message for the empty-candidates case (see below). Documented here as a deliberate, minimal-scope choice.
- `src/jarvis/core/orchestrator.py` — **§3.4**: added `_try_handle_mounted_on_declare(self, user_input) -> dict | None` right after `_safe_active_project` (same file region as the other `_try_start_*` IDLE bridges), and wired it into `_handle_user_text_inner` immediately after the existing IDLE catalog-rebind block and **before** FN-005's help-choose chain — matching the IC's "near other IDLE bridges (catalog rebind), before LLM fallback" placement. Behavior exactly as locked:
  - `NONE` → returns `None`, falls through to existing routing unchanged (verified by T9).
  - `AMBIGUOUS_TARGET` with candidates → `{"status": "interactive", "action": "component_description_prompt", "message": "Hay varias placas declaradas. Indica cuál: <key> (<label>), ..."}`; with empty candidates → an honest "No encontré esa parte declarada..." message, same status/action.
  - Subject key not present in the project's `components` → `{"status": "error", ...}` naming the component as not yet declared (T8) — the writer is never called in this case.
  - `SET`/`CLEAR` → calls `set_component_mounted_on` exactly as-is (no forked copy, no changed validation), catches its `ValueError` (dangling target / self-mount — should be rare after parse, per the IC) and surfaces the message, otherwise saves state and returns `{"status": "ok", "action": "component_description_saved", "message": "Declarado: <key> montado en <target>. Se verá en el Board como \"montado en\"."}` or the clear equivalent.
- `tests/test_continuity_mounted_on_declare_b1.py` (**new**) — 16 tests: T1-T6 pure-parse cases (including two extra `NONE`-guard cases and a dedicated regression proving a subject noun can never resolve as its own target), T7 orchestrator happy-path SET (plus a Board-projection smoke assertion, §3.6), T7b ambiguous-path no-write, T7c clear-path, T8 missing-subject honest error, T9 non-regression for `"cambiar frame"` still opening the frame catalog.

## Behavior changed

- IDLE, active-project chat input matching a mount declare/clear phrase now writes `ComponentSpec.mounted_on` via the existing `set_component_mounted_on` writer and persists it — confirmed end-to-end (write → reload → Board projector shows the `"montado en"` field, same projector code from the prior IC, unmodified).
- Ambiguous bare "la placa"/"el plate" with 2+ declared plates never guesses — it lists every plate's key and label and makes no write, confirmed by a test asserting `mounted_on` stays `None` after the ambiguous turn.
- A subject noun that isn't yet a declared component (e.g. "monta la batería..." when `battery` has no `ComponentSpec` yet) returns an honest error and makes no write — confirmed by test.
- No other IDLE phrase's routing changed — the new dispatch returns `None` (a pure pass-through) for anything that isn't recognized as SET/CLEAR/AMBIGUOUS_TARGET, confirmed by the `"cambiar frame"` non-regression test still opening the frame catalog exactly as before.
- `set_component_mounted_on`'s own validation (target/self-mount rejection) is unchanged — the orchestrator calls it as-is and only adds a try/except around it; the parser's own subject/target resolution is deliberately looser (it doesn't need to duplicate the writer's checks) since the writer is the actual enforcement point.

## Fix made during implementation (worth flagging explicitly)

While writing the exact-key-match regression case ("esc montado en frame_plate"), I found that an earlier draft of `_resolve_target` searched the **entire** normalized phrase for a target, which meant the subject's own key (`esc`, when `esc` is itself a declared `ComponentSpec` key) could match as its own target before the real target (`frame_plate`) was ever considered, since `_exact_key_match` iterates over every declared key including the subject's. Fixed by restricting all target-resolution search to the substring **after the first `\ben\b`** — natural for the locked phrase shapes ("X montado en Y", "monta X en Y"), and it also reads more correctly ("the target is whatever comes after 'en'", not "anything in the sentence"). Covered by `test_exact_key_target_esc_montado_en_frame_plate`, which fails without the fix.

## Tests

Executed: `python -m pytest -q` → **2380 passed**, 0 failed (baseline 2364 + 16 new, all in the single new file). Ran the new file alone first (16 passed) before the full suite. No existing test was modified or weakened.

## Non-goals honored

No position/orientation/offset field, no Board edge drawing, no fit/clearance check. `set_component_mounted_on`'s semantics were called, never forked or altered — confirmed via `git diff --stat` showing zero lines changed in `component_writers.py` this cycle. `parent_key`, glyphs, and `ui/**` untouched — confirmed via `git diff --stat` (only `orchestrator.py` modified; `mounted_on_declare_assist.py` and the test file are net-new). No mount inferred from Board `x`/`y`, `localStorage`, BOM co-membership, or cardinality-of-one — the parser's only inputs are the raw user text and the `components` dict's keys/labels, and cardinality-of-one is explicitly handled as a real resolution (exactly one plate declared → that plate), not a "guess" — this matches the IC's own plate-rule step 3, not the forbidden "invent from convenience" pattern. No multi-turn Conversation Engine — this is a single deterministic turn, same class as the idle catalog rebind precedent. No catalog seed touched. No package version bump (`pyproject.toml` still `0.3.8`). No test weakened — the new file is entirely additive; zero existing test files were edited.

## Remaining risk / notes for review

- The IC's own `Kind` table lists exactly 4 kinds; the "target token present but resolves to nothing at all" case (distinct from "ambiguous among named candidates") reuses `AMBIGUOUS_TARGET` with an empty `candidates` tuple rather than a 5th kind, as noted above — flagged for Cursor to confirm this reuse is acceptable rather than requiring a dedicated `UNRESOLVED_TARGET` kind in a follow-up.
- Subject-noun matching is intentionally permissive (fixed regex list, no fuzzy matching) — a genuinely novel phrasing not in §3.2's table (e.g. a nickname not listed) falls through to `NONE`/existing routing rather than being caught, consistent with "deterministic parse, no LLM, no invented mapping."
