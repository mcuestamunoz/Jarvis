# Implementation Contract — User command guide to craft montage (`B1-user-guide-craft-montage`)

**Project:** Jarvis  
**Date:** 2026-09-14  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer walk of the guide on a live project

**Status:** READY FOR ★  
**Parents:**
- Craft montage honesty lock — [`.jes/artifacts/engineer_lock_craft_montage_honest_reproducible.md`](engineer_lock_craft_montage_honest_reproducible.md) — “done” = plate · mounts · stack/pack/Situar · silhouette honesty (not ERF ASSEMBLY READY)
- Silhouette semantics lock — [`.jes/artifacts/engineer_lock_silhouette_checklist_semantics.md`](engineer_lock_silhouette_checklist_semantics.md) — `parece un dron` = **checklist**, never visual recognition
- Continuity / assists map — [`docs/system_map/08_continuity/CONTINUITY_MAP.md`](../../docs/system_map/08_continuity/CONTINUITY_MAP.md)
- Live smoke projects: `10-min-autonomía`, `autonomía-de-5min`
- Gap: many IDLE/Continuity features shipped as Spanish phrases; **no single user-facing command walk** from “nuevo proyecto” → craft montage on Board

**Type:** **Documentation Buy** (primary deliverable = markdown under `docs/`).  
**Mandatory Phase 0 = deep inventory** of what Jarvis actually exposes today (commands / phrases / assists / Board actions).  
**Phase 1 = user guide** — step-by-step **command-level** path to the craft-montage endpoint.  
**Not** new product features. **Not** `src/` / `ui/` / `tests/` / `library/` changes unless a Phase 0 finding forces a one-line doc-only correction (prefer report the gap; do not “fix” product in this Buy). **Not** version bump. **Not** claiming ASSEMBLY READY / VERIFIED CAD / visual drone recognition.

**Outputs (both required):**
1. `.jes/artifacts/inventory_user_facing_commands_craft_montage_b0.md` — Phase 0 inventory (evidence-backed)
2. `docs/USER_GUIDE_CRAFT_MONTAGE.md` — Phase 1 guide (Spanish primary; command examples copy-pasteable)
3. `.jes/artifacts/implementation_report_user_guide_craft_montage_b1.md` — short report: inventory method, guide TOC, gaps found, what was deferred

