# Investigation Contract — Motor thrust is not an intrinsic property

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer — catalog hygiene: *cada número ↔ variante + condición*; cola 2 after ESC mass CLOSED  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_catalog_motor_thrust_not_intrinsic.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Report:** [investigation_report_catalog_motor_thrust_not_intrinsic.md](investigation_report_catalog_motor_thrust_not_intrinsic.md)  
**Review:** [investigation_review_catalog_motor_thrust_not_intrinsic.md](investigation_review_catalog_motor_thrust_not_intrinsic.md)  
**IC:** [implementation_contract_catalog_motor_thrust_not_intrinsic_b1.md](implementation_contract_catalog_motor_thrust_not_intrinsic_b1.md)  
**Parents (mandatory):**
- ESC mass hygiene B1 CLOSED — [implementation_review_catalog_esc_mass_hygiene_b1.md](implementation_review_catalog_esc_mass_hygiene_b1.md) @ suite **2344**
- [investigation_contract_catalog_esc_variant_coherence.md](investigation_contract_catalog_esc_variant_coherence.md) §8 (queued this investigation)
- Motor OP / dual-truth lineage: `resolve_operating_point`, fallback `operating_points[]`, DSE voltage coherence (do **not** re-litigate Phase 2.5 hover)
- Geometry Progression Lock — **do not** open pose / assembly / fit
- Engineer claim (locked framing): **10.042 N is not a property of the EMAX motor** — it is an operating point under propeller / voltage / test conditions

**Type:** Catalog / schema honesty investigation for **motor thrust semantics**.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · suite **2344**

**Single objective (locked):**

> Determine how Jarvis today treats top-level `MotorSpec.thrust_n` vs `operating_points[]`, whether the duplication of **10.042** on `emax_rs2205s_2300` (and siblings) misrepresents thrust as an intrinsic motor property, and what the **smallest defensible Buy** is so every thrust number is associated with the correct **condition** (propeller, voltage, evidence class) — without breaking bind / resolve / Board / feasibility.

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not open pose/`mounted_on`/fit/CAD/FEA. Do not touch ESC mass (CLOSED). Do not open Here3/Pixhawk variant. Do not invent new OP rows or “fix” thrust numbers without a cited condition. Do not remove `resolve_operating_point` or rewrite Phase 2.5 hover.**

---

## 0. Role split (do not invert)

```text
Engineer  → named cola 2; abre investigation
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_catalog_motor_thrust_not_intrinsic.md
Engineer ★ → Buy B0/B1/B2 / Defer / re-scope
```

---

## 1. Why this investigation exists

Catalog hygiene after ESC: the Board looks physically plausible, but engineering defensibility requires **condition association**.

Live smell (re-verify):

| Surface | Today |
|---|---|
| `emax_rs2205s_2300.thrust_n` | **10.042** — looks like a motor attribute |
| Same SKU `operating_points[]` fallback | **10.042**, `fallback_only: true`, note: RS2205 2300KV + **HQ5045 BN** + 4S = 1024 gf — **not propeller-independent** |
| `resolve_operating_point` | Prefer exact OP → fallback OP → else **legacy** bare `MotorSpec.thrust_n` |

Wrong next step:

```text
delete thrust_n blindly · break MotorSpec required field · invent new physics · open pose · retouch ESC · claim Board glyph proves thrust
```

Right question:

> What is the **minimum honesty fix** so thrust is never presented as an intrinsic motor property when it is actually a conditioned operating point?

---

## 2. Locked stances (inherit)

1. Thrust without propeller + voltage (+ evidence class) is **not** a motor intrinsic like `kv_rating` or `diameter_mm`.
2. Fallback OP rows that already document condition must remain the **authoritative** conditioned fact where they exist.
3. Top-level `thrust_n` may still exist as a **schema/legacy peak** for ranking/design-space — but the report must say whether that role is honest, harmful, or transitional.
4. Provenance: do not invent OP conditions; cite existing `source_note` / manufacturer pages already on the row.
5. No Geometry rung climb; no Continuity redesign unless a Buy explicitly needs a copy change and Engineer ★ it later.
6. ESC / FC / sensors out of scope.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `MotorSpec` / `_motor_from_raw` | Is `thrust_n` required? How is it used in design-space / ranking? |
| `library/motores/_datos.json` | How many rows have top-level `thrust_n`? How many also have `operating_points[]`? Which duplicate a fallback OP value? Spotlight `emax_rs2205s_2300` (10.042) and `sunnysky_r2205_2500` if relevant |
| `resolve_operating_point` | Exact → fallback → legacy path; when does bare `thrust_n` win? |
| `bind_motor_from_catalog` / Board `_fields` | Does the card show top-level thrust as if intrinsic? |
| `per_motor_max_thrust_n` / feasibility / Continuity copy | Where the number surfaces to the Engineer |
| Tests | Pins of `10.042` and bare `thrust_n` semantics |

---

## 4. Governing questions the report must answer

### Know

1. As-is: schema requirement, seed patterns, resolve ladder, Board/CLI surfaces for motor thrust.
2. For `emax_rs2205s_2300`: prove (or refute) that **10.042** top-level === fallback OP value and that the OP already carries the HQ5045 BN / voltage condition.
3. How many other motor rows have the same “peak thrust looks intrinsic but is really an OP” smell?
4. What breaks if top-level `thrust_n` is removed, made optional, renamed, or demoted to “legacy peak only”?

### Claim — honesty model

5. Phrase matrix: “motor produces 10.042 N,” “catalog peak,” “fallback OP,” “legacy_estimate,” Board field label honesty.
6. Options (with evidence):
   - **H0** Doc-only / `source_note` — leave schema.
   - **H1** Keep required `thrust_n` but **forbid** presenting it as unconditioned; sync/document that it mirrors fallback OP when present; Board/CLI copy hygiene.
   - **H2** Make `thrust_n` optional / derive display + resolve exclusively from `operating_points[]` (+ explicit legacy only when no OP).
   - **H3** Split vocabulary (`catalog_peak_thrust_n` vs OP) — only if evidence demands a rename for clarity.
7. Explicit: do **not** invent a propeller-free physical thrust for the motor.

### Buy shape

8. Rank **B0** / **B1** / **B2** / Defer with blast radius (seeds, tests, resolve, Board).  
9. **Default lean** (required) — prefer smallest honesty win that does not break OP resolution.

---

## 5. Out of scope

- Pose / assembly / fit / CAD / FEA / glyphs  
- ESC mass (CLOSED) · Here3 / Pixhawk  
- New OP curation campaigns / Phase 2.5 hover rewrite  
- Removing `resolve_operating_point`  
- System Optimization · Conversation Engine · version bump · weakening tests  

---

## 6. Deliverable format

Write `.jes/artifacts/investigation_report_catalog_motor_thrust_not_intrinsic.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is: schema + resolve ladder + surfaces  
- **C.** Seed inventory (duplication / OP coverage counts; EMAX spotlight)  
- **D.** Honesty options H0–H3 + phrase matrix  
- **E.** Blast radius if `thrust_n` changes (files/tests)  
- **F.** Buy options + **default lean**  
- **G.** Non-goals  

No code. No version bump. No test changes.

---

## 7. Success criterion

Engineer can ★ **Buy B1** (or B0 / B2 / Defer) knowing whether the next IC is **copy/provenance hygiene**, **schema demotion**, or **vocabulary split** — and that thrust remains conditioned, never “a property of the motor alone.”
