# Design brief — Next after closeout: mission stack → energy + Continuity ladder

**Date:** 2026-09-17  
**Authority:** Engineer — “desarrolla mejor el próximo paso” (no caliper / no bench)  
**Parents:** [vigilancia reflection](engineer_note_vigilancia_next_without_caliper.md) · software closeout #1–#5 **CLOSED**  
**Status:** Design brief — **IC READY FOR ★** → [implementation_contract_mission_mass_energy_b1.md](implementation_contract_mission_mass_energy_b1.md)

---

## 1. Problem (concrete, on live vigilancia)

Today the project can say:

- “I lift ~1.5 kg AUW with margin 3.62”  
- “I carry a RunCam and ELRS” (labels)  
- Continuity: “don’t add generic payload — decide mission margin”

It **cannot** honestly say:

- “This camera+radio stack weighs X g and draws Y W, so AUW/autonomy move”  
- “Next useful step is: declare camera mass / mount camera / set ≥N min endurance”

So vigilancia is stuck between **ASSEMBLY READY** (airframe story) and **mission-ready** (product story), with Continuity correctly refusing the wrong lever and offering no right one.

```text
  [airframe closed] ──x──► [mission numbers] ──► [mission Continuity]
         ▲                        ▲
    done today              MISSING SEAM
```

---

## 2. Product sentence (locked intent)

```text
Cuando ya declaraste cámara/radio de misión, Jarvis te pide (o acepta)
masa y, si puedes, potencia — números tuyos o de ficha, nunca inventados —
los mete en el AUW/energía, y el siguiente paso útil deja de ser
“revisar margen” en el vacío.
```

---

## 3. Claim ceiling (non‑negotiable)

| Jarvis **may** affirm | Jarvis must **not** affirm |
|---|---|
| User/datasheet-declared `mass_g` / `power_w` on mission components entered the mass/energy math | “Validated flight time” / bench OP for Gemfan+XING-E (HD-005) |
| Continuity suggests declare mass / mount / endurance target | Invented grams or watts from model name (“RunCam” ≠ 28 g) |
| Autonomy/margin **recomputed** after those declares (still OP-honest) | Plate L×W, axial prop fit, firmware, MAVLink |
| Double-count warning if `payload_kg` still holds the same kilos | Silent overwrite of `payload_kg` without Engineer-visible honesty |

**Engineer input required for numbers:** paste from datasheet / shop page / your estimate marked provisional — **same discipline as estimated-temporary**, not agent web scrape inventing SKUs.

---

## 4. User journey (target, vigilancia)

1. Project already has `cameras` + `radio_module` (medium) + sim PASS.  
2. Continuity **stops** parking on only “Revisar margen vs carga de misión”.  
3. Next step becomes something like:  
   - **“Declara masa de cámara (g) — ficha o estimación”**  
   - then radio mass / optional power  
   - or **“Monta la cámara en la placa”** if mass already set and mount missing  
   - or **“Declara autonomía objetivo (min)”** if restriction absent  
4. User: `declara la cámara 28 g` / `cámara 28g ficha` (exact grammar TBD in IC).  
5. Writer sets `cameras.properties.mass_g` + mirrors e.g. `mission_payload_mass_kg` (name TBD) into total mass.  
6. `simular` / `estado`: AUW up, margin down a bit, autonomy still OP-honest — Continuity moves to the next hole.

No caliper. No bank. Optional later: `library/cameras` seeds replace declared with cited.

---

## 5. Technical seams (exist today — extend, don’t invent subsystems)

| Seam | Today | Extend |
|---|---|---|
| Identity | `extract_camera_properties` / radio → `model` only | Accept `mass_g` / optional `power_w` when user states them |
| Writers | `set_battery_component` / `set_motor_component` mirror mass | New or extended writer for mission keys → `current_parameters` mirrors |
| Mass math | `payload_kg` + structure + `battery_mass_kg` + `motor_mass_kg` | Add mission component masses; **honesty rule** vs `payload_kg` (see §6) |
| Continuity / reasoning | Mission waterfall ends at “revisar margen” | Ladder after that soft step (deterministic priorities) |
| Restrictions | Autonomy phrases exist in places | Ensure Continuity ranks endurance gap when mission intent + no target |

Prefer **one shared mirror helper** pattern (battery/motor), not a Conversation Engine.

---

## 6. Design fork — `payload_kg` vs component masses (must decide in IC)

Live vigilancia has `payload_kg = 1.0` **and** camera/radio with **zero** mass props → risk of double-counting when masses appear.

