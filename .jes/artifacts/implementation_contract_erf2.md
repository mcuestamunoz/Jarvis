# Implementation Contract — ERF-2 Dependency Hardening

**Project:** Jarvis  
**Date:** 2026-08-19  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** Product behavior — deterministic electrical compatibility + Readiness extension (ERF-1 compatible).

**Vision anchor:** [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) §ERF-2  
**Investigation (CLOSED):** [`.jes/artifacts/investigation_erf2_dependency_hardening.md`](investigation_erf2_dependency_hardening.md)  
**Design (CLOSED — Engineer ratified 2026-08-19):** [`.jes/artifacts/design_erf2_dependency_hardening.md`](design_erf2_dependency_hardening.md)

**Checkpoint base:** tag **`checkpoint-erf1`** (`63c427b`)  
**Workflow:** Claude implements **Slices 1→4 in order** + tests + report → Engineer → Cursor review → CLI walk → commit/tag only if Engineer asks. **Do not commit or push unless asked.**

---

## 0. Why this cut

ERF-1 answers **what is missing**. ERF-2 adds **known electrical incompatibilities** without becoming a full solver:

```text
ProjectState + library + components
        ↓
electrical_compatibility.evaluate()  → CompatibilityResult (facts)
        ↓
engineering_readiness (extend)       → gaps + 9 subsystems + INCOMPATIBLE
        ↓
CLI (Slice 4)
```

**Hard rules (inherit ERF-1 + ERF-2 design):**

- `INCOMPATIBLE` **only** when topology + evidence are deterministically established (★3).
- **1 motor ↔ 1 ESC** — compare per-motor draw vs `esc.current_a`, never `× motor_count` on ESC (★4).
- **No** Continuity changes, **no** ERF-1 Slice 4b, **no** KV/voltage gaps, **no** H5 ESC catalog requirement.

---

## 1. Locked decisions (do not re-open)

| ★ | Requirement |
|---|---|
| ★1 | Purpose: detect **known deterministic incompatibilities** — not design the electrical system. |
| ★2 | New module `electrical_compatibility.py` owns **facts**; `engineering_readiness` **aggregates** only. |
| ★★3 | **`INCOMPATIBLE` gate:** never emit `INCOMPATIBLE` without deterministic topology + evidence. Missing → `UNVERIFIABLE` or `INCOMPLETE`. |
| ★4 | **Topology MVP:** conventional multirotor = 1 ESC channel rating per motor; predicate `esc.current_a < I_motor` (per-motor). |
| ★5 | Add `esc` to `BLOCK_TO_COMPONENTS["propulsion"]`. |
| ★6 | ERF-2 gaps **orthogonal** to ERF-1 (sim PASS + ESC undersized → `NOT_ASSEMBLY_READY`). |
| ★7 | H5 ESC catalog **not required** for MVP. |
| ★8 | **Nine subsystems:** ERF-1 eight + `electronics`. **No** `integration` / `communications`. |
| ★9 | **Continuity out of MVP** — Readiness + CLI only (Slices 1–4). |
| ★10 | `GAP-PROP-MOTOR-MISMATCH` = expose `library.match_motor_propeller` — **no duplicate rule**. |
| ★11 | **No** `GAP-MOTOR-ESC-VOLTAGE-MISMATCH` / KV-voltage INCOMPATIBLE. |
| Gap IDs | Stable type IDs (same discipline as ERF-1). |
| Persistence | Derived on read — no new persisted state. |
| ERF-1 | All six ERF-1 gap types + G9-B behavior **must remain**; 40 ERF-1 tests updated where subsystem count changes, behavior otherwise green. |

---

## 2. Out of scope (hard)

| Forbidden |
|---|
| `project_continuity.py` changes |
| ERF-1 Slice 4b |
| `GAP-MOTOR-ESC-VOLTAGE-MISMATCH` or KV/heuristic voltage INCOMPATIBLE |
| ESC JSON catalog / H5 (optional parallel track only) |
| `FeasibilitySimulator` electrical fields |
| Full electrical solver, wiring, connectors, integration geometry |
| `"aplica la mejor"` optimizer |
| Impl C procurement BOM |
| LLM compatibility inference |
| Subsystems `integration`, `communications`, `sensors` |
| Implicit `depends_on` |
| Weakening ERF-1 tests to pass |
| System Map file edits (propose in report only) |
| G17/G14/G13 CLI micro-fixes |
| Commit/push unless Engineer asks |

