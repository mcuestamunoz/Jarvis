# Engineer note — Voice product brief (TTS / “JARVIS-like”)

**Date:** 2026-10-03  
**Status:** **OPEN living product brief** — not an IC; not permission to pick a vendor SDK in core  
**Tip parent:** voice cola @ **`v0.7.0`** (T39 ★) · T41 operator path Implemented @ **`0.7.1`** (pending review) — the wrapper this brief asked for now ships: [`docs/USER_GUIDE_VOICE.md`](../../docs/USER_GUIDE_VOICE.md) + `scripts/voice/`  
**Parents:** [voice DC ★](design_contract_assistant_chat_voice_channels_b0.md) · [cola note](engineer_note_voice_phase_c_cola.md)

**Purpose:** Lock the *desired voice character* and the **cheapest / free-first** path to get there, without blocking T37–T38 technical seams. Marvel “JARVIS exact voice” is **out** (license). Target = **JARVIS-like**, not a film clone.

---

## 1. Voice brief (locked for demos)

| Trait | Choice |
|---|---|
| Accent | **British English** (`en_GB`) |
| Register | **Grave / deeper male** |
| Delivery | **Short** — Skill-first lines already are; no long narration |
| Style | **Sin teatro** — calm, dry, assistant; no cinematic swell |
| Language of Skills today | Spanish phrases in chat — TTS may speak Spanish text with an `en_GB`-flavored voice **or** later add `es_ES` voice; first demos can use English status lines / accept accented Spanish |
| Explicitly out | Cloning Paul Bettany / Marvel JARVIS · tip-pinning a cloud SDK in `pyproject` · Authority-from-voice |

---

## 2. Cost ladder (prefer free)

| Priority | Path | \$ | Quality vs brief | How it plugs (T38) |
|---|---|---|---|---|
| **P0 — default** | **Piper local** — free ONNX voices, CPU, offline | **\$0** (disk + CPU) | Good enough for v1 demos; try `en_GB-alan-medium`, `en_GB-northern_english_male-medium` | `JARVIS_TTS_CMD` (or equiv.) → wav/play |
| P1 | OS TTS already on machine (`say`, `espeak-ng`, Windows SAPI) | \$0 | Often thinner / more robotic | same external cmd seam |
| P2 | Cloud free tier (Azure/Google/ElevenLabs trial) | \$0 then pay-as-you-go | Often richer | HTTP wrapper behind same seam |
| P3 | Paid neural / custom voice | \$\$ | Closest to “cinematic” without illegal clone | only if P0 fails the brief |

**Recommendation:** ship T38 against **Piper P0**. A/B two `en_GB` male voices offline. Escalate to cloud only if Engineer rejects the local timbre.

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
2. Download one `en_GB` male voice (start: **alan-medium**).  
3. Wrapper script: stdin or argv text → `piper` → play / write wav.  
4. Point T38 env (e.g. `JARVIS_TTS_CMD`) at that script.  
5. Run a Skill turn (`hold` / `estado`) and listen: grave? short? no theater?  
6. If thin: try `northern_english_male-medium` before paying for cloud.

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
