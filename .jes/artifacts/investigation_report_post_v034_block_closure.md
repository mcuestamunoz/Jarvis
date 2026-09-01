# Investigation Report — Post-v0.3.4 Block Closure Capability

**Contract:** `.jes/artifacts/investigation_contract_post_v034_block_closure.md`
**Investigator:** Claude Code
**Baseline:** tag `v0.3.4` / `checkpoint-motor-op-voltage-coherence` · commit `a563fe7` — verified: `git diff --stat a563fe7 HEAD -- src/` is **empty** (HEAD `dd92809` differs only in `docs/`, `.jes/state/`, and one probe script; `src/` is byte-identical). All citations below are valid against current HEAD.
**Date:** 2026-09-01

---

## Executive summary

Jarvis can reach a **real, non-fabricated, honestly-gapped `ASSEMBLY_READY`** end-to-end for one motor/propeller/battery/ESC combo (`sunnysky_r2205_2500` + `gf_5045x3` + `lipo_4s_1500mah` + freeform ESC), and honestly **refuses** it for an incompatible one (same SKUs, motor_count 2→4, discharge exceeded → `NOT_ASSEMBLY_READY`, `GAP-BATTERY-DISCHARGE-EXCEEDED`, `HIGH`). `ASSEMBLY_READY` is **provably insufficient** as a block-closure claim (§Gate B.3): it is a 9-subsystem global conjunction with no block-scoped counterpart, and 8 of 9 subsystems share one identical, non-subsystem-specific `VALIDATED` boolean (`ctx.sim_status=="pass"`). The one genuinely block-specific, real-physics concept in the codebase is `electrical_compatibility`'s COMPATIBLE checks — these are strong and already sufficient to ground an honest B-PROP-ENERGY closure claim. **Hypothesis (A) is supported**: closure looks derivable from existing signals plus a missing block-scoped rollup + VALIDATED-conflation fix, not a new physics/compatibility subsystem. No Gate D candidate (ESC catalog, battery data curation, OP density, G24-C, FN-R, C-108, G1, C-081) is BLOCKING for B-PROP-ENERGY; the one true structural (non-density) gap is that **ESC has no catalog family at all**, which blocks only B-BOM's ESC line reaching `sku_resolved`. Gate F recommends **Block Closure before Catalog Foundation** — every Foundation-adjacent candidate resolved to ENHANCING/structural-but-narrow, not BLOCKING. Two new findings surfaced that were not anticipated by the contract: (1) the compatible reference case is **fragile to catalog composition** — only one motor/battery-voltage alignment in the current library reaches `manufacturer_test` tier; (2) a **live regression**: `"definir bateria <sku>"` / `"cambia la bateria a <sku>"` on an already catalog-bound battery silently destroys `catalog_ref` and reintroduces the G27-class 6S→6Wh misparse, on the `define_missing_params` code path (distinct from the wizard path G27 hardened) — new regression evidence per ★4, not a reopening of the closed G27 arc.

---

## 0. Baseline verification

| Check | Result |
|---|---|
| `git diff --stat a563fe7 HEAD -- src/` | **empty** — zero `src/` drift from tag `v0.3.4` |
| `git diff --stat a563fe7 HEAD` (all) | 12 files, all `docs/`, `.jes/state/engineering_state.json`, `scripts/cli_probe_impl_d_sku_bom.py` (probe hardening only) |
| Full suite (`pytest -q`) | **2036 passed**, 0 failed |
| `scripts/cli_probe_p2_2_operating_point_bridge.py` | 6/6 PASS |
| `scripts/cli_probe_battery_catalog_bind_ux.py` | 6/6 PASS |
| `scripts/cli_probe_dse_motor_op_dual_truth.py` | 6/6 PASS |
| `scripts/cli_probe_closure_policy_propeller_sku.py` | 4/4 PASS (+1 optional) |
| `scripts/cli_probe_requirements_closure.py` | 5/5 PASS |
| `scripts/cli_probe_g21_g22_post_checkpoint.py` | 3/3 PASS |
| `scripts/cli_probe_impl_d_sku_bom.py` | 4/4 PASS |

Baseline is clean. All findings below are against this exact state.

---

## Gate A — Existing closure capability

### Reference case: why the contract's suggested SKUs fail, and what was used instead

The contract's example combo (`sunnysky_r2305_2500` / `hq_5045_bn` / `lipo_6s_10000mah`) **cannot reach `exact_operating_point`**: `sunnysky_r2305_2500` has no `operating_points[]` at all (`library/motores/_datos.json:107-114`). Of 8 motors carrying `operating_points`, only two have real bench data: `emax_rs2205s_2300` (`:165-225`) and `sunnysky_r2205_2500` (`:226-255`). `emax_rs2205s_2300`'s exact row sits at `voltage_v=16.0` (`:193`); `resolve_operating_point` (`library.py:567-660`) matches within `±0.05V` (`library.py:503`) of the query voltage, which is always `battery.nominal_voltage` (`component_writers.py:122-149`, `:337`). Every 4S battery in the library is `nominal_voltage=14.8` exactly — none is within 0.05V of 16.0/16.8. **`emax_rs2205s_2300` is structurally unreachable at manufacturer_test tier by any battery in the current library.**