---

## 3. Modules and public surfaces

### 3.1 New module — `src/jarvis/core/electrical_compatibility.py`

```python
def evaluate_electrical_compatibility(project_state: Any) -> CompatibilityResult:
    """Pure. No I/O. No LLM. Facts only — not gaps."""
```

**Allowed imports:** `project_closure.classify_component`, `knowledge.library.default_library`, `schemas` types, stdlib/math only.

**Forbidden imports:** `engineering_readiness`, `project_continuity`, `orchestrator`, LLM.

### 3.2 Extended module — `src/jarvis/core/engineering_readiness.py`

- Import and call `evaluate_electrical_compatibility` inside `build_engineering_readiness`.
- Add four ERF-2 gap builders; extend subsystem keys and evidence builders.
- Update `_COMPONENT_SUBSYSTEM_MAP`: `"esc": "electronics"` (for gap `blocks[]` and electronics line — was `"propulsion"` in ERF-1).

### 3.3 Architecture — `src/jarvis/core/system_architecture_catalog.py`

```python
"propulsion": ["motors", "propellers", "esc"],
```

### 3.4 CLI — `src/jarvis/adapters/cli/main.py`

Extend `_render_readiness_block` for nine lines + `INCOMPATIBLE` label (no new logic — display only).

---

## 4. Data contracts

### 4.1 `CompatibilityResult`

```python
CheckOutcome = Literal[
    "defined", "missing",           # esc_presence
    "compatible", "undersized",     # esc_vs_motor
    "within_limit", "exceeded",     # battery_discharge
    "compatible", "mismatch",       # prop_motor
    "unverifiable", "not_applicable",
]

@dataclass
class CompatibilityFact:
    check: str           # e.g. "esc_vs_motor"
    outcome: CheckOutcome
    evidence: list[GapEvidence]  # reuse engineering_readiness.GapEvidence shape

@dataclass
class CompatibilityResult:
    esc_presence: CheckOutcome       # defined | missing | unverifiable
    esc_vs_motor: CheckOutcome       # compatible | undersized | unverifiable | not_applicable
    battery_discharge: CheckOutcome  # within_limit | exceeded | unverifiable | not_applicable
    prop_motor: CheckOutcome         # compatible | mismatch | unverifiable | not_applicable
    facts: list[CompatibilityFact]   # optional audit trail; tests may assert on top-level fields
    # computed helpers (optional, for readiness):
    i_motor_a: float | None          # per-motor draw when computed
    i_total_a: float | None          # i_motor * motor_count when computed
    esc_current_a: float | None
    battery_limit_a: float | None
```

JSON-serializable for tests (dataclasses.asdict).

### 4.2 Subsystems v2 — exactly nine keys

```python
SUBSYSTEM_KEYS: tuple[str, ...] = (
    "requirements",
    "architecture",
    "structure",
    "propulsion",
    "energy",
    "electronics",   # NEW
    "control",
    "catalog",
    "bom",
)
```

**Forbidden keys:** `integration`, `communications`, `sensors`, `electronics`-adjacent lines without authority.

### 4.3 Overall rollup (extends ERF-1 §4.5)

```text
NOT_ASSEMBLY_READY if:
  (A) any ERF-1/ERF-2 condition for NOT_ASSEMBLY_READY from ERF-1 still applies
  OR (B) any subsystem verdict ∈ {INCOMPLETE, INCOMPATIBLE, UNVERIFIABLE}
       except ACCEPTED_WARNING_TYPES path unchanged for catalog/propulsion G9-B

ASSEMBLY_READY iff NOT (A or B) and all subsystems contribute per ERF-1 WARNING rules
```

**New explicit rule:** any subsystem with `verdict == INCOMPATIBLE` → `overall = NOT_ASSEMBLY_READY` (even if sim PASS).

---

## 5. Shared predicates (electrical_compatibility)

