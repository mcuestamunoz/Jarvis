# Investigation Contract — Impl C Catalog-Aware DSE

**Project:** Jarvis  
**Date:** 2026-08-20  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_impl_c_catalog_aware_dse.md`

**Status:** READY FOR CLAUDE

**Type:** Audit + design investigation — DSE must propose **catalog-constrained** candidates and preserve **SKU identity through apply**.

**Checkpoint base:** tag **`checkpoint-g21-g23`** · commit `8dcc151`

**Design authority (read-only):**
- [`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`](../../docs/PHYSICAL_COMPONENT_CATALOG_V1.md) — §6 Phase plan, exit criteria Impl C
- [`.jes/artifacts/implementation_contract_catalog_foundation_v1.md`](implementation_contract_catalog_foundation_v1.md) — Impl A/B boundaries
- [`.jes/artifacts/implementation_contract_g5_dse_component_sync.md`](implementation_contract_g5_dse_component_sync.md) — apply/sync/invalidate order

**Prerequisites (CLOSED — do not re-open without cause):**
- **Impl A** — Catalog Foundation (loaders, `ComponentSpec.catalog_ref` schema)
- **Impl B** — Catalog Bind (`bind_motor_from_catalog`, motor/battery mass rules)
- **G5** — DSE params-only apply → `sync_motors_component_from_params` + `invalidate_diverged_catalog_refs`
- **G9-A** — bound-SKU-aware gap computation (Scenarios B/C/D)
- **G21/G22** — acquisition catalog bind UX + single list/gap authority
- **G23** — FN-015 removed

**Blocks:** Impl D (Create→BOM) — do **not** design BOM consumption in this investigation.  
**Workflow:** Investigate → report → Engineer ratifies ★ decisions → Cursor writes Implementation Contract → Claude implements. **No production fix in this contract.**

---

## 0. Context

### 0.1 Problem statement

After Catalog Bind (Impl B), a user can pick a real motor SKU (`catalog_ref = { family, sku }`). Acquisition, Continuity, and Engineering Readiness now treat bound SKUs honestly (G9-A).

**Design Explorer does not.** Today `DesignExplorer.explore()` generates candidates from:

1. **`EXPLORATION_GRIDS`** — abstract param deltas (`per_motor_max_thrust_n_factor`, `motor_count_delta`, `battery_capacity_wh_factor`, …)
2. **`COMPONENT_VARIATION_RULES`** — synthetic `ComponentSpec` rows with invented numeric properties and **no** `catalog_ref`

When the user applies a DSE candidate:

| Apply path | What happens to SKU identity |
|---|---|
| **Params-only** (`params_delta` non-empty) | `invalidate_diverged_catalog_refs` **clears** `catalog_ref` when thrust/battery diverge — honest, but anti-buildable |
| **Component-driven** (`components_delta` non-empty) | Spec replaces component with freeform declare shape — **`catalog_ref=None` by construction** |

**Symptom (expected today):** User binds `sunnysky_r2305_2500` → `explora opciones` / `optimiza para payload` → `aplica la mejor` → motor is no longer SKU-bound, or candidate was never a real SKU.

**Impl C exit criterion (Design §6):**

> *DSE candidates are catalog-constrained and preserve identity through apply.*

### 0.2 Why now

All bind/honesty prerequisites are checkpointed (`checkpoint-g21-g23`). Building catalog-aware DSE on unresolved acquisition or gap logic would compound dual-truth debt. G9-A Option C (`bound_sku_status` typed field) was explicitly deferred here — investigate whether Impl C needs it.

### 0.3 Target flow (to-be — investigation must validate feasibility)

```text
goal_key + project_state
        ↓
DesignExplorer (catalog branch)
        ↓
ComponentLibrary.find_* / get_*  →  N real SKUs
        ↓
For each SKU: bind_*_from_catalog → ComponentSpec + catalog_ref
        ↓
apply_components_delta → calc/sim → score → ExplorationCandidate
        ↓
User: aplica la mejor
        ↓
orchestrator._handle_apply_exploration
        ↓
components["motors"].catalog_ref persists · params match SKU projection
        ↓
