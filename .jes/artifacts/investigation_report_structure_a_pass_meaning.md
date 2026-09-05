# Investigation Report — Structure A PASS meaning (frontier → Structure B)

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_structure_a_pass_meaning.md](investigation_contract_structure_a_pass_meaning.md)
**Checkpoint:** tag `v0.3.6`; live tree includes claim hygiene, control parity, Structure Foundations claim-copy, Catalog Foundation IC-1→IC-3 (suite 2197, preserved, not reverted)
**Status:** OPEN — for Engineer ★ on meaning table / Buy

Not an Implementation Contract. No `src/` edits, no widening of `_derive_subsystem_verdict`, no Structure B fields. Reconstruction runs in-memory against the live tree.

---

## 1. Executive finding

**`Structure PASS` means, in code, exactly four booleans and nothing about
geometry:** `classify_component("frame") != "missing"` (defined) AND
`calculations.total_mass_kg is not None` (calculated) AND a simulation ran
(simulated) AND that simulation's *thrust* result was `"pass"` (validated) —
`engineering_readiness.py:1193`. `catalog_bound` (whether the frame is a real,
named SKU) is computed but **never** enters this conjunction. This is the
same uniform, cross-subsystem pattern already found and accepted for Control
in the prior investigation — not a Structure-specific defect.

**Reproduced the Engineer walk exactly** (fixture below): a catalog-bound
frame (`armattan_rooster_5in`, real mass/class/material, `catalog_bound=True`)
whose class is compatible with the declared propeller, combined with PASS+
`quality=risky` propulsion and declaration-only Control, renders:

```text
Structure      PASS
Control        PASS *
...
PROJECT STATUS: ASSEMBLY READY
NOTE: margen ajustado — ASSEMBLY READY no implica reserva cómoda.
* Control: declaración — sin física de control
```

**The finding:** `Control` carries a footnote naming its declaration-only
nature; `Structure` does not — even though a catalog-bound frame's PASS is
built from the **same four generic flags**, is **not** gated on
`catalog_bound`, and asserts nothing about geometry, motor mounting, or
fabricability beyond the one LEVEL A class check Structure A already runs.
A user reading `Structure PASS` next to `Control PASS *` has a real basis to
believe Structure carries more engineering weight than Control — it does
not, structurally, in the ERF model.

**Structure B: recommend deferring entirely (Rank 0).** Every named B
candidate (`configuration`, `arm_count`, declared `wheelbase`/mounts) is
either a write-only label with no consumer (weak value) or invites a
geometric-adequacy inference Jarvis cannot honestly support without CAD
(the forbidden line, already refused once for layout params in the Structure
Foundations investigation). **Buy: (b) thin Structure A honesty IC** —
extend the already-shipped Control-parity `PASS *` pattern to Structure, closing
the one real, reproduced asymmetry — not a Structure B investigation, not a
defer-everything no-op.

---

## 2. Code-backed "today" matrix

| Evidence bit | Authority (`file:line`) | What it actually checks | Feeds `Structure PASS`? |
|---|---|---|---|
| `defined` | `_structure_evidence`, `engineering_readiness.py:1044-1045` — `classify_component("frame", ...) != "missing"` | Frame component exists and isn't a bare stub (completeness ≠ `"low"`) | Yes |
| `calculated` | `:1046` — `ctx.calc.get("total_mass_kg") is not None` | A mass number was computed *anywhere* in the project (not frame-specific geometry) | Yes |
| `simulated` | `:1047` — `bool(ctx.sim)` | Any simulation ran at all | Yes |
| `validated` | `:1048` — `ctx.sim_status == "pass" and _component_present(..., "frame")` | The **thrust/feasibility** simulation passed — no structural/mechanical simulation exists anywhere in this codebase (confirmed: zero hits for structural stress/deflection/interference solvers) | Yes |
| `catalog_bound` | `:1049` — `_catalog_ref_set(..., "frame")` | Frame is a real, named catalog SKU (Catalog Foundation IC-1/2/3) vs. free-text | **No** — computed, displayed, never read by `_derive_subsystem_verdict` (`:1193`) or `_derive_overall` |
| LEVEL A class gate | `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE`, `_frame_class_gaps`, `:886-955`; predicate `frame_class_compatibility_state`, `project_closure.py:162-195` | Declared `size_class_inch` vs. declared propeller `diameter_in` — a **class convention check**, never a geometric fit proof (locked wording: "compatibilidad de clase nivel A: no establecida", never "cabe"/"no cabe") | Only indirectly: a live gap blocks the subsystem to `INCOMPLETE` via the Gap Registry (`:1180-1188`), not via the four evidence bits above |
| BOM claim-copy | `_bom_completeness_tail`, `project_closure.py` (Structure Foundations IC) | Displays `— compatibilidad de clase nivel A pendiente` / `— clase incompatible nivel A` on the `frame` BOM line when a class gap is live | Same gate as above; no new authority |
| Continuity claim-copy | `_frame_class_gap_live`, `project_continuity.py` (Structure Foundations IC) | Situation sentence avoids "Diseño validado" when a frame-class gap is live | Same gate; Continuity-only, not ERF |

