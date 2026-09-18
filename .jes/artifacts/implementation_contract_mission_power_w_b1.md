# Implementation Contract — Mission `power_w` → energy / autonomía (`B1-mission-power-w`)

**Project:** Jarvis  
**Date:** 2026-09-18  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **CLOSED** 2026-09-18 — Cursor PASS WITH NOTES · Engineer smoke ACCEPT WITH NOTES (vigilancia)

**Parents:**
- Design brief — [engineer_note_mission_mass_energy_next_step.md](engineer_note_mission_mass_energy_next_step.md) (§ mass+power intent; mass Buy deferred power)
- Mass CLOSED — [B1-mission-mass-energy](implementation_contract_mission_mass_energy_b1.md) — `mass_g` → AUW only; lock #4: no power→energy
- Mount+endurance CLOSED — [B1-mission-continuity-mount-endurance](implementation_contract_mission_continuity_mount_endurance_b1.md)
- Cameras seed CLOSED — Phoenix 2 cite carries **mA in `source_note` only** (not projected `power_w`)
- Live smoke: vigilancia ~**0.7 min** vs objetivo 8 — OP propulsion only; camera/radio draw **not** in denominator
- Calc today — `calculation_engine.py`: autonomy = `Wh / (hover_or_effective_motor_power × motors)` — no mission accessory term

**Type:** When the user **declares** `power_w` on mission components (`cameras`, `radio_module`), Jarvis **stores** it, **mirrors** the sum into energy math as an **additive accessory draw**, and Continuity can ask for missing watts before parking on soft margin / below-target. Autonomy stays OP-honest and **must not** claim validated flight.  
**Not** inventing watts from “RunCam” / “ELRS”.  
**Not** auto-converting Phoenix `200mA@5V` → W without an explicit Engineer-locked formula + projected catalog field (default: **declare-only**; optional catalog `power_w` only if JSON row has the field).  
**Not** VTX · firmware · HD-005 bench · version bump · Conversation Engine · workspace mutate (default tests-only).

**Output:** `.jes/artifacts/implementation_report_mission_power_w_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3100** · UI ≥**105** (or current green at ★)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-mission-power-w`** — declared mission `power_w` → energy denominator + Continuity hole |
| 2 | Keys | **`cameras`** and **`radio_module` only** |
| 3 | Numbers | User- or datasheet-**declared** only (`source=declared` or estimated_temporary discipline if phrase marks estimación). **Never** invent from model string |
| 4 | Catalog | Do **not** invent `power_w` on Phoenix bind this Buy. If a future row has explicit `power_w` in JSON, bind may project it (same as `mass_g`) — report; default seed stays without field |
| 5 | Mirror | Canonical: `components[key].properties["power_w"]` (unit W). Mirror sum → `current_parameters["mission_accessory_power_w"]` (name locked unless report justifies alias) via dedicated writer + `COMPONENT_MIRRORED_PARAMS`. Clearing recomputes |
| 6 | Energy seam | In `calculation_engine` autonomy paths (hover **and** non-hover):  
`total_draw_w = (motor_hover_or_effective_power_w × motors) + mission_accessory_power_w`  
Accessory is **not** multiplied by motor count. If accessory missing/0 → byte-identical autonomy to today |
| 7 | Honesty | Autonomy/sim copy must keep “simplified / not certification” voice. Below-target WARN unchanged in shape. **Forbidden:** “vuelo validado”, inventing better OP to meet 8 min |
| 8 | Grammar | Deterministic ES(+EN) declare-assist, mirror mass Buy style:  
`cámara`/`camera` + number + `W`/`w`/`vatios` (e.g. `cámara 1 W`, `declara la cámara 1.0W`) · `radio`/`elrs` + number + `W`. Target must already exist; else honest refuse |
| 9 | Completeness | Declaring `power_w` does **not** alone bump identity to `high` |
| 10 | Continuity | Extend mission ladder **after mass holes, before soft margin** (exact slot in report; recommend after mount + autonomy-target steps already shipped, **or** parallel “first power hole” after masses — pick one and test): if mission component present and `power_w` missing → **“Declara potencia de cámara/radio (W)”** · `action_type` e.g. `declare_mission_power`. Prefer **one** suggestion (camera before radio). Neutral projects unchanged |
| 11 | Guide | USER_GUIDE: how to declare W; honesty that autonomía baja si sumas draw; no claim de vuelo; note Phoenix mA stays citation until declared W or future catalog field |
| 12 | Forbidden | mA→W invention · Conversation Engine · version bump · LLM · folding accessory into `motor_power_w` / overwriting OP |
| 13 | Live | Default tests-only. Smoke on vigilancia (§3) |

