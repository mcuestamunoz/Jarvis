# Investigation Report — Geometry Assembly Pose Revisit (After Visualizar-3D)

**IC:** [investigation_contract_geometry_assembly_pose_revisit.md](investigation_contract_geometry_assembly_pose_revisit.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2429 (unchanged — investigation only, no code/tests touched)

---

## 1. Executive recommendation

**B0 — keep defer.** Reversal condition 1 (a cited manufacturer mounting-hole pattern for a live SKU) is genuinely **Met** — not hypothetically, literally: the 2026-09-07 pose report predicted, almost verbatim, that "30.5×30.5mm or 20×20mm bolt patterns" would be the evidence that mattered, and the very next Geometry cycle's live re-fetch (2026-09-08, Geometry-for-all B1) found exactly that on iFlight XL7 V4's own page, now on record in its `source_note`. But that same 2026-09-07 report explicitly pre-answered what this specific kind of evidence is worth: a self-geometry hole pattern (where the FC's own screws go) is "genuinely different from 'where does this sit in the whole airframe' pose" and "worth a *separate*, narrower future investigation... not conflated with this IC's relative-assembly-pose question." Condition 2 (a named body-axis/origin convention) and condition 3 (a written Engineer risk-acceptance) are both still **Not met**, confirmed by fresh evidence, not assumption. Since relative assembly pose needs an axis convention regardless of how good any single part's own hole data gets, the lean for *this* rung stays B0. The genuinely new fact — condition 1 firming up — is real and worth naming to the Engineer as a possible **separate**, narrower investigation track, but is not this report's Buy to make.

---

## 2. Delta since 2026-09-07

| Slice | What shipped | Reference-frame impact |
|---|---|---|
| Geometry-for-all B1 (@2418) | `body_length_mm`/`body_width_mm` (iFlight, 202×202mm — a footprint, no height) and `standoffs[].height_mm` text (TBS-5in, iFlight) — both re-verified present in `library/frames/_datos.json` this session | **None on their own** (footprint without height still can't glyph; a height without a diameter still can't glyph) — **but** the same live re-fetch that found these also recorded, in prose, iFlight's page stating "Mounting holes: 30.5\*30.5mm, 20\*20mm" (`library/frames/_datos.json`, `iflight_xl7_v4_7in.source_note`, quoted verbatim below) — this is new, real, on-the-record evidence, scored in §3 |
| Remaining `mounted_on` (Conn, @2429) | Two parse-symmetry bug fixes so `"helices montadas en los motores"`/`"sensor montado en el esc"` resolve correctly | **None** — confirmed `mounted_on_declare_assist.py` and `set_component_mounted_on` still only ever write a bare target *key* string; no offset, no axis, nothing numeric anywhere in the relation |
| Click-inspect B1− | `selectedId`/`onSelect` selection chrome | **None** — a highlight has no spatial meaning at all |
| CSS 3D solids B1 (@2429) | `scene3dScale.ts`/`scene3dLayout.ts`/`Scene3D.tsx`/`Solid3D.tsx` — solids at declared scale in a presentation row | **None** — re-verified this session (§4) |

---

## 3. Reversal scorecard (§E of the 2026-09-07 pose report, quoted verbatim)

> **1.** *"A manufacturer page that does publish a mounting-hole pattern or footprint-anchor for a specific SKU (this is common in the FPV world for flight-controller/ESC 'stack' standards, e.g. 30.5×30.5mm or 20×20mm bolt patterns — genuinely different from 'where does this sit in the whole airframe' pose, and worth a separate, narrower future investigation scoped to 'self-geometry hole pattern,' not conflated with this IC's relative-assembly-pose question)."*

**Met — narrowly, exactly as the condition's own text anticipated.** `library/frames/_datos.json`'s `iflight_xl7_v4_7in.source_note` (re-read in full this session, not assumed): *"Page also lists mounting hole spacing (30.5x30.5mm, 20x20mm) — not seeded here, out of scope for Geometry-for-all (pose-adjacent, flagged in the investigation report instead)."* This is the identical 30.5×30.5mm/20×20mm "stack" bolt-pattern example the 2026-09-07 report named as its own worked example of what would satisfy this condition — found live, on a real seeded SKU's real manufacturer page, one cycle later. **This is genuinely new since 2026-09-07** (that report's own evidence table shows zero mount/hole data on any page as of that date). Per the condition's own parenthetical, this is "genuinely different from... pose" — it tells you the FC/ESC stack's own screw spacing, not where that stack sits relative to the frame's origin. Scored Met on the letter of the condition; its product implication is addressed in §5.

> **2.** *"Jarvis explicitly deciding to define its own self-consistent per-project axis convention (e.g., 'arm-relative polar coordinates from a declared frame center, heading undefined') — a real, nameable design decision, but one big enough that it is itself a fresh, dedicated investigation (a body-frame convention is CAD-adjacent scaffolding), not a rider on this report."*

**Not met.** Fresh, full re-grep of `src/jarvis/schemas/action_schema.py` and `state_schema.py` this session: the only `origin` field anywhere is `HandoffContext.origin: Literal["engineering_intent"]` (`action_schema.py:246`) — an unrelated Continuity-handoff provenance tag, unchanged since before the pose report and confirmed to have nothing to do with spatial coordinates. `ComponentSpec` still carries exactly two relational fields, `parent_key` and `mounted_on` (`action_schema.py:171,184`), neither numeric, neither an axis. `Scene3D.tsx`'s `rotateX(55°)/rotateY(-30°)` default tilt is a **camera** choice — arbitrary, user-draggable, reset every session, never named as "+X = forward" or tied to any component — confirmed by reading the file: nothing in it claims or implies a shared body-frame axis (§4 goes into this in more depth). No axis/origin convention exists anywhere in the product.

> **3.** *"The Engineer explicitly accepting the risk of a 'declared-only, no axis convention, plain free-text description alongside a bare distance' model (see the contingency sketch below) — a legitimate product decision this report is not positioned to make, only to flag as a possibility with named risk."*

**Not met.** Grepped every `engineer_lock_*.md`/`engineer_ratification_*.md` file for any written risk-acceptance language — none found. The 2026-09-08 `engineer_lock_geometry_3d_placement_horizon.md` names pose as the *next rung to investigate*, which is exactly what this report is — an investigation, not a risk-accepted schema Buy. Per this IC's own explicit instruction, the Engineer's `procede` on this investigation does not itself satisfy condition 3.

---

## 4. Answers B–D

### B — What the 3D visor changed (and did not)

1. **Does a CSS box/disk at declared scale create a millimetre placement fact? No.** `scene3dScale.ts`'s `solidExtentPx` converts a component's *own* L×W×H or diameter into a size — never a position relative to any other component or any named origin. `scene3dLayout.ts`'s `layoutSolidsRow` (re-read in full this session) computes a purely presentational `originX` from running footprint + a constant CSS-pixel gap, in input order — its own docstring says so, and its type signature has no field for card `x`/`y` or `mountedOn` to even be read from (proven structurally, not just by convention, by the `U5` decoy test still present and passing: an item carrying an unused `x: 9999` produces an identical layout).
2. **Does sharing `selectedId` between solid and card create a reference frame? No.** `selectedId` is a single opaque string compared for equality (`node.id === selectedId`) in both `SpatialCard.tsx` and `Solid3D.tsx` — it carries no coordinate, no orientation, nothing spatial. It answers "which one," never "where."
3. **Could a later pose Buy project into `Scene3D` without making today's row the SoT?** Yes, in one paragraph: `Scene3D` already receives the full node list and computes its own layout at render time from whatever's in the DTO — it holds no persisted state and writes nothing back. If a future, separately-Bought pose fact ever existed on a `ComponentSpec`, `Scene3D` could read it instead of falling back to `layoutSolidsRow`'s row, the exact same way `SpatialGlyph` already reads `geometry` instead of inventing a shape — a presentation-layer swap, not a re-architecture, and `state.json` would remain the sole source of truth throughout. This is not a design proposal here, only confirmation that today's plumbing doesn't paint anyone into a corner.

### C — Honesty if anyone still wants a tiny Buy

Per this investigation's own §A instruction ("If A is all Not met, do not sketch a schema as if it were recommended"): condition 2 and 3 are Not met, so **no schema sketch is offered in this report**. The 2026-09-07 report's own §6 contingency sketch (single declared scalar + mandatory prose, explicitly not recommended there either) is cited, not revived, and remains exactly as un-endorsed as it was on 2026-09-07.

### D — Buy options

| Option | Recommended? |
|---|---|
| **B0 — Keep defer** | **Yes.** Two of three reversal conditions remain unmet; the one that firmed up (condition 1) was pre-scoped by the parent report itself as answering a *different* question (self-geometry, not relative pose). |
| B1 — Optional declared translation | No — condition 2 (axis convention) still absent; a "declared" number still has no frame to be declared *in*. |
| B1+ — Translation + yaw | No — same blocker, worse. |
| B0+risk | No — condition 3 requires a written Engineer risk-acceptance that does not exist; this report is not positioned to manufacture one, per the IC's own instruction. |
| Reject numeric pose (permanently) | No — unchanged from the parent report's own reasoning: "blocked on evidence," not "impossible in principle." A live, on-the-record hole pattern arriving one cycle after the defer is itself proof the door isn't nailed shut. |

**What would change this lean:** conditions 2 or 3 becoming Met (unchanged from the parent report — no wording fix needed; both conditions read exactly as intended and were scored cleanly against fresh evidence). Additionally, worth naming as a **distinct, separate** possible next step the Engineer may want to ★ independently of pose: a narrower investigation into "self-geometry hole/mount-pattern KNOW" (per-part mount-hole spacing as its own declared fact, e.g. for FC/ESC stack standards) — exactly the separate track the 2026-09-07 report itself proposed when this evidence class showed up. This report does **not** recommend that investigation be opened now, only names it as the honest home for the condition-1 evidence, so it isn't lost or mistakenly folded into the pose question.

---

## 5. Supersede or reaffirm?

**Reaffirm** the 2026-09-07 B0 Defer for relative assembly pose — not superseded. One of its three named reversal conditions became concretely true, which is real, meaningful progress worth recording precisely (this is not a rubber-stamp — evidence changed) — but the report that set those conditions already anticipated this exact evidence and already explained why it answers a different, narrower question than the one B0 was blocking. Reaffirming with an updated, more precise scorecard is the honest outcome, not treating "nothing changed" and not treating "something changed" as the same thing when neither actually reverses the lean.

---

## 6. Risks if we Buy wrong

- **"Solids exist ⇒ pose" is the single most likely wrong inference an outside reader could draw from the shipped CSS 3D pane**, and this report exists partly to foreclose it explicitly: a row of proportionally-scaled boxes and disks is not a placed airframe, and nothing about rendering them in 3D make the *idea* of pose any closer to sourced than it was in 2D. Treating the row's left-to-right order or its fixed camera tilt as meaningful position/orientation would be exactly the invented-convention trap condition 2 exists to prevent.
- **Conflating condition-1's hole-pattern evidence with relative-pose evidence** would be the second most likely mistake — a bolt spacing on one part's own PCB says nothing about where that part's origin sits relative to the frame's origin, which is the actual fact pose needs. Buying B1/B1+ on the strength of condition 1 alone would produce numbers that look sourced (a real quoted mm figure) while still being meaningless for the stated purpose (comparable, honest relative placement) — the same "precise-looking, not honest" trap named throughout this whole investigation line.
- **Under-reporting the delta** (treating condition 1 as fully "Not met" because it doesn't unblock pose) would also be dishonest in the other direction — it would waste real evidence and could cause a future investigator to re-discover the same iFlight hole pattern from scratch instead of building on it.

---

## 7. Later rungs (named, not bought)

```text
visualizar-3D (CLOSED)
  → assembly relation (CLOSED) — mounted_on, guide only
  → pose: place solids at a real position/orientation
      (STILL B0 DEFERRED — this report's own conclusion; reversal
       conditions 2/3 unmet; condition 1 answers a narrower, separate
       question, named above but not opened here)
  → "cabe" / fit vs. that placed situation
      (fit stub QUEUED — DO NOT IMPLEMENT, confirmed still queued,
       not touched, not un-queued by this report)
```

---

## 8. Explicit non-goals honored

No code changed — `git status --short -- src/ ui/ tests/` is empty for this cycle. No pose/offset/orientation/origin field added or sketched as recommended (§C explicitly declines to sketch one, per conditions 2/3 being unmet). No hole pattern, plate center, or axis convention invented — the one hole-pattern fact cited (§3) is a direct quote of an already-existing, already-cited `source_note`, not a new claim. `layoutSolidsRow`/card `x`/`y`/`mounted_on` were read, not treated as millimetre placement — §4.B is explicit that none of them constitute a reference frame. The fit stub was read (confirmed still `QUEUED — DO NOT IMPLEMENT`) and not un-queued. No N-motor/N-propeller solids proposed — `motor_count` as a property was not touched, multiplicity was out of scope and stayed out. The 3D pane's layout (center/overlay/size) was not touched — this report only re-verified the already-shipped `Scene3D`/`.sb-scene3d` structure, per the Engineer's own "parked" instruction. No Three.js/WebGL, no CAD/FEA, no Conversation Engine, no Here3/Pixhawk identity reopened, no version bump, no Implementation Contract written — §6 of the 2026-09-07 report was cited by reference only, not reproduced or revived as a recommendation.
