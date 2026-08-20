# Implementation Contract — G9-A Catalog-Ref Blind Spot (Option B)

**Project:** Jarvis  
**Date:** 2026-08-20  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** Catalog honesty — `resolve_motor_catalog_surface` must respect bound motor `catalog_ref`; orchestrator dedup.

**Investigation:** [`.jes/artifacts/investigation_g9a_catalog_ref_blind_spot.md`](investigation_g9a_catalog_ref_blind_spot.md) — **Option B only** (Engineer ratified)  
**Investigation contract:** [`.jes/artifacts/investigation_contract_g9a_catalog_ref_blind_spot.md`](investigation_contract_g9a_catalog_ref_blind_spot.md)  
**Checkpoint base:** tag `checkpoint-r3b` (`4608eed`)

**Workflow:** Claude implements **Slices 1→2→3 in order** + tests + report → Engineer → Cursor review → batch commit with `checkpoint-r3b` tag context if Engineer asks.

---

## 0. Why this cut

After Catalog Bind (Impl B), `design_properties.components["motors"].catalog_ref` persists the chosen SKU. Yet both Continuity and Engineering Readiness re-run a generic library search **without reading `catalog_ref`**, producing false "no tengo un motor en el catálogo" even when a valid SKU is bound (Scenario B).

Investigation confirmed:

| Issue | Detail |
|---|---|
| Dual call-site | `orchestrator.py:3585–3632` inline block is byte-identical to `engineering_readiness.resolve_motor_catalog_surface` (~180–240); orchestrator does **not** call the shared function |
| Blind spot | Neither path reads `catalog_ref`, `catalog_ref.sku`, or the bound SKU row's design-space |
| G9-B orthogonal | G9-B demotes an already-computed gap; G9-A changes whether `catalog_gap` is `None` — no double-count risk |

**Hard rules:**

- **Option B only** — fix once in `resolve_motor_catalog_surface`; orchestrator delegates; delete inline duplicate.
- Do **not** implement Option C (`bound_sku_status` typed field) — deferred to Impl C investigation.
- Do **not** add battery/propeller catalog-gap logic — motor-only by design (no equivalent gap type exists today).
- Do **not** promote Scenario C to INCOMPATIBLE or a new `GAP-*` type — reuse `GAP-MOTOR-CATALOG-UNRESOLVED` with richer evidence/wording.
- Zero weakened tests; full suite green.

---

## 1. Scenario contract (authoritative)

| # | Condition | `catalog_gap` | `GAP-MOTOR-CATALOG-UNRESOLVED` | Evidence `fact` (when gap fires) |
|---|---|---|---|---|
| A | No `catalog_ref`; library search empty | Generic message (unchanged) | Yes | `catalog_matches.empty` |
| **B** | `catalog_ref` set; SKU resolves; SKU design-space **covers** current requirements | **`None`** | **No** | — |
| **C** | `catalog_ref` set; SKU resolves; requirements **past** SKU design-space | SKU-named message (§1.1) | Yes | `bound_sku_underspec:{sku}` |
| **D** | `catalog_ref` set; SKU **not** in library | Missing-SKU message (§1.2) | Yes | `bound_sku_missing:{sku}` |
| E | `catalog_ref` cleared by G5 divergence | Falls through to A/F | Per A/F | Per A/F |
| F | Unbound motor; library search finds matches | `None` (unchanged) | No | — |

**Requirements inputs** (unchanged from today): `physical_requirements["thrust_per_motor_needed_n"]`, `kv_hint` from `motors.properties["kv_rating"]`, `prop_inch` from `current_parameters["propeller_diameter_in"]`.

**"Covers requirements" predicate** — must match `default_library.find_motors_for_requirements` filter logic exactly (investigation §5 / library.py:254–262):

- Thrust: pass if `m.max_thrust_n >= min_thrust_n` **or** `m.thrust_n >= min_thrust_n`
- KV: pass if `m.kv_min <= kv <= m.kv_max` (when `kv` hint present)
- Prop: pass if any `abs(p - prop_inch) <= 1.0` in `m.compatible_prop_inch` (when `prop_inch` present)

