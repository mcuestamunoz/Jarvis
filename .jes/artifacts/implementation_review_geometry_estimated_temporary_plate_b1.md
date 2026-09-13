# Implementation Review — Estimated-temporary plate envelope B1

**Project:** Jarvis  
**Date:** 2026-09-13  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_geometry_estimated_temporary_plate_b1.md) · [report](implementation_report_geometry_estimated_temporary_plate_b1.md)  
**Verdict:** **PASS WITH NOTES**

**Checkpoint:** package **`0.4.1`** · targeted **18 passed** · report claims full suite **2785**

---

## Checklist vs IC

| Gate | Result |
|---|---|
| `PropertyValue.source` += `estimated_temporary` | **Pass** |
| Plate-only writer (`is_frame_plate_key`) | **Pass** — `set_estimated_temporary_plate_envelope` |
| Continuity provisional parse + IDLE before plain envelope | **Pass** |
| §0.1 120×55 not body/wb rejects | **Pass** (fixture + report check) |
| `cabe` refuse on estimated dims | **Pass** — status `estimated_dims` + honest copy |
| Fit attestation SET refuse | **Pass** — via non-`overlap` status (no writer weaken) |
| No `library/` plate L×W seed | **Pass** |
| Disclosure Continuity + Board `geometría` field | **Pass** |
| Replace via plain `declared` / clear | **Pass** — T6 |
| No version bump / no silent `workspace/` | **Pass** (Path-C: Engineer types live) |
| T1–T7 | **Pass** (18 tests cover + extras) |

---

## Notes

| ID | Note |
|---|---|
| **N1** | Gate (b) as free consequence of (a) is correct and preferable to duplicating logic in the attestation writer. |
| **N2** | `"declara la batería estimada …"` → `NONE` → plain envelope may write battery as `declared`, dropping “estimada”. Acceptable for this Buy’s plate-only scope; future non-plate estimated Buy must not leave that silent drop. |
| **N3** | Live apply = Engineer types on `autonomía-de-5min` (not Claude mutating `workspace/`) — matches IC “no silent workspace” + Path-C precedent. |
| **N4** | Smoke: ensure `frame_plate` has `thickness_mm`, or use triple `120 x 55 x H`. Phrase: `declara frame_plate estimada 120 x 55 mm`. |
| **N5** | Process: concurrent `engineering_state.json` edits flagged — skim before next sync. |

---

## Smoke (Engineer) — IC §3

1. `declara frame_plate estimada 120 x 55 mm` (or + H) on 5min → box + disclosure.  
2. `cabe` involving that plate → refuse (no overlap verdict).  
3. `declaro verificado` → refuse.  
4. Situar/pose boxed avionics onto plate → layout OK.  
5. Catalog MY5/GEP still without plate L×W.

---

## Verdict

**PASS WITH NOTES** — ready for Engineer smoke. After ACCEPT, layout/root architecture path is open with provisional honesty; caliper later → plain `declared` replace.
