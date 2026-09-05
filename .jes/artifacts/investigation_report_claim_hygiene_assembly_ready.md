# Investigation Report — Claim hygiene under ASSEMBLY READY

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_claim_hygiene_assembly_ready.md](investigation_contract_claim_hygiene_assembly_ready.md)
**Checkpoint:** tag `v0.3.6` / `checkpoint-experimental-prop-energy-closed`, commit `f70b278` (verified `git diff f70b278 HEAD --stat` touches only `.jes/state/engineering_state.json`, no `src/` drift)
**Status:** OPEN — for Cursor review, then Engineer ★ on the claim matrix

Not an Implementation Contract. No `src/` edits were made. All reconstructions
below run in-memory against `v0.3.6` source; the fixture script is not part of
the repo (kept in the scratchpad, not committed).

---

## A. Executive answer

The over-claim is **real** and larger than the agenda's own framing. The
primary surface is **`project_continuity.build_project_continuity`'s plain
`elif sim_status == "pass":` situation branch**
(`src/jarvis/core/project_continuity.py:293-294`): it emits *"Diseño validado
en simulación (PASS). Proyecto vivo — listo para el siguiente paso útil."*
for **any** PASS, regardless of `quality`, `warnings`, or
`safety_margin_ratio`. This is the same branch documented (but understated)
as **C-081 / H5** in `docs/system_map/08_continuity/CONTINUITY_MAP.md:38`.

Two things go beyond what H5 described:

