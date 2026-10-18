# Investigation Report — Part A: Voice phase tip (`INV-voice-llm-ci-audit`, CI-INV-0)

**Project:** Jarvis · **Date:** 2026-10-16 · **Investigator:** Claude Code (read-only)
**Contract:** [INV IC](investigation_contract_voice_llm_continuity_interpreter_audit_b0.md) · **Index:** [index](investigation_report_voice_llm_ci_audit_b0.md) · [Part B](investigation_report_voice_llm_ci_audit_part_b_llm_ci_b0.md) · [Part C](investigation_report_voice_llm_ci_audit_part_c_synthesis_b0.md)
**Tree audited:** tip `v0.8.6` (`52e6892`) + uncommitted CI-1/CI-1b (`0.8.7`, untagged). Line numbers = working tree as found 2026-10-16.
**Status:** Implemented — awaiting Cursor review. No ACCEPT claim. No `src/` edit.

Legend: **shipped ★** · **in tree untagged** · **DC only** · **Parked** · **contradicted** · **drift** (docs ≠ code).

---

## A1 — Cola truth T34–T59

Method: each review's `**Verdict:**` line vs `git tag` vs cola Estado.

| Rows | Review verdict (live file) | Tag exists | Cola Estado | Result |
|---|---|---|---|---|
| T35–T38 | PASS WITH NOTES → ★ ACCEPT CLOSED @ `v0.6.43`…`v0.6.46` | yes (all four) | ★ CLOSED | ✅ coherent |
| T39 | ★ @ `v0.7.0` | yes | ★ CLOSED | ✅ |
| T41–T43, T45, T47, T49–T52 | ★ @ `v0.7.1`…`v0.7.9` | yes (all) | ★ CLOSED | ✅ (T48-inv N1 "T47 not ACCEPTed" is **remediated** — `implementation_review_assistant_chat_voice_ptt_b1.md:7` now reads ★ @ `v0.7.5`) |
| T53–T59 | ★ @ `v0.8.0`…`v0.8.6` | yes (all) | ★ CLOSED | ✅ |
| T34-inv, T44-inv, T48-inv, T53-inv | findings ★ | n/a (docs) | CLOSED / FINDINGS ACCEPTED | ✅ |

**Drift (docs only, no code impact):**

| # | Drift | Evidence |
|---|---|---|
| A1-d1 | Consumed DCs still labelled **"DC ready"**: T44-DC, T46-DC, T53-DC, T54-DC, T56-DC (T52-DC, T55-DC correctly say CLOSED/consumed) | `engineer_note_voice_phase_c_cola.md` rows T44-DC, T46-DC, T53-DC, T54-DC, T56-DC |
| A1-d2 | T46-DC (hybrid `--chat --voice-speak` PTT) still listed as live "DC ready" although T53 retired that surface | same row; `main.py:1435-1452` hard-rejects `--voice-speak` outside batch |
| A1-d3 | "Product picture" table is phrased as **target after V9** and the "V8 plan" section still describes the hybrid PTT flow without a "retired" marker | cola §"Operator / use path", §"V8 plan" |
| A1-d4 | Cola header still says "next = T40 Parked, or Engineer pick" — the CI cola has since opened; no cross-link | cola line 5 |

## A2 — Product modes today (tip)

| Surface | Code | Brain | Source tag | Speaks | Status |
|---|---|---|---|---|---|
| `--chat` | `main.py:1468-1470` → `run_chat` `main.py:1107-1118` → `_run_chat_session(speak_tts=False)` | full chat | `TERMINAL` (default; `main.py:994-996` docstring, `orchestrator.py:1580-1592`) | **never** — `_chat_speak_fn(False)` returns a no-op that never imports TTS (`main.py:954-958`) | **shipped ★** product mode 1 |
| `--voice-only` | `main.py:1454-1459` → `run_voice_only` `main.py:1259-1281` | **same** `_run_chat_session` (`main.py:992`) | `TERMINAL` (not `VOICE`) | every `Jarvis >` reply (`_say`, `main.py:1020-1022`); Layer 2 only on the two walls (`main.py:1064`, `main.py:1097-1098`) | **shipped ★** product mode 2 |
| `--voice` | `main.py:1361` (`help=SUPPRESS`) → stderr pointer + exit 2 (`main.py:1438-1444`) | none | — | — | **retired** (T53 lock 9) |
| `--voice-speak` w/o batch, `--chat --voice-speak` | `main.py:1446-1452` exit 2 | none | — | — | **retired** (T53 lock 4) |
| `--chat --voice-only` | `main.py:1455-1457` exit 2 | none | — | — | guard |
| `--voice-fixture PATH` | `main.py:1306-1320` → `run_voice` (`fixture_loop.py:68-86`) | full `handle_user_text` | **`VOICE`** (`fixture_loop.py:60`) | optional (`--voice-speak`), verbatim | batch/CI only (T53 lock 10) |
| `--voice-audio PATH` | `main.py:1323-1342` | same, via `run_voice_turn_from_audio` | **`VOICE`** | optional, verbatim | batch/CI only |

