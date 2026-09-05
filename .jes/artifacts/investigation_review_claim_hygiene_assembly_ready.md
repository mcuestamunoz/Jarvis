# Investigation Review — Claim hygiene under ASSEMBLY READY

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_claim_hygiene_assembly_ready.md](investigation_contract_claim_hygiene_assembly_ready.md)  
**Report:** [investigation_report_claim_hygiene_assembly_ready.md](investigation_report_claim_hygiene_assembly_ready.md)  
**★ thread:** [engineer_ratification_claim_hygiene_assembly_ready.md](engineer_ratification_claim_hygiene_assembly_ready.md)  
**Base:** tag `v0.3.6` / `checkpoint-experimental-prop-energy-closed` · commit `f70b278`

## Verdict

**PASS WITH NOTES**

Buy **B4** is accepted for the **margin/quality slice**. Weak-OP Continuity wiring stays a **named later IC**, not this one. `_derive_overall` / `ASSEMBLY_READY` eligibility stay **unchanged** (no B3 ★ stop).

**Ready for Implementation Contract**  
→ [implementation_contract_claim_hygiene_assembly_ready.md](implementation_contract_claim_hygiene_assembly_ready.md)

Engineer ★ / `procede` on that IC before Claude edits `src/`.

---

## Contract checklist

| Criterion | Result |
|---|---|
| §2 Know / Claim / Measure / Buy answered | **Pass** |
| §3 no physics / no catalogs / no `_derive_overall` default | **Pass** — B4 explicitly rejects B3 |
| §4 surfaces traced with `file:line` | **Pass** |
| §5 reconstruction fixture | **Pass** — appendix reproduces Diseño validado + Corrige warning + ASSEMBLY READY |
| §6 claim matrix + Buy | **Pass** — B4 |
| No `src/` from investigation | **Pass** (report disclosure) |

---

## Independent verification (spot-check)

| Claim | Cursor check |
|---|---|
| Plain PASS situation at `:293-294` ignores quality/warnings | **Confirmed** — `project_continuity.py:293-294` |
| Autonomy-undemonstrated / below branches precede plain PASS | **Confirmed** — `:284-292` |
| Warning next-step branch at `:359` → generic Corrige at `:434` | **Confirmed** — `elif status_type == "warning" or …` |
| H5 generic PASS next-step (`:522-524`) unreachable under `low_margin` | **Confirmed** — `status_type="warning"` wins earlier; H5 note is stale for that traffic |
| Evidence already prints quality + margin | **Confirmed** — `:301-308` |
| `LOW_MARGIN_THRESHOLD = 1.15`; quality `risky` if margin `< 1.1` | **Confirmed** — `simulator.py:13,136-143` |
| `_derive_overall` ignores quality/warnings | **Confirmed** — `engineering_readiness.py:1199-1211`; no `quality` hits in that module |
| Phase suppress when Continuity situation present | **Confirmed** — `main.py:226-228` |
| `WARNING_SHORT` / `WARNING_MESSAGES` in CLI only | **Confirmed** — `main.py:62-83`; Continuity does not import them |

---

## Notes (IC must absorb)

### N1 — Humanize `next_useful_why` in CLI, not Continuity

Report §G suggested Continuity import `WARNING_SHORT`. That would be **core → adapters**. IC: Continuity may keep the warning **code** in `next_useful_why`; `render_startup_context` maps known codes through `WARNING_SHORT` / `WARNING_MESSAGES` when printing `Por qué:`.

### N2 — PhaseLayer display stays suppressed

Do **not** reopen FN-002 phase printing in this IC. The fixed Continuity situation absorbs the honesty; PhaseLayer copy (“inviabilidad”) remains an internal authority mismatch noted for a later thread if needed.

### N3 — CLI caveat without inventing ERF fields

`_render_readiness_block` today receives only `readiness`. IC may (a) pass optional `simulation` from `ctx`, or (b) use `status_type` / `status_reason` already on `ctx` for margin warnings. Prefer (a) if adding a thin `simulation` snapshot to startup ctx is cleaner for unit tests; either way **do not** change `_derive_overall`.

### N4 — Weak OP = follow-up only

`prop_energy_block_closure` Continuity wiring is **out of this IC** (B4 second half). Remains agenda debt after control parity or as its own knowledge thread — not bundled here.

---

## Claim matrix lock (for IC)

| Sentence | PASS + good/acceptable, no margin/load warning | PASS + `quality=risky` **or** margin/load warning (`low_margin` / `high_actuator_load` / `low_force_to_weight_ratio`) |
|---|---|---|
| “Diseño validado en simulación (PASS)…” | Keep | **Forbidden** — replace with locked IC string |
| `PROJECT STATUS: ASSEMBLY READY` | Keep (no caveat) | Keep value; **append** one NOTE caveat line |
| Evidence quality/margin bullet | Keep | Keep |
| Next-step “Corrige la causa…” | N/A | Keep; humanize `Por qué` in CLI |
| Autonomy undemonstrated / below strings | Unchanged | Unchanged |
| `ASSEMBLY_READY` / `NOT_ASSEMBLY_READY` enum | Unchanged | Unchanged |

---

## Out of scope confirmed

Sensor/FC catalogs · control physics · C-A1 · fail-routing N1 · threshold unification · B3 `_derive_overall` · Conversation Engine · HD-*
