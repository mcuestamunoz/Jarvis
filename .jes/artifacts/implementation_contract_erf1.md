# Implementation Contract — ERF-1 Readiness Foundation

**Project:** Jarvis  
**Date:** 2026-08-18  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** Product behavior — deterministic Engineering Readiness projection over existing authorities.

**Vision anchor:** [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md)  
**Investigation (PASS):** [`.jes/artifacts/investigation_erf1_readiness_foundation.md`](investigation_erf1_readiness_foundation.md)  
**Design (CLOSED — Engineer ratified 2026-08-18):** [`.jes/artifacts/design_erf1_readiness_foundation.md`](design_erf1_readiness_foundation.md)

**Checkpoint base:** `main` @ post-G20 (`14f8370` or later)  
**Workflow:** Claude implements **Slices 1→5 in order** + tests + report → Engineer → Cursor review → CLI walk → commit/tag only if Engineer asks. **Do not commit or push unless asked.**

---

## 0. Why this cut

Jarvis can already compute BOM gaps, catalog gaps, architecture progress, requirements, and simulation verdict — but the answers are scattered across `orchestrator`, `project_closure`, and `project_continuity`. Continuity currently **owns gap ranking**, which makes readiness non-composable and hard to test in isolation.

ERF-1 introduces a **Readiness Aggregator** that is authoritative over **gap aggregation and assembly-ready rollup**, not over physics/BOM/sim truth:

```text
Existing authorities
    ↓ deterministic facts
ERF-1 (engineering_readiness)
    ↓
Gap Registry = authoritative aggregation of unresolved gaps
    ↓
Readiness Snapshot = derived summary (8 subsystem lines + overall)
    ↓
Continuity (Slice 4 only) = human narration consumer
```

**Hard rule:** `build_engineering_readiness` MUST NOT accept Continuity output as input. Continuity MUST NOT be refactored before Slices 1–3 are tested.

---

## 1. Locked decisions (do not re-open)

| ★ | Requirement |
|---|---|
| ★1 | **WARNING acceptance:** subsystem `readiness.verdict == WARNING` contributes to `ASSEMBLY_READY` **only** when `readiness.warning_type ∈ ACCEPTED_WARNING_TYPES` (closed list; see §5.3). All other WARNING → blocks assembly. |
| ★2 | **Gap Registry central:** gaps are primary; subsystem lines and `overall` are derived rollups. |
| ★3 | **Evidence ≠ readiness:** every subsystem line carries separate `evidence` and `readiness` objects. |
| ★4 | **depends_on explicit:** declared per gap type in §6 only — **no implicit inference**. |
| ★5 | **Ranking:** unlockable gaps only; sort by severity HIGH > MEDIUM > LOW; **greater** downstream-unblock impact first; tiebreak `gap_id` lexicographic. |
| ★6 | **Existing authorities:** Readiness composes outputs; does not recompute BOM/classification/sim logic differently. |
| ★7 | **No circularity:** Readiness ↛ Continuity input; Continuity → Readiness forbidden. |
| ★8 | **No LLM gap inference.** |
| ★9 | **Continuity refactor last** (Slice 4). |
| ★10 | **Scope ERF-1:** six gap types only; no ESC/FC/integration/electronics gaps. |
| Gap IDs | Stable type IDs; per-instance suffix `:component_key` when multiple (§6.0). |
| Persistence | **Derived on read** — no `readiness.json`, no parallel persisted ProjectState. |
| Subsystems v1 | **Eight lines only:** `requirements`, `architecture`, `structure`, `propulsion`, `energy`, `control`, `catalog`, `bom`. Do **not** emit `electronics`, `communications`, `integration`. |

---

## 2. Out of scope (hard)

| Forbidden |
|---|
| New Conversation Engine / Decision Engine |
| ESC/FC/integration/electrical-compatibility gap types (ERF-2) |
| `"aplica la mejor"` optimizer |
| Full Impl C SKU/procurement BOM |
| LLM-based gap detection or ranking |
| Persisting readiness snapshot to disk |
| Subsystem lines without authority (`electronics`, `communications`, `integration`) |
| Implicit `depends_on` ("motor before battery because obvious") |
| Refactoring Continuity before Slices 1–3 tests green |
| Weakening existing continuity/catalog tests to pass |
| Editing System Map files (propose text in report only) |
| Commit / push unless Engineer asks |

