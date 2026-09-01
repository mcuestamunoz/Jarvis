# Data Acquisition Contract — P27-M3 C-rate capacity derating

**Project:** Jarvis  
**Date:** 2026-09-01  
**Authority:** Engineer ★9 on Phase 2.7  
**Type:** **External data campaign** — not an Implementation Contract, not a code investigation.  
**Unblocks (later, only if T1/T2 land):** bounded M3 investigation/IC for usable Wh vs C-rate.  
**Does not unblock:** `P_battery`, `V_loaded`, OCV/R, mission regimes.

**SKU (locked):** `lipo_4s_1500mah` — CNHL Black Series · part `1501004BK` · Combo A  
**Catalog facts (do not “correct” without source):** 14.8 V · 1500 mAh · 22.2 Wh nameplate · 100 C / 150 A continuous (derived from C-rating)

**Why this campaign (not ESC bench first):** Phase 2.5 already moved Combo A hover power by ×2.35. Phase 2.6 paper η≈96% is ~4% autonomy. Combo A hover current is **≈45.4 C** (`17.01 A × 4 / 1.5 Ah`) — outside the “derating is rounding” regime. A sourced table here is the highest-leverage unknown still compatible with `PHASE26_P_BATTERY_BOUNDARY` (M3 needs no `P_battery`).

**Parallel (not this contract):** ESC-isolated bench of `hobbywing_xrotor_40a_6s` — see Phase 2.6 Gate H. Do not mix datasets into one slice.

---

## 1. Goal

Obtain a **tiered** mapping:

```text
C-rate  →  usable_capacity_fraction   (vs a stated 1C or manufacturer reference)
           + cutoff voltage
           + temperature (or “uncontrolled / stated ambient”)
           + source_type (T1 | T2)
```

Minimum usable table: **≥3 points** that bracket Combo A hover:

| Point | Target C (approx) | Why |
|---|---|---|
| Reference | **1 C** (1.5 A) or manufacturer’s rated capacity condition | Denominator for “% of nameplate” |
| Mid | **10–20 C** | Shape of derating curve |
| Hover-relevant | **40–50 C** (≈60–75 A pack) | Combo A hover ≈ 45 C · 68 A |

Optional fourth: **~100 C / 150 A** (pack continuous rating / ERF-2 bench case). Not required to start M3.

**Capacity at the hover point is the value that would later feed a sibling autonomy field.** 1C-only data does **not** satisfy this contract.

---

## 2. Acceptable evidence tiers

| Tier | Meaning | Accept for a future M3 IC? |
|---|---|---|
| **T1 — manufacturer/datasheet** | CNHL (or OEM cell) discharge table or plot for **this SKU** or a documented same-part listing, with axes readable | **Yes** |
| **T2 — independent instrumented** | Logged discharge of **this pack** (or a pack with explicit substitution rationale: 4S, ~1500 mAh, ≥100 C LiPo, same chemistry class) at stated C-rates, method, cutoff | **Yes**, with method + conditions |
| **T3 — hobby chart / generic LiPo** | “Typical 4.2–3.0 V”, unnamed 25C plots, forum %, Peukert n from Wikipedia | **No** |
| **T4 — none** | Qualitative “high-C loses capacity” | **No** — campaign remains open |

Substitution (T2 only): must state chemistry, S-count, capacity, C-rating, and **why** it stands in for `1501004BK`. Silent class swap is rejection.

---

## 3. Measurement / extract requirements (T2)

If commissioning a bench rather than finding a datasheet:

1. **Pack identity** — SKU / batch / measured mass vs catalog 183 g.  
2. **Charge** — stated charge C and end-of-charge voltage (typically 4.2 V/cell unless manufacturer differs).  
3. **Discharge** — constant current (or constant C) at each table row; **cutoff voltage stated** (e.g. 3.0 or 3.3 V/cell — do not mix cutoffs across rows without labeling).  
4. **Logged** — time, current, pack voltage; usable Ah = ∫I dt until cutoff; usable Wh = ∫V·I dt until cutoff.  
5. **Rest** — note if capacity is immediate or after rest (OCV recovery is **out of M3 scope**; do not turn this campaign into an OCV curve unless extra, clearly separated files).  
6. **Safety** — 45 C on a 100 C pack is inside nameplate continuous current (~68 A < 150 A) but thermal runaway is a lab risk. This contract does **not** specify a test procedure for untrained use; if no safe bench exists, **stop at T1 search** (manufacturer plot) rather than improvise.