### 5.0 Topology lock (★4)

```python
def _topology_determinable(project_state: Any) -> bool:
    """MVP: True when vehicle is aerial multirotor with motor_count >= 1."""
    params = getattr(project_state, "current_parameters", None) or {}
    vt = str(params.get("vehicle_type") or "").lower()
    if vt in ("dron", "drone", "quadcopter", "multirotor", "hexacopter", "octocopter", "uav"):
        try:
            return int(params.get("motor_count") or 0) >= 1
        except (TypeError, ValueError):
            return False
    return False
```

If `False` → `esc_vs_motor = unverifiable` (never `undersized` / never INCOMPATIBLE from ESC check).

**MVP assumption when True:** one declared `components["esc"]` entry represents **per-channel ESC rating** replicated for each motor (conventional quad). Do **not** multiply ESC rating by motor count.

### 5.1 Flight-evaluation prerequisites (for GAP-ESC-UNDEFINED)

```python
def _flight_eval_prerequisites_met(project_state: Any) -> bool:
    components = getattr(project_state.design_properties, "components", None) or {}
    motors_t = classify_component("motors", components.get("motors"), project_state)
    battery_t = classify_component("battery", components.get("battery"), project_state)
    return motors_t in ("declared", "defined") and battery_t in ("declared", "defined")
```

### 5.2 Per-motor current `I_motor` (amperes) — priority order

Return `float | None`:

1. **SKU:** if `components["motors"].catalog_ref.family == "motor"`, load `default_library.get_motor(sku).max_current_a` when not None.
2. **Declared props:** `components["motors"].properties["max_current_a"]` if present (future-safe; may be absent today).
3. **Power estimate:** if `current_parameters["motor_power_w"]` and `V_nom` both available:
   ```python
   V_nom = _nominal_pack_voltage_v(project_state)  # §5.3
   I_motor = float(motor_power_w) / V_nom
   ```
4. Else **`None`** → ESC undersized check → `unverifiable`.

### 5.3 Nominal pack voltage `V_nom` (volts)

Return `float | None`:

1. If `components["battery"].catalog_ref.family == "battery"`: use `BatterySpec.nominal_voltage` if set, else `BatterySpec.cells * 3.7` if cells set.
2. Else if `current_parameters["battery_cell_count"]`: `float(cell_count) * 3.7`.
3. Else **`None`**.

### 5.4 ESC declared current `I_esc`

From `components["esc"].properties["current_a"].value` when `classify_component("esc", ...) != "missing"` and property parseable as float.

If ESC missing or no `current_a` → undersized check `unverifiable` (UNDEFINED gap may still fire separately).

### 5.5 Battery pack continuous limit `I_pack_limit`

Return `float | None`:

1. SKU `BatterySpec.max_continuous_current_a` when battery catalog_ref bound.
2. Else SKU: if `c_rating` and `capacity_mah` both set:  
   `I_pack_limit = c_rating * (capacity_mah / 1000.0)`  (Ah × C = A).
3. Else if `c_rating` and `energy_wh` and `nominal_voltage` (or derived V_nom):  
   `capacity_ah = energy_wh / nominal_voltage`; `I_pack_limit = c_rating * capacity_ah`.
4. Else **`None`** → `battery_discharge = unverifiable`.

### 5.6 Total draw `I_total`

When `I_motor` and `motor_count` known:

```python
I_total = I_motor * int(motor_count)
```

Used **only** for battery pack comparison (not ESC).

---

## 6. Compatibility evaluation rules

### 6.1 `esc_presence`

| Outcome | Predicate |
|---|---|
| `missing` | `_flight_eval_prerequisites_met` AND `classify_component("esc", ...) == "missing"` |
| `defined` | `classify_component("esc", ...) in ("declared", "defined")` |
| `unverifiable` | prerequisites not met AND esc not clearly defined |

### 6.2 `esc_vs_motor` (★3, ★4)

Evaluate **only if** `_topology_determinable` AND `esc_presence == defined` AND `I_esc` and `I_motor` both not None:

