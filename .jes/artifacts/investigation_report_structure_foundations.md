# Investigation Report — Structure Foundations (Fase 1)

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_structure_foundations.md](investigation_contract_structure_foundations.md)
**Checkpoint:** tag `v0.3.6` / commit `f70b278`; live tree includes claim hygiene + control parity (suite 2164, preserved, not reverted)
**Status:** OPEN — for Cursor review, then Engineer `procede` on IC

Not an Implementation Contract. No `src/` edits were made. No frame catalog
JSON or schema was authored (candidate fields only, in §E/§F). Reconstructions
run in-memory against the live tree.

---

## A. Executive answer

Structure A shipped exactly what it promised: mass/material declaration and
LEVEL A class-compatibility screening (`size_class_inch` vs propeller
diameter), correctly wired into **both** architecture-progress copies and the
Gap Registry. Foundations' three pillars (explicit variables, deterministic
completeness, honest claims) are **unevenly met**: completeness/claims have a
real, reproduced gap; explicit variables (beyond mass/material/class) barely
exist and adding more without a consumer is premature.

I found and reproduced two **concrete disagreements**, both still live on
`v0.3.6` + claim hygiene + control parity:

1. **BOM vs Gap Registry:** `_frame_completeness` (mass+material only) never
   reads `size_class_inch`, so BOM shows `✓ frame: ... (high)` — the same
   "nothing more to do" glyph a fully-specified motor gets — **even while**
   `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` sits open and blocks the
   `structure` subsystem to `INCOMPLETE`.
2. **Situation vs next-step self-contradiction:** with everything else PASS
   and a live frame-class gap, Continuity's situation sentence still says
   *"Diseño validado en simulación (PASS)"* while `next_useful_step` in the
   **same** block correctly names the class problem — the identical
   "over-claim sentence next to an honest correction" pattern claim hygiene
   fixed for margin, never extended to non-margin gaps.

