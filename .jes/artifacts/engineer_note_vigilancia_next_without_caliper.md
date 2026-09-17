# Engineer note — What vigilancia still needs (no caliper / no bench)

**Date:** 2026-09-17  
**Authority:** Engineer ask — practical reflection while #5 implements; defines **next product step** after software closeout  
**Live project:** `dron-de-vigilancia-doméstico` (read-only census)  
**Constraint:** Next step must **not** depend on Engineer measuring parts or running thrust/lab tests

---

## Where vigilancia is today (honest)

| Layer | Status |
|---|---|
| Propulsion / energy / ERF | PASS · ASSEMBLY READY · margin ~3.62 |
| Mission identity | `cameras` + `radio_module` medium (model only) |
| Continuity | “Revisar margen vs carga de misión” (correct, but **soft dead-end**) |
| OP evidence | `fallback_operating_point` — combo XING-E+Gemfan **not** exact (HD-005 / banco) |
| Autonomy | ~0.7 min — honest with current OP; **useless as vigilancia endurance claim** |
| `payload_kg` | 1.0 kg blob — **not** decomposed into camera/radio mass |
| Board / `relaciones` | Plate still 🟡 estimated → stack attest blocked (**needs caliper** — out) |
| Mounts | FC / cameras / radio often **unmounted** — declarable in software today |

Jarvis can already **fly the numbers** for a generic lift problem. It cannot yet **finish a vigilancia product story** without either (a) physical bags or (b) a new software seam for mission stack → energy.

---

## Explicitly NOT the next step (depend on you / lab)

| Item | Why park |
|---|---|
| Plate L×W real / `B1-plate-box` | Caliper or OEM cite |
| ESC H “de verdad” / HD-* OP exacto | Banco or estimate bag ★ |
| Path N | Schema HOLD |
| Firmware / MAVLink / bind ELRS / Betaflight | Outside Jarvis SoT |
| Axial hélices↔motores geometry | Needs facts that don’t exist |

---

## What still blocks “continue the drone” in software only

Ranked by **product unlock** for this live project:

### 1. Mission stack does not feed energy (primary gap)

Camera/radio are labels. Mass/power of misión stay outside `calculate_total_mass` / autonomy. Continuity correctly refuses “más kg genéricos”, then has nowhere useful to go.

**Software-shaped Buy (recommended next ★):**  
Allow **Engineer-declared** (or cited) `mass_g` / optional `power_w` on `cameras` / `radio_module` (and later VTX), `source=declared` or catalog when bags exist — **mirror into total mass / electrical budget** like battery/motor already do. Agent must **not** invent numbers; user/datasheet paste or future `library/cameras` bags.

Unlock: autonomia and margin become *mission-aware*; Continuity can leave the soft dead-end.

### 2. Continuity soft dead-end after mission-margin review

After “Revisar margen vs carga de misión”, next useful software steps exist but aren’t ranked: mount camera/radio/FC, declare endurance restriction, declare mission mass, optional VTX identity.

**Thin companion Buy (or same cycle):** mission **checklist / Continuity ladder** (suggest-only, deterministic) for ASSEMBLY READY + mission intent projects.

### 3. Mounts / pose of mission avionics (cheap, already possible)

`montajes estándar` / `mounted_on` for FC→plate, camera, radio — **no new code strictly required**, but Continuity doesn’t push it. Either docs nudge or Continuity #2 above.

### 4. Endurance as a first-class restriction

Vigilancia without “≥ X min” stays a thrust toy. Software: ensure restrictions parse endurance and Continuity tracks FAIL/WARN against computed autonomy — **without** claiming flight validation (still OP-honest).

### 5. Video path hole (optional identity)

Many vigilancia stacks need **VTX / video link** separate from `cameras` + `radio_module` (ELRS). Identity-only key (like cameras) — only if Engineer wants that family named; else fold into radio/camera narrative in checklist.

### 6. #5 extended identity (in flight)

payload/arm/wheels/gearbox — **little unlock for this aerial vigilancia craft**. Fine as closeout hygiene; **not** what unblocks this project’s next useful engineering step.

---

## Recommendation — next ★ after #5 closes

**Developed brief:** [engineer_note_mission_mass_energy_next_step.md](engineer_note_mission_mass_energy_next_step.md)

```text
★ B1-mission-mass-energy (working name)
   mission component mass (user/cited) → AUW
   + Continuity ladder off “margen vs misión”
```

**In:** declared/cited `mass_g` on cameras/radio → mass math (P1 + double-count warn); Continuity asks for mass/mount/endurance — not a dead-end review line.  
**Out:** inventing grams · plate-box · HD-005 · firmware.

---

## One-line product truth

> Vigilancia ya **monta y simula** como dron genérico; le falta que la **carga de misión deje de ser un cartel** y pase a **mover masa/energía y el siguiente paso útil** — sin pedirte el calibre ni el banco.
