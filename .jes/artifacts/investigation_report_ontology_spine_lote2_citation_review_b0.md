# Investigation Report — Ontology spine lote-2 citation review (`B0-ontology-spine-lote2-citation-review`)

**IC:** [`investigation_contract_ontology_spine_lote2_citation_review_b0.md`](investigation_contract_ontology_spine_lote2_citation_review_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-27
**Status:** Investigation / citation audit only. **Tip stays `v0.5.44`.** Zero `ontology/` edits, zero `src/` edits, no `pyproject.toml` bump, no tag. Not claiming ACCEPT — that is Cursor review + Engineer's call.

---

## 0. Honesty summary

```text
cite verified != cite invented
URL reachable != claim automatically supported
dead specific PDF path != the underlying document being fake (stable mirrors exist)
network timeout/bot-wall != dead link
one concrete ICM-42688-P claim, checked word-for-word against the real datasheet text != a generic sensor note
Claude audits citations != Claude marks notes solid
```

All three lote-2 notes are as disciplined as lote-1's — every note explicitly and repeatedly guards against the exact overclaim/SoT-bleed/sim≠hardware failure modes this IC is checking for, and the one note with real ICM-42688-P specifics (Sensores de movimiento) makes exactly **one** concrete hardware claim (SPI supports 3-wire and 4-wire modes) — this session verified that claim **word-for-word against the actual TDK datasheet text** ("AP_SDIO: AP SPI serial data I/O (3-wire mode); AP_SDI: AP SPI serial data input (4-wire mode)"), and it is correct. Of 20 unique cited URLs: **14 fully verified** (fetched, title/content confirmed — including two large PDFs read page-by-page: MIT 8.09's own Euler-equations page and ETH's PX4Space paper's control-architecture section), **3 blocked by network/anti-bot behavior on direct fetch but independently corroborated via search** (all three Analog Devices articles — UNVERIFIED (network), not assumed fine), **1 dead** (the specific TDK datasheet PDF revision v1.5 URL 404s after three redirects — but the same document is confirmed live at multiple alternate stable mirrors, including one this session read directly to confirm the WHO_AM_I register text), and **2 real-but-mislabeled** (an ETH PX4Space bitstream link that resolves to an SPA shell instead of the PDF, and a NASA-hosted university thesis cited under a NASA-sounding title that isn't its actual title). No invented physical numbers, no fabricated datasheet fields/registers, no fake section numbers, and no catalog/Continuity/FS/Safety SoT bleed were found in any of the three notes.

**Overall: all three notes PASS. None warrants a `draft` downgrade.**

---

## 1. Scope + files audited

| Note | Path | SHA-256 (this audit's snapshot) |
|---|---|---|
| Momento y rotación | `ontology/02_Fisica/Mecánica/Momento y rotación/Momento y rotación.md` | `e1bd44d98cf3dab909fe43b0c6d1e2e6fe3a641d9fe0615cd33a635202edea4b` |
| Control robótico | `ontology/04_Robotica/Control robótico/Control robótico.md` | `9a6eb3ef1546c7e11c4c60efb7d989eb918747e59537a9ec22e83ee4457b5d85` |
| Sensores de movimiento | `ontology/04_Robotica/Sensores/Sensores de movimiento/Sensores de movimiento.md` | `3cec03caff56a8a0e0779ccd42e60cc4d004d4a0eac2f6f6b2a9778a224bbbca` |

Method: identical to the lote-1 twin audit — full read of each note, independent fetch/verification of every `[REFERENCIAS]` URL (or a documented network-limitation/dead-link fallback), a targeted invention scan (numeric physical parameters, fake section numbers, fake datasheet registers, universal-guarantee overclaims), and the lote-2-specific extra scans the IC names (§3.3: torque-equation scope, cascade-vs-plant-vs-sim distinctions, accelerometer-vs-specific-force, ICM-42688-P claims against the real datasheet). Lote-1 was not re-opened or re-audited. Only the three named files under `ontology/` were opened.

---

## 2. Momento y rotación — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (OpenStax §10.6–10.7/§12.1, MIT OCW 8.09 §2.4) ✓ · `never_invents: [mass_g, power_w, thrust_gf, autonomy_min]` present ✓ · `jarvis_relevance: [fs, craft, assistant]` — sensible |
| Body vs REFERENCIAS | $\boldsymbol\tau=\mathbf r\times\mathbf F$ and $\|\boldsymbol\tau\|=rF\sin\theta=r_\perp F$ → OpenStax §10.6, verified directly (quote match). $\sum\tau=I\alpha$ (fixed axis) → OpenStax §10.7, verified (already independently confirmed in the lote-1 audit of a different note; re-confirmed here as the same real, unchanged page). The three-component Euler-equation set ($I_1\dot\omega_1-(I_2-I_3)\omega_2\omega_3=\tau_1$, etc.) → **verified by reading MIT 8.09 Chapter 2, §2.4 "Euler Equations" (page 44) directly** — the PDF's own equations (2.68) are an exact match, same subscript/sign pattern, no discrepancy. |
| Overclaim | None. The note explicitly scopes $\tau=I\alpha$ to a fixed axis and separately derives the general 3D case with the inertia tensor — it does not present the fixed-axis form as universal. |
| SoT bleed | Extra scan (IC §3.3: "no invented $I_{xx}$") — confirmed clean: APLICACIONES lists exactly the values the note refuses to provide ("$I_{xx},I_{yy},I_{zz}$; tensor de inercia; thrust de un SKU; brazos de motor; torque de motor; ganancias del controlador") and states they "requieren datos respaldados por las fuentes correspondientes." ERRORES separately flags "Tomar un $I$ de un ejemplo académico como momento de inercia del craft real." |
| Internal consistency | EJEMPLO's "El `step()` del controlador **no es la ecuación de Euler**" is directly reinforced by ERRORES's "Confundir la salida del controlador con la respuesta física de la planta" — no contradiction. |
| Explain-map direction | APLICACIONES: "puente conceptual entre [[Dinámica]], el sistema de propulsión/mixer y la planta 6-DoF" — correct direction, never claims those Buys validate the physics. |

**Verdict: PASS.** Zero findings — every cited claim in this note was independently verified word-level or formula-level against its source, including the one non-OpenStax citation (MIT 8.09), read directly to its own §2.4.

---

## 3. Control robótico — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (ETH Zürich Quadrotor Control/P&S/PX4Space, NASA hierarchical/allocation, MIT Underactuated) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, assistant]` — sensible |
| Body vs REFERENCIAS | The cascaded hierarchy diagram (position → attitude → rate → allocation → actuators) is a **conceptual architecture**, not a formula, and the note itself says so ("Esta arquitectura es una representación conceptual"). Verified against all three ETH sources directly: the "Robot Dynamics" lecture's own table of contents lists exactly "Hierarchical Control → Attitude Control → Control Loop Separation → PID Controller → Altitude Control → Position Control"; the P&S exercise sheet explicitly discusses a "nested controller architecture" with separate outer/inner loops; the PX4Space paper's own §II.A ("Control") states verbatim: "The control system is composed of three cascaded PI and PID controllers... Position controller... Attitude controller... rate controller generates a wrench setpoint... control allocator (CA) module... sends a normalized thrust... as a PWM signal" — an exact structural match to the note's own cascade diagram, verified by reading the paper's own text (§6, finding F2 below covers the specific *link* used, not this content match). The three NASA citations (hierarchical control, computationally efficient allocation, quadratic-programming allocation) were each verified to be exactly what their titles claim. |
| Overclaim | None — the note's own EJEMPLO states directly: "En Jarvis FS, la arquitectura C7 → C8 → rate/torque bridge → mixer → ESC stub y los lazos C38/C39 representan actualmente una arquitectura de control en simulación. Su existencia no constituye por sí misma una validación experimental del vehículo" — this is the exact sim≠hardware-validation guard the IC's own §2 Locked stance 3 requires, stated explicitly rather than merely implied. |
| SoT bleed | Extensively guarded — ERRORES lists ten distinct failure modes including "Equivaler 'hay un lazo funcionando en simulación' con 'el vehículo vuela' o 'la autonomía está validada'" (the IC's own named risk, verbatim) and "Tratar una asignación matemática de control como evidencia de que los actuadores reales pueden producir la acción solicitada." APLICACIONES: "No constituye por sí misma una demostración de vuelo, autonomía ni seguridad operacional. La implementación concreta continúa perteneciendo a `flight_software/` y `native/`" — correctly names the real module paths. |
| Internal consistency | FUNDAMENTO's "Seguridad y autorización: la generación matemática de una acción de control y la autorización para ejecutar una acción sobre hardware son funciones conceptualmente distintas" is echoed consistently in EJEMPLO, PROCEDIMIENTO (step 12), and ERRORES (twice) — no contradiction anywhere. |
| Explain-map direction | APLICACIONES: "mapa conceptual del ladder C7–C11 / C36–C40 como arquitectura de control de movimiento aéreo **en simulación**" — correct direction throughout. |

**Verdict: PASS.** Two citation-link findings (F1, F2 below) on real, on-topic, independently-confirmed-content sources — neither affects any claim's truthfulness, both are link/attribution accuracy issues.

---

## 4. Sensores de movimiento — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (NASA attitude/IMU, Analog Devices MEMS FAQs, TDK ICM-42688-P datasheet) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, assistant]` — sensible |
| Body vs REFERENCIAS | "El acelerómetro mide aceleración específica" — directly matches the NASA correntropy-filter paper's own framing ("measuring the accelerations (accelerated motion together with gravity)"). "Giroscopio + acelerómetro + filtro estiman orientación... EKF" — directly matches the UAV attitude-estimation NASA paper (EKF using gyro/mag/accel/pitot) verified via its own abstract. Gyro bias/drift claim — directly matches the Analog Devices "Misguided Gyro" article (bias instability + angular random walk → accumulated drift), confirmed via search. Sensor error-source claim (bias, noise) — directly matches the Analog Devices FAQ page, confirmed via search. **The one concrete ICM-42688-P claim** — "El ICM-42688-P real soporta interfaces SPI de 3 y 4 hilos" — was checked **directly against the actual TDK datasheet text** (a working alternate mirror of the same DS-000347 document, since the note's own cited v1.5 URL is dead — see F3): the datasheet's own pin-description table states "AP_SDIO: AP SPI serial data I/O (3-wire mode); AP_SDI: AP SPI serial data input (4-wire mode)" — an exact match, word for word. The same datasheet mirror also independently reconfirms `WHO_AM_I`: "Address: 117 (75h) ... Reset value: 0x47" (this Buy did not need to re-verify C42's own citation, but the coincidental cross-check found no discrepancy). |
| Overclaim | None found — this note pre-empts every overclaim pattern the IC's own §3.3 extra-scan column names for it. INTUICION: accelerometer-as-inclinometer interpretation "deja de ser directamente válida" during dynamic motion/vibration. ERRORES explicitly lists "Tratar el acelerómetro como un inclinómetro válido durante cualquier maniobra dinámica," "Asumir que una IMU de 6 ejes contiene necesariamente un magnetómetro" (the IC's own named "6-axis ≠ mag" check, verbatim), and "Confundir `WHO_AM_I` / identificación del dispositivo con calibración" (also IC-named, verbatim). |
| SoT bleed / sim≠hardware | This is the note's central discipline, stated as its own explicit thesis in EJEMPLO: "El flujo SPI scripted + probe (C32–C34) y el driver basado en el datasheet del ICM-42688-P sobre `ScriptedSpi` (C42)... **no demuestran que SPI1 esté físicamente conectado ni que exista comunicación real sobre el hardware**," followed by the bolded chain "**identificación/configuración simulada ≠ comunicación física real ≠ calibración ≠ validación de vuelo**" — this is exactly the IC's own §2 Locked stance 4 requirement, stated as the note's own headline claim rather than a footnote. ERRORES separately lists "Confundir una prueba/probe SPI con comunicación física validada sobre el hardware." NOTAS closes with an explicit datasheet-discipline statement: "Para el ICM-42688-P concreto, cualquier afirmación sobre registros, escalas, rangos, interfaces, ODR, ruido u otros parámetros debe proceder de su datasheet específico y no de una nota genérica" — and the note's own body honors this itself (only one such claim is made, and it is correct). |
| Internal consistency | The table in FUNDAMENTO (sensor → typical magnitude → caveats) is consistent with, and elaborated by, both INTUICION (qualitative behavior) and ERRORES (specific misuse patterns for each sensor named in the table) — no contradiction. |

