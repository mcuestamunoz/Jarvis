# Investigation Report — Structure A (masa + encaje)

**Contract:** [investigation_contract_structure_a.md](investigation_contract_structure_a.md)
**Investigator:** Claude Code
**Date:** 2026-09-03
**Baseline:** tag `v0.3.5` + live tree (DSE apply honesto reviewed, suite 2124)

No `src/` edits. No new tests. Everything below is read/trace only, cited `file:line`.

---

## 1. Executive summary

**Recommended shape: B — masa + fit, one IC.** The two seams (mass write, size-required-when-D-known) share the same writer (`set_frame_material`) and the same completeness/progress call sites, so splitting them into two ICs would mean touching `component_writers.py`, `aerial.py`, and both `_block_progress_status` copies twice instead of once, for no isolation benefit — a fit rule that's "coming next IC" would leave a project honestly-massed but still lying 4/4 on frame size in the interim, which is worse than shipping both together. This confirms Engineer ★2's default.

Two corrections to the draft IC, both non-blocking for shape B, detailed below:

1. **The mass leak is not (only) where the draft IC/notes point.** `apply_material_definition` (`mutation_engine.py:158-172`) does drop grams whenever it's reached, but in the most directly-confirmed path (a live, passing test reproduces it — `tests/test_cli_polish.py::test_t14_iterate_material_compound_pvc_400g_extracts_and_estimates`), the grams are already gone before `mutation_engine.apply_mutation` is even called: the wizard layer (`iterate_interactive_session.py`) strips the user's text down to a bare material name at two call sites (`:295`, `:412`). A third, less-verified path (session seeded with `operacion="definir"` from turn 1) would instead preserve the mass into `component_patch` and lose it one step later, at `mutation_engine`'s DEFINE dispatch priority (`:66-68`, material wins over the component-patch-aware branch). Fixing only `mutation_engine.py`/`apply_material_definition` (as the draft IC's §5 file table implies) will not reproduce the walk's fix in the confirmed case — the real seam is one layer up, in the session file. See §2.
2. **A dedicated `GAP-FRAME-*` type is not required to flip `_derive_overall` to `NOT_ASSEMBLY_READY` on misfit** — an *existing* generic mechanism (`GAP-ARCH-BLOCK-INCOMPLETE`) already does that for free, the moment architecture progress honestly reports structure incomplete. The dedicated gap type is still the right move, but for **copy honesty** (LEVEL A framing, telling the user *why*), not because the rollup needs it. This directly answers the Gate question in §1 of the contract. See §5.

`GAP-PROP-MOTOR-MISMATCH` is confirmed motor↔propeller only (catalog pairing), never frame. `CalculationEngine` confirmed never reads any frame/`size_class_inch` field. No propulsion invasion risk found. See §4.

---

## 2. Masa path table

