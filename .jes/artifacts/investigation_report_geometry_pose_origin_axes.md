# Investigation Report — Geometry Pose Origin & Axes (Body Frame)

**IC:** [investigation_contract_geometry_pose_origin_axes.md](investigation_contract_geometry_pose_origin_axes.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2429 (unchanged — investigation only, no code/tests touched)

---

## 1. Executive recommendation

**B0 — defer convention, full stop (not even name-only).** A component *key* can honestly serve as "the thing you measure from" today (reaffirming the earlier pose investigation's own finding) — but naming a key only answers *which object*, never *where on it* or *which direction*. Both of those remaining pieces hit real, freshly-identified walls: an origin needs a **point** on the reference object, and every frame-part key that could plausibly hold one (`frame`, `frame_plate*`) has **no L×W/shape data at all** (Class A gap, cited from Geometry-for-all, not re-invented here) — so there is no surface to put a point on without inventing one. A horizontal axis needs something to be "forward," and Jarvis's schema does not individuate arms (`frame_arm` is one generic key with a `count` property, not four separately-identified, separately-oriented objects) — so even a **name-only** rule like "+X along the front arm" cannot be expressed today, for lack of a "front arm" to point at. The one axis that *is* free — "+Z is up, away from gravity" — needs no new data and invents nothing, but is useless in isolation: one axis and no origin point cannot place anything relative to anything. Naming a convention scaffold that cannot yet be exercised by any real fact would be progress-theater, not honesty — the same trap this whole investigation line has repeatedly rejected for envelopes, now recurring for axes.

---

## 2. Vision map

```text
cards + mounted_on                                    SHIPPED
  → 3D image at declared scale (CSS 3D row)            CLOSED (rung 1)
  → click solid opens today's card                     CLOSED (rung 2)
  → move / place in physical location                  BLOCKED — this investigation is rung 3's blocker
      (needs: an origin point + named axes — neither exists)
  → later "cabe" vs that spatial situation              not reachable until rung 3
```

This investigation's job was to determine whether rung 3's blocker can be honestly cleared, even partially (naming only, no numbers). It cannot yet, for reasons specific enough to name precisely (§4), not merely "still hard."

---

## 3. Class A vs Class B — all 14 live demo keys (re-verified this session)

| Key | Solid today? (Class A) | `mounted_on`? | Missing for a **solid** | Missing for **placement** (Class B) |
|---|---|---|---|---|
| `motors` | ✅ disk Ø27.9mm | `frame_arm` | — | An origin point on `frame_arm` (has none — no L×W/shape at all) and axes to place the disk relative to it |
| `propellers` | ✅ disk Ø127mm | `motors` | — | `motors` *is* a solid (Class A clear), but still no axis convention to express "how far along the shaft" |
| `esc` | ✅ box 50×21.6×12mm | `frame_plate` | — | An origin point on `frame_plate` (thickness+material+label only, no L×W) |
| `battery` | ✅ box 37×35×75mm | `frame` | — | An origin point on `frame` root (mass/size-class/material only — no shape) |
| `flight_controller` | ✅ box 44×84×12mm | `frame_plate` | — | Same as `esc` — `frame_plate` has no shape to anchor to |
| `frame` (root) | ❌ | — (root) | Unsourced L×W (a footprint alone, even where it exists — see iFlight's `body_length_mm`/`body_width_mm` — has no accompanying height on any seed row); the root also needs to *be* the horizontal-axis reference and cannot until arm individuation exists (§4.B) | Is itself the candidate origin *key* — but has no point on it and no axis defined *from* it |
| `frame_arm` | ❌ | — | Thickness+material only, no L×W ever sourced (unchanged since Geometry-for-all) | Not individuated — one generic key represents however many physical arms exist (`count`), so it cannot itself be "the front arm" |
| `frame_plate` / `_2` / `_3` / `_4` | ❌ | — | Thickness+material+label only; no plate footprint sourced for any of these four rows (iFlight's footprint, where it exists, lives on a *different* seed's root, not any of this project's plates) | Same as `frame_arm` — no shape, so no surface to put an origin point on |
| `frame_cage` | ❌ | — | Material only (`titanio`), zero dims on any seed row | Same |
| `frame_standoff` | ❌ | — | Material only (`aluminio`) on this project's Armattan bind; height-text exists on 2 *other* seed rows (TBS-5in, iFlight) but never a diameter, so still no shape | Same |
| `sensors` (Here3) | ❌ | `esc` | Identity frozen — zero dims path exists for any GPS/sensor model | `esc` *is* a solid (Class A clear) for the target side, but there is still no axis convention to express relative position even onto a solid target |

**One sentence, per §4.C's own instruction: completing Class A (sourcing every plate's L×W, giving the frame root a height, etc.) would not produce an assembled 3D drone** — it would only make more nodes solid-eligible; none of that touches Class B's actual blocker, which is the absence of any origin point or axis definition, a completely separate kind of fact no amount of additional envelope sourcing supplies.

---

## 4. Answers A–E

### A — Origin

**A1 — Which component keys can honestly be an origin today?** Any existing, addressable key (`frame`, `frame_plate`, `frame_plate_2`, `frame_arm`, …) — reaffirming, not challenging, the 2026-09-07 pose report's own finding: naming a key requires zero new data, since these keys already exist. **Reaffirmed with fresh evidence**: re-read `ComponentSpec` (`action_schema.py:143-184`) this session — nothing about which keys exist has changed, and the mechanism (`mounted_on` already names arbitrary keys, `set_component_mounted_on` already validates existence) is unchanged.

**A2 — Is "origin = component key, point unspecified" enough to name a frame, or still not a millimetre origin?** **Not enough, and this is the load-bearing finding of this investigation.** A key names *which object*; it says nothing about *where on that object* is "zero." For `frame_plate` specifically, there is no length, no width, no corner, no center documented anywhere (Class A gap, §3) — there is no surface at all to place a point on without inventing one (a "plate center" or "top-left corner" would be exactly the invention Locked Stance 9/the stop conditions forbid). Naming `frame_plate` as "the origin" is honest as identity, but cannot yet carry a millimetre meaning — it is a placeholder for a fact that doesn't exist yet, not a partial version of that fact.

**A3 (forbidden, confirmed not recommended):** No plate centroid, arm root, "frame center," or canvas-middle convention is proposed anywhere in this report.

### B — Axes

**B4 — Can Jarvis adopt an explicit, declared axis convention (not inferred from the 3D camera)?** **Only partially, and the useful part is missing.** "+Z = up, away from gravity" is genuinely free — it needs no per-project data, applies to every vehicle, and invents nothing (gravity's direction is a physical universal, not a declared fact about any specific frame). But a **horizontal** reference ("+X = forward") is not similarly free: the natural, honest way to define "forward" for a multirotor is "along a named arm" or "toward a named face of the frame" — and Jarvis's schema does not individuate arms. `frame_arm` (`aerial.py`'s `FRAME_ARM_KEY`, confirmed via the live demo and Geometry-for-all's own projection code) is **one generic key carrying a `count` property** — it represents "the arm design, and there are N of them," never four (or six, or eight) separately-identified, separately-positioned objects one of which could honestly be called "the front one." Declaring "+X along the front arm" today would require inventing which arm is front — exactly the kind of unsupported assumption this investigation line has consistently rejected. **Confirmed via fresh re-check of `aerial.py`'s frame-part vocabulary this session**: `FRAME_ARM_KEY`, `FRAME_PLATE_KEY`(+ordinals), `FRAME_CAGE_KEY`, `FRAME_STANDOFF_KEY` are the complete part vocabulary — no per-arm ordinal siblings exist (unlike plates, which do get `frame_plate_2`, `_3`, `_4`).

**B5 — Where would a convention live?** Moot given B4's answer — no convention is recommended to ship. If one ever were, per-project (`ProjectState`) is the only honest choice among the three named options: a global Jarvis constant would falsely imply every airframe shares one physical "forward," which isn't true across configurations (`quad_x` vs `deadcat` already differ in the *string* sense, let alone geometrically); documentation-only would not be a declared, checkable fact at all.

**B6 — Can a component be placed relative to a key whose own target has no envelope?** The *relation* already works regardless — `mounted_on="frame_plate"` requires nothing about `frame_plate`'s shape, confirmed by `set_component_mounted_on`'s own validation (target-existence only, never geometry-existence). A future *numeric* pose fact, however, would be blocked for exactly the Class-A-blocked targets (7 of the 8 non-root frame parts) for the same reason as A2 — no point to measure from. This is worth naming precisely: **relation and placement have different, independent prerequisites** — a relation only ever needed the target to exist; placement additionally needs the target to have a shape.

### C — Gap matrix

See §3. Completing Class A does not produce Class B — restated once, per the IC's own required one-sentence answer, not repeated further.

### D — First Buy vs later visor

**D7 — Smallest convention Buy: names-only vs numbers?** Names-only was this report's own hoped-for minimum, and it does not clear the bar (§4.A2/B4) — the only genuinely free name ("+Z up") is real but insufficient alone, and everything else needed to make a convention *useful* (an origin point, a horizontal reference) currently requires inventing something. **Default lean is therefore B0 for the convention question too**, not just for numbers.

**D8 — Could a later visor move solids using a future convention + user-declared numbers?** Named as later, not designed: yes in principle, and `Scene3D`'s architecture already supports this without rework (confirmed in the immediately-prior pose-revisit report — it computes layout at render time from whatever's in the DTO, holds no persisted state). This remains true and unchanged; not re-derived here beyond citing it.

**D9 — 3D `mounted_on` edges: visor chrome or pose?** Out of any first convention Buy, unchanged from the prior investigation's own stance — the 2D edges already ship the relation guide; a 3D edge would be presentation, not a new fact, and isn't needed to decide anything in this report.

### E — Buy options

| Option | Recommended? |
|---|---|
| **B0 — Defer convention** | **Yes.** Neither an origin point nor a usable horizontal axis can be named without inventing one; the one free axis (+Z up) is real but alone cannot place anything. |
| B1 — Named convention, no mm | No — see D7. A convention that can name "up" but nothing else useful is not a coherent product step; shipping schema/doc scaffolding nothing can yet exercise is the same "looks like progress, isn't" trap the envelope-invention rule exists to prevent. |
| B1+ — Convention + optional declared translation | No — strictly stronger requirement than B1, which already fails. |
| B0+risk scalar+prose | No — no written Engineer risk-acceptance exists (re-confirmed: grepped every `engineer_lock_*`/`engineer_ratification_*` file this session, none found), and this report does not manufacture one. |
| Reject mixing (envelopes-for-3D-completeness) | **Endorsed as a standing rule, not a new Buy** — explicitly, sourcing more plate/cage/standoff envelopes *in order to* make the 3D row "look assembled" would be exactly the wrong reason to do real KNOW work, and this report recommends against ever framing future Geometry-for-all cycles that way. |

**What would change this lean:**
1. Either of the two 2026-09-07/pose-revisit reversal conditions still open (an explicit Jarvis-adopted axis convention decision, or a written Engineer risk-acceptance) — unchanged, not re-litigated here.
2. **A new, more specific condition surfaced by this investigation**: arm individuation — if a future Structure-side Buy ever gave each physical arm its own addressable key (mirroring how plates already get `frame_plate_2`, `_3`, `_4`), "+X along the [specifically-named] arm" would become nameable without invention for the first time. This is **not** a recommendation to build arm individuation — it is named so a future investigator doesn't have to re-derive why axes are blocked from scratch.
3. Any seed ever publishing a plate/frame-root footprint *and* a matching height (a real, complete L×W×H for a plate specifically, not just a root-level body footprint) would clear the origin-point half of the problem for that one part — reaffirming, not superseding, Geometry-for-all's own already-settled "reject inventing it" stance while naming exactly what would change it.

---

## 5. Risks

- **"More envelopes ⇒ closer to placement" is the single most important wrong inference to guard against.** §3/§4.C are explicit that Class A and Class B are independent axes of honesty — a future cycle that sources every plate's L×W would raise the solid count from 5/14 toward 14/14 and would still not produce a single placeable fact, because nothing about a shape answers "relative to what, along which direction."
- **Treating "+Z up" as "we have axes now" would be a smaller but real version of the same mistake** — one free, universal, physics-given axis is not a body frame; it cannot express any horizontal relationship, which is the overwhelming majority of what "place this ESC on that plate" would need to mean.
- **Under-naming the arm-individuation finding** would risk a future cycle re-discovering the same wall from scratch — named explicitly in §4.E as the most concrete, specific condition that would change this lean, precisely to prevent that.

---

## 6. Later rungs (named, not bought)

```text
visualizar-3D (CLOSED) → click-inspect (CLOSED)
  → origin + axes convention                    STILL B0 — this report's conclusion
      [reversal: arm individuation, OR a plate/root L×W+height pair,
       OR a written Engineer risk-acceptance, OR an adopted axis decision —
       none present today]
  → numeric pose (place solids using that convention)   unreachable until the above
  → "cabe" vs that spatial situation               fit stub QUEUED — DO NOT IMPLEMENT,
                                                     confirmed still queued, not touched
```

---

## 7. Non-goals honored

No code changed — `git status --short -- src/ ui/ tests/` is empty for this cycle. No pose field, origin field, or axis field added or sketched as recommended — §4.D explicitly declines even a names-only sketch, since D7 concludes it doesn't clear the bar. No envelope invented for any plate, the frame root, motor axial height, or Here3 — every "missing for a solid" cell in §3 names an absence, never fills it. iFlight's 30.5/20 hole pattern and its `body_length_mm`/`body_width_mm` footprint were read (cited via the already-existing Geometry-for-all/pose-revisit reports) but not re-fetched, re-argued, or seeded as pose — confirmed no `library/**` file touched. `mounted_on` and `Scene3D`'s camera tilt were read and explicitly confirmed **not** to constitute axes (§4.B4, §3) — neither was changed. The fit stub was read (confirmed still `QUEUED — DO NOT IMPLEMENT`) and not un-queued. No N-motor/N-propeller individuation was proposed as a recommendation — arm individuation is named strictly as a *reversal condition* to watch for, not a Buy. The 3D pane's center/overlay/layout was not touched. No Three.js/WebGL, no CAD/FEA, no Conversation Engine, no Here3/Pixhawk identity reopened, no version bump, no Implementation Contract written.
