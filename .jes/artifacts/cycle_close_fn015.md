# Cycle Close — FN-015

> ⛔ **SUPERSEDED by G23 (2026-08-20)** — the feature closed here was
> removed in full. See
> [`.jes/artifacts/implementation_contract_g23_remove_fn015.md`](implementation_contract_g23_remove_fn015.md)
> and [`.jes/artifacts/implementation_report_g23_remove_fn015.md`](implementation_report_g23_remove_fn015.md).
> `tests/test_fn015_pending_help.py` (referenced below) was deleted;
> replaced by `tests/test_g23_fn015_removed.py`. Kept as historical audit
> trail only.

**Closed:** 2026-08-08T13:56:38Z
**Verdict:** PASS WITH NOTES

## Delivered
- `is_help_define_pending_phrase` in `acquisition_target.py` (exclude FN-005 choose; exclude declare+named block; exact catch-phrases; ayudame+definir/valor/poner).
- DEFINE_MISSING: after FN-013, before analyze→LLM → `_help_current_pending_acquisition` (pending[0] only).
- IDLE: after FN-014 → `_try_help_define_pending_idle` opens real next gap + help.
- Component hints via `_COMPONENT_PROMPTS`; assisted motors → `offer_catalog_help`; no battery when pending is propellers.
- Tests: `tests/test_fn015_pending_help.py` (9). Suite: 1485.

## Explicitly not done
- FN-016 navigation / atrás / float-parse on component keys.
- Conversation Engine; ANALYZE_PATTERNS rewrite; silent energy diversion.

## Notes for FN-016
- Marker breadth vs nuanced LLM help questions (accepted).
- Named wrong-block help while wizard open still may leak to LLM.
