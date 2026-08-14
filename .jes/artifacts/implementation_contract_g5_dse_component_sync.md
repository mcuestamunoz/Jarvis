# Implementation Contract — G5 Fix (DSE → component sync)

**Project:** Jarvis  
**Date:** 2026-08-14  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Bug fix — state dual-truth (params-only DSE vs ComponentSpec).  

**Closes:** G5 🔴 — [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md)  
**Investigation (mandatory):** [`.jes/artifacts/investigation_report_g5_dse_iterate_dual_truth.md`](investigation_report_g5_dse_iterate_dual_truth.md) — PASS  
**Review:** [`.jes/artifacts/investigation_review_g5_dse_iterate_dual_truth.md`](investigation_review_g5_dse_iterate_dual_truth.md)  

**Checkpoint base:** `checkpoint-f1-reducir-payload` · commit `d9bf75f`  

**Explicitly deferred:** G3 · G1/G2 · H5 · Catalog Impl C · Continuity/BOM copy for DSE-derived source tags · MIRRORED PARAM global refactor  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews. **No commit/push unless Engineer asks.**

---

## 0. Intent

After a params-only DSE apply elevates motor fields in `current_parameters`, those values must **survive** any subsequent physical iterate (or DEFINE_MISSING recalculation) that does not intentionally change motors.

```text
DSE params-only apply
  motor_count 4→6, per_motor_max_thrust_n 20→30
        ↓
SYNC design_properties.components["motors"]  ← THIS CONTRACT
        ↓
unrelated iterate (safety_factor)
        ↓
resolve_propulsion_parameters → same 6 / 30  (no cliff)
```

Today: component stays stale → `resolve_propulsion_parameters` + `PhysicalOverride.apply_to` silently reverts to 4 / 20.

---

## 1. Fix direction (Engineer lock — Option A)

**Sync `design_properties.components["motors"]` when a params-only DSE apply changes propulsion fields.**

Package as a **shared pure helper** (same shape as Impl B's `invalidate_diverged_catalog_refs`):

```text
sync_motors_component_from_params(components, params) -> components
```

Called from `orchestrator._handle_apply_exploration` **after** params-only delta is resolved and **before** calculate/save — when `best.components_delta` is empty (params-only path).

**Do NOT** change `actions/iterate.py` or `param_definition_session.py` callers of `resolve_propulsion_parameters` in this contract — they become correct once their input (the component) stops going stale.

**Do NOT** implement Option B (skip overwrite on diverge) or Option D (narration-only).

---

## 2. Sync rules

When params-only DSE apply results in `canonical_params` that differ from `components["motors"]` on any of:

| Param | Component property |
|---|---|
| `motor_count` | `properties["motor_count"].value` |
| `per_motor_max_thrust_n` | `properties["thrust_n"].value` (when `output_magnitude == "thrust_n"`) |
| `per_actuator_torque_nm` | equivalent torque property if present (latent — cover if structure exists; no-op if absent) |

**Required:**

1. Update the corresponding property values on the motors `ComponentSpec`.  
2. Preserve other properties (`power_w`, `kv_rating`, `weight_g`, …).  
3. If `catalog_ref` is set and the synced number diverges from SKU truth → call existing `invalidate_diverged_catalog_refs` (already on this path) so identity still clears — do not leave a lying SKU.  
4. Prefer a distinct `source` tag if one already exists in the schema (e.g. `"derived"` / `"declared"`); if inventing a new source enum requires schema churn, keep `"declared"` and document in report as deferred Continuity concern. **Do not** invent a new architectural subsystem for provenance.

If `components["motors"]` is absent → no-op (honest).

---

## 3. IN SCOPE

| # | Work |
|---|---|
| 1 | Shared sync helper (new module or extend `catalog_bind.py` / small `component_sync.py` — prefer near existing bind helpers) |
| 2 | Wire into `_handle_apply_exploration` params-only branch |
| 3 | Promote G5 repro: remove `xfail` from `test_unrelated_numeric_iterate_reverts_dse_elevated_motor_params` → plain assert (must **pass**) |
| 4 | Keep the two control tests; add any needed unit tests for the helper |
| 5 | Report |

---

## 4. OUT OF SCOPE

| Forbidden |
|---|
| Changing `resolve_propulsion_parameters` / `PhysicalOverride.apply_to` semantics |
| Gating the override on `draft.variable` (Option B style) |
| G3 handoff explore |
| H5 / G1 |
| Catalog Impl C |
| Narration-only Continuity message as the sole fix |
| Global writer rewrite |

---

## 5. Tests (required)

| ID | Case |
|---|---|
| T1 | Promote existing G5 xfail → **pass** (DSE elevate → unrelated `safety_factor` iterate → motor_count/thrust **unchanged**) |
| T2 | Control: DSE apply itself still elevates params (existing) |
| T3 | After DSE params-only elevate, `components["motors"]` properties match elevated params |
| T4 | Unrelated iterate after sync: `resolve_propulsion_parameters` path does not cliff |
| T5 | If SKU-bound motor + DSE diverges thrust → `catalog_ref` still cleared (Impl B regression) |
| T6 | Full suite green; zero weakened assertions |

---

## 6. Acceptance criteria (Cursor review)

**PASS** only if:

1. G5 cliff closed: DSE-elevated motor params survive unrelated iterate.  
2. Sync helper is the fix locus; iterate/DEFINE_MISSING callers untouched (or only trivial import if shared).  
3. G5 xfail removed / promoted to green regression.  
4. Impl B catalog invalidation still green.  
5. No G3/H5/Impl C scope creep.

---

## 7. Deliverables

1. Code + tests  
2. `.jes/artifacts/implementation_report_g5_dse_component_sync.md`  
3. Update cli_findings G5 → 🟢 when Engineer confirms  

**Do not commit or push.**

---

## 8. Queue after G5 fix

```text
G5 fix PASS
        ↓
G3 — explore explícito vs handoff
        ↓
G1/G2 + H5 design
        ↓
UX catálogo → Impl C → BOM
```
