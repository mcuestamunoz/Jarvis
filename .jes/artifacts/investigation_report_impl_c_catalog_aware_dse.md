# Investigation Report — Impl C Catalog-Aware DSE

**Contract:** [`investigation_contract_impl_c_catalog_aware_dse.md`](investigation_contract_impl_c_catalog_aware_dse.md)
**Checkpoint base:** `checkpoint-g21-g23` (`8dcc151`) — confirmed current HEAD.
**Investigator:** Claude Code
**Status:** Complete. No `src/` changes, no new tests (investigation only, per contract §2).

---

## 1. Executive summary

DSE candidates today come from two sources: an abstract `params_delta` grid (scales numbers directly, no component identity) and a synthetic `components_delta` grid (`COMPONENT_VARIATION_RULES` — invented property values, `catalog_ref=None` by construction). Neither ever proposes a real catalog SKU, so `aplica la mejor` always either strips or never sets `catalog_ref`.

The good news: the plumbing to fix this **already exists and needs no new machinery**. `apply_components_delta`'s writers (`set_motor_component` etc.) persist whatever `ComponentSpec` a candidate hands them verbatim — including `catalog_ref` — and `sync_motors_component_from_params`/`invalidate_diverged_catalog_refs` (G5) already leave `catalog_ref` untouched unless a real physical divergence is detected. A catalog-native candidate built via `bind_motor_from_catalog(suggestion, base=existing_spec)` and carried in `components_delta["motors"]` survives the entire existing apply pipeline with **zero changes** to `orchestrator._handle_apply_exploration`, `component_writers.py`, or G5's sync/invalidate order.

What's missing is only candidate **generation**: a catalog branch in `DesignExplorer.explore()` that, for goals where a motor SKU is the natural lever (`aumentar_payload`, `mejorar_estabilidad`), calls the exact same ranked search acquisition already uses (`motor_catalog_assist.build_motor_catalog_suggestions` — G22's single authority) instead of `COMPONENT_VARIATION_RULES`' invented values, and binds each result via `bind_motor_from_catalog` before scoring.

**Recommended option:** Option A for candidate shape (populate `components_delta` with real `bind_motor_from_catalog` output — reuses the existing apply path unchanged) + a "reuse acquisition's ranked search" grid strategy (not a new `CATALOG_EXPLORATION_RULES` table of invented values — call `build_motor_catalog_suggestions` directly). Battery catalog candidates for `mejorar_autonomia` are feasible with the identical pattern (`bind_battery_from_catalog`) but recommended as a separate, optional slice (C3) since no battery search/ranking surface parallel to G22 exists yet outside `find_batteries()`'s plain filters. `reducir_payload`/`reducir_masa` have no catalog dimension today (frame has no catalog) and should stay on abstract grids entirely. G9-A's Option C (`bound_sku_status` typed field) is **not needed** — message-level honesty (already how G9-A works) is sufficient for DSE too.

---

## 2. Current pipeline audit

### 2.1 Sequence (explore → apply → persist)

```text
User: "optimiza para aumentar payload" / "explora opciones"
  → IntentResolver.resolve_explore_goal / resolve_explore_goal_with_handoff (FN-024/G3)
  → orchestrator._handle_explore(goal_key, user_input, llm_interface)
      - loads project_state (read-only)
      - resolves goal_key (explicit text > active HandoffContext, FN-024/G3 precedence)
      - DesignExplorer.explore(project_state, goal_key)
          - normalized_state = apply_components_delta(project_state, {})   # baseline re-derivation
          - baseline_calc/sim/score
          - for delta in EXPLORATION_GRIDS[goal_key]:
                apply _apply_delta → calc/sim/score → ExplorationCandidate(params_delta=delta)
          - for comp_delta in _build_component_candidates_for_goal(goal_key):
                apply_components_delta(normalized_state, comp_delta) → calc/sim/score
                → ExplorationCandidate(components_delta=comp_delta)
          - viable = [c for c in candidates if c.simulation.can_fly], sorted by score desc, top 5
      - session.last_exploration_result = exploration   (in-memory only, no disk write)
      - handoff_context.dse_capability = "consumed" (FN-024, only when bound from a handoff)
      - returns numbered candidate list message
User: "aplica la mejor"
  → orchestrator._handle_apply_exploration()
      - best = exploration.viable[0]
      - if best.components_delta: updated_project = apply_components_delta(project_state, best.components_delta)
        else: canonical_params = _apply_delta(base_params, best.params_delta)
      - invalidate_diverged_catalog_refs(components, canonical_params)   # G5 order lock: FIRST
      - sync_motors_component_from_params(components, canonical_params)  # SECOND
      - calculate + simulate + record_action + save_state + render_views
```

**Nothing in `explore()` touches disk or mutates `project_state`** — confirmed by the docstring's own guarantee and by `apply_components_delta`/`_apply_delta` both being pure functions operating on copies. This guarantee is not at risk from adding a catalog branch, since `bind_motor_from_catalog` and `ComponentLibrary.find_*`/`get_*` are equally pure (library reads are cached in-memory, never written to).

### 2.2 Goal → current candidate source table