**Checkpoint:** package **`0.4.1`** · suite current green at ★ time (doc Buy — no suite growth required)

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-user-guide-craft-montage`** — inventory first, then user guide to montage endpoint |
| 2 | Audience | Engineer / power user who drives Jarvis via **CLI Continuity IDLE** (+ Board Situar where relevant). Not a marketing page. Not an architecture dump |
| 3 | Language | Guide body in **Spanish** (matches CLI copy). Inventory may be Spanish or bilingual tables; phrase examples **must** match code (Spanish triggers as shipped) |
| 4 | Endpoint (“punto final”) | **Craft montage honesty endpoint** per lock — not full ERF “assembly ready”. Explicit end state the guide aims at: Board shows plate root + mounted/posed box stack (FC/ESC/battery/sensors as available) + motors/props on Visor stations + user can run `parece un dron` / `relaciones` and understand honesty (B / B\* / estimated_dims). Label clearly: **montaje honesto en Board ≠ ASSEMBLY READY** |
| 5 | Phase 0 gate | **STOP before writing the guide** until the inventory artifact exists and lists evidence per command family. No guide drafted from memory alone |
| 6 | Phrase truth | Every example phrase in the guide must trace to a parser / orchestrator bridge / smoke note. **Forbidden:** inventing friendly aliases that code does not accept |
| 7 | Honesty | Document `estimated_temporary` (placa, ESC H), screening / `cabe` refuse, fit-attestation refuse, silhouette checklist semantics. Never tell the user “ya cabe / verificado” when the system only screens |
| 8 | Scope in | IDLE Continuity commands for: project open/status · catalog help-choose / rebind · envelopes · estimated plate/ESC H · mounts · pose · Path F stack · layout pack · Situar (Board) · `cabe` · `declaro verificado` · `relaciones`/`fit` · `parece un dron` · refresh catalog · kit hardware where it sits on the path. Energy/sim (`calcular`/`simular`/`estado`) as **short adjacent sidebar** only — not the spine of this guide |
| 9 | Scope out | Rewriting ARCHITECTURE.md · system map overhaul · full ERF gap encyclopedia · wizard DEFINE_MISSING deep dive · every historical FN · new assists · fixing bind-esc leak (N1) · plate-box / Path N holds |
| 10 | Live | Prefer validating example phrases against `10-min-autonomía` / docs of record; **no** mandatory workspace mutation. If a probe phrase is typed live, prefer read-only / non-mutating checks |
| 11 | Version | **No** bump |

**Product sentence:**

```text
Un documento que diga, en orden y con comandos reales de Jarvis,
cómo pasar de un proyecto vacío (o a medias) hasta un craft montado
de forma honesta en el Board — sin inventar frases ni sobreclaim.
```

---

## Phase 0 — Deep inventory (mandatory · before the guide)

### 0.1 Mission

Answer, with evidence: **What can a user actually type / click today** that advances craft montage or related Continuity?

### 0.2 Search method (minimum — do all)

Work from **code and tests**, not from chat memory. At minimum:

1. **Orchestrator IDLE bridges** — enumerate every `_try_handle_*` in `src/jarvis/core/orchestrator.py` (early Continuity block ~mounted_on → frame_part and any siblings). For each: trigger summary + writer/assist module.  
2. **All `*_assist.py` under `src/jarvis/core/`** (~19 files today — recount at ★). Extract locked regexes / example phrases from module docstrings + `parse_*` / `is_*` functions.  
3. **Catalog rebind / help-choose** — `catalog_rebind_assist`, motor/prop/battery/esc/frame/control_identity/kit assists; `ayúdame a elegir` vs `cambiar <familia>`.  
4. **Writers surface** — `component_writers.py` public `set_*` that Continuity reaches (envelope, pose, estimated plate/ESC, mount, fit attestation, catalog bind/refresh).  
5. **Board / UI** — Situar / drag / free-camera actions that mutate pose (from `ui/` + Board Situar ICs/smoke) — list as **Board steps**, not fake CLI.  
6. **Smoke / Engineer notes** — `.jes/artifacts/engineer_smoke_*` and closed craft-montage ICs for **phrases that actually worked** on 10min/5min.  
7. **Global CLI** — thin list: `estado`, `resumen`, `calcular`/`simular`, project switch/new — only enough for “where am I / don’t get stuck”.  
8. **Honesty / refuse paths** — document when Jarvis **refuses** (`estimated_dims`, missing box, incomplete pose, disk n/a).

### 0.3 Inventory artifact shape

Write `.jes/artifacts/inventory_user_facing_commands_craft_montage_b0.md` with tables like:

| Family | Example phrase(s) | Module / bridge | Mutates? | Notes / honesty |
|---|---|---|---|---|
| … | `declara el esc estimado 8 mm` | `estimated_temporary_esc_assist` | yes | H only; gates cabe |

Plus:

- **Ordered montage spine** (draft): recommended step order A→…→end (align with craft montage lock A–D).  
- **Gaps / traps**: phrases users might expect that **do not exist** (e.g. FC IDLE rebind if still unwired — library review N1).  
- **Out of montage spine**: energy/sim features found but deferred to sidebar.  
- **Counts**: # assist modules scanned, # orchestrator bridges listed, # smoke phrases reused.

**STOP gate:** Do **not** start `docs/USER_GUIDE_CRAFT_MONTAGE.md` until this inventory file is written and self-consistent (every spine step cites ≥1 inventory row).

---

## Phase 1 — User guide

### 1.1 Path & shape

`docs/USER_GUIDE_CRAFT_MONTAGE.md`

Suggested TOC (adjust only if inventory forces it — document why in report):

1. Qué es este guía / qué **no** promete (montaje Board ≠ ASSEMBLY READY)  
2. Cómo arrancar (proyecto, `estado`, Board)  
3. Identidad + catálogo (frame, motores, hélices, batería, ESC, FC/GPS) — `ayúdame a elegir` / `cambiar …`  
4. Placa main (citada **o** `estimada`) + disclosure  
5. Sobres L×W×H (declare / catalog) · ESC H estimada si aplica  
6. Montajes (`mounted_on` / checklist)  
7. Poses: Path F stack · layout pack · Situar residual  
8. Motores/hélices en Visor (stations / radial — as shipped)  
9. Comprobar: `cabe` · `relaciones` · `declaro verificado` · `parece un dron`  
10. Cheatsheet — una página de frases copy-paste  
11. Apéndice corto — energía/`calcular` (fuera del spine) · limitaciones conocidas (holds plate-box, Path N, bind-esc leak, FC without box, etc.)

### 1.2 Style locks

- Prefer **numbered steps** with a **literal command block** each.  
- After each critical step: one line **qué deberías ver** (card / Board / Continuity message).  
- Mark **estimado** vs **citado** visually (e.g. callout).  
- Keep length usable: target **~400–800 lines** markdown, not a second ARCHITECTURE.md. Prefer depth on montage spine; inventory holds the encyclopedic table.  
- Link to locks / system map only where honesty requires it (silhouette, estimated dims).

### 1.3 Validation

- Spot-check ≥10 guide phrases: either appear in inventory with module cite, or in a smoke artifact.  
- Walk the cheatsheet mentally against `10-min-autonomía` current capabilities (read-only).  
- Report any phrase in older smokes that **no longer** match code (do not put stale phrases in the guide).

---

## 2. You (Claude)

1. ★ received → **Phase 0 only first**: run the search method; write the inventory artifact.  
2. In the report (or inventory footer), list spine order A→end before drafting the guide.  
3. **Phase 1**: write `docs/USER_GUIDE_CRAFT_MONTAGE.md` from the inventory (no memory-only phrases).  
4. Write implementation report (method, TOC, gaps, deferred).  
5. No `src/`/`ui/`/`tests/`/`library/` edits. No version bump.  
6. Optional one-line pointer from `docs/IMPLEMENTATION_TASKS.md` or `README.md` **only if** Engineer ★ asks — default: **do not** reshuffle PRIORIDAD (Cursor owns cola); you may add a “See also” link inside the guide only.

**STOP if** Phase 0 would require inventing commands, or if “endpoint” is reinterpreted as ERF ASSEMBLY READY without Engineer override.

---

## 3. Tests

Doc Buy — **no new pytest required**.  
Optional: zero code change → existing suite still green if anything was touched by mistake (should be untouched).

---

## 4. Smoke (Engineer)

1. Open `docs/USER_GUIDE_CRAFT_MONTAGE.md` + inventory.  
2. On `10-min-autonomía` (or greenfield): follow cheatsheet steps that apply; confirm phrases still fire.  
3. Confirm guide does **not** claim visual recognition or false “cabe”.  
4. ACCEPT → Cursor closes Buy / links from PRIORIDAD.

---

## 5. Out of scope (named debt)

| Item | Note |
|---|---|
| Interactive in-app tutorial / wizard UI | Later |
| Full command encyclopedia of every Continuity line ever | Inventory can be wide; guide stays montage-spine |
| Fix FC IDLE rebind / bind-esc omit-key leak | Separate ★ (already queued notes) |
| Plate-box measured / Path N | Holds unchanged |
| English localization of the guide | Later if ★ |

---

## 6. Done when

- [ ] ★  
- [ ] Inventory artifact complete (Phase 0 method covered)  
- [ ] User guide published at `docs/USER_GUIDE_CRAFT_MONTAGE.md`  
- [ ] Implementation report  
- [ ] Cursor review PASS  
- [ ] Engineer smoke ACCEPT (walk cheatsheet)

---

## 7. Handoff

```text
Engineer → ★ (optionally: preferred demo project for examples)
Claude   → Phase 0 inventory → STOP gate → Phase 1 guide + report
Cursor   → review (phrases ↔ code; honesty; endpoint scope)
Engineer → walk cheatsheet on 10-min · ACCEPT
```
