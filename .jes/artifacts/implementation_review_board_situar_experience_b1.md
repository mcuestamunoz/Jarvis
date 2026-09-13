# Implementation Review — Board Situar experience B1 (`B1-situar-experience`)

**Date:** 2026-09-12  
**Reviewer:** Cursor (JES) — independent  
**Contract:** [implementation_contract_board_situar_experience_b1.md](implementation_contract_board_situar_experience_b1.md)  
**Report:** [implementation_report_board_situar_experience_b1.md](implementation_report_board_situar_experience_b1.md)  
**Implementer:** Claude Code

## Verdict

**PASS WITH NOTES**

E1–E3 match the IC. Pure helpers + tests are the right shape. UI **99** + typecheck clean. Package **`0.4.1`**. Closable after Engineer smoke **S1–S5**.

---

## Checklist

| Lock / criterion | Result | Evidence |
|---|---|---|
| E1 Option A — 2D min height | **Pass** | `.sb-viewport { min-height: 280px }` |
| E1 Option A — Situar pane capped | **Pass** | `.sb-scene3d--situar { max(360px, min(50vh, 560px)) }` (was 56vh / 420 floor) |
| E1 Option B — piece strip | **Pass** | `.sb-scene3d__piece-strip` chips → `onSelect`; only `isDraggableSolid` |
| E2 hit-through only when busy | **Pass** | `isSolidHitThrough` + `situarBusy = dragPreview \|\| posting` |
| E2 idle click selects peer | **Pass** | peers not hit-through when idle; Solid3D mousedown still selects |
| E3 freeze while Situar ON | **Pass** | `situarFrozenClusterRef` + `resolveClusterCenter` |
| E3 OFF / Recentrar | **Pass** | clear ref on Situar OFF; **Recentrar 3D** button |
| Hint copy matches E2 | **Pass** | “click en una caja: elegir…” |
| Ranking / writers / POST / pose math | **Pass** — this Buy | `situarOriginCandidates` not required to change; no bridge edits in this Buy’s file set |
| Version | **Pass** | `0.4.1` |
| T1–T5 | **Pass** | `situarInteractionState.test.ts` 8; full vitest **99**; typecheck clean |

---

## Independent notes

### N1 — Nested ESC when clicking the *outer solid* while idle

With E2, idle click on an overlapping outer box **selects that box**, not the previously selected ESC. Nested ACCEPT still holds if Engineer selects ESC via **card/strip** then drags on **empty pane** (or after drag is busy, peers go hit-through). Smoke S3 should use strip/card + pane background — not “click through the FC face.” IC already preferred strip/card if conflict.

### N2 — `busy` omits pre-threshold `solidDragRef`

`situarBusy` is `dragPreview || posting` only. Between mousedown and the 3px move threshold, peers are still clickable. Document-level listeners usually own the gesture after arming; residual is thin. Accept unless smoke shows mid-start steals.

### N3 — Capturing frozen cluster on first Situar-ON render

`if (situar && ref === null) ref = liveCluster` runs during render. Acceptable; Recentrar clears and re-captures. No double-write of SoT.

### N4 — Dirty tree noise

Workspace also shows unrelated dirty files (e.g. `component_writers.py` from other in-flight work). Not attributed to this Buy; do not treat as a lock fail of experience B1.

### N5 — Role

Claude implemented; Cursor reviewed. Correct.

---

## Smoke (Engineer) — paste from IC

| # | Check |
|---|---|
| S1 | Situar ON → strip chips and/or 2D usable → pick a box |
| S2 | Idle: click another box in 3D → selects → drag moves it |
| S3 | Chip/card **esc** → drag **empty** pane → esc moves |
| S4 | Drop → racimo does **not** recenter; Recentrar 3D works if wanted |
| S5 | Situar OFF → recentering allowed again |

**ACCEPT** if S1–S4 hold.
