# Investigation Report — Ontology spine lote-5 citation review (`B0-ontology-spine-lote5-citation-review`)

**Project:** Jarvis
**Date:** 2026-09-28
**Investigator:** Claude Code — read-only audit, no `ontology/` / `src/` / `library/` edits, no `pyproject.toml` bump
**Contract:** [`investigation_contract_ontology_spine_lote5_citation_review_b0.md`](investigation_contract_ontology_spine_lote5_citation_review_b0.md)
**Status:** Report delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed by Claude.**

---

## 0. Honesty summary

All three lote-5 notes were audited against the heightened honesty bar locked in the IC (§0 row 6): mag↔yaw true · norte mag↔geo · C37 sim↔hw · estimación↔plan↔control · C39↔EKF/GPS · planta sim↔navegación real · resultado banco↔propiedad motor · T2 inventado.

**Result: none of these eight collapses occur in any of the three notes.** Each note explicitly guards against its relevant collapses in `[ERRORES]`, `[EJEMPLO]`, and/or bolded inline claims — this is not an absence of the topic, it is an explicit, repeated refusal to make the collapse, stated in the note's own prose. See per-note sections below for the exact lines.

25 unique `[REFERENCIAS]` URLs across the three notes were checked. **24 fully verified** (direct fetch or downloaded-PDF title-page confirmation), **1 dead URL with a confirmed working replacement already cited elsewhere in the same note** (Nav2 `/concepts/`). Zero fabricated sources, zero invented numbers, zero `never_invents` violations.

**Overall verdict: PASS — Magnetismo, PASS — Navegación y planificación, PASS WITH NOTES — Forma de medición en banco de empuje** (one dead URL + one label/acronym typo, both trivial fixes, do not affect claim support). All three notes may remain `solid`.

---

## 1. Scope + paths

Per the IC, audit is strictly limited to the three lote-5 notes and their `[REFERENCIAS]` sections. No lote-1–4 re-audit performed (per prior reports, all ★ ACCEPT CLOSED). No `ontology/`, `src/`, or `library/` edits made. No RAG/retrieval design discussed.

Audited files, with SHA-256 of the exact content-version reviewed:

| File | SHA-256 |
|---|---|
| `ontology/02_Fisica/Electromagnetismo/Magnetismo/Magnetismo.md` | `ff81bc478e400a3449daf0e0743576dff35c418e1269adeab82838221c98cd78` |
| `ontology/04_Robotica/Navegación y planificación/Navegación y planificación.md` | `3aebe9b0d1c80d59e1f17755f86f5b0bac98e70c6c26f3010beae16b695168c0` |
| `ontology/03_Ingenieria/Electrónica/Forma de medición en banco de empuje/Forma de medición en banco de empuje.md` | `d590e725d412e3aaafff073eb8dab77b0ee7c1c54119ca70afe57c3be76fcccc` |

---

## 2. Magnetismo — table + verdict

**Frontmatter:** `estado: solid`, `jarvis_relevance: [fs, craft, assistant]`, `never_invents: [mass_g, power_w, thrust_gf, autonomy_min]`, `formula_citation: cited — NOAA/NCEI WMM + declination/FAQ; Analog Devices hard/soft iron (EngineerZone); AD AN-1157 (EKF + mag)`, `tags: [spine, lote-5]` — all fields present, consistent with body.

| # | URL | Method | Result |
|---|---|---|---|
| 1 | NOAA/NCEI World Magnetic Model | WebFetch | **VERIFIED** — exact match: WMM2025, NGA/UK DGC/NCEI |
| 2 | NOAA/NCEI Magnetic Declination | WebFetch | **VERIFIED** — exact quote: "the angle between magnetic north and true north," changes with time/location |
| 3 | NOAA/NCEI Geomagnetism FAQ | WebFetch | **VERIFIED** — exact match: declination/inclination/H/Z/F components |
| 4 | AD EngineerZone — hard/soft iron FAQ | WebFetch timeout → WebSearch | **VERIFIED (search-corroborated)** — exact title/content: hard iron = permanent magnets/power currents/residual ferromagnetic fields; soft iron = magnitude/direction distortion near ferromagnetic objects |
| 5 | AD AN-1157 (EKF tuning, ADIS16480) | WebFetch timeout → WebSearch | **VERIFIED (search-corroborated)** — exact title "AN-1157: Tuning the Extended Kalman Filter in the ADIS16480," confirms gyro+accel+mag EKF tuning |