---

## 3. Module and public surface

**Primary module:** `src/jarvis/core/engineering_readiness.py`

**Public entry point:**

```python
def build_engineering_readiness(project_state: Any) -> EngineeringReadinessResult:
    """Pure projection over ProjectState + existing authority helpers. No I/O."""
```

**Allowed imports (authorities):**

| Source | Use |
|---|---|
| `project_closure.derive_physical_requirements` | requirements facts |
| `project_closure.build_component_bom` | BOM buckets |
| `project_closure.classify_component` | evidence only — do not fork classifier |
| `simulation` results on `project_state.latest_results["simulation"]` | sim verdict |
| `system_architecture_catalog.BLOCK_TO_COMPONENTS` | component → subsystem mapping |
| Extracted pure helpers (this contract) | catalog surface, architecture progress, G9-B predicate |

**Forbidden imports:** `project_continuity` from `engineering_readiness` (circularity). Slice 4 may import readiness from continuity.

**DTOs** (dataclasses or TypedDicts — implementer choice; must be JSON-serializable for tests):

```python
@dataclass
class GapEvidence:
    source: str          # e.g. "project_closure.build_component_bom"
    fact: str            # deterministic fact label

@dataclass
class RecommendedNextStep:
    action: str          # deterministic action key
    params: dict[str, Any]

@dataclass
class Gap:
    gap_id: str          # stable id; see §6.0
    gap_type: str        # e.g. "GAP-BOM-MISSING-COMPONENT"
    instance_key: str | None
    title: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    domain: str
    blocks: list[str]    # subsystem keys from §4.1
    depends_on: list[str]
    evidence: list[GapEvidence]
    recommended_next_step: RecommendedNextStep
    resolved: bool       # always False for emitted gaps in ERF-1

@dataclass
class SubsystemEvidence:
    defined: bool
    calculated: bool
    simulated: bool
    validated: bool
    catalog_bound: bool

@dataclass
class SubsystemReadiness:
    evidence: SubsystemEvidence
    verdict: Literal["PASS", "WARNING", "INCOMPLETE", "INCOMPATIBLE", "UNVERIFIABLE"]
    warning_type: str | None
    blocked_by_gap_ids: list[str]

@dataclass
class EngineeringReadinessResult:
    gaps: list[Gap]
    prioritized_gaps: list[Gap]      # unlockable, sorted per §6.7
    top_gap: Gap | None
    subsystems: dict[str, SubsystemReadiness]   # exactly 8 keys §4.1
    overall: Literal["ASSEMBLY_READY", "NOT_ASSEMBLY_READY"]
```

---

## 4. Subsystem model (v1)

### 4.1 Canonical subsystem keys (exactly these eight)

```text
requirements | architecture | structure | propulsion | energy | control | catalog | bom
```

If a key is missing from `subsystems`, the implementation is **wrong**. Do not add placeholder lines for domains without authority.

### 4.2 Component key → subsystem mapping (for gap `blocks[]`)

Use `BLOCK_TO_COMPONENTS` inverse lookup:

```python
def subsystem_for_component_key(component_key: str) -> str:
    """Return one of: structure | propulsion | energy | control | bom (fallback bom)."""
```

Deterministic rules (ERF-1):

| Component keys (from catalog blocks) | Subsystem |
|---|---|
| `frame`, `landing_gear` | `structure` |
| `motors`, `propellers`, `esc` | `propulsion` |
| `battery` | `energy` |
| `flight_controller`, `sensors`, `gps` | `control` |
| unknown / unmapped | `bom` |

Always include `bom` in `blocks[]` for any BOM gap instance.

### 4.3 Evidence flag predicates (per subsystem)

All predicates are **read-only** over `project_state`, `physical_requirements`, `bom`, `sim`, architecture snapshot, catalog surface.