1. **H5's own reproduction path is stale.** H5 assumed PASS+risky reaches the
   generic `elif sim_status == "pass":` **next-step** fallback
   (`project_continuity.py:522-524`, *"Diseño en PASS — puedes iterar..."*).
   It does not: a `low_margin` (or any) warning makes
   `reasoning_layer`'s `has_warnings` signal true
   (`src/jarvis/core/reasoning_layer.py:63`), which sets
   `status_type = "warning"` in `orchestrator.build_startup_context`
   (`src/jarvis/core/orchestrator.py:4315-4317`) — a **higher-priority**
   branch in `build_project_continuity`'s next-step ranking
   (`project_continuity.py:359`, resolving at line 434 to *"Corrige la causa
   del warning/fallo de simulación."*). The generic PASS fallback H5 cites is
   unreachable for real low-margin traffic.
2. Because the **situation** sentence (unlike next-step) is not
   `status_type`-gated at all, the reconstructed block below prints *"Diseño
   validado"* and *"Corrige la causa del warning"* **in the same rendered
   output**, plus `PhaseLayer.infer` independently computing phase
   `"physical_validation"` (*"la simulación indica inviabilidad"* —
   `src/jarvis/core/phase_layer.py:64-69`) for the identical state — a phase
   line that render_startup_context then **hides** because Continuity's
   situation is present (`src/jarvis/adapters/cli/main.py:226-228`). Three
   deterministic authorities (Continuity situation, Continuity next-step,
   PhaseLayer) disagree about the same PASS+risky state, and the CLI shows
   only the most optimistic one plus the most corrective one, side by side.

`ASSEMBLY_READY` reaches this state **by accident of unused fields, not by
design**: `engineering_readiness._derive_overall` and every subsystem-verdict
builder in that module read only `sim.get("status")` — grepping the whole
file for `quality` returns zero hits. No design doc (`design_erf1_readiness_
foundation.md`, `implementation_contract_erf2.md`) states that margin/quality
was deliberately excluded from the Gap Registry; it was simply never modeled
as a gap type.

---

## B. Field table (Know)

| Field | Authority (`file:line`) | Threshold / meaning | Read by Continuity? | Read by `_derive_overall`? |
|---|---|---|---|---|
| `simulation.status` | `simulator.py:77` (`"pass" if can_fly else "fail"`) | pass/fail | Yes — gates situation/next-step branch selection | Yes — the only sim field the Gap Registry reads (`_sim_not_pass_gaps`, `engineering_readiness.py:642-675`) |
| `simulation.quality` | `simulator._resolve_quality`, `simulator.py:136-143` | `<1.0` fail · `<1.1` risky · `<1.3` acceptable · else good | Yes, but only into the **Evidence** bullet (`project_continuity.py:301-308`), never into the **situation** sentence for the plain-PASS branch (`:293-294`) | **No** — zero references to `quality` anywhere in `engineering_readiness.py` |
| `simulation.warnings` (incl. `"low_margin"`) | `simulator._resolve_warnings`, `simulator.py:145-164`; `LOW_MARGIN_THRESHOLD=1.15` at `simulator.py:13` | fires when `can_fly and margin < 1.15` | Indirectly: a non-empty `warnings` list drives `reasoning_layer.has_warnings` → `status_type="warning"` → the **next-step** branch at `project_continuity.py:359-435` (generic *"Corrige la causa..."*, code name only, not humanized) | **No** — no gap type reads `sim.warnings` |
| `simulation.safety_margin_ratio` | `simulator.py:69`, rounded at `:127` | raw ratio | Yes, Evidence bullet only (`:301-308`) | **No** |
| `PhaseLayer` phase | `phase_layer.py:43-44,64-69` — `quality in ("fail","risky")` → `"physical_validation"` | independent of `status_type`/ERF | N/A (separate module) | N/A — but its output is **suppressed** by `main.py:226-228` whenever `continuity.situation` is truthy |
| `readiness.overall` | `engineering_readiness._derive_overall`, `engineering_readiness.py:1199-1211` | HIGH gap ⇒ NOT_READY; else all subsystems PASS or accepted WARNING ⇒ READY | Consumed by `estado`'s readiness block, not by Continuity's own branching | — |
| `prop_energy_block_closure` (weak-OP "evidencia débil") | rendered directly in `main.py:402-439`, not passed through Continuity | `evidence_tier in {manufacturer_test, fallback, weak}` | **No** — `build_project_continuity` has no such parameter at all | **No** |

Threshold fragmentation (cited, not a defect to fix here): four independent
"low margin" cutoffs exist for four different purposes — `simulator.py:13`
(`1.15`, gates the `low_margin` warning), `reasoning_layer.py:19`
(`1.2`, gates an internal tradeoff-insight signal), `suggestion_engine.py:7`
(`1.3`, gates an optimize-margin suggestion), and inline `1.15`/`1.5` literals
in `goal_planner.py:299-327` (goal-strategy ordering). This is already flagged
non-blocking in `docs/system_map/07_simulation/SIMULATION_MAP.md:20`. None of
these formulas were touched or should be, per the contract's locked
constraints.

---

## C. Claim matrix (Claim)

Quoted strings are verbatim from `v0.3.6` source.

| Sentence | Allowed when PASS+good/acceptable | PASS+risky / low_margin (or other margin/load warning) | PASS+autonomy undemonstrated | FAIL |
|---|---|---|---|---|
| *"Diseño validado en simulación (PASS). Proyecto vivo — listo para el siguiente paso útil."* (`project_continuity.py:294`) | **Current: shown. Proposed: unchanged** — this is the honest case | **Current: shown (bug).** **Proposed: not shown** — replace with a margin-qualified sentence (e.g. naming `quality`/margin) before falling through to next-step's own warning branch | Not reached — the autonomy-undemonstrated branch (`:284-292`) already intercepts this case ahead of the plain-PASS branch; confirmed unaffected by this investigation | Not reached — `sim_status != "pass"` branch (`:271-272`) fires first |
| `PROJECT STATUS: ASSEMBLY READY` (`main.py:139-142`) | **Current: shown. Proposed: unchanged** | **Current: shown unconditionally (bug)** — no adjacent caveat when the PASS backing any subsystem carries `quality="risky"` or an active margin/load warning. **Proposed:** append one caveat line (e.g. `NOTE: margen ajustado en <n> subsistema(s) — ver Evidencia`) without changing the `ASSEMBLY_READY`/`NOT_ASSEMBLY_READY` value itself | Same label today — readiness is driven by `_derive_overall`, which is autonomy-blind too via `GAP-REQUIREMENTS-UNMET` only when `current_autonomy_min` is present and below target; out of this investigation's fixture | Not reachable — a `fail` status always yields a HIGH `GAP-SIM-NOT-PASS` gap, forcing `NOT_ASSEMBLY_READY` |
| Evidence bullet `"Simulación: {status} — calidad {quality} — margen {margin:.2f}"` (`project_continuity.py:301-308`) | **Current: shown, honest. Proposed: unchanged** | **Current: shown, honest. Proposed: unchanged** — this line is already correct; the bug is that the situation sentence above it doesn't agree with it | Shown, honest, unchanged | Shown, honest, unchanged |
| Next-step *"Corrige la causa del warning/fallo de simulación."* / why=`low_margin` (`project_continuity.py:434-435`) | Not reached (no warning) | **Current: shown, structurally honest, but `next_useful_why` surfaces the raw warning code (`"low_margin"`) instead of a humanized sentence** (`WARNING_MESSAGES`/`WARNING_SHORT` in `main.py:62-83` are never applied to `next_useful_why`). **Proposed:** humanize via existing `WARNING_SHORT`/`WARNING_MESSAGES` lookup — copy-only, no new field | N/A | Different branch (`_THRUST_FAIL_NEXT_STEP` / autonomy variants), already locked, unaffected |
| `WARNING_MESSAGES["low_margin"]` full text (`main.py:63-66`), rendered only on the `calculate`/`simulate` reply (`main.py:552-560`) | Not applicable (no warning) | **Current: shown, honest, unchanged** — this is the one surface that already tells the user the truth in full sentences | N/A | N/A |
| `PhaseLayer` phase description *"La simulación indica inviabilidad; el diseño necesita ajustes físicos."* (`phase_layer.py:12,64-69`) | Not reached (`quality` not in fail/risky) | **Current: computed but suppressed from CLI output** by `main.py:226-228` whenever `continuity.situation` is present — i.e. exactly the states this investigation cares about. **Proposed:** do not suppress the phase line when `continuity.situation` disagrees with `phase`; or fold its meaning into the (fixed) situation sentence instead | N/A (autonomy branch takes over) | Reached in some fail states, but suppressed the same way whenever Continuity has a situation — out of scope here (fail-routing honesty already locked) |
| `BLOQUE PROPULSIÓN/ENERGÍA: CERRADO — evidencia débil (no hay punto de operación de catálogo)` (`main.py:417-421`) | Correctly hedged already, own axis | Correctly hedged already; **the problem is not this line, it's that the situation sentence above it in the same render doesn't defer to it** — Continuity has no wiring to read `prop_energy_block_closure` at all (see field table row) | N/A | N/A |

---

## D. Measure

- **Situation sentence over-claim** is falsified today by fields already
  computed on every PASS: `simulation.quality` and `simulation.warnings`
  (both already in `sim`, which `build_project_continuity` already binds at
  `project_continuity.py:230`). No new physics, no new field — a pure
  read-and-branch change.
- **`PROJECT STATUS: ASSEMBLY READY` over-claim** is falsified by the same
  two fields, but they are not currently threaded into
  `_render_readiness_block`/`render_startup_context` at all — `readiness`
  (the ERF dict) carries no per-subsystem margin info, only verdicts. The
  cheapest falsifier is the raw `simulation` dict already present in `ctx`
  (`render_startup_context`'s caller already has it via
  `ctx.get("continuity")`/upstream `sim`), not a new ERF field.
- **What Jarvis must refuse to claim without a lab measurement:** that a
  `risky`/`low_margin` design is "validado" in the sense of having comfortable
  margin, and that "ASSEMBLY READY" means margin is comfortable — it only
  means "no HIGH gap and no un-accepted WARNING verdict." Both refusals are
  already possible with existing fields; no lab measurement is invoked or
  needed for the margin axis.
- **Weak-OP-evidence claim** (`prop_energy_block_closure`) is a **different**
  falsifier: it requires wiring a field that Continuity does not currently
  receive at all. This is a strictly bigger, separate change (a new
  parameter threaded from orchestrator through `build_project_continuity`),
  not a same-branch read. Conflating it with the margin fix would inflate the
  smallest honest purchase.

---

## E. Buy recommendation

**B4 — Split: margin/quality claim hygiene now; weak-OP-evidence claim
language as a separate later IC.**

Justification, using only seams already traced above:

- The margin/quality fix reads fields (`quality`, `warnings`,
  `safety_margin_ratio`) that `build_project_continuity` **already receives**
  in the `sim` dict it binds at `project_continuity.py:230`, and that
  `render_startup_context` can reach via the same upstream context. It is a
  same-branch, same-parameter-list copy/gate change on both named surfaces
  (Continuity situation **and** CLI `PROJECT STATUS` heading — both are
  quoted verbatim in this investigation's own motivating example, so fixing
  only one leaves the other still lying).
- The weak-OP-evidence claim (`prop_energy_block_closure` "evidencia débil")
  requires threading a **new** parameter into `build_project_continuity` that
  does not exist today — a materially larger change with its own call-site
  surface (`main.py:397-439` currently renders it fully outside Continuity).
  Bundling it into the same IC would exceed "smallest safe scope."
- `ASSEMBLY_READY` eligibility (`_derive_overall`, gap types, subsystem
  verdicts) is untouched in both slices — no Engineer ★ stop is triggered by
  this recommendation. If a future thread decides margin should gate
  `ASSEMBLY_READY` itself (turn "risky" into a gap type), that is a **B3**
  decision and must be named to Engineer ★ separately; this investigation
  does not recommend it.

Rejected options: **B1** (Continuity-only) leaves `PROJECT STATUS: ASSEMBLY
READY` — a string this investigation's own contract quotes as part of the
lie — unfixed. **B2** (Continuity + CLI, no split) is the right shape for the
margin slice but silently drops the weak-OP-evidence half the contract's
title also names; B4 keeps that half visible as a named follow-up instead of
dropping it. **B0** would leave a reproducible, cited self-contradiction
(situation says "validado", next-step says "corrige la causa del warning", in
the same render) undocumented for Engineer ★ to act on. **B3** is not
justified: no field currently modeled would need new *physics* to gate
`ASSEMBLY_READY` — only new claim text — so changing `_derive_overall`
would be scope the contract explicitly asks to avoid defaulting to.

---

## F. Explicit non-goals confirmed

Not proposed by this investigation:
- Sensor / FC / ESC catalogs (control stays declarative, per Engineer
  ratification).
- Catalog honesty C-A1 as a motor-list feature.
- Reopening fail-routing N1 (`simulation.status == "fail"` distinctness is
  unaffected and unexamined for change here).
- Control physics or control parity (separate, not-yet-authorized agenda
  thread).
- H5 ESC catalog, Conversation Engine, or any goal-thread/"risk thread"
  subsystem (H5's own note floats a "structured risk thread field" — this
  report takes no position on it, consistent with H5's "no FN queued until a
  data-contract note exists").
- Any change to `simulator._resolve_quality`, `LOW_MARGIN_THRESHOLD`, or any
  of the four independent margin-threshold constants cited in §B (fragmentation
  noted, not resolved).
- Any change to `engineering_readiness._derive_overall`, gap types, or
  subsystem-verdict logic (would be a B3/Engineer ★ decision — not
  recommended).
- Broad `orchestrator.py` split or Continuity rewrite beyond the two named
  branches.
- Hardware HD-* campaigns.

---

## G. Suggested IC skeleton (margin/quality slice only — not an Implementation Contract)

- **Files:** `src/jarvis/core/project_continuity.py` (gate the
  `elif sim_status == "pass":` situation branch at `:293-294` on
  `sim.get("quality")` and `sim.get("warnings")`; humanize
  `next_useful_why` for the warning-code case at `:434-435` via existing
  `WARNING_SHORT`); `src/jarvis/adapters/cli/main.py`
  (`_render_readiness_block`/`render_startup_context`: append one caveat
  line after `PROJECT STATUS: ASSEMBLY READY` when the backing `simulation`
  shows `quality=="risky"` or an active margin/load warning).
- **Behavior change:** situation copy and one CLI heading gain a
  margin-aware caveat on PASS+risky/PASS+warning states; `ASSEMBLY_READY`
  value, subsystem verdicts, gap types, thresholds, and formulas are
  byte-identical.
- **Tests:** extend `tests/test_project_continuity.py` and
  `tests/test_engineering_readiness_continuity.py` with a PASS+risky/
  low_margin fixture (shape validated in this investigation) asserting the
  new situation wording and that PASS+good/acceptable output is unchanged;
  extend `tests/test_main_cli.py` / `tests/test_engineering_readiness_cli.py`
  for the CLI caveat line and its absence on PASS+good.
- **Forbidden:** `simulator.py` formulas/thresholds; anything in
  `engineering_readiness.py`'s gap catalog, `_derive_subsystem_verdict`, or
  `_derive_overall`; the `ASSEMBLY_READY`/`NOT_ASSEMBLY_READY` strings
  themselves; `prop_energy_block_closure` wiring (separate B4 follow-up);
  autonomy-undemonstrated / autonomy-below branches (already locked,
  confirmed unaffected in this investigation's fixture).

---

## Appendix — reconstruction fixture (§5 of the contract)

Built as an in-memory `SimpleNamespace` `ProjectState` (same shape as
`tests/test_engineering_readiness_subsystems.py::
test_assembly_ready_true_when_everything_pass_no_gaps`, the existing
"everything PASS, no gaps" fixture), with `latest_results.simulation` set to:

```text
status=pass, can_fly=True, quality=risky, safety_margin_ratio=1.05,
warnings=[low_margin]
```

Run through `build_engineering_readiness`, `build_project_continuity` (with
`status_type="warning"`, `status_reason="low_margin"` — the values
`orchestrator.build_startup_context` actually derives per
`reasoning_layer.py:63` + `orchestrator.py:4315-4317`, not guessed), and
`render_startup_context`. Verbatim output:

```text
gaps: []
overall: ASSEMBLY_READY
  requirements: verdict=PASS · architecture: PASS · structure: PASS
  propulsion: PASS · energy: PASS · electronics: PASS · control: PASS
  catalog: PASS · bom: PASS

Situación: Diseño validado en simulación (PASS). Proyecto vivo — listo
para el siguiente paso útil.
Evidencia:
   • Simulación: pass — calidad risky — margen 1.05
   • Requisito: ≥ 3.30 N/motor
   • Masa máx.: 999.00 kg (actual 1.50 kg)
   • Catálogo: candidatos sunnysky_r2305_2500, emax_rs2205_2300
Siguiente paso: Corrige la causa del warning/fallo de simulación.
   Por qué: low_margin

ENGINEERING READINESS
Requirements   PASS
Architecture   PASS
Structure      PASS
Propulsion     PASS
Energy         PASS
Electronics    PASS
Control        PASS
Catalog        PASS
BOM            PASS

PROJECT STATUS: ASSEMBLY READY
```

This is the field reconstruction the contract asked for: `sim.status==pass`,
`can_fly==True`, `quality=="risky"`/`warnings` contains `low_margin`,
ERF `overall=="ASSEMBLY_READY"` (reachable, as shown), Continuity situation
contains "Diseño validado" (confirmed, not disproven), and it also shows the
self-contradiction with the next-step line that H5's own note did not
anticipate (§A.1).
