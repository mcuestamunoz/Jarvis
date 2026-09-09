# Investigation Contract — Propeller cited envelope (Geometry; live Gemfan 5045)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_propeller_envelope_b1.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ **B0+B1** → [IC READY](implementation_contract_geometry_propeller_envelope_b0_b1.md)  
**Report:** [investigation_report_geometry_propeller_envelope_b1.md](investigation_report_geometry_propeller_envelope_b1.md)  
**Engineer pass:** [engineer_validation_propeller_catalog_2026-09-09.md](engineer_validation_propeller_catalog_2026-09-09.md)  
**Review:** [investigation_review_geometry_propeller_envelope_b1.md](investigation_review_geometry_propeller_envelope_b1.md)  
**Parents:**
- Motor height cited B1 **CLOSED** smoke ACCEPT (2026-09-09) — Engineer: *lo mismo para las hélices*
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — plate L×W remains **later**; this insert is sourced **propeller** dims, not rung 4
- [investigation_report_geometry_motor_envelope.md](investigation_report_geometry_motor_envelope.md) — sourced-only, SKU-scoped labels, no sibling copy
- Fit stub — **QUEUED — DO NOT IMPLEMENT**

**Type:** Schema / provenance investigation for **Propeller** extra cited dims.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · suite **2480** · height smoke ACCEPT

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not invent mm/g from sibling SKUs. Do not invent `motor_power_w`. Do not open plate L×W, `"cabe"`, cylinder, Three.js, Conversation Engine.**

---

## 0. Role split

```text
Engineer  → named hélices after motor-height smoke
Cursor    → this contract; review report; IC only after ★
Claude    → investigation_report_geometry_propeller_envelope_b1.md
```

---

## 1. Why this exists

Motor height B1: one **cited** vendor number → catalog → bind → card text; 3D shape unchanged.

Engineer: do the **same** for propellers.

Live card `gemfan_5045_hbn` already shows `diameter_in` 5 in / `pitch_in` 4.5 in and a **disk** Ø 127 mm. This is **not** a shapeless family. The question is which **additional** vendor facts (mass, hub, blade count, …) a **real propeller page** affirms for this SKU — not “copy motor `height_mm` onto hélices.”

Wrong next step:

```text
copiar height_mm 31.7 a hélices · copiar mass_g del gemfan_5030
· tratar oscarliang (artículo de motor EMAX) como ficha Gemfan
· disco + altura = cilindro · inventar W del motor
```

Right question:

> What is the **minimum sourced bag** we can add to the live propeller SKU (and any other honestly seedable helix rows) so the card shows vendor dims the way the EMAX motor card does — without inventing, without a new 3D primitive, without touching autonomy watts?

---

## 2. Locked stances

1. Sourced-only; row’s own cited page; never sibling copy (`gemfan_5030.mass_g` ≠ this SKU).
2. Ladder: extra dims = **`representar` text**. Disk from `diameter_in` stays. No hub-height cylinder.
3. `bind_propeller_from_catalog` already projects `diameter_in`, `pitch_in`, and `mass_g` **when set**. A Buy may be seed-only if schema/bind already suffice.
4. Live `source_url` today is `https://oscarliang.com/emax-rs2205s-2300kv-motors/` — an **EMAX motor** article. Treat as **suspect provenance**. Find a page that is actually about **Gemfan 5045 HBN** (manufacturer or the listing the seed claims). Quote live. If none: recommend **B0** (leave gap) rather than scrape Oscar Liang for prop mass.
5. Watts / hover / `motor_power_w` are **out**. EMAX motor has no `max_watts`; Continuity is honest. This investigation is hélices geometry/identity dims only.
6. Mapping rung 4 (plate L×W) and `"cabe"` stay out.
7. Board `_fields` already shows every property — no per-brand UI.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `PropellerSpec` | Fields today (`library.py`); what is optional vs required |
| `library/helices/_datos.json` | Row count; which have `source_url` / `identity_status` / `mass_g` / `source_note` |
| Live SKU `gemfan_5045_hbn` | Exact keys; **missing** `mass_g`; Oscar Liang URL |
| `bind_propeller_from_catalog` | What it already projects |
| Board / 3D | Live disk from `diameter_in` — confirm no code change needed for “show properties” |
| Sibling `gemfan_5030` | Has `mass_g` 5 — **forbidden** as source for 5045 HBN |

---

## 4. Governing questions

### Know

1. As-is propeller geometry on card vs catalog vs bind.
2. Which helix rows are seedable **today** from a **propeller** page (live-fetched)?
3. Is the Oscar Liang URL acceptable identity evidence, or must `source_url` be replaced / `identity_status` downgraded?

### Claim

4. Accept/reject each candidate field (`mass_g`, hub/`height_mm`, `blade_count`, material, …) with a live quote per SKU.
5. First seed set: SKU(s), numbers, `source_note` quotes. Explicit **omit** list.
6. If bind already projects `mass_g`, is B1 **seed + source_note only**?

### Honesty / ladder

7. Phrase matrix: “we know prop size,” “hub height = motor height,” “Board = CAD,” “mass from sibling 5030,” “visualization verifies.”
8. Ladder rung of recommended Buy.

### Buy shape

9. Rank **B0** (gap / fix URL only) / **B1** (seed cited fields on verified helix page(s)) / B2 (new schema keys + 3D) / Defer.  
10. **Default lean** (required). Prefer B1 seed-only if a real Gemfan page states mass (or similar) and bind already displays it.

---

## 5. Out of scope

Motor watts · invent `motor_power_w` · plate L×W · `"cabe"` · cylinder / hub extrusion · Three.js · Conversation Engine · copying `gemfan_5030` mass · Structure PASS · version bump

---

## 6. Deliverable

Write `.jes/artifacts/investigation_report_geometry_propeller_envelope_b1.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is inventory (schema / seed / bind / live card)  
- **C.** Live quotes from each candidate page (re-fetch; do not reuse Oscar Liang motor dims as prop dims)  
- **D.** Accept/reject field table  
- **E.** Honesty / ladder matrix  
- **F.** Buy recommendation (B0/B1/…) with default lean  
- **G.** Explicitly not this increment  

No `src/` edits.
