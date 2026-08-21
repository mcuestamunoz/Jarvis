# G24 — DSE apply only #1; catalog SKU visible but not selectable (clears identity)

**Date:** 2026-08-21  
**Severity:** 🔴 product / UX  
**Status:** OPEN — registered during Impl C Engineer CLI walk  
**Category:** Bug (apply UX) + known ranking residual (scoring policy)  
**Project evidence:** `5540bda0ac16` (`autonomia`) — post Impl C generation + thrust bridge (working tree, pre-commit)  
**Does not reopen:** Impl C generation ★1–★7, thrust bridge ★1–★8, G5 invalidate semantics (correct when params diverge)

---

## One-line

After `optimiza para aumentar payload`, a real catalog motor appears in the top-5 (`#5 motors [sku]:…`), but the only apply verb (`aplica la mejor`) always applies `#1`. When `#1` is a params-only abstract candidate, apply clears `catalog_ref` (G5) — the user cannot apply the catalog option they just saw.

---

## Observed (Engineer CLI 2026-08-21)

```text
# Prior: architecture A → catalog pick → sunnysky_r2305_2500 bound (7.5 N)
# estado → Catalog PASS (G9-A Scenario B) ✓

User > optimiza para aumentar payload

Jarvis > … 5 configuración(es) viable(s):
  1. motores=6, empuje/motor (N)=11.2 → score=3.349
  2. empuje/motor (N)=15 → score=2.977
  3. motores=8 → score=2.977
  4. carga útil (kg)=1.2, motores=6 → score=2.257
  5. motors [hobbywing_xrotor_2207_2450]: … thrust_n=11.5 … → score=2.251

  Di «aplica la mejor» para aplicar la configuración #1 al proyecto.
```

**Facts:**

1. Impl C **generation works** — `#5` is a real SKU with `[sku]` label (product win).
2. CLI apply path is **only** `viable[0]` (`orchestrator._handle_apply_exploration` + intent `aplica la mejor` / equivalente). There is **no** `aplica la 5` / apply-by-index.
3. With thrust already declared, abstract `EXPLORATION_GRIDS` entries (unbounded cost-free thrust / motor_count) outrank real SKUs under locked `_score_candidate` (Impl C ★6 / thrust-bridge ★3★8 — scoring not changed on purpose).
4. Therefore the natural user path after seeing a catalog option is: `aplica la mejor` → `#1` params-only → G5 `invalidate_diverged_catalog_refs` **clears** the bound `catalog_ref` — identity loss that feels like a regression even though G5 is doing its job.

### Confirmed after `aplica la mejor` (same session)

CLI apply output:

```text
per_motor_max_thrust_n: 7.5 → 11.25
motor_count: 4 → 6
```

`estado` still showed `Catalog PASS` (misleading — unbound + library matches can still PASS Catalog without a bound SKU).

Disk check `workspace/autonomia-5540bda0ac16/state.json` after apply:

```text
catalog_ref: None                          ← identity cleared (G5)
name: sunnysky_r2305_2500                  ← stale label (name not cleared)
thrust_n: 11.25 source=calculated          ← sync from abstract params
motor_count: 6 source=calculated
power_w: 220 / kv_rating: 2500             ← leftover from old SKU (frankenstein)
```

**G24 evidence closed:** apply `#1` destroys `catalog_ref` while leaving a lying motor `name` and mixed SKU numbers.

### Related — `sistema` → LLM leak (same turn)

Engineer typed `sistema` to inspect components; turn fell through to **LLM** (undesired). Not the same root as G24 apply UX — dedicated finding: [cli_finding_g25_sistema_llm_leak.md](cli_finding_g25_sistema_llm_leak.md). Prefer `estado` / `qué motores tenemos` until fixed. Do not use bare `sistema` as Continuity verb today.

---

## Expected (product)

At minimum one of:

| Option | Behavior |
|---|---|
| **A** | User can apply a listed candidate by number (`aplica 5` / `aplica la 5`) or by selecting the catalog row |
| **B** | When catalog candidates exist, `aplica la mejor` prefers a catalog-sourced viable over abstract params-only (ranking/tiebreak policy) |
| **C** | Explore message warns explicitly that `#1` is abstract and will drop SKU identity if applied, and points to how to apply a catalog row |

Preferred long-term: **A + honest copy**; **B** only after Engineer ratifies scoring/ranking (explicitly deferred from Impl C).

---

## Root cause (two layers — do not collapse)

| Layer | Cause | Authority |
|---|---|---|
| **Apply UX** | `_handle_apply_exploration` hardcodes `best = exploration.viable[0]`; intent resolver has no apply-by-index | Bug / missing product verb |
| **Ranking** | Abstract thrust factors score higher than bounded real SKUs when `per_motor_max_thrust_n` already set | Known residual (Impl C thrust-bridge report §7) — **not** a bridge bug |

Fixing only ranking without apply-by-index still leaves users unable to choose `#2–#5`. Fixing only apply-by-index makes catalog usable even when abstract wins `#1`.

---

## Severity rationale

- User is shown a **buildable** SKU (`#5`) then guided to a verb that applies a **non-SKU** config and **destroys** the bound identity.
- Undermines Impl C’s product story on the most common path (already bound motor → explore → apply).
- Automated probes that only exercise no-prior-thrust fixtures (catalog fills top-5) **miss** this path — CLI walk required to surface it.

---

## Out of scope / not this bug

- Thrust bridge itself (SKU-switch apply when a catalog candidate **is** applied) — **PASS**, separately proven.
- G5 clearing `catalog_ref` on true params divergence — correct; the bug is **steering the user into that path** without a way to apply the catalog row.
- Impl D / BOM.

---

## Suggested follow-up (not an IC yet)

```text
G24-A  Apply-by-index (or apply catalog candidate) — product verb
G24-B  Ranking/tiebreak when catalog viable present — Engineer policy
G24-C  Honest explore CTA when #1 is params-only and catalog rows exist
```

Recommend **G24-A** first (smallest product unlock). Do **not** fold into Impl C commit; register as post–`checkpoint-impl-c` residual.

**Engineer note (2026-08-21):** Full-project CLI walk continues after G24 (acquisition → readiness) — Impl C validated in-system, not in isolation.

---

## Related artifacts

- [`.jes/artifacts/implementation_review_impl_c_catalog_dse_thrust_bridge.md`](implementation_review_impl_c_catalog_dse_thrust_bridge.md) — Note: already-declared-thrust top-5 residual  
- [`.jes/artifacts/implementation_report_impl_c_catalog_dse_thrust_bridge.md`](implementation_report_impl_c_catalog_dse_thrust_bridge.md) §7  
- Code: `orchestrator._handle_apply_exploration` (`viable[0]`); `intent_resolver` apply patterns; `design_explorer._score_candidate` / `EXPLORATION_GRIDS`

---

**End of finding.**
