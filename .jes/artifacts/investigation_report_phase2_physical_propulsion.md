# Investigation Report — Phase 2 Physical Propulsion Engine

**Contract:** [`investigation_contract_phase2_physical_propulsion.md`](investigation_contract_phase2_physical_propulsion.md)
**Checkpoint base:** `checkpoint-impl-d` (`24fa7ba`)
**Status:** Investigation complete. **No `src/` or test files touched** (verified — see §14 sign-off).

---

## 1. Executive summary

Today's propulsion physics is a **single-point, context-free number**: `per_motor_max_thrust_n` — either declared directly, derived from a crude propeller-diameter/RPM heuristic (fixed `Ct=0.12`, never reads a bound propeller's real `ct`), or projected 1:1 from a catalog motor's `MotorSpec.thrust_n` via the Impl C thrust bridge. Sim (`FeasibilitySimulator`) consumes exactly four scalars — `available_total_thrust_n`, `required_thrust_n`, `weight_n`, `autonomy_min` — and nothing about voltage, current, RPM, or efficiency. This is a **narrow, stable integration surface**: Phase 2 v1 can feed it a better `per_motor_max_thrust_n` without touching sim or calc-engine control flow at all.

The Catalog V1 design doc (`docs/PHYSICAL_COMPONENT_CATALOG_V1.md` §4.2) **already speced** an `operating_points[]` field — `prop_id, voltage_v, rpm?, thrust_n, current_a?, power_w?` — on `MotorSpec`/`BatterySpec`/`PropellerSpec`. That field exists in the dataclasses today (`library.py`) but is **populated in zero seed rows** and read by **zero consumer code**. Phase 2 v1 is therefore mostly a "turn on what's already reserved" problem, not a new-subsystem problem — directly consistent with the vision's own §12 guidance (small validation set first) and this contract's hard constraint (prefer extending calc/library over a parallel Physics Engine).

ERF-2 (`electrical_compatibility.py`) already does real per-motor current, ESC-vs-motor, and battery-discharge checks **when catalog data is present** (`max_current_a`, `max_continuous_current_a`) — but every one of those fields is unpopulated in the current seed JSON, so every check silently resolves to `unverifiable` today. This is a second "reserved but dormant" surface Phase 2 can activate.

**G26/G27 verdict (§6): both are NO — neither is a hard prerequisite for the Phase 2 data/calc contract.** G27 lives entirely in the free-text/semantic-adapter update path (`semantic_intent_adapter.py::_parse_value`), never in the catalog-bind path (`bind_battery_from_catalog` already projects `energy_wh` correctly with provenance). G26 lives in `_parse_constraints` reading only the `restrictions` string — unrelated to physics math, it blocks ASSEMBLY READY UX only. Both remain real, urgent parallel debt — not gates.

**Recommended first slice: Option A — Lookup Operating Point**, sourced from a small hand-curated `operating_points[]` table for 2–5 already-seeded motor SKUs, populating `per_motor_max_thrust_n` (+ new provenance-carrying fields) only when a real (motor[, propeller][, voltage]) combo matches a table row; honest fallback to today's Model 1 behavior otherwise. No new subsystem, no propeller-bind UX required as a hard dependency, no G24/G26/G27 fix required.

---

## 2. As-is propulsion physics audit

### 2.1 Calculation entry (`calculation_engine.py`)

Force-resolution order inside `CalculationEngine.build()` (single `if/elif` chain, first hit wins — `calculation_engine.py:79-154`):

