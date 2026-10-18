# Implementation Contract — Unknown → brief situate (`B1-llm-unknown-situate-brief`)

**Project:** Jarvis  
**Date:** 2026-10-18  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.8.7`** (CI-1…CI-1d + this Buy)

**Status:** **IC READY** — Engineer REJECT of CI-1d egress shape: full Continuity wall on `hablar` is useless for voice/agile UX.  
**Parents:** [CI-1d IC](implementation_contract_llm_unknown_situate_b1.md) · [CI-1d review](implementation_review_llm_unknown_situate_b1.md) · Engineer smoke paste (full wall on `hablar`) · [CI-0 DC](design_contract_continuity_interpreter_epoch_b0.md) · tip **`v0.8.6`** · package **`0.8.7`**  
**Type:** Correct CI-1d **egress** — keep the early claim (0 LLM, no wizard, no analyze dump); replace `_handle_project_status` with a **short situate** message.  
**Opens:** cola **CI-1e**. Package stays **`0.8.7`**. Tag **`v0.8.7`** only after Engineer ★ including this Buy.

**Not:** CI-2 LLM compose · changing Continuity ranking · retiring `interpret` · G-03 · widening `is_explain_ask` · T40 · Conversation Engine · reverting the CI-1d claim (unknown still must not call interpret/analyze).

---

## Why this Buy

CI-1d correctly stopped analyze/wizard on nonsense, but routed to `_handle_project_status()` → **full** `render_startup_context` wall (components, readiness table, TOP GAPS, ontology…). Engineer:

> mal — estás mandando todo el estado. Piensa en voz: no es útil ni ágil.

Intent: **reorient briefly** — not dump Continuity Layer 1 wall. Same fields Continuity already computed; **tiny extract** printed and spoken.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-llm-unknown-situate-brief`** (CI-1e). Package remains **`0.8.7`**. Tag **`v0.8.7`** only after Engineer ★ (CI-1b/1c/1d criteria + this brief egress) |
| 2 | **Keep CI-1d claim:** `unknown` + active project + not `is_explain_ask` → **0** `interpret` / `analyze`. Same for CI-1c backstop when it would have situated |
| 3 | **Replace destination:** those turns must **not** call `_handle_project_status()` / must **not** return `action == "project_status"`. Return a dedicated brief situate result (lock 4–5) |
| 4 | **New action** `situate` (name locked): `{"status": "ok", "action": "situate", "message": <brief>}` — optional `project_id` / `workspace_path` OK if already habitual; **no** `startup_context` required for print (may attach ctx only if tests need it; print must not use full wall) |
| 5 | **Brief body (0 LLM, deterministic)** from `build_startup_context()` Continuity/readiness fields only, Spanish, **≤ ~6 short lines**, shape: |
| | (a) fixed lead: `No capté una orden clara.` |
| | (b) project display name / objective **one line** if available (short — not the full header block) |
| | (c) `continuity.situation` if present |
| | (d) `continuity.next_useful_step` if present (+ humanized `next_useful_why` if already available without new subsystem) |
| | (e) optional one readiness line: listo / no listo para ensamblar from `readiness.overall` |
| | **Forbidden in this message:** evidence bullet list, architecture/components tree, ENGINEERING READINESS table, TOP GAPS block, ontology “Conceptos”, propulsion/OP detail, BOM |
| 6 | **`render_response`:** `action == "situate"` prints **only** `message` (like `analyze` — **no** `Acción ejecutada: situate` prefix). Voice-only: speak-as-printed (existing non-`project_status` path) — brief is what TTS hears |
| 7 | Explicit typed `estado` / Continuity-defer phrases **unchanged** — still full `project_status` wall |
| 8 | Explain-shaped unknown + `explicame el margen` + deterministic create + no-project create + FN-022 **unchanged** from CI-1b/1c/1d |
| 9 | Update spoken-continuity map: new row for `situate` (must-speak-brief / speak-as-printed); fix CI-1d note on `project_status` row (unknown nonsense is **not** a `project_status` trigger anymore) |
| 10 | Tests T1–T6; update CI-1d tests that expect `project_status` for `hablar`; cola/PRIORIDAD/state; **no** package bump |