`sunnysky_r2205_2500` + propeller `gf_5045x3` @ `14.8V` (`:236-253`) is the **only** motor/propeller/battery-family alignment in the baseline library that lands exactly on a real battery's nominal voltage. Reference case used:

```
motor:     sunnysky_r2205_2500  (catalog-bound)
propeller: gf_5045x3            (catalog-bound)
battery:   lipo_4s_1500mah      (catalog-bound, 14.8V exact match)
ESC:       "esc 60a"            (freeform, no catalog — per contract)
```

Driven through the real `JarvisOrchestrator` (`create_project` → `system_definition_session` → catalog binds via `bind_*_from_catalog`/`set_*_component` → `handle_user_text("esc 60a")` → `calcular` → `simular` → `build_engineering_readiness`), no hand-built `ProjectState`.

### Compatible case (motor_count=2)

| Hop | Result | Evidence |
|---|---|---|
| catalog-bound | 3/3 families bound, ESC freeform | BOM lines `✓ motors: sunnysky_r2205_2500 [sunnysky_r2205_2500] qty=2`, `✓ propellers: gf_5045x3 [gf_5045x3] qty=2`, `✓ battery: lipo_4s_1500mah [lipo_4s_1500mah] qty=1`, `◇ esc: esc 60a (declarativo)` (`project_closure.py:429-445`) |
| OP voltage coherent (MOP-1/2) | `resolution_type=exact_operating_point`, `source_type=manufacturer_test`, `resolved_at_voltage_v=14.8`, `confidence=0.97` | `library.py:637-640`; query voltage from `component_writers.py:337` |
| electrical_compatibility | `esc_presence=defined`, `esc_vs_motor=compatible`, `battery_discharge=within_limit`, `prop_motor=compatible`; `i_total_a=80.0`, `esc_current_a=60.0`, `battery_limit_a=150.0` | `evaluate_electrical_compatibility` (`electrical_compatibility.py:306`); limit `100×1.5=150A` (`:209-210`); `i_total=40A×2=80A` (`:224-230`) |
| calculation | `autonomy_min=1.125` | `latest_results.calculations` |
| simulation PASS | `status=pass, can_fly=true, quality=good, safety_margin_ratio=1.3893, thrust_to_weight_ratio=1.6672` | `latest_results.simulation` |
| subsystem PASS | propulsion, energy, electronics, catalog, bom, structure, control, architecture, requirements all `PASS` | `build_engineering_readiness(saved).subsystems` (`engineering_readiness.py:1091`) |
| zero HIGH gaps | `gaps (n=0)` | same call |
| **ASSEMBLY_READY** | `overall=ASSEMBLY_READY` | same call |

This is real and reproducible — not hand-constructed. **Caveat:** every *existing* regression artifact that asserts `ASSEMBLY_READY` (`cli_probe_closure_policy_propeller_sku.py:34-92`, `test_requirements_closure.py:63-92`, both via `_assembly_ready_shape_state`) does so by hand-building a `ProjectState` with `latest_results.simulation` hardcoded to `{"status":"pass",...}` — none of them actually drive `calcular`/`simular`. This investigation's trace is the first evidence that the real end-to-end flow, with no shortcuts, reaches `ASSEMBLY_READY` honestly.

### Incompatible case (same SKUs, motor_count 2→4)

`i_total_a` → `160.0` (40A×4), exceeding the same battery's real `battery_limit_a=150.0`.

| Hop | Result |
|---|---|
| OP resolution | unchanged: `exact_operating_point`/`manufacturer_test`, `14.8V` |
| electrical_compatibility | `battery_discharge=exceeded` (`electrical_compatibility.py:270-280`); `prop_motor=compatible` still |
| simulation | `status=pass` (thrust/weight unaffected — overpowered airframe) |
| subsystem readiness | `propulsion=INCOMPATIBLE`, `energy=INCOMPATIBLE`, `blocked_by=['GAP-BATTERY-DISCHARGE-EXCEEDED', ...]` |
| gap | `GAP-BATTERY-DISCHARGE-EXCEEDED`, severity `HIGH`, evidence `i_total_a=160.0; battery_limit_a=150.0` (`electrical_compatibility.py:778-806`) |
| overall | `NOT_ASSEMBLY_READY` |

**The system honestly refuses closure — no silent pass.** `INCOMPATIBLE` is a distinct `Literal` value (`engineering_readiness.py:82-87`), not folded into a generic failure state.

A third case (motor_count=1, no ESC/frame/control declared): `sim.status=fail` (`thrust_to_weight_ratio=0.75`), `GAP-SIM-NOT-PASS` fires — and so does `GAP-MOTOR-CATALOG-UNRESOLVED`, **even though the motor is catalog-bound at `manufacturer_test` tier**. That gap ID's real trigger is "resolved OP doesn't meet computed thrust requirement," not "unresolved" (evidence string: `bound_sku_underspec:sunnysky_r2205_2500`). **This is a vocabulary trap directly relevant to Gate B** — the gap name misdescribes its own trigger condition.

