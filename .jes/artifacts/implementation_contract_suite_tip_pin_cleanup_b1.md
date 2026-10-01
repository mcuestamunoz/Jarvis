# Implementation Contract — Suite tip-version pin cleanup (`B1-suite-tip-pin-cleanup`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor  
**Implementer:** **Cursor** — Engineer ordered correction (“hay que corregir esto”)  
**Reviewer:** Cursor self-audit + Engineer ACCEPT → tag **`v0.6.26`**

**Status:** **Implemented** — await Engineer ★ ACCEPT → tag **`v0.6.26`**.  
**Parents:**
- [DC ★ CLOSED](design_contract_suite_tip_pin_cleanup_b0.md)
- Tip parent: T14 allow-list package `0.6.25` (Cursor PASS WITH NOTES; ACCEPT may land same tip chain)

**Type:** Suite honesty — retire tip/package version pins; policy guard going forward.  
**Opens:** **`0.6.26` / `v0.6.26`** on ACCEPT.  
**Cola:** suite debt → **T17**

**Not:** CHARGE · copper · Skills runtime · N1 fulfill docstring polish · forge PR hygiene · product behavior · registry capability `version` field checks (those stay).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-suite-tip-pin-cleanup`** |
| 2 | Delete every test whose sole job is asserting exact `pyproject.toml` package version (historical `0.5.x`, early `0.6.1`–`0.6.5`, and live tip bumps that only re-assert current package) |
| 3 | Mixed tests (e.g. geometry library + version): keep behavioral asserts; drop version pin only |
| 4 | Add guardrail `tests/test_suite_no_tip_version_pins_b1.py` forbidding tip-pin patterns |
| 5 | Policy from now: **do not** add tip/package version pin tests in new Buys |
| 6 | Version **`0.6.26`**; docs PRIORIDAD · short PLATFORM/CONNECTIONS note |
| 7 | Out: copper · CHARGE · Skills dispatcher · orchestrator fulfill docstring polish · closing old PRs |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `tests/test_*.py` (~70 files) | remove tip-pin tests / version asserts |
| `tests/test_suite_no_tip_version_pins_b1.py` | **new** policy guard |
| `tests/test_geometry_prop_adapter_visor_x_b1.py` | keep library check; drop version |
| `pyproject.toml` | `0.6.26` |
| Docs / PRIORIDAD / state | short note |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | Guardrail green — no tip-pin patterns remain |
| T2 | Full suite: previously parked ~52 tip-pin fails gone |
| T3 | No product behavior change (vehicle/allowlist/FN-016/ESC still green) |

---

## 3. Acceptance

- [x] Historical tip pins removed  
- [x] Live tip pin tests removed (policy)  
- [x] Guardrail landed  
- [ ] Engineer ACCEPT · tag **`v0.6.26`**
