# Work Plan — CLI Polish Bundle (post Continuity + G10)

**Date:** 2026-08-17 (closed **2026-08-18**)  
**Base commit:** `1b4769f` (Continuity Hardening + G10 materials/frame + findings G16–G19)  
**Delivered:** `15aa503` · tag **`checkpoint-continuity-polish`**  
**Prior checkpoint:** `checkpoint-g3` (`a3b72b8`)  
**Tests baseline:** 1753 → **1768** after polish  
**CLI evidence project:** `prueba-9f1031895508` (re-walk) · prior `continuity-bom` (`fa9f25c1d2a2`)

---

## 1. Executive summary

Continuity Hardening and G10 materials landed in `1b4769f`. CLI BOM walk exposed residual polish gaps (routing, Continuity CTA, catalog UX). **Audit → IC → impl S1–S7 → review → CLI re-walk → checkpoint are complete.** Verdict: **PASS WITH NOTES**. Post-checkpoint micro-fix `d224dc1` closed G20/G20-B. Open follow-ups: G17 residual, G14, G13 iterate path.

---

## 2. What is closed (do not re-open without regression evidence)

| ID | Area | Evidence |
|---|---|---|
| F-1 | Payload direction | checkpoint-f1 |
| G5 | DSE→component sync | checkpoint-g5 |
| G3 | Active-goal continuity | checkpoint-g3 + CLI |
| G14 | No motors→hélices false write | Continuity impl + CLI |
| G15 | list-motors mid-wizard + filtered max | Continuity impl + CLI (sin `?`) |
| G10 | Frame acquisition materials | `plastico` + `PVC 400g` + `plástico 550g` acquisition CLI |
| Continuity ★1–★7 | Acquisition Target Authority | impl review PASS WITH NOTES |

---

## 3. Gap register — polish bundle scope (2026-08-18 status)

### Tier 1 — closed or partial in S1–S7

| ID | Status | Notes |
|---|---|---|
| **G9-B** | ✅ Fixed S1 | Demote catalog-gap CTA when PASS + declared ≥ floor |
| **G18** | ✅ Fixed S3 | Aerial `definir motores` gate |
| **G17** | ⚠️ Partial S4 | Wizard force-motors; IDLE bare phrase residual |
| **G19** | ✅ Fixed S7 | CTA bridge list-motors + DSE |
| **G16-A** | ✅ Fixed S2 | Global `list_motors` + soft-interrupt |

### Tier 2 — partial / follow-up

| ID | Status | Notes |
|---|---|---|
| **G12 / FN-013** | ⚠️ Partial S5 | `definir bateria` fixed; other retarget paths → R3 |
| **G16-B** | ✅ Fixed S2 | CTA dedupe |
| **G13** | 🟡 Open | Unit T14 closed; CLI iterate path differs |
| **G20 / G20-B** | ✅ Closed post-checkpoint | Fixed in `d224dc1` (dynamic composite in-progress labels) |
| **G9-A** | 🟡 Deferred | catalog_ref blind spot |
| **G11 / G8 / G7** | 🟡 R3 | Iterate/DEFINE_MISSING preempt |

### Tier 3 — deferred (unchanged)

| ID | Summary |
|---|---|
| G6 | Mass breakdown deterministic |
| F-2 | Diámetro hélices → iterate |
| F-5 | catalog_ref divergence post-DSE |
| F-3 | Expected: configurar hélices → RPM only |

---

## 4. Two-layer problem (G9-B + G19) — must be understood by audit

```text
CAPA FÍSICA                         CAPA CATÁLOGO / CONTINUITY
────────────────                    ──────────────────────────
per_motor_max_thrust_n = 30 N       find_motors(≥3.3N, 2400KV, 10")
motor_count = 6                     → 0 SKU (KV+prop filter)
empuje_disponible = 180 N
empuje_requerido = 19.777 N         CTA: "Declara empuje ≥ 3.3 N"
margen = 9.1 PASS                   (misleading — physics already OK)
```

Audit must propose a **single coherent policy** for when catalog_gap is shown vs suppressed, and how Continuity CTA connects to existing DSE (`declarar empuje` → `explora opciones`).

---

## 5. Phase plan

```text
Phase 0  ✅ CLI walk + findings register + commit 1b4769f
Phase 1  ✅ Claude audit → investigation_cli_polish_audit.md
Phase 2  ✅ Engineer locks closed in IC (no separate design doc)
Phase 3  ✅ Implementation Contract → implementation_contract_cli_polish.md
Phase 4  ✅ Implementation S1–S7 (Claude + Cursor)
Phase 5  ✅ Cursor review + CLI re-walk PASS WITH NOTES
Phase 6  ✅ Checkpoint `checkpoint-continuity-polish` (`15aa503`)
Phase 7  🟡 R3 remainder · G13/G17/G14 · Impl C
```