**Userdict vs. evidence bits:** the CLI/ERF renders one word, `PASS`
(`main.py`'s `_render_readiness_block`), for what is actually four unrelated
booleans plus a class-convention side-check. Nothing in the rendered word
itself distinguishes "mass+material both freely declared, class never
checked because no propeller exists yet" from "catalog-bound SKU, class
verified compatible against a real propeller" — both render identically as
bare `Structure PASS` today (confirmed: the BOM tail is the only place these
differ, and only for the two class-gap states, not for the "not_required"
state).

---

## 3. Locked ✓ / ✗ meaning table (for Engineer ★)

```text
Structure A PASS means:
  ✓ A frame component is declared (name-only, or a real catalog SKU) and is not a stub.
  ✓ mass_kg and material (when declared) fed the project's total-mass calculation.
  ✓ If a propeller diameter is already known, the frame's declared size_class_inch
    is not smaller than that diameter (a class-convention check, LEVEL A).
  ✓ The project's thrust/feasibility simulation (not a structural one) passed.
  ✓ If catalog-bound: the mass/material/class numbers trace to a named,
    sourced product (Catalog Foundation) instead of a free-text guess.

Structure A PASS does NOT mean:
  ✗ Motors fit on the frame (no mount pattern, no motor position, no arm
    geometry is modeled anywhere).
  ✗ The propeller has physical clearance from the frame/arms/landing gear
    (no clearance/interference model exists).
  ✗ The declared wheelbase/dimensions are known or consistent with anything
    (no such field exists in Structure A).
  ✗ The battery or flight controller physically mounts on this frame
    (no mounting-pattern data exists for any component).
  ✗ The frame is strong enough for the declared mass/thrust (no
    stress/deflection/load model exists — "structural" here means "declared
    mass entered a sum," not "verified to hold load").
  ✗ The frame is fabricable, buildable, or purchasable as specified
    (a catalog SKU is real; a free-text description is not checked against
    any manufacturing constraint).
  ✗ Any CAD/FEA/geometric proof was run (none exists in this codebase).
```

This table is descriptive of current code, not a proposal to change any of
it — Engineer ★ locks the wording, not the underlying booleans (§6 of the
contract explicitly forbids widening `_derive_subsystem_verdict` here).

---

## 4. Claim-copy gap inside Structure A (lean: **Yes, close it**)

**Reproduced, not hypothesized** (fixture in Appendix): with a catalog-bound,
class-compatible frame, PASS+risky propulsion, and declaration-only Control,
the readiness block renders:

```text
Structure      PASS
...
Control        PASS *
...
* Control: declaración — sin física de control
```

Structure's PASS carries no asterisk despite resting on the same four
generic evidence flags Control's does (§2), plus a class-convention check
that — critically — **only fires when a propeller is already declared**;
when no propeller exists yet, `frame_class_compatibility_state` returns
`"not_required"` and Structure can PASS having run *zero* class checks at
all, indistinguishable in the rendered word from a class-verified state.

This is the same defect class the Structure Foundations IC already closed
for the **BOM line** and **Continuity situation** (both correctly show a
caveat when a class gap is *live*) — but the **readiness block's bare
`Structure` verdict line** was never touched by that IC, because at the time
no reproduction showed it coexisting with a misleadingly bare `PASS`. This
investigation's walk reproduction is that missing evidence: `Structure PASS`
with no footnote sits directly above `Control PASS *`, in the same block, in
every project where propulsion/energy/control also close — which is common,
not an edge case.

**Recommendation:** extend the same asterisk+footnote pattern Control
already carries (`main.py`'s `_render_readiness_block`) to Structure,
scoped to the same "declaration reflects identity, not mechanical proof"
framing — not a new claim, not a new gap type, not a `_derive_overall`
change. This is a **thin Structure A honesty IC**, not Structure B.

---

## 5. Minimum Structure B candidates — ranked

| Rank | Candidate | Value | Illusion risk | Verdict |
|---|---|---|---|---|
| — | `configuration` (e.g. "quad-X", "hex") | Low — a display label with no consumer anywhere (no check reads it); same "write-only vocabulary" critique the Structure Foundations investigation already raised for layout params | Low — a bare label is unlikely to be misread as a verified fact | **Not recommended, but lowest-risk if Engineer ever wants *any* B step** — value is real but marginal (mental-mapping/identity only) |
| — | `arm_count` | Low-moderate — same write-only critique, **plus** a live hazard: it would be a second, potentially-diverging count of the same physical fact `current_parameters["motor_count"]` already tracks (flagged as an open risk in the Catalog Foundation investigation's field-authority table, never resolved) | Moderate — a number invites more confidence than a label, and a diverging arm_count vs motor_count would itself be a new, self-inflicted honesty bug | **Reject** — value does not clear the new hazard it would introduce |
| — | Declared `wheelbase`/dimensions/mounts | Only realized if paired with an actual geometric/clearance check — which is explicitly out of scope (CAD/FEA/tip-clearance forbidden) | **High** — a "wheelbase: 250mm" number sitting next to `Structure PASS` (or even `PASS *`) strongly invites the exact "motors fit"/"clearance verified" inference §3's ✗ list forbids. Already rejected once, on identical reasoning, in the Structure Foundations investigation | **Reject** |

**Recommendation: Rank 0 — defer Structure B entirely.** No candidate
clears "real mechanical meaning" without either (a) adding an unconsumed
field with no honest use, or (b) inviting exactly the illusion this
investigation's own §3 table is written to prevent. This is not a
capacity/effort judgment — it is that the *category* of representation
Structure B would add (position, geometry, mounting) cannot be made
honestly meaningful without the CAD/FEA layer the ratification explicitly
keeps closed. Deferring is the correct engineering call, not a placeholder
for "later this cycle."

---

## 6. Out (even if Structure B opens later)

- CAD, FEA, STL/STEP generation, generative geometry.
- Tip-clearance physics, motor-mount interference checks, or any
  "cabe"/"no cabe" claim.
- Fabricated structural ratings (load, stress, deflection) — no such data
  exists in any catalog family today, frame included.
- `arm_count` as a claim-closing field, ever, unless first reconciled with
  `motor_count` by a named authority (not attempted here).
- Widening `_derive_subsystem_verdict`'s PASS conjunction to require
  `catalog_bound` for Structure — confirmed unnecessary (§2): the four
  existing flags already gate PASS identically whether the frame is
  catalog-bound or free-text, and this investigation found no reproduced
  lie that requires changing that.
- Reopening Catalog Foundation IC-1/2/3 scope.

---

## 7. Open questions for Engineer ★

1. **Exact wording** for a Structure `PASS *` footnote — should it name
   "identity, not geometry" (mirroring Control's "sin física de control"),
   or something that also covers the LEVEL A class check specifically
   (since Structure, unlike Control, *does* run one real, if narrow, check)?
   This report does not draft the locked string — that is Engineer's call
   per this session's established pattern (claim hygiene / control parity
   both had Engineer/Cursor lock the exact sentence in the IC, not the
   investigation).
2. **Should the footnote condition on `frame_class_compatibility_state`
   being `"not_required"` specifically** (i.e., only when *zero* class
   checks ran, arguably the more misleading state) **or on every Structure
   PASS unconditionally** (matching Control's blanket treatment, simpler,
   more consistent)? Both are defensible; this report leans toward the
   blanket treatment for consistency with Control's own precedent, but
   names the narrower option as a real alternative.
3. Does Engineer want `configuration` as a purely declarative, unconsumed
   label at some future point for BOM/documentation richness alone (not a
   claim-closing field)? This report classifies it low-value/low-risk but
   does not recommend it now — no proven need surfaced during this
   investigation.

---

## 8. Buy recommendation

**(b) Thin Structure A honesty IC** — extend the Control-parity `PASS *` +
footnote pattern to Structure's readiness line. Smallest option that closes
the one real, reproduced gap (§4); no Structure B, no widened verdict logic,
no new claim. Suggested non-binding shape (Engineer ★ to confirm before any
IC): `src/jarvis/adapters/cli/main.py`'s `_render_readiness_block` gains a
second `PASS *`-eligible key (`structure`), with its own footnote line,
using the exact same `catalog_bound`-free, verdict-only signal Control's
already does — no ERF/Continuity change required, mirroring how narrowly
Control Parity's own IC scoped itself.

---

## Appendix — reconstruction fixture

Built as an in-memory fixture (same "fully closed" shape used across the
Catalog Foundation/Control Parity investigations): frame bound via
`bind_frame_from_catalog("armattan_rooster_5in")` (real SKU: 5″ class,
125g, fibra de carbono), propeller declared at 5″ (class-compatible),
motors/battery/ESC declared, `flight_controller`/`sensors` declared
(Control declaration-only), simulation `status=pass`, `quality=risky`,
`safety_margin_ratio=1.05`, `warnings=["low_margin"]` (weak propulsion
evidence, matching the Engineer walk). Full rendered `estado` output:

```text
Situación: Comprobación de empuje: PASS. Margen ajustado — el diseño no está
validado con reserva cómoda.
...
Componentes / gaps:
   ✓ frame: armattan_rooster_5in [armattan_rooster_5in] qty=1 (high)
   ...

ENGINEERING READINESS

Requirements   PASS
Architecture   PASS
Structure      PASS
Propulsion     PASS
Energy         PASS
Electronics    PASS
Control        PASS *
Catalog        PASS
BOM            PASS
* Control: declaración — sin física de control

PROJECT STATUS: ASSEMBLY READY
NOTE: margen ajustado — ASSEMBLY READY no implica reserva cómoda.
```

`readiness.subsystems["structure"]` = `defined=True, calculated=True,
simulated=True, validated=True, catalog_bound=True, verdict=PASS` —
`catalog_bound=True` here changes nothing about the verdict or its
rendering; only the BOM `[sku]` identity suffix differs from a free-text
equivalent.
