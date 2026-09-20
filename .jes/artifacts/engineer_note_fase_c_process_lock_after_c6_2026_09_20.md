# Engineer note — Fase C process lock after C6 (2026-09-20)

**Author:** Cursor (capture of Engineer evaluation)  
**Trigger:** Engineer affirmed path; discipline for next Buy.

---

## Affirmed

- Small verifiable rungs; each Buy must not pretend to solve the next.
- Keep: RejectAll · command surface ≠ execution · Authority ≠ allow · Python scaffold ≠ production C++ FC · craft↔platform coupling = **zero**.
- Tag = important tip block (not automatically every C). Clean tip after ACCEPT.

## After C6 ACCEPT @ `v0.5.4`

**Do not open three fronts** (estimation + real Safety + C++ + ELRS at once).

**One question before any C7 IC:**

> ¿Cuál es el siguiente cuello de botella técnico que merece convertir en un peldaño?

Likely candidate (not authorized until IC ★): **state estimation** — filtered IMU → attitude/state. Substantially harder than C6 (frames, bias, gravity, drift, observability). Needs its own IC and acceptance criteria before code.

## Explicitly not now

| Out | Why |
|---|---|
| Craft Continuity ↔ FS wiring | Keep isolation |
| Physical drone / ESC path | Ladder incomplete + Safety/HW |
| Real ELRS/CRSF | C5 already defined the boundary |
| plate-box / HD-* | Unrelated; needs physical data |
| “Ya que estamos…” multi-Buy | Process anti-pattern |

## Process

```text
C6 ACCEPT @ v0.5.4 (clean tip)
  → decide what C7 must demonstrate
  → IC only
  → ★
  → implement → review → ACCEPT
```

Each version must state **what new capability exists** and **what remains impossible**.
