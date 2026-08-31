# Validation Case — ★6 Operating Point Dataset Comparison

**Status:** Companion narration to `scripts/cli_probe_validation_case_op_dataset.py` (Validation Case ★6 Regression Gate IC).
**Purpose:** State explicitly, in one place, what the ★6 dataset already proves — no new sourcing, no new numbers. Every figure below is cited from [`phase2_star6_operating_point_validation_case.md`](phase2_star6_operating_point_validation_case.md) and reproduced verbatim by Jarvis's resolver.

---

## Why this is a comparison of a lookup, not a derivation

For every `exact_operating_point`/`fallback_operating_point` row, `resolve_operating_point` (`src/jarvis/knowledge/library.py`) returns the curated row's own fields directly — it does not compute thrust, power, current, or RPM from first principles. "Jarvis's result" and "the real source" are therefore the same object by construction for these three rows; there is no numeric divergence to report for them. The one place a genuine number *is* computed and can diverge from a real-world figure is the catalog **rating** (`motor_power_w`, the SKU's flat `max_watts`) versus the resolved **operating point** (`motor_op_power_w`) — see §4.

---

## OP-2 — EMAX RS2205S 2300KV / 16.0 V / HQ5045BN

| Field | ★6 source (GetFPV test table) | Jarvis result |
|---|---|---|
| Thrust | 9.7086 N | 9.7086 N ✓ |
| Power | 432.0 W | 432.0 W ✓ |
| Current | 27.0 A | 27.0 A ✓ |
| RPM | 23560 | 23560.0 ✓ |
| Source | `https://www.getfpv.com/emax-rs2205s-2300kv-racespec-motor-cw.html` | `source_type=manufacturer_test`, `confidence=0.98` |

## OP-3 — SunnySky R2205 2500KV / 14.8 V / GF5045×3

| Field | ★6 source (Banggood-hosted manufacturer PDF) | Jarvis result |
|---|---|---|
| Thrust | 12.5525 N | 12.5525 N ✓ |
| Power | 592.0 W | 592.0 W ✓ |
| Current | 40.0 A | 40.0 A ✓ |
| RPM | 27082 | 27082.0 ✓ |
| Source | `https://img.banggood.com/file/products/20181018062904ER22052500KV.pdf` | `source_type=manufacturer_test`, `confidence=0.97` |

## OP-0 — EMAX RS2205S / 4S headline fallback (honest, not a full OP)

| Field | ★6 source (EMAX product page, fallback-only) | Jarvis result |
|---|---|---|
| Thrust | 10.0420 N | 10.0420 N ✓ |
| Power / current / RPM | not published for this headline figure | absent (`motor_op_power_w`/`motor_op_current_a`/`motor_op_rpm` not set) |
| Resolution | — | `resolution_type=fallback_operating_point`, never presented as exact |

No propeller was specified for this figure in the source; Jarvis correctly classifies it as `fallback_operating_point`, not `exact_operating_point`, when no propeller is bound (`hq_5045_bn`'s exact rows require a matched propeller).

---

## §4 — The one real divergence: catalog rating vs. resolved operating point

Unlike the lookups above, `motor_power_w` (the SKU's flat catalog `max_watts` — a manufacturer's headline rating, not tied to a specific combo) and `motor_op_power_w` (the real draw at the specific bound motor+propeller+voltage combo) are genuinely different numbers, already computed and already shown:

```text
emax_rs2205s_2300 @ OP-2 combo:
  motor_power_w    = 400.0 W   (catalog rating — P2-2 Option A, never overwritten)
  motor_op_power_w = 432.0 W   (resolved operating point — the real draw at this load)
  delta            ≈ 8%
```

Both numbers are visible in `estado` as two distinct lines — `"Propulsión (evidencia): ..."` and `"Propulsión (OP eléctrico): ..."` — and neither is presented as the other. This is the honest "model vs. reality" gap this dataset surfaces today; it does not require, and this document does not add, any new sourced data.

---

## What this document is not

- Not new sourced data — every number above is already in the ★6 doc and already in `library/motores/_datos.json`/`library/helices/_datos.json`.
- Not a new `estado` surface — the two lines cited above already exist; this document only narrates them together.
- Not a battery/ESC validation — no curated real-test data exists for those domains yet (a separate, future Engineer sourcing decision).

**Regression gate:** `scripts/cli_probe_validation_case_op_dataset.py` asserts every figure in this document against the live resolver/bridge/render chain, permanently.
