# Engineer smoke — Pre-assembly reds R1/R2 (CLI walk)

**Date:** 2026-09-08  
**Status:** ACCEPT (Engineer: corregido desde CLI + 4 motores)  
**Project:** `autonomía-de-10min` (`9ada1a1b0cca`)  
**Parent:** [engineer_lock_geometry_pre_assembly_honesty.md](engineer_lock_geometry_pre_assembly_honesty.md)

## Walk

| Red | Phrase | Result |
|---|---|---|
| R2 GPS | `sensor montado en el frame` | `sensors.mounted_on` = **`frame`** (was `esc`) |
| R1 count | `4 motores` + FN-004 `sí` | `motor_count` **4** in params and motors spec (`declared`) |

Cursor verified on disk after `active_iteration` 72. No hand-edit.

## Side effect

`motors.mounted_on` cleared (`null`; was `frame_arm`) on the count/SKU rewrite. Optional: `motores montados en los brazos`.

## Verdict

**ACCEPT.** Two reds closable without IC.
