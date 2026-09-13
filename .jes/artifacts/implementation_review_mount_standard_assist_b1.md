# Implementation Review — Mount standard assist B1 (`B1-mount-standard-assist`)

**Project:** Jarvis  
**Date:** 2026-09-13  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_mount_standard_assist_b1.md) · [report](implementation_report_mount_standard_assist_b1.md)  
**Verdict:** **PASS WITH NOTES**

**Checkpoint:** package **`0.4.1`** · targeted tests **16 passed** (`tests/test_mount_standard_assist_b1.py`) · report claims full suite **2763**

---

## Checklist vs IC

| Gate | Result |
|---|---|
| Pure suggest-only builder from live `components` | **Pass** — `build_mount_standard_checklist`; no writer import |
| In-scope edges only (prop→motors, motors→arm if arm, stack→plate/frame) | **Pass** — arm-as-subject / harness / pose absent |
| Target pick: 1 plate / bare frame / AMBIGUOUS 2+ | **Pass** — `_plate_target`; T4 covered |
| Silent write forbidden | **Pass** — IDLE bridge returns message only; confirm = retype via existing declare bridge |
| Triggers documented (1–2 Spanish) | **Pass** — `montajes estándar` · `qué falta montar` |
| Example phrases parse as SET (T5) | **Pass** — real `parse_mounted_on_declare`; bare-frame phrase also SET (spot-check) |
| No pose / plate L×W / subject-vocab widen / Scene3D / version / `workspace/` | **Pass** (by inspection + report) |
| T1–T6 | **Pass** — T1–T5 in new file; T6 package `0.4.1` + suite claim 2763 |
| Pattern: thin module + IDLE after mount-declare | **Pass** — wired immediately after `_try_handle_mounted_on_declare` |

---

## Notes

| ID | Note |
|---|---|
| **N1** | UX = **retype phrase**, not number→writer. Allowed by IC §0#5; documented. Smoke may feel friction — additive numbered pick is optional follow-up, not a FAIL. |
| **N2** | Stack subjects: any existing `mounted_on` omits the row (incl. non-standard e.g. `sensors→esc`). Prop/motor edges only omit when the **standard** target is already set (`!= motors` / `!= frame_arm`). Honest “missing edge” vs “sub-optimal mount” — by design; do not treat as bug. |
| **N3** | `sensors` uses same plate/frame rule as esc/FC/battery (no prefer-`esc`). Matches IC “single best target” + report rationale; live 15min `sensors→esc` stays off-checklist once declared. |
| **N4** | Process: implementer flagged `git checkout --` on `engineering_state.json` during sync. Session-start git status had that file **already modified**; checkout resets to last commit, so a pre-session uncommitted sync *could* have been discarded. Current file shows a clean 14-line mount-assist delta vs HEAD and mentions prior pending smokes in `current_mode`. **No concrete missing key proven** — Engineer may skim if other cycle notes lived only in that file. |
| **N5** | `orchestrator.py` working tree still carries a large pre-existing uncommitted pile; this Buy’s own footprint in that file is the IDLE gate (~15 lines) + `_try_handle_mount_standard_assist` (~35 lines). Do not attribute the whole orchestrator diff to this cycle. |

---

## Smoke (Engineer) — IC §3

On `autonomía-15min` (few mounts):

1. `montajes estándar` (or `qué falta montar`) → missing standard edges + exact phrases.  
2. Retype one phrase → `mounted_on` set; Board edge if applicable.  
3. Re-trigger → that edge gone.  
4. Confirm: no pose write; no claim that plate box / assembly root activated.

---

## Verdict

**PASS WITH NOTES** — ready for Engineer smoke. Next cola per IC §6: **`B1-plate-box`** (citation/caliper gated; no ★ yet).
