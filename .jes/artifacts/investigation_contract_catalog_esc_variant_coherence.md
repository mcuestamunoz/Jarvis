# Investigation Contract — ESC XRotor variant coherence (PN ↔ dims ↔ mass)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer — catalog hygiene next: *cada número ↔ variante + condición correctas*  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_catalog_esc_variant_coherence.md`

**Status:** OPEN — awaiting report  
**Parents (mandatory):**
- [implementation_review_geometry_esc_envelope_b1.md](implementation_review_geometry_esc_envelope_b1.md) — B1 dims CLOSED @ **2327**; N2 left `mass_g=26` untouched
- [investigation_report_geometry_esc_envelope.md](investigation_report_geometry_esc_envelope.md) — live page: Version B `30901001` = 50×21.6×12 @ **15 g**; seed mass **26 g**
- `library/esc/_datos.json` → `hobbywing_xrotor_40a_6s` `source_note` (debt already flagged)
- Geometry Progression Lock B1 — **do not** open pose / assembly / fit
- Board glyphs B1 CLOSED @ suite **2344** / commit `64da71c`

**Type:** Catalog data-hygiene / provenance investigation for **one** ESC row.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · suite **2344** · glyphs CLOSED

**Single objective (locked):**

> For `hobbywing_xrotor_40a_6s`, establish a **defensible triple** — **Product Number ↔ envelope dims ↔ mass** — from the manufacturer page (and only that page / cited primary sources), so the catalog row is one real physical variant, not a collage of sibling SKUs.

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not open pose/`mounted_on`/fit/CAD/FEA. Do not touch Here3 / Pixhawk identity. Do not “fix” motor `thrust_n` in this investigation (queued second — see §8). Do not invent a second ESC SKU unless evidence forces a split and Engineer can ★ it.**

---

## 0. Role split (do not invert)

```text
Engineer  → named next focus: catalog hygiene (variant ↔ number)
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_catalog_esc_variant_coherence.md
Engineer ★ → Buy hygiene IC / Defer / re-scope (e.g. mass-only vs PN rematch)
```

---

## 1. Why this investigation exists

Geometry **representar** + **visualizar** made the Board look physically plausible. Engineer smoke judgment:

> El siguiente nivel ya no es “¿los números parecen reales?”, sino “¿cada número está asociado a la variante y condición correctas?”

ESC is the **already-written debt**:

| Field today | Seed | Page (prior fetch, re-verify live) |
|---|---|---|
| `part_number` | `30901001` | International/Asian Version B |
| `length/width/height_mm` | 50 / 21.6 / 12 | Matches Version B |
| `mass_g` | **26** | Page states **15 g** for that PN (Version A sibling ≠ this row) |

Wrong next step:

```text
silently patch 26→15 · invent PN · open pose · retouch Pixhawk/Here3 · bundle motor thrust
```

Right question:

> What is the **minimum honest correction** (or split) so this one SKU is engineering-defensible?

---

## 2. Locked stances (inherit)

1. Provenance: only numbers stated for **this** part number (or explicitly mapped variant). Never average siblings.
2. Dims already seeded for `30901001` stay unless live re-fetch disproves them.
3. Mass discrepancy is in-scope; electrical ratings (40A/60A, 2–6S) are **out** unless a source conflict appears that invalidates identity.
4. Geometry ladder: this is **catalog KNOW hygiene**, not a new Geometry rung. No glyphs change required unless a Buy changes bound properties.
5. No Conversation Engine / Continuity ESC picker / System Optimization.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `library/esc/_datos.json` | Full row: PN, dims, mass, `source_url`, `source_note` |
| `EscSpec` / loader | Which fields are required vs optional; bind projection |
| Tests | Assertions pinning `mass_g == 26` and dims 50/21.6/12 |
| Official page | Live re-fetch `source_url` (www mirror); quote **all** variants with PN / size / weight |
| Board / projector | Confirm mass appears as field text only; glyph uses dims only |

---

## 4. Governing questions the report must answer

### Know

1. Live official table: every variant (PN, size, weight, wires yes/no). Quote verbatim.
2. Which variant does seed `30901001` claim today? Does dims match? Does mass match?
3. Where did `26 g` likely come from (older note, wrong variant, marketing copy)? Best-effort provenance — say unknown if unknown.

### Claim — coherent row

4. Options with evidence:
   - **H1** Keep PN + dims; correct `mass_g` → page weight for that PN.
   - **H2** Keep mass 26 if a **cited** primary source defends it for this PN (else reject H2).
   - **H3** Split catalog into two SKUs (Version A vs B) — only if product needs both; default lean should prefer **one** coherent row unless evidence demands split.
5. Exact recommended field set after Buy (numbers + `source_note` rewrite).
6. Test / bind impact surface (list files that assert `26`).

### Honesty

7. Phrase matrix: “ESC weighs 26 g,” “same as Version A,” “Board glyph proves mass,” “fixed without source.”
8. Confirm Here3 / Pixhawk / motor thrust are **out** of this Buy.

### Buy shape

9. Rank: **B0** doc-only / **B1** mass (+ note) for current PN / **B2** rematch PN or split SKUs / Defer.  
10. **Default lean** (required).

---

## 5. Out of scope

- Pose / `mounted_on` / assembly / fit / CAD / FEA  
- Here3 / Pixhawk variant investigation  
- Motor top-level `thrust_n` / operating-point schema (queued §8)  
- ESC efficiency / Phase 2.6 losses  
- New ESC electrical families / 4-in-1  
- Glyph renderer changes (unless report proves glyph must change — expected: **no**)  
- Version bump · weakening tests  

---

## 6. Deliverable format

Write `.jes/artifacts/investigation_report_catalog_esc_variant_coherence.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** Live variant table (PN / dims / mass / wires)  
- **C.** Seed vs page delta for `hobbywing_xrotor_40a_6s`  
- **D.** Provenance of `26 g` (or “unknown”)  
- **E.** Options H1–H3 + honesty matrix  
- **F.** Buy options + **default lean**  
- **G.** Non-goals / test impact list  

No code. No version bump. No test changes.

---

## 7. Success criterion

Engineer can ★ **Buy B1** (or B0 / B2 / Defer) to make this ESC row **one** physical variant — without licensing pose or a motor-thrust rewrite.

---

## 8. Queued second (do not investigate here)

**Motor thrust-as-property smell (formalized, not this contract):**

- Symptom: `emax_rs2205s_2300` carries top-level `thrust_n: 10.042` **and** the same figure inside `operating_points[]` (`fallback_only`, HQ5045 BN @ voltage).
- Claim to formalize later: **10.042 N is not a property of the EMAX motor**; it is an operating point under propeller/voltage/test conditions.
- Next after this ESC investigation closes (or in parallel only if Engineer ★): open a separate investigation contract — e.g. `catalog_motor_thrust_not_intrinsic` — before any IC that removes or relocates top-level `thrust_n`.

Do **not** expand this ESC report into that motor rewrite.
