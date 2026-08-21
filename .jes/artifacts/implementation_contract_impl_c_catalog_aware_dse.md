# Implementation Contract — Impl C Catalog-Aware DSE

**Project:** Jarvis  
**Date:** 2026-08-20  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Catalog-aware Design Space Explorer — motor SKU candidates for selected goals; identity preserved through existing apply path.

**Investigation:** [`.jes/artifacts/investigation_report_impl_c_catalog_aware_dse.md`](investigation_report_impl_c_catalog_aware_dse.md) — **CLOSED**  
**Investigation review:** [`.jes/artifacts/investigation_review_impl_c_catalog_aware_dse.md`](investigation_review_impl_c_catalog_aware_dse.md) — **PASS**  
**Checkpoint base:** tag **`checkpoint-g21-g23`** · commit `8dcc151`

**Workflow:** Claude implements **Slices C1→C2→C4→C5 in order** (C3 deferred) + tests + report → Engineer → Cursor review → CLI probe → commit/tag if Engineer asks.

---

## 0. Engineer ratification (locked — do not reopen in implementation)

| ★ | Decision |
|---|---|
| **★1** | **Option A** — `components_delta["motors"]` carries the `ComponentSpec` from `bind_motor_from_catalog()` |
| **★2** | **Strategy 3** — catalog branch first via `build_motor_catalog_suggestions()`; honest fallback when library search empty; **no** new motor search authority |
| **★3** | **C1 motor-only:** `aumentar_payload` + `mejorar_estabilidad`. **C3 battery deferred** (optional post-v1) |
| **★4** | **Exclude** currently bound motor SKU from catalog candidate list |
| **★5** | **Single-family** per candidate — motor-only in v1; no battery combo; no `motor_count` cross-product in catalog candidates |
| **★6** | **Do not change** `_score_candidate`; labels must be sufficiently informative (SKU visible) |
| **★7** | **Do not implement** `bound_sku_status` (G9-A Option C) |
| **★8** | Frame/component-rule mismatch — **informational only**, out of scope |

**Additional locks (Engineer 2026-08-20):**

- **Do not modify** `G5` (`component_sync.py`, sync/invalidate order).
- **Do not modify** `G9-A` (`engineering_readiness.resolve_motor_catalog_surface`).
- **Do not modify** `orchestrator._handle_apply_exploration()` (apply path).
- **Do not modify** `component_writers.py`.
- **Do not create** `CATALOG_EXPLORATION_RULES` with invented numeric values.
- **Do not create** a new motor search/ranking function — reuse `build_motor_catalog_suggestions` only.
- **Do not remove** existing abstract `EXPLORATION_GRIDS` / `COMPONENT_VARIATION_RULES` entries (Strategy 3 skips conditionally at generation time only).

**Architecture constraint (strict):**

> Implement the **minimum change** required to satisfy the ratified ★ decisions. Do **not** reinterpret architecture or open new design decisions. Do **not** modify scoring, `ExplorationCandidate` schema, apply path, G5, G9-A, or `component_writers.py` **unless** a demonstrable contradiction with the approved investigation appears during implementation — in that case **STOP** and report; do not silently expand scope.

**One allowed exception to "orchestrator unchanged":** Slice **C4** may append a catalog-fallback note to `_handle_explore`'s user message by reading a new optional field on `ExplorationResult` (see §4.4). This is **not** an apply-path change.

---

## 1. Problem / intent

Today `DesignExplorer.explore()` never proposes real catalog SKUs. Params-only candidates clear bound identity via `invalidate_diverged_catalog_refs`; synthetic component candidates have `catalog_ref=None`.

Investigation confirmed: a catalog-native candidate in `components_delta["motors"]` **already survives** the full apply pipeline unchanged. Impl C's work is **candidate generation in `design_explorer.py`** (+ C4 message wiring + tests).

**Target behavior (v1):**

```text
optimiza para aumentar payload / mejorar estabilidad
        ↓
DesignExplorer catalog branch
        ↓
build_motor_catalog_suggestions(project_state, limit=5)
        ↓
bind_motor_from_catalog(suggestion, base=existing_motors_spec)
        ↓
ExplorationCandidate(components_delta={"motors": bound_spec}, ...)
        ↓
aplica la mejor  →  existing apply path  →  catalog_ref persists
        ↓
G9-A Scenario B (no false catalog gap) · G5 iterate regression green
```

---

## 2. Production changes — `design_explorer.py` only (C1)

All new logic lives in `src/jarvis/core/design_explorer.py` unless C4 explicitly names `orchestrator.py`.

