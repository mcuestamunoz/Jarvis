# Investigation Report — Structure Catalog Foundation (Frames)

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_structure_catalog_foundation.md](investigation_contract_structure_catalog_foundation.md)
**Checkpoint:** tag `v0.3.6`; live tree includes claim hygiene + control parity + Structure Foundations claim-copy (suite 2171, preserved, not reverted)
**Status:** OPEN — for Engineer ★ on model / Buy

Not an Implementation Contract. No `src/` edits, no `CatalogRef` extension, no
`library/frames/` were authored. No SKU was invented — the few named example
models in §6/§8 are named only as *the kind of* identity a future seed would
need to source and verify, not as data this report asserts as fact.

---

## 1. Executive finding

**Not yet — for bind or assist. A small, honest case exists for schema+seed
only (IC-1-equivalent), but I cannot prove enough incremental
engineering-decision value to recommend IC-2 (bind+BOM) or IC-3 (assist) now.**

The decisive fact (traced in §5): `component_writers.set_frame_material`
already writes any declared mass into `current_parameters
["structure_mass_override_kg"]`, and `CalculationEngine.build`
(`calculation_engine.py:196-207`) already consumes that override
**unconditionally**, regardless of whether the mass came from free text or
would come from a catalog SKU. This is different from motor/battery, where
binding **changes what calc does** (2A: motor mass only counts when
SKU-bound; 4A: battery mass uses the SKU's real value instead of a 150 Wh/kg
heuristic — `PHYSICAL_COMPONENT_CATALOG_V1.md:65,67`). For frame, a catalog
SKU's mass number would land in the exact same variable, computed the exact
same way, as a free-text "0.45kg" today. **Binding a frame SKU would not
unlock a single new engineering claim beyond what Structure A already
permits** (LEVEL A class screening, §5) — it would only make the *inputs* to
that same screening traceable to a named, sourced product instead of a
free-text guess.

