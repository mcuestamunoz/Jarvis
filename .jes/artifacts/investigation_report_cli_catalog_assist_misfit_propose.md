# Investigation Report — CLI catalog-assist + misfit propose

**IC/Contract:** `investigation_contract_cli_catalog_assist_misfit_propose.md` (★1–★5 ratified)
**Investigator:** Claude Code · **Status:** investigation only, no `src/`/test files touched.

---

## 0. Fixture confirmation

`workspace/inspección-autonomía-mínima-5-minutos-eb61a0ed6fe2/state.json` exists and matches the chat transcript:

- `design_properties.components`: `motors.catalog_ref={family:motor, sku:sunnysky_r2305_2500}` (completeness=high), `propellers.catalog_ref={family:propeller, sku:gf_5045x3}`, `battery.catalog_ref={family:battery, sku:lipo_6s_10000mah}`; `esc`/`frame`/`flight_controller` = null.
- `current_parameters`: `motor_count=2`, `motor_power_w=220.0`, `motor_kv_rating=2500.0`, `propeller_diameter_in=5.0`, `battery_capacity_wh=222.0`, `structure_mass_override_kg=0.65`. `propulsion_resolution` JSON: `resolution_type="legacy_estimate"`, `source_type="estimated"`, `thrust_n=7.5`.
- `latest_results.simulation`: `status="fail"`, `available_thrust_n=15.0`, `required_thrust_n=30.0893`, `per_motor_load_ratio=2.006`, `safety_margin_ratio=0.4985`, `autonomy_min=30.2727`.

All numeric evidence below is computed against this exact state, not a synthetic one, unless noted.

---

## 1. Gate A — Walk fixture vs Combo A offer

`library.find_motors_for_requirements` (`src/jarvis/knowledge/library.py:311-336`) filters candidates via `_motor_covers_requirements` (`:69-87`) — rejects only if **both** the point `thrust_n` and the `design_space.max_thrust_n` ceiling miss the target — then sorts by `(is_generic, abs(thrust_n - min_thrust_n), name)` (`:329-336`). **Closest point-thrust wins; there is no headroom/margin heuristic.**

Library data (`library/motores/_datos.json`):

| SKU | `thrust_n` | `design_space` | KV | `max_watts` | ops points on `gf_5045x3` |
|---|---|---|---|---|---|
| `sunnysky_r2305_2500` | 7.5 | 6.0–9.5 | 2300–2700 | 220 | — |
| `sunnysky_r2205_2500` | 12.5525 | 10.0–15.5 | 2300–2700 | 756 | 10 `manufacturer_test` |

Live-called `find_motors_for_requirements(min_thrust_n=4.7, kv=None, prop_inch=5.0)` — reproducing the D8 create-time state (~4.7 N/motor, no battery bound, no KV hint yet): **rank #1 = `sunnysky_r2305_2500`** (`|7.5−4.7|=2.8`). `sunnysky_r2205_2500` ranks **#8 of 9** with the prop filter, **#11 of 22** unfiltered — never top-5 at create time.

**Root cause:** the D8 sort optimizes for closest-fit-to-the-current-estimate, not headroom for a design that later gets heavier (6S battery swap mid-walk, PVC `structure_mass_override_kg=0.65`). A motor picked against the lightest early estimate is systematically undersized once the design grows — this is a structural misfit generator, not a data-curation gap, and not something a bigger catalog fixes by itself.

**Combo A reachability:** confirmed **not reachable from the numbered pick UI** at any realistic early-estimate thrust value (empirically verified above). Only reachable by typing the exact SKU string verbatim, or via test/programmatic bind. Recommendation §5 does **not** propose "tell the user to type the SKU."

---

## 2. Gate B — Post-bind "ayúdame a elegir" (the stuck loop)

Two independent short-circuits share one blind spot: **any `catalog_ref` at all reads as "done," never re-checked against current feasibility.**

1. `orchestrator.py:1463-1526` `_try_start_assisted_motor_help` (IDLE fresh entry). Line 1482-1483:
   ```python
   if catalog_bound_motor_covers_power_w(project_state.design_properties):
       return None
   ```
   `catalog_bound_motor_covers_power_w` (`project_closure.py:45-72`) is a pure identity check (`ref is not None and family == "motor"`) — it never looks at `latest_results.simulation`, thrust sufficiency, or the underspec evidence fact described below. On the fixture this returns `True` unconditionally, so the function bails before reaching its own propulsion-gap branch (`:1485-1491`, which would call `offer_catalog_help()`). Falls through to propeller/battery help (both also bound → `None`). `assist` stays `None`.

