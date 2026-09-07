# Investigation Contract — ESC declared envelope (Geometry axis, next family)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_esc_envelope.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 (+N3) → IC READY  
**Report:** [investigation_report_geometry_esc_envelope.md](investigation_report_geometry_esc_envelope.md)  
**Review:** [investigation_review_geometry_esc_envelope.md](investigation_review_geometry_esc_envelope.md)  
**IC:** [implementation_contract_geometry_esc_envelope_b1.md](implementation_contract_geometry_esc_envelope_b1.md)  
**Parents (mandatory):**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [implementation_review_geometry_battery_envelope_b1.md](implementation_review_geometry_battery_envelope_b1.md) — Battery box L×W×H PASS @ **2316**
- [implementation_review_geometry_motor_envelope_b1.md](implementation_review_geometry_motor_envelope_b1.md) — Motor stator/Ø/shaft PASS @ **2323**
- Geometry ladder: `KNOW → representar → visualizar → comparar → verificar`

**Type:** Schema / provenance / first-increment investigation for **ESC** family.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · Motor B1 CLOSED suite **2323**

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy shape before any IC (default intent: **B1 ESC box envelope**, representar only — confirm or re-scope with evidence).

**Do not implement. Do not bump version. Do not weaken tests. Do not open MEASURE fit/clearance/FEA/CAD. Do not add Board glyphs. Do not touch Battery/Motor schema. Do not open Frame envelope. Do not invent Conversation Engine. Do not claim visualization ≡ verification.**

---

## 0. Role split (do not invert)

```text
Engineer  → named ESC as next Geometry Buy; procede
Cursor    → this contract; review report; IC only after ★ on Buy shape
Claude    → investigation_report_geometry_esc_envelope.md
Cursor    → investigation review
Engineer ★ → Buy B1 / defer / re-scope
```

---

## 1. Why this investigation exists

Battery (box) and Motor (cylinder) proved the Geometry pattern at rung **`representar`**. ESC is the natural next family: typically a **box** footprint (same vocabulary as Battery: `length_mm` / `width_mm` / `height_mm`), thin catalog today, already flagged in the Battery investigation as a live candidate (Hobbywing XRotor dims mentioned — **re-verify live**, do not rubber-stamp).

Wrong next step:

```text
copy Battery fields blindly · invent mm · bundle FC/stack · claim ESC fits frame
```

Right question:

> What is the **minimum real, reusable geometric bag** for a catalog **ESC** so it represents a physical object — which fields, which SKUs can be seeded today from cited pages, and what is the smallest Buy?

---

## 2. Locked stances (inherit)

1. Geometry axis active; Structure sufficient; Prop/Energy = HD-004; Optimization deferred.
2. Ladder stays at **`representar`** for this Buy.
3. Provenance: only when the row’s own `source_url` states the dim; never invent; never copy from a sibling SKU.
4. Prefer **shared box vocabulary** with Battery (`length_mm` / `width_mm` / `height_mm`) if sources support it — do **not** invent a parallel ESC-only naming without evidence.
5. Axis mapping: same discipline as Battery — labeled axes when present; else verbatim `A×B×C` order + quote in `source_note`.
6. No fit vs stack/frame; no Structure PASS change; no glyph.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `EscSpec` | Confirm **no** envelope fields today (`library.py`) |
| `library/esc/_datos.json` | Row count; which have `source_url` / `identity_status` |
| `bind_esc_from_catalog` | Signature (SKU + library — likely Battery-shaped); docstring honesty |
| Board | Freeform ESC vs catalog-bound ESC in live projects — what card exists today |
| Battery/Motor precedent | Reuse vs diverge |

**Known starting point (re-verify):** catalog currently has a thin ESC seed (expect on the order of **1** verified row — confirm exact N). Hobbywing page may publish multiple size variants — quote live and decide which numbers apply to **this** SKU only.

---

## 4. Governing questions the report must answer

### Know

1. As-is ESC geometry (or absence) in schema, seed, bind, Board.
2. How many ESC rows are honestly seedable **today** (live-fetched dims from each row’s own `source_url`)?
3. Binding path: confirm `bind_esc_from_catalog(sku, *, library=…)` can project dims like Battery (no `MotorSuggestion`-style complication) — or name any gap.

### Claim — minimum ESC object model

4. Field bag: accept/reject `length_mm` / `width_mm` / `height_mm` (and any other candidate) with evidence.
5. First seed set: SKU(s), exact numbers, mapping rule, `source_note` quotes.
6. Explicit outs (4-in-1 vs individual topology, stack height confusion, FC footprint, free-text, etc.).

### Honesty / ladder

7. Phrase matrix: “we know ESC size,” “fits the stack,” “Board = CAD,” “same as battery box,” “visualization verifies.”
8. Ladder rung of recommended Buy.

### Buy shape

9. Rank B0 / **B1** / B2 (ESC+FC) / B3 glyph / Defer.  
10. **Default lean** (required).

---

## 5. Out of scope

Fit/clearance · CAD/FEA · Board glyph · Battery/Motor/Frame schema edits · FC / stack 30.5 as this IC · free-text ESC mm extractors · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · inventing dims · weakening tests

---

## 6. Deliverable format

Write `.jes/artifacts/investigation_report_geometry_esc_envelope.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is inventory + bind path  
- **C.** Minimum ESC geometric bag  
- **D.** Seedable SKUs + live source quotes  
- **E.** Honesty / ladder matrix  
- **F.** Buy options + **default lean**  
- **G.** Non-goals for the first ESC IC  

No code. No version bump. No test changes.

---

## 7. Success criterion

Engineer can ★ **Buy B1** (or B0 / Defer / re-scope) without ambiguity — and without licensing fit/CAD theater.
