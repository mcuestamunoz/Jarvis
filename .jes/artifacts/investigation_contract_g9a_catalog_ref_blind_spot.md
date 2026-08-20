# Investigation Contract — G9-A Catalog-Ref Blind Spot

**Project:** Jarvis  
**Date:** 2026-08-20  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Output:** `.jes/artifacts/investigation_g9a_catalog_ref_blind_spot.md`

**Status:** READY FOR CLAUDE

**Type:** Audit + design investigation — catalog-gap computation ignores bound `catalog_ref` on motors (Continuity + ERF readiness surface).

**Checkpoint base:** tag `checkpoint-r3b` (`4608eed`)

**Related (closed, do not re-open without cause):**
- **G9-B** — CLI Polish S1: demote `motor_catalog_gap` as `next_useful_step` when PASS + declared thrust covers floor (ranking bug, not data-source bug).
- **Impl B** — `catalog_ref` binding on pick/confirm (identity persists on component).

---

## 0. Context

After Catalog Bind (Impl B), a motor picked from the library carries `ComponentSpec.catalog_ref = { family, sku }`. The binding is durable on `design_properties.components["motors"]`.

Yet Continuity and Engineering Readiness still compute motor catalog gaps **from scratch** every call using only:

- `physical_requirements["thrust_per_motor_needed_n"]`
- inferred `kv_rating` from motor component properties
- `propeller_diameter_in` from `current_parameters`

They never ask: *"Is there already a bound SKU, and does that SKU satisfy (or partially satisfy) the current design space?"*

**Symptom (CLI):** User binds `sunnysky_r2305_2500` (or similar). After DSE apply or payload change, requirements grow. Panel still shows:

```text
Catálogo: Necesitas empuje ≥ X N/motor, ~YKV, hélice ~Z";
         no tengo un motor en el catálogo que cubra ese espacio.
GAP-MOTOR-CATALOG-UNRESOLVED
```

…even though a specific SKU is already bound and may still be the correct (or best available) identity for the BOM.

**Why now:** G9-B fixed **over-weighting** of an already-computed gap against PASS states. G9-A fixes **how the gap is computed** — the remaining catalog honesty debt before Impl C (catalog-aware DSE).

---

## 1. What Claude must investigate

### 1.1 Dual call-site audit (mandatory)

Map **both** places that compute `catalog_gap` / `catalog_matches`:

| Call site | Location | Consumer |
|---|---|---|
| Inline in `build_startup_context` | `orchestrator.py` ~3585–3632 | `motor_catalog_gap`, `motor_catalog_matches` → Continuity, CLI `estado` |
| `resolve_motor_catalog_surface` | `engineering_readiness.py` ~180–240 | `GAP-MOTOR-CATALOG-UNRESOLVED` in readiness rollup |

For each:

1. Confirm they are still byte-for-byte equivalent (or document drift).
2. List every input field read and every field **not** read (especially `catalog_ref`, `catalog_ref.sku`, bound motor thrust from SKU row).
3. Trace output consumers: `build_project_continuity`, `build_engineering_readiness`, CLI formatters, gap ranking.

Produce a table:

| Field on `motors` component | Read by gap computation? | Used for |
|---|---|---|
| `catalog_ref` | ? | |
| `catalog_ref.sku` | ? | |
| `properties.kv_rating` | yes | kv_hint |
| `properties.thrust_n` | ? | |
| … | | |

### 1.2 Bound-SKU scenarios (data contract)

Enumerate **concrete scenarios** and what the honest UX should be for each. At minimum:

| # | Scenario | Expected gap? | Expected evidence / CTA |
|---|---|---|---|
| A | No motor / no `catalog_ref` | Yes (if library search empty) | Current behavior |
| B | `catalog_ref` set, SKU row exists, SKU meets current requirements | **No** catalog-unresolved gap | BOM shows SKU; maybe silence or PASS note |
| C | `catalog_ref` set, SKU row exists, SKU **underspec** for new requirements (thrust/KV/prop) | ? | Gap, warning, or INCOMPATIBLE? |
| D | `catalog_ref` set, SKU row deleted/missing from library JSON | ? | Honest "bound SKU unknown" |
| E | `catalog_ref` cleared by G5 invalidation after DSE diverge | Yes | Current re-search behavior |
| F | Generic/unbound motor with declared thrust but no SKU | Yes | Current behavior |