1. **Direct declared thrust** — `max_force_per_actuator_n` or `per_motor_max_thrust_n` in `current_parameters`. This is what a catalog motor bind (Impl B) and the Impl C thrust bridge both write to. **Wins unconditionally over everything below.**
2. **Torque → force** (ground vehicles) — `per_actuator_torque_nm` + `wheel_radius_m` + `gear_ratio` → `calculate_traction_force_from_torque`. Irrelevant to aerial propulsion; included here only because it shares the same `elif` chain.
3. **Propeller aerodynamic estimate** — only reached if (1) and (2) are both absent. Needs `propeller_diameter_m`/`_in` **and** `propeller_rpm` (or `motor_kv_rating` + `battery_cell_count` to derive RPM via `RPM ≈ KV × cells×3.7V × 0.85`). Calls `calculate_thrust_from_propeller(diameter_m, rpm, ct=0.12, air_density=1.225)` — **`ct` defaults to `0.12` and is read only from a loose `parameters.get("propeller_ct")` key that no writer or bind path ever sets.** Even when `propellers` is catalog-bound with a real `PropellerSpec.ct`, this path never reads it (confirmed: `set_propeller_component` bridges only `diameter_in`/`pitch_in`, never `ct`).
4. **No path resolves** → emits `missing_propulsion_parameters` / `missing_propeller_parameters` / `missing_transmission_parameters` tool result, engine continues (no crash), sim later receives `available=None`.

**Conclusion: for a catalog-bound motor, thrust is never anything but the SKU's single `thrust_n` point value (via the Impl C bridge) or a user override.** There is no context (voltage, propeller pairing, load) in the number at all today — it is Model 1's central limitation, exactly as the vision doc frames it.

### 2.2 Who writes `per_motor_max_thrust_n` / `motor_count` / `battery_capacity_wh`

