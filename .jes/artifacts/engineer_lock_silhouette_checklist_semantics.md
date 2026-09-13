# Engineer lock — Silhouette checklist semantics (not visual recognition)

**Date:** 2026-09-13  
**Authority:** Engineer (via mentor reflection) after silhouette S1 smoke ACCEPT  
**Status:** LOCKED  
**Parents:** [IC silhouette S1](implementation_contract_board_silhouette_product_b_b1.md) · [craft montage lock](engineer_lock_craft_montage_honest_reproducible.md) · fit attestation CLOSED  

---

## What `parece un dron` / `silhouette_checklist` **is**

A **deterministic structural/geometric checklist** over `ProjectState`:

```text
ProjectState → geometry + pose + mount topology (+ quad_x/wb when available)
  → checklist rows
  → verdict: racimo (A) | silueta estimada (B*) | silueta (B)
```

Defensible claim:

> The **declared** spatial configuration has features compatible with a quad-X craft silhouette.

The `*` on estimated plate is mandatory epistemology — not “valid CAD geometry.”

---

## What it is **not**

| Forbidden reading | Why |
|---|---|
| Visual recognition / “I saw the object” | No image model; Board is a projection of declared state |
| Project-wide “no problems” / ASSEMBLY READY | Autonomy/requirements can still FAIL while silhouette is B* |
| Fit VERIFIED / physical similarity | Overlap attestation is a **later** chain step |
| Completeness fiction | `pose_cycle: n/a` must stay honest when no check exists |

CLI may keep the human phrase **“¿Parece un dron?”**; internally and in review copy, prefer **drone-like declared silhouette / silueta de configuración**.

---

## Validation chain (product order — do not invert)

```text
KNOW (dims) → STATE (pose/mount) → REPRESENT (Board)
  → ASSEMBLY assists → SILHOUETTE CHECK (this Buy)
  → FIT CHECK (overlap screening) → FIT VERIFIED (attest, scoped)
```

**Do not** open another visual/recognition layer now. Board glyphs + 3D envelopes + pose + Situar + silhouette checklist are enough representation for the next problem.

---

## Next jump (locked intent)

From:

> configuration looks like a quad-X silhouette  

To:

> verify **concrete geometric relations** (motor↔arm, FC↔plate, ESC↔stack, battery↔frame, prop↔motor, …)

That is the approach to **Fit VERIFIED** — relation-scoped evidence, not a new “looks like” feature.

---

## Optional thin UX (not a new capability)

Prefer checklist footer scoped as:

> Silueta: sin bloqueos críticos **dentro de este checklist**.

over bare “Nada crítico pendiente” when B*/B, so users do not read project-global green. Follow-up Buy only if Engineer ★.

---

## Decision

Silhouette S1 remains **CLOSED / smoke ACCEPT**. No visual-recognition Buy. Cola product next = fit-relation verification path (see fit-attest notes), plus holds already on plate-box / Path N.
