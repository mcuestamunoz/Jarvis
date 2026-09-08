# Investigation Contract — Catalog-bound property freshness B1 (ESC stale mass + rebind gap)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer ★ Fase 1 hygiene sequence (E → geometry-all → connect) after Board status review  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_catalog_bound_property_freshness_b1.md`

**Status:** READY FOR INVESTIGATION  
**Parents:**
- Engineer sequence in plan `geometry_status_next` — Fase 1 = hygiene **E**
- [implementation_contract_catalog_esc_mass_hygiene_b1.md](implementation_contract_catalog_esc_mass_hygiene_b1.md) — CLOSED; **N4:** already-bound projects keep stale `26` until rebind
- [implementation_contract_idle_catalog_rebind_b3.md](implementation_contract_idle_catalog_rebind_b3.md) — CLOSED; **explicitly Not** ESC/FC/sensors
- ESC envelope B1 — `bind_esc_from_catalog` exists; **no** orchestrator catalog-pick UX (N4)
- [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md)

**Type:** Investigation only — how catalog-bound `ComponentSpec` properties stay honest when seeds change, and what minimum Continuity/product path closes the ESC Board lie (`mass_g` 26 vs seed 15).  
**Not** an Implementation Contract. **Do not implement.**  
**Not** geometry-for-all (Fase 2). **Not** mount-connect (Fase 3). **Not** fit/pose. **Not** Here3/Pixhawk identity unfreeze (name only if it collides).

**Checkpoint base:** package **`0.3.8`** · suite **2385**

**Single objective (locked):**

> Determine the **minimum honest product path** so a project that still shows catalog-stale physicals (esp. ESC `hobbywing_xrotor_40a_6s` `mass_g=26` while seed=`15`) can become truthful again — without inventing identity, without silent auto-mutation of engineering state on Board load, and without opening Fase 2/3.

**Product sentence this must enable:**

```text
Los números del Board que vienen de catálogo coinciden con el seed citado — o el usuario tiene un camino Continuity para refrescarlos / re-elegir
```

**Live evidence (Engineer Board + triage 2026-09-08):**

| Fact | Cite |
|---|---|
| Seed `library/esc/_datos.json` `hobbywing_xrotor_40a_6s.mass_g` | **15** |
| Project `workspace/autonomía-de-10min-9ada1a1b0cca` `components.esc` | `catalog_ref` SKU same · `properties.mass_g` **26** · `mounted_on=frame_plate` |
| Idle rebind families | `frame` / `motors` / `propellers` / `battery` only — **no esc** |
| `bind_esc_from_catalog` | Exists in `catalog_bind.py`; prior reports: **no** production CLI pick path |

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not invent ESC Version-A SKUs. Do not auto-rewrite `state.json` on Board open. Do not open plate footprints, sensors dims, mount-connect, fit, or pose. Do not unfreeze Here3/Pixhawk identity in this report’s Buy — flag only.**

---

## 0. Role split

```text
Engineer  → Fase 1 hygiene first in preferred sequence
Cursor    → this contract; review; IC after ★
Claude    → investigation_report_catalog_bound_property_freshness_b1.md
Engineer ★ → Buy lean / Defer / re-scope
```

---

## 1. Why this investigation exists

ESC mass hygiene B1 fixed the **seed**. The demo Board still shows **26 g** because bound projects were never refreshed, and Continuity cannot “cambiar esc” (B3 excluded ESC; no ESC picker UX).

Fase 1 of the Engineer sequence is **trust numbers before geometry-for-all**. This investigation chooses the smallest durable product Buy to restore that trust for catalog-bound fields — starting with ESC, generalizing only if cheap and honest.

---

## 2. Locked stances

1. Seed remains source of catalog truth for SKU-bound rows.  
2. Declared freeform (no `catalog_ref`) is **not** auto-overwritten by seed.  
3. Board load must **not** silently mutate `ProjectState`.  
4. Prefer Continuity-visible user action over hidden migration.  
5. Preserve `mounted_on` and other orthogonal fields across any refresh/rebind.  
6. Here3 / Pixhawk identity stays FROZEN unless Engineer ★ separately.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `bind_esc_from_catalog` / ESC library loader | Projection of `mass_g` + envelope |
| Idle `catalog_rebind_assist` + orchestrator IDLE block | Which families; how offer/apply works for battery/motor |
| Any ESC offer/apply in orchestrator | Confirm absence or find hidden path |
| `invalidate_diverged_catalog_refs` | Does seed change clear ref or leave stale values? |
| Demo project esc component | Confirm triage facts; note `mounted_on` must survive |
| Other families in same project | Any other seed↔bound mismatches? (sample motors/battery/frame) |

---

## 4. Governing questions (answer all)

**A. Mechanism**
1. Why does `catalog_ref` + stale `mass_g` coexist after seed edit? (confirm N4)  
2. Does divergence invalidation fire for ESC mass? If not, is that a gap or intentional?

**B. Product paths**
3. Minimum path to make demo Board show 15 g honestly?  
4. Should Fase 1 Buy be ESC-only or a generic “refresh from `catalog_ref`” for all families that have bind_*?

**C. Continuity / UX**
5. Is “cambiar esc” + full picker required, or is “actualizar/refrescar esc desde catálogo” (no picker) enough when `catalog_ref` already set?  
6. What copy is honest after refresh? (no “corregido automáticamente”)

**D. Buy options** — recommend exactly one default lean:

| Option | Meaning |
|---|---|
| **B0 — Walk only** | Engineer manually re-binds via whatever path exists; doc note; no code |
| **B1 — Refresh-from-catalog_ref** | Writer: if `catalog_ref` set, re-project physicals from seed; Continuity phrase; preserve `mounted_on` |
| **B1+ — Idle ESC rebind + catalog offer UX** | Full picker like battery B3 (larger) |
| **B2 — Auto-refresh on load** | Reject unless report proves no silent-mutation risk |

State reversal criteria.

**E. Out of scope checklist** — confirm Fase 2/3 / fit / pose / identity freezes untouched.

---

## 5. Non-goals

Geometry-for-all · mount-connect campaign · fit · pose · inventing plate L×W · ESC Version-A SKU split · Board code · version bump · silent `state.json` rewrite on projector read

---

## 6. Deliverable shape (report)

1. Executive recommendation (Buy + why).  
2. Evidence table with file cites.  
3. Answers A–E.  
4. Risks of wrong Buy.  
5. If Buy ≠ B0: field/API sketch only — **not** an IC.  
6. Explicit note for Engineer: demo project remains stale until Buy ships or walk uses the new path.

---

## 7. Done criteria

- [ ] Report written  
- [ ] All governing questions answered  
- [ ] Default lean stated  
- [ ] No code  
- [ ] Cursor review next; Engineer ★ before IC

---

## 8. Stop conditions

Stop and ask before: recommending Board-load mutation, inventing ESC SKUs, or folding Fase 2 geometry into this Buy.
