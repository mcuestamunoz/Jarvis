# Investigation Report — Next Engineering Block (P2-2 vs G24 vs H5)

**Contract:** [`investigation_contract_next_engineering_block.md`](investigation_contract_next_engineering_block.md)
**Checkpoint base:** `checkpoint-closure-policy` / doc hygiene `73bd9fa`
**Investigator:** Claude Code
**Status:** Complete. No `src/` changes, no test changes, no version bump — investigation only, per contract §0.4.

---

## 1. Executive summary

Baseline is healthy (§2). All three candidates were traced in code, not assumed from vision docs:

- **P2-2** (Phase 2 physics continuation): P2-1's `resolve_operating_point` already computes `current_a`, `power_w`, `rpm`, `efficiency_gf_per_w` at the exact/fallback operating point — but **none of these are bridged anywhere**; `component_writers.py` only reads `thrust_n` off the result and discards the rest. Live-verified: a bound `emax_rs2205s_2300` + `hq_5045_bn` combo resolves a real `power_w=432.0`/`current_a=27.0`, while `current_parameters["motor_power_w"]` stays at the SKU's flat `max_watts=400.0` — feeding a ~7-8% error into every downstream autonomy/discharge calculation for a catalog-bound project. Low-risk, additive, no schema/UX change needed for the first cut.
- **G24** (DSE apply UX): reproduced live on this baseline exactly as documented. With a catalog-bound motor already declared, `optimiza para aumentar payload` returns a top-5 list of abstract params-only candidates (no catalog candidate even surfaces in this run); `aplica la mejor` always takes `viable[0]`; the apply clears `catalog_ref` (G5, correct) but leaves a stale `.name` — a real, live, reproducible trust-breaking bug in a core supported user action.
- **H5** (ESC catalog): confirmed **no live ASSEMBLY_READY blocker** — freeform ESC already satisfies every gap/verdict path, including the full ESC-vs-motor electrical check (`electrical_compatibility.py` reads a freeform `current_a` property, never `catalog_ref`). `CatalogRef.family` is a closed `Literal["motor","battery","propeller"]` — adding ESC reopens a Catalog V1 design lock (1A), not just an additive slice.

**Recommendation: G24-A (apply-by-index) first**, P2-2's bridging cut as an independent, low-risk secondary (can ship before or after G24, no ordering dependency between them), **H5 deferred** — no live blocker, largest scope, reopens a closed schema lock.

---

## 2. Baseline verification (`73bd9fa`, HEAD `e529270` = contract commit)

| Check | Result |
|---|---|
| `pytest tests/` | **1976 passed**, 0 failed |
| `cli_probe_requirements_closure.py` | **5/5 PASS** |
| `cli_probe_battery_catalog_bind_ux.py` | **6/6 PASS** |
| `cli_probe_closure_policy_propeller_sku.py` | **4/4 PASS + 1 optional PASS** |
| `tests/test_phase2_lookup_operating_point.py` | **16 passed** |
| Impl C / G24-relevant test files present | `test_impl_c_catalog_aware_dse.py`, `test_impl_c_catalog_dse_thrust_bridge.py`, `test_g5_dse_iterate_dual_truth.py`, `test_da2_components_delta.py`, `test_u3_dse_exploration.py`, `test_fn024_handoff_context_dse.py` |

No surprise failures. Baseline confirmed healthy — proceeding to candidate analysis.

---

## 3. Candidate A — P2-2 (Phase 2 continuation)

### 3.1 Scope box

P2-2 = §12.2+ of `PHYSICAL_PROPULSION_ENGINE_PHASE2.md`: bridging the **already-resolved** operating-point data (current, power, rpm, efficiency) into calc/electrical checks, and eventually a curated "Real World Validation Case" (2-5 real motors, 2-3 propellers, 1-2 batteries/ESCs, compare model vs manufacturer data). **Not** DSE/apply UX (G24), **not** catalog schema expansion (H5).

