# Engineer smoke — Kit boxes typed mm (power_connector / signal_harness) (2026-09-10)

**Project:** live Board (5min / current pack)  
**Status:** **WALK** — no new IC (Declared sensors + kit envelope B1 already **CLOSED** @ **2593**)  
**Authority:** Engineer “procede con XT60 o harness con mm tipados”

## Locked honesty

- L×W×H are **Engineer-typed** (`source=declared`).  
- Catalog rows (Pololu XT60 / Pi Hut JST) have **no** box dims — **do not** invent from marketing or from `cable_length_options_mm`.  
- Pose is optional and separate (`respecto` = pose grammar).

## Suggested Continuity (pick your own mm)

Envelope (no `respecto`):

```text
declara el conector 30 x 20 x 10 mm
```

```text
declara el harness 30 x 10 x 5 mm
```

(Alternate nouns: `xt60`, `cable de señal`, `power_connector`, `signal_harness`.)

Optional situar (after boxes exist; origin must be a **box** — e.g. Main Plate):

```text
declara el conector a 0 mm en x y 40 mm en y y 5 mm en z respecto a frame_plate
```

```text
declara el harness a 0 mm en x y -40 mm en y y 5 mm en z respecto a frame_plate
```

## Pass when

| Step | Expected |
|---|---|
| Connector declare | `power_connector` card shows L×W×H; solid in 3D |
| Harness declare | `signal_harness` box; pin/pitch untouched |
| No catalog seed | library kit rows still lack length/width/height |
| Optional pose | kit solids join / sit near the racimo |

Record ACCEPT here when both envelopes (and optional poses) look right.
