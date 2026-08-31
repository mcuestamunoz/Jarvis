# Implementation Report — P2-2 Operating Point Bridge (IC 2 / Next Engineering Block)

**Contract:** [`implementation_contract_p2_2_operating_point_bridge.md`](implementation_contract_p2_2_operating_point_bridge.md)
**Implementer:** Claude Code
**Base:** working tree post G24-A (2001 suite) · tag `checkpoint-closure-policy` / docs `73bd9fa`
**Status:** Complete, all slices (P2-1 … P2-7) implemented, full suite green (**2013 passed**, +12 new), CLI probe **6/6 PASS**.

---

## 1. Slices delivered

| Slice | File | Change |
|---|---|---|
| P2-1 | `src/jarvis/core/component_writers.py` | `set_motor_component`: writes `motor_op_power_w`/`motor_op_current_a`/`motor_op_rpm` when `resolution_type ∈ {exact, fallback}` and each field is non-`None`; pops all three on `legacy_estimate` or unbound/freeform. `motor_power_w` untouched everywhere. |
| P2-2 | `src/jarvis/core/calculation_engine.py` | New `effective_motor_power_w(parameters)` — prefers `motor_op_power_w`, falls back to `motor_power_w`. Autonomy branch uses it; gate condition switched from bare `motor_power_w is not None` to `effective_power_w is not None` (equivalent in every real code path, see §3). |
| P2-3 | `src/jarvis/core/electrical_compatibility.py` | `_per_motor_current_a`: `motor_op_current_a` checked first, before catalog `max_current_a`, declared `max_current_a`, and the `motor_power_w/voltage` estimate — locked order, all four branches preserved. |
| P2-4 | `src/jarvis/core/orchestrator.py`, `src/jarvis/adapters/cli/main.py` | New `_motor_op_electrical_from_params` helper + `motor_operating_point_electrical` startup-context key; `render_startup_context` renders a distinct `"Propulsión (OP eléctrico): ..."` line only when present. |
| P2-5 | `tests/test_phase2_lookup_operating_point.py`, `tests/test_electrical_compatibility.py` | 12 new tests (9 + 3). |
| P2-6 | `scripts/cli_probe_p2_2_operating_point_bridge.py` (new) | 6/6 PASS. |
| P2-7 | this report | — |

