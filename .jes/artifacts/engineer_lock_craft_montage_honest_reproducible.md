# Engineer lock — Craft montage as next product objective (honest · reproducible)

**Date:** 2026-09-13  
**Authority:** Engineer — *próximo objetivo = layout-pack / stack / Situar que monte el craft; limpio, honesto, reproducible para otros proyectos (no solo cumplir uno).*  
**Status:** LOCKED intent · **Path F IN FLIGHT (Claude)** · mechanism first · no invent · no one-project hack  
**Parents:** [cola Situar](engineer_note_board_situar_work_cola.md) · [layout-pack IC](implementation_contract_geometry_layout_pack_cited_b1.md) · [stack-rule](implementation_contract_geometry_stack_rule_b1.md) · [silhouette Product B](implementation_contract_board_silhouette_product_b_b1.md) · [estimated plate](implementation_contract_geometry_estimated_temporary_plate_b1.md) · greenfield smoke [10min](field_note_smoke_greenfield_10min_b0.md)

---

## Product sentence (locked)

```text
Jarvis debe poder montar un craft en el Board de forma limpia y honesta:
mecanismo reutilizable para cualquier proyecto con datos citados/declarados,
no un layout hardcodeado que solo “cumpla” el 10min o el 5min.
Sin tabla / sin caja de placa / sin confirmación del usuario → no inventa poses.
```

---

## What “done” means (visual · honest)

On **any** project that meets the same gates (not a named SKU special-case):

1. **`frame_plate` box** at assembly root (world 0) — cited/caliper **or** `estimated_temporary` with disclosure (layout only; never “cabe” / verified CAD).  
2. **Mount graph** expressible edges declared (mount-assist / Continuity) — user confirms.  
3. **Stack / pack poses** for box subjects (FC, ESC, battery, sensors, …) relative to plate — from **cited pack rows** and/or **Path F stack rule** on envelopes — never from wheelbase→body invent.  
4. **Motors/props** on Visor X from **cited wheelbase** (already shipped) — not disk-as-pose-origin invent.  
5. **Situar** remains the residual tool for anything not in pack/rule — never replaced by silent LLM pose.  
6. **Product B (“parece un dron”)** only when prerequisites bag is met and copy does not overclaim estimated plate as measured.

Gallery-of-parts (greenfield 10min screenshot) = **Product A racimo** until the above.

---

## Reproducibility rule (anti-hack)

| Layer | Must be reusable | May be kit-specific |
|---|---|---|
| Writers | `set_component_mounted_on` · `set_component_declared_box_pose` · envelope declare | — |
| Assists | mount-standard · layout-pack loader · Path F stack propose · Situar UX | — |
| Pack **format** | Same schema for every kit (`pack_id`, authority, rows, `requires_plate_box`) | — |
| Pack **data** | — | One filled §0.1 table per kit (MY5, GEP-Racer, …) |
| Tests | Fixture pack + missing-prereq skip + no invent | Optional live apply ★ per project |

**Forbidden:** hardcoding Δmm for `10-min-autonomía` / `autonomía-de-5min` inside orchestrator or visor; “typical freestyle stack” without a pack row; copying body 225×200 or 175×173 onto plate L×W as “real”.

---

## Ordered path (clean · already on cola)

```text
A. Plate present (2b estimated OK for layout smoke · 2 caliper/cita replaces for “de verdad”)
B. Mounts (1 mount-assist) — confirm phrases
C. Poses:
     C1 ★ NOW: Path F craft montage — [IC](implementation_contract_geometry_craft_montage_path_f_b1.md)
        (centered stack on plate; estimated plate OK; multi-project)
     C2 layout-pack-cited — when §0.1 XY table filled
     C3 Situar — residual / override
D. Silhouette Product B — claim only after A+B+C honest on that project
```

**Next engineering focus:** ★ + implement **`B1-craft-montage-path-f`**. Smoke on **5min and 10min**. Layout-pack XY and Product B stay gated.

---

## Explicit non-goals (until separate ★)

- Continuity kit-tip spam (G1) — useful lateral; does **not** replace montage objective  
- HD-005 / true hover autonomy  
- Invent plate from OEM body envelope  
- Three.js rewrite / LLM auto-pose  
- Claiming Product B on racimo-only boards  

---

## Engineer next concrete move

1. Keep purge / lateral Bugs as Claude landings — do not derail.  
2. Choose **first pack kit** (recommend `hglrc_my5_5in` — already on 5min + 10min) **or** ★ Path F on estimated plate.  
3. Fill [layout-pack §0.1](implementation_contract_geometry_layout_pack_cited_b1.md) with measured/cited rows **or** caliper plate for plate-box.  
4. Smoke the **same** assist phrases on two projects before Product B claim.