| Writer | Path | Provenance carried? |
|---|---|---|
| `component_writers.set_motor_component` | Bind (catalog) or freeform declare | Impl C bridge: only bridges `spec.properties["thrust_n"].value` when present; no `source_type`, only `PropertyValue.source ∈ {declared,inferred,calculated}` on the component property itself — the mirrored `current_parameters` value carries **no provenance at all** (it's a bare float) |
| DSE apply (`_handle_apply_exploration` → `apply_components_delta`) | Explore → apply `#1` | Same bridge, same no-provenance-on-param limitation |
| `iterate_interactive_session` numeric wizard | User types a bare number | Direct float write, `source="declared"` on the component property (if any), param itself still bare |
| `semantic_intent_adapter` → iterate preseed | Free-text NL ("aumentar bateria a X") | **No catalog lookup at all** — regex-extracts a bare number from LLM-proposed `valor` text (root cause of G27, see §6) |
| `bind_battery_from_catalog` | Catalog battery bind (test-callable, no live UX yet) | `battery_capacity_wh = spec.energy_wh`, `source="declared"`, `confidence=0.95` — **correct**, cell/voltage-aware because it reads the whole `BatterySpec`, not free text |

### 2.3 Catalog thrust today — context-free truth

`MotorSpec.thrust_n` is a bare peak/point value with no attached voltage, propeller, or RPM. `bind_motor_from_catalog` projects it as one `PropertyValue`; the Impl C bridge mirrors it 1:1 into `per_motor_max_thrust_n`. **Yes — catalog thrust is treated as universal/context-free truth today**, exactly the gap Phase 2 exists to close.

### 2.4 Sim (`simulation/simulator.py::FeasibilitySimulator.evaluate`)

Consumes exactly: `calculations.available_total_thrust_n` (`motors × per_motor_max_thrust_n`), `required_thrust_n`, `weight_n`, `autonomy_min`, `thrust_per_motor_required_n`. **Nothing about current, voltage, RPM, or efficiency reaches sim.** `can_fly = available >= required`; `safety_margin_ratio`; quality/warnings thresholds (`LOW_MARGIN_THRESHOLD=1.15`, `HIGH_LOAD_THRESHOLD=0.9`, `LOW_TW_RATIO=1.3`). This is a narrow, stable surface — Phase 2 v1 does not need to touch this file at all if it populates `per_motor_max_thrust_n` upstream.

### 2.5 Autonomy (Wh / W model)

`calculate_autonomy_min(battery_capacity_wh, total_power_w) = (Wh/W)×60`. `motor_power_w` is a bare param (from `MotorSpec.max_watts` or freeform declare) × `motors`. No current/voltage decomposition — pure energy-balance, no I·V or efficiency term. This is the exact model G27 corrupts when `battery_capacity_wh` is silently wrong.

### 2.6 Electrical (`electrical_compatibility.py`, ERF-2)

Already implements, as **pure facts** (not gaps, not consumed by calc/sim):

- `_per_motor_current_a`: catalog `MotorSpec.max_current_a` → else declared `max_current_a` property → else `motor_power_w / V_nom` estimate.
- `_nominal_pack_voltage_v`: catalog `BatterySpec.nominal_voltage` or `cells×3.7` → else declared `battery_cell_count×3.7`.
- `_esc_current_a`: declared ESC `current_a` property only (no ESC catalog/`ESCSpec` exists — confirmed, see §3).
- `_battery_pack_limit_a`: catalog `max_continuous_current_a` → else `c_rating × capacity_Ah`.
- `_prop_motor`: `library.match_motor_propeller` — `compatible_prop_ids` exact match, else `compatible_prop_inch` ± tolerance, else `unverifiable`. Deterministic, no aerodynamic model, never fabricates a match.

**This is already a real "electrical facts" layer with the exact fields Phase 2's Operating Point needs (current, voltage, ESC sizing) — it is simply gracefully `unverifiable` today because the seed JSON never populates `max_current_a`/`voltage_min`/`voltage_max`/`nominal_voltage`(present)/`max_continuous_current_a`(present).** It never feeds calc/sim; it only feeds `engineering_readiness.py` gap derivation. Phase 2 could populate these same fields and get ERF-2 facts "for free," but ERF-2 by design stays a facts-only layer, not a source of thrust/power for sim — Phase 2's Operating Point is a distinct concern from ERF-2's compatibility facts, even though they'd read the same enriched catalog rows.

---

## 3. Catalog data inventory vs vision

Verified directly against seed JSON (`library/motores/_datos.json`, `library/baterias/_datos.json`, `library/helices/_datos.json`) — **not just the dataclass schema.**

| Family | Fields present in schema (`library.py`) | Fields **actually populated** in seed JSON | Vision Phase 2 needs | Gap |
|---|---|---|---|---|
| **Motor** | `thrust_n, kv_rating, weight_g, max_watts, compatible_prop_inch, design_space, manufacturer, model, max_current_a, voltage_min, voltage_max, compatible_prop_ids, operating_points[], source_url` | Only `thrust_n, kv_rating, weight_g, max_watts, compatible_prop_inch, design_space` (+ `is_generic` on 1 row). **Zero rows** have `manufacturer/model/max_current_a/voltage_min/voltage_max/compatible_prop_ids/operating_points/source_url` | kv, voltage_range, max_current, R (resistance — **not in schema at all**), `performance_tests[]` (≈ `operating_points[]`) | Schema mostly ready; **zero data**; **no resistance field exists anywhere** (motor or ESC) |
| **Propeller** | `diameter_in, pitch_in, mass_g, ct, cp, compatible_kv_band, tags, operating_points[]` | `diameter_in, pitch_in, mass_g` (+ `compatible_kv_band`/`tags` on some rows). **Zero rows** have `ct`, `cp`, or `operating_points` | diameter, pitch, blades, mass | `blade_count` **not in schema**; `ct`/`cp` reserved but unpopulated and **never read by calc** even when present (§2.1) |
| **Battery** | `chemistry, energy_wh, mass_g, cells, nominal_voltage, capacity_mah, max_continuous_current_a, c_rating, design_space, operating_points[]` | Most rows have `chemistry, energy_wh, mass_g, cells, nominal_voltage, capacity_mah, c_rating`; 2 of ~9 rows also have `max_continuous_current_a`. **Zero rows** have `operating_points` | cells, V_nom, capacity, C-rating, mass | Schema **already covers** vision's battery needs almost exactly; only `internal_resistance` is missing (not in schema, not in vision's own required list either) |
| **ESC** | **No `ESCSpec` class exists.** No `library/escs/` directory. | — | voltage_range, continuous_current, peak_current, protocol, efficiency | **Full gap — no ESC catalog entity at all.** Confirmed intentional: vision doc and `ENGINEERING_READINESS_VISION.md` both explicitly defer "H5 ESC catalog" as out-of-scope/future |

