# Investigation Contract — CLI fail-routing coherence

**Project:** Jarvis  
**Date:** 2026-09-03  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_cli_fail_routing_coherence.md`

**Status:** INVESTIGATION CLOSED — JES revision R1–R5 **PASS WITH NOTES**  
**Review:** [investigation_review_cli_fail_routing_coherence.md](investigation_review_cli_fail_routing_coherence.md)  
**Revision:** [investigation_revision_cli_fail_routing_coherence.md](investigation_revision_cli_fail_routing_coherence.md)  
**IC:** [implementation_contract_cli_fail_routing_coherence.md](implementation_contract_cli_fail_routing_coherence.md)  
Engineer `procede` (2026-09-03)

**Type:** Product-path investigation. Trace why deterministic facts already
present in state/readiness fail to produce an actionable next step. No
implementation. No broad orchestrator refactor. No D8 policy change.

**Base:** live tree after Structure A + N1 hotfix, reviewer suite **2143**.

**Field note:** [engineer_cli_walk_fail_routing_coherence.md](engineer_cli_walk_fail_routing_coherence.md)  
**Related review:** [implementation_review_structure_a.md](implementation_review_structure_a.md)  
**N1 closure:** [implementation_review_structure_a_n1_hotfix.md](implementation_review_structure_a_n1_hotfix.md)

---

## 0. Role and constraints

Claude investigates and writes the report. Do **not** edit `src/`, tests,
catalog JSON, docs, or Engineer workspace.

Treat Claude's broad core audit as **leads**, not product authority. Verify
every claim used by this report with `file:line` and a tmp/in-memory probe.

Do not:

- split `orchestrator.py`;
- introduce a Conversation Engine / Decision Engine;
- change `_derive_overall`, ERF evidence, or `ASSEMBLY_READY`;
- change D8 `_motor_covers_requirements` or catalog data;
- change simulation formulas, thrust, autonomy, OP resolution, or mass;
- reopen Option B ERF, G24-B scoring, Tier 3, CAD, H5, or hardware debt;
- implement any fix.

Preserve `workspace/autonomía-de-10-minutos-86f6a0e8effa`. Reconstruct in
`tmp_path` or in-memory fixtures.

---

## 1. Locked facts and honesty constraints

These are not questions:

1. `simulation.status == "fail"` must not be presented as a warning-only
   state merely because `warnings[]` is non-empty.
2. Jarvis must not say “el empuje ya es PASS” unless deterministic evidence
   says thrust passes (`can_fly is True` and/or available ≥ required under the
   existing authority).
3. “Arquitectura 4/4” is evidence, not a resolution action for a simulation
   failure. Repeating `simular` with unchanged inputs is not a useful next
   step.
4. If `GAP-FRAME-SIZE-MISSING` is active while frame acquisition is pending,
   the prompt must request `size_class_inch` explicitly. It must not loop on
   already-known mass/material.
5. `ayúdame a elegir` must not silently degrade to a status reprint when a
   supported assisted path can address the active blocker.
6. A catalog row displayed as `8.0 N` must not imply it nominally satisfies
   `≥8.09 N`. D8 design-space admissibility and applied nominal thrust are
   different claims.

The report may determine that items 4–5 need separate ICs. It may not weaken
these constraints.

---

## 2. Field fixture

Reconstruct this state without mutating Engineer workspace:

```text
vehicle                 dron
objective               autonomy 10 min
payload                 1.0 kg
motors                  4
motor initially         sunnysky_r2305_2500, 7.5 N, 220 W
propeller               gemfan_5030, D=5 in
battery                 lipo_4s_10000mah, 148 Wh, 0.98 kg
frame                   PVC 0.65 kg, class initially absent, then 5 in
ESC                     40 A
control                 Pixhawk 4 + Here3
architecture            4/4 after frame class/control
replacement motor       emax_rs2205_2300, nominal 8.0 N
final total mass        2.75 kg
required                32.373 N / 8.0932 N per motor
available               32.0 N
autonomy                8.88 min < 10 min
sim.status              fail
sim.can_fly             false
sim.warnings            [autonomy_below_restriction]
```

Observed outputs to reproduce:

```text
Indica material y masa. Ej: 'fibra de carbono 450g'
Estructura (frame) en progreso — define los parámetros que faltan.
Arquitectura completa (4/4) — puedes optimizar o simular.
La autonomía ...; el empuje ya es PASS.
⚠ Última simulación: WARNING (autonomía por debajo de restricción)
```

---

## 3. Mandatory traces

### 3.1 Frame-class acquisition routing

Trace all paths producing a frame prompt after mass+material are already
known and class is missing:

- `_component_prompt_for_first_missing`;
- `_handle_component_description` low/fallback probe;
- `_append_arch_progress_hint`;
- `get_block_in_progress_reason`;
- wizard reprompt and `ayúdame a elegir`;
- `build_acquisition_brief`;
- Continuity `_frame_class_next_step`.

For each, record:

```text
entry utterance → session mode/pending keys → branch → exact output
```

Explain why the Structure A conditional prompt exists but was bypassed in the
walk. Name the smallest shared authority that could answer:

```text
frame next missing datum = mass | material | size class | class incompatibility
```

Do not design a new subsystem.

### 3.2 Simulation FAIL vs status_type WARNING

Trace:

- `derive_project_signals` (or equivalent source of `has_warnings`,
  `has_simulation`, fail status);
- `build_startup_context` status hierarchy;
- CLI renderer for `status_type=="warning"`;
- `EngineeringReadiness` `GAP-SIM-NOT-PASS`.

Answer:

1. Can `sim.status=fail` + any warning always become `status_type=warning`?
2. Which outputs use `status_type`, which use raw `sim.status`, and where do
   they contradict?
3. Can the first IC fix presentation/routing without changing simulator or
   ERF contracts?

### 3.3 False thrust-PASS sentence

Trace `_autonomy_calculated_below_target` and every call site selecting
`_AUTONOMY_BELOW_NEXT_STEP`.

Build the truth table:

```text
thrust pass/fail × autonomy pass/fail × sim status → current next step
```

At minimum include:

- thrust PASS + autonomy below (existing intended case);
- thrust FAIL + autonomy below (field case);
- thrust FAIL + autonomy pass;
- missing thrust + autonomy below.

Name the existing deterministic authority for thrust pass/fail. Do not
duplicate the force comparison in CLI copy if `can_fly` / calculation output
already owns it.

### 3.4 Architecture-complete proactive question on FAIL

Trace creation and consumption of:

```text
proactive_question = "Arquitectura completa (...) — puedes optimizar o simular."
```

Specifically:

- why it is created before closure/readiness facts are ranked;
- why Continuity's fail branch prefers it;
- why `_append_arch_progress_hint` can append the same non-action after a
  component/motor pick;
- all tests pinning this sentence.

Propose a minimal ownership rule:

```text
architecture progress owns evidence;
active failure owns next action.
```

Do not refactor the whole orchestrator.

### 3.5 Contextual `ayúdame a elegir`

Trace IDLE help-choose fallback order:

```text
motor → propeller → battery → status/reasoning fallback
```

For the final fixture, show why `_try_start_assisted_motor_help` returns no
offer even though applied nominal thrust is insufficient.

Answer whether the first routing IC can:

- route from `GAP-SIM-NOT-PASS` to an existing supported action; and
- avoid claiming a motor picker can solve the failure when catalog candidate
  semantics remain unresolved.

No generic Conversation Engine.

### 3.6 Catalog design-space vs applied nominal thrust (dependency gate)

Confirm with `file:line`:

- D8 admits `emax_rs2205_2300` because
  `design_space.max_thrust_n=10.0` covers 8.09 N;
- the displayed/applied value is `thrust_n=8.0`;
- ranking uses distance from nominal `thrust_n`, allowing an under-nominal
  row to rank first;
- `bound_motor_sku_is_underspec` reuses D8 coverage and therefore does not
  consider the bound SKU underspecified afterward.

Pick exactly one recommendation:

- **C-A — separate catalog-honesty investigation (default):** first routing
  IC does not change D8; a second investigation defines nominal-safe vs
  range-only groups/copy.
- **C-B — copy-only inside routing IC:** only if an existing field already
  exposes range-only status without new policy.
- **C-STOP:** if useful routing cannot be made honest before catalog policy.

Do not recommend silently filtering by nominal thrust without discussing the
loss of design-space candidates. Do not recommend applying
`max_thrust_n` as actual thrust.

### 3.7 Optimization entry (bounded)

Trace why `optimizar propulsión` enters the generic iteration wizard instead
of using the active simulation blocker. Decide only whether this is:

- same routing seam;
- separate DSE/intent work;
- intentional behavior needing better copy.

Do not redesign optimization in this investigation.

---

## 4. Core-audit triage boundary

The report must include a short matrix:

```text
audit finding → caused this walk / related mechanism / unrelated
```

Mandatory entries:

- orchestrator dispatcher size/order;
- triplicated catalog help;
- range-only motor candidates;
- frame/prop mirrored-param debt;
- zero motors crash;
- material substring fabrication;
- `ninguno` project selection;
- DSE “aplica opción 3” fallback;
- estimative sweep disappearing.

Only the first three are expected to relate directly. Do not absorb unrelated
audit debt into this IC.

---

## 5. Mandatory report shapes

Recommend exactly one first implementation shape:

- **A — Local fail-routing coherence (default):** frame-class prompt + raw
  sim-fail status + honest thrust/autonomy next-step + suppress
  architecture-complete non-action on fail. Catalog semantics stays a
  separate investigation.
- **B — Split:** frame-class acquisition IC first, then simulation routing IC,
  only if seams/tests cannot be changed safely together.
- **C — Stop for product decision:** if ranking thrust vs autonomy requires an
  Engineer choice not derivable from existing blockers.
- **D — Architecture refactor required:** only with proof that no localized
  fix is safe. This triggers a separate Engineer ★ and no implementation.

If A, specify exact files/functions/tests and show why no new subsystem is
needed.

---

## 6. Required report sections

1. Executive verdict and shape A/B/C/D.
2. Reproduced field fixture.
3. Frame-class prompt path table.
4. FAIL/WARNING and thrust/autonomy truth table.
5. Architecture evidence vs next-action ownership.
6. `ayúdame a elegir` trace.
7. Catalog dependency gate C-A/B/STOP.
8. Core-audit relation matrix.
9. First IC file/test map.
10. Frozen honored.

Every causal claim needs `file:line`. No production edits.

---

## 7. Tests/probes to sketch for the future IC

- Known prop D + frame mass/material + missing class:
  `ayúdame a elegir`/reprompt names **clase en pulgadas**, not mass/material.
- `sim.status=fail`, `warnings=[autonomy_below_restriction]`:
  rendered status remains FAIL, not WARNING.
- Thrust FAIL + autonomy below: next step never says “empuje ya es PASS”.
- Architecture 4/4 + unchanged sim FAIL: next step names blocker; does not
  recommend merely simulating again.
- Thrust PASS + autonomy below: existing autonomy sentence remains valid.
- Existing PASS/undemonstrated-autonomy, watts recovery, T1/T1+2,
  Structure A, and N1 tests remain green.

---

## 8. After investigation

Write `.jes/artifacts/investigation_report_cli_fail_routing_coherence.md`.
Stop. Cursor reviews. A later ratified Implementation Contract is the only
authorization to edit `src/`.
