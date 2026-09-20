# Engineer note — Docs truth-sync Fase C (2026-09-20)

**Author:** Cursor (docs audit)  
**Trigger:** Engineer asked for detailed documentation review; subsequent work depends on accurate docs.  
**Update:** Engineer ★ ACCEPT **C4+C5 as one block** → tag **`v0.5.3`** (skip intermediate `v0.5.2`).

---

## Ground truth (after block ACCEPT)

| Fact | Value |
|---|---|
| Release | **C4 + C5** one ACCEPT commit + tag **`v0.5.3`** |
| Tags present | `v0.5.0`, `v0.5.1`, **`v0.5.3`** — **no** `v0.5.2` (never cut; planned mid-step abandoned) |
| `pyproject.toml` | **`0.5.3`** |
| Suite | **3236** passed, 1 skipped |
| C4 | ACCEPT CLOSED (review PASS) — autonomy surface |
| C5 | ACCEPT CLOSED (review PASS) — radio dual-role stub |
| Craft tip | Still `v0.4.3` SoT (unchanged) |

---

## Why no `v0.5.2` tag

ICs originally planned C4 → `0.5.2` then C5 → `0.5.3`. Engineer decided both Buys are one platform surface block. Package was already at `0.5.3` when C5 landed; cutting a fake `v0.5.2` after the fact would confuse tip history. **Canonical release for C4+C5 = `v0.5.3`.**

---

## Lies / drift found (before first sync)

1. PRIORIDAD / PLATFORM / README claimed **C4 ACCEPT CLOSED @ tag `v0.5.2`** — tag did not exist.  
2. C4 **report** said ACCEPT CLOSED while uncommitted.  
3. Package jumped to **`0.5.3`** while reviews/ACCEPT open.  
4. system_map canvas claimed C1–C4 @ `0.5.2` as shipped.

Corrected living narrative now matches the single-block ACCEPT above.

Scaffold honesty unchanged: Python ≠ production FC (C++); RejectAll; no craft coupling; dual-role stub ≠ live ELRS.
