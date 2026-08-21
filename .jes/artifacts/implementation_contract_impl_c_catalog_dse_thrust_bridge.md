# Implementation Contract — Impl C Follow-up: Catalog DSE Thrust Bridge

**Project:** Jarvis  
**Date:** 2026-08-21  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR CLAUDE

**Type:** Narrow residual fix — propagate `ComponentSpec.motors.properties.thrust_n` → `current_parameters["per_motor_max_thrust_n"]` on the component-driven path so catalog-DSE evaluate/apply use the SKU’s real thrust and preserve `catalog_ref` on SKU-switch.

**Parent IC:** [`.jes/artifacts/implementation_contract_impl_c_catalog_aware_dse.md`](implementation_contract_impl_c_catalog_aware_dse.md) — generation cut implemented in working tree  
**Parent review:** [`.jes/artifacts/implementation_review_impl_c_catalog_aware_dse.md`](implementation_review_impl_c_catalog_aware_dse.md) — **PASS WITH NOTES** (Note A = this residual)  
**Parent report:** [`.jes/artifacts/implementation_report_impl_c_catalog_aware_dse.md`](implementation_report_impl_c_catalog_aware_dse.md)

**Workflow:** Claude implements on top of the **uncommitted** Impl C generation cut → tests + report → Cursor review → **single commit/checkpoint for complete Impl C** only if Engineer asks.

---

## 0. Estado y relación con Impl C

```text
Base:
  Impl C Catalog-Aware DSE — generation cut, actualmente en working tree,
  SIN commit / SIN checkpoint.

Este IC NO sustituye Impl C.
Completa el gap descubierto en Implementation Review (Note A).

Objetivo:
  generation + correct physical thrust propagation + SKU-switch identity
  = Impl C product-complete.

Al final (Engineer):
  un único commit/checkpoint de Impl C completo
  (generation cut + este bridge), no dos commits separados.
```

**Hard process rules:**

- Do **not** commit the generation cut alone.
- Do **not** reopen Impl C ★1–★7 (candidate shape, Strategy 3, goal scope, scoring, etc.).
- Do **not** redesign DSE, add ranking preference for catalog candidates, or change `_score_candidate`.
- Minimum change that closes the thrust gap. If a contradiction with locked surfaces appears → **STOP** (see §9).

---

## 1. Problema confirmado

```text
ComponentSpec.motors.properties.thrust_n   (SKU-authoritative)
        ↓
apply_components_delta() / set_motor_component()
        ↓
❌ per_motor_max_thrust_n  NOT updated
        ↓
calculation / simulation consume stale value or None
```

`set_motor_component` today bridges `motor_power_w`, `motor_count`, `motor_kv_rating`, `motor_mass_kg` — **never** `per_motor_max_thrust_n`. Both paths below are broken:

| Path | What goes wrong |
|---|---|
| **Explore evaluation** | Catalog candidate SKU B is scored with prior SKU A’s thrust (or `None` → `can_fly=False`) |
| **Real component-driven apply** | Apply writes SKU B’s spec, then G5 `invalidate_diverged_catalog_refs` sees params thrust ≠ spec thrust → clears `catalog_ref`; `sync_motors_component_from_params` may overwrite `thrust_n` back to the stale params value |

**Bridge rule (locked):**

> The bridge must propagate the SKU’s **real** `thrust_n`. It must **not** calculate, estimate, invent, or substitute thrust via factors, heuristics, or library re-lookups beyond what is already on the `ComponentSpec`.

---

## 2. Decisiones bloqueadas (Engineer 2026-08-21)