Notes:
- **Skills-only brain is gone from the product path.** `run_voice_turn` is reachable only from batch flags. It is not Skills-only either: it calls the full `handle_user_text(..., source=VOICE)` (`fixture_loop.py:60`); "Skills-only" was a v1 *scope* claim (T34-DC lock 4), never a code fork.
- **`IntentSource.VOICE` changes exactly one thing:** `_parse_intent` picks `VoiceIntentAdapter` (`orchestrator.py:420-422`). The daily `--voice-only` mode never sets it (A4 row T34-3).
- Layer 2 fires on two sites only: startup wall `main.py:1066-1068` and `action == "project_status"` `main.py:1097-1098`. Every other turn is speak-as-printed (`main.py:1099-1100`).

## A3 — Layer 1 / Layer 2 inventory vs [spoken-continuity map](engineer_note_chat_spoken_continuity_map.md)

Classes in the map still match tip behaviour for every row it lists. Three problems:

| # | Problem | Evidence | Severity |
|---|---|---|---|
| A3-g1 | **Missing row — `analyze` turn.** `render_response` has a dedicated `analyze` branch (`main.py:611-612`: no `Acción ejecutada` header, LLM message as body). Under `--voice-only` it is spoken as printed (`main.py:1099-1100`), i.e. **LLM-generated text reaches TTS today** (incl. the CI-1 smoke echo and the goal-plan prepend). The map has no row for it; it falls under "Main-turn success" only by accident. | `main.py:611`, `orchestrator.py:7468-7506`, map Table 1 | **high** (classification gap on the exact surface CI-2/CI-4 will change) |
| A3-g2 | **Missing row — wall suffixes are printed but never spoken.** On `project_status`, `render_response` appends `[Wizard activo] {reprompt}`, dismiss notes (`main.py:585-593`), but the speak side uses `spoken_text_for_wall(...)` which rebuilds from `ctx` and ignores `printed_wall` (`spoken_continuity.py:251-263`). A voice user mid-iterate-wizard who says `estado` never **hears** what the wizard is waiting for. Not classified anywhere. | `main.py:591-593`, `main.py:1097-1098`, `spoken_continuity.py:261-263` | **medium** (voice journey) |
| A3-g3 | **Line citations stale since T53** (same class as T48-inv N3). E.g. banner map `main.py:966-968` → tip `1024-1026`; EOF exit `979-980` → `1037-1039`; startup wall `1003-1005` → `1066-1068`; main-turn error `1030` → `1093`; JSON fallback `743` → `763`; `render_startup_context` wall refs `main.py:296-537` shifted (+~14). Column header still "Speaks (`0.7.4`)?" | map Table 1/2 vs `main.py` | low (docs) |

No new surface was added T54–T59 that the map misses: Grabando cue, `[voz]` echo, cancel/settle/keys, blank-take (silent `""`, `main.py:1251-1252`) are all rows or explicitly "no new surface".

## A4 — DC lock matrix vs tip

Only locks with non-trivial status are listed; every other numbered lock in T34/T44/T52/T53/T54/T55/T56-DC is **still true** at tip (spot-checked against the cited code).

