# Engineer note — Voice product brief (TTS / “JARVIS-like”)

**Date:** 2026-10-03 · **updated:** 2026-10-05 (T49 — default voice flips to Spanish)  
**Status:** **OPEN living product brief** — not an IC; not permission to pick a vendor SDK in core  
**Tip parent:** voice cola @ **`v0.7.6`** (T49 ★) · stack T41–T49 ★ ACCEPT CLOSED · default demo voice **Spanish `es_ES-davefx-medium`** · guide: [`docs/USER_GUIDE_VOICE.md`](../../docs/USER_GUIDE_VOICE.md)  
**Parents:** [voice DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [cola note](engineer_note_voice_phase_c_cola.md) · [T48-inv Q8](investigation_report_assistant_voice_phase_t_review_b0.md)

**Purpose:** Lock the *desired voice character* and the **cheapest / free-first** path to get there, without blocking T37–T38 technical seams. Marvel “JARVIS exact voice” is **out** (license). Target = **JARVIS-like**, not a film clone.

---

## 1. Voice brief (locked for demos — **updated T49, `0.7.6`**)

| Trait | Choice |
|---|---|
| Accent | **Spanish** (`es_ES`) — **default**, flipped from `en_GB` by T49 once T48-inv Q8 confirmed every Skill/Continuity reply is Spanish prose |
| Register | **Grave / deeper male** — unchanged |
| Delivery | **Short** — Skill-first lines already are; no long narration — unchanged |
| Style | **Sin teatro** — calm, dry, assistant; no cinematic swell — unchanged |
| Default voice | **`es_ES-davefx-medium`** — Spanish voice reading Spanish text, closing the mismatch the brief itself used to accept as a first-demo compromise |
| Alt voice | **`es_ES-sharvard-medium`** — try before considering any paid/cloud voice |
| Legacy / optional | **`en_GB-alan-medium`** — the original demo default (T38/T41), still documented and fully supported via the same `JARVIS_PIPER_MODEL` env var; no longer the default |
| Explicitly out | Cloning Paul Bettany / Marvel JARVIS · tip-pinning a cloud SDK in `pyproject` · Authority-from-voice |

---

## 2. Cost ladder (prefer free)

| Priority | Path | \$ | Quality vs brief | How it plugs (T38) |
|---|---|---|---|---|
| **P0 — default** | **Piper local** — free ONNX voices, CPU, offline | **\$0** (disk + CPU) | Good enough for v1 demos; try `es_ES-davefx-medium` (default, T49), `es_ES-sharvard-medium` (alt); `en_GB-alan-medium` stays available as legacy | `JARVIS_TTS_CMD` (or equiv.) → wav/play |
| P1 | OS TTS already on machine (`say`, `espeak-ng`, Windows SAPI) | \$0 | Often thinner / more robotic | same external cmd seam |
| P2 | Cloud free tier (Azure/Google/ElevenLabs trial) | \$0 then pay-as-you-go | Often richer | HTTP wrapper behind same seam |
| P3 | Paid neural / custom voice | \$\$ | Closest to “cinematic” without illegal clone | only if P0 fails the brief |

**Recommendation:** ship against **Piper P0**. Default demo voice is Spanish `es_ES-davefx-medium` (T49 ★); A/B `sharvard` before cloud. `en_GB-alan-medium` remains legacy optional.

**Download note (Piper):** yes — one small voice model file (~tens of MB) **outside the Jarvis package**, not a tip-pinned dep in core. Engine + voice stay **external** (same discipline as T37 STT).

---

## 3. Phasing vs code cola

| When | What |
|---|---|
| **Now / T37** | STT **process** seam (fake script in tests). No voice model required for CI |
| **T38** | TTS **process** seam: `render_response` text → external cmd → speaker/file. Default demo cmd = Piper + chosen `en_GB` voice |
| **Vendor ★ (optional)** | Only if we leave Piper for a paid/cloud voice — separate Engineer decision |
| **T39** | Product milestone `v0.7.0` — speak → Skills → spoken reply (fixture or real I/O) |

Do **not** put Piper/whisper wheels into `pyproject.toml` in T37/T38 core Buys unless a later ★ explicitly says so.

---

## 4. Demo checklist (cheap path)

1. Install Piper **outside** the repo (or user-local venv).  
2. Download one `es_ES` male voice (default, T49: **davefx-medium**).  
3. Wrapper script: stdin or argv text → `piper` → play / write wav.  
4. Point T38 env (e.g. `JARVIS_TTS_CMD`) at that script.  
5. Run a Skill turn (`hold` / `estado`) and listen: grave? short? no theater?  
6. If thin: try `sharvard-medium` before paying for cloud. `en_GB-alan-medium` remains documented as the legacy/original demo voice.

> **Steps 1–5 are now a written guide, not an exercise** — T41
> (`B1-assistant-voice-demo-ready`, Implemented @ `0.7.1`, pending review)
> ships [`docs/USER_GUIDE_VOICE.md`](../../docs/USER_GUIDE_VOICE.md) with
> copy-paste commands, plus `scripts/voice/piper_tts.sh` (step 3, with a
> `--check` config probe) and `scripts/voice/fixtures/demo_skills.txt`
> (step 5). Step 6 is still an **open listening call for the Engineer** —
> nobody has judged `alan-medium` against "grave / corto / sin teatro" yet,
> because that needs a real Piper install and a pair of ears, not code.

---

## 5. Maintenance

Update this note when Engineer picks a voice file name or rejects P0. Point from [cola note](engineer_note_voice_phase_c_cola.md). No connect-plugs CLOSED rows from this brief alone.
