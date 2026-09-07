# Investigation Report — Minimum Sensor KNOW for Aerial Autonomy Claim

**Project:** Jarvis
**Date:** 2026-09-07
**Investigator:** Claude Code
**Contract:** [investigation_contract_minimum_sensor_know_aerial_autonomy_claim.md](investigation_contract_minimum_sensor_know_aerial_autonomy_claim.md)
**Parents:** Control parity CLOSED suite 2164 · Geometry FC B1 CLOSED suite 2332
**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy claim-copy → IC READY  
**Review:** [investigation_review_minimum_sensor_know_aerial_autonomy_claim.md](investigation_review_minimum_sensor_know_aerial_autonomy_claim.md)  
**IC:** [implementation_contract_sensors_bom_honesty_tail_b1.md](implementation_contract_sensors_bom_honesty_tail_b1.md)

**Not an Implementation Contract. No `src/` edits made.** Every physical-capability claim below was live-fetched this session from official manufacturer/project documentation, not assumed from product names.

---

## A. Executive answer

The concern is real and worse, in one specific way, than the contract's own framing suggested. `BLOCK_TO_COMPONENTS["control"] = ["flight_controller", "sensors"]` (`system_architecture_catalog.py:163`), but the ERF verdict function `_control_evidence` reads **only** `flight_controller` presence (`engineering_readiness.py:1077-1083`) — `sensors` never gates the Control subsystem verdict directly. What *does* force a sensor to exist before Control PASS is reachable is the architecture-block completeness gate (`orchestrator.py:2053-2070`), which requires every `BLOCK_TO_COMPONENTS["control"]` key to be non-"low." But `_sensor_completeness` (`aerial.py:715-724`) returns `"medium"` — satisfying that gate — for **any single recognized `gps_model` or `sensor_type`**, with zero distinction between them. Concretely: a project declaring "Pixhawk 4" + "barómetro" closes the `control` architecture block and can reach `Control PASS *` exactly as readily as "Pixhawk 4" + "Here3" — **a barometer is not GPS, and Jarvis's own verdict machinery cannot tell the difference.** This is confirmed structurally, not by example: `sensors` can never reach BOM's `"defined"` tier at all (`classify_component`, `project_closure.py:434-462`, requires `completeness=="high"`, which `_sensor_completeness` never returns) — it is permanently `"declarative"` (◇), while `flight_controller` reaches `"defined"` (✓) the moment a specific model is named. Live-fetched sourcing: Pixhawk 4 carries 2 internal IMUs and an internal barometer but **no internal magnetometer** (PX4 docs); Here3/Here3+ carry a multi-constellation GNSS receiver, an integrated magnetometer, and their *own* separate IMU used for heading/INS fusion, not primary flight control (CubePilot docs). Neither fact is represented anywhere in Jarvis today — `sensors` only ever knows a bare keyword. **Minimum KNOW for Outdoor Waypoint Navigation requires, at minimum, a GNSS-capable fact and a compass/heading-reference fact** — neither is guaranteed by "some sensor declared," and Indoor Position Hold's minimum KNOW is *actively different* (no GNSS need; a modality Jarvis's `SENSOR_TYPE_MAP` doesn't even have vocabulary for), proving the "minimum" is claim-scoped, not universal, exactly as the contract anticipated. **Recommend: claim-copy/honesty-only as the primary Buy** — extend the exact precedent Control parity already set for `flight_controller` ("identidad, sin dato físico") to the sensors line, and name the GNSS/compass gap explicitly in copy — no schema, no catalog, no Control PASS change.

---

## B. As-is inventory

