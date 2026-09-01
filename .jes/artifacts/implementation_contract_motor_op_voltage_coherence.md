# Implementation Contract — Motor OP Voltage Coherence

**Project:** Jarvis  
**Date:** 2026-08-31  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after approval

**Type:** Bug fix + DSE coherence — closes stale / voltage-incoherent `exact_operating_point` lock-in and DSE explore/apply autonomy cliff. **Not** UX routing (FN-R*). **Not** H5 / G24-B / Validation Case dataset work.

**Investigation:** [`.jes/artifacts/investigation_report_dse_motor_op_dual_truth.md`](investigation_report_dse_motor_op_dual_truth.md)  
**Review:** [`.jes/artifacts/investigation_review_dse_motor_op_dual_truth.md`](investigation_review_dse_motor_op_dual_truth.md) — **PASS WITH NOTES**  
**Ratification:** [`.jes/artifacts/engineer_ratification_dse_motor_op_dual_truth.md`](engineer_ratification_dse_motor_op_dual_truth.md) — **★1–★4 locked**

**Checkpoint base:** tag **`v0.3.3`** / **`checkpoint-validation-case-regression-gate`** · commit `ceb44b4`  
**Pre-fix suite:** **2030 passed, 2 failed (expected), 1 skipped** — `tests/test_dse_motor_op_dual_truth.py`

**Arc:** Motor OP Voltage Coherence @ v0.3.3 → target checkpoint **`v0.3.4`** candidate after review.

**Workflow:** Engineer approves IC → Claude implements slices in order → full suite green → probe → report → Cursor review → checkpoint/version if Engineer asks.

---

## 0. Engineer ratification (locked)

| ★ | Decision | IC obligation |
|---|---|---|
| **★1** | No `exact_operating_point` when `voltage_v is None` | **MOP-1** — resolver change |
| **★2** | Option D explore/apply coherence (acotado) | **MOP-3** — DSE uses live param authority; optional honesty surface **MOP-4** |
| **★3** | CASE A+B sufficient; CASE C not a gate | Flip repro tests; CASE C remains optional post-fix |
| **★4** | Extend P2-2; do not weaken `test_battery_pick_does_not_regress...` | **MOP-2** conditional battery-bind re-resolve + **MOP-5** sibling tests |

**Explicitly NOT in scope:** blanket re-validation on every battery bind (ratification direction (1)); making explore trust stale OP (investigation Option A — **rejected**).

---

## 1. Problem / intent

### 1.1 Root cause (investigation-verified)

```text
resolve_operating_point (library.py)
  voltage_v is None → voltage_matches True for every exact row
        ↓
set_motor_component @ motor/prop bind (no battery yet)
  locks exact_operating_point @ 16.0 V row (432 W) — never validated against real pack
        ↓
set_battery_component @ battery bind
  deliberately does NOT re-call set_motor_component (P2-2/IC2)
        ↓
live current_parameters: motor_op_power_w=432 frozen vs 6S/22.2 V battery
        ↓
DesignExplorer.explore re-normalizes with real voltage → honest params (no 432 W)
        ↓
_handle_apply_exploration merges delta onto stale live params
        ↓
User cliff: explore promises 12.8 min, calcular/apply deliver 7.7 min
```

### 1.2 Target end state

| Surface | After fix |
|---|---|
| Motor/prop bind **without** known battery voltage | **No** `exact_operating_point`; no `motor_op_*` from unvalidated exact row |
| Battery bind after motor/prop | **Conditional** re-resolution at real pack voltage when prior OP was never voltage-validated |
| Battery bind when OP **already** validated at compatible voltage | **No** downgrade — P2-2 regression preserved |
| `calcular` / `simular` / explore baseline / apply result | **Same** autonomy authority (`effective_motor_power_w`) — CASE A+B green |
| Field-walk combo `emax_rs2205s_2300` + `hq_5045_bn` + `lipo_6s_10000mah` | Honest resolution at 22.2 V (fallback per ★6 dataset — **not** stale 432 W exact) |

---