That is real value (§2's Q11 answer below is not "just a prettier name") but
it is an **identity/traceability/error-reduction** value, not a new
capability — and the codebase already has a live precedent for shipping
exactly that much, safely, with zero forced consumer: the **ESC catalog**.
`library/esc/_datos.json` is a real, provenance-carrying catalog
(`manufacturer`, `model`, `part_number`, `source_url`, `source_note`,
`identity_status`), `CatalogRef.family` already accepts `"esc"`
(`schemas/action_schema.py:139`), and `catalog_bind.bind_esc_from_catalog`
(`catalog_bind.py:177-215`) is a complete, tested projector function — **yet
it has exactly one caller, a test** (`tests/test_catalog_foundation_v1.py:349`).
No orchestrator command, no CLI flow, no assist module ever calls it. This
has shipped, been reviewed, and caused zero regressions for months. It is
direct proof that "schema + seed + zero reachability" is a safe, already-accepted
shape in this codebase — which is exactly IC-1's proposed scope for frames.

**Recommendation: IC-1-equivalent only (schema + seed), if Engineer wants to
bank the groundwork now; otherwise B0 (no code, revisit later) is equally
defensible.** IC-2/IC-3 are named with their real costs in §6 so Engineer can
choose either path with eyes open — this report does not consider the
narrower gain proven yet.

---

## 2. Field authority table

| Candidate | Bucket | Why |
|---|---|---|
| `manufacturer` | Identity | Names the product; no claim by itself. Precedent: `EscSpec.manufacturer` (`library.py:142` area), free string, never branched on. |
| `model` | Identity | Same as above; precedent: `MotorSpec`/`EscSpec` `model` fields. |
| `catalog_ref` | Provenance/Identity | The `{family, sku}` pointer itself (`CatalogRef`, `action_schema.py:130-140`) — requires `family: Literal[...]` to include `"frame"`, which does **not exist today** and is explicitly not to be added in this investigation. |
| `mass_kg`/`mass_g` | Physical | Already a Structure A field (`_frame_completeness`, `domains/aerial.py:262-281`). A catalog value would be the **same field**, sourced differently — see §4. |
| `size_class_inch` | Physical (LEVEL A only) | Already a Structure A field, already load-bearing for `frame_class_compatibility_state` (`project_closure.py:162-195`). A catalog value would feed the exact same screening — never a new rule. |
| `material` | Physical | Already a Structure A field; feeds only the density-based mass-mutation heuristic (`mutation_engine.py:240-286`), never a strength/fit claim. |
| `configuration` | Declarative | (e.g. "quad-X", "hex") — no consumer anywhere today (confirmed: zero hits for a frame-configuration concept in `src/jarvis`). Naming it does not close any claim. |
| `arm_count` | Declarative | No consumer. Distinct from `motor_count` (`current_parameters`), which already exists and already drives BOM/`per_motor_max_thrust_n` math — a frame-level `arm_count` would be a **second, potentially-diverging** count of the same physical fact unless explicitly reconciled with `motor_count`. Not proven necessary; flagged as a real hazard if ever introduced. |
| `wheelbase` | **Not yet** | Locked stance §8 names this explicitly: a manufacturer publishing `wheelbase` does not license any clearance/interference claim. No consumer exists, and Structure A's own LEVEL A discipline (class vs propeller diameter only, never geometry) gives no honest use for it today. Recording it inertly (never consumed) is the *only* safe treatment if it is ever added — same treatment as `configuration`/`arm_count`. |

No field above is classified **Claim-closing** on its own merit beyond what
Structure A's `size_class_inch` already closes (§3). Identity fields
(`manufacturer`, `model`, `catalog_ref`) never close a claim by themselves —
they only make an already-closable claim (LEVEL A class compatibility)
traceable to a named source instead of a free-text declaration.

---

## 3. Claim unlock / non-unlock matrix

| Chain | Claim | Status |
|---|---|---|
| IDENTITY (`catalog_ref={family:"frame", sku:"X"}`) → KNOWN PROPERTY (`size_class_inch` from SKU, `identity_status:"verified"` + `source_url` present) → CLAIM SUPPORTED | *"Este frame declara clase N pulgadas (fuente: catálogo, [manufacturer] [model])."* — the **same** LEVEL A sentence Structure A already emits for a free-text declaration, just with a named source instead of "declared." | **Would be unlocked by IC-1+IC-2** — this is the one honest claim upgrade catalog binding offers: same claim, better provenance. It is **not** a new claim type. |
| IDENTITY → KNOWN PROPERTY (`mass_kg` from SKU) → CLAIM SUPPORTED | *"Este frame declara Y kg (fuente: catálogo)."* | Same as above — provenance upgrade only; **numerically identical effect on calc** as free text (§1, §5). |
| IDENTITY → mass/material/class known → **"El diseño estructural es correcto."** | Forbidden | **Never unlocked.** No structural analysis exists or is proposed. |
| IDENTITY → **"Los motores caben."** / **"La hélice tiene clearance."** | Forbidden | **Never unlocked.** No geometry, no arm length, no motor-mount position is modeled. Catalog identity says nothing about physical layout beyond the single declared `size_class_inch` number Structure A already screens. |
| IDENTITY → **"El frame soportará el empuje."** | Forbidden | **Never unlocked.** No load/strength data field is proposed (`_MEASURABLE` and the candidate list above contain no stress/strength field). |
| IDENTITY → **"El sistema está listo para ensamblar."** | Forbidden | **Never unlocked.** `catalog_bound` does not enter `_derive_subsystem_verdict`'s PASS conjunction today (confirmed: `_structure_evidence`, `engineering_readiness.py:1043-1050`, computes `catalog_bound` but `_derive_subsystem_verdict`, `:1141-1196`, never reads it) and this investigation does not propose changing that. |
| `catalog_bound=True` (any family) → **anything about Structure/system readiness** | Forbidden | Confirmed structurally impossible today — `_derive_overall` (`:1199-1211`) reads only `gaps` and subsystem `verdict`, never `catalog_bound`, for any of the nine subsystems. |

---

## 4. Q12 — evidence bar (catalog-declared vs authoritative)

The codebase already has a **live, working evidence-bar convention** — reuse
it rather than invent a new one:

| Provenance field | Precedent | Meaning |
|---|---|---|
| `source_url` | `MotorSpec`/`BatterySpec`/`PropellerSpec`/`EscSpec` (`library.py:63,117,142,164`) | Link to a manufacturer page/datasheet. Optional; absence is honest, not an error. |
| `source_note` | Same four specs (`library.py:65-66,120-121,143-144`) | Free-text human note, e.g. the ESC seed's *"HOBBYWING official: 40A continuous / 60A peak..."* (`library/esc/_datos.json`). |
| `identity_status` | Same four specs | Free string today (e.g. `"verified"` on the one ESC seed row) — **never machine-branched on anywhere in `src/jarvis`** (confirmed by full-repo grep). It is documentary metadata for human/audit trust, not an enforced gate. |

**Q12 answer:** a frame catalog field becomes *authoritative* (safe to feed
into the same LEVEL A screening Structure A already runs) exactly when it
carries a `source_url` pointing to a manufacturer spec page or datasheet, or
a `source_note` describing where the seed author read it — the same bar the
existing four families already (inconsistently, but non-fabricated) apply.
A field with no such note is still usable (same as any free-text
declaration is usable today), but is **catalog-declared, not
manufacturer-verified** — no stronger a claim than a user typing the same
number. This bar does not require new schema machinery: it is the existing
`source_url`/`source_note`/`identity_status` triple, unused for a fifth
family.

---

## 5. Interaction with Structure A + `catalog_bound` honesty

**Structure A composition (not replacement):** a hypothetical frame
`catalog_ref` would project `mass_kg`, `material`, and/or `size_class_inch`
into the **same** `ComponentSpec.properties` dict Structure A's
`set_frame_material` already writes to (`component_writers.py:71-102`).
`_frame_completeness` (`domains/aerial.py:262-281`) and
`frame_class_compatibility_state` (`project_closure.py:162-195`) are pure
functions over that dict — they would not need to know or care whether the
values came from free text or a catalog projection. **This is confirmed,
not assumed:** `CalculationEngine.build` already treats
`structure_mass_override_kg` as source-agnostic (§1) — there is no
"free-text mass is second-class" asymmetry to fix for frame, unlike motor/
battery.

**`catalog_bound` reachability — described, not fixed (per this contract's
explicit instruction):**

- `_structure_evidence` already computes `catalog_bound =
  _catalog_ref_set(ctx.project_state, "frame")` (`engineering_readiness.py:1049`).
  This line has been **structurally unreachable since it was written** —
  `CatalogRef.family` (`action_schema.py:139`) has never included `"frame"`,
  so no `ComponentSpec` for a frame can ever carry a non-`None` `catalog_ref`
  today. This is a stronger form of "unreachable" than ESC's: ESC's
  `catalog_bound` is reachable **in principle** (schema allows it, a bind
  function exists) but unreached **in practice** (no caller). Frame's is
  unreachable **in principle** (schema forbids it) until a Literal change —
  which this investigation is explicitly told not to make.
- `_bom_sku_resolved` (`project_closure.py:472-511`) would also need a new
  branch — its own docstring says *"no v1 resolve path for other families"*
  (`:511`) for anything outside `{motor, battery, propeller, esc}`.
- `_derive_subsystem_verdict`/`_derive_overall` never read `catalog_bound`
  for any family (confirmed §3) — extending the family list would not, by
  itself, touch `ASSEMBLY_READY` eligibility. That stays true regardless of
  which IC (if any) Engineer authorizes later.

**Divergence-clearing precedent and its real cost:** `invalidate_diverged_
catalog_refs` (`catalog_bind.py:234-309`) only handles `motor` and
`battery` divergence today — **not propeller, not ESC**. A frame bind
(IC-2) would need its own divergence branch (clear `catalog_ref` if a later
free-text mass/material/class declaration diverges from the bound SKU's
projected values) to avoid the exact "frankenstein" hazard (a stale SKU
label next to numbers that no longer match it) this function exists to
prevent for motor/battery. This is a genuine, non-trivial design cost for
IC-2 — not automatic, not free, and not yet even fully solved for two of
the four already-shipped families.

---

## 6. Recommended phased scope

| Phase | Scope | Cost | Proven necessary now? |
|---|---|---|---|
| **IC-1 — Schema + seed** | Add `"frame"` to `CatalogRef.family`; new `library/frames/_datos.json` (a handful of real, named, sourced frame models — `manufacturer`/`model`/`mass_kg`/`material`/`size_class_inch`/`source_url`/`source_note`/`identity_status`, mirroring the ESC seed shape exactly); `ComponentLibrary.get_frame`/`has_frame`/`find_frames_for_*` reader methods, mirroring `get_esc`/`has_esc`. **No writer, no bind, no BOM/Continuity change, no consumer.** | Low — proven low by the ESC precedent (shipped, tested, zero regressions, zero consumer, months old). | **Optional groundwork, not required.** Safe to do or safe to skip; no lie exists today that IC-1 would fix. |
| **IC-2 — Bind + BOM identity** | `bind_frame_from_catalog` (mirroring `bind_esc_from_catalog`); extend `invalidate_diverged_catalog_refs` with a frame branch (mass **and** `size_class_inch` divergence — two fields, unlike motor/battery's one); extend `_bom_sku_resolved` with a `"frame"` branch; BOM `_bom_identity_suffix` already generic (no change needed there). | Medium — real new code paths, real new tests, a genuinely two-dimensional divergence check (mass + class) that has no precedent (existing divergence checks are single-field). | **Not proven.** §1's calc-parity finding means this phase buys traceability/error-reduction only — I found no engineering decision that becomes more *possible* (only more *traceable*) with it. |
| **IC-3 — Assist (`ayúdame a elegir` for frame)** | New acquisition CTA, `acquisition_brief.py` catalog-CTA list extension, numbered-list UX mirroring motor/battery/propeller. | Medium-high — full UX surface, matching the richest existing family flows. | **Not proven**, and depends on IC-2 first per the design's own dependency order (bind before assist, `PHYSICAL_COMPONENT_CATALOG_V1.md:196` — "Impl C forbidden until B stable," same discipline applies here). |

**IC-1 alone is not "possibly enough for Fase 1" in the sense of being a
capability jump — it is enough in the sense of being a safe, zero-risk,
zero-claim-impact way to bank sourced identity data for later, exactly
mirroring what the codebase already did for ESC.** If Engineer's goal is
"have real frame SKUs ready to bind whenever a later thread proves the
bind is worth it," IC-1 is the right minimum. If Engineer's goal is a new
user-facing capability now, none of the three phases currently clear that
bar — B0 (no code) is the honest answer.

---

## 7. Explicit out

- CAD, FEA, STL/STEP generation, generative geometry — not evaluated, not
  proposed, no field in the candidate list implies them.
- `wheelbase`, `arm_count`, `configuration` as claim-closing fields — all
  classified **Not yet**/**Declarative** in §2; none are proposed as part of
  IC-1's seed schema.
- Layout params as a Buy — the prior Structure Foundations investigation
  already rejected this on its own merits (weak fit, no consumer, risks the
  forbidden tip-clearance line); this investigation does not revisit that.
- Reopening BOM/Continuity claim-copy wording — closed by the prior slice;
  this report found no seam that *forces* a reopen (§5's `catalog_bound`
  reachability gap is described, not fixed, per this contract's explicit
  instruction).
- Extending `CatalogRef.family` — described as the blocking schema fact
  (§5), not implemented here.
- Wiring `catalog_bound` into any subsystem verdict or `ASSEMBLY_READY` —
  confirmed unnecessary and unproposed (§3, §5).
- Inventing SKU data — the example model names in §1/§8 are named only as
  *categories of real product* a future seed author would need to verify
  against a manufacturer source, never as data this report asserts as fact.

---

## 8. Risks / open questions for Engineer ★

1. **Is "identity/traceability, not new capability" a strong enough reason
   to spend IC-1's (low but nonzero) cost now, or should frame stay
   deferred until a concrete downstream need appears** (e.g., a future
   "generate a shopping list" feature that would want real SKUs across all
   families, frame included)? This report takes no position — it is a
   product-priority call, not an engineering one.
2. **`arm_count` vs `motor_count` divergence hazard** (§2): if a future
   thread ever wants an `arm_count` field, it must be explicitly reconciled
   with the existing `current_parameters["motor_count"]` or left
   permanently un-consumed — this report does not resolve which.
3. **Divergence-clearing is already inconsistent** across shipped families
   (motor + battery covered; propeller + ESC not). A frame IC-2 would add a
   *third* uncovered-or-covered family to that inconsistency depending on
   whether Engineer wants it done right the first time or matched to the
   current (imperfect) baseline. Flagged, not decided, here.
4. **Seed sourcing effort**: IC-1's "few real SKUs" (Q8) requires someone
   to actually locate and verify manufacturer specs (mass, material,
   declared size class) for each seed row — the same manual-curation cost
   every prior seed (`motores`, `baterias`, `helices`, `esc`) already paid.
   Not a code risk, but a real time cost worth naming before Engineer ★.

---

## 9. Thin non-binding outline (only if Engineer ★ authorizes IC-1)

- **Files (illustrative, not authoritative):** `src/jarvis/schemas/
  action_schema.py` (`CatalogRef.family` Literal +`"frame"`);
  `src/jarvis/knowledge/library.py` (`FrameSpec` dataclass + `get_frame`/
  `has_frame`/loader, mirroring `EscSpec`); new `library/frames/_datos.json`
  (a handful of seeded, sourced rows).
- **Explicitly not touched even in IC-1:** `component_writers.py`,
  `catalog_bind.py`, `project_closure.py`, `engineering_readiness.py`,
  `project_continuity.py`, any CLI/BOM rendering, any test beyond loader
  unit tests for the new `FrameSpec`/`get_frame`/`has_frame` API.
- **Tests:** loader round-trip (JSON → `FrameSpec`), `has_frame`/`get_frame`
  happy-path + honest-miss, mirroring existing `test_catalog_foundation_v1.py`
  patterns for the other four families.
- Any IC-2/IC-3 scope stays a **separate, later, Engineer-named** thread —
  not implied or pre-authorized by this outline.
