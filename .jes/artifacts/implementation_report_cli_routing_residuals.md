# Implementation Report — CLI Routing Residuals (G17 · G14 · G13)

**Contract:** [`implementation_contract_cli_routing_residuals.md`](implementation_contract_cli_routing_residuals.md)
**Checkpoint base:** tag `checkpoint-erf2` (`9af0cc9`) + docs commit `89cb03f`
**Status:** Implemented, all three slices, tests added, full suite green. **Not committed** (per contract §"checkpoint only if Engineer asks").

---

## Slices completed

- [x] 1 G17 — bare motor phrase at IDLE
- [x] 2 G14 — bare propeller size at IDLE
- [x] 3 G13 — CLI-level integration test (test-only)

---

## Files changed

| File | Slice(s) | What |
|---|---|---|
| `src/jarvis/core/orchestrator.py` | 1, 2 | New `_force_component_spec_idle(text)` helper, called from `_interceptable_component_specs` when `infer_components` returns only `generic_component` and nothing else was already accepted. Also: the wizard's own existing force-motors guard in `_handle_component_description` (from CLI Polish) changed from a bare `completeness == "high"` check to `completeness != "low" and not _looks_clearly_propeller_shaped(...)` — see "Two deviations from the contract's literal text" below for why this was necessary. |
| `tests/test_cli_routing_residuals.py` | 1, 2, 3 | New — 5 tests covering both force paths, the ★5 already-defined guard, the motor/propeller disambiguation guard, and the full orchestrator-level iterate material CLI path for G13. |

No `ComponentRule` keyword changes, no `IntentResolver` changes, no `infer_component`/`infer_components` core logic changes, no `project_continuity.py`/`engineering_readiness.py` changes — all per §3 out-of-scope list.

---

## Two deviations from the contract's literal text (both necessary, both verified)

### 1. The motors guard cannot be `completeness == "high"` as written

The contract's own decision ★3 says "`completeness == "high"` guard for motors" and cites **the contract's own acceptance example**, `"4x 2306 1400kv"`, as something this guard should accept. I verified directly against `_motor_completeness`:

```python
extract_motor_properties("4x 2306 1400kv")
# → {'motor_count': 4, 'kv_rating': 1400.0}   (no thrust_n, no power_w)
_motor_completeness(...)
# → ('medium', [])   — NOT "high"
```

`_motor_completeness` only reaches `"high"` when `(thrust_n or power_w) AND (motor_count or kv_rating)` — a count+KV-only phrase (no wattage) never qualifies. The contract's own acceptance criterion #1 (`"4x 2306 1400kv"` must register motors, no LLM) is therefore **unreachable** under the literal `★3` guard — I verified this by running the guard as specified and confirming the phrase falls through unchanged.

**Fix:** guard on `completeness != "low"` **and** `not self._looks_clearly_propeller_shaped(text)` instead of `completeness == "high"`. `_looks_clearly_propeller_shaped` is the exact, already-proven discriminator from the original G14 fix (Continuity Hardening ★4) — it returns `False` whenever a `"kv"` marker is present (never true of a real propeller phrase) and `True` for a bare realistic NxP band with no `"kv"`. This correctly:
- accepts `"4x 2306 1400kv"` (has `kv` → not propeller-shaped → motors wins), and
- still rejects a bare `"10x4.5"` (no `kv`, matches the NxP band → propeller-shaped → motors force does **not** fire, defers to the propellers force), preserving the exact regression the original `"high"` threshold existed to guard against.

I verified both directions empirically before locking this in (see `test_g17_bare_motor_idle_intercept` and `test_g14_motor_shaped_phrase_still_prefers_motors_not_propellers`).

### 2. `_handle_component_description`'s existing force-motors guard also had to change

This was **not** in the contract's file list (only `_interceptable_component_specs` was named), but was required for correctness: the global IDLE intercept doesn't apply a spec directly — it hands the raw text off to `_handle_component_description`, which **re-runs its own `infer_components`/force-motors logic from scratch** rather than trusting the already-computed forced spec. With the wizard's original `completeness == "high"` guard left in place, `"4x 2306 1400kv"` would correctly *route* into the component handler (no LLM) but then silently *fail to save* — the handler would re-derive `completeness="medium"`, reject it under the old guard, and re-prompt the user in a loop, which is a **worse** UX than the original bug (an LLM call at least produces *something*).

