"""Project Continuity (A') — Situation + Evidence + one Next useful step.

Pure helpers over startup-context inputs / ProjectState. No Decision Engine.
"""
from __future__ import annotations

from typing import Any


def _catalog_gap_covered_by_declared_thrust(
    project_state: Any, sim_status: str, req: dict[str, Any]
) -> bool:
    """G9-B: is the catalog-gap a BOM identity note, not a physics blocker?

    True only when the simulation PASSes AND the user already declared a
    per-motor thrust that covers the computed floor — in that case the gap
    (no SKU for this KV/prop/thrust combo) is honest but not actionable, and
    must not outrank the PASS branch. Any other case (no PASS, no declared
    thrust, or declared thrust under the floor) keeps the gap winning
    ``next_useful_step`` — this is a `>=` comparison, never a blanket
    suppression on ``sim_status == "pass"`` alone (G9-B regression guard).
    Does NOT read ``catalog_ref`` (G9-A stays deferred/out of scope).
    """
    if sim_status != "pass":
        return False
    declared = (getattr(project_state, "current_parameters", None) or {}).get(
        "per_motor_max_thrust_n"
    )
    if declared is None:
        return False
    needed = req.get("thrust_per_motor_needed_n")
    if needed is None:
        return False
    try:
        return float(declared) >= float(needed)
    except (TypeError, ValueError):
        return False


