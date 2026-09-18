# Implementation Contract — Mission Continuity: mount + endurance (`B1-mission-continuity-mount-endurance`)

**Project:** Jarvis  
**Date:** 2026-09-17  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** **CLOSED** 2026-09-18 — Cursor PASS WITH NOTES · Engineer smoke ACCEPT WITH NOTES (vigilancia live)

**Parents:**
- Fase M cola — M2 after **H1 CLOSED** + **P1 mass-energy CLOSED**
- Mass Buy documented gaps **#9c / #9d** — [IC](implementation_contract_mission_mass_energy_b1.md) · [report](implementation_report_mission_mass_energy_b1.md) §4
- Live: `dron-de-vigilancia-doméstico` — masses declared → Continuity parks on **“Revisar margen vs carga de misión”** while camera/radio often **unmounted** and **no** autonomía objetivo in restrictions
- Mount today — `mounted_on_declare_assist` subjects **exclude** `cameras` / `radio_module`; `mount_standard_assist._STACK_SUBJECTS` locked to esc/FC/battery/sensors (“never widen without a new ★”) — **this IC is that ★**
- Endurance today — `restrictions` → `state_schema._parse_constraints` → `parsed_constraints["autonomy_min"]` → Continuity/`autonomy_target_min` already exist; ReasoningLayer context lacked that field (mass Buy skipped rather than duplicate regex)

**Type:** After mission identity + mass are done, Continuity’s mission-aware high-margin waterfall must ask for **mount** (cámara/radio → airframe) and **autonomía objetivo (min)** before the soft margin line — using **existing** mount writers / restrictions parsers, not a second mount system and not a duplicated autonomy regex.  
**Not** inventing poses/mm · not plate-box · not `power_w`→energy (M3) · not VTX (M4) · not firmware.  
**Not** Conversation Engine / LLM.  
**Not** version bump. **Not** `workspace/` mutation (tests-only; Engineer smoke on vigilancia may save mounts/restrictions).

**Output:** `.jes/artifacts/implementation_report_mission_continuity_mount_endurance_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**3068** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-mission-continuity-mount-endurance`** — Continuity ladder steps for mount + endurance after mission mass |
| 2 | Ladder order | Extend `_mission_aware_high_margin_suggestion` **after** existing identity+mass steps, **before** soft margin. Final order (first hole wins): identity camera → identity radio → camera mass → radio mass → **mount holes** → **autonomy target missing** → soft “Revisar margen…” (never `increase_payload` under mission intent) |
| 3 | Mount subjects (★ widen) | Add **`cameras`** and **`radio_module`** as mount subjects in **`mounted_on_declare_assist`** (same pattern table / noun discipline as FC/battery). Example phrases must parse: e.g. `cámara montada en la placa` / `radio montado en el frame` (exact grammar in report; ES+EN nouns OK) |
| 4 | Mount checklist | Widen `mount_standard_assist._STACK_SUBJECTS` with the same two keys + Spanish nouns (`cámara`/`radio`) so `montajes estándar` / `qué falta montar` lists them when present and unmounted. **Do not** invent a parallel checklist module |
| 5 | Mount Continuity CTAs | When mission intent active + high margin + masses done (or mass N/A if component absent): if `cameras` present and `mounted_on` missing → label e.g. **“Monta la cámara en la placa/frame”** · `action_type` e.g. `declare_mission_mount` · reason cites exact Continuity-ready phrase from mount assist when possible. Same for `radio_module`. Prefer **one** suggestion (first hole: camera before radio). Optional: if both mounted and FC present unmounted, fall through to existing stack subjects via soft margin or leave FC to `montajes estándar` — **do not** require FC mount for ACCEPT if cameras/radio covered |
| 6 | Ambiguous plates | Keep mount assist rule: 2+ `frame_plate*` → ambiguous, never guess. Continuity may say “elige placa (montajes estándar)” rather than invent a target |
| 7 | Autonomy target read | **Do not** re-implement `_AUTONOMY_CONSTRAINT_RE`. Pass `parsed_constraints` (or at least `autonomy_min`) into ReasoningLayer `context` from the existing builder, **or** call a **public** helper exported from `state_schema` / shared module that wraps the same `_parse_constraints` authority. Report which path |
| 8 | Autonomy Continuity CTA | If mission intent + no `autonomy_min` in parsed constraints → **“Declara autonomía objetivo (min)”** · `action_type` e.g. `declare_autonomy_target` · reason points to existing restrictions grammar (e.g. `restricciones: 8 min` / whatever `extract_restrictions_update` already accepts — **document exact smoke phrase**). Must not invent minutes |
| 9 | After target exists | No new CTA required this Buy if target present — existing Continuity/ERF autonomy-below / undemonstrated paths stay. Soft margin OK when mounts done + target present. Honesty: ~0.7 min computed vs e.g. 8 min target may WARN/FAIL — **do not** claim validated flight or invent better OP |
| 10 | Neutral projects | No mission intent → byte-identical `increase_payload` / Continuity behavior to today |
| 11 | Guide | Short USER_GUIDE note: mount cámara/radio phrases + how to set autonomía in restrictions; link to mass section |
| 12 | Forbidden | Second mount system · duplicate autonomy regex · invent pose/mm · `power_w` energy · VTX · plate-box · firmware · Conversation Engine · version bump · LLM |
| 13 | Live | Default **tests-only** |

