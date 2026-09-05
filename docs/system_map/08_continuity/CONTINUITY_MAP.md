# 08 — Continuity

**Purpose.** Situation / Evidence / Next-step ("A'" Project Continuity), plus the BOM/completeness classifier (FN-020), the **Engineering Readiness aggregator (ERF-1)**, and the phase/reasoning signal layers that feed startup context. This is the subsystem that answers "where am I and what's next" — the authority `project_status` (C-021/C-035) reads from.

**Inbound:** C-071 (from Simulation), C-060 (current_parameters, indirectly via requirements), **C-107** (authorities → `build_engineering_readiness`), **C-111** (ERF-2, `electrical_compatibility` → gap generation). **Outbound:** C-021/C-035 (to Runtime's `_handle_project_status`), C-036 (to Acquisition, shared `_next_pending_block` read), **C-108** (partial — catalog-gap ranking only, when `readiness=` supplied), **C-109/C-110** (startup context + CLI render).

## Key modules

| Path | Role |
|---|---|
| `core/engineering_readiness.py` | **ERF-1/ERF-2** — Gap Registry + nine-subsystem assembly-ready rollup; pure aggregator over closure/arch/sim/electrical (C-107, C-111). ERF-2 adds `electronics` subsystem, 4 electrical gap types, `INCOMPATIBLE` verdicts (★3 gate), and `electrical_compatibility.py` as pure fact provider. Not a write authority; does not replace BOM/sim/classifier logic. |
| `core/electrical_compatibility.py` | **ERF-2** — pure deterministic checks: ESC presence, per-motor ESC vs motor current, battery discharge, prop↔motor match. Called by `build_engineering_readiness`. No I/O, no LLM. |
| `core/project_continuity.py` | `build_project_continuity` — the Situation/Evidence/Next-step formula itself |
| `core/project_closure.py` | `classify_component`, `component_presence_tier`, `build_component_bom`, `derive_physical_requirements`, `energy_model_honesty_note` (FN-020's single classifier lives here). **Impl D / IC 3:** `_bom_sku_resolved` + `format_bom_lines` — motor/battery/propeller/`frame` `[sku]` suffix from live `has_*` re-check; **display-only** (never read by gap builders or `_derive_subsystem_verdict`). **Control Parity / Structure Foundations (2026-09-04):** `_bom_completeness_tail` — identity-only for `flight_controller`; class-screening suffix for `frame`. **Structure B (2026-09-04→05):** `build_component_bom` skips any spec with `parent_key is not None` (never a top-level peer); `format_bom_lines` / `_frame_part_sublines` append display-only `└` under `frame` for `frame_arm`, ordinal `frame_plate`…`frame_plate_8` (curated `label` + thickness when set), `frame_cage`, `frame_standoff`. Neither changes `classify_component`, gap builders, or Structure PASS. |
| `core/phase_layer.py` | `PhaseLayer.infer` — project phase (planning/complete/…) |
| `core/reasoning_layer.py` | `ReasoningLayer.build` — signals, insights, tradeoffs, suggested_actions (large module, ~550 lines) |

## Important functions (Level 2)

- `build_project_continuity(...) -> {situation, evidence, next_useful_step, next_useful_why}` (`project_continuity.py`) — pure function, recomputed every call from `ProjectState` + `component_bom` + `physical_requirements`. Optional kw-only `readiness=` (ERF-1 Slice 4): when supplied from `build_startup_context`, catalog-gap branches consult `readiness.top_gap` / `subsystems["catalog"]` (C-108); all other ranking branches unchanged. Legacy ranking order when `readiness` omitted (first match wins): blocking physics → sim warning/fail → honest catalog gap (**demoted when PASS + declared `per_motor_max_thrust_n >= floor`** — G9-B/S1, 2026-08-18) → incomplete/missing BOM → architecture block pending → optimization suggestion (PASS + closed) → fallback "design validated."
- `build_engineering_readiness(project_state) -> EngineeringReadinessResult` (`engineering_readiness.py`, ERF-1/ERF-2) — ten gap types (ERF-1: 6 + ERF-2: 4 electrical), nine subsystem lines (`requirements`…`bom` + `electronics`), derived on read. ERF-2 adds `INCOMPATIBLE` verdicts with ★3 deterministic-evidence gate and `_INCOMPATIBLE_VERDICT_SUBSYSTEMS` for narrowed verdict impact. **IC 1:** `_requirements_evidence.defined` uses `requirements_declared()` — numeric `parsed_constraints` **or** explicit-none `restrictions` (`"no"`, `"ninguna"`, …) without fabricating keys. Consumed by orchestrator startup context (C-109) and optionally by Continuity (C-108).
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

- **C-081** ✅ **CLOSED (Claim Hygiene IC + Structure Foundations IC, 2026-09-04)** — the plain `elif sim_status == "pass":` **situation** branch (not the next-step branch H5 originally targeted) now has two additional gates before the generic "Diseño validado" fallback: `margin_claim_weak(sim)` (quality `"risky"` or an active `low_margin`/`high_actuator_load`/`low_force_to_weight_ratio` warning → locked `_MARGIN_WEAK_SITUATION` sentence) and `_frame_class_gap_live(readiness)` (a live `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` → locked `_FRAME_CLASS_GAP_SITUATION` sentence). Both reuse existing fields/gap registry data, no new thresholds. See `MISMATCHES.md` H5 (closed) and `.jes/artifacts/investigation_report_claim_hygiene_assembly_ready.md` / `investigation_report_structure_foundations.md`. **Residual (not closed):** the general "PASS + any other live gap type" pattern was not audited — only margin/quality and frame-class were proven and fixed; PhaseLayer's independent `physical_validation` verdict for the same risky-quality state is still silently suppressed by `main.py`'s FN-002 rule whenever Continuity has a situation (named, not fixed, in the claim-hygiene report as N2).
- **G20 / G20-B** ✅ closed in `d224dc1` — composite in-progress labels are now dynamic and reflect the active energy sub-gap (`motor_power_w` vs battery), removing the prior label/wizard expectation mismatch.
- **G9-A** 🟡 — `build_startup_context` catalog-gap computation still blind to bound `catalog_ref` (separate from G9-B demotion fix).
- **ERF-1 Slice 4b** 🟡 — C-108 is catalog-gap ranking only; full Continuity handoff (BOM/arch/FN-005 branches) deferred. See `.jes/artifacts/implementation_report_erf1.md`.
- **Project Closure (IC 1–3)** ✅ — requirements explicit-none + G26 path; battery/propeller catalog pick live; propeller `sku_resolved` display fix. Product contract: `ENGINEERING_READINESS_VISION.md` §11. Checkpoints: `checkpoint-requirements-closure` → `checkpoint-battery-catalog-bind-ux` → `checkpoint-closure-policy`.

## Tests

`tests/test_engineering_readiness_gaps.py`, `tests/test_engineering_readiness_subsystems.py`, `tests/test_engineering_readiness_aggregator.py`, `tests/test_engineering_readiness_continuity.py`, `tests/test_engineering_readiness_cli.py`, **`tests/test_engineering_readiness_erf2_gaps.py`**, **`tests/test_engineering_readiness_erf2_subsystems.py`**, **`tests/test_erf2_architecture.py`**, **`tests/test_electrical_compatibility.py`**, `tests/test_project_continuity.py`, `tests/test_project_closure_v1.py`, `tests/test_project_coherence.py`, `tests/test_fn020_completeness_coherence.py`, `tests/test_phase_layer.py`, `tests/test_reasoning_layer.py`, **`tests/test_cli_polish.py`** (G9-B, G19 CTA), **`tests/test_requirements_closure.py`**, **`tests/test_impl_d_sku_bom.py`** (incl. IC 3 propeller `sku_resolved`), **`tests/test_frame_parts_graph_v1.py`** (BOM `└` plate siblings).
