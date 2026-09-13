# Field Note — Mount checklist tips use keys the parser rejects (FC / sensors)

**Date:** 2026-09-13  
**Project:** `10-min-autonomía`  
**Authority:** Engineer smoke transcript  
**Status:** **ABSORBED** into [implementation_contract_geometry_arm_radial_mount_tip_b1.md](implementation_contract_geometry_arm_radial_mount_tip_b1.md) (combined with arm radial). Await Engineer ★ on that IC.  
**Related:** mount-standard-assist B1 · `mounted_on_declare_assist.py`

---

## Symptom

Checklist says:

```text
'flight_controller montado en <clave>'
'sensors montado en <clave>'
```

Typing those exact phrases → **NONE** → “No se pudo interpretar la intención”.

`esc montado en frame_plate` and `battery montado en frame_plate` work (keys match subject regex / alias).

---

## Root cause (Cursor verified)

| Phrase | Parse |
|---|---|
| `flight_controller montado en frame_plate` | **NONE** — subject pattern is `flight controller` / `controladora` / `fc`, **not** underscore key |
| `sensors montado en frame_plate` | **NONE** — pattern is `sensor`/`sensores`/`gps`, **not** English plural `sensors` |
| `controladora montada en frame_plate` | SET |
| `sensor montado en frame_plate` | SET |

`mount_standard_assist.format_…` for **ambiguous** rows emits the raw `subject` key in the tip string. Parser `_resolve_subject` never does exact component-key match (only noun patterns). Tip and parser disagree.

---

## Workaround (Engineer — now)

```text
controladora montada en frame_plate
sensor montado en frame_plate
```

(or `fc montado en frame_plate` / `gps montado en frame_plate`)

---

## Suggested Buy (thin)

**`B1-mount-ambiguous-tip-parse-align`**

1. Ambiguous tips use **same nouns as `example_phrase`** (controladora / sensor / esc / batería), not raw keys; **or**  
2. `_resolve_subject` accepts exact `components` keys (`flight_controller`, `sensors`, …) like targets already do via `_exact_key_match`.

Prefer **both**: tip nouns for UX + exact-key subject for paste-from-checklist.

Regression: checklist tip string for FC/sensors must parse as SET against a fixture with those keys + `frame_plate`.

---

## Out of this note

Layout-pack IC (Claude in flight). Path F N1 empty-copy.
