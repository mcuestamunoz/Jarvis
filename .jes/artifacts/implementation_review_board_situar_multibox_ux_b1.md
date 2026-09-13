# Implementation Review — Board Situar multi-box UX B1 (independent)

**Date:** 2026-09-12  
**Reviewer:** Cursor (JES) — **independent pass after implementer = Cursor role slip**  
**Contract:** [implementation_contract_board_situar_multibox_ux_b1.md](implementation_contract_board_situar_multibox_ux_b1.md)  
**Report:** [implementation_report_board_situar_multibox_ux_b1.md](implementation_report_board_situar_multibox_ux_b1.md)

## Verdict

**PASS WITH NOTES**

Code matches the IC locks. UI suite **87** green. Package **`0.4.1`**. Closable after Engineer smoke.  
**Process note:** this Buy was implemented by Cursor; next ICs keep **Claude = implement · Cursor = redact IC + review only**.

---

## Checklist (IC §0–§4)

| Lock / criterion | Result | Evidence |
|---|---|---|
| Nested-hit kept (pointer-events + pane→selected) | **Pass** | `Scene3D.tsx` `pointerEventsNone` + `onBackgroundMouseDown` unchanged in behavior |
| Hint: selected piece + Alt orbit | **Pass** | hint: “mueve la seleccionada · otras: passthrough · Alt+arrastre: órbita” |
| Dim hit-through | **Pass** | `.sb-solid--hit-through` faces `opacity: 0.35` + dashed |
| Pure ranking helper + wire | **Pass** | `situarOriginCandidates.ts` → `rankBoxOriginCandidates(pickerNodeId, solids)` |
| Preferred = mountedOn box + frame_plate box | **Pass** | helper lines 39–51; T1/T2 |
| Empty mounts → full other-box list | **Pass** | T2; 15min-safe |
| Never silent default origin | **Pass** | still `— elegir —` + Fijar origen disabled until pick |
| Labels | **Pass** | `formatOriginCandidateLabel` |
| No writer / isDraggableSolid / version / workspace | **Pass** | `0.4.1`; no bridge edits; new files UI-only |
| T1–T5 | **Pass** | vitest re-run 8 files / **87** |
| Out of scope not touched | **Pass** | no silhouette / copy-situar / cluster freeze |

---

## Independent notes

### N1 — Role slip (process)

IC handoff said Implementer → code; Cursor → review. Engineer “procede” was taken as implement-now. **Going forward:** Cursor stops at IC + cola docs; Claude implements; Cursor reviews.

### N2 — Prior self-review superseded

The earlier [review](implementation_review_board_situar_multibox_ux_b1.md) written in the same implement session is **not** independent. **This file is the review of record.**

### N3 — Duplicate root id string

`ASSEMBLY_ROOT_CANDIDATE_ID = "frame_plate"` duplicates `scene3dLayout.ts` private `ASSEMBLY_ROOT_ID`. Acceptable for this thin Buy; do not “fix” by exporting across modules without ★ (keeps layout root policy local).

### N4 — Smoke still required

Dim + ranking do not prove the FATAL gesture in browser. Engineer: ≥2 boxes, select A, drag near B → A moves, peers dim.

### N5 — Report accuracy

Report claim “UI-only / no version bump” holds. Untracked new files must be committed with the Buy when Engineer asks for git.

---

## Done / next

1. Engineer smoke → ACCEPT / reject.  
2. Next implementation Buy: **Claude executes**; Cursor only redacts IC and reviews.
