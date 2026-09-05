# Physical Component Catalog v1 — Architectural Design

**Status:** DESIGN CLOSED (Engineer 2026-08-12) — **implementation status:** §13 below (sync 2026-09-05: frame IC-1→3 + Structure B graph + G-N1 + arm thickness + plate multiplicity @ suite **2294**)  
**Date:** 2026-08-12  
**Author:** JES / Cursor (Engineer Interface)  
**Authority:** Engineer confirmation after Catalog v1 connection audit  

**Derived from:**  
- Engineer vision (SKU-real / buildable configs after `v0.2.0` / `checkpoint-fn026-h4`)  
- `.jes/artifacts/catalog_v1_connection_audit.md`  
- `.jes/artifacts/implementation_review_catalog_v1_audit.md` (PASS WITH NOTES)  
- Engineer lock: **1A 2A 3A 4A 5A + split A/B/C/D** (2026-08-12)  

**Explicitly not this document:** Implementation code · full Impl A/B/C/D contracts · H5/C-081 · ESC catalog · Conversation Engine / Step D · Create→BOM implementation details  

**Next:** see `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD (await Engineer next focus after plate multiplicity B2 CLOSED @ **2294**).

---

## 0. Checkpoint decision (Engineer)

```text
v0.2.0 / checkpoint-fn026-h4     ✅ H1–H4 closed · System Map 0 RED
Catalog v1 AUDIT                 ✅ PASS WITH NOTES
Engineer decisions 1A–5A         ✅ LOCKED (below)
This design                       ✅ CLOSED

Next:
  Implementation Contract — Impl A (Foundation)  ← READY
        ↓
  Claude implements Foundation only
        ↓
  Cursor review → CLI → commit
        ↓
  Impl B → C → D (separate contracts)
```

**Process rule:**

```text
Vision → Audit connections → Design CLOSED → IC per phase → code → review → CLI → commit
```

Do **not** skip Design → Impl A. Do **not** collapse A+B into one coding cut.

---

## Decision log — CLOSED (2026-08-12)

### Policy name

**Physical Catalog as identity + data authority; calc remains on `current_parameters`.**

> The curated `library/**` catalogs are the authority for **physical component identity and physical component data** (SKU, mass, KV, Wh, diameter, …).  
> `ProjectState.current_parameters` remains the authority consumed by calculation and simulation.  
> Binding (SKU → `ComponentSpec` → writers → params) is an explicit, user-confirmed projection — never LLM-invented, never silent.  
> Catalog identity must be representable on `ComponentSpec` before Catalog-aware DSE is allowed.

### Locked Engineer answers (1A–5A)

| # | Decision | Lock |
|---|---|---|
| **1A** | Identity field | `ComponentSpec.catalog_ref: { family, sku } \| None` — not a bare string; not a rich object with timestamps in v1 |
| **2A** | Motor mass in calc | Only when component is **SKU-bound** (`catalog_ref` set). Free-text declared motors keep today’s physics |
| **3A** | Material ES/EN bug | **Separate micro-fix** (alias → library keys). Not inside Catalog Foundation Impl A |
| **4A** | Batteries | Schema: `chemistry` string + required `energy_wh` + required `mass_g` (or `mass_kg`). Seed **LiPo-first**. Heuristic 150 Wh/kg only if **not** SKU-bound |
| **5A** | Assist modules | Impl A extends **`ComponentLibrary` only**. Keep `motor_catalog_assist` as-is. No Continuity gap redesign / no battery·prop Continuity gaps in A. Generalize assist later (B or UX cut) |

### Implicit locks (Engineer)

- `catalog_ref` is **optional** on `ComponentSpec` in Foundation; **writers do not populate it in Impl A**.  
- **No Catalog-aware DSE until Impl B is stable** (identity must survive bind). Impl C depends on B.

---

## 1. Problem / frontier

After H1–H4, Jarvis iterates **abstract continuous parameters** well. Continuity already surfaces honest motor catalog gaps (“no SKU covers ≥ N”). The next leap is **buildable configurations**, not more conversational handoff FNs.

**Central audit finding (accepted):** even today’s motor catalog pick discards SKU identity after the turn — only numeric properties survive into `ComponentSpec`. There is no durable “this is SKU X” field. Foundation must add that representation; Bind must write it; DSE must not invent SKU configs before Bind exists.

---

## 2. Authority table

| Question | Authority | Must not |
|---|---|---|
| What SKUs exist and what are their physical fields? | `library/**/_datos.json` via **single** reader `ComponentLibrary` (`knowledge/library.py`) | Per-consumer JSON reads; LLM inventing rows |
| What does calc/sim use? | `ProjectState.current_parameters` | Reading catalog objects directly inside `calculation_engine` |
| How does a SKU affect physics? | Explicit **Bind** (Impl B): user confirm → `catalog_ref` + projected properties → `component_writers` → params | Silent overwrite; LLM “matching” free text to SKU |
| What if no SKU matches? | Honest gap (D8 pattern) | Fabricated generic presented as a real product |
| Narrate in language? | LLM | Choosing or inventing SKU / specs |

---

## 3. Target layout

```text
library/
  motores/_datos.json      # enrich existing (~18–20 SKUs)
  baterias/_datos.json     # new (seed ~8–15, LiPo-first)
  helices/_datos.json      # new (seed ~10–20)
  materiales/_datos.json   # densities — unchanged role in Catalog v1
                           # (material alias bug = separate micro-fix)
