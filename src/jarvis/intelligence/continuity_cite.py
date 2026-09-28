"""Continuity topic → ontology cite bridge — `B1-continuity-explain-cite-r3`.

`CONTINUITY_TOPIC_MAP` is a small, hand-picked, finite dict: a Continuity
topic tag (e.g. `"c_rate"`) to a list of solid ontology `id`s. This is
the **only** place in `jarvis.intelligence` that knows about Continuity
topic vocabulary — `jarvis.core.project_continuity` itself never imports
this module and never reads `ontology/` (see that module's own
`_explain_topics_for_continuity`, which only emits the finite topic
tags; resolving them to cites happens here, one layer up, at the CLI
seam — same grain as `jarvis explain` itself importing `intelligence`).

`cites_for_topics` is exact-lookup only: an unknown topic is skipped
silently (never an invented note), and a topic whose mapped id is not
`estado: solid` today resolves to no cite for that id (A2's own
`retrieve_by_id` contract) rather than a crash or a stale/fabricated
cite.
"""

from __future__ import annotations

from pathlib import Path

from jarvis.intelligence.ontology_retrieve import OntologyCite, retrieve_by_id

CONTINUITY_TOPIC_MAP: dict[str, list[str]] = {
    "c_rate": ["c-rate-de-bateria"],
    "operating_point": ["punto-de-operacion-vs-capacidad-intrinseca"],
    "motor": ["motores", "motor-dc"],
    "current": ["corriente-y-circuitos"],
    "thrust_stand": ["forma-medicion-banco-empuje"],
}


def cites_for_topics(
    topics: list[str], *, ontology_root: Path | None = None
) -> list[OntologyCite]:
    """Resolve known topics to solid cites. Unknown topics are skipped
    silently; ids are de-duped (first occurrence wins) so the same note
    is never listed twice when two topics both map to it."""
    seen_ids: set[str] = set()
    cites: list[OntologyCite] = []
    for topic in topics:
        for note_id in CONTINUITY_TOPIC_MAP.get(topic, []):
            if note_id in seen_ids:
                continue
            cite = retrieve_by_id(note_id, ontology_root=ontology_root)
            if cite is None:
                continue
            seen_ids.add(note_id)
            cites.append(cite)
    return cites


def format_continuity_cite_lines(cites: list[OntologyCite]) -> list[str]:
    """Thin CLI formatter: one short line per cite, pointing at the full
    `jarvis explain <id>` command — never the note's own DEFINICION/
    INTUICION bodies (those stay in `jarvis explain` itself, not here)."""
    return [f"  - {cite.id}  →  jarvis explain {cite.id}" for cite in cites]