---

## 6. Audit deliverables (Phase 1)

Claude produces **`investigation_cli_polish_audit.md`** covering:

1. **Per-finding deep dive** (G9-B, G16, G17, G18, G19, G12-FN013, G13) with code paths, root cause, blast radius.
2. **Cross-cutting themes:** Continuity authority vs catalog authority vs physics authority.
3. **Proposed slice ordering** with dependencies and risk.
4. **Test matrix** (unit + CLI probes) per slice.
5. **Explicit non-goals** (what not to patch; G10 materials regression guard).
6. **Acceptance criteria** for CLI re-walk (zero mandatory `cancelar`, no misleading PASS+gap CTA).

---

## 7. Suggested implementation slices (pre-audit hypothesis — audit may reorder)

| Slice | Findings | Hypothesis |
|---|---|---|
| S1 | G9-B | Suppress/rephrase catalog_gap when declared thrust covers requirement + sim PASS |
| S2 | G16-A + G19 | Global `list_motors` intent + orchestrator soft-interrupt (G10 ★8 parity) |
| S3 | G18 | `vehicle_type` guard on E1 terrestrial define_params |
| S4 | G17 | force-motors mirror FN-019 |
| S5 | G12-FN013 | Sync pending to named block before brief |
| S6 | G16-B | Dedupe catalog CTA (message vs question) |
| S7 | G19 | Wire Continuity CTA → DSE/list-motors; reasoning suggestion handlers |
| S8 | G13 | Iterate material compound parse (optional, may defer) |

**Audit validates or rejects this ordering.**

---

## 8. CLI re-walk acceptance (Phase 5) — **PASS WITH NOTES** (2026-08-18)

Project: `prueba-9f1031895508` (fresh dron walk, Engineer transcript).

| # | Probe | Expected | Result |
|---|---|---|---|
| 1 | `¿que motores tenemos en el catalogo?` at IDLE | Deterministic list (0 LLM) | ✅ PASS |
| 2 | Post-DSE apply with PASS + margin > 2 | No "declara empuje ≥ X" using physical floor | ✅ PASS (G9-B) |
| 3 | `definir motores` on dron | Aerial propulsion path, not robot | ✅ PASS (G18) |
| 4 | `4x 2306 2400KV 50W` in motors wizard | Registers without keyword | ⚠️ PARTIAL — needs `motores` prefix at some paths (G17) |
| 5 | `definir bateria` after propulsion | Battery wizard without stale motors body | ✅ PASS (S5/G12) |
| 6 | catalog_gap active | CTA mentions `explora opciones` or list-motors | ✅ PASS (G19) |
| 7 | `plastico 550g` / `PVC 400g` frame acquisition | Parses | ✅ PASS (G10) |

**Additional findings (post-walk, not blockers):** G20/G20-B (energy 3/4 label + `si`→motor_power_w wizard), G14 (`10x4.5` routing), G13 iterate `PVC 400g`.  
**Update:** G20/G20-B closed by post-checkpoint micro-fix `d224dc1`.

**Tag:** `checkpoint-continuity-polish`

---

## 9. References

- Findings: [cli_findings_post_catalog_bind_v1.md](cli_findings_post_catalog_bind_v1.md)
- Audit IC: [implementation_contract_cli_polish_audit.md](implementation_contract_cli_polish_audit.md)
- Continuity design: [design_continuity_hardening.md](design_continuity_hardening.md)
- G10 design: [design_g10_materials_frame.md](design_g10_materials_frame.md)
- Roadmap: [docs/IMPLEMENTATION_TASKS.md](../docs/IMPLEMENTATION_TASKS.md)

---

## 10. Engineer decision points (post-audit) — CLOSED in IC 2026-08-18

| # | Decision | Lock |
|---|---|---|
| 1 | G9-B threshold | per-motor `>=` + sim PASS |
| 2 | G18 location | orchestrator gate; IntentResolver stays stateless |
| 3 | G19 executability | relabel two suggestions only |
| 4 | G13 | S8 probe; no code unless reproduced |
| 5 | Checkpoint | `checkpoint-continuity-polish` ✅ |
| 6 | Packaging | one IC S1–S7 ✅ |

G9-A remains deferred (Impl C). Baseline chain: `1b4769f` → audit `39b85b2` → polish `15aa503` · **`checkpoint-continuity-polish`**.
