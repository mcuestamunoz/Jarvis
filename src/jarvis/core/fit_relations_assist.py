"""Fit relations checklist B1 (`B1-fit-relations-checklist`) — pure,
read-only "qué falta verificar" checklist of NAMED assembly relations
(child -> plate/arm/motors), reusing the existing screening + attestation
machinery instead of any new geometry math.

Next jump after Silhouette S1 (engineer_lock_silhouette_checklist_
semantics.md): "parece un dron" answers a shape question; this module
answers a CONCRETE one — for each in-scope relation, what's missing to
screen it, what already screens `overlap` (or, for `motors`↔`frame_arm`,
`station_reach_ok` — Disk-station radial reach B1, `B1-disk-station-
reach`; or, for `propellers`↔`motors`, `catalog_pair_ok` — Disk-station
catalog-pair B1, `B1-propellers-motors-catalog-pair`) and is ready for
the Engineer's own sign-off (box/reach families only — catalog pairing
has no attest path, IC lock #8), what's already attested, and what's
honestly `n/a` (reserved for any future mount-only pair with no evidence
class at all — none remain in `_MOUNT_ONLY_RELATIONS` today). Never calls
a writer: `screen_posed_envelope`/`format_screening` (pose_envelope_
screening.py) for the box family, `screen_station_reach`/`format_
station_reach` (station_reach_screening.py) for `motors`↔`frame_arm`,
`electrical_compatibility.prop_motor_pairing_outcome` (same authority
ERF's `prop_motor` check already uses) for `propellers`↔`motors`, and the
fingerprint-validity check for the reach family mirrors spatial_board.py's
own read-only re-verification of `declared_fit_attestation`; the plate
pick reuses `craft_montage_stack_assist._plate_box_origin`/
`_is_estimated_temporary_box`; the "still needs a mount" warn row reuses
`mount_standard_assist.build_mount_standard_checklist`'s own,
already-correct plate/frame/ambiguous target resolution rather than a
second copy of it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.craft_montage_stack_assist import (
    _is_estimated_temporary_box,
    _plate_box_origin,
    _STACK_SUBJECTS as _PLATE_RELATION_CHILDREN,
    _SUBJECT_NOUNS as _PLATE_RELATION_NOUNS,
)
from jarvis.core.mount_standard_assist import build_mount_standard_checklist
from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.core.pose_envelope_screening import format_screening, screen_posed_envelope
from jarvis.domains.aerial import is_frame_plate_key

# Locked trigger phrases (IC §0 lock #3): "relaciones", "fit", "qué falta
# verificar", "verificaciones de encaje". Accent/case-insensitive via
# _normalize_help, same as every other IDLE phrase gate in this codebase.
# Deliberately narrow so it never steals "parece un dron"/"silueta"/
# "montajes estándar"/"layout pack" (none of those substrings match here).
_TRIGGER_RE = re.compile(
    r"\brelaciones\b|\bfit\b|que\s+falta\s+verificar|verificaciones\s+de\s+encaje"
)


def is_fit_relations_assist_trigger(user_input: str) -> bool:
    """True when *user_input* asks the "qué falta verificar" question."""
    return bool(_TRIGGER_RE.search(_normalize_help(user_input)))


# Locked relation set (IC §0 lock #5, fixed order): the four stack
# subjects onto the single unambiguous boxed `frame_plate*` (screening
# applies), then the two disk-only mount edges — `motors`↔`frame_arm` gets
# a real (non-AABB) station-reach screening (Disk-station radial reach B1,
# `B1-disk-station-reach`); `propellers`↔`motors` gets a real catalog-pair
# screening (Disk-station catalog-pair B1, `B1-propellers-motors-catalog-
# pair` — reuses the same `match_motor_propeller` authority ERF's
# `prop_motor` check already uses; no axial/shaft evidence class exists,
# see investigation_report_disk_station_fit_attest_b0.md §C, so this is
# deliberately pairing-only, never a reach/clearance claim). Reusing
# `craft_montage_stack_assist`'s own child order/nouns for the plate
# family, never a second table.
_MOUNT_ONLY_RELATIONS: tuple[tuple[str, str], ...] = (
    ("motors", "frame_arm"),
    ("propellers", "motors"),
)


@dataclass(frozen=True)
class FitRelationRow:
    """One checklist row. ``status`` is one of: ``missing_origin`` /
    ``no_box_child`` / ``no_box_origin`` / ``ambiguous_plate`` /
    ``estimated_dims`` / ``no_pose`` / ``screen_pose_incomplete`` /
    ``screen_no_overlap`` / ``screen_overlap`` / ``attested`` /
    ``n_a_disk`` (reserved — no live pair uses it today) /
    ``station_reach_ok`` / ``station_reach_over`` /
    ``station_reach_insufficient`` / ``station_reach_estimated`` (these
    four, `B1-disk-station-reach`, apply ONLY to `motors`↔`frame_arm`) /
    ``catalog_pair_ok`` / ``catalog_pair_mismatch`` /
    ``catalog_pair_unverifiable`` (these three, `B1-propellers-motors-
    catalog-pair`, apply ONLY to `propellers`↔`motors` — informational,
    never `attested`, no human sign-off exists for this evidence class).
    ``mount_warning`` is an INDEPENDENT annotation (IC §0 lock #7's own
    "optional warn row... does not block screening") — it can be present
    alongside any status, since a relation can screen fine while still
    lacking a declared `mounted_on`."""

    child: str
    origin_key: str | None
    status: str
    reason: str
    suggest: str | None = None
    mount_warning: str | None = None
    candidates: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FitRelationsAssessment:
    rows: tuple[FitRelationRow, ...] = field(default_factory=tuple)
    ready_count: int = 0
    attested_count: int = 0
    blocked_count: int = 0
    na_count: int = 0


_ATTEST_PHRASE_TEMPLATE = "declaro {word} {noun}"


def _attest_phrase(noun: str) -> str:
    word = "verificada" if noun.startswith("la ") else "verificado"
    return _ATTEST_PHRASE_TEMPLATE.format(word=word, noun=noun)


def _mount_warning(mount_suggestions_by_subject: dict[str, Any], child: str) -> str | None:
    suggestion = mount_suggestions_by_subject.get(child)
    if suggestion is None or suggestion.kind != "suggested":
        return None
    return f"sin montaje declarado — escribe \"{suggestion.example_phrase}\""


def _attestation_is_valid(spec: Any, origin_spec: Any, components: dict[str, Any]) -> bool:
    """Re-derives the fingerprint the same way `spatial_board.py`'s own
    projector does (never trusts a stored seal without recomputing) —
    mirrors that read-only re-verification rather than a shared helper
    that doesn't exist yet, same discipline as that module's own inline
    check."""
    from jarvis.core.component_writers import compute_fit_attestation_fingerprint
    from jarvis.workspace.spatial_board import _geometry_from_spec

    attestation = getattr(spec, "declared_fit_attestation", None)
    if attestation is None:
        return False
    pose = spec.declared_box_pose
    child_geometry = _geometry_from_spec(spec)
    origin_geometry = _geometry_from_spec(origin_spec)
    if child_geometry is None or origin_geometry is None:
        return False
    current_fingerprint = compute_fit_attestation_fingerprint(pose, child_geometry, origin_geometry)
    return current_fingerprint == attestation.fingerprint


def _plate_relation_row(
    child: str, components: dict[str, Any], mount_suggestions_by_subject: dict[str, Any]
) -> FitRelationRow:
    from jarvis.workspace.spatial_board import _geometry_from_spec

    noun = _PLATE_RELATION_NOUNS[child]
    child_spec = components[child]
    mount_warning = _mount_warning(mount_suggestions_by_subject, child)

    plate_key = _plate_box_origin(components)
    if isinstance(plate_key, tuple):
        return FitRelationRow(
            child=child, origin_key=None, status="ambiguous_plate",
            reason="varias placas tienen caja declarada — no elijo cuál es la principal",
            candidates=plate_key, mount_warning=mount_warning,
        )
    if plate_key is None:
        any_plate_declared = any(is_frame_plate_key(k) for k in components)
        if any_plate_declared:
            return FitRelationRow(
                child=child, origin_key=None, status="no_box_origin",
                reason="la placa no tiene caja L×W×H declarada todavía",
                suggest="declara frame_plate estimada L x W mm (o una medida real)",
                mount_warning=mount_warning,
            )
        return FitRelationRow(
            child=child, origin_key=None, status="missing_origin",
            reason="no hay ninguna placa (frame_plate) declarada todavía",
            mount_warning=mount_warning,
        )

    plate_spec = components[plate_key]
    child_geometry = _geometry_from_spec(child_spec)
    if child_geometry is None or child_geometry.get("shape") != "box":
        suggest = (
            f"declara {noun} L x W x H mm" if child in ("battery", "sensors") else None
        )
        reason = "sin caja L×W×H declarada todavía"
        if suggest is None:
            reason += " (normalmente llega por catálogo/SKU, no por declare manual)"
        return FitRelationRow(
            child=child, origin_key=plate_key, status="no_box_child",
            reason=reason, suggest=suggest, mount_warning=mount_warning,
        )

    if _is_estimated_temporary_box(plate_spec):
        return FitRelationRow(
            child=child, origin_key=plate_key, status="estimated_dims",
            reason=f"{plate_key}: geometría ESTIMATED_TEMPORARY — bloqueado para declarar verificado",
            suggest="declara frame_plate L x W x H mm (medida real)",
            mount_warning=mount_warning,
        )
    if _is_estimated_temporary_box(child_spec):
        suggest = f"declara {noun} L x W x H mm (medida real)" if child in ("battery", "sensors") else None
        return FitRelationRow(
            child=child, origin_key=plate_key, status="estimated_dims",
            reason=f"{child}: geometría ESTIMATED_TEMPORARY — bloqueado para declarar verificado",
            suggest=suggest, mount_warning=mount_warning,
        )

    if getattr(child_spec, "declared_box_pose", None) is None:
        return FitRelationRow(
            child=child, origin_key=plate_key, status="no_pose",
            reason=f"{child}: sin pose declarada respecto a {plate_key}",
            suggest="apilar en placa (o layout pack, o Situar en el Board)",
            mount_warning=mount_warning,
        )

    if _attestation_is_valid(child_spec, plate_spec, components):
        return FitRelationRow(
            child=child, origin_key=plate_key, status="attested",
            reason="verificado por el Engineer — no es una comprobación geométrica de Jarvis",
            mount_warning=mount_warning,
        )

    screening = screen_posed_envelope(child_spec, components)
    if screening.status == "overlap":
        return FitRelationRow(
            child=child, origin_key=plate_key, status="screen_overlap",
            reason=format_screening(screening),
            suggest=_attest_phrase(noun), mount_warning=mount_warning,
        )
    status = "screen_pose_incomplete" if screening.status == "pose_incomplete" else "screen_no_overlap"
    return FitRelationRow(
        child=child, origin_key=plate_key, status=status,
        reason=format_screening(screening),
        suggest="reposiciona en Situar (Board) o corrige la pose declarada",
        mount_warning=mount_warning,
    )


def _motor_reach_attestation_is_valid(
    motor_spec: Any, frame_spec: Any, arm_spec: Any
) -> bool:
    """Disk-station radial reach B1 — re-derives the station-reach
    fingerprint the same way `_attestation_is_valid` re-derives the box
    fingerprint (never trusts a stored seal without recomputing)."""
    from jarvis.core.component_writers import compute_station_reach_fingerprint

    attestation = getattr(motor_spec, "declared_fit_attestation", None)
    if attestation is None:
        return False
    current_fingerprint = compute_station_reach_fingerprint(frame_spec, arm_spec, motor_spec)
    return current_fingerprint == attestation.fingerprint


def _motors_frame_arm_reach_row(
    child: str, origin: str, components: dict[str, Any], mount_warning: str | None
) -> FitRelationRow:
    """Disk-station radial reach B1 (`B1-disk-station-reach`) — real,
    non-AABB screening for `motors` -> `frame_arm` only. See
    `_propellers_motors_catalog_pair_row` for the sibling
    `propellers` -> `motors` evidence class (catalog pairing, not reach —
    B1-propellers-motors-catalog-pair, no axial facts exist to reuse this
    same L-vs-R math there)."""
    from jarvis.core.station_reach_screening import format_station_reach, screen_station_reach

    motor_spec = components[child]
    screening = screen_station_reach(motor_spec, origin, components)

    if screening.status == "station_reach_ok":
        frame_spec = components.get("frame")
        arm_spec = components[origin]
        if frame_spec is not None and _motor_reach_attestation_is_valid(motor_spec, frame_spec, arm_spec):
            return FitRelationRow(
                child=child, origin_key=origin, status="attested",
                reason="verificado por el Engineer — no es una comprobación geométrica de Jarvis",
                mount_warning=mount_warning,
            )
        return FitRelationRow(
            child=child, origin_key=origin, status="station_reach_ok",
            reason=format_station_reach(screening),
            suggest=_attest_phrase("el motor"), mount_warning=mount_warning,
        )

    return FitRelationRow(
        child=child, origin_key=origin, status=screening.status,
        reason=format_station_reach(screening), mount_warning=mount_warning,
    )


_CATALOG_PAIR_STATUS_MAP: dict[str, str] = {
    "compatible": "catalog_pair_ok",
    "mismatch": "catalog_pair_mismatch",
    "unverifiable": "catalog_pair_unverifiable",
}


def _format_catalog_pair(status: str) -> str:
    """Locked Spanish copy (IC lock #6) — "emparejamiento de catálogo".
    Deliberately avoids the literal forbidden tokens (never a synonym
    dodge via reordering): "cabe", "alcance", "hub", "eje", "clearance",
    "combo exacto de empuje", "VERIFIED" físico — including inside a
    disclaimer clause, where a first draft of this copy accidentally used
    "hub"/"eje" while explicitly saying they're NOT verified. Caught by
    this Buy's own test T6 and rephrased below without those words at
    all, not merely reworded around them."""
    if status == "catalog_pair_ok":
        return (
            "Motor y hélice tienen emparejamiento de catálogo compatible "
            "(ids o pulgadas compatibles) — no confirma dimensiones "
            "mecánicas ni el rendimiento real de ese combo."
        )
    if status == "catalog_pair_mismatch":
        return (
            "Motor y hélice están en catálogo pero el emparejamiento no es "
            "compatible (ni ids ni pulgadas coinciden) — no confirma "
            "dimensiones mecánicas."
        )
    return (
        "Jarvis no verifica emparejamiento de catálogo; falta SKU/familia "
        "de motor y/o hélice, o no están en catálogo."
    )


def _propellers_motors_catalog_pair_row(
    child: str, origin: str, components: dict[str, Any], mount_warning: str | None
) -> FitRelationRow:
    """Disk-station catalog-pair B1 (`B1-propellers-motors-catalog-pair`)
    — replaces the unconditional `n_a_disk` for `propellers` -> `motors`
    with the SAME catalog-pairing authority ERF's `prop_motor` check
    already uses (`electrical_compatibility.prop_motor_pairing_outcome`),
    never a second copy. Mount (`mounted_on`) and pairing are independent
    signals (IC lock #4): this row's status never depends on whether
    `propellers.mounted_on == "motors"` is declared — `mount_warning`
    stays its own, separately-computed annotation, exactly as for every
    other row in this checklist. No human attest exists for this evidence
    class (IC lock #8) — `catalog_pair_ok` is informational only, never
    `attested`, never offers a `suggest` phrase."""
    from jarvis.core.electrical_compatibility import prop_motor_pairing_outcome

    outcome = prop_motor_pairing_outcome(components)
    status = _CATALOG_PAIR_STATUS_MAP[outcome]
    return FitRelationRow(
        child=child, origin_key=origin, status=status,
        reason=_format_catalog_pair(status), mount_warning=mount_warning,
    )


def _mount_only_relation_row(
    child: str, origin: str, components: dict[str, Any], mount_suggestions_by_subject: dict[str, Any]
) -> FitRelationRow | None:
    if origin not in components:
        return FitRelationRow(
            child=child, origin_key=None, status="missing_origin",
            reason=f"'{origin}' no declarado todavía",
        )
    mount_warning = _mount_warning(mount_suggestions_by_subject, child)
    if child == "motors" and origin == "frame_arm":
        return _motors_frame_arm_reach_row(child, origin, components, mount_warning)
    if child == "propellers" and origin == "motors":
        return _propellers_motors_catalog_pair_row(child, origin, components, mount_warning)
    return FitRelationRow(
        child=child, origin_key=origin, status="n_a_disk",
        reason=(
            "sin screening de caja hoy (disco) — el montaje sí se puede "
            "declarar; verificación de disco es un Buy aparte"
        ),
        mount_warning=mount_warning,
    )


def assess_fit_relations(components: dict[str, Any]) -> FitRelationsAssessment:
    """Pure, read-only assessment — mutates nothing, calls no writer.

    Fixed relation order (IC §0 lock #5): flight_controller/esc/battery/
    sensors -> the single unambiguous boxed `frame_plate*`, then
    motors -> frame_arm (Disk-station radial reach B1 — real
    `station_reach_*` screening, `B1-disk-station-reach`) and
    propellers -> motors (Disk-station catalog-pair B1 — real
    `catalog_pair_*` screening, `B1-propellers-motors-catalog-pair`,
    informational only — no attest path). A subject absent from the
    project is skipped entirely (never demanded) — same "missing_child"
    honesty every sibling assist in this family already uses.
    """
    mount_suggestions_by_subject = {s.subject: s for s in build_mount_standard_checklist(components)}

    rows: list[FitRelationRow] = []
    for child in _PLATE_RELATION_CHILDREN:
        if child not in components:
            continue
        rows.append(_plate_relation_row(child, components, mount_suggestions_by_subject))

    for child, origin in _MOUNT_ONLY_RELATIONS:
        if child not in components:
            continue
        row = _mount_only_relation_row(child, origin, components, mount_suggestions_by_subject)
        if row is not None:
            rows.append(row)

    ready = sum(1 for r in rows if r.status in ("screen_overlap", "station_reach_ok"))
    attested = sum(1 for r in rows if r.status == "attested")
    na = sum(1 for r in rows if r.status == "n_a_disk")
    blocked = len(rows) - ready - attested - na
    return FitRelationsAssessment(
        rows=tuple(rows), ready_count=ready, attested_count=attested,
        blocked_count=blocked, na_count=na,
    )


def format_fit_relations_checklist(assessment: FitRelationsAssessment) -> str:
    """Locked Spanish copy — checklist-scoped verdict + row detail. Never
    claims Requirements/ASSEMBLY READY, never renames screening ->
    VERIFIED. `station_reach_*` rows (motors/frame_arm) say "alcance de
    estación" — never AABB "cabe", never hub/blade clearance.
    `catalog_pair_*` rows (propellers/motors) say "emparejamiento de
    catálogo" — never cabe/alcance/hub/eje/clearance/"combo exacto de
    empuje"/VERIFIED físico."""
    if not assessment.rows:
        return (
            "Relaciones de encaje: ningún par en el alcance de este "
            "checklist está declarado todavía — nada que listar."
        )

    lines = [
        f"Relaciones de encaje: {assessment.ready_count} listas para declarar "
        f"verificado · {assessment.attested_count} ya declaradas · "
        f"{assessment.blocked_count} bloqueadas · {assessment.na_count} n/a "
        "(esto no es ASSEMBLY READY ni el estado del proyecto)."
    ]
    for row in assessment.rows:
        if row.status == "attested":
            marker = "✓"
        elif row.status in ("screen_overlap", "station_reach_ok"):
            marker = "→"
        elif row.status == "n_a_disk":
            marker = "·"
        elif row.status == "ambiguous_plate":
            marker = "?"
        elif row.status == "catalog_pair_ok":
            # Informational match, never attestable (IC lock #8) — never
            # the same "ready to declare verified" arrow as screen_overlap
            # / station_reach_ok.
            marker = "≈"
        else:
            marker = "✗"
        target = row.origin_key or "(placa)"
        line = f"  {marker} {row.child} → {target}: {row.reason}"
        if row.status == "ambiguous_plate":
            line += f" ({', '.join(row.candidates)})"
        if row.suggest:
            line += f" — escribe \"{row.suggest}\""
        lines.append(line)
        if row.mount_warning:
            lines.append(f"      aviso: {row.mount_warning}")

    lines.append("Escribe la frase que quieras confirmar — nada se declara solo.")
    return "\n".join(lines)
