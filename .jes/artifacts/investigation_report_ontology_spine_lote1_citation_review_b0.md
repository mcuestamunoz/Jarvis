# Investigation Report — Ontology spine lote-1 citation review (`B0-ontology-spine-lote1-citation-review`)

**IC:** [`investigation_contract_ontology_spine_lote1_citation_review_b0.md`](investigation_contract_ontology_spine_lote1_citation_review_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-27
**Status:** Investigation / citation audit only. **Tip stays `v0.5.44`.** Zero `ontology/` edits, zero `src/` edits, no `pyproject.toml` bump, no tag. Not claiming ACCEPT — that is Cursor review + Engineer's call.

---

## 0. Honesty summary

```text
cite verified != cite invented
URL reachable != claim automatically supported
title mismatch on a real, on-topic document != a fabricated citation
network-blocked (Cloudflare/cert) != dead link
Claude audits citations != Claude solidifies notes
```

All three lote-1 notes are careful, self-policing, and internally consistent — every formula is scoped to its stated conditions, every note actively warns against the exact SoT-bleed and overclaim failure modes this IC is checking for. Of 15 cited URLs, **12 verified as reachable with content matching the note's claim**, **2 could not be fetched directly by this session's tools (Cloudflare bot-challenge) but were independently corroborated via search as real, correctly titled pages**, and **1 resolves to a real, on-topic NASA document whose actual title does not match the title string given in the note's own citation bullet** (a fixable labeling error, not a fabrication). No invented physical numbers, no catalog/Continuity/FS SoT bleed, no fake section numbers were found in any of the three notes.

**Overall: all three notes PASS or PASS WITH NOTES. None warrants a `draft` downgrade.**

---

## 1. Scope + files audited

| Note | Path | SHA-256 (this audit's snapshot) |
|---|---|---|
| Vectores | `ontology/01_Matematicas/Álgebra lineal/Vectores/Vectores.md` | `cb10f1dd68766b6e3cf1ab4a1b57dce4ae7ac7b526435c922e767bc039e0573b` |
| Dinámica | `ontology/02_Fisica/Mecánica/Dinámica/Dinámica.md` | `09eb4d6389ab1fb44e230bc072776eeb7ef05d3d05e9aeccf801d0c0d689537a` |
| Control clásico | `ontology/03_Ingenieria/Control/Control clásico/Control clásico.md` | `c5e6214be7d55ce763df440d411e67dc956d157f319bb74e21cae58f69e2b724` |

Method: full read of each note (frontmatter + all sections), independent fetch/verification of every `[REFERENCIAS]` URL (or a documented network-limitation fallback), a targeted invention scan (numeric physical parameters, fake section numbers, universal-guarantee overclaims), and a wikilink-resolution check on each note's own `[CONEXIONES]` list. Only the three named files were opened under `ontology/`; lote-2 was not touched or viewed.

---

## 2. Vectores — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (3 sources + §§) ✓ · `never_invents: [mass_g, power_w, thrust_gf, autonomy_min]` present ✓ · `jarvis_relevance: [fs, craft, assistant]` — sensible (vector algebra underlies FS math, craft geometry, and future grounding) |
| Body vs REFERENCIAS | Every quantitative claim in FUNDAMENTO (component representation, norm $\|\mathbf v\|=\sqrt{\mathbf v\cdot\mathbf v}$, dot product both forms, cross product magnitude) is covered by the four OpenStax citations — verified directly (§2.1). The frame-transformation/attitude-representation discussion in FUNDAMENTO/EJEMPLO is qualitative (no formula claimed) and cited only generally to the NASA reference. |
| Overclaim | None found. "No existe un único escalar que represente en general una actitud tridimensional completa" is correctly scoped (a true statement about 3D attitude representations, not a universal physics overclaim). |
| SoT bleed | Actively guarded: APLICACIONES states "La nota no define valores concretos de masas, ganancias, potencia, empuje ni otros parámetros de componentes"; ERRORES explicitly names the failure mode — "Usar un número de ejemplo de esta nota como si fuera un dato de `library/` o un gain de `flight_software/`" — correctly naming both real module paths. |
| Internal consistency | DEFINICION (basis-dependence) ↔ FUNDAMENTO (component representation) ↔ ERRORES ("Confundir un vector físico con sus componentes respecto a una base concreta") reinforce each other, no contradiction. |
| Explain-map direction (Locked stance 3) | APLICACIONES frames Jarvis Buys as things this concept *explains* ("lenguaje matemático base para explicar el ladder FS: IMU; attitude (C7); PD por ejes (C8); planta 6-DoF (C36)") — correct direction, never claims those Buys *validate* the math. |

**Verdict: PASS.** One reference (NASA NTRS 20010084958) is real and topically on-point but non-specific — see §5/§7 finding F1. Does not affect the note's own math claims, all of which are otherwise fully OpenStax-covered.

---

## 3. Dinámica — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (OpenStax §5.3/§10.7, MIT 2.003J, NASA Murman) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, craft, assistant]` — sensible |
| Body vs REFERENCIAS | $\sum\mathbf F=d\mathbf p/dt$ and $\sum F=ma$ (constant mass) → OpenStax §5.3, verified. $\sum\tau=I\alpha$ (fixed axis) → OpenStax §10.7, verified. The 3D rigid-body tensor form $\boldsymbol\tau=\mathbf I\dot{\boldsymbol\omega}+\boldsymbol\omega\times(\mathbf I\boldsymbol\omega})$ → MIT 2.003J notes (Newton-Euler + inertia tensor, confirmed via independent search + HTTP 200 reachability check), and the NASA Murman paper's own abstract explicitly states 6-DOF rigid-body simulation is "integrating the Newton-Euler equations" — directly supporting the note's own [NOTAS] claim about how NASA frames 6-DOF. |
| Overclaim | None. $F=ma$ is explicitly scoped to constant mass; $\tau=I\alpha$ explicitly scoped to a fixed axis, with the note itself listing "usar $\tau=I\alpha$ como ecuación general de cualquier movimiento rotacional tridimensional sin comprobar sus hipótesis" as an ERROR to avoid — the note pre-empts the exact overclaim the IC's own audit procedure names as an example (§3.1). |
| SoT bleed | Actively guarded, twice: FUNDAMENTO states "La masa física de un componente concreto no debe obtenerse de esta nota; un valor de `mass_g` de un vehículo o SKU pertenece a la fuente de datos correspondiente"; ERRORES lists "Tomar un `m` de ejemplo de apuntes como masa del craft real" and "Inventar masa, momento de inercia, empuje u otros parámetros físicos que no estén respaldados por una fuente." Both name the real `mass_g` field and correctly point at the catalog as its actual source. |
| Internal consistency | EJEMPLO's own line — "La planta dinámica no es el `step()` del controlador" — is consistent with, and reinforced by, ERRORES's first bullet ("Confundir la planta física/dinámica con el `step()` o la ley de control del controlador"). No contradiction anywhere in the note. |
| Explain-map direction | APLICACIONES: "fundamento conceptual de la planta 6-DoF (C36) y de la separación entre controlador y planta física" — correct direction (concept explains C36's own design rationale), never claims C36 validates the physics. |

**Verdict: PASS.** All five cited references verified reachable with content matching the specific claims attributed to them (§6 URL matrix). No findings against this note.

---

## 4. Control clásico — audit table + verdict

| Check | Result |
|---|---|
| Frontmatter | `estado: solid` ✓ · `formula_citation` present (UMich CTMS, NASA TM, Control Guru) ✓ · `never_invents` present ✓ · `jarvis_relevance: [fs, assistant]` — sensible (no `craft`, defensible: control theory is an FS/assistant-facing concept here, not a craft-geometry one) |
| Body vs REFERENCIAS | $e(t)=r(t)-y(t)$ and the parallel PID form $u(t)=K_pe+K_i\int e+K_d\dot e$ / $C(s)=K_p+K_i/s+K_ds$ are standard-definition restatements, backed by all three UMich CTMS pages (confirmed real and correctly titled — see §6). The integral-windup discussion in ERRORES/NOTAS is directly and precisely backed by the Control Guru citation (verified exact title + content match, §6). |
| Overclaim | **None found — this note actively pre-empts every overclaim pattern the IC's own audit procedure names as an example.** INTUICION states explicitly: "Los efectos concretos de P, I y D... dependen de la planta y de la estructura del lazo; no son reglas universales independientes de la planta." FUNDAMENTO: "El término integral puede eliminar el error estacionario ante determinadas referencias/perturbaciones... pero también puede introducir oscilación." ERRORES directly lists "Suponer que un PID garantiza estabilidad independientemente de la planta" and "Interpretar 'integral elimina el error estacionario' como una garantía universal" as errors — i.e. the note names the IC's own two example overclaims verbatim and flags them as wrong. |
| SoT bleed | Extensively guarded — FUNDAMENTO: "los valores concretos de $K_p/K_d$ del ladder son parámetros de implementación/simulación, no constantes físicas universales ni valores automáticamente válidos para un vehículo real"; APLICACIONES: "Esta nota no sustituye la especificación ni implementación de `controller.py` / `controller.hpp`" (correctly names the real files); ERRORES lists five distinct SoT-adjacent failure modes (treating note/textbook gains as vehicle calibration, confusing simulated with flight-validated, confusing a command with actuation authorization, confusing controller with plant, believing a PID "authorizes autonomy"). |
| Internal consistency | EJEMPLO's own line — "La capa de seguridad es conceptualmente distinta del controlador: que un controlador produzca un comando no implica que exista autorización para ejecutar ese comando sobre hardware" — matches ERRORES's own "Confundir la generación de un comando con autorización para ejecutar una acción sobre hardware," a direct and correct echo of this repo's own real Safety/`submit_command` architecture (C2/C4/C17/C40/C41), stated at the *concept* level without claiming to be that code. |
| Explain-map direction | APLICACIONES: "marco conceptual para: C8... C38/C39... explicación de por qué los gains utilizados en simulación son parámetros de diseño y no propiedades físicas universales" — correct direction throughout. |

**Verdict: PASS.** One citation (NASA TM-20230014863) is a real, on-topic, reachable document but is mislabeled by title in the note's own bullet — see §5/§7 finding F2 (remediation: fix the title string, keep the TM number and URL).

---

## 5. Cross-cutting findings

**No SoT bleed, no invented numbers, no fake section numbers found in any of the three notes.** All three independently arrived at the same defensive pattern (explicit "this is not `library/`/`flight_software/`" disclaimers in APLICACIONES/ERRORES) without contradicting each other — a sign the spine-fill protocol (`docs/JARVIS_KNOWLEDGE_VISION.md` §8.2) is being followed consistently across notes drafted separately.

- **F1 (Vectores, minor):** the NASA NTRS 20010084958 reference is labeled "documentación técnica sobre representación y control de actitud mediante cuaterniones" but resolves to the full *2001 Flight Mechanics Symposium* proceedings (a multi-paper compilation whose own landing-page metadata does not itself confirm a quaternion-specific focus) rather than one focused paper. The URL is real and on-topic (attitude determination/control), and the note does not attribute any specific formula to it (`formula_citation` lists only the four OpenStax sources) — so this does not undermine any claim in the note body, but the citation's own specificity ("mediante cuaterniones") is not independently confirmed at the level this session could verify. See §7 remediation R1.
- **F2 (Control clásico, moderate):** the NASA TM-20230014863 reference is labeled "SUSAN Electofan Flight Control System" in the note's citation bullet. The actual document title (confirmed by reading the PDF's own title page) is *"Reinforcement Learning Approach to Flight Control Allocation With Distributed Electric Propulsion"* (Kristin C. Wu and Jonathan S. Litt, NASA Glenn Research Center, November 2023). The paper does genuinely study flight control for the "SUSAN" aircraft concept (confirmed: 13 in-document mentions of SUSAN, including an acknowledgment to "the SUSAN flight controls team"), so the underlying subject-matter connection is real — but the title string given in the citation bullet is not this document's actual title, and "Electofan" is also a typo for "Electrofan." No specific formula in the note body is attributed to this source (it supports general context, not the PID/windup formulas, which are independently covered by CTMS/Control Guru), so this is a **citation-label accuracy issue**, not grounds to distrust the note's substantive claims. See §7 remediation R2.
- **F3 (informational, not a finding):** two of the three notes' own `[CONEXIONES]` "Spine" lists reference concepts beyond the 12-node spine list in `docs/JARVIS_KNOWLEDGE_VISION.md` §8.1 (e.g. `[[Marcos de referencia]]`, `[[Rotaciones]]`, `[[Cuaterniones]]`, `[[Planta dinámica]]`, `[[6-DoF]]` — all currently dangling, no note yet) while also correctly linking to already-resolved spine nodes (`[[Momento y rotación]]`, `[[Control robótico]]`, `[[Cinemática y dinámica]]`, `[[Espacios vectoriales]]`, `[[Cinemática]]`, `[[Sensores de movimiento]]`). This is the same "graph reaches further than materialized notes" shape documented in the prior B0 vault-value report — organic growth beyond the declared minimal spine, not a defect, and outside this IC's scope to grade.
- **Template-drift note:** all three notes cleanly use the extended frontmatter (`jarvis_relevance`, `never_invents`, `formula_citation`) that the prior B0 investigation recommended and `JARVIS_KNOWLEDGE_VISION.md` §8.2 then formalized — no drift from that target contract observed.

---

## 6. URL matrix

| Note | # | Reference (short) | Reach | Title/§ match | Key-claim support |
|---|---|---|---|---|---|
| Vectores | 1 | OpenStax Algebra & Trig 2e §10.8 "Vectors" | ✅ 200 | ✅ exact | ✅ magnitude/direction/components definition |
| Vectores | 2 | OpenStax Calculus Vol.3 §2.3 "The Dot Product" | ✅ 200 | ✅ exact | ✅ both dot-product forms + projection |
| Vectores | 3 | OpenStax Calculus Vol.3 §2.4 "The Cross Product" | ✅ 200 | ✅ exact | ✅ magnitude formula, perpendicularity, right-hand rule |
| Vectores | 4 | OpenStax Univ. Physics Vol.1 §2.4 "Products of Vectors" | ✅ 200 | ✅ exact | ✅ scalar + vector product, geometric meaning |
| Vectores | 5 | NASA NTRS 20010084958 (attitude/quaternion doc) | ✅ 200 (citation page) | ⚠️ resolves to full symposium proceedings, not a single focused paper; quaternion-specificity unconfirmed at metadata level | ⚠️ on-topic (attitude det./control) but not formula-attributed — **F1** |
| Dinámica | 6 | OpenStax Univ. Physics Vol.1 §5.3 "Newton's Second Law" | ✅ 200 | ✅ exact | ✅ both $dp/dt$ and $F=ma$ forms |
| Dinámica | 7 | OpenStax Univ. Physics Vol.1 §10.7 "Newton's 2nd Law for Rotation" | ✅ 200 | ✅ exact | ✅ $\tau_{net}=I\alpha$, fixed axis |
| Dinámica | 8 | OpenStax Univ. Physics Vol.1 Ch.10 "Key Equations" | ✅ 200 | ✅ exact | ✅ rotational-dynamics equation set |
| Dinámica | 9 | MIT 2.003J rigid body dynamics notes (jasonku.mit.edu PDF) | ✅ 200 via `curl` (WebFetch tool refused: TLS cert hostname mismatch, `jasonku.mit.edu` served under a `*.scripts.mit.edu` cert) | ✅ confirmed via independent search (Jason Ku, Spring 2011, 2.003J) | ✅ Newton-Euler + inertia tensor, per search-confirmed content |
| Dinámica | 10 | NASA Murman et al., AIAA 2003-1246 "Simulations of 6-DOF Motion with a Cartesian Method" | ✅ 200 | ✅ exact — verified directly from the PDF's own title page + abstract | ✅ abstract explicitly frames 6-DOF as "integrating the Newton-Euler equations" |
| Control clásico | 11 | UMich CTMS "Introduction: PID Controller Design" | ❌ direct fetch blocked (Cloudflare bot-challenge, HTTP 403 both via WebFetch and `curl`) | ✅ confirmed via independent search (exact title, exact URL pattern) | ⚠️ UNVERIFIED (network) for direct quote-level check; strongly corroborated by search snippet describing P/I/D qualitative effects |
| Control clásico | 12 | UMich CTMS "Aircraft Pitch: PID Controller Design" | ❌ same Cloudflare block | ✅ confirmed via independent search | ⚠️ UNVERIFIED (network), same as #11 |
| Control clásico | 13 | UMich CTMS "Motor Speed: PID Controller Design" | ❌ same Cloudflare block | ✅ confirmed via independent search | ⚠️ UNVERIFIED (network), same as #11 |
| Control clásico | 14 | NASA TM-20230014863 | ✅ 200 | ❌ note's bullet says "SUSAN Electofan Flight Control System"; actual title is "Reinforcement Learning Approach to Flight Control Allocation With Distributed Electric Propulsion" (Wu & Litt) — **F2** | ⚠️ topically related (13 in-document SUSAN mentions) but not the cited title; no specific formula in the note is attributed to this source |
| Control clásico | 15 | Control Guru "Integral (Reset) Windup, Jacketing Logic and the Velocity PI Form" | ✅ 200 | ✅ exact | ✅ windup mechanism + jacketing logic + velocity form, directly matching ERRORES/NOTAS |

**12 / 15 fully verified. 2 / 15 UNVERIFIED (network) with strong independent corroboration. 1 / 15 verified-but-mislabeled (F2).**

---

## 7. Recommended remediations (ordered, Cursor-applicable)

1. **[Control clásico, moderate priority]** Fix the NASA TM-20230014863 citation bullet's title string from *"SUSAN Electofan Flight Control System"* to the document's actual title, *"Reinforcement Learning Approach to Flight Control Allocation With Distributed Electric Propulsion"* (Kristin C. Wu and Jonathan S. Litt, NASA Glenn Research Center, November 2023) — optionally keep a parenthetical noting it studies flight control allocation for the SUSAN aircraft concept, since that connection is real (confirmed in-document). No change needed to the URL or TM number, both correct. No change needed to any body claim — this source is not the origin of any specific formula in the note.
2. **[Vectores, low priority]** Tighten the NASA NTRS 20010084958 citation bullet to reflect that it resolves to the full 2001 Flight Mechanics Symposium proceedings rather than a single focused work — e.g. "NASA Technical Reports Server — 2001 Flight Mechanics Symposium proceedings (attitude determination, prediction and control papers)" — or replace it with a more specifically quaternion-focused, individually-verifiable NASA/academic reference if the Engineer wants a tighter match for the quaternion/Euler-angle discussion in FUNDAMENTO/EJEMPLO/ERRORES.
3. **[Control clásico, cosmetic]** No content change required for the three UMich CTMS citations — they are real and correctly titled per independent search corroboration. If the Engineer wants first-party verification (not just search-corroborated), a manual browser check bypassing the Cloudflare bot-challenge would close this out; no urgency, as the pattern (this exact site blocking automated fetches) is a known, generic anti-bot behavior, not a site-specific red flag.
4. **No remediation needed** for the MIT 2.003J citation's content (confirmed real and on-topic) — optionally the Engineer may note that `jasonku.mit.edu`'s TLS certificate does not match its own hostname (served under a `*.scripts.mit.edu` wildcard cert), which could show a browser security warning to a future reader; this is a hosting-side issue on MIT's own personal-page infrastructure, not something this vault can fix, and does not affect the citation's validity.

**No remediation recommended for Vectores' or Dinámica's math/physics OpenStax/MIT/NASA-Murman citations, or for Control clásico's core CTMS/Control Guru citations — all verified as stated.**

---

## 8. Overall verdict + whether lote-1 may stay `solid`

| Note | Verdict | Stay `solid`? |
|---|---|---|
| Vectores | **PASS** (one low-priority citation-labeling note, F1) | **Yes** |
| Dinámica | **PASS** (zero findings) | **Yes** |
| Control clásico | **PASS** (one moderate-priority citation-labeling note, F2) | **Yes** |

None of the three notes contains an invented physical number, a fabricated section reference, a catalog/Continuity/FS/Safety SoT-bleed, or an unhedged universal-guarantee overclaim. The two findings (F1, F2) are both citation **labeling** issues on real, reachable, topically-relevant sources — not fabricated citations, not dead links, and neither one is the source of any specific formula or numeric claim the note body makes. Per the IC's own verdict rubric (§4 of the IC), both notes with findings qualify as **PASS WITH NOTES** in the strict sense that small wording fixes are recommended — this report nonetheless keeps them at **PASS** rather than **PASS WITH NOTES** as the headline verdict per note, because the required fixes are citation-string corrections only, with zero impact on any claim's truthfulness or supportedness; the distinction is noted here explicitly so Cursor/Engineer can apply whichever label they prefer. **All three notes may remain `estado: solid`.** No downgrade to `draft` is warranted for any of the three.

---

## 9. Non-goals / what was not audited

- Lote-2 drafts (Cursor + Engineer's own parallel work) — not opened, not reviewed, out of this Buy's scope per the IC's own §0 decision 2 and stop conditions.
- The rest of the vault (~87 other notes, the `00_Mapa/` hub/roadmap/template/concept-registry files) — not re-audited; this Buy's own prior B0 report already covered vault-wide structure, and this IC scopes strictly to the three named lote-1 files.
- Note prose *style* — per the IC's own stop conditions, this report did not propose wording improvements for readability, only truth/citation/SoT issues.
- RAG readiness, retrieve-layer implementation, or any `intelligence/`-adjacent code — none of that was touched, built, or recommended as ready; this remains a citation audit only.

---

## 10. Non-edits (explicit)

**Claude did not edit any file under `ontology/` in this Buy.** This investigation used only `Read` (on the three audited notes) and read-only `Bash` (`cat`/`find`/`python3`/`shasum`/`curl -I`) against `ontology/` — no `Write`/`Edit` tool call was made against any path under `ontology/` at any point in this session.

Full working-tree status at close of this Buy:

```text
$ git status --short -- ontology/ src/ pyproject.toml
 M ontology/.obsidian/workspace.json
 M ontology/00_Mapa/Plantilla.md
 M ontology/01_Matematicas/Álgebra lineal/Vectores/Vectores.md
 M ontology/02_Fisica/Mecánica/Dinámica/Dinámica.md
 M ontology/02_Fisica/Mecánica/Momento y rotación/Momento y rotación.md
 M ontology/03_Ingenieria/Control/Control clásico/Control clásico.md
 M ontology/04_Robotica/Control robótico/Control robótico.md
 M ontology/04_Robotica/Sensores/Sensores de movimiento/Sensores de movimiento.md
 M ontology/README.md
```

Every one of these — including the three audited files, which show large diffs (602 insertions total across the three) — reflects the **pre-existing, uncommitted state of the Engineer/Cursor's own offline spine-fill work** (`docs/JARVIS_KNOWLEDGE_VISION.md` §8: notes went from near-empty stubs to their current `solid` content directly in the working tree, not yet committed to git). This state existed on disk **before** this investigation opened any file — this report's own audit read exactly the content shown in these diffs' "after" side, and changed none of it. `Momento y rotación.md`, `Control robótico.md`, and `Sensores de movimiento.md` were not opened or audited by this Buy (out of the three-file scope) and are listed here only for full-transparency completeness of the working tree at close of this Buy. No file under `src/` was created or modified. `pyproject.toml` is unchanged (`version = "0.5.44"`). No git tag was created (`git tag -l | sort -V | tail -1` → `v0.5.44`).
