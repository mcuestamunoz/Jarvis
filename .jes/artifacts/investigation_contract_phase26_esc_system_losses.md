# Investigation Contract — Phase 2.6 ESC / System Electrical Loss Model

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_phase26_esc_system_losses.md`

**Status:** READY FOR CLAUDE

**Type:** Architecture + physics-model investigation — determine whether Jarvis can move from **`P_motor_input`** (Phase 2.5 hover-regime motor bench input power) to an **honest `P_battery`** estimate using **real ESC/system data**, without inventing efficiency. **Not** an implementation plan.

**Checkpoint base:** commit **`fc46938`** · tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`**

**Prior arcs (CLOSED — do not re-open without regression proof on `fc46938`):**

| Delivered @ Phase 2.5 | Scope |
|---|---|
| **Hover flight energy (P25-H)** | `resolve_operating_point_at_thrust`; `motor_hover_*`; `hover_energy_autonomy_min` |
| **Discrete OP dataset (P25-D)** | Combo A 10/10 rows @ 14.8 V + gf_5045x3 |
| **Dual bind/calc OP split** | Bind: `resolve_operating_point` → bench-max `motor_op_*`; Calc: hover at `T_hover_motor` |
| **Honest UNVERIFIABLE gates** | No extrapolation; no bench fallback when hover dataset out of range |
| **ESC catalog foundation** | `library/esc/`, `EscSpec`, `bind_esc_from_catalog` — **compatibility only** |
| **Electrical compatibility (ERF-2)** | `esc_vs_motor`, `battery_discharge` — **current margin**, not energy loss |
| **Combo probes** | Phase 2.5 **4/4** · minimum universe **3/3** · suite **2058/2058** |

**Still frozen (do not implement in this investigation):**

| ID | Topic |
|---|---|
| **Battery voltage sag / SOC / R_internal** | Separate arc — **after** motor→battery boundary is defined |
| **Flight mission model** | HOVER / CRUISE / CLIMB / DESCENT — not until single-regime chain is coherent |
| **Proportional scaling** | `(T_req / T_max) × P_max` — forbidden |
| **G24-B** | `_score_candidate` rewrite |
| **Wiring + avionics + BEC draw** | Out of v1 unless sourced and scoped in report |
| **ESC as OP identity field** | Motor + Propeller + Voltage only (Phase 2.5 ★★8) |

**Primary reference SKU (catalog-verified):**

- **`hobbywing_xrotor_40a_6s`** — `library/esc/_datos.json` · official product page in `source_url`
- Combo A′ already binds this ESC without affecting hover OP resolution (`cli_probe_minimum_universe_combo.py`)

**Design authority (read-only — context, not proof):**