| Surface | Finding | Citation |
|---|---|---|
| Architecture block | `BLOCK_TO_COMPONENTS["control"] = ["flight_controller", "sensors"]` — both keys required, non-"low," for the block to reach `"complete"` | `system_architecture_catalog.py:163`, `orchestrator.py:2053-2070` (`_block_progress_status`, component-type branch) |
| ERF subsystem evidence | `_control_evidence`: `defined = _component_present(ctx.project_state, "flight_controller")` — **sensors is never read.** `calculated` is the same predicate as `defined`; nothing in this function inspects `sensors` at all. | `engineering_readiness.py:1077-1083` |
| Gap builders | Grepped the whole readiness module for any `"sensors"`/`"SENSOR"` gap: **zero results** beyond the component→subsystem label map (`"sensors": "control"`, used only to attribute an unrelated gap's `blocks[]` to a subsystem name, not to create one). **No `GAP-SENSOR-*` type exists.** | `engineering_readiness.py:149-159` (full-module grep) |
| Sensor completeness | `_sensor_completeness`: `("medium", [])` the instant `gps_model` **or** `sensor_type` is present — `"high"` is **not a reachable value**, ever, by design (docstring only documents medium/low). A bare "barómetro" and a declared "Here3" grade identically. | `aerial.py:715-724` |
| FC completeness (contrast) | `_flight_controller_completeness` **can** reach `"high"` (confidence ≥ 0.85, i.e. a specific numbered model like "Pixhawk 4") | `aerial.py:567-581` |
| BOM classification asymmetry | `classify_component` requires `completeness == "high"` **and** measurable **and** no missing fields to reach `"defined"`. `sensors` structurally cannot satisfy the first condition — it is **permanently capped at `"declared"`** → BOM's `"declarative"` bucket (`◇ ... (declarativo)`, `project_closure.py:825-846`). `flight_controller` reaches `"defined"` (`✓`) the moment a specific model is declared. This is the exact asymmetry the parent Control-parity review already named — confirmed here as a structural, permanent property of the current completeness functions, not an incidental gap. | `project_closure.py:360-384` (`_MEASURABLE` includes both `gps_model`/`sensor_type` and `model`), `project_closure.py:434-462` (`classify_component`) |
| Existing honesty precedent | `flight_controller`'s BOM line **already** carries an explicit non-physical-data caveat: `f"{completeness} — identidad, sin dato físico"` — Control parity's own prior work named this exact hazard for FC alone. **Sensors has no equivalent caveat today.** | `project_closure.py:730-748` (`_bom_completeness_tail`) |
| Free-text vocabularies | `FLIGHT_CONTROLLER_MAP` (`aerial.py:523-535`, closed vocabulary incl. `pixhawk_4`), `GPS_MAP` (`aerial.py:628-638`, incl. `here3`/`here3_plus` as **distinct** canonical strings), `SENSOR_TYPE_MAP` (`aerial.py:644-659`, `imu`/`compass`/`barometer` — **no "optical flow," "lidar," "vio," or any indoor-positioning keyword exists**). | `aerial.py:523-659` |
| Geometry FC B1 | Confirmed (per its own closed IC) to attach **only** `length_mm`/`width_mm`/`height_mm` to `pixhawk_4` — no sensing capability fact of any kind. Orthogonal, as the parent review already stated; re-confirmed by reading the live table (`FLIGHT_CONTROLLER_DIMENSIONS`, `aerial.py`, added by the prior IC) — no capability keys present. | prior IC, re-verified this session |
| Energy autonomy (orthogonal, re-confirmed) | `autonomy_min`/hover-energy computation lives entirely in `calculation_engine.py:331-342` + `tools/electricity.py` — a Wh/consumption calculation with **zero** reference to `flight_controller`/`sensors` components. Confirmed structurally disjoint, not just conceptually. | `calculation_engine.py:331-342` |
| Live Board/ERF example | Re-confirmed from the parent contract's own claim: a project can show `Control PASS *` (declaration-only, per its own footnote `"* Control: declaración — sin física de control"`, `adapters/cli/main.py:135`) while `PROJECT STATUS: NOT ASSEMBLY READY` — correct today, and this investigation does not touch that coexistence. | `adapters/cli/main.py:135` |

---

## C. Pixhawk 4 contributed sensing (sourced)

Live-fetched from `docs.px4.io/main/en/flight_controller/pixhawk4.html` this session:

- **IMU (redundant, on-board):** "ICM-20689" (primary), "BMI055 or ICM20602" (secondary) — two independent accelerometer/gyroscope units, both physically on the FMU board.
- **Barometer (on-board):** "MS5611."
- **Magnetometer/compass: NOT on the FMU board.** The page states the compass ("integrated magnetometer IST8310") lives on the *external* GPS/compass module ("GPS: u-blox Neo-M8N GPS/GLONASS receiver"), not the flight controller itself.
- **External interfaces (not sensing capability, but relevant to what "sensors" can attach):** dedicated GPS port, 5 serial ports, 3 I2C, 4 SPI, 2 CAN, analog battery-monitor inputs, RC input (CPPM/Spektrum-DSM/S.Bus).

**What must not be independently re-declared as if new information:** if a user or a future extractor treats "IMU" or "barómetro" as a meaningful additional `sensors` fact for a Pixhawk-4-identified project, that is **redundant with what the FC identity already implies** — not wrong to store, but not new navigation-relevant KNOW either. **What genuinely is missing from the FC alone:** compass/heading reference — Pixhawk 4 has none on-board; it is only ever present via whatever external GPS/compass module is separately declared (the stock bundled M8N+IST8310, Here3, or otherwise).

---

## D. Here3 contributed sensing (sourced)

Live-fetched from `docs.cubepilot.org/here-3/here-3-manual.md` this session (covers both variants; differences noted):

- **GNSS receiver:** "u-blox high precision GNSS modules (M8P-2)," multi-constellation: "GPS L1C/A, GLONASS L1OF, BeiDou B1I."
- **Magnetometer/compass:** integrated ("Built-in Inertial Measurement Unit (compass, gyroscope, and accelerometer), for advanced navigation needs"), exposed to the flight controller as an external DroneCAN/UAVCAN compass.
- **IMU:** integrated, but a **separate** unit from the FC's own — "Here 3: ICM20948," "Here 3+: ICM42688,RM3100." Used for GNSS/INS fusion and heading, not as the flight controller's primary control-loop IMU (that role stays with the FC's own on-board IMUs per §C).
- **Positioning accuracy:** "3D FIX: 2.5 m / RTK: 0.025 m" for both variants — **the RTK figure requires a correction source (base station/service) that is not part of declaring "Here3" alone.** A bare "Here3" declaration honestly supports only the 2.5m standard-fix claim, not the 0.025m RTK claim, unless RTK infrastructure is separately known.
- **Connection:** DroneCAN, 1Mbit/s (Here3) vs 8Mbit/s (Here3+) — the two variants are electronically/protocol-compatible, differing in processor and bus speed, not in which sensors are present.
- **Ambiguity flagged, not resolved:** Jarvis's own `GPS_MAP` already tracks `here3` and `here3_plus` as distinct canonical strings (`aerial.py:630-631`) — correctly avoiding conflating them, consistent with what this source confirms (same sensor set, different silicon/bus speed).

**Contrast with Pixhawk 4's stock bundled GPS (§C):** a simple u-blox M8N + IST8310 compass, standard UART/I2C, no RTK path, no dedicated IMU — a materially different capability tier than Here3, and Jarvis's `GPS_MAP` already has a separate `generic_gps` bucket for the bare "gps" keyword that would (correctly) not claim Here3-tier precision.

---

## E. Minimum KNOW by modality

### Primary: Outdoor waypoint navigation

**NAVIGATION-CAPABLE KNOW bag** (presence facts, not schema):

1. A flight-controller identity capable of autonomous mission execution (Pixhawk-class/ArduPilot/PX4 — already implied by the existing `FLIGHT_CONTROLLER_MAP` identities; not itself sufficient alone).
2. **A GNSS-capability fact** — `gps_model` present and, ideally, not the bare `generic_gps` bucket if precision matters to the claim (per §D's RTK-vs-standard-fix distinction).
3. **A compass/heading-reference fact** — since Pixhawk-class FCs have none on-board (§C), this must come from the declared GNSS/compass module itself (Here3 and the stock bundled GPS both provide one; a hypothetical GPS-only module without a compass would not).
4. Altitude reference (barometer) — **usually already true for any Pixhawk-class FC** (§C) and does not need independent re-declaration once the FC identity is known; naming it here only so the bag is complete, not because Jarvis needs a new field for it.

**What this bag explicitly does NOT claim:** that a mission has been flown, that the EKF converges in practice, that RC-loss/failsafe behavior is configured, or that the specific airframe/vibration environment lets the IMUs function — all AUTONOMOUS FLIGHT CLAIM territory (§F), not KNOW.

### Contrast: Indoor position hold

The minimum bag is **not** a subset or superset of the outdoor one — it is different in kind:

- GNSS is **not required and often not usable** indoors — the outdoor bag's central fact (GNSS-capable) is irrelevant here.
- What outdoor waypoint nav doesn't need at all — a **relative-position sensing modality** (optical flow + rangefinder, a motion-capture/UWB positioning system, or visual-inertial odometry from a companion computer) — becomes the load-bearing fact instead.
- **Jarvis has no vocabulary for this today.** `SENSOR_TYPE_MAP` (`aerial.py:644-659`) recognizes `imu`/`compass`/`barometer` only — no "optical flow," "flujo óptico," "lidar," "rangefinder," or "VIO" alias exists anywhere in the file (confirmed by full-content grep). A user declaring "sensor de flujo óptico" today would simply fail to match any `ComponentRule` keyword and produce no sensor property at all — an honest failure (nothing invented), but a real vocabulary gap, not a design decision.

This asymmetry is the clean proof the contract asked for: the outdoor bag is not "the minimum sensors for any autonomy" — it is wrong (GNSS-centric) for a mode Jarvis's own sensor vocabulary cannot yet even name. A full indoor design is out of scope here, per the contract; this is cited only to establish non-universality.

---

## F. Evidence bar for AUTONOMOUS FLIGHT CLAIM (outdoor waypoint)

Climbing from NAVIGATION-CAPABLE KNOW to AUTONOMOUS FLIGHT CLAIM requires an **operational artifact external to the declared parts list** — no combination of catalog/geometry/identity facts, however complete, can substitute for it:

- A flight log (dataflash/ulog) showing a waypoint mission actually executed on the declared hardware+firmware combination, with GPS fix maintained and EKF/estimator healthy throughout — the standard PX4/ArduPilot evidence artifact for "this configuration flew this modality."
- Or a manufacturer/community capability statement tied to the *exact* declared combination (e.g. "Pixhawk 4 + ArduCopter + Here3 is a documented, widely-flown combination for GPS waypoint missions") — weaker than a log, but a real, citable claim rather than an inference from parts alone.

**This rung is explicitly Deferred as a mechanism, per the contract's own instruction** — Jarvis has no flight-log ingestion path, no simulation-log equivalent for this specific claim, and building one would be exactly the kind of lab-campaign/HD-style evidence wall this investigation is told not to open. Naming the requirement (an artifact, not a fact bag) is sufficient for this cycle; deciding how Jarvis would ever ingest or store such an artifact is out of scope here.

---

## G. Representation options (illustrative only — no decision)

Ranked by how much they change today's model, **not** a recommendation to build any of them this cycle:

1. **Claim-copy only, no schema change** (lowest disturbance): extend the existing `_bom_completeness_tail` FC precedent (`project_closure.py:747-748`) to `sensors`, and/or a CLI note when a modality-relevant capability (GNSS, compass) is entirely absent from any declared sensor. No new field, no new component, no new verdict.
2. **Identity-linked capability facts** (mirrors Geometry FC B1's own pattern, `aerial.py`'s `FLIGHT_CONTROLLER_DIMENSIONS` table): a small, sourced table keyed by canonical `gps_model`/FC `model` stating `provides_gnss: bool`, `provides_compass: bool`, `provides_imu: bool` — declarative, not catalog-bound, same honesty shape as the geometry table. Would let a future (still undecided) display compute "GNSS known: yes/no" without inventing a verdict.
3. **A separate, explicitly-named "navigation readiness" display** cross-referencing option 2's facts against one **named modality's** requirement list (e.g. "Outdoor waypoint: GNSS ✓, compass ✓, IMU ✓ (FC-internal)") — pure read-only projection, never a PASS/verdict, never touching `_control_evidence`. This is the first design that could plausibly need a schema conversation, and is named here only as the shape such a conversation would take, not as a proposal to build it.
4. **A sensor catalog family** (`library/sensors/`, mirroring Battery/Motor/ESC): explicitly the **latest**-appropriate option, per the contract's own locked sequence (KNOW → evidence → catalog decision → validation → implementation) — not proposed for any near-term Buy.

**Default lean on this axis: option 1 only, for now** — the smallest move, reusing an already-shipped precedent, deciding nothing about schema.

---

## H. Honesty / phrase matrix

| Implication | True today? | Over-claim risk | Desired wording |
|---|---|---|---|
| "Pixhawk + Here3 = autonomous drone" | No — both are real, correctly-declared identities, but neither alone nor together constitutes flight evidence (§F) | High — this is the exact collapse the contract names | "Pixhawk 4 + Here3 declarados: KNOW de navegación potencial, no vuelo demostrado." |
| "GNSS present = waypoint flight demonstrated" | No — GNSS presence is one of several NAVIGATION-CAPABLE KNOW facts (§E), not the flight evidence itself (§F) | High | Never state GNSS presence and flight capability in the same clause without the KNOW/CLAIM distinction. |
| "Control PASS * = Autonomous PASS" | No, and structurally cannot become so without a code change no one has made — `_control_evidence` doesn't even read `sensors` (§B) | High — the sharpest finding this session: Control PASS today doesn't even require GNSS-class sensing, only *some* recognized sensor keyword | Footnote already says "declaración — sin física de control" (`adapters/cli/main.py:135`) — accurate; extend the same discipline to any sensors-adjacent copy, per §G option 1. |
| "Energy ~N min = navigational autonomy" | No — confirmed structurally disjoint code paths (§B) | Medium — same English word, unrelated computation | Keep "autonomía energética" and "autonomía de navegación" as visibly distinct terms wherever both could appear near each other. |
| "Here3 dims = navigation capability" (Geometry axis) | No — Geometry FC B1 confirmed to carry zero capability facts, dims only (§B) | Low, already guarded by the prior IC's own non-goals | No change needed; cited here only to close the loop the contract asked for. |
| **(new)** "A declared barometer means GPS is present" | **This is the literal, structural default today** — `_sensor_completeness` cannot distinguish them, and neither can the architecture-block gate that lets Control reach PASS (§B) | **Highest-priority finding of this report** — not a hypothetical, a confirmed code path | Any future copy touching "sensors declared" must not imply GNSS/compass presence without checking the specific `gps_model`/`sensor_type` value, never the bare fact that *a* sensor exists. |
| **(new)** "Declaring 'IMU' for a Pixhawk-4 project adds new capability" | Partially misleading — the FC already has 2 IMUs on-board (§C); an independently declared `sensor_type=imu` is redundant information, not new navigation KNOW | Low/cosmetic, but worth naming for anyone designing option 2/3 in §G later | If a capability table (§G option 2) is ever built, it should not double-count an internal-to-FC capability as if a separate declared sensor were the only source of it. |

---

## I. Buy options + default lean

| Option | What | When to Buy |
|---|---|---|
| Defer all code | Ship nothing, revisit later | Not recommended — the barometer/GPS conflation (§H) is a live, confirmed honesty gap worth a same-cycle, near-zero-risk fix |
| **Claim-copy / honesty only** | Extend the FC BOM-tail precedent to sensors; name the GNSS/compass gap in relevant copy; no schema, no new field, no catalog | **Recommended — see below** |
| KNOW model investigation follow-up | A dedicated, later investigation to design §G option 2/3's capability-fact shape properly (which facts, which identities, provenance discipline) before any code | Reasonable **second** step, not this Buy — the contract itself asks not to decide schema this cycle |
| Geometry Here3 dims (orthogonal) | Add `length_mm`/`width_mm`/etc. to Here3, mirroring FC B1 | Legitimate, separate Geometry-axis Buy — explicitly does not touch the autonomy-claim question (§B, re-confirmed) — could proceed independently of this investigation's own recommendation |
| Sensor catalog | `library/sensors/` | Explicitly late per the locked sequence (§3.4 of the contract) — not proposed |

### Default lean: **Claim-copy / honesty only**

The smallest move that prevents the specific collapse this investigation found: extend `_bom_completeness_tail`'s existing FC pattern (`"{completeness} — identidad, sin dato físico"`) to a sensors-appropriate equivalent (e.g., naming that a declared sensor type is not itself a GNSS/compass guarantee), and/or a CLI-level note distinguishing "control declared" from "navigation-relevant sensing known." No verdict logic changes, no `_control_evidence` change, no new component, no catalog. This directly serves the contract's own success criterion (keep CONTROL DECLARED distinct from NAVIGATION-CAPABLE KNOW) without licensing any promotion.

**Suggested first IC title (for Cursor, not decided here):** *"Sensors BOM/CLI honesty tail (GNSS/compass presence ≠ generic sensor presence) — copy only, no schema."*

---

## J. Non-goals for any first follow-on IC

Implementing a capability-fact schema (§G options 2-4) · `library/sensors/` · Continuity sensor wizard · changing `_control_evidence`/Control PASS verdict logic · Assembly Ready rewrite · Geometry dims on Here3 as a substitute for capability facts (orthogonal, separate Buy if pursued) · CAD/FEA · energetic-autonomy model changes · indoor-positioning vocabulary (`SENSOR_TYPE_MAP` additions) as a side effect of this claim-copy fix · Prop/Energy HD-004 unlock · System Optimization · Conversation Engine · version bump · inventing any datasheet fact beyond what §C/§D cite · weakening tests.