| Outcome | Predicate |
|---|---|
| `compatible` | `I_esc >= I_motor` |
| `undersized` | `I_esc < I_motor` |
| `unverifiable` | topology false OR esc missing OR I_esc None OR I_motor None |
| `not_applicable` | never in MVP — use `unverifiable` instead |

**Mutual exclusion with UNDEFINED:** if `esc_presence == missing`, force `esc_vs_motor = unverifiable` (do not emit undersized).

### 6.3 `battery_discharge`

Evaluate when `I_pack_limit` and `I_total` both not None:

| Outcome | Predicate |
|---|---|
| `within_limit` | `I_total <= I_pack_limit` |
| `exceeded` | `I_total > I_pack_limit` |
| `unverifiable` | either limit unknown |
| `not_applicable` | battery not declared/defined |

### 6.4 `prop_motor` (★10 — library only)

Evaluate when **both** catalog refs bound:

```python
motor_ref = components["motors"].catalog_ref
prop_ref = components["propellers"].catalog_ref
```

Predicates:

| Outcome | Predicate |
|---|---|
| `compatible` | `motor_ref.family == "motor"` AND `prop_ref.family == "propeller"` AND `default_library.match_motor_propeller(motor_ref.sku, prop_ref.sku) is True` |
| `mismatch` | both families correct AND `match_motor_propeller(...) is False` |
| `unverifiable` | only one side bound, or neither bound, or missing components |
| `not_applicable` | motors/propellers stubs with no catalog path — prefer `unverifiable` over `not_applicable` in implementation if simpler |

**Forbidden:** reimplement diameter tolerance or `compatible_prop_ids` logic outside `library.match_motor_propeller`.

---

## 7. Gap catalog (ERF-2 — four types)

Append to ERF-1 gaps in `build_engineering_readiness`. Same `Gap` DTO. All `depends_on: []`.

### 7.0 Mutual exclusion table

| esc_presence | esc_vs_motor | Gap emitted |
|---|---|---|
| missing | * | `GAP-ESC-UNDEFINED` only |
| defined | undersized | `GAP-ESC-UNDERSIZED` only |
| defined | compatible | none from ESC pair |
| defined | unverifiable | none (electronics may be UNVERIFIABLE) |

### 7.1 `GAP-ESC-UNDEFINED`

| Field | Value |
|---|---|
| **Trigger** | `compatibility.esc_presence == "missing"` |
| **Severity** | HIGH |
| **blocks** | `["electronics", "propulsion", "bom"]` |
| **depends_on** | `[]` |
| **title** | `"ESC not defined"` |
| **evidence** | `[{source: "electrical_compatibility.evaluate", fact: "esc_presence.missing"}, …]` |
| **recommended_next_step** | `{action: "define_component", params: {component_key: "esc"}}` |
| **Verdict mapping** | `electronics: INCOMPLETE`, `bom: INCOMPLETE` if blocked — **not INCOMPATIBLE** |

### 7.2 `GAP-ESC-UNDERSIZED`

| Field | Value |
|---|---|
| **Trigger** | `compatibility.esc_vs_motor == "undersized"` |
| **Severity** | HIGH |
| **blocks** | `["electronics", "propulsion", "energy"]` |
| **depends_on** | `[]` |
| **title** | `"ESC current rating below per-motor demand"` |
| **evidence** | Include numeric `I_esc`, `I_motor`, optional `motor_count` as facts |
| **recommended_next_step** | `{action: "revise_esc_rating", params: {}}` |
| **Verdict mapping** | `electronics: INCOMPATIBLE`, `propulsion: INCOMPATIBLE` |

### 7.3 `GAP-BATTERY-DISCHARGE-EXCEEDED`

| Field | Value |
|---|---|
| **Trigger** | `compatibility.battery_discharge == "exceeded"` |
| **Severity** | HIGH |
| **blocks** | `["energy", "propulsion"]` |
| **depends_on** | `[]` |
| **title** | `"Battery discharge limit exceeded"` |
| **evidence** | `I_total`, `I_pack_limit` facts |
| **recommended_next_step** | `{action: "revise_battery_or_load", params: {}}` |
| **Verdict mapping** | `energy: INCOMPATIBLE` |

### 7.4 `GAP-PROP-MOTOR-MISMATCH`