**Verdict: PASS.** One citation-link finding (F3 below, a dead specific PDF revision with confirmed-live alternates) — does not affect the truthfulness of any claim, and the note's own single concrete hardware claim was independently re-verified against the primary datasheet text as part of this audit.

---

## 5. Cross-cutting findings

**No SoT bleed, no invented numbers, no fake section numbers, no fabricated datasheet fields/registers found in any of the three notes.** All three continue the same defensive pattern documented in the lote-1 audit (explicit "this is not `library/`/`flight_software/`" disclaimers), and lote-2 adds a heightened, explicit sim≠hardware discipline specifically around the SPI/WHO_AM_I material — exactly where the IC's own §1 flags "higher risk."

- **F1 (Control robótico, cosmetic):** the ETH Zürich "PX4Space" citation's title is paraphrased as "PX4Space: A Software Framework for Space Robotics" — the paper's actual title (confirmed by reading its own title page via an author-hosted mirror) is *"PX4Space: PX4 for Spacecraft and Space Robotics"* (Pedro Roque, Elias Krantz, Jaeyoung Lim, Christer Fuglesang, Roland Siegwart, Dimos V. Dimarogonas — KTH/ETH Zürich). Close paraphrase, not a fabrication; the paper is real and its content (cascaded PI/PID controllers + control allocator, §II.A) exactly matches what the note cites it for.
- **F2 (Control robótico, moderate — link only):** the specific ETH Research Collection bitstream URL cited (`research-collection.ethz.ch/bitstreams/e70472b7.../download`) returns HTTP 200 but serves the site's Angular single-page-app shell rather than the PDF — automated tools (and possibly some browsers without JS/session state) cannot retrieve the document from this exact link. An alternate, working link for the same paper was found and read directly during this audit (an author-hosted mirror at `pedroroque.dev/assets/pdf/PX4Space.pdf`); the ETH Research Collection's own stable handle page also exists (`research-collection.ethz.ch/handle/20.500.11850/698049`) as a citable alternative, though it also returned a server error to this session's own automated fetch (likely the same JS-rendering limitation). See §7 remediation R1.
- **F3 (Sensores de movimiento, low-moderate — dead specific link, content unaffected):** the cited TDK datasheet URL (`invensense.tdk.com/wp-content/uploads/2021/06/DS-000347-ICM-42688-P-v1.5.pdf`) is **dead** — it now 404s after three redirect hops (TDK has restructured its site; the current official version is v1.9, per `invensense.tdk.com/en-us/download-resource/ds-000347-icm-42688-p-datasheet`). This is the same document under the same DS-000347 number; multiple working alternate mirrors exist (this audit read one directly — `cdiweb.com/datasheets/invensense/ds-000347-icm-42688-p-v1.2.pdf` — and independently confirmed both the note's SPI 3-wire/4-wire claim and the WHO_AM_I register facts word-for-word from that mirror's own text). See §7 remediation R2.
- **F4 (Sensores de movimiento, moderate — title/attribution mismatch):** the citation bullet "NASA — *Attitude sensors with navigation solutions*" (`s3vi.ndc.nasa.gov/ssri-kb/static/resources/2016-12-ms-matsumoto.pdf`) resolves to a real, reachable document, but that document's actual title (confirmed by reading its own title page) is *"Guidance, Navigation, and Control of Small Satellite Attitude Using Micro-Thrusters"* — a University of Hawaiʻi at Mānoa master's thesis by Cullen Matsumoto (December 2016), hosted on a NASA-affiliated knowledge-base site but not itself a NASA-authored work. The thesis's own abstract does describe an IMU (accelerometer + gyro) and an Extended Kalman Filter for satellite attitude estimation, so the content is genuinely on-topic for what the note cites it to support — but neither the title nor the "NASA —" attribution in the bullet match the actual document. This is the same class of finding as lote-1's F2 (TM-20230014863/SUSAN). See §7 remediation R3.
- **Datasheet-fidelity note (positive finding, not a defect):** per the IC's own heightened bar for ICM-42688-P claims (§0 decision 6: "claim must match TDK datasheet... Invented registers/ODR/noise = FAIL"), this audit went beyond checking that the cited URL exists — it read an actual working mirror of the datasheet's own text and confirmed, character-for-character, both of the two ICM-42688-P facts this vault currently states anywhere (3-wire/4-wire SPI support, in this note; WHO_AM_I address `0x75`/value `0x47`, previously cited in C42's own header comment and independently re-confirmed here). No invented register, ODR, noise, or range value was found anywhere in lote-2.

---

## 6. URL matrix

| Note | # | Reference (short) | Reach | Title/content match | Key-claim support |
|---|---|---|---|---|---|
| Momento y rotación | 1 | OpenStax Univ. Physics Vol.1 §10.6 "Torque" | ✅ 200 | ✅ exact | ✅ $\tau=r\times F$, magnitude, right-hand rule |
| Momento y rotación | 2 | OpenStax Univ. Physics Vol.1 §10.7 "Newton's 2nd Law for Rotation" | ✅ 200 | ✅ exact (same page re-confirmed from lote-1) | ✅ $\tau_{net}=I\alpha$ |
| Momento y rotación | 3 | OpenStax Univ. Physics Vol.1 Ch.10 "Key Equations" | ✅ 200 | ✅ exact (re-confirmed from lote-1) | ✅ rotational equation set |
| Momento y rotación | 4 | OpenStax Univ. Physics Vol.1 §12.1 "Conditions for Static Equilibrium" | ✅ 200 | ✅ exact | ✅ $\sum F=0$, $\sum\tau=0$ |
| Momento y rotación | 5 | MIT OCW 8.09 Classical Mechanics III, Ch.2 §2.4 "Euler Equations" | ✅ 200 | ✅ exact — read directly, page 44 | ✅ Euler equations verbatim match, including subscript/sign pattern |
| Control robótico | 6 | ETH Zürich "Robot Dynamics: Rotary Wing UAS — Control of a Quadrotor" | ✅ 200 | ✅ exact — read directly (title, authors, TOC) | ✅ hierarchical/cascaded control structure confirmed |
| Control robótico | 7 | ETH Zürich Quadrotor P&S Exercise Sheet 02 | ✅ 200 | ✅ exact — read directly | ✅ "nested controller architecture," outer/inner loop PID |
| Control robótico | 8 | ETH Zürich "PX4Space" bitstream link | ⚠️ HTTP 200 but serves SPA shell, not the PDF | ⚠️ title paraphrased ("A Software Framework..." vs actual "PX4 for Spacecraft and...") — **F1** | ✅ content independently confirmed via alternate mirror — **F2** |
| Control robótico | 9 | NASA NTRS 19890017100 "Hierarchical control of intelligent machines applied to space station telerobots" | ✅ 200 | ✅ exact | ✅ hierarchical task-decomposition architecture |
| Control robótico | 10 | NASA NTRS 20080004670 "Computationally efficient control allocation" | ✅ 200 | ✅ exact | ✅ linear control-allocation method |
| Control robótico | 11 | NASA NTRS 20110015070 "Quadratic Programming for Allocating Control Effort" | ✅ 200 | ✅ exact | ✅ QP-based control allocation |
| Control robótico | 12 | MIT "Underactuated Robotics" intro | ✅ 200 | ✅ exact | ✅ actuators/DOF/equations-of-motion relationship |
| Sensores de movimiento | 13 | NASA NTRS 20220001452 "Maximum Correntropy Kalman Filter for Orientation Estimation..." | ✅ 200 | ✅ exact | ✅ IMU = accel + gyro, specific-force framing |
| Sensores de movimiento | 14 | NASA NTRS 20140002398 "UAV Attitude Estimation Using a Low-Cost INS" | ✅ 200 | ✅ exact | ✅ EKF + complementary filter using gyro/mag/accel |
| Sensores de movimiento | 15 | NASA-hosted (s3vi.ndc.nasa.gov) "Attitude sensors with navigation solutions" | ✅ 200 | ❌ actual title "Guidance, Navigation, and Control of Small Satellite Attitude Using Micro-Thrusters" (U. Hawaiʻi thesis, not NASA-authored) — **F4** | ⚠️ topically on-point (IMU, EKF) but not the cited title/author |
| Sensores de movimiento | 16 | Analog Devices "Analyzing Frequency Response of Inertial MEMS in Stabilization Systems" | ❌ direct fetch timed out (curl exit 28 / WebFetch timeout, all HTTP versions) | ✅ confirmed via independent search (exact title, author, volume) | ⚠️ UNVERIFIED (network) for direct quote check; strongly corroborated |
| Sensores de movimiento | 17 | Analog Devices "The Case of the Misguided Gyro" (RAQ 139) | ❌ same network block | ✅ confirmed via independent search | ⚠️ UNVERIFIED (network); search snippet directly confirms bias-instability + ARW drift claim |
| Sensores de movimiento | 18 | Analog Devices FAQ "major error sources for inertial sensors" | ❌ same network block | ✅ confirmed via independent search | ⚠️ UNVERIFIED (network); search snippet confirms bias/noise error-source content |
| Sensores de movimiento | 19 | TDK InvenSense ICM-42688-P Datasheet v1.5 | ❌ **dead** — 404 after 3 redirects | N/A (document itself is real; this specific revision path is gone) | ✅ content independently re-verified via a working v1.2 mirror of the same DS-000347 doc — **F3** |
| Sensores de movimiento | 20 | TDK InvenSense inertial-sensors product page | ✅ 200 | ✅ exact | ✅ "High-Precision 6-Axis MEMS MotionTracking Device" |

**14 / 20 fully verified directly. 3 / 20 UNVERIFIED (network) with strong independent corroboration. 1 / 20 dead link with confirmed-live alternates (F3). 2 / 20 real-content-confirmed but title/link-labeled inaccurately (F1+F2 count as one source; F4).**

---

## 7. Recommended remediations (ordered, Cursor-applicable)

1. **[Sensores de movimiento, low-moderate priority]** Replace the dead TDK datasheet URL (`invensense.tdk.com/wp-content/uploads/2021/06/DS-000347-ICM-42688-P-v1.5.pdf`, now 404) with a currently-live one — either the official TDK download-resource page (`https://www.invensense.tdk.com/en-us/download-resource/ds-000347-icm-42688-p-datasheet`, currently serving v1.9) or the mirror this audit already confirmed working (`https://www.cdiweb.com/datasheets/invensense/ds-000347-icm-42688-p-v1.2.pdf`). No change needed to any claim in the note body — both the SPI 3-wire/4-wire statement and (separately, for C42) the WHO_AM_I register facts were re-confirmed directly against the v1.2 mirror's own text during this audit.
2. **[Sensores de movimiento, moderate priority]** Fix the citation bullet currently labeled "NASA — *Attitude sensors with navigation solutions*" (`s3vi.ndc.nasa.gov/...matsumoto.pdf`) to reflect its actual title and authorship: *"Guidance, Navigation, and Control of Small Satellite Attitude Using Micro-Thrusters"*, Cullen Matsumoto, M.S. thesis, University of Hawaiʻi at Mānoa, December 2016 (hosted on a NASA-affiliated knowledge base, not a NASA-authored publication). No change needed to the note's own claims — the thesis's abstract genuinely supports the IMU/EKF context it is cited for.
3. **[Control robótico, low priority]** Either fix the PX4Space citation's title string to the paper's actual title ("PX4Space: PX4 for Spacecraft and Space Robotics") or swap the cited URL for one that reliably serves the PDF to an automated/non-JS client — this audit found and read a working author-hosted mirror at `https://pedroroque.dev/assets/pdf/PX4Space.pdf`, which could replace or supplement the ETH bitstream link. The paper's own content (cascaded PI/PID + control allocator) fully supports what the note cites it for; only the link/title strings need attention.
4. **No remediation needed** for any of the three Analog Devices citations in Sensores de movimiento, or for any of the OpenStax/MIT/NASA-allocation citations in Momento y rotación/Control robótico — all confirmed real and correctly titled, either by direct fetch or by independent search corroboration.

**No remediation recommended for Momento y rotación at all** — this is the only one of the six notes audited across both lote-1 and lote-2 with zero findings of any kind.

---

## 8. Overall verdict + whether lote-2 may stay `solid`

| Note | Verdict | Stay `solid`? |
|---|---|---|
| Momento y rotación | **PASS** (zero findings) | **Yes** |
| Control robótico | **PASS** (two link/title-labeling notes, F1+F2, same underlying source) | **Yes** |
| Sensores de movimiento | **PASS** (one dead-but-mirrored link, F3; one title/attribution mismatch, F4) | **Yes** |

None of the three notes contains an invented physical number, a fabricated datasheet register/field, a fake section reference, a catalog/Continuity/FS/Safety SoT bleed, or an unhedged sim-equals-hardware overclaim. All four findings (F1–F4) are citation **labeling or link-staleness** issues on real, content-confirmed sources — not fabricated citations. Three of the four findings (F1, F2, F3) do not touch any claim's substance at all (the underlying documents' content was independently confirmed to support exactly what each note cites them for). F4 is the same class of issue as lote-1's own F2 (a real document, wrong title/attribution in the bullet, content still on-topic). Given the IC's own PASS/PASS WITH NOTES/FAIL rubric, this report keeps all three at **PASS** as the headline verdict — the recommended fixes are citation-string corrections only, with zero impact on truthfulness — while flagging exactly which small edits Cursor should apply (§7). **All three notes may remain `estado: solid`.** No downgrade to `draft` is warranted for any of the three.

