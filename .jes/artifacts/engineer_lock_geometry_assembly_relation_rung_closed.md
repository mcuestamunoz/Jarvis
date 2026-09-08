# Engineer Lock — Geometry Assembly Relation Rung CLOSED

**Date:** 2026-09-08  
**Authority:** Engineer (plan ACCEPT: idle Geometry after Board status review)  
**Status:** ★ LOCKED — assembly **relation** rung closed; numeric pose deferred; fit not default-next  
**Parents:**
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)
- Assembly: `mounted_on` @ **2364** · Continuity @ **2380** · Board edges B2 @ **2385** + smoke ACCEPT
- Pose: [implementation_contract_geometry_assembly_pose_b1plus_defer.md](implementation_contract_geometry_assembly_pose_b1plus_defer.md) — **B0 DEFERRED**
- Fit stub: [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**

---

## Locked claim

> Jarvis’s Geometry ladder has a closed **assembly relation** capability: a component may be **declared** mounted on another (`mounted_on`), declared/cleared from Continuity IDLE, and shown on the Board as text `"montado en"` plus a presentation edge.  
> That is **not** numeric pose, **not** “cabe”, and **not** CAD.

**Product sentence (honest):**

```text
Sé qué es + qué volumen declarado ocupa + a qué se declara montado
(+ lo veo en el Board: texto + línea)
```

**Not:**

```text
Pose mm · cabe · ensamblado verificado · el drag del Board es la geometría del drone
```

---

## Ladder position (locked)

```text
KNOW → representar → visualizar (glyphs)
  → ASSEMBLY RELATION (mounted_on + Continuity + edges)  ← ★ CLOSED
  → pose mm                                          ← DEFERRED (B0)
  → comparar / verificar (fit)                       ← FROZEN as default next
  → CAD / MEASURE / FEA                              ← later ★
```

Authority gate unchanged: **CAD/FEA/fit as default next still FROZEN**.

---

## What may happen without a new IC

- Engineer/user may use Continuity phrases already shipped to declare remaining mounts (e.g. sensors / propellers).
- Board hard-refresh to see `"montado en"` + edges.
- No code change required.

---

## What requires a new ★

| Ask | Artifact first |
|---|---|
| Fit / “cabe” / compare | **Investigation contract** (stub exists; not enough for READY IC) |
| Numeric pose | Reversal conditions in pose investigation §E + new READY IC (stub DEFERRED) |
| FC/ESC stack hole-pattern KNOW | Fresh narrow investigation (orthogonal to airframe pose) |
| Here3 / Pixhawk identity | Unfreeze + identity investigation |

---

## Explicit non-goals while this lock holds

Implementing fit · inventing pose mm · treating Board layout as SoT · Conversation Engine · version bump without Engineer ask · opening Geometry implementation ICs without investigation when the model is undefined

---

## Mode

**Idle** — package `0.3.8` · suite **2385**. No active implementation operation for Claude on this lock (doc-only close of the rung).
