"""`jarvis explain <query>` — first human-facing Assistant surface.

`B1-assistant-terminal-canal`, extended by `B1-explain-maps-expand` with
`--list` (solid ids + known aliases) and `--rung KEY` (FS rung / HD key
-> mapped ontology ids, via the static `explain_maps` tables). A
deterministic, command-first canal over A2 retrieve
(`ontology_retrieve.retrieve_by_id`/`retrieve_by_nombre`/
`list_solid_ids`): resolve a query to one `solid` note, then print its
`[DEFINICION]`/`[INTUICION]`/path/`never_invents` cite. Not chat, not
RAG, not an LLM call, not a Continuity/orchestrator command — this
module never imports `jarvis.core` or any LLM client, and never
constructs `JarvisOrchestrator`.

Resolve order for the positional query path (IC §0 row 4, unchanged by
the expand Buy, deterministic, no fallthrough re-ordering):
  1. query as frontmatter `id` (exact)
  2. else exact `nombre` (casefold)
  3. else the finite `EXPLAIN_ALIASES` table (exact casefold key)
  4. else a miss — `None` / non-zero exit, never a fabricated cite

`--rung KEY` is a *separate* lookup (static `explain_maps.ids_for_rung`,
not the query resolve order above) and deliberately does not dump full
`[DEFINICION]` bodies by default — it prints the mapped ids (+ `nombre`
when retrievable), keeping the output scannable rather than noisy.
"""

from __future__ import annotations

import sys
from pathlib import Path

from jarvis.intelligence.explain_aliases import EXPLAIN_ALIASES
from jarvis.intelligence.explain_maps import ids_for_rung
from jarvis.intelligence.ontology_retrieve import (
    OntologyCite,
    list_solid_ids,
    retrieve_by_id,
    retrieve_by_nombre,
)


def resolve_explain_query(
    query: str, *, ontology_root: Path | None = None
) -> OntologyCite | None:
    """Resolve `query` to a `solid` note's cite, or `None` on a miss."""
    stripped = query.strip()
    if not stripped:
        return None

    cite = retrieve_by_id(stripped, ontology_root=ontology_root)
    if cite is not None:
        return cite

    cite = retrieve_by_nombre(stripped, ontology_root=ontology_root)
    if cite is not None:
        return cite

    alias_id = EXPLAIN_ALIASES.get(stripped.casefold())
    if alias_id is not None:
        return retrieve_by_id(alias_id, ontology_root=ontology_root)

    return None


def format_explain_cite(cite: OntologyCite) -> str:
    """Render a cite for terminal output: identity, path, DEFINICION,
    INTUICION, optional formula_citation, and a never_invents honesty
    line when that list is non-empty."""
    lines = [
        f"{cite.nombre}  (id: {cite.id})",
        f"Fuente: {cite.path}",
        "",
        "[DEFINICION]",
        cite.definicion or "(sin definición registrada en la nota)",
        "",
        "[INTUICION]",
        cite.intuicion or "(sin intuición registrada en la nota)",
    ]
    if cite.formula_citation:
        lines.append("")
        lines.append(f"Citas: {cite.formula_citation}")
    if cite.never_invents:
        lines.append("")
        lines.append(
            "Honestidad: esta explicación no inventa "
            + ", ".join(cite.never_invents)
            + " — esos valores deben venir de catálogo/Continuity, nunca de esta nota."
        )
    return "\n".join(lines)


def run_explain_cli(query: str, *, ontology_root: Path | None = None) -> int:
    """Resolve + format + print `query`. Returns a process exit code —
    0 on a solid-note hit, 1 on an honest miss. Never raises for an
    unresolved query."""
    cite = resolve_explain_query(query, ontology_root=ontology_root)
    if cite is None:
        print(
            f"No solid ontology note for: {query}"
            " (hint: use the note's id, its exact nombre, or a known alias"
            " such as 'c-rate')",
            file=sys.stderr,
        )
        return 1
    print(format_explain_cite(cite))
    return 0


def run_explain_list_cli(*, ontology_root: Path | None = None) -> int:
    """Print every solid note id, then every known alias -> id line.
    Read-only vault scan (`list_solid_ids`); always exits 0."""
    ids = list_solid_ids(ontology_root=ontology_root)
    print("Solid ontology ids:")
    for note_id in ids:
        print(f"  {note_id}")
    print()
    print("Known aliases:")
    for alias, target_id in sorted(EXPLAIN_ALIASES.items()):
        print(f"  {alias} -> {target_id}")
    return 0


def run_explain_rung_cli(key: str, *, ontology_root: Path | None = None) -> int:
    """Print the FS rung / HD key and its mapped ontology ids (+ nombre
    when retrievable). Does not print DEFINICION/INTUICION bodies — use
    the positional query path for that. Exit 0 on a known key, 1 on an
    unknown one (never a fabricated mapping)."""
    ids = ids_for_rung(key)
    if ids is None:
        print(f"Unknown rung/HD key: {key}", file=sys.stderr)
        return 1
    print(f"{key.strip().upper()} ->")
    for note_id in ids:
        cite = retrieve_by_id(note_id, ontology_root=ontology_root)
        if cite is not None:
            print(f"  {note_id}  ({cite.nombre})")
        else:
            print(f"  {note_id}  (not found / not solid)")
    return 0
