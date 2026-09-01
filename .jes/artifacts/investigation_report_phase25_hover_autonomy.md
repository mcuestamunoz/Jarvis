# Investigation Report — Phase 2.5 Hover Flight Energy Model

**Contract:** `.jes/artifacts/investigation_contract_phase25_hover_autonomy.md` (rev. 2026-09-01, Engineer research pass, ★★1–★★12 locks)
**Investigator:** Claude Code
**Baseline:** commit `0e2e71c` — "Add minimum-universe physical catalog with verified ESC foundation" (current HEAD)
**Date:** 2026-09-01

---

## Executive summary

Combo A (`sunnysky_r2205_2500` + `gf_5045x3` + `lipo_4s_1500mah`@14.8V, 4 motors, `payload_kg=1.718` → `total_mass_kg=2.88`) reproduces the contract's illustrative numbers almost exactly when driven through the real orchestrator: today's autonomy is **0.5625 min**, computed from the single curated OP row's bench-max power (`motor_op_power_w=592.0`, resolved at `12.552N`). The honest hover-regime figure — bounded linear interpolation between the 700gf (6.864N, 241W) and 800gf (7.845N, 293W) rows — is **251.559 W/motor**, giving **1.3237 min**, a **2.35×** understatement today. `T_hover_motor = weight_n/motor_count = 7.0632N` matches the contract's `≈7.06N` example. **★★1/★★2 confirmed**: the Combo A manufacturer PDF data is sufficient; only 1 of 10 published rows is curated into `library/motores/_datos.json`.

One correction to the contract's own framing, found independently and consistently by two separate investigation threads (Gate A/C and Gate G): **`safety_factor` does not "leak into" the energy path** — it never touches it at all. `calculate_required_thrust`'s `safety_factor`-inflated output feeds only `thrust_per_motor_required_n`/`available_total_thrust_n`/simulator margin (exactly per ★★3). The actual defect is an **absence**: `resolve_operating_point` is called once at component-**bind** time with no thrust argument at all (`component_writers.py:339`), and nothing ever re-resolves against calc-time thrust demand. This is invisible with today's single-row catalog and becomes a real bug only once curation adds rows and the existing `v1_max_thrust` policy keeps winning for both feasibility and energy. This refines, but does not contradict, the contract's diagnosis — recommend the eventual IC describe the mechanism this way.

Gate D/I recommends extending `library.py` with a new `resolve_operating_point_at_thrust(...)` function (Option 1) rather than a new module — `library.py` is already the codebase's OP resolver, has zero circular-import risk, and `core/` already depends on it (`component_writers.py:44`). Gate G confirms Combo B (single OP row) can only ever produce `exact_operating_point` or `UNVERIFIABLE` — bounded interpolation is mathematically impossible with fewer than two rows, a hard precondition for Gate D/I's design. Gate B/E confirms `effective_motor_power_w` has no legitimate non-autonomy consumer (safe to fully replace, not just deprecate-alongside) and that DSE inherits hover-honest autonomy automatically with zero wiring changes (G24-B stays untouched). **Primary recommendation: H-C (curate 9 rows) then H-B (OP Engine + calc wiring)**, consistent with ★★9.

