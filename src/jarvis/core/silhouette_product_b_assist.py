"""Silhouette Product B assist B1 (`B1-silhouette-product-b`, Path S1) —
pure, read-only "¿parece un dron?" checklist + verdict over live
Continuity state.

Product A (racimo) vs Product B (silueta) is the Engineer's own locked
distinction (engineer_lock_geometry_3d_mapping_path.md): a plate with no
declared box is always racimo; a boxed plate with the stack posed AND
mounted is a silhouette, marked **B\\*** ("estimada") while any plate
dimension is `estimated_temporary`, and plain **B** once the plate is
`declared`/cited. This module answers that question only — it never
writes, never invents a millimetre, and never widens vocabulary already
owned by `mount_standard_assist.py` / `craft_montage_stack_assist.py` /
`layout_pack_assist.py`: every suggested phrase is exactly one those
sibling modules (or the existing pose/mount-declare bridges) already
accept.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.craft_montage_stack_assist import (
    _is_estimated_temporary_box,
    _plate_box_origin,
    _STACK_SUBJECTS,
)
from jarvis.core.motor_catalog_assist import _normalize_help

# Locked trigger phrases (IC §0 lock #3): "silueta", "parece un dron"
# (with or without the leading "¿"), "product b". Accent/case-insensitive
# via _normalize_help, same as every other IDLE phrase gate in this
# codebase. "¿" is stripped by the punctuation-agnostic \b word match, so
# no separate variant is needed for the interrogative form.
_TRIGGER_RE = re.compile(r"\bsilueta\b|parece\s+un\s+dron|\bproduct\s+b\b")


def is_silhouette_assist_trigger(user_input: str) -> bool:
    """True when *user_input* asks the "¿parece un dron?" question."""
    return bool(_TRIGGER_RE.search(_normalize_help(user_input)))


@dataclass(frozen=True)
class SilhouetteRow:
    """One checklist row. ``status`` is one of ``ok`` / ``missing`` /
    ``estimated`` / ``n/a``. ``suggest`` is an exact, already-parseable
    phrase from a sibling assist or writer bridge — never invented copy."""

    gate: str
    status: str  # "ok" | "missing" | "estimated" | "n/a"
    detail: str = ""
    suggest: str | None = None


@dataclass(frozen=True)
class SilhouetteAssessment:
    """Full checklist + verdict. ``verdict`` is one of ``racimo`` /
    ``silueta_estimada`` / ``silueta`` — never any other string (IC §0
    lock #5's own closed enum)."""

    verdict: str
    rows: tuple[SilhouetteRow, ...] = field(default_factory=tuple)


def _plate_authority_estimated(components: dict[str, Any], plate_key: str) -> bool:
    return _is_estimated_temporary_box(components[plate_key])


def _stack_present_subjects(components: dict[str, Any]) -> tuple[str, ...]:
    """Stack subjects that both exist in the project AND have their own
    declared box — subjects absent or still boxless are simply not part
    of the pose/mount gates (a project that never declared a sensor is
    never asked to pose one)."""
    from jarvis.workspace.spatial_board import _geometry_from_spec

    present = []
    for subject in _STACK_SUBJECTS:
        spec = components.get(subject)
        if spec is None:
            continue
        geometry = _geometry_from_spec(spec)
        if geometry is not None and geometry.get("shape") == "box":
            present.append(subject)
    return tuple(present)


def assess_silhouette(components: dict[str, Any]) -> SilhouetteAssessment:
    """Pure, read-only assessment — mutates nothing, calls no writer.

    Verdict logic (IC §0 lock #2 / §1.1):
      - no boxed plate                              -> racimo
      - boxed plate but stack/mounts incomplete for
        present boxed subjects                      -> racimo (not yet)
      - boxed plate, stack+mounts OK, plate estimated -> silueta estimada (B*)
      - boxed plate, stack+mounts OK, plate declared  -> silueta (B)
    Visor X/wheelbase and pose-cycle rows are warn-only — never demote a
    verdict that plate+stack+mounts already earned.
    """
    rows: list[SilhouetteRow] = []

    plate_key = _plate_box_origin(components)
    if plate_key is None or isinstance(plate_key, tuple):
        # No single unambiguous boxed plate — never guessed, same as the
        # sibling assists' own ambiguous-origin handling.
        detail = (
            "varias placas tienen caja declarada — no elijo cuál es la "
            "principal" if isinstance(plate_key, tuple) else
            "ninguna placa tiene caja L×W×H declarada todavía"
        )
        rows.append(SilhouetteRow(
            gate="placa_con_caja", status="missing", detail=detail,
            suggest="declara frame_plate estimada L x W mm",
        ))
        return SilhouetteAssessment(verdict="racimo", rows=tuple(rows))

    plate_estimated = _plate_authority_estimated(components, plate_key)
    rows.append(SilhouetteRow(
        gate="placa_con_caja", status="ok",
        detail=f"{plate_key} tiene caja L×W×H declarada",
    ))
    rows.append(SilhouetteRow(
        gate="autoridad_placa",
        status="estimated" if plate_estimated else "ok",
        detail=(
            f"{plate_key}: geometría ESTIMATED_TEMPORARY — silueta llevará *"
            if plate_estimated
            else f"{plate_key}: geometría declarada/citada — sin *"
        ),
    ))

    present_subjects = _stack_present_subjects(components)
    stack_complete = True

    # Row 3 (IC §1.1) — pose, all present subjects together, fixed order.
    for subject in present_subjects:
        spec = components[subject]
        posed = getattr(spec, "declared_box_pose", None) is not None
        if not posed:
            stack_complete = False
            rows.append(SilhouetteRow(
                gate=f"pose_{subject}", status="missing",
                detail=f"{subject}: sin pose declarada respecto a {plate_key}",
                suggest="apilar en placa",
            ))
        else:
            rows.append(SilhouetteRow(
                gate=f"pose_{subject}", status="ok",
                detail=f"{subject}: pose declarada respecto a {plate_key}",
            ))

    # Row 4 (IC §1.1) — mount, all present subjects together, fixed order.
    for subject in present_subjects:
        spec = components[subject]
        mounted = getattr(spec, "mounted_on", None) is not None
        if not mounted:
            stack_complete = False
            rows.append(SilhouetteRow(
                gate=f"montaje_{subject}", status="missing",
                detail=f"{subject}: sin montaje declarado",
                suggest="montajes estándar",
            ))
        else:
            rows.append(SilhouetteRow(
                gate=f"montaje_{subject}", status="ok",
                detail=f"{subject}: montaje declarado",
            ))

    from jarvis.workspace.spatial_board import _quad_x_wheelbase_mm

    if _quad_x_wheelbase_mm(components) is not None:
        rows.append(SilhouetteRow(
            gate="visor_x_wb", status="ok",
            detail="frame quad_x + wheelbase citados — motores/hélices visibles en X",
        ))
    else:
        rows.append(SilhouetteRow(
            gate="visor_x_wb", status="n/a",
            detail="frame sin quad_x+wheelbase citados — X no verificable hoy",
        ))

    # No shared "pose cycle" honesty check exists anywhere in the codebase
    # today (searched Continuity/pose modules) — reporting n/a rather than
    # inventing new detection logic (IC §1.1 row 6's own "else skip with
    # n/a" allowance).
    rows.append(SilhouetteRow(
        gate="pose_cycle", status="n/a",
        detail="sin verificación de ciclo de pose disponible todavía",
    ))

    if not stack_complete:
        return SilhouetteAssessment(verdict="racimo", rows=tuple(rows))
    if plate_estimated:
        return SilhouetteAssessment(verdict="silueta_estimada", rows=tuple(rows))
    return SilhouetteAssessment(verdict="silueta", rows=tuple(rows))


_VERDICT_COPY = {
    "racimo": "racimo (A)",
    "silueta_estimada": "silueta estimada (B*)",
    "silueta": "silueta (B)",
}


def format_silhouette_checklist(assessment: SilhouetteAssessment) -> str:
    """Locked Spanish copy — verdict line + row-by-row detail, honest
    'nada crítico pendiente' when everything present is satisfied. Never
    says VERIFICADO / CAD medido del kit / ensamblado."""
    lines = [f"¿Parece un dron? → {_VERDICT_COPY[assessment.verdict]}"]

    missing_rows = [r for r in assessment.rows if r.status == "missing"]
    for row in assessment.rows:
        if row.status == "missing":
            marker = "✗"
        elif row.status == "estimated":
            marker = "*"
        elif row.status == "n/a":
            marker = "·"
        else:
            marker = "✓"
        line = f"  {marker} {row.gate}: {row.detail}"
        if row.suggest:
            line += f" — escribe \"{row.suggest}\""
        lines.append(line)

    if assessment.verdict == "silueta_estimada":
        lines.append(
            "Nada crítico pendiente — silueta con placa ESTIMADA; "
            "sustituye L×W por una medida real cuando llegue el frame "
            "para quitar el *."
        )
    elif assessment.verdict == "silueta":
        lines.append("Nada crítico pendiente — silueta con placa declarada, sin *.")
    elif missing_rows:
        lines.append("Escribe la frase sugerida para avanzar — nada se declara solo.")

    return "\n".join(lines)
