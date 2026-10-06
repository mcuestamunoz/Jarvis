# Implementation Report — Voice FULL Continuity narrated (`B1-assistant-voice-full-spoken`, T52)

**Project:** Jarvis
**Date:** 2026-10-06
**Implementer:** Claude Code (Engineer paste)
**Contract:** [IC](implementation_contract_assistant_voice_full_spoken_b1.md) · [T52-DC](design_contract_assistant_voice_full_spoken_b0.md)
**Parents:** [FN-017](engineer_note_voice_spoken_polish_field_fn017.md) · [T51 ★](implementation_review_assistant_voice_brief_spanish_b1.md) @ `v0.7.8` · [T45 ★](implementation_review_assistant_chat_spoken_continuity_b1.md)
**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-06) · tip **`v0.7.9`**.
**Package:** `0.7.8` → **`0.7.9` / `v0.7.9`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/adapters/voice/spoken_continuity.py` | New `full_spoken_continuity(ctx)` = `brief_spoken_continuity(ctx)` (unchanged) + body, each section omitted when empty: **A** `Evidencia:` + `continuity.evidence[:6]` · **B** `Huecos prioritarios:` + `prioritized_gaps[:3]` → T51 title map + `Siguiente: <action>` (never `gap_id`/`depends_on`/`severity`/`blocks`) · **C** `Arquitectura {progress}. Siguiente bloque: {label}[ en progreso]` (DC template verbatim) or `Arquitectura {progress}. Completa.` · **D** `Requisitos físicos:` + `physical_requirements_lines` · **E** `Bloque propulsión y energía: cerrado.` / `no cerrado.`. `spoken_text_for_wall` returns `full_spoken_continuity(ctx)` on a FULL phrase — `printed_wall` stays in the signature (so `run_chat` call sites are untouched) but is never spoken. |
| `src/jarvis/adapters/voice/__init__.py` | export `full_spoken_continuity` |
| `tests/test_assistant_voice_full_spoken_b1.py` | **new** T1–T7, one function per IC §2 row: T1 brief head + Spanish status, no `PROJECT STATUS`/`ASSEMBLY READY`, A–E order · T2 Evidencia ≤6 / header omitted when empty / brief-only when A–E empty · T3 `Autonomy target not met` mapped, unknown raw, no `GAP-`, `Siguiente:` · T4 FULL ≠ printed wall, `estado` == brief · T5 screen-only fence (BOM, subsystem `PASS` row, Conceptos, prop detail, rule glyphs) + real renderers still print them · T6 architecture/closure templates · T7 end-to-end `run_chat` `completo` + tip-pin/ESC/deps/`run_chat` TTS guard/guide/map |
| `tests/test_assistant_chat_spoken_continuity_b1.py` | **updated** T3/T3b (asserted FULL == printed wall) — see §2 |
| `pyproject.toml` | `0.7.9` — no new dependency |
| `docs/USER_GUIDE_VOICE.md` | §4.1 FULL bullet, PTT example comment, §8 two bullets |
| `.jes/artifacts/engineer_note_chat_spoken_continuity_map.md` | tip line, legend, extractor line, Table 2 reclassification, new "FULL spoken shape" section |
| `docs/PLATFORM_CAPABILITY_VISION.md` · `docs/system_map/CONNECTIONS.md` | new T52 paragraphs |
| FN-017 · voice cola · `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD/cola · `.jes/state/engineering_state.json` | T52 → Implemented, await Cursor review |

**Not touched:** `run_chat` / every `render_*` / `_render_readiness_block` / `engineering_readiness` / `speak_sanitize` / orchestrator. No LLM.

**Screen-only even on FULL** (map reclassified from speak-on-request → screen-only): `component_bom_lines`, `readiness.subsystems`, `explain_topics` (Conceptos), `propulsion_resolution`, `motor_operating_point_electrical`, `hover_energy`, `battery_endurance.envelope`; English `PROJECT STATUS` line.

## 2. Pre-existing tests updated (intentional)

`test_assistant_chat_spoken_continuity_b1.py::test_t3_*` / `test_t3b_*` asserted the FULL capture contained `ENGINEERING READINESS`/`TOP GAPS` (FULL == printed wall). Renamed and updated to assert exactly one capture carries `Huecos prioritarios` and no capture carries `ENGINEERING READINESS`/`TOP GAPS`. Module docstring updated accordingly.

## 3. Tests executed

```text
pytest tests/test_assistant_voice_full_spoken_b1.py tests/test_assistant_chat_spoken_continuity_b1.py \
       tests/test_assistant_voice_brief_spanish_b1.py tests/test_assistant_voice_speak_sanitize_b1.py -q
→ 29 passed

pytest -q
→ 4052 passed, 9 skipped, 0 failed   (baseline T51: 4045 passed → +7 new)
```

## 4. Remaining risks

- Section B action map and Continuity why-code humanize landed as post-review hygiene (T52-N1/N2) on the same tip before ACCEPT.
- IC T7 says "`0.7.9`": `pyproject` is `0.7.9`, but T7 does not pin the version in-test — suite tip-pin policy (`test_no_pyproject_tip_version_pins_in_suite`) is run instead, same as T51's T6.
