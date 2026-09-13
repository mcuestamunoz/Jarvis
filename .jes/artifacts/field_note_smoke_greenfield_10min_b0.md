# Field Note — Greenfield smoke: 10 min autonomía (from zero)

**Date:** 2026-09-13  
**Project:** `10-min-autonomía` (`7e400f0a4983`)  
**Authority:** Engineer CLI walk + UI board screenshot  
**Status:** OPEN — triage (no code this note)  
**Parallel:** Catalog sourced-only purge appears **landed in library** (5 bat / 3 mot / 6 prop) — Tattu visible as #5; motor list only sourced three.

---

## What worked

| Step | Result |
|---|---|
| New project wizard (dron → 10 min → payload 1 → detallado → 4 motors → no sé empuje) | OK |
| Motor pick #3 XING-E | Bind + calc OK |
| `ayúdame a elegir` props / ESC / battery / frame / FC / GPS | Numbered lists + bind OK |
| Battery list after purge | **5 sourced only**, includes `tattu_…` |
| Kit SKUs typed (`pololu_xt60_pair`, `pihut_…`) | Bind OK |
| `prop_adapter` → `va directa` | Bind OK |
| `declara frame_plate estimada 120 x 55 mm` | ESTIMATED_TEMPORARY OK; UI Top plate shows **120×55×2** |
| Board cards | Catalog identities + plate dims visible |
| Block prop/energy | Closed (fallback OP disclosed) |

---

## Bugs / product noise (ranked)

| ID | Symptom | Likely cause / note |
|---|---|---|
| **G1** | After motor bind, Continuity **locks on `power_connector`** for many turns while props/ESC/battery/frame still incomplete | Next-step ranks kit BOM gaps over **active acquisition block** (propulsion→energy→structure→control). User had to ignore tip and keep saying `ayúdame a elegir`. |
| **G2** | `ayúdame a definir` (post-motor) → dumps `estado` with **Arquitectura 0/4** while motors already bound; tip still power_connector | Bare help phrase does not resume **current block gap** (propellers); architecture counter inconsistent with component list. |
| **G3** | Typo `ayúdame a elegur` → **LLM qualitative essay** (margen 3.22, trade-offs) instead of refuse / “¿quieres decir ayúdame a elegir?” | Typo escapes help-choose gate → analyze path. |
| **G4** | Autonomy **0.7 min** from ~682 W peak OP × 34 Wh — presented as flight time vs 10 min goal | Known honesty/HD-005 class: **peak catalog W used as hover energy**. Tip correctly says “revisa energía”, but number is not hover-demonstrated. |
| **G5** | Board 3D: parts in a **horizontal gallery**, not a craft silhouette | Expected until layout-pack / Situar / plate+stack cola — **not a regression** from this walk. Estimated plate exists but no auto-pose. |
| **G6** | Mid-walk `Arquitectura: 0/4` then later `4/4` while Continuity still said gaps | Presentation inconsistency during acquisition; confirm whether progress counter lags block completion. |
| **G7** | After full BOM, `PROJECT STATUS: NOT ASSEMBLY READY` only on autonomy unmet | Correct vs Requirements INCOMPLETE — OK. Contrast with older 5min “ASSEMBLY READY + bloque no cerrado” tension (separate). |

---

## UI screenshot cross-check

- Project title **10 min autonomía**; motors XING-E, prop Gemfan 51466, ESC SpeedyBee, battery Tattu, MY5 plates (Top **120×55×2** estimated), FC F405, Holybro M10, kit present.  
- 3D = lined primitives (plates left, 4 green disks, boxes right) — **gallery**, not assembled drone.  
- Matches CLI state after estimated plate.

---

## Suggested Buys (do not steal layout cola)

| P | ★ candidate | Scope |
|---|---|---|
| **P0** | **`B1-continuity-active-block-before-kit`** | While propulsion/energy/structure/control acquisition incomplete, next-step must prefer **current block incomplete component** (e.g. propellers) over kit `power_connector` / harness / prop_adapter. |
| **P1** | **`B1-help-define-resumes-block`** | `ayúdame a definir` / help-choose during DEFINE_MISSING resumes the **active gap catalog**, not bare estado + kit tip. |
| **P1** | **`B1-help-choose-typo-guard`** | Near-miss `elegur`/`eligir` → clarify or map to help-choose; never silent LLM analyze. |
| **P2** | Autonomy peak-W disclosure / HD-005 | Do not treat as greenfield-only; keep under energy honesty. |
| — | Silhouette / layout pack | Already on layout cola (#4–#5); G5 is the visual symptom. |

---

## Out of this note

Catalog purge implementation review (Claude report when ready). Sensors rebind B3. Frame stale-rebind B4.
