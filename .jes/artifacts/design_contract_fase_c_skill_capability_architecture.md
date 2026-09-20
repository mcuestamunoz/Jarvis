# Design Contract — Skill / Capability Architecture (`DC-fase-c-skill-capability-architecture`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **design contract only**  
**Implementer:** none yet — **no `src/` / no new packages** until Engineer ★ a later Implementation Contract derived from this  
**Reviewer:** Engineer ★ (ratify / amend) · Cursor holds the living text

**Status:** **★ CLOSED** (Engineer 2026-09-20 — APPROVED WITH AMENDMENT)  
**Type:** **Design / Architecture Lock** for **Fase C** (platform + team flight software).  
**Not** an Implementation Contract. **Not** a version bump to `0.5.0` by itself. **Not** permission to create `flight_software/` on disk.

**Parents:**
- [`docs/PLATFORM_CAPABILITY_VISION.md`](../../docs/PLATFORM_CAPABILITY_VISION.md) — directional vision (2026-09-10); this contract **concretizes** §13  
- [`docs/ENGINEERING_READINESS_VISION.md`](../../docs/ENGINEERING_READINESS_VISION.md) — readiness / assembly (orthogonal axis)  
- As-is craft SoT @ **`v0.4.3`**: `docs/ARCHITECTURE.md` · `docs/system_map/*` · engineering Continuity  
- M7 / pre–Fase C close: [fase M closeout](engineer_note_fase_m_closeout_m7.md) · [v0.4.3 note](engineer_note_v0_4_3_pre_fase_c_close.md)  
- Engineer briefing 2026-09-20: intent channels (terminal → voice → radio), Safety before actuation, Vehicle vs Device, first-FC ladder

**Outputs of this Buy (design-only):**
1. This contract (ratified locks)  
2. On Engineer ★: short ratification note or checklist tick below  
3. Later (separate): first **Implementation Contract** slice → package **`0.5.0`**

**Checkpoint base:** package **`0.4.3`** · tip pre–Fase C CLOSED

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Open Fase C with **structure first** | No flight-control code Buy until this DC is ★ (or explicitly waived) |
| 2 | Vision parent | `PLATFORM_CAPABILITY_VISION.md` remains directional; **this DC** is the working architecture lock for Fase C design |
| 3 | Product sentence | Jarvis is a **platform for physical systems**; the drone is the **first consumer**, not the whole product |
| 4 | Split | **Assistant ≠ Flight Software** — Assistant issues intents/tasks; Flight Software keeps the vehicle controllable + runs autonomy behaviors |
| 5 | Intent sources | Terminal · voice · radio · API (and future UI) are **Intent ingress** only — they **must not** skip Safety / Authority or drive actuators directly |
| 6 | Resolution chain | `Intent → Task → Required Capabilities → Capability Resolver → Provider → Skill/Execution` then **Safety / Authority → physical actuation** |
| 7 | Providers | A Provider may be a **Vehicle** or a **Device** (non-vehicle effector/sensor hub) — Assistant binds to capabilities, not to motor drivers |
| 8 | Package intent (future layout) | `flight_software/` · `vehicle_profiles/` · `capabilities/` (or equivalent) · existing `workspaces/` · existing `library/`/`catalog` — **names locked conceptually**; on-disk creation needs a later IC |
| 9 | First FC progression | Deterministic ladder for *first* flight-control slice (see §7) — educational / architecture order, not a claim that all layers ship in `0.5.0` |
| 10 | Version | **`0.5.0`** opens on the **first Implementation Contract** that lands Fase C product code (or a tiny scaffold IC Engineer explicitly calls “0.5.0 open”). This DC alone does **not** bump |
| 11 | Bridge to craft | Current Jarvis @ `0.4.3` remains the **engineering design SoT** (Continuity, catalog, Board). Fase C **consumes** designed vehicles; it does not replace craft montage |
| 12 | **★ Amendment (Engineer 2026-09-20)** | **This C0 defines architecture and conceptual contracts only.** It does **not** by itself authorize any implementation, and does **not** presuppose that `Vehicle`, `Device`, `Safety`/`Authority`, `Intent ingress`, or `radio` are implemented. Each acquires authority **only** via its own validated Implementation Contract. |

**Product sentence:**

```text
Antes de escribir firmware o meter voz en el loop, Jarvis fija
cómo la intención humana se convierte en capacidades resueltas,
quién las provee (vehículo o dispositivo), y qué puerta de
seguridad debe pasar antes de tocar el hardware.
```

---

## 1. Document boundaries

