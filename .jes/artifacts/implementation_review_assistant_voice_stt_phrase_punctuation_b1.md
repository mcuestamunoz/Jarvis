# Implementation Review — STT phrase-match punctuation honesty (`B1-assistant-voice-stt-phrase-punctuation`, T55 / V11)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Reviewer:** Cursor (independent — not implementer)  
**Contract:** [IC](implementation_contract_assistant_voice_stt_phrase_punctuation_b1.md) (amended lock 2b) · [V11-DC](design_contract_assistant_voice_stt_phrase_punctuation_b0.md) · [report](implementation_report_assistant_voice_stt_phrase_punctuation_b1.md)  
**Tip under review:** `37c1671` on `cursor/chat-voice-ptt-impl-8ac5` · package **`0.8.2`**  
**Parent:** `9312fdd` / **`v0.8.1`** (T54 ★) · docs commit `f1ade32`

**Verdict:** **PASS WITH NOTES** → Engineer ★ **ACCEPT CLOSED** (2026-10-14) @ tip **`v0.8.2`** (`37c1671` + ACCEPT board).

**Process note:** Independent Cursor review of record. Same-session self-PASS is not review of record. Engineer ★ ACCEPT CLOSED → tag **`v0.8.2`**. N1–N3 non-blocking (live whisper smoke optional).

---

## 1. Scope check vs IC

| Lock / IC item | Evidence | Result |
|---|---|---|
| 1 · Buy · `0.8.2` | `pyproject.toml` `version = "0.8.2"`; no speech deps | **Pass** |
| 2a · `spoken_continuity._normalize` | `_EDGE_PUNCTUATION` + both-ends strip after NFKD | **Pass** |
| 2b · shared `_normalize_for_continuity_match` (all matchers) | Same strip; comment documents shared Skill-first scope; no Continuity-only fork | **Pass** |
| 3 · Tables unchanged; widening flagged | Report §0; T2 pins ARM/HOLD/GO_TO; near-misses fail | **Pass** |
| 4 · Layer 1/2 payloads unchanged | Diff excludes extractors/`render_*`; T3 E2E narrated FULL once | **Pass** |
| 5 · Exit path | `main.py` untouched; T4 `Salir.` / `salir!` | **Pass** |
| 6 · Dead PTT | Helpers deleted from `external_record` + exports; T5 | **Pass** |
| 7 · Modes / silence cut | Untouched; T54 tests still green in focused run | **Pass** |
| 8 · Guide | §4.1 + §8 T55 bullet (Continuity/FULL **and** Skills) | **Pass** |
| 9 · Spoken-continuity map | Tip only; no new egress | **Pass** |
| 10 · Tests | New file covers IC T1–T7 content as shipped T1–T6 (see judgment) | **Pass** |
| 11 · Out of scope | No wake-word, barge-in, IntentResolver, orchestrator | **Pass** |

**Not live-smoked** with whisper — IC §3 remains Engineer ACCEPT gate.

---

## 2. Judgment calls — **accepted**

| # | Choice | Review |
|---|---|---|
| 1 | Lock 2b = **all Skill-first matchers** (Engineer before impl; Cursor IC amend) | **Accept.** Shared helper; fork would be inconsistent. Software ARM latch only — Safety gate unchanged. Report §0 honest. |
| 2 | Strip **both ends** (not trailing-only) | **Accept.** IC T1 requires `¿completo?`; same set as `_is_voice_only_exit`. Interior decimals preserved (`Go to 1.5 2.5`). |
| 3 | Shipped tests labeled T1–T6 covering amended IC T1–T7 asserts (Skill widening folded into T2; guide = T6) | **Accept.** Coverage complete; renumber only. |

---

## 3. Notes (non-blocking)

| ID | Severity | Note |
|---|---|---|
| **N1** | Info / ACCEPT gate | **No live whisper smoke.** Say `completo` / `estado` / optional `armar.` per IC §3 before ★. |
| **N2** | Info | **Typed `--chat` also** accepts edge punct on Skill phrases now (same helper). Harmless; documented in report. |
| **N3** | Info | `IntentResolver._normalize_text` (core non-Skill-first) untouched — correct per lock; STT miss outside Skill-first still possible. |
| **Carry** | — | Anti-echo / barge-in / cancel-hotkey remains **V12+** (INV “V11+”, renumbered). **T40** Parked. |

---

## 4. Tests executed by reviewer

```text
pytest tests/test_assistant_voice_stt_phrase_punctuation_b1.py \
       tests/test_assistant_voice_only_loop_b1.py \
       tests/test_assistant_voice_silence_cut_b1.py -q
→ 21 passed in 40.28s
```

Spot-check: `Completo.` / `¿completo?` FULL; `completos` false; `Estado.` → `estado`; `Go to 1 2.` parses; PTT attrs gone from `adapters.voice`.

Implementer reports full suite **4067 passed / 9 skipped / 0 failed** — not re-run in full here; focused set green.

---

## 5. Recommendation

**PASS WITH NOTES.** Engineer ★ ACCEPT CLOSED (2026-10-14) → tag **`v0.8.2`** (same day as T54 ★ `v0.8.1`). N1 live whisper smoke remains optional operator validation.