G9-A readiness: Scenario B (sufficient bound SKU) — no false catalog gap
```

---

## 1. What Claude must investigate

### 1.1 Current DSE pipeline audit (mandatory)

Trace the full explore → apply → persist path. Produce a sequence diagram or step table.

| Step | File / symbol | Question to answer |
|---|---|---|
| Explore entry | `orchestrator._handle_explore` | How is `goal_key` resolved? Handoff from Goal Plan / FN-024? |
| Candidate generation | `DesignExplorer.explore` | Exact order: params grid vs component grid; dedup/cache behavior |
| Params grid | `EXPLORATION_GRIDS`, `_apply_delta` | Which goals touch motors/battery? Which deltas invalidate bound SKU on apply? |
| Component grid | `COMPONENT_VARIATION_RULES`, `_build_component_candidates_for_goal` | Which specs are synthetic? Any path sets `catalog_ref` today? |
| Scoring | `_score_candidate` | Same function for all candidate types? Biases toward higher thrust/power? |
| Apply | `orchestrator._handle_apply_exploration` | Params-only vs `components_delta` branch; order of `invalidate_diverged` → `sync_motors` |
| Post-apply iterate | `actions/iterate.py`, `component_sync.py` | Does a catalog-native apply survive next iterate turn? |
| Readiness | `resolve_motor_catalog_surface` (G9-A) | After catalog-DSE apply, which G9-A scenario (B/C/D) fires? |

**Deliverable:** annotated call graph + table mapping each `goal_key` to current candidate sources (params / component / both).

### 1.2 Catalog API inventory (mandatory)

List every `ComponentLibrary` method relevant to DSE candidate generation. For each: inputs, outputs, deterministic guarantees, and whether acquisition already uses it.

Minimum methods to cover:

- `get_motor` / `get_battery` / `get_propeller`
- `find_motors_for_requirements` (D8)
- `find_motors_by_kv`
- `match_motor_propeller`
- `bind_motor_from_catalog` / `bind_battery_from_catalog` (`catalog_bind.py`)

**Question:** Can DSE reuse the **same** motor search surface as acquisition (`build_motor_catalog_suggestions` / G22 single authority), or must it call `ComponentLibrary` directly? Document duplication risk.

### 1.3 Goal × family matrix (design input)

For each `goal_key` in `GOAL_LABELS`, classify:

| goal_key | Touches motors? | Touches battery? | Touches frame/structure? | Catalog candidate feasible in v1? |
|---|---|---|---|---|
| `mejorar_autonomia` | ? | ? | ? | ? |
| `aumentar_payload` | ? | ? | ? | ? |
| `reducir_payload` | ? | ? | ? | ? |
| `reducir_masa` | ? | ? | ? | ? |
| `mejorar_estabilidad` | ? | ? | ? | ? |

Recommend **which goals enter Impl C v1** and which stay on abstract grids (with explicit rationale).

### 1.4 Candidate shape options (mandatory — 2–3 options)

Today `ExplorationCandidate` carries:

```python
params_delta: dict
components_delta: dict[str, ComponentSpec]
generation_metadata: dict | None  # reserved v2
```

Investigate and compare options for catalog-native candidates:

| Option | Shape | Apply path | Pros | Cons |
|---|---|---|---|---|
| **A** | Populate `components_delta` with `bind_motor_from_catalog(...)` output | Existing component branch | Reuses G5 apply path | Must ensure `catalog_ref` not stripped |
| **B** | New field e.g. `catalog_bindings: list[CatalogRef]` + minimal delta | New apply branch | Explicit identity | Schema + orchestrator churn |
| **C** | `generation_metadata` carries SKU; writers bind at apply time | Deferred bind | Smaller explore() diff | Identity not in candidate until apply — risky |

For each option: files touched (estimate), test surface, interaction with `invalidate_diverged_catalog_refs`, and whether G5 sync still needed.

**One option must be minimal diff; one must be most correct long-term.**

### 1.5 Catalog grid strategy (mandatory — 2–3 options)

How should catalog candidates be enumerated?

| Strategy | Description | Risk |
|---|---|---|
| **Parallel branch** | Keep `EXPLORATION_GRIDS`; add `CATALOG_EXPLORATION_RULES` per goal | Dual authority during migration |
| **Replace motor-related grid entries** | Remove thrust/power factor entries; catalog-only for motor goals | Regression on unbound projects |
| **Hybrid** | Catalog branch when `library` has matches; else fallback to abstract grid | Complexity; honest messaging needed |

For motor catalog enumeration specifically:

- Filter source: project requirements (`physical_requirements.thrust_per_motor_needed_n`, kv, prop diameter)?
- Include/exclude currently bound SKU?
- Cap: top-N (acquisition uses ~5?) — combinatorics if motor_count also varies
- Generic/is_generic motors: sort last per Design §8?

### 1.6 Apply + identity preservation (critical)

Audit `orchestrator._handle_apply_exploration` (~3204–3260) and `catalog_bind.invalidate_diverged_catalog_refs`.

Answer explicitly:

1. If candidate is built via `bind_motor_from_catalog` and applied through `apply_components_delta`, does `catalog_ref` survive end-to-end today? (Expected: yes — confirm.)
2. Should catalog-native candidates **skip** `invalidate_diverged_catalog_refs` (identity by construction)?
3. When params-only grid still runs in parallel, does apply order need a discriminator (`generation_metadata.source = "catalog"`)?
4. Battery: same questions for `bind_battery_from_catalog` if battery enters v1 scope.

Reference G5 order lock:

```text
invalidate_diverged_catalog_refs  (needs stale component for true divergence)
        ↓
