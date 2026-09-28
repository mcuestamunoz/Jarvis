# Ontology crosswalks — FS · HD · Geometry

**Status:** Docs teach only (ONT-docs) · landed 2026-09-28 · ontology branch **CLOSED @ `v0.6.0`**  
**Epoch:** explain SoT ready for Assistant **`0.6.1+`** (R2) · runtime read-only retrieve now exists under `src/jarvis/intelligence/ontology_retrieve.py` (`B1-ontology-retrieve-r2`, package `0.6.2`) — exact `id`/`nombre` lookup only, still not Continuity SoT  
**Vision:** [`JARVIS_KNOWLEDGE_VISION.md`](JARVIS_KNOWLEDGE_VISION.md) §5 B/C/D/G · §6 seams  
**Vault:** [`ontology/`](../ontology/README.md) · spine lotes 1–5 solid + cite-audited  
**Close:** [`engineer_note_v0_6_0_ontology_epoch_close.md`](../.jes/artifacts/engineer_note_v0_6_0_ontology_epoch_close.md)

This file maps **product surfaces → concept notes**. It does **not** authorize `src/` imports of `ontology/`, catalog writes, HD curve invention, or treating sim rungs as flight validation.

```text
ontology/     EXPLAINS
docs/         cites (this file)
✗ Continuity / library / flight_software / native  — do not read ontology to decide or compute
```

---

## 1) FS ladder ↔ ontology (explain map)

Paths are under `ontology/`. Notes listed are **solid** spine nodes unless noted. Use for human onboarding and future cite ICs — **never** as SoT for `step()`, gains, or WHO_AM_I.

| Rung / module (illustrative) | Role (one line) | Ontology explain |
|---|---|---|
| C3 `ImuHal` / sim IMU | Sensing contract | [[Sensores de movimiento]] · [[IMU]] |
| C6 IMU filter | Post-process samples ≠ attitude | [[IMU]] · [[Sensores de movimiento]] |
| C7 complementary attitude | Estimate attitude from accel+gyro | [[IMU]] · [[Giroscopio]] · [[Acelerómetro]] · [[Control robótico]] · [[Vectores]] |
| C8 PD attitude → body rates | Control rates, not motor forces | [[Control clásico]] · [[Control robótico]] · [[Momento y rotación]] |
| C9 Quad-X mixer | Allocation of forces/moments | [[Actuadores]] · [[Control robótico]] · [[Momento y rotación]] |
| C10 ESC PWM stub | Command encoding ≠ physical torque | [[Actuadores]] · [[Motores]] · [[Motor DC]] |
| C11–C12 / plant + rate bridge | Toy plant / typed bridge | [[Dinámica]] · [[Control robótico]] |
| C24 `step()` tick | Named control tick; plant outside | [[Control robótico]] · [[Navegación y planificación]] |
| C31 DShot encode (RAM) | Frame in memory ≠ GPIO | [[Motor DC]] · [[Actuadores]] |
| C36 6-DoF plant | Sim plant outside `step` | [[Dinámica]] · [[Navegación y planificación]] |
| C37 mag yaw (sim) | Mag observation ≠ true heading | [[Magnetismo]] · [[IMU]] |
| C38 altitude loop | z → collective (sim) | [[Control robótico]] · [[Navegación y planificación]] |
| C39 position loop | xy → tilt (sim) | [[Navegación y planificación]] · [[Control robótico]] |
| C40–C41 autonomy / safety sim | Setpoints + allowlist ≠ execute | [[Navegación y planificación]] · [[Control robótico]] |
| C42 ICM WHO_AM_I on `ScriptedSpi` | Identity on bus ≠ calibration/flight | [[IMU]] · [[Sensores de movimiento]] |
| C43 craft↔FS bind | Profile reads craft identity | craft SoT ≠ ontology; see vault README |

**Honesty locks (FS):** sim ≠ copper · filter ≠ estimator ≠ true attitude · mixer command ≠ thrust known · WHO_AM_I ≠ calibrated IMU · C39 ≠ EKF/GPS stack.

C++ parity under `native/flight_control/` follows the same explain map; see [`native/flight_control/README.md`](../native/flight_control/README.md).

---

## 2) HD-* / lab ↔ ontology (evidence shape)

HD items stay in [`HARDWARE_DEBT.md`](HARDWARE_DEBT.md). Ontology states **what kind of evidence** is missing — never invents the missing numbers.

| HD | Missing evidence (concept) | Ontology |
|---|---|---|
| HD-001 | C-rate → usable capacity under load | [[C-rate de batería]] · [[Corriente y circuitos]] · [[Punto de operación vs capacidad intrínseca]] |
| HD-002 | ESC loss η / isolated P_pack vs P_motor | [[Corriente y circuitos]] · [[Actuadores]] · [[Motores]] |
| HD-003 | Sag / OCV / R_internal | [[Corriente y circuitos]] · [[C-rate de batería]] |
| HD-004 | OP→consumption curve (autonomy wall) | [[Forma de medición en banco de empuje]] · [[Punto de operación vs capacidad intrínseca]] · [[Motores]] |
| HD-005 | Craft OP XING-E + 51466-3 + 4S | [[Forma de medición en banco de empuje]] · [[Punto de operación vs capacidad intrínseca]] · [[Motor DC]] |

**Honesty locks (HD):** T1 ≠ T2 ≠ estimado · stand set ≠ motor intrinsic · thrust without conditions is not a reusable OP · never fake HD-004/005 curves from ontology.

---

## 3) Geometry / Board literacy

Geometry code and `library/` fixtures remain the SoT for dimensions. Ontology (and this table) only teach confusions that keep reappearing in Board / Structure reports.

| Confusion | Correct split |
|---|---|
| Envelope / AABB drawn on Board | **Not** a CAD solid or manufacturable fit |
| Slot / plate pose in visor | Layout / mounting intent — **not** tolerance stack-up |
| Catalog `dims_mm` / sourced dims | Cited fixture data in `library/` — **not** from ontology notes |
| “Looks centered” in Taller CSS | Visual assist — **not** metrology |

When a structural/mech note is later solid (e.g. under `03_Ingenieria/Mecánica estructural`), link it here. Until then, this section is the standing literacy lock.

**Honesty locks (geometry):** envelope ≠ CAD · AABB ≠ fit · visor ≠ caliper · ontology never supplies Δmm for a SKU.

---

## 4) Catalog honesty (pointer)

Standing vocabulary already solid in lote-4/5:

- [[Punto de operación vs capacidad intrínseca]]
- [[Forma de medición en banco de empuje]]
- [[Corriente y circuitos]] (incl. RF ≠ DC)
- [[C-rate de batería]]
- [[Motores]] / [[Motor DC]] / [[Actuadores]]

`ComponentLibrary` does **not** read these notes.

---

## 5) Non-goals

- Importing `ontology/` from `src/` or `native/` **until** Assistant R2 IC ★
- Replacing `library/` rows with note prose
- Closing any HD-* by inventing OP tables
- Claiming FS rungs are flight-validated because a note exists
- RAG / Assistant retrieve without cola A0–A2 ([`IMPLEMENTATION_TASKS.md`](IMPLEMENTATION_TASKS.md) PRIORIDAD)

**Next product use:** Assistant path — ★ DC placement → `intelligence/` scaffold → read-only spine retrieve → terminal “¿por qué?”.
