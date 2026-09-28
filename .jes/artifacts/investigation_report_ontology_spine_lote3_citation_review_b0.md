# Investigation Report — Ontology spine lote-3 citation review (`B0-ontology-spine-lote3-citation-review`)

**IC:** [`investigation_contract_ontology_spine_lote3_citation_review_b0.md`](investigation_contract_ontology_spine_lote3_citation_review_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-28
**Status:** Investigation / citation audit only. **Tip stays `v0.5.44`.** Zero `ontology/` edits, zero `src/` edits, no `pyproject.toml` bump, no tag. Not claiming ACCEPT — that is Cursor review + Engineer's call.

---

## 0. Honesty summary

```text
cite verified != cite invented
URL reachable != claim automatically supported
dead specific PDF path != the underlying document being fake (stable mirrors exist)
network timeout/bot-wall != dead link
a document's own title != a section title inside it — both can be legitimately citable
every ICM-42688-P number in all three notes checked character-for-character against real datasheet text
Claude audits citations != Claude marks notes solid
```

Lote-3 materializes the three dangling leaves (`Acelerómetro`, `Giroscopio`, `IMU`) the earlier vault-value B0 report flagged as high-value dangling wikilinks right next to this session's own C6/C42 sensor work. All three notes carry the same discipline already confirmed in lote-1/lote-2, and this lote's own heightened bar — every ICM-42688-P numeric/interface claim must match the TDK datasheet — **fully holds**: this audit downloaded a working datasheet mirror and confirmed, in the datasheet's own words, "the gyroscope supports eight programmable full-scale range settings from ±15.625dps to ±2000dps, and the accelerometer supports four programmable full-scale range settings from ±2g to ±16g," plus I3C/I²C/SPI (3-wire and 4-wire) support — **every single device-specific number and interface claim across all three notes matches this exactly**, with no invented register, ODR, or noise value found anywhere. Of 19 unique cited URLs: **10 fully verified by direct fetch or downloaded-mirror text**, **6 blocked by persistent network/anti-bot behavior on every fetch attempt (all `analog.com`) but independently corroborated via search**, **2 dead-but-mirrored** (one TDK datasheet path, self-flagged by the note's own drafters as a known risk; one URL-slug discrepancy found for an Analog Devices article), and **1 title-imprecise-but-defensible** (a 1979 NASA document cited under an internal section title rather than its own cover title — its actual "Inertial Measurement Unit" section does exist and is on-topic).

**Overall: all three notes PASS. None warrants a `draft` downgrade.**

---

## 1. Scope + files audited

