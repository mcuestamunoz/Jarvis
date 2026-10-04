# Implementation Contract — Chat spoken continuity (`B1-assistant-chat-spoken-continuity`)

**Project:** Jarvis  
**Date:** 2026-10-04  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code**  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.7.4`**

**Status:** **IC ready for Claude** (Engineer paste = Buy).  
**Parents:** [T44-DC](design_contract_assistant_chat_spoken_continuity_b0.md) · [T44-inv review](investigation_review_assistant_chat_spoken_continuity_b0.md) · [living map](engineer_note_chat_spoken_continuity_map.md) · [T43](implementation_review_assistant_chat_voice_speak_b1.md) @ `0.7.3` · [USER_GUIDE_VOICE](../../docs/USER_GUIDE_VOICE.md)  
**Type:** Layer 2 extractor on `--chat --voice-speak` **Continuity walls** — print stays full truth; speak becomes brief unless a FULL phrase is used.  
**Opens:** **`0.7.4` / `v0.7.4`**. **Cola:** **T45**

**Not:** LLM summary · changing `render_startup_context` output · recorting screen · T40 · wake-word · `--voice` rewrite · ACCEPT claim · making bare `--chat` speak.

---

## Why this Buy

Engineer heard the Continuity wall on `--chat --voice-speak` (project load / `estado`) and locked: **truth on screen, spoken continuity above**. T44-inv mapped fields; T44-DC locked the plan. This IC implements **slice 1**: walls only.

---

## 0. Engineer Buy (locked from T44-DC)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-spoken-continuity`** — deterministic spoken extract for Continuity walls |
| 2 | **Print unchanged** — `render_startup_context` / `render_response` / `_say` prints stay the full wall. Do **not** shorten Layer 1 |
| 3 | **Speak path only** — when `speak_tts=True`, Continuity-shaped walls speak `brief_spoken_continuity(ctx)` instead of the printed block. Empty brief → skip speak (print still happens) |
| 4 | **Walls =** (a) project-load `startup_block` + `startup_ctx`, (b) turns whose result `action == "project_status"` (including `CONTINUITY_DEFER_PHRASES` / `estado`). All other `_say` surfaces stay speak-as-printed (Skills, errors, help, exit, define-wizard, craft bodies) |
| 5 | **Brief fields (order):** `situation` · `next_useful_step` · humanized `next_useful_why` (reuse wall helper; move it next to the extractor if `cli.main` import would cycle) · `PROJECT STATUS: {ASSEMBLY READY\|NOT ASSEMBLY READY}` from `readiness.overall` · top gap **title** only. Join with newlines; omit missing |
| 6 | **FULL this turn** — if the user line matches the locked FULL set (after the same normalize as Continuity defer): speak the **printed** wall this turn (today’s T43 behavior). Set does **not** persist. FULL phrases: `completo`, `estado completo`, `dame detalles`, `dame detalles del proyecto`, `detalles del proyecto`, `cuentame todo`, `cuentame el proyecto`, `cuenta el proyecto`, `describe el proyecto`, `explica el proyecto` |
| 7 | **Extractor** — new pure function in `src/jarvis/adapters/voice/spoken_continuity.py` (name flexible). No orch ranking change. Do not reuse `_voice_speak_fn` (double-print) |
| 8 | **Guide + map** — `USER_GUIDE_VOICE.md`: `--chat --voice-speak` now hears the brief by default; `dame detalles` / `completo` reads the wall. Update living map classes + Continuity return citation `:676-682`. PRIORIDAD · cola · short PLATFORM/CONNECTIONS (**no new C-xxx**) |
| 9 | **Version** `pyproject` → **`0.7.4`** — no speech deps |
| 10 | **Tests T1–T6** — fake TTS + isolated workspace. Out: LLM · T40 · ACCEPT claim · changing `--voice` |

---

## 1. Files

