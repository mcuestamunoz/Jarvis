# Investigation Contract — Motor declared envelope (Geometry axis, next family)

**Project:** Jarvis  
**Date:** 2026-09-06  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_motor_envelope.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Report:** [investigation_report_geometry_motor_envelope.md](investigation_report_geometry_motor_envelope.md)  
**Review:** [investigation_review_geometry_motor_envelope.md](investigation_review_geometry_motor_envelope.md)  
**IC:** [implementation_contract_geometry_motor_envelope_b1.md](implementation_contract_geometry_motor_envelope_b1.md)  
**Parents (mandatory):**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [investigation_review_geometry_minimum_physical_object.md](investigation_review_geometry_minimum_physical_object.md) — Battery B1 lean
- [implementation_review_geometry_battery_envelope_b1.md](implementation_review_geometry_battery_envelope_b1.md) — **PASS** @ suite **2316**
- Board smoke (2026-09-06): project `autonomía-de-10min` battery card shows `length_mm`/`width_mm`/`height_mm` after rebind to `lipo_4s_1500mah` — **ACCEPT** field for Geometry B1

**Type:** Schema / provenance / first-increment investigation for **Motor** family.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · Geometry Battery B1 CLOSED suite **2316** · Board smoke ACCEPT

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not open MEASURE fit/clearance/FEA/CAD import/meshes. Do not add Board glyphs. Do not touch Battery schema. Do not open Frame envelope. Do not invent Conversation Engine. Do not claim visualization ≡ verification.**

---

## 0. Role split (do not invert)

```text
Engineer  → named Motor as next Geometry family after Battery smoke
Cursor    → this contract; review report; IC only after ★ Buy
Claude    → investigation_report_geometry_motor_envelope.md
Cursor    → investigation review
Engineer ★ → Buy / defer / re-scope
```

---

## 1. Why this investigation exists

Battery B1 proved the Geometry pattern:

```text
optional dims on *Spec → catalog seed (sourced only) → bind_* → Board text via generic _fields
```

Ladder position remains **`representar` only**. Next family named by Engineer: **Motor**.

Wrong next step (forbidden):

```text
copy Battery L×W×H onto Motor · invent mm for unsourced SKUs · draw a cylinder · claim “fits the arm”
```

Right question:

> What is the **minimum real, reusable geometric bag** for a catalog **motor** so it represents a physical object (same honesty as Battery B1) — which fields, which SKUs can be seeded today, and what is the smallest Buy?

---

## 2. Locked stances (inherit)

1. Geometry axis active; Structure sufficient; Prop/Energy = HD-004; Optimization deferred.
2. Ladder: `KNOW → representar → visualizar → comparar → verificar` — this Buy stays at **representar**.
3. Provenance: field set **only** when the row’s cited `source_url` states it; never invent; never derive from sibling SKU.
4. Board authority unchanged (`state.json` truth; projector read-only).
5. Battery pattern is **precedent**, not a mandate to reuse L×W×H if Motor’s natural shape is cylinder (`diameter_mm` + `height_mm`).
6. Propeller keeps `diameter_in` / `pitch_in` — do not migrate.
7. No fit vs frame/arm; no Structure PASS footnote change.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `MotorSpec` | Fields today (`library.py`) — confirm **no** envelope dims |
| `library/motores/_datos.json` | Which rows have `source_url` / `identity_status`? Quote pages live for candidate dims |
| `bind_motor_from_catalog` | What it projects today; how dims would attach (note: takes `MotorSuggestion`, not raw `MotorSpec` — map the path honestly) |
| Board | Confirm motor cards already show generic properties (live project uses `emax_rs2205_2300`) |
| Battery B1 | Diff pattern to reuse vs diverge (box vs cylinder vocabulary) |

**Known hint from Battery investigation (re-verify, do not rubber-stamp):** EMAX RS2205 page may state stator Ø, stator height, shaft Ø, overall motor Ø/height — treat as evidence to **confirm or refute** for seeding, and check whether **other** sourced motor rows also publish usable dims.

---

## 4. Governing questions the report must answer

### Know

1. As-is motor geometry (or absence) in schema, seed, bind, Board.
2. How many motor rows are honestly seedable **today** (live-fetched dims from each row’s own `source_url`)?
3. Binding path: does `bind_motor_from_catalog(MotorSuggestion)` need to read `ComponentLibrary.get_motor(sku)` for dims, or can suggestion dict carry them? Smallest honest path.

### Claim — minimum motor object model

4. Propose the field bag (name, units, optionality). Candidates to evaluate (accept/reject with evidence):

| Field | Likely use |
|---|---|
| `diameter_mm` | overall can / bell Ø |
| `height_mm` | overall axial height |
| `stator_diameter_mm` / `stator_height_mm` | manufacturer “2205”-style |
| `shaft_diameter_mm` | shaft |
| Battery-style `length_mm`/`width_mm` | usually **wrong** for outrunners |

Prefer the **smallest** bag that still means “physical object” on the Board. Explicitly reject attribute drip (e.g. shaft-only without envelope).

5. First seed set: which SKUs, exact numbers, mapping rule (labeled vs unordered).
6. Explicit outs for this increment.

### Honesty / ladder

7. Phrase matrix (required): “we know motor size,” “fits the arm mount,” “Board preview = CAD,” “prop diameter related,” “visualization verifies.”
8. Ladder rung of recommended Buy (`representar` only vs premature `visualizar`).

### Buy shape

9. Rank:

| Option | What |
|---|---|
| **B0** | Docs/vocab lock only |
| **B1** | Schema + seed sourced motors + bind → Board text |
| **B2** | Motor + ESC same IC |
| **B3** | Glyph/cylinder preview |
| **Defer** | Insufficient sourced dims |

10. **Default lean** (required): one recommendation + smallest safe scope + non-goals.

---

## 5. Out of scope

Fit/clearance · arm↔motor mount validation · CAD/FEA · Board glyph · Battery/Frame/ESC dims in this IC · free-text motor mm extractors · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · inventing dims · weakening tests

---

## 6. Deliverable format

Write `.jes/artifacts/investigation_report_geometry_motor_envelope.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is inventory + bind-path analysis  
- **C.** Minimum motor geometric bag  
- **D.** Seedable SKUs + live source quotes  
- **E.** Honesty / ladder matrix  
- **F.** Buy options + **default lean**  
- **G.** Non-goals for the first Motor IC  

No code. No version bump. No test changes.

---

## 7. Success criterion

Engineer can ★ **Buy B0/B1/B2/B3**, **Defer**, or **re-scope** without ambiguity — and without licensing fit/CAD theater.
