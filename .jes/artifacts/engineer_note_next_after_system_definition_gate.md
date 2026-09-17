# Engineer note — Next after SYSTEM_DEFINITION block-gate CLOSED

**Date:** 2026-09-15  
**Authority:** Engineer — smoke waived; asks what Jarvis should do next; floats “define all flight-control software structure”  
**Status:** Recommendation only — **no Buy opened**

---

## Closed

`B1-system-definition-block-gate` — refuse unresolvable architecture blocks (cámara/radio/…). Honesty bug closed. Smoke waived.

---

## Direct answer: flight-control **software** stack?

**No — not the next Jarvis ★.**

Jarvis’s SoT is **deterministic airframe / energy / geometry / catalog identity**. Autopilot firmware (Betaflight/PX4/ArduPilot), MAVLink graphs, radio binding, companion apps, and GCS software are **external products**. Building “toda la estructura de software de control de vuelo” inside Jarvis would:

- invent a second product (avionics IDE),  
- break the “LLM ≠ engineering truth” rule if the stack is narrated rather than cited,  
- not unblock the real gap the vigilancia smoke showed: **mission payload** (cámara, link, autonomía como driver).

Honest FC role today (keep): **identity + physical envelope** (`library/fc`). Optional later: capability **tags** from datasheets (UARTs, F4/F7) — still not firmware generation.

---

## What *is* the next product step

The gate made “B → cámara” **safe** (refuse). The novice still cannot **complete** a vigilancia design. Next is to make mission subsystems **resolvable**, in order:

| Priority | Candidate | What it unlocks |
|---|---|---|
| **1** | **B1-min (b)** or thin catalog: identity `ComponentRule` (+ later cited `library/cameras` / link when bags exist) | SYSTEM_DEFINITION B can accept perception/comms without stuck BOM; Continuity can ask for camera |
| **2** | Wizard / Continuity **nudge** (“vigilancia → ¿cámara/link?”) | Novice notices the path (only after 1) |
| **3** | Mass/power of payload via mirrored params | Energy sizing tracks real stack |
| **Park** | Continuity “aumentar carga útil” vs mission | After holes exist |
| **Park** | Flight-stack software / flashing / MAVLink | Outside Jarvis core — document as OUT |
| **Holds** | plate-box / Path N / disk attest | Only with caliper/cite bags |

**Default lean:** ★ open investigation/IC for **mission payload resolvability** (identity-first cameras/radio_module — Engineer defines “enough” for a rule; **no** invent mm/g; catalog seeds only with cited bags).

---

## One-line product sentence

```text
Jarvis diseña el craft (masa, energía, geometría, identidades citadas);
el software de vuelo se elige/configura fuera — Jarvis solo debe saber
qué cámara/link/FC lleva el dron para dimensionarlo con honestidad.
```