**Not touched, confirmed by `git diff --stat -- src/`:** `src/jarvis/knowledge/library.py` (zero diff — `resolve_operating_point` matching/selection rules untouched, the contract's hardest constraint), `design_explorer.py`, `project_closure.py`, `action_schema.py`/`CatalogRef`, `pyproject.toml`.

---

## 2. §2 locked semantics — implementation notes

### 2.1 Bridge write/pop rules

Implemented inside the existing `if resolved_op is not None:` block in `set_motor_component`, reusing the pre-existing `if resolved_op.resolution_type in ("exact_operating_point", "fallback_operating_point"):` condition (already present for the `thrust_n` property mutation) rather than duplicating a new check — the OP-electrical write loop lives inside that same branch, and an `else:` on it pops all three keys for `legacy_estimate`. The outer `else:` (resolved_op is `None` — unbound/freeform) also pops all three. Per-field: each of `power_w`/`current_a`/`rpm` is written only when non-`None` on `ResolvedOperatingPoint`, popped individually otherwise — verified live and via `test_bridge_writes_motor_op_keys_fallback`, whose real seed data (`emax_rs2205s_2300`'s only `fallback_only=True` row has `power_w=current_a=rpm=None`) exercises exactly this per-field pop path with real data, not a synthetic one.

**Hashability:** `ResolvedOperatingPoint.power_w`/`current_a`/`rpm` are already typed `float | None` (`library.py:529-532`, unchanged) — no casting needed, no dict/list values introduced into `current_parameters`.

### 2.2 Effective power for autonomy

`effective_motor_power_w` is the single authority the contract asked for — `calculation_engine.py`'s autonomy branch is its only caller. The autonomy gate condition (`if battery_capacity_wh is not None and ... is not None and motors is not None`) now checks `effective_power_w is not None` instead of the bare `motor_power_w is not None`. These are equivalent for every real code path (`motor_op_power_w` can only be non-`None` when `motor_power_w` was already set earlier in the same write, by construction of `set_motor_component`), and using the effective value as the gate avoids a latent mismatch between "what the gate checks" and "what the calc actually uses."

**Regression proof:** `test_autonomy_unchanged_when_no_motor_op_power` — a plain `motor_power_w`-only param dict produces byte-identical autonomy to the pre-P2-2 formula (`(battery_wh / (power_w × motors)) × 60`).

### 2.3 Effective per-motor current

Inserted as a new first check in `_per_motor_current_a`, before the catalog-`max_current_a` branch. All three pre-existing fallback branches (catalog `max_current_a`, declared `max_current_a` on the spec, `motor_power_w/voltage` estimate) are otherwise untouched — only reachable now when `motor_op_current_a` is absent, exactly per the locked order.

**Order proof against real catalog data was not directly possible:** confirmed live (`grep`/direct check) that **no motor in the current seed declares `max_current_a`** — the catalog-rating branch is dead code with today's data regardless of P2-2. `test_i_motor_a_prefers_motor_op_current_over_catalog_max_current_a` proves the order via a `monkeypatch`-injected `MotorSpec` (same pattern as the pre-existing `test_prop_motor_mismatch_calls_library(monkeypatch)` in the same file) rather than real seed data.

### 2.4 `propulsion_resolution` JSON

Left completely unmodified — still written for every `resolved_op is not None` path, still carries only thrust/provenance metadata. The optional "audit mirror" (adding `power_w`/`current_a`/`rpm` into the same JSON blob) was **not** implemented — the contract marks it explicitly optional/non-blocking, and the flat `motor_op_*` keys already satisfy the calc-bridge contract on their own; adding a second copy of the same numbers into the JSON blob would be pure duplication with no consumer, so it was left out (documented here as a disclosed scope decision, not an oversight).

### 2.5 `estado` / CLI display

New context key `motor_operating_point_electrical` (a small dict or `None`) is derived once in `orchestrator.py` and rendered in `adapters/cli/main.py` right after the existing `propulsion_resolution` evidence line. Live-verified output for the validated combo:

```text
Propulsión (evidencia): exact_operating_point · manufacturer_test · 9.7086 N
Propulsión (OP eléctrico): power=432.0 W · current=27.0 A · rpm=23560.0
```

For `legacy_estimate`/freeform, `motor_operating_point_electrical` is `None` and the line is omitted entirely (`test_estado_hides_op_electrical_line_for_legacy`) — no fabricated OP values are ever shown next to a rating-only motor.

---

## 3. Live verification — the contract's validated example, reproduced exactly

```text
emax_rs2205s_2300 + hq_5045_bn @ ~16V (battery_cell_count=4.32):
  resolution_type    = exact_operating_point
  motor_power_w      = 400.0   (catalog max_watts — unchanged)
  motor_op_power_w   = 432.0
  motor_op_current_a = 27.0
  motor_op_rpm       = 23560.0

Autonomy (battery_capacity_wh=100.0):
  with motor_op_power_w (432W × 4):    autonomy_min = 3.4722 min
  rating-only (400W × 4, OP key popped): autonomy_min = 3.75 min
  -> OP-aware calc is honestly lower, as expected (higher real power draw).

electrical_compatibility.i_motor_a: 27.0 (was 25.0 = 400/16 pre-P2-2 estimate)

Legacy SKU (emax_rs2205_2300, no operating_points data):
  resolution_type = legacy_estimate
  motor_power_w   = 250.0 (catalog rating, unaffected)
  motor_op_power_w / motor_op_current_a / motor_op_rpm: absent (popped)

Battery catalog bind (Bat-0 regression, explicit contract requirement):
  binding lipo_4s_5000mah after the motor+propeller exact-OP bind above
  leaves propulsion_resolution, motor_op_power_w, and motor_op_current_a
  completely unchanged — confirmed live (component_writers.set_battery_
  component never calls set_motor_component, so the motor's OP bridge is
  structurally untouched by any battery-only write).
```

---

## 4. Tests added (12)

**`tests/test_phase2_lookup_operating_point.py`** (9 new):
1. `test_bridge_writes_motor_op_keys_exact` — the contract's validated example.
2. `test_bridge_writes_motor_op_keys_fallback` — per-field pop proof using real fallback-row data (all fields `None` for this SKU).
3. `test_bridge_legacy_estimate_no_motor_op_keys`
4. `test_bridge_freeform_motor_no_motor_op_keys`
5. `test_bridge_pops_stale_motor_op_keys_on_divergence_to_legacy` — a prior exact bind's OP keys don't survive a later write that resolves to `legacy_estimate`.
6. `test_autonomy_uses_motor_op_power_when_present`
7. `test_autonomy_unchanged_when_no_motor_op_power` — regression.
8. `test_estado_shows_op_electrical_line_when_resolved`
9. `test_estado_hides_op_electrical_line_for_legacy`

**`tests/test_electrical_compatibility.py`** (3 new):
1. `test_i_motor_a_uses_motor_op_current_when_present`
2. `test_i_motor_a_falls_back_when_no_motor_op_current` — regression.
3. `test_i_motor_a_prefers_motor_op_current_over_catalog_max_current_a` — monkeypatched, per §2.3 above.

**Zero weakened tests.** No existing assertion in either file was changed; both files' pre-existing tests (16 + 14 = 30) pass unmodified.

---

## 5. Tests executed

```text
pytest tests/test_phase2_lookup_operating_point.py -v   → 25 passed (16 pre-existing + 9 new)
pytest tests/test_electrical_compatibility.py -v        → 17 passed (14 pre-existing + 3 new)
pytest tests/ (full suite)                                → 2013 passed (2001 pre-existing + 12 new)
python scripts/cli_probe_p2_2_operating_point_bridge.py   → 6/6 PASS (step 6 = full closure probe, 5/5)
python scripts/cli_probe_g24_apply_by_index.py             → 6/6 PASS (regression, unaffected)
python scripts/cli_probe_battery_catalog_bind_ux.py         → 6/6 PASS (regression, unaffected)
python scripts/cli_probe_closure_policy_propeller_sku.py    → 4/4 + 1 optional PASS (regression, unaffected)
```

Targeted regression sweep (Impl C / DSE / G24 / Closure) also run explicitly: `test_battery_catalog_bind_ux.py`, `test_catalog_bind_v1.py`, `test_impl_c_catalog_dse_thrust_bridge.py`, `test_impl_c_catalog_aware_dse.py`, `test_g24_apply_by_index.py`, `test_design_explorer.py` — 137 passed, all green.

---

## 6. `git diff --stat -- src/`

```text
src/jarvis/adapters/cli/main.py             | 18 ++++++++
src/jarvis/core/calculation_engine.py       | 23 +++++++++-
src/jarvis/core/component_writers.py        | 26 +++++++++++
src/jarvis/core/electrical_compatibility.py | 15 ++++++-
src/jarvis/core/intent_resolver.py          | 52 ++++++++++++++++++++++
src/jarvis/core/orchestrator.py             | 67 +++++++++++++++++++++++++----
6 files changed, 190 insertions(+), 11 deletions(-)
```

`intent_resolver.py` and part of `orchestrator.py`'s diff are the prior, already-reviewed G24-A change carried in the same working tree (this IC's base per the contract's own "checkpoint base: working tree post G24-A"); the P2-2-specific portion of `orchestrator.py` is the `_motor_op_electrical_from_params` helper + one new startup-context key (§2.5).

**Confirms the contract's hardest line: zero `src/jarvis/knowledge/library.py` diff** — `resolve_operating_point`'s matching/selection logic and the OP resolver's own regression contract from P2-1 are completely untouched.

---

## 7. Scope decisions disclosed

1. **`propulsion_resolution` JSON audit-mirror fields not added** — explicitly optional per contract §2.4; flat `motor_op_*` keys already satisfy the calc-bridge requirement with no consumer needing the duplicate. Documented in §2.4 above.
2. **Catalog-`max_current_a` ordering tested via `monkeypatch`, not real seed data** — no motor SKU in the current library declares `max_current_a` (confirmed by direct inspection); the branch is dead code with today's data independent of this IC. Used the same monkeypatch pattern the file already established (`test_prop_motor_mismatch_calls_library`).
3. **Autonomy gate condition changed from `motor_power_w is not None` to `effective_power_w is not None`** — functionally equivalent for every real code path (§2.2), chosen to keep the gate and the consumed value in sync rather than risk a future divergence between the two.
4. **CLI probe step 6 shells out to `cli_probe_requirements_closure.py`** as a subprocess rather than re-implementing its 5 assertions inline — reuses the existing, already-reviewed probe verbatim as the closure regression gate, matching the contract's "(or run subset import — full 5/5 preferred)" guidance by preferring the full run.

---

## 8. Gate check (contract §6)

| Criterion | Result |
|---|---|
| Validated combo: `motor_power_w==400`, `motor_op_power_w==432`, `motor_op_current_a==27` | **PASS** |
| `legacy_estimate` and freeform: zero `motor_op_*` keys; legacy autonomy/current unchanged | **PASS** |
| Autonomy uses OP power when present; electrical uses OP current when present | **PASS** |
| `estado` shows rating vs OP distinctly when OP exists | **PASS** |
| Full suite green; probe 6/6; closure probe 5/5 unchanged | **PASS** — 2013/2013, 6/6, 5/5 |
| `git diff` confirms no `library.py` OP resolver logic changes | **PASS** |
| G24-A tests/probe still pass | **PASS** — 6/6, zero regressions |
| Zero weakened tests without disclosure | **PASS** |

**Ready for Cursor review.**

---

## 9. Queue

```text
IC 2 (P2-2) PASS (pending Cursor review)
  ↓
Engineer: optional checkpoint (checkpoint-p2-2-op-bridge)
  ↓
Version decision (★5) — single 0.3.x tag covering G24-A + P2-2, Engineer's call
  ↓
Deferred queue unchanged: H5 · G24-B · G24-C · Validation Case · frankenstein .name cleanup
```

No tag created, no push, no version bump — all explicitly out of scope for this contract, left for Engineer.
