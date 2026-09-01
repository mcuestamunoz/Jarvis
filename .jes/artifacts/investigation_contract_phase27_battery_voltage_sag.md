# Investigation Contract — Phase 2.7 Battery Voltage / Sag / SOC Model

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_phase27_battery_voltage_sag.md`

**Status:** READY FOR CLAUDE

**Type:** Architecture + physics-model investigation — determine whether Jarvis can move from **nominal catalog battery energy** (`battery_capacity_wh`) to an **honest loaded-battery energy model** (SOC / open-circuit voltage / internal resistance / usable energy under hover load) **without inventing `P_battery`** and **without falsifying Phase 2.6's ESC boundary**. **Not** an implementation plan.

**Checkpoint base:** commit **`fc46938`** · tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`**

**Engineer ratification — Phase 2.6 closure (★ RATIFICADO 2026-09-01):**

```text
PHASE26_P_BATTERY_BOUNDARY — FROZEN

motor_hover_power_w  →  P_motor_input     ✅ known (Phase 2.5)
P_motor_input        →  ESC/system loss   ⛔ UNVERIFIABLE (Phase 2.6 INSUFFICIENT DATA)
ESC/system loss      →  P_battery         ⛔ NO IMPLEMENTAR until T1/T2 ESC bench data

hover_energy_autonomy_min = motor-input-only autonomy (valid interim lower bound)
Do NOT rename or collapse into system_autonomy without sourced chain.
```

**Parallel track (not blocking Phase 2.7):** ESC bench campaign / data acquisition — reopens P26-D/P26-E when T1/T2 ESC-isolated loss data exists.

**Prior arcs (CLOSED — do not re-open without regression proof on `fc46938`):**

| Delivered | Scope |
|---|---|
| **Phase 2.5 Hover Energy** | `motor_hover_*`, `hover_energy_autonomy_min`, bounded OP interpolation |
| **Phase 2.6 ESC/System Loss** | **INSUFFICIENT DATA** — `P_battery` absent; E4 UNVERIFIABLE only defensible outcome |
| **ERF-2 electrical compatibility** | `battery_discharge` = C-rate **limit check** (bench `i_total` vs `i_limit`) — **not** a sag/energy model |
| **Battery catalog foundation** | `BatterySpec`, `energy_wh`, `c_rating`, `max_continuous_current_a` — identity + discharge **limit**, not loaded voltage physics |
| **Combo probes** | Phase 2.5 **4/4** · Phase 2.6 report baseline **2058/2058** · combo **3/3** |

**Still frozen (do not implement in this investigation):**

| ID | Topic |
|---|---|
| **ESC efficiency / `P_battery` bridge** | Phase 2.6 boundary — no η, no `P_battery = P_motor_input` |
| **Flight mission model** | cruise / climb / descent — after single-regime hover chain is coherent |
| **Proportional scaling** | forbidden |
| **G24-B** | `_score_candidate` rewrite |
| **Peukert / thermal runaway / aging** | unless sourced and scoped in report |
| **Full coulomb-counting flight simulation** | out of scope |

**Primary reference SKU (catalog-verified):**

- **`lipo_4s_1500mah`** — CNHL Black Series · Combo A battery · `library/baterias/_datos.json`
- **`sunnysky_r2205_2500` + `gf_5045x3` @ 14.8 V** — hover OP source (Phase 2.5, unchanged)

**Design authority (read-only — context, not proof):**

- [`docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md`](../../docs/PHYSICAL_PROPULSION_ENGINE_PHASE2.md) §5.3 — battery schema lists `internal_resistance` as design wishlist; **not implemented in catalog**
- [`.jes/artifacts/investigation_report_phase26_esc_system_losses.md`](investigation_report_phase26_esc_system_losses.md) — `P_battery` absent; hover chain intact
- [`.jes/artifacts/implementation_contract_phase25_hover_autonomy.md`](implementation_contract_phase25_hover_autonomy.md) — `hover_energy_autonomy_min` naming lock

---

## Engineer locks (★★ — ratified before investigation; report must not contradict)