**Baseline caveat (unrelated to this investigation's scope):** 2 pre-existing test failures exist on `0e2e71c` itself (§0) — not introduced by anything in this investigation, not touching hover/energy code, not fixed here (out of scope).

---

## 0. Baseline verification

| Check | Result |
|---|---|
| HEAD | `0e2e71c` (matches contract's stated baseline exactly — no diff to reconcile) |
| Full suite (`pytest -q`) | **2047 passed, 2 failed** — `tests/test_battery_catalog_bind_ux.py::test_idle_help_choose_offers_battery_once_propulsion_bound` (`KeyError: 'power_w'` — a test fixture reads `motor_spec.properties["power_w"]`, but `bind_motor_from_catalog` no longer populates that key for `emax_rs2205s_2300` under the current catalog schema) and `tests/test_propeller_catalog_bind_ux.py::test_propeller_idle_help_choose_when_freeform_unbound` (asserts stale message text `"Hélices del catálogo"`; the live route now returns generic `"Candidatos del catálogo para este espacio de diseño:"` with 5 motor-shaped candidates, not propeller candidates — a routing-content mismatch). Both are **pre-existing on this baseline commit**, unrelated to `library.py`/`calculation_engine.py`/hover energy, and are **not fixed in this investigation** (out of scope per contract §5: "investigation only"). Flagging for Engineer as baseline hygiene debt, separate from the Phase 2.5 arc. |
| `scripts/cli_probe_minimum_universe_combo.py` | **3/3 PASS** (Combo A, Combo A′, Combo B) — re-run live this session |

---

## Gate A — As-is flight-energy physics audit

Reference case driven through the real `JarvisOrchestrator` (same `_bind_combo` pattern as the existing combo probe): `sunnysky_r2205_2500` + `gf_5045x3` + `lipo_4s_1500mah`@14.8V, `motor_count=4`, `structure_mass_factor=0.5`, `safety_factor=1.2` (probe defaults), `payload_kg=1.718` → `total_mass_kg=2.88` (matches the contract's `~2.88 kg` example: `estimate_structure_mass` → `structure_mass_kg=payload×0.5`, `mechanics.py:7-15`; `total_mass_kg=payload+structure+battery_mass_kg(0.183)+motor_mass_kg(0.12)`, `calculation_engine.py:77-81`).

### Required numeric finding (actual traced values)

| Quantity | Current Jarvis (actual) | Correct regime (actual) |
|---|---:|---|
| `T_hover_motor` | **not computed anywhere in code** (confirmed by grep — zero hits for `hover`/`T_hover` outside docs/contract) | **7.0632 N** = `weight_n(28.2528)/motor_count(4)` |
| Power for autonomy | `motor_op_power_w=592.0` (`component_writers.py:387`, bind-time resolved, the ONLY curated row) | **251.559 W/motor** — bounded linear interpolation, bracket `(6.864N,241W)`–`(7.845N,293W)` from the Combo A Dataset table, per ★★4/★★5/★★11 (no extrapolation, no curve fit, no proportional scaling) |
| `autonomy_min` | **0.5625 min** (live `CalculationEngine().build(params).autonomy_min`) | **1.3237 min** = `22.2/(251.559×4)×60` |

Ratio today/correct ≈ **0.42** — today's figure understates true hover autonomy by more than half. These numbers reproduce the contract's illustrative example (`≈7.06N`, `≈251W`, `≈0.56min`, `≈1.33min`) almost to the decimal, confirmed by live execution.

**Regime-mismatch statement, confirmed literally:** `592 W/motor` is the manufacturer-published power at `12.552N` (the 1280gf row, `library/motores/_datos.json:264-281`). Actual hover demand for this reference case is `7.0632N` — roughly 56% of that bench-max thrust. **592 W/motor is correct for 12.552N; it is the wrong regime for 7.06N hover.**

**Independent cross-check (Gate H/G fork):** using the live `energy_wh=22.2` (`library/baterias/_datos.json`) and the contract's own 592W/251W figures, `22.2/(592×4)×60=0.5625min` and `22.2/(251×4)×60=1.3269min` — both land almost exactly on the primary trace above. No discrepancy found between the two independently-run traces.

**Also confirmed:** Combo A at its default `motor_count=4` already has `battery_discharge=exceeded` (`i_total_a=160.0 > battery_limit_a=150.0`, `cli_probe_minimum_universe_combo.py:129-133`) — a real, independent, already-honest HIGH-severity electrical-compatibility gap that coexists with the regime error. The two findings are **not causally linked**: the readiness gap doesn't affect the autonomy calculation, and vice versa — both are simply true of this reference case at this motor count.

---

## Gate B — Power semantics (four concepts — not collapsed)

| Concept | Current code representation | Conflation status | Minimal new field needed |
|---|---|---|---|
| **Nominal rating** (`motor_power_w`) | `MotorSpec.max_watts` → `current_parameters["motor_power_w"]`; fallback branch of `effective_motor_power_w` (`calculation_engine.py:34-47,46-47`) | None — never overwritten anywhere (explicit design invariant, `calculation_engine.py:39-41` docstring) | N/A — already correctly scoped |
| **Bench max OP** (`motor_op_power_w`) | Written by `component_writers.py:339,387` from `resolve_operating_point(...).power_w` at **bind time** (motor+propeller+voltage only — no thrust argument, `library.py:696-701`) | **Yes — the core Gate A regime error.** `effective_motor_power_w` (`calculation_engine.py:43-45`) treats this bind-time-frozen bench-max value as authoritative for autonomy, with zero re-evaluation against `required_thrust_n`/`thrust_per_motor_required_n` (computed two lines later in the same file, `:87-89`, but never passed to the OP resolver or consulted here) | N/A — the field itself is fine; the conflation lives in the **consumer** (`effective_motor_power_w`), not the field |
| **Hover motor input** (`motor_hover_power_w` — proposed) | **Does not exist.** No code path resolves OP at a computed thrust target — `resolve_operating_point` accepts only `motor_sku`/`propeller_sku`/`voltage_v` | N/A (doesn't exist) | New `current_parameters["motor_hover_power_w"]` set by a new calc-time call (e.g. `resolve_operating_point_at_thrust(...)`), paired with `motor_hover_current_a` and a `motor_hover_source_type` (`manufacturer_test`/`interpolated`/`fallback`/`UNVERIFIABLE`), mirroring the existing `motor_op_power_w`/`motor_op_current_a` pairing (`component_writers.py:387-388`). Does not touch `motor_op_power_w`; OP identity stays motor+prop+voltage (★★8) |
| **Battery/system** (`P_battery` — deferred, ★★7) | **Does not exist** — no `efficiency`/`eta`/`η`-named field touches power anywhere in `calculation_engine.py` or `electrical_compatibility.py` (confirmed by grep) | N/A — correctly absent, satisfying ★★7 as a **current-state fact**, not a gap | Out of scope per ★★7. When eventually added, must multiply `motor_hover_power_w × motor_count`, never alias onto either OP power field |

---

## Gate C — Hover thrust demand (★★3 — locked formula; mechanism investigated)

**★★3's formula has no existing code representation** — confirmed by grep (`hover`, `T_hover`, `weight_n.*motor_count`: zero hits in `src/jarvis/`). It is a genuinely new derived quantity, structurally distinct from `required_thrust_n` (`weight_n × safety_factor`, `mechanics.py:60-67`) — not a rename, a new formula with implicit `safety_factor=1.0` and a different divisor.

**Where `safety_factor` actually goes (traced, live values, `safety_factor=1.2`):**
- `calculate_required_thrust(weight_n, safety_factor)` (`mechanics.py:60-67`) → `required_thrust_n=33.9034` → feeds only `thrust_per_motor_required_n` (`calculation_engine.py:172-177`, traced `8.4758N`) and `available_total_thrust_n` (`:178`, traced `50.21N`).
- `simulator.py:66-70` — `safety_margin_ratio = available_total_thrust_n / required_thrust_n` — this is the **only** consumer of `required_thrust_n`: feasibility/simulation margin, exactly per ★★3.
- The autonomy branch (`calculation_engine.py:180-197`) reads only `battery_capacity_wh`, `effective_motor_power_w(parameters)`, `motors is not None` — it **never reads `required_thrust_n`, `thrust_per_motor_required_n`, or `available_total_thrust_n`**. Confirmed live: varying `safety_factor` changes the feasibility/margin chain but leaves `autonomy_min` bit-for-bit unchanged.

**Corrected finding (two independent forks — Gate A/C and Gate G — reached this same conclusion separately):** the contract's Gate C task frames this as "safety_factor incorrectly enters energy path." The precise mechanism is the **opposite of contamination — an absence**: `resolve_operating_point` is called at bind time with **no thrust argument of any kind** (`component_writers.py:339`), so neither the raw `weight_n` nor the safety-inflated `required_thrust_n` nor the honest `T_hover_motor` ever reaches OP resolution. This is invisible today because there is exactly one OP row to "select." It becomes a live bug the moment curation adds rows, because `resolve_operating_point`'s existing `v1_max_thrust` policy (`library.py:717,770-773`) will keep picking the highest-thrust row for whatever calls it — feasibility and (if left unchanged) energy alike — regardless of actual demand. **Net effect matches the contract's diagnosis exactly (592W used regardless of hover regime); the mechanism description should read "thrust-demand-blind OP binding," not "safety_factor leakage."** This does not contradict ★★3 — it confirms ★★3 is already structurally satisfied (safety_factor never touches energy, nothing to remove) while sharpening where the real gap is.

**Minimal fix scope (structural, not implemented):** autonomy computation gates only on `battery_capacity_wh is not None and effective_power_w is not None and motors is not None` (`calculation_engine.py:187`) — no thrust-related conditional exists to remove. The minimal fix is purely additive: compute `T_hover_motor = weight_n/motor_count`, and give the autonomy branch a new, thrust-demand-aware power source instead of unconditionally trusting whatever `motor_op_power_w` bind time set.

---

## Gate D — Discrete OP Dataset + bounded interpolation (mechanism trace)

1. **`ResolvedOperatingPoint` has zero room for interpolation/provenance today.** The dataclass (`library.py:635-666`) is flat — no `source_points`, `interpolation_axis`, `bounded`, or `target_thrust_n` field; `resolution_type` has no `"interpolated"` member. Recommend a **new, distinct result type** for the hover-specific resolver (not a `ResolvedOperatingPoint` schema migration) — regression-safe, satisfies ★9 (don't reopen Motor OP Voltage Coherence without regression proof).
2. **Row identity:** no `id`/`row_ref` field exists in the JSON schema. `thrust_n` is unique per row within one motor+prop+voltage series (confirmed across all 10 Combo A rows) and is already the interpolation axis (★★4) — recommend using `thrust_n` itself as the provenance join key rather than adding a new schema field; derive a human-readable label (`f"{thrust_n}N"`) at read time if display needs one.
3. **RPM interpolation is safe to defer, confirmed not assumed.** The only consumer of `.rpm`/`motor_op_rpm` anywhere in `src/` is `orchestrator.py:141` (`_motor_op_electrical_from_params`), an explicitly display-only estado/CLI helper — never read by `calculation_engine.py`, `electrical_compatibility.py`, or `simulator.py`. Power-only v1 interpolation is correct; RPM has zero calc-correctness impact.
4. **Split from `resolve_operating_point` is required, and it's a bind-time-vs-calc-time split, not just two APIs for one moment.** `resolve_operating_point` has exactly one call site in `src/` (`component_writers.py:339`), invoked at bind time — before the vehicle's mass/weight/hover-thrust is known for that calc cycle. A hover-specific resolver needs `T_hover_motor`, which only exists after `CalculationEngine.build()` runs. The two functions read the same underlying `motor.operating_points` data with no shared mutable state — no coupling risk from coexisting.

### Gate I — Operating Point Engine placement

**Recommendation: extend `library.py` with a new function (Option 1) — one recommendation, not a menu, per the contract's ask.**

- **Import-graph:** `calculation_engine.py` currently imports only `jarvis.tools.*`, `jarvis.schemas.tool_schema`, `jarvis.core.parameter_requirements` (`:1-18`) — zero dependency on `jarvis.knowledge.library` today. Wiring hover resolution in creates a new `core/calculation_engine.py → knowledge/library.py` edge **regardless of which option is chosen** — even inlining (Option 3) would still need to read `operating_points[]`, which only `library.py` exposes. `library.py` imports nothing from `jarvis.*` (leaf module by design, per its own docstring: "the ONLY place that reads `_datos.json`... never read JSON directly"). `component_writers.py` already imports `resolve_operating_point` from `library.py` (`:44`) — `core/ → knowledge/library.py` is the established direction; a new `core/flight_energy.py` module would duplicate this exact edge for no structural benefit.
- **CLAUDE.md forbidden-subsystem test:** CLAUDE.md's Architecture principles say "prefer existing engines, resolvers, services... over introducing parallel logic" and forbid new subsystems "merely to solve routing or convenience problems." `library.py` **already is** the codebase's OP resolver (owns `resolve_operating_point`, `ResolvedOperatingPoint`, the epsilon-match/fallback/legacy-estimate policy). A bracket-and-interpolate resolver is the same *kind* of operation with a different selection policy — extending it satisfies "prefer existing resolvers" directly. A new `jarvis/core/flight_energy.py`, despite the contract's own framing that it's "NOT a Physics Engine subsystem," would still be a new file with no existing call sites, tests, or ownership — the CLAUDE.md test isn't file-count, it's whether something is a thin extension of an existing owner (Option 1 clearly is) vs. an independently-addressable new unit (Option 2 reads as one regardless of self-description). Option 3 (inline in `calculation_engine.py`) is rejected separately: that file doesn't read `_datos.json`-derived data today, and `library.py`'s own docstring makes it the sole authority for that — inlining would violate an existing module boundary.
- **Where ★★12's pipeline lives:** Level 1 (`total_mass_kg → weight_n → T_hover_motor`) stays in `calculation_engine.py`, a same-file, same-pattern addition next to where `weight_n`/`required_thrust_n` are already computed (`:77-89`). Level 2 (bracket/interpolate/`UNVERIFIABLE`) lives in `library.py` as the new resolver. `calculation_engine.py.build()` calls it once per calc cycle, a single deterministic function call — structurally identical to how `component_writers.py:339` already calls `resolve_operating_point` today with no manual step in between. This does not risk the "fully autonomous, zero manual steps" guarantee.

---

## Gate E — Integration surfaces

1. **`effective_motor_power_w` — deprecate for autonomy, keep for what?** Only two real call sites in the entire codebase: its own use inside `calculation_engine.py:186`, and `scripts/cli_probe_minimum_universe_combo.py:103,166` (a probe assertion, not a second production consumer). **No sim-margin, DSE, or other subsystem calls it directly** — they consume `autonomy_min`/`available_total_thrust_n`, the *output* of `CalculationEngine.build()`. No legitimate non-autonomy consumer was found — it can be **fully replaced**, not just deprecated-alongside, once `motor_hover_power_w` exists.
2. **`electrical_compatibility` — hover current as separate fact vs. replacement?** `_per_motor_current_a` (`electrical_compatibility.py:129-172`) prefers `motor_op_current_a` (bench-max, 40A for Combo A) before falling to catalog max/declared/estimate — feeding both `_esc_vs_motor` and `_battery_discharge`. **Recommendation (for Engineer, not decided here): keep bench-max current as the authority for these two margin/safety checks** — they exist to catch worst-case draw (climb, wind, maneuvering), and hover-cruise current is not the physically correct input for a margin check. Adding hover current as a separate, clearly-labeled fact would be additive and safe but is not required for hover-autonomy honesty specifically.
3. **Autonomy label — does a regime/evidence-tier label exist today?** No `regime`/`flight_regime` string exists anywhere in `src/` (grep confirmed). But the **exact honesty-labeling pattern already exists** for thrust resolution: `adapters/cli/main.py:270-285` renders `f"Propulsión (evidencia): {resolution_type} · {source_type}"` plus a fallback-specific suffix; a second line (`:293-303`) renders raw OP power/current. A `motor_hover_power_w` label would **extend this established convention**, not invent a new one.
4. **DSE — safe to defer, and why.** `_score_candidate` (`design_explorer.py:354-364`, frozen G24-B — not touched by this investigation) reads `sim.autonomy_min` directly at line 364 — it does not call `effective_motor_power_w` itself. **DSE needs zero code changes** to become hover-aware; it automatically inherits whatever `autonomy_min` `CalculationEngine.build()` produces. One behavioral side-effect worth flagging for the IC (not DSE's own scope): once autonomy figures drop to the honest hover value, `mejorar_autonomia` candidate rankings could shift — a downstream test-visible consequence of the calc change, not something DSE code needs to implement.

---

## Gate F — Reference cases (Combo A / A′ / B / extrapolation-negative)

- **Combo A:** `resolve_operating_point(..., voltage_v=14.8)` → `resolution_type="exact_operating_point"`, `source_type="manufacturer_test"`, `thrust_n=12.5525`, `current_a=40.0`, `power_w=592.0` (live-run confirmed, `cli_probe_minimum_universe_combo.py:113-120`). `motor_power_w=756.0` (nominal) vs `motor_op_power_w=592.0` (OP) stay distinct (`component_writers.py:386-392`).
- **Combo A′** (+ ESC `hobbywing_xrotor_40a_6s`): **confirmed in code, not just asserted by lock** — ESC binding is a separate writer call (`set_control_component`) from motor binding; `i_motor_a` stays `40.0`, identical to Combo A. `resolve_operating_point`'s signature (`library.py:696-702`) has no ESC parameter at all. ★★8 holds structurally.
- **Combo B** (`emax_rs2205s_2300`+`gemfan_5045_hbn`): only **one active OP row** exists for this motor (full array has a null-data `fallback_only` row plus two `evidence_status="hold"` rows excluded from resolution, `library.py:743-744`). At 14.8V (catalog battery voltage) it resolves to `fallback_operating_point` with **no power/current data**; at 16.0V it's `exact_operating_point` (`thrust_n=13.4841`, `power_w=485.3`). **With exactly one usable row, bounded interpolation is mathematically impossible** — no second point to bracket against. Any `T_hover_motor` other than exactly `13.4841N` must resolve `UNVERIFIABLE` per ★★5 — this is a hard precondition ("≥2 non-hold rows"), not a soft "partial interpolation" case.
- **Extrapolation negative:** no code path attempts this today (the OP Engine doesn't exist yet) — a forward design confirmation, not a live trace. `resolve_operating_point`'s full body (`:696-804`) has no thrust-bounds check of any kind (it takes no thrust argument), so this check is entirely unbuilt. Per ★★5, any `T_hover_motor` below `min(OP.thrust_n)=1.961N` or above `max=12.552N` (once fully curated) must yield `UNVERIFIABLE`, never an extrapolated value — Gate D/I's design must build this boundary check explicitly.

---

## Gate G — Blockers (confirmed against contract's own leans)

| Candidate | Contract lean | Verdict | Evidence |
|---|---|---|---|
| Seed 9 missing OP rows | BLOCKING (curation) | **Confirmed BLOCKING** | `library/motores/_datos.json:264-281` — exactly 1 element; no code path can interpolate against a single point |
| Resolver split | Likely BLOCKING | **Confirmed BLOCKING** (stronger than "likely") | `resolve_operating_point(motor_sku, *, propeller_sku, voltage_v, library)` has no thrust parameter at all — cannot be pointed at `T_hover_motor` even in principle; in-place extension would break the existing `v1_max_thrust` feasibility contract relied on elsewhere |
| `safety_factor` in energy path | Likely BLOCKING bug | **Lean imprecise, net effect still BLOCKING** | Real defect is broader: zero thrust demand of any kind reaches `resolve_operating_point`'s bind-time call — not `safety_factor` specifically. Recommend the IC describe this as "thrust-demand-blind OP binding" (see Gate C) |
| G26/G27 | Likely PARALLEL | **Confirmed PARALLEL** | Both are freeform-text parse bugs (`restrictions` / battery SKU-string misparse); Combo A binds its battery via `bind_battery_from_catalog`, the catalog path neither bug touches |
| ESC efficiency | DEFER | **Confirmed DEFER** | No efficiency/η field exists in `library/esc/_datos.json`; ★★7 forbids inventing it; Combo A′ passes fully with no loss model |
| Second motor / more sources | NOT NEEDED | **Confirmed NOT NEEDED** | ★★1/★★9 lock Combo A as sufficient; Combo B exists only as a single-row/voltage-honesty contrast case |

---

## Gate H — IC slice recommendation

**H-C (curation-only) scope:** add 9 rows to `sunnysky_r2205_2500.operating_points[]`, each shaped like the existing 1280gf row (`propeller_sku`, `voltage_v=14.8`, `thrust_n`/`current_a`/`power_w` from the contract's table, `fallback_only=false`, `source_type="manufacturer_test"`, `source_reference`, `confidence`, `source_note`, `approved_by`, `approved_date`). **Open completeness question for the IC** (not resolved here): the contract's table gives `thrust_n`/`current_a`/`power_w` for the 9 new rows but no `rpm`/`efficiency_gf_per_w`, even though the existing row has both and the source PDF is described as a thrust/current/power/RPM table. Given Gate D's finding that **nothing in the calc path consumes RPM today**, `rpm`/`efficiency_gf_per_w` may be left `null` for v1 without correctness impact — sourcing them from the PDF is optional polish, not a blocker. The `evidence_status="hold"` mechanism (`library.py:743-744`) is available if partial-completeness rows need to land incrementally without participating in resolution yet.

**H-B (curation + code) scope:** everything above, plus the Operating Point Engine (Gate D/I: `resolve_operating_point_at_thrust` in `library.py`, `T_hover_motor` computation in `calculation_engine.py`, bracket/interpolation + `UNVERIFIABLE` boundary, provenance, new autonomy wiring replacing `effective_motor_power_w` for autonomy specifically, `estado`-visible regime label per Gate E #3).

**Order-of-magnitude sanity check (independent second computation):** `22.2/(592×4)×60=0.5625min`, `22.2/(251×4)×60=1.3269min` — both match Gate A's precise trace (`0.5625`, `1.3237`) with no discrepancy.

**Recommendation: H-C then H-B** (or a single IC with H-C as its first sub-slice) — H-C is a pure, low-risk data change with one open (non-blocking) sourcing question; H-B is the only path that fixes the actual code defect (thrust-demand-blind OP binding).

---

## 3. Mandatory output table

| Capability | Supported today? | Evidence | Blocker | First slice |
|---|---|---|---|---|
| Hover thrust from mass (T/W≈1) | **NO** | `weight_n` is computed (`calculation_engine.py:83-85`) but nothing divides it by `motor_count` into a hover-thrust quantity — grep for `hover`/`T_hover` in `src/jarvis/`: zero hits | Code addition (new derived value) | H-B |
| Discrete OP dataset (10 rows) | **PARTIAL** | 1/10 rows curated (`library/motores/_datos.json:264-281`) | Data curation | H-C/H-B |
| Hover power from bracket interpolation | **NO** | `ResolvedOperatingPoint` has no `source_points`/provenance fields (`library.py:635-666`); `resolve_operating_point` takes no thrust argument (`:696-702`) | New resolver function | H-B |
| Honest hover autonomy | **NO** | Live trace: `0.5625 min` (592W/motor) vs correct `1.3237 min` (251.559W/motor) — Gate A | Same as above + calc wiring | H-B |
| No extrapolation policy | **NO** | No thrust-bounds check exists anywhere in `resolve_operating_point` (`:696-804`) — nothing to extrapolate with yet, but nothing prevents it either once thrust-aware resolution is built without this check | Must be built explicitly (★★5) | H-B |
| `interpolated` provenance | **NO** | `resolution_type` Literal has no `"interpolated"` member (`library.py:651-653`) | New result type/schema | H-B |
| Separate bench vs hover power | **PARTIAL** | `motor_power_w` vs `motor_op_power_w` already separate and never overwritten (Gate B) — but `motor_op_power_w` vs proposed `motor_hover_power_w` distinction does not exist yet | New field | H-B |
| `P_motor_input` ≠ `P_battery` | **YES** (vacuously — see note) | No efficiency/η field touches power anywhere in `calculation_engine.py`/`electrical_compatibility.py` (Gate B grep) — the separation holds because `P_battery` simply doesn't exist yet, not because of an active guard | None | docs/honesty |
| ESC outside OP identity | **YES** | `resolve_operating_point` signature has no ESC parameter (`:696-702`); Combo A′ trace confirms ESC bind doesn't change `motor_op_power_w`/current (Gate F) | None | none |
| User-visible flight regime + tier | **PARTIAL** | No `regime`/`flight_regime` string exists (grep, zero hits) — but the honesty-labeling *pattern* already exists for thrust resolution (`adapters/cli/main.py:270-285,293-303`) to extend | New label, same convention | H-B |
| **Autonomous hover-energy pipeline (★★12)** | **NO** | Full chain absent: no `T_hover` computation, no thrust-aware resolver, no calc-time OP call (`resolve_operating_point` only called at bind time, before mass/weight is known, `component_writers.py:339`) | Entire OP Engine + calc wiring | H-B |

---

## 4. IC outline (H-B primary, H-C as first sub-slice) — outline only, not a full IC

**Slice 0 — H-C (data curation):**
- Add 9 rows (200–1000gf) to `sunnysky_r2205_2500.operating_points[]` in `library/motores/_datos.json`, matching the existing 1280gf row's shape exactly; `source_type="manufacturer_test"` throughout.
- Decide (Engineer/IC): source `rpm`/`efficiency_gf_per_w` from the PDF now, or leave `null` for v1 (Gate D confirms zero calc-path consumers of RPM today — `null` is not a correctness risk).
- Optional: stage via `evidence_status="hold"` if rows need to land incrementally.

**Slice 1 — H-B (code):**
- `library.py`: new `resolve_operating_point_at_thrust(motor_sku, *, propeller_sku, voltage_v, target_thrust_n, library=None)` — exact/bracket/`UNVERIFIABLE` per ★★4–★★6, `thrust_n` as row-identity key (no schema change), returning a new result type (not `ResolvedOperatingPoint`) carrying `source_type ∈ {manufacturer_test, interpolated, UNVERIFIABLE}` + provenance to both bracketing rows when interpolated.
- `calculation_engine.py`: compute `T_hover_motor = weight_n / motors` alongside the existing weight/required-thrust block; call the new resolver at calc time; introduce `motor_hover_power_w`/`motor_hover_current_a`; autonomy branch uses `motor_hover_power_w` in place of `effective_motor_power_w` (Gate E confirms no other production consumer exists to preserve).
- `electrical_compatibility.py`: no change for v1 (Gate E lean — bench-max current stays the safety-margin authority).
- CLI/estado: extend the existing `adapters/cli/main.py:270-285`-pattern with a hover regime + evidence-tier line.
- Tests/probe: new probe reproducing the Combo A hover-autonomy trace (`0.5625min → 1.3237min`) and the Combo B / extrapolation-negative `UNVERIFIABLE` cases.

---

## Engineer ★ questions (pre-locked where marked; evidence surfaced otherwise)

| ★ | Question | Status |
|---|---|---|
| ★1 | Honest hover autonomy today? | **Pre-locked NO** — confirmed: regime error (592W vs 251.559W/motor) + curation gap (1/10 rows), both verified live |
| ★2 | H-A sufficient? | **Pre-locked NO** — H-B required for validation |
| ★3 | Hover thrust formula? | **★★3 LOCKED** — `weight_n/motor_count`; confirmed no existing code computes it, and confirmed `safety_factor` never touches the energy path (see Gate C correction) |
| ★4 | Min rows for interpolation? | **★★4** — ≥2 bracketing published rows; Gate F confirms this is a hard precondition (Combo B's single row cannot interpolate at all) |
| ★5 | Resolver split? | **Confirmed YES**, and confirmed structurally necessary (bind-time vs. calc-time split, not cosmetic) — Gate D/I |
| ★6 | Discharge: hover vs bench current? | **Recommend bench-max stays authoritative** for `esc_vs_motor`/`battery_discharge` margin checks (worst-case draw, not hover-cruise draw); hover current as an additive separate fact is optional, not required — Gate E, Engineer's call |
| ★7 | Next data task? | **★★2** — seed PDF table rows 200–1000gf; Gate H flags the RPM/efficiency completeness question as non-blocking |
| ★8 | DSE in slice 1? | **Confirmed safe to defer** — DSE needs zero code changes, inherits hover-honest autonomy automatically (`design_explorer.py:354-364`); Engineer should note downstream ranking shifts as an expected side effect, not a bug |
| ★9 | OP Engine placement? | **Gate I recommends `library.py` extension** (Option 1) — import-graph + CLAUDE.md forbidden-subsystem analysis both favor it over a new module |
| ★10 | Accept `P_motor_input` for v1 autonomy (not `P_battery`)? | **★★7 LOCKED** — confirmed vacuously true today (no `P_battery`/efficiency field exists at all) |
| ★11 | Must hover-energy path be fully autonomous from ProjectState? | **★★12 LOCKED** — confirmed achievable by design: Gate D/I's placement is a single deterministic function-call boundary (calc engine → library.py), structurally identical to the existing bind-time `resolve_operating_point` call, no manual/user/LLM step required |

---

## Deliverables produced

- This report: `.jes/artifacts/investigation_report_phase25_hover_autonomy.md`
- Baseline table: §0 (including the 2 pre-existing, out-of-scope test failures on `0e2e71c`)
- No production fix, no JSON curation, no version bump, no new subsystem created
- No committed test/probe file — reference-case traces were run via scratchpad-only scripts per fork convention (optional per contract §6, not required for PASS)
- §4 above is the requested IC outline (not a full IC) for `implementation_contract_phase25_hover_autonomy.md`, to be drafted only after Engineer ★ ratification
