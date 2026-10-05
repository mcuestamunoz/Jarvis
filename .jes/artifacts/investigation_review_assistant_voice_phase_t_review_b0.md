# Investigation Review — Voice phase T review (`INV-assistant-voice-phase-t-review`, T48-inv)

**Date:** 2026-10-05  
**Reviewer:** Cursor (forensic pass — Engineer handoff: tip on `cursor/chat-voice-ptt-impl-8ac5`)  
**Against:** [INV](investigation_contract_assistant_voice_phase_t_review_b0.md) · [report](investigation_report_assistant_voice_phase_t_review_b0.md) · [cola](engineer_note_voice_phase_c_cola.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · tip parent T47 `44cb5fe` / report commit `6d419e0`  
**Tip reviewed:** `6d419e0` (T48-inv) on `cursor/chat-voice-ptt-impl-8ac5` — sibling T49 `8419582` already on tip; this review grades the INV against the INV tip (`0.7.5` docs-only).  
**Verdict:** **PASS WITH NOTES** → await Engineer ★ on findings.

**Process note:** Claude Code investigated under Engineer paste (= Buy). This is the independent Cursor review of record. Same-session self-PASS is not review of record. **No ACCEPT claimed here.** **No `src/` in this Buy** (confirmed).

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| `src/` / tests / package bump on T48 commit | **Clear** — `git diff 44cb5fe..6d419e0` is INV + cola + PRIORIDAD + state only; `pyproject` stayed `0.7.5` for the INV |
| ACCEPT claimed | **Clear** — Q4/Q12 and report header refuse ACCEPT |
| Wake-word / T40 reopen | **Clear** — Q10; no `world/` under `src/jarvis/` |
| Blind restatement of prior reports | **Clear** — Q1/Q3/Q6 cite tip symbols; live checks re-run this pass |
| DC lock drift missed | **Clear** — spot-checks below match “zero drift” on the locks re-verified here |
| Report accuracy (count / artifact wording) | **Notes** — N1, N2 |

---

## 1. INV checklist (Q1–Q12)

| Q | Verdict |
|---|---|
| Q1 Cola truth table | **PASS WITH NOTES** — ACCEPT yes/no per row matches tags (`v0.6.43`–`v0.6.46`, `v0.7.0` exist; `v0.7.1`–`v0.7.5` do not). **N1:** T47 review verdict was misquoted as “ACCEPT CLOSED”; live file says await ACCEPT. **N2:** “nine Buys” overstates the ACCEPT backlog (see Q4). |
| Q2 Operator paths | **PASS** — five paths match tip wiring (`run_chat` / `run_voice_*` / argparse); only PTT opens a live mic |
| Q3 DC lock audit | **PASS** — spot-checked T34 AuthoritySource, T44 extractor purity, T46 trigger/once/print-only cue / `os.close` after mkstemp — hold |
| Q4 ACCEPT backlog + order | **PASS WITH NOTES** — recommended T41→T42→T43→T45→T47 (+ T44-inv findings) is sound; **N2** count |
| Q5 Open notes harvest | **PASS** — T47 N1 remediated on tip (`main.py:1025-1026`); T45 N5 English leak correctly flagged (fixed later by T49) |
| Q6 Honesty fences | **PASS** — this pass: `AuthoritySource` literal; `inspect.getsource(run_chat)` → `[]`; `record_turn.sh --check` with stripped PATH exits 1 |
| Q7 Living map | **PASS WITH NOTES** — content-complete; **N3** line-citation drift (pre-T47 and post-N1 PTT rows) |
| Q8 TTS language → T49 | **PASS** — correctly framed as docs-default mismatch; seam model-agnostic (T49 landed separately) |
| Q9 Gaps vs “voz de principio a fin” | **PASS** — Spanish default / multilingual STT example / live-ear / reasoning-without-footer / T40 |
| Q10 Next Buy | **PASS** — ACCEPT backlog before new voice code; T40 Parked |
| Q11 Connect-plugs | **PASS** — no invented CLOSED; `a4-voice-world` still honest |
| Q12 Cola / PRIORIDAD / state | **PASS** — T48-inv Implemented await Cursor review was wired before T49 overwrote tip state |

---

## 2. Spot-checks (this pass)

On tip after T49 (`8419582`) for live symbols that T48 claimed for `0.7.5` (behavior unchanged by T49 docs):

- `AuthoritySource = Literal["radio", "api", "operator"]` (`safety.py:96`).
- PTT: `is_ptt_trigger` + `os.close(fd)` after `mkstemp` (`main.py:1020-1026`); cue is bare `print` (`:1022`).
- `hablar`/`habla` ∉ `CONTINUITY_DEFER_PHRASES`.
- No `world/` package under `src/jarvis/`.
- T47 review line 7 (live): `PASS WITH NOTES → await Engineer ★ ACCEPT → tag v0.7.5` — **not** “ACCEPT CLOSED” (N1).
- Q4 backlog enumeration in the report body lists **six** items (T41, T42, T43, T44-inv, T45, T47), not nine (N2).
- Map PTT rows now sit ~1–5 lines off tip after N1 remediation (`Grabando` map `:1021` → tip `:1022`; `[voz]` map `:1038` → tip `:1043`) (N3).

Targeted tests this pass (not full suite):  
`pytest tests/test_assistant_voice_tts_spanish_b1.py tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py tests/test_assistant_chat_voice_ptt_b1.py -q` → **33 passed**.

---

## 3. Notes

**N1 — Q1 misquotes T47’s review verdict.**  
Report claims the T47 review says `PASS WITH NOTES → Engineer ★ ACCEPT CLOSED … @ tip v0.7.5`. Live artifact says `await Engineer ★ ACCEPT → tag v0.7.5`. The **tag/ACCEPT tracking conclusion still holds** (no `v0.7.5` tag; cola/PRIORIDAD correctly await ACCEPT). Fix the Q1 cell wording if the report is ever re-edited; do not treat T47 as ACCEPTed.

**N2 — “Nine Buys” ACCEPT backlog is overstated.**  
Q4’s own numbered list is six items (five code Buys + T44-inv findings). PRIORIDAD/`engineering_state` inherited the “nine” figure. Substance of the backlog and recommended order is fine; correct the count in SoT prose when convenient.

**N3 — Living-map line citations drifted further after T47 N1.**  
T48 correctly flagged pre-T47 ~30–40 line drift. After `os.close(fd)` remediation, even the five T47 PTT rows are off by a few lines. Cosmetic; refresh on the next Buy that already touches `main.py` + the map.

---

## 4. Awaiting

```text
Cursor verdict: PASS WITH NOTES
Await Engineer ★ on findings
Key takeaways for Engineer:
  - T41–T47 (plus T44-inv) still await ★ ACCEPT; tags v0.7.1–v0.7.5 absent
  - 33 DC locks re-checked by Claude; Cursor spot-check found no lock break
  - Next process step: ACCEPT stack (or live listen after T49 Spanish default)
  - T40 stays Parked
```
