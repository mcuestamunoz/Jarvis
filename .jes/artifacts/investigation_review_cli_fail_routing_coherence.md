# Investigation Review — CLI fail-routing coherence

**Date:** 2026-09-03  
**Reviewer:** JES / Cursor  
**Report:** [investigation_report_cli_fail_routing_coherence.md](investigation_report_cli_fail_routing_coherence.md)  
**Contract:** [investigation_contract_cli_fail_routing_coherence.md](investigation_contract_cli_fail_routing_coherence.md)

**Verdict:** **PASS WITH NOTES** (R1–R5 closed by JES revision, Engineer `Procede` 2026-09-03)

**Revision:** [investigation_revision_cli_fail_routing_coherence.md](investigation_revision_cli_fail_routing_coherence.md)

Original review below is retained as the gap list. The revision reproduced the active frame wizard and the exact 4/4 CTA, locked **C-A1**, and defined FAIL as a render/Continuity contract without a new `status_type` enum. Implementation is authorized **only** via [implementation_contract_cli_fail_routing_coherence.md](implementation_contract_cli_fail_routing_coherence.md).

---

## 1. What passes

### P1 — exact physics fixture and contradiction reproduced

The report reconstructed the final state in `tmp_path` and reproduced, in one
real render:

- raw `sim.status=fail`;
- false “el empuje ya es PASS”;
- contradictory CLI `WARNING`;
- architecture 4/4 evidence.

The values match the field fixture: `32.0 < 32.373 N`, autonomy `8.88 < 10`
min, `can_fly=False`.

### P2 — FAIL/WARNING cause is established

The trace of `status_type` through `has_warnings`, followed by the
unconditional CLI warning line, is sufficient to prove the contradictory
render mechanism.

### P3 — false thrust-PASS cause is established

The report proves that `_autonomy_calculated_below_target` checks autonomy
only and is selected inside the non-pass branch without a thrust gate. The
required truth-table cases are present.

### P4 — D8/ranking mechanism is established

The report proves that:

- D8 can admit by `design_space.max_thrust_n`;
- ranking uses distance to nominal `thrust_n`;
- the selected SKU writes a nominal value below the requirement;
- the same D8 predicate makes the bound SKU appear non-underspecified.

This is strong evidence for a separate catalog-honesty decision.

### P5 — frozen scope honored

No production, test, catalog, docs, or Engineer-workspace mutation is
reported. No broad orchestrator refactor was proposed.

---

## 2. Required revision R1 — reproduce the actual frame wizard loop

The contract required every frame-prompt path, including:

- `_handle_component_description` low/fallback;
- wizard reprompt;
- `build_acquisition_brief`;
- `ayúdame a elegir`;
- session mode and pending keys.

The report covers the IDLE startup context but does not reproduce the walk
transition:

```text
frame already contains PVC + 0.65 kg
GAP-FRAME-SIZE-MISSING active
active component acquisition still expects frame
user: "ayúdame a elegir"
output: "Indica material y masa. Ej: 'fibra de carbono 450g'"
```

This omission matters because the direct source of that exact sentence is not
`build_startup_context`. It is the hand-written low-completeness frame branch
in `orchestrator.py:3350-3372`:

```python
elif (expected_keys and expected_keys[0] == "frame") or (...):
    has_mass = "mass_kg" in spec.properties
    has_material = "material" in spec.properties
    ...
    else:
        msg = "Indica material y masa. Ej: 'fibra de carbono 450g'"
```

For `"ayúdame a elegir"`, the current utterance itself contains neither mass
nor material, so this branch can ask for both again even when persisted frame
state already has both. It bypasses
`_component_prompt_for_first_missing` (`orchestrator.py:2272-2294`), whose
Structure A prompt does mention class in inches.

`build_acquisition_brief` is also relevant: its question comes directly from
static `COMPONENT_PROMPTS` (`acquisition_brief.py:58-68`), whose frame copy is
still material+mass only. The report did not trace this required surface.

### Claude must add

1. A real-orchestrator reproduction of this active-session turn.
2. Before/after session mode, `pending_missing_params`,
   `pending_param_definitions`, and `pending_missing_reason`.
3. Exact dispatcher branch and output.
4. A call-site table for `_handle_component_description`,
   `_component_prompt_for_first_missing`, `build_acquisition_brief`, active
   reprompt, and IDLE startup.
5. A corrected smallest-authority recommendation that covers both startup and
   active wizard surfaces. Do not place a shared contract on private
   `_frame_completeness` without naming its stable owner and input shape.

Until this is done, §3.1's statement that the generic startup branch is the
root cause is only one root cause, not the explanation of the observed loop.

---