| Subsystem | `defined` | `calculated` | `simulated` | `validated` | `catalog_bound` |
|---|---|---|---|---|---|
| **requirements** | `parsed_constraints` non-empty | any of thrust/mass/autonomy in calc or sim | `simulation` dict exists | `sim_status == "pass"` | N/A → `False` |
| **architecture** | `design_properties.system_blocks` non-empty | same as defined for ERF-1 | `simulation` exists | arch complete AND sim pass | N/A → `False` |
| **structure** | `classify_component("frame", ...) != "missing"` | `calculations.total_mass_kg` present | sim exists | sim pass AND frame not stub | frame `catalog_ref` set |
| **propulsion** | motors not missing/stub | `required_thrust_n` or thrust_per in req | sim exists | sim pass | motors `catalog_ref` set |
| **energy** | battery not missing/stub | `battery_capacity_wh` in params or calc energy fields | sim exists | sim pass | battery `catalog_ref` set |
| **control** | FC not missing/stub | FC not stub | sim exists | sim pass | FC `catalog_ref` set |
| **catalog** | catalog query attempted when motor constraints exist | thrust_per or kv known | sim exists | sim pass | no active motor catalog gap OR gap G9-B-demoted |
| **bom** | any expected component present | BOM built | sim exists | sim pass | all defined components have `catalog_ref` |

`catalog_bound` for **catalog** subsystem: `True` when `GAP-MOTOR-CATALOG-UNRESOLVED` is absent OR G9-B demotion applies (accepted warning path).

### 4.4 Subsystem verdict derivation

For each subsystem key `S`:

1. Collect `blocking_gaps(S) = { g | g.gap_id in prioritized unresolved gaps AND S ∈ g.blocks }`.
2. If any blocking gap has severity `HIGH` → `verdict = INCOMPLETE` (unless accepted-warning path below).
3. Else if any blocking gap exists → `verdict = INCOMPLETE`.
4. Else if evidence shows subsystem not `defined` → `INCOMPLETE`.
5. Else if accepted-warning condition for `S` (§5.3) → `verdict = WARNING`, set `warning_type`.
6. Else if all evidence flags required for closure are true → `PASS`.
7. Else → `UNVERIFIABLE` (only when sim/calc cannot run — e.g. `status_type == "blocking"` and no simulation).

Set `blocked_by_gap_ids` to sorted list of gap_ids from step 1.

**Note:** `INCOMPATIBLE` is reserved in the enum but **not emitted in ERF-1** unless an existing authority already exposes incompatibility (none today — always use other verdicts).

### 4.5 Overall rollup

```text
ASSEMBLY_READY iff:
  (A) no unresolved gap with severity HIGH
  AND (B) ∀ subsystem S:
        subsystems[S].verdict == PASS
        OR (subsystems[S].verdict == WARNING
            AND subsystems[S].warning_type ∈ ACCEPTED_WARNING_TYPES)

NOT_ASSEMBLY_READY otherwise
```

---

## 5. Accepted WARNING types (closed list — ★1)

Only these entries may satisfy condition (B) for `ASSEMBLY_READY`:

| `warning_type` | Applies to subsystem | Predicate (all must hold) |
|---|---|---|
| `CATALOG-GAP-DEMOTED-POST-PASS` | `catalog` (and may set same on `propulsion` if motor catalog gap active) | `GAP-MOTOR-CATALOG-UNRESOLVED` exists **AND** `catalog_gap_covered_by_declared_thrust(project_state, sim_status, req) == True` |

**G9-B predicate** — must be **byte-for-byte equivalent** to today's `project_continuity._catalog_gap_covered_by_declared_thrust`:

```python
def catalog_gap_covered_by_declared_thrust(
    project_state: Any, sim_status: str, req: dict[str, Any]
) -> bool:
    if sim_status != "pass":
        return False
    declared = (project_state.current_parameters or {}).get("per_motor_max_thrust_n")
    if declared is None:
        return False
    needed = req.get("thrust_per_motor_needed_n")
    if needed is None:
        return False
    return float(declared) >= float(needed)
```

