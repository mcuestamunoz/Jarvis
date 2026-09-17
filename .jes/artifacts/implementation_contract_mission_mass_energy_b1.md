# Implementation Contract — Mission mass → AUW + Continuity ladder (`B1-mission-mass-energy`)

**Project:** Jarvis  
**Date:** 2026-09-17  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **CLOSED** — Engineer smoke ACCEPT 2026-09-17 (vigilancia: declare-camera-mass → declare-radio-mass → soft margin)

**Parents:**
- Design brief — [engineer_note_mission_mass_energy_next_step.md](engineer_note_mission_mass_energy_next_step.md)
- Vigilancia reflection — [engineer_note_vigilancia_next_without_caliper.md](engineer_note_vigilancia_next_without_caliper.md)
- Software closeout **#1** CLOSED — [B1-continuity-mission-intent](implementation_contract_continuity_mission_intent_b1.md) (soft dead-end: “Revisar margen vs carga de misión”)
- Mission payload identity CLOSED — `cameras` / `radio_module` declarable; mass props **not** wired into AUW
- Mass math today — `calculation_engine.py`: `total = payload_kg + structure + battery_mass_kg + motor_mass_kg` (no mission-component term)
- Mirror pattern — `set_battery_component` / `set_motor_component` → `COMPONENT_MIRRORED_PARAMS`

**Type:** When the user **declares** (ficha / estimación) `mass_g` on mission components (`cameras`, `radio_module`), Jarvis **stores** those numbers, **mirrors** their sum into mass calc (**P1**: additive + double-count warn vs `payload_kg`), and Continuity’s mission-aware high-margin path **stops parking** on only “Revisar margen…” — it ranks the next honest hole (declare mass → mount → endurance).  
**Not** inventing grams from model names.  
**Not** `library/cameras` / radio physics bags.  
**Not** `power_w` / energy draw into autonomy (follow-on ★).  
**Not** VTX as a third identity key.  
**Not** P2/P3 `payload_kg` displace/replace.  
**Not** Conversation Engine / LLM.  
**Not** version bump. **Not** `workspace/` mutation (tests-only; Engineer smoke on live vigilancia is read + declare, may save if Engineer chooses).

**Output:** `.jes/artifacts/implementation_report_mission_mass_energy_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3044** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-mission-mass-energy`** — declared mission `mass_g` → AUW mirror + Continuity ladder |
| 2 | Keys in | **`cameras`** and **`radio_module` only**. No `payload_bay` / `arm` / VTX this Buy |
| 3 | Numbers | User- or datasheet-**declared** only (`source` = `declared` or existing `estimated_temporary` discipline if the phrase marks estimación). **Never** invent mass from model string (“RunCam” ≠ 28 g) |
| 4 | Scope v1 | **`mass_g` only**. Optional parse of `power_w` may be **ignored** or stored on the component **without** energy/autonomy coupling — report choice; default: **do not claim power entered energy math** |
| 5 | `payload_kg` policy | **P1 — Additive + warn.** Mission masses **add** to AUW via a new mirrored param (name TBD in report; working: `mission_payload_mass_kg`). If `payload_kg > 0` **and** mission mass sum > 0 → Continuity/insight **warns** double-count (“reduce `payload_kg` or you’re counting twice”). **Do not** silently zero/displace `payload_kg` |
| 6 | Mirror seam | Canonical: `components[key].properties["mass_g"]`. Mirror: sum(g)/1000 → `current_parameters[mission_payload_mass_kg]` **only** via a dedicated writer/helper (extend `component_writers` + register in `COMPONENT_MIRRORED_PARAMS`). Calc: `total_mass` includes that term alongside battery/motor. Clearing mass clears/recomputes the mirror |
| 7 | Grammar (IDLE / iterate) | Deterministic phrases — match existing declare-assist style (ES primary; EN aliases OK). Minimum accepted shapes (exact regex in report): |
| 7a | | `cámara`/`camara`/`camera` + number + `g`/`gramos` (e.g. `cámara 28 g`, `declara la cámara 28g`, `camera 28g ficha`) |
| 7b | | `radio`/`elrs`/`rx` + number + `g` (e.g. `radio 3 g`, `declara el radio 5g`) — tune so bare `rx` does not steal unrelated paths (reuse radio identity keyword discipline) |
| 7c | | Must target an **already present** component key when ambiguous; if cameras present and phrase is camera-shaped → write cameras; same for radio. If target missing → honest refuse (“declara primero la cámara”) — **do not** auto-create identity this Buy |
| 8 | Completeness | Declaring `mass_g` does **not** by itself bump identity to `high`. Keep cameras/radio completeness ladder as today (model → medium). Mass is orthogonal engineering data |
| 9 | Continuity ladder | Extend `_mission_aware_high_margin_suggestion` (and Continuity consumption of it) so that when cameras+radio are medium+ the soft **“Revisar margen vs carga de misión”** is **not** the only outcome. **First hole wins** (exact labels in report; Spanish Continuity voice): |
| 9a | | `cameras` present, no `mass_g` → **“Declara masa de cámara (g)”** · `action_type` e.g. `declare_mission_mass` |
| 9b | | `radio_module` present, no `mass_g` → **“Declara masa de radio (g)”** |
| 9c | | Mission component present, `mounted_on` missing → existing standard mount Continuity phrase / priority (reuse mount assist — do not invent a second mount system) |
| 9d | | `mission_intent_active` + no autonomy target in restrictions/`autonomy_target_min` → **“Declara autonomía objetivo (min)”** — wire only if a **deterministic** restriction/param path already exists; else document gap and keep ladder stop at 9c + soft margin |
| 9e | | Else → keep soft **“Revisar margen vs carga de misión”** (never `increase_payload` under mission intent) |
| 10 | Double-count insight | When P1 warn condition holds, surface a clear insight/Continuity note (not only buried logs). Must not block sim |
| 11 | Neutral projects | No mission components + no mission keywords → byte-identical Continuity/`increase_payload` behavior to today |
| 12 | Guide | One short USER_GUIDE (or craft montage) note: how to declare mission grams; honesty that AUW rises only after declare; double-count vs `payload_kg` |
| 13 | Forbidden | Invent mass · catalog camera bags · `power_w`→autonomy coupling as “validated” · P2/P3 · fold into `payload_kg` silently · Conversation Engine · version bump · LLM |
| 14 | Live | Default **tests-only**. Engineer smoke on `dron-de-vigilancia-doméstico` (§3) |