```

**Naming:** do not create a bare module named `component_catalog.py`. Keep physical catalog under `knowledge/` / `library/`. Do not confuse with `system_architecture_catalog.py` (unrelated).

---

## 4. Schemas (v1)

### 4.1 `catalog_ref` on `ComponentSpec` (new, additive)

```text
catalog_ref: {
  family: "motor" | "battery" | "propeller"
  sku:    string   # key in the corresponding library JSON
} | None
```

- Optional. Default `None` = declared / inferred / unbound (today’s behavior).  
- Impl A: field exists; **no writer fills it**.  
- Impl B: assisted pick / confirm sets it and projects properties.  
- Do **not** overload `ComponentSpec.name` as the SKU contract.

### 4.2 Motor (enrich existing `MotorSpec` / JSON)

**Required:** `thrust_n`, `kv_rating`, `weight_g`, `max_watts`, `compatible_prop_inch`, `design_space` (as today).  
**Optional:** `manufacturer`, `model`, `max_current_a`, `voltage_min` / `voltage_max`, `compatible_prop_ids`, `operating_points[]`, `source_url` / `datasheet_ref` (nice-to-have; not mandatory for A exit).

`operating_points[]` shape (optional, **zero consumer code in A/B**):

```text
prop_id | prop_inch, voltage_v, rpm?, thrust_n, current_a?, power_w?
```

Empty table → honest fallback to nominal point (D8 discipline). Do not require dense thrust tables in seed.

### 4.3 Battery (new)

**Required:** `id` (JSON key), `chemistry` (string), `energy_wh`, `mass_g` (or `mass_kg`), plus voltage identity via `cells` and/or `nominal_voltage`.  
**Optional:** `capacity_mah`, `max_continuous_current_a`, `c_rating`, `design_space`, `operating_points[]`.

Seed: **LiPo-first**. Schema must not hard-block other chemistries later.

### 4.4 Propeller (new)

**Required:** `id`, `diameter_in`, `pitch_in`.  
**Optional:** `mass_g`, `ct`, `cp`, `compatible_kv_band`, `tags`, `operating_points[]`.

### 4.5 Data quality

| Forbidden | Allowed |
|---|---|
| Invent missing mass / thrust / SKU | Optional field absent → unknown |
| Silent generic as “real product” | Explicit `is_generic` labeled last (motors today) |
| LLM-authored catalog rows in product path | Curated JSON only |

---

## 5. Compatibility (deterministic)

Motor ↔ propeller (Impl A API level):

1. Explicit `compatible_prop_ids` when present.  
2. Else diameter / `compatible_prop_inch` conventions.  
3. No aerodynamic “smart” model in A.  
4. No LLM compatibility judgments.  
5. Missing match ≠ fabricated match.

---

## 6. Phase plan (LOCKED)

```text
DESIGN CLOSED
│
├── Impl A — Catalog Foundation
│   ├── motores (enrich) + baterías + hélices JSON
│   ├── ComponentLibrary load / get / find / match
│   ├── ComponentSpec.catalog_ref (optional, unused by writers)
│   ├── honest not-found / gap at library API
│   └── NO calc change · NO DSE change · NO Continuity redesign · NO Bind write path
│
├── Impl B — Catalog Bind
│   ├── pick / confirm → writes catalog_ref + projected properties
│   ├── fix iterate discard (SKU identity lost today)
│   ├── align DEFINE_MISSING catalog pick to same identity contract
│   ├── motor mass in calc IFF catalog_ref set
│   ├── battery mass/energy from SKU IFF catalog_ref set (else 150 Wh/kg heuristic)
│   ├── invalidate/clear catalog_ref if continuous DSE apply diverges SKU numbers (§C audit)
│   └── BOM / Continuity may distinguish catalog-bound vs declared-only
│
├── Impl C — Catalog-aware DSE   (forbidden until B stable)
│
└── Impl D — Create → BOM / SKU BOM
```

### Exit criteria (Design-level)

| Phase | Exit when |
|---|---|
| **A** | Three family loaders; typed API; `catalog_ref` on schema; existing motor D8/matching regressions green; calc/DSE/Continuity behavior unchanged; full suite green |
| **B** | Bound pick persists `catalog_ref`; mass rules as 2A/4A; no numeric regression for unbound projects; iterate discard fixed |
| **C** | DSE candidates are catalog-constrained and preserve identity through apply |
| **D** | Create/BOM consumes SKU identity (separate contract) |

### Out of this thread

H5 / C-081 · ESC / frame SKU catalogs · Conversation Engine · Step D · mandatory dense `operating_points` · Continuity battery/prop gaps inside Impl A · material alias micro-fix (tracked separately)

---

## 7. Data flow

### As-is (problem)

```text
library/motors → ComponentLibrary → assist / Continuity gap
                      ↓ pick
              thrust_n + weight_g only  ⚠ SKU discarded
                      ↓
              ComponentSpec → writers → params → calc
              (calc never reads weight_g; battery mass = 150 Wh/kg)
