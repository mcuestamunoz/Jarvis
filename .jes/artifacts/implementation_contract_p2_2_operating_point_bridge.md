# Implementation Contract — P2-2 Operating Point Bridge (IC 2 / Next Engineering Block)

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Phase 2 continuation — bridge **already-resolved** operating-point electrical data (`power_w`, `current_a`, `rpm`) from `resolve_operating_point` into `current_parameters`, and wire calc/electrical consumers to prefer OP values when present. **Does not** change OP matching rules, DSE, G24, H5, or Validation Case dataset work.

**Investigation:** [`.jes/artifacts/investigation_report_next_engineering_block.md`](investigation_report_next_engineering_block.md) — §3 P2-2  
**IC 1 (closed):** [`.jes/artifacts/implementation_review_g24_a_apply_by_index.md`](implementation_review_g24_a_apply_by_index.md) — **ACCEPTED**  
**Checkpoint base:** working tree post G24-A (**2001** suite) · tag **`checkpoint-closure-policy`** / docs **`73bd9fa`**

**Arc position:** IC **2 of 2** (Next Engineering Block). **Real World Validation Case** explicitly **out of scope** — separate future investigation.

**Workflow:** Claude implements **P2-1 → P2-6 in order** + report → Cursor review → CLI probe → checkpoint/version if Engineer asks.

---

## 0. Engineer ratification (locked — ★ P2-2 Option A)

| ★ | Decision |
|---|---|
| **Semantic rule** | **Catalog rating ≠ Operating Point.** Never conflate the two in one field. |
| **`motor_power_w`** | **Unchanged meaning** — catalog `max_watts` / bind rating. **Never** overwrite with `resolved_op.power_w`. |
| **OP flat keys** | Add **`motor_op_power_w`**, **`motor_op_current_a`**, **`motor_op_rpm`** to `current_parameters`. |
| **Write gate** | Set `motor_op_*` **only** when `resolution_type ∈ {exact_operating_point, fallback_operating_point}`. |
| **`legacy_estimate`** | **No** `motor_op_*` keys. `motor_power_w` and all legacy consumers **byte-identical** to baseline. |
| **Autonomy calc** | Use `motor_op_power_w` when present; else `motor_power_w`. |
| **Electrical current** | Use `motor_op_current_a` when present; else existing fallback chain (`max_current_a` → declared → `motor_power_w/voltage`). |
| **`motor_op_rpm`** | Bridge only — **no new calc/control consumers** in this IC. |
| **`propulsion_resolution`** | Remains JSON provenance blob for thrust/resolution metadata. **Not** the sole calc store — `motor_op_*` are the calc bridge. |
| **`estado` / CLI** | Show **both** when OP exists: catalog rating (`motor_power_w`) **and** OP electrical (`motor_op_*`). Do not present OP as nominal rating. |
| **Version bump** | **Out of scope** — Engineer call after review PASS (★5). |

**Validated example (must reproduce in tests/probe):**

```text
emax_rs2205s_2300 + hq_5045_bn @ ~16 V (exact_operating_point):
  motor_power_w      = 400.0   # catalog max_watts — unchanged
  motor_op_power_w   = 432.0   # resolved OP
  motor_op_current_a = 27.0
  motor_op_rpm       = [from OP row when present]
```

---

## 1. Problem / intent

### 1.1 Today

P2-1 (`resolve_operating_point`, `component_writers.set_motor_component`) already resolves `power_w`, `current_a`, `rpm` on `ResolvedOperatingPoint` (`library.py:506-537`) but the bridge writes only:

- `per_motor_max_thrust_n` ← `resolved_op.thrust_n`
- `propulsion_resolution` ← JSON (thrust/resolution metadata — **not** electrical fields)

`motor_power_w` is set from catalog **`max_watts`** at bind time (`component_writers.py:229-230`), never from OP.

**Downstream impact (live on baseline):**

| Consumer | Today | Gap |
|---|---|---|
| `calculation_engine.py:164-170` | `total_power = motor_power_w × motors` | Uses 400 W not 432 W (~7–8% autonomy error) |
| `electrical_compatibility._per_motor_current_a` | Falls back to `motor_power_w / voltage` when no `max_current_a` | Uses 25 A not 27 A (~7.4%) |
| `estado` / CLI | Shows propulsion_resolution thrust provenance | No OP electrical vs rating distinction |

### 1.2 Target

After bind + OP resolution (exact or fallback):

```text
current_parameters:
  motor_power_w       = catalog rating (always when bound)
  motor_op_power_w    = resolved_op.power_w   (when exact/fallback)
  motor_op_current_a  = resolved_op.current_a (when exact/fallback)
  motor_op_rpm        = resolved_op.rpm       (when exact/fallback and non-None)
  propulsion_resolution = JSON (unchanged role + optional mirror fields OK but not required for PASS)
```

Calc/electrical read OP-first; legacy_estimate and freeform paths unchanged.

---

## 2. Locked semantics (non-negotiable)

### 2.1 Bridge write rules (`component_writers.set_motor_component`)

Inside the existing `if resolved_op is not None:` block:

**When `resolution_type in ("exact_operating_point", "fallback_operating_point")`:**

- Write `motor_op_power_w`, `motor_op_current_a`, `motor_op_rpm` from `resolved_op` when each respective field is **not None** on `ResolvedOperatingPoint`.
- **Pop** any `motor_op_*` key whose source field is `None` (do not leave stale OP from a prior bind).
- **Do not** modify `motor_power_w` in this block — it stays whatever bind passed in (`max_watts`).

**When `resolution_type == "legacy_estimate"`:**

- **Pop** all `motor_op_*` keys (`motor_op_power_w`, `motor_op_current_a`, `motor_op_rpm`).
- Keep existing `propulsion_resolution` + `per_motor_max_thrust_n` legacy behavior unchanged.

**When `resolved_op is None` (freeform / unbound):**

- Pop all `motor_op_*` keys (same as legacy path for electrical bridge).
- Existing freeform thrust bridge unchanged.

**Hashability lock:** `motor_op_*` values must be **plain floats** (same discipline as `per_motor_max_thrust_n` — no dict/list values in `current_parameters`).

### 2.2 Effective power for autonomy

Add a small helper (module-level in `calculation_engine.py` or shared util — **single authority**):

```text
effective_motor_power_w(parameters) :=
    parameters["motor_op_power_w"]
    if present and not None
    else parameters["motor_power_w"]
```

Use `effective_motor_power_w × motor_count` for `calculate_autonomy_min`. **Do not** change thrust, mass, or propulsion resolution logic.

### 2.3 Effective per-motor current (`electrical_compatibility.py`)

At the **start** of `_per_motor_current_a` (before catalog `max_current_a` lookup is acceptable **if Engineer order preserved** — locked order below):

```text
1. params["motor_op_current_a"]  if present → return float
2. catalog motor max_current_a   (existing)
3. declared max_current_a on spec  (existing)
4. motor_power_w / voltage       (existing — uses catalog rating, not OP power)
```

**Rationale:** OP current is the most specific measured value for the resolved combo; catalog peak current and power/voltage estimate remain fallbacks when OP absent.

### 2.4 `propulsion_resolution` JSON

**Minimum for PASS:** unchanged obligation — still written for all `resolved_op is not None` paths.

**Optional (non-blocking):** append `power_w`, `current_a`, `rpm` to the JSON blob for audit mirror. If omitted, PASS still holds when `motor_op_*` bridge + consumers are correct.

**Forbidden:** making calc/electrical read **only** from JSON — flat `motor_op_*` keys are the calc contract.

### 2.5 `estado` / startup context display

**Touch surface:** `orchestrator._build_startup_context` (pass through from `current_parameters`) + `adapters/cli/main.py` `render_startup_context`.

When any `motor_op_*` present, add a **distinct** line block after the existing propulsion_resolution evidence line, e.g.:

```text
Propulsión (OP eléctrico): power=432 W · current=27 A · rpm=…
```

When only `motor_power_w` (no OP keys), do **not** show fake OP values.

**Must not** relabel `motor_op_power_w` as "potencia motores" or replace catalog rating display — rating stays in param/calc context as today; OP is additive evidence.

---

## 3. Implementation slices (P2-1 … P2-6)

Execute **in order**. Each slice should leave the suite green.

### P2-1 — Bridge (`component_writers.py`)

- Implement §2.1 write/pop rules in `set_motor_component`.
- **Do not** change `resolve_operating_point` (`library.py`).
- **Do not** change when `resolve_operating_point` is called or voltage/propeller selection logic.

### P2-2 — Autonomy consumer (`calculation_engine.py`)

- Implement `effective_motor_power_w` helper per §2.2.
- Wire into autonomy branch only (`build()` energy section ~164-170).
- Regression: project with only `motor_power_w` (no OP keys) → identical autonomy to baseline.

### P2-3 — Electrical consumer (`electrical_compatibility.py`)

- Implement §2.3 preference order in `_per_motor_current_a`.
- Add/adjust tests in `tests/test_electrical_compatibility.py` for OP-current path (catalog-bound combo with `motor_op_current_a` set on state — minimal synthetic `ProjectState` or param dict pattern already used in that file).

### P2-4 — Estado display (`orchestrator.py` + `adapters/cli/main.py`)

- Expose `motor_op_power_w`, `motor_op_current_a`, `motor_op_rpm` in startup context (or derive display from `current_parameters` already in context).
- Render §2.5 distinct OP electrical line when any OP key present.

### P2-5 — Tests

**Extend** `tests/test_phase2_lookup_operating_point.py` (primary gate — do not weaken existing 16 tests):