T1 extract from a plot is valid if C-rates and % capacity (or Ah) are readable and the cutoff is stated or industry-standard on that sheet.

---

## 4. What this does **not** acquire

| Out of scope | Why |
|---|---|
| `R_internal` / EIS / sag voltage | M2 — separate campaign; still blocked on I_load (I4) |
| OCV(SOC) table | Same |
| ESC η / `P_battery` | Phase 2.6 frozen |
| Peukert exponent fitted from two points | Easy to invent — forbidden as sole model |
| Relabeling `hover_energy_autonomy_min` | ★★6 / ★5 |

---

## 5. Current used as C-rate (lock for any future IC)

Pack C-rate is `I_pack / 1.5 Ah`. `I_pack` is **not** known (`PHASE26` + P27 ★4).

For **this campaign**, quote C-rate from **measured pack current** on the bench (the instrument’s I). That is T2 truth for the table itself.

For a **future Jarvis M3 apply**, the IC must pick an explicit proxy and label it — default lean (not implemented):

```text
C_hover_proxy = (motor_hover_current_a × motor_count) / capacity_Ah
              ≈ 45.4 C for Combo A
```

That proxy is **I1-class** (motor current as pack current). Allowed only as a **named assumption** after this table exists — never silently. Do not use bench-max 160 A (107 C) as the hover energy derate.

---

## 6. Done criteria (campaign)

**PASS (data in hand):** a T1 or T2 table with ≥3 points including a 40–50 C neighborhood, cutoff stated, stored as a JES appendix (markdown + numbers; **no** `library/baterias/_datos.json` edit until a later IC).

**OPEN (still INSUFFICIENT DATA):** no T1 sheet and no safe T2 run. Autonomy stays `hover_energy_autonomy_min`. This is an allowed steady state.

**FAIL:** inserting T3/T4 numbers into catalog or calc “to have a derate”.

---

## 7. After PASS — not automatic implementation

```text
data appendix (this campaign)
      ↓
short investigation delta (M3 only — usable Wh fraction, no V_loaded)
      ↓
Engineer ★
      ↓
implementation_contract  (sibling field + provenance; hover_energy_autonomy_min untouched)
```

Until that IC: **zero production code.**

---

## 8. Practical first actions (human, not agent)

1. Search CNHL / Black Series 1500 mAh 100C **discharge graphs** (manufacturer PDF, not retailer marketing).  
2. If none: search independent instrumented reviews of **1501004BK** specifically.  
3. If none: decide whether a lab discharge at 1 C / ~15 C / ~45 C is available. If not, leave campaign **OPEN** and keep 1.32 min.

Do **not** ask the implementation agent to invent the table or scrape T3 hobby charts into JSON.

---

## 9. Day-0 T1 search (2026-09-01) — still OPEN

First-pass web search after ratification. **No table ingested.** Campaign remains **OPEN**.

| Source | What it has | Tier vs this SKU |
|---|---|---|
| Baltic Drones listing (catalog `source_url`, P27 Gate D) | 1500 mAh / 14.8 V / 100C / 183 g | **T4** — already audited |
| ChinaHobbyLine AU / Rotorama / Amazon listings for `1501004BK` | Same nameplate fields; Rotorama marks pack **discontinued** | **T4** — no curve |
| RCexplained CNHL **5200 mAh 4S 90C** discharge + IR | Instrumented, **wrong SKU** (capacity/C-rating class mismatch) | **Reject** — no silent substitution |
| ChinaHobbyLine “17 packs C-rating” blog | Marketing/index article; not a `{C, %}` table for `1501004BK` | **T3/unusable** |

**Conclusion:** manufacturer/retailer surface for this part is identity-only (same as P27 Gate D). Next human step is either a lab T2 discharge at 1 C / ~15 C / ~45 C, or leave OPEN and keep 1.32 min.