### 3.2 What "P2-2" means in code today (A1)

Nothing. `grep -rln "P2-2"` across `src/` returns zero hits — only docs/artifact filenames reference it. The only Phase 2 code is P2-1: `resolve_operating_point`/`ResolvedOperatingPoint` (`library.py:506-565, 567-...`).

### 3.3 What P2-1 already delivers, verified live (A2)

`ResolvedOperatingPoint` (`library.py:506-537`) is fully typed with `thrust_n`, `resolution_type`, `source_type`, `confidence`, `voltage_v`, `rpm`, `current_a`, `power_w`, `efficiency_gf_per_w`, `propeller_sku`, `fallback_only`, `source_reference`, `source_note`, `motor_sku` — this is already the §10 "OperatingPoint" data shape the vision doc asks for, populated straight from curated `operating_points[]` rows in `library/motores/_datos.json`.

`component_writers.set_motor_component` (`component_writers.py:250-330`) calls `resolve_operating_point(sku, propeller_sku=..., voltage_v=...)` and:

```python
updated_params["per_motor_max_thrust_n"] = resolved_op.thrust_n   # bridged
updated_params["propulsion_resolution"] = json.dumps({...})       # thrust_n, resolution_type,
                                                                    # source_type, confidence,
                                                                    # voltage_v, propeller_sku,
                                                                    # fallback_only, source_reference,
                                                                    # motor_sku — NOT current_a,
                                                                    # power_w, rpm, efficiency_gf_per_w
```

**Live-verified discrepancy** (reproduced this session, not assumed):

```text
MotorSpec.max_watts (flat catalog peak) for emax_rs2205s_2300:        400.0 W
resolve_operating_point(..., propeller_sku="hq_5045_bn", voltage_v=16.0):
  resolution_type = exact_operating_point
  thrust_n = 9.7086   (bridged into per_motor_max_thrust_n — correct)
  power_w  = 432.0    (NEVER bridged — motor_power_w stays 400.0)
  current_a = 27.0    (NEVER bridged; max_current_a is None on this SKU,
                        so electrical_compatibility._per_motor_current_a
                        falls back to motor_power_w/voltage = 400/16 = 25.0 A,
                        a ~7.4% underestimate of the real 27.0 A)
```

This directly corrupts `calculate_autonomy_min(battery_capacity_wh, motor_power_w × motors)` (`tools/electricity.py:25-30`, consumed via `calculation_engine.py:164-178`) and the `GAP-BATTERY-DISCHARGE-EXCEEDED`/`GAP-ESC-UNDERSIZED` checks (`electrical_compatibility.py:129-159`) for every catalog-bound propulsion project — the more accurate number is computed and then thrown away.

### 3.4 Conceptually open vs. already partially present (A3)

| Vision item | Status |
|---|---|
| §6 Operating Point (motor+prop+voltage+thrust) | ✅ delivered (P2-1) |
| §7 Power model (electrical/mechanical) | 🟡 **data exists** (`power_w`, `current_a` on `ResolvedOperatingPoint`), **not bridged** — this is the P2-2 gap, not a from-scratch build |
| §8 Thrust/validation chain | ✅ thrust delivered; power/current validation not wired to real OP data (uses flat catalog fields instead) |
| §9 Data provenance/confidence | ✅ `source_type`/`confidence`/`source_reference` already on every row and on `ResolvedOperatingPoint` — genuinely done, just not surfaced beyond `propulsion_resolution`'s JSON blob |
| §12.2 Real World Validation Case | ❌ not started — needs a small curated dataset + a comparison/divergence report, a new, larger piece of work |
| ESC in the OP model (§5.4/§6) | ❌ `resolve_operating_point`'s signature has no `esc_sku` parameter at all — ESC validation lives entirely in `electrical_compatibility.py`, independent of P2-1/P2-2 |

### 3.5 Prerequisites (A4)