**Critical:** Scenario C is the unresolved design question from the original G9 audit — *"bound-but-underspec'd SKU → gap, warning, or silence?"* Claude must propose a **recommended default** with reasoning, not leave it open.

### 1.3 Relationship to ERF-2 / existing gaps

Audit interaction with:

- `GAP-MOTOR-CATALOG-UNRESOLVED` (`engineering_readiness.py` `_motor_catalog_gaps`)
- `GAP-PROP-MOTOR-MISMATCH` (if bound SKU thrust ≠ declared)
- `GAP-BOM-INCOMPLETE-COMPONENT:motors`
- G9-B demotion guard in `project_continuality.py` (PASS + declared thrust covers floor)

Answer: if G9-A clears `catalog_gap` when SKU is bound-and-sufficient, does readiness/catalog subsystem verdict change correctly? Any double-count or contradiction?

### 1.4 Dedup / single authority

ERF-1 §6.1 noted `resolve_motor_catalog_surface` was meant to become the single authority; orchestrator still keeps an inline duplicate.

Investigate:

- Can G9-A fix land **only** in `resolve_motor_catalog_surface` with orchestrator delegating to it (recommended)?
- Blast radius of dedup vs fix-in-place in both sites.
- Existing tests that would break if orchestrator stops inlining.

### 1.5 Design options

Propose **2–3 concrete options** for catalog_ref-aware gap computation.

For each option specify:

- When is `catalog_gap` None vs non-None?
- How is the bound SKU validated (library lookup by `catalog_ref.sku`)?
- What happens when requirements drift past bound SKU limits?
- Files touched (estimate).
- Tests needed.
- Risks (false silence, stale SKU label, regression on G9-B).

One option must be **minimal** (smallest diff). One must be **most correct long-term** (single authority + full scenario matrix).

### 1.6 Test inventory

List existing tests that touch catalog gap / motor catalog surface:

- `tests/test_cli_polish.py` (G9-B)
- `tests/test_engineering_readiness_*.py`
- `tests/test_project_continuity.py`
- Any catalog bind tests

Note which fixtures assume the current blind behavior and would need updating.

---

## 2. Scope boundaries

### In scope

- Audit of both catalog-gap call sites.
- Scenario matrix + data contract recommendation.
- ERF-2 / Continuity / G9-B interaction analysis.
- Dedup recommendation.
- 2–3 design options with trade-offs.
- Test inventory + proposed probes.

### Out of scope (do not implement)

- Any `src/` changes.
- Any new tests (investigation only).
- Impl C (catalog-aware DSE candidates).
- Impl D (BOM).
- Library JSON seed changes.
- Propeller/battery `catalog_ref` (motor-only unless trivially same pattern — document only).
- G9-B re-open or ranking changes.

---

## 3. Output format

Single artifact: `.jes/artifacts/investigation_g9a_catalog_ref_blind_spot.md`

Sections:

1. Dual call-site audit table + drift note
2. Field-read matrix (`motors` component → gap computation)
3. Scenario matrix (A–F) with recommended UX per scenario
4. ERF-2 / Continuity / G9-B interaction notes
5. Dedup recommendation (single authority or not)
6. Design options (2–3, with trade-offs)
7. Test inventory + proposed regression probes
8. Recommendation (investigator's preferred option + reasoning)
9. Suggested Implementation Contract outline (slices, acceptance criteria — **no full IC**, just bullets for Engineer)

---

## 4. Hard constraints for any future IC

These are locked regardless of which option is chosen:

- **Never fabricate a catalog match** — if SKU lookup fails, say so honestly.
- **Bound SKU with valid `catalog_ref` must not show "no tengo un motor en el catálogo"** when that SKU meets current requirements (Scenario B).
- **G9-B demotion behavior must not regress** — PASS + declared thrust covers floor still demotes gap from `next_useful_step`.
- **G5 invalidation contract unchanged** — DSE diverge still clears stale `catalog_ref`.
- **Single authority preferred** — if dedup is feasible within G9-A scope, prefer one function both orchestrator and readiness call.
- **Zero weakened tests.**

---

**End of contract.**