| Path | Writer that actually runs | Reaches `structure_mass_override_kg`? | Walk leak? |
|---|---|---|---|
| Acquisition component description ("carbono 450g" answering a `frame` prompt) | `orchestrator.py:2273-2307` `_apply_inferred_component_spec` → `extract_frame_properties` (`aerial.py:206-239`) → `set_frame_material` (`component_writers.py:49-104`) | **Yes** — `set_frame_material` writes both `components["frame"].properties` and `current_parameters["structure_mass_override_kg"]` atomically (`component_writers.py:94-99`) | No — this path is correct today. |
| Iterate wizard, material variable, "cambiar material" then a later turn "PVC 200g" | `iterate_interactive_session.py:294-296` `_awaiting_material_value` branch → `self._extract_material_from_text(normalized)` | **No** | **Yes** — `_extract_material_from_text` (`iterate_interactive_session.py:1266-1273`) matches only against `_KNOWN_MATERIALS` aliases and returns the bare canonical name; the mass substring in `normalized` is discarded here, one whole layer before `mutation_engine` runs. `draft.value` becomes `"pvc"`, never `"pvc 200g"`. |
| Iterate wizard, material variable, name embedded in the strategy answer (e.g. step-2 answer is directly "PVC 200g") | `iterate_interactive_session.py:409-419` (Gap-1 same-turn block) → `self._extract_material_from_text(updated_draft.strategy)` | **No** | **Yes** — same extractor, same truncation, a second independent call site. Whichever of these two fires (depends on whether the material name arrived in the same turn as the strategy or a follow-up turn), the mass is gone before `draft.value` is set. |
| Iterate wizard, session **seeded with `operacion="definir"`/DEFINE from turn 1** (`_build_initial_draft`, `iterate_interactive_session.py:511-524`, confirms `operation` is a raw pass-through of the seed) + variable "material" | `iterate_interactive_session.py:327-372` `_needs_definition_value` (requires `operation == DEFINE`, checked *before* `_apply_answer` runs on this turn's text) → `infer_component(normalized, ...)` on the **full, untouched** raw text, builds `component_patch["frame"]` if `infer_component` resolves a frame rule from bare "pvc 200g" (not verified here — `infer_component`'s frame-key resolution from text with no "frame"/"chasis" keyword was not traced; flag for the real IC, not re-derived here) | **No — and this is the more interesting failure** | **Different mechanism, same result.** Even if `component_patch["frame"]` ends up correctly populated with `mass_kg`, it is never used: `mutation_engine.apply_mutation`'s DEFINE dispatch (`:66-68`) checks `_is_material_definition` (`:365-368`, true — variable contains "material") *before* `_is_power_unit_definition` (`:69-70`, the only branch that reads `component_patch` via `apply_component_definition`). `apply_material_definition` (`:158-172`) is called instead and only ever reads `draft.value`, ignoring `component_patch` entirely. So this third path also loses the mass, but at the **dispatch-priority** step in `mutation_engine.py`, not at the extraction step in the session. Whether this exact path or the two `_extract_material_from_text` truncations above is what the walk actually hit depends on how the session was seeded (not fully re-derivable from the walk note alone) — but all three converge on the same observable symptom: `structure_mass_override_kg` never changes. |
| `actions/iterate.py` DEFINE dispatch, once a draft with `variable` containing `"material"` reaches it | `mutation_engine.py:66-68` `apply_mutation` → `_is_material_definition` (`mutation_engine.py:365-368`, true for any variable/strategy/objective containing `"material"`) → `apply_material_definition` (`mutation_engine.py:158-172`) | **No** — writes only `design_properties.structure.material`, a string, never mass, never calls `set_frame_material` | **Yes, but downstream of the real leak** — even a rich `draft.value` (say, unmodified "pvc 200g" survived) would still only be written as a literal string here; there's no regex/extractor call in this function at all. |
| `actions/iterate.py` DEFINE routing | `IterateAction.run` (`actions/iterate.py:142-145`) → `_run_declarative_iteration` (`actions/iterate.py:296-...`) | **No** — `_run_declarative_iteration` calls only `_apply_design_property_mutation` (`actions/iterate.py:299`, merges `design_properties.structure`/`components` patches); it **never** calls `_apply_mutation_to_parameters` (`actions/iterate.py:454-474`, the function that would write `structure_mass_override_kg` from a `mutated_state["total_mass_kg"]`/`current_parameters` key) — that call only happens on the non-DEFINE branch (`actions/iterate.py:147`, unreachable once `draft.operation == DEFINE`) | **Structural, not incidental** — even if `apply_material_definition` were changed to also emit mass data in its returned dict, `_run_declarative_iteration` has no code path that would route it into `current_parameters`. A fix must either (a) explicitly call `set_frame_material` inside `_run_declarative_iteration` when the material draft carries a parsed mass (draft IC's own §2.1 intent, just needs the mass to actually survive to this point — see finding above), or (b) add a `current_parameters` merge step there. (a) is smaller and matches the acquisition path's own pattern. |
| Acquisition regression ("carbono 450g" via component description) | Same first row | Yes, unchanged | N/A — already correct; add a regression test per draft IC's ask so nothing here changes. |

**One writer that should own mass:** `set_frame_material` (`component_writers.py:49`), already true. **Callers that bypass it:** the two `_extract_material_from_text` call sites in `iterate_interactive_session.py` (lines 295, 412) truncate the raw text before any mass could ever reach a writer, and `apply_material_definition` (`mutation_engine.py:158`) never calls a writer at all. **A correct fix must change the extraction point** (`iterate_interactive_session.py`, not just `mutation_engine.py`) so the raw material+mass text is parsed with `extract_frame_properties` (or equivalent) *before* it gets reduced to a bare material name, and must add an explicit `set_frame_material` call (plus recalc, mirroring `_apply_inferred_component_spec`'s frame branch) somewhere reachable from the DEFINE path in `actions/iterate.py`.

`PVC` density check: refutes engineer-notes hypothesis #"PVC may have no usable physics" — the library **does** have `pvc` with `density_kg_m3=1380.0` (confirmed via `default_library.get_material("pvc")`), so `apply_material_mutation`'s density-ratio path would work if reached. This is irrelevant to the walk's exact symptom (declared grams silently discarded, not a density-ratio substitute), but means the "no physical data" honesty message the draft IC's tests table expects for "material-only pvc, no grams" is **not** the PVC-specific case — PVC always has usable density; that honesty message only applies to a material genuinely absent from the library (there isn't one reachable via `_KNOWN_MATERIALS`/`MATERIAL_ALIASES` that lacks a library entry, as far as traced — worth a quick check in the real IC, not a blocker here).

---

## 3. Completeness / 4/4 / ERF dual analysis

Two **byte-identical duplicated** implementations of block-progress logic exist:

- `orchestrator.py:1932-2003` `_block_progress_status`
- `engineering_readiness.py:364-422` `_block_progress_status` ("pure port... unchanged logic", `engineering_readiness.py:365-369`, kept separate to avoid a circular import)

For `"structure"` (a plain `"component"`-type block per `get_block_type`, `system_architecture_catalog.py:121`), **both** copies use only the generic component-type fallback branch (`orchestrator.py:1989-2003` / `engineering_readiness.py:410-422`): `component_presence_tier(components[key]) != "stub"` for every key in `BLOCK_TO_COMPONENTS["structure"]` (`["frame"]`). This predicate (`project_closure.py:223-238`) is **coarse**: `"stub"` iff `completeness in (None, "low")`, `"present"` otherwise — it does **not** look at `_frame_completeness`'s missing-fields distinction (`aerial.py:242-261`, which separately reports `"high"`/`"medium"`/`"low"`).

Consequence, confirmed by reading both functions together: **a frame with `completeness="medium"` (mass present, material missing — or, after this IC, mass+material present but a required `size_class_inch` missing) already counts as `"present"` for architecture 4/4 today.** This is a pre-existing gap in the codebase (architecture progress and BOM/Continuity already use different bars — noted in `project_closure.py:241-247`'s own docstring on `classify_component`), not something this IC introduces, but it means **the size-required rule cannot be enforced by only changing `_frame_completeness`** — that function's output isn't consulted by architecture progress at all. The draft IC already anticipated this (§2.2: "If `_frame_completeness` stays props-only, the project-level helper must still mark the structure block incomplete") — confirmed necessary, not optional.

**Required change, both copies:** the `"structure"` branch in `_block_progress_status` needs an *additional* AND-condition — `component_presence_tier` says present **AND** (no propeller diameter known, OR a new `frame_size_state` helper says fit/not-required). Because the two functions are duplicated verbatim, this predicate must be added to **both** `orchestrator.py:1989-2003` and `engineering_readiness.py:410-422`, or they silently diverge (architecture display honest, ERF `derive_architecture_progress` still lying, or vice versa) — this is the exact "dual 4/4" risk both the contract and draft IC named. Recommend one small shared pure helper (e.g. `frame_size_ok(project_state) -> bool`, living next to `catalog_bound_motor_lacks_nameplate_watts` in `project_closure.py`) called identically from both copies, rather than inlining the logic twice.

`ERF._structure_evidence` (`engineering_readiness.py:966-973`) is a **separate** signal again: `validated = sim_status == "pass" and _component_present(...)` — same coarse `component_presence_tier` check, so it also would **not** see a missing/misfit size unless a Gap Registry entry blocks `"structure"` (see §5 — gap-blocking is checked *before* evidence fields in `_derive_subsystem_verdict`, `engineering_readiness.py:1082-1119`, so this one is actually covered by the gap addition, not by touching `_structure_evidence` itself).

---

## 4. Invasion check — files Structure A must not write

Confirmed by reading, not by inference:

- **`calculation_engine.py:238-291`** — the only propulsion force-resolution block. Priority order confirmed: (1) `per_motor_max_thrust_n`/`max_force_per_actuator_n` from `current_parameters` (`:239-242`, this is where a catalog-bound thrust or OP-resolved value already lands); (2) torque→force conversion (`:244-262`); (3) aerodynamic inference via `calculate_thrust_from_propeller(propeller_diameter_m, propeller_rpm, Ct, air_density)` (`:281-291`), reading `propeller_diameter_m`/`propeller_diameter_in`/`propeller_rpm` from `current_parameters` only. **Nowhere in this function is `design_properties.components["frame"]` or any `size_class_inch` read.** A first IC cannot call `calculate_thrust_from_propeller` from frame class because frame class never enters this function at all — confirmed, not merely assumed.
- **`src/jarvis/tools/aerodynamics.py:12`** `calculate_thrust_from_propeller` — do not touch (frame class must never become an argument here).
- **`src/jarvis/knowledge/library.py:696` `resolve_operating_point`, `:899` `resolve_operating_point_at_thrust`** — do not touch (Discrete OP / motor-propeller matching; no frame involvement, confirmed no frame field referenced in either signature).
- **`src/jarvis/core/motor_catalog_assist.py:191` `derive_kv_prop_filters`, `:222` `build_motor_catalog_suggestions`** — G22 filters; do not touch (frame size must never become a filter input here — that would be "copy class from prop" inverted into "filter prop by frame", equally forbidden).
- **`GAP-PROP-MOTOR-MISMATCH`** (`engineering_readiness.py:856-878`) confirmed sourced from `compatibility.prop_motor` (via `library.match_motor_propeller`, `electrical_compatibility.py`), `blocks=["propulsion", "catalog"]` — purely a motor↔propeller catalog-pairing gap, structurally unrelated to frame. A new `GAP-FRAME-PROP-SIZE` is a genuinely distinct gap type/blocks set (`structure`, not `propulsion`), no collision.

No helper in any of the above files needs to become frame-aware; a Structure A IC reads `current_parameters["propeller_diameter_in"]` (already a stable public key, confirmed at `calculation_engine.py:268`) purely to decide `prop_diameter_known` — it does not need to touch any of these files to do that.

---

## 5. Gap-registry + incomplete vs ASSEMBLY_READY (the §1 Gate)

Traced `_derive_overall` and `_derive_subsystem_verdict` directly (`engineering_readiness.py:1064-1134`):

```python
def _derive_overall(gaps, subsystems):
    if any(g.severity == "HIGH" for g in gaps):
        return "NOT_ASSEMBLY_READY"
    for readiness in subsystems.values():
        if readiness.verdict == "PASS":
            continue
        if readiness.verdict == "WARNING" and readiness.warning_type in ACCEPTED_WARNING_TYPES:
            continue
        return "NOT_ASSEMBLY_READY"
    return "ASSEMBLY_READY"
```

The `HIGH`-severity check is only a **fast path**. The loop underneath returns `NOT_ASSEMBLY_READY` for **any** subsystem whose verdict isn't `PASS` (or an explicitly accepted `WARNING`) — **regardless of the severity that caused it.** And `_derive_subsystem_verdict` (`:1082-1119`) checks blocking gaps for a subsystem *before* ever consulting that subsystem's evidence fields: any gap (any severity, as long as it's not filtered into the accepted-warning carve-out) with `subsystem_key in g.blocks` forces that subsystem's verdict to `INCOMPLETE` (`:1111`), never `PASS`.

**This proves the Gate hypothesis literally, with two independent routes to the same result:**

1. A dedicated `GAP-FRAME-SIZE-MISSING` / `GAP-FRAME-PROP-SIZE` with `severity="MEDIUM"` and `blocks=["structure"]` (as the draft IC specifies) makes the `"structure"` subsystem verdict `INCOMPLETE` → `_derive_overall`'s loop hits it → `NOT_ASSEMBLY_READY`. **No code change to `_derive_overall` needed**, exactly as frozen.
2. Independently: `_architecture_gaps` (`engineering_readiness.py:526-564`) **already** emits a generic `GAP-ARCH-BLOCK-INCOMPLETE` (severity `MEDIUM`, `blocks=["architecture"]`) whenever `derive_architecture_progress(...)["is_complete"]` is `False`. Once §3's fix makes the `"structure"` block honestly non-`"complete"` when size is required-but-missing, `is_complete` becomes `False` *for that reason alone*, and this pre-existing mechanism **also** flips `_derive_overall` to `NOT_ASSEMBLY_READY` — with **zero new gap type**.

So: **structure-incomplete already yields "not assembly ready" without any `_derive_overall`/HIGH change, and in fact without even a new gap type strictly for the rollup mechanics.** Engineer §4 ("misfit → NOT ASSEMBLY READY") and the draft IC/`_derive_overall` freeze ("MEDIUM, no new HIGH") are simultaneously satisfiable — confirmed, not merely "likely." The Gate is closed: **do not recommend HIGH or a `_derive_overall` change.**

**Why the dedicated gap types are still worth adding** (this is where the draft IC's shape earns its keep): route 2 alone would only ever surface the generic, English, no-context title `"Architecture block incomplete"` / action `"continue_architecture_block"` in the CLI's readiness block (`adapters/cli/main.py:144-157`, which renders `gap['title']` and `next_step.get('action')` verbatim — confirmed, this is the only place `prioritized_gaps` render outside Continuity). That tells the user nothing about *why* — not the D vs class numbers, not that thrust is unaffected, not the LEVEL A caveat Engineer explicitly locked. A dedicated `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` gap is the honest way to put a real title in that same slot.

**Existing `Gap.title` convention is short and English-ish** ("Architecture block incomplete", "{key} not defined", "Motor and propeller catalog pairing incompatible" — `engineering_readiness.py:554, 577, 866`), unlike the draft IC's long Spanish locked-copy paragraphs. There is no long-form prose field on `Gap` (`engineering_readiness.py:59-71`: `gap_id, gap_type, instance_key, title, severity, domain, blocks, depends_on, evidence, recommended_next_step, resolved` — no `message`/`description`). **The draft IC does not say where its locked Spanish copy is meant to render**, and the existing convention for rich Spanish CTA prose in this codebase is `project_continuity.py`'s `next_useful_step`/`next_useful_why` (every prior IC this session — watts-recovery, T1/T1+2, stale-energy-recalc — put its locked user-facing sentence there, never in `Gap.title`). Recommend: keep `Gap.title` short (matching convention, e.g. `"Frame size class missing"` / `"Propeller does not fit frame size class"`), and add the full locked Spanish sentences as a **new Continuity rank** — meaning `src/jarvis/core/project_continuity.py` belongs in the real IC's file list, which the draft IC's §5 table omits entirely.

---

## 6. Draft IC: keep / change / drop

| Item | Verdict | Why |
|---|---|---|
| §1 intent (masa honesta + size required iff D known, unidirectional, LEVEL A) | **Keep** | Matches Engineer ratification ★2-★4 exactly; nothing to reopen. |
| §2.1 "reuse `extract_frame_properties`... persist via `set_frame_material`" | **Keep the destination, change the trigger point** | Confirmed correct end-state, but §2 above shows the raw text never survives to reach any `mutation_engine`-level fix — the parse must happen in `iterate_interactive_session.py` at (or before) the two `_extract_material_from_text` call sites, not solely inside `mutation_engine.py`/`actions/iterate.py`. §5's file table (`mutation_engine.py` and/or `actions/iterate.py` and/or "iterate session") already hedges toward this with "keep the seam you find" — confirmed the seam is the session file, primarily. |
| §2.2 fit table (D known+no class→gap+incomplete; D≤class→FIT PASS level A; D>class→misfit+incomplete; D unknown→mass+material only) | **Keep verbatim** | Matches Engineer §6 exactly; no code contradicts it. |
| §2.2 "implement in the same place that already decides structure block complete... prefer a small shared helper" | **Keep, and make it load-bearing** | Confirmed mandatory, not optional — see §3. Both `_block_progress_status` copies must change. |
| Two gap types, both MEDIUM, not in `_INCOMPATIBLE_VERDICT_SUBSYSTEMS`, no `can_fly=False`, `_derive_overall` unchanged | **Keep** | All confirmed correct and sufficient in §5 — MEDIUM already flips `_derive_overall` via the generic subsystem-verdict path; no HIGH, no rollup edit needed. |
| Locked gap copy text | **Change destination** | Keep the sentences; do not put them verbatim in `Gap.title` (breaks existing short/English convention) — route the long form through a new Continuity rank instead, short honest title on the Gap itself. See §5. |
| §5 file table | **Incomplete — add `project_continuity.py` and `iterate_interactive_session.py`; keep `component_writers.py`, `engineering_readiness.py`; `orchestrator.py` needed for real (both `_block_progress_status` AND `_component_prompt_for_first_missing`), not "only if"** | See §3, §5, §7. |
| §3 test table referencing `tests/test_fase2_uxc.py` | **Drop — file does not exist.** | Confirmed via `ls tests/`. The closest existing homes for a frame-completeness-without-prop regression are `tests/test_frame_component.py` and `tests/test_g10_materials_frame.py`. |
| "+0.25 slack" (engineer-notes item 5, not actually in the draft IC's locked table but flagged as a hypothesis) | **Drop, no slack found needed** | The draft IC itself already locks `D <= size_class_inch` (no slack) in its fit table (§2.2) and in Acceptance (§6: "7 in prop on 5 in class → misfit"). No code or test anywhere assumes a margin. Nothing to justify. |
| "PVC may have no usable physics" (engineer-notes item, draft IC §3 "if library has no PVC density, today's honesty message still OK") | **Refuted for PVC specifically** | `default_library.get_material("pvc")` returns `density_kg_m3=1380.0` — PVC has real density. The honesty-message test case is real (some material could lack a library entry) but PVC is not that material; the test should either use a genuinely-absent material name or be reframed as "material name not recognized at all," not "pvc lacks density." |

---

## 7. Recommended first IC: files, tests, non-goals (shape B)

**Files** (supersedes draft IC §5):

| File | Role |
|---|---|
| `src/jarvis/core/iterate_interactive_session.py` | Primary fix: at the two `_extract_material_from_text` call sites (`:294-296`, `:409-419`), parse the **full** raw text (the same string currently fed to `_extract_material_from_text`) with `extract_frame_properties` (or an equivalent that also returns `size_class_inch` once §2.2 lands) before truncating to material-name-only; carry the parsed mass/size forward on the draft (e.g. into `component_patch` or a new draft field) so `actions/iterate.py` can route it. |
| `src/jarvis/actions/iterate.py` | `_run_declarative_iteration`: when the material draft carries a parsed mass (and/or size), call `set_frame_material` directly (mirroring `_apply_inferred_component_spec`'s frame branch, `orchestrator.py:2273-2307`) and recalc, instead of relying on `_apply_design_property_mutation`'s string-only merge. |
| `src/jarvis/core/mutation_engine.py` | `apply_material_definition` — confirm/keep it dropping mass is fine **only if** the session layer no longer hands it truncated text as the sole payload; if the fix instead keeps `draft.value` as the full raw string and does the parse here, this is the alternate location — investigator's preference is the session layer (single normalized-text access point, avoids re-parsing an already-truncated string), but either is viable; do not do both. |
| `src/jarvis/core/component_writers.py` | Extend `set_frame_material` with optional `size_class_inch: float | None = None` (draft IC §2.2, unchanged). |
| `src/jarvis/domains/aerial.py` | Extend `extract_frame_properties` with the inches regex (`5"` / `5 in` / `5 inch` / `5 pulgadas`), no mm conversion, no copy-from-prop (draft IC §2.2, unchanged). |
| `src/jarvis/core/project_closure.py` | New small shared predicate (e.g. `frame_size_ok(project_state) -> bool` or a richer `frame_size_state(...)` returning not-required/missing/fit/misfit) — single source both `_block_progress_status` copies and the new gap builder read, per §3/§5. |
| `src/jarvis/core/orchestrator.py` | `_block_progress_status` (`:1932-2003`) — add the size-required AND-condition to the `"structure"` branch via the new shared predicate. Also `_component_prompt_for_first_missing`/`_COMPONENT_PROMPTS` (`:2267-2271`, `acquisition_target.py:117`) — mention pulgadas when `prop_diameter_known` (draft IC §2.2, confirmed reachable only via a small conditional here, not a dict edit). |
| `src/jarvis/core/engineering_readiness.py` | `_block_progress_status` (`:364-422`) — same AND-condition, same shared predicate, kept in sync with the orchestrator copy. New gap builder(s) for `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` (MEDIUM, `blocks=["structure"]` / `["structure","catalog"]`), registered in `build_engineering_readiness`'s `gaps +=` sequence (`:1159-1170`), short titles per §6. |
| `src/jarvis/core/project_continuity.py` | New rank (after the existing catalog/energy ranks, before the generic `sim_status == "pass"` fallback — exact slot to be decided against the live rank order at implementation time) carrying the full locked Spanish sentences for missing-class and misfit, LEVEL A phrasing, never "verificado." |
| `tests/test_structure_a.py` | New — mass-write regression (both leak call sites, not just one), acquisition regression, fit table (all four states), thrust-identical assertion. |
| `tests/test_frame_component.py` / `tests/test_g10_materials_frame.py` | Frame completeness without prop still mass+material only (replaces the draft IC's reference to the non-existent `test_fase2_uxc.py`). |
| `tests/test_engineering_readiness_gaps.py` | New MEDIUM gap does not flip `_derive_overall` to `NOT_ASSEMBLY_READY` *by itself beyond the honest state* — i.e. assert severity MEDIUM, assert it's absent from `_INCOMPATIBLE_CLASS_GAP_TYPES`/`_INCOMPATIBLE_VERDICT_SUBSYSTEMS`, and (per §5's proof) explicitly assert that a project with the gap present *does* read `NOT_ASSEMBLY_READY` overall — that is the intended, correct behavior, not a regression to guard against. |
| `docs/IMPLEMENTATION_TASKS.md`, `.jes/state/engineering_state.json` | Sync after report, as usual. |

**Non-goals** (unchanged from draft IC §4, all confirmed untouched by the plan above): CAD/FEM/STL/topology; wheelbase/arm-length/mm→inch conversion; inventing any density; control/sensor/ESC catalog; DSE grids/scoring; Option B/Block PARCIAL/Tier 3; failing sim on fit; new domain module; `_derive_overall` code change (confirmed unnecessary, §5).

---

## 8. Frozen honored

No `src/` edited. No new tests written. No CAD/FEM/STL/topology proposed. No density invented (PVC's real density was read, not invented, to refute a hypothesis). No `size_class_inch` routed into `CalculationEngine`/thrust/power/RPM/Ct/autonomy — confirmed by direct trace of `calculation_engine.py:238-291`, no code in the recommendation touches that function. No `Ct` invented from pitch/blades/bullnose. No copying `size_class_inch` from the propeller — recommendation explicitly keeps them independently declared. No "STRUCTURAL FIT: VERIFIED" claim proposed — recommendation is LEVEL A/CLASS-BASED framing throughout, routed through Continuity same as every other honest-uncertainty sentence in this codebase. No HIGH gap or `_derive_overall` change recommended (§5 proves it's unnecessary, not just undesired). No control/sensors/ESC catalog touched. No Option B/`_derive_overall`/Block PARCIAL touched. No DSE scoring/`EXPLORATION_GRIDS` touched. No G24-B/Tier 3/Conversation Engine touched. `workspace/` not mutated — all evidence gathered by reading `src/`/`tests/`/`docs/` and running read-only Python against `default_library` in-process. The draft IC was not implemented.
