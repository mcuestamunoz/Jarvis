# Investigation Report — CLI fail-routing coherence

**Contract:** [investigation_contract_cli_fail_routing_coherence.md](investigation_contract_cli_fail_routing_coherence.md)
**Investigator:** Claude Code
**Date:** 2026-09-03

No `src/` edits. No test edits. No docs edits. Every causal claim below was verified by reconstructing the field fixture in a `tmp_path` project and running the real orchestrator/Continuity/CLI-render code paths — not by reading alone.

---

## 1. Executive verdict

**Shape A — Local fail-routing coherence.** Every mechanism traced below is a single localized bug: a derivation that ignores a field it should read, a render branch missing a guard its siblings already have, or a message-selection condition missing one check. None require touching the simulator, ERF/`_derive_overall`, D8's admission predicate, or a broad orchestrator refactor. §9 names exact files/functions.

The catalog-ranking issue (§3.6/§7) is real and is the direct cause of the walk's motor pick, but its fix is **out of scope for shape A** — Locked Fact #6 and the IC's own C-A/C-B/C-STOP gate apply, and I confirm below (§7) that **C-A is the only option available today**: no existing field distinguishes "covers nominal" from "covers only by design-space margin," so even a copy-only fix would require a new data field — that is catalog policy, not routing.

Two findings go slightly beyond the IC's named mechanisms because they surfaced directly while reproducing the fixture (§3.4, second half, and §3.5): the `_append_arch_progress_hint` suppression added by the Structure A/N1 hotfix only covers the "autonomy undemonstrated" case, not a general thrust-only failure; and `_try_start_assisted_motor_help`'s underspec check is the same D8-margin logic named in §3.6, so §3.5 and §3.6 are the *same* root cause viewed from two call sites, not two separate bugs.

---

## 2. Reproduced field fixture

Reconstructed in `tmp_path` (not the Engineer workspace), matching §2 of the contract: `dron`, autonomy 10 min, payload 1.0 kg, 4 motors, propeller `gemfan_5030` (5 in), battery `lipo_4s_10000mah` (148 Wh, 0.98 kg), frame PVC 0.65 kg, ESC 40 A, `flight_controller`/`sensors` declared, architecture `system_blocks=["propulsion","energy","structure","control"]`.

**State 1 — before motor swap, frame class still absent** (motor `sunnysky_r2305_2500`, 7.5 N nominal):

```text
sim.status=fail  can_fly=False  warnings=[]  safety_margin_ratio=0.9294
available_thrust_n=30.0  required_thrust_n=32.2788  autonomy_min=10.0909 (target 10 — met)
build_startup_context: status_type=blocking  proactive_question="Estructura (frame) en progreso — define los parámetros que faltan."
readiness gaps: GAP-ARCH-BLOCK-INCOMPLETE, GAP-SIM-NOT-PASS, GAP-FRAME-SIZE-MISSING
```