| DC · lock | Lock text (short) | Tip | Status |
|---|---|---|---|
| T34-1 | Same brain | `_run_chat_session` shared (`main.py:992`) | ✅ true |
| T34-2/3 | Voice ingress = `VoiceIntentAdapter`, `source=VOICE` threaded | Threaded (`orchestrator.py:1580-1615`) **but daily `--voice-only` stays `TERMINAL`** | **drifted** — VOICE tag only on batch paths; harmless today (adapters equivalent) but any future VOICE-specific policy would silently not apply to the daily mode |
| T34-4 | v1 = twelve Skills; craft/LLM **out** | `--voice-only` = full brain incl. LLM fallthrough | **amended by T53-2** (correct, ★) — guide `USER_GUIDE_VOICE.md:18` says so |
| T34-7 | No `"voice"` AuthoritySource | `AuthoritySource = Literal["radio","api","operator"]` (`capabilities/safety.py:96`) | ✅ true |
| T44-2 | **No LLM in Layer 2** | Layer 2 extractors are 0-LLM (`spoken_continuity.py` imports stdlib + `_humanize_next_useful_why` only). **But** LLM `analyze` text is spoken verbatim on `--voice-only` (A3-g1) — outside Layer 2 by definition (speak-as-printed), so the lock is not *broken*, yet the ear already gets LLM text with no Layer 2 discipline | ✅ true for Layer 2 · **amended by CI-0 lock 3** for future compose (see table below) |
| T44-3 | Brief only on the two walls; other turns speak-as-printed | `main.py:1092-1100` | ✅ true |
| T44-7 | Bare `--chat` text-only; `--voice` unchanged | `--chat` silent ✅; `--voice` **retired** | partly **superseded by T53** (correct) |
| T52-1..10 | FULL narrated ≠ print, 0-LLM, screen-only set | `spoken_continuity.py:178-248` | ✅ true |
| T53-1..14 | two modes, same brain, kill hybrid, mic cadence, ephemeral wav, honesty | `main.py:1158-1281`, `1435-1470` | ✅ true (T53-6 "fixed duration" **amended by T54** silence cut, ★) |
| T54 / T55 / T56 locks | record cut external; punct strip; cancel = interrupt not exit | `scripts/voice/record_turn.sh`; `spoken_continuity._normalize`; `main.py:963-987` | ✅ true |

### T44 "No LLM in Layer 2" vs CI-0 — explicit conflict table (IC acceptance item)

| Aspect | T44-DC lock 2 / T52-DC lock 2 (★ shipped) | CI-0 DC lock 3 + amendment table (DC ready, **no code**) | Tip reality |
|---|---|---|---|
| Who writes spoken words on walls | deterministic extract only | LLM **may compose** language from Layer 1 fields | deterministic only (`brief_spoken_continuity` / `full_spoken_continuity`) |
| Layer 1 authority | screen = sole truth | unchanged (CI-0 lock 2) | unchanged |
| Fallback | — | deterministic extract stays fallback + regression baseline | is the only path |
| Scope of amendment | — | "for language compose only" | not yet exercised — **no CI-2 IC exists** |
| Non-wall turns | speak-as-printed (T44-3) | CI-0 lock 4: Continuity-shaped egress spoken **and** printed in both modes | `analyze` LLM text already spoken verbatim on voice-only; `--chat` speaks nothing |
| Verdict | **valid ★ for what shipped** | **supersedes T44-2 only when a CI-2 IC lands** | **no contradiction today** — the conflict is latent and must be resolved inside CI-2 DC (which turns become compose, which stay extract, what the fallback is) |

## A5 — Operator journey gaps (daily Spanish voice)

| # | Gap | Evidence | Class |
|---|---|---|---|
| A5-1 | **Spanish STT is opt-in.** `whisper_stt.sh` passes `${JARVIS_WHISPER_ARGS:-}` — no default `-l es`; the comments recommend it | `scripts/voice/whisper_stt.sh:11,18,80` | product gap (low–medium; operator config) |
| A5-2 | **Silence hallucinations reach the brain** (`Gracias.` etc.) — T59 N2. With the Gemma default they now open a **create-project wizard** (Part B B3-1) instead of failing | T59 review N2; Part B B3-1 | **high** (worsened by CI-1) |
| A5-3 | Wizard reprompt not spoken on `estado` mid-wizard | A3-g2 | product gap (medium) |
| A5-4 | `analyze` answers spoken in full, unbounded length, no Layer 2 brief, may contain plan prepend / instruction echo | A3-g1; logs `20261015T135747`, `20261016T091434` (`"En resumen, el usuario quiere que actúe como…"`) | **high** (CI-2/CI-4 territory) |
| A5-5 | Silence cut is level-based (mid-sentence pause ends turn; noisy rooms run to cap); ffmpeg only | T54 review N2/N3 | accepted product limit |
| A5-6 | Craft wizard bodies spoken as printed (long option lists) | T44-3; CI-0 lock 4 "per later IC" | product gap → CI-2 scope question, **not T40** |
| A5-7 | `world/` / spoken GO_TO destinations | T34-8/9 | **Parked (T40)** |
| — | blank takes, cancel/settle/keys, exit punctuation | T56–T59 ★ (`main.py:1158-1256`) | closed |

