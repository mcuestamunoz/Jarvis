# 08 — Continuity

**Purpose.** Situation / Evidence / Next-step ("A'" Project Continuity), plus the BOM/completeness classifier (FN-020) and the phase/reasoning signal layers that feed it. This is the subsystem that answers "where am I and what's next" — the authority `project_status` (C-021/C-035) reads from.

**Inbound:** C-071 (from Simulation), C-060 (current_parameters, indirectly via requirements). **Outbound:** C-021/C-035 (to Runtime's `_handle_project_status`), C-036 (to Acquisition, shared `_next_pending_block` read).

## Key modules

| Path | Role |
|---|---|
| `core/project_continuity.py` | `build_project_continuity` — the Situation/Evidence/Next-step formula itself |
| `core/project_closure.py` | `classify_component`, `component_presence_tier`, `build_component_bom`, `derive_physical_requirements`, `energy_model_honesty_note` (FN-020's single classifier lives here) |
| `core/phase_layer.py` | `PhaseLayer.infer` — project phase (planning/complete/…) |
| `core/reasoning_layer.py` | `ReasoningLayer.build` — signals, insights, tradeoffs, suggested_actions (large module, ~550 lines) |

## Important functions (Level 2)

- `build_project_continuity(...) -> {situation, evidence, next_useful_step, next_useful_why}` (`project_continuity.py:10`) — pure function, recomputed every call from `ProjectState` + `component_bom` + `physical_requirements`. Ranking order for `next_useful_step` (first match wins): blocking physics → sim warning/fail → honest catalog gap → incomplete/missing BOM → architecture block pending → optimization suggestion (PASS + closed) → fallback "design validated."
- `classify_component(key, spec, project_state) -> "missing"|"stub"|"declared"|"defined"` (`project_closure.py`, FN-020) — **the single classifier** shared with `03_acquisition`'s architecture-progress check (C-082/C-083). Before FN-020 there were two independently-defined completeness thresholds that could disagree (architecture "present" vs. BOM "incomplete" for the same `medium`-completeness component) — this function is the fix.
- `component_presence_tier(spec) -> "stub"|"present"` — the presence-only primitive `orchestrator._component_is_low` wraps (C-083).
- `build_component_bom(project_state) -> {defined, incomplete, missing, declarative}` — buckets driven entirely by `classify_component`; `incomplete` now means genuinely `stub`, never merely-`medium`-but-measurable.
- `PhaseLayer.infer(context) -> phase` (`phase_layer.py:28`) — feeds into `build_startup_context`'s `phase`/`phase_description`.
- `ReasoningLayer.build(context, suggestions) -> ReasoningOutput` (`reasoning_layer.py:28`) — `_extract_signals`, `_build_insights`, `_build_suggested_actions`; this is where `missing_physics_parameters`/`has_warnings` signals (used by `orchestrator.build_startup_context`'s `status_type` hierarchy) come from.

## Local state touched

None — this entire subsystem is pure/read-only. (Its output is consumed to *set* session fields elsewhere — e.g. Bug 54's `pending_define_missing` — but Continuity itself never writes.)

## LLM

NO — zero LLM involvement anywhere in this subsystem, by design (this is the explicit alternative to LLM narration for "what's next").

## Known issues owned by this subsystem

- **C-081** 🟡 PARTIAL (WEAK) — the `elif sim_status == "pass":` branch of `build_project_continuity`'s next-step logic does not read `safety_margin_ratio` at all, so PASS+risky and PASS+comfortable produce identical generic text. See `MISMATCHES.md` H5 (design-only, no FN queued).

## Tests

`tests/test_project_continuity.py`, `tests/test_project_closure_v1.py`, `tests/test_project_coherence.py`, `tests/test_fn020_completeness_coherence.py`, `tests/test_phase_layer.py`, `tests/test_reasoning_layer.py`.