def build_project_continuity(
    *,
    project_state: Any,
    status_type: str,
    status_reason: str | None,
    phase: str | None,
    architecture_progress: str | None,
    next_architecture_label: str | None,
    next_block_status: str | None,
    proactive_question: str | None,
    suggested_action: dict[str, Any] | None,
    physical_requirements: dict[str, Any] | None,
    component_bom: dict[str, Any] | None,
    energy_model_note: str | None,
    motor_catalog_gap: str | None,
    motor_catalog_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the three-question continuity contract for a live project.

    Ranking for ``next_useful_step`` (first match wins):
      1. Blocking physics / missing params (status blocking)
      2. Simulation warning / fail
      3. Honest catalog gap (no matching part)
      4. Incomplete / missing BOM components
      5. Architecture block still in progress / pending
      6. Optimization suggestion only when the design is otherwise closed
      7. Fallback: design validated / continue
    """
    sim = (getattr(project_state, "latest_results", None) or {}).get("simulation") or {}
    calc = (getattr(project_state, "latest_results", None) or {}).get("calculations") or {}
    bom = component_bom or {}
    req = physical_requirements or {}

    incomplete = list(bom.get("incomplete") or [])
    missing = list(bom.get("missing") or [])
    sim_status = (sim.get("status") or "").lower()
    can_fly = sim.get("can_fly")

    # ── Situation (where am I?) ───────────────────────────────────────────────
    if status_type == "blocking":
        situation = "Diseño bloqueado: faltan parámetros físicos para simular con rigor."
    elif status_type == "no_data":
        situation = "Proyecto abierto sin simulación útil todavía."
    elif sim_status and sim_status != "pass":
        situation = f"Última simulación: {sim_status} — el diseño no está cerrado."
    elif incomplete or missing:
        if can_fly or sim_status == "pass":
            situation = (
                "Física orientativa en PASS, pero el sistema aún tiene gaps de componentes."
            )
        else:
            situation = "Proyecto en progreso: componentes o arquitectura incompletos."
    elif architecture_progress and next_architecture_label:
        situation = (
            f"Arquitectura {architecture_progress}: pendiente {next_architecture_label}."
        )
    elif sim_status == "pass":
        situation = "Diseño validado en simulación (PASS). Proyecto vivo — listo para el siguiente paso útil."
    else:
        situation = "Proyecto activo; revisa evidencia y el siguiente paso."

    # ── Evidence (why?) ───────────────────────────────────────────────────────
    evidence: list[str] = []
    if sim_status:
        quality = sim.get("quality")
        margin = sim.get("safety_margin_ratio")
        bits = [f"Simulación: {sim_status}"]
        if quality:
            bits.append(f"calidad {quality}")
        if margin is not None:
            bits.append(f"margen {float(margin):.2f}")
        evidence.append(" — ".join(bits))
    if req.get("thrust_per_motor_needed_n") is not None:
        _thrust_line = f"Requisito: ≥ {float(req['thrust_per_motor_needed_n']):.2f} N/motor"
        # FN-009: honest coupling — required thrust grows once battery mass enters
        # total_mass_kg, so this is a provisional floor until battery is declared.
        _battery_declared = (
            (getattr(project_state, "current_parameters", None) or {}).get("battery_capacity_wh")
            is not None
        )
        if not _battery_declared:
            _thrust_line += " (mínimo provisional — sube al declarar la batería)"
        evidence.append(_thrust_line)
    if req.get("autonomy_target_min") is not None:
        cur = req.get("current_autonomy_min")
        line = f"Autonomía objetivo: {float(req['autonomy_target_min']):.0f} min"
        if cur is not None:
            line += f" (actual ~{float(cur):.1f} min)"
        evidence.append(line)
    if req.get("max_mass_kg") is not None:
        cur_m = req.get("current_mass_kg")
        line = f"Masa máx.: {float(req['max_mass_kg']):.2f} kg"
        if cur_m is not None:
            line += f" (actual {float(cur_m):.2f} kg)"
        evidence.append(line)
    if architecture_progress:
        evidence.append(f"Arquitectura: {architecture_progress}")
    for entry in incomplete[:3]:
        miss = ", ".join(entry.get("missing_fields") or []) or "incompleto"
        evidence.append(f"Gap: {entry.get('key')} — {miss}")
    for key in missing[:3]:
        evidence.append(f"Falta definir: {key}")
    if motor_catalog_gap:
        evidence.append(f"Catálogo: {motor_catalog_gap}")
    elif motor_catalog_matches:
        names = ", ".join(m.get("name", "?") for m in motor_catalog_matches[:2])
        evidence.append(f"Catálogo: candidatos {names}")
    if energy_model_note:
        evidence.append(energy_model_note)
    if not evidence:
        evidence.append("Sin evidencia de cálculo/simulación aún.")

    # ── Next useful step (one winner) ─────────────────────────────────────────
    next_step: str
    next_why: str

    if status_type == "blocking":
        next_step = proactive_question or "Define los parámetros físicos que faltan."
        next_why = status_reason or "Sin ellos la simulación no es fiable."
    elif status_type == "warning" or (sim_status and sim_status not in ("pass", "", "ok")):
        warn = (sim.get("warnings") or [None])[0] or status_reason
        next_step = proactive_question or "Corrige la causa del warning/fallo de simulación."
        next_why = str(warn) if warn else "La última simulación no es PASS."
    elif motor_catalog_gap and not _catalog_gap_covered_by_declared_thrust(
        project_state, sim_status, req
    ):
        thrust = req.get("thrust_per_motor_needed_n")
        if thrust is not None:
            next_step = (
                f"Declara empuje real por motor (≥ {float(thrust):.1f} N) "
                "o elige una pieza fuera de catálogo; Jarvis no inventará un SKU."
            )
        else:
            next_step = (
                "Cierra el hueco de catálogo: declara empuje real o cambia requisitos."
            )
        next_why = (
            f"{motor_catalog_gap} Di 'qué motores tenemos' para ver el catálogo, "
            "o 'explora opciones' para que Jarvis pruebe configuraciones alternativas."
        )
    elif (getattr(project_state, "current_parameters", None) or {}).get("motor_power_w") is None and (
        any(e.get("key") == "motors" for e in incomplete)
        or "motors" in missing
        or motor_catalog_matches
    ):
        # FN-005 / P4: align Continuity with assisted energy/motor acquisition
        thrust = req.get("thrust_per_motor_needed_n")
        if motor_catalog_matches:
            names = ", ".join(m.get("name", "?") for m in motor_catalog_matches[:2])
            next_step = (
                "Elige un motor del catálogo o declara potencia en W "
                f"(candidatos: {names}). Di 'ayúdame a elegir' si quieres la lista."
            )
        elif thrust is not None:
            next_step = (
                f"Define la potencia nominal del motor (~{float(thrust):.1f} N/motor). "
                "Modelo, W aproximados, o 'ayúdame a elegir'."
            )
        else:
            next_step = (
                "Define la potencia nominal del motor (modelo, W, o 'ayúdame a elegir')."
            )
        next_why = "Falta motor_power_w / especificación de motors para cerrar energía y BOM."
    elif missing:
        key = missing[0]
        next_step = f"Define el componente pendiente: {key}."
        next_why = f"{key} aparece en la arquitectura y aún no está definido."
    elif incomplete:
        entry = incomplete[0]
        key = entry.get("key", "componente")
        miss = ", ".join(entry.get("missing_fields") or [])
        if miss and miss != "incompleto":
            next_step = f"Completa {key} (falta: {miss})."
        else:
            next_step = f"Revisa y completa la especificación de {key}."
        next_why = f"{key} sigue incompleto en el BOM."
    elif next_architecture_label:
        tag = " (en progreso)" if next_block_status == "in_progress" else ""
        next_step = proactive_question or f"Siguiente bloque: {next_architecture_label}{tag}."
        next_why = f"Arquitectura {architecture_progress or '?'} aún no cerrada."
    elif suggested_action and sim_status == "pass" and not incomplete and not missing:
        next_step = suggested_action.get("label") or "Optimiza o itera el diseño."
        next_why = suggested_action.get("reason") or "Diseño cerrado; puedes explorar mejoras."
    elif sim_status == "pass" and motor_catalog_gap:
        # G9-B demoted here: PASS + declared thrust already covers the floor —
        # the catalog gap is an honest BOM/identity note, not a physics
        # blocker. Named in next_why (not hidden), with the two working
        # escape hatches (S2's list-motors, pre-existing DSE explore) by name.
        margin = sim.get("safety_margin_ratio")
        margin_bit = f" (margen {float(margin):.1f}x)" if margin is not None else ""
        next_step = (
            f"Diseño en PASS{margin_bit} — puedes iterar, explorar alternativas, "
            "o vincular una pieza real del catálogo."
        )
        next_why = (
            f"No hay gaps físicos bloqueantes. Nota de catálogo: {motor_catalog_gap} "
            "— di 'qué motores tenemos' para ver el catálogo, o 'explora opciones' "
            "para que Jarvis pruebe configuraciones que sí tengan SKU."
        )
    elif sim_status == "pass":
        next_step = "Diseño en PASS — puedes iterar, explorar alternativas o documentar el cierre."
        next_why = "No hay gaps bloqueantes en BOM/catálogo."
    else:
        next_step = proactive_question or "Continúa definiendo el sistema o lanza calculate/simulate."
        next_why = "Aún no hay un cierre físico claro."

    return {
        "situation": situation,
        "evidence": evidence,
        "next_useful_step": next_step,
        "next_useful_why": next_why,
    }