**State 2 — after motor swap to `emax_rs2205_2300` (8.0 N nominal) + frame class set to 5 in** (matches the IC's fixture numbers exactly):

```text
sim.status=fail  can_fly=False  warnings=[autonomy_below_restriction]
required_thrust_n=32.373  available_thrust_n=32.0  total_mass_kg=2.75  autonomy_min=8.88 (target 10)
```

Rendered output (`render_startup_context`, real call):

```text
Situación: Última simulación: fail — el diseño no está cerrado.
...
Siguiente paso: La autonomía calculada está por debajo del objetivo. Revisa energía
   (batería o consumo) o el requisito; el empuje ya es PASS.
   Por qué: autonomy_below_restriction
────────────────────────────────────────────
⚠ Última simulación: WARNING (autonomía por debajo de restricción)
   Arquitectura 4/4 — completa ✓
```

This single render reproduces Locked Facts #1, #2, and #3 simultaneously, byte-for-byte matching the walk's observed outputs.

---

## 3. Frame-class prompt path table (§3.1)

| Entry point | `file:line` | What actually fires in State 1 |
|---|---|---|
| `build_startup_context` architecture-in-progress branch | `orchestrator.py:4383-4412` | **Root cause.** For `arch_next_block="structure"` (a `"component"`-type block, not `"composite"`), the `if get_block_type(arch_next_block) == "composite":` gate at `:4397` is **False**, so the reason-aware branch (`get_block_in_progress_reason`, which already supports component-type blocks per Bug 67) is **never called**. The `else` at `:4409-4412` unconditionally emits `f"{arch_next_label} en progreso — define los parámetros que faltan."` — the generic mass/material prompt — regardless of *why* structure is in-progress. |
| `get_block_in_progress_reason` | `orchestrator.py:2024-2053` | Already correctly extended to `"component"`-type blocks (Bug 67) — it *would* return `"missing_params"` here (frame is non-stub: mass+material present, so not `"missing_components"`) — but is unreachable for structure because of the caller gate above. Even if reached, `"missing_params"` alone does not distinguish "mass/material missing" from "size class missing" from "class incompatible" — it is a two-way split, not aware of Structure A's states. |
| `project_continuity._frame_class_next_step` | `project_continuity.py:123-159` | The correct, Structure-A-specific message *exists* and is gated only on `readiness is not None` (confirmed in State 1: `GAP-FRAME-SIZE-MISSING` **is** in the gap list). It never fires here because Continuity's rank-2 branch (`status_type == "warning" or sim_status not in ("pass","","ok")`) intercepts first (sim_status is `"fail"` in both states) and falls through to its own generic `else` (`proactive_question or "Corrige la causa..."`), which echoes the *already-wrong* `proactive_question` computed in `build_startup_context` — the rich rank never gets a chance to run because Continuity's `next_useful_step` is short-circuited one rank earlier. |
| `_component_prompt_for_first_missing` | `orchestrator.py:2272-2295` | Correctly Structure-A-aware (checks `propeller_diameter_in` and mentions pulgadas) — but this function only fires when a component-description **wizard is actively open** for `"frame"` (`pending_missing_params=["frame"]`). In State 1, no wizard is open — the user is looking at `estado`/Continuity output, not answering a live frame prompt. Not reachable from this walk step. |
| `ayúdame a elegir` (IDLE fallback chain) | `orchestrator.py:1463-1560` (motor), similar propeller/battery helpers | Structure has no analogous "assisted frame help" entry — the fallback chain is motor→propeller→battery only, so it cannot possibly route to a frame-class prompt from this entry point at all (a gap, not a bug in the existing chain). |

**Smallest shared authority (the seam the IC asks to name):** the pieces already exist and just aren't wired together. `frame_class_compatibility_state(project_state)` (`project_closure.py`, Structure A) already returns `not_required | missing | class_compatible | class_incompatible`, and `_frame_completeness(props)` (`domains/aerial.py`) already returns `high | medium | low` for mass/material. A single helper `frame_next_missing_datum(project_state) -> "mass" | "material" | "size_class" | "class_incompatible" | None` composing these two (mass/material first, then class) is the entire missing piece — no new subsystem, one new function reused by (a) the `orchestrator.py:4397` gate (extend it to also call `get_block_in_progress_reason`-style logic for `"structure"`, or add a structure-specific branch alongside the composite one) and (b) `_component_prompt_for_first_missing` (already has half of this logic; can call the same helper instead of its own inline check).

---

## 4. FAIL vs WARNING / thrust vs autonomy truth table (§3.2, §3.3)

### 4.1 `status_type` derivation ignores `sim.status` entirely

`orchestrator.py:4261-4274`:

```python
if signals.get("missing_physics_parameters"):
    status_type = "blocking"
elif signals.get("has_warnings"):        # ← bool(simulation.get("warnings")) — nothing else
    status_type = "warning"
elif signals.get("has_simulation"):
    status_type = "nominal"
else:
    status_type = "no_data"
```

`signals["has_warnings"]` (`reasoning_layer.py`, confirmed by reading) is exactly `bool(warnings)` — it never inspects `simulation.get("status")`. **Answer to Q1: yes, confirmed** — `sim.status="fail"` + any non-empty `warnings[]` always becomes `status_type="warning"`, with zero regard for whether the simulation actually failed. Reproduced directly: State 2 has `sim.status="fail"` and `status_type` comes out `"warning"`.

Worse, and not explicitly asked but found while tracing: **State 1** (`sim.status="fail"`, `warnings=[]`) produces `status_type="blocking"` for an *unrelated* reason (missing_physics_parameters from a different signal) in this fixture, but in a fixture where physics params are all present and thrust simply fails with no warning code, `status_type` would fall through to `"nominal"` — a hard thrust FAIL displayed as if nothing were wrong at all. This is the same root cause, a third undesirable output the hierarchy can produce.

### 4.2 The render layer compounds it with a missing guard

`adapters/cli/main.py:230-248`:

```python
elif status_type == "warning":
    lines.append(f"{icon}Última simulación: WARNING ({short})")     # ← unconditional
elif status_type == "nominal" and not continuity.get("situation"):   # ← gated
    lines.append(f"{icon}Última simulación: OK")
elif status_type == "no_data" and not continuity.get("situation"):   # ← gated
    lines.append(f"{icon}Sin simulación previa")
```

The `"warning"` branch is the **only** one of the three not gated on `not continuity.get("situation")`. Continuity's own `situation` line (`project_continuity.py`, reads `sim.get("status")` raw, correctly says `"fail"`) is printed unconditionally just above (`main.py:210-223`) whenever it's non-empty. Result: both lines print, back to back, contradicting each other — reproduced verbatim in §2's transcript.

### 4.3 Where outputs contradict — answer to Q2

| Output | Reads | In State 2 |
|---|---|---|
| `continuity.situation` | raw `sim.get("status")` (`project_continuity.py`, "Última simulación: {status}" pattern) | `"fail"` — honest |
| `continuity.next_useful_step` (rank 2 else-branch) | raw `sim_status` for the branch *guard*, but the *message inside* depends only on `_autonomy_calculated_below_target` | claims **"el empuje ya es PASS"** — dishonest, see 4.4 |
| `status_type` / `status_reason` | `signals["has_warnings"]` only | `"warning"` — dishonest, ignores `sim.status="fail"` |
| CLI `⚠ Última simulación: WARNING (...)` line | `status_type` | prints `"WARNING"` literal string, contradicting the situation line 3 lines above |

**Answer to Q3: yes** — every fix here is a local derivation/render change. No simulator/ERF contract is touched; `GAP-SIM-NOT-PASS` (ERF) already correctly reads raw `sim.status` and is unaffected either way.

### 4.4 The false thrust-PASS sentence — exact root cause

`project_continuity.py:343-398`, inside the branch guarded by `status_type == "warning" or sim_status not in ("pass","","ok")` (i.e., we are *already inside* the "sim did not pass" branch):

```python
elif _underspec_live:
    ...
elif _autonomy_calculated_below_target(req, sim):
    next_step = _AUTONOMY_BELOW_NEXT_STEP        # "...; el empuje ya es PASS."
    next_why = "autonomy_below_restriction"
else:
    ...
```

`_autonomy_calculated_below_target` (`project_continuity.py:101-112`) checks only autonomy-vs-target — it has **no thrust/`can_fly` check at all**. The branch's own guard condition already proves `sim_status` is not `"pass"` (that's why we're inside it), yet the selected sentence unconditionally asserts thrust passed. This is not a race or an edge case — it is a direct logical contradiction inside one `elif` block, confirmed by execution: State 2 has `can_fly=False`, `sim.status="fail"`, and the rendered next step still says "el empuje ya es PASS."

**Truth table** (only the cell combinations the contract requires, plus what actually fires):

| Thrust | Autonomy | sim.status | Current next step |
|---|---|---|---|
| PASS | below target | pass | `_AUTONOMY_BELOW_NEXT_STEP` (`project_continuity.py:463-464`, gated on `sim_status=="pass"` — **correct, this is the intended case**, added by `implementation_contract_cli_feasibility_autonomy_below.md`) |
| **FAIL** | below target | fail | `_AUTONOMY_BELOW_NEXT_STEP` (`:396-397`, **not** gated on thrust — **the field bug**, false "empuje ya es PASS") |
| FAIL | pass | fail | `_underspec_live` check first; if that's also False, falls to the generic `else` at `:399+` ("Corrige la causa del warning/fallo de simulación.") — honest but generic, no false claim |
| missing thrust | below target | (blocking, params missing) | Rank 1 fires first (`status_type=="blocking"`), never reaches this code — no false claim |

**Existing authority for thrust pass/fail, to reuse rather than duplicate:** `sim.can_fly` (bool, already computed by `FeasibilitySimulator`) or `sim.safety_margin_ratio >= 1.0` — both already present on the `simulation` dict Continuity already has as `sim`. No new calculation needed; the fix is a guard, not new physics: `elif _autonomy_calculated_below_target(req, sim) and sim.get("can_fly"):` for the existing sentence, plus a **new**, separate sentence for the `can_fly is False` + autonomy-below combination that names both problems honestly.

---

## 5. Architecture evidence vs next-action ownership (§3.4)

`proactive_question = "Arquitectura completa (...) — puedes optimizar o simular."` is created in two places:

1. **`build_startup_context`**, `orchestrator.py:4409-4412` region (the generic in-progress branch analyzed in §3) — not this exact sentence, but the same family of "architecture status as next-step" text, created *before* Continuity ranks the real blocker, because architecture progress is computed unconditionally as part of `build_startup_context`'s param/proactive-question cascade, independent of whether a simulation is currently failing.
2. **`_append_arch_progress_hint`**, `orchestrator.py:3421-3446` — appended after a `define_missing_params`/component-description turn completes, when `_next_pending_block` returns `None` (architecture 4/4).

Continuity's fail branch (rank 2, §4.4) *doesn't* directly prefer the architecture sentence in State 2 — it prefers the false autonomy sentence instead, which is arguably worse. The architecture-complete non-action shows up as a **second, separate** line (`"Arquitectura 4/4 — completa ✓"`, `main.py` architecture-progress footer, gated only on `arch_progress` truthiness, not on sim status) alongside the wrong next step — reproduced in §2's transcript.

**`_append_arch_progress_hint`'s suppression gap** (found directly, not just theorized): the Structure A/N1 hotfix added exactly one suppression condition —

```python
if _autonomy_objective_undemonstrated(req, calc, sim):   # orchestrator.py:3439
    return result   # suppress "puedes optimizar o simular"
```

`_autonomy_objective_undemonstrated` (`project_continuity.py`) is `True` when autonomy is `None`/stale **or** below target. It says nothing about thrust. **Confirmed by re-deriving State 1** (thrust FAIL, autonomy target *met*, no warnings): `_autonomy_objective_undemonstrated` returns `False` here, so if a component pick completed in that exact state, `_append_arch_progress_hint` would still emit `"puedes optimizar o simular"` on top of a hard thrust failure. This is the same class of bug as the field walk, just not the literal fixture — the fix needs to check `sim.get("can_fly") is not True` (or equivalent), not only autonomy.

**Minimal ownership rule, as the contract suggests, is directly implementable:** the generic architecture-progress messaging (both the `build_startup_context` in-progress branch and `_append_arch_progress_hint`'s "complete" branch) needs one added guard each — "does the current simulation have an active FAIL/blocker?" — before emitting a non-action sentence. Continuity already computes this (`sim_status not in ("pass","","ok")`); the same check just needs to reach these two call sites, which currently don't consult it at all.

No orchestrator refactor is implied — both are single functions with one missing `if`.

---

## 6. `ayúdame a elegir` trace (§3.5)

State 2, real call: `o.handle_user_text("ayúdame a elegir", ...)` → `{"action": "project_status", "message": None}` — a bare status reprint, reproduced twice in a row (no loop-breaking).

Root cause, `_try_start_assisted_motor_help` (`orchestrator.py:1463-1560`):

```python
if catalog_bound_motor_covers_power_w(project_state.design_properties):   # :1489 — identity-only, True (motor is catalog-bound)
    if bound_motor_sku_is_underspec(project_state):                       # :1495 — False, confirmed by execution
        ...offer catalog list...
    if bound_motor_needs_watts_recovery(project_state):                   # :1505 — False (emax_rs2205_2300 declares 250 W)
        ...offer watts-filtered list...
    return None                                                            # :1517 — nothing left to try, falls through to project_status
```

`bound_motor_sku_is_underspec` returns `False` (confirmed directly) because it reuses D8's `_motor_covers_requirements`, which admits `emax_rs2205_2300` via `max_thrust_n=10.0 ≥ 8.09` — the exact same design-space-vs-nominal gap named in §3.6/§7. Once both underspec and watts-recovery are False, this function has no third branch and returns `None`; nothing downstream in the IDLE dispatch claims the turn, so it degrades all the way to `project_status`.

**Answer to the two IC questions:**

- *Can the first routing IC route from `GAP-SIM-NOT-PASS` to an existing supported action?* Yes — the catalog list (`_offer_component_motor_catalog`) already exists and is already reachable from this exact function for the underspec/watts-recovery cases; the fix is adding a third condition (bound motor's SKU is catalog-admitted but the *current, real* simulation failed on thrust for this motor) that reuses the same offer call, not a new subsystem.
- *Can it avoid claiming a motor picker "solves" the failure while catalog semantics remain unresolved?* Yes, and it must — the offered copy needs to say something honest like "el motor cubre por margen de diseño del catálogo, pero la simulación real no alcanza el empuje" rather than reusing the underspec branch's stronger claim, until §7's catalog-honesty investigation lands its own copy. This is a wording/gating decision for the future IC, not a blocker to routing correctly.

§3.5 and §3.6 are **the same root cause** (D8's margin-based coverage feeding both the ranking in §3.6 and the underspec check in §3.5) observed from two different call sites — worth fixing together, still without touching D8 itself (only the *routing decision* of "should the picker reopen," not "which motors D8 admits").

---

## 7. Catalog dependency gate (§3.6)

Confirmed by direct execution, not just reading:

```text
_motor_covers_requirements (library.py:69-89):
    accepts if max_thrust_n >= min_thrust_n OR thrust_n >= min_thrust_n (either, not both)

find_motors_for_requirements sort key (library.py:329-336):
    (is_generic, abs(thrust_n - min_thrust_n), name)   ← distance from NOMINAL thrust_n

find_motors_for_requirements(min_thrust_n=8.0932, prop_inch=5.0) →
  #1 emax_rs2205_2300        thrust_n=8.000  max_thrust_n=10.00  covers_nominal=False
  #2 sunnysky_r2305_2500     thrust_n=7.500  max_thrust_n=9.50   covers_nominal=False
  #3 brotherhobby_avenger_2500  thrust_n=9.500  covers_nominal=True   ← genuinely-covering candidates rank BELOW the under-nominal ones
  ...
```

Both top-ranked candidates fail nominal coverage; every genuinely-covering candidate ranks lower, because the sort key rewards numerical closeness to the floor, not whether the floor is actually met. `bound_motor_sku_is_underspec` (§6) reuses the same admission predicate, so it also does not flag this SKU as underspecified post-bind.

**Recommendation: C-A (default), confirmed as the only viable option today** — I checked whether C-B (copy-only, using an existing field) is available: `MotorSuggestion` (`motor_catalog_assist.py:14-23`) has no field distinguishing nominal-covering from margin-only candidates (`idx, name, thrust_n, kv_rating, weight_g, max_watts, is_generic` — nothing else). Exposing this distinction to the user requires adding a new field/predicate, which is catalog policy, not routing — out of scope for this IC by its own constraints. C-A stands: a separate catalog-honesty investigation should define nominal-safe vs. range-only groups/copy for `MotorSuggestion`/`_format_candidate_line`, and only then can the routing fix in §5/§6 use honest wording when reopening the picker for this case.

---

## 8. Core-audit triage matrix (§4)

| Audit finding | Relation to this walk |
|---|---|
| Range-only motor candidates (audit Bug 103) | **Caused this walk directly.** Identical mechanism to §3.6/§7 — the audit finding and this investigation's §3.6 are the same bug, found independently by two different passes. |
| Frame/prop mirrored-param debt (audit Bugs 82-85) | **Related mechanism, not the direct cause.** This walk's frame class was set via `set_frame_material` directly (no divergence path exercised); the frame-prompt bug traced in §3.1 is a *different* mechanism (a missing reason-aware branch in `build_startup_context`, not a mirrored-param sync gap). Both live in the Structure A/frame area but are independent bugs. |
| Orchestrator dispatcher size/order (audit finding on `_handle_user_text_inner`) | **Related mechanism.** None of the bugs found here live inside the 606-line dispatcher itself — `build_startup_context`, `_append_arch_progress_hint`, and `project_continuity.py`'s rank chain are separate, smaller functions. But the general pattern this investigation found (generic fallback messages added once, never revisited when a more specific case like Structure A was added later) is the same *kind* of drift the audit's size/complexity finding warns about. Not a reason to split `orchestrator.py` as part of this IC — noted per the contract's explicit prohibition. |
| Triplicated catalog help (audit Bug 91) | **Unrelated.** That finding is about `_handle_component_description`'s offer/pick triplication (motors/propellers/battery description flow). This walk's `ayúdame a elegir` degradation runs through `_try_start_assisted_motor_help` (the IDLE IntentResolver fallback chain), a structurally different code path. |
| Zero motors crash (audit Bug 80) | **Unrelated.** Different mechanism (division by zero), different trigger (motor_count=0), not reachable from this walk. |
| Material substring fabrication (audit Bug 81) | **Unrelated.** Text-parsing bug in `domains/materials.py`, not exercised by this walk (frame material was bound directly via catalog writer, not parsed from ambiguous text). |
| `ninguno` project selection (audit Bug 88) | **Unrelated.** CLI startup project-selection bug, no connection to an active project's fail-routing. |
| DSE "aplica opción 3" fallback (audit Bug 97) | **Unrelated.** DSE apply-index parsing, not exercised — this walk never reaches a DSE apply step. |
| Estimative sweep disappearing (audit Bug 99) | **Unrelated.** Concerns `build_with_estimative_sweep` adoption gaps; this walk's `calcular`/`simular` calls go through the real orchestrator `handle_user_text` path (which does use the sweep wrapper per `actions/calculate.py`/`actions/simulate.py`) — not a factor in the reproduced outputs above. |

Only the first entry is directly causal; the rest are correctly out of scope for this IC, confirming the contract's own boundary was drawn correctly.

---

## 9. First IC file/test map (Shape A)

**Files/functions** (for a future, separately-ratified Implementation Contract — nothing here is authorization to edit):

| File | Function | Change |
|---|---|---|
| `core/orchestrator.py` | `build_startup_context` status_type hierarchy (`:4261-4274`) | Elevate `sim.status not in ("pass","","ok")` (or `can_fly is False`) to at least `"warning"`-strength independent of `has_warnings`, so a FAIL is never displayed as `"nominal"`, and is distinguishable from a genuine warning-only PASS. |
| `adapters/cli/main.py` | `render_startup_context` (`:241-244`) | Gate the `status_type=="warning"` WARNING line on `not continuity.get("situation")`, matching the nominal/no_data branches — or retire it now that Continuity's `situation` line already covers this honestly. |
| `core/project_continuity.py` | rank-2 branch (`:396-398`) | Guard `_AUTONOMY_BELOW_NEXT_STEP` selection on thrust actually passing (`sim.get("can_fly")` or margin ≥ 1); add a new, separate sentence for thrust-FAIL + autonomy-below that names both, never claims PASS. |
| `core/orchestrator.py` | `build_startup_context` architecture in-progress branch (`:4383-4412`) | Extend the `get_block_type(...) == "composite"` reason-aware gate (or add a parallel structure-specific branch) to use the small shared authority named in §3 (`frame_class_compatibility_state` + `_frame_completeness`) instead of the generic fallback, for `"structure"`. |
| `core/orchestrator.py` | `_append_arch_progress_hint` (`:3439`) | Extend the suppression condition beyond `_autonomy_objective_undemonstrated` to also cover `sim.get("can_fly") is not True` generally. |
| `core/orchestrator.py` | `_try_start_assisted_motor_help` (`:1517`) | Before returning `None`, add a condition: bound motor is D8-admitted-by-margin but the *current* simulation's thrust actually fails for this motor → reopen the catalog list with honest, non-underspec copy (§6/§7). |

**Non-goals reaffirmed:** `_motor_covers_requirements`/D8 sort key untouched (separate catalog-honesty investigation per §7); `MotorSuggestion` shape untouched; `_derive_overall`/ERF untouched; no `orchestrator.py` split; no new subsystem.

**Tests to add** (future IC), mirroring the contract's §7 skeleton with the exact scenarios verified above:

- Frame class missing + prop known + mass/material known → reprompt names "clase en pulgadas", not mass/material (needs the §3/§9 fix first — currently fails).
- `sim.status="fail"`, `warnings=["autonomy_below_restriction"]` → rendered status stays FAIL-labeled, never "WARNING" (currently fails — reproduced in §2).
- Thrust FAIL + autonomy below → next step never contains "el empuje ya es PASS" (currently fails — reproduced in §4.4).
- Architecture 4/4 + thrust-only FAIL (autonomy target met) → `_append_arch_progress_hint` suppressed (currently fails — derived in §5, not yet directly executed as a full turn but the suppression-condition gap is confirmed by code + State 1's signal values).
- `ayúdame a elegir` with a D8-margin-admitted bound motor whose real simulation fails on thrust → does not degrade to bare `project_status` (currently fails — reproduced in §6).
- Regression: existing PASS/undemonstrated-autonomy (`test_cli_stale_energy_recalc.py`), autonomy-below-with-PASS-thrust (`test_project_continuity.py`), watts-recovery, T1/T1+2, Structure A, and N1 tests must stay green — none of the traced fixes touch the guards those tests exercise (`sim_status=="pass"` gated branches are untouched; only the "not pass" branches gain new sub-conditions).

---

## 10. Frozen honored

No `src/` edits. No test edits. No catalog JSON edits. No Engineer `workspace/` mutation — all fixtures built in `tmp_path`. `orchestrator.py` not split. No Conversation/Decision Engine introduced. `_derive_overall`, ERF evidence, and `ASSEMBLY_READY` not touched (confirmed: `GAP-SIM-NOT-PASS`/`GAP-REQUIREMENTS-UNMET:autonomy` both correctly appeared in the readiness dump in §2, driven by existing, unmodified logic). D8's `_motor_covers_requirements` and catalog data read only, never proposed for change (§7 explicitly recommends deferring to a separate investigation). No simulation formula, thrust, autonomy, OP resolution, or mass calculation touched — every number reproduced above came from the existing, unmodified `CalculationEngine`/`FeasibilitySimulator`. Option B ERF, G24-B scoring, Tier 3, CAD, H5, and hardware debt not reopened. No fix implemented.
