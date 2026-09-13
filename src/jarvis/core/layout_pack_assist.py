"""Cited kit layout pack B1 (`B1-layout-pack-cited`) — named, disclosed
pose+mount packs for a specific kit frame SKU, built from a filled §0.1
citation bag.

Reuses `craft_montage_stack_assist.flush_centered_z_mm` (the exact same
Path F arithmetic — never a second formula) and the existing, unmodified
pose-declare and mount-declare grammars/writers — this module only
curates WHICH subjects belong to a named pack and whether each also gets
a mount phrase. It computes z FRESH from CURRENT envelopes at propose
time, never the citation bag's own frozen worked-example numbers (a live
project's child heights can legitimately differ from the bag's — this
module always trusts the live boxes, never a stale table value).

Never writes anything itself. The orchestrator's IDLE bridge is what
calls the existing pose/mount writers once the user retypes a proposal.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jarvis.core.craft_montage_stack_assist import flush_centered_z_mm
from jarvis.core.motor_catalog_assist import _normalize_help

# ── §0.1 registry — every row traces to a filled citation bag ───────────
#
# hglrc_my5_flush_stack_b1: Engineer-confirmed Path F flush (supuesto) on
# an estimated_temporary frame_plate — smoked 2026-09-13 on
# 10-min-autonomía. NOT an OEM drawing, NOT a caliper XY measurement,
# NOT "verified CAD" — z is recomputed live from the same formula
# B1-craft-montage-path-f already uses; the bag's own worked-example
# numbers (FC 4.9 / ESC 5.0 / battery 15.5 / sensors 8.2, from that
# project's live child heights 7.8/8.0/29.0/14.4 over a 2mm-thick
# estimated plate) are the regression-fixture expectation, not a value
# ever read back out of this registry.
_PACKS: dict[str, dict[str, Any]] = {
    "hglrc_my5_flush_stack_b1": {
        "kit_frame_sku": "hglrc_my5_5in",
        "authority": (
            "Engineer-confirmed Path F flush (supuesto) on estimated_temporary "
            "plate — smoke 2026-09-13, proyecto 10-min-autonomía"
        ),
        "requires_plate_box": True,
        "origin_key": "frame_plate",
        # subject | Spanish noun (with article) | participle for "montado en"
        "rows": (
            ("flight_controller", "la controladora", "montada"),
            ("esc", "el esc", "montado"),
            ("battery", "la batería", "montada"),
            ("sensors", "el sensor", "montado"),
        ),
    },
}

# Subjects explicitly, permanently excluded from every pack this Buy
# defines (lock #3/#8 — never invented into a pack row):
#   motors, propellers   — Visor X from wheelbase, not a Continuity disk pose
#   frame_arm            — Visor X station boxes; radial-beam-to-plate is a
#                           separate, un-★'d Buy
#   frame_plate_2/3       — no cited/estimated L×W yet
#   power_connector, signal_harness, prop_adapter — no box geometry today


@dataclass(frozen=True)
class LayoutPackRow:
    """One pack checklist row. ``kind == "proposed"`` carries whichever of
    ``example_pose_phrase``/``example_mount_phrase`` still needs
    confirming (either may be `None` if that half is already declared).
    ``kind == "skipped"`` names a declared-but-boxless subject.
    ``kind == "done"`` names a subject that already has BOTH a pose and a
    mount — nothing left for this pack to add. Distinguishing "done" from
    a bare empty list matters: `propose_layout_pack` returning `[]` means
    the plate-box PREREQUISITE itself was unmet (honest "nothing to
    propose at all"), never "everything already succeeded" — that second,
    much happier case still returns one "done" row per subject so the
    two are never confused in the rendered copy."""

    subject: str
    kind: str  # "proposed" | "skipped" | "done"
    origin_key: str | None = None
    z_mm: float | None = None
    example_pose_phrase: str | None = None
    example_mount_phrase: str | None = None
    reason: str = ""


_BARE_TRIGGER_RE = re.compile(r"\blayout\s+pack\b")
_NAMED_TRIGGER_RE = re.compile(r"aplicar\s+layout\s+([a-z0-9_]+)")


def list_pack_ids() -> tuple[str, ...]:
    return tuple(sorted(_PACKS))


def resolve_layout_pack_trigger(user_input: str) -> str | None:
    """Returns a pack_id to propose, or `None` when the phrase isn't a
    layout-pack trigger at all.

    "aplicar layout <pack_id>" names a specific pack explicitly. Bare
    "layout pack" resolves to the only registered pack when exactly one
    exists (today); with 2+ packs registered in the future, bare would
    need its own listing branch — not needed yet, so not built speculatively.
    """
    normalized = _normalize_help(user_input)
    named = _NAMED_TRIGGER_RE.search(normalized)
    if named:
        candidate = named.group(1)
        return candidate if candidate in _PACKS else None
    if _BARE_TRIGGER_RE.search(normalized):
        packs = list_pack_ids()
        return packs[0] if len(packs) == 1 else None
    return None


def propose_layout_pack(pack_id: str, components: dict[str, Any]) -> list[LayoutPackRow]:
    """Pure, read-only proposals for a registered pack against the CURRENT
    components — `[]` for an unknown pack_id or an honestly-unmet
    prerequisite (e.g. `requires_plate_box` and the origin isn't boxed)."""
    from jarvis.workspace.spatial_board import _geometry_from_spec

    pack = _PACKS.get(pack_id)
    if pack is None:
        return []

    origin_key = pack["origin_key"]
    origin_spec = components.get(origin_key)
    origin_geometry = _geometry_from_spec(origin_spec) if origin_spec is not None else None
    if pack["requires_plate_box"] and (origin_geometry is None or origin_geometry.get("shape") != "box"):
        return []

    rows: list[LayoutPackRow] = []
    for subject, noun, participle in pack["rows"]:
        spec = components.get(subject)
        if spec is None:
            continue  # not declared at all — nothing to propose

        geometry = _geometry_from_spec(spec)
        if geometry is None or geometry.get("shape") != "box":
            rows.append(LayoutPackRow(
                subject=subject, kind="skipped",
                reason="sin caja L×W×H declarada todavía",
            ))
            continue

        already_posed = getattr(spec, "declared_box_pose", None) is not None
        already_mounted = getattr(spec, "mounted_on", None) is not None
        if already_posed and already_mounted:
            rows.append(LayoutPackRow(
                subject=subject, kind="done", origin_key=origin_key,
                reason="ya tiene pose y montaje declarados — nada que añadir",
            ))
            continue

        pose_phrase = None
        z_mm = None
        if not already_posed:
            z_mm = flush_centered_z_mm(origin_geometry, geometry)
            pose_phrase = (
                f"declara {noun} a 0 mm en x, 0 mm en y, {_fmt(z_mm)} mm en z "
                f"respecto a {origin_key}"
            )
        mount_phrase = None
        if not already_mounted:
            mount_phrase = f"{noun} {participle} en {origin_key}"

        rows.append(LayoutPackRow(
            subject=subject, kind="proposed", origin_key=origin_key, z_mm=z_mm,
            example_pose_phrase=pose_phrase, example_mount_phrase=mount_phrase,
            reason=f"pack {pack_id} — flush Path F (supuesto); {pack['authority']}",
        ))

    return rows


def _fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(round(value, 4))


def format_layout_pack(pack_id: str, rows: list[LayoutPackRow]) -> str:
    """Locked Spanish copy — never claims measured kit CAD, never
    VERIFICADO/"cabe"/Product B; every proposal line names the pack's own
    disclosed authority verbatim."""
    if pack_id not in _PACKS:
        available = ", ".join(list_pack_ids()) or "ninguno todavía"
        return f"No conozco el pack '{pack_id}'. Packs disponibles: {available}."

    if not rows:
        # An entirely empty list only ever means the plate-box PREREQUISITE
        # itself was unmet (requires_plate_box) — "everything already
        # done" is represented by "done" rows below, never a bare [].
        return (
            f"Layout pack '{pack_id}': falta la caja de la placa de origen "
            "(cita o estimada) — nada que proponer todavía."
        )

    lines = [f"Layout pack '{pack_id}' — supuesto flush Path F, no CAD medido del kit:"]
    idx = 1
    for row in rows:
        if row.kind == "skipped":
            lines.append(f"  · {row.subject}: {row.reason}")
            continue
        if row.kind == "done":
            lines.append(f"  ✓ {row.subject} → {row.origin_key}: {row.reason}")
            continue
        lines.append(f"  {idx}. {row.subject} → {row.origin_key}")
        if row.example_pose_phrase:
            lines.append(f"     pose: escribe \"{row.example_pose_phrase}\"")
        if row.example_mount_phrase:
            lines.append(f"     montaje: escribe \"{row.example_mount_phrase}\"")
        lines.append(f"     ({row.reason})")
        idx += 1
    if idx == 1:
        lines.append("  (nada pendiente — todo lo que tiene caja ya está posado y montado, o falta caja.)")
    else:
        lines.append("Escribe la frase que quieras confirmar — nada se declara solo.")
    return "\n".join(lines)