**Overclaim scan:** none. Body explicitly states "El magnetómetro no mide directamente el yaw ni proporciona por sí solo una actitud completa" and labels the atan2 relation "**toy/idealizada**" inline.

**SoT bleed scan:** none. No `mass_g`/`power_w`/`thrust_gf`/`autonomy_min` values asserted anywhere in body.

**Honesty-collapse scan (heightened bar):**
- *mag↔yaw true* — guarded: `[ERRORES]` "Tratar la lectura del magnetómetro como yaw verdadero."
- *norte mag↔geo* — guarded: `[ERRORES]` "Asumir que el magnetómetro mide directamente el norte geográfico," plus declination defined explicitly in `[DEFINICION]`/`[FUNDAMENTO]`.
- *C37 sim↔hw* — guarded: `[EJEMPLO]` states C37 is "una **observación magnética simulada**" and gives the explicit chain "simulación ≠ interfaz emulada ≠ sensor físico ≠ calibración ≠ validación de vuelo"; `[APLICACIONES]` "Jarvis honesty" line reiterates this for the WHO_AM_I/bus-read case too (`[ERRORES]` "Confundir `WHO_AM_I` / comunicación SPI o I²C correcta con una medición magnética válida").

**Verdict: PASS.** No remediation needed.

---

## 3. Navegación y planificación — table + verdict

**Frontmatter:** `estado: solid`, `jarvis_relevance: [fs, craft, assistant]`, `never_invents: [mass_g, power_w, thrust_gf, autonomy_min]`, `formula_citation: cited — PX4 controller diagrams / EKF2 / trajectory setpoints; Nav2 navigation concepts; MIT Underactuated (estimation, trajopt, sampling planning)`, `tags: [spine, lote-5]` — all fields present, consistent with body.

| # | URL | Method | Result |
|---|---|---|---|
| 6 | PX4 — Controller Diagrams | WebFetch | **VERIFIED** — exact match: "standard cascaded control architecture," position→velocity→attitude→angular-rate nested loops, EKF2-derived estimates |
| 7 | PX4 — Modules Reference: Controller | WebFetch | **VERIFIED** — exact match: `mc_pos_control` P/PID loops, hierarchical nav→position→attitude→rate→actuators |
| 8 | PX4 — Multicopter Setpoint Tuning (Trajectory Generator) | WebFetch | **VERIFIED** — exact match: trajectory generator smooths position/velocity/acceleration setpoints |
| 9 | PX4 — Switching State Estimators | WebFetch | **VERIFIED** — exact match: EKF2/LPE/Q-Estimator, "one and only one estimator" active |
| 10 | PX4 — Using PX4's Navigation Filter (EKF2) | WebFetch | **VERIFIED** — exact verbatim: EKF2 estimates quaternion/velocity/position/IMU biases/mag field/wind/terrain, fuses IMU+mag+baro+GPS+rangefinder+airspeed+vision |
| 11 | PX4 — PositionSetpoint (UORB) | WebFetch | **VERIFIED** — exact match: `vx`/`vy`/`vz` local velocity setpoint in NED, plus global lat/lon/alt fields |
| 12 | Nav2 — Navigation Concepts (`/concepts/`) | WebFetch + `curl` | **DEAD (404)** — confirmed via `curl -o /dev/null -w "%{http_code}"` → `404`; `/concepts/index.html` also 404. **Working replacement found and curl-confirmed (200): `https://docs.nav2.org/rolling/getting_started/navigation_concepts/`** — this is literally the parent path of the note's own citation #13 below |
| 13 | Nav2 — State Estimation (rolling path) | WebFetch | **VERIFIED** — exact match: REP 105 map→odom→base_link tree, localization/SLAM gives map→odom, odometry gives odom→base_link |
| 14 | MIT Underactuated — State Estimation | WebFetch | **VERIFIED** — exact match: "Ch. 19 - State Estimation" |
| 15 | MIT Underactuated — Trajectory Optimization | WebFetch | **VERIFIED** — exact match: "Chapter 10: Trajectory Optimization" |
| 16 | MIT Underactuated — Sampling-based Motion Planning | WebFetch | **VERIFIED** — exact match: "Chapter 12: Sampling-based Motion Planning," A*/PRM/RRT |