### 2.1 New constants

Add near `COMPONENT_VARIATION_RULES`:

```python
# Impl C (Catalog-aware DSE v1): goals that get a motor-catalog candidate branch.
_CATALOG_MOTOR_GOAL_KEYS: frozenset[str] = frozenset({
    "aumentar_payload",
    "mejorar_estabilidad",
})

# Slice C4: appended to explore message when Strategy 3 catalog search is empty.
_CATALOG_MOTOR_FALLBACK_NOTE: str = (
    "Nota: no hay motores del catálogo que cubran el espacio de diseño actual; "
    "las opciones listadas son variaciones paramétricas o de otros componentes."
)
```

Do **not** add a `CATALOG_EXPLORATION_RULES` table of invented values.

### 2.2 New function — `_get_bound_motor_sku(project_state) -> str | None`

Pure helper. Returns `components["motors"].catalog_ref.sku` when `catalog_ref.family == "motor"`, else `None`.

### 2.3 New function — `_build_catalog_motor_spec(suggestion, *, base: ComponentSpec | None) -> ComponentSpec`

Wraps `bind_motor_from_catalog(suggestion, base=base)` from `jarvis.core.catalog_bind`.

**Required data-hygiene fix (investigation §10):** when `base is not None`, the returned spec **must** set `name=str(suggestion["name"])` (SKU string) on the merged spec — `bind_motor_from_catalog`'s `model_copy` merge does not update `.name` today. Implement via `.model_copy(update={"name": sku, ...})` **after** bind, without modifying `catalog_bind.py`.

Preserve `motor_count` from `base` via existing bind merge behavior.

### 2.4 New function — `_build_catalog_motor_candidates_for_goal(goal_key, project_state, *, normalized_state) -> tuple[list[dict[str, ComponentSpec]], bool]`

**Purpose:** generate catalog-native motor candidates for one explore call.

**Returns:**

- `list[dict[str, ComponentSpec]]` — one entry per SKU: `{"motors": bound_spec}`
- `bool had_library_matches` — `True` iff `build_motor_catalog_suggestions` returned **≥1 suggestion before ★4 bound-SKU exclusion**; `False` iff the suggestions list was empty (Strategy 3 "catalog search empty")

**Algorithm (exact):**

1. If `goal_key not in _CATALOG_MOTOR_GOAL_KEYS` → return `([], False)`.
2. Import and call **`motor_catalog_assist.build_motor_catalog_suggestions(project_state, limit=5)`** — the G22 single authority; pass `project_state`, not `normalized_state`, so requirements/filters match acquisition.
3. If step 2 returns empty → return `([], False)`. **This is the only condition for "catalog search empty"** (Strategy 3 / C4).
4. Set `had_library_matches = True`.
5. Read `bound_sku = _get_bound_motor_sku(project_state)`.
6. Read `base_motor = normalized_state.design_properties.components.get("motors")` (may be `None`).
7. For each `suggestion` in suggestions:
   - If `bound_sku is not None` and `suggestion["name"] == bound_sku` → **skip** (★4).
   - `spec = _build_catalog_motor_spec(suggestion, base=base_motor)`.
   - Append `{"motors": spec}` to result list.
8. Return `(result_list, had_library_matches)`.

**Do not:**

- Vary `motor_count` inside catalog candidates (★5).
- Combine motor + battery in one candidate (★5).
- Call `find_motors_for_requirements` directly unless through `build_motor_catalog_suggestions`.
- Cap differently than `limit=5` (matches acquisition default and `MAX_VIABLE`).

**Viability filtering:** this function returns **all** post-exclusion specs. The caller (`explore()`) runs each through `apply_components_delta` → calc/sim and drops non-viable (`can_fly=False`) exactly like today's component grid. `had_library_matches` is **not** affected by viability — only by step 2 emptiness.

### 2.5 Label enhancement — `_build_label_components` (★6)

When building labels for catalog candidates, the SKU must be visible in the explore list.

Update `_build_label_components` so that when `spec.catalog_ref is not None`:

```text
motors [sunnysky_r2305_2500]: thrust_n=12.5, kv_rating=2400, power_w=280.0, ...
```

Format: `f"{comp_key} [{spec.catalog_ref.sku}]: {prop_summary}"` when `catalog_ref` set; unchanged behavior when `catalog_ref is None`.

Do **not** change `_score_candidate`.

### 2.6 New helper — `_is_synthetic_motor_component_delta(comp_delta: dict[str, ComponentSpec]) -> bool`

