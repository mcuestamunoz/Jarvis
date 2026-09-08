# Investigation Contract — Connect remaining `mounted_on` (Fase 3 / Conn)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer ★ preferred sequence **E → G → Conn** after Board status review  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_connect_remaining_mounted_on_b1.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · ★ Buy **B1** · IC READY (dual lock)  
**Report:** [investigation_report_connect_remaining_mounted_on_b1.md](investigation_report_connect_remaining_mounted_on_b1.md)  
**Review:** [investigation_review_connect_remaining_mounted_on_b1.md](investigation_review_connect_remaining_mounted_on_b1.md)  
**IC:** [implementation_contract_connect_remaining_mounted_on_b1.md](implementation_contract_connect_remaining_mounted_on_b1.md)  
**Parents:**
- Engineer sequence: Fase 1 hygiene **E** CLOSED-ish (refresh PASS @ **2406**) → Fase 2 geometry-all **G** CLOSED @ **2418** → Fase 3 **Conn**
- [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md) — relation rung CLOSED; may declare remaining mounts **without new IC** via Continuity already shipped
- Continuity declare B1 CLOSED @ **2380** — `mounted_on_declare_assist` + `set_component_mounted_on` + Board text/edges
- Board edges B2 CLOSED @ **2385**
- [implementation_contract_geometry_for_all_b1.md](implementation_contract_geometry_for_all_b1.md) — G CLOSED

**Type:** Investigation only — which remaining undeclared mounts are product-worth connecting, whether Continuity already covers them (walk-only), and the **minimum Buy** if any code is still needed.  
**Not** an Implementation Contract. **Do not implement.**  
**Not** pose / fit / CAD. **Not** inventing mounts from Board layout. **Not** Here3 identity unfreeze. **Not** reopening G.

**Checkpoint base:** package **`0.3.8`** · suite **2418**

**Single objective (locked):**

> Determine whether Fase 3 Conn is **(a)** an Engineer Continuity walk with tools already shipped, **(b)** a thin assist/copy gap worth a small IC, or **(c)** something else — with an evidence-backed gap matrix on the live demo and a clear lean including **B0 = no code**.

**Product sentence this must enable (after Buy or walk):**

```text
Los componentes que deben declarar montaje en el Board lo tienen — vía Continuity — sin inventar relaciones ni pose.
```

**Live demo snapshot (Cursor triage 2026-09-08 — `workspace/autonomía-de-10min-9ada1a1b0cca`):**

| Key | `mounted_on` | Notes |
|---|---|---|
| `motors` | `frame_arm` | Connected |
| `esc` / `flight_controller` | `frame_plate` | Connected |
| `battery` | `frame` | Connected |
| `propellers` | **None** | Subject noun already in Continuity assist |
| `sensors` (Here3) | **None** | Subject noun already in Continuity assist; identity still FROZEN (name-only OK for declare) |
| `frame_*` parts (arm/plates/cage/standoff) | **None** | Have `parent_key=frame`; **not** Continuity subjects today (only targets) |
| `frame` | **None** | Root — usually no mount |

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy before any IC (including if lean is B0 close-out).

**Do not implement. Do not bump version. Do not weaken tests. Do not invent mounts from Board x/y, BOM co-membership, or “only one plate.” Do not open fit/pose. Do not change `parent_key` semantics in this investigation’s Buy.**

---

## 0. Role split

```text
Engineer  → Fase 3 Conn after G
Cursor    → this contract; review; IC only after ★ (or B0 close doc)
Claude    → investigation_report_connect_remaining_mounted_on_b1.md
Engineer ★ → Buy lean / walk-only close / re-scope
```

---

## 1. Why this investigation exists

Assembly **relation** is already a shipped capability (schema + Continuity + Board edges). The Engineer sequence still named **Conn** as Fase 3: connect remaining mounts (battery/sensors/propellers… — Continuity first).

The lock itself says remaining declares may need **no new IC**. This investigation must prove whether Conn is already done-by-walk, or whether a real product gap remains (parse subjects, discoverability, structure-part mounts vs `parent_key`, honesty copy, etc.).

