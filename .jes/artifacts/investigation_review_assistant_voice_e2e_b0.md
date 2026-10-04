# Investigation Review — Assistant voice end-to-end (`INV-assistant-voice-e2e`)

**Date:** 2026-10-03  
**Reviewer:** Cursor (forensic pass — Claude paste “Hecho — T34-inv entregado…”)  
**Against:** [INV](investigation_contract_assistant_voice_e2e_b0.md) · [report](investigation_report_assistant_voice_e2e_b0.md) · [Skill-first DC ★](design_contract_assistant_chat_skill_first_b0.md) · [connect-plugs map](engineer_note_connect_plugs_real_data_map.md)  
**Tip reviewed:** `9ce9c6e` on `cursor/voice-e2e-investigation-impl-8ac5` (parent authorize `69273c5` / T33 ★ `v0.6.42`)  
**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-03) — findings → T34-DC ★ + cola T35…T40.

**Process note:** Claude Code investigated under ★ AUTHORIZED INV. This is the independent Cursor review of record.

---

## 0. Forensic checklist

| Risk | Result |
|---|---|
| Blind seed / stale T32 status | **Clear** — re-verified `_resolve_go_to_destination` / `parse_go_to_destination` landed on tip |
| Invented parallel brain | **Clear** — reuses `handle_user_text` + `run_skill` + existing fulfills |
| Craft forced into v1 | **Clear** — craft/wizards explicitly deferred (Q3/Q7/V6) |
| Vendor STT lock | **Clear** — Q4 recommends external + fixture-first (A+C) |
| Debts CLOSED by prose | **Clear** — connect-plugs voice rows still Parked/OPEN |
| `src/` mutation | **Clear** — commit touches docs + report only |
| Phase plan not ★-able | **Clear** — V0–V6 independently scoped; first Buy = DC then V1 IC |
| Tip / package | **Clear** — stays `0.6.42` |

---

## 1. INV checklist (Q1–Q12)

| Q | Verdict |
|---|---|
| Q1 Ingress boundary | **PASS** — `VoiceIntentAdapter` stub; recommend `raw_text: str`; source-threading gap named |
| Q2 Chat brain reuse | **PASS** — channel-agnostic `handle_user_text` proven (CLI + MCP); terminal-coupled parse sites mapped |
| Q3 Surface inventory | **PASS** — Skill-first twelve = v1; craft defer; explain CLI / board never |
| Q4 Audio I/O | **PASS** — zero speech deps confirmed; A+C recommended |
| Q5 Egress | **PASS** — adapter after result; reuse `render_response` for v1 |
| Q6 GO_TO metadata | **PASS** — plug landed; spoken decimals deferred; bare go-to honesty in v1 |
| Q7 world/ | **PASS** — not required for C.1; sibling later |
| Q8 Safety/authority | **PASS** — same ArmedAllowlist; `AuthoritySource` has no `"voice"` |
| Q9 CLI migrate | **PASS** — voice beside `--chat` → shared helper → craft later |
| Q10 Phase table | **PASS** — V0–V6 |
| Q11 First Buy | **PASS** — DC `B1-assistant-chat-voice-channels` → IC `B1-assistant-voice-intent-ingress` |
| Q12 Map/PRIORIDAD | **PASS** — pointers + T34-DC/T35 placeholders |

---

## 2. Spot-checks (this pass)

```text
TerminalIntentAdapter.parse in orchestrator.py → 12 call sites
  (explain, continuity, ARM, DISARM, HOLD, LAND, GO_TO, TAKEOFF,
   RETURN_HOME, FOLLOW, PATROL, CHARGE)
MCP JarvisSessionManager.chat → handle_user_text + render_response  ✓
VoiceIntentAdapter → NotImplementedError                             ✓
AuthoritySource = Literal["radio","api","operator"] — no "voice"     ✓
No world/ · no speech deps in pyproject                              ✓
T32 resolver symbols present                                         ✓
```

---

## 3. Notes

**N1 — “Thirteen” vs twelve.** Report prose says thirteen `TerminalIntentAdapter.parse` sites; the cited line list and a tip count are **12** (no thirteenth). Non-blocking; DC/IC should say **twelve**.

**N2 — Process.** Engineer ★ ACCEPT findings (2026-10-03) → T34-DC ★ CLOSED · cola T35…T40 queued. Tip stays `0.6.42` until T35 opens `0.6.43`.

---

## 4. Closed

```text
★ ACCEPT CLOSED on findings
T34-DC ★ CLOSED · cola note engineer_note_voice_phase_c_cola.md
Next authorize when Engineer says proceed: T35 Intent-ingress IC @ 0.6.43
```