---

## Gate B — Meaning of "closed"

### Vocabulary → code map

| Concept | Code symbol | Citation | Verdict |
|---|---|---|---|
| DECLARED | `classify_component()` → `"declared"` | `project_closure.py:160-188` | Real symbol, but weak — see Finding B-1 |
| VALIDATED | `SubsystemEvidence.validated` | `engineering_readiness.py:77`, computed at `:904,922,934,946,955,965,973,984` | Real field, but **conflated** — see Finding B-2 |
| COMPATIBLE | `electrical_compatibility.CheckOutcome` (`"compatible"`/`"within_limit"`) | `electrical_compatibility.py:22-28`, `_esc_vs_motor` (`:250-264`), `_battery_discharge` (`:270-280`), `_prop_motor` (`:286-300`) | **Strongest, genuinely block-specific concept in the codebase** — real numbers, no conflation found |
| SIM_PASS | `SimulationResult.status` | `simulator.py:77` | One project-wide thrust/weight check, no per-subsystem breakdown |
| READY | `SubsystemReadiness.verdict` (subsystem) / `EngineeringReadinessResult.overall` (project) | `engineering_readiness.py:82-87`, `:90-95`, `:1015-1070`, `:1073-1085` | Two real levels exist; **no third, block-scoped level exists** |
| CLOSED | *(none)* | exhaustive `grep -rn "CLOSED" src/jarvis/` → 2 hits, both design-doc references in module docstrings (`catalog_bind.py:9`, `explore_continuity.py:3`) | **Zero code representation, anywhere, for any scope** |

### Conflation findings

- **Finding B-1** — `"declared"` requires no actual property values. `project_closure.py:142-157` (`component_presence_tier`) marks a component `"present"` whenever `completeness != "low"`, independent of whether `properties` is populated; `classify_component` (`:160-188`) then falls through to `"declared"`. Live proof: `cli_probe_closure_policy_propeller_sku.py:56` builds an ESC with **zero properties**, `completeness="high"`, and it reaches `ASSEMBLY_READY` with `electronics=PASS` (probe step 4, confirmed passing this session).
- **Finding B-2** — `VALIDATED` is one global boolean, not per-subsystem proof. The literal `ctx.sim_status=="pass"` is copy-pasted into 8 of 9 subsystem evidence builders (`engineering_readiness.py:904,922,934,946,955,965,973,984`). `ctx.sim_status` traces to the single project-wide `SimulationResult.status` (`simulator.py:77`), which is purely `available_total_thrust_n >= required_thrust_n` — nothing about ESC margin, discharge margin, or prop/motor pairing. When `electronics.evidence.validated == True`, that is **not** evidence the ESC was ever checked against anything.
- **Finding B-3** — `ASSEMBLY_READY` is a rollup with no block-scoped counterpart. `_derive_overall` (`engineering_readiness.py:1073-1085`) is a conjunction across **all 9** `SUBSYSTEM_KEYS` (`:105-115`) plus a HIGH-gap check across the **entire, unfiltered** gap list. A HIGH gap in `structure` (unrelated to propulsion/energy) flips `overall` to `NOT_ASSEMBLY_READY` even with propulsion+energy flawless; conversely `ASSEMBLY_READY==True` cannot be read as certifying any single block (Finding B-1 shows it tolerates an empty-property ESC).
- **Finding B-4** — the one real evidence-strength ladder in the codebase, `resolution_type` (`library.py:521-524`, `Literal["exact_operating_point","fallback_operating_point","legacy_estimate"]`), is **motor-OP-scoped only**. Battery discharge, ESC compatibility, and prop/motor pairing all collapse to the flat `CheckOutcome` Literal with no evidence-tier metadata at all.

### Is `ASSEMBLY_READY` sufficient for any block-level closure claim today? **NO — proof:**

`_derive_overall` takes the **full** gap list and **full** subsystem dict with no per-block filter (`engineering_readiness.py:1073-1085`). Two provable consequences: (1) **false negative** — propulsion+energy can be fully compatible and sim-validated while `overall=NOT_ASSEMBLY_READY` from an unrelated `GAP-REQUIREMENTS-UNMET` (`:624-722`, HIGH severity, zero propulsion involvement); (2) **false positive for engineering rigor** — `ASSEMBLY_READY` is reachable with a zero-property ESC (Finding B-1), because no subsystem verdict requires `catalog_bound` or property richness, only presence + the shared global `validated` boolean (Finding B-2).

### Per-block vocabulary coverage