Returns `True` when `comp_delta` contains `"motors"` and that spec has `catalog_ref is None` (today's synthetic `COMPONENT_VARIATION_RULES` motor entries). Used only for Strategy 3 skip logic on `aumentar_payload`.

### 2.7 Integration in `DesignExplorer.explore()` (exact placement)

Inside `explore()`, after baseline normalization/scoring and **before** the existing `# ── Params-only grid ──` loop, insert the catalog branch. **Params-only grid loop remains unchanged and always runs.**

```text
explore(project_state, goal_key):
    ... baseline (existing) ...

    catalog_motor_note: str | None = None
    skip_synthetic_motor_component_grid = False

    if goal_key in _CATALOG_MOTOR_GOAL_KEYS:
        catalog_deltas, had_library_matches = _build_catalog_motor_candidates_for_goal(
            goal_key, project_state, normalized_state=normalized_state,
        )
        if had_library_matches:
            skip_synthetic_motor_component_grid = True
        else:
            catalog_motor_note = _CATALOG_MOTOR_FALLBACK_NOTE

        for comp_delta in catalog_deltas:
            ... same try/apply_components_delta/_evaluate/score/append pattern
                as existing "# ── Component grid ──" loop ...

    # ── Params-only grid ──   (UNCHANGED)
    for delta in EXPLORATION_GRIDS.get(goal_key, []):
        ...

    # ── Component grid ──   (existing loop, with skip guard)
    for comp_delta in _build_component_candidates_for_goal(goal_key):
        if skip_synthetic_motor_component_grid and _is_synthetic_motor_component_delta(comp_delta):
            continue
        ... existing loop body unchanged ...
```

**Strategy 3 rules (locked):**

| Condition | Synthetic motor component grid (`aumentar_payload` power_w rule) | Params grid | C4 note |
|---|---|---|---|
| `had_library_matches == True` | **Skip** synthetic motor deltas only | **Always run** | No |
| `had_library_matches == False` | **Run** (fallback) | **Always run** | **Yes** — set `catalog_motor_note` |
| Bound SKU was only match (post-exclusion list empty but step 2 non-empty) | **Skip** synthetic motor | **Always run** | **No** — search was not empty |

For **`mejorar_estabilidad`:** catalog branch adds motor SKUs. The existing synthetic **frame-mass** `COMPONENT_VARIATION_RULES` entry **still runs** (orthogonal lever; ★8 mismatch is out of scope). `skip_synthetic_motor_component_grid` only skips motor synthetic deltas — on this goal there is none, so the flag has no skip effect beyond documentation consistency.

**Do not** skip params-grid thrust/motor_count entries for any goal.

### 2.8 `ExplorationResult` — one optional field (C4 wiring only)

Add to `ExplorationResult`:

```python
catalog_motor_note: str | None = None
```

Set from `explore()` return: pass through `catalog_motor_note` when non-`None`.

**Do not** add fields to `ExplorationCandidate`. **Do not** change `generation_metadata` semantics.

---

## 3. Slice C2 — Apply + identity regression (tests only; no production code expected)

Investigation concluded the existing apply path already preserves `catalog_ref` for component-driven candidates. **C2 is test-only** unless implementation discovers a demonstrable contradiction (§0 STOP rule).

### 3.1 Required end-to-end chain (mandatory test coverage)

The contract **requires** proving the real DSE catalog-native path — not merely that `apply_components_delta` accepts `catalog_ref`:

```text
catalog candidate (ExplorationCandidate with components_delta["motors"].catalog_ref set)
        ↓
session.last_exploration_result = exploration
        ↓
orchestrator._handle_apply_exploration()
        ↓
apply_components_delta(project_state, best.components_delta)
        ↓
saved state: components["motors"].catalog_ref persists (SKU matches)
        ↓
resolve_motor_catalog_surface / build_engineering_readiness → G9-A Scenario B (no GAP-MOTOR-CATALOG-UNRESOLVED when SKU covers requirements)
        ↓
orchestrator.handle_user_text(unrelated iterate, e.g. safety_factor)
        ↓
saved state: catalog_ref still set; motor_count/thrust unchanged vs post-apply
```

Mirror the structure of `tests/test_catalog_bind_v1.py::test_dse_apply_diverging_thrust_clears_motor_catalog_ref` (manual `ExplorationResult` + `_handle_apply_exploration`) for the **non-diverging catalog-native counterpart**, then extend with orchestrator iterate turn (G5 regression shape from `tests/test_g5_dse_iterate_dual_truth.py`).

---

## 4. Slice C4 — Honest fallback messaging (`orchestrator.py` minimal)

**Only change in orchestrator:** in `_handle_explore`, when building the success message (`viable_count > 0` branch), if `exploration.catalog_motor_note is not None`, insert **one line** immediately after the header line:

```text
Exploración completada para «{goal_label}» — {viable_count} configuración(es) viable(s) encontrada(s):

Nota: no hay motores del catálogo que cubran el espacio de diseño actual; las opciones listadas son variaciones paramétricas o de otros componentes.

  Línea base → ...
```

Use the exact string from `_CATALOG_MOTOR_FALLBACK_NOTE` (import from `design_explorer` or duplicate constant with comment pointing to single source — prefer import to avoid drift).

When `viable_count == 0` and `catalog_motor_note` is set, append the same note before the existing "ninguna produce un diseño viable" paragraph (one line, same text).

**Do not** change `_handle_apply_exploration`.

---

## 5. Slice C3 — Battery catalog (DEFERRED — do not implement)

`mejorar_autonomia` battery catalog candidates via `bind_battery_from_catalog` + `find_batteries` are **explicitly out of this contract** (Engineer ratification ★3). Document in Implementation Report as deferred optional slice. Implementer must **not** ship C3 unless Engineer publishes an extension IC.

---

## 6. Tests — `tests/test_impl_c_catalog_aware_dse.py` (new)

Implement focused tests; do not weaken existing suites.

### C1 — Catalog candidate generation

| Test | Assert |
|---|---|
| `test_catalog_branch_generates_bound_motor_candidate_aumentar_payload` | On a project fixture with real library matches + `can_fly` baseline, `explore(..., "aumentar_payload")` returns ≥1 candidate with `components_delta["motors"].catalog_ref.family == "motor"` and non-None SKU |
| `test_catalog_branch_generates_bound_motor_candidate_mejorar_estabilidad` | Same for `"mejorar_estabilidad"` |
| `test_bound_sku_excluded_from_catalog_candidates` | Bind motor SKU X → explore → no candidate has `catalog_ref.sku == X` |
| `test_strategy3_skips_synthetic_motor_on_aumentar_payload_when_library_matches` | When `build_motor_catalog_suggestions` returns matches, no viable/candidate has synthetic `motors` spec with `catalog_ref is None` and only `power_w` from `COMPONENT_VARIATION_RULES` — catalog motor candidates present instead |
| `test_strategy3_keeps_synthetic_motor_when_library_empty` | Mock or fixture with empty strict search → synthetic motor component candidates still generated for `aumentar_payload`; `exploration.catalog_motor_note` equals `_CATALOG_MOTOR_FALLBACK_NOTE` |
| `test_params_grid_still_runs_with_catalog_branch` | When catalog branch active, at least one `params_delta`-only candidate still present for the same goal (proves params grid independence) |
| `test_catalog_candidate_label_includes_sku` | Candidate label contains `[sku]` substring matching `catalog_ref.sku` |
| `test_reducir_payload_explore_unchanged` | `explore(..., "reducir_payload")` candidate set matches pre-Impl-C behavior (no catalog candidates — goal not in `_CATALOG_MOTOR_GOAL_KEYS`) |
| `test_reducir_masa_explore_unchanged` | Same for `"reducir_masa"` |

Use `default_library` real seed data where possible; mock `build_motor_catalog_suggestions` only when necessary for empty-search Strategy 3 cases.

### C2 — Apply + identity + G9-A + G5 (mandatory)

| Test | Assert |
|---|---|
| `test_catalog_native_dse_apply_preserves_catalog_ref` | Manual `ExplorationResult` with catalog `components_delta` → `_handle_apply_exploration()` → saved `catalog_ref` matches applied SKU |
| `test_catalog_native_dse_apply_g9a_scenario_b` | After apply above, `build_engineering_readiness` (or `resolve_motor_catalog_surface`) → no `GAP-MOTOR-CATALOG-UNRESOLVED` when bound SKU covers requirements — reuse G9-A Scenario B fixture pattern |
| `test_catalog_native_dse_apply_survives_unrelated_iterate` | Full chain §3.1: apply catalog candidate → iterate `safety_factor` (or equivalent) → `catalog_ref` still set; `motor_count` / `per_motor_max_thrust_n` unchanged |

### C4 — Fallback messaging

| Test | Assert |
|---|---|
| `test_explore_message_includes_catalog_fallback_note_when_search_empty` | `_handle_explore` / `handle_user_text("optimiza para aumentar payload")` on empty-search fixture → response `message` contains exact `_CATALOG_MOTOR_FALLBACK_NOTE` text |
| `test_explore_message_no_fallback_note_when_catalog_matches` | Bound/unbound project with library matches → `catalog_motor_note is None`; message does **not** contain fallback note |

### C5 — Integration regressions

| Test | Assert |
|---|---|
| `test_full_explore_apply_path_with_real_catalog_candidate` | Where library + physics allow: `explore` → pick viable catalog candidate → `_handle_apply_exploration` end-to-end without manual `ExplorationResult` construction |
| `test_existing_dse_apply_diverging_still_clears_catalog_ref` | Regression: `test_catalog_bind_v1.py::test_dse_apply_diverging_thrust_clears_motor_catalog_ref` still passes — params-only diverging apply unchanged |
| `test_g5_iterate_dual_truth_still_green` | Full `tests/test_g5_dse_iterate_dual_truth.py` unchanged behavior |

**Regression suites (must stay green):** `tests/test_design_explorer.py`, `tests/test_catalog_bind_v1.py`, `tests/test_g9a_*` / G9-A tests, `tests/test_g21_g22_*`, `tests/test_u3_dse_exploration.py`, `tests/test_f1_reducir_payload.py`.

---

## 7. CLI probe — acceptance criteria (C5)

Create `scripts/cli_probe_impl_c_catalog_dse.py` (untracked script pattern like `scripts/cli_probe_g21_g22_post_checkpoint.py`) documenting automated or semi-automated steps. Engineer manual walk acceptable if script uses orchestrator API.

**All 7 steps must PASS:**

```text
1) New project → definir propulsion → ayúdame a elegir → pick SKU #1
2) estado → catalog_ref set; G9-A Scenario B (no false generic catalog gap)
3) optimiza para aumentar payload  (or explora opciones with explicit payload goal)
4) Explore list shows ≥1 candidate whose label contains [sku] or catalog motor properties
5) aplica la mejor
6) estado → catalog_ref set (same or upgraded SKU); no GAP-MOTOR-CATALOG-UNRESOLVED if SKU sufficient
7) iterate unrelated param (e.g. safety factor) → catalog_ref / motor_count / thrust unchanged
```

Document results in Implementation Report.

---

## 8. Implementation Report (required)

Create: `.jes/artifacts/implementation_report_impl_c_catalog_aware_dse.md`

Sections:

1. Summary  
2. Files changed (expect: `design_explorer.py`, `orchestrator.py` C4-only, `tests/test_impl_c_catalog_aware_dse.py`, probe script)  
3. Functions added (§2.2–2.6)  
4. Strategy 3 behavior observed on fixtures  
5. Confirm **no** changes to apply path / G5 / G9-A / `component_writers` / `catalog_bind.py` (or STOP note if exception)  
6. Test list + suite count  
7. CLI probe evidence  
8. C3 deferred note  

---

## 9. Out of scope (hard)

| Forbidden | Belongs to |
|---|---|
| Impl D (Create→BOM) | separate IC |
| C3 battery catalog (`mejorar_autonomia`) | extension IC |
| Phase 2 Physical Propulsion Engine | long horizon |
| Propeller / ESC catalog in DSE | later |
| New motor search / `CATALOG_EXPLORATION_RULES` invented values | forbidden by ★2 |
| Changes to `_score_candidate` | ★6 |
| `ExplorationCandidate` schema changes | §0 |
| `bound_sku_status` | ★7 |
| Apply path / G5 / G9-A / `component_writers.py` changes | §0 (STOP if needed) |
| Removing abstract `EXPLORATION_GRIDS` entries | future decision |
| Frame `COMPONENT_VARIATION_RULES` cleanup (★8) | separate IC |
| Library JSON seed expansion | out of scope |

---

## 10. Acceptance (Cursor review)

**PASS** if:

1. C1 catalog branch matches §2 algorithm and Strategy 3 table.  
2. C2 tests prove §3.1 full chain (not only `apply_components_delta` unit).  
3. C4 exact fallback string appears when and only when `build_motor_catalog_suggestions` returns empty.  
4. ★4 bound-SKU exclusion verified.  
5. Params grid still runs (test).  
6. `reducir_payload` / `reducir_masa` byte-identical explore behavior.  
7. No forbidden file changes (§9).  
8. Full suite green; zero weakened tests.  
9. CLI probe 7/7 documented PASS.

**FAIL** if: new motor search authority, schema churn on `ExplorationCandidate`, apply-path edits without STOP report, or C3 shipped without extension IC.

---

**End of contract.**