| goal_key | `EXPLORATION_GRIDS` entries | `COMPONENT_VARIATION_RULES` entries | Notes |
|---|---|---|---|
| `mejorar_autonomia` | 14 (battery factor, motor_count delta, motor_power factor, structure factor, combos) | 1 rule → 4 battery-capacity values (300/500/800/1200 Wh) | Both sources active |
| `aumentar_payload` | 9 (payload factor, thrust factor, motor_count delta, combos) | 1 rule → 4 motor power-w values (150/200/300/400 W) | Both sources active |
| `reducir_payload` | 5 (payload factor down, structure+payload combo, motor_count-1+payload) | **none** | Params-only |
| `reducir_masa` | 5 (structure factor, payload factor, combo) | 1 rule → 3 frame mass-kg values | Both sources active |
| `mejorar_estabilidad` | 7 (motor_count delta, thrust factor, safety_factor factor, combos) | 1 rule → 2 frame mass-kg values | Both sources active, note: component rule varies **frame**, not motors, despite the goal's params grid being motor-thrust-driven — a real inconsistency (§4 recommendation addresses this) |

**Dedup/cache:** `_evaluate(params)` caches by `frozenset(params.items())`. Every candidate — params-only or component-driven — funnels through this one cache keyed purely on the *resulting flat params dict*, never on component identity. Confirmed hazard for catalog candidates (§10).

### 2.3 Post-apply survival (iterate, G9-A)

- **`iterate` next turn:** G5's `sync_motors_component_from_params` (already runs unconditionally after every DSE apply, not just catalog ones) keeps `resolve_propulsion_parameters`'s component-derived read current, so a catalog-native apply is no more at risk of the G5 dual-truth bug than today's params-only applies already aren't — this is existing, proven protection, not something Impl C needs to add.
- **G9-A readiness:** `resolve_motor_catalog_surface` reads `components["motors"].catalog_ref` fresh every call — a catalog-native DSE apply that leaves `catalog_ref` set is indistinguishable from a catalog-native *acquisition* bind (G21) at read time. No G9-A code changes needed; confirmed in §8.

---

## 3. Catalog API inventory

| Method | Inputs | Output | Deterministic | Used by acquisition today? |
|---|---|---|---|---|
| `get_motor(name)` | exact/normalized name | `MotorSpec`, raises `KeyError` if missing | Yes | Yes (`resolve_motor_from_text`, G9-A bound-SKU validation) |
| `has_motor(name)` | name | `bool` | Yes | Yes (G9-A Scenario D) |
| `find_motors_for_requirements(min_thrust_n, kv, prop_inch)` | design-space filters | `list[MotorSpec]`, sorted `(is_generic, |Δthrust|, name)` | Yes | Yes — the D8 authority; used directly by `resolve_motor_catalog_surface` (G9-A) and wrapped by `build_motor_catalog_suggestions` |
| `find_motors_by_kv(kv, tolerance)` | kv + tolerance | `list[MotorSpec]` | Yes | No longer (G22 removed its use as a *fallback* in `build_motor_catalog_suggestions`; still used by `iterate_interactive_session.py`'s own suggestion path — separate, unrelated call site, out of G22's scope) |
| `match_motor_propeller(motor_id, prop_id)` | two SKU names | `bool` | Yes | Not yet wired into any acquisition/gap path — pure library capability |
| `get_battery(name)` / `has_battery(name)` | name | `BatterySpec` / `bool` | Yes | Yes (`bind_battery_from_catalog`) |
| `find_batteries(min_energy_wh, chemistry)` | plain filters, no design-space matching | `list[BatterySpec]` sorted `(energy_wh, name)` | Yes | No live acquisition entry point calls this yet (Impl A/B note: "no battery catalog pick flow exists") |
| `get_propeller` / `has_propeller` / `find_propellers` | — | — | Yes | No live acquisition entry point (propeller pick explicitly out of scope, per this contract §2) |
| `bind_motor_from_catalog(suggestion, *, base=None)` | a `MotorSuggestion` (from `build_motor_catalog_suggestions`/`find_motors_for_requirements`-derived dict) | `ComponentSpec` with `catalog_ref` set | Yes | Yes — the one shared bind helper (G21 component-wizard pick, numeric-wizard pick, iterate mid-session pick) |
| `bind_battery_from_catalog(sku, *, library=None, base=None)` | sku string | `ComponentSpec` with `catalog_ref` set | Yes | Test-callable only — no UX entry point yet (confirmed unchanged since Impl B) |

**Answer to §1.2's question:** DSE should call `motor_catalog_assist.build_motor_catalog_suggestions(project_state, limit=N)` directly (or the `derive_kv_prop_filters` + `find_motors_for_requirements` pair it wraps) — **not** a new DSE-local search. This is the exact function G22 made the single authority for "what motor SKUs fit this design space," and reusing it means a catalog-DSE candidate list and `list_motors`/the G9-A gap will never disagree about which SKUs exist for the current requirements — the same discipline G22 just finished establishing. Building a parallel search inside `design_explorer.py` would silently reopen the G22 dual-authority bug one layer up.

---

## 4. Goal × family matrix