Wrong next moves without evidence:

- Auto-mount propellers→motors because “obvious”
- Treat `parent_key` as `mounted_on` (or duplicate it blindly)
- Build a Conversation Engine “assembly wizard”
- Open fit because cards still float on the Board canvas

---

## 2. Locked stances

1. `mounted_on` stays **declared** only — Continuity/user phrase; no silent inference.  
2. Reuse `set_component_mounted_on` — no second writer.  
3. `parent_key` (structure composition) ≠ `mounted_on` (assembly relation) — orthogonal; report must not collapse them without ★.  
4. Ambiguous plate rule stays: never guess among 2+ plates.  
5. Pose DEFERRED / fit FROZEN as default-next — unchanged.  
6. Here3 identity FROZEN — declaring `sensors` montado en … is still allowed as a name/key relation if Continuity already supports it; do not invent GPS dims.  
7. Prefer B0 (walk) when assist already covers the remaining subjects.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| Demo `state.json` | Full mounted_on matrix (extend Cursor snapshot) |
| `mounted_on_declare_assist.py` | Subject nouns, target nouns, SET/CLEAR/AMBIGUOUS — what phrases work for propellers/sensors today |
| Orchestrator IDLE mount bridge | Confirm live path still active |
| Board projector edges | Which undeclared keys float; what appears after a declare |
| Structure parts | Whether any precedent mounts `frame_arm`→`frame` via `mounted_on`, or only `parent_key` |
| Prior Continuity / assembly reports | Reuse; do not contradict CLOSED relation rung |

**Empirical (required):** dry-run Continuity parse (and optionally orchestrator) for at least:

- `"hélices montadas en los motores"` / `"propellers montados en motors"`
- `"sensor montado en la placa"` / Here3 phrase
- one structure-part-as-subject phrase if attempted (expect NONE today)

Cite results — do not guess.

---

## 4. Questions the report must answer

### A. Gap matrix

For each undeclared key: **should** it have `mounted_on` for an honest Board story? Blocker = missing Continuity subject / ambiguous target / composition-only (`parent_key`) / root / out of scope?

### B. Continuity coverage

Which Conn candidates are **already declareable** with zero code? Quote working phrases vs NONE.

### C. `parent_key` vs `mounted_on` for frame parts

Is Conn meant to mount structure parts onto `frame`, or is composition already sufficient and Conn = **payload/electronics/propellers/sensors only**? Pick a clear recommendation with rationale.

### D. Buy options (must include)

| Option | Intent |
|---|---|
| **B0 — Walk-only / close Conn as product-complete** | Engineer declares remaining via existing Continuity; maybe a short smoke checklist; **no code** |
| **B1 — Thin assist gap** | Only if evidence shows a real missing noun/target/copy/discoverability hole (e.g. structure-part subjects, or “qué falta por montar” status line) |
| **B1+ — Guided missing-mount list** | Continuity surfaces undeclared candidates without auto-writing |
| **B2 — Auto-infer mounts** | **Default reject** unless overwhelming evidence (conflicts locked stance 1) |

### E. Contingency sketch (if Buy ≠ B0)

Not an IC: which file(s), which phrases, reuse writer only.

### F. Out of scope checklist

Confirm pose / fit / G reopen / identity unfreeze / Board layout SoT untouched.

---

## 5. Report format (mandatory)

1. **Executive recommendation** — B0 / B1 / B1+ / B2 + one sentence.  
2. **Gap matrix** — demo + Continuity coverage.  
3. **Empirical parse results.**  
4. **Buy options** + rejection of silent inference.  
5. **Contingency sketch** (if any).  
6. **Non-goals honored.**

---

## 6. Done criteria (investigation)

- [ ] Demo matrix cited  
- [ ] Propellers/sensors Continuity path proven or disproven live  
- [ ] Clear stance on frame-part `mounted_on` vs `parent_key`  
- [ ] B0 allowed and evaluated honestly  
- [ ] No code  

---

## 7. Stop conditions

Stop and ask before: proposing auto-mount inference, merging `parent_key` into `mounted_on`, or opening fit/pose as part of Conn.