2. `orchestrator.py:2867-2984` `_handle_component_description`, gate at line **2936**:
   ```python
   motors_want_help = "motors" in expected_keys and _wants_catalog_help(gate_components.get("motors"))
   ```
   Same blind predicate (`catalog_ref is None`, in effect). `motors_want_help=False` on the fixture → `_offer_component_motor_catalog` (`:2561-2611`, which **does** call the real G22 search) is never reached.

**Live repro:** `orch.handle_user_text("ayúdame a elegir", llm)` on the untouched fixture, called twice in a row, returns **the exact same text both times** — a genuine stuck loop: the CTA tells the user to say the help phrase, and saying it does nothing, because gate #2 above still reads "catalog_ref is not None" as "no help needed."

**The detection this needs already exists and is already computed every turn.** `engineering_readiness.resolve_motor_catalog_surface` (`:200-300`, called from `_motor_catalog_gaps` at `:431`) independently evaluates the same bound motor against the same requirements and produces, on this fixture:

```
gap_evidence_fact = "bound_sku_underspec:sunnysky_r2305_2500"
catalog_matches   = [{sunnysky_r2205_2500, thrust_n=12.55, max_thrust_n=15.5, kv=2500, compatible_prop_inch=(5,)}]
recommended_next_step = RecommendedNextStep(action="list_motors", params={})
```

Neither short-circuit above ever consults `gap_evidence_fact` or `recommended_next_step`. **The fix is wiring, not new detection or new search:** both gates need to also check `gap_evidence_fact == "bound_sku_underspec:*"` (or equivalent) and, when true, call the same `build_motor_catalog_suggestions`/`_offer_component_motor_catalog` that already exists and is already exercised elsewhere in the codebase (Gate C confirms it returns the identical, already-formatted candidate).

**Test-safety check:** `tests/test_g21_g22_catalog_bind_ux.py::test_g21_idle_help_choose_noop_when_catalog_ref_set` (`:175-204`) does **not** assert a blanket "bound motor → help-choose is always a noop." Its own docstring documents the fallback chain legitimately advancing to the *next unbound component* when motor is bound but propeller isn't — the guard is specifically against a **false motor re-bind**, not against ever reopening a list. On this fixture motor **and** propeller **and** battery are all bound, so the fallback chain has nowhere left to advance — a narrower, distinct gap. A Tier 1 fix adds a new branch ("everything bound but the bound motor is thrust-underspec") without touching or weakening this test's actual assertion.

### Gate E Path 2 — Battery: same bug shape, different fix shape

Battery has the same-shaped short-circuits (`_try_start_assisted_battery_help` `:1561-1588`, `battery_wants_help` gate `:2972-2980`, identical `_wants_catalog_help` predicate) — structurally the same blind spot exists.

**But no equivalent detection surface exists for battery.** `grep -rn "bound_sku_underspec\|resolve_.*catalog_surface" src/` finds these terms **only** on the motor path. The only battery-misfit gap in readiness is `_battery_discharge_exceeded_gap` (`:782`, ERF-2 discharge-**current** check) — not a capacity/energy-underspec check. `build_battery_catalog_suggestions` (`battery_catalog_assist.py:62-85`) exists as a search entry point but is **unfiltered** (`project_state` accepted-but-unused, explicitly deferred per its own docstring).

**Conclusion:** motor's fix is "wire an existing, already-computed, already-filtered detection into two call sites." Battery's equivalent would require *inventing* new underspec detection plus real filtering on `build_battery_catalog_suggestions` — new logic, not a wiring fix, and out of scope for a first IC restricted to existing authorities (C4/C5). **Recommend as a named non-goal**, not folded into the first IC's file list. Moot on this exact fixture anyway — the battery is not the misfit component here.

---

## 3. Gate C — G22 filters on the failed walk combo

