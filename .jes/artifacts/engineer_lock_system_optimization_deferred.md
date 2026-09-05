# Engineer lock — System-level Optimization deferred (2026-09-05)

**Status:** LOCKED (docs only — no investigation, no IC)  
**Author:** Engineer strategic decision → Cursor recorded  
**Suite:** **2294** · Structure plate multiplicity smoke ACCEPT  

## Decision

**Do not open System-level Optimization now.**

## Why (code-backed)

1. `explora` builds candidates from current state + grids, recompute/simulate in memory, keeps `can_fly=True`.
2. `aplica la mejor` applies viable `#1` by **goal score** — may warn if score does not improve, still applies.
3. Readiness, gaps, Continuity, ASSEMBLY READY, and closure constraints **do not** participate.
4. Therefore today is **local simulation optimization**, not system-level design optimization.
5. That jump is a valid future product improvement **only when current behavior demonstrates real pain**. Do **not** implement because Vision §7 names the target.

## Rule

> We will not implement Optimization because the Vision says it exists.  
> We will implement it when current behavior proves we need that jump.

## Related walls / closures

- Structure representation + plate multiplicity + CLI smoke → **CLOSED / ACCEPT**
- Prop/Energy experimental autonomy → **physical wall HD-004** ([engineer_lock_prop_energy_evidence_wall.md](engineer_lock_prop_energy_evidence_wall.md))
- Next software work → **none by default**; wait for Engineer-named pain/evidence

## Reopen condition

Engineer names a concrete CLI/product failure of local DSE (e.g. apply worsens project vs Continuity next-step / readiness, or “mejor” is systematically misleading) → then investigation contract, not a surprise IC.