**Slice 1 task:** move this function to `project_closure.catalog_gap_covered_by_declared_thrust` (public). Update `project_continuity` to import it (may happen in Slice 4 to minimize early churn — but readiness must import from `project_closure`, never from continuity).

No other `warning_type` is valid in ERF-1. Narrative "probably OK" WARNING is forbidden.

---

## 6. Gap catalog (exact creation rules)

### 6.0 Gap identity

| Case | `gap_type` | `instance_key` | `gap_id` |
|---|---|---|---|
| Singleton type | e.g. `GAP-SIM-NOT-PASS` | `None` | `GAP-SIM-NOT-PASS` |
| Per-component | `GAP-BOM-MISSING-COMPONENT` | component key | `GAP-BOM-MISSING-COMPONENT:{key}` |
| Per-component | `GAP-BOM-INCOMPLETE-COMPONENT` | component key | `GAP-BOM-INCOMPLETE-COMPONENT:{key}` |

`depends_on` references **`gap_id`** strings (full id with suffix).

### 6.1 Shared helper — motor catalog surface

Extract from `orchestrator.build_startup_context` (lines ~3206–3253) into:

```python
def resolve_motor_catalog_surface(
    project_state: Any, physical_requirements: dict[str, Any]
) -> tuple[str | None, list[dict[str, Any]]]:
    """Returns (catalog_gap_message | None, catalog_matches). Pure. Same logic as orchestrator today."""
```

Orchestrator should call this helper (Slice 3 or 5) to avoid drift — optional but recommended; readiness **must** call it.

### 6.2 Shared helper — architecture progress

Port `orchestrator._next_pending_block` / progress semantics into pure function:

```python
def derive_architecture_progress(project_state: Any) -> dict[str, Any]:
    """Returns {progress, next_block, next_label, next_block_status, is_complete: bool}."""
```

Readiness uses `is_complete == False` OR `next_block is not None` for arch gap.

---

### 6.3 `GAP-MOTOR-CATALOG-UNRESOLVED`

| Field | Value |
|---|---|
| **Trigger** | `resolve_motor_catalog_surface` returns `catalog_gap is not None` (implies `catalog_matches == []` and motor constraints were queried) |
| **Severity** | `MEDIUM` |
| **Domain** | `catalog` |
| **blocks** | `["catalog", "propulsion", "bom"]` |
| **depends_on** | `[]` |
| **title** | `"Motor SKU unresolved"` |
| **evidence** | `[{source: "engineering_readiness.resolve_motor_catalog_surface", fact: "catalog_matches.empty"}, optional thrust/kv/prop facts]` |
| **recommended_next_step** | `{action: "list_motors", params: {}}` if `thrust_per_motor_needed_n` known; else `{action: "explore_design_space", params: {}}` |

**Accepted-warning path:** does **not** remove the gap from registry; demotion affects subsystem verdict + ranking impact (gap still exists but catalog/propulsion lines may show `WARNING` + `CATALOG-GAP-DEMOTED-POST-PASS` when G9-B predicate true). Continuity Slice 4 preserves G9-B narration.

---

### 6.4 `GAP-ARCH-BLOCK-INCOMPLETE`

| Field | Value |
|---|---|
| **Trigger** | `derive_architecture_progress(...).is_complete is False` |
| **Severity** | `MEDIUM` |
| **Domain** | `architecture` |
| **blocks** | `["architecture"]` |
| **depends_on** | `[]` |
| **title** | `"Architecture block incomplete"` (include `next_label` in evidence) |
| **evidence** | architecture progress facts |
| **recommended_next_step** | `{action: "continue_architecture_block", params: {"block": next_block}}` |

---

### 6.5 `GAP-BOM-MISSING-COMPONENT`

| Field | Value |
|---|---|
| **Trigger** | For each `key` in `bom.missing` (from `build_component_bom`) |
| **Severity** | `HIGH` |
| **Domain** | mapped subsystem (§4.2) |
| **blocks** | `[subsystem_for_component_key(key), "bom"]` (dedupe, stable order) |
| **depends_on** | `[]` |
| **title** | `f"{key} not defined"` |
| **evidence** | `[{source: "project_closure.build_component_bom", fact: f"missing.{key}"}]` |
| **recommended_next_step** | `{action: "define_component", params: {"component_key": key}}` |

