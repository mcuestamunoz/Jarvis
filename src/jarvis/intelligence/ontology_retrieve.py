"""Read-only retrieve over the `ontology/` vault — `B1-ontology-retrieve-r2`.

Looks up a single `solid` note by its frontmatter `id` (or, via the
optional helper, by exact `nombre`) and returns a small, structured
`OntologyCite`: identity/path/state metadata, `never_invents` (surfaced
so callers cannot silently invent a craft number the note itself
refuses to supply), and the extracted `[DEFINICION]`/`[INTUICION]`
sections.

This is exact lookup only — no fuzzy matching, no embeddings, no LLM
ranking, no relevance scoring. A miss returns `None`, never a
best-effort guess. Every read is `Path.read_text` — this module never
opens a file for writing and never touches `library/`, the craft
workspace, or `jarvis.core` (Continuity/orchestrator) state.

Frontmatter is parsed with a small line-based reader tailored to this
repo's own R1 Plantilla shape (`key: value` scalars and `key: [a, b]`
flow lists) rather than a general YAML parser — the vault's frontmatter
is a fixed, simple grammar and this avoids adding a new dependency for
a one-shape read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ONTOLOGY_ROOT = REPO_ROOT / "ontology"

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_SECTION_NAME_RE = re.compile(r"[A-Z_]+")


@dataclass(frozen=True)
class OntologyCite:
    id: str
    nombre: str
    path: str
    estado: str
    jarvis_relevance: list[str]
    never_invents: list[str]
    formula_citation: str | None
    definicion: str
    intuicion: str


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def _parse_flow_list(raw: str) -> list[str]:
    raw = raw.strip()
    if not (raw.startswith("[") and raw.endswith("]")):
        return []
    inner = raw[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",")]


def _extract_section(text: str, section_name: str) -> str:
    if not _SECTION_NAME_RE.fullmatch(section_name):
        raise ValueError(f"invalid section name: {section_name!r}")
    pattern = re.compile(
        rf"^##\s*\[{section_name}\][^\n]*\n(.*?)(?=^##\s*\[[A-Z_]+\]|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    body = match.group(1)
    body = re.sub(r"\n-{3,}\s*\Z", "", body)
    return body.strip()


def _repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _build_cite(fields: dict[str, str], text: str, path: Path) -> OntologyCite:
    return OntologyCite(
        id=fields.get("id", ""),
        nombre=fields.get("nombre", ""),
        path=_repo_relative(path),
        estado=fields.get("estado", ""),
        jarvis_relevance=_parse_flow_list(fields.get("jarvis_relevance", "")),
        never_invents=_parse_flow_list(fields.get("never_invents", "")),
        formula_citation=fields.get("formula_citation") or None,
        definicion=_extract_section(text, "DEFINICION"),
        intuicion=_extract_section(text, "INTUICION"),
    )


def _iter_notes(ontology_root: Path):
    for md_path in sorted(ontology_root.rglob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fields = _parse_frontmatter(text)
        if fields:
            yield md_path, text, fields


def retrieve_by_id(
    note_id: str, *, ontology_root: Path | None = None
) -> OntologyCite | None:
    """Return the cite for a `solid` note whose frontmatter `id` matches
    exactly, else `None`. A note that exists but is not `solid` is
    treated the same as a miss — no explicit-not-found distinction is
    made from draft/stub, per IC §0 row 5 (default scope filter)."""
    root = ontology_root or DEFAULT_ONTOLOGY_ROOT
    for path, text, fields in _iter_notes(root):
        if fields.get("id") == note_id and fields.get("estado") == "solid":
            return _build_cite(fields, text, path)
    return None


def retrieve_by_nombre(
    nombre: str, *, ontology_root: Path | None = None
) -> OntologyCite | None:
    """Same as `retrieve_by_id`, matched on exact `nombre` (casefolded).
    No fuzzy/partial matching."""
    root = ontology_root or DEFAULT_ONTOLOGY_ROOT
    target = nombre.strip().casefold()
    for path, text, fields in _iter_notes(root):
        if (
            fields.get("nombre", "").strip().casefold() == target
            and fields.get("estado") == "solid"
        ):
            return _build_cite(fields, text, path)
    return None


def list_solid_ids(*, ontology_root: Path | None = None) -> list[str]:
    """Return every `solid` note's frontmatter `id`, sorted. A read-only
    vault scan (`B1-explain-maps-expand`, for `jarvis explain --list`) —
    no write, no embeddings, no ranking, just the same `_iter_notes`
    walk the lookups above already use."""
    root = ontology_root or DEFAULT_ONTOLOGY_ROOT
    return sorted(
        fields["id"]
        for _, _, fields in _iter_notes(root)
        if fields.get("estado") == "solid" and fields.get("id")
    )