| Path | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | **new** `brief_spoken_continuity(ctx) -> str` + FULL phrase helper if kept here |
| `src/jarvis/adapters/voice/__init__.py` | export the extractor (thin) |
| `src/jarvis/adapters/cli/main.py` | load + `project_status` speak brief vs full; print untouched |
| `src/jarvis/config.py` or voice module | FULL phrase frozenset (do not steal non-FULL `CONTINUITY_DEFER_PHRASES` into full) |
| `docs/USER_GUIDE_VOICE.md` | honesty: brief default; full on request |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | shipped classes + N1 citation fix |
| `tests/test_assistant_chat_spoken_continuity_b1.py` | **new** T1–T6 |
| `pyproject.toml` | `0.7.3` → **`0.7.4`** |
| Docs / cola / state | T45 Implemented await review |

Prefer not touching `project_continuity.py` / `orchestrator.py` ranking.

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | `brief_spoken_continuity` on a fat fake ctx (situation, next, why, readiness table + BOM-like fields present) → string contains situation/next/status; **does not** contain `ENGINEERING READINESS` / `Componentes / gaps` / `Evidencia:` |
| T2 | `run_chat(speak_tts=True)` path that would speak a wall: **capsys still has the full wall**; fake TTS stdin is the **brief** (no `ENGINEERING READINESS`) |
| T3 | User line in FULL set (e.g. `dame detalles` or `completo`) with speak on → fake TTS receives wall markers (`ENGINEERING READINESS` or `Componentes`) **and** print still full |
| T4 | Short Skill (`armar`) still speak-as-printed (fake TTS contains `vehicle_arm_policy` / `ARMADA`); `speak_tts=False` never invokes TTS |
| T5 | Missing TTS: honest `TTS no disponible`; loop survives |
| T6 | `0.7.4` · no speech deps · tip-pin + ESC green · guide mentions brief vs `completo`/`dame detalles` · map file still present |

If a full `run_chat` wall is hard without a seeded project, T2 may combine a unit-level speak-path helper test **plus** monkeypatch of `build_startup_context` / the speak wrapper — but T2 must prove **print ≠ speak** on a wall, not only the pure function.

---

## 3. Acceptance

- [ ] `--chat --voice-speak` load/`estado`: screen full, ears brief  
- [ ] `dame detalles` / `completo`: ears = wall that turn  
- [ ] Bare `--chat` silent · `--voice` unchanged · `0.7.4` · map + guide updated  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.7.4`**

---

## 4. Paste for Claude

```text
Implementation — B1-assistant-chat-spoken-continuity (T45)
Parent: T44-DC + T43 @ 0.7.3. Package → 0.7.4.

IC: .jes/artifacts/implementation_contract_assistant_chat_spoken_continuity_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_spoken_continuity_b0.md
Map: .jes/artifacts/engineer_note_chat_spoken_continuity_map.md
Guide: docs/USER_GUIDE_VOICE.md

Two layers, NO LLM:
- Layer 1 TRUTH = print full Continuity (DO NOT change render_startup_context
  / render_response output)
- Layer 2 = speak brief extract on Continuity WALLS only
  (project load + action==project_status / estado)
- Other turns stay speak-as-printed
- Brief fields: situation, next_useful_step, humanized next_useful_why,
  PROJECT STATUS from readiness.overall, top gap title only
- FULL this turn (finite phrases, same normalize as Continuity defer):
  completo, estado completo, dame detalles, dame detalles del proyecto,
  detalles del proyecto, cuentame todo, cuentame el proyecto,
  cuenta el proyecto, describe el proyecto, explica el proyecto
  → speak the printed wall that turn only (no session latch)
- New adapters/voice/spoken_continuity.py pure function
- Tests T1–T6: print still wall + TTS brief; FULL phrase TTS is wall;
  Skill speak-as-printed; bare chat silent; 0.7.4; no speech deps
- Update guide + living map (fix Continuity return cite 676-682)
NO ACCEPT claim · NOT LLM · NOT T40 · NOT recort screen · NOT --voice rewrite
```