| goal_key | Touches motors? | Touches battery? | Touches frame/structure? | Catalog candidate feasible in v1? |
|---|---|---|---|---|
| `mejorar_autonomia` | Yes (motor efficiency, power↓) | **Yes — primary lever** (capacity↑) | Yes (mass↓, secondary) | **Battery: yes** (pattern identical to motors, `bind_battery_from_catalog` exists). Motor-efficiency-by-SKU is a weaker fit (no "efficiency" field on `MotorSpec`, would require picking a lower-`max_watts` SKU as a proxy — not v1). |
| `aumentar_payload` | **Yes — primary lever** (higher-thrust SKU) | No | No | **Yes — v1 candidate** |
| `reducir_payload` | Weakly (`motor_count_delta: -1` in one params entry) | No | Yes (structure factor combo) | **No** — no catalog dimension naturally reduces payload; a *smaller/cheaper* motor SKU is a valid real-world response but scoring is `-payload_kg` (motor swap doesn't change payload at all) — catalog branch would add candidates that can't move this goal's own score. Stay on abstract grid. |
| `reducir_masa` | No (component rule targets frame, not motors — see §2.2 inconsistency note) | No | **Yes — primary lever**, but frame has **no catalog** (`bind_frame_from_catalog` does not exist; frame acquisition is freeform material+mass only) | **No** — blocked on a frame catalog that doesn't exist yet, out of this IC's scope by the contract's own "library JSON seed expansion" / new bind-family exclusion |
| `mejorar_estabilidad` | **Yes — primary lever** (higher-thrust SKU raises `safety_margin_ratio`) | No | Weakly (component rule uses frame mass, inconsistent with the params grid's motor focus — same note as `reducir_masa`) | **Yes — v1 candidate** |

**Recommendation for Impl C v1:** `aumentar_payload` and `mejorar_estabilidad` (motor catalog only) — exactly the two goals the contract's own example slice table (§1.12) names for C1. `mejorar_autonomia` battery catalog is real and low-risk (same pattern, existing `bind_battery_from_catalog`) but recommended as a separate slice (C3, optional) since it has no acquisition-side precedent to reuse (no G21-equivalent battery pick UX exists — DSE would be the *first* battery catalog consumer, a bigger first-of-its-kind risk than reusing G21/G22's already-proven motor path). `reducir_payload`/`reducir_masa` stay on abstract grids — no catalog dimension exists to offer honestly.

**Also flagged (not asked, but discovered):** `mejorar_estabilidad`'s and `reducir_masa`'s existing `COMPONENT_VARIATION_RULES` entries both vary **frame mass**, which doesn't match either goal's own dominant params-grid lever (motor thrust for stability, structure factor for mass — frame mass overlaps structure factor already). This predates Impl C and is not a catalog problem, but worth a maintenance note for whoever writes the IC: the component-grid entries for these two goals were seemingly copy-pasted without goal-specific tuning.

---

## 5. Candidate shape options

### Option A — `components_delta` carries `bind_motor_from_catalog` output (recommended)

`components_delta = {"motors": bind_motor_from_catalog(suggestion, base=existing_motors_spec)}`. Flows through the **existing** component branch of `explore()` (`apply_components_delta(normalized_state, comp_delta)` → calc/sim/score) with no new code path, and through the **existing** apply branch of `_handle_apply_exploration()` unchanged.

- **Files touched:** `design_explorer.py` only (new candidate-generation function; `ExplorationCandidate`/`ExplorationResult` schema unchanged).
- **Test surface:** new tests for the generation function + a handful of `explore()`/`_handle_apply_exploration()` integration tests confirming `catalog_ref` survives. No schema migration tests needed.
- **Interaction with `invalidate_diverged_catalog_refs`:** confirmed safe no-op (§7.1) — no skip needed.
- **G5 sync still needed?** Yes, unconditionally, exactly as today — it's a no-op when nothing diverged (which a fresh catalog bind never does against its own just-derived params).

### Option B — new `catalog_bindings` field + dedicated apply branch

Add `catalog_bindings: list[CatalogRef] | None` to `ExplorationCandidate`; `_handle_apply_exploration` gets a third branch that resolves each `CatalogRef` back through `bind_*_from_catalog` at apply time and writes it explicitly.

- **Files touched:** `schemas/tool_schema.py` or wherever `ExplorationCandidate` truly lives, `design_explorer.py`, `orchestrator.py` (new apply branch), plus every place that pattern-matches on `if best.components_delta:` (currently one call site, but any future consumer of `ExplorationCandidate` would need to know about the third shape).
- **Test surface:** larger — new schema field, new apply branch, new interaction tests with the two existing branches (mutual exclusivity? combinable?).
- **Pros:** identity is explicit and inspectable without reaching into `components_delta[key].catalog_ref`.
- **Cons:** the "identity is explicit" pro is largely cosmetic — `components_delta["motors"].catalog_ref` is exactly as inspectable, and Option B duplicates the apply-time bind-and-write logic `bind_motor_from_catalog` + `set_motor_component`/`apply_components_delta` already do correctly. Real schema churn for no capability Option A lacks.

### Option C — SKU carried only in `generation_metadata`, bound at apply time

`generation_metadata = {"catalog_sku": "sunnysky_r2305_2500", "family": "motor"}`; `components_delta` stays empty or carries only the delta's *numeric* effect (so scoring/labeling work identically to today's synthetic candidates); the actual `bind_motor_from_catalog` call happens inside `_handle_apply_exploration` when it sees `generation_metadata.catalog_sku`.

- **Files touched:** `design_explorer.py` (candidate generation uses real SKU numbers for scoring, stashes the SKU string), `orchestrator.py` (new metadata-driven bind branch in apply).
- **Cons — the reason this is not recommended:** identity does not exist on the candidate until apply time. Between explore and apply, nothing has actually confirmed the *bind* itself would succeed (e.g. `has_motor` could theoretically fail if the library changed mid-session, though this is extremely unlikely given no runtime library mutation exists) — but more importantly, this defers the exact work Option A already does for free, for a smaller `explore()` diff that isn't actually smaller once the apply-time bind branch is written. It also means `exploration.viable[i].components_delta` is empty for a catalog candidate, which is surprising for anything downstream that inspects candidates before apply (e.g. a future CLI preview).

