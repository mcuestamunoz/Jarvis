# Investigation Contract — Minimum Geometric KNOW for a Physical Catalog Object

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_minimum_physical_object.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Report:** [investigation_report_geometry_minimum_physical_object.md](investigation_report_geometry_minimum_physical_object.md)  
**Review:** [investigation_review_geometry_minimum_physical_object.md](investigation_review_geometry_minimum_physical_object.md)  
**IC:** [implementation_contract_geometry_battery_envelope_b1.md](implementation_contract_geometry_battery_envelope_b1.md)  
**Parent lock:** [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)

**Type:** Schema / provenance / first-increment investigation.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** tag **`v0.3.8`** / `checkpoint-spatial-board-projector` · Structure CLOSED suite **2294** · live tree B3 slots suite **2310**

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not open MEASURE fit/clearance/FEA/CAD import/meshes. Do not widen Structure PASS. Do not invent Conversation Engine. Do not turn the Board into a mutation surface. Do not claim visualization ≡ verification.**

---

## 0. Role split (do not invert)

```text
Engineer  → locked Geometry as next strategic axis; wants minimum object model first
Cursor    → this contract; review report; IC only after ★ Buy
Claude    → investigation_report_geometry_minimum_physical_object.md
Cursor    → investigation review
Engineer ★ → Buy / defer / re-scope
```

---

## 1. Why this investigation exists

Structure now KNOW-claims a composed frame (parts graph, plates, thickness). The Board shows those facts as cards. That is still **identity + scalar properties**, not a **physical object** the engineer can progressively enrich toward real build.

Wrong next step (forbidden as default Buy):

```text
add length_mm → add width_mm → add STL → claim “cabe” …
```

Attribute drip without a reusable object model — same failure mode Structure B rejected.

Right question:

> What is the **minimum real, reusable geometric information** so a catalog part stops being only identity+properties and starts representing a **physical object** — feedable into `state.json` / workspace and progressively shown on the Board — **without** jumping KNOW → VERIFICADO?

---

## 2. Locked stances (inherit)

1. **Hierarchy:** Structure sufficient · Prop/Energy = HD-004 wall · Optimization deferred · Geometry = next strategic axis.
2. **Ladder:** `KNOW → representar → visualizar → comparar → verificar`. This investigation covers **representar** (and may *name* what visualization would consume later). It does **not** Buy comparar/verificar.
3. **M0 unchanged:** root mass remains sole physics mass authority unless Engineer later overrides.
4. **Board authority:** `state.json` truth; projector read-only; CLI/writers mutate. Geometry fields on cards are **display of declared KNOW**, not layout-as-engineering.
5. **DESCRIPCIÓN ≠ VALIDACIÓN.** Declared envelope ≠ fit PASS ≠ Structure PASS widen.
6. **Sources must be real.** Prefer manufacturer datasheet / product page dims already published. Do not invent mm to fill schema.

---

## 3. Baseline to inventory (do not pretend greenfield)

Cite `file:line` on the live tree. Answer what **already exists** that is geometry-adjacent:

| Surface | What to check |
|---|---|
| Catalog specs | `FrameSpec.wheelbase_mm`, arm/plate `thickness_mm`, `PlateSeed`, motor/prop/battery fields — any L/W/H/Ø/footprint? |
| `PropertyValue` / `ComponentSpec` | Can arbitrary declared dims already live as properties without new schema? |
| Bind / free-text | What dims project today (`catalog_bind`, `aerial` extractors)? |
| Board projector | What fields surface on cards; what would opaque new keys look like? |
| Honesty | Structure PASS * footnote; ASSEMBLY READY; any claim that would become a lie if dims appear |

Also inventory **which component families** have public, simple, reusable dims (e.g. propeller diameter already; battery pack L×W×H often published; FC stack 30.5; motor stator/can Ø) vs which are hard (full frame plate outline).

---

## 4. Governing questions the report must answer

### Know — as-is

1. What geometric (or geometry-adjacent) fields does Jarvis **already** store or project, per component family?
2. Where is the hard line today between **identity** and **physical object** in code/docs?
3. What can the Board already show if we only filled more declared properties (no new viz)?

### Claim — minimum object model

4. Propose the **smallest reusable geometric bag** for “this catalog row is a physical object” (name fields, units, optionality, provenance). Prefer one shared shape over per-SKU one-offs.
5. Which **first component family** should carry that bag (simplest real SKUs, not the hardest frame)? Justify with source availability.
6. What is **explicitly out** of the first increment (mount holes, mesh, relative pose, fit rules, 3D viz widget)?

### Honesty / ladder

7. Phrase matrix (required):

| Implication | True if we add declared dims only? | Over-claim risk | Desired wording |

Cover at least: “we know the object’s size,” “it fits the frame,” “Board preview = CAD,” “Structure PASS includes geometry,” “visualization verifies.”

8. Map the proposal onto the ladder: which rung does the first Buy reach (`representar` only vs `visualizar` stub)?

### Buy shape

9. Rank options:

| Option | What | When to Buy |
|---|---|---|
| **B0** | Docs/claim lock only — no schema | … |
| **B1** | Schema + catalog seed for **one** simple family + Board shows fields | … |
| **B2** | Shared envelope type + N families | … |
| **B3** | Board geometric glyph/preview (2D) consuming declared envelope | … |
| **Defer** | Evidence insufficient / wrong axis timing | … |

10. **Default lean** (required): one recommended next Buy **or** explicit defer — with the smallest safe scope and non-goals.

---

## 5. Out of scope (do not evaluate as Buy)

- Fit / clearance / interference solvers  
- CAD file import, FEA, generative geometry  
- `mounts_on` as validation graph  
- Σ part mass → physics (M0)  
- Prop/Energy experimental unlock  
- System Optimization  
- Conversation Engine  
- Making Board a write surface for engineering fields  
- Implementing Spatial Board B3 (separate IC already ★’d) — may *cite* how geometry fields would appear on cards/slots

---

## 6. Deliverable format

Write `.jes/artifacts/investigation_report_geometry_minimum_physical_object.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is inventory (table + citations)  
- **C.** Minimum object model proposal  
- **D.** First family recommendation + source evidence  
- **E.** Honesty / ladder matrix  
- **F.** Buy options + **default lean**  
- **G.** Explicit non-goals for the first IC (if any)

No code. No version bump. No test changes.

---

## 7. Success criterion for this investigation

Engineer can ★ one of: **Buy B0/B1/B2/B3**, **Defer**, or **re-scope** — without ambiguity about what “geometry” means in the first increment, and without licensing fit/CAD theater.
