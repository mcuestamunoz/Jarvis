# Engineer note — After craft-montage smoke: next product lens (design, not mounts)

**Date:** 2026-09-15  
**Authority:** Engineer greenfield smoke ACCEPT (`dron-de-vigilancia-doméstico`) + design question (novice 0→drone; software/comms; Continuity next-step vs intent)  
**Status:** Observation / recommendation only — **no Buy opened**

---

## Closed this cycle

- `B1-user-guide-craft-montage` — ACCEPT (CLI E2E greenfield + Board silhouette path)
- `B1-estimated-temporary-esc-skystars` — ACCEPT (used in same walk / related live)

---

## Continuity “Aumentar carga útil” vs mission text (GPT observation)

**Agree — park as observe, do not implement now.**

Evidence in code: when sim is PASS with high thrust margin, `reasoning_layer` suggests `increase_payload` / “Aumentar carga útil” from **margin heuristics**, not from parsing `objetivo = dron de vigilancia doméstico`. Continuity then surfaces that as `next_useful_step` when BOM gaps are closed.

| Signal | Reality |
|---|---|
| Engineering | Coherent: spare thrust → “you *could* raise payload” |
| Product intent | Weak: surveillance needs camera / endurance / nav / link, not more kg |

Named debt (observe only): **Continuity next-step vs declared mission intent**. Related known partial handoffs already in Continuity map. Reopen only with explicit ★ + investigation contract — not a drive-by fix.

---

## If the user knows nothing (design spine, **before** mounts)

Recommended order of **questions**, not parts:

1. **Mission** — what must it do? (vigilancia casa → hover/loiter, video, indoor/outdoor, range, noise, night?)  
2. **Constraints** — flight time target, max size/weight, budget class, legal/ops.  
3. **Payload stack (functional)** — camera (+ gimbal?), companion computer?, radio/link?, GNSS needs?  
4. **Energy budget** — Wh / cells from (3)+(hover power), not from “pick a pretty Lipo”.  
5. **Propulsion match** — motor/prop/ESC that can lift AUW with margin.  
6. **Airframe class** — size that fits props + stack volume.  
7. **Control identity** — FC/GPS that match power/protocol class (identity + envelope only today).  
8. **Only then** — Board montage (guide we just closed).

Jarvis today is strong at **(5)–(8)** once payloads/energy are numeric. Weak at **(1)–(3)** as a guided product path: wizard asks payload kg but does not decompose “vigilancia” into camera/link/autonomy requirements.

---

## Software / communications / FC “internals”

**Honest boundary:** Jarvis does **not** generate flight-stack firmware, MAVLink graphs, radio configs, or companion software. FC is **identity + physical envelope** (+ Control PASS\* declaration). That is correct for the current product: deterministic engineering of the *airframe*, not an autopilot IDE.

How to approach without lying:

| Layer | Who owns it | Jarvis role (future, if ★) |
|---|---|---|
| Autopilot firmware (Betaflight/PX4/ArduPilot) | External / Engineer | Catalog **capability tags** (F4/F7, UARTs, GPS port) — not flashing |
| Air link (ELRS/Crossfire/Wi‑Fi) | External | Optional **component family** + mass/power draw for energy |
| Video (analog/DJI/Walksnail) | External | Same — mass, power, antenna volume for Board |
| Companion / GCS / app | External | Out of Continuity spatial; maybe later “mission software checklist” (suggest-only) |
| Wiring pinout / DShot / UART map | External + datasheets | `source_note` honesty only until a real schema exists |

**Do not** invent a Conversation Engine that “writes the FC software.” Prefer: **requirements → component holes → cited catalog rows** (camera, VTX, RX) that feed mass/power/geometry — same discipline as motors/ESC.

---

## Recommended next ★ candidates (pick one; Engineer)

| Priority lean | Candidate | Why |
|---|---|---|
| **A — Novice design** | Investigation B0: mission → functional payload holes (camera/link/endurance) before propulsion | Fixes the “from zero” gap without touching mounts |
| **B — Honesty polish** | Guide patch: `actualiza el frame` + arm L×W×H + ESC H after MY5/Skystars; multi-placa | Cheap; encodes smoke friction |
| **C — Catalog hygiene** | `bind_esc` omit-key leak · FC IDLE rebind | Correctness under rebind |
| **D — Geometry holds** | plate-box / disk-station attest | Only when caliper/cite bags exist |
| **Park** | Continuity intent-aware next-step | Observe in more smokes; ★ later |

Default recommendation after this smoke: **A** (or thin **B** if we want docs-only first), not firmware generation, not Continuity rewrite.
