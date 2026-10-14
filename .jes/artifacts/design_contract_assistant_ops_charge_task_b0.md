# Design Contract — Assistant ops CHARGE Task (`DC-assistant-ops-charge-task`)

**Date:** 2026-10-01  
**Status:** **★ CLOSED** (Engineer: next cola after T14/T17 ★)  
**Author:** JES / Cursor  
**Type:** First **ops** Assistant Task — CHARGE is **not** an `AutonomyVerb`  
**Parents:** T14 allow-list ★ · T11 arm UX ★ · **no new INV** (seam already mapped)

## Intent

CHARGE appears today only as a `verb_not_allowed` probe string. Product needs an honest chat path for battery/charge ops intent that does **not** pretend to be a flight AutonomyVerb and does **not** steal mission “carga útil” lines.

## Locks

1. New Task kind `request_charge` → capability `ops.charge` (`not_implemented`, provider kind **`device`** — battery/charge ops; do **not** use `vehicle`/`AutonomyVerb`; do **not** invent a new `ProviderKind`).
2. Finite phrase table `OPS_CHARGE_PHRASES` — exact match only. Seed minimum: `charge`, `cargar`, `cargar bateria`, `cargar batería` (normalize accents). **Refuse** payload/mission lines (`carga util`, `aumentar la carga`, etc.).
3. Membership check only; **no** `ArmedAllowlistSafetyGate` (not a flight verb); **no** `SoftwareCapabilitySafetyGate` (capability is `not_implemented`+device, not `available`+software). Fulfill must still be honest UX — never claim charging happened.
4. Fulfill in orchestrator: **never** `propose_command` / `AutonomyVerb` / sim executor. Message: charge ops not implemented — never claim battery charging.
5. Precedence: after PATROL, before `return None`.
6. Out: copper · AutonomyVerb.CHARGE · allow-list change · Skills runtime · payload mass “carga”.

## Opens

IC **`B1-assistant-ops-charge-task`** → package **`0.6.28`**.