- [`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md) §5.4, §7 — mentions `efficiency` on ESC schema and `P_motor_input = P_battery × η_ESC` as **design vision**; investigation must prove what is **implementable today**
- [`.jes/artifacts/investigation_report_phase25_hover_autonomy.md`](investigation_report_phase25_hover_autonomy.md) Gate B — `P_battery` correctly **absent** today
- [`.jes/artifacts/implementation_contract_phase25_hover_autonomy.md`](implementation_contract_phase25_hover_autonomy.md) ★10 — v1 hover autonomy uses `P_motor_input`, not full battery draw

---

## Engineer locks (★★ — ratified before investigation; report must not contradict)

| Lock | Rule |
|---|---|
| **★★1** | Phase 2.6 scope is **only** the link **`P_motor_input → P_battery`** (ESC + immediate system electrical losses). **No** battery sag, SOC, C-rate derating, or mission model. |
| **★★2** | **No invented efficiency.** If no defendable loss model exists from sourced data → **`P_battery = UNVERIFIABLE`** with explicit documentation of what is missing. A generic “typical BLHeli η ≈ 95%” is **forbidden** unless tied to a cited, tiered source in the report. |
| **★★3** | **`P_motor_input`** for hover energy = **`motor_hover_power_w`** when `hover_applicable=True` and hover OP resolves — **never** bench-max `motor_op_power_w`. Phase 2.5 architecture is frozen. |
| **★★4** | **ESC is not** part of Operating Point identity (motor + propeller + voltage). Loss model reads bound ESC from project state separately — same discipline as Phase 2.5. |
| **★★5** | **`electrical_compatibility`** margin checks (`esc_vs_motor`, `battery_discharge`) may continue using **bench-max / worst-case current** for safety — **do not** conflate that with the hover energy chain (Phase 2.5 IC ★6 precedent). Investigation **maps** both paths; it does **not** mandate changing ERF-2 in slice 1. |
| **★★6** | Each layer keeps its **own evidence tier and its own UNVERIFIABLE outcome**: hover OP can resolve while `P_battery` cannot — that is **honest**, not a bug. |
| **★★7** | Primary validation cases = **Combo A** (hover OP + battery) and **Combo A′** (+ `hobbywing_xrotor_40a_6s`). Combo B remains voltage-honesty contrast only — not the primary loss-model case. |
| **★★8** | Investigation must audit **three loss-model classes** and score each for defendability: **(A)** constant η, **(B)** current-dependent efficiency table/curve, **(C)** resistive / I²R (equivalent circuit). Recommend **at most one** for a future IC — or **none** if data insufficient. |
| **★★9** | If implementation becomes possible, autonomy must use a **new honestly-named field** (investigation proposes naming — e.g. `hover_battery_autonomy_min` or `system_energy_autonomy_min`) — **never** silently replace `hover_energy_autonomy_min` semantics (Phase 2.5 naming lock). |
| **★★10** | **`hover_energy_autonomy_min` remains valid** as “motor input power only” even after Phase 2.6 — it is a **lower bound**, not wrong — unless relabeled in UI. Report must recommend label/provenance strategy. |
| **★★11** | Wiring harness, flight controller, receiver, GPS, BEC loads — **explicitly OUT OF SCOPE** for Phase 2.6 v1 unless investigation finds zero-cost sourced data (expect: defer). |
| **★★12** | **Investigation only** — no production code, no `library/esc/_datos.json` curation, no version bump. Optional xfail repro test documenting today's `P_battery` absence is allowed. |

**Forbidden (block in any future IC without new investigation):**

```text
P_battery = P_motor_input                     ← identity — FORBIDDEN (losses exist physically)
P_battery = P_motor_input / 0.95              ← invented constant η — FORBIDDEN without sourced tier
P_battery from motor_op_power_w                 ← wrong regime — FORBIDDEN
P_battery from battery_capacity_wh alone      ← no physics — FORBIDDEN
Collapse hover + battery + ESC into one OP row ← breaks identity split — FORBIDDEN
```

**Target energy chain (investigation maps each arrow to code or UNVERIFIABLE):**

```text
ProjectState + bound components
      ↓
mass → weight_n → T_hover_motor          [Phase 2.5 — CLOSED]
      ↓
Discrete OP @ thrust → P_motor_input     [Phase 2.5 — CLOSED]
      ↓
Bound ESC SKU + I_motor + V_pack         [Phase 2.6 — THIS CONTRACT]
      ↓
ESC/system loss model OR UNVERIFIABLE
      ↓
P_battery (per motor or total — report decides)
      ↓
(battery sag / SOC — DEFERRED Phase 2.7+)
      ↓
honest autonomy / mission time
```

---

## Known starting facts (Engineer pre-audit — investigator must verify, not assume)

These are **hypotheses to confirm or falsify** with file:line evidence and external source review:

| Fact | Lean | Verify |
|---|---|---|
| `EscSpec` / `_datos.json` carry **current limits only** — no `efficiency`, `r_on_mohm`, or loss table | **Likely true** | `library/esc/_datos.json`, `EscSpec` in `library.py` |
| `hover_energy_autonomy_min` uses `motor_hover_power_w × motor_count` / `battery_capacity_wh` | **True post-2.5** | `calculation_engine.py` |
| No `P_battery` / `motor_system_power_w` / `esc_loss_w` field in `CalculationBundle` | **Likely true** | `tool_schema.py`, grep `src/` |
| HOBBYWING XRotor 40A official docs emphasize **40A/60A, voltage range, low Rds marketing** — **not** η curves | **Likely true** | `source_url`, manual PDF if linked |
| Combo A hover @ payload 1 kg → `motor_hover_power_w ≈ 124.85 W`, `i_motor ≈ 8.4 A` (interpolated) | **From probe** | `cli_probe_minimum_universe_combo.py`, `cli_probe_phase25_hover_energy.py` |
| Combo A′ ESC `esc_vs_motor=compatible` at 40A ESC vs 40A bench OP current | **True** | combo probe — **not** the same question as hover-current compatibility |

**Numeric anchor (Combo A, payload 1 kg, 4 motors, 14.8 V — investigator must re-derive):**

```text
P_motor_input ≈ 124.85 W/motor  (hover, interpolated)
I_motor       ≈  8.4 A/motor      (hover, from OP)
P_battery     =  ???              (today: UNVERIFIABLE by design)
hover_energy_autonomy_min ≈ 2.67 min  (uses P_motor_input — not P_battery)
```

If a sourced loss model yields e.g. 3–8 W ESC loss per motor at this operating point, report must show **before/after autonomy delta** and label tier — even as a **paper exercise** without implementing.

---

## Investigation gates

### Gate A — Current energy chain (post Phase 2.5)

Trace the **live** path from `CalculationEngine.build()` for Combo A:

1. Where `motor_hover_power_w` is set (`_resolve_hover_energy` → `resolve_operating_point_at_thrust`)
2. Where `hover_energy_autonomy_min` is computed
3. Confirm **`P_battery` is not used anywhere** in autonomy today
4. Confirm **`effective_motor_power_w` is not used** when `hover_applicable=True`
5. List every field that would need to exist for a honest `P_battery` chain

**Deliverable:** ASCII diagram with **file:line** per box.

---

### Gate B — Power semantics (six concepts — must not collapse)

| Concept | Expected representation today | Investigation question |
|---|---|---|
| Nominal motor rating | `motor_power_w` | Unchanged — not hover energy |
| Bench-max OP | `motor_op_power_w` / `motor_op_current_a` | Bind/feasibility + ERF-2 margin — not hover energy |
| Hover motor input | `motor_hover_power_w` / `motor_hover_current_a` | **Upstream input to Phase 2.6** |
| ESC loss | **Absent** | Can we define `esc_loss_w` or equivalent honestly? |
| Pack draw | **`P_battery` — absent** | Per-motor or total? AC or DC at pack terminals? |
| Stored energy | `battery_capacity_wh` | Phase 2.6 uses nominal Wh — sag is deferred |

Report must state whether `P_motor_input` in OP rows is **already** `V × I` at the motor terminals (likely yes) and what physical losses sit **between pack and that measurement**.

---

### Gate C — ESC catalog audit

1. Full schema audit: `EscSpec`, `library/esc/_datos.json`, `bind_esc_from_catalog`
2. List every field that **could** support a loss model vs what is **actually populated** for `hobbywing_xrotor_40a_6s`
3. Compare to `PHYSICAL_PROPULSION_ENGINE_PHASE2.md` §5.4 `efficiency` field — **design vs implementation gap**
4. Quantify curation work if investigation recommends adding sourced fields (e.g. `efficiency_table`, `r_on_mohm`, `loss_w_at_current_a[]`)

---

### Gate D — External source audit (defendability tiers)

Investigator must search and tier sources for **`hobbywing_xrotor_40a_6s`** (and generically for multicopter ESCs if needed for context):

| Tier | Meaning | Accept for IC? |
|---|---|---|
| **T1 — manufacturer_test** | Official datasheet/manual with numeric η or loss vs current | Yes, if explicit |
| **T2 — independent_instrumented** | Third-party bench (dyno, power analyzer) with method stated | Yes, with caveats documented |
| **T3 — community/heuristic** | Forum rules of thumb, “~95% efficient” | **No** for implementation — cite as rejected |
| **T4 — none** | No numeric loss data found | → **`P_battery = UNVERIFIABLE`** recommendation |

Minimum external work:

- HOBBYWING product page + manual linked from catalog `source_url`
- At least **one** independent test reference (or explicit “none found”)
- Explicit statement: is **constant η** defensible? Is **I-dependent** model defensible?

**Do not** add data to JSON — document what **would** be curated in a future slice.

---

### Gate E — Loss model options (score, do not implement)

Evaluate each model against Combo A hover point (and optionally bench-max 40 A point as contrast):

| Model | Formula sketch | Data required | Risk |
|---|---|---|---|
| **E1 — Constant η** | `P_battery = P_motor_input / η` | Single sourced η | Hides current dependency |
| **E2 — η(I) table** | interpolate η between sourced current points | ≥2 sourced (I, η) or (I, P_loss) rows | Best if data exists |
| **E3 — I²R** | `P_battery = P_motor_input + I² × R_esc` | Sourced `R_esc` or MOSFET Rds(on) + count | Needs voltage/temp assumptions |
| **E4 — UNVERIFIABLE** | no claim | Document gap | **Default if E1–E3 fail** |

Recommend **one** primary path for a future IC — or **E4** with a precise “data acquisition contract” listing exact fields to curate.

**Strict rule check:** if best available source is T3 only → report verdict **INSUFFICIENT DATA**, not “implement 95%”.

---

### Gate F — Integration surfaces (map only)

For each surface, answer **change needed?** / **new fields?** / **UNVERIFIABLE UX?**

| Surface | File(s) | Questions |
|---|---|---|
| Loss resolver | `library.py` vs `calculation_engine.py` vs extend `electrical_compatibility.py` | Where does loss math live per CLAUDE.md “prefer existing resolvers”? |
| Calc pipeline | `calculation_engine.py` | New branch after `_resolve_hover_energy`? |
| Bundle / persistence | `tool_schema.py`, `latest_results` | New fields + JSON resolution string mirroring hover pattern? |
| Estado / CLI | `orchestrator.py`, `adapters/cli/main.py` | How to show `P_motor_input` vs `P_battery` vs `hover_energy_autonomy_min` without conflation? |
| Probes | `cli_probe_minimum_universe_combo.py`, new probe? | What assertion proves honesty? |
| ERF-2 | `electrical_compatibility.py` | Confirm **no mandatory change** for Phase 2.6 v1 (★★5) |
| DSE | `design_explorer.py` | Inherited via `autonomy_min` — flag side effects only |

**Module placement (Gate I — one recommendation):**

Apply CLAUDE.md test: extend existing owner vs new subsystem. Lean: **`library.py`** for ESC loss lookup (mirrors OP resolver ownership) + **`calculation_engine.py`** for chain orchestration — report confirms or rejects with import-graph evidence.

---

### Gate G — Reference cases

| Case | Must demonstrate |
|---|---|
| **Combo A** | Hover OP resolves → `P_motor_input` known → **`P_battery` today UNVERIFIABLE** → document gap |
| **Combo A′** | + ESC bound → compatibility passes → **still no `P_battery`** unless loss data exists |
| **Combo A — no ESC bound** | Is loss step skipped honestly or assumed zero? Report must recommend policy |
| **Combo B** | Single-row / out-of-range hover — Phase 2.5 None path unchanged |
| **Legacy motor + ESC** | Freeform ESC `current_a` only — loss model availability |

Optional paper trace: if Gate D finds a **hypothetical** sourced η=96% at 8 A, show autonomy delta vs `hover_energy_autonomy_min` — labeled **illustrative only**.

---

### Gate H — Blockers + IC slice recommendation

Classify:

| Candidate | Likely verdict |
|---|---|
| No ESC efficiency in catalog | BLOCKING for implementation — not for investigation |
| No manufacturer η data | BLOCKING for E1 — may still allow E3 if R sourced |
| No independent confirmation | BLOCKING or INSUFFICIENT DATA |
| Phase 2.5 hover path not wired | Should be **NOT BLOCKING** (closed) — verify |
| Battery sag needed first | **REJECT** — wrong order per Engineer (motor→battery before sag) |

Recommend future IC slices (names only):

- **P26-D** — catalog curation (if sourced loss data identified)
- **P26-E** — energy bridge (`P_motor_input` → `P_battery` → new autonomy field)
- Or: **NO IC** — document UNVERIFIABLE boundary and open Phase 2.7 battery investigation

---

## 3. Mandatory output table

| Capability | Supported today? | Evidence | Blocker | First slice |
|---|---|---|---|---|
| Hover `P_motor_input` from OP dataset | | Phase 2.5 | | none |
| Bound ESC identity in project | | catalog | | none |
| ESC continuous current for margin | | ERF-2 | | none |
| Sourced ESC efficiency / loss data | | | | P26-D? |
| `P_battery` from physics (not identity) | | | | P26-E? |
| Separate hover vs system autonomy labels | | | | P26-E? |
| Honest UNVERIFIABLE when data missing | | Phase 2.5 pattern | | docs |
| Battery sag / loaded voltage | | deferred | Phase 2.7 | — |
| Mission regime model | | deferred | future | — |

---

## 4. IN SCOPE

1. Baseline verify @ `fc46938` — suite + Phase 2.5 probe + combo probe  
2. Gates A–I with ★★ locks applied  
3. Combo A / A′ numeric trace for `P_motor_input` and **`P_battery` gap**  
4. ESC catalog + external source audit with tier labels  
5. Loss model scoring (E1–E4)  
6. Integration surface map + module placement recommendation  
7. Mandatory table populated  
8. Engineer ★ questions — mark pre-answered where ★★ locks apply  
9. Verdict: **PASS** (implementable) · **INSUFFICIENT DATA** (UNVERIFIABLE boundary) · **PASS WITH NOTES**  
10. Optional IC outline for `implementation_contract_phase26_esc_system_losses.md`

---

## 5. OUT OF SCOPE

- Production implementation or JSON curation  
- Battery voltage sag, SOC, C-rate, internal resistance model  
- Flight mission / multi-regime energy  
- Changing OP identity to include ESC  
- Inventing η or “industry typical” constants without tier  
- Weakening Phase 2.5 probes or hover architecture  
- Modifying `electrical_compatibility` as mandatory slice-1 work  
- Version bump  

---

## 6. Deliverables

1. `.jes/artifacts/investigation_report_phase26_esc_system_losses.md`  
2. Baseline table (suite + probes @ `fc46938`)  
3. External source appendix (URLs, tiers, what was rejected)  
4. Optional repro script note or xfail test sketch documenting `P_battery` absence  
5. IC outline (or explicit “no IC — insufficient data” recommendation)

---

## 7. Acceptance (Cursor review)

| Verdict | Criteria |
|---|---|
| **PASS** | Gates A–I; table filled; ★★ locks respected; sourced loss model defensible at T1/T2; clear IC slice; Combo A trace complete |
| **PASS WITH NOTES** | **`INSUFFICIENT DATA`** verdict well-evidenced — boundary defined, battery arc correctly deferred; minor placement debate |
| **FAIL** | Proposes invented η; collapses power concepts; reopens Phase 2.5 hover architecture; implements code; skips external audit; recommends battery sag before `P_battery` boundary |

---

## 8. Engineer ★ questions (report surfaces)

| ★ | Question | Pre-lock |
|---|---|---|
| **★1** | Can Jarvis honestly compute `P_battery` today? | Expect **NO** — investigate gap |
| **★2** | Is constant η ever defensible for `hobbywing_xrotor_40a_6s`? | Report decides with tiers — **★★2 forbids invention** |
| **★3** | Best loss model class (E1–E4)? | **★★8** — score all four |
| **★4** | Keep `hover_energy_autonomy_min` as motor-input-only label? | **★★9/★★10 LOCKED** — yes, add sibling if needed |
| **★5** | Change ERF-2 current source to hover current? | **★★5** — report recommends; lean **no** for v1 |
| **★6** | Catalog fields to add if data found? | Report lists — no edit in investigation |
| **★7** | Next arc if INSUFFICIENT DATA — battery sag or ESC test campaign? | Engineer lean: **still define boundary first**; then battery **or** source ESC bench data |
| **★8** | Module placement? | Gate I — one recommendation |
| **★9** | DSE impact? | Report flags inheritance only |
| **★10** | Accept UNVERIFIABLE as successful investigation outcome? | **★★2/★★6 LOCKED** — **yes** |

---

## 9. Suggested investigation order

```text
1. Baseline verify @ fc46938
2. Gate A — live hover energy chain trace
3. Gate B — six power concepts
4. Gate C — ESC catalog schema audit
5. Gate D — external source tier audit (HOBBYWING + independent)
6. Gate E — score E1–E4 against sourced evidence
7. Gate F + I — integration map + module placement
8. Gate G — Combo A / A′ reference cases
9. Gate H — blockers + IC slice (or INSUFFICIENT DATA path)
10. Mandatory table + ★ with pre-lock column
```

---

## 10. Post-investigation workflow

```text
Phase 2.5 checkpoint ✅ (v0.3.5)
      ↓
Phase 2.6 Investigation (this contract)
      ↓
Engineer ★ on report
      ↓
IF PASS → implementation_contract_phase26_esc_system_losses.md
IF INSUFFICIENT DATA → document boundary; decide: ESC test data campaign OR Phase 2.7 battery (still using P_motor_input until P_battery exists)
      ↓
implement → review → probe → checkpoint (only if implemented)
```

**Explicit sequencing lock (Engineer):**

```text
Phase 2.6  motor_input → P_battery   (this contract)
Phase 2.7  battery sag / SOC / R     (only after 2.6 boundary exists)
Phase 3.x  mission regimes           (only after hover chain coherent)
```

---

## 11. Copy-paste prompt for Claude Code

```text
You are the Investigator for Jarvis.

Read and execute:
  .jes/artifacts/investigation_contract_phase26_esc_system_losses.md

Baseline: commit fc46938 · tag v0.3.5 / checkpoint-phase25-hover-energy.

Deliver:
  .jes/artifacts/investigation_report_phase26_esc_system_losses.md

Non-negotiable:
  - Engineer ★★1–★★12 locks in contract § "Engineer locks"
  - Scope: P_motor_input → P_battery ONLY — NO battery sag, NO mission model
  - NO invented η — if data insufficient → P_battery UNVERIFIABLE with exact gap list
  - Phase 2.5 hover architecture is frozen (motor_hover_power_w upstream, not motor_op_power_w)
  - ESC NOT in OP identity — separate bound component
  - Audit hobbywing_xrotor_40a_6s catalog + external sources with tiers T1–T4
  - Score loss models E1–E4; recommend at most one or NONE
  - Combo A / A′ primary reference cases — numeric trace with file:line
  - Keep hover_energy_autonomy_min semantics — propose sibling field if system autonomy added later
  - Do NOT implement production code or edit JSON
  - Cite file:line; fill mandatory table §3
  - Verdict: PASS | INSUFFICIENT DATA | PASS WITH NOTES — INSUFFICIENT DATA is a valid success
```

---

**End of contract.**