| Lock | Rule |
|---|---|
| **★★1** | Phase 2.7 scope is **battery loaded-energy physics only**: `V_oc(SOC)`, `R_internal`, `I_load`, `V_loaded`, usable energy / autonomy under load — **not** ESC loss, **not** `P_battery` invention, **not** mission regimes. |
| **★★2** | **Phase 2.6 boundary is frozen.** Investigation must **not** bridge `P_motor_input` → pack draw by assuming η=1, identity `P_battery = V_nom × I_motor`, or any other implicit ESC-loss bypass. |
| **★★3** | **`battery_capacity_wh` semantics must be audited.** Report must trace catalog `energy_wh` → `bind_battery_from_catalog` → `current_parameters["battery_capacity_wh"]` → `calculate_autonomy_min` and state what physical quantity it **actually** represents today (nominal Wh? nameplate? at what voltage/current?). |
| **★★4** | **No invented battery physics.** If no defendable `V_oc(SOC)`, `R_internal`, or usable-energy model exists from sourced data → relevant outputs **`UNVERIFIABLE`** with explicit gap documentation. Generic LiPo rules (e.g. “3.7 V/cell forever”, “R=50 mΩ typical”) are **forbidden** unless tiered T1/T2 for the **bound SKU or chemistry class with explicit substitution rationale**. |
| **★★5** | **Forbidden shortcut:** `battery_capacity_wh → "more realistic autonomy"` without a defined **usable energy under load** model. Wh division alone is **not** “realistic” — it is the **status quo** (`tools/electricity.py`). Any new autonomy figure requires a new honestly-named field and provenance. |
| **★★6** | **`hover_energy_autonomy_min` remains valid** as motor-input-only interim result (Phase 2.5 + Engineer ★). Phase 2.7 may propose a **sibling** field (e.g. `hover_loaded_battery_autonomy_min`) — **never** silently replace or relabel the existing field. |
| **★★7** | **`I_load` without `P_battery` is a first-class investigation problem.** Report must explicitly decide what current (if any) may enter the battery model given ESC loss is unknown: e.g. `motor_hover_current_a` as proxy (with stated assumption), iterative solve, bounds only, or UNVERIFIABLE — **not** assumed equal without tier. |
| **★★8** | Each battery sub-model keeps its **own evidence tier and UNVERIFIABLE outcome**: OCV curve can exist while R_internal does not; usable-energy can be UNVERIFIABLE while a voltage estimate is partial. |
| **★★9** | Primary validation = **Combo A** (`lipo_4s_1500mah` + SunnySky hover OP). Combo A′ (+ ESC) optional — must not change hover numbers; battery model must not require ESC loss data. |
| **★★10** | **`electrical_compatibility._battery_discharge`** (C-rate limit vs bench `i_total`) may remain a **separate margin check** — same discipline as Phase 2.5/2.6 (ERF-2 vs energy chain). Investigation maps both; does not mandate merging them in slice 1. |
| **★★11** | **Investigation only** — no production code, no `library/baterias/_datos.json` curation, no version bump. Optional xfail/repro documenting today's nominal-Wh autonomy is allowed. |
| **★★12** | If a future model is implementable, it must run **autonomously** from `ProjectState` + bound battery identity (deterministic — no LLM), mirroring Phase 2.5's ★★12 pipeline discipline. |

**Forbidden (block in any future IC without new investigation):**

```text
P_battery = P_motor_input                           ← Phase 2.6 boundary — FORBIDDEN
P_battery = motor_hover_power_w                       ← FORBIDDEN
I_pack = motor_hover_current_a  (silent identity)   ← FORBIDDEN without sourced tier + explicit assumption label
autonomy = battery_capacity_wh / P_motor × 60         ← relabeled "realistic" — FORBIDDEN (status quo already)
Invented R_internal or OCV curve                    ← FORBIDDEN without T1/T2
Assume SOC = 100% for entire flight                 ← FORBIDDEN as sole model
Peukert exponent without sourced data               ← FORBIDDEN
Collapse battery sag into ESC loss model            ← FORBIDDEN (separate layers)
```

**Target energy architecture (investigation maps each box to code or UNVERIFIABLE):**

```text
                         ┌── Phase 2.6 (FROZEN) ──────────────────┐
                         │  P_motor_input → ESC loss → P_battery  │
                         │              ⛔ UNVERIFIABLE             │
                         └────────────────────────────────────────┘

ProjectState + bound battery SKU
      ↓
catalog energy_wh / capacity_mah / nominal_voltage / c_rating   [audit ★★3]
      ↓
SOC (initial? fixed? derived?)                                   [Gate E]
      ↓
V_oc(SOC)                                                        [Gate D/E]
      ↓
R_internal(SOC) or equivalent                                      [Gate D/E]
      ↓
I_load policy (given unknown P_battery — ★★7)                      [Gate E]
      ↓
V_loaded = V_oc − I_load × R_internal   (or UNVERIFIABLE)
      ↓
usable energy / effective Wh under hover load                      [Gate E]
      ↓
new honestly-named autonomy field (sibling to hover_energy_autonomy_min)
      ↓
(hover_energy_autonomy_min unchanged — motor-input lower bound)
```

