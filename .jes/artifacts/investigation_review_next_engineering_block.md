# Investigation Review — Next Engineering Block (P2-2 vs G24 vs H5)

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_next_engineering_block.md`](investigation_contract_next_engineering_block.md)  
**Report:** [`.jes/artifacts/investigation_report_next_engineering_block.md`](investigation_report_next_engineering_block.md)  
**Base:** `73bd9fa` (doc hygiene) · contract `e529270` · tag `checkpoint-closure-policy`

## Verdict

**PASS WITH NOTES**

Report satisfies contract §1.1–1.7 and §2 structure. All three candidates traced with file:line evidence; comparison matrix precedes recommendation; one primary block (G24-A) with explicit deferrals. **No `src/` changes, no version bump** — investigation discipline respected.

**Defect-first review:** No FAIL findings. Three notes for Engineer before IC drafting.

---

## Contract checklist

| Gate | Result |
|---|---|
| §1.1 Baseline verification | **Pass** — 1976 suite, 5/5 + 6/6 + 4/4 probes, P2-1 16 passed (Cursor re-ran suite + all three probes) |
| §1.2 P2-2 (A1–A8) | **Pass** — scope box, prerequisite table, bridging gap quantified with live OP numbers |
| §1.3 G24 (B1–B9) | **Pass** — two-layer root cause (apply vs ranking), fix-option table, test workaround documented |
| §1.4 H5 (C1–C9) | **Pass** — schema lock 1A cited, no live blocker, ERF-2 deferral still valid |
| §1.5 Comparison matrix | **Pass** — filled before §7 recommendation |
| §1.6 Recommendation | **Pass** — G24-A primary; P2-2 secondary; H5 deferred |
| §1.7 ★ decisions (5) | **Pass** |
| §2 Report structure (11 sections) | **Pass** |
| §3 Hard constraints acknowledged | **Pass** |
| No implement / no version bump | **Pass** |
| ★1 code-first / no invented SKUs | **Pass** |
| ★3 three scope boxes kept distinct | **Pass** |
| ★4 Project Closure not reopened | **Pass** |

---

## Independent verification (Cursor)

### Baseline

| Check | Cursor result |
|---|---|
| `pytest tests/` | **1976 passed** |
| `cli_probe_requirements_closure.py` | **5/5 PASS** |
| `cli_probe_battery_catalog_bind_ux.py` | **6/6 PASS** |
| `cli_probe_closure_policy_propeller_sku.py` | **4/4 PASS (+ optional)** |
| `tests/test_phase2_lookup_operating_point.py` | **16 passed** (prior run) |

### P2-2 — operating-point bridge gap

Confirmed in code: `set_motor_component` bridges `thrust_n` and `propulsion_resolution` JSON only — no `power_w` / `current_a` / `rpm` in `current_parameters`.

Live OP resolution (Cursor, `resolve_operating_point` only):

```text
emax_rs2205s_2300 + hq_5045_bn @ 16 V:
  max_watts (catalog flat) = 400.0 W
  OP power_w = 432.0 W, current_a = 27.0 A, thrust = 9.7086 N
  resolution_type = exact_operating_point
```

`_per_motor_current_a` (`electrical_compatibility.py:129+`) has no OP-resolved path — falls through to `motor_power_w / voltage` when `max_current_a` is absent on the SKU. **Report's ~7–8% gap claim accepted.**

### G24 — apply path

Confirmed:

```3576:3576:src/jarvis/core/orchestrator.py
        best = exploration.viable[0]
```

`grep` across `src/`: **zero** apply-by-index patterns (`aplica la N`, `aplica #N`, etc.). `intent_resolver.py` `APPLY_PATTERNS` match generic `"aplica la mejor"` only — no index capture.

Test workaround confirmed:

```446:452:tests/test_impl_c_catalog_aware_dse.py
    # Force the picked catalog candidate to the front so "aplica la mejor"
    # applies it deterministically, without depending on how it ranked.
    exploration2 = exploration.model_copy(update={"viable": [catalog_candidates[0]]})
```