| Prerequisite | Status |
|---|---|
| Catalog bind (motor+propeller+battery) | ✅ (Catalog V1 + IC 2) |
| `resolve_operating_point` | ✅ (P2-1) |
| Electrical compatibility checks | ✅ (ERF-2) — reads `motor_power_w`/estimated current, not OP-resolved current (the gap) |
| ESC catalog (H5) | **Not required** — `electrical_compatibility._esc_current_a` already reads a freeform `current_a` property; the P2-1 OP model never included ESC in its own resolution signature |
| G24 fixed | **Not required for the bridging cut** — orthogonal code path (`component_writers.py`, not `design_explorer.py`) |

### 3.6 New capability if P2-2 ships first (A5)

A catalog-bound propulsion project's `estado`/autonomy/discharge numbers become the **real, curated manufacturer-test values** instead of a flat catalog peak — directly closes a quantifiable (~7-8% in the verified example) accuracy gap for every project using P2-1's exact/fallback resolution path. The "Real World Validation Case" (a later, separate cut) would let the Engineer point at a specific real combo and see Jarvis's number next to the manufacturer's, with the delta shown honestly.

### 3.7 Scope / risk (A6)

- **First cut (bridging):** `component_writers.py` (bridge `power_w`/`current_a`/`rpm` into `current_parameters`, likely new keys — e.g. `motor_current_a_resolved`, or overwrite `motor_power_w` only when an exact/fallback OP exists, mirroring the existing `per_motor_max_thrust_n` precedent) + `electrical_compatibility.py` (`_per_motor_current_a` prefers OP-resolved current when present) + `calculation_engine.py` (no change needed if `motor_power_w` itself is corrected upstream). **No** schema change, **no** new UX, **no** new library data.
- **Second cut (Real World Validation Case):** new, small, curated dataset + a comparison report/probe — larger, more open-ended, genuinely new scope.
- Forbidden overlaps: must not touch P2-1's `resolve_operating_point` matching rule itself (locked, IC 2 already proved re-triggering it carelessly can regress `exact`→`fallback`), must not touch DSE ranking (G24 territory) or catalog schema (H5 territory).

### 3.8 Reusable fixtures/probes (A7)

`tests/test_phase2_lookup_operating_point.py` already asserts `resolved_op.power_w`/`current_a` values from `resolve_operating_point` directly — extending it to assert the **bridged** `current_parameters` values is a natural, small addition, not a new test file. `cli_probe_requirements_closure.py`'s Fixture-2-shape pattern is reusable for an "autonomy number changed after bridging" probe.

### 3.9 Blockers (A8)

None. P2-2's bridging cut has zero unmet prerequisites and is independent of G24/H5.

---

## 4. Candidate B — G24 (DSE apply / catalog row selection)

### 4.1 Scope box

G24 = the **apply** step of `optimiza para <goal>` → `aplica la mejor` always applies `viable[0]`, and the **ranking** step (why an abstract params-only candidate outranks a real catalog SKU when physics is otherwise equal) is a documented, separate, intentionally-unchanged layer (Impl C ★6). Two layers, kept distinct per ★3.

### 4.2 Reproduced on baseline (B1) — YES

Live repro this session (fresh project, `sunnysky_r2305_2500` catalog-bound via `bind_motor_from_catalog`+`set_motor_component`, then a real `optimiza para aumentar payload` + `aplica la mejor` turn through `orchestrator.handle_user_text`, zero LLM calls, zero fixture forcing):

```text
Exploración completada para «maximizar carga útil» — 5 configuración(es) viable(s):
  1. motores=6, empuje/motor (N)=11.2 → score=3.557   (abstract, no [sku])
  2. empuje/motor (N)=15 → score=3.162                 (abstract)
  3. motores=8 → score=3.162                            (abstract)
  4. carga útil (kg)=1.2, motores=6 → score=2.399       (abstract)
  5. empuje/motor (N)=11.2 → score=2.371                (abstract)

> aplica la mejor
  per_motor_max_thrust_n: 7.5 → 11.25
  motor_count: 4 → 6

post-apply catalog_ref: None          ← cleared (G5, correct)
post-apply name: sunnysky_r2305_2500  ← STALE, still reads like a real SKU
post-apply thrust_n: 11.25 (source='calculated')  ← diverged number under a stale label
```