**Independence principle (Engineer ★):**

Phase 2.7 studies **what the battery can deliver under load** given nominal catalog identity — **even while pack-side power draw remains unknown**. The two layers compose later when ESC data exists; they must not be merged prematurely.

---

## Known starting facts (Engineer pre-audit — investigator must verify)

| Fact | Lean | Verify |
|---|---|---|
| Autonomy today = `battery_capacity_wh / (P × motors) × 60` | **True** | `tools/electricity.py:25-30`, `calculation_engine.py` |
| `battery_capacity_wh` comes from catalog `energy_wh` on bind | **True** | `catalog_bind.py`, `component_writers.set_battery_component` |
| `BatterySpec` has `operating_points[]` field but JSON rows are **empty** | **Likely** | `library/baterias/_datos.json` — grep `operating_points` |
| No `R_internal`, no OCV table in catalog | **True** | `BatterySpec` fields, JSON |
| ERF-2 `battery_discharge` uses bench `motor_op_current_a` × motor_count vs C-rate limit | **True** | `electrical_compatibility.py:129-145, 278-288` |
| Combo A @ 4 motors: `i_total=160A > i_limit=150A` → GAP already honest | **True** | combo probe, Phase 2.5 report |
| Hover current @ Combo A ≈ 17 A/motor vs bench 40 A/motor | **From Phase 2.5** | `motor_hover_current_a` vs `motor_op_current_a` |

**Numeric anchor (Combo A, payload 1.718 kg fixture — investigator re-derive; payload 1.0 kg alternate in combo probe):**

```text
battery_capacity_wh     = 22.2 Wh (catalog lipo_4s_1500mah)
motor_hover_power_w     ≈ 251.6 W/motor (interpolated hover)
motor_hover_current_a   ≈ 17.0 A/motor
hover_energy_autonomy_min ≈ 1.32 min  (nominal Wh / motor input power)
V_nom                   = 14.8 V

Today: NO V_loaded, NO SOC, NO R_internal, NO usable-Wh-under-load
```

---

## Investigation gates

### Gate A — Current battery energy chain (post Phase 2.5 / 2.6)

Trace live path for Combo A:

1. `bind_battery_from_catalog("lipo_4s_1500mah")` → what lands in `current_parameters`
2. `_resolve_hover_energy` → `motor_hover_power_w`, `motor_hover_current_a`
3. `calculate_autonomy_min(battery_capacity_wh, motor_hover_power_w × motors)`
4. Confirm **no** voltage sag, SOC, or R term anywhere
5. Confirm **`P_battery` still absent** (Phase 2.6 regression check)
6. List fields needed for honest loaded-battery autonomy

**Deliverable:** ASCII diagram with **file:line** per box.

---

### Gate B — Battery power / energy semantics (must not collapse)

| Concept | Expected today | Investigation question |
|---|---|---|
| Nameplate / catalog energy | `BatterySpec.energy_wh` → `battery_capacity_wh` | Is this measured at nominal V? Full pack Wh? At what cut-off? |
| Nominal voltage | `nominal_voltage` / `cells × 3.7` | Used for OP matching and `I=P/V` fallbacks — not loaded terminal voltage |
| Capacity (Ah) | `capacity_mah` | Consistent with `energy_wh / V_nom`? Document any mismatch |
| C-rate limit | `c_rating`, `max_continuous_current_a` | ERF-2 margin only — not energy depletion |
| Hover motor input power | `motor_hover_power_w` | Upstream load **demand** — not pack-side draw |
| Pack-side power | **`P_battery` — absent (Phase 2.6)** | Must remain absent; Phase 2.7 does not fill this |
| Loaded terminal voltage | **Absent** | Can it be estimated without `P_battery`? |
| Usable energy under load | **Absent** | Minimum definition required before any “realistic” autonomy |
| Autonomy (motor-input) | `hover_energy_autonomy_min` | Lower bound — frozen semantics |
| Autonomy (loaded-battery) | **Absent** | New sibling field only if model defensible |

---

### Gate C — Battery catalog audit

