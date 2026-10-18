# Implementation Report — Assistant voice demo ready (`B1-assistant-voice-demo-ready`, T41)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Implementer:** Claude Code (Engineer paste)  
**Contract:** [`implementation_contract_assistant_voice_demo_ready_b1.md`](implementation_contract_assistant_voice_demo_ready_b1.md)  
**Parents:** [T39 ★ ACCEPT CLOSED](implementation_review_assistant_voice_v1_checkpoint_b1.md) @ `v0.7.0` · [TTS product brief](engineer_note_voice_tts_product_brief.md) · [cola note](engineer_note_voice_phase_c_cola.md) · [DC voice/channels ★](design_contract_assistant_chat_voice_channels_b0.md)  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.7.1` / pending **`v0.7.1`**.

---

## 1. What landed

**Zero `src/` change** — confirmed via `git status` before committing: the only changes are `pyproject.toml`'s version bump, three new files under `scripts/voice/`, one new guide, one new test file, and docs.

| Area | Change |
|---|---|
| `docs/USER_GUIDE_VOICE.md` | **new** operator guide, in `USER_GUIDE_EXPLAIN.md`'s style (Spanish, copy-paste commands, honesty section, cheatsheet, known limits). §1 qué es / qué no es · §2 install Piper **outside** the package (+ the `.onnx.json` gotcha) · §3 env + `--check` · §4 first spoken demo · §5 optional mic→STT · §6 honesty · §7 one-page cheatsheet · §8 known limits |
| `scripts/voice/piper_tts.sh` | **new** TTS wrapper. Egress text on **stdin** → Piper → play (autodetect `afplay`/`aplay`/`paplay`) or write wav via `JARVIS_VOICE_WAV_OUT`. Env: `JARVIS_PIPER_MODEL` (required), `JARVIS_PIPER_BIN`, `JARVIS_PIPER_ARGS`, `JARVIS_VOICE_WAV_OUT`, `JARVIS_VOICE_PLAYER`. `--check` is a config probe that speaks nothing. Every missing piece — unset model, absent model file, absent Piper binary, Piper non-zero exit, Piper exit-0-but-no-audio, no wav player, empty stdin — exits **non-zero** with a message on stderr |
| `scripts/voice/whisper_stt.sh` | **new** STT helper. Audio path argument → **bare transcript on stdout** (whitespace collapsed; engine noise forced to stderr), which is exactly what T37's `JARVIS_STT_CMD` seam reads. Env: `JARVIS_WHISPER_MODEL` (required), `JARVIS_WHISPER_BIN`, `JARVIS_WHISPER_ARGS`; `--check` probe. Empty transcript is a non-zero failure, never an empty "success" |
| `scripts/voice/fixtures/demo_skills.txt` | **new** 8-line demo fixture: `estado`, `explain c-rate-de-bateria`, `armar`, `hold`, `go to 1.0 2.0`, `land`, `desarmar`, `charge` — `armar` deliberately before the flight verbs so the demo shows the richer `allow`/`not_implemented` + sim-tick path |
| `tests/test_assistant_voice_demo_ready_b1.py` | **new** T1–T5 (8 test functions) |
| `pyproject.toml` | `0.7.0` → **`0.7.1`** — **no** new dependency |
| Docs / cola / brief / state | PRIORIDAD (+ T41 row, A4 row) · PLATFORM · CONNECTIONS (no new C-xxx) · ARCHITECTURE tip line · cola note T41 row + tip parent · TTS brief tip parent + demo-checklist pointer · `engineering_state.json` |

**Not touched:** every file under `src/jarvis/` (including all four `adapters/voice/*.py`, `adapters/cli/main.py`, and `core/orchestrator.py`), `render_response`, `run_skill`, any `_handle_*` fulfill, `pyproject.toml`'s dependency lists (no `piper`/`whisper`/`vosk`/… — asserted by T4), tip-version pins (T17 guardrail green), ESC fence (T16, re-verified on orchestrator + all voice adapters), `AuthoritySource` (still no `"voice"`).

---

## 2. What I verified, and what stays operator-verified

**This environment has no Piper and no whisper installed, and no audio device** — so the honest split is:

**Verified here, end to end, with real commands:**

- The guide's headline command works: `python -m jarvis.main --voice-fixture scripts/voice/fixtures/demo_skills.txt --voice-speak` with `JARVIS_TTS_CMD` pointed at `piper_tts.sh` drove **8 fixture lines → 8 Skill turns → 8 texts handed to the synthesizer → 8 wav plays**, against a **stub `piper`** that mimics Piper 1.x's `--model`/`--output_file` CLI.
- The combined path works: `--voice-audio <wav> --voice-speak` with both wrappers wired ran audio → `whisper_stt.sh` → `"hold"` → Skill-first brain → honest `reject`/`disarmed` → `piper_tts.sh` → wav → played.
- Text with spaces and double quotes arrives on the synthesizer's stdin **byte-identical** (the reason the wrapper takes text on stdin rather than argv).
- Every failure path exits non-zero with a clear stderr message: unset/absent model, absent binary, non-zero engine exit, engine exit-0-with-no-audio, no player, empty stdin, missing audio arg, absent audio file, empty transcript.
- `--check` on both wrappers reports readiness (exit 0) or exactly what is missing (exit 1) without speaking or transcribing.
- Three factual claims in the guide were checked against real behavior before publishing: the quoted `hold` output matches the real command byte-for-byte; the `armar` latch does **not** persist across `--voice-audio` invocations (each builds a fresh orchestrator — `adapters/cli/main.py:1038`) but **does** persist across `--voice-fixture` lines (one orchestrator, looped); blank fixture lines are ignored.

**Explicitly NOT verified here — operator-verified by design:**

- **The real Piper happy path.** The wrapper calls `piper --model M --output_file W`, the Piper 1.x form. A build with different flag names would surface as a clear Piper error on stderr with a non-zero exit (not a silent failure), and `JARVIS_PIPER_ARGS` exists as the escape hatch — but *no real Piper binary was exercised*. The guide's §8 says this plainly rather than implying a tested integration.
- **The real whisper.cpp happy path**, same reasoning (`-m/-f/-nt` is the whisper.cpp form).
- **Audio actually coming out of a speaker**, and therefore **the voice character itself**. The brief's step 6 — does `en_GB-alan-medium` sound *grave / corto / sin teatro*? — is still an open listening call for the Engineer; I added that explicitly to the brief's demo checklist rather than letting a shipped wrapper imply the timbre was signed off.
- **Mic capture.** The `ffmpeg`/`arecord` one-liners in §5.3 are standard invocations documented for the operator; no microphone was recorded from. They are deliberately *outside* `adapters/voice/` per IC lock 6.

---

## 3. A test bug caught and fixed (not a product issue)

My first draft of T5 passed a **nonexistent** audio path while asserting the wrapper would complain about the missing `JARVIS_WHISPER_MODEL`. The script correctly complained about the missing *audio file* first — validating the argument it was just handed before inspecting the environment. The script's order is the sensible one, so I fixed the **test** (now it asserts both orderings explicitly: absent audio → "audio file not found"; present audio + unset model → `JARVIS_WHISPER_MODEL`) rather than reshuffling working code to match a wrong expectation.

Separately, and consistent with T39: T4 deliberately does **not** assert the literal bumped version string, because `assert 'version = "0.7.1"' in text` is itself one of T17's forbidden tip-pin regex shapes. T4 asserts the no-speech-deps half and leaves the version to `pyproject.toml` + the git tag.

---

## 4. Tests executed

```text
pytest tests/test_assistant_voice_demo_ready_b1.py -q
→ 8 passed

pytest tests/test_fase_c_esc_pwm_stub_rung_b1.py tests/test_suite_no_tip_version_pins_b1.py \
       tests/test_fase_c_radio_dual_role_b1.py tests/test_connect_plugs_real_data_map_b1.py -q
→ 39 passed (T16 ESC fence + T17 tip-pin guardrail + radio fence + connect-plugs map all green)

pytest tests/ -q
→ 3999 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T41 tip (stash push/pop): baseline was `3991 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 8 new T41 tests passing.

The tests never require Piper, whisper, a voice model, or a speaker: the honesty paths are asserted directly, and the happy-path plumbing runs against stub binaries created in `tmp_path`. `_run_wrapper` also strips every `JARVIS_*` voice variable from the child environment, so an operator's real config can never make these tests pass or fail spuriously.

---

## 5. Remaining

None for this Buy. Two follow-ups belong to the Engineer, not to code:

1. **The listening call** (brief §4 step 6): install Piper, run the demo fixture, and judge `en_GB-alan-medium` against *grave / corto / sin teatro* — escalating to `en_GB-northern_english_male-medium` before anything paid. The brief now records this as explicitly open.
2. **`estado` reads long aloud** (guide §8): the full Continuity block has separators and bullets that sound dense spoken. The other eleven Skills are one or two sentences and read well. A voice-tuned renderer would be its own Buy — this one deliberately reuses `render_response` unchanged.

**T40** (craft/`world` voice) remains the only Parked item in the voice phase C cola, with its own future DC.