## 2. Locked semantics (non-negotiable)

### 2.1 Resolver — no exact match without known voltage (★1)

In `resolve_operating_point` (`library.py`), **change** exact-row eligibility:

```text
# TODAY (bug):
voltage_matches = voltage_v is None or row_voltage is None or abs(...) <= epsilon

# TARGET:
voltage_matches = (
    voltage_v is not None
    and (
        row_voltage is None
        or abs(float(row_voltage) - voltage_v) <= _OP_VOLTAGE_EPSILON_V
    )
)
```

**Effects (locked expectations):**

| Call | Result |
|---|---|
| `voltage_v=None`, prop bound | **No** exact row selected → fallback/legacy path only |
| `voltage_v=16.0`, `hq_5045_bn` | `exact_operating_point` @ 432 W (existing P2-2 validated combo) |
| `voltage_v=22.2`, `hq_5045_bn` | `fallback_operating_point` @ 10.042 N, `power_w=None` (existing test expectation) |

**Do not** change: max-thrust selection among multiple exact rows; fallback row selection; `_OP_VOLTAGE_EPSILON_V`; propeller SKU matching.

### 2.2 Propulsion resolution metadata — voltage provenance

Extend `propulsion_resolution` JSON written by `set_motor_component` (additive fields only):

```json
{
  "resolution_type": "...",
  "thrust_n": ...,
  "voltage_validated": true | false,
  "resolved_at_voltage_v": <float|null>
}
```

| Condition | `voltage_validated` | `resolved_at_voltage_v` |
|---|---|---|
| `resolve_operating_point` called with `voltage_v is not None` | `true` | that voltage |
| Called with `voltage_v is None` | `false` | `null` |

**Hashability:** JSON string in `current_parameters` only — no nested dict values as param values (existing P2-2 discipline).

### 2.3 Conditional motor re-resolution on battery bind (★4 complement — narrow, not blanket)

After `set_battery_component` succeeds (catalog bind path and freeform path that sets real `battery_cell_count` / catalog nominal voltage), **when all hold:**

1. `components["motors"]` is catalog-bound (`catalog_ref.family == "motor"`), and  
2. Stored `propulsion_resolution.voltage_validated == false` **OR** stored `resolved_at_voltage_v` is incompatible with the **new** pack nominal voltage (same ε as resolver), and  
3. Propellers catalog-bound or present enough for `resolve_operating_point`