| ★ | Decision |
|---|---|
| **★1** | `motors.properties["thrust_n"].value` on the applied `ComponentSpec` is the sole source for `current_parameters["per_motor_max_thrust_n"]` when that property is present |
| **★2** | This IC’s production intent is the **component-driven** path (explore evaluation via `apply_components_delta` + `_handle_apply_exploration` when `components_delta` is non-empty). Params-only DSE path must remain unchanged |
| **★3** | Do **not** change `_score_candidate` |
| **★4** | Do **not** change `ExplorationCandidate` schema |
| **★5** | Do **not** change G9-A (`resolve_motor_catalog_surface`) |
| **★6** | Do **not** change G5 (`invalidate_diverged_catalog_refs` / `sync_motors_component_from_params` / call order) unless a demonstrable contradiction appears → **STOP** |
| **★7** | Do **not** change `catalog_bind.py` unless **STOP** |
| **★8** | Do **not** introduce scoring/ranking preference for catalog candidates |

**Observation rule (not a scoring change):**

> If after the bridge, catalog candidates still rarely appear in top-5 under the existing scoring formula, **do not** modify scoring in this IC. Record observation in the Implementation Report. First restore correct physics; ranking policy is a separate Engineer decision.

---

## 3. Production scope

### 3.1 Preferred surface (locked recommendation)

Implement the bridge inside **`set_motor_component`** in `component_writers.py` (the single writer both explore and apply already call).

**When to bridge:**

```text
IF motors ComponentSpec has properties["thrust_n"] with a non-None value
THEN current_parameters["per_motor_max_thrust_n"] = float(thrust_n.value)
```

**When not to bridge:**

- Spec has no `thrust_n` property (e.g. synthetic `COMPONENT_VARIATION_RULES` power_w-only motors) → leave `per_motor_max_thrust_n` untouched (today’s behavior).
- Params-only DSE candidates never call `set_motor_component` for a new thrust from a catalog spec → unchanged.

**Do not** invent thrust from `power_w`, KV, or library lookup inside the writer.

Optional: only bridge when `output_magnitude == "thrust_n"` **or** when `thrust_n` property is present — if both conditions are available, prefer bridging whenever `thrust_n` is present (catalog binds already set `output_magnitude="thrust_n"`). Document choice in report. Semantics must match ★1.

### 3.2 Explore evaluation (must follow for free)

Because `DesignExplorer.explore()` already evaluates catalog candidates via:

```text
apply_components_delta(normalized_state, comp_delta)
  → set_motor_component(...)
  → calc / sim / score
```

fixing `set_motor_component` is sufficient for:

```text
catalog candidate SKU B
    ↓
apply_components_delta
    ↓
per_motor_max_thrust_n = SKU B thrust_n
    ↓
calculate → simulate → score
```

**Do not** add a parallel bridge inside `design_explorer.py`.

### 3.3 Real apply (must follow for free)

`_handle_apply_exploration` already does:

```text
apply_components_delta(...)          # ← bridge must land here
invalidate_diverged_catalog_refs(...)
sync_motors_component_from_params(...)
```

With a correct bridge **before** invalidate:

- new `per_motor_max_thrust_n` matches new `thrust_n` → invalidate is a **no-op** for motors → `catalog_ref` survives
- sync sees matching values → no frankenstein overwrite

**Do not** reorder G5 calls. **Do not** skip invalidate for catalog candidates.

### 3.4 Explicitly out of production scope

| Forbidden | Why |
|---|---|
| Changes to `_score_candidate` / top-5 preference | ★3 / ★8 |
| `ExplorationCandidate` / new schema fields | ★4 |
| G9-A | ★5 |
| G5 logic / order changes without STOP | ★6 |
| `catalog_bind.py` without STOP | ★7 |
| Battery thrust/capacity bridge redesign | out of scope |
| C3 battery catalog | deferred |
| Impl D / BOM | later |
| Removing abstract `EXPLORATION_GRIDS` | separate decision |

---

## 4. SKU-switch — primary acceptance chain

This is the **critical** product proof:

```text
SKU A bound (catalog_ref set; per_motor_max_thrust_n = A.thrust_n)
      ↓
explore (aumentar_payload or mejorar_estabilidad)
      ↓
catalog candidate SKU B (B ≠ A; components_delta["motors"].catalog_ref.sku == B)
      ↓
apply SKU B (via _handle_apply_exploration — real path)
      ↓
catalog_ref.sku == B
thrust_n == B.thrust_n
per_motor_max_thrust_n == B.thrust_n
motor_count unchanged
      ↓
iterate unrelated (e.g. safety_factor)
      ↓
catalog_ref.sku == B
thrust_n == B.thrust_n
per_motor_max_thrust_n == B.thrust_n
motor_count unchanged
```

---

## 5. Viability (explore physics)

Deliberate fixture:

```text
Project without prior per_motor_max_thrust_n  OR  with stale thrust
+ catalog candidate whose SKU thrust is sufficient for can_fly
        ↓
after bridge: per_motor_max_thrust_n = that SKU's thrust_n
        ↓
can_fly == True
        ↓
candidate ∈ exploration.viable   (not only exploration.candidates)
```

This proves the bridge fixes **evaluation**, not only post-apply persistence.

---

## 6. Scoring — hard constraint

> If after the bridge, catalog candidates still do not appear in the CLI top-5 under existing `_score_candidate`, **do not** modify scoring in this IC.

Report the observation. Ranking policy is deferred.

CLI acceptance (§8) requires a catalog candidate to be **present and selectable without forcing `viable[0]`** only if natural ranking puts one in `.viable` **and** the user path can apply it. Minimum hard gate for product-complete:

- A catalog candidate with correct thrust can be in `.viable` (physics).
- When that candidate is applied (including via a test that selects it by SKU identity from `.viable` / `.candidates` without rewriting thrust), identity + thrust survive.

For the **CLI probe specifically** (§8): **no forcing / rewriting `viable[0]`**. The probe must use the natural explore result. If after bridge no catalog SKU appears in the printed top-5, the probe must still prove via automated assertions on `exploration.viable` / apply of a catalog member of `.viable` if present; if none is viable, document as physics/scoring observation and ensure unit tests §7 cover SKU-switch + viability fixtures that **do** place a catalog candidate in `.viable` by fixture design (not by mutating scores).

**Clarification for implementer:**  
- **Unit/integration tests** may construct fixtures so a catalog SKU is physically viable and assert it lands in `.viable`.  
- **CLI probe** must not splice a non-viable / non-top candidate into `viable[0]` to fake a pass. If the natural top-5 after a real explore contains a catalog SKU, apply that one. If not, probe reports observation + still runs apply against a catalog candidate taken from `exploration.viable` when any catalog entry is viable (order preserved from explore — pick the highest-scoring catalog viable, without inventing scores). If zero catalog entries are viable after bridge on the probe project, **STOP and report** fixture inadequacy — do not force.

---

## 7. Tests

New / extended file: `tests/test_impl_c_catalog_dse_thrust_bridge.py` (or extend `tests/test_impl_c_catalog_aware_dse.py` — prefer a **new** focused file for this residual).

| Test | Assert |
|---|---|
| `test_component_driven_catalog_thrust_bridges_to_params` | `set_motor_component` / `apply_components_delta` with catalog-bound spec → `per_motor_max_thrust_n == thrust_n.value` |
| `test_catalog_dse_evaluation_uses_candidate_thrust` | Explore catalog candidate for SKU B while project has SKU A thrust → evaluated params / calc available thrust reflect **B**, not A |
| `test_catalog_native_sku_switch_preserves_identity_and_new_thrust` | Full §4 chain through `_handle_apply_exploration` |
| `test_catalog_native_sku_switch_survives_unrelated_iterate` | §4 after `safety_factor` iterate |
| `test_real_catalog_candidate_can_be_viable_with_correct_thrust` | Fixture where SKU thrust enables flight → that catalog candidate ∈ `.viable` |
| `test_first_bind_c2_regression_still_preserves_catalog_ref` | Prior C2 first-bind behavior still green |
| `test_params_only_diverging_apply_still_clears_catalog_ref` | Regression: `test_dse_apply_diverging_thrust_clears_motor_catalog_ref` semantics unchanged |
| G5 suite | `tests/test_g5_dse_iterate_dual_truth.py` green |
| G9-A suite | existing G9-A tests green |

