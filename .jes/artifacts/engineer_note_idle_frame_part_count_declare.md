# Engineer note — IDLE frame-part count declare (cola)

**Date:** 2026-09-10  
**Authority:** Engineer — IDLE `6 standoffs` jumped LLM; real frames use 6/8 posts, not only 4  
**Status:** COLA — not PRIORIDAD · no IC until ★ after Board drag B1 (or insert)  
**Parents:** G-N1 parts-only (wizard-only today) · [standoff count gate B4-min](implementation_contract_geometry_standoff_count_gate_b4.md) CLOSED @ **2661**

---

## Pain

In IDLE (ASSEMBLY READY), phrases like `6 standoffs` / `6 separadores` parse in `extract_all_frame_part_properties` but **never reach** `upsert_frame_part` — G-N1 parts-only is gated on `DEFINE_MISSING` + `expected_keys[0]=="frame"`. Input falls to the LLM.

Without `frame_standoff.properties.count`, B4-min omits corner copies (no default 4). Engineer cannot set count from the normal CLI chat.

---

## Product need

1. **IDLE bridge (this cola item):** deterministic parts-only upsert in IDLE when frame already exists — same extract + `upsert_frame_part`, never LLM, never rewrite root from a part clause.  
2. **Related later (not this note’s Buy):** visor layout for N≠4 (6/8 posts). B4-min only draws corners when `count==4`; N=6/8 still one box until a dedicated layout Buy.

---

## Suggested Buy shape (when ★)

Thin IC: IDLE `extract_all_frame_part_properties` → `upsert_frame_part` when frame completeness ≠ low and no root mass/size/config/wheelbase update — mirror orchestrator G-N1 block (~4316) into IDLE beside pose/envelope bridges. Tests: `6 standoffs` sets count without LLM; `standoffs aluminio` still material-only; refuse inventing N from photos.

**Out until separate ★:** N=6/8 station formula · invent Rooster `standoff_count` seed · Conversation Engine.
