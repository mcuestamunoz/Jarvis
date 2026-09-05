# Implementation Report — Control parity (claim copy B1)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_control_parity.md](implementation_contract_control_parity.md)
**Baseline:** tag `v0.3.6` + claim hygiene in tree · suite closed at 2160

---

## Files changed

- `src/jarvis/adapters/cli/main.py` — `_render_readiness_block`: when the `control` subsystem's verdict is `PASS`, its line gets a trailing ` *`, and one footnote (`* Control: declaración — sin física de control`) is appended after the nine subsystem lines and before the blank line + `PROJECT STATUS:`. No other subsystem line is ever marked. Verdict strings, `PROJECT STATUS` text, and the margin-weak `NOTE:` line (claim hygiene) are unchanged and can co-occur with this footnote.
- `src/jarvis/core/project_closure.py` — new `_bom_completeness_tail(entry)` helper; `format_bom_lines`'s `defined` branch now calls it instead of reading `entry.get("completeness")` directly. Only `key == "flight_controller"` gets the appended ` — identidad, sin dato físico`; every other `defined` entry (motors, battery, propellers, frame, ESC) renders byte-identical to before.
- `tests/test_engineering_readiness_cli.py`, `tests/test_project_closure_v1.py` — new tests (below).

No edits to `engineering_readiness.py` (evidence builders, `_derive_subsystem_verdict`, `_derive_overall`, gap types), `classify_component`, `component_presence_tier`, `_MEASURABLE`, `library/`, `project_continuity.py`, or the `ASSEMBLY_READY`/`NOT_ASSEMBLY_READY` enum strings.

## Behavior changed

- **CLI readiness block:** `Control` line reads `Control        PASS *` (instead of `Control        PASS`) whenever its verdict is `PASS`, with one footnote line naming it declaration-only. `Control` at any other verdict (`INCOMPLETE`/`WARNING`/etc.) is unchanged — no asterisk, no footnote. No other subsystem is ever marked.
- **BOM lines:** a `flight_controller` entry in the `defined` bucket now renders `✓ flight_controller: {name}{...} ({completeness} — identidad, sin dato físico)` instead of `({completeness})`. `sensors` (always `declarative`, never `defined`) and every other component's `defined` line are unchanged.
- **Not changed:** `Control`/any subsystem's verdict value, `overall`/`ASSEMBLY_READY` eligibility, architecture `n/4` counters and "Arquitectura completa" CTAs, Continuity situation/evidence/next-step (control is not named there), sensors' `declarative` bucket, all catalog/gap logic.

## Tests added/updated

- `test_engineering_readiness_cli.py`: `test_cli_control_pass_gets_declaration_asterisk_and_footnote` (asterisk + footnote present, Propulsion/Energy unmarked), `test_cli_control_not_pass_has_no_asterisk_or_footnote`.
- `test_project_closure_v1.py`: `test_bom_flight_controller_defined_gets_identity_suffix` (flight_controller suffix present, motors line unaffected and still ends in plain `(high)`), `test_bom_sensors_declarative_unaffected_by_control_suffix`.

## Tests executed

- Targeted: `pytest tests/test_engineering_readiness_cli.py tests/test_project_closure_v1.py tests/test_impl_d_sku_bom.py tests/test_project_coherence.py -q` → 62 passed.
- Full suite: `pytest -q` → **2164 passed** (2160 baseline + 4 new tests), zero failures, zero skipped, zero weakened.

## Residual risks / documented debt

- **B2 future ★ (per investigation report §E):** `_control_evidence`'s `validated` flag still borrows the unrelated thrust simulation's pass/fail — control can never be "genuinely" physics-validated under today's architecture. This IC does not touch that; it remains an explicit future Engineer ★ decision (does Jarvis want declaration-only subsystems to ever gate `ASSEMBLY_READY`?), not something this claim-copy slice resolves.
- **Architecture `n/4` still declaration-complete for the control quarter:** the counter and "Arquitectura completa" CTA are unchanged per IC §2.3 — a project can still show `4/4` with `"pixhawk"` + `"gps"` alone. Named as residual, not fixed here.
- Continuity does not name "control" anywhere — unaffected by this IC, and not identified as a distinct over-claim in the investigation (Continuity's plain-PASS situation sentence was already the claim-hygiene thread's target, not control-specific).