| Authority | Role |
|---|---|
| This DC (when ★) | Fase C **platform architecture locks** |
| `PLATFORM_CAPABILITY_VISION.md` | Broader to-be narrative; defer to this DC on conflict after ★ |
| `ARCHITECTURE.md` / `system_map/` | **As-is** craft/engineering runtime — do not pretend Flight Software exists there yet |
| `IMPLEMENTATION_TASKS.md` | Execution queue |
| Future ICs | Only path to create packages / code / `0.5.0` |

**Forbidden from this DC alone:** creating `flight_software/`, wiring radio→ESC, claiming ASSEMBLY READY implies flyable autonomy, Conversation Engine revival, silent rename of `workspace/` craft projects.

---

## 2. Top-level platform shape

```text
                    JARVIS
                      │
             ┌────────┴────────┐
             │                 │
        Assistant          Flight Software
             │                 │
      Intent / Task        Flight Control
             │                 │
       Capabilities          Autonomy
             │
        Skill
             │
        Provider
             │
       ┌─────┴─────┐
       │           │
    Vehicle     Device
       │
    Workspace (design instance)
```

### 2.1 Assistant

- Interprets human (or system) **intent**  
- Produces **tasks** that declare **required capabilities**  
- Does **not** know PWM, mixer maps, or ESC protocols  
- May sit above many vehicles/systems (drone first)

### 2.2 Flight Software

Reusable vehicle-class software (not one workspace’s one-off):

```text
flight_software/
├── flight_control/    # keep vehicle physically controllable
└── autonomy/          # missions / behaviors (TAKEOFF, HOLD, GO_TO, …)
```

Also planned as **platform capability modules** (may live under capabilities or sibling packages — naming in first scaffold IC):

```text
voice / assistant / perception / …   # reusable; not “inside the FC firmware blob” by default
```

### 2.3 Separation of concerns (locked)

| Layer | Answers |
|---|---|
| **Workspace** | Which system am I **designing** / which project instance? (today: craft Continuity @ `0.4.3`) |
| **Vehicle profile** | Which **hardware configuration** does this airframe need? |
| **Flight software** | How is this **vehicle class** controlled / made autonomous? |
| **Capability / Skill** | What can Jarvis (or a provider) **do**, independent of one airframe? |
| **Catalog / library** | Physical components + evidence (today’s `library/`) |

---

## 3. Intent ingress (terminal → voice → radio → …)

### 3.1 Principle

All human/command channels are **peers at Intent**:

| Source | Role | Must not |
|---|---|---|
| **Terminal / CLI** | Intent (and today’s engineering Continuity) | Drive actuators bypassing Safety |
| **Voice** | Intent | Become a second flight stack |
| **Radio / RC / ELRS** | Intent and/or **authority channel** (see §5) — design must say which | Skip Safety when mapped to “arm / mode” |
| **API / GCS / Board UI** | Intent | Direct mixer writes |

### 3.2 Continuity with today’s CLI

`jarvis --chat` today is the **engineering Assistant surface** for craft design.  
Fase C extends the **same Intent notion** toward operated vehicles — without requiring chat-in-Board (explicitly deferred).

Radio (ELRS, etc.) may later be both:

- an **Intent source** (“go home”), and  
- a **Safety / Authority** input (pilot override, kill, mode)  

Those two roles must be modeled **separately** in the first capability/safety IC — do not collapse “RC stick” into “Assistant skill”.

---

## 4. Resolution chain (normative)

```text
User / Event / Channel
        ↓
     Intent
        ↓
      Task
        ↓
Required Capabilities
        ↓
Capability Resolver
        ↓
   Provider (Vehicle | Device)
        ↓
Skill implementation (or FC/Autonomy command)
        ↓
 Safety / Authority gate
        ↓
Physical execution (flight_control → actuators)
```

**Reject path (honest):**

```text
REJECTED
reason: localization_invalid | capability_unavailable | authority_denied | …
```

Assistant/Skill **may request** `GO_TO` / `FOLLOW` / `LAND`; the physical stack **may refuse**.

---

## 5. Safety / Authority (non-negotiable)

```text
Assistant / Intent channel
        ↓
   Skill / Task
        ↓
   Capability bind
        ↓
 Safety / Authority     ← hard gate
        ↓
 Flight Control
        ↓
 Actuators (ESC, …)
```

Locks:

1. No Intent source writes motor commands directly.  
2. Safety has **veto** over actuation.  
3. Pilot/radio authority (when present) is modeled as **Authority**, not as a Skill that “wins by shouting”.  
4. Engineering simulation @ `0.4.3` remains non-authoritative for live flight claims.

---

## 6. Schemas (design targets — for later IC)

### 6.1 Skill

```text
Skill
├── identity
├── version
├── inputs
├── outputs
├── requirements      # capability ids
├── preconditions
├── permissions
├── execution
├── state
└── failure_modes
```

Skills compose capabilities (e.g. `FOLLOW_PERSON` → perception + tracking + localization + navigation).  
**Not** coupled to a single airframe SKU.