1. Full schema: `BatterySpec`, `_battery_from_raw`, `library/baterias/_datos.json`
2. Per-SKU audit: which rows have `max_continuous_current_a`, `c_rating`, `operating_points`, `source_url`
3. **`lipo_4s_1500mah`** deep audit: verify `energy_wh=22.2` vs `14.8V × 1.5Ah = 22.2 Wh` consistency
4. Compare to `PHYSICAL_PROPULSION_ENGINE_PHASE2.md` §5.3 `internal_resistance` — design vs implementation gap
5. If sourced data found: minimum curation shape (OCV table, R_internal, discharge curve rows) — **document only**

---

### Gate D — External source audit (defendability tiers)

Search for **`lipo_4s_1500mah`** / CNHL 1501004BK and, if SKU-specific data insufficient, **defensible LiPo 4S class** data with explicit substitution rationale:

| Tier | Meaning | Accept for IC? |
|---|---|---|
| **T1 — manufacturer/datasheet** | Official OCV curve, impedance spec, discharge table for this SKU | Yes |
| **T2 — independent_instrumented** | Published bench (impedance spectroscopy, loaded discharge at stated C-rate) | Yes with method + conditions |
| **T3 — chemistry heuristic** | Generic LiPo OCV 3.0–4.2 V/cell, “~50 mΩ” rules | **No** for implementation |
| **T4 — none** | No numeric curve / R for this identity | → **UNVERIFIABLE** for that sub-model |

Minimum external work:

- Catalog `source_url` (Baltic Drones / CNHL listing) — what it actually claims
- Manufacturer page / datasheet if discoverable
- ≥1 independent LiPo electrical model reference (academic or industry)
- Explicit: is **`V_oc(SOC)`** defensible? **`R_internal(SOC)`**? **C-rate capacity derating only** (M3)?

---

### Gate E — Battery model options (score, do not implement)

Evaluate against Combo A hover load:

| Model | Sketch | Data required | Risk |
|---|---|---|---|
| **M1 — Fixed R, fixed V_oc** | `V_loaded = V_oc_nom − I×R` | Sourced R, defined V_oc | Hides SOC; **I_load policy still required (★★7)** |
| **M2 — OCV(SOC) + R(SOC)** | Equivalent circuit, integrate energy | Sourced curves + initial SOC policy | Best if T1/T2 data exists |
| **M3 — C-rate capacity derating only** | Reduce usable Wh by C-rate factor; **no** terminal voltage | Sourced derating table or C-rate vs capacity % | May be partial; must not fake voltage |
| **M4 — Peukert / kinetic** | `I^n` capacity adjustment | Sourced n, chemistry validation | Easy to invent — strict tier gate |
| **M5 — UNVERIFIABLE** | No loaded-battery claim | Document gap | **Valid success** |

**`I_load` policy options (must score under ★★7):**

| Policy | Assumption | Honest? |
|---|---|---|
| **I1** | `I_load = motor_hover_current_a × motor_count` (pack total) | Only if report tiers assumption “ESC losses negligible for current” — **likely rejected** |
| **I2** | `I_load` from `P_motor_input / V_loaded` (iterative with R) | Uses motor power as **demand** — **not** claiming it equals `P_battery`; document circular solve |
| **I3** | Bounds: `I_motor` ≤ `I_pack` ≤ `I_motor / η_min` with η_min UNVERIFIABLE | Honest envelope only |
| **I4** | **UNVERIFIABLE** — cannot define pack current without Phase 2.6 | Valid if no defensible proxy |

Recommend **at most one** implementable model class — or **M5** with precise data-acquisition contract.

---

### Gate F — Integration surfaces (map only)

| Surface | Questions |
|---|---|
| Loss/energy resolver | `library.py` vs `calculation_engine.py` vs new helper — follow Phase 2.5/2.6 precedent |
| Calc pipeline | Slot after `_resolve_hover_energy`, **before** autonomy — parallel branch, not replacing hover path |
| Bundle fields | New sibling autonomy + JSON resolution string (mirror `hover_energy_resolution`) |
| Estado / CLI | Distinct lines: motor-input autonomy vs loaded-battery autonomy vs UNVERIFIABLE |
| Probes | Extend combo / Phase 2.5 probes with loaded-battery assertions or UNVERIFIABLE defaults |
| ERF-2 | Confirm `_battery_discharge` independence (★★10) |
| DSE | Inheritance via `autonomy_min` — flag if new field should **not** feed DSE until Engineer decides |

