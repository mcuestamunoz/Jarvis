# Engineer CLI Walk — fail-routing coherence

**Date:** 2026-09-03  
**Authority:** Engineer  
**Project fixture:** `workspace/autonomía-de-10-minutos-86f6a0e8effa`  
**Status:** WALK FAILED — preserve fixture; investigation authorized

## Outcome

Core state and calculations remained traceable, but the guided CLI repeatedly
failed to tell the user what fact was missing or what action could resolve the
active failure. This is a routing/coherence failure, not evidence that
Structure A physics or its N1 mirror hotfix is wrong.

## Confirmed good

- `PVC 650g 5 pulgadas` wrote frame mass `0.65 kg` and
  `size_class_inch=5`.
- N1 remained closed: the frame mass override survived partial class/material
  updates.
- `D=5`, class `5` closed Structure through LEVEL A class compatibility.
- Architecture reached 4/4 after Pixhawk 4 + Here3.
- Final calculation honestly reported:

```text
total_mass_kg          2.75
required thrust        32.373 N
available thrust       32.0 N
required per motor      8.0932 N
autonomy                8.88 min < 10 min
sim.status              fail
can_fly                 false
```

## Field failures

### F1 — missing frame class is known but not requested

After `PVC 650g`, the system emitted `GAP-FRAME-SIZE-MISSING`, yet:

```text
Siguiente bloque: Estructura (frame) — en progreso,
define los parámetros que faltan.
```

and `ayúdame a elegir` answered:

```text
Indica material y masa. Ej: 'fibra de carbono 450g'
```

Repeating mass/material did not progress. Only the Engineer-supplied phrase
`PVC 650g 5 pulgadas` closed the block.

Known seams:

- `_component_prompt_for_first_missing` has the Structure A pulgadas prompt.
- `_handle_component_description` has a separate frame low-completeness probe
  that hand-writes material/mass copy and bypasses that helper.
- `_append_arch_progress_hint` hand-writes generic “define los parámetros”.
- Continuity's `_frame_class_next_step` loses to higher ranking branches.

### F2 — simulation FAIL rendered as WARNING

After choosing a motor with 8.0 N nominal against 8.09 N required:

```text
Simulation: status=fail, can_fly=false
CLI: ⚠ Última simulación: WARNING (autonomía por debajo de restricción)
```

`build_startup_context` chooses `status_type="warning"` whenever warnings are
present, before considering `simulation.status=="fail"`.

### F3 — false claim: “el empuje ya es PASS”

With `32.0 < 32.373 N`, Continuity emitted:

```text
La autonomía calculada está por debajo del objetivo.
Revisa energía (...) ; el empuje ya es PASS.
```

`_autonomy_calculated_below_target` checks only autonomy evidence. The
warning/fail branch reuses `_AUTONOMY_BELOW_NEXT_STEP` without gating the
thrust-PASS clause on `can_fly` or the thrust comparison.

### F4 — non-actionable loop after architecture 4/4

On repeated `simular` / `estado` with unchanged `sim.status=fail`:

```text
Siguiente paso: Arquitectura completa (4/4) — puedes optimizar o simular.
```

Architecture completion is a fact, not a resolution action. Orchestrator
creates this `proactive_question` before Continuity ranks the simulation
failure; the generic fail branch then prefers that question over
`fix_simulation_blocker`.

### F5 — global `ayúdame a elegir` ignores the active blocker

At 4/4 with thrust insufficient, `ayúdame a elegir` reprinted project status
instead of opening a relevant motor flow. The Engineer had to type
`definir motor` manually.

### F6 — catalog screening and applied thrust diverge semantically

For a requirement of 8.09 N/motor, the motor list ranked:

```text
1. emax_rs2205_2300 → 8.0 N
```

It is admitted because D8 accepts the catalog `design_space.max_thrust_n=10`,
but applying the SKU writes its nominal `thrust_n=8.0`, which fails the live
calculation. The row does not disclose “range-only candidate”.

This is a separate product-semantics dependency. The fail-routing
investigation must trace it, but must not silently change D8.

### F7 — optimization entry remains generic

`optimizar propulsión` opened:

```text
¿Qué quieres modificar? (material, dimensiones, componentes, carga, etc.)
```

It did not use the known thrust shortfall. Trace as context; do not create a
Conversation Engine.

## Audit relation

Claude's core audit supports several mechanisms:

- 606-line central dispatcher and order-sensitive guards;
- duplicated acquisition/help-choose branches;
- catalog candidates admitted by heuristic max range but displayed with
  nominal thrust;
- recurrent canonical/mirror divergence family.

The audit does not itself prove F1–F5. This walk does. Conversely, unrelated
audit findings (zero motors, material substring, DSE apply index, sweep
visibility) are not causes of this walk and remain separate triage items.

## Engineer decision

Engineer: **“Procede”** (2026-09-03).

First action: investigation of CLI fail-routing coherence. No broad
`orchestrator.py` refactor and no D8/catalog policy change without a later IC.
