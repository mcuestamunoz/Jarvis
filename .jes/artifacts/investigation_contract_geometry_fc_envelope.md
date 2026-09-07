# Investigation Contract — Flight Controller declared geometry (Geometry axis)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_fc_envelope.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Report:** [investigation_report_geometry_fc_envelope.md](investigation_report_geometry_fc_envelope.md)  
**Review:** [investigation_review_geometry_fc_envelope.md](investigation_review_geometry_fc_envelope.md)  
**IC:** [implementation_contract_geometry_fc_envelope_b1.md](implementation_contract_geometry_fc_envelope_b1.md)  
**Parents (mandatory):**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [implementation_review_geometry_esc_envelope_b1.md](implementation_review_geometry_esc_envelope_b1.md) — ESC box B1 PASS @ **2327** (explicitly deferred FC/stack)
- [investigation_report_geometry_esc_envelope.md](investigation_report_geometry_esc_envelope.md) — named FC/stack 30.5 as a **different geometric idea**
- Board live (2026-09-07): project `autonomía-de-10min` shows motors/ESC/battery mm; **flight_controller** card = Pixhawk 4 `model` only — **no dims**
- Geometry ladder: `KNOW → representar → visualizar → comparar → verificar`

**Type:** Schema / provenance / first-increment investigation for **Flight Controller** (and adjacent stack-mount vocabulary if evidence supports it).  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · ESC B1 CLOSED suite **2327** · Board smoke Battery+Motor+ESC ACCEPT

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy shape before any IC (default intent: **smallest honest FC representar Buy** — confirm or re-scope with evidence; may conclude **Defer** or **foundation-first** if catalog absence blocks a Battery-shaped slice).

**Do not implement. Do not bump version. Do not weaken tests. Do not open MEASURE fit/clearance/FEA/CAD. Do not add Board glyphs. Do not touch Battery/Motor/ESC schema. Do not open Frame envelope. Do not invent Conversation Engine. Do not claim visualization ≡ verification. Do not invent a full FC catalog foundation as a side-quest unless the report proves it is the *minimum* path to any honest FC geometry.**

---

## 0. Role split (do not invert)

```text
Engineer  → named FC as next Geometry focus after Board smoke (empty FC card)
Cursor    → this contract; review report; IC only after ★ on Buy shape
Claude    → investigation_report_geometry_fc_envelope.md
Cursor    → investigation review
Engineer ★ → Buy B1 / B0 foundation / Defer / re-scope
```

---

## 1. Why this investigation exists

Battery (box), Motor (cylinder/stator), ESC (box) proved catalog→bind→Board **representar**. The live Board still shows:

```text
flight_controller · Pixhawk 4 · model only
```

ESC investigation correctly **refused** to bundle FC/stack: 30.5 mm mount spacing is a different geometric claim than an ESC box. Engineer now asks for that next idea — on purpose.

Wrong next step:

```text
copy Battery L×W×H onto Pixhawk free-text · invent 30.5 · claim “fits stack” ·
spin up library/fc/ + Continuity wizard + glyph in one IC
```

Right question:

> What is the **minimum real, reusable geometric bag** for a **flight controller** (and only if evidence forces it: stack mount pattern) so the Board card stops being identity-only — **given that Jarvis today has no FC catalog family** — and what is the smallest Buy that stays honest?

---

## 2. Locked stances (inherit)

