# Investigation Report — Motor Declared Envelope (Geometry axis, next family)

**Project:** Jarvis
**Date:** 2026-09-06
**Investigator:** Claude Code
**Contract:** [investigation_contract_geometry_motor_envelope.md](investigation_contract_geometry_motor_envelope.md)
**Parents:** [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md) · Battery B1 CLOSED suite 2316, Board smoke ACCEPT
**Status:** OPEN — for Cursor review → Engineer ★ on Buy

**Not an Implementation Contract. No `src/` edits made.** Every dimension claim below was re-fetched live this session from each candidate row's own cited `source_url`, not reused from the Battery investigation's passing mention of EMAX RS2205.

---

## A. Executive answer

`MotorSpec` (`library.py:36-66`) has zero geometry fields today — confirmed. Exactly 2 of 20 motor seed rows carry a real `source_url`/`identity_status: verified` (`emax_rs2205s_2300`, `sunnysky_r2205_2500`) — both re-fetched live this session. Both agree, unambiguously, on **stator diameter (22mm) and stator height (5mm)** — the "2205" in each SKU's own name literally encodes this, and both pages state it independently. Both also state an *overall* diameter, but under different labels ("Motor Diameter" 27.9mm vs "Rotor Diameter" 27.4mm) that plausibly mean the same physical feature. **The one field the Battery precedent would tempt reuse of — an overall axial "height"/"length" — does NOT survive scrutiny**: EMAX states "Motor Height: 31.7mm" while SunnySky states "Body Length: 18mm" for a motor of the *same* stator class (22×5mm) — nearly double, because EMAX's figure includes its own separately-stated "15mm Extended Prop Shaft" and SunnySky's doesn't. Treating these as the same field would silently conflate two different physical facts under one name — the identical mistake the Frame Assembly Physical Model investigation already named and rejected for plate roles. **Recommendation: seed `stator_diameter_mm`, `stator_height_mm`, `diameter_mm` (overall bell) — omit overall axial height/length from this increment.** Binding path: `bind_motor_from_catalog` takes a `MotorSuggestion` dict today, not a SKU (`catalog_bind.py:24-26`) — the smallest honest path is one added optional `library` parameter + one `lib.get_motor(sku)` call inside `bind_motor_from_catalog`, mirroring Battery/Propeller/ESC's existing pattern; `MotorSuggestion`'s `TypedDict` (`motor_catalog_assist.py:14-23`) does **not** need widening. **Buy: B1**, Motor only, same shape and size as Battery B1.

---

## B. As-is inventory + bind-path analysis

| Surface | Finding | Citation |
|---|---|---|
| `MotorSpec` fields | `name, thrust_n, kv_rating, weight_g, compatible_prop_inch, min/max_thrust_n, kv_min/max, is_generic, max_watts, manufacturer, model, max_current_a, voltage_min/max, compatible_prop_ids, operating_points, source_url, part_number, identity_status, source_note` — **zero geometry fields**, confirmed by full read. | `library.py:36-66` |
| Loader | `_motor_from_raw` parses each optional field with the same `float(data["x"]) if data.get("x") is not None else None` convention this axis already uses for battery/frame fields | `library.py:295-337` |
| Seed rows | 20 total motors in `library/motores/_datos.json`. **Exactly 2** have `source_url`+`identity_status: "verified"`: `emax_rs2205s_2300`, `sunnysky_r2205_2500`. The other 18 (including the differently-named, unsourced `emax_rs2205_2300` — note the missing trailing "s," a **different** row than the sourced `emax_rs2205s_2300`) have no citable page — confirmed by scripted scan of the whole file. | `library/motores/_datos.json` |
| `bind_motor_from_catalog` today | Signature is `bind_motor_from_catalog(suggestion: MotorSuggestion, *, base=None)` — **no `sku`/`library` parameter**, unlike Battery/Propeller/ESC's `bind_*_from_catalog(sku: str, *, library=None, base=None)`. It builds `ComponentSpec.properties` entirely from the `MotorSuggestion` dict's own keys (`thrust_n`, `kv_rating`, `weight_g`, `max_watts`) — it never calls `ComponentLibrary.get_motor()` at all. | `catalog_bind.py:24-79` |
| `MotorSuggestion` shape | `TypedDict` with `idx, name, thrust_n, kv_rating, weight_g, max_watts, is_generic` — a lightweight ranked-candidate summary for the assisted-pick UX, built from library scans (`find_motors_for_requirements`), not the full catalog record. **No dims field, and no reason to add one here** (see below). | `motor_catalog_assist.py:14-23` |
| Board | Confirmed by the same generic mechanism proven for Battery: `spatial_board.py:181-189`'s `_fields()` iterates `spec.properties.items()` with no per-family branching — any new named property on a bound motor's `ComponentSpec` renders automatically, zero Board code needed. | `spatial_board.py:181-202` |
| Battery B1 pattern reused vs diverged | **Reused:** sourced-only provenance rule, `PropertyValue(unit="mm", confidence=0.9, source="declared")` shape, zero Board change. **Diverged:** cylinder vocabulary (`stator_diameter_mm`/`diameter_mm`), not box (`length_mm`/`width_mm`) — per locked stance #5/#6, Battery's shape was never a mandate to reuse verbatim. **Diverged again:** the bind function itself needs a small signature change (add `library` param), since Motor's bind — unlike the other three — never had a `sku`/`library` entry point to begin with. | — |

