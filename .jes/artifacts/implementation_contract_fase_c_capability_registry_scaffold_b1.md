# Implementation Contract — Fase C capability schema + registry stub (`B1-fase-c-capability-registry-scaffold`)

**Project:** Jarvis  
**Date:** 2026-09-20  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check of honesty (no fake “available flight”)

**Status:** **ACCEPT CLOSED** (Engineer 2026-09-20) · Cursor review PASS · tag **`v0.5.0`**
  
**Parents:**
- [Design Contract C0 ★ CLOSED](design_contract_fase_c_skill_capability_architecture.md) — with Engineer amendment (architecture ≠ implemented)  
- [`docs/PLATFORM_CAPABILITY_VISION.md`](../../docs/PLATFORM_CAPABILITY_VISION.md) — directional parent  
- Craft SoT tip **`v0.4.3`** — Continuity / catalog / Board **unchanged** by this Buy  

**Type:** **First Fase C Implementation Contract** — typed **schemas** + **minimal Capability Registry stub**.  
**Opens package:** **`0.5.0`** (bump in this Buy when ★ and implemented).  
**Not** flight_control runtime · not Safety gate executable · not Intent ingress adapters · not Vehicle/Device **runtime** providers · not radio/ELRS · not autonomy commands · not craft montage changes.

**Outputs (required):**
1. Schema + registry code under an agreed package path (see §0)  
2. Seed data that is **honest about non-availability** (see §3)  
3. Tests T1–T12  
4. `.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md`  
5. Living-doc pointers: PRIORIDAD / PLATFORM_CAPABILITY_VISION §13 / short ARCHITECTURE or system_map note that **scaffold ≠ FS shipped**  
6. `pyproject.toml` → **`0.5.0`** (+ README tag blurb); git tag **`v0.5.0`** only after Engineer ACCEPT of this Buy (may be same closeout commit or follow-up — report which)

**Checkpoint base:** package **`0.4.3`** until this Buy lands **`0.5.0`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-capability-registry-scaffold`** — Skill / Capability / Provider **schemas** + **Capability Registry stub** |
| 2 | C0 amendment | This IC is the **first** authority that may create Fase C packages on disk. C0 alone never authorized that |
| 3 | Package path | Prefer **`src/jarvis/capabilities/`** (schemas + registry). **Do not** create `flight_software/`, `vehicle_profiles/`, or a fake runtime FC tree in this Buy. Those names remain **conceptual** until their own ICs |
| 4 | What “registry stub” means | In-process (or JSON/YAML seed loaded into memory) catalog of Capability / Provider / optional Skill **records**. Query API: list / get by id / “who offers capability X?”. **No** network discovery, **no** process supervisor, **no** health probes against hardware |
| 5 | Honesty | **Forbidden:** marking `flight_control` (or any flight/actuation capability) as **available** / ready / healthy-for-execution. If a flight-related id appears in seed, it must be explicitly **`not_implemented`** or **omitted**. Prefer **omit** flight_control from seed in C1 |
| 6 | No execution path | **No** function that turns Intent/Task/Skill into actuator commands, mixer output, ESC writes, or autonomy `GO_TO`/`LAND` execution. Registry is **descriptive**, not a dispatcher |
| 7 | No Safety/Intent/Radio implementation | Interfaces or enums **may** name future concepts only if clearly non-operational (e.g. comments / `Literal` stubs unused). **Do not** ship Safety gate logic, voice, or ELRS |
| 8 | Bridge to craft | **Do not** mutate Continuity, orchestrator IDLE, Board, or `library/` as part of this Buy. Optional **read-only** mention in docs that craft SoT remains `0.4.3` surface |
| 9 | Seed content (minimal) | Ship **at most**: (a) 1–2 **non-flight** capabilities that already exist as *product ideas* without claiming new runtime — e.g. ids reserved for future `engineering_design` / `simulation_eval` marked `availability: stub` **or** an empty registry with zero capabilities and tests that empty-list is valid; (b) **zero or one** Provider record of kind `vehicle` or `device` with **empty** `offered_capabilities` **or** only stub non-flight ids. Engineer preference locked below: **empty registry + schemas + tests that empty is valid**, plus **one documented example fixture used only in tests** (not loaded as “live available” product seed). See §3 |
| 10 | Version | Bump to **`0.5.0`** in this Buy; tag `v0.5.0` on Engineer ACCEPT (or same commit if Engineer says tag-with-land) |
| 11 | Tests | New focused test module(s); no weakening of craft suite |
| 12 | Forbidden | Conversation Engine · inventing available flight · creating `flight_software/` · wiring Assistant→motors · Board chat |

**Product sentence:**

```text
Abrir Fase C en 0.5.0 con los contratos tipados Skill/Capability/Provider
y un Capability Registry stub que solo describe — nunca ejecuta ni
finge que el dron ya vuela.
```

**Seed preference (locked — Engineer 2026-09-20 via this IC draft):**

```text
Default product seed = EMPTY registry (0 capabilities, 0 providers, 0 skills).
Schemas + query API must work on empty.
Tests MAY use fixtures that construct in-memory records (including a
deliberately not_implemented flight_control row) to prove validation —
those fixtures are NOT the default loaded registry for the running product.
```

---

## 1. Schemas (normative fields — minimal viable)

Implement as Pydantic models (or project-equivalent) under `src/jarvis/capabilities/`.

### 1.1 `CapabilityRecord`

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Stable slug, e.g. `navigation` |
| `version` | `str` | Semver-ish string |
| `provider_id` | `str \| None` | Optional bind; stub may be null |
| `availability` | enum | At least: `stub` · `not_implemented` · `unavailable` — **do not** add `available` / `ready` in C1 **or** if added, **no seed/fixture used as product default may set it** for flight-related ids. Lock: **C1 enum includes `stub` and `not_implemented` only** (extend later ICs) |
| `requirements` | `list[str]` | Capability ids this one needs (may be empty) |
| `health` | enum or str | C1: `unknown` only (or omit field). **No** `healthy` pretending hardware OK |

### 1.2 `ProviderRecord`

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | |
| `kind` | `Literal["vehicle", "device"]` | Conceptual kinds from C0 — **records are data**, not live vehicles |
| `offered_capability_ids` | `list[str]` | Must reference known capability ids if non-empty; empty OK |
| `health` | | C1: `unknown` only |

### 1.3 `SkillRecord` (optional in C1)

If included:

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | |
| `version` | `str` | |
| `required_capability_ids` | `list[str]` | |
| `availability` | same restricted enum as Capability | |

**C1 may ship Skill schema without any skill instances** (empty).

### 1.4 Validation rules (C1)

1. Unknown `kind` → reject.  
2. Duplicate ids in registry → reject on load.  
3. `offered_capability_ids` / `required_capability_ids` referencing missing capability id → reject **or** explicit `unresolved` policy — **lock: reject on load** for stub integrity.  
4. **No** field named `execute`, `dispatch`, `command_esc`, etc.

---

## 2. Capability Registry stub API (normative)

```text
CapabilityRegistry
  .capabilities() -> list[CapabilityRecord]
  .providers() -> list[ProviderRecord]
  .skills() -> list[SkillRecord]          # empty OK
  .get_capability(id) -> CapabilityRecord | None
  .get_provider(id) -> ProviderRecord | None
  .providers_offering(capability_id) -> list[ProviderRecord]
  .load_default() -> CapabilityRegistry   # EMPTY product default