**No test today covers the bug shape** (real ranking, catalog candidate not at `#1`, unqualified apply). Report §4.10 accepted.

### H5 — ESC catalog

Confirmed `CatalogRef.family: Literal["motor", "battery", "propeller"]` at `action_schema.py:139`. Freeform ESC path sufficient for readiness — no regression on Closure arc.

---

## Assessment of recommendation

| Candidate | Report | Cursor view |
|---|---|---|
| **G24-A (primary)** | Apply-by-index; only candidate with active state destruction on a supported command | **Ratify ★1/★2** — urgency argument sound; does not touch locked ★6 scoring |
| **P2-2 bridging (secondary)** | Independent low-risk cut; Real World Validation Case deferred | **Ratify ★3** — ship as IC 2 after or parallel to G24; no ordering dependency |
| **H5 (deferred)** | Schema lock 1A reopening; no live blocker | **Ratify ★4** — defer until explicit Engineer ratification of 1A change |

**G24 vs P2-2 urgency framing accepted:** G24 is trust-breaking user action (silent identity loss); P2-2 is quiet accuracy debt. Both are small, additive cuts — consistent with a single `0.3.x` checkpoint after both PASS (★5 Engineer's call).

**Closure non-blocker re-verified:** G24 does not block `ASSEMBLY_READY`; frankenstein post-apply state correctly yields `sku_resolved=False`.

---

## Notes (non-blocking)

### Note 1 — IC sequence: two ICs, one optional checkpoint

Report §7 sequences G24-A then P2-2 bridging. **Recommend Engineer ratify 2 ICs** (not one mega-IC):

1. **IC "G24-A — DSE Apply By Index"** — gate: test without `viable` reorder + CLI probe  
2. **IC "P2-2 — Operating Point Bridge"** — gate: extend `test_phase2_lookup_operating_point.py` + autonomy/discharge probe  

Version/tag may cover both after both PASS (★5) — Engineer's call whether one or two checkpoints.

### Note 2 — G24-A intent design is an IC detail, not investigation gap

Report correctly identifies missing apply-by-index. IC must specify: index parsing (`"aplica la 5"` / `"aplica #5"`), bounds check on `viable[]`, and regression that `"aplica la mejor"` remains `viable[0]`. No investigation FAIL — these are implementation-contract decisions.

### Note 3 — P2-2 bridge: overwrite vs new keys

Report §3.7 notes two valid shapes (overwrite `motor_power_w` when OP exists vs new resolved keys). **Engineer/IC should pick one** before implementation — affects `calculation_engine` consumers and regression contract. Recommend mirroring existing `per_motor_max_thrust_n` precedent (overwrite when exact/fallback OP) unless Engineer prefers additive keys for audit trail.

---

## ★ ratification guidance for Engineer

| ★ | Cursor recommendation |
|---|---|
| ★1 Primary next block: G24-A | **Ratify** |
| ★2 G24 scope: apply-by-index only (Option A) | **Ratify** — defer G24-B/C |
| ★3 P2-2 first cut: bridging only, not Validation Case | **Ratify** — secondary IC |
| ★4 H5: defer entirely | **Ratify** |
| ★5 Version bump timing: after IC PASS(es) | **Engineer's call** — single `0.3.x` tag covering G24 + P2-2 bridge is reasonable |

---

## Next step

```text
Engineer ★ (★1–★5, especially P2-2 key-overwrite choice in Note 3)
  ↓
Version decision (optional, post-ratification)
  ↓
Cursor: implementation_contract_g24_apply_by_index.md  (IC 1)
  ↓
Claude implements → review → probe → checkpoint
  ↓
Cursor: implementation_contract_p2_2_operating_point_bridge.md  (IC 2)
  ↓
Claude implements → review → probe → checkpoint (or merge tag with IC 1)
```

Do **not** draft ICs or bump version until Engineer ★ ratifies primary block.

---

**End of review.**