**Answer to the mandatory §1.2 question:** Yes — Phase 2 v1 **can** run on a small hand-curated lookup table of manufacturer operating points without new motor intrinsic models, because the `operating_points[]` field already exists on all three specs and needs only (a) real data for 2–5 SKUs and (b) one consumer function that reads it. No schema migration is required for the minimal slice. A `resistance` field for motors and an `ESCSpec` class are real future gaps but are **not** required for v1 (thrust/power estimate from a lookup table doesn't need internal resistance).

---

## 4. Operating-point — data contract (proposal, fields only)

Aligned with vision §6 and the Catalog V1 doc's own §4.2 sketch (which is already the closest thing to a ratified schema — I'm reusing it, not inventing a new one):

```text
OperatingPoint:
  motor_ref:      CatalogRef (family="motor")        # required
  propeller_ref:  CatalogRef (family="propeller") | None   # optional — absent = "motor alone" point
  battery_ref:    CatalogRef (family="battery") | None     # optional — voltage context only
  voltage_v:      float                               # required — the point is meaningless without it
  rpm:            float | None
  thrust_n:       float                                # required — this is what calc consumes
  current_a:      float | None
  power_w:        float | None                         # derivable from voltage_v * current_a if absent
  efficiency:     float | None                          # thrust_n / power_w or vendor-stated
  source_type:    "manufacturer_test" | "calculated" | "estimated" | "assumed"   # required
  confidence:     float                                 # required, reuses PropertyValue's existing 0..1 convention
  source_note:    str | None                            # free text: "T-Motor datasheet 2023-10", "Ct=0.11 estimate"
```

**Where it lives:** `library.py`'s existing `operating_points: tuple[dict[str, Any], ...]` field on `MotorSpec` (and optionally `PropellerSpec`/`BatterySpec` for cross-referencing) — **not** a new `ProjectState` field, **not** a new derived-calc-artifact class. The lookup is keyed by `(motor_sku, propeller_sku | None, voltage_v)` and resolved at the point `set_motor_component`/the thrust bridge already runs — i.e., extend the existing bridge, don't add a parallel resolution path. This directly satisfies the hard constraint "prefer extending calc/library over a parallel Physics Engine subsystem."