1. Geometry axis active; Structure sufficient; Prop/Energy = HD-004; Optimization deferred.
2. Ladder stays at **`representar`** for any recommended Buy from this report.
3. Provenance: only dims the chosen identity’s own cited source states; never invent; never copy from a sibling model string.
4. **Do not** pretend FC is already Battery-shaped: there is **no** `library/fc/` (or equivalent) in the live tree today — re-verify and treat that as a governing fact, not a footnote.
5. Mount pattern ≠ box envelope ≠ “stack height” clearance. Keep vocabularies separate unless one source defines them together for one SKU.
6. No fit vs frame/ESC; no Structure PASS change; no glyph; no comparar/verificar.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| Catalog | Confirm absence (or surprising presence) of FC/flight-controller family under `library/`, `*Spec`, `ComponentLibrary.get_*` |
| Free-text FC | `FLIGHT_CONTROLLER_MAP` / `extract_flight_controller_properties` / `_flight_controller_completeness` — what properties exist today (expect `model` only) |
| Bind | Confirm **no** `bind_flight_controller_from_catalog` (or equivalent); how does FC enter `components` today? |
| Board | Live freeform FC card fields for Pixhawk-class projects; what would new keys look like via generic `_fields` |
| Precedents | Battery/Motor/ESC optional-field → bind → Board path vs Structure free-text scalar path (`wheelbase_mm`, thickness) — which pattern can FC honestly reuse **without** inventing a catalog? |
| Sources | For at least one concrete identity the product already recognizes (e.g. Pixhawk 4 / Pixhawk 4 Mini — quote live manufacturer pages): which numbers exist (body L×W×H, mount hole spacing, weight), and which are ambiguous across Mini vs full / FMU vs carrier |

**Known starting point (re-verify, do not rubber-stamp):**
- `library/` today: baterias, motores, esc, frames, helices, materiales — **no FC folder**.
- Board smoke project shows `flight_controller` with `model: pixhawk_4` only.
- Aerial comment historically rejects bare-mm “stack height” false positives — cite if still true.

---

## 4. Governing questions the report must answer

### Know

1. As-is FC geometry (or absence) in schema, catalog, bind, free-text, Board.
2. Is there **any** honest seed path today without inventing a new catalog family? If not, what is the *minimum* foundation slice (one SKU file? properties-only on free-text? defer)?
3. For Pixhawk 4 (and Mini if needed for disambiguation): live-fetched dims + mount numbers from each product’s own page — exact quotes, mapping, collisions.

### Claim — minimum FC object model

4. Field bag: accept/reject candidates with evidence, e.g.:
   - box: `length_mm` / `width_mm` / `height_mm`
   - mount: `mount_pattern_mm` or pair `mount_spacing_x_mm` / `mount_spacing_y_mm` (30.5-class)
   - other: hole Ø, standoff assumptions — only if sourced
5. Explicit outs: stack height as clearance, “fits 30.5 frame”, 4-in-1 ESC confusion, carrier vs FMU board, free-text mm extractor, Continuity FC catalog wizard.
6. Identity rule: free-text `model` string vs future catalog SKU — what can B1 claim without lying.

### Honesty / ladder

7. Phrase matrix: “we know FC size,” “30.5 stack,” “fits the frame,” “Board = CAD,” “same as battery box,” “visualization verifies.”
8. Ladder rung of recommended Buy.

### Buy shape

9. Rank at least:
   - **B0** — foundation only (tiny FC catalog or equivalent bind path) **without** dims yet  
   - **B1** — first declared geometry on one disambiguated identity (box and/or mount — report must choose)  
   - **B2** — box + mount + wizard / multi-SKU drip  
   - **B3** — Board glyph  
   - **Defer** — evidence insufficient or foundation too large for Geometry axis now  
10. **Default lean** (required) — one line Engineer can ★.

---

## 5. Out of scope

Fit/clearance · CAD/FEA · Board glyph · Battery/Motor/ESC/Frame schema edits · free-text FC-mm extractors as default · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · inventing dims · weakening tests · bundling “visualizar” · claiming FC dims unlock Structure PASS

---

## 6. Deliverable format

Write `.jes/artifacts/investigation_report_geometry_fc_envelope.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is inventory (catalog absence is first-class)  
- **C.** Minimum FC geometric bag (+ foundation path if required)  
- **D.** Source quotes for concrete Pixhawk-class identity(ies)  
- **E.** Honesty / ladder matrix  
- **F.** Buy options + **default lean**  
- **G.** Non-goals for the first FC IC  

No code. No version bump. No test changes.

---

## 7. Success criterion

Engineer can ★ **Buy B0 / B1 / Defer / re-scope** without ambiguity — knowing whether FC needs a catalog foundation before any mm, and without licensing fit/CAD theater.
