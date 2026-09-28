"""Finite alias seed table for `jarvis explain` — `B1-assistant-terminal-canal`,
expanded by `B1-explain-maps-expand`.

A frozen `dict[str, str]`, not a search index: keys are exact,
casefolded alias strings; values are the target note's frontmatter
`id`. Every target below was verified `estado: solid` in `ontology/`
before being seeded (IC §1.1 / expand-Buy §1 — an alias pointing at a
non-solid or missing note must never be shipped). Expanding this table
further is a later docs/IC edit, not fuzzy matching added here.

`B1-explain-maps-expand` extended the original four A3 seeds
(`c-rate`/`crate`/`op`/`operating point`) with one short alias per
remaining solid spine note (verified against the full vault scan at
seed time — see the implementation report), covering every solid id:
`vectores`, `corriente-y-circuitos`, `magnetismo`, `dinamica`,
`momento-y-rotacion`, `control-clasico`, `c-rate-de-bateria`,
`forma-medicion-banco-empuje`, `punto-de-operacion-vs-capacidad-intrinseca`,
`actuadores`, `motor-dc`, `motores`, `control-robotico`,
`navegacion-y-planificacion`, `acelerometro`, `giroscopio`, `imu`,
`sensores-de-movimiento`.
"""

from __future__ import annotations

EXPLAIN_ALIASES: dict[str, str] = {
    # A3 seed (kept unchanged).
    "c-rate": "c-rate-de-bateria",
    "crate": "c-rate-de-bateria",
    "op": "punto-de-operacion-vs-capacidad-intrinseca",
    "operating point": "punto-de-operacion-vs-capacidad-intrinseca",
    # Expand-Buy seed — one short key per remaining solid spine id.
    "imu": "imu",
    "gyro": "giroscopio",
    "giroscopio": "giroscopio",
    "accel": "acelerometro",
    "acelerometro": "acelerometro",
    "motor-dc": "motor-dc",
    "motor dc": "motor-dc",
    "motores": "motores",
    "actuadores": "actuadores",
    "dinamica": "dinamica",
    "dynamics": "dinamica",
    "vectores": "vectores",
    "vectors": "vectores",
    "magnetismo": "magnetismo",
    "mag": "magnetismo",
    "corriente": "corriente-y-circuitos",
    "banco": "forma-medicion-banco-empuje",
    "thrust stand": "forma-medicion-banco-empuje",
    "control clasico": "control-clasico",
    "pid": "control-clasico",
    "control robotico": "control-robotico",
    "navegacion": "navegacion-y-planificacion",
    "nav": "navegacion-y-planificacion",
    "momento": "momento-y-rotacion",
    "sensores movimiento": "sensores-de-movimiento",
}
