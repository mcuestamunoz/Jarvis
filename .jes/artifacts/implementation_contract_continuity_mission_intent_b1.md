# Implementation Contract — Continuity next-step vs mission intent (`B1-continuity-mission-intent`)

**Project:** Jarvis  
**Date:** 2026-09-16  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** CLOSED — Engineer smoke ACCEPT 2026-09-16  

**Parents:**
- Software closeout queue #1 — [engineer_note_software_closeout_queue.md](engineer_note_software_closeout_queue.md)
- Mission payload identity **CLOSED** — cameras/radio declarable ([IC](implementation_contract_mission_payload_identity_b1.md))
- Observation (parked, now unblocked) — [investigation_report_mission_functional_payload_holes_b0.md](investigation_report_mission_functional_payload_holes_b0.md) §Q5: `increase_payload` fires on `high_margin` only; never reads `objective`
- Live smoke: `dron-de-vigilancia-doméstico` → PASS + “Aumentar carga útil” despite vigilancia / cameras declared
- Continuity ranking — `project_continuity.py` ranks optimization **last** among unfinished gaps; this Buy fixes the **optimization suggestion itself**, not the whole ranker

**Type:** When thrust margin is high, **do not** lead with “Aumentar carga útil” if the project’s **mission intent** (objective/restrictions text and/or declared mission components) says otherwise; offer a **deterministic** mission-aware next step instead (or suppress only).  
**Not** Conversation Engine / LLM rewrites of Continuity.  
**Not** inventing camera mass / plate dims / firmware.  
**Not** wizard vigilancia nudge (queue #2).  
**Not** changing simulation physics.  
**Not** version bump. **Not** `workspace/` mutation unless ★ Path D (default: tests-only).

**Output:** `.jes/artifacts/implementation_report_continuity_mission_intent_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2968** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-continuity-mission-intent`** — suppress/replace `increase_payload` under mission intent |
| 2 | Where | Primary: `reasoning_layer.py` path that appends `increase_payload` on `has_simulation and high_margin` (~319). Ensure Continuity/`estado` surfaces the result (today it consumes reasoning suggestions — do not invent a parallel Continuity ranker). If a second identical fire-site exists in the same file/callers, fix both with one shared helper |
| 3 | Mission signal (closed, deterministic) | `mission_intent_active(project_state) → bool` true if **either**: **(A)** normalized `objective` and/or `restrictions` contain any keyword from a **frozen** tuple (Spanish/English), **or** **(B)** `design_properties.components` has key `cameras` and/or `radio_module` (any completeness). Report exact keyword tuple |
| 4 | Keywords (minimum set — may extend in report if tests need; do not invent open NLP) | At least: `vigilancia`, `vigilancia doméstica`, `surveillance`, `inspección`, `inspection`, `fotografía`, `photography`, `cámara`, `camara`, `camera`, `fpv`, `comunicación`, `comunicacion`, `telemetría`, `telemetria` — tune to avoid over-match on unrelated words; document exclusions |
| 5 | When mission active + high_margin | **Do not** append `increase_payload` / “Aumentar carga útil”. Instead append **one** alternative suggestion (same priority band ~0.8) with locked copy: |
| 5a | Prefer if `cameras` absent | label e.g. **“Declarar carga de misión (cámara)”** · reason cites objective/mission · `action_type` new closed string e.g. `complete_mission_payload` (add to tool schema allowlist if required) · `action` may stay `iterate` or a no-op-safe Continuity-visible only — **do not** invent a new orchestrator wizard this Buy |
| 5b | Prefer if `cameras` present but completeness `low` | label e.g. **“Completar identidad de cámara”** · hint model (RunCam / …) |
| 5c | Prefer if cameras medium+ and `radio_module` absent/low | parallel radio labels |
| 5d | Else (mission text only, both present medium+) | Soften to e.g. **“Revisar margen vs carga de misión”** — still **not** “Aumentar carga útil”; or suppress enrichment entirely and let Continuity fall through to validated/continue. Pick one in implementation; document in report |
| 6 | When mission **not** active | Byte-identical `increase_payload` behavior to today |
| 7 | Helper | Single pure helper (name OK) used by reasoning enrichment — unit-testable without CLI |
| 8 | Continuity / CLI | `estado` / startup continuity for vigilancia-like fixture must **not** show “Aumentar carga útil” as next step when mission signal true and design otherwise closed (sim PASS, BOM complete enough for today’s ranking). Update/extend existing continuity tests that assumed margin→payload |
| 9 | Forbidden | LLM/Conversation Engine · parsing free-form beyond frozen keywords · changing HIGH_MARGIN_THRESHOLD · flipping ASSEMBLY_READY · inventing catalog · auto-declaring camera · version bump |
| 10 | Live | Default **tests-only**. Optional ★ Path D: none required; Engineer smoke on vigilancia project |

**Product sentence:**

```text
Si el proyecto es de vigilancia (o ya lleva cámara/radio),
Jarvis no te empuja a “cargar más kilos” solo porque sobra empuje;
te señala completar la carga de misión.
```

### 0.1 Enough / not enough

| Enough this Buy | Not this Buy |
|---|---|
| Keyword + component-key gate; alternate Continuity label | Full mission planner / NLP |
| Tests on synthetic objective + live-shaped fixtures | Workspace mutate |
| | Wizard nudge at create (#2) |

---

## 1. You (Claude)

1. Add `mission_intent_active` (or equivalent) + keyword constant.  
2. Gate `increase_payload` enrichment; add alternate suggestion(s) per lock #5.  
3. Wire schema/`action_type` if needed.  
4. Tests T1–T8. Report keyword tuple + exact labels.  
5. No version bump. No workspace write unless ★.

**STOP if** forced to call LLM for next-step or to invent camera physics.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Objective containing `vigilancia` + high_margin → **no** `increase_payload` in enriched suggestions |
| T2 | Neutral objective (`prueba` / empty mission keywords) + high_margin → `increase_payload` still present (regression) |
| T3 | No keyword but `components["cameras"]` present → mission active → no `increase_payload` |
| T4 | Alternate label/reason appears when cameras absent (5a) |
| T5 | Cameras low → “completar identidad” path (5b) |
| T6 | `mission_intent_active` unit cases: keyword hit / miss / over-match guard if any |
| T7 | Continuity/`estado`-level assertion: vigilancia-shaped closed design does not surface “Aumentar carga útil” as `next_useful_step` |
| T8 | Full pytest green; `0.4.1` |

---

## 3. Smoke (Engineer)

1. Open `dron-de-vigilancia-doméstico` (or equivalent) with sim PASS + high margin.  
2. `estado` → **Siguiente paso** is **not** “Aumentar carga útil”.  
3. Neutral throwaway with PASS + high margin (no mission keywords, no cameras) → still may show aumentar carga (confirm regression).  
4. Optional: declare `cámara RunCam` on neutral project → next-step stops pushing payload increase.

---

## 4. Out of scope (named debt)

| Item | Queue |
|---|---|
| Wizard vigilancia nudge at SYSTEM_DEFINITION | #2 |
| propellers↔motors | #3 |
| bind-esc / FC change hygiene | #4 |
| payload_bay/arm identity | #5 |
| plate-box / HD-* | Parked physical |

---

## 5. Done when

- [x] ★  
- [x] Helper + gate + alternate suggestion + T1–T8 + report  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_continuity_mission_intent_b1.md)  
- [x] Engineer smoke ACCEPT (`estado` + post-`simular` Continuity = “Revisar margen vs carga de misión”; N1 only on SuggestionEngine bullet)

---

## 6. Handoff

```text
Engineer → ★ B1-continuity-mission-intent
Claude   → implement + tests + report
Cursor   → review
Engineer → smoke §3 (vigilancia estado)
```
