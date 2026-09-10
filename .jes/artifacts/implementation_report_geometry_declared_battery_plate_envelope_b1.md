# Implementation Report — Declared battery envelope + Main Plate L×W B1

**IC:** [implementation_contract_geometry_declared_battery_plate_envelope_b1.md](implementation_contract_geometry_declared_battery_plate_envelope_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2573 → **2583** (2573 + 10 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/declared_envelope_declare_assist.py` | **New.** Pure parser (`parse_declared_envelope_declare` → `EnvelopeDeclareResult`, kinds `SET`/`CLEAR`/`AMBIGUOUS_PLATE`/`INCOMPLETE`/`NONE`). Reuses `mounted_on_declare_assist`'s public wrappers (`resolve_component_subject_noun`, `resolve_declared_part_noun`) — no private `_`-prefixed import. Gate: `respecto` anywhere → `NONE` (pose owns it) checked first; `declara(r)` + a 2- or 3-number `mm` triple/pair for SET; `quita(r) (el) sobre` / `quita(r) (las) cotas` for CLEAR. Subject resolution accepts only `"battery"` or a `is_frame_plate_key` key — any other resolved key (frame root, arm, cage, standoff, motors, esc, fc, sensors) is filtered to `None`. Added a dedicated `"placa principal"`/`"main plate"` resolver (`_resolve_main_plate`) that matches a plate's own `label` property normalizing to exactly `"main plate"` — independent of the generic label-substring match, since the utterance never literally contains the English label text. |
| `src/jarvis/core/component_writers.py` | Added `set_component_declared_box_envelope(project_state, component_key, length_mm, width_mm, height_mm)` — the one write path for the box triple on `battery`/`frame_plate*` only (`ValueError` for anything else, including `frame` root/motors). SET merges exactly those three `PropertyValue`s (`source="declared"`) into the spec's existing properties, preserving `catalog_ref`, `declared_box_pose`, `mounted_on`, and every other property (including a plate's own `thickness_mm`, never touched). All-`None` clears the three keys, idempotent if already absent. Added `is_frame_plate_key` to the existing `jarvis.domains.aerial` import. |
| `src/jarvis/core/orchestrator.py` | Added the IDLE dispatch bridge (`_try_handle_declared_box_envelope`, called right after the pose bridge and before the `"cabe"` bridge — same insertion point and honesty-message style as the pose/mount bridges). For a two-number plate `SET`, the orchestrator (not the parser) reads that plate's own `thickness_mm` and passes it as `height_mm` to the writer, appending an honest "Alto tomado del thickness_mm citado" note. Confirm messages state the three mm and `source=declared`; forbidden tokens (`"cabe"`, `"verificado"`, `"ensamblado"`, `"230"`) never appear in generated copy. |
| `tests/test_geometry_declared_battery_plate_envelope_b1.py` | **New.** P1–P10 exactly per IC §4. |

`library/`, `workspace/`, `ui/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new changes in any of those beyond what already existed from earlier closed cycles this session; version still `0.3.8`).

---

## Behavior changed

- Two new IDLE phrases: `"declara la batería L x W x H mm"` (battery, all three numbers required — never infers a height) and `"declara la placa principal L x W mm"` (or an exact/labeled plate key; third axis from the utterance if named, else copied from that spec's own cited `thickness_mm`, never invented). Clear phrases (`"quita el sobre de X"` / `"quita las cotas de X"`) pop exactly the three box keys, leaving `thickness_mm` and every other property untouched.
- `_geometry_from_spec` (unchanged) now naturally draws a `box` for whichever `battery`/`frame_plate*` spec has all three keys declared — no projector change was needed.
- **The "juntos" payoff**: once a plate has a declared box (via this Buy), the already-shipped `set_component_declared_box_pose` accepts it as an origin (previously it always raised, since no plate ever had `geometry: box`) — verified directly (P7): before the plate SET, posing anything against `frame_plate` raises `ValueError`; after, it succeeds. No pose-writer code was touched to achieve this — it's a direct consequence of the box now existing.
- No physics/`current_parameters`/PASS impact — these three keys are purely additive display properties, same class as the catalog envelope's own `length_mm`/`width_mm`/`height_mm` handling.
- `refresh_component_from_catalog` on `battery` continues to preserve the declared L×W×H after this write (verified, P9) — `bind_battery_from_catalog`'s existing `{**base.properties, **projected}` merge never overwrites a key the catalog seed (`lipo_3s_2200mah`, still no L×W×H) doesn't itself provide.

---

## Tests added / executed

New: `tests/test_geometry_declared_battery_plate_envelope_b1.py` — 10/10 passing:
- P1: battery 80×34×22 SET — three props `source=declared`, `catalog_ref`/Wh/mass/cells unchanged, projector box 80/34/22.
- P2: `"declara la placa principal 100 x 100 mm"` — L=100 W=100, `height_mm=4` applied at the orchestrator layer from cited `thickness_mm` (parser itself returns `height_mm=None`), `thickness_mm` still 4, frame `wheelbase_mm` still 230, one `frame_plate` node.
- P3: battery two-number phrase → `INCOMPLETE`, no write.
- P4: bare `"declara la placa 100 x 100 mm"` with two plates declared → `AMBIGUOUS_PLATE` with both candidates.
- P5: CLEAR battery pops only the three box keys; `battery_capacity_wh`/`mass_g`/`cell_count` survive.
- P6: writer `ValueError` on `frame`/`motors`; no geometry invented on the frame root.
- P7: pose-origin unlock — `ValueError` before the plate SET, succeeds after.
- P8: a `"respecto"` phrase → parser `NONE` (pose's own grammar untouched).
- P9: `refresh_component_from_catalog("battery")` after P1 → L×W×H still 80/34/22.
- P10: full orchestrator IDLE round-trip — SET battery phrase persists and returns an honest, forbidden-token-free confirm message; `"cambiar batería"` afterward still opens the battery catalog rebind (unaffected — that dispatch runs earlier in the IDLE chain, before this Buy's bridge).

Full suite: `python -m pytest -q` → **2583 passed**, 0 failed.

---

## Live verification (read-only)

Ran the new parser + writer against the real `autonomía-de-5min` project's live `frame_plate` spec (never saved back): `"declara la placa principal 100 x 100 mm"` resolves to `frame_plate`, and applying it with the live `thickness_mm=4` yields `geometry == {shape: box, 100, 100, 4}` while `frame.wheelbase_mm` stays exactly `230.0` — confirming the "never stitch 230 into L or W" lock holds against real data, not just fixtures. No `workspace/` file was written.

---

## Non-goals honored

No `length_mm`/`width_mm` seeded onto `lipo_3s_2200mah` or any Rooster plate in `library/`. No `wheelbase_mm`/`max_stack_height_mm`/`body_*` read anywhere in the new parser or writer. `set_battery_component` never called by this path — energy fields are fully untouched. `_geometry_from_spec`'s box-requires-full-triple gate unchanged. No visor-X (`solidCopyOffsetsMm`/`layoutSolidsRow`) code touched. No auto-declared battery pose — P7 only proves the writer *would* now accept it if asked. No `ui/`/`Conversation Engine`/version bump.

---

## Remaining risks

- None identified specific to this change — the writer's `ValueError` scope (`battery` or `is_frame_plate_key` only) and the parser's subject filter are both exercised directly by tests (P6).
- As accepted by the IC itself: a plate's `AMBIGUOUS_PLATE` resolution during a `CLEAR` phrase (not explicitly in the P-list) is handled symmetrically with `SET` for consistency, but has no dedicated regression test — low risk, since it reuses the exact same `_resolve_subject` path already covered for `SET` (P4).
- Live Engineer smoke (typing real millimetres against `autonomía-de-5min`, then optionally declaring a `respecto` pose against the now-boxed plate) remains a separate, manual step per IC §6 — not exercised by this report beyond the read-only verification above.