---

### Gate G — Reference cases

| Case | Must demonstrate |
|---|---|
| **Combo A** | Hover OP + `lipo_4s_1500mah` — trace nominal autonomy vs what a loaded model **would** change (paper exercise OK if labeled) |
| **Combo A — discharge gap** | `i_total=160A > 150A` at bench current — separate from sag; both can be true |
| **Combo A — hover current** | Would hover load (≈68 A total) pass C-rate limit? Does that affect sag investigation scope? |
| **Combo A′ (+ ESC)** | Hover numbers unchanged; battery model must not require ESC η |
| **SKU without `max_continuous_current_a`** | e.g. legacy rows — ERF-2 unverifiable vs energy model unverifiable |
| **Phase 2.6 regression** | Still no `P_battery` field after any paper exercise |

---

### Gate H — Blockers + IC slice recommendation

Classify:

| Candidate | Likely verdict |
|---|---|
| No OCV/R in catalog | BLOCKING for M1/M2 implementation — not for investigation |
| No SKU-specific electrical data | Likely **INSUFFICIENT DATA** for full M2 |
| `I_load` undefined without ESC loss | **BLOCKING or partial** — ★★7 central |
| Phase 2.5 hover path | NOT BLOCKING — verify unchanged |
| M3 C-rate derating only | May be **partial PASS** if sourced — report decides |
| Peukert without data | REJECT |

Recommend:

- **P27-D** — catalog curation (OCV/R/discharge rows) if sourced
- **P27-B** — loaded-battery energy bridge + sibling autonomy field
- Or **NO IC** — document UNVERIFIABLE boundary; keep `hover_energy_autonomy_min` as interim honest figure

**Explicit sequencing (Engineer ★):**

```text
P25  Hover motor energy              ✅ CLOSED
P26  Motor → Battery / ESC loss      ⚠️ CLOSED: UNVERIFIABLE
P27  Battery voltage / sag / SOC     ← THIS CONTRACT
Future: compose P26 + P27 at pack terminal
Future: mission regimes
```

---

## 3. Mandatory output table

| Capability | Supported today? | Evidence | Blocker | First slice |
|---|---|---|---|---|
| Nominal Wh autonomy (`hover_energy_autonomy_min`) | | Phase 2.5 | — | none |
| Catalog `energy_wh` semantics documented | | | audit | P27-D? |
| `V_oc(SOC)` from sourced data | | | | P27-D? |
| `R_internal` / equivalent | | | | P27-D? |
| `I_load` policy without `P_battery` | | ★★7 | ESC boundary | report |
| `V_loaded` under hover load | | | | P27-B? |
| Usable energy under load | | | | P27-B? |
| Sibling loaded-battery autonomy field | | | | P27-B? |
| `P_battery` / ESC loss | **NO (frozen)** | Phase 2.6 | ESC data | P26-D (parallel) |
| ERF-2 C-rate limit check | | ERF-2 | — | none |
| Battery sag + ESC loss composed | | | both layers | future |

---

## 4. IN SCOPE

1. Baseline @ `fc46938` + Phase 2.5/2.6 reports + probes  
2. Gates A–H with ★★ locks  
3. Combo A numeric trace (nominal vs loaded-battery gap)  
4. Catalog + external source audit with tiers  
5. Battery model scoring M1–M5 + `I_load` policies I1–I4  
6. **`battery_capacity_wh` meaning** — explicit audit (★★3)  
7. Mandatory table populated  
8. Engineer ★ questions  
9. Verdict: **PASS** · **INSUFFICIENT DATA** · **PASS WITH NOTES** (partial M3 only is valid WITH NOTES)  
10. Optional IC outline — or explicit NO IC  

---

## 5. OUT OF SCOPE

- Production implementation or JSON curation  
- ESC efficiency / `P_battery` (Phase 2.6 frozen)  
- Mission multi-regime model  
- Inventing OCV/R/Peukert without tier  
- Relabeling `hover_energy_autonomy_min` as “real autonomy”  
- Weakening Phase 2.5/2.6 probes  
- Version bump  

---

## 6. Deliverables

1. `.jes/artifacts/investigation_report_phase27_battery_voltage_sag.md`  
2. Baseline table (suite + probes)  
3. External source appendix (URLs, tiers, rejected heuristics)  
4. `battery_capacity_wh` semantics memo (within report §Gate B/C)  
5. `I_load` policy recommendation (within report §Gate E) — even if UNVERIFIABLE  
6. Optional IC outline or explicit NO IC  

