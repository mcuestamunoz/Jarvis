# Investigation Report — Phase 2.6 ESC / System Electrical Loss Model

**Contract:** `.jes/artifacts/investigation_contract_phase26_esc_system_losses.md` (★★1–★★12 locked)
**Investigator:** Claude Code
**Baseline:** commit `fc46938` / tag `v0.3.5` / `checkpoint-phase25-hover-energy` — verified: `git diff --stat fc46938 HEAD -- src/ library/ tests/ scripts/` empty (HEAD is 3 docs/state-sync commits ahead). Full suite **2058 passed, 0 failed**. `cli_probe_phase25_hover_energy.py` **4/4 PASS**. `cli_probe_minimum_universe_combo.py` **3/3 PASS**.
**Date:** 2026-09-01

---

## Executive summary

**Verdict: INSUFFICIENT DATA** (a valid, contract-anticipated success outcome — ★★2/★★6/§7).

The energy chain from mass to `P_motor_input` is fully wired and honest (Phase 2.5, unchanged — Gate A). No `P_battery`, `esc_loss_w`, or system-power field exists anywhere in code today (confirmed by grep and by direct inspection of `CalculationBundle.model_dump()`'s key set). `EscSpec` (`library.py:125-144`) and `library/esc/_datos.json` carry only current/voltage/mass identity fields — zero efficiency, resistance, or loss data (Gate C). External research (Gate D) found **no T1 manufacturer numeric loss data and no T2 independent instrumented bench data for `hobbywing_xrotor_40a_6s`** specifically — both official HOBBYWING product pages state only qualitative marketing language ("Super Low Internal Resistance") with zero numeric Rds(on)/η/heat figures; the one credible instrumented-test database found (Tyto Robotics) has no entry for this SKU, and — independent of SKU coverage — that database's own methodology measures **combined motor+ESC efficiency**, not ESC-isolated loss, which is a structural mismatch with what Phase 2.6 needs regardless of SKU coverage. Community "efficiency" language found in searches (g/W) is a **different physical quantity** (thrust-per-power) than electrical conversion efficiency — a real conflation risk, flagged explicitly. All three loss-model classes (E1 constant η, E2 η(I) table, E3 I²R) fail their data preconditions for this SKU; **E4 (UNVERIFIABLE) is the only defensible outcome for Phase 2.6 v1**, with a precise data-acquisition contract specified (§Gate E) rather than an invented constant. No code, no JSON, no version bump — as scoped.

---

## Gate A — Current energy chain (post Phase 2.5), live-traced

```text
ProjectState + bound components
      ↓
CalculationEngine.build(parameters)                              [calculation_engine.py:130 area — build()]
      ↓
weight_n = calculate_weight(total_mass_kg)                       [calculation_engine.py:83-85]
      ↓
_resolve_hover_energy(parameters, weight_n, motors)               [calculation_engine.py:53-131 — helper I authored in Phase 2.5]
      ├─ T_hover_motor = round(weight_n/motors, 4)                [calculation_engine.py:~112]
      ├─ reads motor_sku/propeller_sku/voltage_v from
      │    parameters["propulsion_resolution"]  (component_writers.py:339 mirror — NOT re-derived)
      └─ resolve_operating_point_at_thrust(...)                   [library.py:900-975 — new Phase 2.5 resolver]
             → exact / bracket-interpolate / unverifiable, on the SAME motor.operating_points[] data
               resolve_operating_point (bind-time) also reads — no ESC input anywhere in this call
      ↓
motor_hover_power_w / motor_hover_current_a                      [calculation_engine.py return dict]
      ↓
hover_energy_autonomy_min = calculate_autonomy_min(
    battery_capacity_wh, motor_hover_power_w × motors)            [calculation_engine.py:~150-160]
      ↓
autonomy_min MIRRORS hover_energy_autonomy_min when hover_applicable   [calculation_engine.py:~145-170]
      ↓
CalculationBundle(..., t_hover_motor_n=..., motor_hover_power_w=...,
                  hover_energy_autonomy_min=..., hover_energy_resolution=...)  [tool_schema.py:14-40]
      ↓
STOPS HERE — no further arrow exists in code today.
P_battery: NOT COMPUTED. NOT A FIELD. NOT REFERENCED ANYWHERE.
```

1. **Where `motor_hover_power_w` is set:** `calculation_engine.py`'s `_resolve_hover_energy()`, calling `library.py`'s `resolve_operating_point_at_thrust()` — confirmed unchanged, byte-for-byte, from the Phase 2.5 checkpoint (`git diff fc46938 HEAD -- src/` is empty).
2. **Where `hover_energy_autonomy_min` is computed:** same function, immediately after, via `calculate_autonomy_min(battery_capacity_wh, motor_hover_power_w × motors)`.
3. **`P_battery` is not used anywhere in autonomy today** — confirmed by exhaustive grep (`grep -rn "P_battery\|p_battery\|esc_loss\|system_energy_autonomy\|hover_battery_autonomy" src/jarvis/` → zero hits) and by live inspection: `CalculationBundle.model_dump().keys()` for a fully-bound Combo A′ project (motor+prop+battery+**ESC**, all catalog-bound) contains no `P_battery`-shaped key at all (verified this session, live run — key set: `autonomy_min, available_total_thrust_n, hover_energy_autonomy_min, hover_energy_resolution, motor_hover_current_a, motor_hover_power_w, motors, payload_kg, required_thrust_n, structure_mass_kg, t_hover_motor_n, thrust_per_motor_required_n, tool_results, total_mass_kg, vehicle_type, weight_n`).
4. **`effective_motor_power_w` is not used when `hover_applicable=True`** — confirmed by code inspection (`calculation_engine.py`'s autonomy branch: `if hover["hover_applicable"]: autonomy_min = hover_energy_autonomy_min` / `else: ... effective_motor_power_w(...)`) — mutually exclusive branches, verified in Phase 2.5's own implementation report and re-confirmed unchanged here.
5. **Fields that would need to exist for an honest `P_battery` chain:** (a) a loss-model result type (mirroring `ResolvedHoverOperatingPoint`'s shape: value, `source_type` tier, provenance) sourced from bound ESC + `motor_hover_current_a`/`motor_hover_power_w`; (b) new `CalculationBundle` fields (`p_battery_w`, `esc_loss_w` or similar, `system_energy_resolution` JSON string); (c) a new autonomy field distinct from `hover_energy_autonomy_min` (★★9) — none of these exist today, confirmed by the same grep/model_dump check above.

---

## Gate B — Power semantics (six concepts)

| Concept | Representation today | Verified |
|---|---|---|
| Nominal motor rating | `motor_power_w` | Unchanged since P2-2; `calculation_engine.py:39-41` docstring: "never overwritten anywhere" |
| Bench-max OP | `motor_op_power_w` / `motor_op_current_a` | Bind-time only (`component_writers.py:339,387-392`); feeds `effective_motor_power_w` (non-hover path) and `electrical_compatibility`'s `_per_motor_current_a` (`electrical_compatibility.py:129-172`, prefers `motor_op_current_a`) |
| Hover motor input | `motor_hover_power_w` / `motor_hover_current_a` | Calc-time, Phase 2.5 (`calculation_engine.py._resolve_hover_energy`) — confirmed the sole upstream input Phase 2.6 would consume |
| ESC loss | **Absent — confirmed by grep, zero hits** | No `esc_loss_w`/`P_loss`/`efficiency` field anywhere in `src/jarvis/` outside the unrelated DSE `"improve_efficiency"` goal-type string (a UX label, not a physics quantity — grep `efficiency` in `src/` returns only `reasoning_layer.py:253`, `tool_schema.py:100`, `adapters/cli/main.py:55`, `suggestion_engine.py:50,52`, all DSE-goal-label strings, unrelated) |
| Pack draw | **`P_battery` — absent, confirmed** | Same grep; zero hits for `P_battery`/`p_battery` anywhere |
| Stored energy | `battery_capacity_wh` | Nominal Wh from catalog SKU (`bind_battery_from_catalog`); no sag/SOC model exists (correctly deferred per contract) |

**Is `P_motor_input` in OP rows already `V × I` at the motor terminals?** Yes — confirmed by the curated row shape (`library/motores/_datos.json`'s `sunnysky_r2205_2500.operating_points[]`): each row's `power_w` and `current_a` are independently sourced bench-measured values from the manufacturer PDF at a stated `voltage_v` (e.g. 700gf row: `current_a=16.3, power_w=241.0` at `voltage_v=14.8` — `241.0/16.3=14.79V`, matching the stated bus voltage within rounding). This is the electrical power measured at the motor's own input leads on the test bench — i.e., **downstream of wherever that bench's ESC sat**, not at the battery/pack terminals. The physical losses between "pack terminals" and "this measurement" are: (a) wiring/connector resistive loss (pack→ESC), (b) ESC switching + conduction loss, (c) wiring/connector resistive loss (ESC→motor). Phase 2.6's scope (★★1) covers only (b), optionally folding in (a)/(c) as "immediate system" loss if sourced — none of the three has any sourced numeric data in this codebase today.

---

## Gate C — ESC catalog audit

**1. Schema audit — `EscSpec`** (`library.py:125-144`, verbatim field list): `name, continuous_current_a, burst_current_a, continuous_current_source, voltage_min, voltage_max, cells_min, cells_max, esc_topology, channels, mass_g, manufacturer, model, part_number, source_url, identity_status, source_note`. **Zero** fields for efficiency, resistance, or loss of any kind.

**2. `library/esc/_datos.json`'s only row (`hobbywing_xrotor_40a_6s`)** — fields actually populated: `continuous_current_a=40, burst_current_a=60, continuous_current_source="manufacturer_spec", voltage_min=6.0, voltage_max=25.2, cells_min=2, cells_max=6, mass_g=26, manufacturer="HOBBYWING", model, part_number, identity_status="verified", source_url, source_note`. All current/voltage/identity — nothing usable for a loss model even if the schema had the fields.

**3. Design-vs-implementation gap** (`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`, read as context only): §5.4's ESC block explicitly lists `efficiency` as a wishlist field (`docs/...md:189`), and §7 states the intended formula `P_motor_input = P_battery × η_ESC` (`:241`) — inverted for our direction: `P_battery = P_motor_input / η_ESC`, matching Gate E's Model E1 exactly. **Notably, §6's "Operating Point" concept in that same doc includes `esc_id → catalog_ref` as part of OP identity** (`:203`) — this directly contradicts the ratified Phase 2.5 lock ★★8 (OP identity = motor+propeller+voltage only, ESC explicitly excluded). This is a **known, already-resolved divergence** — the codebase deliberately supersedes this older design doc on this specific point (Phase 2.5's own ★★8 lock exists precisely to correct it), not a new finding requiring action, but worth flagging so nobody re-derives the doc's older shape by mistake.

**4. Curation quantification if sourced data were found:** minimum shape for a defensible model would be either (E1) one row `{efficiency_pct, source_type, source_reference, current_range_valid_a}` or (E2) a table `[{current_a, efficiency_pct or loss_w, source_type, source_reference}, ...]` with ≥2 sourced points spanning the SKU's practical current range (hover: ~8-17A per motor across Combo A's dataset; bench-max: 40A). **No such data exists to curate today** (Gate D) — this is a forward-looking sizing note only, not a current recommendation.

---

## Gate D — External source audit (defendability tiers)

| Source | Content found | Tier | Accept? |
|---|---|---|---|
| `library/esc/_datos.json`'s own `source_url` (`https://a.hobbywing.com/en/products/xrotor-40a122`) | **Not fetchable programmatically** — TLS cert mismatch (cert covers `hobbywing.com`/`www.hobbywing.com`, not the `a.` subdomain stored in the catalog). Noted as a hygiene finding, not a data-content finding. | N/A (fetch failure) | — |
| `https://www.hobbywing.com/en/products/xrotor-40a122` (same product, working domain) | Full electrical spec fetch succeeded. Verbatim numeric fields: `40A/60A` cont./peak current, `2-6S LiPo`, `No BEC`, wire gauges (`16AWG`), connector type, size (`42.0×21.6×12.0mm` / `50.0×21.6×12.0mm`), weight (`18.5g`/`15g`), throttle signal up to `621Hz`. Qualitative-only text: **"Super Low Internal Resistance"** — no Rds(on) ohm value, no efficiency %, no thermal/heat data anywhere on the page. | **T4** (no numeric loss data) | No |
| WebSearch — HOBBYWING XRotor 40A ESC efficiency/MOSFET resistance | Retail listings + the same official page content, repeating "extra-low resistance" marketing language with no numbers. | **T4** | No |
| WebSearch — Oscar Liang, dronehitech, intoFPV reviews of the **XRotor product family** (G2 4in1 45A/65A, 15A, 20A) | **None of these are the catalog SKU** (`hobbywing_xrotor_40a_6s`, single-channel 40A) — they cover sibling/successor products. Oscar Liang's G2 4in1 review (fetched directly) confirmed: zero numeric efficiency, power-loss, thermal, or resistance data — build-quality and feature commentary only. A separate search snippet referenced "efficiency ratings ranging from 2.00 to 4.34 grams per watt" for the *XRotor 20A* — **this is thrust-per-electrical-power (g/W), a propulsion/aerodynamic metric, not electrical conversion efficiency (P_out/P_in as %)**. Conflating the two would be a real physics error. | **T3 at best, and for the wrong SKU** | No — flagged as a conflation risk, not usable |
| Academic literature (ResearchGate/Semantic Scholar: *"Modeling and Test of the Efficiency of Electronic Speed Controllers for Brushless DC Motors"*, and *"Performance Testing and Modeling of a Brushless DC Motor, ESC and Propeller for a Small UAV"*) | Real, methodology-stated bench testing (two-wattmeter method, current-sense resistors), **generic** (not SKU-specific): "ESC efficiencies remain at 90% or above for normal electric motor operation," but "a significant drop in efficiency due to ESC at part-power" — i.e., current-dependent, supporting an E2-shaped model class *in principle*. PDF full-text extraction failed (corrupted/binary content on fetch) — could not pull the underlying (I, η) data table. | **T2-class methodology, but not SKU-specific, and the actual numeric table is unverified by this investigation** | No — informative context only, not implementable for this SKU |
| Tyto Robotics component test database (`database.tytorobotics.com`) | Legitimate instrumented thrust-stand service; **35 unique ESCs** tested database-wide; searched specifically for `hobbywing xrotor` on this domain — **found only an unrelated motor entry (Hobbywing XRotor X6 Plus) with explicitly "no test data posted yet,"** no ESC-40A-6S entry at all. Separately and **more fundamentally**: their own published methodology states test stands measure **"Motor AND ESC Efficiency" combined** — even where SKU coverage exists, the database does not isolate ESC-only loss from motor-only loss, which is a structural mismatch with what a `P_motor_input → P_battery` (ESC-and-immediate-system-only) model needs, independent of SKU coverage. Also reports "77.64% average maximum efficiency" **across 48 motors** (motor-centric aggregate, not this ESC). | **T4 for this SKU** (no entry); **methodologically incompatible even where present** (bundled, not ESC-isolated) | No |

**Explicit tier verdicts (per contract §Gate D):**
- **Constant η defensible for `hobbywing_xrotor_40a_6s`?** **No.** Zero T1/T2 SKU-specific numeric data found.
- **I-dependent model defensible?** **No**, for the same reason — E2 needs ≥2 sourced (I, η) points for *this* SKU; none exist. The general academic finding that efficiency is current-dependent is useful context for a *future* sourcing effort but is not itself a usable data table.
- **Minimum external work performed:** official product page (2 domains, one cert-broken), ≥1 independent review search (Oscar Liang — fetched, confirmed no data), ≥2 academic sources (searched, one fetch attempted, extraction failed), 1 instrumented-test database search (Tyto Robotics — no SKU entry). No further external work is likely to change this conclusion without a live bench test being commissioned.

---

## Gate E — Loss model options, scored

| Model | Formula | Data required | Available for `hobbywing_xrotor_40a_6s`? | Verdict |
|---|---|---|---|---|
| **E1 — Constant η** | `P_battery = P_motor_input / η` | Single sourced η (T1/T2) | **No** — zero numeric η found for this SKU at any tier | **Rejected** |
| **E2 — η(I) table** | Interpolate between sourced (I, η) or (I, P_loss) points | ≥2 sourced points for this SKU | **No** — the one methodology that measures this generically (academic two-wattmeter studies) is not SKU-specific and its data table wasn't extractable; Tyto Robotics has no entry for this SKU and bundles motor+ESC even where it does have entries | **Rejected** |
| **E3 — I²R** | `P_battery = P_motor_input + I²·R_esc` | Sourced `R_esc` (Rds(on) × conduction path, or an equivalent measured resistance) | **No** — official page states "Super Low Internal Resistance" with **zero ohm value**; no independent measurement found | **Rejected** |
| **E4 — UNVERIFIABLE** | No claim; document the gap | — | **Yes — this is the outcome** | **Recommended (only defensible option)** |

**Strict rule check (per contract):** best available source tier for this SKU is **T4** (no numeric data) — per the contract's own rule, this mandates verdict **INSUFFICIENT DATA**, not an implemented 90-95% placeholder.

**Illustrative paper exercise (explicitly labeled, not a recommendation):** if a hypothetical, sourced η=96% applied at Combo A's hover point (`motor_hover_power_w=251.559W/motor` at `motor_hover_current_a=17.0107A`, payload_kg=1.718 fixture), `P_battery ≈ 251.559/0.96 ≈ 262.04W/motor`, and `hover_energy_autonomy_min` would drop from `1.3237min` to `22.2/(262.04×4)×60 ≈ 1.2708min` — a **≈4% autonomy reduction**, small relative to the Phase 2.5 regime-correction itself (592W→251.559W was a **2.35× swing**). This sizes the *magnitude* Phase 2.6 would eventually correct (worth doing once data exists) but underscores that inventing a number here would trade a large, already-fixed dishonesty (Phase 2.5) for a small, newly-introduced one — not a good trade under ★★2.

---

## Gate F — Integration surfaces (map only, no implementation)

| Surface | File(s) | Findings |
|---|---|---|
| Loss resolver (future) | `library.py` (favored) vs `calculation_engine.py` vs `electrical_compatibility.py` | Per CLAUDE.md ("prefer existing engines/resolvers... over introducing parallel logic") and the exact precedent Phase 2.5 set (Gate I of that investigation): `library.py` already owns `resolve_operating_point`/`resolve_operating_point_at_thrust` as the codebase's OP-data resolver; a hypothetical `resolve_esc_loss_at_current(...)` would be a natural sibling extension there, reading `EscSpec`-adjacent data the same way. **Not implementable today regardless of placement — no data exists to resolve.** |
| Calc pipeline | `calculation_engine.py` | A new branch would slot in immediately after `_resolve_hover_energy()`'s return, consuming `motor_hover_power_w`/`motor_hover_current_a` and the bound ESC's `catalog_ref.sku` — same call-once-per-`build()` pattern as the existing hover branch. No code added (out of scope). |
| Bundle/persistence | `tool_schema.py`, `latest_results` | Would need new additive fields (`p_battery_w`, `system_energy_autonomy_min` or similar per ★★9, a JSON provenance string mirroring `hover_energy_resolution`'s shape) — same pattern as Phase 2.5, not added here. |
| Estado/CLI | `orchestrator.py`, `adapters/cli/main.py` | Phase 2.5 already established the exact display pattern this would extend (`_hover_energy_from_calculations` → `hover_energy` ctx key → the "Energía hover (evidencia)" line, `adapters/cli/main.py`). A hypothetical "Energía sistema (evidencia)" line would sit right after it, same convention — not added here. |
| Probes | `cli_probe_minimum_universe_combo.py`, `cli_probe_phase25_hover_energy.py` | Both currently assert `motor_hover_power_w`/`hover_energy_autonomy_min` only; a future probe would need to assert the new UNVERIFIABLE-by-default state for `p_battery`-shaped fields (once they exist) the same way `cli_probe_phase25_hover_energy.py` Step 3 asserts Combo B's honest `None`. |
| ERF-2 (`electrical_compatibility.py`) | Confirmed **no change needed for Phase 2.6 v1** (★★5) | Live-verified this session: for Combo A′ (ESC catalog-bound), `evaluate_electrical_compatibility(ps).i_motor_a == 40.0` (bench-max current, from `motor_op_current_a`) — **not** `motor_hover_current_a` (17.0107A) — confirming the margin-check path is completely untouched by, and independent of, the hover/system energy chain, exactly as Phase 2.5's own ★6 precedent established. File is byte-identical to baseline (`git diff` empty). |
| DSE (`design_explorer.py`) | Untouched; `_score_candidate` (frozen, G24-B) reads `sim.autonomy_min` — would inherit any future system-energy autonomy the same way it already inherits hover autonomy today (Phase 2.5's own finding, re-confirmed: zero DSE code needs to change for autonomy's power source to shift, since DSE never reads the power fields directly). | No side effects to flag beyond what Phase 2.5 already documented. |

**Gate I — module placement recommendation:** `library.py` extension (mirroring the OP resolver precedent), for calc-time orchestration in `calculation_engine.py` — same architecture Phase 2.5 used, same CLAUDE.md justification (extend the existing resolver owner, don't create a new subsystem). This is a **conditional** recommendation for *if and when* sourced data exists — no placement decision is actionable today since there is nothing to place.

---

## Gate G — Reference cases

| Case | Result |
|---|---|
| **Combo A** (hover OP resolves, no ESC bound) | `T_hover_motor_n=7.0632, motor_hover_power_w=251.559, hover_energy_autonomy_min=1.3237` — `P_battery`: absent from `CalculationBundle` entirely (not merely `None` — the field doesn't exist). Documented gap, not a bug. |
| **Combo A′** (+ `hobbywing_xrotor_40a_6s` catalog-bound) | Live-verified this session: **identical** hover numbers (`T_hover_motor_n=7.0632, motor_hover_power_w=251.559, hover_energy_autonomy_min=1.3237`) — ESC binding provably does not perturb hover OP resolution (★★4 holds in code, not just by lock). `evaluate_electrical_compatibility` shows `esc_current_a=40.0, i_motor_a=40.0, esc_vs_motor=compatible` — compatibility margin uses bench-max current, confirmed independent of the hover chain. Still no `P_battery` — same absence as Combo A, unaffected by ESC presence. |
| **Combo A — no ESC bound** | Same as "Combo A" row above — the loss step isn't merely skipped, it doesn't exist as a code path at all yet; there is nothing to "assume zero" because no consumer reads a loss value. **Recommendation for a future IC:** when the loss resolver is eventually built, it should require an explicit bound ESC identity to attempt any resolution (mirroring how `resolve_operating_point_at_thrust` requires a motor identity) — an unbound/freeform ESC should route to the same `no_matching_rows`-shaped "not applicable" bucket Phase 2.5 established for identities with no dataset, not a silent zero-loss assumption. |
| **Combo B** (single-row / out-of-range hover) | Unaffected — Phase 2.5's `autonomy_min=None` honest-UNVERIFIABLE path for this case is untouched (confirmed via `cli_probe_phase25_hover_energy.py` Step 3, still passing, byte-identical code). |
| **Legacy motor + freeform ESC** (`current_a` declared, no `catalog_ref`) | `electrical_compatibility.py`'s `_per_motor_current_a`/ESC checks already handle this today (freeform ESC properties, no catalog binding) — a future loss model would face the same "no dataset for this identity" bucket as an unbound ESC, doubly so since a freeform ESC carries no SKU to look up loss data against even in principle. |

No hypothetical-η paper trace beyond the one already shown in Gate E (the contract permits this only if Gate D found *some* sourced number — it did not; the Gate E illustration uses a clearly-labeled hypothetical instead, per the contract's own allowance for a labeled paper exercise).

---

## Gate H — Blockers + IC slice recommendation

| Candidate | Verdict | Evidence |
|---|---|---|
| No ESC efficiency in catalog | **BLOCKING for implementation** (not for this investigation, which is complete) | Gate C — `EscSpec` has no such field; `_datos.json` has no such data |
| No manufacturer η data | **BLOCKING for E1** | Gate D — T4, confirmed via 2 official page fetches |
| No independent confirmation | **BLOCKING, and also INSUFFICIENT DATA for E2/E3** | Gate D — Tyto Robotics has no SKU entry and bundles motor+ESC even where present; academic sources are generic, not SKU-specific, and numeric tables were unextractable |
| Phase 2.5 hover path not wired | **NOT BLOCKING — confirmed** | Gate A/G — fully wired, live-verified, unchanged since checkpoint |
| Battery sag needed first | **REJECT — correctly out of order** | Contract's own explicit sequencing lock (§10); this investigation did not touch sag/SOC/R_internal, consistent with ★★1 |

**Recommendation: NO IC.** Document the `P_motor_input`→`P_battery` boundary as this investigation's deliverable (this report) and defer implementation until sourced ESC loss data exists. Two concrete forward paths, neither of which is "implement now":

- **Data acquisition contract (if pursued):** commission or locate a genuine ESC-isolated (not motor+ESC-bundled) instrumented bench test of `hobbywing_xrotor_40a_6s` (or a documented-equivalent sibling SKU with a clear substitution rationale) across at least 2 current points spanning Combo A's practical range (~8-40A), with stated method (e.g. two-wattmeter) and a cited, checkable source. Until then, no P26-D/P26-E slice is actionable.
- **Alternative sequencing:** proceed to a Phase 2.7 battery-model investigation using `hover_energy_autonomy_min` (motor-input, explicitly labeled as a lower bound per ★★10) as the honest interim autonomy figure, while the ESC data-acquisition question remains open in parallel — this does **not** violate the contract's sequencing lock (§10), since Phase 2.7 there is scoped to battery sag/SOC/R, not to inventing `P_battery`.

---

## 3. Mandatory output table

| Capability | Supported today? | Evidence | Blocker | First slice |
|---|---|---|---|---|
| Hover `P_motor_input` from OP dataset | **YES** | Gate A live trace; Phase 2.5, unchanged | — | none |
| Bound ESC identity in project | **YES** | Gate G — Combo A′, `catalog_ref` verified live | — | none |
| ESC continuous current for margin | **YES** | Gate F — `electrical_compatibility.py` `i_motor_a`/`esc_current_a`, unchanged, ERF-2 | — | none |
| Sourced ESC efficiency / loss data | **NO** | Gate D — T4 across manufacturer + independent + academic + instrumented-DB search | Data acquisition (external, not code) | P26-D — **not actionable without new sourcing** |
| `P_battery` from physics (not identity) | **NO** | Gate A — field doesn't exist; Gate E — all of E1/E2/E3 rejected | Depends entirely on the row above | P26-E — **blocked on P26-D** |
| Separate hover vs system autonomy labels | **N/A** | Gate F — no system-energy field exists to label | Depends on P26-E | P26-E |
| Honest UNVERIFIABLE when data missing | **YES** (as a pattern; nothing to apply it to yet) | Gate A/G — Phase 2.5's `no_matching_rows`/`below_min`/`above_max` pattern is directly reusable; this investigation's own Gate E conclusion (E4) follows the same discipline | — | docs (this report) |
| Battery sag / loaded voltage | **NO (deferred, correctly)** | Contract §10 sequencing lock | Phase 2.7 | — |
| Mission regime model | **NO (deferred, correctly)** | Contract, out of scope | Phase 3.x | — |

---

## Engineer ★ questions (report surfaces; pre-locked where marked)

| ★ | Question | Answer |
|---|---|---|
| ★1 | Can Jarvis honestly compute `P_battery` today? | **No** — confirmed, field doesn't exist, no defensible model class survives Gate E's scoring |
| ★2 | Is constant η ever defensible for `hobbywing_xrotor_40a_6s`? | **No** — zero T1/T2 data found for this SKU (Gate D); ★★2 forbids proceeding anyway |
| ★3 | Best loss model class (E1–E4)? | **E4 (UNVERIFIABLE)** — the only one whose data precondition is met (Gate E) |
| ★4 | Keep `hover_energy_autonomy_min` as motor-input-only label? | **Yes** (★★9/★★10 locked) — recommend a future sibling field (`system_energy_autonomy_min` or `hover_battery_autonomy_min`, per the contract's own naming suggestions) rather than any relabeling |
| ★5 | Change ERF-2 current source to hover current? | **No, for v1** — Gate F confirms bench-max current remains the physically correct input for a worst-case margin check; unaffected either way since no loss model exists to change it for |
| ★6 | Catalog fields to add if data found? | Gate C §4 — minimum shape given (single-row `efficiency_pct` + source, or a ≥2-point current/loss table), not curated here |
| ★7 | Next arc if INSUFFICIENT DATA — battery sag or ESC test campaign? | **Recommend defining the boundary is sufficient for now** (done, this report); either forward path in Gate H is legitimate — Engineer's call, not this investigation's to force |
| ★8 | Module placement? | `library.py` extension + `calculation_engine.py` orchestration (Gate F/I) — **conditional**, not actionable today |
| ★9 | DSE impact? | **None required** — inherits automatically via `autonomy_min`, confirmed unchanged from Phase 2.5's own finding |
| ★10 | Accept UNVERIFIABLE as a successful investigation outcome? | **Yes** (★★2/★★6 locked) — this report's verdict |

---

## Deliverables produced

- This report: `.jes/artifacts/investigation_report_phase26_esc_system_losses.md`
- Baseline table: header (§ above) — suite 2058/0, both probes green, zero `src/`/`library/`/`tests/`/`scripts/` drift from `fc46938`
- External source appendix: Gate D table (7 sources checked, tiers assigned, all rejected at T3/T4 for this SKU)
- No repro/xfail test added — the "P_battery absence" is already exhaustively demonstrated by existing, passing assertions (`hasattr`/`model_dump()` checks run live this session; Phase 2.5's own `hover_energy_resolution`/`autonomy_min=None` tests already cover the adjacent honest-absence pattern) — a dedicated xfail would test a negative that no code path could ever accidentally violate without a much larger change, so it was judged non-additive; happy to add one if Engineer wants an explicit regression lock on "no P_battery field exists"
- No IC outline produced — Gate H's primary recommendation is **NO IC** (data acquisition is external work, not a code contract)