**Product sentence:**

```text
Con la misión ya identificada y pesada, Jarvis te pide montar cámara/radio
y fijar minutos de autonomía objetivo — con las herramientas que ya existen —
antes de aparcar en “revisar margen”.
```

### 0.1 Enough / not enough

| Enough this Buy | Not this Buy |
|---|---|
| Continuity asks mount then endurance after masses | Auto-mount / invent plate |
| `cámara`/`radio` parseable as mount subjects + checklist rows | FC mount mandatory |
| Autonomy CTA via existing restrictions → `parsed_constraints` | Better OP / invent endurance |
| Tests + guide | M3 `power_w` · M4 VTX · P2 payload |

---

## 1. You (Claude)

1. Widen mount subject tables (declare assist + standard checklist) for cameras/radio.  
2. Plumb autonomy into ReasoningLayer context without regex duplication.  
3. Extend mission Continuity waterfall: mount → endurance → soft margin.  
4. Tests T1–T10 + guide + report (exact phrases, labels, context plumbing choice).  
5. No version bump. No workspace write unless Engineer smoke saves.

**STOP if** forced to invent a second mount system, duplicate autonomy parsing, or invent flight minutes.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Parse: `cámara montada en …` (locked phrase) → SET `cameras.mounted_on` when target resolvable |
| T2 | Parse: radio mount phrase → SET `radio_module.mounted_on` |
| T3 | `montajes estándar` with unmounted cameras present → checklist includes cámara row |
| T4 | Continuity: masses set, camera unmounted → top mission suggestion is mount-camera (not soft margin) |
| T5 | Continuity: mounts done, no autonomy_min → declare-autonomy-target |
| T6 | Continuity: mounts done + autonomy_min present → soft margin OK; still **no** `increase_payload` |
| T7 | Neutral high-margin project → `increase_payload` still available |
| T8 | ReasoningLayer does **not** introduce a second autonomy regex (assert shared helper / context field) |
| T9 | Ambiguous multi-plate: Continuity/mount does not invent a plate key |
| T10 | Full pytest green; `0.4.1` |

---

## 3. Smoke (Engineer)

On **`dron-de-vigilancia-doméstico`** (masses already declared):

1. `estado` → expect mount CTA (not only soft margin).  
2. Mount e.g. `cámara montada en la placa` / `radio montado en el frame` (adjust to live plate/frame keys).  
3. `estado` → **Declara autonomía objetivo (min)**.  
4. Set restrictions with a parseable `N min` via existing grammar.  
5. `estado` / `simular` → soft margin or autonomy-below honesty vs ~0.7 min — **not** fake validated endurance.  
6. Optional: `montajes estándar` lists misión subjects.

**ACCEPT when:** Continuity leaves soft-margin parking via mount then endurance CTAs; existing writers/parsers do the work.

---

## 4. Out of scope

| Item | Note |
|---|---|
| M3 `power_w` → energy | Next cola |
| M4 VTX | Opt |
| Pose Δmm / plate L×W | Physical |
| Firmware / Fase C | After M7 |
| Auto-bind mounts on identity declare | Not this Buy |

---

## 5. Done when

- [x] Mount widen + Continuity ladder + autonomy plumb + T1–T10 + report + guide  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_mission_continuity_mount_endurance_b1.md)  
- [x] Engineer smoke ACCEPT WITH NOTES (vigilancia 2026-09-18) — ambiguous CTA + mount + autonomy_min + honest below-target; radio left unmounted (CTA advanced correctly)

---

## 6. Handoff

```text
Engineer → ★ B1-mission-continuity-mount-endurance (this IC)
Claude   → implement
Cursor   → review
Engineer → smoke §3 on vigilancia
```
