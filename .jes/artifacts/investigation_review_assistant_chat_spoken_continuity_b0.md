# Investigation Review — Chat spoken-continuity map (`INV-assistant-chat-spoken-continuity`, T44-inv)

**Date:** 2026-10-04  
**Reviewer:** Cursor (forensic pass — Claude paste “T44-inv complete…”)  
**Against:** [INV](investigation_contract_assistant_chat_spoken_continuity_b0.md) · [report](investigation_report_assistant_chat_spoken_continuity_b0.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · T43 tip `0.7.3`  
**Tip reviewed:** `3b20d20` on `cursor/chat-spoken-continuity-impl-8ac5` (parent INV `7cc6c19` / T43 review `bfcc964`)  
**Verdict:** **PASS WITH NOTES** → await Engineer ★ on findings → small **DC** then IC (speak path only).

**Process note:** Claude Code investigated under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.** **`CLAUDE.md` not edited** (norm still pending ★).

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| `src/` / tests / package bump | **Clear** — `git diff` vs parent INV: zero `src/` `tests/` `pyproject.toml`; version stays `0.7.3` |
| LLM summarizer proposed | **Clear** — brief shape = five existing fields |
| Second Continuity truth | **Clear** — extract from `build_project_continuity` / `readiness` already computed |
| Invented Conversation Engine | **Clear** — next Buy = extractor + speak-path only; print stays truth |
| CLAUDE.md edited without ★ | **Clear** — clause in report + map header only |
| T40 / world scope creep | **Clear** — Q11; T40 stays Parked |
| Failure mode misidentified | **Clear** — load + `estado` share `build_startup_context` → `render_startup_context` → spoken verbatim |
| Blind / stale citations | **Notes** — N1 line-number miss on Continuity return; keys themselves match |

---

## 1. INV checklist (Q1–Q12)

| Q | Verdict |
|---|---|
| Q1 Chat egress inventory | **PASS** — `run_chat` print/`_say`/`speak` surfaces match tip (`main.py:949–1032` + `_print_welcome` / `_chat_speak_fn`) |
| Q2 Continuity field map | **PASS WITH NOTES** — five Continuity keys and `build_startup_context` return (`orchestrator.py:7862–7938`) match; **N1** wrong line span for Continuity `return` |
| Q3 Speak-vs-print | **PASS** — banner/welcome print-only; `_say` print+speak; `_chat_speak_fn(False)` never imports TTS; `inspect.getsource(run_chat)` fence still empty |
| Q4 Ranking | **PASS** — brief / on-request / screen-only justified as continuity-to-continue, not aesthetics |
| Q5 Brief shape | **PASS** — `situation` · `next_useful_step` · `next_useful_why` · `readiness.overall` · `prioritized_gaps[0].title`; BOM/table excluded |
| Q6 Full-on-request | **PASS WITH NOTES** — phrase-set sibling of `CONTINUITY_DEFER_PHRASES` is the right seam; **N3** existing phrases already dump the wall |
| Q7 Non-Continuity classes | **PASS WITH NOTES** — Skill/wizard/error speak-as-printed; wall = extract; **N4** reasoning-without-footer left for DC/IC |
| Q8 Living map | **PASS** — `engineer_note_chat_spoken_continuity_map.md` is usable SoT |
| Q9 Process norm | **PASS** — paste-ready `CLAUDE.md` clause; not applied |
| Q10 Next Buy | **PASS** — small DC (two-layer + Q5 list + “completo” trigger) then narrow IC (extractor; truth `print` untouched) |
| Q11 T40 | **PASS** |
| Q12 Cola | **PASS** — T40 Parked; no new C-xxx / connect-plugs debt |

---

## 2. Spot-checks (this pass)

Re-read on tip `3b20d20`:

- `run_chat` / `_say` / `speak(startup_block)` — load wall is `main.py:1003–1005`.
- `_handle_project_status` → same `build_startup_context` (`orchestrator.py:6799–6826`).
- Continuity keys actually returned at `project_continuity.py:676–682` (`situation`, `evidence`, `next_useful_step`, `next_useful_why`, `explain_topics`) — names match Q5; **lines in report/map do not** (N1).
- `attach_project_coherence` `coherent_actions` (`orchestrator.py:1550–1559`) excludes vehicle Skills — Q7 holds.
- `EngineeringReadinessResult.overall` / `prioritized_gaps` exist (`engineering_readiness.py:96–101`); `PROJECT STATUS` line uses `overall` (`main.py:229–232`); gap title at `main.py:243`.
- `CLAUDE.md` has no spoken-continuity clause (correct for this INV).
- TTS structural fence: `[]` forbidden tokens in `run_chat` source.

Full suite claim (4009 / 9 skipped) not re-run here — no `src/`/`tests/` delta.

---

## 3. Notes

**N1 — Continuity return cited at `:389–395`; actual `return` is `:676–682`.**  
`build_project_continuity` starts at `:288` (correct). `:389–395` is situation-string construction (thrust PASS / autonomía no demostrada), not the dict return. **Field names in Q2/Q5/map are still right.** Fix citations in the living map on the DC Buy (do not block ★).

**N2 — `next_useful_why` is humanized on the wall, raw on the coherence footer.**  
Wall: `_humanize_next_useful_why(...)` (`main.py:314`). Footer: raw field (`main.py:689`). DC must lock which form the brief extractor speaks so Layer 2 does not diverge from the screen line the Engineer is looking at.

**N3 — `CONTINUITY_DEFER_PHRASES` already includes “full dump” language.**  
Same intercept already matches `estado`, `resumen`, `dame detalles`, `detalles del proyecto`, `cuentame el proyecto`, … (`config.py:51+`) — all today’s wall. DC must **split** which phrases keep `estado`-style (screen full + **speak brief**) vs which mean **speak full** (`dame detalles` / `completo`). Do not add `completo` in isolation as if `estado` were the only trigger.

**N4 — Reasoning-without-footer is an honest open call (Q7).**  
DC should lock the default (report suggestion: top `PRIORIDAD CRÍTICA` label) or defer that class to speak-on-request until a later Buy.

**N5 — A few `build_startup_context` keys are unused as independent print rows** (`proactive_question`, `energy_model_note`, `motor_catalog_gap`, raw `component_bom`). They feed Continuity/wizard/propulsion prose. Map is complete enough for the spoken layer; optional extra rows on DC if Engineer wants belt-and-braces.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Await Engineer ★ on findings
Next: small DC (two-layer + Q5 fields + phrase split for breve vs completo)
     then IC: brief extractor on speak path only; screen truth unchanged
Land CLAUDE.md norm + cola pointer after ★ (not before)
Tip stays 0.7.3 until the code Buy
```