One gap instance per missing key.

---

### 6.6 `GAP-BOM-INCOMPLETE-COMPONENT`

| Field | Value |
|---|---|
| **Trigger** | For each entry in `bom.incomplete` (stub tier) |
| **Severity** | `MEDIUM` |
| **Domain** | mapped subsystem |
| **blocks** | `[subsystem_for_component_key(key), "bom"]` |
| **depends_on** | `[]` |
| **title** | `f"{key} incomplete"` |
| **evidence** | missing_fields from BOM entry |
| **recommended_next_step** | `{action: "complete_component", params: {"component_key": key, "missing_fields": [...]}}` |

One gap instance per incomplete entry.

---

### 6.7 `GAP-SIM-NOT-PASS`

| Field | Value |
|---|---|
| **Trigger** | Simulation dict exists AND `sim_status = (sim.get("status") or "").lower()` NOT IN `("", "pass", "ok")` |
| **Also trigger when** | `status_type == "blocking"` AND no simulation has run yet (treat as not validated) — emit this gap instead of duplicating param prompts in readiness |
| **Severity** | `HIGH` |
| **Domain** | `requirements` |
| **blocks** | `["requirements", "propulsion", "energy"]` |
| **depends_on** | `[]` |
| **title** | `"Simulation not PASS"` |
| **evidence** | sim status, optional warnings[0] |
| **recommended_next_step** | `{action: "fix_simulation_blocker", params: {"sim_status": sim_status}}` |

Do **not** emit when `sim_status == "pass"` even if BOM gaps exist.

---

### 6.8 `GAP-REQUIREMENTS-UNMET`

| Field | Value |
|---|---|
| **Trigger** | Any of: (a) `max_mass_kg` and `current_mass_kg` both set and `current_mass_kg > max_mass_kg`; (b) `autonomy_target_min` and `current_autonomy_min` both set and `current_autonomy_min < autonomy_target_min`; (c) `status_type == "blocking"` (missing parameters for rigorous sim — from same signal orchestrator uses) |
| **Severity** | `HIGH` for (a)(b); `MEDIUM` for (c) alone |
| **Domain** | `requirements` |
| **blocks** | `["requirements"]` |
| **depends_on** | `[]` |
| **title** | Deterministic per trigger: `"Mass limit exceeded"`, `"Autonomy target not met"`, `"Parameters blocking simulation"` |
| **evidence** | numeric facts from `derive_physical_requirements` |
| **recommended_next_step** | `{action: "resolve_requirement", params: {"kind": "mass"|"autonomy"|"blocking_params"}}` |

Do not double-emit with `GAP-SIM-NOT-PASS` for the same root cause: if (c) triggers, prefer `GAP-REQUIREMENTS-UNMET` only when sim absent; if sim fail exists, `GAP-SIM-NOT-PASS` wins and suppresses (c).

---

### 6.9 `depends_on` matrix (ERF-1 — all empty)

| gap_type | depends_on |
|---|---|
| `GAP-MOTOR-CATALOG-UNRESOLVED` | `[]` |
| `GAP-ARCH-BLOCK-INCOMPLETE` | `[]` |
| `GAP-BOM-MISSING-COMPONENT` | `[]` |
| `GAP-BOM-INCOMPLETE-COMPONENT` | `[]` |
| `GAP-SIM-NOT-PASS` | `[]` |
| `GAP-REQUIREMENTS-UNMET` | `[]` |

Future contracts may add edges; ERF-1 ships no dependencies.

### 6.10 Prioritization algorithm

```python
def prioritize_gaps(gaps: list[Gap]) -> list[Gap]:
    unlockable = [g for g in gaps if all(dep resolved for dep in g.depends_on)]
    # ERF-1: all deps empty → all gaps unlockable unless resolved flag used later

    def unblock_count(g: Gap) -> int:
        return len(set(g.blocks))

    def sort_key(g: Gap) -> tuple:
        sev = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[g.severity]
        return (sev, -unblock_count(g), g.gap_id)

    return sorted(unlockable, key=sort_key)
```