**Minimal diff:** Option A. **Most correct long-term:** also Option A — it is both. Option B is not more correct, only more explicit at a cost; Option C is strictly worse on both axes.

---

## 6. Grid strategy options

### Strategy 1 — Parallel branch: new catalog generation function per goal (recommended)

Add a function analogous to `_build_component_candidates_for_goal`, e.g. `_build_catalog_motor_candidates_for_goal(goal_key, project_state) -> list[dict[str, ComponentSpec]]`, gated by a small declarative table naming which goals get a motor-catalog branch (`{"aumentar_payload", "mejorar_estabilidad"}` for v1) — **not** a table of invented values like `COMPONENT_VARIATION_RULES`; internally it calls `build_motor_catalog_suggestions(project_state, limit=N)` and `bind_motor_from_catalog(suggestion, base=existing)` per suggestion. `EXPLORATION_GRIDS`/`COMPONENT_VARIATION_RULES` stay untouched — added to, not replaced.

- **Risk:** "dual authority during migration" (per the contract's own framing) is real but narrow: for `aumentar_payload`/`mejorar_estabilidad`, the *existing* params-grid thrust-factor entries (`per_motor_max_thrust_n_factor`) and the *existing* component-grid motor-power entries (`COMPONENT_VARIATION_RULES["aumentar_payload"]`) would keep generating synthetic candidates **alongside** real ones in the same `exploration.viable` list, competing on score. This is not a correctness bug (both are legitimate "what if" candidates), but it does mean a synthetic, unbindable candidate could still rank #1 and get applied via `aplica la mejor`, silently losing the SKU opportunity the catalog branch worked to offer. This is the actual argument for Strategy 2/3, addressed below.

### Strategy 2 — Replace the motor-related synthetic entries for catalog-eligible goals

For `aumentar_payload` and `mejorar_estabilidad` specifically, remove `COMPONENT_VARIATION_RULES`'s synthetic motor-power rule (only `aumentar_payload` has one today) and leave the params-grid thrust-factor entries as an honest **physics-only preview** (useful even when unbound — "if you had a motor with 2x this thrust..."), but exclude them from ever being the `viable[0]` pick and let the catalog branch's candidates always outrank a same-improvement synthetic one. This requires either a tiebreak rule in scoring or a hard "prefer catalog-sourced when present" pass before `viable.sort()`.

- **Risk (named directly in the contract):** on an **unbound** project (no motors component, or motors present but the catalog search returns empty for current requirements), the catalog branch contributes zero candidates and the params grid is all that's left — exactly today's behavior, so no regression *there*. The risk is narrower than the contract's phrasing suggests: it's not "regression on unbound projects" in general, it's specifically "a synthetic candidate that used to be `viable[0]` might now lose a tiebreak to a worse-scoring-but-real candidate if the tiebreak rule is naive." Needs a precise, tested tiebreak spec if chosen.

### Strategy 3 — Hybrid: catalog branch when the library has matches, else abstract fallback

Run the catalog branch first; if it returns zero candidates (empty `find_motors_for_requirements`), fall back to running the old synthetic component-grid rule for that goal (not the params grid, which stays independent regardless). If the catalog branch returns ≥1 candidate, **skip** the synthetic component rule entirely for that goal (params grid still runs — it's not motor-identity-bearing, no conflict).

- **Complexity:** moderate — one conditional per goal in `explore()`, not a new field or scoring change.
- **Honest messaging:** when catalog-empty triggers the fallback, the DSE candidate list should say so explicitly in its label/message (mirrors G9-A's own "no tengo un motor" honesty, not a silent substitution) — a one-line addition to `_handle_explore`'s message builder.
- **This is the recommended strategy**, combined with Strategy 1's generation function: run the catalog branch (Strategy 1's function) for eligible goals; only fall back to the *synthetic component rule* (not the params grid, which is orthogonal) when the catalog branch is empty. This directly resolves Strategy 1's "dual authority" risk (synthetic motor-power candidates for `aumentar_payload` stop being generated once a catalog branch successfully runs) without Strategy 2's scoring-tiebreak complexity.

### Motor catalog enumeration specifics (answers to §1.5's sub-questions)

- **Filter source:** `physical_requirements.thrust_per_motor_needed_n`, `kv_hint` (from the existing motors component if any), `prop_inch` (from `current_parameters["propeller_diameter_in"]`) — identical to `build_motor_catalog_suggestions`'s own inputs, since we call it directly.
- **Include/exclude currently bound SKU:** recommend **exclude** — a candidate that reproduces the exact currently-bound SKU has `improvement == 0` by construction (same physics) and adds noise to a 5-slot list. `build_motor_catalog_suggestions` doesn't know about "currently bound" today; the catalog-DSE function should filter it out post-search (one `sku != current_catalog_ref.sku` check), not change the shared acquisition function's behavior.
- **Cap:** top-5, matching acquisition's own default (`build_motor_catalog_suggestions(..., limit=5)`) and `MAX_VIABLE`. No motor_count cross-product in v1 (see combinatorics, §9).
- **Generic motors sort last:** already true — `find_motors_for_requirements`'s sort key is `(is_generic, |Δthrust|, name)`, generics always sort after real SKUs. No new logic needed; inherited for free by reusing the function.

---

## 7. Apply + identity analysis (§1.6 direct answers)

1. **Does `catalog_ref` survive end-to-end via `bind_motor_from_catalog` → `apply_components_delta`?** **Confirmed yes.** `apply_components_delta` routes a `"motors"` key straight to `set_motor_component(state, spec, power_w)`, which writes `updated_components = {..., "motors": spec}` — the **entire** spec object, `catalog_ref` included, no stripping, no reconstruction. Traced line-by-line in `component_writers.py:207` and `:243-246`.
2. **Should catalog-native candidates skip `invalidate_diverged_catalog_refs`?** **No skip needed.** Traced the exact comparison: `invalidate_diverged_catalog_refs` compares `components["motors"].properties["thrust_n"].value` against `canonical_params["per_motor_max_thrust_n"]`. For a catalog-native candidate, `canonical_params` is read from `updated_project.current_parameters` **after** `apply_components_delta` already ran and derived `per_motor_max_thrust_n` from that same spec's `thrust_n` (via `resolve_propulsion_parameters`, driven by `output_magnitude="thrust_n"` — which `bind_motor_from_catalog` always sets). Both values trace to the identical source; they cannot diverge from a fresh bind. Confirmed this is exactly the same self-consistency the *acquisition* catalog pick already relies on (same writer, same derivation, G9-A never needed a skip there either).
3. **Does params-only-grid-in-parallel need a `generation_metadata.source` discriminator?** **No**, given Option A + Strategy 3. `_handle_apply_exploration`'s branch selection (`if best.components_delta:`) already discriminates component-driven from params-only candidates — a catalog motor candidate simply *is* a `components_delta` candidate, indistinguishable in kind from today's synthetic ones at apply time (the whole point of Option A). No new field needed.
4. **Battery — same questions:** yes, identical answers, substituting `bind_battery_from_catalog`/`set_battery_component` and the battery half of `invalidate_diverged_catalog_refs` (compares `battery_capacity_wh`). Confirmed the divergence-check function already has a symmetric battery branch (`invalidate_diverged_catalog_refs`'s second half, audited during G9-A). No changes needed there either.

**G5 order lock for mixed projects:** `invalidate_diverged_catalog_refs` and `sync_motors_component_from_params` both operate on the **whole** `components` dict, motor and battery branches independently, in one pass each — a project with a bound battery *and* a catalog-motor DSE candidate hits both branches in the same two calls, in the same fixed order, with no interaction between the motor and battery checks (traced: the two branches inside `invalidate_diverged_catalog_refs` are sequential `if` blocks on different dict keys, no shared state). Mixed-bound projects are not a new risk Impl C introduces.

---

## 8. G9-A / G5 / G21 interaction notes

| Post-apply state | G9-A scenario | Expected gap? | Confirmed by |
|---|---|---|---|
| Applied catalog motor SKU meets requirements | **B** | No — `catalog_gap is None`, subsystem verdict `PASS` | Same code path G9-A's own `test_gap_motor_catalog_unresolved_absent_when_bound_sku_covers` already exercises; a DSE-applied bind is byte-identical in shape to an acquisition-applied bind at the point G9-A reads it (`components["motors"].catalog_ref`) |
| Applied SKU underspec for new requirements (e.g. payload later increased again past this SKU) | **C** | Gap naming the SKU, not the generic "no tengo un motor" | Same — G9-A's Scenario C logic is agnostic to *how* the SKU got bound |
| Explore proposed SKU but user didn't apply | — | No state change | `explore()` is confirmed read-only/pure (§2.1); nothing persists until `aplica la mejor` |
| Catalog branch empty (no library match for current requirements) | A/F | Honest "no SKU covers space" | This is Strategy 3's fallback trigger — the DSE message itself should say so (new copy, not new logic) when falling back to the synthetic/abstract candidates |

**Does Impl C need G9-A's Option C (`bound_sku_status` typed field)?** **No.** Every interaction above is resolved by the *existing* message-level honesty G9-A already provides — DSE doesn't need to branch on a typed status to decide what to generate or how to label a result; it only needs to know "does `find_motors_for_requirements` return anything" (a plain list-empty check, already available) and, post-apply, G9-A's own machinery narrates the outcome to the user on the *next* `estado`/Continuity read, which needs no DSE-side involvement at all. This confirms the investigation's own §0.2 hypothesis.

**G21 interaction:** none beyond what's already stated in §3 — DSE reusing `build_motor_catalog_suggestions` means it automatically inherits every G21/G22 fix (single authority, no KV fallback) with zero duplicated logic, and zero risk of DSE and acquisition ever disagreeing about which SKUs exist for a given design space.

---

## 9. Unbound vs bound project behavior

| Project state | Recommended explore behavior |
|---|---|
| No motor / no `catalog_ref` | Catalog branch still runs (search doesn't require an existing bound motor — `kv_hint`/`prop_inch` come from whatever's declared, possibly `None`, and `find_motors_for_requirements` degrades gracefully to a broader search, same as acquisition's own unbound-help-choose path). `base=None` is passed to `bind_motor_from_catalog` (no existing spec to merge onto) — matches the acquisition component-wizard's own first-pick shape exactly. Abstract grid (params + synthetic component) keeps running in parallel/fallback per Strategy 3. |
| Bound motor, explore payload | Catalog branch proposes *alternative* SKUs (excluding the current one, §6) at the **same `motor_count`** (read from the existing spec via `bind_motor_from_catalog`'s `base=` merge) — does not also vary `motor_count` in v1. A separate params-grid entry (`motor_count_delta`) already explores the "more of the same motor" direction independently; combining both dimensions in one catalog candidate is deferred (combinatorics, below). |
| Bound motor, explore autonomía | Recommended v1: **battery-only** catalog branch (C3, optional slice) — motor "efficiency" has no catalog field to search on (§4), so a motor-swap candidate for this goal would be inventing a ranking criterion (`max_watts` as an efficiency proxy) not backed by any real physics the simulator uses. Do not combine motor+battery catalog search in one candidate in v1 — compounds the combinatorics risk for a goal where battery capacity is already the dominant, well-understood lever. |

**Combinatorics limit:** with 20 real motors and 10 real batteries in the library today (verified via `default_library.list_motors()`/`list_batteries()`), a single-family top-5 search (§6) is trivially cheap — no explosion risk *at today's library size*. The risk is architectural, not data-volume: motor-SKU × `motor_count`-delta × battery-SKU cross-products would multiply candidate count by each dimension's cardinality with no natural cap, and — more importantly — **no existing scoring/labeling machinery expects a multi-dimensional catalog candidate** (label building, `_build_label_components`, assumes one spec's own properties, not a combo). Recommendation: **v1 stays single-family per candidate** (motor-only OR battery-only, never both, never crossed with a count delta) — this is a design choice, not a computed limit, and should be an explicit ★ decision (§13) rather than left implicit.

---

## 10. Scoring + cache notes

### Scoring fairness (§1.9)

For `aumentar_payload`, `_score_candidate` = `sim.safety_margin_ratio * calc.payload_kg`. A motor-catalog candidate never changes `payload_kg` (only the params-grid `payload_kg_factor` entries do) — so among catalog candidates specifically, score is monotonic in `safety_margin_ratio`, which is monotonic in thrust. **The highest-thrust real SKU in the search result will always rank first among catalog candidates.** This is not a bug in the scoring function (it correctly reflects "which real motor gives the most margin"), but it does mean a modest, well-matched SKU can never outrank an overspec'd one on this axis alone.

- **Is this acceptable for v1?** Recommend **yes, with a labeling caveat**: real SKUs ranked purely by physics outcome is an honest, defensible v1 behavior — no fabrication, no synthetic advantage. The thing worth fixing is not the score, it's that the *label* should make the overspec visible (e.g. include the SKU's own margin-over-requirement) so a user isn't surprised the "best" pick is also the priciest/heaviest real part. That's a labeling/UX decision, not a scoring-formula change.
- **Normalization?** Not recommended for v1 — a "score per SKU tier" or "penalize overspec" adjustment would be a new, invented weighting with no physics backing (same category of risk the hard constraints forbid for SKU *selection*; scoring is adjacent enough to warrant the same caution). Defer unless Engineer explicitly wants it.
- **Label UX:** **yes, the label must include the SKU name.** `_build_label_components` reads `spec.properties` (`f"{comp_key}: {prop_summary}"`, e.g. today's synthetic `"motors: power_w=220.0"`) — **not** `spec.name` — so it will already render `thrust_n`/`kv_rating`/`power_w` for a catalog-bound spec correctly, with **no change needed**. One real (separate) data-hygiene gap traced: `bind_motor_from_catalog(suggestion, base=existing)`'s `model_copy` never updates `name` when merging onto a `base` — a catalog-DSE candidate generated with `base=existing_motors_spec` inherits the *old* spec's `name` (whatever freeform description or prior SKU it was), not the new SKU string. This doesn't affect the DSE label (label doesn't read `.name`) or `catalog_ref.sku` (correct, independent field), but would affect any *other* future consumer that displays `component.name` directly (e.g. a BOM line, out of this IC's scope). Worth a one-line fix (`name=sku` explicitly passed alongside `base=` in the future IC's generation function) but not a blocker — flagged for the implementer, not a ★ decision.

### Cache/dedup hazard (§1.10)

The `_evaluate()` cache keys on `frozenset(params.items())` — the **derived flat params dict**, not component identity. For a catalog motor candidate, the derived params include `motor_power_w`, `motor_kv_rating`, `motor_count`, and (via `resolve_propulsion_parameters`) `per_motor_max_thrust_n` — **not** `catalog_ref.sku`. Two different real SKUs that happen to produce numerically identical derived params (e.g. two motors with the same thrust/kv/count) would collide in the cache and the second candidate would silently reuse the first's `calc`/`sim` object.

- **Does this matter for the returned `calc`/`sim`?** No correctness risk — if two SKUs are physically identical in every param the calculation engine reads, they genuinely do produce the same calc/sim, so sharing the cached result is *correct*, not stale.
- **Does it matter for `catalog_ref`/`label`/identity?** **No** — the cache only stores `(calc, sim)`, never the candidate object itself; each candidate still builds its own `ExplorationCandidate` with its own `components_delta`/`label` from its own loop iteration, using the shared `(calc, sim)` tuple. Two same-physics SKUs would appear as two distinct, correctly-labeled candidates with identical scores (both real, both correctly ranked, no fabrication) — a case of "two real options tie," not a bug.
- **Conclusion:** the cache key does **not** need `catalog_ref.sku` added. The existing TODO comment about two different `ComponentSpec`s colliding was written for the *synthetic* component grid (where collision would be coincidental/unintended); for catalog candidates, "same derived physics → shared calc/sim, still two labeled real candidates" is the correct behavior, not a hazard. No change recommended.

---

## 11. Test inventory + CLI probe

### Existing tests touching this surface

| File | Count | Coverage | Assumes abstract-only grids? |
|---|---|---|---|
| `tests/test_design_explorer.py` | 62 (class-based) | `_apply_delta`, `_score_candidate`, `_build_label`, grid structure, `DesignExplorer.explore()` integration, `IntentResolver` explore patterns, `_handle_apply_exploration` edge cases (mocked) | Yes — `TestDesignExplorerExplore`/`TestHandleApplyExploration` construct synthetic candidates/mocks; none reference `catalog_ref`. Will need new test classes for the catalog branch, not rewrites of existing ones (existing behavior for goals *without* a catalog branch, or when the catalog branch is empty, must stay byte-identical). |
| `tests/test_da2_components_delta.py` | 2 | `apply_components_delta` composite delta application | No catalog assumption — generic |
| `tests/test_u3_dse_exploration.py` | 11 | Structure-mass/frame factor exploration (U3 slice) | No catalog assumption |
| `tests/test_f1_reducir_payload.py` | 25 | `reducir_payload` goal specifically | Confirms this goal has no component grid today — consistent with §4's "no catalog dimension" finding |
| `tests/test_catalog_bind_v1.py` | 14 | `bind_motor_from_catalog`/`bind_battery_from_catalog`, `catalog_ref` persistence, G5 divergence/invalidation — includes `test_dse_apply_diverging_thrust_clears_motor_catalog_ref`, which already builds a *manual* `ExplorationResult` with a `params_delta` (not `components_delta`) candidate to prove divergence-clearing. This is the closest existing precedent to a "catalog-DSE apply" test and should be the template a future IC's own tests follow for the *non*-diverging (Scenario B) counterpart. | Confirms the apply-path plumbing (§7) is already tested for the params-only divergence case; the mirror case (component-driven, non-diverging, `catalog_ref` survives) has **no test today** — a real gap the future IC must close. |
| `tests/test_g5_dse_iterate_dual_truth.py` | 5 | G5 sync/invalidate ordering, iterate-after-DSE regression | No catalog-candidate-specific case; would benefit from one exercising a catalog-native apply followed by an unrelated iterate turn |

### Proposed regression probes for the future IC (bullets, not written here)

1. Catalog branch generates ≥1 candidate with `components_delta["motors"].catalog_ref is not None` for `aumentar_payload` on a project whose requirements have real SKU matches.
2. Currently-bound SKU is excluded from its own candidate list (§6).
3. Apply a catalog candidate → `catalog_ref` survives on disk (mirrors `test_dse_apply_diverging_thrust_clears_motor_catalog_ref`'s structure but asserts *non*-clearing).
4. G9-A Scenario B fires immediately after a catalog-DSE apply (no false gap) — direct reuse of G9-A's own test pattern against a DSE-applied project state.
5. Empty catalog search (no library match) → Strategy 3 fallback fires, message is honest about it (not silently substituting synthetic candidates without saying so).
6. Iterate an unrelated param after a catalog-DSE apply → `catalog_ref`/`motor_count`/thrust unchanged (G5 regression, mirrors existing `test_g5_dse_iterate_dual_truth.py` shape).
7. `reducir_payload`/`reducir_masa` explore output is byte-identical before/after the IC lands (proves no regression on goals with no catalog branch).

### CLI probe (contract §1.11 — reproduced, not modified; validated feasible against current code)

```text
1) New project → definir propulsion → ayúdame a elegir → pick SKU #1
2) estado → confirm catalog_ref set, G9-A Scenario B
3) explora opciones / optimiza para aumentar payload
4) List shows ≥1 candidate with real SKU in label
5) aplica la mejor
6) estado → same or upgraded catalog_ref; no GAP-MOTOR-CATALOG-UNRESOLVED if SKU sufficient
7) iterate unrelated param → motor_count/thrust/catalog_ref unchanged (G5 regression)
```

All seven steps are exercised by paths already confirmed to exist and behave correctly in this investigation (steps 1-2 are G21/G9-A, already tested; steps 3-7 are exactly what §5-§9 traced).

---

## 12. Recommended approach

**Option A** (candidate shape) + **Strategy 3, built on Strategy 1's generation function** (grid strategy): a new `_build_catalog_motor_candidates_for_goal(goal_key, project_state)` in `design_explorer.py`, gated to `{"aumentar_payload", "mejorar_estabilidad"}` in v1, that calls `motor_catalog_assist.build_motor_catalog_suggestions` (reusing G22's single authority, not a new search) and `bind_motor_from_catalog(suggestion, base=existing_motors_spec)` per result, excluding the currently-bound SKU. When this branch returns candidates, skip that goal's synthetic `COMPONENT_VARIATION_RULES` entry (only `aumentar_payload` has one) for that explore call; when it returns none (unbound project or empty library search), fall back to the existing synthetic/abstract candidates unchanged, with an honest one-line note in the explore message.

Reasoning, in priority order:

1. **Zero changes to the apply path, G5, or G9-A** — confirmed by tracing every relevant function line-by-line (§7, §8). This is the single strongest argument: the identity-preservation problem the contract opens with is already solved by existing code, for *any* candidate shaped like Option A. Impl C's real work is generation, not apply.
2. **No new dual-authority risk** — reusing `build_motor_catalog_suggestions` means DSE inherits G21/G22's already-hardened single motor-search authority instead of building a second one.
3. **Combinatorics stay bounded by construction** (single-family, top-5, no cross-products) without needing a new limiting mechanism — it's just "don't write the cross-product code," not "add a cap that could be gotten wrong."
4. **Battery (C3) and other goals are explicitly deferred**, not because they're infeasible (battery is proven feasible, same pattern) but because v1 should prove the pattern once, cleanly, on the two goals where it's unambiguously the right lever, before extending it — consistent with the contract's own hard constraint against collapsing scope.

---

## 13. ★ Decisions for Engineer

**★1 — Candidate shape:** Option A (populate `components_delta` with `bind_motor_from_catalog` output). *Recommended; no viable alternative identified that isn't strictly worse (§5).*

**★2 — Grid strategy:** Strategy 3 (catalog branch first, fallback to existing synthetic/abstract candidates when catalog search is empty), built on a new generation function (Strategy 1's shape) that calls `build_motor_catalog_suggestions` directly rather than a new `CATALOG_EXPLORATION_RULES` table of invented values. *Recommended.*

**★3 — v1 goal scope:** `aumentar_payload` + `mejorar_estabilidad` (motor catalog only). `mejorar_autonomia` (battery catalog) deferred to an optional slice C3. `reducir_payload`/`reducir_masa` stay on abstract grids permanently (no catalog dimension exists for them). *Recommended; Engineer may choose to fold C3 into v1 if battery-catalog risk is deemed acceptable — the pattern is proven, just untested at the acquisition layer.*

**★4 — Currently-bound SKU exclusion:** exclude the currently-bound SKU from its own goal's catalog candidate list (§6). *Recommended as a UX nicety, not a correctness requirement — Engineer may prefer to include it as an explicit "keep current" baseline reference row instead.*

**★5 — Combinatorics limit:** v1 candidates are single-family only (motor-only or battery-only), never combined with each other or with a `motor_count` delta in the same candidate. *Recommended as an explicit, documented v1 boundary, not an implicit omission — future ICs can lift it deliberately.*

**★6 — Scoring:** no change to `_score_candidate` — real SKUs ranked purely by physics outcome (highest thrust/margin wins among catalog candidates) is accepted for v1, with the caveat that candidate **labels** should make each SKU's own numbers legible (already mostly free via `_build_label_components`, per §10). *Recommended.*

**★7 — G9-A Option C (`bound_sku_status` typed field):** **not needed** for Impl C. Message-level honesty is sufficient at every interaction point traced in §8. *Recommended: do not implement as part of Impl C; leave deferred exactly as G9-A's own investigation already concluded.*

**★8 — Frame/`reducir_masa` component-rule mismatch (§4 discovery):** not part of Impl C's scope, but flagged — the existing `COMPONENT_VARIATION_RULES` entries for `mejorar_estabilidad` and `reducir_masa` vary frame mass in a way that doesn't obviously match either goal's dominant lever. *Not a ★ decision requiring action here — noted for a future, separate cleanup IC if Engineer agrees it's worth a look.*

---

## 14. Suggested Implementation Contract outline

*(Bullets only, per contract §1.12 / §3 — not a full IC.)*

**Slice C1 — Motor catalog candidates for `aumentar_payload` + `mejorar_estabilidad`**
- New `_build_catalog_motor_candidates_for_goal(goal_key, project_state)` in `design_explorer.py`; gate set `{"aumentar_payload", "mejorar_estabilidad"}`.
- Calls `motor_catalog_assist.build_motor_catalog_suggestions` + `bind_motor_from_catalog(suggestion, base=existing)`; excludes currently-bound SKU (★4).
- `explore()` wires the new branch in per Strategy 3: run catalog branch; if non-empty, skip that goal's synthetic `COMPONENT_VARIATION_RULES` entry for this call; params grid runs regardless (orthogonal).
- Acceptance: `optimiza para aumentar payload` / `optimiza para estabilidad` on a bound-or-unbound project lists ≥1 real-SKU candidate when the library has matches; byte-identical output to today when it doesn't.

**Slice C2 — Apply-path + identity regression coverage**
- No production code expected (§7 confirms the existing apply path already works) — this slice is test-only: probes #3, #4, #6 from §11.
- Acceptance: catalog-native `aplica la mejor` preserves `catalog_ref`; G9-A Scenario B fires immediately after; an unrelated iterate turn afterward doesn't revert it (G5 regression).

**Slice C3 — Battery catalog for `mejorar_autonomia` (optional, Engineer's call per ★3)**
- Same pattern as C1, substituting `find_batteries`/`bind_battery_from_catalog` — note `find_batteries` has no design-space ranking today (plain threshold filter, not D8-style), so this slice may also need a small battery-ranking addition or an explicit decision to ship without one.
- Acceptance: same shape as C1, battery family.

**Slice C4 — Honest fallback messaging**
- When Strategy 3's catalog branch is empty, the explore message states so explicitly (one line), rather than silently substituting synthetic candidates.
- Acceptance: message-level test, no behavior change to candidate generation itself.

**Slice C5 — Integration tests + CLI probe script**
- All 7 probes from §11 as automated tests (mirroring the G9-A/G21 precedent of a scripted-equivalent probe when a full interactive CLI session isn't run).
- Full suite green, zero weakened tests.

**Out of scope for the IC (carried forward from this investigation's own §2 boundaries):**
- Impl D (BOM), Phase 2 (operating points), propeller catalog pick UX, ESC catalog, library seed expansion, LLM SKU selection.
- Full removal of `EXPLORATION_GRIDS`'/`COMPONENT_VARIATION_RULES`' abstract entries for catalog-eligible goals (Strategy 3 skips them conditionally at generation time; deleting them outright is a bigger, separate decision Engineer hasn't been asked to make here).
- `bound_sku_status` implementation (★7 — not needed).
- Frame/`reducir_masa` component-rule cleanup (★8 — separate, optional future IC).