**Provenance placement — an integration decision, not yet made:** `PropertyValue.source` (`action_schema.py:127`) is a closed `Literal["declared","inferred","calculated"]` with **no `manufacturer_test`/`estimated`/`assumed` distinction**, and today's catalog-bind paths already (ab)use `source="declared"` to mean "SKU-projected, trustworthy" — conflating "user typed it" and "catalog gave us this" under one label. Vision's honesty requirement ("never present estimate as manufacturer_test") needs a finer enum than what exists. Two options, both additive:
- **(a)** Add `manufacturer_test`/`estimated`/`assumed` as new `Literal` members on `PropertyValue.source` (breaking nothing — existing values stay valid; a `Literal` union grows, doesn't shrink).
- **(b)** Keep `source_type` as an Operating-Point-only field (as sketched above), separate from `PropertyValue.source`, since an OP's provenance describes the *thrust number's origin*, not the *component property's origin* — they can legitimately diverge (a catalog-declared motor SKU can still have an *estimated* OP thrust for an unproven propeller pairing).

Recommend **(b)** for v1 — narrower blast radius, no schema-wide `Literal` change, and it matches "do not reopen Impl D BOM schema without cause" in spirit (don't touch `PropertyValue` for every consumer just to serve one new feature). Flagged as ★-decision (§12).

**Hard rule validated:** a motor SKU's OP thrust is only presented when `(motor[, propeller][, voltage])` actually matches a table row; absent a match, fall back to today's Model 1 point value **labeled honestly as `source_type="estimated"`** (the SKU's bare `thrust_n`) rather than silently reusing it unlabeled as today.

---

## 5. Integration with ProjectState / calc / sim / ERF / BOM

**Q1 — Replace or populate `per_motor_max_thrust_n`?**
**Populate**, not replace. §2.4 shows sim/calc consume only the scalar; Phase 2 v1's job is to compute a *better-sourced* scalar and write it through the existing bridge point (`component_writers.set_motor_component`, same call site as today's Impl C bridge), plus (new) attach the OP's `source_type`/`confidence` somewhere inspectable (e.g. a sibling `current_parameters["per_motor_max_thrust_n_provenance"]` or, cleaner, a `ComponentSpec.properties["operating_point"]` PropertyValue-shaped entry — implementation detail for the IC, not this investigation). Calc engine's `if/elif` chain in §2.1 needs **zero changes** — it already treats `per_motor_max_thrust_n` as authoritative when present.

**Q2 — Propeller has no `catalog_ref` (freeform `5x4.5`)?**
Honest fallback: OP lookup requires a `propeller_ref` for any point where the table stores propeller-specific data; a freeform-declared propeller (today's default — `bind_propeller_from_catalog` exists but has no live pick UX, per `catalog_bind.py:135`) cannot match a `(motor,propeller)` keyed row. Fall back to a `(motor, voltage)`-only lookup row if the table has one, else to today's Model 1 point value labeled `source_type="estimated"`. Never fabricate a propeller match.

**Q3 — Interaction with G5 invalidate / Impl C thrust bridge — does OP thrust still clear `catalog_ref` on diverge?**
Yes, unchanged and correctly so. G5's `invalidate_diverged_catalog_refs` compares the live `per_motor_max_thrust_n` param against the bound SKU's expected value; an OP-sourced thrust is still *a* `per_motor_max_thrust_n` value on the same param key, so any subsequent DSE/manual divergence from it clears `catalog_ref` exactly as today — no interaction change needed, no code to touch. (This also means: if the OP thrust for `(motor,propeller,voltage)` differs from the bare `MotorSpec.thrust_n` the bind path would have set alone, that's fine — divergence detection compares against current state, not against a "first bind" baseline.)

**Q4 — Continuity / ERF: new gaps or reuse existing?**
Reuse. No new gap type is warranted for v1: an OP lookup miss is not a new failure mode distinct from "motor bound, thrust estimated" (today's implicit state) — it's the same physical situation, now *labeled honestly* instead of silently assumed precise. If Engineer later wants a `GAP-OP-UNRESOLVED`-style nudge ("bind a propeller to get a validated operating point"), that's a UX polish item for a later slice, not a v1 requirement — flagged in §13, not built here.

**Q5 — BOM (Impl D) unchanged — confirm no need to reopen.**
Confirmed. `build_component_bom`/`format_bom_lines` project `catalog_ref`/`sku_resolved`/`quantity` from `ComponentSpec` — nothing about thrust provenance. An OP-sourced thrust value doesn't change component identity, resolution, or bucket routing. **No reopening of Impl D BOM schema required or recommended.**

---

## 6. G26 / G27 dependency verdict (mandatory)

| Finding | What breaks | Root cause (traced this session) | Does Phase 2 data/calc contract require it fixed first? |
|---|---|---|---|
| **G27** `LiPo 6S 10000mAh` → `battery_capacity_wh=6.0` | Silent wrong Wh; autonomy cliff | `semantic_intent_adapter.py::SemanticIntentAdapter._parse_value` (lines ~258-276): the LLM proposes `{"variable":"battery_capacity_wh","valor":<raw text>}`, then a **pure regex** `re.search(r"-?\d+(?:\.\d+)?", text)` grabs the **first bare digit sequence** in that text — "6" from "6S" — never inspecting `mAh`/`S`-cell tokens. This feeds `orchestrator.py::_semantic_preseed` → the iterate wizard → `component_writers.py`'s numeric bridge. **This path is entirely separate from and does not touch `bind_battery_from_catalog`**, which is verified correct (`spec.energy_wh` with cell/voltage-aware provenance, `catalog_bind.py:94-102`). | **NO.** The bug lives only in the free-text/semantic-update path. Phase 2 v1 (§8, Option A/B) sources its Operating Point from `catalog_ref`-bound components — the same path `bind_battery_from_catalog` already gets right. A user who free-text-declares a battery today already gets this wrong in Model 1, independent of Phase 2 — it is real, urgent, parallel product debt, but it does not corrupt the catalog-bound data Phase 2 v1 would actually read. |
| **G26** `restrictions` string not updated by free-text constraint changes → `parsed_constraints` stays empty | Requirements INCOMPLETE; blocks ASSEMBLY READY | `state_schema.py::_parse_constraints` (line 20) reads **only** `current_parameters["restrictions"]` (regex `\d+\s*min` / weight regex) and falls back to `objective`. The turn `"cambia restrictions a autonomia minima 15 min"` writes a loose `current_parameters["autonomia"]` key instead of rewriting the `restrictions` string — `_parse_constraints` never sees it, by construction. This is a routing/write-target bug, not a physics or catalog issue — confirmed no code path here touches `MotorSpec`/`BatterySpec`/`PropellerSpec`/calc/sim at all. | **NO.** `_parse_constraints`/`parsed_constraints`/Requirements completeness is entirely orthogonal to thrust/power/current computation. It gates a *readiness verdict* (ASSEMBLY READY), not the *calculation* Phase 2 touches. Confirmed exactly per this contract's own recommendation rule: "G26 usually does not block operating-point math; it blocks ASSEMBLY READY UX." |

**Recommendation: neither G26 nor G27 blocks the Phase 2 data/calc contract. Do not open a debt IC for either as a Phase 2 prerequisite.** Both remain real product debt, independently worth fixing on their own priority (G27 especially — it's a silent-wrong-number defect with user-facing consequences today, in Model 1, with zero Phase 2 involvement). Recommend Engineer keep both on the existing post-Impl-D debt queue, ranked on their own merits, not gated behind Phase 2.

---

## 7. G24 (DSE apply) — deferral confirmed

**Confirmed: Phase 2 investigation does NOT depend on G24.** G24 is entirely about the DSE *exploration/apply* UX — `_handle_apply_exploration` hardcoding `viable[0]`, and abstract params-only candidates outscoring bound-SKU candidates under the (intentionally unchanged) `_score_candidate` policy. None of §2-§5 above required touching `design_explorer.py`, the exploration scoring, or the apply-by-index question. Phase 2 v1's OP lookup happens at the same bridge point Impl C's thrust bridge already occupies (`set_motor_component`), which DSE apply already calls today regardless of G24's UX gap — an OP-sourced thrust would flow through DSE apply exactly as today's SKU thrust does, G24 bug and all. **No elevation; defer as ranked (G24 after Phase 2, per Engineer's own ranking in `IMPLEMENTATION_TASKS.md`).**

---

## 8. Design options for first Implementation Contract (2-3, recommend one)

| Option | Scope | Pros | Cons |
|---|---|---|---|
| **A — Lookup OP** | Hand-curate `operating_points[]` for 2-5 already-seeded motor SKUs (e.g. `sunnysky_r2305_2500`, `brotherhobby_avenger_2500`, `hobbywing_xrotor_2207_2450` — already used in Impl C/D tests) × 1-2 propellers × 1-2 voltages. New reader function (e.g. `resolve_operating_point(motor_sku, propeller_sku, voltage_v) -> OperatingPoint | None`) in `library.py`. Extend `set_motor_component`'s bridge to call it and attach `source_type`. Honest fallback to Model 1 (`source_type="estimated"`) on miss. | Minimal surface (§5 shows zero calc/sim changes needed); matches vision §12 exactly; reuses schema/fields that already exist; testable with the same motors already in the test suite | Coverage is tiny by design (2-5 SKUs) — most projects still fall back to "estimated" |
| **B — Bind-combo** | Require both motor **and** propeller `catalog_ref` before any OP is resolved (no motor-alone fallback); build the missing propeller-bind live UX (today only test-callable, §5 Q2) | Strongest identity story — thrust always traceable to a real pairing | Needs new propeller-pick product UX (Continuity/assist) as a hard dependency — larger than "v1 slice"; contract explicitly wants small first cut |
| **C — Full electro-mech** | Current, ESC limits, efficiency all folded into one calc cut alongside thrust | Closest to the full vision | Too large for v1 per the contract's own instruction; would also require populating the still-nonexistent `ESCSpec`/resistance fields (§3) |

**Recommend Option A.** It is the only one that requires zero new product UX (no propeller-bind flow needed as a hard gate — it degrades gracefully to motor-alone lookup or Model 1 fallback), touches the narrowest code surface (§5 shows the bridge point already exists), and is explicitly what the vision's own §12 implementation-strategy section asks for (small validation set, not full coverage). B is a natural Phase 2 v2 once propeller-bind UX exists for other reasons; C is out of scope for any near-term slice.

---

## 9. What stays Model 1 (unchanged)

- Safety-margin formula, `LOW_MARGIN_THRESHOLD`/`HIGH_LOAD_THRESHOLD`/`LOW_TW_RATIO` thresholds, `FeasibilitySimulator` control flow — **zero changes** (§2.4, §5 Q1).
- Structure mass estimation (`estimate_structure_mass`), total mass, weight, required-thrust, safety-factor math — untouched, no OP involvement.
- Ground-vehicle torque→force path — untouched, aerial-only feature.
- Autonomy formula (`Wh/W × 60`) — unchanged; Phase 2 v1 improves the accuracy of the *inputs* (`per_motor_max_thrust_n`, indirectly `motor_power_w` if the OP carries `power_w`), not the formula.
- ERF-2 electrical-compatibility facts layer — stays a separate, parallel facts projection; Phase 2 v1 does not wire OP data into it (that would be a distinct, later integration question, not part of this slice).
- G5 invalidate-on-diverge semantics — unchanged (§5 Q3).
- BOM/Impl D schema — unchanged (§5 Q5).
- Catalog-aware DSE generation/scoring (Impl C) — unchanged; G24's ranking residual is untouched (§7).

---

## 10. Test / probe inventory

- **Existing tests pinning `thrust_n` as a motor property:** 72 files reference `thrust_n`, 62 reference `per_motor_max_thrust_n` (grep count across `tests/`). These become **regression contracts** for the "no OP match → fall back to today's bare `thrust_n` value" path — Option A's fallback must reproduce today's exact numeric behavior for every SKU not in the new curated table, so none of these 62-72 files should need edits.
- **Tests that would become obsolete/need updating when OP lands:** none identified as *needing* changes for Option A specifically, because Option A is additive-only (new lookup, new fallback label, same numeric fallback value). A future Option B (mandatory propeller pairing) would likely need updates to tests that currently bind a motor with no propeller and expect full thrust — none of which exist as hard requirements today (`bind_propeller_from_catalog` has no live UX yet, so no test currently assumes propeller-optional OP behavior would need mandatory pairing).
- **Sketch of a future CLI probe** (for the eventual Implementation Contract, not built here):
  1. Bind a motor SKU present in the new curated OP table (no propeller bound).
  2. `estado` / thrust display shows the bare-SKU fallback thrust, labeled `estimated`.
  3. Bind a matching propeller SKU also present in the table.
  4. `estado` / thrust display now shows the OP-resolved thrust, labeled `manufacturer_test` (or whatever `source_type` the curated row carries), and the value differs from the bare-SKU fallback (proving the lookup actually fired, not just relabeled the same number).
  5. Bind a motor **not** in the curated table → confirm fallback to Model 1 with honest `estimated` label, never silently claiming `manufacturer_test`.

---

## 11. Recommended approach

Option A (§8), scoped as: (1) curate `operating_points[]` for 2-3 motors × 1-2 propellers × 1 voltage each in the existing seed JSON — real, sourceable numbers only (no invented data); (2) one new pure reader in `library.py` (`resolve_operating_point`); (3) extend the existing thrust-bridge call site in `component_writers.set_motor_component` to try the OP lookup first, falling back to today's bare `thrust_n` behavior unchanged; (4) surface `source_type`/`confidence` somewhere inspectable (`estado`/CLI display) so the "never present estimate as manufacturer_test" hard rule is checkable in the CLI walk. No calc-engine, sim, ERF, BOM, or DSE-scoring changes required for this slice per §5/§9.

---

## 12. ★ Decisions for Engineer

1. **★1 — Provenance placement (§4):** OP provenance as a narrow `OperatingPoint.source_type` field (recommended, option b) vs. extending `PropertyValue.source`'s `Literal` (option a). Recommend (b).
2. **★2 — First-slice scope confirmation (§8):** confirm Option A (Lookup OP, motor+propeller+voltage keyed, 2-3 SKUs) as the first Implementation Contract's scope, deferring B/C.
3. **★3 — G26/G27 verdict ratification (§6):** confirm neither is a Phase 2 prerequisite; confirm they stay on the independent debt queue at Engineer's own ranking (not gated behind Phase 2).
4. **★4 — G24 deferral ratification (§7):** confirm no elevation; G24 stays ranked after Phase 2 per existing `IMPLEMENTATION_TASKS.md` ordering.
5. **★5 — Where the OP-resolved thrust's provenance surfaces (§5 Q1):** a new `ComponentSpec.properties["operating_point"]`-shaped entry vs. a sibling `current_parameters` key vs. deferring surface-decision entirely to the IC. Recommend deferring to the IC (implementation detail, not an architecture question).
6. **★6 — Curated SKU selection for the seed table (§11):** which 2-3 motor SKUs / which propeller(s) / which voltage(s) — needs real sourceable data (datasheet or credible estimate), Engineer/Cursor to supply or approve the specific numbers before the IC is written (this investigation does not fabricate operating-point numbers).

---

## 13. Suggested Implementation Contract outline (slices only, ordered)

```text
P2-1  Curate operating_points[] seed data for 2-3 motor SKUs (real, sourced numbers; ★6)
P2-2  library.py: resolve_operating_point(motor_sku, propeller_sku, voltage_v) -> OperatingPoint | None
                  (pure reader, no I/O beyond existing JSON load; honest None on miss)
P2-3  component_writers.set_motor_component: try OP lookup at existing bridge call site;
                  fall back to today's bare thrust_n behavior unchanged on miss (regression-safe)
P2-4  Surface source_type/confidence in estado / CLI display (★5 resolves exact location)
P2-5  Tests: OP-hit case, OP-miss fallback case (byte-identical to today's numeric behavior),
                  honest-label case (estimated vs manufacturer_test never conflated)
P2-6  CLI probe per §10 sketch
P2-7  (Deferred, not in this IC) propeller-bind live UX, ESCSpec, Option B/C, ERF-2 OP wiring
```

---

## 14. Explicit: implement Phase 2? Not yet — gates remaining

**Not yet.** Remaining gates before any `src/` change:

1. Engineer ★-ratification of §12 (especially ★1 provenance placement and ★2 scope).
2. ★6 — real sourced operating-point numbers supplied/approved (this investigation deliberately does not invent physical data).
3. Cursor writes the Implementation Contract for the P2-1..P2-6 slice (§13) — not this document.

**Compliance check (this investigation):** `git status --porcelain=v1 -- src/ tests/` returns empty at time of writing — no production or test files were modified in the course of this investigation.

---

**End of report.**