---

## 9. Out of scope

- **Lote-1** (`Vectores`, `Dinámica`, `Control clásico`) — not re-audited; see the twin IC/report (`investigation_contract_ontology_spine_lote1_citation_review_b0.md` / `investigation_report_ontology_spine_lote1_citation_review_b0.md`) for that independent audit.
- The rest of the vault (~84 other notes, `00_Mapa/` hub/roadmap/template/concept-registry files) — out of this Buy's scope, already covered structurally (not content-graded) by the earlier `B0-ontology-vault-value-for-jarvis` report.
- Note prose style — per the IC's own stop conditions, no wording improvements were proposed for readability, only truth/citation/SoT issues.
- RAG readiness, retrieve-layer implementation, or any `intelligence/`-adjacent code — none touched, built, or recommended as ready.
- Obsidian math delimiter style (`$`/`$$`) — per the IC's own §2 Locked stance 7 (and lote-1's §2.6), this was **not** treated as a defect; it is the documented, intentional convention for this vault.

---

## 10. Non-edits (explicit)

**Claude did not edit any file under `ontology/` in this Buy.** This investigation used only `Read` (on the three audited notes) and read-only `Bash`/`WebFetch`/`WebSearch` tools (`shasum`, `curl -I`/`-v`, `pdftotext` run against locally-saved fetch results, and external URL fetches/searches) — no `Write`/`Edit` tool call was made against any path under `ontology/` at any point in this session.

```text
$ git status --short -- ontology/ src/ pyproject.toml
```

At close of this Buy, the working tree still reflects the same pre-existing, uncommitted state of the Engineer/Cursor's own offline spine-fill work already disclosed in the lote-1 twin report's own §10 (including the three files audited here, which were already at their current `solid` content before this investigation opened them). This investigation changed none of it. No file under `src/` was created or modified. `pyproject.toml` is unchanged (`version = "0.5.44"`). No git tag was created (`git tag -l | sort -V | tail -1` → `v0.5.44`).