**Smoke ACCEPT (Engineer)** — project loaded:

```text
User > hablar
→ short situate (lead + situation/next step…), NOT full wall
→ NO components / readiness table / TOP GAPS / ontology block
→ NO analyze dump · NO create wizard · no new llm_logs row
User > gracias
→ same brief situate
User > estado
→ still FULL Continuity wall (unchanged)
User > explicame el margen
→ analyze path (CI-1b criteria)
```

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | CI-1d early claim + CI-1c backstop → `_handle_situate()` (or equivalent); helper builds brief from `build_startup_context` |
| `src/jarvis/adapters/cli/main.py` | `render_response` branch for `action == "situate"` (message only) |
| `tests/test_llm_unknown_situate_brief_b1.py` | **new** T1–T6 |
| `tests/test_llm_unknown_situate_b1.py` · `tests/test_llm_interpret_unknown_guard_b1.py` | Expect `situate` / brief message, not `project_status` wall |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | New `situate` row; retract CI-1d trigger from `project_status` row |
| CI cola · PRIORIDAD · `engineering_state.json` | CI-1e Implemented awaiting review |
| `pyproject.toml` | **no version change** |

Prefer a small private helper on the orchestrator (or next to Continuity) over importing `brief_spoken_continuity` from the voice adapter into core (layering). Reusing the **same field set** as the brief spoken extract is encouraged; do not invent new Continuity fields.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `hablar` / `gracias` / `hola` + `_RefuseLLM` → `action == "situate"`, message contains lead `No capté una orden clara.`, contains situation or next-step text from a closed project, **does not** contain `ENGINEERING READINESS` / `TOP GAPS` / `Conceptos (ontology)` / `Componentes / gaps` |
| T2 | 0 interpret/analyze calls on those phrases; no create-wizard copy |
| T3 | `render_response(situate_result)` equals (or is) the brief message — no `Acción ejecutada` |
| T4 | `estado` still → `project_status` + full wall markers (e.g. `ENGINEERING READINESS` or `Situación:`) |
| T5 | `explicame el margen` still analyze; `nuevo` still create wizard; `poco margen` still FN-022 |
| T6 | Explain-shaped unknown `qué es el margen` still can reach analyze (CI-1d lock 3) |

No live Ollama. No tip pins.

---

## 3. Acceptance

- [ ] Engineer smoke §0  
- [ ] `estado` still full wall  
- [ ] Cursor review · Engineer ★ · tag **`v0.8.7`**

---

## 4. Paste for Claude

```text
Implementation — B1-llm-unknown-situate-brief (CI-1e)
Parent: Engineer REJECT of CI-1d full wall on "hablar" (voice/agile).
Package stays 0.8.7. Tag v0.8.7 only after Engineer ★.

IC: .jes/artifacts/implementation_contract_llm_unknown_situate_brief_b1.md
Parents: CI-1d IC/review · CI-0 DC

GOAL: Keep CI-1d early claim (unknown + project + not explain → 0 LLM).
Replace _handle_project_status with action "situate" + short message:
lead "No capté una orden clara." + situation/next step (+ optional
readiness one-liner). Never print full Continuity wall on that path.
render_response: message only (like analyze). estado stays full wall.
Update spoken-continuity map. Fix CI-1d tests.

DO:
- orchestrator: _handle_situate (+ wire early claim + CI-1c backstop)
- main.py render_response situate branch
- tests/test_llm_unknown_situate_brief_b1.py T1–T6
- update CI-1d / CI-1c test expectations
- spoken map + cola / PRIORIDAD / state
- Implementation report. No ACCEPT. No pyproject bump.

NO: CI-2 LLM compose · Continuity ranking change · delete interpret ·
G-03 · ActionPolicy · T40
```

---

## 5. Cursor note

Claude may implement the full IC without per-edit approval. Stop if the Buy requires Continuity ranking changes or LLM compose.