In this run, **no catalog candidate even reached the top 5** (a stricter symptom than the original finding, which showed one at `#5` — state-dependent on whether another SKU beats the abstract scores for this specific goal/project shape). The core defect — apply always takes `#1`, identity silently destroyed, `.name` left stale — reproduces exactly regardless.

### 4.3 Apply path today (B2)

`orchestrator._handle_apply_exploration` (`orchestrator.py:3534-3576`): `best = exploration.viable[0]` — literal, hardcoded. `grep`-confirmed: **zero** occurrences of any "apply by index"/"aplica la N" pattern anywhere in `orchestrator.py` or `intent_resolver.py` — the feature does not exist, not a routing bug hiding an existing one.

### 4.4 Generation path (B3)

Impl C's catalog branch genuinely works — confirmed by `test_catalog_branch_generates_bound_motor_candidate_aumentar_payload`/`test_full_explore_apply_path_with_real_catalog_candidate` (`test_impl_c_catalog_aware_dse.py`) and "Strategy 3" in `design_explorer.py:499+` (`explore()`, comment at line 614: `# Impl C Strategy 3: real catalog motor candidates already generated`). Generation is not the gap — visibility/selection is.

### 4.5 Ranking layer (B4)

`_score_candidate` (`design_explorer.py:354-375`) scores purely on simulated physics outcome (`autonomy_min`, `safety_margin_ratio × payload_kg`, `-total_mass_kg`, `safety_margin_ratio`) — **no term anywhere references `catalog_ref`, cost, or feasibility**. An abstract `EXPLORATION_GRIDS` delta (e.g. `per_motor_max_thrust_n_factor: 1.5`) can scale to any value with zero real-world cost, so it will generally out-score a real SKU capped at what that specific product actually delivers. Confirmed intentional and locked: `_build_label_components`'s own docstring says *"`_score_candidate` is unchanged (★6 locks scoring)"*.

### 4.6 G5 interaction (B5)

`_handle_apply_exploration` (`orchestrator.py:3607-3626`): for a params-only candidate, `invalidate_diverged_catalog_refs` runs immediately after `_apply_delta`, before `sync_motors_component_from_params` — clears `catalog_ref` on divergence (correct, G5's job) but never touches `.name` (by design — `.name` isn't its job either). The frankenstein `.name` behavior is the **documented, accepted shape** of G5, not a new bug — G24's job is to stop the user from landing there involuntarily, not to change what happens once they do.

### 4.7 Gap class (B6)

**UX/product debt in an existing, supported, advertised action** (`"Di «aplica la mejor» para aplicar la configuración #1"` is literally printed to the user every time). This is not a missing capability — Impl C already generates real catalog candidates — it's that the one verb available to act on the explore results (`aplica la mejor`) cannot reach them when they don't rank first, which per §4.5 is close to "never, once thrust is already declared."

### 4.8 Fix options (B7)

| Option | Effort | Notes |
|---|---|---|
| **G24-A — apply by index** (`"aplica la 5"` / `"aplica #5"`) | Small | New intent pattern + `_handle_apply_exploration(index: int = 0)`. Doesn't touch scoring (★6-safe). Matches the finding doc's own Option A. |
| **G24-B — ranking tiebreak/preference for catalog rows** | Medium | Touches the locked `_score_candidate` — would need an explicit new ★ to unlock, since Impl C deliberately fixed this scoring shape. Higher review risk. |
| **G24-C — honest CTA only** (warn "#1 is abstract, will drop your SKU; say 'aplica la 5' to keep it") | Small, but depends on G24-A shipping first to have something to point at | Copy-only if paired with A; standalone it's incomplete (still no way to act on the warning). |