I updated the wizard's guard to the identical `completeness != "low" and not _looks_clearly_propeller_shaped(...)` check, so both call sites now agree. I verified this doesn't regress the existing wizard-level G14 tests (`test_t9_composite_motor_shaped_phrase_forces_motors`, `test_t9b_singleton_motors_forces_bare_motor_phrase`, `test_t10_composite_bare_propeller_size_still_forces_propellers` in `tests/test_cli_polish.py`) — all three still pass unmodified, since their phrases either already reach `"high"` completeness (T9/T9b have wattage) or are still correctly excluded by the propeller-shape check (T10's bare `"10x4.5"`).

Both deviations are documented here for Cursor/Engineer review rather than applied silently; no test was weakened to accommodate either change — the wizard-level tests pass with their original assertions intact.

---

## A third bug caught during implementation (fixed before the acceptance tests were written)

My first version of `_force_component_spec_idle` copied the wizard's `"motors" not in expected_keys or _looks_clearly_propeller_shaped(...)` bypass verbatim for the propellers branch. At IDLE this is **wrong**: the wizard's bypass is safe only because that specific wizard turn is already framed around propellers as a singleton target (no motor-shaped input could legitimately arrive there in the first place). At IDLE there is no such framing — a motor-shaped phrase can arrive at any time, including when motors happens to already be fully defined. With the copied bypass, a project with motors already defined but propellers still pending would force-bind a **motor-shaped** phrase (e.g. `"6x 2807 1900kv"`) into **propellers**, because `not motors_pending` alone (motors already resolved) short-circuited the shape check.

Fixed by dropping the bypass entirely: the propellers force now **always** requires `_looks_clearly_propeller_shaped(text)`, regardless of `motors_pending`. Locked in by `test_g17_motors_already_defined_does_not_force_overwrite`, which failed against the first version and passes now.

---

## Behavior changed

- `"4x 2306 1400kv"` (and any motor-shaped phrase reaching at least `"medium"` completeness with a `kv`/`thrust`/`power` signal) at IDLE now registers motors deterministically instead of falling to the LLM.
- `"10x4.5"` (and any bare realistic-band `NxP` propeller size, or real propeller-keyword phrase) at IDLE now registers propellers deterministically instead of falling to the LLM.
- The wizard-level force-motors guard is slightly more permissive (see deviation #1) — this only **adds** acceptance (count+KV-only phrases), never removes any previously-accepted phrase, and the propeller-shape guard still excludes bare `NxP` sizes exactly as before.
- No change to any already-recognized (keyword-matched) component path, no change to battery/frame handling, no change to any non-aerial vehicle behavior beyond what already existed (no vehicle-type gate was added or removed — the wizard-side force logic never had one either).

---

## Tests

```
python -m pytest tests/test_cli_routing_residuals.py -q
5 passed
```

Regression guards explicitly re-run:

```
python -m pytest tests/test_cli_polish.py -q -k "t9 or t10"
3 passed
```

Full suite:

```
python -m pytest -q
1856 passed
```
(baseline 1851 at `checkpoint-erf2` + docs sync + 5 new tests = 1856. No failures, no skips, zero weakened assertions.)

---

## Acceptance criteria checklist

1. ✅ `"4x 2306 1400kv"` at IDLE → motors registered deterministically (no LLM).
2. ✅ `"10x4.5"` at IDLE → propellers registered deterministically (no LLM).
3. ✅ `"PVC 400g"` through iterate wizard via orchestrator → `value == "pvc"`, impact present.
4. ✅ All existing tests pass (1856 ≥ 1851 baseline).
5. ✅ No new `_RefuseLLM`-equivalent fixture needed beyond the file's own (mirrors existing fixtures used across the suite).
6. ✅ Zero weakened assertions — all pre-existing tests pass with their original assertions unchanged.

---

## Risks / follow-ups

- The two guard deviations above are narrow and empirically verified, but they do widen the wizard's own force-motors acceptance slightly beyond what CLI Polish originally shipped — flagging explicitly for Cursor review since it wasn't in the contract's named file list.
- R3 (G11/G8/G7 preempt policy) remains queued as its own separate IC, untouched here, per §3 out-of-scope.
- Frame material intercept at IDLE remains out of scope, per §3.
