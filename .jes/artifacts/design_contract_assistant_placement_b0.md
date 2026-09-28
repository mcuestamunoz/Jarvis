# Design Contract — Assistant placement in the repo (`DC-assistant-placement`)

**Project:** Jarvis  
**Date:** 2026-09-26  
**Author:** Cursor (Engineer Interface) — **design contract only**  
**Implementer:** none for this DC — disk scaffold is **A1 IC** (`B1-intelligence-scaffold`)  
**Reviewer:** Engineer ★ (ratify / amend)

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-28) — placement lock ratified. A1–A6 ★ CLOSED through **`v0.6.5`**. A4 voz/world **Parked**. R4 later.  
**Type:** Design / Architecture Lock — **where Assistant will live**, not voice, not house map, not lavadora.  
**Not** an Implementation Contract. **Not** a version bump. **Not** permission to create `intelligence/` or `world/` on disk.

**Parents:**
- [`docs/PLATFORM_CAPABILITY_VISION.md`](../../docs/PLATFORM_CAPABILITY_VISION.md) §3, §9, §11, §12 — directional; examples such as `"Ve a la cocina"` are **horizon illustrations**, not Buys
- [`design_contract_fase_c_skill_capability_architecture.md`](design_contract_fase_c_skill_capability_architecture.md) (**C0 ★ CLOSED**) — already locks **Assistant ≠ Flight Software**; voice/assistant/perception “may live under capabilities or sibling packages”
- Engineer 2026-09-26: assistant examples (voz, mapa de casa, equipos por habitación, puerta principal, “dime si la lavadora ha finalizado”) are **future capability shape**. First phase = **repo home + seams**. That work is **not now** as product.

**Correction:** [month note](engineer_note_software_month_until_bench_2026_09_26.md) A1–A3 (`VoiceIntentAdapter` → GO_TO `"cocina"`) was the **wrong grain**. Retracted as cola de implementación. Horizon stays in the vision; this DC owns **placement**.

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Horizon ≠ cola | Frases de voz, mapa de casa, lavadora, puerta = **ejemplos de forma futura**. No son ICs de este mes |
| 2 | First assistant work | **Placement + seams** (this DC). Empty package / adapters / STT / world graph = later ICs, each ★ on its own |
| 3 | C0 still holds | Assistant issues intents/tasks; does **not** know PWM/mixer/ESC; does **not** live inside the FC blob |
| 4 | Engineer already has a home | Craft chat / Continuity / `project_status` stay in **`src/jarvis/core/`**. Assistant-platform does **not** swallow Jarvis Engineer |
| 5 | Flight software stays vehicle | **`src/jarvis/flight_software/`** is control + autonomy verbs. No house rooms, no appliances, no “lavadora” |
| 6 | Intent peers already named | Voice is an **Intent ingress** peer (`capabilities/intent.py` stub). Filling `VoiceIntentAdapter` is **not** this DC |
| 7 | World graph is a later slot | Rooms / doors / devices-in-rooms need a **named home** so they are not stuffed into Continuity craft or into `flight_control`. **No schema this Buy** |
| 8 | No Conversation Engine | Do not create a parallel orchestrator. Do not move engineering truth or `step()` into the LLM |

---

## 1. What already exists (do not relocate)

| Folder today | What it is | What it is not |
|---|---|---|
| `src/jarvis/core/` | Jarvis **Engineer**: diseño, Continuity, orquestador CLI/MCP | El runtime de “oye Jarvis, ve a la lavadora” |
| `src/jarvis/capabilities/` | Intent / Safety / registry vacío; radio dual-role; CRSF host | Assistant, memory, world map |
| `src/jarvis/flight_software/` | Escalera de control + verbos de autonomía (papelitos) | Inteligencia de casa, voz, Engineer |
| `src/jarvis/vehicle_profiles/` | Perfil de vehículo-clase | Un piso |
| `library/` + workspace | Craft SoT de **diseño** del aparato | Mapa de habitaciones |

C0 §2.1 already: Assistant interprets intent, produces tasks that declare required capabilities, may sit above many vehicles. **On disk, that layer was never opened.** C1 opened `capabilities/` empty. C2 opened Intent stubs. The **intelligence column** in the vision sketch was never a package.