| Field | Value |
|---|---|
| **Trigger** | `compatibility.prop_motor == "mismatch"` |
| **Severity** | HIGH |
| **blocks** | `["propulsion", "catalog"]` |
| **depends_on** | `[]` |
| **title** | `"Motor and propeller catalog pairing incompatible"` |
| **evidence** | `[{source: "library.match_motor_propeller", fact: "match_false", …}]` |
| **recommended_next_step** | `{action: "revise_propeller_or_motor", params: {}}` |
| **Verdict mapping** | `propulsion: INCOMPATIBLE`; `catalog: INCOMPATIBLE` if match attempted with bound SKUs |

---

## 8. Subsystem evidence and verdict mapping

### 8.1 New — `electronics` evidence builder

| Flag | Predicate |
|---|---|
| `defined` | `classify_component("esc", ...) in ("declared", "defined")` |
| `calculated` | same as defined for ERF-2 MVP |
| `simulated` | simulation dict exists (inherit pattern from ERF-1) |
| `validated` | `sim_status == "pass"` |
| `catalog_bound` | `components["esc"].catalog_ref` set — likely false in MVP; keep honest |

### 8.2 Verdict derivation — INCOMPATIBLE path (★3)

For each subsystem `S`:

1. If any blocking gap with `INCOMPATIBLE`-class mapping affects `S` → `verdict = INCOMPATIBLE`.
2. Else existing ERF-1 derivation (INCOMPLETE, WARNING, PASS, UNVERIFIABLE).

**INCOMPATIBLE-class gaps:** `GAP-ESC-UNDERSIZED`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `GAP-PROP-MOTOR-MISMATCH`.

**INCOMPLETE-class gaps:** `GAP-ESC-UNDEFINED` (+ existing ERF-1 gaps).

**Electronics UNVERIFIABLE when:** no ESC component and prerequisites not met; or ESC present but no current evidence for undersized check and no INCOMPATIBLE gap.

### 8.3 Propulsion / energy interaction

- ESC undersized blocks `propulsion` + `energy` in gap `blocks[]`; energy may stay `PASS` if only propulsion INCOMPATIBLE from ESC — but if `GAP-BATTERY-DISCHARGE-EXCEEDED`, `energy: INCOMPATIBLE`.
- Sim PASS does not suppress INCOMPATIBLE (★6).

---

## 9. Implementation slices (binding order)

### Slice 1 — Compatibility authority

**Files:** `src/jarvis/core/electrical_compatibility.py`, `tests/test_electrical_compatibility.py`

**Deliverables:**

- `evaluate_electrical_compatibility` implementing §5–§6
- Unit tests: undersized, compatible, unverifiable, battery exceeded, prop mismatch (mock library or real catalog SKUs from tests)
- **No** `engineering_readiness` changes yet

**Regression:** existing suite green.

---

### Slice 2 — ESC in architecture

**Files:** `system_architecture_catalog.py`, `tests/test_architecture_progress.py`, `tests/test_fn020_completeness_coherence.py` (if affected)

**Deliverables:**

- `esc` in `BLOCK_TO_COMPONENTS["propulsion"]`
- BOM may list `esc` in `missing` when absent — test fixture

**Do not** require acquisition prompt / `COMPONENT_PROMPTS` change in MVP.

---

### Slice 3 — Readiness extension

**Files:** `engineering_readiness.py`, update ERF-1 tests for nine subsystems, `tests/test_engineering_readiness_erf2_gaps.py`, `tests/test_engineering_readiness_erf2_subsystems.py`

**Deliverables:**

- Four gap builders wired to `CompatibilityResult`
- `SUBSYSTEM_KEYS` → 9; `_COMPONENT_SUBSYSTEM_MAP["esc"] = "electronics"`
- `INCOMPATIBLE` emitted per §8
- ERF-1 gaps unchanged in behavior
- Update:
  - `test_readiness_emits_exactly_eight_subsystems` → **nine**
  - `test_no_electronics_subsystem_lines` → assert `electronics in keys` AND `integration/communications` absent
  - CLI forbidden test: **Electronics must appear** when rendering

**Forbidden:** `project_continuity` import/edits.