Also keep full `tests/test_impl_c_catalog_aware_dse.py` green (generation cut). The previous honest skip on C5 full explore-apply may be **promoted to a real pass** if bridge + fixture allow — preferred; if still skipped solely due to scoring/top-5 (not thrust), convert skip reason or replace with the new viable-membership test above.

---

## 8. CLI probe acceptance

Update `scripts/cli_probe_impl_c_catalog_dse.py` (or add `scripts/cli_probe_impl_c_thrust_bridge.py` that covers steps 3–7 on **one** project with a prior bound SKU).

**Hard gates (no soft generation-only pass for step 4):**

```text
1–2) (optional continuity) bind SKU A via acquisition — catalog_ref set, G9-A Scenario B
3) optimiza para aumentar payload  (or mejorar estabilidad)
4) exploration contains ≥1 catalog candidate; if any catalog candidate is in .viable,
   it was evaluated with that SKU's thrust (assert via candidate calc/sim or label+[sku])
5) apply a catalog viable candidate WITHOUT forcing a non-viable into viable[0]
   (see §6 clarification)
6) estado: catalog_ref == applied SKU; per_motor_max_thrust_n == that SKU thrust;
   no false GAP-MOTOR-CATALOG-UNRESOLVED when SKU covers requirements
7) iterate safety_factor → catalog_ref + thrust + motor_count unchanged
```

> **Forbidden:** selecting/forcing an arbitrary candidate into `viable[0]` that was not already in `exploration.viable` to make the probe pass.

---

## 9. STOP rules

If implementing the bridge appears to require:

- changing G5 order or invalidate semantics, or
- changing `catalog_bind.py`, or
- changing scoring / `ExplorationCandidate`, or
- inventing thrust not present on the `ComponentSpec`,

then:

```text
STOP
  ↓
document contradiction in Implementation Report
  ↓
do not expand architecture
  ↓
Engineer decision
```

Do **not** silently expand scope.

---

## 10. Exit criterion (Impl C product-complete)

> **Impl C is product-complete only when** a project with a catalog-bound motor can explore an alternative SKU, evaluate it using that SKU’s physical thrust, apply it while preserving `catalog_ref`, keep that thrust after an unrelated iterate, and demonstrate via tests + CLI that a catalog candidate can be viable without splicing a non-viable candidate into `viable[0]`.

Until this exit criterion is met: **no** `checkpoint-impl-c` / no claim that Impl C is CLOSED as product.

---

## 11. Implementation Report (required)

Create: `.jes/artifacts/implementation_report_impl_c_catalog_dse_thrust_bridge.md`

Sections:

1. Summary  
2. Files changed (expect: `component_writers.py` primary; possibly tiny call-site comments only elsewhere)  
3. Bridge rule implemented (exact condition)  
4. Confirm G5 order / G9-A / scoring / `catalog_bind` untouched (or STOP note)  
5. SKU-switch evidence  
6. Viability evidence  
7. Scoring observation (top-5 catalog visibility — report only)  
8. Tests + suite count  
9. CLI probe evidence  
10. Ready for single Impl C commit? (yes/no + residual)

---

## 12. Acceptance (Cursor review)

**PASS** if:

1. Bridge lands in `set_motor_component` (or STOP-justified equivalent that both explore and apply share).  
2. Explore evaluation uses candidate SKU thrust.  
3. SKU-switch apply preserves `catalog_ref` + new thrust; iterate survives.  
4. At least one fixture proves a catalog candidate ∈ `.viable` via correct thrust.  
5. Params-only diverge + G5 + G9-A + generation-cut tests green.  
6. CLI probe respects §8 (no fake `viable[0]`).  
7. No scoring / schema / forbidden-file drift.

**FAIL** if: thrust invented; scoring changed; G5 reordered without STOP; probe fakes apply; generation cut committed separately against process rules.

---

**End of contract.**