---

## 2. Proposed repo shape (conceptual — names for the DC, not mkdir)

```text
src/jarvis/
├── core/                 # ENGINEERING  — already. Stay.
├── capabilities/         # CAPABILITIES — already. Intent/Safety/registry. Voice adapter stays a peer here when its IC comes.
├── flight_software/      # VEHICLE      — already. Control + autonomy. Stay.
├── vehicle_profiles/     # already
├── intelligence/         # ON DISK via A1 IC scaffold — Assistant home (tasking / memory / planning later)
│                         #                sits above Intent; never inside flight_control
└── world/                # NOT ON DISK  — candidate later: rooms, doors, devices-per-room
                          #                consumed by Assistant; executed via capabilities → vehicle/device
```

**Default recommendation (amendable on ★):**

- **`intelligence/`** = Assistant as a *platform layer* (the vision’s INTELLIGENCE column).
- **`world/`** = deferred sibling (or `intelligence/world` later). Do **not** invent the house graph now; **do** refuse to put it under `flight_software/` or `library/frames/`.
- **Voice** remains an **ingress** in `capabilities/intent.py` (already stubbed). It is not the Assistant package.
- **Jarvis Engineer vía dron** (fase 2 de horizonte) = the **same** `core/` Continuity, reached through a future Intent channel. Not a copy of Engineer inside `intelligence/` and not inside the FC.

**Rejected placements:**

| Put Assistant here | Why not |
|---|---|
| `flight_software/` | C0 lock: Assistant ≠ FC |
| `core/orchestrator.py` as a new brain | Orchestrator is craft routing; a second Conversation Engine is forbidden |
| `library/` | Catalog of parts, not rooms |
| Inside the MCU tree `native/flight_control/` | Firmware is vehicle control |

---

## 3. Seams (so the base stays optimal)

```text
human / event
    → Intent ingress     (terminal | voice | radio | api)     capabilities/
    → Assistant          (tasks, required capabilities)       intelligence/   [future]
    → Capability resolve (who can do this)                    capabilities/
    → Safety / Authority                                      capabilities/
    → flight_software or a Device provider
```

World (future): Assistant may *ask* “which room is the washer in?” of `world/`. `world/` does not fly the quad. `flight_software` does not own the washer.

Craft Engineer stays a **different** question (“cómo va el proyecto 10-min”) answered by `core/`, even if the *channel* someday is voice on the same radio.

---

## 4. Out of scope (explicit)

- STT / wake-word / “oye Jarvis”
- Mapa de casa, habitaciones, puerta principal, equipos por habitación
- Ver si la lavadora ha terminado (device provider + perception)
- `VoiceIntentAdapter` que deje de lanzar `NotImplementedError`
- `world/` en disco · STT/casa (sigue parked). `intelligence/` scaffold = **A1 IC only**, not this DC alone
- Mezclar esto con C36–C43 (planta sim / lazos / ejecutor)

Those need their own ICs **much later**, after this placement is ★ and after the vehicle software ladder has somewhere to *bind* a GO_TO. Placement first so those ICs do not dump files into the wrong tree.

---

## 5. Next after this DC is ★

Cola operativa (epoch `0.6`) — PRIORIDAD en [`IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md):

1. **A1** — IC scaffold: `src/jarvis/intelligence/` vacío + README + test import; no llama `flight_software` (mismo grain que C1 registry).
2. **A2** — IC R2: retrieve **read-only** del spine ontology (estrecho: lote-4/5 honesty + [`ONTOLOGY_CROSSWALKS.md`](../../docs/ONTOLOGY_CROSSWALKS.md)); cite; no escribe catalog/Continuity/`step()`.
3. **A3** — canal terminal/CLI: pregunta “¿por qué?” → respuesta + cita nota. Voz / world / casa = **después** (A4 parked).

A0 ★ CLOSED. A1 IC AUTHORIZED for empty `intelligence/` scaffold. Still **zero** `world/` / retrieve / canal until their ICs.

Ontology vault + crosswalks are **ready as explain SoT** for A2; they do not replace this placement DC.
