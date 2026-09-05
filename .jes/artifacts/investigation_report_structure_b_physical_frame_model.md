# Investigation Report — Structure B Physical Frame Model

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_structure_b_physical_frame_model.md](investigation_contract_structure_b_physical_frame_model.md)
**Parents consumed:** [investigation_report_structure_a_pass_meaning.md](investigation_report_structure_a_pass_meaning.md) (§2–§5, per contract §4); Catalog Foundation IC-1→IC-3
**Checkpoint:** tag `v0.3.6`; live tree includes claim hygiene, control parity, Structure Foundations claim-copy, Catalog Foundation, Structure A PASS-meaning investigation (suite 2197, preserved)
**Status:** OPEN — for Engineer ★ on model + sequencing

Not an Implementation Contract. No `src/` edits, no schema changes, no seed edits. This is a model/vocabulary design question — the report proposes field shapes and claim sentences; it does not write code.

---

## 1. Executive finding

**Frame stays one `ComponentSpec` — there is no assembly/parts ontology
anywhere in this codebase to extend, and inventing one would be a bigger
change than "minimum model" allows.** `ComponentSpec.properties` is a flat
`dict[str, PropertyValue]` (`action_schema.py:143-163`); no component
anywhere — not motors (`motor_count` is a scalar, not N motor records), not
propellers, not battery — is ever represented as a parent record with
nested child records. The correct, precedent-consistent Fase 1 model is
**more scalar properties on the same frame spec**, not a "frame → arms →
plates" object graph: `configuration` (closed vocabulary, declared-only),
`arm_count` (declared-only, explicitly *not* reconciled with `motor_count`),
and `wheelbase_mm` (declared-only, numeric). Mass stays declared-on-the-
assembly (today's rule) — sum-of-parts is not attempted, because there are
no parts to sum.

None of these fields touch `_frame_completeness`, `classify_component`, or
any evidence bit `_structure_evidence` reads — Structure A PASS's meaning
(prior report §2) is unchanged by definition, satisfying locked stance #2.

**Buy: (b) — ship the already-fully-specified Structure honesty IC first
(from the PASS-meaning investigation), then a separate, later model IC** for
these three fields. They are two different kinds of decision (claim-copy
wording vs. new declared vocabulary) and bundling them would blur which
change fixed which problem — inconsistent with how every prior slice this
phase shipped (one concern per IC).

---

## 2. KNOW / CLAIM / MEASURE matrix

| Field | KNOW (can Jarvis record it?) | CLAIM (what may it say?) | MEASURE (excluded) |
|---|---|---|---|
| `mass_kg` (existing) | Yes — declared or catalog-sourced | "Este frame declara N kg" | Whether that mass is accurate, whether it holds the declared load |
| `material` (existing) | Yes | "Material declarado: X" | Whether the material is structurally adequate |
| `size_class_inch` (existing) | Yes | LEVEL A class-vs-propeller-diameter sentence (locked, Structure A) | Geometric interference/clearance |
| `configuration` (new) | Yes, from a **closed vocabulary** matched against declared text (never inferred from `motor_count`) | "Configuración declarada: quad-X" | Whether that configuration is aerodynamically/structurally valid, whether it matches the *actual* motor layout |
| `arm_count` (new) | Yes, declared only | "Brazos declarados: N" | Whether N is consistent with `motor_count`, whether the arms physically exist/are sized correctly |
| `wheelbase_mm` (new) | Yes, declared only (user text or catalog SKU, per §3 wheelbase already sourced for all 4 IC-1 seed rows — see §6) | "Wheelbase declarado: N mm" | Motor/propeller clearance, mounting fit, frame rigidity at that span |
| `plates`/`standoffs`/`hardware` (Engineer's SÍ draft) | Possible in principle (same scalar-property pattern) | Identity/count only | Any structural adequacy claim |
| Manufacturer/SKU identity (existing, Catalog Foundation) | Yes | "Fuente: catálogo, {manufacturer} {model}" | That the named product is correctly represented beyond the fields actually seeded |

**Universal read across every row:** KNOW and CLAIM stay at "a number/label
was declared, from this source" — never "...and therefore X is true about
the physical assembly." MEASURE is the same wall the prior report drew
around Structure A; this investigation does not move it, only adds more
KNOW/CLAIM fields inside it.

---

## 3. Ontology decision table

| Question | Decision | Why |
|---|---|---|
| Is an arm a separate `ComponentSpec`? | **No.** | No nesting mechanism exists in `ComponentSpec` (`properties: dict[str, PropertyValue]`, flat, scalar-valued only). Motors — the closest precedent for "many identical physical instances" — are already a single spec + a `motor_count` scalar, not N motor records. Frame should follow the same convention: one spec, `arm_count` as a scalar property. |
| Is frame mass declared-on-assembly, sum-of-parts, or either? | **Declared-on-assembly only (today's rule, unchanged).** | Sum-of-parts requires parts with their own mass, which requires the nesting this table just rejected. Not attempted in Fase 1. |
| What's universal vs. type-dependent (quad-X vs. hex vs. deadcat)? | `mass_kg`/`material`/`size_class_inch`/`wheelbase_mm` are universal (every frame has *a* mass, material, class, span). `configuration` **is** the type-dependent field — arm count and geometry differ by type, which is exactly why `configuration` should be a first-class field rather than trying to derive type from `arm_count` or `motor_count`. |
| What does "tipo"/`configuration` mean as a field? | **Closed vocabulary, matched from declared text** — mirror the existing `FLIGHT_CONTROLLER_MAP`/`GPS_MAP` alias-table pattern (`domains/aerial.py`): a small canonical set (`quad_x`, `quad_plus`, `hex`, `deadcat`, `tricopter`, …) matched from user text, never invented, absent when unrecognized (same discipline as material/GPS aliasing). **Never** derived from `motor_count` — `motor_count=4` is compatible with quad-X, quad-plus, *and* a narrow deadcat; deriving one from the other would be exactly the kind of invented fact §1 forbids. |
| Manufacturer vs. user-declared vs. Jarvis-inferred/unknown — when is each state used? | **Reuse the existing three-state `PropertyValue.source` vocabulary** (`action_schema.py:127`: `"declared" \| "inferred" \| "calculated"`) — no new vocabulary needed. All four new fields are `source="declared"` only (free text or catalog projection); none should ever be `"inferred"` or `"calculated"` in Fase 1 (there is no formula that derives wheelbase/arm_count/configuration from anything else Jarvis knows). Absence of the key = unknown; there is no separate "estimated" state and none is needed. |
| Catalog Foundation interaction — extend `FrameSpec` seed schema, or project-state-only? | **Read-only discussion, not decided here** (per deliverable §6/contract §3.A.8) — see §6 below. |

---

## 4. Allowed vs. forbidden claim sentences (declared geometry)

**Allowed (KNOW/CLAIM, identity/count/declaration only):**

```text
"Configuración declarada: quad-X."
"Brazos declarados: 4 (declarado, no verificado contra motor_count)."
"Wheelbase declarado: 250 mm (fuente: catálogo, TBS Source One V5)."
"Wheelbase declarado: 250 mm (declarado por el usuario)."
"Frame: identidad {manufacturer} {model}, clase {N}\", masa {X} g,
 wheelbase declarado {Y} mm — ninguno de estos valores implica
 compatibilidad de montaje ni holgura verificada."
```

**Forbidden (MEASURE, fit/adequacy/proof):**

```text
"El wheelbase permite montar los motores sin interferencia."      # clearance
"Los brazos soportan el empuje declarado."                         # strength
"La configuración quad-X es compatible con la hélice elegida."     # invented cross-check
"4 brazos para 4 motores — configuración correcta."                # arm_count↔motor_count claim
"El chasis está verificado para ensamblaje."                       # fabricability/assembly proof
"Wheelbase suficiente para las hélices declaradas."                # clearance, phrased as sufficiency
```

The forbidden list is not hypothetical phrasing — each line names exactly
the ✗ bullets already locked in the prior investigation's §3 table (motors
fit, clearance, strength, fabricability), now restated for the three new
fields so a future IC cannot reintroduce them through a different word
choice ("suficiente," "correcta," "sin interferencia" are all synonyms for
the same forbidden claim).

---

## 5. Composition with Structure A PASS (no silent widen)

Confirmed, not assumed: `_structure_evidence` (`engineering_readiness.py:
1043-1050`) reads exactly `classify_component("frame")`,
`calc.total_mass_kg`, `bool(sim)`, `sim_status=="pass"` — none of the three
new fields appear in any of those four checks, and this report does not
propose adding them. `_frame_completeness` (`domains/aerial.py:262-281`)
checks only `mass_kg`/`material` — adding `configuration`/`arm_count`/
`wheelbase_mm` as further **optional** properties does not change what
counts as `"high"` completeness; a frame with mass+material but no declared
wheelbase stays exactly as "complete" as it is today. `Structure PASS`'s
meaning (prior report §3's locked ✓/✗ table) is **unchanged** by this
model — richer identity, not richer validation.

The prior report's optional `PASS *`/footnote honesty gap (its §4) is
**orthogonal** to this model: that gap exists today, with zero new fields,
because Structure's PASS is already indistinguishable from a mechanically-
verified one in the readiness block. Adding `configuration`/`arm_count`/
`wheelbase_mm` neither creates nor closes that gap — it is a separate fix
with its own IC, which is why §1 recommends sequencing them rather than
merging them.

---

## 6. Catalog seed implications (read-only discussion)

`FrameSpec` (`library.py`, Catalog Foundation IC-1) today carries `mass_g`,
`size_class_inch`, optional `material`/`manufacturer`/`model`/`part_number`/
provenance fields — no `configuration`/`arm_count`/`wheelbase_mm`.

**Sourcing note (context only, no seed file touched here):** wheelbase data
already surfaced during IC-1's own sourcing pass for all four current seed
rows' manufacturer/retailer pages (TBS Source One V5: 226 mm motor-to-motor
for the 5″ version, per the retailer page cited in that IC's report; iFlight
XL7 V4: 285 mm; Armattan Rooster: 230 mm motor-to-motor, from the
manufacturer's own page) — meaning a future seed-enrichment IC would not be
starting from zero evidence. This is **not** a recommendation to add it now
(explicitly out of this investigation's scope, and Catalog Foundation stays
closed as a phase per locked stance #6) — it is named so Engineer knows the
data already exists if a later IC is opened for it.

If such an IC ever ships: extending `FrameSpec` with an optional
`wheelbase_mm: float | None` field is additive and low-risk by the same
argument IC-1 already proved for `material` (optional, absent when a source
doesn't state it, never invented) — but `configuration`/`arm_count` are
**not** naturally catalog fields the same way, since a single named product
(e.g. "TBS Source One V5") is typically sold in one fixed configuration —
they would more often be *declared by the user* for a freeform frame than
*read from a catalog row*. This asymmetry (wheelbase = catalog-friendly,
configuration/arm_count = user-declaration-friendly) is worth naming for
whoever scopes that future IC.

---

## 7. Fase 1 model (minimum slice) + explicit out

**Fase 1 — three new optional, declared-only, additive properties on the
existing `frame` `ComponentSpec`:**

| Field | Type | Provenance | Consumer |
|---|---|---|---|
| `configuration` | closed vocabulary string (e.g. `quad_x`/`quad_plus`/`hex`/`deadcat`/`tricopter`) | `source="declared"` only, matched via a new alias table mirroring `FLIGHT_CONTROLLER_MAP` | None (display/identity only) |
| `arm_count` | int | `source="declared"` only | None — explicitly never cross-checked against `motor_count` |
| `wheelbase_mm` | float | `source="declared"` only | None |

**Explicit out — Fase 1:**
- Plates, standoffs, hardware, mounting-pattern fields (Engineer's SÍ draft
  names them; this report does not include them in the minimum slice —
  no proven immediate need, same "smallest option" discipline this phase
  has used throughout).
- Any consumer of these three fields (no gap type, no completeness
  requirement, no BOM/Continuity claim beyond straight display).
- Seed (`library/frames/_datos.json`) enrichment (§6 — discussion only).

**Explicit out — all of Structure B MEASURE (unchanged from prior report,
restated for this investigation's own record):**
- CAD, FEA, meshes, fabrication.
- Fit/clearance/interference inference of any kind.
- Strength/load/deflection claims.
- Deriving `configuration` or `arm_count` from `motor_count` or vice versa.
- Any sentence from §4's forbidden list, regardless of future field
  additions.

---

## 8. Open questions for Engineer ★

1. **Sequencing confirmation:** does Engineer agree the Structure honesty IC
   (`PASS *`, already fully specified in the prior report) should ship
   **before** this model, as two separate ICs? This report's Buy leans yes;
   Engineer may instead want them combined, or the model first.
2. **`configuration` vocabulary:** should the closed set be small and fixed
   (`quad_x`/`quad_plus`/`hex`/`deadcat`/`tricopter`) or does Engineer want
   a specific list locked before an IC is written? This report proposes a
   starting set mirroring the FC/material alias-table pattern, not a final
   one.
3. **Wheelbase seed enrichment** (§6): worth a later, separate IC given the
   sourcing groundwork already exists? Not decided here — named for
   Engineer's prioritization only.
4. **Plates/standoffs/hardware:** confirmed out of Fase 1 — does Engineer
   want them named as a *named future Fase 2* (not MEASURE, just "not yet
   scoped"), or dropped from the Structure B conversation entirely absent a
   concrete need?

---

## 9. Thin non-binding IC outline (Buy lean (b) — model IC, ships *after* the honesty IC)

- **Files (illustrative):** `src/jarvis/domains/aerial.py` (new
  `configuration` alias table + extractor, mirroring
  `extract_flight_controller_properties`; extend `extract_frame_properties`
  to also recognize `arm_count`/`wheelbase_mm` numeric patterns, same
  regex-extraction style already used for mass/size class); `_MEASURABLE`
  (`project_closure.py`) gains the three new keys so a declared value
  routes to the `"declared"`/`"defined"` BOM bucket instead of being
  silently dropped as non-measurable (same treatment `"model"`/`"gps_model"`
  already get).
- **Behavior change:** frame can carry three more optional display
  properties; BOM line may show them (format to be locked by the IC, not
  this report); `_frame_completeness`, `classify_component`,
  `_structure_evidence`, `Structure PASS` semantics: **unchanged**.
- **Tests:** extraction unit tests (declared text → correct
  `configuration`/`arm_count`/`wheelbase_mm`, unrecognized text → absent,
  never fabricated); a regression asserting `_frame_completeness` and ERF
  `structure` verdict are byte-identical with and without these fields
  present.
- **Forbidden:** everything in §7's "explicit out," everything in §4's
  forbidden-sentence list, any `_derive_subsystem_verdict`/`_derive_overall`
  change, any seed JSON edit (§6 stays a separate, later, explicitly-named
  IC if it happens at all).