---

## 7. Acceptance (Cursor review)

| Verdict | Criteria |
|---|---|
| **PASS** | Defensible M1/M2/M3 with T1/T2 data; `I_load` policy explicit; sibling autonomy naming; ★★2/★★5/★★6 respected; Combo A traced |
| **PASS WITH NOTES** | Partial model only (e.g. M3 derating without voltage); or `I_load` UNVERIFIABLE but usable-energy bounds defined |
| **INSUFFICIENT DATA** | Well-evidenced UNVERIFIABLE boundary; **valid success** — no IC; `hover_energy_autonomy_min` remains interim figure |
| **FAIL** | Invents OCV/R; sets `P_battery`; relabels hover autonomy as “real”; skips ★★3 audit; recommends battery sag that assumes `P_battery`; implements code |

---

## 8. Engineer ★ questions (report surfaces)

| ★ | Question | Pre-lock |
|---|---|---|
| **★1** | Can Jarvis honestly compute loaded-battery autonomy today? | Expect **NO** |
| **★2** | What does `battery_capacity_wh` actually mean in catalog + calc? | **★★3 — report must answer** |
| **★3** | Best battery model class M1–M5? | Report scores all |
| **★4** | What `I_load` policy is defensible without `P_battery`? | **★★7 — report decides** |
| **★5** | Keep `hover_energy_autonomy_min` unchanged? | **★★6 LOCKED — yes** |
| **★6** | Sibling field naming? | Report proposes |
| **★7** | Is M3 (C-rate derating only) worth a partial IC? | Report decides |
| **★8** | Change ERF-2 to hover current? | **★★10 lean — no** |
| **★9** | Next after P27 if INSUFFICIENT DATA? | ESC bench vs generic LiPo class data vs accept interim lower bound |
| **★10** | Accept UNVERIFIABLE as success? | **★★4/★★8 LOCKED — yes** |

---

## 9. Suggested investigation order

```text
1. Baseline verify @ fc46938
2. Gate A — live battery + hover autonomy chain
3. Gate B + C — semantics + catalog audit (★★3)
4. Gate D — external source tiers (CNHL SKU + LiPo class)
5. Gate E — score M1–M5 and I_load I1–I4
6. Gate G — Combo A reference cases
7. Gate F + H — integration map + IC / NO IC recommendation
8. Mandatory table + ★
```

---

## 10. Post-investigation workflow

```text
Phase 2.6 boundary ✅ RATIFICADO (INSUFFICIENT DATA)
      ↓
Phase 2.7 Investigation (this contract)
      ↓
Engineer ★ on report
      ↓
IF PASS → implementation_contract_phase27_battery_voltage_sag.md
IF INSUFFICIENT DATA → interim: hover_energy_autonomy_min + documented gap
IF partial → PASS WITH NOTES + bounded IC (e.g. M3 only)
      ↓
Future: ESC bench data (P26 reopen) + P27 compose → pack-terminal chain
      ↓
Future: mission regimes
```

---

## 11. Copy-paste prompt for Claude Code

```text
You are the Investigator for Jarvis.

Read and execute:
  .jes/artifacts/investigation_contract_phase27_battery_voltage_sag.md

Baseline: commit fc46938 · tag v0.3.5 / checkpoint-phase25-hover-energy.
Phase 2.6 boundary RATIFICADO — P_battery UNVERIFIABLE — do NOT reopen.

Deliver:
  .jes/artifacts/investigation_report_phase27_battery_voltage_sag.md

Non-negotiable:
  - Engineer ★★1–★★12 locks in contract § "Engineer locks"
  - Scope: battery V_oc / R / I_load / V_loaded / usable energy ONLY
  - NO P_battery, NO ESC η, NO P_motor_input = pack draw shortcuts
  - Audit battery_capacity_wh semantics end-to-end (★★3)
  - I_load without P_battery is a first-class problem (★★7) — score I1–I4
  - hover_energy_autonomy_min stays motor-input-only (★★6)
  - Score M1–M5; INSUFFICIENT DATA is valid success
  - Combo A (lipo_4s_1500mah + SunnySky hover) primary reference
  - Do NOT implement production code or edit JSON
  - Cite file:line; fill mandatory table §3
  - ERF-2 battery_discharge is separate margin check (★★10)
```

---

**End of contract.**