`top_gap = prioritized_gaps[0] if prioritized_gaps else None`

**G9-B note:** do not remove catalog gap from list when demoted; demotion affects subsystem WARNING acceptance only. Ranking may still surface catalog gap — Slice 4 Continuity maps demoted catalog gap per existing G9-B branches.

---

## 7. Implementation slices (binding order)

### Slice 1 — Gap contract + rules (+ G9-B extract)

**Files:** `engineering_readiness.py` (gap types, DTOs, extraction, prioritization), `project_closure.py` (public `catalog_gap_covered_by_declared_thrust`), tests `tests/test_engineering_readiness_gaps.py`

**Deliverables:**

- All six gap types emit correctly from fixture ProjectStates
- `prioritize_gaps` deterministic
- `depends_on` always explicit per §6.9
- No Continuity import
- Unit tests per gap type trigger + non-trigger

**Do not:** touch Continuity ranking yet.

---

### Slice 2 — Evidence + subsystem mapping

**Files:** `engineering_readiness.py`, `tests/test_engineering_readiness_subsystems.py`

**Deliverables:**

- Eight subsystem keys exactly
- Evidence flags per §4.3
- Verdict derivation per §4.4
- `ACCEPTED_WARNING_TYPES` / G9-B path on catalog (+ propulsion when applicable)
- `overall` rollup per §4.5

---

### Slice 3 — Readiness aggregator

**Files:** `engineering_readiness.py`, `resolve_motor_catalog_surface`, `derive_architecture_progress`, tests `tests/test_engineering_readiness_aggregator.py`

**Deliverables:**

- `build_engineering_readiness(project_state)` composes authorities end-to-end
- Derived on read — no persistence
- Test: same ProjectState → identical JSON twice
- Test: Readiness builder signature accepts **no** continuity argument
- Optional: wire helper into orchestrator for catalog surface (drift guard)

**Do not:** change Continuity behavior yet.

---

### Slice 4 — Continuity handoff

**Files:** `project_continuity.py`, `orchestrator.py` (pass readiness into continuity), existing continuity tests must pass

**Target shape:**

```python
continuity = build_project_continuity(
    project_state=project_state,
    readiness=readiness,   # NEW optional kw-only; required when called from orchestrator
    ...existing kwargs...,
)
```

**Rules:**

1. When `readiness` provided, `next_useful_step` / `next_useful_why` derive from `readiness.top_gap.recommended_next_step` + existing copy templates (Spanish CLI tone preserved).
2. Preserve G9-B demotion narration when top gap is demoted catalog gap (existing test behavior).
3. Remove **duplicated ad-hoc ranking** branches only where readiness now owns ordering; situation/evidence strings may remain for human context.
4. `project_continuity` imports `catalog_gap_covered_by_declared_thrust` from `project_closure` (delete local duplicate).

**Regression gate:** full `tests/test_project_continuity.py` + G9-B/G19/FN-023 related tests green.

---

### Slice 5 — CLI / status surface

**Files:** `orchestrator.py` (startup context / views), view formatters as needed

**Deliverables:**

Expose on startup context (or `estado_actual` view):

```text
ENGINEERING READINESS
<8 subsystem lines with verdict>
PROJECT STATUS: ASSEMBLY_READY | NOT ASSEMBLY READY
TOP GAPS (up to 3 from prioritized_gaps)
  <gap_id, title, severity, blocks, depends_on, recommended action key>
```

Do not add electronics/communications/integration lines.

---

## 8. Test matrix (required)

