# Investigation Report — Voice phase T review (`INV-assistant-voice-phase-t-review`, T48-inv)

**Project:** Jarvis
**Date:** 2026-10-05
**Investigator:** Claude Code (Engineer paste)
**Contract:** [`investigation_contract_assistant_voice_phase_t_review_b0.md`](investigation_contract_assistant_voice_phase_t_review_b0.md)
**Parents:** [cola note](engineer_note_voice_phase_c_cola.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · [guide](../../docs/USER_GUIDE_VOICE.md) · [TTS brief](engineer_note_voice_tts_product_brief.md)
**Status:** **Implemented** — await Cursor review → Engineer ★ on findings.
**Package:** tip stays **`0.7.5`** — docs/report only, **no `src/` change**.

**Scope discipline:** read-only forensic review. No `src/` file touched. No ACCEPT claimed for any Buy. Full suite re-run (`4026 passed, 9 skipped`) — identical to the count on tip before this INV; this report changes zero behavior.

---

## Q1 — Cola truth table (Estado vs artifacts; ACCEPT yes/no)

Verified by opening each row's own report/review artifact directly, not by trusting the cola table's prose.

| Buy | Cola "Estado" | Artifact says | Tip code matches? | **ACCEPT?** |
|---|---|---|---|---|
| T34-inv | ✅ ★ CLOSED | [review ★](investigation_review_assistant_voice_e2e_b0.md): ACCEPT CLOSED | — (docs) | **Yes** — ★ CLOSED |
| T34-DC | ✅ ★ CLOSED | [DC ★](design_contract_assistant_chat_voice_channels_b0.md): "★ CLOSED (Engineer 2026-10-03)" | locks hold, see Q3 | **Yes** — ★ CLOSED |
| T35 | ✅ ★ ACCEPT CLOSED @ `v0.6.43` | [review ★](implementation_review_assistant_voice_intent_ingress_b1.md:7): "`Verdict: PASS WITH NOTES → Engineer ★ ACCEPT CLOSED (2026-10-03) @ tip v0.6.43`" | `VoiceIntentAdapter` present (`capabilities/intent.py:31` `VOICE = "voice"`) | **Yes** |
| T36 | ✅ ★ ACCEPT CLOSED @ `v0.6.44` | [review ★](implementation_review_assistant_voice_fixture_loop_b1.md:7): same verdict line @ `v0.6.44` | `adapters/voice/fixture_loop.py::run_voice` present | **Yes** |
| T37 | ✅ ★ ACCEPT CLOSED @ `v0.6.45` | [review ★](implementation_review_assistant_voice_stt_external_b1.md:7) @ `v0.6.45` | `external_stt.py::transcribe_audio_file` present, reused unchanged through T47 | **Yes** |
| T38 | ✅ ★ ACCEPT CLOSED @ `v0.6.46` | [review ★](implementation_review_assistant_voice_tts_external_b1.md:7) @ `v0.6.46` | `external_tts.py::speak_egress` present | **Yes** |
| T39 | ✅ ★ ACCEPT CLOSED @ `v0.7.0` | [review ★](implementation_review_assistant_voice_v1_checkpoint_b1.md:7) @ `v0.7.0` | voice v1 checkpoint — all twelve Skills reachable by voice | **Yes** |
| T41 | Implemented · Cursor PASS WITH NOTES (ACCEPT deferred) | [review](implementation_review_assistant_voice_demo_ready_b1.md): N2 "Await Engineer ★ ACCEPT → tag v0.7.1" | `docs/USER_GUIDE_VOICE.md` + `scripts/voice/piper_tts.sh` present | **No** — still open |
| T42 | Implemented · Cursor PASS WITH NOTES | [review](implementation_review_assistant_voice_interactive_cli_b1.md): N2 "Engineer ★ ACCEPT → tag v0.7.2" | `run_voice_interactive` present (`main.py:1162`), structural TTS-seam guard confirmed in Q6 | **No** |
| T43 | Implemented · Cursor PASS WITH NOTES | [review](implementation_review_assistant_chat_voice_speak_b1.md): N2 "Engineer ★ ACCEPT → tag v0.7.3" | `_chat_speak_fn` present (`main.py:930`) | **No** |
| T44-inv | Implemented · Cursor PASS WITH NOTES | [review](investigation_review_assistant_chat_spoken_continuity_b0.md:9): "No ACCEPT claimed here" | living map exists (Q7) | **No** (findings-level ★, not a code ACCEPT — not yet recorded either) |
| T44-DC | DC ready | [DC](design_contract_assistant_chat_spoken_continuity_b0.md:6): "DC ready — Engineer asked to lock the plan" | locks consumed by T45, see Q3 | n/a — design lock, not an ACCEPT-bearing code Buy |
| T45 | Implemented · Cursor PASS WITH NOTES | [review](implementation_review_assistant_chat_spoken_continuity_b1.md): N2 refers to pending ACCEPT; cola itself still says "await Engineer ★ ACCEPT" | `spoken_continuity.py` present, locks hold, see Q3 | **No** |
| T46-DC | DC ready — locked, consumed by T47 | [DC](design_contract_assistant_chat_voice_ptt_b0.md:6): "DC ready — Engineer *dale*" | locks consumed by T47, see Q3 | n/a — design lock |
| T47 | Implemented · Cursor PASS WITH NOTES | [review](implementation_review_assistant_chat_voice_ptt_b1.md:7): "PASS WITH NOTES → Engineer ★ ACCEPT CLOSED (2026-10-05) @ tip v0.7.5" — **note: this line's own wording anticipates a tag that has not actually been cut** (no `git tag` matching `v0.7.5` exists — see below); N1 mkstemp fd leak remediated on tip `44cb5fe` | `main.py:1023-1027` confirms `fd, tmp_name = tempfile.mkstemp(...); os.close(fd)` | **No** — tag not cut |
| T40 | Parked | no artifact beyond a placement-DC pointer | no `world/` package on disk (`ls src/jarvis/` has no `world`) | n/a — Parked |

**Drift found:** T47's own review file states the verdict line as if ACCEPT already landed ("→ Engineer ★ ACCEPT CLOSED (2026-10-05) @ tip v0.7.5"), but `git tag -l` shows no `v0.7.5` tag, and the cola/`engineering_state.json`/`IMPLEMENTATION_TASKS.md` all still correctly say "await Engineer ★ ACCEPT." This is a **wording drift inside the review artifact's own verdict line**, not a real ACCEPT — every other SoT (cola, state, PRIORIDAD) is internally consistent and honest about it still being open. Flagging it here rather than treating it as settled.

```text
$ git tag -l | grep -E "^v0\.7\.|^v0\.6\.4[3-6]$"
v0.6.43
v0.6.44
v0.6.45
v0.6.46
v0.7.0
```
`v0.6.43`–`v0.6.46` (T35–T38) and `v0.7.0` (T39) **are** real tags — T35–T39's "ACCEPT CLOSED @ v0.x" lines are correctly backed by an actual `git tag` object, not narrative-only. **None of `v0.7.1`–`v0.7.5` exist as tags** — confirmed by the same grep returning only `v0.7.0`. This matches Q1's table exactly: T41–T47 are the Buys without Engineer ACCEPT, and consistently, none of them has a tag either. **ACCEPT CLOSED and tag-cut track each other correctly in this repo's history** — the only drift found is T47's own single verdict-line wording (above), not a systemic tag/ACCEPT mismatch.

**Net:** nine Buys (T41–T47, excluding the two DC-only locks) are Cursor PASS WITH NOTES, zero are Engineer ACCEPT, since `v0.7.0`. Only T35–T39 (and T34-inv/T34-DC) carry a real Engineer ★ ACCEPT.

---

## Q2 — Four (+ one) operator paths

Re-verified directly against `main()`'s argparse wiring (`main.py:1213-1309`) and each `run_*` function's own source — not from any prior report's description.

| Path | CLI | Brain / `source` | Speaks? | Mic on when |
|---|---|---|---|---|
| `--chat` (bare) | `main.py:1216`, dispatched `main.py:1313-1314` → `run_chat(speak_tts=False)` | `handle_user_text` default `TERMINAL` — full Continuity/craft/LLM | **Never** — `_chat_speak_fn(False)` (`main.py:930-946`) returns a no-op `speak` that never imports `speak_egress`; confirmed structurally in Q6 | Never |
| `--chat --voice-speak` | `main.py:1244-1252` (`--voice-speak` flag), `run_chat(speak_tts=True)` | same `TERMINAL` brain, unchanged | **Every** printed `Jarvis > …` reply, **except** the two Continuity-wall sites (project load `main.py:1057-1061`, `project_status` turn `main.py:1029-1035`-equivalent via `spoken_text_for_wall`), which speak T45's brief extract by default, full wall only on a locked FULL phrase this turn | Never (text typed) |
| `--chat --voice-speak` + typed `hablar`/`habla` (PTT) | same flag combo, intercepted inside `run_chat`'s loop at `main.py:1020-1044` | same `TERMINAL` brain — the transcript falls through the identical loop, no `source=VOICE` | Same rules as the row above, applied to the transcript | **Only** for `JARVIS_RECORD_SECONDS` (default 7s) immediately after typing `hablar`/`habla`; off otherwise |
| `--voice` | `main.py:1217-1223`, dispatched `main.py:1301-1302` → `run_voice_interactive()` (`main.py:1162`) | `source=VOICE` (Skills-only — no Continuity/craft/LLM, per T34-DC lock 4) | **Always** — this REPL always speaks every reply, no `--voice-speak` flag needed for it (confirmed: `run_voice_interactive`'s own docstring and T42's IC lock 5) | Never (text typed; STT only enters via `--voice-audio`, a separate path) |
| Batch/fixture — `--voice-fixture PATH` | `main.py:1226-1233`, dispatched `main.py:1309-1310` → `run_voice_fixture(path, speak_tts=args.voice_speak)` (`main.py:1123`) | `source=VOICE`, one line per fixture row, no keyboard | Only if `--voice-speak` also passed | Never — fixture text, not audio |
| Batch/one-shot — `--voice-audio PATH` | `main.py:1235-1242`, dispatched `main.py:1305-1306` → `run_voice_audio(path, speak_tts=args.voice_speak)` (`main.py:1140`) | `source=VOICE`, **one turn only** — new orchestrator per invocation, no latch persistence across calls (confirmed in the guide's §8 "no persiste" bullet, re-checked against `run_voice_audio`'s body: it constructs a fresh `JarvisOrchestrator()` every call) | Only if `--voice-speak` also passed | Only during that single external STT call on the given file — Jarvis itself never touches a mic; the file is already recorded |

**Confirmed:** exactly one path ever captures live audio from a microphone — the PTT intercept inside `--chat --voice-speak` (`JARVIS_RECORD_CMD`, timed). `--voice-audio` processes an already-recorded file; it does not open a mic itself. This matches T46-DC's lock 2 ("push-to-talk, not always-on... Capture starts only when the operator types a locked trigger") and the guide's §1 "Qué no es" bullet precisely.

---

## Q3 — DC lock audit (T34 / T44 / T46) vs tip code

### T34-DC (`design_contract_assistant_chat_voice_channels_b0.md`) — ★ CLOSED, 10 locks

| # | Lock | Tip status |
|---|---|---|
| 1 | Same brain, no parallel Skill runtime | **Holds** — every path above dispatches through `handle_user_text`/`run_skill`; no second dispatcher found in `adapters/voice/` |
| 2 | Ingress = text, no audio bytes in `capabilities/`/`intelligence/` | **Holds** — `VoiceIntentAdapter.parse(raw_text: str)` (`capabilities/intent.py`); audio decode lives only in `adapters/voice/external_stt.py`/`external_record.py` + `scripts/voice/` |
| 3 | Source threading, default `TERMINAL` | **Holds** — `run_chat` never passes `source`; `run_voice_interactive`/`run_voice_fixture`/`run_voice_audio` pass `VOICE` |
| 4 | v1 surface = twelve Skills only on `--voice`; craft/LLM out | **Holds** — `--voice` never reaches `_classify`/LLM fallthrough (T34-DC's own locked scope); `--chat --voice-speak` is explicitly the *other* path where craft/LLM is in scope (T43), by design, not a violation of this lock (this lock only binds `--voice`) |
| 5 | STT/TTS external, no tip-pinned vendor SDK | **Holds** — `pyproject.toml` (checked, Q6) has no `piper`/`whisper`/`vosk`/`speechrecognition`/etc. |
| 6 | Egress via `render_response`, no fulfill fork | **Holds** — `_say`/`speak` always wrap an already-rendered string; no new render path for voice specifically |
| 7 | Same Safety gate, no `"voice"` Authority source | **Holds** — `AuthoritySource = Literal["radio", "api", "operator"]` (`safety.py:95`), re-verified by reading the type, not prose |
| 8 | GO_TO metadata plug ready, bare `go to` ok for v1 | **Holds** — unchanged since T32, not touched by T41–T47 |
| 9 | `world/` not required for V1–V5 | **Holds** — no `world/` package on disk |
| 10 | Out-unless-★ list (copper/ESC, craft voice UX, Authority-from-voice, etc.) | **Holds** — none of T41–T47 touched any of these |

### T44-DC (`design_contract_assistant_chat_spoken_continuity_b0.md`) — DC ready, 10 locks, consumed by T45

| # | Lock | Tip status |
|---|---|---|
| 1 | Two layers, Layer 1 only truth | **Holds** — `spoken_continuity.py`'s own docstring (lines 1-9) states this explicitly; `render_startup_context`/`render_response` unmodified by T45/T47 (confirmed: neither function name appears in T45's or T47's own file-change lists) |
| 2 | No LLM in Layer 2 | **Holds** — `brief_spoken_continuity` (`spoken_continuity.py:72-111`) reads only dict fields already computed; zero LLM import |
| 3 | Brief by default on the two wall sites only | **Holds** — `spoken_text_for_wall` called at exactly two `run_chat` sites (startup block, `project_status` turn); every other `_say` call is untouched |
| 4 | Brief payload — exact 5-item ordered list | **Holds** — `brief_spoken_continuity` lines 92-109 implement precisely `situation` → `next_step` (+ humanized `why`) → `PROJECT STATUS:` phrase → top gap title, in that order |
| 5 | Explicitly-excluded fields stay out of brief | **Holds** — `evidence`, BOM lines, readiness subsystem table, propulsion/hover/endurance, `explain_topics`, block-closure — none appear in `brief_spoken_continuity`'s body |
| 6 | FULL-this-turn-only, finite ten-phrase set, no session latch | **Holds** — `FULL_CONTINUITY_PHRASES` is a tuple of exactly ten literal strings (`spoken_continuity.py:41-52`); `is_full_continuity_request` is a pure per-call function, no module/session state |
| 7 | Bare `--chat` text-only; `--voice` unchanged | **Holds** — confirmed in Q2; `run_voice_interactive` does not import `spoken_continuity` at all (grep confirms zero reference) |
| 8 | Extractor lives in `adapters/voice/`, called from speak path only | **Holds** — `spoken_continuity.py` is exactly there; `brief_spoken_continuity` is called from `run_chat`'s speak lines, never from a print line |
| 9 | Living map updated same-Buy | **Holds for T45**; T47 also complied (Q7) |
| 10 | Out-unless-★ list | **Holds** — none of the excluded items (LLM summary, wake-word, T40, recorting screen) appear anywhere in T45/T47 |

### T46-DC (`design_contract_assistant_chat_voice_ptt_b0.md`) — DC ready, 13 locks, consumed by T47

| # | Lock | Tip status |
|---|---|---|
| 1 | Same session/brain, no `run_voice_turn`/`source=VOICE` | **Holds** — `run_chat`'s PTT block (`main.py:1020-1044`) never calls `run_voice_turn`; `handle_user_text` is reached later in the same loop body with the substituted `user_input`, no `source` kwarg |
| 2 | Push-to-talk, not always-on | **Holds** — capture only starts inside the `if speak_tts and is_ptt_trigger(user_input):` branch, once per typed line |
| 3 | Finite trigger set `hablar`/`habla`, not in `CONTINUITY_DEFER_PHRASES` | **Holds** — `PTT_TRIGGER_PHRASES = frozenset({"hablar", "habla"})` (`external_record.py:47`); grepped `CONTINUITY_DEFER_PHRASES` (`config.py:51-112`, full set re-printed in this review) — neither string present |
| 4 | Intercept once, no re-intercept on transcript | **Holds** — the `is_ptt_trigger` check happens once per `input()` line, before the substitution; the transcript assignment (`main.py:1044`) happens *after* the check already ran for this iteration, and the next loop iteration re-reads from `input()`, not from the old transcript |
| 5 | Keyboard stays, empty line still `continue` | **Holds** — `main.py:1017-1018` unchanged, precedes the PTT check |
| 6 | PTT only with `speak_tts=True` | **Holds** — `speak_tts and is_ptt_trigger(...)` — bare `--chat` never evaluates the trigger check at all (short-circuit) |
| 7 | Record = external process, typed `RecordError` family, no ffmpeg hardcode in Python | **Holds** — `external_record.py`'s `record_audio_file` shells out via `shlex.split`+`subprocess.run`; `RecordConfigError`/`RecordProcessError` both typed; ffmpeg/arecord only appear in the shell wrapper |
| 8 | Timed capture, `Grabando {n} s…` print-only | **Holds** — `main.py:1022` is a bare `print`, never passed to `speak(...)` |
| 9 | Existing STT reused, `User > [voz] {transcript}` print | **Holds** — `transcribe_audio_file` imported from the pre-existing `external_stt.py`, zero new STT seam; `main.py:1043` |
| 10 | Honesty on missing config/failure/empty transcript/Ctrl-C | **Holds** — `RecordError`/`SttError` each print+`continue`; `KeyboardInterrupt` prints `Grabación cancelada.`+`continue` (`main.py:1031-1039`) |
| 11 | Operator wrapper with `--check` | **Holds** — `scripts/voice/record_turn.sh --check` exists, exits non-zero with a diagnostic when no recorder is found (re-verified live in this review, see Q6) |
| 12 | `--voice`/`--voice-audio` unchanged, T42 guard unchanged | **Holds** — see Q2, Q6 |
| 13 | Out-unless-★ list | **Holds** — none of wake-word/always-on/barge-in/dual-Enter/`--voice` PTT/`source=VOICE`/LLM/T40/speech-deps-in-pyproject/ACCEPT-claim appear |

**Net: zero lock drift found across all three DC lock sets.** Every numbered lock in T34-DC, T44-DC, and T46-DC still holds on tip `0.7.5`.

---

## Q4 — ACCEPT backlog + recommended order

**Backlog (oldest first, all Cursor PASS WITH NOTES, zero Engineer ACCEPT):**

1. **T41** `B1-assistant-voice-demo-ready` @ `0.7.1`
2. **T42** `B1-assistant-voice-interactive-cli` @ `0.7.2`
3. **T43** `B1-assistant-chat-voice-speak` @ `0.7.3`
4. **T44-inv** (findings-level ★, not a code tag)
5. **T45** `B1-assistant-chat-spoken-continuity` @ `0.7.4`
6. **T47** `B1-assistant-chat-voice-ptt` @ `0.7.5`

**Recommended ACCEPT order (dependency-aware, not a claim):** T41 → T42 → T43 → T45 → T47, in exactly that order, because each one's own review explicitly says the next Buy "must not wait on" the prior's ACCEPT tag (T45's DC: "T45 must not wait on T41/T42/T43 ACCEPT tags"; T46-DC: "T47 must not wait on T41–T45 ACCEPT tags") — meaning they were *built* independently but they still *landed* in this order, so accepting them out of order would leave an earlier-numbered, longer-pending Buy formally un-reviewed while a later one is closed. A single bundled ACCEPT across all six (T41, T42, T43, T45, T47, plus a findings-level nod to T44-inv) is also reasonable given none of them has had a behavior regression found against it in this INV — that choice is the Engineer's, not recommended over the sequential one here, just named as the real alternative.

**Not recommending ACCEPT here** — Q4 is reporting the backlog and an order, never claiming the ACCEPT itself (per this INV's own out-of-scope lock and `CLAUDE.md`'s forbidden-without-approval list).

---

## Q5 — Open review-notes harvest

Every N-numbered note across the T41–T47 review cluster, read directly from each artifact's own "Notes" section:

| Buy | Note | Status |
|---|---|---|
| T41 | N1 — live Piper demo exercised; fixed a Linux `mktemp` bug in `piper_tts.sh` (`a190fb9` + T5b regression test) | **Remediated at the time**, captured as history, no outstanding action |
| T41 | N2 — process note (await ACCEPT) | **Open** — ACCEPT itself (see Q4), not a code defect |
| T42 | N1 — interactive use is keyboard+spoken, not mic; matches IC lock 5 | **Not a defect** — confirms intended design |
| T42 | N2 — process note (await ACCEPT); optional bundling with T41 | **Open** — ACCEPT only |
| T43 | N1 — T42's structural T4 test is a token fence, not a full "no TTS path" proof; stale docstring wording, not a behavior defect | **Still open, cosmetic** — `tests/test_assistant_voice_interactive_cli_b1.py:102-106`'s `test_t4_chat_flag_alone_never_invokes_tts` docstring still reads *"a separate, deliberately untouched entry point"*, unchanged since T43's note was written; re-read live this session. **Optional follow-up**, not a correctness bug |
| T43 | N2 — process note (await ACCEPT) | **Open** — ACCEPT only |
| T44-inv | review's own process note: "No ACCEPT claimed here" | **By design** — findings-level, not code ACCEPT |
| T45 | N1 — `CONTINUITY_DEFER_PHRASES` gained three aliases (`completo`/`estado completo`/`cuentame todo`); documented side-effect, not a defect | **Resolved/documented**, confirmed still true (Q3 above re-verified `FULL_CONTINUITY_PHRASES`) |
| T45 | N2 — T6 doesn't assert package `0.7.4` as a literal string | **Still open, cosmetic** — same pattern repeats in T47 N2 below; neither blocks ★ |
| T45 | N3 — extractor lazy-imports `cli.main._humanize_next_useful_why` to avoid an import cycle | **By design**, re-confirmed present at `spoken_continuity.py:84` |
| T45 | N4 — no session latch; a follow-up `estado` after a `completo` turn is brief again, not full | **By design** (T44-DC lock 6 explicitly requires no latch) — not a defect, optional extra test not added |
| T45 | N5 — small English leak in guide §4.1 ("unless que also pidas") | **Still present** — re-read the current guide (`USER_GUIDE_VOICE.md:113`): `"a menos que also pidas 'completo' otra vez"` — the English word "also" is still there mid-Spanish-sentence. **Confirmed still open**, cosmetic, flagging for T49's guide edits to fix opportunistically since T49 touches the same file |
| T47 | N1 — `tempfile.mkstemp` fd leak | **Remediated** — confirmed on tip (`44cb5fe`): `fd, tmp_name = tempfile.mkstemp(...); os.close(fd)` at `main.py:1025-1026`, `finally: tmp_path.unlink(...)` unchanged |
| T47 | N2 — T7 doesn't assert `0.7.5` as a literal string | **Still open, cosmetic** — same class as T45 N2 |
| T47 | N3 — T1 proves fall-through via Skill egress markers, not a `handle_user_text` spy | **By design**, sufficient for the IC; optional stronger spy not added |
| T47 | N4 — living map line citations for pre-T47 surfaces use older line numbers; new PTT rows are correct | **Pre-existing drift, not introduced by T47** — confirmed: e.g. the map's "Startup banner" row cites `main.py:966-968`; current tip has the banner at `main.py:1000-1002` (shifted down by the PTT block's new imports/lines). **This is a new, small drift found by this INV** — the map's pre-T47 line citations are now stale by ~30-40 lines across the board. Not a behavior defect (the map is documentation, not executable), but worth a cheap fix next time anyone touches that map. |

**New finding from this INV (not in any prior review):** the living map's pre-T47 `main.py` line citations (Table 1, rows before the five new PTT rows) have drifted by roughly 30-40 lines because T47 inserted new imports/lines before them. The five new PTT rows T47 added cite correct current lines (self-consistent at the time T47 landed). This is the same class of drift T47's own N4 already flagged for pre-T47 surfaces — re-confirmed here against the *current* tip, where the drift has grown slightly further. **Recommendation:** fold a full line-citation refresh into the next Buy that already touches `main.py` and the map together, rather than opening a dedicated Buy just for line numbers.

---

## Q6 — Honesty fences still hold?

Each fence re-verified by reading the live symbol/type, not by citing a prior report's claim:

1. **No `"voice"` Authority source.** `src/jarvis/capabilities/safety.py:95`: `AuthoritySource = Literal["radio", "api", "operator"]`. Confirmed by type — adding `"voice"` would be a `mypy`/Pydantic validation failure, not a convention that could silently drift.
2. **T42's `run_chat`-source structural TTS-seam guard.** Re-ran the exact check test T47's own T6 uses:
   ```text
   $ python3 -c "import inspect; from jarvis.adapters.cli.main import run_chat; \
     s = inspect.getsource(run_chat); \
     print([t for t in ('speak_egress','JARVIS_TTS_CMD','_voice_speak_fn','TtsError') if t in s])"
   []
   ```
   Empty list confirmed live, independent of the test suite.
3. **Record/STT/TTS honest-failure paths — no silent success.**
   - `record_audio_file` (`external_record.py:134-150`): raises `RecordProcessError` on non-zero exit, on an unrunnable binary (`OSError`), **and** on a `0` exit with no/empty output file — the "exit 0 but lied" case is explicitly checked (`out.stat().st_size == 0`).
   - `transcribe_audio_file` raises `SttEmptyTranscriptError` on a `0` exit with blank/whitespace-only stdout (re-confirmed at `external_stt.py:92`, read this session).
   - `speak_egress`/`TtsError`: unchanged since T38, not touched by T45/T47.
   - `scripts/voice/record_turn.sh --check`, re-run live in this review with `PATH` stripped:
     ```text
     $ PATH=/nonexistent-review-path ./scripts/voice/record_turn.sh --check
     record_turn.sh: no recorder found (install ffmpeg, or arecord on Linux)
     $ echo $?
     1
     ```
     Confirms non-zero exit and a stderr diagnostic, independently of the T47 test suite.
4. **ESC fence + tip-pin suites, re-run this session:**
   ```text
   $ pytest tests/test_fase_c_esc_pwm_stub_rung_b1.py tests/test_suite_no_tip_version_pins_b1.py -q
   19 passed in 0.35s
   ```
5. **Full suite, re-run this session:** `4026 passed, 9 skipped` — identical to the pre-INV tip count (this INV changed zero `src/` files).
6. **Whole voice test cluster, re-run together this session** (all ten voice test files, not individually as each Buy ran them):
   ```text
   $ pytest tests/test_assistant_voice_intent_ingress_b1.py tests/test_assistant_voice_fixture_loop_b1.py \
            tests/test_assistant_voice_stt_external_b1.py tests/test_assistant_voice_tts_external_b1.py \
            tests/test_assistant_voice_v1_checkpoint_b1.py tests/test_assistant_voice_demo_ready_b1.py \
            tests/test_assistant_voice_interactive_cli_b1.py tests/test_assistant_chat_voice_speak_b1.py \
            tests/test_assistant_chat_spoken_continuity_b1.py tests/test_assistant_chat_voice_ptt_b1.py -q
   63 passed in 22.07s
   ```
   No cross-Buy interference found — every voice Buy's tests still pass when run as one combined cluster, not just in isolation.

**Net: every honesty fence re-checked holds on tip `0.7.5`.** No regression found.

---

## Q7 — Spoken-continuity map currency for `0.7.5`

Read `engineer_note_chat_spoken_continuity_map.md` in full against tip. **Table 1 (chat egress surfaces)** carries all five new T47 PTT rows (Grabando cue, `[voz]` echo, Grabación/STT no disponible, Grabación cancelada), all correctly classified **screen-only** per T46-DC lock 8. **Table 2 (Continuity/startup-context fields)** is unchanged since T45 and still accurately describes the shipped `brief_spoken_continuity` shape (cross-checked field-by-field against `spoken_continuity.py` in Q3 above — all five brief fields match).

**Gap found (same one Q5 flagged):** pre-T47 row line-citations in Table 1 have drifted ~30-40 lines from the PTT block's new imports pushing everything down. This is a citation-accuracy gap, not a missing-row gap — every surface that exists in code has a row; some of those rows now point at the wrong line number. No surface is undocumented.

**Net: the map is content-complete for `0.7.5` (nothing missing), with a cosmetic line-citation drift on older rows** (same finding as Q5, not double-counted as a separate defect — flagged once here for the map specifically).

---

## Q8 — TTS language: Spanish Skills vs old `en_GB` — coordinate with T49

Confirmed by reading `engineer_note_voice_tts_product_brief.md` §1, `docs/USER_GUIDE_VOICE.md` §2/§3/§8, and `scripts/voice/piper_tts.sh`'s header comment, directly:

- **Product brief** (`engineer_note_voice_tts_product_brief.md:14-21`) locks the demo voice as **`en_GB`** (British English), explicitly noting: *"Language of Skills today | Spanish phrases in chat — TTS may speak Spanish text with an `en_GB`-flavored voice or later add `es_ES` voice."* The brief already anticipated this as a future choice, not yet made.
- **Guide §2** (`USER_GUIDE_VOICE.md:42`): *"El brief fija como voz por defecto de demo `en_GB-alan-medium`."*
- **Guide §3 cheatsheet** (`USER_GUIDE_VOICE.md:62`, `296-300`): every example `JARVIS_PIPER_MODEL` path uses `en_GB-alan-medium.onnx`.
- **Guide §8** (`USER_GUIDE_VOICE.md:341`), already self-aware of the mismatch: *"Los Skills responden en español, la voz por defecto es `en_GB`. ... Si molesta, el camino es una voz `es_ES` de Piper — mismo wrapper, solo cambia `JARVIS_PIPER_MODEL`; no hace falta tocar código."*
- **`piper_tts.sh`** itself is already fully **model-agnostic** — `JARVIS_PIPER_MODEL` is a required env var with no hardcoded path in the script body; only the header *comment* (`scripts/voice/piper_tts.sh:7`) shows an `en_GB-alan-medium.onnx` example.

**What this means for T49:** the seam requires **zero `src/jarvis` change** — the mismatch is entirely in **documentation defaults and comment examples**, exactly as T49's own scope note ("Prefer NO `src/jarvis` changes — seam already model-agnostic") anticipates. T49's job is to flip the *example/default* paths in the brief + guide + script comments from `en_GB-alan-medium` to `es_ES-davefx-medium` (default) / `es_ES-sharvard-medium` (alt), and to note the STT-side equivalent (multilingual `ggml-base.bin` over `ggml-base.en.bin` for Spanish `hablar` transcripts) as a guide-only recommendation — `scripts/voice/whisper_stt.sh` likewise takes its model path from an env var, not a hardcode, re-confirmed by reading it (not shown in full here since T49 doesn't need to change it, only the guide text pointing at it).

---

## Q9 — Gaps vs "voz de principio a fin"

A fully coherent, start-to-finish **Spanish** voice product still has these open gaps after T47 + (pending) T49:

1. **Default demo voice is English while every reply is Spanish** — T49 closes this at the *documentation-default* level (Q8). No code gap once T49 lands; the seam already supports it.
2. **Default STT example model is `ggml-base.en.bin`** (`USER_GUIDE_VOICE.md:246`, English-only Whisper model) — for spoken Spanish input via `hablar`/`--voice-audio`, a multilingual model (`ggml-base.bin`) transcribes better. T49's own scope lists this as "guide only," correctly — the seam (`JARVIS_STT_CMD`) is model-agnostic exactly like the TTS seam.
3. **No end-to-end live-mic demo has actually been run and judged by a human ear** for Spanish specifically — T41's own N1 only confirms an `en_GB` live demo was exercised. This INV cannot close that gap (it requires a live mic + human judgment); flagging it as the one thing no amount of code/doc review substitutes for.
4. **The `reasoning`-without-coherence-footer block** (rare path, e.g. `create_project` before any Continuity exists) still speaks-as-printed, dense and multi-part — T44-inv's own Q7 flagged a future IC to speak only the top `PRIORIDAD CRÍTICA` label by default; still not done, still correctly out of scope for both T45 and T47, and out of scope for T48-inv/T49 too (neither touches that code path).
5. **T40 (craft/`world/` voice)** remains the largest actual gap toward "principio a fin," but it is explicitly its own future DC (Q10) — not a T48-inv or T49 gap.

None of these are blocking; they are the honest list of what "voz de principio a fin" still needs beyond what T34–T49 ship.

---

## Q10 — Next-Buy recommendation

**After T48-inv + T49 land:** recommend returning to the **ACCEPT backlog** (Q4) before opening any new voice code Buy — nine Buys deep with zero ACCEPT since `v0.7.0` is a process risk (an un-reviewed-by-Engineer Buy is not the same as a verified-safe one, even when Cursor's PASS WITH NOTES found no blocking defect each time). If the Engineer wants to keep building first, the next genuinely new *product* gap (per Q9) worth its own small DC would be the `reasoning`-without-footer brief extraction — same shape as T45, scoped narrowly, no new architecture.

**T40 stays Parked.** This INV found zero live evidence of `world/` package code, zero craft-voice-UX code, and zero Authority-from-voice code anywhere in the T41–T47 diffs (re-confirmed in Q3's lock audits and by `ls src/jarvis/` showing no `world/` directory). Nothing in this review changes T40's status.

---

## Q11 — Connect-plugs wording

Read `engineer_note_connect_plugs_real_data_map.md` rows `voice-intent-ingress`, `a4-voice-world`, `go-to-metadata-plug-for-world`, `world-package` directly.

- `voice-intent-ingress`: **★ CLOSED** @ `v0.6.43` — accurate, matches Q1.
- `a4-voice-world`: *"Voice half ★ complete @ v0.7.0; world deferred (T40)"* — still accurate. T44–T47 (spoken-continuity egress + PTT ingress) both landed entirely **inside** this already-★-closed voice-half surface (confirmed by Q3's lock audits: neither T44-DC nor T46-DC reopened T34-DC, both say so explicitly in their own "Later... does not reopen this DC" notes on T34-DC itself). **No wording fix needed** — the row correctly does not mention T44–T47 by number, since it never needed a new row for them (T44-inv's own Q11 already made this same call, re-confirmed here against the now-landed T45+T47 code, not just the T44-inv plan).
- `go-to-metadata-plug-for-world` / `world-package`: unchanged, untouched by any voice Buy since T34-inv, still correctly **OPEN shaped**/**Parked**.

**Net: no wording fix needed anywhere in the connect-plugs map.** This INV's own Q11 answer confirms T44-inv's prediction held true once the code actually landed.

---

## Q12 — Cola / PRIORIDAD / state

- **PRIORIDAD after this INV:** "T48-inv Implemented (Claude Code) — await Cursor review → Engineer ★ on findings. T49 (Spanish TTS default) lands next in the same session, coordinating with this INV's Q8 answer."
- **Cola row:** add **T48-inv** between T47 and T40 in `engineer_note_voice_phase_c_cola.md`'s table, Estado = "Implemented · await Cursor review," linking this report.
- **`engineering_state.json`:** `execution_status: "implemented_awaiting_cursor_review"`, `active_operation.ids: ["T48-inv", "INV-assistant-voice-phase-t-review"]`, `required_artifacts` pointing at this INV contract + report, `closed_this_turn: ["T48-inv forensic review complete"]`.
- **No ACCEPT claimed** for T48-inv itself, nor for any of the nine backlogged Buys named in Q4.

---

## Forensic method — what was actually re-run

1. Opened every cola-row artifact directly off disk for Q1 (not the cola table's own summary).
2. Read `main.py`'s argparse block and every `run_voice_*`/`run_chat` function signature live for Q2.
3. Walked all three DC files' numbered locks one-by-one against the corresponding tip symbol/line for Q3 — 33 locks total (10 + 10 + 13), zero drift found.
4. Re-ran, live, in this session: full suite (`4026 passed, 9 skipped`), ESC-fence + tip-pin suites (`19 passed`), the full ten-file voice test cluster together (`63 passed`), the `inspect.getsource` zero-reference check, and `record_turn.sh --check` with a stripped `PATH`.
5. Grepped `AuthoritySource`, `CONTINUITY_DEFER_PHRASES`, `FULL_CONTINUITY_PHRASES`, `PTT_TRIGGER_PHRASES` directly rather than citing prior prose.
6. Checked `git tag -l` to verify which "ACCEPT CLOSED @ v0.x" claims in artifact prose are backed by an actual git tag (only `v0.7.0` is).

No `src/` file was modified. No test file was modified. `pyproject.toml` stays `0.7.5` for this INV.