| Test (indicative name) | Assert |
|---|---|
| `test_bridge_writes_motor_op_keys_exact` | `emax_rs2205s_2300` + `hq_5045_bn` + matching voltage → `motor_power_w==400`, `motor_op_power_w==432`, `motor_op_current_a==27`, `motor_op_rpm` present if OP row has rpm |
| `test_bridge_legacy_estimate_no_motor_op_keys` | `emax_rs2205_2300` legacy → no `motor_op_*`; `motor_power_w` unchanged |
| `test_bridge_freeform_motor_no_motor_op_keys` | Existing freeform test pattern — no OP keys |
| `test_autonomy_uses_motor_op_power_when_present` | Calc engine / orchestrator calc path: autonomy lower with OP power than rating-only (or direct calc_engine unit) |
| `test_electrical_uses_motor_op_current_when_present` | `_per_motor_current_a` returns 27 not 25 for validated combo |

**Zero weakened tests.** Any change to existing P2-1 assertions must be disclosed with rationale (same discipline as prior ICs).

**Bat-0 regression (locked):** battery catalog bind must **not** re-call `set_motor_component` in a way that clears OP keys or downgrades `exact`→`fallback` — if battery bind path touches motor writer, assert OP preserved; prefer existing IC 2 closure test pattern (`test_impl_c` / battery UX tests) — run relevant battery bind tests unchanged.

### P2-6 — CLI probe (`scripts/cli_probe_p2_2_operating_point_bridge.py`)

Deterministic probe — **no LLM**.

| Step | Action | Pass criterion |
|---|---|---|
| 1 | Create project; bind motor `emax_rs2205s_2300` + propeller `hq_5045_bn` + voltage ~16 V (battery catalog or cell count) | `motor_power_w == 400.0` |
| 2 | Inspect `current_parameters` after bind | `motor_op_power_w == 432.0`, `motor_op_current_a == 27.0` |
| 3 | `calcular` / calc path | `autonomy_min` reflects OP power (≠ autonomy if only 400 W used) |
| 4 | `estado` | Shows distinct OP electrical line; does not conflate with rating |
| 5 | Legacy motor SKU (`emax_rs2205_2300`) bind | No `motor_op_*` keys; behavior unchanged |
| 6 | Closure smoke | `cli_probe_requirements_closure.py` still **5/5** (or run subset import — full 5/5 preferred) |

Target: **6/6 PASS**.

### P2-7 — Implementation report

`.jes/artifacts/implementation_report_p2_2_operating_point_bridge.md` — slices, test/probe counts, Bat-0 check, explicit confirmation `library.py` OP matcher untouched.

---

## 4. Files — expected touch set

| File | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | P2-1 |
| `src/jarvis/core/calculation_engine.py` | P2-2 |
| `src/jarvis/core/electrical_compatibility.py` | P2-3 |
| `src/jarvis/core/orchestrator.py` | P2-4 (startup context only — minimal) |
| `src/jarvis/adapters/cli/main.py` | P2-4 (render only) |
| `tests/test_phase2_lookup_operating_point.py` | P2-5 (extend) |
| `tests/test_electrical_compatibility.py` | P2-5 (extend) |
| `scripts/cli_probe_p2_2_operating_point_bridge.py` | P2-6 (new) |

**Must NOT change:**

- `src/jarvis/knowledge/library.py` — `resolve_operating_point` matching/selection rules (P2-1 ★-locked)
- `design_explorer.py`, G24 apply path, `_score_candidate`
- `CatalogRef` / H5 / ESC catalog
- `project_closure.py`, requirements closure, G27
- `pyproject.toml` version
- Real World Validation Case dataset / new library SKUs

---

## 5. Explicit non-goals (this IC)

- Overwriting `motor_power_w` with OP power (Option B — **rejected**)
- Reading calc/electrical **only** from `propulsion_resolution` JSON
- New DSE grids / explore ranking / G24 work
- Frankenstein `.name` after G5 (G24/G5 debt)
- `motor_op_rpm` feeding new control/RPM calculations
- Validation Case harness / manufacturer comparison report
- H5 ESC catalog
- Version bump / tag — Engineer after review

---

## 6. Acceptance (Cursor review)

**PASS** if:

- Validated combo: `motor_power_w==400`, `motor_op_power_w==432`, `motor_op_current_a==27` after bind
- `legacy_estimate` and freeform: **zero** `motor_op_*` keys; legacy autonomy/current unchanged
- Autonomy uses OP power when present; electrical uses OP current when present
- `estado` shows rating vs OP distinctly when OP exists
- Full suite green; probe **6/6**; closure probe **5/5** unchanged
- `git diff` confirms **no** `library.py` OP resolver logic changes
- G24-A tests/probe still pass (no regression on 2001 baseline)
- Zero weakened tests without disclosure

**FAIL** if:

- `motor_power_w` overwritten by OP values
- `motor_op_*` written on `legacy_estimate`
- `resolve_operating_point` matching rules changed
- Calc reads OP from JSON only without flat keys
- DSE / G24 / Closure behavior regresses

---

## 7. Queue after IC 2

```text
IC 2 PASS + probe 6/6
  ↓
Engineer: optional checkpoint (e.g. checkpoint-p2-2-op-bridge)
  ↓
Version decision (★5) — single 0.3.x tag covering G24-A + P2-2 if Engineer chooses
  ↓
Deferred queue unchanged: H5 · G24-B · G24-C · Validation Case · frankenstein .name
```

---

**End of contract.**