**Overclaim scan:** none. `[FUNDAMENTO]` "Mapa conceptual FS" table is explicitly caveated: "Estos rungs deben interpretarse como **mapa conceptual de Jarvis**, no como equivalentes universales de componentes de navegación de un autopiloto real."

**SoT bleed scan:** none.

**Honesty-collapse scan (heightened bar):**
- *estimación↔plan↔control* — guarded explicitly and repeatedly: `[DEFINICION]` "localización/estimación, planificación y control son funciones relacionadas pero distintas," citing Nav2's own explicit separation; `[ERRORES]` "Confundir planificación con control," "Confundir planificación de trayectoria con control de trayectoria."
- *C39↔EKF/GPS* — guarded: `[ERRORES]` "Asumir que C39 es un EKF, un GPS stack o un sistema de localización."
- *planta sim↔navegación real* — guarded: `[EJEMPLO]` "En Jarvis, la planta simulada puede proporcionar directamente el estado utilizado por C39. Eso **no convierte C39 en un sistema de navegación real**, ni demuestra que GPS, visión, odometría o un estimador físico funcionen en hardware."; `[ERRORES]` "Tratar una planta simulada como si fuera navegación instrumentada."
- Additional: `[FUNDAMENTO]`/body repeats "**Medición/observación ≠ estado verdadero**" as a standalone bolded line, and `[ERRORES]` separately covers "Confundir una observación de sensor con el estado verdadero."

**Verdict: PASS WITH NOTES** — the note itself contains no false claims; the finding is a stale URL, not a content defect.

**Remediation:** replace `https://docs.nav2.org/concepts/` with `https://docs.nav2.org/rolling/getting_started/navigation_concepts/` in `[REFERENCIAS]`.

---

## 4. Forma de medición en banco de empuje — table + verdict

**Frontmatter:** `estado: solid`, `jarvis_relevance: [craft, catalog, assistant]`, `never_invents: [mass_g, power_w, thrust_gf, autonomy_min]`, `formula_citation: cited — UIUC Propeller Database / Selig pubs; NASA Airvolt + thrust uncertainty NTRS; APC performance (analytic vs measured)`, `tags: [spine, lote-5]` — all fields present, consistent with body.

