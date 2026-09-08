# Investigation Report — Geometry Pose Box-Anchored Origin (Existing Solids)

**IC:** [investigation_contract_geometry_pose_box_anchor.md](investigation_contract_geometry_pose_box_anchor.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2429 (unchanged — investigation only, no code/tests touched)

---

## 1. Executive recommendation

**B0 — defer, but with a genuinely new, separable finding worth recording: the origin *point* half of this problem is honestly solvable; the axis half is not, for a different and more specific reason than the previous cycle's.** A geometric center of an existing declared box (FC, ESC, or battery) is a well-defined function of `length_mm`×`width_mm`×`height_mm` alone — no invention, no extra KNOW, real progress over the plate-center candidate that *did* require invention. But re-reading all three box seeds' own source notes this session surfaces a fact the prior investigations never had reason to check: **every one of them explicitly documents its L/W/H labels as "verbatim print order"** — the battery's own note goes further and calls its axes **"unlabeled"** outright. None of the three sources ever claimed which edge is "up," "forward," or anything else physically meaningful; the labels are an artifact of which order a marketing page happened to print three numbers in. A point without any verified axis to measure *along* cannot express a translation, so the Buy still cannot proceed to anything numerically usable — but this is a **different, freshly-evidenced** wall than "no data exists" (the plate case), and it is worth Jarvis knowing precisely which wall it is now standing at.

---

## 2. Relation to the origin/axes (plate/front-arm) B0

**Unchanged and not re-litigated**: `frame_plate` still has no L×W to put a point on; `frame_arm` is still one generic key representing however many physical arms exist, so "the front arm" still cannot be named. That investigation's conclusion stands exactly as written.

**What this investigation adds**: a *different* candidate class — nodes that already have a full `geometry: box` — was not previously scored on its own terms. It turns out to fail differently: not "no point exists" (a point does, honestly), but "no axis has ever been verified to mean anything beyond a bare magnitude." This is new information, not a restatement.

---

## 3. Live box/disk census (re-verified this session, not assumed)

Re-ran the real projector against the actual demo project's `state.json`:

| Key | `geometry.shape` | Dims | `mounted_on` |
|---|---|---|---|
| `flight_controller` | `box` | 44.0 × 84.0 × 12.0 mm | `frame_plate` (shapeless target) |
| `esc` | `box` | 50.0 × 21.6 × 12.0 mm | `frame_plate` (shapeless target) |
| `battery` | `box` | 37.0 × 35.0 × 75.0 mm | `frame` (shapeless target) |
| `motors` | `disk` | Ø27.9 mm | `frame_arm` (shapeless target) |
| `propellers` | `disk` | Ø127.0 mm | `motors` (a box-having... no, a disk-having target) |
| all 9 remaining keys | `None` | — | mostly `None`, `sensors→esc` |

Exactly **3 boxes, 2 disks, 9 none** — confirmed, matching the IC's own prediction precisely. `_geometry_from_spec` (`spatial_board.py:227-276`, re-read in full) is unchanged since Glyph B1: box requires the complete L×W×H triple, disk requires exactly one diameter, `None` otherwise — no new shape logic exists to reconsider.

**The DTO's field names carry no directional documentation anywhere** — grepped `action_schema.py`/`types.ts` for any comment associating `length_mm`/`width_mm`/`height_mm` with a real-world direction: none exists (`types.ts:24` is the bare type union, no annotation beyond the field names themselves).

**Source notes, quoted verbatim, all re-read this session:**
- Flight controller (`aerial.py:546-561`, `FLIGHT_CONTROLLER_DIMENSIONS["pixhawk_4"]`): *"PX4 official docs... and Holybro's own product page... agree. **Verbatim print order** mapped to length/width/height. No mounting hole pattern stated..."*
- ESC (`library/esc/_datos.json`, `hobbywing_xrotor_40a_6s.source_note`): *"Page states size \"50.0x21.6x12.0mm\"... — **verbatim print order** mapped to length/width/height."*
- Battery (`library/baterias/_datos.json`, `lipo_4s_1500mah.source_note`): *"Page states size \"37X35X75mm\" (**unlabeled axes**, no tolerance note beyond \"1-5mm difference\") — mapped **verbatim print order** to length/width/height (N2a)."*

All three — independently sourced, different manufacturers, different part families — use the identical honest hedge: the three numbers are real and sourced, but their *order* (and therefore which one is "up," "forward," or "sideways" on the real object) is not a manufacturer claim, it is this project's own data-entry convention for turning an unordered size triple into three named fields.

---

## 4. Answers A–E

### A — Who can be origin?

**A1 — Which live keys have `box`, and can any be origin?** `flight_controller`, `esc`, `battery` (§3). Any one of them *can* be origin in the sense that a point can be derived from its own declared dims (§B) — there is no reason to restrict to a single default like "always FC"; origin is legitimately a per-relationship choice, same as `mounted_on`'s own target is chosen per-relationship rather than hardcoded.

**A2 — May origin be optional and user-declared as an existing box key?** Yes in principle — this mirrors `mounted_on` itself (optional, declared, names an existing key) and would need no new validation concept beyond "the named key must currently have a `box` `geometry`." Not implemented here; named as a mechanically reasonable shape for a future IC, not a recommendation to build it now (§C blocks the Buy regardless).

**A3 — Confirm disks cannot be origin in B1 without inventing an in-plane heading.** **Confirmed.** A disk's DTO carries exactly one number, `diameter_mm` — a circle has rotational symmetry in its own plane, so there is no "which way is +X within the disk" without inventing one (any radius is as good as any other, by construction of a circle). Even the disk's *out-of-plane* direction (the axis a motor shaft would spin around) is not recoverable from `diameter_mm` alone. Disks are correctly excluded as origin candidates; nothing found here reopens the motor-cylinder question.

**A4 — Confirm shapeless keys stay invalid origins.** Confirmed unchanged — `frame_plate`/`frame_arm`/`frame_cage`/`frame_standoff`/`frame` root all still return `None` from `_geometry_from_spec` (re-verified live, §3), so there is nothing to derive a point from; the prior investigation's conclusion for this class is untouched.

### B — What point on the box?

**B5/B6 — Smallest honest derived point; is it invention?** **Geometric center** — `(length_mm/2, width_mm/2, height_mm/2)` measured from any consistently-chosen corner — is the default: it is a pure function of the three already-sourced numbers, requires no new KNOW, and needs no assumption about which edge is "up" or "forward" (a center is a center regardless of orientation). This is **not** invention: it does not add a physical fact the source never stated; it computes a mathematical property (a rectangular prism's own centroid) that is true by definition of the shape, the same way "this box's volume is L×W×H" would be. A named corner (e.g., "the min-L/min-W/min-H corner") is equally honest and equally cheap, and is named as a later, interchangeable choice — not a second recommendation, just noting the center isn't the *only* honest option, in case a future IC prefers a corner for a different reason (e.g. matching how a datasheet diagrams a part).

**B7 — Units.** mm, in whatever local frame is eventually chosen — moot pending §C.

### C — What axes?

**C8 — Can DTO length/width/height be identified as a local X/Y/Z *of the part* without claiming drone heading?** **Not honestly, and this is the report's central finding.** Even stripped of any airframe claim, calling `length_mm` "the X-edge" implies at minimum that there *is* a consistent, singular edge the sourced number refers to — but "verbatim print order" (§3, all three parts) means the assignment of a given number to "length" vs. "width" vs. "height" was made by whoever transcribed the manufacturer's page, not by the manufacturer asserting "this is the length." Two different transcribers reading the same page could have produced two different, equally defensible length/width/height assignments for the same physical part. A local frame built on top of that labeling would be internally self-consistent (three numbers, three axes, no math error) but would not be a *fact about the part* — it would be a fact about which order a number appeared in a bulleted spec list. This is a materially different failure mode from the plate/arm case (there, the data plain doesn't exist; here, data exists but was never sourced *as* an axis assignment) — worth distinguishing precisely rather than folding into "still B0" without explanation.

**C9 — Does the first Buy need an extra "which DTO axis is airframe forward" field, and is that field declared or blocked?** Moot given C8 — there is no honest *local* axis to promote to "airframe forward" in the first place. Naming such a field would be adding a second layer of unverified assignment on top of the first.

**C10 — `+Z up` (gravity) vs. `height_mm` — can they conflict, and what's the honest rule?** They can, and the battery's own source note proves it in the most direct way available: it calls its own axes **"unlabeled,"** meaning even Jarvis's own data-entry has no confidence `height_mm` corresponds to the battery's installed-vertical dimension (a battery is frequently mounted on its broad face, making its "height" as printed on a spec sheet the *horizontal* thickness once installed, not the vertical one). The honest rule is: **no relationship between `height_mm` and gravity-relative up is assumed or assumable from the current data** — asserting one would be exactly the invented-axis-convention this whole line of investigation exists to prevent.

### D — Who can be placed?

**D11/D12/D13 — Translation for another box; a disk (motor) in that frame; no-`geometry` nodes.** All three are moot given C8 — a translation vector requires axes to be expressed along, and none exist yet, regardless of whether the *target* being placed is a box, a disk, or nothing at all. No-`geometry` nodes (frame parts, sensors) remain exactly what the prior two investigations already concluded: relation-only (`mounted_on` text + 2D edge), no millimetre pose — reaffirmed, not re-derived.

### E — Buy options

| Option | Recommended? |
|---|---|
| **B0 — Defer** | **Yes.** Point is solved; axes are not, for a freshly-specific reason (unverified label order, not absent data). Both are required together for anything numerically expressible. |
| B1 — Named local prism frame | No — see C8/C10: a "local, no-airframe-claim" frame still requires *some* verified, consistent edge-to-axis assignment, which none of the three sourced parts actually has (their own notes say so). |
| B1+ — Prism frame + optional translation | No — strictly stronger than B1, which already fails. |
| B2 — Claim airframe +X | No — same reasoning as origin/axes B0, unchanged. |
| **Reject (box-anchor is the same trap as plate-center)** | **Partially endorsed, precisely qualified**: the *axis* half is indeed the same class of trap (an unverified assumption dressed as a declared fact). The *point* half is genuinely **not** the same trap — it is honestly derivable and this report says so plainly, rather than discarding the whole candidate as equally tainted. |

**What would change this lean:**
1. A source that documents which physical edge/face a part's L/W/H actually correspond to (a diagram, an explicit "length = along the USB connector" style manufacturer statement) — for even one of the three seeded boxes, this would make that specific part's local axes honestly nameable, independent of any airframe claim.
2. Either of the still-open origin/axes conditions from the prior two investigations (an adopted Jarvis-wide convention decision written down, or arm individuation making a "front" nameable) — unchanged, not re-derived here.
3. A written Engineer risk-acceptance of "declared center + explicitly unverified/arbitrary local axes, labeled as such" — not currently present, and this report does not manufacture one, consistent with every prior cycle's discipline on this exact point.

**Field-name sketch:** not provided — per the IC's own instruction, a sketch is only offered when the lean ≠ B0, and only up to what that lean supports. This report's lean is B0.

---

## 5. Risks

- **Treating a box's geometric center as "the origin is solved" without also solving axes would be the single most likely misreading of this report.** A point with no verified axis to measure along cannot express a translation — "we found an honest origin" is real progress, but it is not "we found a pose convention," and this report is explicit about the gap between those two claims.
- **Treating `length_mm`/`width_mm`/`height_mm` as if they were a manufacturer-verified local frame would silently promote a data-entry artifact into a claimed physical fact** — the exact failure mode C8/C10 name concretely, with direct quotes, rather than as a hypothetical.
- **Treating the CSS 3D row's own per-object display axes (`solidExtentPx`'s `length→x, width→y, height→z` display convention, confirmed in the prior CSS 3D report as "a visor display convention only, not a CAD/body reference frame") as if this investigation had upgraded them into real axes** — it has not; that mapping remains exactly what it always was, presentation only.

---

## 6. Later rungs (named, not bought)

```text
visualizar-3D (CLOSED) → click-inspect (CLOSED)
  → box origin POINT                              honestly derivable (this report) —
                                                    but inert alone
  → verified local/airframe AXES                   STILL BLOCKED — needs either a
                                                    diagram-sourced edge meaning, an
                                                    adopted Jarvis convention decision,
                                                    or arm individuation (prior report)
  → numeric pose (place using point + axes)        unreachable until axes exist
  → later visor rider: move Scene3D solids
      using a real pose fact                        named, not designed, per prior report
  → "cabe" vs that spatial situation                fit stub QUEUED — DO NOT IMPLEMENT,
                                                     confirmed still queued, not touched
```

---

## 7. Non-goals honored

No code changed — `git status --short -- src/ ui/ tests/` is empty for this cycle. No pose/origin/axis field added or sketched as recommended (§E explicitly withholds the field-name sketch, since the lean is B0). No plate L×W, plate center, front arm, or motor cylinder invented — `frame_plate`/`frame_arm` were re-confirmed shapeless (§4.A4), not revisited as origin candidates, and disks were explicitly re-confirmed excluded as origins without inventing an in-plane heading (§4.A3). Arm individuation was not ★'d — cited once, unchanged from the prior report, not re-argued as a recommendation. No manufacturer page was live-fetched this session — every quote in §3 comes from already-committed seed/source files, read fresh, not re-verified against the internet. `Scene3D`'s tilt and `layoutSolidsRow` were not touched and not treated as the frame (§5, explicit). The fit stub was not opened or un-queued. No Three.js/pane-chorome change, no version bump, no CAD/FEA, no Conversation Engine, no Here3/Pixhawk identity reopened, no Implementation Contract written.