`build_motor_catalog_suggestions` (`motor_catalog_assist.py:219-253`) is the real production call site: `min_thrust = derive_physical_requirements(project_state)["thrust_per_motor_needed_n"]` (`project_closure.py:101-124`, `required_thrust_n / motor_count`); `kv_hint, prop_inch = derive_kv_prop_filters(project_state)` (`motor_catalog_assist.py:190-217`, reads the bound motor's `kv_rating` and `current_parameters["propeller_diameter_in"]`). Called from `_offer_component_motor_catalog` (`orchestrator.py:2561-2611`) with the live `project_state`, no override args.

Live-called it on the walk's real state:

| Input | Value |
|---|---|
| `thrust_per_motor_needed_n` | 15.04465 (`30.0893 / 2`) |
| `kv_hint` | 2500 |
| `prop_inch` | 5.0 |

**T1 result (no relax) — NOT empty, but insufficient:**

| Candidate | `thrust_n` | `max_thrust_n` | `max_watts` | 2×thrust_n | vs `required_thrust_n=30.0893` |
|---|---|---|---|---|---|
| `sunnysky_r2205_2500` | 12.5525 | 15.5 | 756 | 25.105 N | **short** |

It passes `_motor_covers_requirements` because `design_space.max_thrust_n=15.5 ≥ 15.04465` — even though the point `thrust_n=12.5525 < 15.04465`. But `calculations`/`simulation`'s `available_total_thrust_n` is computed from the **point** `thrust_n`, not `design_space.max_thrust_n` — so this candidate would cut `per_motor_load_ratio` from `2.006` to `~1.20` (real, meaningful progress) but **would not reach PASS**.

**Filter-relaxation trials** (same `find_motors_for_requirements`, called directly with relaxed args — investigation math, not a new function):

| Relax | Best/new candidate | `thrust_n` | 2×thrust_n vs 30.09N | Prop-compatible with bound `gf_5045x3`? |
|---|---|---|---|---|
| Drop KV only (`kv=None, prop_inch=5.0`) | `emax_eco_ii_2207_1700` | 14.5 | 29.0 N — still short | **Yes** (`compatible_prop_inch=(6,7)`) |
| Drop prop only (`kv=2500, prop_inch=None`) | *(no new candidate)* | — | — | — |
| Drop both (thrust-only, `min_thrust_n=15.04465`) | `sunnysky_v4006_740` | 16.0 | **32.0 N — PASS-capable** | **No** — `compatible_prop_inch=(12,13)`, confirmed via `default_library.match_motor_propeller("sunnysky_v4006_740", "gf_5045x3") == False` |

**This is the load-bearing finding for the tier decision:** the only candidate in this library that would actually restore feasibility on this fixture (`sunnysky_v4006_740`) is **propeller-incompatible** with the already-bound `gf_5045x3` — a genuine frankenstein pairing, not a hypothetical one. The KV-only relax stays prop-compatible but still doesn't reach PASS (29.0N < 30.09N). Dropping KV also risks a voltage/KV mismatch against the walk's 6S pack (2500KV target vs a 1700KV candidate) — a second, independent frankenstein axis beyond propeller fit.

**Classification: on this fixture, T1 is a non-empty, useful-but-insufficient list. It is not empty and not useless** — it nearly halves the load-ratio gap with zero filter relax and zero new risk. Filter relaxation (T1+2) is evidenced but does not close the gap cleanly here: KV-drop-only stays safe but insufficient; full relax reaches feasibility only by pairing an incompatible propeller.

---

## 4. Gate D — Continuity, SuggestionEngine, DSE catalog keys

- **Continuity rank collision:** `project_continuity.py:179-182` (rank 2: sim warning/fail) matches first on this fixture (`sim_status="fail"`) and returns before the catalog-gap branch (`:183-197`, rank 3) is ever evaluated — a plain `elif` chain, first match wins, exactly as the function's own docstring orders it (`:35-42`). **This is documented, intentional priority, not an oversight.** Partial mitigation already exists: the catalog gap is not fully hidden — it still appears in the `evidence` list (`:162-163`, `f"Catálogo: {motor_catalog_gap}"`) even though `next_useful_step` omits it.
- **SuggestionEngine** (`suggestion_engine.py:13-87`): on this fixture emits exactly `reduce_weight` (`:58-65`) and `increase_thrust` (`:78-85`). The `Suggestion` schema has `type`/`reason`/`expected_effect`/`priority` fields only — **no SKU field exists at all**, structurally, not just unused this call.
- **`_CATALOG_MOTOR_GOAL_KEYS`** (`design_explorer.py:210-213`) = `frozenset({"aumentar_payload", "mejorar_estabilidad"})`. There is no `"aumentar_empuje"` goal key anywhere in the system — the only goal keys that exist are `mejorar_autonomia`, `aumentar_payload`, `mejorar_estabilidad`, `reducir_masa`, `reducir_payload` (`goal_planner.py`).
- **FN-022 correction:** the contract's framing ("does the empuje→mejorar_estabilidad remap lose catalog motors?") does not hold up. `goal_planner.py:144-160`'s `mejorar_estabilidad` keyword table explicitly includes `"empuje"`, `"aumentar empuje"`, `"thrust"`, etc. — a deliberate design choice (comment `:149-153`: this goal's strategies already lead with thrust/margin levers). **`mejorar_estabilidad` IS a member of `_CATALOG_MOTOR_GOAL_KEYS`** — a user's thrust-fix intent *does* reach a goal that gets DSE catalog-motor candidates. FN-022 is not a leak.
- **Same G22, no DSE-local relaxation:** `design_explorer.py:252-289` `_build_catalog_motor_candidates_for_goal` calls `build_motor_catalog_suggestions(project_state, limit=5)` directly (`:274`) — the identical G22 authority. Since Gate C found G22 non-empty (1 candidate) on this fixture, DSE's `mejorar_estabilidad` catalog branch would surface that same single candidate, for the identical reason — no additional route, no additional risk.

### Tier 3 absorption — PARTIAL

DSE already has real goal-routing (`_CATALOG_MOTOR_GOAL_KEYS`) and real apply-by-index machinery (`orchestrator.py:3667-3719`, `_handle_apply_exploration`, "G24-1", 1-based index into `exploration.viable`) — but for **one component family at a time**. That combination could plausibly extend, without a new subsystem, to single-family "propose + apply by index" reoffers for motor, propeller, or battery independently (T1/T2-shaped work). Genuine Tier 3 — jointly searching motor+propeller+battery so the offered combo is mutually compatible — is explicitly **not** what DSE does today: `design_explorer.py:643` carries the comment *"Guard: mixed deltas not supported yet (DA2 keeps them separate)"*, and every candidate built in `explore()` carries exactly one `params_delta` **or** one single-key `components_delta` — never both, never two component keys at once. Absorbing joint search later requires either extending DSE's candidate model to mixed multi-component deltas (defensible — reuses the same evaluate/score loop) or an outer cross-product/compatibility-filter loop across single-family candidate sets (risks becoming exactly the "second search/ranking function" C4 forbids). **Not free — flag for whoever scopes a future Tier-3 IC.**

---

## 5. Gate G — First-IC recommendation

### Recommendation: **T1**

**Justification:** Gate B identified a genuine, reproducible bug — a stuck loop where the CLI's own CTA ("ayúdame a elegir") does nothing, twice, because two short-circuits treat "any `catalog_ref` bound" as "no help needed," blind to the underspec case. The fix requires **zero new detection and zero new search**: `resolve_motor_catalog_surface`/`gap_evidence_fact`/`recommended_next_step` are already computed every turn (`engineering_readiness.py`), and `build_motor_catalog_suggestions` already returns the correct, already-formatted single candidate (Gate C). Gate C additionally shows this candidate is **useful, not useless** (load ratio 2.006→~1.20) even though it doesn't reach PASS — so T1 alone converts "silent stuck loop" into an honest, evidenced answer, with zero filter-relax risk.

T1+2 is **not** justified as the *first* IC on this fixture: Gate C's T1 list is not empty/useless (the contract's own trigger condition for T1+2), and the one relaxation that *would* reach feasibility (drop both KV+prop) surfaces a confirmed propeller-incompatible motor (`sunnysky_v4006_740`) — introducing exactly the frankenstein risk the contract asks to guard against. Recommend T1+2 as a closely-following **second** IC, evidenced but deferred, carrying the frankenstein warning from day one (§7 below).

### Future-IC file list for T1 (not a patch — for whoever writes the IC)

| File | Change shape |
|---|---|
| `src/jarvis/core/orchestrator.py` | `_try_start_assisted_motor_help` (`:1463-1526`) and the `motors_want_help` gate in `_handle_component_description` (`:2936`) — add a check against `gap_evidence_fact`/`bound_sku_underspec:*` (or equivalent readiness signal) alongside the existing `catalog_ref is None` check; on match, route to the existing `_offer_component_motor_catalog` (`:2561-2611`) instead of returning `None`. |
| `src/jarvis/core/engineering_readiness.py` | Possibly expose `gap_evidence_fact`/`resolve_motor_catalog_surface`'s underspec verdict in a form the orchestrator gates can cheaply consult (may already be sufficient as-is via `readiness` — decide in the IC, don't assume a new field is needed). |
| `src/jarvis/core/project_continuity.py` | Optional, smaller: surface the already-present `evidence` catalog line more prominently, or leave rank order as-is (Gate D found this intentional, not broken) — IC author's call, not mandatory for T1's core fix. |
| `tests/test_g21_g22_catalog_bind_ux.py` | Extend, do not weaken — add a case for "motor+propeller+battery all bound, motor thrust-underspec" distinct from the existing false-re-bind guard (`test_g21_idle_help_choose_noop_when_catalog_ref_set`, unchanged). |
| `tests/test_project_continuity.py`, `tests/test_g9a_catalog_ref_gap.py` | Regression-check only — confirm unaffected. |

