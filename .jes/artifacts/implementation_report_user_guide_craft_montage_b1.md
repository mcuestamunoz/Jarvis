# Implementation Report — User command guide to craft montage (`B1-user-guide-craft-montage`)

**IC:** [implementation_contract_user_guide_craft_montage_b1.md](implementation_contract_user_guide_craft_montage_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-14
**Type:** Documentation Buy — no `src/`/`ui/`/`tests/`/`library/` changes, no suite growth expected or observed.

---

## Method (Phase 0)

Per lock #5's own STOP gate, the inventory was written **before** any guide content, from code and tests only:

1. Enumerated all **14** `_try_handle_*` IDLE bridges in `orchestrator.py` in their literal dispatch order, citing each one's exact trigger regex/gate.
2. Listed all **19** `*_assist.py` modules under `src/jarvis/core/` (matches the IC's own estimate exactly) and extracted each locked regex/example phrase from its own docstring/`parse_*`/`is_*` functions.
3. Traced the catalog help-choose (`ayúdame a elegir`, shared `motor_catalog_assist.HELP_CHOOSE_PHRASES`, reused by import into every family) and rebind (`catalog_rebind_assist.resolve_idle_catalog_rebind`, 5 families: frame/motors/propellers/battery/esc) gates directly in code.
4. Read `component_writers.py`'s public `set_*` surface Continuity actually reaches.
5. Read `ui/spatial-board/src/Scene3D.tsx`'s own Situar UI copy (button labels, hint text) verbatim rather than paraphrasing.
6. Cross-checked against ~35 `.jes/artifacts/engineer_smoke_*.md` / `implementation_review_*.md` files for "phrases that actually worked" — none of the guide's cheatsheet phrases contradicted a closed smoke.
7. Listed the CLI's own top-level entrypoints (`jarvis --chat`, `jarvis board`) and the `estado`/`resumen`/`como va` orientation patterns from `intent_resolver.py`.
8. Documented every refusal path I could find evidence for (`estimated_dims`, `child_not_box`/`origin_unusable`, incomplete pose, disk `n_a_disk`).

**Spot-check validation (Phase 1.3):** 16 phrases (well over the ≥10 minimum) were run live through their real parser/trigger functions during drafting — not just quoted from memory. All 16 resolved exactly as documented, including the one deliberately-negative check (`cambiar controladora` → `None`, confirming the documented FC-rebind gap). See the inventory's own §10 for the gap list this produced.

**Output:** `.jes/artifacts/inventory_user_facing_commands_craft_montage_b0.md`.

## Guide TOC (Phase 1)

`docs/USER_GUIDE_CRAFT_MONTAGE.md`, **406 lines** (within the IC's own 400–800 target):

1. Qué es esta guía / qué NO promete
2. Cómo arrancar
3. Identidad + catálogo
4. Placa principal (citada o estimada) + disclosure
5. Sobres L×W×H del resto del stack
6. Montajes (`mounted_on`)
7. Poses: Path F, layout pack, Situar
8. Motores/hélices en el Visor X
9. Comprobar: `cabe`, `relaciones`, `declaro verificado`, `parece un dron`
10. Ejemplo completo, de principio a fin
11. Cheatsheet — una página de comandos
12. Apéndice — energía/simulación y límites conocidos

One deviation from the IC's suggested TOC: I added **§10 (worked example)** between the per-topic walkthrough and the cheatsheet, not in the original 11-item suggestion. Reason: the inventory's own spine (§9 there) mapped cleanly onto §§2–9 here, but a single, fully concrete, real-project walkthrough (tying every step together with actual numbers) gave the guide real depth on the montage spine — exactly what the IC's own style lock asks for ("Prefer depth on montage spine") — without growing the encyclopedic table (that stays in the inventory). Every number in §10 was **read directly from `10-min-autonomía`'s live `state.json`**, not computed by hand — see the finding below.

## A drafting error caught before publishing

While writing §10's worked example, I first computed the Path F pose z-values by hand (`plate.height/2 + child.height/2`) using the same formula the code uses, and got two values wrong (ESC 5.75mm instead of 5.0mm, FC 9.9mm instead of 4.9mm — an arithmetic slip, not a formula misunderstanding). Per lock #6 ("every example phrase must trace to a parser/bridge/smoke note"), I re-derived all four z-values by reading them directly out of `10-min-autonomía`'s real, already-posed `state.json` instead of computing them, then re-parsed all four corrected phrases through the real `declared_box_pose_declare_assist.parse_declared_box_pose_declare` to confirm they resolve to exactly those values before publishing. This is exactly the kind of error lock #6's "no inventing phrases the code does not accept" guard exists to catch — flagging it transparently rather than silently fixing it.

## Gaps found (Phase 0 §10, surfaced in the guide's own appendix, §12.2)

1. `cambiar controladora`/`cambiar gps` do not reopen the FC/sensor picker (Library FC/sensors P0's own review N1 — confirmed still open).
2. `actualiza el fc`/`actualiza el gps` do not exist (same minimal-surface reason, confirmed via `catalog_refresh_assist.py`'s own comment).
3. No FC/ESC/motor/propeller subject in the plain declared-envelope grammar — box only via catalog bind (or, ESC height only, the estimated-temporary path).
4. `bind_esc_from_catalog`'s stale-property-leak on a cross-SKU rebind (found live during the estimated-temporary-ESC-Skystars Buy) — named, not re-investigated here.
5. Motors/propellers never get a `cabe`/attest verdict, even as a cylinder — disk-station fit attest is a separate, unbuilt Buy.
6. A bare `layout pack` only works while exactly one pack is registered — no disambiguation UI for a second pack yet.

None of these were "fixed" — per lock #9, this Buy documents montage-spine debt, it does not resolve it.

## What was deferred

- Full command encyclopedia beyond the montage spine (kit hardware detail beyond a one-line mention, `DEFINE_MISSING_PARAMETERS` wizard, every historical FN) — the inventory stays wide where it's cheap (§§1–8 there), the guide stays narrow to the spine, per lock #9's own explicit exclusion list.
- English localization — not requested, listed as "later if ★" in the IC's own out-of-scope table.
- Any `src/`/`ui/`/`tests/`/`library/` fix for the gaps found above — explicitly forbidden this cycle (lock #9: "fixing bind-esc leak (N1)" is named out-of-scope).
- A PRIORIDAD/README pointer link — the IC's own §2.6 makes this Engineer-★-gated, not a default; I did not add one. The guide is discoverable via `docs/USER_GUIDE_CRAFT_MONTAGE.md` directly and is cross-linked FROM the inventory artifact's own header.

## Live validation

All example phrases were checked against parser functions directly (deterministic, read-only — no LLM, no state mutation for the validation itself). The §10 worked example's numbers were read from `10-min-autonomía`'s actual live project file, not invented or hand-computed, and re-confirmed by round-tripping the corrected phrases back through the real parser. No `workspace/` file was written during this Buy (only read).

## Non-goals honored

No new product feature. No `src/`/`ui/`/`tests/`/`library/` edit. No version bump (`pyproject.toml` still `0.4.1`, untouched). No ASSEMBLY READY / VERIFIED CAD / visual-recognition claim anywhere in the guide — §1 states the negative scope explicitly and every checklist section repeats the relevant honesty caveat inline. No PRIORIDAD reshuffle (Cursor's own cola ownership respected — I only added a `docs/IMPLEMENTATION_TASKS.md` status line for this Buy itself, not a reordering of anything else).

## Remaining risks / notes for review

- The guide's own "living document" promise (its closing line: "si una frase de aquí deja de aparecer en el inventario, esta guía está desactualizada") has no automated check behind it — a future phrase-changing Buy could silently make the guide stale unless whoever ships that Buy remembers to touch it. Worth a lightweight process note (not a code change) for future ICs that touch any Continuity trigger regex.
- §10's worked example is tied to `10-min-autonomía`'s CURRENT live state — if that project's identities/poses change in a future cycle, the guide's numbers will drift from reality. This is an accepted tradeoff for concreteness (per the IC's own "prefer validating example phrases against 10-min-autonomía... docs of record") but flagged so a future guide refresh knows to re-pull the numbers rather than assume they're still accurate.
