# Design Contract — STT phrase-match punctuation honesty (`DC-assistant-voice-stt-phrase-punctuation`)

**Project:** Jarvis  
**Date:** 2026-10-14  
**Author:** JES / Cursor  
**Status:** **DC ready** — next after T54 reviewed @ `0.8.1`. Engineer “siguiente ic” → this DC + T55 IC.  
**Type:** Block lock — **V11** polish on Continuity / FULL phrase match under STT  
**Cola:** **V11-DC** / **T55-DC**  
**Parents:** [T53 review ★](implementation_review_assistant_voice_only_loop_b1.md) (N2) · [T54 review](implementation_review_assistant_voice_silence_cut_b1.md) · [V10-DC](design_contract_assistant_voice_silence_cut_b0.md) · [cola voz](engineer_note_voice_phase_c_cola.md) · tip package **`0.8.1`**

**Not** an Implementation Contract. **Not** wake-word · barge-in / anti-echo · T40 · silence-cut redo · speech SDK.

---

## Intent

Voice-only exit already ignores trailing STT punctuation (`Salir.` → exit). Continuity defer + FULL phrase match do **not**: whisper often emits `Completo.` / `Estado.` → exact-match fails → brief spoken (or no Continuity wall) that turn.

T53 review **N2** deferred this out of V9/V10. V10-DC lock 11 named it explicitly **Out of V10**. This DC locks the fix so T55 stays a **normalize honesty** Buy — same phrase tables, same Layer 1/2 payloads, no new phrases.

---

## Plan

| Step | Cola | Buy | Package | Scope |
|---|---|---|---|---|
| **This DC** | **T55-DC** | `DC-assistant-voice-stt-phrase-punctuation` | no bump | Locks below |
| Code | **T55** | `B1-assistant-voice-stt-phrase-punctuation` | **`0.8.2` / `v0.8.2`** | Trailing-punct strip on Continuity/FULL normalize; optional dead PTT export cleanup |
| Later | own IC | anti-echo / barge-in / cancel / hotkey (INV “V11+”) | TBD | **Out** — renumbered **V12+** |
| Parked | **T40** | craft/`world` | TBD | **Out** |

---

## Product picture (after V11 ★)

```text
STT transcript "Completo." / "Estado." / "Dame detalles."
  → same Continuity defer + FULL match as typed "completo" / "estado" / "dame detalles"
  → Layer 1 print unchanged
  → Layer 2 brief or full_spoken_continuity unchanged payloads
```

Two modes unchanged. Silence cut (T54) unchanged.

---

## Locks (block-level)

| # | Lock |
|---|---|
| 1 | **Scope = phrase-match normalize only** — do not change Continuity field ranking, brief/FULL extractors, STT/TTS seams, record silence cut, or session brain |
| 2 | **Trailing punctuation** — after the existing strip + casefold + NFKD accent-strip, also strip a finite trailing set aligned with voice-only exit: at least `.,;:!?¡¿` (IC may share one helper or duplicate the tiny strip — prefer one shared private helper inside each module that already owns a `_normalize`, **or** a single shared helper if the DC/IC fence allows without new architecture). Exact phrase tables stay the same finite locked sets |
| 3 | **Where it applies** — (a) `is_full_continuity_request` / `spoken_continuity._normalize`; (b) **`assistant_task._normalize_for_continuity_match` itself** (one function, one strip). That helper is shared by Continuity defer **and** every Skill-first matcher that already calls it (ARM / DISARM / HOLD / LAND / GO_TO / FOLLOW / PATROL / CHARGE / …, including `parse_go_to_destination`). **Explicit widening:** STT `Armar.` / `Hold!` / `Go to 1 2.` match the same locked phrase tables as typed text. Do **not** fork a Continuity-only normalize. Typed `--chat` gets the same forgiveness (harmless) |
| 4 | **Not fuzzy** — still exact match after normalize. No substring, no edit-distance, no LLM. Mid-string punctuation is not a goal (exact full-string phrases only). **No new phrases** — tables unchanged; only trailing punct strip |
| 5 | **Exit words** — already punct-tolerant in `_is_voice_only_exit`; do not regress. Prefer keeping that path; optional align to the same strip set |
| 6 | **Dead PTT hygiene (T53 N1)** — **in scope if tested**: remove unused `is_ptt_trigger` / `PTT_TRIGGER_PHRASES` from product exports (and implementation if nothing else imports them). Hybrid PTT is retired; do not resurrect `hablar` intercept. If removal forces large test churn outside voice, leave helpers private/unexported with a one-line “retired” note — IC picks the smaller honest path |
| 7 | **Guide** — one honesty line: STT trailing punctuation on Continuity/FULL **and** locked Skill-first phrases is ignored (same idea as `salir.`) |
| 8 | **Package** — **`0.8.2` / `v0.8.2`**. No tip pins in tests. No new C-xxx. No speech deps |
| 9 | **Out of V11** — wake-word · always-on · barge-in / anti-echo while TTS plays · cancel-hotkey · T40 · silence-cut redo · expanding FULL/CONTINUITY phrase tables · ACCEPT claim |

---

## Opens

T55 IC: [`implementation_contract_assistant_voice_stt_phrase_punctuation_b1.md`](implementation_contract_assistant_voice_stt_phrase_punctuation_b1.md).

**Process:** Engineer ★ ACCEPT T54 → tag **`v0.8.1`** when ready (review already PASS WITH NOTES). T55 may paste after that tag, or on package tip `0.8.1` with parent note — IC opens **`0.8.2`**.

SoT: [cola](engineer_note_voice_phase_c_cola.md) · [`docs/IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md) PRIORIDAD