→ **Re-call** `set_motor_component` with the **existing** motors `ComponentSpec` (same bind path as propeller pick's motor refresh — do not invent parallel OP logic).

**When NOT to re-call (P2-2 lock):**

- `voltage_validated == true` **and** new battery nominal within ε of `resolved_at_voltage_v` → **no-op** on motor writer (preserves `test_battery_pick_does_not_regress_already_resolved_propulsion_op` for the wizard path where resolution was already stable at pick time).

**Implementation locus (pick one, document in report):**

- Hook inside `set_battery_component` tail, **or**
- `_apply_component_battery_catalog_pick` after `set_battery_component` (mirror propeller pick refresh pattern)

**Forbidden:** unconditional `set_motor_component` on every battery bind (direction (1)).

### 2.4 DSE explore/apply coherence (★2 acotado)

**Single autonomy authority:** `calculation_engine.effective_motor_power_w()` — already exists; must be the power used for explore scoring **and** apply outcomes when params-only.

**MOP-3 rules:**

1. **Params-only baseline + params-only candidates:** `base_params = dict(project_state.current_parameters)` — **do not** run `apply_components_delta(state, {})` to build the params-only grid baseline or deltas. Live state after MOP-1/2 is the honest source of truth.
2. **Component-driven candidates** (`components_delta` non-empty): keep existing `apply_components_delta(normalized_state, comp_delta)` path unchanged.
3. **`_handle_apply_exploration` params-only branch:** merge delta onto live `project_state.current_parameters` (unchanged entry point) — after MOP-1/2 live state matches explore's params-only base, so apply delivers explore's promise.
4. **Optional display (MOP-4):** if `propulsion_resolution.voltage_validated == false` in live state, explore message may append one honest line: *"Línea base usa estimación — voltaje de batería pendiente de validación"* — **read-only**; no new subsystem.

**Forbidden under MOP-3 alone:**

- Changing resolver rules (that's MOP-1)
- Copying stale `motor_op_power_w` into explore to fake agreement (ratification ★2 forbidden row)

### 2.5 P2-2 preserved semantics

| Rule | Status |
|---|---|
| `motor_power_w` = catalog rating, never overwritten by OP | **Unchanged** |
| `motor_op_*` only on exact/fallback with non-None fields | **Unchanged** |
| Autonomy / electrical OP-first consumers | **Unchanged** |
| `legacy_estimate` → no `motor_op_*` | **Unchanged** |

---

## 3. Implementation slices (execute in order)

Each slice should keep or restore suite green except the two intentional repro failures until **MOP-6**.

### MOP-1 — Resolver voltage gate (`library.py`)

- Implement §2.1.
- Update/add unit tests in `tests/test_phase2_lookup_operating_point.py`:
  - `voltage_v=None` + bound prop → **not** `exact_operating_point` (may assert fallback/legacy).
  - Existing 16.0 V exact + 22.2 V fallback tests **must remain green** (adjust only if assertion was accidentally relying on None-matches-all).

### MOP-2 — Voltage provenance + conditional battery re-resolve

- `component_writers.set_motor_component`: write §2.2 JSON fields.
- Battery bind hook: §2.3 conditional `set_motor_component` re-call.
- Verify `test_battery_pick_does_not_regress_already_resolved_propulsion_op` still **passes** without weakening.

### MOP-3 — DSE params-only authority (`design_explorer.py`)

- Split baseline: params-only grid uses live `current_parameters`; component grid keeps normalization.
- Confirm explore baseline autonomy equals `CalculationEngine().build(live_params).autonomy_min` for OP-bound fixtures.

### MOP-4 — Optional honesty line (low priority within IC)

- `orchestrator._handle_explore` message append when `voltage_validated == false`.
- Skip if timeboxed — **not** blocking PASS if MOP-1–3 + tests green.

### MOP-5 — Tests

| Test file | Action |
|---|---|
| `tests/test_dse_motor_op_dual_truth.py` | **Flip** CASE A + B assertions to **PASS** (same fixture; expectations invert). Remove "expected fail" docstring language. CASE C: keep skip or add post-fix if natural. |
| `tests/test_phase2_lookup_operating_point.py` | MOP-1 resolver tests + bridge test that motor bind before battery does not set `motor_op_power_w` from exact row |
| `tests/test_battery_catalog_bind_ux.py` | **No weakening** of `test_battery_pick_does_not_regress...` |
| **New** `test_motor_op_revalidated_on_battery_bind_when_voltage_was_unknown` | ★4 sibling: prop+motor bind without voltage → no exact/`motor_op_power_w` → 6S battery bind → honest fallback at 22.2 V, **no** stale 432 W |
| **New** `test_motor_op_unchanged_on_compatible_battery_bind_when_voltage_validated` | ★4 sibling: battery voltage known before/at motor bind → exact at 16 V → compatible battery swap → OP unchanged |

**Regression anchors (must run unchanged green):**

- `tests/test_g5_dse_iterate_dual_truth.py`
- `tests/test_phase2_lookup_operating_point.py` (full file)
- `scripts/cli_probe_p2_2_operating_point_bridge.py` — **6/6** (may need step ordering note if probe binds motor before battery — document in report)
- `scripts/cli_probe_validation_case_op_dataset.py` — **6/6**

### MOP-6 — CLI probe (`scripts/cli_probe_dse_motor_op_dual_truth.py`)

Deterministic — **no LLM**. Mirror field-walk sequence:

| Step | Action | Pass criterion |
|---|---|---|
| 1 | Create project; bind motor `emax_rs2205s_2300` + prop `hq_5045_bn` **without** battery | **No** `motor_op_power_w=432` from exact; `voltage_validated==false` or no `motor_op_*` |
| 2 | Bind `lipo_6s_10000mah` | Honest resolution at 22.2 V; **no** stale 432 W; thrust consistent with fallback |
| 3 | `calcular` | Autonomy matches `222/(effective_power×4)×60` within rounding |
| 4 | `optimiza para autonomia` | Explore baseline autonomy **equals** step 3 calc autonomy (±0.01 min) |
| 5 | `aplica la mejor` (top candidate) | Post-apply autonomy **equals** explore promise for that candidate (±0.01 min) |
| 6 | `estado` | Shows propulsion evidence; no contradictory OP line |

Target: **6/6 PASS**.

### MOP-7 — Implementation report

`.jes/artifacts/implementation_report_motor_op_voltage_coherence.md` — slices, test/probe counts, P2-2 regression check, explicit note on `test_battery_pick` scenario, field-walk number table (before/after).

---

## 4. Files — expected touch set

| File | Slice |
|---|---|
| `src/jarvis/knowledge/library.py` | MOP-1 |
| `src/jarvis/core/component_writers.py` | MOP-2 |
| `src/jarvis/core/design_explorer.py` | MOP-3 |
| `src/jarvis/core/orchestrator.py` | MOP-4 (optional explore message) |
| `tests/test_phase2_lookup_operating_point.py` | MOP-1, MOP-5 |
| `tests/test_dse_motor_op_dual_truth.py` | MOP-5 (flip) |
| `tests/test_battery_catalog_bind_ux.py` | MOP-5 (new sibling only — do not edit regression test body) |
| `scripts/cli_probe_dse_motor_op_dual_truth.py` | MOP-6 (new) |

**May touch minimally:**

- `src/jarvis/core/orchestrator.py` — `_apply_component_battery_catalog_pick` if hook lives there instead of `set_battery_component`

**Must NOT change:**

- `design_explorer._score_candidate`, G24 viable selection, `_finalize_viable_list`
- H5 / ESC catalog / new library SKUs
- FN-R routing / acquisition maps (separate arc)
- `invalidate_diverged_catalog_refs` thrust-only logic (unless additive voltage helper shares file — document)
- Weaken or delete `test_battery_pick_does_not_regress_already_resolved_propulsion_op`

---

## 5. Explicit non-goals

- Blanket OP re-validation on every battery bind
- Explore preserving stale `motor_op_*` (Option A — rejected)
- Message-only fix without calc coherence (Option E alone)
- CASE C margin-cliff reproduction as merge gate
- H5, G24-B, battery/ESC data curation
- FN-R1–R5 CLI routing fixes
- Version bump in implementer PR (Engineer after review)

---

## 6. Acceptance (Cursor review)

**PASS** if:

- Full suite **green** — **zero** intentional failing repro tests
- CASE A + B in `test_dse_motor_op_dual_truth.py` **pass**
- ★4 sibling tests pass; `test_battery_pick_does_not_regress...` **passes unchanged**
- P2-2 probe **6/6**; Validation Case probe **6/6**
- New probe **6/6**
- Field-walk numbers: explore baseline = live calc; apply delivers explore promise (same fixture as investigation)
- `motor_power_w` never overwritten by OP; P2-2 Option A intact
- Report documents battery-bind hook choice and any probe ordering caveat

**FAIL** if:

- `voltage_v is None` still selects `exact_operating_point`
- Stale 432 W survives motor→prop→6S battery sequence
- DSE explore baseline still disagrees with `calcular` on fixed fixture
- P2-2 compatible-battery regression weakened
- G5 / G24 / Closure probes regress without disclosed rationale

---

## 7. Queue after IC

```text
IC PASS + probe 6/6 + suite green
  ↓
Engineer: checkpoint (e.g. checkpoint-motor-op-voltage-coherence)
  ↓
Version v0.3.4 (recommended)
  ↓
Deferred unchanged: H5 · G24-B · battery/ESC curation · FN-R routing arc
```

---

**End of implementation contract.**
