# Implementation Contract — Wizard vigilancia / mission nudge at SYSTEM_DEFINITION (`B1-wizard-mission-nudge`)

**Project:** Jarvis  
**Date:** 2026-09-16  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** CLOSED — Engineer smoke ACCEPT 2026-09-16  

**Parents:**
- Software closeout queue **#2** — [engineer_note_software_closeout_queue.md](engineer_note_software_closeout_queue.md)
- Investigation ranked “B1 wizard nudge” — [investigation_report_mission_functional_payload_holes_b0.md](investigation_report_mission_functional_payload_holes_b0.md) §D
- Prerequisites **CLOSED**: block-gate · mission-payload identity · Continuity mission-intent (smoke ACCEPT 2026-09-16)
- Live seam: every `create_project` opens `SystemDefinitionSession` step 0 with A/B/C; novices often pick **A** and never see that **B** can add `cámara` / `radio` now that those keys resolve

**Type:** Suggest-only one-line nudge on the SYSTEM_DEFINITION A/B/C prompt when the new project’s **objective/restrictions** already signal mission intent (vigilancia / cámara / …), pointing the user at **B** to declare camera/radio — **without** auto-adding blocks or gating A/C.  
**Not** Conversation Engine / LLM.  
**Not** new session mode / schema field.  
**Not** Continuity rewrite (done in #1).  
**Not** SuggestionEngine N1 (`increase_payload` on `simular` — stays queue #4).  
**Not** inventing catalog / mass / mm.  
**Not** version bump. **Not** `workspace/` mutation (tests-only).

**Output:** `.jes/artifacts/implementation_report_wizard_mission_nudge_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2985** · UI ≥**105** (or current green at ★ time)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-wizard-mission-nudge`** — suggest-only mission line on SYSTEM_DEFINITION step 0 |
| 2 | Where | `SystemDefinitionSession.start` (or the single helper that builds the step-0 A/B/C `message`). Do **not** invent a parallel create-confirm wizard. Idle re-entry via `definir sistema` may reuse the same helper if objective still matches — OK; report whether it does |
| 3 | When to nudge | Append the line **iff** mission text signal is active on **objective and/or restrictions** (project just created / current state). Prefer **reusing** `mission_intent_active` / `_MISSION_INTENT_KEYWORDS` from `reasoning_layer.py` (import the frozen keywords or a thin text-only helper) so Continuity and wizard do not drift. If `mission_intent_active` is true only because `cameras`/`radio_module` already exist, **skip** the nudge (already declared — no “escribe B” spam) |
| 4 | Copy (locked intent; exact Spanish in report) | One short line, e.g. *Si tu misión necesita cámara o radio/enlace, elige **B** para añadirlos ahora (luego `cámara` / `radio`).* Must stay **suggest-only** — never “debes”, never refuse **A**/**C** |
| 5 | Behavior unchanged otherwise | **A** / **B** / **C** semantics, block gate, and camera/radio identity rules unchanged. Nudge does **not** preselect B, does **not** stub components, does **not** change `recommended_start` |
| 6 | Neutral objective | Objective without mission keywords → byte-identical step-0 message to today (no extra line) |
| 7 | Forbidden | LLM · auto-declare camera/radio · new orchestrator mode · changing block gate / ComponentRules · Continuity / SuggestionEngine edits · version bump · workspace mutate |
| 8 | Live | Default **tests-only**. Engineer smoke = greenfield create with “vigilancia” in objective |

**Product sentence:**

```text
Si acabas de decir que el dron es de vigilancia,
Jarvis te recuerda en el A/B/C que puedes añadir cámara/radio con B —
sin obligarte ni inventar el hardware.
```

### 0.1 Enough / not enough

| Enough this Buy | Not this Buy |
|---|---|
| One conditional line on step-0 prompt | Mission planner / multi-step wizard |
| Shared keyword authority with Continuity #1 | SuggestionEngine N1 fix (#4) |
| Tests on synthetic objectives | Catalog / mass |

---

## 1. You (Claude)

1. Wire conditional append on SYSTEM_DEFINITION step-0 message (locks #2–#5).  
2. Reuse Continuity keyword authority (lock #3); document import path.  
3. Tests T1–T6 + report with exact nudge string.  
4. No version bump. No workspace write.

**STOP if** forced to auto-add blocks or call LLM for the nudge text.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | `start` with objective containing `vigilancia` (no cameras/radio yet) → step-0 message **includes** the nudge line |
| T2 | Objective neutral (e.g. “dron de prueba”) → message **excludes** nudge; matches pre-Buy shape aside from unrelated churn |
| T3 | Objective mission-like **but** `cameras` already present → **no** nudge |
| T4 | Restrictions alone contain a mission keyword (objective empty/neutral) → nudge present |
| T5 | Choosing **A** after nudge still applies base architecture only (no auto camera/radio) |
| T6 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

1. `n` → create throwaway drone · objective includes **vigilancia** (or similar).  
2. SYSTEM_DEFINITION A/B/C message shows the one-line nudge pointing at **B**.  
3. **A** still works as today (no forced camera).  
4. Optional: **B** → `cámara` / `radio` still accepted (identity rules live).  
5. Neutral-objective create → no nudge line.

---

## 4. Out of scope (named debt)

| Item | Note |
|---|---|
| SuggestionEngine `increase_payload` on `simular` (N1) | Queue **#4** |
| propellers↔motors evidence | #3 |
| More identity rules | #5 |
| `library/cameras` physics bags | Parked |
| plate-box / HD-* | Parked physical |

---

## 5. Done when

- [x] ★  
- [x] Nudge + keyword reuse + T1–T6 + report  
- [x] Cursor review PASS WITH NOTES — [review](implementation_review_wizard_mission_nudge_b1.md)  
- [x] Engineer smoke ACCEPT (A/B/C + nudge line; B→cámara → cameras stub)

---

## 6. Handoff

```text
Engineer → ★ B1-wizard-mission-nudge (this IC)
Claude   → implement nudge + tests + report
Cursor   → review
Engineer → smoke §3
```