---

### Slice 4 — CLI surface

**Files:** `adapters/cli/main.py`, `tests/test_engineering_readiness_cli.py`

**Deliverables:**

- Render **nine** subsystem lines including `Electronics`
- Show `INCOMPATIBLE` verbatim in status column
- TOP GAPS includes ERF-2 gap types when present
- JSON startup context still serializable

---

## 10. Test matrix (required)

| Test | Slice | Asserts |
|---|---|---|
| `test_esc_undersized_per_motor_not_total` | 1 | 20A ESC, 30A I_motor → undersized; must fail if wrongly using ×4 |
| `test_esc_compatible_at_boundary` | 1 | I_esc == I_motor → compatible |
| `test_esc_unverifiable_no_topology` | 1 | non-dron vehicle → unverifiable, not undersized |
| `test_esc_unverifiable_missing_current` | 1 | esc without current_a → unverifiable |
| `test_battery_discharge_exceeded_sku` | 1 | bound battery C-rating + high load |
| `test_battery_discharge_unverifiable_no_sku` | 1 | no limit fields → unverifiable |
| `test_prop_motor_mismatch_calls_library` | 1 | patch/spy `match_motor_propeller` once |
| `test_bom_lists_esc_missing` | 2 | arch expects esc → missing bucket |
| `test_gap_esc_undefined_not_incompatible` | 3 | UNDEFINED → electronics INCOMPLETE |
| `test_gap_esc_undersized_incompatible` | 3 | electronics + propulsion INCOMPATIBLE |
| `test_sim_pass_esc_undersized_not_ready` | 3 | sim pass + overall NOT_ASSEMBLY_READY |
| `test_nine_subsystems_exactly` | 3 | 9 keys, forbidden comms/integration |
| `test_erf1_gaps_still_emit` | 3 | motor catalog gap unchanged |
| `test_erf1_regression_full` | 3 | all prior ERF-1 tests pass (after count renames) |
| `test_cli_shows_electronics_line` | 4 | render includes Electronics |
| `test_cli_shows_incompatible_label` | 4 | INCOMPATIBLE visible |

**Regression guards:** full `pytest` suite; `tests/test_catalog_foundation_v1.py` unchanged behavior for `match_motor_propeller`.

---

## 11. Acceptance criteria (definition of done)

1. `electrical_compatibility.evaluate` exists, pure, no LLM.
2. Four ERF-2 gap types only (+ six ERF-1 unchanged).
3. Nine subsystem lines; no integration/comms.
4. `INCOMPATIBLE` only per ★3 predicates.
5. Per-motor ESC compare (★4) covered by test.
6. `esc` in architecture BOM path.
7. `match_motor_propeller` not duplicated.
8. No Continuity changes.
9. CLI shows nine lines + INCOMPATIBLE.
10. Full suite green; implementation report lists files, tests, risks.

---

## 12. Implementation report template (Claude → Engineer)

```markdown
## ERF-2 Implementation Report

### Slices completed
- [ ] 1 Compatibility authority
- [ ] 2 ESC in architecture
- [ ] 3 Readiness extension
- [ ] 4 CLI surface

### Files changed
- ...

### Behavior changed
- Slice 1-2: none observable until Slice 3
- Slice 3: new gaps + INCOMPATIBLE + 9 subsystems
- Slice 4: CLI Electronics line

### Tests added / updated
- ...

### Tests executed
`pytest tests/test_electrical_compatibility.py tests/test_engineering_readiness*.py -q`
`pytest -q`

### Risks / follow-ups
- Slice 5 Continuity (deferred)
- H5 ESC catalog
- ERF-1 Slice 4b (deferred)
```

---

## 13. Authority clarification

| Question | Authority |
|---|---|
| Is ESC current enough for one motor? | `electrical_compatibility` |
| Is battery C-rating enough for total load? | `electrical_compatibility` |
| Do motor/prop SKUs match? | `library.match_motor_propeller` |
| Which gaps exist / assembly ready? | `engineering_readiness` |
| Does it fly physically? | `simulator` (unchanged) |

---

**End of contract.** Engineer ratifies → send to Claude. **No `src/` until approved.**
