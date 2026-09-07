# Implementation Contract — Geometry assembly pose B1+ (numeric pose) — **QUEUED**

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Status:** **QUEUED — DO NOT IMPLEMENT**  
**Queue position:** **2 of 3** (after Board edges B2)

**Parents:**
- [investigation_report_geometry_assembly_espacial_b1.md](investigation_report_geometry_assembly_espacial_b1.md) — **B1+ rejected** this cycle: no catalog mount source, no reference frame
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)

---

## Gate (hard)

This IC is a **placeholder in the Engineer-approved assembly queue only**.

**Blocked until:**

1. Board edges B2 CLOSED, and  
2. Engineer ★ opens a **fresh investigation** that answers: reference frame origin, units, declared-vs-unknown honesty, and what may be stored without inventing catalog mount patterns.

**Do not** write pose fields, offsets, orientation, or Continuity “pose mm” parsers under this filename until that investigation is REVIEWED and a superseding READY IC replaces this stub.

---

## Intent (queued product sentence — provisional)

> “Sé con qué pose declarada (origen + números honestos) queda montado un componente.”

---

## Explicit non-goals until unblocked

Inventing mm offsets · treating Board `x`/`y` as pose · fit/clearance · CAD · version bump
