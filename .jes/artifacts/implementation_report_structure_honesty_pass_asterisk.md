# Implementation Report — Structure honesty (`PASS *`)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_structure_honesty_pass_asterisk.md](implementation_contract_structure_honesty_pass_asterisk.md)
**Baseline:** tag `v0.3.6` · suite closed at 2197 · Control parity `PASS *` already shipped

---

## Files changed

- `src/jarvis/adapters/cli/main.py` — `_render_readiness_block` refactored from a single `control_pass` boolean into a small ordered `_PASS_DECLARATION_FOOTNOTES: tuple[tuple[str, str], ...]` table (`("structure", ...)`, `("control", ...)`), so any subsystem's `PASS *` + footnote is driven by one lookup instead of duplicated if/else branches. New `_STRUCTURE_DECLARATION_FOOTNOTE = "* Structure: identidad / clase nivel A — sin geometría de chasis"`. `_CONTROL_DECLARATION_FOOTNOTE`'s string is byte-identical to before (untouched). Footnotes are collected while iterating `_READINESS_SUBSYSTEM_ORDER`, so they render in that same order (structure before control) without hardcoding it a second time.
- `tests/test_engineering_readiness_cli.py` — one pre-existing test (`test_cli_control_not_pass_has_no_asterisk_or_footnote`) asserted a blanket `"*" not in text` using the `_ASSEMBLY_READY_READINESS` fixture, which has `structure=PASS` — that assertion's premise (no asterisk can exist anywhere in that fixture) is exactly what this IC changes. Narrowed it to the two assertions it actually meant: no `Control        PASS *` line, no Control footnote — not weakened, made precise. New tests added (below).

No edits to `engineering_readiness.py`, `project_continuity.py`, `project_closure.py`, `classify_component`, `_frame_completeness`, `BLOCK_TO_COMPONENTS`, `library/`, or the `_CONTROL_DECLARATION_FOOTNOTE` string — confirmed via `git diff --stat` showing zero diff on `engineering_readiness.py` and `library/frames/_datos.json`.

## Behavior changed

- Whenever the `structure` subsystem's ERF verdict is `PASS`, the CLI readiness line now reads `Structure      PASS *`, with a footnote `* Structure: identidad / clase nivel A — sin geometría de chasis` appended after the nine subsystem lines (before `PROJECT STATUS:`) — same posture as Control's existing `PASS *`.
- Blanket rule, as specified: fires regardless of `frame_class_compatibility_state` (including the `"not_required"` case, where zero class checks ran) — matching Control's own unconditional treatment and avoiding a second-order claim-hygiene gap (a PASS that ran no class check looking identical to one that ran and passed).
- When both Structure and Control are PASS, both footnotes render, Structure's first (natural consequence of `_READINESS_SUBSYSTEM_ORDER` placing `structure` before `control`, not a separate ordering rule).
- **Not changed:** `structure`'s verdict value (`"PASS"` stays `"PASS"` in the JSON/dataclass), `ASSEMBLY_READY` eligibility, `_derive_subsystem_verdict`/`_derive_overall`, any other subsystem's rendering, the margin-weak `NOTE:` line (independent, can coexist).

## Tests added/updated

- `tests/test_engineering_readiness_cli.py`: `test_cli_structure_pass_gets_declaration_asterisk_and_footnote`, `test_cli_structure_not_pass_has_no_asterisk_or_footnote`, `test_cli_structure_and_control_both_pass_show_both_footnotes_in_order` (asserts Structure's footnote appears before Control's by string position). One existing test narrowed (see above).

## Tests executed

- Targeted: `pytest tests/test_engineering_readiness_cli.py -q` → 18 passed.
- Full suite: `pytest -q` → **2200 passed** (2197 baseline + 3 new tests), zero failures, zero skipped, zero weakened.

## Residual

- Graph model IC ([implementation_contract_structure_b_parts_graph.md](implementation_contract_structure_b_parts_graph.md)) is next per the ship order this IC's parents named — not started here.
- The footnote wording covers "identity / LEVEL A class" generically; it does not distinguish the `"not_required"` case from the `"class_compatible"` case in the copy itself (both render the same asterisk+footnote) — this was an explicit, reasoned choice (§2.1 of the IC), not an oversight.