### 6.2 Capability

```text
Capability
├── identity
├── provider          # Vehicle | Device ref
├── version
├── availability
├── requirements
└── health
```

Examples (non-exhaustive): `navigation`, `localization`, `voice_input`, `speech_output`, `vision`, `flight_control`, `perception`, …

### 6.3 Provider

```text
Provider
├── kind: vehicle | device
├── identity
├── offered_capabilities[]
├── health / readiness
└── binding to profile / workspace (as applicable)
```

| Kind | Meaning |
|---|---|
| **Vehicle** | Mobile platform that can execute motion/flight (drone first) |
| **Device** | Non-vehicle provider (fixed camera hub, dock, sensor station, …) offering capabilities without being the airframe |

### 6.4 Capability Registry (future)

Jarvis must eventually answer: which capabilities exist, who offers them, are they available/healthy.  
First scaffold IC may ship a **minimal in-repo registry stub**; full runtime discovery is later.

---

## 7. First flight-control progression (architecture order)

For the **first** deterministic flight-control learning/implementation spine (drone):

```text
MCU / HAL
  → IMU
  → sampling
  → filtering
  → state estimation
  → controller
  → mixer
  → ESC
  → controlled flight
```

Locks:

- This is the **preferred teaching and slice order** for `flight_control/`.  
- A single IC may land **one rung** (e.g. HAL+IMU sampling) — not the whole ladder.  
- Autonomy behaviors (`TAKEOFF`, `HOLD`, `GO_TO`, …) sit **above** this ladder and still pass Safety.  
- Does **not** replace existing craft “Control PASS *” honesty @ `0.4.3` (identity-only FC remains design-time).

---

## 8. Autonomy vocabulary (initial set)

Non-normative starter set (may grow):

```text
TAKEOFF | HOLD | GO_TO | FOLLOW | RETURN_HOME | LAND | PATROL
```

Each maps to required capabilities + Safety checks — never to raw ESC output.

---

## 9. Relationship to current craft Jarvis (`v0.4.3`)

| Today (engineering) | Fase C (operation / FS) |
|---|---|
| Design vehicle in workspace | Operate / control vehicle class software |
| `library/` components + Continuity | `vehicle_profiles/` bind design → runnable profile |
| Board Taller 3D / CLI craft | Intent channels + FS + Safety |
| Sim / energy honesty | Live flight claims only with explicit evidence gates |

**Bridge rule:** a Workspace design should eventually **export or bind** a Vehicle Profile; Flight Software consumes the profile — it does not scrape Board card pixels.

---

## 10. Suggested Fase C attack order (after this DC ★)

Not locked as Buys until Engineer picks — recommended:

```text
C0  ★ this Design Contract
C1  Capability / Skill / Provider schema + registry stub (docs + maybe minimal package) → opens 0.5.0
C2  Intent ingress model (terminal + placeholder voice/radio adapters) + Safety gate interface
C3  First flight_control rung (HAL/IMU or equivalent) under vehicle_profiles smoke
C4  Autonomy command surface (HOLD/LAND…) behind Safety
C5  Radio/ELRS as Authority + Intent (explicit dual-role design)
…
```

Firmware vendor stacks (Betaflight / PX4 / …) are **options inside Provider/flight_control**, not a bypass of this architecture — decide per IC.

---

## 11. Explicit non-goals (this DC)

| Out | Why |
|---|---|
| Implementing FS packages | Needs IC + `0.5.0` |
| Chat panel inside Board | Engineer deferred |
| Full voice pipeline | Later capability |
| Claiming live autonomous flight | Evidence / Safety not ready |
| Replacing craft montage SoT | Orthogonal product surface |

---

## 12. Acceptance of this Design Contract

**Engineer ★ 2026-09-20 — APPROVED WITH AMENDMENT** (lock #12).

Checklist (accepted):

- [x] Assistant ≠ Flight Software split  
- [x] Intent sources + Safety gate (as **architecture**, not as shipped code)  
- [x] Vehicle vs Device providers (conceptual)  
- [x] Resolution chain  
- [x] First FC ladder as spine (not one-shot)  
- [x] `0.5.0` reserved for first implementation IC  
- [x] Amendment: C0 does not authorize implementation or imply those concepts exist in code  

**Next:** Cursor → **C1** Implementation Contract (schema + registry stub → `0.5.0`).

---

## 13. Handoff

```text
Engineer → read + ★ / amend this DC
Cursor   → first Fase C IC (schema/registry or Engineer-priority slice) → 0.5.0
Claude   → implement only after that IC ★
```

**Pointer from vision:** `PLATFORM_CAPABILITY_VISION.md` §13 is satisfied by **this artifact**; keep vision as narrative parent.