| Test | Slice | Asserts |
|---|---|---|
| `test_readiness_emits_exactly_eight_subsystems` | 2 | no extra/missing keys |
| `test_no_electronics_subsystem_lines` | 2 | forbidden keys absent |
| `test_gap_motor_catalog_unresolved_trigger` | 1 | catalog gap message + empty matches |
| `test_gap_bom_missing_one_per_key` | 1 | instance gap_ids |
| `test_gap_sim_not_pass_when_fail` | 1 | HIGH gap |
| `test_gap_requirements_mass_exceeded` | 1 | HIGH gap |
| `test_g9b_warning_type_catalog_subsystem` | 2 | PASS sim + declared thrust + catalog gap → WARNING + `CATALOG-GAP-DEMOTED-POST-PASS` |
| `test_assembly_ready_false_when_high_gap` | 2 | BOM missing → NOT_ASSEMBLY_READY |
| `test_assembly_ready_true_only_when_all_pass_or_accepted_warning` | 2 | crafted fixture |
| `test_prioritize_gaps_severity_then_unblock_then_id` | 1 | ordering |
| `test_readiness_deterministic_twice` | 3 | identical output |
| `test_readiness_does_not_import_continuity` | 1 | static/import smoke |
| `test_build_engineering_readiness_no_continuity_param` | 3 | signature guard |
| `test_continuity_uses_readiness_top_gap` | 4 | mock readiness injected |
| `test_continuity_g9b_regression` | 4 | existing G9-B tests pass |
| `test_startup_context_includes_readiness_block` | 5 | CLI surface |

Add fixtures under `tests/` — prefer extending existing ProjectState builders from `test_project_closure_v1.py` / `test_project_continuity.py`.

---

## 9. Regression guards (must not break)

| Guard | Reason |
|---|---|
| G9-B catalog demotion | `_catalog_gap_covered_by_declared_thrust` semantics |
| G19 CTA paths | Continuity next-step when PASS |
| FN-023 / FN-020 | BOM vs architecture consistency |
| FN-005 motor power prompt | Continuity acquisition alignment |
| Existing `test_project_continuity.py` | Full suite green after Slice 4 |

Readiness Slices 1–3 must **not** change CLI behavior. Only Slice 4+ may shift next-step wording if backed by same `top_gap` logic.

---

## 10. Acceptance criteria (definition of done)

1. `build_engineering_readiness` exists and is pure/deterministic.
2. Six gap types only, stable IDs, explicit `depends_on`.
3. Eight subsystem lines; no electronics/comms/integration.
4. Evidence and readiness separated on every line.
5. `ACCEPTED_WARNING_TYPES` closed; G9-B is sole entry.
6. `overall` follows §4.5 exactly.
7. No Continuity input to readiness; no persisted readiness file.
8. Continuity consumes readiness after Slice 4; existing continuity tests pass.
9. CLI shows readiness block after Slice 5.
10. Implementation report lists files changed, behavior deltas, tests run.

---

## 11. Implementation report template (Claude → Engineer)

```markdown
## ERF-1 Implementation Report

### Slices completed
- [ ] 1 Gap contract
- [ ] 2 Evidence/subsystems
- [ ] 3 Aggregator
- [ ] 4 Continuity handoff
- [ ] 5 CLI surface

### Files changed
- ...

### Behavior changed
- Slice 1-3: none (internal projection only)
- Slice 4: Continuity ranking source → readiness.top_gap
- Slice 5: new CLI block

### Tests added
- ...

### Tests executed
`pytest tests/test_engineering_readiness_*.py tests/test_project_continuity.py -q`

### Risks / follow-ups
- ERF-2: ESC/FC/integration gaps
- Optional: orchestrator catalog helper dedup
```

---

## 12. Authority clarification (for implementer)

**ERF-1 is authoritative over:**

- which gaps exist;
- gap severity, blocks, depends_on, ordering;
- assembly-ready rollup over the eight subsystem lines.

**ERF-1 is NOT authoritative over:**

- whether a motor physically produces enough thrust (simulator);
- whether a component is BOM-missing (`classify_component` / `build_component_bom`);
- whether architecture block is pending (orchestrator/architecture helpers);
- user-facing Spanish phrasing (Continuity).

When in doubt, **read** the existing authority and **aggregate** — never re-derive with different thresholds.

---

**End of contract.** Engineer ratifies → send to Claude. No code until approved.