sync_motors_component_from_params
```

Catalog-native apply must not break this for **mixed** projects (bound battery + catalog motor candidate, etc.).

### 1.7 Interaction with G9-A scenarios

After catalog-DSE apply, map expected readiness behavior:

| Post-apply state | G9-A scenario | Expected gap? |
|---|---|---|
| Applied catalog motor SKU meets requirements | B | No false unresolved gap |
| Applied SKU underspec for new requirements | C | Gap with honest message |
| Explore proposed SKU but user didn't apply | — | No state change |
| Catalog branch empty (no library match) | A or F | Honest "no SKU covers space" — explore should say so |

Does Impl C need G9-A **Option C** (`bound_sku_status` typed field) for DSE labeling/ranking, or is message-level honesty enough?

### 1.8 Unbound vs bound project behavior

| Project state | Recommended explore behavior |
|---|---|
| No motor / no `catalog_ref` | Catalog candidates from library search; abstract grid fallback? |
| Bound motor, explore payload | Replace motor with higher-thrust SKUs? Or also vary motor_count via params? |
| Bound motor, explore autonomía | Motor efficiency SKUs vs battery SKUs — combo or single-family? |

Document combinatoric explosion limits (motor SKU × motor_count delta × battery SKU).

### 1.9 Scoring fairness

`_score_candidate` for `aumentar_payload` = `safety_margin_ratio * payload_kg`. A higher-thrust SKU may always win.

Investigate:

- Is that acceptable for v1 (real SKUs ranked by physics outcome)?
- Need normalization (score per SKU tier, penalize overspec)?
- Label UX: should candidate `label` include SKU name for CLI list?

### 1.10 Cache / dedup hazard

`DesignExplorer` caches by `frozenset(params.items())` — TODO in code notes two different `ComponentSpec`s can collide.

For catalog candidates: does cache key need component identity (`catalog_ref.sku`)? Quantify impact if ignored.

### 1.11 Test inventory + proposed probes

List existing tests touching DSE / explore / apply:

- `tests/test_design_explorer*.py` (if any)
- `tests/test_g5_*` / component sync
- `tests/test_g21_g22_*`
- `tests/test_g9a_*` / readiness
- `tests/test_catalog_bind*.py`
- R3 preempt + explore soft-interrupt

Note fixtures assuming abstract grids.

**Proposed CLI probe (for future IC acceptance — document only, do not implement):**

```text
1) New project → definir propulsion → ayúdame a elegir → pick SKU #1
2) estado → confirm catalog_ref set, G9-A Scenario B
3) explora opciones / optimiza para aumentar payload
4) List shows ≥1 candidate with real SKU in label
5) aplica la mejor
6) estado → same or upgraded catalog_ref; no GAP-MOTOR-CATALOG-UNRESOLVED if SKU sufficient
7) iterate unrelated param → motor_count/thrust/catalog_ref unchanged (G5 regression)
```

### 1.12 Slice recommendation

Propose ordered implementation slices for the Implementation Contract (bullets only — **no full IC**):

Example structure (investigator may revise):

| Slice | Scope | Exit criterion |
|---|---|---|
| C1 | Motor catalog candidates for `aumentar_payload` + `mejorar_estabilidad` | Explore lists real SKUs |
| C2 | Catalog-native apply path + identity preservation | Apply keeps `catalog_ref` |
| C3 | Battery catalog for `mejorar_autonomia` (optional) | Same pattern |
| C4 | Deprecate competing abstract motor grid entries | No dual authority |
| C5 | Integration tests + CLI probe script | Documented PASS |

---

## 2. Scope boundaries

### In scope

- Full audit §1.1–1.12
- 2–3 design options each for candidate shape (§1.4) and grid strategy (§1.5)
- G9-A / G5 / G21 interaction analysis
- Test inventory + CLI probe specification
- Slice recommendation + ★ decisions for Engineer
- Estimate blast radius (files, tests, regressions)

### Out of scope (do not implement)

- Any `src/` production changes
- Any new tests (investigation only)
- Impl D (BOM / Create→BOM)
- Phase 2 Physical Propulsion Engine (operating points)
- Propeller catalog pick UX
- H5 ESC catalog
- Library JSON seed expansion
- Conversation Engine / LLM SKU selection
- Full removal of all abstract `EXPLORATION_GRIDS` (investigate yes; implement only via future IC)
- `bound_sku_status` implementation (investigate need only)

---

## 3. Output format

Single artifact: `.jes/artifacts/investigation_report_impl_c_catalog_aware_dse.md`

Required sections:

1. **Executive summary** (≤15 lines)
2. **Current pipeline audit** — diagram + goal × source table
3. **Catalog API inventory**
4. **Goal × family matrix** with v1 recommendation
5. **Candidate shape options** (A/B/C) + trade-offs
6. **Grid strategy options** + trade-offs
7. **Apply + identity analysis** — answers to §1.6
8. **G9-A / G5 / G21 interaction notes**
9. **Unbound vs bound behavior matrix**
10. **Scoring + cache notes**
11. **Test inventory + CLI probe spec**
12. **Recommended approach** (investigator preference + reasoning)
13. **★ Decisions for Engineer** (numbered, each with options)
14. **Suggested Implementation Contract outline** (slices, acceptance criteria, out-of-scope — bullets only)

---

## 4. Hard constraints for any future IC

These are locked regardless of investigation outcome:

- **LLM never chooses or invents SKU** — catalog enumeration is deterministic via `ComponentLibrary`.
- **No second JSON reader** — all catalog reads through `knowledge/library.py`.
- **Never fabricate a catalog match** — empty search → honest gap, not synthetic SKU.
- **Bound SKU must not show false "no tengo un motor"** after catalog-native apply when SKU meets requirements (G9-A Scenario B).
- **G5 order preserved** — `invalidate_diverged` before `sync_motors` on any apply path that still needs it.
- **G9-A / G21 single authority** — do not introduce a third motor list/gap source.
- **Design Explorer stays read-only** — explore does not mutate project state or disk.
- **Backwards compatibility** — unbound projects must not regress silently; if abstract grids remain, document when each path fires.
- **Zero weakened tests** in eventual implementation.

---

## 5. Acceptance (Cursor investigation review)

**PASS** if report answers all §1 questions, includes ≥2 options for shape + grid strategy, and delivers actionable ★ decisions + slice outline.

**FAIL** if inconclusive, proposes LLM catalog selection, collapses Impl C into Impl D, or includes production code changes.

---

## 6. Queue after investigation

```text
Investigation PASS
        ↓
Engineer ratifies ★1–★N
        ↓
Cursor: implementation_contract_impl_c_catalog_aware_dse.md
        ↓
Claude implements → Cursor review → CLI probe → checkpoint
        ↓
Impl D (Create→BOM)
```

---

**End of contract.**