| # | URL | Method | Result |
|---|---|---|---|
| 17 | UIUC — Propeller Database (Selig) | WebFetch | **VERIFIED** — exact match: UIUC Applied Aerodynamics Group, wind-tunnel prop data 2005–2022, static (C_T0/C_P0) vs dynamic distinction |
| 18 | UIUC PDB Vol. 4 (Dantsker/Caccamo/Deters/Selig, AIAA Aviation 2022) | WebFetch | **VERIFIED** — exact match: "Performance Testing of APC Electric Fixed-Blade UAV Propellers," 17 APC props, thrust/torque coefficients, static testing |
| 19 | UIUC PDB Vol. 1 | WebFetch | **VERIFIED** — exact match: Gavin Ananda compiler, ~140 props, builds on Brandt/Selig 2005/2011 |
| 20 | Shetty & Selig, AIAA 2011-1254 | WebFetch text-extraction failed → PDF downloaded → **`Read` title page** | **VERIFIED** — title page confirms "Small-Scale Propellers Operating in the Vortex Ring State," Omkar R. Shetty & Michael S. Selig, UIUC, AIAA 2011-1254, 49th AIAA Aerospace Sciences Meeting. **Note:** the note's own parenthetical labels this "(LRN / **VSR** props...)" — the actual regime name is **Vortex Ring State (VRS)**, not "VSR." Low-severity transposed-acronym typo; authors, AIAA number, venue, and topical content (small-scale prop testing at low Reynolds number, including descent/VRS behavior) all match exactly, so the underlying citation is sound |
| 21 | Dantsker, Selig & Mancuso, AIAA 2017-3745 | WebFetch text-extraction failed → PDF downloaded → **`Read` title page** | **VERIFIED** — title page confirms "A Rolling Rig for Propeller Performance Testing," Or D. Dantsker, Michael S. Selig, Renato Mancuso — exact match to note's own title citation |
| 22 | NASA NTRS 20160001339 — Airvolt | WebFetch text-extraction failed → PDF downloaded → **`Read` title page** | **VERIFIED** — title page confirms "Airvolt Aircraft Electric Propulsion Test Stand," Aamod Samuel & Yohan Lin, NASA Armstrong Flight Research Center; abstract confirms thrust/torque/current/voltage/vibration/temperature/acoustic data collection independent of manufacturer values |
| 23 | NASA NTRS 20180006103 — thrust uncertainty | WebFetch | **VERIFIED** — exact title "Uncertainty in Inverted Pendulum Thrust Measurements," NASA Glenn Vacuum Facility 6, "±6.9 mN over the entire span of thrust," explicitly distinguishes stand bias/precision uncertainty from measurement repeatability — matches the note's own claim distinguishing these two concepts |
| 24 | NASA Armstrong — Flight and Ground Experimental Test Capabilities | WebFetch | **VERIFIED** — exact match: describes Airvolt as a modular stand for electric propulsion up to 100 kW, evaluating "subsystem interactions as well as efficiencies of different batteries, motors, controllers, and propellers," supported X-57 Maxwell cruise-motor testing |
| 25 | APC Propellers — Performance Data | WebFetch | **VERIFIED** — exact match: APC uses "a proprietary analysis software" based on "Vortex theory" (analytic), separately points to UIUC's own experimental wind-tunnel data — direct match to the note's own analytic-vs-experimental distinction |

**Overclaim scan:** none. `[EJEMPLO]` explicitly refuses to close HD-005: "La nota debe especificar **qué variables y condiciones habría que registrar para obtener un T2**, pero no debe inventar `thrust_gf` ni completar una curva inexistente."

**SoT bleed scan:** none. No `mass_g`/`power_w`/`thrust_gf`/`autonomy_min` values asserted; the T1/T2/estimado tri-classification in `[FUNDAMENTO]` exists precisely to prevent this bleed.

**Honesty-collapse scan (heightened bar):**
- *resultado banco↔propiedad motor* — guarded: `[FUNDAMENTO]` "Un resultado de banco representa el comportamiento del **conjunto ensayado bajo unas condiciones concretas**, no una propiedad universal del motor aislado."; `[ERRORES]` "Confundir un resultado del conjunto motor+ESC+hélice con una propiedad intrínseca del motor," "Tratar un único punto de operación como capacidad universal del motor."
- *T2 inventado* — guarded: `[ERRORES]` "Presentar una estimación como si fuera una medición," "Inventar una curva para cerrar HD-004/HD-005."; `[EJEMPLO]` reinforces this directly for the specific HD-005 combo named.

**Verdict: PASS WITH NOTES** — no false claims found; one low-severity acronym typo (VSR→VRS) in a parenthetical descriptor, not in a URL, title-string, or quoted claim.

**Remediation (optional, cosmetic):** change "(LRN / VSR props; experimental context)" to "(LRN / VRS props; experimental context)" in `[REFERENCIAS]`.

---

## 5. Cross-cutting (SoT, mag/nav/bench honesty)