| Option | Rule | Pros | Cons |
|---|---|---|---|
| **P1 — Additive + warn** | Mission `mass_g` sum **adds** to AUW; if `payload_kg > 0` and mission masses > 0, Continuity/insight warns “reduce payload_kg or you’re double-counting” | Smallest code; honest | User must fix blob manually |
| **P2 — Displace** | When any mission mass declared, treat `payload_kg` as “other only”; copy shows effective split | Cleaner physics | Bigger behavior change |
| **P3 — Replace blob** | First mission mass declare prompts to zero/lower `payload_kg` | Explicit | Extra wizard friction |

**Lean for first B1:** **P1** (additive + warn). P2 later if smoke hurts.

---

## 7. Continuity ladder (deterministic, after mission intent + sim PASS)

Suggested priority (first hole wins) — exact labels in future IC:

| Priority | Condition | Next step (intent) |
|---|---|---|
| 1 | `cameras` present, no `mass_g` | Declare camera mass (g) |
| 2 | `radio_module` present, no `mass_g` | Declare radio mass (g) |
| 3 | Mission component unmounted (`mounted_on` missing) | Standard mount phrase |
| 4 | Mission intent + no endurance in restrictions | Declare autonomía objetivo |
| 5 | Masses present + high margin | Soft “revisar margen vs misión” (keep) **or** efficiency — never generic increase_payload |
| 6 | Else | Existing Continuity ranker |

This **unblocks** the soft dead-end without LLM.

---

## 8. Ranked Buy shapes

### ★ Recommended primary — **B1-min: mission mass mirror + Continuity ladder**

**ID (working):** `B1-mission-mass-energy` (name free)

| In | Out |
|---|---|
| IDLE/grammar to set `mass_g` (optional `power_w`) on `cameras` / `radio_module` | Invent numbers |
| Mirror into mass calc (P1 + warn) | `library/cameras` seeds (unless Engineer bags ready) |
| Continuity ladder §7 | Plate-box, HD-005, firmware, VTX family (unless thin) |
| Tests + guide one-pager | Version bump unless asked |

**Size:** Medium (writer + calc touch + Continuity + tests). One ★.

### Alternative A — Continuity ladder **only** (thinner)

CTA “declara masa…” without wiring mass yet → frustration if user declares and nothing moves. **Not recommended** alone.

### Alternative B — B0 first (1–2 days)

Investigate: exact mass formula call sites, payload_kg interactions, restriction parsers for autonomía, mount checklist gaps. Useful if calc path is messier than expected. **Do B0 only if ★ on B1-min stalls on “where does mass enter?”**

### Alternative C — Catalog cameras bags

Needs Engineer cite bags (g, mm). **Park** until you supply rows — then supersedes declared mass for those SKUs.

### Parked forever here

Firmware stack · plate caliper · thrust stand · Path N.

---

## 9. What you (Engineer) must bring for smoke (no lab)

Not measurements of *your* craft — **any** cited or estimated grams:

| Example | Source class |
|---|---|
| “RunCam ~12–30 g” from shop page | declared / estimated_temporary |
| “ELRS RX ~1–5 g” | declared |
| “quiero ≥ 8 min” | restriction text |

Jarvis stores provenance; never scrapes a fake catalog.

---

## 10. Success criteria (how we’ll know the next step worked)

On `dron-de-vigilancia-doméstico` after the Buy:

1. Continuity top step is **not** only the soft margin line when camera has no mass.  
2. After declaring camera mass, `estado`/sim shows **higher AUW** (or explicit warn if payload_kg double-count).  
3. Neutral non-mission project unchanged.  
4. Still **no** claim of validated endurance beyond current OP honesty.

---

## 11. Sequencing vs #5

| Now | Then |
|---|---|
| Finish `#5` extended identity (hygiene; little vigilancia unlock) | ★ this brief as **next PRIORIDAD** |
| Do **not** start mass-mirror mid-#5 | Draft IC from §8 primary when #5 CLOSED |

---

## 12. Open questions for Engineer (answer at ★ time)

1. **P1 vs P2** for `payload_kg` (§6)? Default P1.  
2. Include **`power_w`** in v1 or mass-only first? Lean **mass-only v1**; power as follow-on (autonomy already weak from OP).  
3. **VTX** as third identity key now, or checklist text only? Lean **later**.  
4. Grammar language: Spanish only vs ES+EN? Match existing declare assists.

---

## One-line

> El próximo paso no es más montaje ni más catálogo de motores: es **hacer que la misión pese (con tus números) y que Continuity sepa qué pedir después**.
