# Implementation Review — Board Situar multi-box UX B1 **fix** (ranking + drop settle)

**Date:** 2026-09-12  
**Reviewer:** Cursor (JES) — independent  
**Contract:** [implementation_contract_board_situar_multibox_ux_b1.md](implementation_contract_board_situar_multibox_ux_b1.md) (+ Engineer ★ Option 1+2 + thin drop fix)  
**Report:** [implementation_report_board_situar_multibox_ux_b1.md](implementation_report_board_situar_multibox_ux_b1.md) §Fix  
**Implementer:** Claude Code

## Verdict

**PASS WITH NOTES**

Root cause of inert labels is correct and independently confirmed. Option 1+2 tiers fire on live **5min** / **15min**. Drop preview-hold + cluster freeze match the Engineer’s “vuelve / se aleja” diagnosis. UI **91** + typecheck clean. Closable after Engineer re-smoke.

---

## Checklist

| Claim | Cursor |
|---|---|
| Original preferred tiers inert (mount→frame part, no box) | **Pass** — reconfirmed on 5min/10min/15min projector census |
| Tier 2 mount-siblings | **Pass** — code + T4; live 5min `esc`↔`FC` → `mismo montaje` |
| Tier 3 already-an-origin | **Pass** — code + T5; live 15min `sensors` → battery+FC labeled |
| Tier priority (sibling > origin) | **Pass** — T6 |
| Full unlabeled fallback / never silent default | **Pass** — T7; Fijar origen unchanged |
| Tests mirror real shapes (not only box→box mount) | **Pass** — T4/T5 |
| Preview held until `nodes` refetch | **Pass** — `onSolidDragUp` + `useEffect([nodes])`; clear on POST fail |
| Cluster frozen while preview \|\| posting | **Pass** — `lastClusterRef` |
| No writer / POST shape / version bump | **Pass** — `0.4.1` |
| Suites | **Pass** — vitest **91**; `tsc --noEmit` clean |

### Live ranking recount (projector, post-fix logic)

| Project | Subject | Preferred (non-empty) |
|---|---|---|
| 5min | `esc` | `flight_controller` mismo montaje |
| 5min | `flight_controller` | `esc` mismo montaje |
| 5min | `battery` / `sensors` | `flight_controller` origen de otra pieza |
| 15min | `esc` | `flight_controller` origen de otra pieza |
| 15min | `sensors` | `battery` + `flight_controller` origen de otra pieza |
| 15min | `battery` | *(none — only unlabeled fallback)* |

Matches intent; wording in report that “battery … preferred” means **as a candidate for others**, not that battery’s own picker always has a preferred row.

---

## Notes

### N1 — Final cluster unfreeze still moves peers once

Freeze covers the POST+refetch **gap**. When preview clears and `clusterFrozen` becomes false, `liveCluster` updates and peers can **still slide once** to the new bbox center. That is honesty of visor chrome, not a regress of the snap-back. Smoke: accept if the moved piece **does not** flash home; a single soft reframe of the group at settle is OK. Freezing cluster for the whole Situar session would be a later ★.

### N2 — Stale module comment

`Scene3D.tsx` still says preview is “cleared on every mouseup” above the state (~L88–90). Behavior contradicts that. Hygiene; not a functional fail.

### N3 — `useEffect([nodes])` clears any pending preview on any nodes refresh

If a concurrent refetch landed mid-drag, preview would drop. Unlikely in current Board (only pose POST triggers refetch). Accept residual.

### N4 — No Scene3D unit test for freeze/hold

Report is honest. Vitest coverage is ranking-only; drop settle is smoke-gated. Fine for this thin UI timing Buy.

### N5 — Role

Claude implemented; Cursor reviews. Correct split.

---

## Re-smoke (Engineer)

1. Hard refresh Board.  
2. **5min:** Situar ON → picker on `esc` without origin (or clear) → see **`flight_controller (mismo montaje)`**.  
3. **15min:** picker on `sensors` → **`battery` / `flight_controller (origen de otra pieza)`**.  
4. Select box A via card (Situar OFF first if pane covers cards) → Situar ON → drag → **release**: piece should **not** snap home; peers should not slide for the whole POST wait.  
5. Hint + dim peers still present.

**ACCEPT** if 2–4 hold.