---

## C. Minimum motor geometric bag

**Accept/reject each candidate field, against the two live-fetched sources:**

| Field | EMAX RS2205S states | SunnySky R2205 states | Verdict |
|---|---|---|---|
| `stator_diameter_mm` | "Stator Diameter: 22mm" | "Stator Diameter: 22mm" | **Accept** — both agree, unambiguous, matches the "2205" naming convention itself |
| `stator_height_mm` | "Stator Height: 5mm" | "Stator Thickness: 5mm" | **Accept** — different label, same physical quantity (both agree 5mm, and both explicitly call it the stator's own dimension, not the body's) |
| `diameter_mm` (overall) | "Motor Diameter: 27.9mm" | "Rotor Diameter: 27.4mm" | **Accept, with per-row label kept in `source_note`** — both plausibly measure the same feature (the widest point of an outrunner's rotor bell, which *is* "the motor's diameter" for mounting/prop-clearance purposes), but the label difference is real and must stay visible, not silently unified into one implied-universal term (Frame Assembly plate-role precedent) |
| **`height_mm` (overall axial)** | "Motor Height: 31.7mm" (page separately states a "15mm Extended Prop Shaft") | "Body Length: 18mm" (no shaft mentioned) | **Reject for this increment.** 31.7mm vs 18mm for the *same stator class* is not measurement noise — it's two different physical facts (one shaft-inclusive, one not) wearing the same candidate field name. Adding `height_mm` today would either silently favor one convention or require a disambiguating label field neither Battery nor this contract's own field-name list anticipated. Naming this as a real open question for a future increment, not deciding it here. |
| `shaft_diameter_mm` | "Shaft Diameter: 3mm" | not stated | **Accept, sourced-only** — not "shaft-only" (the contract's own rejected shape): it rides alongside the stator+overall-diameter envelope above, present only for the one row that states it, exactly the same asymmetric-coverage pattern Battery already established (`lipo_6s_6000mah` has no shaft-analog field either, and that was fine). |
| `length_mm` / `width_mm` (Battery-style box) | n/a | n/a | **Reject** — an outrunner motor is radially symmetric; a box envelope has no meaning here, confirmed by neither source stating one. Exactly the divergence locked stance #5 anticipated. |

**Proposed bag:** `stator_diameter_mm`, `stator_height_mm`, `diameter_mm`, `shaft_diameter_mm` (asymmetric — 3/4 fields both rows can seed, the 4th only EMAX). No new type; four more optional `float | None` fields on `MotorSpec`, exactly mirroring how Battery's three were added.

---

## D. Seedable SKUs + live source quotes

Both re-fetched live this session, not reused from the Battery investigation's passing mention:

| SKU | Source | Quoted values |
|---|---|---|
| `emax_rs2205s_2300` | `shop.emaxmodel.com/products/emax-rs2205-racespec-motor-cooling-series` | "Stator Diameter: 22mm" · "Stator Height: 5mm" · "Shaft Diameter: 3mm" · "Motor Diameter: 27.9mm" · "Motor Height: 31.7mm" (**not seeded — see §C**) · "Approx. 30g with wires" |
| `sunnysky_r2205_2500` | `sunnyskyusa.com/products/sunnysky-r2205-brushless-motors` | "Stator Diameter: 22mm" · "Stator Thickness: 5mm" · "Rotor Diameter: 27.4mm" · "Body Length: 18mm" (**not seeded — see §C**) · "Weight: 31g" |

Proposed seed values (this report's recommendation, not yet written to any file):

| SKU | `stator_diameter_mm` | `stator_height_mm` | `diameter_mm` | `shaft_diameter_mm` |
|---|---|---|---|---|
| `emax_rs2205s_2300` | 22 | 5 | 27.9 | 3 |
| `sunnysky_r2205_2500` | 22 | 5 | 27.4 | — (omit, not stated) |

Every other motor row (18 of 20, including the unsourced `emax_rs2205_2300` — the different, non-"S" row) omits all four fields — no `source_url`, nothing to cite, nothing invented.

**Binding path (governing question 3, answered):** the suggestion dict is the wrong place to carry dims — it's a ranked-candidate summary, not the catalog record, and widening its `TypedDict` would touch every construction call site in `motor_catalog_assist.py` for a fact those call sites don't need (thrust/kv/weight ranking doesn't care about stator size). The smallest honest path is the one Battery/Propeller/ESC already use: give `bind_motor_from_catalog` an optional `library: ComponentLibrary | None = None` parameter, and inside the function do `lib = library or default_library; spec = lib.get_motor(sku)` (where `sku` is already computed at `catalog_bind.py:41` from `suggestion["name"]`) to read the four new fields and project them exactly like Battery's `if spec.length_mm is not None: ...` pattern. A future IC would need to decide how to handle a `sku` not present in the library (defensive `try/except KeyError`, or trust that every `MotorSuggestion.name` is always a real catalog key, which today's ranking code guarantees) — flagged as an implementation detail, not decided here.

---

## E. Honesty / ladder matrix

| Implication | True if we add the proposed fields? | Over-claim risk | Desired wording |
|---|---|---|---|
| "We know the motor's size" | **Partially, honestly.** True for stator size and overall diameter on the 2 sourced rows — the same epistemic status as `thrust_n`/`weight_g` today. **Not** true for overall axial length — deliberately excluded because the two real sources disagree on what "size" even means there (§C). | Low, provided the excluded field stays excluded rather than guessed at. | "Stator y diámetro exterior declarados (fuente: catálogo)" — never claim a complete envelope. |
| "Fits the arm mount" | **No.** No comparison against `frame_arm`/`wheelbase_mm`/mount-hole spacing is proposed or implied. Nothing in this bag states a bolt pattern at all — neither source even publishes one (confirmed, both pages checked, "not specified"). | High if ever implied — this is the exact `representar → verificar` jump the parent lock forbids. | Never emit a fit/mount sentence from these fields; that would need its own future Buy with its own evidence (bolt-pattern sources neither page has today). |
| "Board preview = CAD" | **No.** Same as Battery — text rows on an existing card type, no shape drawn. | Medium if marketed loosely. | Keep Board copy scoped to "declared component data." |
| "Prop diameter related" | **No relationship implied or computed.** `compatible_prop_inch` (existing field) already states compatibility declaratively; the new `diameter_mm` is the *motor's own* width, not a prop-clearance calculation. | Low, as long as no sentence pairs `diameter_mm` with `compatible_prop_inch` as if one derives the other. | Keep the two fields displayed independently, as today's `_fields()` already does for every property. |
| "Visualization verifies" | **N/A — no visualization proposed**, same non-goal as Battery B1. | Low. | First IC's done-criteria should stop at "field parses, projects, displays as text," identical to Battery's. |

**Ladder position:** rung 2, **`representar`** only — same rung as Battery B1, not a step further.

---

## F. Buy options + default lean

| Option | What | When to Buy |
|---|---|---|
| B0 | Docs/vocab lock only (name the 4 fields, no code) | If Engineer wants to ★ the field names before any code — reasonable given the `height_mm` exclusion is itself a judgment call worth confirming |
| **B1** | **Schema (4 optional fields on `MotorSpec`) + seed the 2 sourced rows + `bind_motor_from_catalog` gains `library` param + Board shows via existing generic path** | **Recommended — see below** |
| B2 | Motor + ESC in the same IC | Rejected as first slice, same reasoning as the Battery investigation's rejection of bundling families — ESC's own dims (verified live in the Battery investigation: Hobbywing XRotor "42.0x21.6x12.0mm") are a *box*, not a cylinder, and deserve their own source-verification pass, not a bundled afterthought |
| B3 | Glyph/cylinder preview | Not now — `visualizar`, premature before Motor's own numbers exist |
| Defer | — | Not applicable — 2 real sourced rows exist today, evidence is sufficient, the one hard question (overall height ambiguity) has a clean resolution (exclude it) rather than blocking the whole increment |

### Default lean: **B1, Motor only, four fields as scoped in §C**

Smallest safe scope: one dataclass (`MotorSpec`), four optional fields (one — `shaft_diameter_mm` — sourced on only 1 of 2 rows, same asymmetric-coverage precedent as Battery), one signature change to `bind_motor_from_catalog` (add `library` param, mirroring the other three binds), zero `MotorSuggestion`/`motor_catalog_assist.py` changes, zero Board changes. Slightly larger than Battery B1 (which needed no bind-signature change) but still the smallest coherent unit — and it deliberately does **not** include the field that would have been the most tempting direct copy from Battery (`height_mm`), because the evidence this session refutes it rather than confirms it.

**Suggested first IC title (for Cursor, not decided here):** *"Motor declared envelope (stator + overall diameter + shaft) — representar only."*

---

## G. Non-goals for the first Motor IC

Fit/clearance/arm-mount validation · CAD/FEA · Board glyph/cylinder preview · Battery/Frame/ESC dims (ESC named as a reasonable **second** family, not bundled here) · free-text motor-dimension extractors in `aerial.py` · overall axial `height_mm`/`length_mm` (excluded on evidence, §C — not an oversight; a future IC could revisit it only with a labeling convention that survives the EMAX-vs-SunnySky disagreement) · widening `MotorSuggestion`/touching `motor_catalog_assist.py` · mounting-hole/bolt-pattern fields (neither source states one) · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · inventing dims for any of the 18 unsourced motor rows · weakening tests.