| Block | DECLARED | VALIDATED | COMPATIBLE | SIM_PASS | READY | CLOSED |
|---|---|---|---|---|---|---|
| B-REQ | real dedicated predicate (`engineering_readiness.py:881-895`) | generic shared boolean | N/A | shared global | subsystem verdict | none |
| B-ARCH | `bool(dp.system_blocks)` (`:909`) | generic + one extra real predicate: `arch_progress["is_complete"]` (`:922`) — the **one** subsystem with a genuine block-specific addition | N/A | shared global | subsystem verdict | none |
| B-PROP-ENERGY | presence-only, split motors/propellers (`:927-937`)/battery (`:939-949`) | generic shared boolean (`:946,955`) | **real, genuine** — the 4 `electrical_compatibility` checks | shared global (no propulsion-specific sim) | two subsystem verdicts + electronics | none |
| B-BOM | `build_component_bom`-derived (`:981`) | generic shared boolean (`:984`) | N/A directly; `catalog_bound` (`:986-988`) is BOM's own block-specific traceability check | shared global | subsystem verdict | none |
| B-DSE | N/A (not component-shaped); closest analog = applied-vs-not via `component_sync` | no dedicated concept; covered instead by a regression-tested explore/apply equality invariant | N/A | proxied through downstream subsystems | **no dedicated subsystem key exists** | none |
| B-CONT | N/A | N/A | N/A | N/A | **no verdict of its own** — consumes readiness (C-108, `CONNECTIONS.md:114`, "🟡 PARTIAL") to rank next-step copy only | none |

---

## Gate C — Evidence strength (reference case)