**Forbidden in this IC (per contract §2/§4):** filter relaxation of any kind, joint combo search, unlocking G24-B, ESC catalog work, `_derive_overall`/Block Closure changes.

---

## 6. Hygiene items — in or out of the first IC

### Watts CTA (Gate E) — **in scope, but needs a predicate split, not copy-only**

`catalog_bound_motor_covers_power_w` (`project_closure.py:45-72`) is a pure identity check (`ref is not None and family == "motor"`) — it never inspects `max_watts`, despite its name and its reuse as `_catalog_bound_motor_lacks_watts` (`reasoning_layer.py:442-448`, a bare alias). `sunnysky_r2305_2500` has a real `max_watts=220.0` (confirmed live) — yet the CTA "este motor de catálogo no declara vatios" fires whenever `missing_energy_parameters` is true and the motor is catalog-bound **at all** (`reasoning_layer.py:108-117`), regardless of whether that SKU actually declares watts. One predicate is answering a different question than its caller believes.

**Recommendation:** keep `catalog_bound_motor_covers_power_w` unchanged for its original job (architecture-progress gating, Block Closure) — that behavior is correct even for a genuinely watts-less SKU. Give the CTA's copy its own check against the bound SKU's actual `max_watts` (e.g. `default_library.get_motor(sku).max_watts is None`). Smallest file list: `reasoning_layer.py` (new/separate predicate), optionally `project_closure.py` if a shared helper is preferred. **Include in the first IC if the IC author judges the seam small enough** — it shares the orchestrator/reasoning_layer neighborhood with the T1 fix but is logically independent; not a hard requirement.

