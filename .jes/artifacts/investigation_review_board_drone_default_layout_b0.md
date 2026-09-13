# Investigation Review — Drone default layout / main-plate assembly root (B0)

**Date:** 2026-09-13  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_board_drone_default_layout_b0.md](investigation_contract_board_drone_default_layout_b0.md)  
**Report:** [investigation_report_board_drone_default_layout_b0.md](investigation_report_board_drone_default_layout_b0.md)  
**Parents:** Continuity spatial assembly ★ · Product A/B · #4g-A plate CAD B0 · Situar experience B1 (separate ergonomics)

## Verdict

**PASS WITH NOTES** · recommended first Buy **`B1-mount-standard-assist`** (Cursor keeps Claude’s lean).

“Main plate as assembly start + situate by dimension” is **not shipped** and must not be claimed. Root code already exists; it is **data-blocked** (no `frame_plate` box). Standard mount graph is **partially** expressible today — assist Buy is the only zero-data next step. Plate box / stack rule / cited layout pack stay **DEFER**/ranked. No IC until Engineer ★.

---

## Checklist

| Criterion | Result |
|---|---|
| §§A–G present | **Pass** |
| Root activation cited (`ASSEMBLY_ROOT_ID` + box gate) | **Pass** |
| Live census 5/10/15min read-only | **Pass** — Cursor re-checked (below) |
| Graph vs Continuity subjects/targets | **Pass** — `_SUBJECT_PATTERNS` + arm target |
| Envelope-only pose honesty + feature-lock quote | **Pass** |
| Ranked Buys incl. B0/DEFER; single first lean | **Pass** — `B1-mount-standard-assist` |
| No invent mm / no implement / Situar UX not reopened as layout | **Pass** |
| Decision card usable for ★ | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| `ASSEMBLY_ROOT_ID == "frame_plate"` needs box | **Confirmed** `scene3dLayout.ts:35,66-67` |
| No live project has `frame_plate` geometry | **Confirmed** — 5/10/15min all `None` |
| 15min pose **cycle** esc↔battery↔FC | **Confirmed** — `esc→battery→FC→esc` (+ sensors→FC) |
| Subjects = FC/ESC/motors/battery/sensors/propellers only | **Confirmed** `mounted_on_declare_assist.py:63-70` |
| `frame_arm` target via `_ARM_RE`, not subject | **Confirmed** |
| prop→motor declared on 5min/10min | **Confirmed** |
| motors→frame_arm on live 10min **now** | **N1** — raw `motors.mounted_on` is **None** today (grammar still yes; Conn smoke was historical) |

---

## Notes

### N1 — Live `motors→arm` under-declared

Report cites Conn smoke for 10min `motors→frame_arm`. Fresh `state.json`: **no** motors mount on 5/10/15min. Does **not** weaken “expressible”; it **strengthens** the assist Buy (checklist would flag undeclared motor→arm). IC for assist must use **live** undeclared edges, not assume smoke state.

### N2 — Keep `B1-mount-standard-assist` first

Zero new citation; suggest Continuity phrases for expressible edges only; user confirms; never auto-write pose. Do **not** widen subjects (`frame_arm`, kit hardware) inside that first Buy unless Engineer ★ a separate noun-vocab Buy.

### N3 — `B1-plate-box` stays DEFER (data)

Agree: activating root needs L×W (caliper Option B or new cite). Code path already shipped. Do not invent from body 175×173.

### N4 — Pose cycle on 15min is evidence, not this Buy’s fix

Cycle is a live consequence of no root + sibling poses. Optional later hygiene (detect/refuse cycles in writer) is **out** of mount-assist unless Engineer folds it in. Mention in smoke notes when situating 15min.

### N5 — `B1-stack-rule` never silent

Agree with §C / feature lock. Any envelope stacking needs its own ★ + disclosed copy.

### N6 — `B0` still legitimate

If Engineer wants no more Continuity UX code this cycle, ★ **B0** and wait for plate caliper before any spatial “standard.”

---

## Engineer ★ menu

| ★ | Cursor lean |
|---|---|
| **`B1-mount-standard-assist`** | **Recommend first** |
| `B0` | Valid pause |
| `B1-plate-box` | **DEFER** until citation/caliper |
| `B1-stack-rule` / `B1-layout-pack-cited` | After plate (or narrow prop-on-motor ★) |
| Parked | LLM auto-pose · invent plate · Three.js · reopen Situar as layout |

---

## Done / next

1. Engineer ★ **`B1-mount-standard-assist`** (or **B0** / amend).  
2. If ★ assist → Cursor writes Implementation Contract (suggest-only; live undeclared matrix; no subject-vocab widen unless locked).  
3. Claude implements only after IC ★.

**No implementation in this review.**
