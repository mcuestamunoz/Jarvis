# Investigation Contract — CLI feasibility vs readiness semantics

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_cli_feasibility_semantics.md`

**Status:** READY FOR CLAUDE

**Type:** Product-semantics investigation. Trace what the chat **claims** after a thrust PASS when energy/hover evidence is absent. **Not** new physics. **Not** a fidelity-ladder subsystem. **Not** an ERF §11 rollup rewrite.

**Checkpoint base:** tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`** · commit `fc46938`

**You are Claude Code.** This file is your work order. Cursor does not investigate and does not implement this slice. You write the report. Cursor reviews it. Engineer ★ comes after that review. A later Implementation Contract (also written for you) is the only authorization to edit `src/`.

**Do not implement. Do not bump `pyproject.toml`. Do not weaken tests. Do not invent watts, ESC η, pack R, or C-rate.**

---

## 0. Role split (do not invert)

```text
Cursor  → writes this contract (and later the IC)
Claude  → investigates, writes investigation_report_cli_feasibility_semantics.md
Cursor  → investigation review
Engineer ★ → then Cursor writes IC for Claude
Claude  → implements from the IC only
```

Optional seed notes (Cursor, **not** a report):  
[`.jes/artifacts/engineer_notes_cli_feasibility_semantics.md`](engineer_notes_cli_feasibility_semantics.md)

Treat those notes as **hypotheses**. Verify or refute against code and the field fixture. Do **not** copy them as your report. If a note is wrong, say so with a file:line.

---

## 1. Field fixture (input — inspect, do not mutate)

Live project from the Engineer CLI walk:

`workspace/autonomía-de-5min-c09442c25db0`

Observed in chat (you must confirm in `state.json` / `latest_results`):

```text
objetivo: autonomía de 5 min, payload 1 kg, architecture 4/4
Simulation: pass, quality acceptable, margen ~1.28
autonomy_min: null
hover_energy_autonomy_min: null
energy_status: missing_energy_parameters
PROJECT STATUS: ASSEMBLY READY
Continuity CTA: Declarar motor_power_w
Propulsión (evidencia): fallback_operating_point · … (sin hélice de catálogo)
BOM propellers: hq_5045_bn catalog_ref set
```

Product framing (context, not a finding you must rubber-stamp):

```text
SIMULATION PASS  ≠  ENERGY MODEL CLOSED  ≠  5 min flight  ≠  ASSEMBLY READY (ERF §11)
```

Vision (out of **architecture** scope for this investigation): first constructible candidate, then progressive evidence. You only answer: **what must the CLI say today, with existing fields, so it does not over-claim.**

---

## 2. Product constraints (treat as locked unless the Engineer rewrites this contract)

| ID | Constraint |
|---|---|
| **C1** | Presentation + ranking only. Do **not** change `ASSEMBLY_READY` (ERF §11). |
| **C2** | Do not recommend inventing `motor_power_w` when motors are catalog-bound and `max_watts` is null. Do not reopen P27-A / P26. Do not write W into catalog. |
| **C3** | Do not propose a persisted fidelity ladder on `ProjectState`. Map claims onto existing sim/calc/continuity/reasoning fields. |
| **C4** | Fallback OP copy vs BOM identity is in scope. Resolver HOLD / `fallback_only` policy is **not**. |
| **C5** | Out of scope: DSE value-of-information, Structure v1–v5, HD-001/002/003, Block Closure B-PROP-ENERGY, H5/C-081, Conversation Engine. |

If your evidence shows C1 must be broken (Energy PASS / `ASSEMBLY_READY` in the same slice), **stop** and say so in the report — do not expand scope yourself.

---

## 3. What you must investigate

### 3.1 Situation strings

Trace every producer of:

```text
Diseño validado en simulación (PASS)
Física orientativa en PASS
```

Document the **exact predicate** that upgrades orientativa → validado.

Question: BOM-complete heuristic, or stronger physics?

### 3.2 CTA `motor_power_w` after architecture 4/4

Mid-BOM already has `catalog_bound_motor_covers_power_w` (FN-005). The field session still asked for `motor_power_w` after 4/4.

Trace and **name which surface won** on the fixture:

| Surface | Start here |
|---|---|
| Continuity rank | `src/jarvis/core/project_continuity.py` |
| ReasoningLayer | `src/jarvis/core/reasoning_layer.py` `_build_suggested_actions` |
| Param contract | `src/jarvis/core/parameter_requirements.py` `MISSING_ENERGY_PARAMETERS` |
| Architecture vs calc | `param_present_for_architecture` vs `missing_params_for_reason` |
| Orchestrator | `build_startup_context` when `signals.missing_energy_parameters` |
| Honesty note | `energy_model_honesty_note` in `project_closure.py` |

### 3.3 Silent autonomy

`calcular` / `simular` omit `autonomía=` when null. `estado` hover/ESTIMATIVO omit when `_hover_energy_from_calculations` is None.

Question: honest omission vs missing **negative** (no number, named reason class)? Recommend the smallest CLI addition that does **not** invent minutes.

### 3.4 Propulsion evidence suffix

`src/jarvis/adapters/cli/main.py`: `fallback_operating_point` → `" (sin hélice de catálogo)"`.

Question: suffix from resolver identity (`propulsion_resolution.propeller_sku`) vs BOM (`propellers.catalog_ref`)? Recommend one sentence. **No** resolver policy change.

### 3.5 Options for a future IC (you recommend; you do not implement)

| Option | Scope |
|---|---|
| **A** | Continuity situation + next_step + honesty note + ReasoningLayer/orchestrator energy CTA + CLI fallback suffix + explicit “no L1 autonomía” line when objective has `autonomy_min` and calc is null. ERF untouched. |
| **B** | A + change `_energy_evidence` so Energy is not PASS when autonomy is a constraint and calc autonomy is null |
| **C** | Persist a new evidence-tier / design-vN field |

Recommend one. Reject options that violate §2 unless you stop for Engineer rewrite.

### 3.6 Tests / probe sketch

List tests that pin “Diseño validado” / energy CTA (`tests/test_project_continuity.py`, architecture energy labels, G21 bound-without-watts). Sketch one unit fixture or probe: sim PASS, catalog-bound emax without W, 4S battery, `autonomy_min` null, closed BOM — must **not** CTA invent W, must **not** say diseño validado (if you recommend changing that string).

---

## 4. Explicit non-goals

- Inventing hover power, ESC η, pack R, C-rate
- Reopening P27-A
- Changing `resolve_operating_point` / HOLD / voltage epsilon
- Teaching DSE “what to measure”
- Renaming `PROJECT STATUS: ASSEMBLY READY` in this investigation (C1)

---

## 5. Done when your report contains

1. As-is claim graph (situation / next / ERF / calc energy) with file:line.
2. Which surface produced the 5 min session CTA, verified on the fixture.
3. Recommended option A/B/C with a file list **for the future IC** (not a patch).
4. Test/probe risks. ERF §11 impact (none if you recommend A).

Sign off: **no `src/` or test files touched.**
