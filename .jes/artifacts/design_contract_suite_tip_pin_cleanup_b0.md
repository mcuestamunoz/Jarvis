# Design Contract — Suite tip-version pin cleanup (`DC-suite-tip-pin-cleanup`)

**Date:** 2026-10-01  
**Status:** **★ CLOSED** (Engineer ordered correction)  
**Author:** JES / Cursor  

## Intent

Historical Buys left `pyproject.toml` version asserts in their test files. Those pins were bumped until C43 (`0.5.44`) / early Assistant (`0.6.1`–`0.6.5`), then parked red against live tip — ~52 suite failures that were **not** product regressions.

Engineer: **retire them** and **do not pin tests to tip/package version going forward**.

## Locks

1. Remove all suite asserts that check exact `pyproject.toml` package version.
2. Policy: new Buys must not add tip-version pin tests. Guardrail test enforces this.
3. Capability / skill `version` fields in the registry remain valid product checks (not tip pins).
4. No product behavior change. No copper / CHARGE / Skills runtime / forge hygiene in this Buy.

## Opens

Package **`0.6.26`** / tag **`v0.6.26`** on ACCEPT.