**Product sentence:**

```text
Si declaras los vatios de cámara/radio, Jarvis los suma al consumo
del modelo energético — la autonomía se recalcula con honestidad,
sin inventar ficha ni certificar el vuelo.
```

### 0.1 Enough / not enough

| Enough this Buy | Not this Buy |
|---|---|
| Declare W → mirror → autonomy denominator moves | Invent W from brand / mA scrape |
| Continuity can ask for missing W | Validated endurance / bench OP |
| Tests + guide | Auto Phoenix power_w without JSON field · VTX · M4 |

### 0.2 Defaults at ★ (override if Engineer says otherwise)

| Topic | Default |
|---|---|
| Continuity slot | After M2 autonomy-target step, before soft margin (power hole only if masses done) |
| Phoenix | No auto W; user may `cámara 1 W` from cite (200mA@5V ≈ 1 W — **user** owns the number) |
| Radio | Declare-only unless later catalog |

---

## 1. You (Claude)

1. Grammar + writer + mirror param + calc additive draw (both autonomy paths).  
2. Continuity ladder slot per §0.2.  
3. Tests T1–T10 + guide + report (exact phrases, param name, before/after autonomy on fixture).  
4. No version bump. No invent. No workspace write unless smoke.

**STOP if** forced to invent watts from model/mA without declared number or JSON `power_w`.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Parse `cámara 1 W` → cameras.power_w declared |
| T2 | Parse radio W similarly |
| T3 | Missing identity → honest refuse |
| T4 | Mirror `mission_accessory_power_w` = sum W |
| T5 | Calc: with accessory > 0, autonomy_min **strictly less** than identical state with 0 (same battery/motors) |
| T6 | Accessory 0 / absent → autonomy unchanged vs pre-Buy fixture |
| T7 | Continuity CTA when power missing (mission intent) |
| T8 | Neutral project (no mission) → no power CTA / no behavior change |
| T9 | Direct write of mirrored param still blocked (gatekeeper) |
| T10 | Full suite; `0.4.1` |

---

## 3. Smoke (Engineer)

On **`dron-de-vigilancia-doméstico`** (Phoenix bound, masses/mount/autonomy as today):

1. Note baseline autonomía (~0.7 min).  
2. `cámara 1 W` (or your cited estimate) → confirm stored + mirror.  
3. `calcular` / `simular` → autonomía **≤** baseline (honest); still WARN vs 8 min; **no** validated-flight claim.  
4. Optional: `estado` Continuity no longer asks camera power if set.  
5. Optional: radio W.

**ACCEPT when:** declared watts move energy math; no invention; honesty preserved.

---

## 4. Out of scope

| Item | Note |
|---|---|
| Auto mA→W from Phoenix `source_note` | Needs separate ★ + formula lock |
| VTX / more keys | M4+ |
| HD-005 exact OP | Lab |
| Version bump / Fase C | After M7 |

---

## 5. Done when

- [x] Engineer ★ (implement proceeded)  
- [x] Grammar + mirror + calc + Continuity + T1–T10 + report + guide  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_mission_power_w_b1.md)  
- [x] Engineer smoke ACCEPT WITH NOTES (vigilancia 2026-09-18) — declare OK; displayed autonomía stays 0.7 (CLI 1-decimal vs ~kW motor draw); honesty WARN preserved; `[runcam_phoenix_2]` display OK

---

## 6. Handoff

```text
Engineer → smoke §3 on vigilancia
Cursor   → close on ACCEPT
Cola     → M4 / M6 / M7
```
