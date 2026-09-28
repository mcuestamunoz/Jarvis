"""Static product-key -> ontology id maps — `B1-explain-maps-expand`.

`FS_EXPLAIN_MAP` bridges a small, hand-picked set of flight_software rung
labels to ontology ids; `HD_EXPLAIN_MAP` does the same for two Hardware
Debt keys. Both mirror `docs/ONTOLOGY_CROSSWALKS.md` §1/§2 verbatim for
the seeded keys only — this Buy does not encode every crosswalk row,
and every id listed below was independently confirmed `estado: solid`
in `ontology/` before being seeded here.

These are **static dicts**, not a rung/HD registry read from anywhere
else: this module never imports `jarvis.flight_software` and never
discovers rungs dynamically. A rung/HD key here is documentation
shorthand for bridging to ontology ids — never a `jarvis.core`
parameter id or a `flight_software` identifier by itself.
"""

from __future__ import annotations

FS_EXPLAIN_MAP: dict[str, list[str]] = {
    "C3": ["sensores-de-movimiento", "imu"],
    "C7": ["imu", "giroscopio", "acelerometro", "control-robotico", "vectores"],
    "C10": ["actuadores", "motores", "motor-dc"],
    "C39": ["navegacion-y-planificacion", "control-robotico"],
    "C42": ["imu", "sensores-de-movimiento"],
}

HD_EXPLAIN_MAP: dict[str, list[str]] = {
    "HD-001": [
        "c-rate-de-bateria",
        "corriente-y-circuitos",
        "punto-de-operacion-vs-capacidad-intrinseca",
    ],
    "HD-005": [
        "forma-medicion-banco-empuje",
        "punto-de-operacion-vs-capacidad-intrinseca",
        "motor-dc",
    ],
}


def ids_for_rung(key: str) -> list[str] | None:
    """Case-normalized lookup across both maps (`C7`/`c7`, `HD-001`/
    `hd-001` all resolve the same). Returns a *copy* of the id list so
    callers can't mutate the static table; `None` on a miss — never an
    empty list standing in for "not found"."""
    normalized = key.strip().upper()
    if normalized in FS_EXPLAIN_MAP:
        return list(FS_EXPLAIN_MAP[normalized])
    if normalized in HD_EXPLAIN_MAP:
        return list(HD_EXPLAIN_MAP[normalized])
    return None
