# Engineer note — `v0.6.0` closes ontology explain branch

**Date:** 2026-09-28  
**Tag:** **`v0.6.0`** (package `0.6.0`)  
**Previous tip:** `v0.5.44` (bloque 0.5 / software-month C36–C43 CLOSED)

---

## What this tag closes

Epoch **`0.6` ontology / explain layer** — vault value + spine + docs crosswalks. **No** Assistant runtime, **no** `intelligence/` on disk, **no** Continuity/FS reading `ontology/`.

| Deliverable | Status |
|---|---|
| B0 vault value for Jarvis | ★ ACCEPT CLOSED |
| Plantilla + spine lotes 1–5 solid | ★ cite-audits ACCEPT CLOSED |
| ONT-docs [`ONTOLOGY_CROSSWALKS.md`](../../docs/ONTOLOGY_CROSSWALKS.md) | LANDED |
| Tip / package | **`v0.6.0` / `0.6.0`** |

Spine (solid + audited): Vectores · Dinámica · Momento · Control clásico/robótico · Sensores · Accel/Gyro/IMU · Actuadores/Motores/Motor DC · Corriente · C-rate · OP vs intrínseco · Magnetismo · Navegación · Forma banco empuje.

---

## What this tag is not

- Not RAG / Assistant retrieve  
- Not CLI citing notes  
- Not closing HD-* with invented curves  
- Not silicon / bench  

---

## Next epoch slice — Assistant @ `0.6.1+`

Cola A0–A3 in [`IMPLEMENTATION_TASKS.md`](../../docs/IMPLEMENTATION_TASKS.md):

1. ★ `DC-assistant-placement`  
2. IC scaffold `src/jarvis/intelligence/`  
3. IC R2 read-only spine retrieve  
4. Terminal/CLI canal  

**First Assistant product tag target:** **`v0.6.1`** (after A0 ★ + at least A1 scaffold ACCEPT). Further retrieve/canal Buys may continue on `0.6.x`.
