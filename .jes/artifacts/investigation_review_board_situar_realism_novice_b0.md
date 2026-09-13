# Investigation Review — Board Situar realism + novice situar path (B0)

**Date:** 2026-09-12  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_board_situar_realism_novice_b0.md](investigation_contract_board_situar_realism_novice_b0.md)  
**Report:** [investigation_report_board_situar_realism_novice_b0.md](investigation_report_board_situar_realism_novice_b0.md)  
**Parents:** Continuity spatial assembly ★ · nested-hit ACCEPT · Board drag pose B1 · Product A racimo · #4g-A CAD B0

## Verdict

**PASS WITH NOTES** · recommended first Buy **`B1-ux-situar`** (Cursor keeps Claude’s lean).

The FATAL “other piece jumps” is explained without overturning prior ACCEPT smokes: nested-hit pane-drag moves the **card-selected** solid while peers are click-through — validated for one nested ESC, never for **N>1 nearby draggable boxes**. Census and code citations hold. Silhouette / novice stay cola or B0/DEFER. No IC until Engineer ★.

---

## Checklist

| Criterion | Result |
|---|---|
| §§A–H present | **Pass** |
| Symptom matrix BUG/UX/HONEST/MISSING | **Pass** |
| Live 15min census read-only | **Pass** — Cursor re-projected (below) |
| §C three mechanisms separable | **Pass** — nested-hit · cluster chrome · pose-chain |
| Honest limits not re-labeled bugs | **Pass** — copies gate · mute plates · Product A |
| No invent mm / no Conversation Engine / no Three.js default | **Pass** |
| Single first Buy + ranked cola | **Pass** — `B1-ux-situar` first |
| Report-only (no `src/`/`ui/`/`library/`/`workspace/` writes) | **Pass** — investigation claim; Cursor did not re-diff Claude’s tree |
| Decision card usable for ★ | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| `pointerEventsNone` when situar + selection | **Confirmed** `Scene3D.tsx:396` |
| Background mousedown → drag **selected** | **Confirmed** `Scene3D.tsx:226-235` |
| Nested-hit note smoke = card ESC → drag anywhere | **Confirmed** `engineer_note_situar_nested_hit_select_card.md` |
| `boxOriginCandidates` = all other boxes | **Confirmed** `Scene3D.tsx:319-321` |
| Writer rejects non-box origin | **Confirmed** `component_writers.py:337-342` |
| `isDraggableSolid` excludes `solidCopies >= 2` | **Confirmed** `boardPoseDrag.ts:33-36` |
| `clusterCenterPx` = visor chrome only | **Confirmed** `scene3dLayout.ts:153-180` |
| `ASSEMBLY_ROOT_ID == "frame_plate"` needs box | **Confirmed** `scene3dLayout.ts:35,66-67` |
| 15min situar-eligible = 4 keys | **Confirmed** (below) |
| `esc`→`battery`, `battery`→`flight_controller` poses | **Confirmed** |
| Zero `mounted_on` on 15min projected nodes | **Confirmed** — all `mounted=None` |

### Census recount — `workspace/autonomía-15min-d2fe43e72976/state.json`

`project_spatial_nodes_from_path` → **15** nodes.

| Draggable boxes | Non-draggable disks | No geometry |
|---|---|---|
| `esc`, `battery`, `flight_controller`, `sensors` | `motors`×4, `propellers`×4 | `frame` + 5 parts + connector/adapter/harness |

Matches report §B.

---

## Notes

### N1 — Keep `B1-ux-situar` as first ★ (do not bundle silhouette/novice)

FATAL for multi-box situar is **selection/hit affordance + unfiltered picker**, not missing Product B. IC must stay thin: copy/affordance for “background drag moves the **selected** piece” + picker candidate narrowing. No new pose semantics, no `isDraggableSolid` change, no plate L×W invent.

### N2 — Overlap `B1-ux-situar` vs `B1-origin-assist`

Report puts **origin filtering** inside first Buy **and** lists `B1-origin-assist` as next cola. At IC time pick **one** home:

- **Option A (prefer):** `B1-ux-situar` includes a **minimal** filter (e.g. prefer `mounted_on` target if set + assembly root when boxed + otherwise all boxes still listed but labeled) — then `B1-origin-assist` shrinks or becomes B0.  
- **Option B:** `B1-ux-situar` = nested-hit affordance/copy **only**; picker filter waits for `B1-origin-assist`.

Do not ship two ICs that both rewrite `boxOriginCandidates`.

### N3 — Live poses are already “wild” (contributes to FATAL feel)

Cursor sees persisted Δmm on the order of **hundreds** (`battery` ≈ −979/−497 mm vs FC; `esc` ≈ −491/−261 vs battery). That is consistent with confused situar gestures under mechanism 1/2 — not a separate Buy, but IC smoke should **reset or re-declare** sane poses on a demo project before ACCEPT, and not treat current 15min numbers as golden.

### N4 — Zero `mounted_on` on 15min weakens “filter by mount” alone

Projected `mountedOn` is **null for every key**. Origin-assist that **only** shows `mounted_on` targets would yield an **empty** preferred list on this project until Continuity Conn walk. IC for any filter Buy must define fallback when no mounts exist (all boxes / root-only / explicit empty state) — never silent default origin.

### N5 — Prior ACCEPT smokes reconciled, not reopened

Nested-hit / Situar UX / free-camera ACCEPT stay valid for their scoped smokes. This investigation does **not** require reopening them; it requires a **new** Buy for the N>1 multi-draggable failure mode their smokes never covered.

### N6 — `B0` still legitimate

If Engineer prefers teaching Continuity CLI only and living with Product A racimo, ★ **B0** is honest. Cursor still recommends `B1-ux-situar` because the multi-box hit confusion is a product footgun on every project that has ≥2 situable boxes.

---

## Engineer ★ menu (from report + review)

| ★ | Meaning | Cursor lean |
|---|---|---|
| **`B1-ux-situar`** | Nested-hit multi-box affordance/copy + (optional) picker honesty — **no** new pose semantics | **Recommend first** |
| `B1-origin-assist` | Rank/filter origins by `mounted_on` + root | Next — or fold minimal into first IC (N2) |
| `B0` silhouette | Racimo stays product until plate box / Option B caliper | Keep |
| `DEFER` silhouette code | Activates when `frame_plate` becomes a box | Keep |
| `B0` novice pack / copy-situar | No evidence to buy now | Keep |
| Parked | Conversation Engine · invent mm · Three.js · Fit VERIFIED · N BOM | Keep |

---

## Done / next

1. Engineer ★ **`B1-ux-situar`** (or **B0**).  
2. If ★ Buy → Cursor writes Implementation Contract (thin; resolve N2/N4 in §locks).  
3. Claude implements only after IC ★.

**No implementation in this review.**
