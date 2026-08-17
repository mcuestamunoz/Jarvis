# Implementation Review — Continuity Hardening Investigation + Design

**Date:** 2026-08-15  
**Reviewer:** Cursor (Implementation Review)  
**Contract:** [implementation_contract_continuity_hardening_investigation.md](implementation_contract_continuity_hardening_investigation.md)  
**Artifacts:** [investigation_continuity_hardening.md](investigation_continuity_hardening.md) · [design_continuity_hardening.md](design_continuity_hardening.md)  

**Verdict: PASS WITH NOTES**

Zero product `src/` / `library/` / `docs/system_map/` edits in this cut (confirmed against review intent). Investigation is System-Map–first, findings mapped to C-xxx, and critical claims spot-checked against live code.

---

## Spot-checks (code)

| Claim | Result |
|---|---|
| Force-propellers fires when `"propellers" in expected_keys` and all specs generic | **CONFIRMED** `orchestrator.py:1771-1776` |
| `"Hélices registradas."` writer | **CONFIRMED** `orchestrator.py:1700` |
| NxP regex `\b(\d+)\s*x\s*(\d+(?:\.\d+)?)\b` matches `"1x 2306"` → diameter/pitch | **CONFIRMED** `aerial.py:102-108` + completeness `"high"` when diameter present (`:125-131`) |
| Cross-block refuse `"no cross-block jump"` | **CONFIRMED** comment `orchestrator.py:1150` |
| C-052 strong-intent before owns-input | **CONFIRMED** `:420-425` — owns-input never reached if `strong in _ITERATE_PREEMPT_INTENTS` |
| Owns-input only `DEFINE` + `step==2` | **CONFIRMED** `:442-445` |
| `format_no_thrust_candidate_message` uses unfiltered `list_motors()` max | **CONFIRMED** `motor_catalog_assist.py:335-342` |

Root synthesis (one authority pattern + G15 messaging leaf) is consistent with evidence.

---

## Notes (do not block ★ lock)

### N1 — ★4 tiebreak needs a concrete composite gate

“First-declared-wins” alone is incomplete for G14: there is **no** `force-motors` path today. On `expected_keys=["motors","propellers"]`, motors inference stays `generic_component` while force-propellers false-positives on `"1x 2306…"`.

Impl contract should specify one of:

1. **Do not force-propellers while `motors` still pending** unless phrase matches a propeller-size heuristic (e.g. diameter in a plausible inch range, or explicit hélice keywords); **or**
2. Prefer motors when composite and phrase matches motor-shaped tokens (KV / `2306` / `W`) even if motors completeness is still medium; **or**
3. Tighten NxP so model numbers are not treated as pitch.

Recommend locking ★4 as: **(1) + first-declared preference when multiple force candidates exist**, and require P1/P2 regressions.

### N2 — ★2 refuse (b) vs overall success criterion

Contract §6.1.7 / design §7 want a full BOM walk **without** `cancelar` as a required ritual. Refuse (b) still requires `cancelar` for retarget. That is acceptable for Slice 2 **if** Engineer accepts: continuity = no silent wrong-wizard / no silent wrong write; explicit cancel remains the only cross-block writer (FN-021-safe). Call this out in ★2 lock text so CLI acceptance isn’t over-claimed.

### N3 — Slice 1 alone does not restore full BOM walk

Agree Slice 1 closes the worst data corruption. Overall success criterion still needs Slice 2 (at least refuse honesty) + Slice 4 for iterate paths. Roadmap should not imply “G14 fixed ⇒ Continuity done.”

### N4 — G10 interaction

Agree: G10 widened G11-B surface; did not create it; do not regress materials vocabulary.

---

## ★ lock recommendation (Cursor → Engineer)

| ★ | Recommend |
|---|---|
| **★1** | **One contract, four slices**, order 1→4. Optional: ship Slice 1 as first impl PR inside that contract for faster CLI proof. |
| **★2** | **(b) Refuse** + honest one-liner. Defer retarget (a) to a later FN if ergonomics demand it. Accept that cancelar remains for cross-block (N2). |
| **★3** | **(a)+(b)** as design proposes. Reject (c) as primary. |
| **★4** | Lock **composite gate (N1 option 1)** + first-declared when multiple forces apply. |
| **★5** | **Yes** — list-motors escape in `ParamDefinitionSession.answer` (mirror G10 ★8 shape). |
| **★6** | **Yes** — filtered max (or explicitly labeled unfiltered). |
| **★7** | **Out of Continuity Hardening** — messaging-only; no thrust gate in this cut (keeps scope tight). Revisit as separate UX finding if needed. |

---

## Next

Engineer locks ★1–★7 (or amends) → Cursor writes **Continuity Hardening Implementation Contract** (Slice 1 can be first shippable unit) → Claude implements → Cursor reviews → CLI BOM walk.