| Claim | Max honest tier | Evidence |
|---|---|---|
| Motor thrust/power/current | **`manufacturer_test`** | `library/motores/_datos.json:236-253`, `source_type="manufacturer_test"`, `confidence=0.97`, sourced bench PDF; `resolve_operating_point` → `exact_operating_point` only on this exact-voltage match |
| Propeller identity | **`spec_sheet`** | `library/helices/_datos.json` — bare `diameter_in`/`pitch_in`, no independent test row; inherits `manufacturer_test` grounding only indirectly (named inside the motor's own OP row) |
| Battery limits | **`spec_sheet`** | `library/baterias/_datos.json` — **no battery in the entire library carries `operating_points`-equivalent tested data**; `_battery_pack_limit_a` (`electrical_compatibility.py:196-218`) is a raw catalog-field computation, never a measured discharge curve |
| ESC current rating | **`declared/freeform`** | `"esc 60a"` → `source="declared"`, no `catalog_ref`, no confidence field; BOM renders `◇ esc: esc 60a (declarativo)` — visually distinct from `[sku]` lines |
| Compatibility verdicts (`battery_discharge`/`esc_vs_motor`/`prop_motor`) | **`derived`**, weakest-link caveat | Computed comparisons (`electrical_compatibility.py:250-300`) — `esc_vs_motor=compatible` trusts the unsourced, user-typed `60A` with the same authority as the bench-tested motor current; `CompatibilityResult`/`Gap` carry no tier/confidence field to distinguish this |
| Simulation PASS | **`derived`** | Pure physics-formula output over the tiers above; never itself measured, regardless of how confidently "PASS" reads |
| BOM/procurement identity (`sku_resolved`) | **`spec_sheet`/`manufacturer_test`** for motor/propeller/battery; **`declared/freeform`** for ESC/frame/sensors | `_bom_sku_resolved` (`project_closure.py:204-225`) — strict `catalog_ref`-plus-live-recheck boolean, honest and un-upgradeable by prose, but **binary**: a `manufacturer_test`-grounded motor line and a `spec_sheet`-grounded battery line render identically |

**Bottom line:** B-PROP-ENERGY reaches `ASSEMBLY_READY` today with a real, non-fabricated combo at `manufacturer_test` tier for the motor — but this is **not robust to catalog composition**: it is the *only* motor/propeller/battery-voltage alignment in the current library that reaches that tier (`emax_rs2205s_2300`, the other manufacturer_test motor, is voltage-unreachable by any current battery), and 6 of 8 `operating_points`-bearing... in fact 14 of 22 motors overall have no `operating_points` at all, landing on `legacy_estimate`/spec_sheet tier. This directly informs Gate F.

---

## Gate D — Blocking vs enhancing (B-PROP-ENERGY)

| # | Candidate | Verdict | Evidence |
|---|---|---|---|
| 1 | ESC catalog (H5) | **ENHANCING** for B-PROP-ENERGY compatibility; **BLOCKING (structural)** for B-BOM's ESC line only | `electrical_compatibility.py:178-190,250-264` computes a real compatible/undersized verdict from a **freeform** ESC property — no catalog needed for the physics check. But `library.py` has no `EscSpec`/`get_esc` (only Motor/Battery/Propeller/Material specs exist), `project_closure.py:254-259` documents ESC quantity as an honest `None`, and `system_architecture_catalog.py:234-241` only resolves `family in {motor,battery,propeller}` — ESC BOM lines can never reach `sku_resolved=True`, not a density problem, a missing family |
| 2 | Battery real-test data curation | **ENHANCING** | 0/10 batteries have `operating_points` populated (direct load verified); `_battery_pack_limit_a` already computes an honest `within_limit`/`exceeded` verdict from spec_sheet fields alone — real-test data raises tier, doesn't enable the claim |
| 3 | OP coverage density | **ENHANCING** | 2/22 motors carry `operating_points`; the other 20 honestly fall to the fallback branch and **decline to fabricate** an exact OP (confirmed: `cli_probe_p2_2_operating_point_bridge.py` step 5 — legacy SKU yields zero `motor_op_*` keys, stays honest). Fallback-honest closure is structurally sound already |
| 4 | Viable combo pre-selection (G24-C) | **ENHANCING** | `evaluate_electrical_compatibility` (`electrical_compatibility.py:306-368`) has zero dependency on how a candidate was surfaced by DSE's `_finalize_viable_list` (`design_explorer.py:494-529`) — whatever ends up bound gets the same post-hoc check regardless |
| 5 | FN-R routing UX | **ENHANCING** (generic re-bind exists) | `orchestrator.py:2637-2641,2645,2749` — explicit re-bind call sites for motor/propeller/battery already shipped under the closed `*_catalog_bind_ux` arcs |
| 6 | C-108 readiness → Continuity | **UNRELATED** to the verdict; ENHANCING for next-step copy only | `project_continuity.py:66-71` — `readiness` only gates two advisory-string branches; the closure verdict is fully computed by `engineering_readiness` *before* Continuity ever runs |
| 7 | DSE ↔ component sync (G1) | **UNRELATED / already resolved** | `orchestrator.py:3684-3700` calls `component_sync.sync_motors_component_from_params` after `invalidate_diverged_catalog_refs`, shipped under `checkpoint-g5-dse-component-sync`, covered by `test_component_sync.py`/`test_g5_dse_iterate_dual_truth.py` — not a pending gap |
| 8 | C-081 sim margin → Continuity | **UNRELATED**, polish only | `project_continuity.py:239-241` — the plain PASS branch sets next-step text **without reading `margin`** at all; no closure-determining path consumes `next_useful_step` |

**Summary:** every candidate is ENHANCING or UNRELATED for B-PROP-ENERGY. The one structural BLOCKING finding (ESC family absence) is scoped narrowly to B-BOM's ESC-line traceability, not to B-PROP-ENERGY's physical/compatibility closure.

---

## Gate E — Closure UX

All traces drove `orchestrator.handle_user_text(text, llm)` with an LLM-refusing stub — the same call the real interactive CLI loop makes (`src/jarvis/adapters/cli/main.py:724,681`) — so these are faithful non-LLM CLI-equivalent paths.

1. **Greenfield** (B-REQ/B-ARCH/B-PROP-ENERGY): `create_project` → arch wizard → catalog-bind motor/prop/battery → ESC freeform → `calcular` → `estado` reaches architecture 4/4 with honest `[sku]` BOM lines. **Finding:** Propulsion=PASS and Energy=PASS were reached **independently** of overall readiness (a minimal-arch run stayed `NOT_ASSEMBLY_READY` on unrelated frame/FC gaps while propulsion/energy were already clean) — direct observational confirmation of the ASSEMBLY_READY≠block-closure distinction, not inference.
2. **Re-open / gap-fix**: forcing `battery_discharge=exceeded` (`lipo_2s_850mah`, 4 motors) reproduces the honest `GAP-BATTERY-DISCHARGE-EXCEEDED` refusal. The "obvious" one-shot fix (`"ayúdame a elegir"` right after) returns **no suggestions** — the catalog offer only fires pre-bind, not post-bind. A working deterministic fix exists only via a specific two-step sequence: `"definir bateria"` (no-op) then `"ayúdame a elegir"` (re-offers the full catalog).
3. **🔴 New regression finding**: on a clean, architecture-4/4, no-open-wizard project with battery already catalog-bound, typing `"definir bateria lipo_6s_10000mah"` **or** `"cambia la bateria a lipo_6s_10000mah"` — naming a real, existing SKU verbatim — does **not** catalog-bind it. It falls through to the freeform numeric parser (`param_definition_session.py:1040-1048`, regex `\d+(?:\.\d+)?` grabs the "6" from "6**s**") and **silently destroys the pre-existing valid `catalog_ref`**, replacing a real 22.2 Wh catalog-bound battery with a nonsensical 6.0 Wh freeform value — presented as a confident success ("Parámetros aplicados... Sistema recalculado"), no warning. This is the identical failure signature to the closed `cli_finding_g27_battery_6s_parsed_as_6wh.md` (context only), but on the **`define_missing_params`** code path, which the G27 checkpoint's wizard-path hardening did not cover. **Per ★4, this is new regression evidence on a currently-open code path — not a reopening of the closed G27 arc.**
4. **B-DSE**: `"optimiza para mejorar autonomia"` → `"aplica la mejor"` deterministically applies, `estado` reflects the exact promised value (`autonomy_min=4.0364` matches exactly) — matches `cli_probe_dse_motor_op_dual_truth.py`'s already-established 6/6. **Adjacent finding:** an ordinary physical-parameter mutation (`"aumenta el empuje del motor a 20N"`, 2.5× divergence from the catalog spec) routes through `define_missing_params`, **not** through the `invalidate_diverged_catalog_refs`-wired paths (only DSE-apply and `actions/iterate.py:156-157` call it) — `estado` kept showing `[sunnysky_r2305_2500]` as resolved after a 2.5× divergent mutation. The G24-D "frankenstein `.name`-clear" guarantee is proven for the DSE-apply/iterate routes, **not** for this ordinary mutation route.
5. **B-BOM**: `estado`'s `component_bom_lines` honestly renders `[sku]`/incomplete distinctions with no JSON inspection — the one gap is the divergence case above (Path 4), where it stays stale.
6. **B-CONT**: `estado` always carries a `continuity` context key plus a `Siguiente paso:`/`Por qué:` line, deterministically, no raw-JSON needed. Post-ASSEMBLY_READY-specific Continuity content wasn't independently re-verified beyond `cli_probe_requirements_closure.py` step 2 (confirms `"PROJECT STATUS: ASSEMBLY READY"` renders deterministically).

### UX closure matrix

| Block | Backend-can-close | User-can-reach-via-CLI |
|---|---|---|
| B-REQ | assumed per contract | **YES** — `cli_probe_requirements_closure.py` 5/5 |
| B-ARCH | assumed | **YES** — reproducible 4/4 |
| B-PROP-ENERGY | YES (Gate A) | **PARTIAL** — greenfield bind YES; re-open works only via a non-obvious two-step sequence; natural single-shot re-bind phrasing actively corrupts state (Path 3) |
| B-BOM | assumed | **PARTIAL** — honest on the happy path; stale on the `define_missing_params` divergence route |
| B-DSE | assumed | **YES** — deterministic explore→apply, exact value match |
| B-CONT | assumed | **YES** (partial verification) — advisory copy always CLI-reachable; post-ready-specific content not independently re-verified by this trace |

---

## Gate F — Catalog Foundation dependency

1. **Families needed today**: `system_architecture_catalog.py:158` — `BLOCK_TO_COMPONENTS["propulsion"]=["motors","propellers","esc"]`. Combined with `library/`'s actual four data files and `library.py`'s four spec classes (no ESC/frame/FC), the code-recognized catalog-bindable families are **motor, propeller, battery**. ESC is architecture-recognized but has no catalog family. No frame/flight-controller family exists anywhere.
2. **Minimum fields per family**: Motor (`library.py:37-58`) — calc/compatibility fields present; `operating_points` schema exists but populated in only 2/22 rows (the real gap, not a missing field). Battery (`:100-113`) — voltage identity, C-rating, capacity all present as spec_sheet fields sufficient for `_battery_pack_limit_a`; `operating_points` populated in 0/10 rows. Propeller (`:117-128`) — diameter/pitch present; `ct`/`cp`/`compatible_kv_band` optional, per-row population not independently verified in this investigation (flagged, not resolved). ESC — no schema class exists at all.
3. **Actual SKU counts** (direct load, not estimate): motors **22**, propellers **16**, batteries **10**, materials **8**, ESC **0**. Matches the contract's stated "~22/~16/~10" exactly.
4. **Would conclusions change materially with 5-10 more SKUs per family?** **No.** Every Gate D verdict was decided by code structure (does a function/field/family exist and get consumed), not row count: ESC's BOM-traceability gap is caused by a total absence of an `EscSpec` accessor — untouched by motor/prop/battery expansion. The battery/OP "ENHANCING not BLOCKING" verdicts rest on the fallback and spec_sheet paths already being *honest* at low density — more rows raise how often the higher tier is hit, not whether the fallback path is correct. G24-C/C-108/C-081/G1 verdicts are about module wiring, unaffected by catalog size. This is an argued-from-code-structure conclusion (not independently re-tested against a resized library, per ★2 — no SKUs were fabricated to test it).
5. **Recommendation: Block Closure first, not Catalog Foundation first.** Every candidate that would justify sequencing Catalog Foundation first (ESC catalog, battery/OP curation, SKU density) resolved to ENHANCING, not BLOCKING, for B-PROP-ENERGY. The one true structural gap (ESC family absence) is scoped to B-BOM's ESC-line traceability, not the primary reference case's physical/compatibility closure. If a bounded catalog change is wanted regardless, the defensible minimum is **+1 ESC schema class with 3-5 representative SKUs** (closes the one real structural gap) — not motor/prop/battery expansion, which Gate D shows is not load-bearing for closure. Per §11: since Catalog Foundation is **not** the primary recommendation, no separate `investigation_contract_catalog_foundation.md` outline is produced in this report.

---

## §4 — Mandatory output table

| Block | Can close today? | Evidence tier reached | Physical guarantee | Traceability | UX closure | Missing contract |
|---|---|---|---|---|---|---|
| Requirements (B-REQ) | **PARTIAL** — subsystem verdict exists and is honest on achievable/unachievable constraints (`cli_probe_requirements_closure.py` 5/5), but "VALIDATED" is the generic shared global-sim boolean (Gate B, `engineering_readiness.py:904`), not a requirements-specific check | `derived` — achievability is a real deterministic calc over user-declared constraint values (no catalog data involved) | N/A | N/A — requirements have no SKU/catalog identity to trace | **YES** (Gate E) | None for presence/achievability; closure strength is bounded by the shared, non-requirements-specific `VALIDATED` field (Gate B Finding B-2) |
| Architecture (B-ARCH) | **YES** — `arch_progress["is_complete"]` is a genuine, block-specific completeness predicate (`engineering_readiness.py:922`), reproducibly reachable via CLI (Gate E Path 1/3) | `derived` (structural completeness check); underlying component tiers vary (declared→manufacturer_test) | N/A | **PARTIAL** — completeness doesn't require catalog-bound instances; a zero-property component can still count `"declared"` (Gate B Finding B-1) | **YES** (Gate E) | 4/4 completeness doesn't distinguish catalog-bound richness from empty declared stubs (Finding B-1) |
| Propulsion/Energy (B-PROP-ENERGY) | **PARTIAL** — real `ASSEMBLY_READY` reached for one non-fabricated combo, with honest refusal on an incompatible one (Gate A); but reachability is fragile to catalog composition (Gate A/C: only one motor/battery-voltage alignment in the library reaches `manufacturer_test`) and the natural re-bind UX path actively corrupts state (Gate E) | Heterogeneous: `manufacturer_test` (motor only) / `spec_sheet` (propeller, battery) / `declared-freeform` (ESC) — Gate C | **YES for the demonstrated combo** — real `electrical_compatibility` checks pass with real numbers, and the incompatible case is honestly refused (`INCOMPATIBLE` verdict, `GAP-BATTERY-DISCHARGE-EXCEEDED`, HIGH) | **PARTIAL** — `sku_resolved` honest for motor/prop/battery, structurally impossible for ESC (Gate D #1); frankenstein-divergence clearing not proven on the `define_missing_params` mutation route (Gate E Path 4 adjacent finding) | **PARTIAL** — greenfield bind YES; re-open works only via a non-obvious two-step sequence; natural single-shot re-bind phrasing corrupts state (new regression, Gate E) | No block-scoped rollup exists (`ASSEMBLY_READY` is a 9-way global conjunction, Finding B-3); `VALIDATED` is the shared global-sim boolean, not propulsion/energy-specific (Finding B-2); reference-case closability depends on one coincidental library voltage alignment, not a general property; the natural free-text re-bind phrasing corrupts state on a code path G27 didn't harden |
| BOM/Procurement (B-BOM) | **PARTIAL** — `sku_resolved` is real and honest for catalog-bindable families, but ESC/frame/sensors can never reach it (no catalog family, Gate D #1), and divergence-clearing is unproven on one mutation route | Heterogeneous — `manufacturer_test`/`spec_sheet` for motor/propeller/battery, permanently `declared/freeform` for ESC (no catalog exists); BOM display has no field to distinguish the two (Gate C) | N/A — BOM concerns identity/traceability, not physics; physical guarantees for its constituent components are covered under B-PROP-ENERGY | **PARTIAL** — strong for 3 catalog-bindable families, structurally impossible for ESC; frankenstein-clearing proven only for DSE-apply/`iterate` routes, not `define_missing_params` (Gate E) | **PARTIAL** — `estado` renders honest `[sku]` lines on the happy path (Gate E Path 5), stale on the divergence-via-mutation case | No ESC catalog family exists (structural, not data-density — Gate D #1), so B-BOM can never be honestly "closed" project-wide, only per-catalog-bindable-family; no evidence-tier field distinguishes manufacturer_test- vs spec_sheet-grounded resolved SKUs |
| DSE (B-DSE) | **YES** for the explore/apply coherence claim itself — regression-tested equality invariant (`cli_probe_dse_motor_op_dual_truth.py` 6/6), live CLI-reachable (Gate E Path 4); but there is no dedicated "DSE closed" verdict distinct from whichever subsystems its applied params touch | `derived` (explore/apply values are calc outputs); downstream tier inherits from whatever motor/battery ends up bound after apply | N/A | **PARTIAL** — `component_sync`/`invalidate_diverged_catalog_refs` correctly wired for the DSE-apply route (Gate D #7), but the equivalent honesty guarantee is unproven for the ordinary `define_missing_params` mutation route (shared gap with B-BOM) | **YES** (Gate E Path 4 — deterministic, exact value match) | No dedicated DSE subsystem/verdict exists in `SUBSYSTEM_KEYS`; DSE "closed" is entirely proxied through downstream subsystems it touches — likely fine (derivable) but not an explicit contract today |
| Continuity (B-CONT) | **N/A** — Continuity has no verdict of its own to close; it is advisory next-step text consuming an already-final readiness verdict (Gate B, Gate D #6) | N/A — Continuity produces no independent claim to grade | N/A | N/A — advisory copy, not a component/procurement claim | **YES** (Gate E Path 6 — `continuity` key + `Siguiente paso`/`Por qué` always CLI-reachable; post-ready-specific content not independently re-verified) | Continuity has no closure concept to be missing — by design it's advisory copy downstream of an already-final verdict; C-081 margin-to-Continuity wiring is UX/copy polish only, not a closure blocker (Gate D #8) |

---

## Primary recommendation

**One bounded next arc: a Block Closure IC scoped to B-PROP-ENERGY**, built as a **rollup + UX contract over existing signals** (Hypothesis A), not a new physics/compatibility subsystem or `BLOCK_STATUS` enum. Concretely, in priority order:

1. Define an explicit block-scoped closure derivation for B-PROP-ENERGY — a named rollup over `{propulsion, energy, electronics}` subsystem verdicts + the 4 `electrical_compatibility` facts, distinct from the 9-way `ASSEMBLY_READY` conjunction (addresses Finding B-3). This is a derivation/UX addition, not new engineering logic.
2. **Fix the battery re-bind corruption** found in Gate E (Path 3: `"definir bateria <sku>"` / `"cambia la bateria a <sku>"` silently destroying `catalog_ref` via `define_missing_params`). This is new regression evidence (★4-compliant, not a G27 reopen) and directly undermines any UX-closure claim for the block this arc targets — should land before or alongside item 1, not after.
3. Disambiguate the `VALIDATED` field (Finding B-2) so a block-closure claim doesn't silently borrow the shared global-sim boolean as if it were propulsion/energy-specific proof.
4. Extend the frankenstein/divergence-clearing guarantee (currently proven only for DSE-apply/`iterate` routes) to the `define_missing_params` mutation route, or explicitly document it as a known gap if deferred.

**Ordered alternates / explicit deferrals** (per Gate D, none BLOCKING for B-PROP-ENERGY): ESC catalog (H5) — defer, narrow to B-BOM traceability only, revisit only if Engineer wants ESC procurement identity specifically; battery/OP real-test data curation — defer, spec_sheet/fallback is already honest; G24-C viable pre-selection — defer, post-hoc detection is sufficient; FN-R routing UX — defer, generic re-bind already exists (distinct from the new corruption bug above); C-108 Continuity handoff — defer, polish only; G1 DSE↔component sync — **no work needed**, already resolved; C-081 sim margin→Continuity — defer, polish only. **Catalog Foundation investigation** — not primary (Gate F); if pursued at all, bound it to the ESC schema gap only (+3-5 representative SKUs), not motor/prop/battery expansion.

---

## Engineer ★ questions (evidence surfaced, not unilaterally answered)

| ★ | Question | Evidence-grounded lean |
|---|---|---|
| ★1 | Derivable vs. new authority? | **Derivable** — the strongest concept (COMPATIBLE) is already real and block-specific (Gate B); the gap is a missing rollup + a conflated `VALIDATED` field, not missing physics |
| ★2 | Is B-PROP-ENERGY closable today at Snapshot B tier? | **Yes, for one demonstrated non-fabricated combo**, with honest refusal on an incompatible one — but that closability is fragile to catalog composition (Gate A/C), which bears on ★6 |
| ★3 | Gate D blocking vs enhancing for B-PROP-ENERGY? | **None BLOCKING** — all 8 candidates ENHANCING/UNRELATED; the one structural gap (ESC family) is scoped to B-BOM, not B-PROP-ENERGY |
| ★4 | Next arc priority? | **Block Closure IC** (bounded, per Primary recommendation above); Catalog Foundation, FN-R, H5, C-108 all deferred per Gate D/F evidence |
| ★5 | Minimum SKU count if Catalog Foundation goes first? | Foundation is not recommended first (Gate F); if pursued anyway, **+1 ESC schema class, 3-5 representative SKUs** is the only evidence-justified bound — motor/prop/battery expansion is not load-bearing for any Gate D verdict |
| ★6 | Accept fallback-honest closure, or require evidence upgrade? | Evidence leans toward **accept fallback-honest closure as a documented, lower-confidence mode** — the fallback path is honest (declines to fabricate, Gate D #3), but Engineer should weigh this against Gate A/C's finding that the *only* `manufacturer_test`-tier combo in the current library is one coincidental voltage alignment — a "closed" claim resting exclusively on that combo would not generalize |

---

## Deliverables produced

- This report: `.jes/artifacts/investigation_report_post_v034_block_closure.md`
- Baseline table: §0 above
- No production fix, no version bump, no new `BLOCK_STATUS` subsystem, no committed test/probe file (reference-case traces were run via scratchpad-only scripts per fork, not added to the repo — optional per contract §7, not required for PASS)
- No `investigation_contract_catalog_foundation.md` outline produced — Gate F did not recommend Catalog Foundation as primary (§11)