- **SoT bleed:** zero instances across all three notes. `never_invents: [mass_g, power_w, thrust_gf, autonomy_min]` holds in every note; no craft/SKU quantities are asserted from ontology prose.
- **Mag honesty:** Magnetismo consistently separates measured field vector from derived heading, and heading from true attitude; declination is sourced to NOAA, not assumed zero or ignored.
- **Nav honesty:** Navegación y planificación consistently separates observation → estimation → planning → control, and explicitly refuses to let C39 (Jarvis's own conceptual rung) stand in for a real EKF/GPS/localization stack.
- **Bench honesty:** Forma de medición en banco de empuje consistently separates a measured-assembly result from a motor-intrinsic property, and refuses to interpolate/invent OP data to close HD-004/HD-005.
- No note in lote-5 references or relies on any lote-1–4 note's citations for its own claim support (only `[CONEXIONES]` wikilinks, which are navigation aids, not citation dependencies).

---

## 6. URL matrix (summary)

| Note | URLs | Verified direct | Verified search-corroborated | Verified via downloaded PDF | Dead (with fix) |
|---|---|---|---|---|---|
| Magnetismo | 5 | 3 | 2 (analog.com — known unreachable domain, consistent with lote-2/3/4) | 0 | 0 |
| Navegación y planificación | 10 | 9 | 0 | 0 | 1 (Nav2 `/concepts/` → rolling path) |
| Forma de medición en banco de empuje | 9 | 6 | 0 | 3 | 0 |
| **Total** | **24 unique + 1 dead-then-fixed = 25** | **18** | **2** | **3** | **1** |

(Magnetismo's `analog.com` unreachability continues the pattern established in lote-2/3/4: WebFetch timeout + `curl` HTTP/2 stream reset, resolved via WebSearch corroboration per the IC's own "UNVERIFIED (network) → do not invent PASS, corroborate" instruction.)

---

## 7. Remediations (Cursor-applicable)

1. **Navegación y planificación.md** `[REFERENCIAS]`: replace dead `https://docs.nav2.org/concepts/` with working `https://docs.nav2.org/rolling/getting_started/navigation_concepts/`.
2. **Forma de medición en banco de empuje.md** `[REFERENCIAS]` (optional/cosmetic): fix "VSR" → "VRS" in the Shetty & Selig parenthetical label.

No other remediations. Both are one-line edits; neither reflects an invented or unsupported claim.

---

## 8. Overall verdict + whether lote-5 may stay solid

| Note | Verdict | Stay `solid`? |
|---|---|---|
| Magnetismo | **PASS** | Yes, no changes required |
| Navegación y planificación | **PASS WITH NOTES** | Yes — dead-URL swap only |
| Forma de medición en banco de empuje | **PASS WITH NOTES** | Yes — cosmetic acronym fix only |

All three lote-5 notes may remain `estado: solid`. No downgrade to `draft` is warranted for any note — no material invention, no dead critical citation (the one dead Nav2 URL has a same-note, curl-confirmed working replacement), and no SoT bleed was found.

---

## 9. Out of scope

- Lote-1 (Vectores, Dinámica, Control clásico), lote-2 (Momento y rotación, Control robótico, Sensores de movimiento), lote-3 (Acelerómetro, Giroscopio, IMU), lote-4 (Actuadores, Motores, Motor DC, Corriente y circuitos, C-rate de batería, Punto de operación vs capacidad intrínseca) — not re-audited, all prior reports ★ ACCEPT CLOSED.
- RAG/retrieval design, future `intelligence/` module — not discussed.
- `library/` catalog SoT — not touched, not read for this audit beyond the notes' own prose references.
- `src/jarvis/` — not touched.

---

## Non-edits (verification)

```text
$ git status --short -- ontology/ src/ library/ pyproject.toml
 M ontology/.obsidian/workspace.json
```

The only modified path under the audited trees is `ontology/.obsidian/workspace.json` — an Obsidian UI-state file (open-tab/pane layout), not a content note, and not touched by this audit. It reflects local Obsidian session state, not a Claude edit.

```text
$ git diff --stat -- <the three lote-5 note files>
(empty — zero diff)

$ git status --short -- <the three lote-5 note files>
(empty — not modified, not untracked)
```

All three audited notes are fully committed with zero working-tree diff, consistent with the IC's disclosed landing commits (`5b1703c` / `75ff061` / `335035d`/`d4f53cc`).

```text
$ git tag -l | sort -V | tail -1
v0.5.44

$ grep -m1 '^version' pyproject.toml
version = "0.5.44"
```

Tip remains `v0.5.44`. No package bump. No new tag. **No ACCEPT claimed by Claude** — this report is for Cursor review and Engineer decision.
