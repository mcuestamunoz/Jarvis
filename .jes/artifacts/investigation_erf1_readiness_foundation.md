# Investigation — ERF-1 Readiness Foundation

**Date:** 2026-08-18  
**Status:** **PASS** — absorbed into [design_erf1_readiness_foundation.md](design_erf1_readiness_foundation.md) (Engineer review 2026-08-18)  
**Contract:** `implementation_contract_erf1_investigation.md`  
**Vision anchor:** `docs/ENGINEERING_READINESS_VISION.md`

---

## 1) Executive summary

ERF-1 is viable **now** without introducing new architectural subsystems.

The codebase already has deterministic authorities for major readiness dimensions, but they are distributed:

- `project_continuity` owns ranking and next-step narration.
- `orchestrator` owns architecture block progress and proactive gap prompts.
- `project_closure` owns requirements derivation and BOM completeness.
- `simulator` owns physical feasibility verdict.
- `phase_layer` owns lifecycle projection.

The missing piece is not a new domain engine, but a **single deterministic aggregation surface** that normalizes these outputs as "engineering readiness + gaps + dependencies".

---

## 2) Answer to the central question

### Question

> "¿Cuál es la autoridad única y determinista que puede responder qué falta para ser ensamblable, sin segunda ProjectState ni duplicar Continuity/BOM/Simulation?"

### Answer (investigation conclusion)

Use a **Readiness Aggregator** as a thin deterministic projection over existing authorities.

It must:

1. **Read**, never own, the same ProjectState and current outputs.
2. **Compose**, never recompute from scratch, continuity/BOM/simulation truths.
3. Emit a normalized snapshot:
   - readiness lines,
   - gap registry,
   - dependency graph/order,
   - single recommended next engineering step.

This keeps one source of truth and avoids "parallel state" failure modes.

---

## 3) Current authority map (as-is)

| Concern | Current authority |
|---|---|
| Next engineering step | `project_continuity.build_project_continuity` |
| Architecture completion | `orchestrator._block_progress_status` / `_next_pending_block` |
| Component/BOM completeness | `project_closure.build_component_bom` + `classify_component` |
| Requirements derivation | `project_closure.derive_physical_requirements` |
| Physical validation | `simulation.simulator.FeasibilitySimulator.evaluate` |
| Lifecycle phase | `phase_layer.PhaseLayer.infer` |

Observation: all are deterministic and already in use; no LLM authority required for this layer.

---

## 4) Proposed ERF-1 authority surface (target, no code yet)

### 4.1 Readiness snapshot (normalized)

Proposed shape (conceptual):

```text
readiness:
  requirements: PASS|WARNING|INCOMPLETE|UNVERIFIABLE
  architecture: PASS|IN_PROGRESS|INCOMPLETE
  structure: ...
  propulsion: ...
  energy: ...
  electronics: ...
  control: ...
  sensors: ...
  communications: ...
  integration: ...
  catalog: ...
  bom: ...
  overall: ASSEMBLY_READY|NOT_READY
```

Each line must include deterministic evidence references (existing computed facts, not free text inference).

### 4.2 Gap registry

Proposed minimal contract:

```text
gap_id
title
severity
domain
blocked_readiness_lines[]
depends_on_gap_ids[]
evidence[]
recommended_next_step
```

### 4.3 Dependency ordering

Rule set (ERF-1 scope):

- Prefer blockers that unlock other blockers.
- Prefer deterministic resolvable gaps over ambiguous prose-only requests.
- Preserve domain safety order (e.g., unresolved propulsion/energy before optimization suggestions).

---

## 5) ERF-1 scope boundary (important)

### In ERF-1

- Normalization + aggregation + prioritization.
- Deterministic status language.
- Gap dependency ordering.
- Continuity consuming readiness/gap output.

### Explicitly not in ERF-1

- Full electrical compatibility solver (`motor-esc-battery` deep checks) -> ERF-2.
- Geometric fit and wiring/connectors -> later integration phase.
- Full commercial BOM closure (quantities/pricing/availability) -> Impl C-aligned phase.
- System-level optimizer implementation for "aplica la mejor" -> later phase.

---

## 6) Risks and controls

| Risk | Control |
|---|---|
| Creating second truth | Aggregator is projection-only over existing outputs |
| Duplicating continuity logic | Continuity reads readiness result, not vice versa loops |
| Over-scoping into solver work | Strict ERF-1 non-goals and phase lock |
| Regressing CLI polish behavior | ERF-1 tests include existing continuity/gap regressions |

---

## 7) Suggested future implementation slices (for next contract)

1. **Slice A — Data contract scaffold**
   - Add readiness/gap DTO and projection function skeleton.
2. **Slice B — Readiness line mapping**
   - Map current authorities into normalized statuses.
3. **Slice C — Gap extraction + dependency order**
   - Deterministic gap registry and ranking rules.
4. **Slice D — Continuity integration**
   - `next_useful_step` sourced from readiness gaps.
5. **Slice E — CLI/status surface**
   - Readiness summary rendering.

---

## 8) Acceptance probes for ERF-1 (design-time definition)

- A project can be `simulation PASS` and still `overall NOT_READY` when electronics/comms/integration are incomplete.
- Readiness output differentiates:
  - physically validated vs catalog unresolved.
- Top-priority gap is deterministic and explainable from evidence.
- No LLM dependency required to produce readiness/gap snapshot.

---

## 9) Engineer verdict (2026-08-18)

**PASS — sufficient for design.** Three precision rules absorbed into design ★1–★3:

1. No circularity (Readiness never consumes Continuity output).
2. Separate evidence taxonomy from readiness verdict.
3. Gap as deterministic derived entity with explicit creation rules.

Next: ratify [design_erf1_readiness_foundation.md](design_erf1_readiness_foundation.md), then Implementation Contract for Claude.

