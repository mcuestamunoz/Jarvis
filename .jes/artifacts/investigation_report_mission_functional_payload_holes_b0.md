# Investigation Report — Mission → functional payload holes before propulsion (B0)

**IC:** [investigation_contract_mission_functional_payload_holes_b0.md](investigation_contract_mission_functional_payload_holes_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-15
**Type:** Read-only investigation. No code/schema/library edit. No version bump. No `workspace/` write (census only, read-only).

---

## Executive summary (read this first)

The investigation surfaced one finding that changes the shape of the recommended next Buy: **the mission-decomposition hook the Engineer wants is not entirely absent** — it exists today as `SystemDefinitionSession`'s "B — Añadir o modificar bloques" step, which fires **automatically after every `create_project`**, and already carries a working Spanish alias table mapping `"cámara"`/`"payload"`/`"carga útil"`/`"comunicación"`/`"brazo"` to canonical blocks (`perception`/`payload`/`communication`/`manipulation`). It was never invisible by design — it is invisible **in practice**, because (a) it is a single low-context A/B/C prompt easy to answer "A" (use the 4-block aerial default) without reading option B's examples, and (b) even when a user picks B and adds e.g. `"cámara"`, the resulting `cameras` component key has **no `ComponentRule` anywhere in `aerial.py`'s registry** — so it can never progress past `completeness: "low"`, ever. Today, exercising this path makes the BOM view **worse**, not better: it adds a permanently-stuck "incomplete" row with no Continuity phrase able to resolve it.

This means the smallest honest next step is not "invent a new mission-checklist subsystem" — it is closer to "finish wiring a path that already exists at the architecture-catalog layer, and make it impossible to silently skip past for a mission that clearly implies a functional payload." See §D for the ranked Buy options this produces.

---

## Q1 — As-is create path (with evidence)

`CreateProjectInteractiveSession.PROMPTS` (`src/jarvis/core/interactive_session.py:52-99`) is the **complete, exhaustive** set of questions the create wizard can ever ask:

| Step | Field | Question (verbatim) |
|---|---|---|
| 0 | `vehicle_type` | "¿Qué sistema quieres diseñar? (dron, robot, etc.)" |
| 1 | `objective` | "¿Cuál es el objetivo principal? (ej: levantar 2kg)" |
| 2 | `payload_kg` | "¿Cuál es la carga útil en kg?" |
| 3 | `restrictions` | "¿Tienes restricciones? (tamaño, autonomía, presupuesto, etc.)" |
| 4 | `detail_level` | "Nivel de diseño: conceptual o detallado" |
| 10 | `motors` (aerial) | "¿Cuántos motores tiene el sistema?" |
| 11 | `aerial_path` | "¿Cómo defines la fuerza de propulsión? (empuje declarado / hélices / no sé aún)" |
| 12/13/14 | thrust or prop diameter/RPM | numeric follow-ups |
| 90 | confirm | — |

`ProjectDraft` (`src/jarvis/schemas/action_schema.py:100-113`) is the schema these answers land in — it has **no field** for camera, video link, radio/comms, companion compute, or any autonomy/endurance target. `objective`/`restrictions` are stored as **raw strings** (`current_parameters["objective"]`, `["restrictions"]`) — confirmed live: `dron-de-vigilancia-doméstico`'s `current_parameters["objective"] == "dron de vigilancia doméstico"`, `["restrictions"] == "no"`, verbatim, unparsed beyond one regex (see Q1 contrast below).

**One real exception, evidence-gated:** `state_schema._parse_constraints` (`src/jarvis/schemas/state_schema.py:45-79`) mines `autonomy_min`/`max_weight_kg` out of `restrictions`, falling back to `objective`, via two numeric regexes (`_AUTONOMY_CONSTRAINT_RE`/`_WEIGHT_CONSTRAINT_RE`). This is genuine, working mission-text mining — but it only fires when the text happens to contain a **parseable number attached to a recognized unit**, never a general decomposition.

**Contrast, live census (read-only):**

| Project | `objective` | `restrictions` | `parsed_constraints` |
|---|---|---|---|
| `dron-de-vigilancia-doméstico` | "dron de vigilancia doméstico" | "no" | `{}` (empty) |
| `10-min-autonomía` | "10 min autonomía" | "no" | `{"autonomy_min": 10.0}` |

`10-min-autonomía` only gets an autonomy target because its **objective string happens to contain the digits "10" next to "min"** — pure regex luck, not a deliberate mission-decomposition step. `vigilancia`'s objective has no number, so nothing is mined. **Mission-blind steps: all of them (0–4, 10–14)** — none reads `objective`/`restrictions` for anything except this one numeric regex.

## Q2 — Architecture holes (the central finding)

### The block/alias layer already exists — and already fires automatically

Immediately after a successful `create_project`, the orchestrator **unconditionally** launches `SystemDefinitionSession.start(vehicle_type, project_state)` (`src/jarvis/core/orchestrator.py:6806-6810`, comment: *"Launch system definition session after successful create_project. Always offered — message adapts based on detail_level inside start()"*). For a known domain like `"dron"`, this presents:

```text
Para un dron, la arquitectura típica incluye:
  • Propulsión (motores + hélices + ESC)
  • Energía (batería)
  • Estructura (frame)
  • Control (controladora + sensores)

Recomendado: empieza por propulsion — es el bloque que define el dimensionado del resto.

  A — Usar esta arquitectura base
  B — Añadir o modificar bloques
  C — Saltar (definir después)
```
(`src/jarvis/core/system_definition_session.py:134-178`)

`BLOCK_ALIASES` (`src/jarvis/core/system_architecture_catalog.py:188-212`) already maps, in Spanish, exactly the concepts this investigation is about:

| User types | Resolves to block |
|---|---|
| `"vision"`, `"vision artificial"`, `"camaras"`, `"camara"`, `"lidar"`, `"sensores vision"` | `perception` |
| `"comunicacion"`, `"telemetria"`, `"radio"` | `communication` |
| `"payload"`, `"carga util"` | `payload` |
| `"manipulador"`, `"brazo"`, `"arm"` | `manipulation` |

`BLOCK_TO_COMPONENTS` (`system_architecture_catalog.py:147-171`) maps those blocks to component keys: `perception → ["cameras", "lidar"]`, `communication → ["radio_module"]`, `payload → ["payload_bay"]`, `manipulation → ["arm"]`. **Confirmed live** (pure-function call, no state touched):

```text
normalize_block_alias("camara")       -> "perception"
normalize_block_alias("payload")      -> "payload"
normalize_block_alias("comunicacion") -> "communication"
blocks_to_component_keys([..., "perception", "payload"])
    -> [..., "cameras", "lidar", "payload_bay"]
```

Picking "B" and typing `"cámara"` really does add a `cameras` key to `design_properties.components` via `_build_component_stubs` (`system_definition_session.py:67-82`), reaching `_apply_and_finish` → `workspace_manager.save_state`.

### Why it doesn't help today

`_build_component_stubs` creates `ComponentSpec(completeness="low", source="declared")` — **`suggested_key` is left `None`** (confirmed live: `stubs["cameras"].suggested_key is None`). For `motors`/`propellers`/etc. this is fine, because `aerial.py`'s `ComponentRuleRegistry` (`aerial_registry`) has a rule keyed on those exact strings, so a later free-text phrase (`"4 motores 2306"`) routes through `infer_component_for_key` and fills in `suggested_key`/properties/completeness for real. **No such rule exists for `cameras`, `lidar`, `radio_module`, `payload_bay`, or `arm`** — confirmed by a full grep of `src/jarvis/domains/aerial.py` for `camera|cámara|vtx|gimbal|companion|video.?tx|video.?link|elrs|fpv|payload|radio_module|lidar`: **zero matches** outside one unrelated "FPV" mention in `project_closure.py:163` (structure class-slack, unrelated). Once created, the stub has no phrase that can ever move it past `completeness: "low"`.

`build_component_bom` (`src/jarvis/core/project_closure.py:582-616`) reads `expected_keys` straight from `design_properties.components.keys()` (or the block-derived superset) — so `cameras`/`payload_bay` **do** show up in the BOM's "incomplete" bucket once added, permanently, with no resolving phrase. **Exercising the already-shipped B-path today makes a project's BOM honestly worse, not better** — it surfaces a real gap the system then has no way to help close.

### Existing keys vs stub-only vs missing (feeds the taxonomy in §B)

- **GNSS** already exists as a real, working concept — but folded into `sensors`/`gps_model`, not a first-class "navigation" block (`aerial.py` `GPS_MAP`/`extract_sensor_properties`, `library/sensors/_datos.json`).
- **Kit-identity holes** (`power_connector`, `signal_harness`, `prop_adapter`) are unrelated to mission payload — `KIT_HOME_BLOCK` (`system_architecture_catalog.py:305-309`) ties them to `energy`/`control`/`propulsion` respectively; they nag because their home block is already declared and (for `prop_adapter`) `motors`+`propellers` are already present (`KIT_REQUIRES_COMPONENTS`, line 317-319) — this is BOM completeness noise, structurally unconnected to "vigilancia" as a mission.
- **FC/GPS** stay identity + envelope only (`library/fc/`, `library/sensors/`), confirmed unchanged — no reopening of that P0 needed or suggested here.

## Q3 — Mass/energy coupling

`CalculationEngine.build` (`src/jarvis/core/calculation_engine.py:194-222`) treats `payload_kg` as **one opaque scalar**, feeding `calculate_total_mass(payload_kg, structure_mass_kg + battery_mass_kg + motor_mass_kg)` directly. `battery_mass_kg`/`motor_mass_kg` are **mirrored params** (`COMPONENT_MIRRORED_PARAMS`, `system_architecture_catalog.py:242-257`) — each is zero unless its component is catalog-bound, and is written **only** by that component's own writer (`set_battery_component`/`set_motor_component`), never directly. This is the established, honest pattern for "a real component's cited mass enters total mass."

**If a functional payload component (camera, link) ever gets a real cited mass**, the same mirrored-param pattern is the obvious, already-proven place for it to enter total mass (`camera_mass_kg`, zero when unbound) — **never** silently added on top of the user's own typed `payload_kg` without an explicit UI signal, or the craft's total mass double-counts the same physical kilogram twice. This is the concrete form of the IC's own "double-counting mass" risk (§C): it is not hypothetical, it is exactly what would happen if a camera family's mass were wired into `calculate_total_mass` without also telling the user to lower their own `payload_kg` guess (or, longer-term, deriving `payload_kg` as a computed sum — a much bigger redesign, out of scope here).

No autonomy/endurance target is ever asked as a **design driver** (something the propulsion/energy sizing should aim at) — `autonomy_min` (when mined at all, per Q1) only feeds `engineering_readiness.py`/`project_continuity.py`'s own **readiness check** (comparing achieved vs. target autonomy after sizing), never the other direction (sizing decisions driven by a stated target). Confirmed: `engineering_readiness.py:332`, `716-740`; `project_continuity.py:67-91` all *read* `autonomy_target_min` from `physical_requirements`, none of them feed it forward into a propulsion/battery sizing decision.

## Q4 — Novice spine: ranked Buy options

See §D below (full table). Given the §Q2 finding, my primary recommendation is **not** a new catalog family or a new checklist assist built from scratch — it's finishing and hardening the path that already exists.

## Q5 — Continuity "Aumentar carga útil" (observe only — confirmed, not touched)

`reasoning_layer.py:319-328`:

```python
if not enriched and signals["has_simulation"] and signals["high_margin"]:
    enriched.append(ReasoningSuggestion(
        action="iterate", label="Aumentar carga útil",
        reason="El margen de empuje actual permite explorar más carga útil.",
        priority=0.8, action_type="increase_payload",
    ))
```

`signals["high_margin"] = has_simulation and margin >= HIGH_MARGIN_THRESHOLD` (`reasoning_layer.py:61`) — a **pure thrust-margin-from-simulation** metric. Zero read of `objective`/`restrictions`/mission text anywhere in this function or its callers (confirmed by reading the full signal-computation block; no reference to `objective` exists in `reasoning_layer.py`).

**Existing suppression is unrelated to mission**, confirmed by reading the tests that assert `"Aumentar carga útil" not in cont["next_useful_step"]` (`tests/test_project_continuity.py:407,433,552`, `tests/test_project_coherence.py:98`): every one of them suppresses the suggestion because a **real, unfinished architecture gap** (catalog gap, incomplete BOM) outranks an optimization suggestion — a priority-ordering rule, not a mission-awareness gate. There is no code path today that would suppress "Aumentar carga útil" *because* the objective says "vigilancia" and the BOM has no camera.

**Recommendation:** park, per the IC's own lock #4/§E instruction — do not implement a Continuity rewrite here. The honest coupling point, if a mission-holes Buy ships (§D), is: `reasoning_layer`'s `increase_payload` suggestion should eventually be aware of "does this project have any declared-but-unresolved functional-payload hole" and suppress/soften itself then — but that requires the holes to exist and be inspectable first. Sequencing matters: mission-holes Buy before Continuity-awareness Buy, never the reverse.

---

## A. Create-path map (as-is)

| Step | User answer (vigilancia smoke) | Field written | Enables next | Mission-blind? |
|---|---|---|---|---|
| STEP_VEHICLE | "dron" | `vehicle_type` | aerial step branch | — |
| STEP_OBJECTIVE | "dron de vigilancia doméstico" | `objective` (raw string) | nothing downstream except the autonomy/weight regex (found nothing here) | **YES** |
| STEP_PAYLOAD | "1" (kg) | `payload_kg` | total mass calc | **YES** — no functional breakdown |
| STEP_RESTRICTIONS | "no" | `restrictions` | same regex mining (found nothing) | **YES** |
| STEP_DETAIL | "detallado" | `detail_level` | which create-wizard branch continues (both reach aerial steps; only changes SYSTEM_DEFINITION's recommendation text) | **YES** |
| STEP_AERIAL_MOTORS | "4" | `motors`/`current_parameters["motor_count"]` | propulsion sizing | **YES** |
| *(auto, after confirm)* SYSTEM_DEFINITION offer | *(picked "A" or equivalent, per the smoke narrative)* | `system_blocks = ["propulsion","energy","structure","control"]` | architecture progress / BOM expected keys | **This is the ONE step that COULD have been mission-aware — the hook exists (see Q2) but was skipped** |
| IDLE — catalog picks | "ayúdame a elegir" × N | `components[...]` | montage, per the closed guide | — |

## B. Hole taxonomy

| Concept | Exists as key today? | Catalog? | Mass in energy? | Geometry? | Classification |
|---|---|---|---|---|---|
| camera / gimbal | `cameras` key reachable via SYSTEM_DEFINITION "B", but **no `ComponentRule`** | No `library/` family | No mirrored param | No `_geometry_from_spec` support | **STUB-ONLY** (worse than missing — a dead-end low-completeness row) |
| video tx / goggles path | not a distinct key (`radio_module` is the closest, undifferentiated) | none | none | none | **MISSING** |
| RC / ELRS / radio | `radio_module` key reachable via "B", same dead-end as cameras | none | none | none | **STUB-ONLY** |
| companion computer | no key, no alias | none | none | none | **MISSING** |
| autonomy target (min) | `autonomy_target_min`, mined opportunistically from objective/restrictions text (Q1) | n/a (a number, not a component) | read by readiness checks only, never a sizing input | n/a | **EXISTS**, but as a passive comparison target, not a design driver |
| GNSS (already sensors) | `sensors.gps_model`, real | `library/sensors/` (Holybro M10 cited) | display-only mass, same as any sensor envelope | box envelope when cited | **EXISTS** |
| kit connector/harness/adapter | `power_connector`/`signal_harness`/`prop_adapter` | `library/kit_hardware/` | none (kit rows have no mass field) | box envelope when declared | **EXISTS**, but explicitly NOT a mission-payload concept (§Q2) |
| `arm` (manipulator) | reachable via "B" (`manipulation` block), same dead-end | none | none | none | **STUB-ONLY** |
| Firmware / MAVLink / radio flashing | no key, deliberately | n/a | n/a | n/a | **OUT** (explicit non-goal, §F) |

## C. Coupling risks

- **Double-counting mass**: confirmed real (§Q3) — a future camera/link mass MUST enter total mass via its own mirrored param (matching `battery_mass_kg`/`motor_mass_kg`'s own pattern), and the guide/UX must tell the user to stop including that same kilogram inside their own typed `payload_kg` guess, or the craft is honestly overweight in the model without the user realizing why.
- **ERF BOM INCOMPLETE forever if a hole has no catalog**: already happening TODAY for anyone who takes the existing "B" path (§Q2) — this is not a hypothetical risk of a future Buy, it is a **live bug in the already-shipped SYSTEM_DEFINITION flow**, worth naming to Cursor/Engineer regardless of which Buy is chosen.
- **ASSEMBLY READY while mission undemonstrated**: not observed as an active false claim (`relaciones`/`parece un dron` both stay geometry-scoped and already print "esto no es ASSEMBLY READY" / never claim mission fitness), but a future mission-holes Buy must keep that boundary — a "payload stack checklist" must never be folded into the geometry honesty checklists' own PASS/FAIL language.
- **`sensors` key overloaded (GNSS vs camera)**: not observed as an ACTUAL collision — `cameras` is a structurally separate dict key from `sensors` in the existing (if inert) schema, so there is no naming collision today. The risk is prospective: `extract_sensor_properties`'s own `SENSOR_TYPE_MAP` (IMU/barometer/compass) lives on the `sensors` key too, so a future camera `ComponentRule` should bind to the **separate** `cameras` key already reserved by `BLOCK_TO_COMPONENTS`, not fold camera identity into `sensors` and recreate the overload risk from scratch.

## D. Ranked Buy options

| ID | Shape | In | Out | Risk |
|---|---|---|---|---|
| **B0** | Leave gap; guide-only ("mission before montage" prose pointer in `USER_GUIDE_CRAFT_MONTAGE.md`'s own intro, no code) | docs | code | Novice still lost in CLI; the live SYSTEM_DEFINITION bug (§C) stays unfixed and un-flagged |
| **B1-min fix (recommended primary)** | Fix the already-shipped SYSTEM_DEFINITION dead-end: either (a) gate the "B" block-alias options so `perception`/`communication`/`payload`/`manipulation` are NOT offered/accepted until a `ComponentRule` exists for their keys (fail closed, matches this codebase's own "never invent, never half-ship" discipline), or (b) add the minimal `ComponentRule`s (identity + no invented mass/mm — `completeness` stays `low`/`medium` honestly) so a stub can at least reach a real, inspectable state. **Either branch is a genuinely small, additive, evidence-grounded fix** — no new subsystem, no new catalog family required for (a); (a) is strictly smaller than (b) | `system_architecture_catalog.py` gate or `aerial.py` registry addition | new catalog SKUs, firmware, Continuity rewrite | (a) is nearly risk-free (closes a real bug); (b) risks scope creep into "how much does a camera ComponentRule need to know" without Engineer-supplied evidence bags |
| **B1 wizard nudge** | After `objective` is captured, if it contains an unmapped `BLOCK_ALIASES` term-adjacent keyword (e.g. "vigilancia", "fpv", "carga", "video") that the CURRENT keyword table doesn't already catch, surface a **one-line, suggest-only** nudge pointing at the SYSTEM_DEFINITION "B" option ("¿tu misión necesita cámara/radio/payload? escribe B para añadirlos") rather than a brand-new step | one conditional message in the create-confirm flow | new session mode, new schema field | Keyword brittleness (IC's own named risk) — must stay suggest-only, never gate project creation |
| **B1 catalog family** | `library/cameras` (+ `library/payload`?) with cited seeds, mirrored mass param, `ComponentRule` | new family, needs Engineer evidence bags per SKU | invented mm/g (forbidden) | Needs real Engineer-supplied bags before any seed — same discipline as every prior catalog family this session; do not start without them |
| **Separate ★ (parked)** | Continuity next-step vs. declared mission (couple `increase_payload` suppression to "does this project have an unresolved mission-payload hole") | `reasoning_layer.py` | mission decomposition itself | Easy to overfit to one mission phrasing; sequencing must come AFTER a mission-holes Buy exists, never before |

**Recommendation:** ★ **B1-min fix, branch (a)** first (closes a real, already-shipped honesty bug, smallest possible surface, no new schema) — optionally paired with the **B1 wizard nudge** in the same or an immediately-following cycle, since both are thin and the nudge is what actually helps a novice *notice* the block-alias path exists. Park the catalog family and the Continuity-awareness Buy explicitly until Engineer supplies real evidence bags / more smokes respectively.

## E. Continuity observe (short)

Covered fully in Q5 above — cited, parked, no implementation plan beyond "future IC if ★," per lock #4.

## F. Non-goals confirmed

No firmware generation, no MAVLink, no radio flashing, no companion-app generation — confirmed zero code today does or references any of this (§B, "OUT" row). No montage/geometry work touched or recommended here (plate-box, Path N, Situar are explicitly out per lock #6, and nothing in this investigation's findings depends on them). No invented catalog SKU, mass, or mm anywhere in this report — every number cited above is either a `file:line` reference or a live, read-only census value. No Conversation Engine — the recommended primary Buy (D, "B1-min fix (a)") is a **closed-form gate/fix** on an existing deterministic session class, not a new intent/reasoning layer.

---

## Live census evidence (read-only, no `workspace/` write)

Both reads were plain `json.load` on the existing `state.json` files — no `ProjectState` was constructed, no writer was called, no state was saved.

```text
dron-de-vigilancia-doméstico: objective="dron de vigilancia doméstico",
  payload_kg=1.0, restrictions="no", parsed_constraints={}
  components: motors, propellers, esc, battery, frame, flight_controller,
    sensors, frame_arm, frame_plate(+2,+3), prop_adapter, signal_harness,
    power_connector — no camera/link/comms key present
  system_blocks: [propulsion, energy, structure, control]

10-min-autonomía: objective="10 min autonomía", restrictions="no",
  parsed_constraints={"autonomy_min": 10.0}   # number-in-objective luck, not decomposition
```