## 3. Required revision R2 — exact 4/4 proactive-question path

The contract requested the exact sentence:

```text
Arquitectura completa (4/4) — puedes optimizar o simular.
```

The report says it is created in two places but then acknowledges that its
first cited place is only the same “family” of text. The exact startup
creation is `orchestrator.py:4450-4455`, not the in-progress region:

```python
if not proactive_question:
    proactive_question = (
        f"Arquitectura completa ({arch_progress}) — "
        f"puedes optimizar o simular."
    )
```

The second exact source is `_append_arch_progress_hint` at
`orchestrator.py:3446`.

The report must:

1. Trace `orchestrator.py:4450-4455` into Continuity's generic fail fallback
   for **thrust FAIL + autonomy pass**, where the autonomy-specific sentence
   does not intercept it.
2. Reproduce that path with a real call, not only infer the condition.
3. Distinguish the valid evidence footer
   `"Arquitectura 4/4 — completa ✓"` from the invalid next action
   `"puedes optimizar o simular"`. The footer need not be suppressed merely
   because simulation failed.
4. List all tests pinning the sentence/behavior. At minimum, current searches
   locate relevant assertions/fixtures in:
   - `tests/test_fn020_completeness_coherence.py`;
   - `tests/test_project_continuity.py`;
   - `tests/test_cli_stale_energy_recalc.py`;
   - `tests/test_fn021_session_hygiene.py`.
5. Add the `build_startup_context` complete-architecture branch to the future
   file/test map. It is currently missing there.

---

## 4. Required revision R3 — resolve C-A vs Shape A contradiction

The report makes incompatible recommendations:

- §7 says C-A is required and range-only semantics must be handled by a
  separate catalog-honesty investigation.
- §6 says the first routing IC can reopen the catalog with explicit
  margin-only copy.
- §9 includes detection of “D8-admitted-by-margin” plus that copy in the first
  Shape A implementation.

The latter two already classify and expose range-only candidates, which is
the product semantic deferred by C-A.

Also, the claim that C-B is technically impossible because
`MotorSuggestion` lacks a dedicated boolean is too strong:
`MotorSuggestion.thrust_n` and the known required thrust can derive nominal
coverage at a caller. The reason to prefer C-A is product-policy ownership
and consistent grouping/copy across surfaces, not literal impossibility.

### Claude must choose one coherent sequence

- **C-A1:** first routing IC excludes catalog reopening for this case; separate
  catalog-honesty investigation lands before contextual motor help can be
  completed; or
- **C-A2:** catalog-honesty investigation/IC precedes the routing IC, allowing
  the later routing change to consume its ratified classification; or
- **C-STOP:** Shape A cannot honestly satisfy contextual help until the
  Engineer decides catalog semantics.

Do not leave margin classification/copy inside the first routing IC while
simultaneously declaring it deferred.

---

## 5. Required revision R4 — define FAIL semantics, not “warning-strength”

The future map proposes:

```text
Elevate sim.status fail to at least "warning"-strength.
```

That wording does not satisfy the locked constraint that FAIL must not be
presented as warning-only. Suppressing the duplicate CLI line would improve
rendering while leaving `status_type` semantically wrong for downstream
ranking.

The revised report must name the exact derivation contract:

- precedence of missing-physics blocking, raw simulation FAIL, genuine
  warning-only PASS, nominal, and no-data;
- resulting `status_type`/`status_reason` for each;
- whether an existing value such as `blocking` is reused or a public contract
  would need extension;
- affected consumers/tests.

Do not invent a new public enum casually. If the existing shape cannot
express the distinction safely, flag that as an IC decision.

---

## 6. Required revision R5 — tighten citations and future ownership

Add exact `file:line` citations for causal claims currently described only as
“confirmed by reading”, especially:

- `reasoning_layer.py` derivation of `has_warnings`;
- `_autonomy_objective_undemonstrated`;
- raw simulation status used by Continuity;
- the exact generic fail fallback consuming `proactive_question`.

After R1, revise the proposed frame helper's owner and all call sites. A small
helper remains acceptable; a new subsystem does not.

---

## 7. Review conclusion

The investigation has established three real defects and one catalog
dependency:

1. FAIL/WARNING contradiction — established.
2. false thrust-PASS sentence — established.
3. generic architecture next action on failure — mechanism strongly indicated,
   exact mandatory path still incomplete.
4. frame-class loop — field evidence exists, but the report traced the wrong
   surface for the exact `"Indica material y masa"` output.
5. catalog D8/ranking/help interaction — mechanism established, sequencing
   unresolved.

Claude should revise the same report, preserving its successful sections and
adding/correcting R1–R5. Stop after the revised report. JES reviews again.