## A6 — Honesty fences (re-verified)

| Fence | Evidence | Result |
|---|---|---|
| No `"voice"` AuthoritySource | `capabilities/safety.py:96`; `grep '"voice"' src/jarvis` → only `IntentSource.VOICE = "voice"` (`capabilities/intent.py:31`) | ✅ |
| External STT fail-closed | `SttConfigError` on missing cmd, `SttProcessError` on run/exit, `SttEmptyTranscriptError` on empty (`external_stt.py:104-122`); config error ends session, process error reopens mic (`main.py:1236-1245`) | ✅ |
| External record fail-closed | `RecordConfigError`/`RecordProcessError` (`external_record.py:138-162`); handled `main.py:1233-1243` | ✅ |
| TTS fail-closed + sanitize | `speak_egress` → `sanitize_for_speech` (`external_tts.py:109-130`); `TtsError` printed once (`main.py:972-973`) | ✅ |
| Blank-STT path | `is_blank_stt_transcript` (`external_stt.py:74`) → `""`, no echo (`main.py:1251-1252`) | ✅ |
| No tip pins | `tests/test_suite_no_tip_version_pins_b1.py:26` | ✅ |
| **Suite independent of live services** | **Violated (pre-existing, voice tests):** `test_assistant_chat_voice_ptt_b1.py::test_t3_bare_chat_hablar_never_records` and `test_assistant_voice_only_loop_b1.py::test_t3_bare_chat_never_records_or_speaks` call real `run_chat()`, which builds `JarvisLLMInterface(client=OllamaClient())` (`main.py:1017`) and the default logger. Proven this INV: running only those two tests → **2 live Gemma calls (28.9 s)** and +2 files in `runtime/llm_logs/` (`20261016T150758…`, `…150808…`, both `hablar → create_project`). Tests pass either way (assert only "no Grabando"), so the leak is silent. | ❌ **gap** (see Part B B7, Part C G-03) |

## A7 — Voice vs full chat brain

`--voice-only` runs the **identical** `_run_chat_session` body as `--chat` (`main.py:1107-1118` vs `1259-1281`): same orchestrator, same `JarvisLLMInterface(OllamaClient())`, same `handle_user_text` + `attach_project_coherence` (`main.py:1086-1087`), same startup picker. Differences are only `read_line` (mic after picker), `is_exit` (+`salir`, punct-tolerant), `speak`. **No Skills-only leftover on the product path.** The only asymmetry is the `TERMINAL` source tag (A4 T34-2/3).

## A8 — N-notes harvest (T48–T59)

| Note | Status at tip | Evidence |
|---|---|---|
| T48-inv N1 (T47 verdict misquote) | remediated | T47 review line 7 ★ |
| T48-inv N3 / map line drift | **open, regressed** | A3-g3 |
| T52 N1/N2 (raw action codes / why codes spoken) | remediated | `_ACTION_SPEAK_MAP` `spoken_continuity.py:91`; `_humanize_next_useful_why` |
| T52 N4 (top gap spoken twice) | by design | T52 review |
| T53 N1 (dead PTT exports) | remediated by T55 | `external_record.py:22-23` (retired note only) |
| T53 N2 (`Completo.` punct) | remediated by T55 | `spoken_continuity._normalize` |
| T53 N3 / T56 N2 (Ctrl-C while brain thinks) | partly — T58 keys cover speech/take windows; brain-thinking window still prior behaviour | T58 review |
| T54 N2/N3 (level-based cut, ffmpeg only) | open — accepted limit | A5-5 |
| T55 N3 (`IntentResolver._normalize_text` not punct-tolerant) | open, low | T55 review |
| T56 N3 / T58 N2,N3 (POSIX, arrow=Esc, shared pgid) | open — by design | reviews |
| T59 N2 (hallucinations reach brain) | **open, worsened by CI-1** | A5-2 |
| T59 N3 (closed marker set) | open — by design | T59 review |
| All "Info / ACCEPT gate: no live smoke" notes (T54–T59 N1) | closed by Engineer ★ on each tag | reviews |

**T40 recommendation:** stay **Parked**. No evidence in tip code, logs, or journey gaps that a `world/`/craft-voice DC is the bottleneck; every high voice gap above is LLM/egress-shaped (CI-2/CI-3/CI-1c), not world-shaped.