Neither requires new vocabulary, a catalog, or CAD. **Primary Buy: claim/
completeness-copy only** — a BOM suffix (mirroring control parity's
`flight_controller` pattern) and one additional situation-branch gate
(mirroring claim hygiene's own `margin_claim_weak` gate), both reading facts
already computed. A frame catalog and declared layout params are real,
separately-evaluable options (§E) but neither is proven necessary to stop a
current lie, and layout params risk brushing against the explicitly forbidden
tip-clearance-physics line — so neither is the primary recommendation.

---

## B. As-is map (Know)

### Vocabulary present vs absent

| Present | Authority | Absent |
|---|---|---|
| `mass_kg`, `material` (`_frame_completeness`, `domains/aerial.py:262-281`) | drives BOM/architecture presence | `wheelbase`, `arm_length`, `arm_count`, `tip_clearance`, `frame_configuration` (X/H/quad-hex layout) — zero extraction, zero schema, zero mention anywhere in `src/jarvis` |
| `size_class_inch` (Structure A, LEVEL A class only) — `extract_frame_properties`, `aerial.py:206-259`; explicitly no mm pattern (`:216-217,248-250`) | class-compatibility screening only (`frame_class_compatibility_state`) | `landing_gear` — a subsystem-map **key only** (`engineering_readiness.py:151`), never in `BLOCK_TO_COMPONENTS` (`system_architecture_catalog.py:146-166`), no domain rule — dead/unreachable today |
| Material **density** catalog (`library/materiales/_datos.json`, 8 materials, `density_kg_m3` only) via `ComponentLibrary.get_material` (`library.py:33,191,196`) | consumed by `mutation_engine.py:240-286`'s material-swap **relative** mass-impact estimate (`density_ratio × structural_fraction`) — a DSE/iterate heuristic, not a geometry-derived absolute mass | No volume/geometry input anywhere — frame mass is always **user-declared**, never `density × volume` |
| `CatalogRef` schema (`schemas/action_schema.py:139`) | motor/battery/propeller/esc identity binding | `family: Literal["motor","battery","propeller","esc"]` — **`"frame"` is not a valid value today**; a frame catalog needs a schema change, not just a JSON file |

### Completeness / "structure complete" authorities

| Authority | What it checks | `file:line` | Reads `size_class_inch`? |
|---|---|---|---|
| `_frame_completeness` (component completeness → BOM bucket) | `mass_kg` + `material` only | `domains/aerial.py:262-281` | **No** |
| `component_presence_tier` (architecture "present" bar) | `completeness != "low"` | `project_closure.py:410-425` | No (delegates to the above) |
| `_block_progress_status` × 2 copies ("structure" architecture block) | component present **AND** `frame_class_compatibility_state in {not_required, class_compatible}` | `orchestrator.py:1989-2007` (structure gate at `:2001-2007`); `engineering_readiness.py` component-branch (same gate, verified live) | **Yes** — via the one shared helper `frame_size_blocks_structure_complete` (`project_closure.py:197-215`) |
| ERF `_structure_evidence` (four evidence flags) | `defined`=classify≠missing; `calculated`=`calculations.total_mass_kg` present; `simulated`=any sim; `validated`=`sim_status=="pass"` | `engineering_readiness.py:1043-1050` | No — but `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` (`:886-955`) separately block the subsystem via the Gap Registry, verified in §Reconstruction |
| `frame_next_missing_datum`/`_question` (Continuity/CLI routing) | mass → material → class → incompatible, in that order | `project_closure.py:218-298` | Yes, correctly ordered last (mass/material first, per its own docstring rationale) |

**Where they disagree (verified live, §Reconstruction):** `_frame_completeness`/BOM is the **one** authority that never reads `size_class_inch` — both `_block_progress_status` copies and the Gap Registry already agree with each other (Structure A closed that specific "dual 4/4" risk by extracting the one shared `frame_size_blocks_structure_complete` predicate, confirmed called identically from both `orchestrator.py:2001-2007` and `engineering_readiness.py`'s copy). This is a **known, by-design** separation — Structure A's IC never proposed changing `_frame_completeness` — not an oversight, but it produces the BOM/ERF mismatch named in §A finding 1.

---

## C. Claim matrix

| Sentence / verdict | Allowed today | Over-claims? | Proposed Fase 1 meaning |
|---|---|---|---|
| BOM `✓ frame: {name} (high)` | "`mass_kg` and `material` are both declared." | **Yes**, when a `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` is open — same glyph as a fully-specified, gap-free component. | Keep the bucket (`classify_component` untouched); append a suffix when the live gap registry blocks structure via a frame-class gap, e.g. `(high — compatibilidad de clase nivel A pendiente)` (mirrors control parity's `flight_controller` suffix, `project_closure.py:713-724`) |
| Continuity situation *"Diseño validado en simulación (PASS)..."* | "PASS, no margin/quality warning, autonomy demonstrated (or not required)." (per claim hygiene's `margin_claim_weak` gate, `project_continuity.py:198-204`) | **Yes** — reproduced (§Reconstruction): fires unchanged even when a `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` is the **only** open gap and `next_useful_step` in the same block already names it. | Add one more situation-branch gate, same shape as the two already there (autonomy-undemonstrated, margin-weak): when `sim_status=="pass"` and a frame-class gap is live, use a sentence naming it (e.g. *"Comprobación de empuje: PASS. Compatibilidad de clase (nivel A) pendiente."*) instead of "Diseño validado" |
| `Arquitectura n/n — completa ✓` | "All blocks, including structure's class gate, are `complete`." | **No** — already correctly gated (verified in §Reconstruction: `0/1` when class missing/incompatible, `1/1` only when compatible or not-required). | Unchanged |
| `Structure` readiness line (`PASS`/`INCOMPLETE`) | Same shared design-table pattern as every subsystem (`validated=sim_status=="pass"`, `implementation_contract_erf1.md:195-204`) — not structure-specific. | No new over-claim beyond the uniform, already-accepted ERF-1 pattern (same one control parity's investigation named and explicitly declined to re-litigate). | Unchanged — out of this thread per locked stance §1 |
| `frame_next_missing_question` copy (mass/material/size/incompatible) | LEVEL A, "no verificada," never "cabe"/"no cabe" | No — already honest and correctly ordered (`project_closure.py:258-298`). | Unchanged |

---

## D. Structure A residuals

| Residual | Blocking for Foundations? | Why |
|---|---|---|
| BOM `(high)` vs live frame-class gap (§C row 1) | **Non-blocking, but real** — a fixable claim-copy gap Foundations should close as its minimum jump (see §F). | Doesn't prevent building on Structure A; it's exactly the kind of "honest claims" gap Foundations' objective names. |
| Situation self-contradiction on frame-class gaps (§C row 2) | **Non-blocking for architecture** but is the **same defect class** claim hygiene closed for margin — scoped narrowly here to frame-class only (not a general "any gap" rewrite of the situation branch, which would be reopening claim hygiene as a workstream, out of scope per §1/§G). | Recommend closing the frame-class instance now (small, same pattern, same file); flag any broader "PASS + any live gap" situation audit as a **separate future thread**, not this one. |
| Dual `_block_progress_status` copies (`orchestrator.py:1932-2009`, `engineering_readiness.py`) | **Non-blocking** — the one place they could silently diverge (the frame-class gate) was already extracted into one shared helper (`frame_size_blocks_structure_complete`) and verified called identically from both copies. General duplication of the surrounding param/composite/component branches remains (pre-existing, not Structure-A-specific), but no observed lie stems from it today. | Named for awareness, not a Foundations blocker. |
| `get_block_in_progress_reason` two-value enum (`missing_components`/`missing_params`) has no case for "class-incompatible" | **Non-blocking — already resolved.** Verified: `orchestrator.py:4446` only calls `get_block_in_progress_reason` for `composite` block types; `structure` (block type `"component"`) is special-cased at `:4458-4474` to call `frame_next_missing_question` directly, bypassing the two-value enum entirely. | The seam the contract asked me to check turns out to be a correctly-closed edge case, not a live gap. |
| `landing_gear` dead vocabulary key | **Non-blocking.** | Cosmetic/dead code, not a claim risk (nothing ever populates it, so nothing ever claims anything false about it). |

**No blocking gap found** that would require re-opening Structure A itself.

---

## E. Option analysis

| Option | What it buys | Evidence needed | Fase 1 fit? |
|---|---|---|---|
| **Claim/completeness copy only** | Closes both reproduced disagreements (§A) with zero new vocabulary, zero schema change, zero new gap types. | None new — reads `readiness.gaps`/`subsystems["structure"]`, already computed. | **Yes — recommended (§F).** |
| **Thin frame catalog** | Real SKU identity (brand/model/mass/material/`size_class_inch` from a manufacturer sheet) instead of free-text guesses; `catalog_bound=True` becomes reachable for structure, matching motor/battery/propeller/esc parity. | A `CatalogRef.family` schema change (`schemas/action_schema.py:139` — `"frame"` not in the `Literal` today); a new `library/frames/_datos.json` (manufacturer-declared mass/material/class only — never a measured/verified fit); a bind/search flow mirroring `motor_catalog_assist.py`. Evidence rule: catalog rows carry **declared** spec-sheet values only, same LEVEL A discipline as today's free-text declaration — a catalog row must never claim "fits" beyond the same `size_class_inch` vs propeller-`D` screening Structure A already does. | Fits the maturity bar, but is a **meaningfully sized, separate feature** (comparable to the original motor-catalog work) that fixes no currently-broken claim — it raises confidence/identity, not honesty. Not proven necessary now. |
| **Declared layout params** (wheelbase/arm/tip clearance) | Lets Jarvis **record** additional structural facts the user already knows. | Would need "declarado, no verificado" framing throughout (never implying CAD/interference proof) — same discipline Structure A used for `size_class_inch`. **Without a consumer**, these fields are write-only: nothing today would read wheelbase/arm/clearance for any check, screening, or claim. Pairing them with even a LEVEL-A-style declarative screening (e.g. "declared arm length vs declared prop radius") risks crossing into the explicitly forbidden **tip-clearance physics** line — the contract names this as out of scope, and I could not find a way to make such a check meaningfully different from an implied interference/fit claim. | **Weak fit** — not recommended as primary; flagged as a candidate only if Engineer explicitly wants inert data capture with no consumer, or names a specific declarative-only screening that a future ★ can scope precisely (this report does not draft one). |
| **CAD / FEA / generative geometry / geometric FIT VERIFIED** | Real physical fit/stress proof. | Manufacturer or lab-grade geometry + solver — categorically outside this project's deterministic-and-declarative discipline today. | **No.** Explicitly excluded by the ratification and this contract; not evaluated further. |

---

## F. Buy

**Claim/completeness copy only** (no new vocabulary, no catalog, no
`_derive_overall`/gap-type change).

Two changes, both proven necessary by reproduction, both structurally
identical to fixes already shipped and reviewed in this same phase:

1. **BOM suffix for `frame` when a live frame-class gap blocks structure** —
   same shape as control parity's `_bom_completeness_tail` special-case for
   `flight_controller` (`project_closure.py:713-724`), just keyed on
   `key == "frame"` + a live `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE`
   instead of a hardcoded key check alone.
2. **One narrow situation-branch gate for frame-class gaps** — same shape as
   claim hygiene's `margin_claim_weak` gate
   (`project_continuity.py:198-204,313-318`): insert one more
   `elif sim_status == "pass" and <frame-class gap live>:` branch before the
   plain PASS fallback, using a locked sentence naming the class-compatibility
   gap instead of "Diseño validado."

Why not more: a frame catalog and declared layout params are real options
(§E) but neither is proven necessary to stop a currently-reproduced lie —
recommending either now would be scope beyond what Foundations' objective
requires ("represent, evaluate, and communicate... without CAD or generative
geometry" — the *evaluate/communicate* gap is fully addressed by claim copy;
*represent* gains nothing from new unconsumed fields). This keeps the same
"smallest option that stops the lie" discipline claim hygiene and control
parity both used, and carries the same near-zero risk profile (no ERF
predicate change, no `_derive_overall` change, no eligibility flip).

**Forbidden in the IC that would follow:** `_frame_completeness`,
`classify_component`, `component_presence_tier`, `_derive_subsystem_verdict`,
`_derive_overall`, `frame_class_compatibility_state`,
`frame_size_blocks_structure_complete`, `GAP-FRAME-*` severity/blocks, any
new `CatalogRef` family, any `library/` addition, any new property key
(wheelbase/arm/clearance/configuration), `ASSEMBLY_READY`/
`NOT_ASSEMBLY_READY` strings.

---

## G. Explicit non-goals confirmed

Not proposed by this investigation:
- CAD, FEA, STL/STEP generation, generative geometry.
- Tip-clearance physics or any declared-layout consumer that would imply
  geometric interference/fit checking.
- "Cabe físicamente" / geometric FIT VERIFIED language of any kind.
- Class → thrust coupling (thrust/power/RPM/Ct remain untouched by frame
  class, confirmed unchanged — `set_frame_material`'s own docstring,
  `component_writers.py:64-67`).
- A frame catalog as the deliverable of *this* investigation (evaluated in
  §E as a named, separately-schedulable option — not authored here).
- Control catalog / control parity (closed thread, not reopened).
- HD-* hardware campaigns.
- Re-litigating Structure A's own LEVEL A rules, `_frame_completeness`
  formula, or the two `_block_progress_status` copies' shared gate (found
  correctly closed, not reopened).
- A general "PASS + any live gap" rewrite of Continuity's situation branch
  (claim hygiene round 2) — the frame-class instance is closed narrowly here;
  the broader pattern (any non-margin gap type coexisting with "Diseño
  validado") is named in §D as future work, not this thread's Buy.

---

## H. Suggested IC skeleton (claim-copy slice only — not an Implementation Contract)

- **Files:** `src/jarvis/core/project_closure.py` (`_bom_completeness_tail`:
  extend the `flight_controller`-only branch to also cover `frame` when a
  live frame-class gap blocks structure — needs the gap/readiness signal
  threaded in, or a pure re-derivation via `frame_class_compatibility_state`
  + `propeller_diameter_in`, whichever the IC author judges smaller-diff);
  `src/jarvis/core/project_continuity.py` (one new `elif` situation branch,
  locked sentence, placed among the existing PASS-branch guards).
- **Behavior change:** BOM `frame` line gains a suffix only when a live
  frame-class gap exists; Continuity situation reads honestly for that one
  case; `ASSEMBLY_READY`, subsystem verdicts, gap severities, architecture
  counters: byte-identical.
- **Tests:** extend `tests/test_project_closure_v1.py` (or the BOM-format
  test file the IC author picks) for the frame suffix present/absent;
  extend `tests/test_project_continuity.py` for the new situation string,
  plus a regression asserting PASS+class-compatible keeps "Diseño validado"
  unchanged.
- **Forbidden:** everything listed at the end of §F.