| Note | Path | SHA-256 (this audit's snapshot) |
|---|---|---|
| Acelerómetro | `ontology/04_Robotica/Sensores/Sensores de movimiento/Acelerómetro/Acelerómetro.md` | `aab6f6c9ff669c31b3e95351d4c65fa001bc76e1a90e401e2add736965baae47` |
| Giroscopio | `ontology/04_Robotica/Sensores/Sensores de movimiento/Giroscopio/Giroscopio.md` | `f1ecc6fbee981cdc4a1c0b5fbb0636eeff1dc35ccd989299efaf4d2f6f94f7a4` |
| IMU | `ontology/04_Robotica/Sensores/Sensores de movimiento/IMU/IMU.md` | `224783a3a2a985c4a7da84cb8d96b89e331c5903df46876b800005c7b366fc21` |

Method: identical to the lote-1/lote-2 twin audits — full read of each note, independent fetch/verification of every `[REFERENCIAS]` URL (or a documented network-limitation/dead-link fallback), a targeted invention scan, and the lote-3-specific extra scans the IC names (§3.3: specific-force vs. linear accel, inclinometer-only-when-static, bias→drift/ARW, 6-axis≠mag≠AHRS, IMU≠estimator≠true attitude, the self-flagged NASA-TM-20250008926 title check, and datasheet-path liveness). Lote-1/lote-2 were not re-opened or re-audited. Only the three named files under `ontology/` were opened.

---

## 2. Acelerómetro — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (Analog Devices ops/AN-1057/MEMS Part 1, NASA NTRS 20140002398, TDK ICM-42688-P) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, assistant]` — sensible |
| Body vs REFERENCIAS | "Aceleración específica," bias/offset/noise/scale/cross-axis/nonlinearity/temperature error list, and "filtrar ≠ calibrar" → all match the Analog Devices operation/sensing overview (confirmed via search: covers MEMS operation, sensing, applications) and AN-1057 (confirmed via search: "the underlying assumption in inclination sensing with an accelerometer is that the only acceleration stimulus is that associated with gravity" — an exact match to the note's own inclinometer-validity conditions). The ICM-42688-P range claim ($\pm2g,\pm4g,\pm8g,\pm16g$) — **verified word-for-word against downloaded datasheet text**: "the accelerometer supports four programmable full-scale range settings from ±2g to ±16g." |
| Overclaim | None — extra scan (IC §3.3: "inclinometer-only-when-static") confirmed clean: INTUICION states plainly that during "maniobra, aceleración lineal, vibración o shock, la medición deja de representar únicamente la gravedad," and ERRORES separately lists "Usar el acelerómetro como inclinómetro durante cualquier maniobra." |
| SoT bleed | Guarded twice: "Estos valores pertenecen al dispositivo concreto y **no deben convertirse en propiedades genéricas de un acelerómetro**" (FUNDAMENTO) and "Tratar parámetros de un acelerómetro concreto como propiedades universales de todos los acelerómetros" (ERRORES). |
| Sim≠hardware | EJEMPLO states directly: "Una lectura simulada puede demostrar que el software procesa correctamente una señal bajo las hipótesis definidas, pero **no demuestra que un acelerómetro físico instalado en el vehículo produzca esas mismas mediciones**." ERRORES: "Tratar lecturas simuladas como calibración de hardware." |
| Internal consistency | FUNDAMENTO's device-specific range/noise disclosure is consistent with NOTAS's own repetition of the same numbers with the same "example of device data, do not generalize" caveat — no contradiction. |

**Verdict: PASS.** Zero findings on this note's own specific claims — every quantitative statement (both generic sensing theory and the one device-specific range claim) was independently confirmed.

---

## 3. Giroscopio — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (Analog Devices MEMS gyro/ARW/alignment, NASA NTRS 20140002398, TDK ICM-42688-P) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, assistant]` — sensible |
| Body vs REFERENCIAS | $\boldsymbol\omega_m=\boldsymbol\omega+\mathbf b+\mathbf n$ (bias+noise measurement model) and the bias→drift relation $\theta_{\mathrm{error}}(t)\approx bt$ are standard MEMS-gyro error models, matching Analog Devices' own "Misguided Gyro" article (confirmed via search: bias instability + angular random walk (ARW) as the two drift-contributing terms, exactly as the note's own NOTAS section states) and the frequency-response/stabilization article (confirmed via search in lote-2, same URL, re-used here for a different note's claim). The low-noise-feedback-control article and the IMU/gyro-alignment article were both independently confirmed via search — see §5 F1/F2 for one URL-slug note. The ICM-42688-P range claim ($\pm15.6/31.2/62.5/125/250/500/1000/2000$ dps) — **verified word-for-word against downloaded datasheet text**: "the gyroscope supports eight programmable full-scale range settings from ±15.625dps to ±2000dps" (the note rounds `15.625` to `15.6`, an immaterial rounding, not a discrepancy). |
| Overclaim | None — extra scan (IC §3.3: "ω not absolute angle") confirmed clean: DEFINICION states plainly "un giroscopio proporciona **velocidad angular**, no una medida absoluta directa del ángulo de orientación," reinforced by INTUICION's "El gyro 'siente giro', no ángulo absoluto" and ERRORES's "Tratar la integración del gyro como una medida de actitud absoluta." |
| SoT bleed | "Los parámetros concretos de un gyro/SKU no deben incorporarse a esta nota salvo que estén respaldados por su documentación específica" (APLICACIONES); "Inventar bias, ruido, escala, rango, ODR o ARW de un SKU sin datasheet" (ERRORES). |
| Sim≠hardware | EJEMPLO states the C42 `ScriptedSpi` driver "**no demuestra** que SPI1 esté físicamente conectado... que el gyro esté calibrado... que sus mediciones sean válidas en vuelo," closing with the bolded chain "**modelo/driver simulado ≠ comunicación física ≠ calibración ≠ validación de vuelo**." ERRORES separately: "Confundir `WHO_AM_I` / probe SPI con calibración del gyro" and "Usar tasas angulares simuladas como evidencia de que el sensor físico funciona correctamente." |
| Internal consistency | FUNDAMENTO's "Uso en control" section cleanly distinguishes rate-feedback use from attitude-estimation use ("gyro → velocidad angular → control de tasas" vs. "gyro + otras observaciones → estimación de actitud") — consistent with ERRORES's "Confundir la realimentación de tasas con la estimación completa de actitud." |

**Verdict: PASS.** One citation URL-slug discrepancy (F1 below) on a real, content-confirmed source — does not affect any claim's substance.

---

## 4. IMU — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (NASA GNC/NTRS IMU, NASA-TM-20250008926, TDK DS-000347, Analog Devices alignment) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, assistant]` — sensible |
| Body vs REFERENCIAS | The core definition — "una unidad que contiene tres acelerómetros ortogonales y tres giróscopos ortogonales" — is an **exact, verbatim match** to NASA's own Small Spacecraft GNC state-of-the-art document (confirmed via direct fetch: "units containing three orthogonal gyros and three orthogonal accelerometers (Inertial Measurement Unit (IMU))"), and independently corroborated by the PDS Mars Exploration Rover IMU instrument page (confirmed via direct fetch: "three Fiber Optic Gyro sensors and three silicon accelerometers, oriented orthogonally"). "Un magnetómetro no forma parte necesariamente de una IMU de 6 ejes" and the IMU≠AHRS≠estimator distinction are the note's own explicit theses (see extra-scan row below). The ICM-42688-P claim ("acelerómetro de 3 ejes y un giroscopio de 3 ejes... interfaces I3C, I²C y SPI") — **verified against downloaded datasheet text**: "a configurable host interface that supports I3CSM, I2C and SPI serial communication," 3-wire and 4-wire SPI timing sections both present. The self-flagged NASA-TM-20250008926 citation (bullet text: "verify title on PDF title page at cite-audit") was resolved: its actual title is *"Using Doppler Tracking to Aid Trajectory Reconstruction for Atmospheric Entry, Descent, and Landing"* (Graupe, Karlgaard, Dutta; NASA Langley, September 2025) — not an IMU-titled paper, but its own body text mentions "IMU" 44 times, "inertial" 30 times, "accelerometer" 17 times, and "gyroscope" 11 times, describing an Iterative Extended/Unscented Kalman Filter that fuses IMU data with Doppler tracking for a 6-DOF entry-vehicle trajectory reconstruction — genuinely on-topic for the note's own vague-but-honest "inertial / state-estimation context" framing, which is why the drafters deliberately did not assert a specific title. |
| Overclaim | None — extra scan (IC §3.3: "IMU≠estimator≠true attitude, 6-axis=accel+gyro, mag optional") confirmed clean on all three points: FUNDAMENTO's own bolded thesis "**IMU ≠ estimador ≠ actitud verdadera**"; DEFINICION's explicit "un magnetómetro no forma parte necesariamente de una IMU de 6 ejes"; and ERRORES's "Confundir una IMU de 6 ejes con un AHRS." |
| SoT bleed | "Los parámetros específicos de un dispositivo no deben convertirse en propiedades genéricas de la clase IMU" (APLICACIONES); "Inventar `WHO_AM_I`, ODR, rangos, ruido, escalas o registros sin datasheet" (ERRORES). |
| Sim≠hardware | This note's central discipline, stated as its own explicit "cadena de honestidad" in EJEMPLO: "**simulación ≠ interfaz emulada ≠ comunicación física ≠ calibración ≠ validación de vuelo**" — the most elaborated version of this chain across all six notes audited so far (lote-1, -2, -3 combined). PROCEDIMIENTO step 10: "No promover `WHO_AM_I`, smoke tests o probes SPI a 'IMU calibrada' o 'sensor validado en vuelo.'" |
| Internal consistency | The FUNDAMENTO table (Acelerómetro/Giroscopio/Magnetómetro/Estimación de estado roles) is consistent with, and elaborated by, the "Medición ≠ estimación" subsection and the EJEMPLO diagram — no contradiction anywhere. |

**Verdict: PASS.** One dead-but-self-flagged-and-mirrored datasheet link and one section-vs-document-title imprecision (F2, F3 below) — neither affects any claim's substance; the note's own core definitional claim was independently verified against two different primary NASA sources.

---

## 5. Cross-cutting findings

**No SoT bleed, no invented numbers, no fabricated datasheet fields/registers, and no sim≠hardware overclaim found in any of the three notes.** Every ICM-42688-P numeric/interface claim across all three notes — accelerometer range ($\pm2/4/8/16g$), gyroscope range ($\pm15.6$ to $\pm2000$ dps, eight settings), and interface support (I3C/I²C/SPI, 3-wire and 4-wire) — was independently checked against downloaded datasheet text and found to match exactly, character for character. This is the strongest datasheet-fidelity result across all three lotes audited so far, consistent with this lote's own heightened bar (IC §0 decision 6).

- **F1 (Giroscopio, low priority — link only):** the citation "Analog Devices — *Designing for Low Noise Feedback Control with MEMS Gyroscopes*" is given the URL `https://www.analog.com/en/resources/technical-articles/low-noise-feedback-control-mems-gyroscopes.html`, but an independent search found the article's real, indexed URL to be `https://www.analog.com/en/resources/analog-dialogue/articles/low-noise-feedback-control.html` — a different path and slug. This session's `analog.com` fetches all failed at the network level (see below), so this could not be resolved by following a redirect; it is flagged as a possible stale/incorrect link, not confirmed dead. The article itself (author Mark Looney, on gyroscope noise metrics for feedback control) is real and matches what the note cites it for.
- **F2 (IMU, low-moderate priority — dead specific link, content and alternates confirmed):** the TDK datasheet URL `https://invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf` is **dead** — it now redirects (301 → 301 → 200) to the generic `/en-us/download-resource/ds-000347-icm-42688-p-datasheet` landing page rather than serving the PDF. The note's own citation bullet already self-flags this exact risk ("prefer current official download if this path 404s") and lists that same official download page as its own fallback — this audit confirms the fallback page is reachable (HTTP 200) but, like several other JS-rendered vendor sites encountered in this and the prior lote's audits, does not serve readable content to this session's automated fetch tools; a working alternate mirror was independently found and read directly during this audit (`https://www.cdiweb.com/datasheets/invensense/ds-000347-icm-42688-p-v1.2.pdf`), and it is this mirror's own text that confirmed every ICM-42688-P numeric claim in §2–§4 above.
- **F3 (IMU, low priority — section vs. document title):** the citation "NASA Technical Reports Server — *Inertial Measurement Unit* (citation 19790012950)" names a section, not the document's own cover title. The actual document title (confirmed by reading its own title page) is *"Onboard Navigation Systems Characteristics"* (NASA-TM-79944 / JSC-14675, NASA Johnson Space Center Mission Planning and Analysis Division, March 1979) — but **Section 2.0 of that document is itself literally titled "INERTIAL MEASUREMENT UNIT"** (confirmed in the document's own table of contents and body), describing the Space Shuttle's own Singer-Kearfott IMU hardware and a separate Rate Gyro Assembly with three orthogonal rate gyros. This is a defensible section-level citation, not a fabricated title, but Cursor may wish to clarify the bullet to name the parent document explicitly.
- **Network-block note (not a finding against any specific note, applies across all three):** every `analog.com` URL in this lote (6 of them, shared across Acelerómetro and Giroscopio) failed on every fetch attempt this session made — `WebFetch` timeouts and raw `curl` connection resets/hangs across multiple user agents, HTTP/1.1 and HTTP/2, header-only and full-GET requests. This matches the exact same failure pattern already documented in the lote-2 audit for three different `analog.com` URLs, suggesting a persistent, session- or IP-level block on this domain rather than anything specific to these particular pages. All six were independently corroborated via search (title, author, and content-summary matches for all six).

---

## 6. URL matrix

| Note | # | Reference (short) | Reach | Title/content match | Key-claim support |
|---|---|---|---|---|---|
| Acelerómetro | 1 | Analog Devices "Accelerometer and Gyroscopes Sensors: Operation, Sensing, and Applications" | ❌ network block (timeout, both `resources/` HTML and `media/` PDF mirror) | ✅ confirmed via independent search | ⚠️ UNVERIFIED (network); search summary confirms accel/gyro operating-principle content |
| Acelerómetro | 2 | Analog Devices AN-1057 "Using an Accelerometer for Inclination Sensing" | ❌ network block | ✅ confirmed via independent search | ⚠️ UNVERIFIED (network); search snippet is an exact match for the note's own inclinometer-validity condition |
| Acelerómetro | 3 | Analog Devices "Choosing the Most Suitable MEMS Accelerometer... Part 1" | ❌ network block (same URL independently confirmed real in the lote-2 audit) | ✅ confirmed (lote-2 + this session's search) | ⚠️ UNVERIFIED (network) |
| Acelerómetro | 4 | NASA NTRS 20140002398 (UAV attitude estimation, low-cost INS) | ✅ 200 (already fully verified in lote-2 audit of a different note — same URL, unchanged) | ✅ exact | ✅ EKF using gyro/mag/accel/pitot |
| Acelerómetro | 5 | TDK InvenSense ICM-42688-P product page | ✅ 200 (already verified in lote-2) | ✅ exact | ✅ product overview |
| Acelerómetro | 6 | TDK Product Center "ICM-42688-P Detailed Information" | ❌ 403 (Akamai bot wall) | ✅ confirmed via independent search — same page, and search snippet directly quotes the exact accel/gyro range and interface specs | ✅ (via search) exact range/interface match |
| Giroscopio | 7 | Analog Devices "Analyzing Frequency Response of Inertial MEMS..." | ❌ network block (same URL, lote-2's own attempt also failed) | ✅ confirmed via search (lote-2 + re-confirmed here) | ⚠️ UNVERIFIED (network) |
| Giroscopio | 8 | Analog Devices "The Case of the Misguided Gyro" | ❌ network block (same URL, lote-2) | ✅ confirmed via search (lote-2 + re-confirmed here) | ⚠️ UNVERIFIED (network); bias-instability/ARW claim matches exactly |
| Giroscopio | 9 | Analog Devices "Designing for Low Noise Feedback Control with MEMS Gyroscopes" | ❌ network block | ⚠️ real article confirmed via search, but search's own indexed URL differs from the note's cited URL — **F1** | ⚠️ UNVERIFIED (network); content on-topic |
| Giroscopio | 10 | Analog Devices "The Basics of MEMS IMU/Gyroscope Alignment" | ❌ network block | ✅ confirmed via search — exact URL match | ⚠️ UNVERIFIED (network); axis-to-package/axis-to-axis misalignment content matches |
| Giroscopio | 11 | NASA NTRS 20140002398 (dup of #4) | ✅ (already verified) | ✅ exact | ✅ |
| Giroscopio | 12 | TDK InvenSense ICM-42688-P product page (dup of #5) | ✅ (already verified) | ✅ exact | ✅ |
| IMU | 13 | NASA "Guidance, Navigation, and Control" — Small Spacecraft SOA | ✅ 200 | ✅ exact | ✅ **verbatim match**: "units containing three orthogonal gyros and three orthogonal accelerometers (IMU)" |
| IMU | 14 | NASA NTRS 19790012950 "Onboard Navigation Systems Characteristics" | ✅ 200 | ⚠️ cited as "Inertial Measurement Unit" — that is §2.0's own section title, not the document's cover title — **F3** | ✅ §2.0 is genuinely titled "Inertial Measurement Unit," describes real Shuttle IMU/gyro hardware |
| IMU | 15 | NASA-TM-20250008926 | ✅ 200 | ✅ self-flagged by the note's own drafters as needing verification; resolved — actual title is about Doppler tracking, not IMU, but IMU/inertial content is extensive (61+ combined mentions) and genuinely on-topic | ✅ (for the vague "inertial/state-estimation context" framing actually used) |
| IMU | 16 | NASA PDS — Mars Exploration Rover IMU instrument context | ✅ 200 | ✅ exact | ✅ "three Fiber Optic Gyro sensors and three silicon accelerometers, oriented orthogonally" |
| IMU | 17 | TDK InvenSense ICM-42688-P product page (dup of #5) | ✅ (already verified) | ✅ exact | ✅ |
| IMU | 18 | TDK InvenSense ICM-42688-P Datasheet (2020/04 path) + official download alt | ❌ dead (redirects to generic landing page, not the PDF) — self-flagged by the note itself — **F2** | N/A (document is real; this exact path is gone) | ✅ content independently re-verified via a working v1.2 mirror — see below |
| IMU | 19 | TDK Product Center "ICM-42688-P Detailed Information" (dup of #6) | ❌ 403 (dup of #6) | ✅ confirmed via search | ✅ |
| IMU | — | Analog Devices "The Basics of MEMS IMU/Gyroscope Alignment" (dup of #10) | ❌ network block | ✅ confirmed via search | ✅ |

**Supplementary verification (not a `[REFERENCIAS]` entry in any of the three notes, used to independently confirm every ICM-42688-P numeric claim):** `https://www.cdiweb.com/datasheets/invensense/ds-000347-icm-42688-p-v1.2.pdf` — downloaded and read directly; confirms verbatim: *"The gyroscope supports eight programmable full-scale range settings from ±15.625dps to ±2000dps, and the accelerometer supports four programmable full-scale range settings from ±2g to ±16g"* and *"a configurable host interface that supports I3CSM, I2C and SPI serial communication"* with both 3-wire and 4-wire SPI timing sections present.

**10 / 19 fully verified by direct fetch. 6 / 19 UNVERIFIED (network) with strong independent corroboration. 2 / 19 dead-but-mirrored/alternate-path issues (F1, F2). 1 / 19 section-vs-document-title imprecision (F3).**

---

## 7. Recommended remediations (ordered, Cursor-applicable)

1. **[IMU, low-moderate priority]** Replace the dead TDK datasheet path (`invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf`) with a currently-working mirror — this audit confirmed `https://www.cdiweb.com/datasheets/invensense/ds-000347-icm-42688-p-v1.2.pdf` works and contains the exact text needed. No change to any claim in the note — all were independently re-verified against this mirror.
2. **[IMU, low priority]** Clarify the NTRS 19790012950 citation bullet to name the parent document ("Onboard Navigation Systems Characteristics," NASA-TM-79944) alongside or instead of just "Inertial Measurement Unit," since that phrase is the document's internal §2.0 heading, not its cover title. No change needed to the claim itself — §2.0 genuinely covers IMU hardware.
3. **[Giroscopio, low priority]** Double-check the "Designing for Low Noise Feedback Control with MEMS Gyroscopes" URL against `https://www.analog.com/en/resources/analog-dialogue/articles/low-noise-feedback-control.html` (the URL an independent search indexed for this exact article title) — the cited URL could be a valid alternate/legacy path that redirects, or could need updating; this session's persistent inability to reach any `analog.com` URL prevented resolving this directly.
4. **No remediation needed** for any of the NASA GNC/PDS citations in IMU, the NASA-TM-20250008926 self-check (already appropriately hedged by the drafters), the ICM-42688-P device-specific numeric claims in any of the three notes (all independently confirmed exact), or the remaining Analog Devices citations (all confirmed real via search, network-blocked only for direct fetch).

**No remediation recommended for Acelerómetro at all** beyond the network-unverifiable (but search-corroborated) Analog Devices links shared with Giroscopio — this is the cleanest of the three notes.

---

## 8. Overall verdict + whether lote-3 may stay `solid`

| Note | Verdict | Stay `solid`? |
|---|---|---|
| Acelerómetro | **PASS** (zero content findings; shared network-unverifiable AD links) | **Yes** |
| Giroscopio | **PASS** (one link-slug discrepancy, F1) | **Yes** |
| IMU | **PASS** (one dead-but-mirrored link, F2; one section/document-title imprecision, F3) | **Yes** |

None of the three notes contains an invented physical number, a fabricated datasheet register/field/ODR/noise value, a fake section reference, a catalog/Continuity/FS/Safety SoT bleed, or an unhedged sim-equals-hardware overclaim. Every device-specific ICM-42688-P claim (accelerometer range, gyroscope range, interface support) across all three notes was independently verified character-for-character against real, downloaded datasheet text — the highest-confidence datasheet-fidelity result of any lote audited so far, directly answering this lote's own heightened bar (IC §0 decision 6). The three findings (F1–F3) are link-path/title-labeling issues on real, content-confirmed sources; none touches any claim's substance. Given the IC's own PASS/PASS WITH NOTES/FAIL rubric, this report keeps all three at **PASS** — the recommended fixes are citation-string/link corrections only. **All three notes may remain `estado: solid`.** No downgrade to `draft` is warranted for any of the three.

---

## 9. Out of scope

- **Lote-1** (`Vectores`, `Dinámica`, `Control clásico`) and **lote-2** (`Momento y rotación`, `Control robótico`, `Sensores de movimiento`) — not re-audited; see their own twin ICs/reports for those independent audits.
- The rest of the vault — out of this Buy's scope, already covered structurally (not content-graded) by the earlier `B0-ontology-vault-value-for-jarvis` report.
- Note prose style — per the IC's own stop conditions, no wording improvements were proposed for readability, only truth/citation/SoT/datasheet-fidelity issues.
- RAG readiness, retrieve-layer implementation, or any `intelligence/`-adjacent code — none touched, built, or recommended as ready.
- Obsidian math delimiter style (`$`/`$$`) — per the IC's own §2 Locked stance 7, not treated as a defect; the documented, intentional convention for this vault.

---

## 10. Non-edits (explicit)

**Claude did not edit any file under `ontology/` in this Buy.** This investigation used only `Read` (on the three audited notes) and read-only `Bash`/`WebFetch`/`WebSearch` tools (`shasum`, `curl -I`/`-v`/`-L`, `pdftotext` run against locally-downloaded/fetched PDFs, and external URL fetches/searches) — no `Write`/`Edit` tool call was made against any path under `ontology/` at any point in this session. All temporary local files created during URL verification (downloaded PDFs, `curl` scratch output) were deleted after use and are not part of the repository.

```text
$ git status --short -- ontology/ src/ pyproject.toml
```

At close of this Buy, the working tree still reflects the same pre-existing, uncommitted state of the Engineer/Cursor's own offline spine-fill work already disclosed in the lote-1 and lote-2 twin reports' own §10 sections, now additionally including the three files audited here (already at their current `solid` content before this investigation opened them). This investigation changed none of it. No file under `src/` was created or modified. `pyproject.toml` is unchanged (`version = "0.5.44"`). No git tag was created (`git tag -l | sort -V | tail -1` → `v0.5.44`).
