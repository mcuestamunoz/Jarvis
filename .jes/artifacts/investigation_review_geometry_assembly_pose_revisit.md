# Investigation Review — Geometry assembly pose revisit (after visualizar-3D)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_assembly_pose_revisit.md](investigation_contract_geometry_assembly_pose_revisit.md)  
**Report:** [investigation_report_geometry_assembly_pose_revisit.md](investigation_report_geometry_assembly_pose_revisit.md)  
**Parents:** 2026-09-07 pose B0 Defer · visualizar-3D CLOSED (click-inspect + CSS 3D) @ **2429**

## Verdict

**PASS WITH NOTES**

Default lean **B0 — keep defer** is correct. The report **reaffirms** (does not supersede) the 2026-09-07 B0. Condition 1 is honestly scored **Met — narrowly** and correctly **not** used to Buy relative-assembly pose. Conditions 2 and 3 are **Not met**. CSS 3D row and `selectedId` are not a reference frame. **No READY pose IC.** Fit stub stays **QUEUED**.

Engineer ★ still required to **lock keep-B0** (or override). Naming a separate hole-pattern KNOW track is allowed; this review does **not** open it.

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + one paragraph | **Pass** — B0 keep defer |
| Delta table vs 2026-09-07 | **Pass** |
| §E 1/2/3 scored Met / Not met + cite | **Pass** |
| B–D answered; no pose schema sketched | **Pass** — §C decline is correct (see N3) |
| Reaffirm vs supersede | **Pass** — reaffirm with a more precise scorecard |
| 3D row ≠ pose; click-inspect ≠ frame | **Pass** |
| Fit stub still QUEUED; no code / no IC | **Pass** |
| Multiplicity / 3D-pane chrome out | **Pass** |
| Fourth reversal invented to escape B0 | **Pass** — none |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| iFlight `source_note` lists 30.5×30.5 and 20×20, **not seeded** as fields | **Confirmed** — `library/frames/_datos.json` `iflight_xl7_v4_7in.source_note` (“not seeded here, out of scope for Geometry-for-all”) |
| Hole numbers exist as structured seed keys | **None** — grep `library/` for `hole_pattern` / `hole_spacing` / `mounting_hole` hits only that prose note |
| Live demo frame is **not** iFlight | **Confirmed** — `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` binds `armattan_rooster_5in` |
| `ComponentSpec` still `parent_key` + `mounted_on` only | **Confirmed** — `action_schema.py:171,184`; comment at 180 still “No pose” |
| `state_schema.py` pose/offset/orientation/origin_key | **Empty grep** |
| Only schema `origin` = `HandoffContext.origin` | **Confirmed** — `action_schema.py:246`, `Literal["engineering_intent"]` |
| `layoutSolidsRow` cannot take card `x` / `mountedOn` | **Confirmed** — signature `{ id, geometry }[]`; U5 still in `scene3dLayout.test.ts` (`x: 9999`) |
| `DEFAULT_TILT` 55° / −30° | **Confirmed** — `Scene3D.tsx:6` |
| Fit stub status | **Confirmed** — `QUEUED — DO NOT IMPLEMENT` |
| Engineer written risk-acceptance of scalar+prose | **None** in `engineer_lock_*.md` |

---

## Agreement with report core

1. **Visualizar-3D does not reverse B0** — correct and load-bearing.  
2. **Condition 1 Met ≠ Buy pose** — the parent §E parenthetical already classified stack bolt patterns as a **different question**. Scoring Met on the letter while keeping B0 for *this* rung is the honest move.  
3. **Condition 2 still the blocker for any mm bag** — agree. Camera tilt is visor chrome.  
4. **`procede` on this investigation ≠ condition 3** — agree (IC lock).  
5. **Future pose could project into `Scene3D` later** — agree as plumbing fact, not a design Buy.  
6. **Do not permanently Reject** — agree; condition 1 arriving is evidence the door is evidence-gated, not nailed shut.

---

## Notes

### N1 — Condition 1 is catalog **prose**, not demo KNOW

The 30.5 / 20 mm figures live in an iFlight XL7 **`source_note`**. They are not structured fields. The live Board project is **Armattan Rooster**. Do not read today’s 3D pane or demo frame as carrying this fact.

### N2 — Frame-page stack holes ≠ body-frame origin

On a **frame** retailer page, 30.5 / 20 mm usually names the **stack-mount patterns the plate offers**, not “FC origin relative to frame origin.” Still **orthogonal** to relative-assembly pose (no named origin, no axes, no which-hole-to-which-hole). If Engineer later ★ hole-pattern KNOW, seed it as **self-geometry of a mount interface**, not as pose.

### N3 — No pose-bag sketch despite one Met

IC §C allowed a field sketch if any condition was Met. The report declined because the Met condition is the **orthogonal** class and 2/3 are Not met. **Agree** — sketching `x_mm` here would be the conflation N2 forbids.

### N4 — Hole-pattern track is named, not opened

Report names a narrower “self-geometry hole-pattern KNOW” investigation and **does not** recommend opening it now. This review concurs: **not** today’s IC, **not** a rider on keep-B0.

### N5 — Fit stays frozen as default-next

Keep-B0 does **not** auto-★ `"cabe"`.

---

## Recommended Engineer moves

| Choice | Effect |
|---|---|
| ★ **Keep B0** (recommended) | Pose stub stays DEFERRED; Geometry idle on this rung; no schema |
| ★ Hole-pattern KNOW (optional, orthogonal) | New **investigation contract** only — not pose, not fit |
| ★ Override (axis convention or written scalar+prose risk) | Explicit new ★ + READY IC later — do not revive the 2026-09-07 stub as-is |
| ★ Skip to fit | **Forbidden** without a separate fit investigation ★ |

---

## Phase

Investigation **CLOSED** — Engineer ★ **Keep B0** (2026-09-08). Pose stub stays DEFERRED. Next = [origin/axes investigation](investigation_contract_geometry_pose_origin_axes.md). No implementation. Package `0.3.8` · suite **2429**.