```

- Pure data / validation — **no I/O to hardware**, no threads, no asyncio flight loops.  
- Optional: load from a checked-in JSON that is **`{"capabilities":[],"providers":[],"skills":[]}`**.

---

## 3. Honesty rules (acceptance-critical)

| Rule | Detail |
|---|---|
| H1 | Default registry is **empty** |
| H2 | No product path claims flight/actuation capability is implemented |
| H3 | Test fixtures may include `availability=not_implemented` rows for teaching validation — never as `load_default()` |
| H4 | No Assistant/orchestrator hook that “runs a skill” |
| H5 | Docs must say: **scaffold @ 0.5.0 ≠ Flight Software shipped** |

---

## 4. Docs / queue updates (this Buy)

| File | Change |
|---|---|
| `pyproject.toml` / `README.md` | Version **0.5.0**; short “Fase C scaffold” blurb |
| `docs/IMPLEMENTATION_TASKS.md` | C1 CLOSED / in flight as appropriate; PRIORIDAD next C2 or await ★ |
| `docs/PLATFORM_CAPABILITY_VISION.md` | Point §13: C0 ★ + C1 scaffold landed (when done) |
| `docs/ARCHITECTURE.md` or system_map | One paragraph: capabilities package is **registry stub only** |
| C0 DC | Optional “derived IC” link |

---

## 5. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Empty `load_default()` → 0 capabilities, 0 providers, 0 skills |
| T2 | Construct valid CapabilityRecord + ProviderRecord in memory; registry accepts |
| T3 | Duplicate capability id → load/construct error |
| T4 | Provider offers unknown capability id → reject |
| T5 | `kind` must be `vehicle` or `device` |
| T6 | `providers_offering("x")` returns expected subset |
| T7 | Missing get → `None` |
| T8 | Availability enum rejects inventing `available` **or** if enum lacks it, confirmed only `stub`/`not_implemented` |
| T9 | No public registry method dispatches / executes skills (API surface audit in test or naming convention assert) |
| T10 | `pyproject` version == `0.5.0` |
| T11 | Full craft suite still green (no accidental orchestrator coupling) |
| T12 | Report lists files + confirms H1–H5 |

---

## 6. Out of scope (explicit)

| Out | Belongs to |
|---|---|
| `flight_software/` tree, HAL, IMU, mixer, ESC | C3+ |
| Safety / Authority gate implementation | C2+ |
| Intent ingress (voice/radio/API adapters) | C2+ |
| Live Vehicle/Device runtime binding to workspace | Later IC |
| Autonomy TAKEOFF/HOLD/GO_TO execution | C4 |
| ELRS dual-role | C5 |
| Craft Continuity / Board / catalog changes | Not this Buy |
| Marking any capability `available` for flight | Forbidden in C1 |

---

## 7. Report shape

`.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md`:

- Package path chosen  
- Schema field list vs this IC  
- Confirmation: default registry empty; no execution path  
- Tests run + counts  
- Version **0.5.0**  
- Residual: what C2 should pick up  

---

## 8. Acceptance

**PASS when:** T1–T12 · H1–H5 · no `flight_software/` · no craft regression · version 0.5.0.  

**FAIL if:** default seed implies flyable/available flight_control · any Intent→actuator path · C0 treated as implementation license without this IC.

**Engineer ACCEPT when:** spot-check empty default + README honesty line.

---

## 9. Handoff

```text
Engineer → ★ this IC (C1)
Claude   → implement schemas + empty registry + tests + bump 0.5.0 + report
Cursor   → independent review
Engineer → ACCEPT → tag v0.5.0 (if not tagged at land)
Cursor   → C2 IC when Engineer prioritizes Intent/Safety stub
```

---

## 10. PRIORIDAD blurb

```text
Fase C: C0 ★ CLOSED (amendment). C1 B1-fase-c-capability-registry-scaffold
READY — schemas + empty Capability Registry stub → 0.5.0; no FS runtime.
```
