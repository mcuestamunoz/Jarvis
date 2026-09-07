# Investigation Contract — Minimum Sensor KNOW for Aerial Autonomy Claim

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer (Component Validation Lead stance) — adopted verbatim as locked framing  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_minimum_sensor_know_aerial_autonomy_claim.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy claim-copy → IC READY  
**Report:** [investigation_report_minimum_sensor_know_aerial_autonomy_claim.md](investigation_report_minimum_sensor_know_aerial_autonomy_claim.md)  
**Review:** [investigation_review_minimum_sensor_know_aerial_autonomy_claim.md](investigation_review_minimum_sensor_know_aerial_autonomy_claim.md)  
**IC:** [implementation_contract_sensors_bom_honesty_tail_b1.md](implementation_contract_sensors_bom_honesty_tail_b1.md)  
**Parents (mandatory):**
- [implementation_review_control_parity.md](implementation_review_control_parity.md) — Control PASS * = declaration only; sensors declarative asymmetry
- [implementation_contract_control_parity.md](implementation_contract_control_parity.md) — footnote * Control: declaración — sin física de control
- [engineer_lock_prop_energy_evidence_wall.md](engineer_lock_prop_energy_evidence_wall.md) — energetic autonomy wall (HD-004); **orthogonal** to this investigation’s navigational claims
- [implementation_review_geometry_fc_envelope_b1.md](implementation_review_geometry_fc_envelope_b1.md) — Pixhawk 4 identity-linked box CLOSED @ **2332** (geometry ≠ autonomy claim)
- Live Board / ERF: `control` closes with FC + sensors (e.g. Pixhawk 4 + Here3) while PROJECT STATUS may remain **NOT ASSEMBLY READY** — correct; do not collapse

**Type:** Claim-honesty / minimum KNOW investigation for **aerial control + sensing** relative to autonomy-capable language.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · Geometry FC B1 CLOSED suite **2332** · Control parity CLOSED suite **2164**

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy / Defer / re-scope before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not open `library/sensors/` or FC/sensor catalogs. Do not open CAD/FEA/fit. Do not add Board glyphs. Do not change Control PASS semantics in code. Do not invent Conversation Engine. Do not equate energetic autonomy (~N min) with navigational/operational autonomy. Do not decide a final schema — evidence and claim ladders first; schema sketches are illustrative only.**

---

## 0. Role split (do not invert)

```text
Engineer  → formulated claim ladder + opened this investigation;
            later ★ Buy; Component Validation Lead validates KNOW vs datasheet
Cursor    → this contract; review report; IC only after ★
Claude    → investigation_report_minimum_sensor_know_aerial_autonomy_claim.md
Cursor    → investigation review
Engineer ★ → Buy shape / Defer / re-scope (no accidental Autonomous PASS)
```

---

## 1. Why this investigation exists

Jarvis today treats the architecture block `control` as:

```text
flight_controller
+
sensors
```

and can close it with e.g. **Pixhawk 4 + Here3**. That proves the block is **declared**. It does **not** prove autonomous flight capability.

Live honesty already shows the right coexistence:

```text
Control = PASS *
PROJECT STATUS: NOT ASSEMBLY READY
```

Control PASS must **not** become Autonomous PASS by enriching the `sensors` model.

Wrong next step:

```text
add sensor fields → raise completeness → imply “autonomous drone” ·
open library/sensors/ · drip Here3 mm as if that answered autonomy ·
merge energy autonomy and navigation autonomy into one PASS
```

Right question (locked):

> **What minimum knowledge must Jarvis hold about the control/sensor system to honestly distinguish “control declared”, “potential navigation capability”, and “demonstrated autonomous flight”?**

---

## 2. Locked claim ladder (do not flatten)

```text
CONTROL DECLARED
  Pixhawk + some sensor/GNSS declared
        ↓
NAVIGATION-CAPABLE KNOW
  the elements required for a given navigation modality are known
        ↓
AUTONOMOUS FLIGHT CLAIM
  sufficient evidence that the system can execute that flight modality
```

| Level | Means | Must not mean |
|---|---|---|
| CONTROL DECLARED | Architecture/control block can close; identity present | Navigation or autonomy demonstrated |
| NAVIGATION-CAPABLE KNOW | Required sensing/actuation path for a **named modality** is known as KNOW | That modality has been flown / verified |
| AUTONOMOUS FLIGHT CLAIM | Evidence sufficient for that modality | Automatic promotion from Control PASS or GNSS presence |

**Hard lock:** improving the `sensors` model must not accidentally convert `Control PASS` into an autonomous-flight PASS.

---

## 3. Locked stances (inherit + Engineer formulation)

1. **Control PASS * remains declaration-only** (control parity footnote). This investigation may *name* what higher claims would require; it does **not** license rewriting Control PASS into physics/autonomy.
2. **Energetic autonomy ≠ navigational/operational autonomy.** HD-004 / ~N min estimates stay a separate wall. Do not fold them into this ladder.
3. **Geometry (FC box, future Here3 dims) ≠ autonomy claim.** Representar envelopes stay orthogonal.
4. **No sensor catalog / no CAD** in this investigation’s Buy space. Sequence locked:

```text
INVESTIGATION
  → minimum KNOW
  → evidence requirements
  → decide what (if anything) deserves Catalog
  → component validation (datasheet)
  → only then implementation
```