**Product sentence:**

```text
Cuando ya declaraste cámara/radio de misión, Jarvis te pide (o acepta)
masa — números tuyos o de ficha, nunca inventados —
los mete en el AUW, y el siguiente paso útil deja de ser
“revisar margen” en el vacío.
```

### 0.1 Enough / not enough

| Enough this Buy | Not this Buy |
|---|---|
| Declare `mass_g` on cameras/radio → AUW moves (P1 + warn) | Invented grams from SKU name |
| Continuity ladder 9a–9e (9d best-effort if path exists) | Full energy draw / `power_w` autonomy |
| Tests + guide one-pager | `library/cameras` seeds · VTX · plate-box · HD-* |
| | P2 displace / auto-zero `payload_kg` |

### 0.2 Defaults at ★ (brief §12 — override if Engineer says otherwise)

| Q | Default lock |
|---|---|
| P1 vs P2 | **P1** |
| `power_w` in v1 | **Mass-only** (no energy coupling) |
| VTX | **Later** |
| Grammar language | **ES + EN** aliases, existing declare style |

---

## 1. You (Claude)

1. Inspect calc + writers + Continuity mission waterfall; propose mirror key name in report.  
2. Writer/helper: set/clear `mass_g` on cameras/radio → recompute `mission_payload_mass_kg` (or chosen name); register mirrored param.  
3. `CalculationEngine.build`: include mission mass term in `total_mass`.  
4. IDLE/orchestrator grammar for §0.7 — refuse invent / missing target.  
5. Extend mission-aware Continuity ladder (§0.9); double-count warn (§0.10).  
6. Tests T1–T12 + guide patch + report (exact phrases, labels, mirror key).  
7. No version bump. No workspace write unless Engineer smoke saves.

**STOP if** forced to invent mass, silently overwrite `payload_kg`, or add Conversation Engine.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Helper/writer: set cameras `mass_g=28` → mirrored kg ≈ 0.028; calc `total_mass_kg` rises vs baseline with same `payload_kg` |
| T2 | Radio mass adds; both sum correctly |
| T3 | Clear / remove mass → mirror drops; total regresses |
| T4 | P1 warn: `payload_kg>0` + mission mass>0 → insight/Continuity warn present |
| T5 | Grammar: `cámara 28 g` (or locked ES phrase) on project with cameras → property set, source declared |
| T6 | Grammar refuse: same phrase when cameras absent → no invent stub |
| T7 | Never invent: identity-only “cámara RunCam” still has no `mass_g` |
| T8 | Continuity: cameras medium+, no mass → top mission suggestion is declare-camera-mass (not only soft margin) |
| T9 | After camera mass set, no radio mass → declare-radio-mass (or next hole per ladder) |
| T10 | Neutral high-margin project → `increase_payload` still available (regression #1) |
| T11 | Mission intent + both masses set → soft margin OK; still **no** `increase_payload` |
| T12 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

On live **`dron-de-vigilancia-doméstico`** (or equivalent with cameras+radio medium, sim PASS, high margin, `payload_kg` likely > 0):

1. `estado` → Siguiente paso **not** only “Revisar margen…” if camera has no `mass_g` — expect declare-mass CTA.  
2. Declare e.g. `cámara 28 g` (your cite or provisional estimate).  
3. `simular` / `estado` → AUW **up** (or explicit double-count warn if `payload_kg` still holds the same kilos).  
4. Optional: `radio 3 g` → AUW moves again; Continuity advances (mount / autonomía / soft margin).  
5. Neutral throwaway (no mission) unchanged.

**ACCEPT when:** Continuity asks for mass when missing; declared grams move AUW honestly; no fake validated endurance.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| `power_w` → autonomy / draw | Follow-on Buy |
| `library/cameras` cited bags | Needs Engineer cite rows |
| VTX identity | Parked |
| P2/P3 payload_kg | Only if P1 smoke hurts |
| Plate-box / Path N / HD-* | Parked |
| payload_bay / arm mass | Not this Buy |

---

## 5. Done when

- [x] Mirror + calc + grammar + Continuity ladder + T1–T12 + report + guide  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_mission_mass_energy_b1.md)  
- [x] Engineer smoke ACCEPT 2026-09-17

---

## 6. Handoff

```text
Engineer → ★ B1-mission-mass-energy (this IC) after #5 CLOSED
Claude   → implement mirror + Continuity ladder + tests + report
Cursor   → review
Engineer → smoke §3 on vigilancia
```
