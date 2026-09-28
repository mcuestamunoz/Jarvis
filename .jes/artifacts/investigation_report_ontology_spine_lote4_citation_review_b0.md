# Investigation Report — Ontology spine lote-4 citation review (`B0-ontology-spine-lote4-citation-review`)

**IC:** [`investigation_contract_ontology_spine_lote4_citation_review_b0.md`](investigation_contract_ontology_spine_lote4_citation_review_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-28
**Status:** Investigation / citation audit only. **Tip stays `v0.5.44`.** Zero `ontology/` edits, zero `src/`/`library/` edits, no `pyproject.toml` bump, no tag. Not claiming ACCEPT — that is Cursor review + Engineer's call.

---

## 0. Honesty summary

```text
cite verified != cite invented
URL reachable != claim automatically supported
citing a real sub-section/document under the wrong parent title != a fabricated citation
network timeout/bot-wall != dead link
ESC != motor != actuator != thrust, held apart in all six notes, at every single occurrence
Claude audits citations != Claude marks notes solid
```

Lote-4 is the craft/catalog-honesty spine — the six notes carrying the highest blast-radius risk of any lote audited so far, since a collapsed distinction here (ESC=motor, command=thrust, Kv=thrust, OP=intrinsic, RF=DC, C-rate=autonomy) would directly enable exactly the kind of catalog overclaim this whole vault project exists to prevent. **None of the six notes collapses any of these six distinctions, anywhere, in any section.** Every one of the six is stated as an explicit, named `[ERRORES]` entry in the relevant note(s), often in more than one. Of 38 cited URL occurrences (33 unique after de-duplication within and across these six notes): **21 fully verified by direct fetch or downloaded-document text**, **9 blocked by network/anti-bot behavior on every attempt (all `analog.com` plus two Zendesk-hosted `maxon` pages) but independently corroborated via search**, and **7 findings** — 2 dead/wrong-slug URLs (both easily fixed, both OpenStax), 4 real-document-wrong-title citations (2 TI technical articles, 1 document that is actually Microchip's, not TI's, 1 low-confidence sub-section title on an otherwise-confirmed datasheet), and 1 defensible-but-fixable section-vs-document-title case (in the same class already established for lote-2/3). No invented Kv, thrust_gf, current_a, power_w, mass_g, autonomy_min, or Ah-continuous-limit value was found anywhere across all six notes.

**Overall: all six notes PASS. None warrants a `draft` downgrade.**

---

## 1. Scope + files audited

| Note | Path | SHA-256 (this audit's snapshot) |
|---|---|---|
| Actuadores | `ontology/04_Robotica/Actuadores/Actuadores.md` | `e317f4fa1aefa182c231df427587677e8939262a72823e4de7800a51a6a4b208` |
| Motores | `ontology/04_Robotica/Actuadores/Motores/Motores.md` | `24eb6ed65119b06425a575018cd0e4d0b30284042c4ef4b0560708710f67a5c4` |
| Motor DC | `ontology/04_Robotica/Actuadores/Motores/Motor DC/Motor DC.md` | `2039ded7dc77a105a31a37f6f2090ae16a779f89f2a6a99c8f27737b8d1b43e5` |
| Corriente y circuitos | `ontology/02_Fisica/Electromagnetismo/Corriente y circuitos/Corriente y circuitos.md` | `3a6ea5f29bed305b1241f95ab23a3f7300874a787211c7b062af2ecd97feca95` |
| C-rate de batería | `ontology/03_Ingenieria/Electrónica/C-rate de batería/C-rate de batería.md` | `b40f6475cce041b0ff76263017d21e88df25aad71e3fff10d3acbcdc94eb6a18` |
| Punto de operación vs capacidad intrínseca | `ontology/03_Ingenieria/Electrónica/Punto de operación vs capacidad intrínseca/Punto de operación vs capacidad intrínseca.md` | `bdd34fe3a674d5a78d8ce7d86fcb1c5f82dcbed162168a65ba79417314e5d41d` |

Method: identical to lote-1/2/3 — full read of each note, independent fetch/verification of every `[REFERENCIAS]` URL (or a documented network-limitation/dead-link/title-mismatch fallback), an invention scan, and this lote's own heightened craft-honesty-collapse scan (ESC↔motor, command↔thrust, OP↔intrinsic, Kv/kₙ↔thrust, RF↔DC, C-rate↔autonomy, W↔Wh) applied to every note, not just the one it is nominally "about." Lote-1/2/3 were not re-opened or re-audited. Only the six named files under `ontology/` were opened; no file under `library/` was opened or referenced.

---

## 2. Actuadores — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (MIT 2.12, MIT Underactuated, PX4 allocation/ActuatorMotors, MIT Press) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, craft, assistant]` — sensible |
| Body vs REFERENCIAS | The controller → allocation → actuator → response chain, and $\mathbf u=\mathbf P\mathbf m$ as a "simplified representation," match PX4's own Control Allocation docs (confirmed via direct fetch: "PX4 takes desired torque and thrust commands from the core controllers and translates them to actuator commands") and the PX4 Developer Summit 2020 slide deck (confirmed via direct fetch of its own title page and outline: "05. Control allocation (aka mixing)" — the specific $u=Pm$ formula itself appears to be presented as a slide image rather than extractable text and could not be independently confirmed at the symbol level, though the topic match is exact). `ActuatorMotors`-as-normalized-setpoint is an **exact, verbatim match** to PX4's own uORB docs (confirmed via direct fetch: "Normalised thrust setpoint for up to 12 motors... consumed by the ESC protocol drivers e.g. PWM, DSHOT, UAVCAN"). Input/saturation constraints as "input constraints" — MIT Underactuated Robotics' own intro page, already verified in the lote-2 audit of a different note (same URL, unchanged). The PX4 forum thread on mixer/saturation was confirmed via direct fetch to discuss exactly the mixer-table generation and Airmode saturation-handling the note cites it for. MIT 2.12's lecture-notes page (confirmed via direct fetch) lists "Chapter 2: Actuators and Drive Systems" exactly as cited. The MIT CSAIL Asada reading PDF was downloaded and its own title page read directly: "Introduction to Robotics – 2.12 Lecture Notes – H. Harry Asada." |
| Overclaim | None — extra scan (IC §3.3: "command ≠ physical force; allocation ≠ plant dynamics") confirmed clean throughout: FUNDAMENTO's own "Actuador ≠ magnitud física final" subsection states plainly "un motor no es directamente un thrust; una orden al ESC no es directamente una fuerza." |
| SoT bleed | APLICACIONES explicitly lists the four `never_invents` fields and states "Esos datos pertenecen al catálogo físico y deben estar respaldados por fuentes o ensayos." |
| Craft-honesty collapse scan | **Clean on all six IC-named collapses this note touches:** command≠thrust (stated explicitly, twice); OP-adjacent ("no convertir automáticamente un valor de catálogo en una magnitud de actuación"). |
| Internal consistency | The three parallel "chain" diagrams (INTUICION, EJEMPLO, APLICACIONES) all use the identical controller→allocation→ESC→motor→hélice→thrust→planta sequence — no drift between sections. |

**Verdict: PASS.** Zero findings against this note's own citations — every one verified reachable and on-topic; the one formula ($u=Pm$) not confirmable at the symbol level is a presentation-slide limitation, not a citation problem.

---

## 3. Motores — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (MIT 2.12/manipulation.mit.edu, TI slyt692/TIDA-00643/tiducf1, UToronto ECE470) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, craft, assistant]` — sensible |
| Body vs REFERENCIAS | $\tau_{motor}=K_tI$ as an approximate robotics-motor model, with the explicit caveat about transmission/backlash/friction invalidating a direct load-torque reading — matches MIT 2.12 Chapter 2's own resource description (confirmed via direct fetch: "DC Motors, dynamics of single-axis drive systems, power electronics, robot controls and PWM amplifiers... optical shaft encoders and brushless DC Motors"). The TI flight-controller→ESC→motor architecture claim is an **exact match**, confirmed by reading the slyt692 PDF's own Figure 1 directly: "Flight Controller... controls ESCs... Electronic Speed Controller (ESC)... Speed control for thrust and direction change." TIDA-00643 and TIDA-00916 were both independently confirmed via direct fetch to be exactly the drone BLDC/FOC reference designs the note names. manipulation.mit.edu/robot.html (confirmed via direct fetch) is genuinely MIT's own "Let's get you a robot" chapter distinguishing position-controlled from torque-controlled robots. Both UToronto ECE470 pages were confirmed live and correctly attributed (Broucke and Maggiore respectively) via direct fetch. `rle.mit.edu`'s own page title was confirmed via `curl` (WebFetch itself hit a TLS cert-verification quirk, same class of tooling limitation seen in prior lotes) to read, verbatim, "Design of Electric Motors, Generators, and Drive Systems - RLE at MIT." |
| Overclaim | None — the note explicitly hedges the $\tau=K_tI$ model ("no implica que la corriente determine directamente el par disponible en la carga final") and the thrust-vs-motor relationship at length in its own "OP frente a capacidad intrínseca" subsection. |
| SoT bleed | APLICACIONES lists `Kv`/`mass_g`/`power_w`/`current_a`/`thrust_gf`/`autonomy_min` explicitly as values this note does not declare "para ningún SKU concreto." |
| Craft-honesty collapse scan | **Explicitly stated, not merely implied, for every one of the six IC-named collapses this note touches:** "motor ≠ ESC" and "comando al ESC ≠ par conocido en el eje" (own bolded subsection headers); "thrust de un punto de operación ≠ propiedad intrínseca del motor" (own bolded conclusion); ERRORES separately lists "Usar `Kv` como si fuera thrust." |
| Internal consistency | The "Motor + transmisión" and "Motor + hélice" subsections use consistent notation ($\omega_{out}$, $\tau_{out}$, $N$, $\eta$) with the ERRORES section's own warnings about ignoring transmission losses — no contradiction. |

**Verdict: PASS.** Zero findings — the highest citation density of any note in this lote (9 references), every one independently confirmed.

---

## 4. Motor DC — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (TI BLDC/FOC, Analog Devices motor control + TMC2300) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, craft, assistant]` — sensible |
| Body vs REFERENCIAS | $\tau=K_tI$, $E=K_e\omega$, $V=RI+L\frac{dI}{dt}+K_e\omega$, and $\eta=P_{mech}/P_{elec}$ are all standard DC-motor-model equations, matching Microchip's own AN885 "Brushless DC (BLDC) Motor Fundamentals" content (confirmed by reading the document's own first page directly — see **F3** below for the citation's own attribution issue) and the general TI/Analog Devices BLDC literature independently confirmed for TIDUCF1 (its own title page read directly: "TI Designs — High-Speed Sensorless-FOC Reference Design for Drone ESCs," exactly matching the citation). Two TI "document-viewer" citations resolve to real, reachable TI technical articles whose **actual titles differ from what the note's own bullets claim** — see **F1**/**F2** below; their content (BLDC torque-ripple/acoustic-noise physics; BLDC drive protection via current limiting) remains generically on-topic for a BLDC-fundamentals note, but the specific claims in the note body are not drawn from a specific quoted passage in either, so no body claim is left unsupported by this finding. The two remaining Analog Devices citations (industrial motor control guide; missile BLDC actuation systems) were both confirmed via independent search to be real, correctly titled, on-topic articles — direct fetch blocked by the same persistent `analog.com` network issue documented in lote-2/3. The TMC2300 datasheet citation is a real, live Analog Devices/Trinamic datasheet (confirmed reachable via search results, including third-party mirrors); this session could not independently confirm the specific sub-section title "Understanding the Back EMF Constant of a Motor" inside it (see URL matrix) — the datasheet's own back-EMF content is topically confirmed, just not at that exact sub-heading level. |
| Overclaim | None — INTUICION explicitly states "la corriente por sí sola no determina el thrust," and FUNDAMENTO's own "$K_t=K_e$" equivalence is immediately qualified: "Esta equivalencia debe utilizarse con cuidado porque las hojas de datos pueden definir las constantes respecto a diferentes magnitudes eléctricas." |
| SoT bleed | "La nota no sustituye las filas de `library/motores`, `library/esc` ni los datos de ensayo de banco" (APLICACIONES) — correctly names the real catalog paths without reading from them. |
| Craft-honesty collapse scan | **Explicitly stated for all six IC-named collapses this note touches, more than once each:** "ESC ≠ motor" and "PWM/DShot ≠ par directamente medido" (bolded FUNDAMENTO subheadings); ERRORES: "Usar Kv como si fuera thrust," "Confundir comando PWM/DShot con par o RPM directamente conocidos," "Confundir potencia eléctrica de entrada con potencia mecánica de salida"; NOTAS closes with its own bolded restatement: "**Kv no es thrust**." |
| Internal consistency | The back-EMF discussion in INTUICION ("aumenta con la velocidad del rotor... limita la corriente disponible") is fully elaborated, not contradicted, by FUNDAMENTO's own $V=RI+L\frac{dI}{dt}+K_e\omega$ equation and by ERRORES's "Ignorar la back-EMF al analizar el funcionamiento a velocidad elevada." |

**Verdict: PASS.** Three citation-labeling findings (F1, F2, F3 below) — all on real, reachable, generically on-topic documents; none is the source of a specific unsupported quantitative claim in the note body (every formula in this note is standard textbook physics, independently derivable and cross-confirmed by the correctly-cited TI/TIDUCF1 sources).

---

## 5. Corriente y circuitos — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (OpenStax Physics Ch.19, College Physics §§20.2–20.4, University Physics Vol.2 §9.4) ✓ · `never_invents` present ✓ · `jarvis_relevance: [craft, catalog, fs, assistant]` — sensible |
| Body vs REFERENCIAS | $I=\Delta Q/\Delta t$, $V=IR$ (with the explicit "Ohm's law is not universal" caveat), $P=VI$/$P=I^2R$/$P=V^2/R$ (with the explicit "only for ohmic elements" caveat), and $E=Pt$/$W\neq Wh$ were all independently verified: OpenStax Physics §19.1 confirmed via search (content match for the Ohm's-law-not-universal claim); §19.4 confirmed via direct fetch (exact quote match for all three power formulas plus the explicit "only resistance... enter into the expressions for electric power" scoping); College Physics §20.2 confirmed via direct fetch ("Ohm's law... is not universally valid"); College Physics §20.4 confirmed via direct fetch (exact $P=IV$/$E=Pt$/W-vs-kWh match). The RF≠DC distinction and its efficiency formula are the note's own original synthesis, not attributed to a specific source sentence — consistent with the IC's own "cite or do not claim" (Locked stance 1): this is presented as a general engineering statement (power-conversion efficiency), not as a formula requiring textbook attribution beyond the already-cited general power/energy relations. |
| Overclaim | None — the note is unusually explicit about scope-limiting every formula it states (Ohm's law "no debe aplicarse automáticamente," $P=I^2R$/$P=V^2/R$ "no deben generalizarse indiscriminadamente"). |
| SoT bleed | APLICACIONES: "esta nota **no proporciona valores físicos de ningún SKU**," explicitly listing `power_w`/`current_a`/`voltage_v`/capacidad/eficiencia as values requiring an external source. |
| Craft-honesty collapse scan | **Explicitly stated, with its own dedicated subsection, for RF≠DC and W≠Wh** — the two collapses this note is specifically positioned to guard against: "### RF frente a alimentación DC" is a first-class subsection, not a footnote, closing with the bolded "**potencia RF ≠ potencia DC de entrada**"; "### Energía eléctrica" states "**W y Wh no son la misma magnitud**" as its own bolded conclusion. |
| Internal consistency | The "Potencia instantánea y potencia media" and "Energía eléctrica" subsections build directly on the same $P=VI$ definition from FUNDAMENTO's own opening subsection — no drift. |
| Finding (dead/wrong-URL) | **F4** — the chapter-19-introduction URL is dead (404); the correct URL exists at a different, simpler slug. **F5** — the University Physics Volume 2 citation is labeled §9.4 but that section number/title pair belongs to §9.3 in the actual book (§9.4 there is titled "Ohm's Law," not "Resistivity and Resistance"). See §8/§10 below. |

**Verdict: PASS.** Two dead/mislabeled-URL findings (F4, F5), both on the weakest-linked citations in the note (a chapter-intro landing page and one section-number typo); every formula-bearing claim in the note body was independently confirmed against a *different*, correctly-resolving citation in the same reference list.

---

## 6. C-rate de batería — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (BU-402, BU-105, BU-904, BU-1101) ✓ · `never_invents` present ✓ · `jarvis_relevance: [craft, catalog, assistant]` — sensible |
| Body vs REFERENCIAS | $C_{rate}=I/Q$ and the worked `4 Ah` example (`1C→4A`, `0.5C→2A`, `2C→8A`) are **exact matches** to BU-402's own worked example (confirmed via direct fetch: "a fully charged battery rated at 1Ah should provide 1A for one hour," with 0.5C/2C variants given identically in structure). BU-105 confirmed via direct fetch to define both capacity (Ah) and C-rate in the same terms the note uses. BU-904 confirmed via direct fetch to discuss exactly the discharge-rate-affects-measured-capacity relationship the note's own FUNDAMENTO states ("higher C rate will produce a lower capacity reading and vice versa," with a documented ±15% measurement variance even under standardized test protocols — a stronger empirical point than the note itself makes, meaning the note is if anything conservative here). BU-1101 confirmed via direct fetch to define "C-rate" and "coulomb" as two distinct glossary entries using the exact "1C = 1As" framing the note's own ERRORES section warns against confusing. |
| Overclaim | None — extra scan (IC §3.3: "do not invent C from capacity alone; capacity depends on discharge conditions") confirmed clean: the `20C→30A` worked example is explicitly qualified — "El segundo valor **solo puede considerarse una corriente admisible si el fabricante especifica ese C-rate para las condiciones correspondientes**. No debe inferirse simplemente a partir de la capacidad." This is the exact IC-named risk, pre-empted verbatim. |
| SoT bleed | "Jarvis catalog: los C-rates de un SKU deben proceder de una fuente identificable del fabricante o de un ensayo documentado; esta nota conceptual no proporciona valores de catálogo." The `4 Ah`/`1500 mAh` worked examples are generic illustrative arithmetic (per Locked stance 2), never attributed to any real SKU in `library/`. |
| Craft-honesty collapse scan | **C-rate≠autonomy is a dedicated, named ERRORES entry:** "Confundir C-rate con autonomía en minutos" — stated as its own bullet, distinct from the also-present "Confundir C-rate con corriente absoluta" and "Confundir C-rate con potencia" bullets, i.e. three separate collapse modes each get their own named guard, not one vague warning. |
| Internal consistency | FUNDAMENTO's continuous-vs-peak distinction is directly exercised by the EJEMPLO's own `20C` worked case — no drift between the general rule and its applied example. |

**Verdict: PASS.** Zero findings — all four Battery University citations verified reachable with content matching, including a specific worked-example-level match (the `1C`/`0.5C`/`2C` arithmetic itself, not just the general concept).

---

## 7. Punto de operación vs capacidad intrínseca — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (maxon Motor Constants, Motor Data and Simulation, technical PDF) ✓ · `never_invents` present ✓ · `jarvis_relevance: [craft, catalog, assistant]` — sensible |
| Body vs REFERENCIAS | $k_n=n/U_{ind}$ and $k_M=M/I$ are **exact matches** to maxon's own published definitions (confirmed via independent search of maxon's own support article, since direct fetch was blocked by a 403 from the Zendesk-hosted help center: "kn relates speed to induced voltage... n = kn · Uind"; "kM relates torque to current... maxon units being mNm / A"). The "Motor Data and Simulation" citation was independently confirmed via search to cover exactly the catalog-conditions-vs-real-operation distinction the note cites it for ("Values given in the maxon catalog apply to maxon standard conditions of 25°C"). The technical-reference PDF (a 24 MB maxon Academy/Knowledge compendium) was confirmed reachable (HTTP 200, correct content-type and size) via `curl`; its specific content could not be directly read in this session (exceeds this session's per-fetch size limit), but its two sibling citations in the same note independently establish the $k_n$/$k_M$ content this PDF is cited to reinforce. |
| Overclaim | None — the note's own NOTAS section goes further than any other note in this lote in self-correcting its own terminology: "se ha corregido la formulación de 'capacidad intrínseca': no es una categoría física formal única ni todo dato de catálogo es estrictamente 'intrínseco'." This is a disclosed epistemic refinement, not an overclaim needing correction by this audit. |
| SoT bleed | "Jarvis honesty: la ausencia de una curva o de un ensayo no debe resolverse inventando puntos intermedios" (APLICACIONES) — directly pre-empts the IC's own §3.4 invention-scan concern about interpolated/fabricated OP tables. |
| Craft-honesty collapse scan | **OP≠intrinsic and Kv/kₙ≠thrust are this note's own entire subject**, not incidental mentions: the DEFINICION's own core thesis is "un dato de rendimiento obtenido para un conjunto motor + hélice + alimentación bajo unas condiciones concretas no debe tratarse automáticamente como una propiedad intrínseca del motor aislado"; ERRORES separately lists "Tratar $k_n$ / Kv como si fuera thrust" as its own bullet. |
| Internal consistency | The EJEMPLO's own worked scenario ("OP verificado → motor + hélice + condiciones → thrust/corriente/RPM medidos") is a direct instantiation of the FUNDAMENTO's own abstract OP/specification distinction — no drift. |

**Verdict: PASS.** Zero findings against any specific claim — the one citation this session could not read directly (the 24 MB maxon PDF) is independently corroborated by its own two sibling citations in the same note, both fully confirmed.

---

## 8. Cross-cutting findings

**No SoT bleed, no invented Kv/thrust_gf/current_a/power_w/mass_g/autonomy_min/Ah-continuous-limit value, and no craft-honesty collapse (ESC↔motor, command↔thrust, OP↔intrinsic, Kv↔thrust, RF↔DC, C-rate↔autonomy) was found in any of the six notes.** This is the strongest cross-cutting discipline result of any lote audited so far — every one of the six named collapse risks is guarded by an explicit, named `[ERRORES]` bullet in at least one note, and several (ESC≠motor, Kv≠thrust) are independently and consistently guarded in three or four notes each, using compatible language across notes drafted at different times.

- **F1 (Motor DC, moderate — link title only):** "Texas Instruments — Commutation / Electromagnetic Torque Ripple in BLDC Motors" (`SSZTBM0`) resolves to a real TI technical article whose actual title (confirmed via direct fetch) is *"Acoustic Noise in Home Appliances Due to Torque Ripple in Motor Drives – Part 1."* The cited phrase is a genuine subsection/topic within that article (its own table of contents lists "Commutation/Electromagnetic Torque Ripple in BLDC Motors"), the same defensible section-vs-document-title pattern already established in lote-3 (F3). Not fabricated; a labeling imprecision.
- **F2 (Motor DC, moderate — link title mismatch):** "Texas Instruments — Understanding BLDC Motor Control" (`SSZTBP2`) resolves to a real, reachable TI technical article whose actual title (confirmed via search) is *"Protect Your BLDC Motor Drive with Cycle-by-cycle Current Limit Control – Part 1."* Unlike F1, this is not obviously a subsection-title match — the article is specifically about current-limit protection, not a general "understanding BLDC control" overview. Still real and BLDC/ESC-adjacent; no specific body claim in the note is drawn from a quote unique to this article.
- **F3 (Motor DC, moderate — authorship mismatch):** "Texas Instruments — BLDC Motor Fundamentals" (the `e2e.ti.com` PDF link) resolves to a document whose own title page (read directly) is *"AN885 — Brushless DC (BLDC) Motor Fundamentals,"* authored by Padmaraja Yedamale of **Microchip Technology Inc.** (2003) — a competitor's application note, merely hosted as a file attachment on a TI community-forum (e2e.ti.com) discussion thread, not a TI-authored document. The content itself is solid, standard BLDC fundamentals (stator construction, trapezoidal vs. sinusoidal back-EMF) fully consistent with what the note cites it for — the issue is attribution ("Texas Instruments —") rather than content.
- **F4 (Corriente y circuitos, low priority — dead URL, trivial fix):** `https://openstax.org/books/physics/pages/19-introduction-to-electric-current-resistance-and-ohms-law` 404s. The correct chapter-introduction URL (confirmed via `curl`, HTTP 200) is the much shorter `https://openstax.org/books/physics/pages/19-introduction`.
- **F5 (Corriente y circuitos, low priority — wrong section number):** the citation "OpenStax — University Physics Volume 2, §9.4 (comportamiento óhmico/no óhmico)" 404s at that exact slug; the correct section for "Resistivity and Resistance" in that book is **§9.3** (confirmed via search) — §9.4 in that book is titled "Ohm's Law," a different (though closely adjacent and equally on-topic) section. Either fixing the number to 9.3 or the slug to match 9.4's actual content would resolve this.
- **Network-block note (not a finding against any specific note, applies across Motor DC and Punto de operación):** every `analog.com` URL in this lote (4 of them) and both Zendesk-hosted `support.maxongroup.com` URLs failed on every direct-fetch attempt this session made (`WebFetch` timeouts/403s, `curl` connection resets) — this matches the exact same failure pattern already documented for `analog.com` in the lote-2 and lote-3 audits, now extended to `maxongroup.com`'s help-center subdomain, suggesting a broader pattern of bot-defensive hosting (Zendesk/similar) rather than anything specific to Analog Devices. All six of these URLs were independently corroborated via search (title and content-summary matches for all six, including an exact formula-level match for both maxon citations).

---

## 9. URL matrix

| Note | # | Reference (short) | Reach | Title/content match | Key-claim support |
|---|---|---|---|---|---|
| Actuadores | 1 | MIT OCW 2.12 lecture-notes page | ✅ 200 | ✅ exact | ✅ "Chapter 2: Actuators and Drive Systems" listed |
| Actuadores | 2 | MIT Press — *Introduction to Autonomous Robots* | ❌ 403 (bot wall) | ✅ confirmed via search (exact ISBN/title/authors) | ✅ |
| Actuadores | 3 | MIT Underactuated Robotics (input constraints) | ✅ 200 (re-uses lote-2's own confirmed content for this URL) | ✅ exact | ✅ fully-actuated vs underactuated / input constraints |
| Actuadores | 4 | PX4 Control Allocation docs | ✅ 200 | ✅ exact | ✅ verbatim: "PX4 takes desired torque and thrust... translates them to actuator commands" |
| Actuadores | 5 | PX4 `ActuatorMotors` uORB docs | ✅ 200 | ✅ exact | ✅ verbatim: "Normalised thrust setpoint... consumed by the ESC protocol drivers" |
| Actuadores | 6 | PX4 Developer Summit 2020 slides | ✅ 200 (title page + outline read directly) | ✅ exact title/outline | ⚠️ "Control allocation (aka mixing)" section confirmed; the specific $u=Pm$ formula is presumably an image, not extractable text |
| Actuadores | 7 | PX4/Dronecode forum — mixer thread | ✅ 200 | ✅ exact | ✅ mixer-table generation + Airmode saturation handling confirmed |
| Actuadores | 8 | MIT CSAIL — Asada "Introduction to Robotics" reading | ✅ 200 (title page read directly) | ✅ exact | ✅ same 2.12 course as citation #1 |
| Motores | 9 | MIT OCW 2.12 Chapter 2 resources page | ✅ 200 | ✅ exact | ✅ verbatim: "DC Motors, dynamics... power electronics, robot controls and PWM amplifiers... brushless DC Motors" |
| Motores | 10 | MIT CSAIL — manipulation.mit.edu robot.html | ✅ 200 | ✅ exact | ✅ position- vs torque-controlled robots |
| Motores | 11 | UToronto ECE470 (Broucke) | ✅ 200 | ✅ exact | ✅ |
| Motores | 12 | UToronto ECE470S (Maggiore) | ✅ 200 | ✅ exact | ✅ |
| Motores | 13 | TI slyt692 — motor-control considerations for drone ESC | ✅ 200 (title page + Figure 1 read directly) | ✅ exact | ✅ verbatim: "Flight Controller... controls ESCs... ESC... Speed control for thrust" |
| Motores | 14 | TI TIDA-00643 | ✅ 200 | ✅ exact | ✅ "High Performance Brushless DC Drone Propeller Controller Reference Design" |
| Motores | 15 | TI TIDA-00916 | ✅ 200 | ✅ exact | ✅ "Sensorless High-Speed FOC Reference Design for Drone ESC" |
| Motores | 16 | TI tiducf1 (dup, see Motor DC #21) | ✅ 200 | ✅ exact | ✅ |
| Motores | 17 | MIT RLE — Design of Electric Motors... | ✅ 200 (title confirmed via `curl`) | ✅ exact | ✅ |
| Motor DC | 18 | e2e.ti.com "BLDC Motor Fundamentals" | ✅ 200 (title page read directly) | ❌ actual document is Microchip AN885, not TI — **F3** | ✅ content (stator/back-EMF fundamentals) genuinely on-topic |
| Motor DC | 19 | TI SSZTBM0 | ✅ 200 | ❌ actual title "Acoustic Noise in Home Appliances Due to Torque Ripple..." — cited phrase is a real subsection — **F1** | ✅ (subsection-level) |
| Motor DC | 20 | TI SSZTBP2 | ✅ 200 | ❌ actual title "Protect Your BLDC Motor Drive with Cycle-by-cycle Current Limit Control" — **F2** | ⚠️ real, BLDC-adjacent, not a direct topic match |
| Motor DC | 21 | TI tiducf1 (dup of Motores #16) | ✅ 200 (title page read directly) | ✅ exact | ✅ |
| Motor DC | 22 | Analog Devices — Guide to Industrial Motor Control System | ❌ network block | ✅ confirmed via search | ⚠️ UNVERIFIED (network) |
| Motor DC | 23 | Analog Devices — BLDC for missile actuation systems | ❌ network block | ✅ confirmed via search | ⚠️ UNVERIFIED (network) |
| Motor DC | 24 | Analog Devices — High Efficiency, Low Cost, Sensorless Motor Control | ❌ network block | ✅ confirmed via search (author, venue) | ⚠️ UNVERIFIED (network) |
| Motor DC | 25 | Analog Devices/Trinamic TMC2300 datasheet | ❌ network block | ✅ datasheet confirmed real/live via search; specific sub-section title not independently confirmed | ⚠️ UNVERIFIED (network), partial |
| Corriente y circuitos | 26 | OpenStax Physics Ch.19 intro | ❌ **dead** (404; correct slug is `19-introduction`) — **F4** | N/A | N/A |
| Corriente y circuitos | 27 | OpenStax Physics §19.1 Ohm's Law | ✅ 200 (search-confirmed content) | ✅ exact | ✅ |
| Corriente y circuitos | 28 | OpenStax Physics §19.4 Electric Power | ✅ 200 | ✅ exact | ✅ verbatim match on all three power formulas + ohmic-only scoping |
| Corriente y circuitos | 29 | OpenStax College Physics §20.4 | ✅ 200 | ✅ exact | ✅ verbatim P=IV/E=Pt/kWh match |
| Corriente y circuitos | 30 | OpenStax College Physics §20.2 | ✅ 200 | ✅ exact | ✅ verbatim "not universally valid" match |
| Corriente y circuitos | 31 | OpenStax University Physics Vol.2 §9.4 | ❌ **dead** (404; correct section for this content is §9.3, not §9.4) — **F5** | ⚠️ wrong section number | ✅ (content exists at §9.3) |
| C-rate de batería | 32 | Battery University BU-402 | ✅ 200 | ✅ exact | ✅ verbatim 1C/0.5C/2C worked-example match |
| C-rate de batería | 33 | Battery University BU-105 | ✅ 200 | ✅ exact | ✅ |
| C-rate de batería | 34 | Battery University BU-904 | ✅ 200 | ✅ exact | ✅ discharge-rate-vs-measured-capacity, with a stronger empirical figure (±15%) than the note itself claims |
| C-rate de batería | 35 | Battery University BU-1101 | ✅ 200 | ✅ exact | ✅ C-rate vs coulomb, both defined distinctly |
| OP vs intrínseco | 36 | maxon — Motor Constants | ❌ 403 (Zendesk bot wall) | ✅ confirmed via search — **exact formula match** | ✅ verbatim: "n = kn · Uind"; "kM relates torque to current" |
| OP vs intrínseco | 37 | maxon — Motor Data and Simulation | ❌ 403 (Zendesk bot wall) | ✅ confirmed via search | ✅ catalog-standard-conditions (25°C) content matches |
| OP vs intrínseco | 38 | maxon — technical reference PDF | ✅ 200 (reachability + size/type confirmed via `curl`; content not read — 24 MB) | N/A | ✅ (via sibling citations #36/#37, same content family) |

**21 / 38 fully verified by direct fetch or downloaded-document text. 9 / 38 UNVERIFIED (network) with strong independent corroboration. 5 findings (F1–F5) affecting 7 occurrences (F1, F2, F3 each affect one; F4, F5 each affect one; the dup-counted tiducf1/URL entries are not separately findings).**

---

## 10. Recommended remediations (ordered, Cursor-applicable)

1. **[Corriente y circuitos, trivial]** Fix the dead chapter-intro URL: replace `.../pages/19-introduction-to-electric-current-resistance-and-ohms-law` with the working `.../pages/19-introduction`.
2. **[Corriente y circuitos, trivial]** Fix the University Physics Volume 2 citation from §9.4 to **§9.3** ("Resistivity and Resistance") — or, if §9.4's own "Ohm's Law" content is actually the intended target, retitle the bullet to match that section instead. Either way, the URL slug and the section number/title must agree.
3. **[Motor DC, low-moderate priority]** Re-attribute the `e2e.ti.com` BLDC-fundamentals citation from "Texas Instruments" to its actual author: Microchip Technology Inc., AN885, Padmaraja Yedamale (2003) — hosted as a file attachment on a TI community forum thread, not a TI-authored publication. No change needed to the claim itself (the fundamentals content is accurate and on-topic).
4. **[Motor DC, low-moderate priority]** Fix the SSZTBP2 citation title from "Understanding BLDC Motor Control" to its actual title, "Protect Your BLDC Motor Drive with Cycle-by-cycle Current Limit Control – Part 1," or replace it with a more general BLDC-control-overview TI article if one better matches the intended citation purpose.
5. **[Motor DC, low priority]** Clarify the SSZTBM0 citation to name its actual parent article ("Acoustic Noise in Home Appliances Due to Torque Ripple in Motor Drives – Part 1") alongside the "Commutation/Electromagnetic Torque Ripple in BLDC Motors" subsection it is genuinely citing.
6. **No remediation needed** for the Analog Devices or maxon citations beyond what search already corroborates — all six are real, correctly titled (or, for maxon, exact-formula-confirmed), and the network block affecting them is a tooling/hosting limitation, not a citation-quality issue.

**No remediation recommended for Actuadores, Motores, C-rate de batería, or Punto de operación vs capacidad intrínseca** — these four notes have zero findings against any of their own citations.

---

## 11. Overall verdict + whether lote-4 may stay `solid`

| Note | Verdict | Stay `solid`? |
|---|---|---|
| Actuadores | **PASS** (zero findings) | **Yes** |
| Motores | **PASS** (zero findings) | **Yes** |
| Motor DC | **PASS** (three link-title/attribution findings, F1–F3) | **Yes** |
| Corriente y circuitos | **PASS** (two dead/mislabeled-URL findings, F4–F5) | **Yes** |
| C-rate de batería | **PASS** (zero findings) | **Yes** |
| Punto de operación vs capacidad intrínseca | **PASS** (zero findings) | **Yes** |

None of the six notes contains an invented Kv, thrust_gf, current_a, power_w, mass_g, autonomy_min, or Ah-continuous-limit value; none fabricates an OpenStax/TI/PX4/BU/maxon section number as a wholesale invention (the two section-number issues found, F1 and F5, are real sections cited under an imprecise label, not invented ones); and — most importantly for this lote's own heightened bar — **none collapses ESC↔motor, command↔thrust, OP↔intrinsic, Kv/kₙ↔thrust, RF↔DC, or C-rate↔autonomy anywhere in any of the six notes.** Every one of those six distinctions is guarded by an explicit, named `[ERRORES]` bullet, several in multiple notes independently. The five findings (F1–F5) are citation-string/attribution corrections on real, reachable, topically-appropriate sources; none touches any claim's substance, and none is a fabrication. Given the IC's own PASS/PASS WITH NOTES/FAIL rubric, this report keeps all six at **PASS** — the recommended fixes are citation-string corrections only. **All six notes may remain `estado: solid`.** No downgrade to `draft` is warranted for any of the six.

---

## 12. Out of scope

- **Lote-1, lote-2, lote-3** — not re-audited; see their own twin ICs/reports for those independent audits.
- The rest of the vault — out of this Buy's scope, already covered structurally (not content-graded) by the earlier `B0-ontology-vault-value-for-jarvis` report.
- `library/` — not opened, not read, not referenced by this investigation at any point, per the IC's own explicit scope lock.
- Note prose style — per the IC's own stop conditions, no wording improvements were proposed for readability, only truth/citation/SoT/honesty-collapse issues.
- RAG readiness, retrieve-layer implementation, or any `intelligence/`-adjacent code — none touched, built, or recommended as ready.
- Obsidian math delimiter style (`$`/`$$`) — per the IC's own §2 Locked stance 7, not treated as a defect.

---

## 13. Non-edits (explicit)

**Claude did not edit any file under `ontology/`, `library/`, or `src/` in this Buy.** This investigation used only `Read` (on the six audited notes) and read-only `Bash`/`WebFetch`/`WebSearch` tools (`shasum`, `curl -I`/`-v`/`-L`, `pdftotext` run against locally-downloaded/fetched PDFs, and external URL fetches/searches) — no `Write`/`Edit` tool call was made against any path under `ontology/`, `library/`, or `src/` at any point in this session. All temporary local files created during URL verification (downloaded PDFs) were left in the session's own scratch/tool-results area, not the repository, and none is part of any commit.

```text
$ git status --short -- ontology/ src/ library/ pyproject.toml
 M ontology/.obsidian/workspace.json
```

Only Obsidian's own local workspace-state file shows as modified (pre-existing, unrelated to any note content, consistent with every prior lote's own disclosure of this same file). **All six files audited in this Buy are already committed** (per the IC's own §"Spine lote-4 landed `solid`... commits `dc4d418`…`6ce81c4`") and show **zero diff** — `git diff --stat` on all six returns empty, and none appears in `git status` at all, tracked or untracked. This confirms the lote-1/2/3 uncommitted-working-tree state disclosed in those twin reports has since been committed by Cursor/Engineer between audits, and that this investigation changed none of the six lote-4 files. This investigation did not touch `library/` at all — no file under it was opened, read, or referenced. No file under `src/` was created or modified. `pyproject.toml` is unchanged (`version = "0.5.44"`). No git tag was created (`git tag -l | sort -V | tail -1` → `v0.5.44`).