5. **Minimum is claim + environment scoped** — not a universal “minimum sensors for any autonomy.”
6. **Schema sketches are optional illustrations only** — no implementation decision this cycle.

---

## 4. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| Architecture `control` | `BLOCK_TO_COMPONENTS` / how FC + sensors close the block |
| Completeness | `_flight_controller_completeness` vs `_sensor_completeness` (incl. sensors never/`rarely` `"high"`) |
| Control evidence / ERF | What `_control_evidence` (or equivalent) actually consumes; Control PASS * wording |
| BOM / closure | FC defined vs sensors declarative; ASSEMBLY READY independence |
| Free-text maps | `FLIGHT_CONTROLLER_MAP`, `GPS_MAP`, `SENSOR_TYPE_MAP` — what identities exist |
| Geometry FC B1 | What Pixhawk 4 now carries (model + box) — confirm it does **not** assert sensing suite |
| Energy autonomy | Where energetic claims live; keep named as orthogonal |

Also inventory **phrase risk**: CLI/ERF/BOM strings that a reader could hear as “autonomous capable” when only Control DECLARED is true.

---

## 5. Governing questions the report must answer

### Physical KNOW (manufacturer-facing; cite sources)

1. **What a Pixhawk-class FC (use Pixhawk 4 as the concrete identity already in product) actually contributes:** IMU, barometer, integrated magnetometer or not, external sensor interfaces — and what must **not** be duplicated as independent user-declared components when already internal.
2. **What a Here3-class external unit actually contributes:** GNSS, magnetometer (variant-specific), other declared functions — what is necessary for outdoor navigation KNOW vs optional extras.
3. Cross-check both against official/manufacturer pages this session (same provenance discipline as Geometry). Flag ambiguities (kit vs board-only, case variants, Here3 vs Here3+).

### Claim / minimum

4. For at least **one** primary modality — **Outdoor waypoint navigation** — what is the **minimum KNOW** bag (capabilities / presence facts, not schema) to reach **NAVIGATION-CAPABLE KNOW** without claiming AUTONOMOUS FLIGHT.
5. Name at least one contrasting modality (e.g. **Indoor position hold**) and state how its minimum KNOW **differs** — enough to prove “minimum is not universal”; full indoor design is out of scope.
6. What evidence would be required to climb from NAVIGATION-CAPABLE KNOW → **AUTONOMOUS FLIGHT CLAIM** for outdoor waypoint (high-level: flight log / mission flown / etc.) — without inventing a lab campaign or opening HD-* work now. If evidence is out of product reach, say **Defer that rung** explicitly.

### Representation (illustrative only)

7. Sketch **options** for how Jarvis might eventually hold this KNOW (e.g. internal_sensors under FC vs external_navigation_sensor capabilities) — rank trade-offs against today’s `flight_controller` + `sensors` cards. **Do not pick a schema Buy** unless Engineer later asks; default lean may be “claim ladder + honesty only” with schema deferred.

### Honesty

8. Phrase matrix for forbidden implications, including at least:

```text
Pixhawk + Here3  ≠  autonomous drone
GNSS present     ≠  waypoint flight demonstrated
Control PASS *   ≠  Autonomous PASS
Energy ~N min    ≠  navigational autonomy
Here3 dims       ≠  navigation capability
```

### Buy shape

9. Rank: **Defer all code** · **Claim-copy / honesty only** · **KNOW model investigation follow-up** · **Geometry Here3 dims** (orthogonal) · **Sensor catalog** (explicitly late) · other.  
10. **Default lean** (required) — prefer the smallest move that prevents claim collapse; do **not** recommend catalog or Autonomous PASS implementation.

---

## 6. Out of scope

Implementing schema · `library/sensors/` · Continuity sensor wizard · changing Control PASS verdict logic · Assembly Ready rewrite · Geometry drip on Here3 as substitute for this question · CAD/FEA · energetic autonomy model changes · Prop/Energy HD-004 unlock · System Optimization · Conversation Engine · version bump · inventing datasheet facts · weakening tests

---

## 7. Deliverable format

Write `.jes/artifacts/investigation_report_minimum_sensor_know_aerial_autonomy_claim.md` with:

- **A.** Executive answer (≤20 lines)  
- **B.** As-is Jarvis control/sensors / Control PASS * inventory  
- **C.** Pixhawk 4 contributed sensing (sourced)  
- **D.** Here3 contributed sensing (sourced)  
- **E.** Minimum KNOW by modality (outdoor waypoint primary; indoor contrast)  
- **F.** Evidence bar for AUTONOMOUS FLIGHT CLAIM (or explicit Defer of that rung)  
- **G.** Representation options (illustrative) + non-decision  
- **H.** Honesty / phrase matrix  
- **I.** Buy options + **default lean**  
- **J.** Non-goals for any first follow-on IC  

No code. No version bump. No test changes.

---

## 8. Success criterion

Engineer can ★ a Buy (or Defer) that:

1. keeps **CONTROL DECLARED** distinct from **NAVIGATION-CAPABLE KNOW** and **AUTONOMOUS FLIGHT CLAIM**;  
2. does not license Control → Autonomous promotion;  
3. separates energy autonomy from navigational autonomy;  
4. does not open sensor catalog/CAD prematurely;  
5. leaves Component Validation Lead a clear list of physical facts to verify against manufacturer sources before any schema IC.
