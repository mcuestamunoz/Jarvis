# Investigation Review — Mission → functional payload holes before propulsion (B0)

**Date:** 2026-09-15  
**Reviewer:** Cursor (Engineer Interface) — independent of investigator session  
**Against:** [contract](investigation_contract_mission_functional_payload_holes_b0.md) · [report](investigation_report_mission_functional_payload_holes_b0.md)

**Verdict:** **PASS WITH NOTES** — ready for Engineer ★ on Buy shape (or B0 park)

---

## Checklist (contract Q1–Q5 · sections A–F)

| Gate | Result |
|---|---|
| Q1 create path exhaustive / mission-blind | **Pass** — `PROMPTS` + live census vigilancia vs 10-min autonomy regex luck |
| Q2 architecture holes + B-path | **Pass** — SYSTEM_DEFINITION auto-launch + `BLOCK_ALIASES` + dead-end stubs verified independently |
| Q3 mass/energy coupling | **Pass** — `payload_kg` opaque scalar; mirrored-param pattern correctly named as future mass entry |
| Q4 ranked Buys incl. B0 | **Pass** — table D present; primary = B1-min (a) |
| Q5 Continuity observe only | **Pass** — `high_margin` → increase_payload cited; park recommended; sequencing after holes |
| No implement / no invent / read-only | **Pass** — report claims honored; no src/library edits in this investigation |
| Non-goals (firmware, montage, CE) | **Pass** — §F explicit |

---

## Independent checks (Cursor)

1. `normalize_block_alias("camara")` → `"perception"`; `BLOCK_TO_COMPONENTS["perception"]` → `["cameras","lidar"]`.  
2. `orchestrator.py` ~6804–6810: after successful `create_project`, **always** starts `SystemDefinitionSession`.  
3. `_build_component_stubs(["cameras",…])` → `completeness="low"`, `suggested_key=None`.  
4. `aerial_registry`: **7** rules only — `propellers`, `motors`, `esc`, `battery`, `frame`, `flight_controller`, `sensors`. **Zero** `cameras` / `lidar` / `radio_module` / `payload_bay` / `arm` strings in `aerial.py`.  
5. `reasoning_layer.py`: `increase_payload` gated on `has_simulation` + `high_margin` only — no `objective` read.

**Headline finding stands:** offering SYSTEM_DEFINITION **B** for perception/communication/payload/manipulation today can create **permanently incomplete BOM rows** with no resolving Continuity path — a **live honesty bug** in shipped code, not a hypothetical.

---

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | Agree / primary | ★ lean **B1-min (a)**: gate aliases / refuse accepting blocks whose component keys lack a `ComponentRule` (fail closed). Smallest surface; closes the dead-end without new schema or invented camera physics. |
| **N2** | Soft | Branch **(b)** (minimal ComponentRules without catalog) is a valid follow-on, but must not invent mass/mm — report already warns. Do not start (b) without Engineer bag for what “identity-only camera” means. |
| **N3** | Soft | **Wizard nudge** (vigilancia → point at B) is useful only **after** (a) or the B-path is no longer poisonous. Sequencing: fix dead-end → then nudge. |
| **N4** | Info | Motors stubs also start `suggested_key=None`; difference is a later rule can fill them. Report’s contrast is correct for `cameras`. |
| **N5** | Park | Continuity “Aumentar carga útil” vs mission — confirmed observe; ★ only after inspectable mission holes exist. |

---

## Recommended Engineer ★ menu

| Choice | Meaning |
|---|---|
| **★ B1-min (a)** | IC: gate SYSTEM_DEFINITION B-options / accept path until ComponentRule exists for target keys |
| **★ B1-min (a) + nudge** | Same + one suggest-only create-confirm hint (after gate) |
| **★ B1-min (b)** | Minimal identity ComponentRules for cameras/… (needs Engineer definition of “enough”) |
| **B0 park** | Docs-only; **leaves live bug open** — not recommended once N1 is understood |
| **Catalog family** | Park until cited camera/link bags exist |

---

## Verdict

**PASS WITH NOTES** — investigation meets the contract; central finding independently reproduced. Awaiting Engineer ★ on Buy shape before any implementation IC.
