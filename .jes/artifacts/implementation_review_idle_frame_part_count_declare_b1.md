# Implementation Review — IDLE frame-part count declare B1

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_idle_frame_part_count_declare_b1.md](implementation_contract_idle_frame_part_count_declare_b1.md)  
**Report:** [implementation_report_idle_frame_part_count_declare_b1.md](implementation_report_idle_frame_part_count_declare_b1.md)

## Verdict

**PASS WITH NOTES**

IC locks held. IDLE bridge is thin, reuses extract + `upsert_frame_part`, stays IDLE, refuses LLM on covered phrases. Suite **2686**. Closable after Engineer smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| IDLE wire after fit-attestation, before FN-005 | **Pass** — `orchestrator.py` ~1075–1088 |
| `extract_all_frame_part_properties` / `upsert_frame_part` reused | **Pass** — zero `aerial.py` diff |
| Frame completeness ≠ low gate | **Pass** — T4 + code |
| Root guard mass/size/config/wheelbase → `None` | **Pass** — T4b |
| Stay IDLE · no `_set_pending_next_block` · no DEFINE_MISSING | **Pass** — T1 mode assert |
| Message `Frame partes: …×N` | **Pass** — T1 |
| G-N1 wizard path untouched | **Pass** — T5 + `test_frame_parts_freetext_gn1` green |
| No N≠4 layout / no Rooster seed / no version bump | **Pass** — `0.4.1` · no library/ui in this Buy |
| Suites | **Pass** — targeted 7 + G-N1 11; report full suite **2686**; Cursor re-ran targeted **18 passed** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Dispatch order attest → frame-part → FN-005 | **Confirmed** |
| Duplicate gate (not shared helper) per IC allowance | **Confirmed** |
| `standoffs aluminio` does not rewrite `frame.material` | **Confirmed** (T3) |
| Version `0.4.1` | **Confirmed** |
| UI baseline note (83 vs IC 80) outside this Buy | **Accepted** — prior Fit/Situar cycle |

---

## Notes

### N1 — Cross-reference asymmetry (not a FAIL)

IDLE docstring points at G-N1. The G-N1 wizard comment block (~4510) does **not** yet point back at `_try_handle_idle_frame_part_declare`. Report overstated “both docstrings pointing at each other.” Optional one-line comment on the wizard branch when convenient — not required to close this Buy.

### N2 — Remaining risk (accepted)

Intentional gate duplication: future extract/writer signature changes need both call sites. Documented on the IDLE method. Acceptable per IC §1.

### N3 — Smoke

Walk IC §6 on a live project with frame already declared.

---

## Phase

Implementation **CLOSED** for review. **Engineer smoke pending.** Package `0.4.1` · suite **2686**.
