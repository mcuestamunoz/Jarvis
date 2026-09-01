# Investigation Report — Phase 2.7 Battery Voltage / Sag / SOC Model

**Contract:** `.jes/artifacts/investigation_contract_phase27_battery_voltage_sag.md` (★★1–★★12 locked)
**Investigator:** Claude Code
**Baseline:** commit `fc46938` / tag `v0.3.5` / `checkpoint-phase25-hover-energy` — verified: `git diff --stat fc46938 HEAD -- src/ library/ tests/ scripts/` empty. Full suite **2058 passed, 0 failed**. `cli_probe_phase25_hover_energy.py` **4/4 PASS**. `cli_probe_minimum_universe_combo.py` **3/3 PASS**.
**Date:** 2026-09-01

---

## Executive summary

**Verdict: INSUFFICIENT DATA** (a valid, contract-anticipated success outcome — ★★4/★★8/§7), with one useful partial finding: `battery_capacity_wh` is confirmed to be exact nameplate energy (`nominal_voltage × capacity_Ah`, verified `14.8V × 1.5Ah = 22.2Wh` bit-for-bit against the catalog row), not a loaded or usable-under-hover-load figure — the ★★3-mandated audit's answer is unambiguous.

No sourced `R_internal`, OCV(SOC) curve, or C-rate capacity-derating table exists for `lipo_4s_1500mah` at any credible tier (Gate D: catalog `source_url`, manufacturer-adjacent retailer pages, and multiple generic-LiPo/academic searches all returned either zero numeric data or only qualitative marketing language — "ultra-low internal resistance" with no ohm value, mirroring Phase 2.6's exact finding pattern for the ESC). Real academic equivalent-circuit methodology exists (Randles/RC models) and real flight-controller practice exists (ArduPilot estimates `R_internal` **online, during flight**, from live telemetry) — neither yields a static, sourced constant this design-time tool could honestly cite for this SKU.

The contract's own central question (★★7, `I_load` without `P_battery`) resolves cleanly: **I1 is rejected** (silently assumes zero ESC loss), **I2 is rejected on inspection — it is not actually independent of the Phase 2.6 boundary**, functionally re-deriving the forbidden `P_battery = P_motor_input` identity through the circuit-solve back door (flagged as a finding, not just scored), **I3 yields only a one-sided, assumption-laden lower bound** (not a usable envelope), leaving **I4 (UNVERIFIABLE)** as the only defensible policy. This blocks M1/M2 (both require `I_load` and `R_internal`) and M4 (needs sourced Peukert `n`); M3 (C-rate derating only, no `I_load` needed) is data-blocked independently (no derating table found) rather than blocked by ★★7 — but is contextually meaningful, since a live-verified paper check shows Combo A's hover current alone is **≈45.4C** on this small 100C-rated pack (well above the "low-C, negligible derating" regime), meaning a real derating correction — if sourced — would likely matter, not just be a rounding error. **Recommendation: NO IC.** `hover_energy_autonomy_min` remains the correct interim honest figure (★★6, untouched).

---

## Gate A — Current battery energy chain, live-traced

```text
library/baterias/_datos.json  lipo_4s_1500mah: energy_wh=22.2, nominal_voltage=14.8,
                               capacity_mah=1500, c_rating=100, max_continuous_current_a=150
      ↓
bind_battery_from_catalog("lipo_4s_1500mah")                      [catalog_bind.py:81-106]
      → projects spec.energy_wh AS-IS into PropertyValue("battery_capacity_wh")  (:100-102)
      ↓
set_battery_component(ps, spec, capacity_wh)                       [component_writers.py:152-199]
      → current_parameters["battery_capacity_wh"] = capacity_wh    (:170-171, direct assignment, no transform)
      → current_parameters["battery_mass_kg"] from spec.mass_g/1000 (catalog-bound path)  (:176-183)
      ↓
CalculationEngine.build(parameters)                                [calculation_engine.py]
      ↓
_resolve_hover_energy(...)  →  motor_hover_power_w=251.559,
                                motor_hover_current_a=17.0107        [Phase 2.5 — unchanged]
      ↓
calculate_autonomy_min(battery_capacity_wh, motor_hover_power_w × motors)
      = (22.2 / (251.559 × 4)) × 60 = 1.3237 min                    [tools/electricity.py:25-33]
      → PURE Wh/W arithmetic — zero voltage terms, zero SOC, zero R
      ↓
hover_energy_autonomy_min = 1.3237  (unchanged, live-reconfirmed this session)
STOPS HERE.
No V_loaded, no SOC, no R_internal, no usable-energy-under-load anywhere in this path.
```

1. **Bind → params:** `bind_battery_from_catalog` (`catalog_bind.py:81-106`) reads `BatterySpec.energy_wh` and projects it byte-for-byte into `battery_capacity_wh` — no voltage, current, or load term enters at this step.
2. **`_resolve_hover_energy` → `motor_hover_power_w`/`motor_hover_current_a`:** confirmed unchanged from Phase 2.5/2.6 (`git diff` empty for `calculation_engine.py`, `library.py`).
3. **`calculate_autonomy_min`** (`tools/electricity.py:25-33`): `autonomy_min = (battery_capacity_wh / total_power_w) × 60` — live-verified this session, `1.3237min`, bit-identical to the Phase 2.5/2.6 reports' own numbers.
4. **No voltage sag, SOC, or R term anywhere** — confirmed by reading the full body of `tools/electricity.py` (36 lines total) and `calculation_engine.py`'s autonomy branch: neither references `nominal_voltage`, any resistance concept, or a charge-state variable.
5. **`P_battery` still absent** (Phase 2.6 regression check) — re-confirmed live this session: `CalculationBundle.model_dump()`'s key set for a fresh Combo A build is unchanged from the Phase 2.6 report's own list; no `p_battery`/`P_battery`-shaped key exists.
6. **Fields needed for an honest loaded-battery autonomy:** a sourced `R_internal` (or equivalent-circuit parameter set), a sourced `V_oc(SOC)` relationship (or at minimum a stated `V_oc` at a defined SOC), an explicit `I_load` policy (★★7 — resolved below as UNVERIFIABLE), a `V_loaded` derivation, a usable-energy-under-load integration, and a new `CalculationBundle` sibling field + JSON provenance string mirroring `hover_energy_resolution`'s shape. None exist today.

---

## Gate B — Battery power/energy semantics

| Concept | Representation today | Finding |
|---|---|---|
| Nameplate/catalog energy | `BatterySpec.energy_wh` → `battery_capacity_wh` | **Confirmed nameplate, at nominal voltage, no stated cutoff.** `energy_wh=22.2` exactly equals `nominal_voltage(14.8) × (capacity_mah(1500)/1000)` — live-verified to full float precision (`22.200000000000003` vs `22.2`, rounding-only difference). No discharge cutoff voltage, no derating, no measured (vs. computed) provenance distinction exists in the schema. |
| Nominal voltage | `nominal_voltage` (14.8V, `= cells(4) × 3.7`) | Used for OP voltage-matching (Phase 2.5's `_resolve_battery_voltage_v`) and as the implicit basis for `energy_wh`'s own arithmetic (above) — **never** a measured/loaded terminal voltage. |
| Capacity (Ah) | `capacity_mah=1500` | Consistent with `energy_wh` (above) — no mismatch found for this SKU. |
| C-rate limit | `c_rating=100`, `max_continuous_current_a=150` | ERF-2 margin only (`electrical_compatibility.py:204-226,278-288`) — a pass/fail current-vs-limit check, zero energy-depletion physics; confirmed by reading the full function bodies (no Wh/energy term referenced). |
| Hover motor input power | `motor_hover_power_w` | Upstream **demand**, Phase 2.5 — not pack-side draw (Phase 2.6 boundary). |
| Pack-side power | **`P_battery` — absent** | Re-confirmed absent this session (Gate A.5) — Phase 2.6 boundary intact, untouched by this investigation per ★★2. |
| Loaded terminal voltage | **Absent** | No code path computes this; Gate E scores whether it's estimable. |
| Usable energy under load | **Absent** | Same — `energy_wh` is used as-is, unconditionally, regardless of load magnitude. |
| Autonomy (motor-input) | `hover_energy_autonomy_min` | Frozen per ★★6 — unchanged, re-verified live (`1.3237min`). |
| Autonomy (loaded-battery) | **Absent** | No sibling field exists; Gate H concludes none should be added yet (no data to back it). |

---

## Gate C — Battery catalog audit

**1. Schema** (`library.py:93-118`, `BatterySpec`, verbatim): `name, chemistry, energy_wh, mass_g, cells, nominal_voltage, capacity_mah, max_continuous_current_a, c_rating, design_space, operating_points, manufacturer, model, part_number, source_url, identity_status` (+ a `source_note` field confirmed by direct JSON inspection, not separately listed in the dataclass excerpt but present in every row). **Zero fields for `internal_resistance`, OCV, or any discharge-curve shape** — `operating_points: tuple[dict, ...] = ()` exists as a field (mirroring `MotorSpec`'s pattern) but is **never populated** for any battery row in `library/baterias/_datos.json` — live-confirmed: `default_library.get_battery("lipo_4s_1500mah").operating_points == ()`.

**2. `lipo_4s_1500mah` deep audit** (`library/baterias/_datos.json:29-45`): `chemistry="lipo", energy_wh=22.2, mass_g=183, cells=4, nominal_voltage=14.8, capacity_mah=1500, c_rating=100, max_continuous_current_a=150 (source: "derived_from_c_rating"), manufacturer="CNHL", model="Black Series 4S 1500mAh 100C XT60", part_number="1501004BK", identity_status="verified", source_url=<Baltic Drones listing>`. **Consistency check (★★3 mandated): `energy_wh` vs `nominal_voltage × capacity_Ah` — exact match**, confirmed to float precision above. No `max_continuous_current_a` independent source beyond `c_rating` arithmetic (i.e. no separately-measured discharge-limit figure — it's a derived, not tested, value, per its own `_source` tag).

**3. Design-vs-implementation gap:** `docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md` §5.3 (`:153-165`, read as context only) lists `internal_resistance` as a battery-schema wishlist field — **not implemented**, matching the contract's own lean exactly. No contradiction with any ratified lock found here (unlike Phase 2.6's finding about OP identity, this doc's battery section doesn't conflict with any Phase 2.5/2.6/2.7 lock — it's simply an unimplemented wishlist item).

**4. Curation quantification (forward-looking only, not recommended today):** a defensible M1 would need one sourced `{r_internal_mohm, source_type, source_reference, conditions(SOC/temp if stated)}` block; a defensible M2 would need a sourced OCV(SOC) table (≥3-5 points spanning practical flight SOC, e.g. 100%→20%) plus R(SOC) if it varies materially; a defensible M3 would need a sourced `{c_rate, usable_capacity_pct}` table with ≥2 points bracketing this pack's actual operating C-rate (~45C at hover, ~107C at bench-max — see Gate G). **None of this exists to curate today** (Gate D).

---

## Gate D — External source audit (defendability tiers)

| Source | Content found | Tier | Accept? |
|---|---|---|---|
| Catalog's own `source_url` (Baltic Drones CNHL Black Series listing) | Fetched directly. Numeric fields: `1500mAh, 14.8V/4S, 100C continuous/200C burst, 5C max charge, 183g±5g, 37×35×75mm, XT60/JST-XH, 12AWG`. **Zero** internal-resistance, OCV, or discharge-curve data of any kind. | **T4** | No |
| WebSearch — "CNHL Black Series internal resistance datasheet mOhm discharge curve" | Retailer/community pages describe CNHL as having "ultra-low internal resistance" and "stable voltage curve" — **qualitative marketing language, zero numeric values**, for both the exact series and the broader CNHL line. | **T3-and-unsourced** (no number to even tier as T3 heuristic) | No |
| `chinahobbyline.com` "3S LiPo Battery Voltage Guide" (fetched directly) | Discusses OCV trending downward during discharge **conceptually** — explicitly confirmed by direct fetch to contain **no numeric voltage-vs-SOC data points**, no method disclosure (manufacturer/independent/heuristic indistinguishable because there are no numbers to source). | **T3, unusable** (no data to even apply a heuristic number from) | No |
| WebSearch — academic equivalent-circuit-model literature (ScienceDirect, IOP, AIP, ResearchGate, arXiv) | Real, methodology-documented literature on Randles/RC battery models: `R0` (ohmic) roughly SOC-independent except near SOC≈0; `R1` (polarization) rises sharply below ~20% SOC. **Generic lithium-ion methodology** (often EV/consumer-cell scale), **no numeric R0/R1/OCV table extracted or confirmed applicable to a small 1500mAh 100C RC LiPo pack** — a scale/chemistry-class substitution would need explicit justification this investigation cannot responsibly manufacture from search snippets alone. | **T2-class methodology, not SKU- or class-verified with actual numbers** | No — informative context only |
| WebSearch — ArduPilot/Betaflight voltage-sag compensation practice | **Real, load-bearing engineering finding, not a data source but a methodology finding:** ArduPilot's own documented approach estimates `R_internal` **online, from live in-flight telemetry** (`V_sag = I × R`, R estimated during flight), not from a static pre-sourced datasheet constant. This is the industry-standard answer to "how do real flight-control systems get R_internal" — and it is **architecturally unavailable to Jarvis**, a design-time tool with no live telemetry, reinforcing that a static sourced number is the *only* path available here, and none exists. | N/A (methodology finding, not a data source) | Informative — explains *why* no static number is the norm, doesn't provide one |
| WebSearch — LiPo C-rate capacity-derating tables | Confirms the *concept* is real (capacity at high C-rate expressed as % of 1C capacity) and real manufacturers sometimes publish such tables — but **no numeric table found for this SKU or a clearly comparable one**; general guidance only ("low C 0.2-0.5C efficient... high C 3-10C+ supports bursts"), no percentages. | **T3, no usable numbers** | No |

**Explicit tier verdicts (★★4):** `V_oc(SOC)` — **not defensible** (T4/T3-unusable, no SKU or credibly-substitutable class data). `R_internal(SOC)` — **not defensible**, same reasoning, reinforced by the ArduPilot finding that even production flight-control firmware doesn't rely on a static sourced value. **C-rate capacity derating (M3 input)** — **not defensible**, no numeric table found despite the concept being real and well-documented qualitatively.

---

## Gate E — Battery model options, scored

| Model | Data required | Available? | Verdict |
|---|---|---|---|
| **M1 — Fixed R, fixed V_oc** | Sourced `R`, defined `V_oc` | **No** — Gate D: zero numeric R found | **Rejected** |
| **M2 — OCV(SOC) + R(SOC)** | Sourced curves + SOC policy | **No** — same | **Rejected** |
| **M3 — C-rate capacity derating only** | Sourced `{C-rate, usable_capacity_pct}` table | **No** — Gate D found the concept but no numeric table | **Rejected** (data-blocked, not ★★7-blocked — see below) |
| **M4 — Peukert/kinetic** | Sourced exponent `n`, chemistry validation | **No** — not searched further once M1-M3 all failed on the same root cause (no numeric electrical data for this SKU); Peukert is explicitly the highest-risk-of-invention model per the contract, and nothing in Gate D surfaced even generic RC-LiPo Peukert exponents | **Rejected** |
| **M5 — UNVERIFIABLE** | Document gap | **Yes — this is the outcome** | **Recommended** |

### `I_load` policy (★★7 — central problem)

| Policy | Assessment |
|---|---|
| **I1** — `I_load = motor_hover_current_a × motor_count` (68.0428A total, live-computed) treated as pack current | **Rejected.** This silently assumes the ESC/wiring pass current through unchanged — physically only true if there is zero power loss *and* the ESC presents the same average voltage to the motor as the battery terminal voltage. Neither is established (Phase 2.6: loss magnitude entirely unsourced). Tiering this "assumption" would require exactly the ESC data Phase 2.6 found absent. |
| **I2** — iterative solve `I_load = P_motor_input / V_loaded` (with R feedback), "using motor power as demand, not claiming it equals P_battery" | **Rejected on inspection — flagged as a finding, not just a score.** Solving `I = P/V` where `P = motor_hover_power_w` **is numerically identical to asserting the battery is delivering `motor_hover_power_w` of electrical power at the pack terminals** — i.e. `P_battery := P_motor_input` inside the circuit equations, regardless of what the surrounding prose calls it. This is the exact forbidden identity (`P_battery = P_motor_input`, contract's own forbidden-formulas list). The contract's own framing hedges this ("not claiming it equals P_battery") but the math does claim it, structurally. **This is the single most important finding of this gate**: I2 is not actually an independent option from I1's problem — it just moves the same forbidden assumption into a solver loop instead of a one-line multiplication. Recommend the report record this explicitly so a future IC doesn't re-derive I2 as if it were safe. |
| **I3** — bounds only: `I_motor ≤ I_pack ≤ I_motor/η_min`, `η_min` UNVERIFIABLE | **Partially defensible, but only as a one-sided bound, and even that needs a stated assumption.** The lower bound `I_pack ≥ I_motor` is plausible *if* one assumes the average voltage the ESC presents to the motor is not higher than the pack's terminal voltage (true for a simple non-boosting BLDC ESC under normal, non-regenerative operation) — but this investigation did not find a sourced confirmation of that assumption either; it is stated here as a physically-reasonable inference, not a cited fact, and should be labeled as such if ever used. The upper bound is **not available at all** — `η_min` has no sourced floor (Gate D), so the envelope is one-sided and of limited practical use (an "at least 17A/motor, no known ceiling" statement is barely more informative than not stating a bound). |
| **I4** — UNVERIFIABLE | **Recommended.** No policy above survives without either inventing data (I1), silently reintroducing the frozen Phase 2.6 identity (I2), or degrading to an uninformative one-sided bound with an unstated assumption (I3). |

**Consequence for M1-M4:** since `I_load` is UNVERIFIABLE (I4), M1/M2 (which need `I_load` for `V_loaded`) are doubly blocked — both by missing `R`/`V_oc` data *and* by the `I_load` problem independently; M4 (Peukert) also needs a current/rate input and is similarly blocked. **M3 is the one model class that does NOT need `I_load` at all** (it derates usable Wh purely by the pack's own C-rate, using currents already computed elsewhere — bench `i_total` from ERF-2, or the hover total computed in Gate G below, neither of which requires solving for an unknown pack current) — its rejection above is purely a **Gate D data gap** (no derating table), independent of ★★7. This distinction matters for Gate H: M3 is the closest any model comes to being implementable, blocked by one missing table, not by the deeper `I_load` problem.

---

## Gate F — Integration surfaces (map only)

| Surface | Findings |
|---|---|
| Loss/energy resolver | Same precedent as Phase 2.5/2.6: `library.py` would own any future sourced-data resolver (mirrors `resolve_operating_point`/`resolve_operating_point_at_thrust`); `calculation_engine.py` would own chain orchestration. **Not actionable today** — no data to resolve. |
| Calc pipeline | Would slot as a parallel branch after `_resolve_hover_energy()`'s return (not replacing it), consuming `motor_hover_power_w`/`motor_hover_current_a` as read-only inputs plus the bound battery's `catalog_ref.sku` — same call-once-per-`build()` shape as the existing hover branch. Not added. |
| Bundle/persistence | Would need a new sibling autonomy field (★★6/★★9-naming-consistent, e.g. `hover_loaded_battery_autonomy_min`) + a JSON provenance string mirroring `hover_energy_resolution`'s shape. Not added. |
| Estado/CLI | Would extend the existing `adapters/cli/main.py` pattern (the "Energía hover (evidencia)" line Phase 2.5 established, and the hypothetical "Energía sistema" line Phase 2.6 scoped) with a third, distinct line — never conflating three different evidence tiers on one line. Not added. |
| Probes | A future probe would need to assert the honest UNVERIFIABLE default for any new loaded-battery field, mirroring how `cli_probe_phase25_hover_energy.py` Step 3 already asserts Combo B's honest `None`. Not added. |
| ERF-2 | **Confirmed independent, ★★10 upheld.** `_battery_discharge`/`_battery_pack_limit_a` (`electrical_compatibility.py:204-226,278-288`) are pure current-vs-limit checks with zero energy/Wh terms — live-reconfirmed this session, `git diff` for this file remains empty across Phase 2.5/2.6/2.7. |
| DSE | `_score_candidate` (frozen) reads `sim.autonomy_min` only — would inherit any future loaded-battery autonomy the same passive way it already inherits hover autonomy (Phase 2.5/2.6's own repeated finding, re-confirmed applicable here). The contract flags this should **not** feed DSE until Engineer decides — moot today since no such field exists. |

No module-placement decision is actionable (Gate I from prior contracts doesn't apply here — nothing to place).

---

## Gate G — Reference cases (live-verified this session)

| Case | Result |
|---|---|
| **Combo A** — nominal vs. what a loaded model *would* change | `battery_capacity_wh=22.2Wh` used as-is; `hover_energy_autonomy_min=1.3237min` (bit-identical to Phase 2.5/2.6 reports). No loaded-model comparison is possible even as a labeled paper exercise — Gate E found no sourced `R`/`V_oc` to plug into a hypothetical, unlike Phase 2.6 which *could* illustrate a labeled hypothetical η. Here, illustrating a made-up `R_internal` would cross directly into ★★4's forbidden territory (no defensible number to even label "illustrative" from, since illustrative-but-fabricated is still fabricated for a physics quantity) — correctly omitted. |
| **Combo A — discharge gap** | Reconfirmed live: `i_total_a=160.0 > i_limit_a=150.0` → `battery_discharge="exceeded"` — this is the bench-max-current margin check (ERF-2), entirely separate from any sag question; both this gap and the sag-UNVERIFIABLE finding are simultaneously true and don't interact. |
| **Combo A — hover current** | **New finding, live-computed this session:** hover total current = `17.0107 × 4 = 68.0428A`, which is `≤ 150A` (`i_limit`) — i.e., **the hover-load current would honestly PASS the C-rate margin check**, in contrast to the bench-max case which fails it. Expressed as a C-rate: `68.0428A / 1.5Ah ≈ 45.36C` — well above the "low-C, negligible derating" regime (0.2-0.5C) cited in Gate D's C-rate research, meaning **if** a derating table existed, it would plausibly represent a real, non-trivial correction at this operating point — not a rounding footnote. This sizes the stakes of the M3 data gap without inventing a number to fill it. |
| **Combo A′ (+ ESC)** | Not separately re-run this session — Phase 2.6's own live verification already established that ESC binding changes nothing about the hover/battery-adjacent numbers (`T_hover_motor_n`, `motor_hover_power_w`, `motor_hover_current_a` all bit-identical with or without ESC bound), and this investigation's battery model (Gate E) needs no ESC data by construction (★★2) — so Combo A′ trivially inherits Combo A's findings unchanged. |
| **SKU without `max_continuous_current_a`** | Not separately traced — ERF-2's own `unverifiable` outcome for this case is pre-existing, unrelated Phase-2.5-and-earlier behavior (`_battery_discharge`, `:286-287`, returns `"unverifiable"` when `i_limit is None`), outside this investigation's diff surface. No energy-model equivalent exists to compare it against, since no energy model was built. |
| **Phase 2.6 regression** | **Reconfirmed clean.** No `P_battery`-shaped field appeared in `CalculationBundle.model_dump()` at any point during this session's live runs. |

---

## Gate H — Blockers + IC slice recommendation

| Candidate | Verdict | Evidence |
|---|---|---|
| No OCV/R in catalog | **BLOCKING for M1/M2 implementation** (not for this investigation) | Gate C/D |
| No SKU-specific electrical data | **INSUFFICIENT DATA**, confirmed across R, OCV, and C-rate-derating fronts | Gate D (6 sources checked) |
| `I_load` undefined without ESC loss | **BLOCKING**, and structurally deeper than a simple data gap — I2's hidden identity-reintroduction is the key finding | Gate E |
| Phase 2.5 hover path | **NOT BLOCKING — verified unchanged** | Gate A/G, `git diff` empty |
| M3 C-rate derating only | **Rejected on data grounds, not ★★7 grounds** — the one model class independent of the `I_load` problem, blocked only by a missing derating table | Gate E/D |
| Peukert without data | **REJECT** | Gate E |

**Recommendation: NO IC.** `hover_energy_autonomy_min` remains the correct, honest interim figure (★★6). This report constitutes the documented UNVERIFIABLE boundary the contract's §7 acceptance table treats as a valid PASS-equivalent outcome.

**If a future arc is pursued, two independent, non-blocking forward paths** (neither implied as more urgent than the other by this investigation):
- **Battery data-acquisition path:** locate or commission T1/T2 electrical data specifically for `lipo_4s_1500mah` or a rigorously-justified same-class substitute (chemistry, cell count, capacity, and C-rating all matched, with the substitution rationale stated explicitly in whatever future contract uses it) — an OCV(SOC) table and/or a C-rate usable-capacity table would each independently unblock a partial model (M2 or M3 respectively) without needing the other.
- **ESC data-acquisition path (Phase 2.6's own parallel track, unaffected by this report):** if `P_battery` ever becomes computable, the `I2`-shaped iterative solve becomes legitimate (P_battery, not P_motor_input, feeds the circuit equations) — this is the natural point where Phase 2.6 and Phase 2.7 compose, exactly as the contract's own target architecture diagram anticipates.

Neither path is blocking the other; both remain open, undecided by this investigation per its own scope (★★1/§5).

---

## 3. Mandatory output table

| Capability | Supported today? | Evidence | Blocker | First slice |
|---|---|---|---|---|
| Nominal Wh autonomy (`hover_energy_autonomy_min`) | **YES** | Gate A — live-reconfirmed `1.3237min`, unchanged | — | none |
| Catalog `energy_wh` semantics documented | **YES** | Gate B/C — confirmed exact nameplate `V_nom×Ah`, no cutoff/loaded-voltage adjustment | — | done (this report) |
| `V_oc(SOC)` from sourced data | **NO** | Gate D — T4/T3-unusable across all sources checked | External data acquisition | P27-D — not actionable without new sourcing |
| `R_internal` / equivalent | **NO** | Gate D — same; reinforced by ArduPilot's online-estimation-only industry practice | External data acquisition | P27-D — not actionable |
| `I_load` policy without `P_battery` | **NO** (I4 UNVERIFIABLE) | Gate E — I1 rejected (invented η=1), I2 rejected (hidden identity reintroduction), I3 one-sided/uninformative | Phase 2.6 ESC boundary (frozen) | report (this document) |
| `V_loaded` under hover load | **NO** | Depends on both rows above | Same | P27-B — blocked on P27-D and/or Phase 2.6 |
| Usable energy under load | **NO** | Same; M3 (voltage-free path) also blocked, independently, on a missing derating table | Data acquisition (either R/OCV or C-rate table) | P27-D |
| Sibling loaded-battery autonomy field | **NO** | Gate F — no field exists, none recommended without data | Depends on above | P27-B |
| `P_battery` / ESC loss | **NO (frozen)** | Phase 2.6, re-confirmed unchanged this session | ESC bench data | P26-D (parallel, unaffected by this report) |
| ERF-2 C-rate limit check | **YES** | Gate A/F/G — `battery_discharge` unchanged, `i_total=160A>150A` bench-max case and `68.04A≤150A` hover-case both live-verified this session | — | none |
| Battery sag + ESC loss composed | **NO** | Both layers individually UNVERIFIABLE (Phase 2.6 + this report) | Both | future |

---

## Engineer ★ questions (report surfaces; pre-locked where marked)

| ★ | Question | Answer |
|---|---|---|
| ★1 | Can Jarvis honestly compute loaded-battery autonomy today? | **No** — confirmed, no model class in Gate E survives its data precondition |
| ★2 | What does `battery_capacity_wh` actually mean? | **Exact nameplate energy** (`nominal_voltage × capacity_Ah`), no cutoff voltage, no load adjustment — verified to float precision (★★3, Gate B/C) |
| ★3 | Best battery model class M1–M5? | **M5 (UNVERIFIABLE)** — the only one whose precondition is met; M3 is the closest partial candidate, blocked only by a missing derating table, not by the deeper `I_load` problem |
| ★4 | What `I_load` policy is defensible without `P_battery`? | **None — I4 (UNVERIFIABLE)**. Flagging explicitly: I2 as specified in the contract is **not actually independent** of the frozen `P_battery=P_motor_input` identity — it reintroduces it structurally through the circuit-solve, a finding worth Engineer's attention for any future contract revision of this option |
| ★5 | Keep `hover_energy_autonomy_min` unchanged? | **Yes** (★★6 locked) — untouched, re-verified live |
| ★6 | Sibling field naming? | Not proposed for adoption now (no model to name); if ever needed, `hover_loaded_battery_autonomy_min` (contract's own suggestion) reads consistently with the existing `hover_energy_autonomy_min` naming family |
| ★7 | Is M3 worth a partial IC? | **Not today** — it is genuinely the closest candidate (no `I_load` problem, and Gate G shows the correction would likely be non-trivial at Combo A's ~45C hover point), but Gate D found zero numeric derating data to build even a partial M3 from. Worth revisiting immediately if a derating table is ever sourced — this is the single most "shovel-ready" future slice identified in this report |
| ★8 | Change ERF-2 to hover current? | **No** (★★10) — confirmed independent and unaffected either way |
| ★9 | Next after P27 if INSUFFICIENT DATA? | Gate H's two parallel paths (battery data acquisition targeting M3's derating table specifically as the highest-leverage single data point, or the existing Phase 2.6 ESC bench path) — Engineer's call, not this investigation's to force |
| ★10 | Accept UNVERIFIABLE as success? | **Yes** (★★4/★★8 locked) — this report's verdict |

---

## Deliverables produced

- This report: `.jes/artifacts/investigation_report_phase27_battery_voltage_sag.md`
- Baseline table: header — suite 2058/0, both probes green, zero `src/`/`library/`/`tests/`/`scripts/` drift from `fc46938`
- External source appendix: Gate D table (6 sources/searches, all tiered T3/T4/methodology-only, none usable)
- `battery_capacity_wh` semantics memo: Gate B/C (★★3) — nameplate energy, verified exact
- `I_load` policy recommendation: Gate E (★★7) — UNVERIFIABLE (I4), with the I2-hidden-identity finding flagged for Engineer attention
- No repro/xfail added — the same reasoning as the Phase 2.6 report applies: existing `hover_energy_autonomy_min`/absence-of-`P_battery` assertions already cover the adjacent honest-absence pattern this investigation extends; happy to add a dedicated one if Engineer wants an explicit regression lock on "no loaded-battery field exists"
- No IC outline produced — Gate H's recommendation is **NO IC**
