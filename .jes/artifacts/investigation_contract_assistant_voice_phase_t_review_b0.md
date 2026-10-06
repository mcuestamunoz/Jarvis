# Investigation Contract — Voice phase T review (`INV-assistant-voice-phase-t-review`)

**Project:** Jarvis
**Date:** 2026-10-05
**Author:** Engineer (direct paste to Claude = Buy, no separate Cursor-authored doc)
**Investigator:** **Claude Code**
**Reviewer:** Cursor on request · Engineer ★ on findings

**Status:** **★ CLOSED** (Engineer 2026-10-05) — Cursor **PASS WITH NOTES** · findings accepted with stack.
**Type:** **Investigation** — full forensic review of the voice phase T cola (T34–T47): cola truth vs artifacts, operator-path audit, DC lock audit, ACCEPT backlog, honesty-fence re-check, TTS-language coordination with T49. **Not** an Implementation Contract. **Not** permission to change `src/`. **No ACCEPT claim.**
**Cola:** **T48-inv**
**Tip parent:** T47 @ **`0.7.5`** (`44cb5fe` — Cursor PASS WITH NOTES + N1 remediation). Tip package **stays `0.7.5`** for this INV (docs/report only).

**Parents:**
- [T34-DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [T34-inv ★](investigation_review_assistant_voice_e2e_b0.md)
- [T44-inv](investigation_report_assistant_chat_spoken_continuity_b0.md) / [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md) / [T45 review](implementation_review_assistant_chat_spoken_continuity_b1.md)
- [T46-DC](design_contract_assistant_chat_voice_ptt_b0.md) / [T47 review](implementation_review_assistant_chat_voice_ptt_b1.md)
- [cola note](engineer_note_voice_phase_c_cola.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · [guide](../../docs/USER_GUIDE_VOICE.md) · [TTS product brief](engineer_note_voice_tts_product_brief.md)

**Why investigate now:** fourteen Buys (T34–T47) have landed across four product phases (V0 intent ingress through V5 checkpoint, V7 spoken-continuity, V8 push-to-talk) with zero Engineer ★ ACCEPT since `v0.7.0`. Before opening T49 (Spanish TTS default) or any further voice Buy, the cola's own "Estado" column needs an independent forensic check against what the artifacts and the tip code actually say — not a restatement of what each Buy's own report already claims.

---

## 0. Scope lock

**In scope:** every artifact and `src/`/`docs/` symbol touched by T34–T47 (read-only). The four/five operator entry points. The three DC lock sets (T34, T44, T46) vs tip code. The open review-notes backlog. The spoken-continuity map's currency. The TTS-language mismatch T49 will address. Connect-plugs wording.

**Out of scope forever (this INV):** any `src/` edit, any ACCEPT claim, wake-word/always-on mic, T40 (craft/`world/` voice — stays Parked unless this INV finds live evidence otherwise), re-opening any ★-closed Buy (T35–T39), re-litigating T41–T47's own design locks.

---

## 1. Questions this investigation must answer

| # | Question |
|---|---|
| **Q1 — Cola truth table** | For every row T34–T47 in `engineer_note_voice_phase_c_cola.md`: does the cola's "Estado" column match (a) the Buy's own report/review artifact, (b) the tip code, (c) whether Engineer ACCEPT was actually granted? Flag any drift. State ACCEPT yes/no per row explicitly. |
| **Q2 — Four (+ one) operator paths** | Re-verify, against tip `main.py`/`adapters/voice/` directly: `--chat` (text only), `--chat --voice-speak` (full chat + speak, brief-on-walls), `--chat --voice-speak` + `hablar`/`habla` (PTT), `--voice` (Skills-only REPL, always speaks), and the batch/fixture path (`--voice-fixture`, `--voice-audio`). For each: brain (`TERMINAL`/`VOICE`), speaks always/never/conditionally, mic on when. |
| **Q3 — DC lock audit** | Walk every numbered lock in `design_contract_assistant_chat_voice_channels_b0.md` (T34), `design_contract_assistant_chat_spoken_continuity_b0.md` (T44), `design_contract_assistant_chat_voice_ptt_b0.md` (T46) against tip code/tests. Flag any lock that has drifted or was never actually wired. |
| **Q4 — ACCEPT backlog + order** | List every Buy still awaiting Engineer ★ ACCEPT (expect T41–T47, nine Buys since `v0.7.0`). Recommend an order (dependency-aware), without claiming ACCEPT. |
| **Q5 — Open review-notes harvest** | Read the Notes section of every implementation/investigation review T41–T47 (and T35–T39 if any residual). List every N-numbered note, mark remediated vs still open, confirm T47 N1 (mkstemp fd leak) is in fact fixed on tip. |
| **Q6 — Honesty fences** | Re-verify, by reading the type/source, not by trusting prior prose: `AuthoritySource` literal (no `"voice"`), T42's `run_chat`-source TTS-seam structural guard, the Record/STT/TTS honest-failure paths (no silent success), the ESC fence and tip-pin suites still green including every new voice file. |
| **Q7 — Spoken-continuity map currency** | Is `engineer_note_chat_spoken_continuity_map.md` Table 1/Table 2 fully current for tip `0.7.5` (including T47's five PTT rows)? Any surface added since without a row? |
| **Q8 — TTS language mismatch (coordinate with T49)** | Confirm, by reading `engineer_note_voice_tts_product_brief.md` + `USER_GUIDE_VOICE.md` §2/§3/§8 + `scripts/voice/piper_tts.sh`, that the shipped default demo voice is still `en_GB-alan-medium` while every Skill/Continuity/chat reply is Spanish prose — document this precisely as T49's starting point, do not resolve it here. |
| **Q9 — Gaps vs "voz de principio a fin"** | What is still missing for a coherent spoken-Spanish, start-to-finish voice product (language default, STT language, any remaining print-only/screen-only surface that should eventually speak)? |
| **Q10 — Next-Buy recommendation** | After T48-inv + T49: what's next? Confirm T40 stays Parked unless this INV surfaced live evidence to the contrary (expect: no). |
| **Q11 — Connect-plugs wording** | Does `engineer_note_connect_plugs_real_data_map.md`'s `a4-voice-world` row (and siblings) still read correctly against T44–T47 landing fully inside the already-★-closed voice-half surface? Any wording fix needed (no new row expected). |
| **Q12 — Cola / PRIORIDAD / state** | Draft the exact PRIORIDAD/cola/`engineering_state.json` wording after this INV: **T48-inv Implemented, await Cursor review.** |

---

## 2. Forensic method (required)

1. Read every cola row's artifact (report/review) directly off disk — do not trust the cola table's own prose.
2. Read `src/jarvis/adapters/cli/main.py`'s `run_chat`/`main()` argparse wiring and `src/jarvis/adapters/voice/*.py` directly for Q2/Q3/Q6 — cite file:line.
3. Grep, don't assume: `AuthoritySource`, `CONTINUITY_DEFER_PHRASES`, `FULL_CONTINUITY_PHRASES`, `PTT_TRIGGER_PHRASES`.
4. Run the full test suite and the targeted ESC-fence/tip-pin suites; cite the pass count.
5. No new Continuity ranking, no LLM, no second truth — this INV only reads and classifies what exists.

---

## 3. Deliverables

| # | Artifact |
|---|---|
| 1 | `.jes/artifacts/investigation_report_assistant_voice_phase_t_review_b0.md` — answers Q1–Q12 with file:symbol citations |
| 2 | Short PRIORIDAD / cola / `engineering_state.json` update (Q12): T48-inv Implemented, await Cursor review |

**Package:** tip stays **`0.7.5`** for this INV (docs/report only, no `src/` change).

---

## 4. Acceptance (investigation)

- [ ] Report answers Q1–Q12 with citations against live tip code, not prior-report prose
- [ ] ACCEPT backlog and recommended order stated without claiming ACCEPT
- [ ] No `src/` change; full suite + ESC fence + tip-pin suites re-run and cited
- [ ] T40 recommendation stated (expect: stays Parked)
- [ ] Cursor review · Engineer ★ on findings

---

## 5. Paste for Claude

```text
Investigation — INV-assistant-voice-phase-t-review (T48-inv)
Parent tip: T47 @ 0.7.5 (44cb5fe). Tip package stays 0.7.5 (docs only).

INV: .jes/artifacts/investigation_contract_assistant_voice_phase_t_review_b0.md

Complete forensic REVIEW of voice phase T (T34-T47):
Q1 cola truth table (Estado vs artifacts; ACCEPT yes/no)
Q2 four+one operator paths (chat / chat+speak / hablar PTT / --voice / batch)
Q3 DC lock audit (T34 / T44 / T46) vs tip code
Q4 ACCEPT backlog + recommended ACCEPT order (do NOT claim ACCEPT)
Q5 open review notes harvest (T47 N1 already remediated — confirm)
Q6 honesty fences still hold?
Q7 spoken-continuity map current for 0.7.5?
Q8 TTS language: Spanish Skills vs old en_GB — coordinate with T49
Q9 gaps vs "voz de principio a fin"
Q10 next Buy recommendation (T40 stays Parked unless evidence)
Q11 connect-plugs wording
Q12 PRIORIDAD/cola/state -> T48-inv Implemented await Cursor review

Deliverable: investigation_report_assistant_voice_phase_t_review_b0.md
NO src/ for the INV · NO ACCEPT claim · NO wake-word · NO T40
```
