# Investigation Report — Phase 2.7-B Parametric / Estimative Battery Model

**Contract:** `.jes/artifacts/investigation_contract_phase27b_parametric_battery_estimate.md` (★★1–★★13 locked)
**Investigator:** Claude Code
**Baseline:** commit `fc46938` / tag `v0.3.5` / `checkpoint-phase25-hover-energy` — verified: `git diff --stat fc46938 HEAD -- src/ library/ tests/ scripts/` empty. Full suite **2058 passed, 0 failed**.
**Date:** 2026-09-01

---

## Executive summary

**Verdict: PASS WITH NOTES.**

L1 (`hover_energy_autonomy_min`) is confirmed unchanged and untouched (Gate A). A labeled, sweep-only estimative model (**E-SWEEP**, a bounded-envelope wrapper around the simplest circuit model, **E-R**) is architecturally implementable **without** a new subsystem — a pure-formula sibling to the existing `calculate_autonomy_min` in `tools/electricity.py` is the natural, precedent-consistent home (★★8's STOP clause is **not** invoked). `E-M3` (C-rate derating) remains blocked, unchanged from P27-A, since — unlike `R_internal`/`V_oc` — it has no generic-chemistry default an investigator can responsibly label "assumed" from first principles; it needs an actual sourced table.

The Gate D paper exercise (Combo A, every number explicitly labeled — contract-given grids for `R`/`I_load`/`V_cutoff`, plus one investigator-added labeled assumption for `V_oc(SOC)` needed to close the model) produced a genuinely useful, honest finding: **the estimated envelope ranges from complete infeasibility (0 min — the load exceeds what the pack can sustain at any SOC) to ≈1.52 min**, and is dominated by `R_internal` — doubling the assumed pack resistance from 20mΩ to 40mΩ (holding load/cutoff fixed) collapses the estimate to zero. `I_load` and `V_cutoff` are also highly sensitive (all three axes move the result by far more than the contract's own 10% threshold — none is "noise"). This directly and empirically answers Gate D's own question: **R_internal measurement is the single highest-leverage data point to prioritize**, ahead of a C-rate-derating campaign, if any physical measurement is ever pursued.

Recommended IC scope (bounded, per ★★11): a sweep-only estimative endurance function + assumption-record schema + sibling `CalculationBundle` fields + a clearly-labeled `estimativo` CLI block — never a single autonomy number, never touching L1, never touching the catalog, never reading `P_battery`.

---

## Gate A — L1 vs L2 surfaces today

L1 is unchanged and re-verified live this session — identical to the P27-A and Phase 2.5/2.6 reports' own numbers:

```text
lipo_4s_1500mah: energy_wh=22.2 (nameplate, verified = 14.8V×1.5Ah exactly, P27-A Gate B/C)
      ↓
hover_energy_autonomy_min = (22.2 / (251.559 × 4)) × 60 = 1.3237 min   [tools/electricity.py:25-33, calculation_engine.py]
```

`git diff --stat fc46938 HEAD -- src/jarvis/tools/electricity.py src/jarvis/core/calculation_engine.py src/jarvis/knowledge/library.py` is **empty** — zero drift since the P27-A checkpoint. No `P_battery`-shaped field exists (re-confirmed via `CalculationBundle.model_dump()` key inspection, same method as P27-A's own check).

**What would be new for L2** (none of this exists today, confirmed by grep — `assumption_record`, `endurance`, `r_internal`, `v_oc`, `estimativ` all return zero hits in `src/jarvis/` outside this session's own paper script):
- An **assumption record** (caller-supplied, not derived from `ProjectState` alone — see ★★7's exact wording: "`ProjectState` + explicit assumption record → result", distinguishing this from Phase 2.5/2.6's fully-autonomous-from-catalog-identity design).
- A **sibling result type** (mirroring `ResolvedHoverOperatingPoint`'s shape) carrying an **envelope**, not a scalar.
- New, additively-optional `CalculationBundle` fields, populated **only** when the caller explicitly opts into an estimative run (unlike hover energy, which runs automatically whenever identity permits it).
- A distinct, clearly-labeled `estimativo` CLI block, visually and textually separated from the L1 line.

---

## Gate B — Parameter set (minimum honest L2)

| Parameter | Catalog today? | Assumed OK if labeled? | Scope requirement (★★13) |
|---|---|---|---|
| `capacity_Ah` / `energy_wh` | **Yes** — nameplate (`BatterySpec.energy_wh`, `capacity_mah`) | As identity only — never re-labeled "usable" (P27-A finding, reconfirmed) | N/A (not a voltage/resistance quantity) |
| `V_oc(SOC)` | **No** | **Yes**, if labeled `source_type="assumed"` and generic-chemistry-only | Must declare **pack** or **cell**; this investigation's own Gate D exercise uses **pack**-scope throughout, stated explicitly |
| `R_internal` | **No** | **Yes**, same discipline, **swept**, never a single silent default | Must declare **pack** or **cell**; Gate D uses **pack**-scope (the contract's own example grid is explicitly labeled "mΩ pack") |
| `I_load` | Hover current exists (`motor_hover_current_a`) but is **motor-side**, not pack current | Sweep (primary) + optional labeled proxy (`n × motor_hover_current_a`, explicitly NOT claimed as pack draw) | N/A — current has no cell/pack ambiguity in this model (single series string, same current through every cell) |
| Cutoff `V` | **No** | **Yes**, labeled, **pack**-scope in this investigation's exercise | Must declare **pack** or **cell** — mixing e.g. a pack-scope R with a per-cell cutoff in one `V − IR` line is exactly what ★★13 forbids |
| Temperature | **No** | Optional; **explicitly neglected** in this investigation's exercise (stated, not silently omitted) | N/A |
| Initial SOC | **No** | **Yes**, labeled; this investigation's exercise starts at SOC=100% but reports the **SOC at which cutoff is reached**, not a "100% for the whole flight" single-point claim | N/A |

### Minimum assumption-record schema (proposed, mirrors `hover_energy_resolution`'s JSON-string convention)

```json
{
  "source_type": "assumed",
  "model_class": "E-SWEEP",
  "r_internal_mohm": 20.0,
  "r_internal_scope": "pack",
  "v_oc_full_v": 16.4,
  "v_oc_empty_v": 13.2,
  "voltage_scope": "pack",
  "v_cutoff_v": 14.0,
  "i_load_a": 68.0,
  "i_load_label": "4x motor_hover_current_a (motor-current hypothesis — NOT pack draw, NOT P_battery)",
  "capacity_ah": 1.5,
  "capacity_source": "catalog_nameplate",
  "endurance_min": 0.4301,
  "soc_at_cutoff": 0.675,
  "assumption_provenance": "generic 4S LiPo chemistry defaults (4.1V/cell full, 3.3V/cell empty at rest); R/I/V_cutoff per Engineer-provided illustrative sweep grid; NOT sourced, NOT SKU-specific, NOT validated (L3)"
}
```

`r_internal_scope` and `voltage_scope` are **mandatory, non-defaulted** fields (★★13) — any future code implementing this must refuse to compute `V_loaded = V_oc − I×R` when the two scope fields disagree (e.g. a `pack` resistance paired with a `cell` OCV) rather than silently multiplying/dividing by cell count. This investigation's own Gate D exercise (below) uses **pack-scope throughout** and never mixes.

---

## Gate C — Model class for L2, scored

| ID | Sketch | Implementable under locks? |
|---|---|---|
| **E-R** | Fixed `R`, single `V_oc` (or simple polyline) → one `V_loaded`/endurance point | **Formula-level yes, presentation-level no as a standalone output** — ★★5 forbids a single scalar reaching the user; E-R is the correct *inner* formula but must always be wrapped by E-SWEEP before it's user-facing |
| **E-SWEEP** | E-R run over a stated grid (R × I_load × V_cutoff) → envelope table | **Yes — recommended.** Matches ★★5's envelope mandate directly; Gate D below demonstrates it end-to-end |
| **E-M3** | C-rate derating table, no voltage term | **Still blocked** — unlike R/V_oc, a derating percentage has no defensible generic-chemistry default an investigator can responsibly label "assumed"; P27-A's Gate D found zero numeric derating table for this SKU or a substitutable class, and nothing in this investigation's own research surfaced one either (no new external search was performed this session — P27-A's finding stands, re-cited, not re-derived) |
| **E-NONE** | — | **Not needed** — E-SWEEP is viable |

**Recommendation: E-SWEEP, wrapping E-R, is the one implementable class.**

---

## Gate D — Sensitivity: what is worth measuring? (Combo A paper exercise, every number labeled)

**Provenance discipline, stated explicitly:** `R` grid (10/20/40/80mΩ, pack-scope), `I_load` grid (50/68/90A — 68A = the contract's own `4×17A` hover-current hypothesis, **explicitly not a pack-draw claim**), and `V_cutoff` grid (13.2V / 14.0V, pack-scope) are **all taken verbatim from the investigation contract's own example grids** — not investigator-invented. One additional assumption was required to make the model well-defined and was **added by this investigation, labeled as such**: a linear `V_oc(SOC)` polyline, pack-scope, using generic 4S-LiPo-chemistry rest-voltage bookends (`V_oc_full=4×4.1=16.4V` at SOC=100%, `V_oc_empty=4×3.3=13.2V` at SOC=0%) — common, widely-used hobby-chemistry defaults, **not sourced for this SKU, not claimed as measured**. `capacity_Ah=1.5` is the one non-assumed input (catalog nameplate).

**Model:** `V_oc(SOC) = V_oc_empty + SOC×(V_oc_full − V_oc_empty)`; `V_loaded(SOC) = V_oc(SOC) − I_load×R`; solve for `SOC_cutoff` where `V_loaded = V_cutoff`; `usable_Ah = capacity_Ah × (1 − SOC_cutoff)`; `endurance_min = usable_Ah / I_load × 60`. `SOC_cutoff ≥ 1.0` is reported as a distinct **infeasible-load** outcome (the pack is already below cutoff at full charge under that load — not merely "very short," but literally unsustainable at any SOC), not folded into `0.0 min` without explanation.

### Live-computed results (this session)

| R (mΩ, pack) | I_load (A) | V_cutoff (V, pack) | Endurance (min) | SOC at cutoff | Outcome |
|---:|---:|---:|---:|---:|---|
| 10 | 68 | 14.0 | 0.7114 | 0.4625 | sustainable |
| 20 | 68 | 14.0 | 0.4301 | 0.6750 | sustainable |
| 40 | 68 | 14.0 | 0.0 | 1.10 | **infeasible at any SOC** |
| 80 | 68 | 14.0 | 0.0 | 1.95 | **infeasible at any SOC** |
| 20 | 50 | 14.0 | 0.7875 | 0.5625 | sustainable |
| 20 | 90 | 14.0 | 0.1875 | 0.8125 | sustainable |
| 20 | 68 | 13.2 | 0.7610 | 0.4250 | sustainable |

*(Full 4×3×2=24-point grid computed; table above shows the base point plus one-axis-at-a-time variation from base `R=20mΩ, I=68A, V_cutoff=14.0V`; full grid available on request, all points self-consistent with the same formula.)*

### Sensitivity ranking (>10% threshold, per Gate D's own question)

All three axes **move the result by far more than 10%** — none is noise:

- **`R_internal`: dominant.** `R: 10→20→40→80mΩ` (I=68A, Vcut=14.0V) → `0.71 → 0.43 → 0.0 → 0.0 min`. Doubling `R` from 20 to 40mΩ **collapses the estimate to complete infeasibility**. This is the single highest-leverage axis.
- **`I_load`: high.** `I: 50→68→90A` (R=20mΩ, Vcut=14.0V) → `0.79 → 0.43 → 0.19 min` — more than halves across the grid.
- **`V_cutoff`: high.** `13.2V→14.0V` (R=20mΩ, I=68A) → `0.76 → 0.43 min`, a ≈43% swing from a 0.8V cutoff choice alone.

**Empirical ranking (not slogan): R_internal measurement is the highest-leverage single data point** — it is the only axis whose plausible range spans "somewhat viable" to "literally cannot sustain this load," which neither `I_load` nor `V_cutoff` do as dramatically in this grid. This directly informs ★7: an R-measurement effort (e.g. commissioning or sourcing an IR-tester reading for this SKU or class, the same measurement ArduPilot estimates online in real flight per P27-A's finding) outranks a C-rate-derating (M3) data campaign in expected value, **for this specific question** — though M3 remains independently useful for the separate ERF-2-adjacent question of usable-capacity-at-high-C, which this exercise does not address.

**Contrast with L1:** the full envelope (0 to ≈1.5 min) straddles and mostly falls **below** `hover_energy_autonomy_min=1.3237min` — starkly illustrating why L1 must never be presented as a validated or even reliably-conservative physical lower bound (★★6): under several *plausible* (not extreme) parameter choices, the loaded-battery estimate is **zero**, far below L1's motor-input-only figure. This is the clearest, most concrete demonstration in this whole investigation series of why ★★5's "no single number" and ★★6's "no lower-bound claim" rules exist.

---

## Gate E — Integration map (map only)

| Surface | Recommendation |
|---|---|
| Core formula | **`tools/electricity.py`** — a new pure function (e.g. `estimate_loaded_endurance(v_oc_full_v, v_oc_empty_v, r_internal_ohm, i_load_a, v_cutoff_v, capacity_ah) -> ToolResult`), sibling to the existing `calculate_autonomy_min` in the **same file**, same pattern (pure formula, `ToolResult` wrapper, no I/O). This is the strongest precedent match found — `tools/` already exists specifically to hold pure physics formulas separate from orchestration (`core/calculation_engine.py` already imports and composes exactly this kind of sibling function from `tools/mechanics.py`, `tools/aerodynamics.py`, `tools/electricity.py`). |
| Sweep orchestration | A thin wrapper (could live in `calculation_engine.py` as a new, **not-auto-invoked** method, or as a small new pure function in `tools/electricity.py` itself, since a sweep is just calling the point-formula in a loop) — **not** a class, **not** a stateful engine. |
| Simulation-module note (checked, ruled out) | `src/jarvis/simulation/energy_model.py` and `flight_model.py` exist in the tree but are **literally empty (0 bytes), unimported anywhere, unchanged since the v0.1 prototype commit** (`git log` confirms single commit, initial scaffold). This could be read either way — "an existing reserved home" or "dead scaffolding the project outgrew when `calculation_engine.py`/`tools/` became the real home for this kind of logic." Flagging both readings rather than picking one: **not recommended** as the placement, because reviving zero-byte files with no prior design intent documented anywhere is a bigger, less-precedented step than extending `tools/electricity.py`, which already has a live, working sibling function doing almost exactly this job. |
| Bundle/persistence | New, **additively-optional** `CalculationBundle` fields (populated only on an explicit estimative call, not on every `build()`) — an envelope (e.g. `battery_endurance_envelope: list[dict] | None`) plus the assumption-record JSON string (Gate B schema), never a scalar `battery_endurance_min` field that invites exactly the single-number misuse ★★5 forbids. |
| CLI | A clearly-headed, visually separate block — e.g. `"Autonomía estimada (ESTIMATIVO — no validado): R=20mΩ (asumido) → 0.43 min · R=40mΩ (asumido) → INVIABLE"` — never adjacent to or formatted like the existing `hover_energy_autonomy_min` line in a way that invites confusion between the two. |
| DSE | **Lean: no, matching ★3's own lean.** `_score_candidate` (frozen) should **not** read any L2 field by default — an assumption-driven envelope is not an appropriate input to automatic candidate ranking without an explicit Engineer decision on which envelope point (optimistic/nominal/pessimistic) DSE would even use, a product question this investigation does not resolve. |
| ERF-2 | Unaffected, independent, unchanged (★★12/P27-A ★★10 — re-confirmed, `git diff` empty for `electrical_compatibility.py`). |

**★★8 STOP-clause check: not invoked.** No new subsystem is required — `tools/electricity.py` extension plus a non-auto-invoked orchestration wrapper is sufficient and precedent-consistent (same architecture Phase 2.5/2.6 used: `tools/`+`core/` for formulas+orchestration, `library.py` for catalog-data resolution — this investigation's model needs no catalog-data resolution beyond nameplate capacity, which already flows through existing paths).

---

## Gate F — IC / NO IC

**Bounded IC recommended** (not NO-IC): the E-SWEEP class is implementable, honestly labelable, and needs no new subsystem — satisfying ★★11's bar for recommending an IC for the *estimative* slice specifically (distinct from P27-A's validated-model NO-IC, which stands unchanged and unreopened).

**Scope, if pursued:**
1. `tools/electricity.py`: `estimate_loaded_endurance(...)` pure formula (Gate D's model, generalized).
2. A sweep wrapper (grid or explicit list of assumption-record inputs → list of results) — no default grid baked into product code; the grid itself is a caller/UX decision, not this investigation's to prescribe as a hardcoded default.
3. `CalculationBundle` additive fields (Gate E) — populated only on explicit opt-in.
4. CLI `ESTIMATIVO` block (Gate E) — labeled, separate from L1.
5. Probe: assert the envelope shape (multiple points, at least one `infeasible` outcome and one `sustainable` outcome for a stated grid) — never assert a single "the" endurance number, mirroring how this report's own Gate D table never collapses to one figure.

**Explicit non-goals for this IC:** no catalog JSON changes, no `P_battery`, no DSE wiring, no L1 changes, no cell↔pack auto-conversion (★★13 — scope mismatch must be a refusal, not a silent multiply).

---

## Mandatory table

| Capability | Today | L2 possible? | Blocker | First slice |
|---|---|---|---|---|
| L1 motor-input autonomy | **YES** | — | — | none |
| Labeled parametric OCV+R at assumed I | **NO** | **YES** — E-SWEEP, Gate D demonstrated end-to-end | none (architecturally clear) | Bounded IC (Gate F) |
| Sensitivity envelope vs R / I | **NO** | **YES** — live-computed this session, R dominant | none | Bounded IC (Gate F) |
| `I_load` as pack current | **NO** | **Not without Phase 2.6** — any pack-current claim reintroduces the frozen `P_battery` boundary | ESC data (Phase 2.6, frozen) | none |
| Validated model (L3) | **NO** | — | T1/T2 data (P27-A, unchanged) | data campaign (parallel) |
| `P_battery` | **NO (frozen)** | — | Phase 2.6 | none |
| DSE uses L2 | **NO** | Must not by default | Engineer ★ (★3) | none |

---

## Engineer ★ (report surfaces)

| ★ | Question | Answer |
|---|---|---|
| ★1 | Allow L2 estimative model in product (labeled), or L1-only until L3? | **Recommend allowing L2**, sweep-only, per Gate C/D/F — it's honestly implementable and Gate D's own numbers show real decision value (the R-sensitivity finding). Engineer's call to ratify. |
| ★2 | Default `I_load` scenario: sweep-only vs optional `n×I_hover` hypothesis? | **Sweep-only as the primary UX**, with `n×motor_hover_current_a` available as **one explicitly-labeled point within a sweep**, never as a silent unlabeled default (matches the contract's own "Scenario... labeled as motor-current hypothesis, not pack draw: Yes if provenance string says so" row) |
| ★3 | May DSE read L2? | **No** (Gate E lean, matches the contract's own lean) |
| ★4 | Sibling name? | Propose `battery_endurance_envelope` (list-shaped, not scalar) for the bundle field, and `battery_endurance_assumption` for the per-point JSON provenance string — deliberately avoiding an `_min` suffix on any single field to discourage exactly the single-number misuse ★★5 forbids |
| ★5 | Keep M3 data campaign parallel? | **Yes** — unaffected by this investigation, still open per P27-A, still useful for the separate high-C usable-capacity question Gate D's own exercise doesn't address |

---

## Deliverables produced

- This report: `.jes/artifacts/investigation_report_phase27b_parametric_battery_estimate.md`
- Baseline table: header — suite 2058/0, zero drift from `fc46938`
- Assumption-record schema: Gate B (JSON shape, mandatory `r_internal_scope`/`voltage_scope` fields per ★★13)
- Gate D sensitivity results: full labeled paper exercise, live-computed this session, provenance of every number stated explicitly (contract-given grids vs. this investigation's one added assumption)
- No production code, no JSON curation, no version bump (★★10)
- Bounded IC outline: Gate F (scope only, not a full contract — awaiting Engineer ★1 ratification before drafting `implementation_contract_phase27b_parametric_battery_estimate.md`)