Factor this into a **single-motor predicate** (private helper in `library.py` preferred, e.g. `_motor_covers_requirements(m, *, min_thrust_n, kv, prop_inch) -> bool`, reused by `find_motors_for_requirements` **or** duplicated once with a comment pointing to the canonical filter — implementer's choice, but the IC acceptance bar is **byte-equivalent semantics**, not DRY for its own sake).

### 1.1 Scenario C message shape

Must **name the bound SKU** and must **not** say "no tengo un motor" as if nothing were bound.

Recommended template (Spanish, adjust wording for natural CLI flow; substance is fixed):

```text
El motor vinculado ({sku}) ya no cubre el hueco de diseño ({need}).
```

When `find_motors_for_requirements` returns alternatives for the **current** requirements, append them (reuse today's `catalog_matches` list formatting — top 5, same dict keys). When no alternatives exist either, append today's generic suffix after naming the stale SKU:

```text
…; no tengo otro motor en el catálogo que cubra ese espacio.
```

Still populate `catalog_matches` from the current-requirements search (not from the bound SKU alone) so Continuity/CTA can offer real alternatives.

### 1.2 Scenario D message shape

```text
El motor vinculado ({sku}) ya no está en el catálogo.
```

No uncaught `KeyError` from `get_motor` — use `has_motor(sku)` or try/except before lookup.

### 1.3 Bound-SKU read path

In `resolve_motor_catalog_surface`, **before** the generic empty-search gap branch:

1. Read `motors_comp = design_properties.components.get("motors")`.
2. If `motors_comp.catalog_ref` is set and `catalog_ref.family == "motor"` (or family absent — treat as motor if on motors component):
   - Resolve `sku = catalog_ref.sku`.
   - If SKU missing from library → Scenario D.
   - Else load `MotorSpec` via `get_motor(sku)`; run covers predicate → Scenario B (`catalog_gap = None`, return early with empty or informational `catalog_matches` as today for the no-search-needed path) or Scenario C (gap + alternatives search).
3. If no `catalog_ref` → existing generic search path unchanged (Scenarios A/F).

**Early-clear for Scenario B:** When bound SKU covers requirements, set `catalog_gap = None` and **skip** emitting the generic gap even if a fresh library search would return empty (the bound identity is authoritative for catalog honesty).

---

## 2. Slices

### Slice 1 — Bound-SKU-aware `resolve_motor_catalog_surface`

**Problem:** Shared function ignores `catalog_ref`; false gaps for bound motors.

**Fix:**

- Add bound-SKU branch per §1.3.
- Add single-motor covers predicate per §1.
- Extend return contract so `_motor_catalog_gaps` can emit scenario-specific evidence:
  - **Preferred:** `resolve_motor_catalog_surface` returns `(catalog_gap, catalog_matches, gap_evidence_fact: str | None)` where `gap_evidence_fact` is `None` when `catalog_gap is None`, else one of `catalog_matches.empty`, `bound_sku_underspec:{sku}`, `bound_sku_missing:{sku}`.
  - Update `_motor_catalog_gaps(req, catalog_gap, *, gap_evidence_fact="catalog_matches.empty")` to use the passed fact in `GapEvidence.fact` instead of hardcoding `catalog_matches.empty`.
  - Update `build_engineering_readiness` call site (~1020) to unpack the third value.

**Files changed:**

- `src/jarvis/knowledge/library.py` — optional `_motor_covers_requirements` helper (if chosen).
- `src/jarvis/core/engineering_readiness.py` — `resolve_motor_catalog_surface`, `_motor_catalog_gaps`, `build_engineering_readiness`.

**Tests** (extend `tests/test_engineering_readiness_gaps.py` — `_motor_spec(catalog_ref=...)` fixture already exists, unused):

- `test_gap_motor_catalog_unresolved_absent_when_bound_sku_covers` — **Scenario B**: bind `brotherhobby_avenger_2500` via `CatalogRef`, requirements within its design-space (`max_thrust_n` 11.5, kv 2500, prop 5") → no `GAP-MOTOR-CATALOG-UNRESOLVED`, `resolve_motor_catalog_surface` returns `(None, ...)`.
- `test_gap_motor_catalog_unresolved_bound_sku_underspec` — **Scenario C**: same SKU bound, inflate `thrust_per_motor_needed_n` past 11.5 (e.g. `required_thrust_n` + `motor_count` fixture like existing trigger test) → gap present, message contains SKU name, evidence fact `bound_sku_underspec:brotherhobby_avenger_2500`, message does **not** contain bare "no tengo un motor en el catálogo" without naming the bound SKU first.
- `test_gap_motor_catalog_unresolved_bound_sku_missing_from_library` — **Scenario D**: `catalog_ref=CatalogRef(family="motor", sku="deleted_motor_xyz")` → gap present, message contains "ya no está en el catálogo", evidence `bound_sku_missing:deleted_motor_xyz`, no exception.
- **Regression:** existing `test_gap_motor_catalog_unresolved_trigger` and `test_gap_motor_catalog_unresolved_absent_when_matches_found` unchanged.

**Optional thin probe** in `tests/test_catalog_bind_v1.py`:

- `test_bind_motor_catalog_gap_cleared_when_covers` — bind via `bind_motor_from_catalog`, run `resolve_motor_catalog_surface` / `build_engineering_readiness` → Scenario B end-to-end.

---

### Slice 2 — Orchestrator dedup (delegate to shared function)

**Problem:** ~48 lines duplicated in `orchestrator.build_startup_context` (~3585–3632); future drift risk.

**Fix:**

- Delete inline catalog-gap block (`orchestrator.py:3585–3632`).
- Import `resolve_motor_catalog_surface` alongside existing `build_engineering_readiness` import (~3634).
- Replace with:

```python
catalog_gap, catalog_matches, _gap_fact = resolve_motor_catalog_surface(
    project_state, physical_requirements
)
```

(Orchestrator passes `catalog_gap`/`catalog_matches` to `build_project_continuity` as today; `_gap_fact` discarded here — readiness path uses it in Slice 1.)

- Remove now-unused `from jarvis.knowledge.library import default_library` in that block **if** no other use in the function scope.

**Files changed:**

- `src/jarvis/core/orchestrator.py` — dedup only; no other behavior changes in this slice.

**Tests:**

- `test_build_startup_context_motor_catalog_gap_delegates_to_shared_resolver` — **Scenario B smoke through orchestrator**: project state with bound SKU + covering requirements → `build_startup_context(...)["motor_catalog_gap"] is None` (or whatever key the startup dict uses — match existing test patterns in `tests/test_project_continuity.py` / orchestrator tests).
- `test_build_startup_context_motor_catalog_gap_underspec_delegates` — **Scenario C smoke**: bound SKU + inflated requirements → `motor_catalog_gap` non-None, contains SKU name.
- **Regression:** any existing test that asserts on `motor_catalog_matches` shape/keys still passes.

---

### Slice 3 — Interaction regressions + full suite

**Problem:** G9-A must not regress G9-B, G5 divergence, or ERF-2 rollup semantics.

**Fix:** Tests only (no production changes unless Slice 1–2 missed a wiring bug).

**Tests:**

- **G9-B + Scenario C** (`tests/test_cli_polish.py` pattern or new probe in `tests/test_engineering_readiness_gaps.py` / `test_engineering_readiness_continuity.py`):
  - Bound SKU underspec → `catalog_gap` non-None (Scenario C).
  - **Plus** `sim_status == "pass"` and `per_motor_max_thrust_n >= thrust_per_motor_needed_n` → G9-B demotion still applies (`catalog_gap_covered_by_declared_thrust` True → catalog subsystem / `next_useful_step` does not lead with catalog gap). Gap remains in evidence; ranking demoted — same G9-B semantics, not swallowed by G9-A.
- **G5 Scenario E:** existing `test_dse_apply_diverging_thrust_clears_motor_catalog_ref` in `tests/test_catalog_bind_v1.py` must pass unchanged — after divergence clears `catalog_ref`, generic Scenario A path applies.
- **G5 dual-truth:** spot-check `tests/test_g5_dse_iterate_dual_truth.py` — no new failures.
- **ERF-2 rollup:** one smoke test that Scenario B clears `GAP-MOTOR-CATALOG-UNRESOLVED` from `build_engineering_readiness(...).gaps` and catalog subsystem verdict improves accordingly (if subsystem tests exist, extend; else add minimal probe).

**Acceptance:** Full suite green (1877+ baseline at `checkpoint-r3b`).

---

## 3. Scope boundaries

### In scope

- `catalog_ref` read on `motors` component only.
- Scenarios B, C, D logic in `resolve_motor_catalog_surface`.
- Richer `GapEvidence.fact` for C/D.
- Orchestrator dedup (Slice 2).
- Regression tests §2 + §3.

### Out of scope (do not implement)

- Option C typed `bound_sku_status` return field — candidate for Impl C.
- Option A (patch both copies without dedup).
- Battery / propeller `catalog_ref` catalog-gap equivalents.
- Changes to `bind_motor_from_catalog`, G5 `invalidate_diverged_catalog_refs`, or electrical compatibility.
- Changes to G9-B demotion predicate (`catalog_gap_covered_by_declared_thrust`).
- New gap types (`GAP-MOTOR-BOUND-STALE`, etc.).
- CLI formatter changes beyond what honest `catalog_gap` strings already surface through Continuity.

---

## 4. Acceptance criteria

1. Bound SKU covering current requirements → `catalog_gap is None`, no `GAP-MOTOR-CATALOG-UNRESOLVED` (Scenario B).
2. Bound SKU no longer covering requirements → gap with SKU-named message, not generic false "no tengo un motor" (Scenario C).
3. Bound SKU missing from library → honest missing-SKU message, no exception (Scenario D).
4. Unbound / no `catalog_ref` → today's Scenario A/F behavior unchanged.
5. `orchestrator.build_startup_context` delegates to `resolve_motor_catalog_surface`; inline duplicate removed.
6. `motor_catalog_gap` / `motor_catalog_matches` in startup context match readiness path for B/C/D (dedup smoke).
7. G9-B demotion still works when Scenario C + PASS + declared thrust covers floor.
8. G5 divergence test unchanged and passing.
9. `tests/test_cli_polish.py` G9-B tests unchanged and passing (pre-built gap strings — insulated).
10. Full suite green; zero weakened tests.

---

## 5. Decision log

| # | Decision | Rationale |
|---|---|---|
| ★1 | Option B only | Investigation §7; Engineer ratified; closes dedup debt ERF-1 flagged |
| ★2 | Single authority: `resolve_motor_catalog_surface` | Proven byte-equivalence; orchestrator already imports `engineering_readiness` |
| ★3 | Reuse `GAP-MOTOR-CATALOG-UNRESOLVED` for C/D | Keeps ERF-2 gap registry closed; honesty via message + evidence fact |
| ★4 | Scenario C = gap, not silence, not INCOMPATIBLE | Investigation §2; identity stale ≠ physics conflict |
| ★5 | Third return value `gap_evidence_fact` | Minimal wiring for `_motor_catalog_gaps`; avoids Option C typed surface |
| ★6 | Motor-only scope | No battery/prop catalog-gap computation exists to fix |
| ★7 | Covers predicate = `find_motors_for_requirements` semantics | Prevents false Scenario B clear or false Scenario C gap |

---

## 6. Review checklist (Cursor — mandatory)

1. Verify bound-SKU branch runs **before** generic empty-search gap emission.
2. Verify Scenario B clears gap even when generic search would return empty.
3. Verify Scenario C message names SKU; evidence fact `bound_sku_underspec:{sku}`.
4. Verify Scenario D uses `has_motor` / safe lookup — no `KeyError` leak.
5. Verify orchestrator inline block deleted; single call to `resolve_motor_catalog_surface`.
6. Verify G9-B tests (`test_cli_polish.py`) still pass unchanged.
7. Verify G5 `test_dse_apply_diverging_thrust_clears_motor_catalog_ref` still passes.
8. Run new G9-A tests + full suite.
9. Confirm no Option C typed fields or new gap types introduced.

---

## 7. Implementation report (Claude deliverable)

After implementation, write `.jes/artifacts/implementation_report_g9a_catalog_ref_blind_spot.md` with:

- Files changed per slice
- Scenario B/C/D probe results (one line each)
- G9-B / G5 regression confirmation
- Test count / suite result
- Any deviation from this contract (must be empty or explicitly flagged)

---

**End of contract.**