### 4.9 Impact on Closure / readiness (B8) — re-verified, NOT a blocker

`_bom_sku_resolved` (`project_closure.py`) computes `sku_resolved` from a live `catalog_ref` re-check — a post-G24-apply frankenstein motor (`catalog_ref=None`, `.name` stale) correctly reports `sku_resolved=False`, never `[sku]` (Impl D's own non-negotiable rule, confirmed still enforced). `classify_component` doesn't care about `.name` shape either — a stale-but-complete motor spec still reaches `defined`/PASS. **G24 does not block `ASSEMBLY_READY`** — confirmed consistent with the Project Closure investigation's own conclusion (★9), re-verified against current code rather than re-cited from memory.

### 4.10 Existing test coverage (B9) — the gap is visible in the tests themselves

`test_full_explore_apply_path_with_real_catalog_candidate` (`test_impl_c_catalog_aware_dse.py`) runs a real `explore()` + real `"aplica la mejor"` turn, then **explicitly forces** the catalog candidate to the front:

```python
# Force the picked catalog candidate to the front so "aplica la mejor"
# applies it deterministically, without depending on how it ranked.
exploration2 = exploration.model_copy(update={"viable": [catalog_candidates[0]]})
```

No test in the suite exercises the actual bug shape: real `explore()` output, thrust already declared, catalog candidate present but **not** in position 0, `"aplica la mejor"` applied as-is. This is the exact probe/test an IC needs to add as its gate.

---

## 5. Candidate C — H5 (ESC catalog + bind)

### 5.1 Scope box

H5 = ESC as a **catalog SKU** (`catalog_ref` + bind path), not the ESC acquisition/compatibility system, which already exists and works freeform.

### 5.2 ESC as-is (C1)

- **Acquisition:** freeform only, via `infer_components`/`_handle_component_description`; `OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS = {"esc"}` (`acquisition_target.py:98`) lets a user declare `"esc 20a"` out-of-band mid-wizard (FN-ESC, ERF-2-era, unrelated to catalog).
- **Writer:** no dedicated `set_esc_component` exists (unlike motors/battery/propellers/frame). `apply_components_delta` (`component_writers.py:449-452`) routes ESC through the generic `set_control_component` (same one used for flight_controller/sensors) as a fallback for "extra keys" — this already writes an arbitrary `ComponentSpec` (including any `catalog_ref` it carries) straight to `design_properties.components["esc"]`, no calc bridge.
- **Readiness:** `_esc_presence`/`_esc_vs_motor` (`electrical_compatibility.py:223-251`) read `classify_component`'s completeness tier and a freeform `current_a` `PropertyValue` — never `catalog_ref`.

### 5.3 What works without ESC catalog (C2)

Everything currently gated on ESC: `_electronics_evidence` subsystem PASS (needs only non-low completeness, `engineering_readiness.py`), `GAP-ESC-UNDEFINED`/`GAP-ESC-UNDERSIZED` (compare a freeform-declared `current_a` against per-motor current draw), BOM `declared`/`defined` bucket routing. All freeform-only, all already live.

### 5.4 Schema delta (C3)

- `CatalogRef.family: Literal["motor","battery","propeller"]` (`action_schema.py:139`) → must add `"esc"`. This is the one genuine "closed design lock" reopening: Physical Component Catalog V1's decision **1A** explicitly scoped `catalog_ref` to these three families; adding a fourth is a schema change to a document marked `DESIGN CLOSED (Engineer 2026-08-12)`, not an additive slice — it needs its own explicit Engineer ratification, not just an IC.
- New `ESCSpec` dataclass in `library.py` (mirrors `BatterySpec`/`PropellerSpec`: `manufacturer`, `continuous_current_a`, `peak_current_a`, `voltage_min`/`voltage_max`, `protocol`, `mass_g` per vision §5.4) + `_load_escs`/`get_esc`/`list_escs`/`has_esc`/`find_escs`.
- New `bind_esc_from_catalog` in `catalog_bind.py` — thin, mirrors `bind_propeller_from_catalog` (no calc-bridge complexity since ESC data doesn't feed `calculation_engine.py`).
- `_bom_sku_resolved` (`project_closure.py`) needs a fourth `if family == "esc": return default_library.has_esc(sku)` branch (same one-line class of fix as IC 3's propeller branch).
- **Writer layer is cheap**, contrary to first appearance: `set_control_component` already generically handles "write spec (with whatever `catalog_ref` it carries) to `components[key]`" — no new writer function needed, unlike battery which needed the `battery_capacity_wh` bridge.

### 5.5 Data delta (C4)

Zero rows exist today (`library/esc/` doesn't exist). Minimum honest seed (★2: no invented SKUs) — a handful of real, sourced ESC models (manufacturer datasheet current ratings), same discipline as the 10-entry battery seed. This is real sourcing work, not a mechanical copy of an existing pattern.

### 5.6 UX delta (C5)

Would mirror the battery pattern exactly (IC 2 precedent: `_offer_component_esc_catalog`, `_apply_component_esc_catalog_pick`, `_try_start_assisted_esc_help`, `esc_suggestions` session field) — a well-worn, low-risk shape to copy, **if** the schema/data work lands first.

### 5.7 Live blocker (C6) — NO

No fixture, gap, or verdict anywhere requires ESC to be catalog-bound. Confirmed identical to the Closure investigation's ★7 conclusion, re-verified against current `engineering_readiness.py`/`electrical_compatibility.py` rather than cited from memory.

### 5.8 Capability unlocked (C7)

Evidence-strength only — a `[sku]` BOM line and a real current/voltage rating pulled from a curated source instead of user-declared free text. No electrical check gets *more capable*; it gets a more trustworthy input for a check that already runs today.

### 5.9 Scope vs. ERF-2's own deferral (C8)

ERF-2's investigation deferred H5 explicitly as "not needed for ERF-2 MVP" — still valid; nothing in this investigation found new pressure to reopen it. The deferral reasoning (freeform is sufficient for the compatibility checks ERF-2 needed) still holds today, one arc later.

### 5.10 Dependency (C9)

Independent of G24 (DSE scoring for ESC candidates was never in scope — `EXPLORATION_GRIDS` has no ESC axis) and independent of P2-2 (P2-1/P2-2's OP resolution signature has no `esc_sku` parameter at all — ESC never entered that model). H5 can be sequenced anywhere; it simply isn't urgent anywhere.

---

## 6. Comparison matrix

| Criterion | P2-2 (bridging cut) | G24 (apply-by-index) | H5 (ESC catalog) |
|---|---|---|---|
| Gap live (repro on baseline) | Yes (quantified accuracy gap) | Yes (live-reproduced this session) | No |
| New user-visible capability | Partial (more accurate numbers, not new actions) | Yes (preserve SKU through explore→apply) | Partial (evidence-strength only) |
| Prerequisites satisfied | Yes | Yes | Partial (schema lock reopening required) |
| Leverage (unlock downstream work) | Medium (every catalog-bound propulsion project) | Medium (every DSE user with a bound motor) | Low (symmetry only) |
| Implementation scope | Short (first cut) / Large (Validation Case) | Short | Medium–Large |
| Architectural risk | Low | Low–Medium | Medium (schema lock) |
| Continuity with P2-1 / Closure / Impl C | Direct continuation of P2-1 | Direct continuation of Impl C | Same shape as IC 2, but new family |
| Product value (Engineer-facing) | Accuracy/trust in numbers | Trust in a core supported action (no silent data loss) | Completeness/symmetry |
| Test/probe gate clarity | Clear, extends existing P2-1 test file | Very clear — existing test already documents the workaround | Clear but needs new data-sourcing work first |
| Version-milestone fit (note only) | `0.3.x`-shaped (bridging is additive) | `0.3.x`-shaped (bugfix/UX-completion) | `0.4.0`-shaped (schema-lock reopening + new family) |

**Interpretation:** P2-2 and G24 are both low-risk, high-clarity, prerequisite-satisfied cuts that extend an already-closed arc without touching schema. H5 is qualitatively different — it is the only candidate that reopens a *closed design lock* (Catalog V1 decision 1A) and the only one with zero live blocker justifying urgency. Between P2-2 and G24, G24's gap is an active correctness/trust break in a supported action (data loss a user did not ask for), while P2-2's gap is a quiet accuracy shortfall (no crash, no lost state) — a meaningful difference in urgency even though both are small, safe cuts.

---

## 7. Recommendation

| Field | Answer |
|---|---|
| **Primary next block** | **G24-A — DSE apply-by-index** |
| **Rationale** | G24 is the only candidate where a user, using a normal, advertised, supported command (`"aplica la mejor"`), has their own already-established state (a catalog-bound motor) silently and irreversibly destroyed with no way to prevent it — confirmed live-reproducible on this exact baseline. Its fix (apply-by-index) does not touch the locked ranking layer (★6), does not touch physics, does not touch catalog schema, and the regression gate is nearly free — an existing test already shows the exact scenario the fix needs to cover, currently worked around by forcing state instead of testing it. P2-2's gap is real and worth closing but is a quiet accuracy shortfall, not a trust-breaking action; there is no dependency forcing one before the other, but G24's user-journey break is the higher-urgency of the two low-risk options. |
| **Deferred candidates** | **P2-2** (bridging cut) — independent, no prerequisite on G24; recommend as the **secondary** cut, sequenced right after or in parallel with G24 since neither touches the other's files. **H5** — defer; no live blocker, reopens a closed schema lock, needs its own explicit Engineer ratification of the 1A design-lock change before any IC is drafted, and needs real ESC data sourced first (★2). |
| **Suggested investigation → IC sequence** | 1: **IC "G24-A Apply By Index"** (this recommendation's primary). 2: **IC "P2-2 Operating Point Bridge"** (bridging cut only — not the full Real World Validation Case, which is its own future investigation). 3: H5 stays in the deferred queue, not sequenced. |
| **Version note (recommendation only)** | Both G24-A and the P2-2 bridging cut are additive/bugfix-shaped — consistent with a `0.3.x` patch tag, not a `0.4.0` milestone. H5, if and when it proceeds, is the more natural `0.4.0` candidate (new catalog family + schema lock reopening) — Engineer's call, not decided here. |
| **Out of scope for the first IC** | Ranking/scoring changes (G24-B), any CTA/copy work that assumes G24-A hasn't shipped (G24-C), the full Real World Validation Case dataset/harness, anything ESC-catalog-shaped, any P2-1 `resolve_operating_point` matching-rule change. |

---

## 8. ★ Decisions for Engineer

**★1 — Primary next block:** ratify **G24-A** (apply-by-index), or override. *Recommended: ratify.*

**★2 — G24 fix scope:** apply-by-index only (Option A) for this IC; ranking tiebreak (Option B) and CTA-only (Option C) explicitly deferred/folded into A as noted in §6.8. *Recommended: A only, this cut.*

**★3 — P2-2 first-cut scope:** the bridging cut (§3.7 first cut) only — bridge `power_w`/`current_a`/`rpm` from `ResolvedOperatingPoint` into `current_parameters`/`electrical_compatibility`. The Real World Validation Case (§3.4, a curated dataset + divergence report) is explicitly **not** included and would need its own future investigation. *Recommended: bridging cut only, as the secondary IC after G24-A.*

**★4 — H5:** defer entirely (no schema-only spike either) until a live blocker or explicit product need appears — the schema-lock reopening (1A) deserves its own dedicated Engineer ratification when it happens, not a byproduct of this comparison. *Recommended: defer, re-evaluate in a future cycle.*

**★5 — Version bump timing:** after G24-A (and optionally P2-2's bridging cut) both PASS review and probe — a single `0.3.x` checkpoint/tag covering both, not two separate version bumps for two small, related cuts. *No strong recommendation on exact patch number — Engineer's call.*

---

## 9. Suggested IC outline(s) (bullets only — no code)

**IC "G24-A — DSE Apply By Index"**
- New intent pattern recognizing `"aplica la N"` / `"aplica #N"` / `"aplica la N-ésima"` alongside the existing `"aplica la mejor"`.
- `_handle_apply_exploration` gains an index parameter (default `0`, preserving today's exact behavior for the unqualified command).
- Regression: the existing `_score_candidate`/`EXPLORATION_GRIDS` ranking is completely untouched — same ordering, only the *choice of which viable entry to apply* changes.
- Gate: a new test mirroring `test_full_explore_apply_path_with_real_catalog_candidate` but **without** forcing `viable` — real `explore()` output where a catalog candidate ranks below `#1`, applied via its real index, `catalog_ref` survives.
- CLI probe: reproduce this report's §4.2 live repro, then show `"aplica la 5"` (or wherever the catalog candidate actually lands) preserving `catalog_ref`.

**IC "P2-2 — Operating Point Bridge"**
- Bridge `resolved_op.power_w`/`current_a`/`rpm` into `current_parameters` when an exact/fallback OP is resolved (mirrors the existing `per_motor_max_thrust_n` bridge precedent in `component_writers.set_motor_component`).
- `electrical_compatibility._per_motor_current_a` prefers the OP-resolved current over the `motor_power_w/voltage` estimate when present.
- Regression: `legacy_estimate` path (no OP match) stays byte-identical — this is the same ★-locked regression contract P2-1 itself used.
- Gate: extend `test_phase2_lookup_operating_point.py` to assert the bridged `current_parameters` values, plus a probe showing `estado`'s autonomy/discharge numbers change for a catalog-bound project (before/after comparison, like this report's §3.3 live numbers).

---

## 10. CLI probe sketch(es) for the recommended path

```text
G24-A probe:
  1. Create project, catalog-bind a motor (thrust already declared).
  2. "optimiza para aumentar payload" -> real explore(), record viable[] order.
  3. If no catalog candidate in top-5, bind a scenario where one does appear
     (adjust goal/constraints) -> confirm its index N > 1.
  4. "aplica la N" -> catalog_ref survives, .name matches the applied SKU,
     no divergence-clear fires (since we applied the SKU itself, not an
     abstract delta).
  5. "aplica la mejor" (no index) on the same exploration -> unchanged
     behavior (viable[0], divergence-clear still fires as today) — regression.

P2-2 bridge probe:
  1. Bind motor+propeller+battery to a combo with a real exact_operating_point
     row (e.g. emax_rs2205s_2300 + hq_5045_bn).
  2. Before fix: current_parameters["motor_power_w"] == SKU max_watts (400.0).
  3. After fix: current_parameters["motor_power_w"] (or a new resolved-current
     field) == resolved_op.power_w (432.0) / current_a == 27.0.
  4. "calcular" -> autonomy_min reflects the corrected power draw.
  5. Regression: an unbound/freeform motor's motor_power_w is untouched.
```

---

## 11. Explicit "do not implement yet" queue

- G24-B (ranking tiebreak) and G24-C (CTA-only) — folded into future consideration, not this cut.
- P2-2's Real World Validation Case (curated dataset + divergence report) — separate future investigation.
- H5 (ESC catalog, schema + data + UX) — deferred, needs its own Engineer ratification of the 1A schema-lock reopening.
- Frame SKU catalog — same class as H5, out of this comparison per contract §0.4, untouched.
- Conversation Engine / Step D — out of scope, untouched.
- Any `_score_candidate`/`EXPLORATION_GRIDS` scoring change — locked (★6, Impl C), not reopened by this investigation.
- Version bump / tag creation — Engineer's call after ★ ratification, not part of this investigation.

---

**End of report.**
