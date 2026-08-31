# Investigation Review — Deferred Queue Post-v0.3.1

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_deferred_queue_post_v031.md`](investigation_contract_deferred_queue_post_v031.md)  
**Report:** [`.jes/artifacts/investigation_report_deferred_queue_post_v031.md`](investigation_report_deferred_queue_post_v031.md)  
**Base:** tag `v0.3.1` / `checkpoint-next-engineering-block` · commit `30c9aec`

## Verdict

**PASS WITH NOTES**

Report satisfies contract §1.1–1.8 and §2 structure. Headline finding **reproduced independently** on `v0.3.1`: catalog-native candidates generated but **truncated out of `.viable`** before the user can apply-by-index — a materially new post-G24-A gap. Recommendation (C primary + D micro-IC; A/B deferred) is well-grounded.

**Defect-first review:** No FAIL findings. Two notes for Engineer before IC drafting — especially **★3(a) vs ★3(b)**.

---

## Contract checklist

| Gate | Result |
|---|---|
| §1.1 Baseline on v0.3.1 | **Pass** — 2013 suite, 5 probes (Cursor re-ran suite + 4 probes) |
| §1.2 Validation Case (A1–A8) | **Pass** — post-P2-1/P2-2 delta honest |
| §1.3 H5 (B1–B7) | **Pass** — re-verified, no new urgency |
| §1.4 G24-B/C (C1–C6) | **Pass** — key finding live-traced |
| §1.5 Frankenstein `.name` (D1–D7) | **Pass** — G5 omission documented, not oversold |
| §1.6 Comparison matrix | **Pass** — before §8 recommendation |
| §1.7 Recommendation | **Pass** — one primary + parallel micro-IC |
| §1.8 ★ decisions (6) | **Pass** — ★3 correctly split (a)/(b) for Engineer |
| §2 Report structure (12 sections) | **Pass** |
| No implement / no version bump | **Pass** |
| ★7 post-v0.3.1 delta | **Pass** |
| Do not reopen G24-A / P2-2 without proof | **Pass** |

---

## Independent verification (Cursor)

### Baseline

```text
pytest tests/                              → 2013 passed
cli_probe_g24_apply_by_index.py            → 6/6 PASS
cli_probe_p2_2_operating_point_bridge.py   → 6/6 PASS
cli_probe_requirements_closure.py          → 5/5 PASS
git diff HEAD -- src/ tests/ pyproject.toml → (empty)
```

### Headline — G24 residual (§5.1)

Bound `sunnysky_r2305_2500` + declared thrust, three goals:

```text
aumentar_payload:     catalog_gen=4  catalog_in_viable=0
mejorar_estabilidad:  catalog_gen=4  catalog_in_viable=0
reducir_masa:         catalog_gen=0  catalog_in_viable=0
```

Matches report exactly. Mechanism confirmed at `design_explorer.py:638-647` — global sort + `viable[:MAX_VIABLE]` with `MAX_VIABLE=5`. **G24-A cannot help when rows never reach the list** — accepted.

### Validation Case (A)

Exact OP path is curated lookup (`library.py:623-626` returns row verbatim) — no model-vs-source numeric delta for exact matches. Rating vs OP divergence **already shipped** via P2-2 (`motor_power_w` vs `motor_op_*`). Deferral rationale **accepted**.

### H5 (B)

`CatalogRef.family` still three families only; no live blocker re-found. Defer **accepted**.

### Frankenstein `.name` (D)

`invalidate_diverged_catalog_refs` clears `catalog_ref` only; `sync_motors_component_from_params` explicitly does not touch `.name`. Micro-IC scope **accepted** as independent of C.

---

## Assessment of recommendation

| Candidate | Report | Cursor view |
|---|---|---|
| **C primary** | Viable selection + G24-C CTA | **Ratify ★1** — strongest post-v0.3.1 gap |
| **D parallel micro-IC** | Clear `.name` on divergence | **Ratify ★5** — bundle same checkpoint window OK |
| **A defer** | Research/doc, not engineering IC | **Ratify ★2** |
| **B defer** | No blocker, 1A lock | **Ratify ★4** |

**★3 (a) vs (b)** — report correctly refuses to pick. Cursor guidance:

| Option | Cursor view |
|---|---|
| **(a) Viable-slot reservation** | **Preferred for first IC** — fixes demonstrated truncation without reopening Impl C ★6 scoring formula; auditable ~10-line selection block |
| **(b) `_score_candidate` rewrite** | Valid but heavier — requires explicit ★6 unlock; save unless Engineer wants ranking philosophy change |

Pair **either** with G24-C honest messaging (including “no catalog row in top 5” case per §5.4).

---

## Notes (non-blocking)

### Note 1 — IC count: two ICs, one checkpoint window

Recommend Engineer ratify **2 ICs** (not one mega-IC):

1. **G24 Viable Selection + Honest CTA** (C)  
2. **Frankenstein Name Clear** (D, micro)

Single `0.3.x` tag after both PASS is reasonable (★6).

### Note 2 — G24-A regression must stay green

Any C fix must preserve apply-by-index and `"aplica la mejor"` = index 1 when row exists. Report §10 gate is correct — add permanent test from §5.1 repro (no G24-TF session patch).

### Note 3 — Artifacts uncommitted

Contract + report + queue updates are local-only until Engineer commits (same as prior cycles).

---

## ★ ratification guidance for Engineer

| ★ | Cursor recommendation |
|---|---|
| ★1 Primary C + parallel D | **Ratify** |
| ★2 Validation Case defer | **Ratify** |
| ★3 G24 fix shape | **Ratify (a) viable-slot reservation** unless product wants scoring rewrite (b) |
| ★4 H5 defer | **Ratify** |
| ★5 `.name` micro-IC with C window | **Ratify** |
| ★6 Version after C+D PASS | **Ratify** — single `0.3.x` patch reasonable |

---

## Next step

```text
Investigation PASS WITH NOTES
  ↓
Engineer ★ (especially ★3 a vs b)
  ↓
Cursor: implementation_contract_g24_viable_selection.md (+ optional D micro contract)
  ↓
Claude implements → review → probes → checkpoint
```

Do **not** draft ICs until ★3 is ratified.

---

**End of review.**