### GAP title (Gate F) — **in scope, cheap, recommend title-only + wire the fix (not ID rename)**

`_motor_catalog_gaps` (`engineering_readiness.py:431-478`) emits **one fixed title**, `"Motor SKU unresolved"` under gap type `GAP-MOTOR-CATALOG-UNRESOLVED`, for three distinct evidence shapes: nothing bound, `bound_sku_underspec:{sku}` (this walk's case), and `bound_sku_missing:{sku}`. Renaming the gap-type ID itself touches 2 source files and **6 test files** (`test_engineering_readiness_continuity.py`, `test_engineering_readiness_gaps.py`, `test_engineering_readiness_subsystems.py`, `test_g21_g22_catalog_bind_ux.py`, `test_g9a_catalog_ref_gap.py`, `test_impl_c_catalog_aware_dse.py`, `test_impl_c_catalog_dse_thrust_bridge.py`) — non-trivial churn for a copy fix.

**Recommendation: leave the ID alone, vary the title/copy conditionally on `gap_evidence_fact`'s prefix** (`engineering_readiness.py:467-470`, cheap). The gap already computes `recommended_next_step=RecommendedNextStep(action="list_motors", params={})` and it already reaches the CLI as a bare token (`cli/main.py:156-157`, `next: {action}`) — but nothing *consults* it as an actionable signal; that's the same wiring gap as Gate B's fix, not a separate problem. **Include in the first IC** — same neighborhood, same root cause (a computed signal nobody reads), small diff.

---

## 7. Frankenstein risk mechanism (for the deferred T1+2 IC)

`_prop_motor` (`electrical_compatibility.py:294-308`) calls `default_library.match_motor_propeller(motor_sku, prop_sku)` (`library.py:610-627`) — deterministic, already exists: explicit `compatible_prop_ids` membership, else `compatible_prop_inch` within tolerance of the propeller's diameter, else `False`. **No new function needed** — this is the exact seam a future T1+2 IC calls to flag or reject a relaxed candidate.

Confirmed live against the walk's bound `gf_5045x3` (5.0"):

- **Compatible (5" family):** `brotherhobby_avenger_2500`, `brotherhobby_returner_r5_2700`, `emax_eco_ii_2207_1700`, `emax_rs2205_2300`, `emax_rs2205s_2300`, `hobbywing_xrotor_2207_2450`, `sunnysky_r2205_2500`, `sunnysky_r2305_2500`, `t-motor_f80_2400`.
- **Incompatible (larger-prop motors):** `sunnysky_v4006_740` (the one PASS-capable thrust-only candidate — `compatible_prop_inch=(12,13)`), `t-motor_mn3110_700` (`(12,13)`), `t-motor_antigravity_mn4006_380` (`(15,16)`), `t-motor_u8_170` (`(22,24)`), `t-motor_mn5008_340` (`(17,18)`), `emax_mt2216_810` (`(10,11)`), `generic_700kv` (`(12,)`).

**Recommendation shape for the deferred T1+2 IC** (per contract §3.7, do not merge into T1): any relaxed candidate that fails `match_motor_propeller(candidate_sku, bound_prop_sku)` must either (a) come with explicit CLI copy that the propeller may need re-binding, or (b) the propeller must be offered in the same turn — and (b) is Tier 2+/3 per the contract, not mergeable into T1+2's scope.

---

## 8. Tests / probe sketch for the future T1 IC

Existing tests confirmed and what they pin:

- `tests/test_g21_g22_catalog_bind_ux.py` — `test_g21_component_wizard_pick_verified_motor_without_nominal_watts` (`:97`), `test_g21_idle_help_choose_noop_when_catalog_ref_set` (`:175`, narrow false-re-bind guard, see §2), `test_idle_help_choose_catalog_bound_without_watts_opens_propellers_not_power_w` (`:207`).
- `tests/test_assisted_acquisition.py` — `test_help_choose_phrases` (`:28`), `test_motor_power_question_has_three_paths_not_raw_key` (`:36`).
- `tests/test_project_continuity.py` — `test_continuity_catalog_gap_beats_optimization_suggestion` (`:98`), `test_continuity_incomplete_bom_without_catalog_gap` (`:129`).
- `tests/test_design_explorer.py`, `tests/test_g24_apply_by_index.py` (`test_apply_by_index_preserves_catalog_ref_when_catalog_not_at_one` `:82`, `test_bound_motor_aplica_la_mejor_clears_catalog_ref` `:160`), `tests/test_g24_viable_selection.py`.

**Probe sketch (prose, not code):** architecture 4/4 project; motor catalog-bound to `sunnysky_r2305_2500`, propeller catalog-bound to `gf_5045x3`, battery bound to a heavy 6S pack (`lipo_6s_10000mah`) — mirrors the walk exactly and reproduces `sim.status="fail"` after `calcular`+`simular`. Send `"ayúdame a elegir"` through the real orchestrator (`_RefuseLLM` stub, no `workspace/` mutation). If T1 is implemented: assert the result is **not** a bare `estado`/`project_status` reprint — either `session.mode == DEFINE_MISSING_PARAMETERS` with `pending_missing_params == ["motors"]`, or the message names a concrete next step (contains `"list_motors"` or a candidate SKU like `sunnysky_r2205_2500`). Assert `derive_prop_energy_block_closure`'s rollup output and `engineering_readiness._derive_overall` are byte-for-byte unaffected by the fix (this is a CLI-routing change, not a readiness/closure change).

---

## 9. Explicit non-goals confirmed respected in this investigation

No `src/` or test file was edited. No SKU/watts/ESC η/hover-minute value was invented — every number cited above came from either the live `state.json`, the live library JSON, or a live (read-only) function call against the real code, quoted verbatim. `derive_prop_energy_block_closure`, N1's discharge-copy gate, `_derive_overall`, and G24-B `_score_candidate` were read for context only and are recommended **unchanged** by every gate above.

## 10. Sign-off

**No `src/` or test files touched.** All findings above were produced via read-only inspection and throwaway, non-persisted Python snippets (`python3 -c "..."` against the real library/orchestrator/state modules); nothing was written to `workspace/`, `src/`, or `tests/`. Ready for Cursor review.
