# Engineer smoke — Board drag → Continuity pose B1

**Date:** 2026-09-10  
**IC / Review:** [IC](implementation_contract_board_drag_pose_b1.md) · [review](implementation_review_board_drag_pose_b1.md)  
**Project:** `autonomía-de-5min` · Board Situar ON  
**Verdict:** **ACCEPT** (core write path) + **UX follow-up required**

---

## Smoke

| # | Check | Result |
|---|---|---|
| 1 | Situar ON → drag singleton solid → pose persists (same writer) | **PASS** — Engineer moved pieces |
| 2 | No drag on station copies expected | Not contested |
| 3 | Usable situar viewport + fluid drag | **FAIL product** — see note |

---

## Engineer feedback (screenshot)

- Pane 3D too small (`height: 260px`) — hard to situate.  
- Need **larger** situar surface + ability to **zoom/deepen** further.  
- Drag feels **not fluid** vs 2D cards (today: no live preview; commit only on drop).

→ [engineer_note_board_situar_ux_followup.md](engineer_note_board_situar_ux_followup.md) · IC when ★.