```

### Target after Impl B

```text
library/{motors,batteries,props} → ComponentLibrary
                      ↓
              assist / confirm (Bind)
                      ↓
              ComponentSpec + catalog_ref + projected props
                      ↓
              writers → current_parameters
                      ↓
              calc (motor/battery mass only if SKU-bound) → sim → Continuity
```

NL declare remains a **manual / unbound** path (no silent fuzzy SKU match).

---

## 8. Dual-truth rules (from audit — accepted)

| Hazard | Rule |
|---|---|
| Continuous DSE thrust vs SKU claim | Clear `catalog_ref` on diverge — never keep stale SKU label next to scaled numbers |
| Battery SKU mass vs 150 Wh/kg | SKU mass wins when bound; heuristic only unbound |
| Prop params without prop component | Tolerated asymmetry today; Catalog adds richer option, does not force component existence |
| `is_generic` motors | Sort last; label as placeholder when bound |

---

## 9. System Map impact (estimate — no IDs allocated here)

- ~5–8 new `C-xxx` across A+B (loaders, bind write, mirrored mass, BOM awareness).  
- Plausible new subsystem map under `docs/system_map/` for physical catalog (or section under engineering).  
- H5 remains deferred; Continuity `motor_catalog_gap` is a **precedent** for live risk threads, not an H5 implementation.  
- Final IDs assigned only in Implementation Contracts / map updates when code lands.

---

## 10. Seed policy

Small curated seed — prove architecture, not market coverage:

```text
Motors:     existing set, enriched (no arbitrary rewrite of valid rows)
Batteries:  ~8–15 LiPo-first, real mass + Wh
Propellers: ~10–20 with diameter/pitch (+ optional mass/Ct)
```

Prefer manufacturer-verifiable values when filling seeds (especially post–Impl A PASS). Do not dump 10k parts.

---

## 11. Open residual (not blocking Design CLOSED)

- Material vocabulary micro-fix (3A) — schedule separately.  
- Whether `source_url` lands in Impl A schema — optional.  
- Exact pydantic model name (`CatalogRef` vs inline dict) — Impl A IC chooses following project conventions.  
- Quantify test blast radius before Impl B mass-in-calc — due diligence in B’s contract.

---

## 12. Acceptance of this design (Engineer)

This document is **CLOSED** when Engineer confirms it matches the 1A–5A lock and A/B/C/D split (already confirmed 2026-08-12).  

After a final skim for contradictions with code, Engineer asks Cursor to emit:

**Implementation Contract — Physical Component Catalog v1 — Impl A (Foundation).**

Until that IC exists, **no Catalog Foundation coding**.

---

## 13. Implementation status (as of 2026-09-05)

> **This section is timeline hygiene only.** Design locks (§Decision log, §6 phase plan, 1A–5A) are unchanged. For as-is behavior see `docs/ARCHITECTURE.md` and `docs/system_map/*`. Live suite **2294**.

| Deliverable | Status | Checkpoint (reference) |
|---|---|---|
| Impl A — Catalog Foundation | ✅ Complete | catalog foundation v1 |
| Impl B — Catalog Bind | ✅ Complete | bind + identity persist |
| Impl C — Catalog-aware DSE | ✅ Complete | `checkpoint-impl-c` |
| Impl D — Create → BOM / SKU BOM | ✅ Complete | `checkpoint-impl-d` |
| Motor catalog pick UX | ✅ Complete | G21 / assisted acquisition |
| Propeller catalog pick UX | ✅ Complete | `v0.3.0` / `checkpoint-propeller-catalog-bind` |
| Battery catalog pick UX | ✅ Complete | IC 2 / `checkpoint-battery-catalog-bind-ux` |
| G27 battery Wh hardening | ✅ Complete | IC 2 (same checkpoint) |
| Project Closure / Assembly Ready policy | ✅ Complete | IC 1–3 / `checkpoint-closure-policy` — product contract in `ENGINEERING_READINESS_VISION.md` §11 |
| Frame catalog — IC-1 (schema + seed) | ✅ Complete (schema+seed only) | Structure Catalog Foundation IC-1 — `CatalogRef.family` gains `"frame"`, `FrameSpec`/`get_frame`/`has_frame`/`list_frames`, `library/frames/_datos.json` (4 seed rows). |
| Frame catalog — IC-2 (bind + BOM + diverge) | ✅ Complete | Structure Catalog Foundation IC-2 — `bind_frame_from_catalog`, `set_frame_material(..., catalog_ref=)`, `_bom_sku_resolved`/`has_frame`, frame branch in `invalidate_diverged_catalog_refs` (mass + class + override). |
| Frame catalog — IC-3 (assist UX) | ✅ Complete | Structure Catalog Foundation IC-3 — `frame_catalog_assist.py`, offer/apply, acquisition-brief CTA. `catalog_bound` still not wired into subsystem verdicts. |
| Structure B Parts Graph Fase 1 | ✅ Complete | `ComponentSpec.parent_key`; sibling keys `frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff`; seed optional `wheelbase_mm`/`configuration`/per-part materials; BOM `└` sub-lines; Structure PASS unchanged. |
| Structure B G-N1 (free-text root+parts) | ✅ Complete | One message may declare root + parts; parts-only follow-up; suite **2229**. Free-text still one node per type (no ordinal multi-plate). |
| IDLE catalog rebind B2+B3 | ✅ Complete | Frame + motors/propellers/battery reopen after arch 4/4; suites **2250**/**2276**. `clear_frame_part_children` by `parent_key`. |
| Structure B arm `thickness_mm` | ✅ Complete | `FrameSpec.arm_thickness_mm` → `frame_arm`; display-only; M0; suite **2286** + smoke. |
| Structure B plate multiplicity B2 | ✅ Complete | `PlateSeed` + `FrameSpec.plates[]` curated; ordinal `frame_plate*` + `label`; N2/N3/N7; BOM labeled lines; suite **2294**. |

**Still deferred (unchanged from §6 / §10 + post-B2 debt):** H5 ESC catalog · Conversation Engine / Step D · wiring `catalog_bound` into subsystem verdicts · G24 DSE apply-by-index · MEASURE (fit/clearance/FEA/CAD) · free-text multi-plate · optional G-N2 Armattan counts / G-N3 `compressed-x` alias / G-N4 diverge orphans · catalog completeness hardcode polish.

Historical §0 checkpoint sketch ("Next: Impl A ← READY") reflects the **2026-08-12 design gate**, not current code state.

---

**End of design.**
