"""Project Continuity (A') — Situation + Evidence + one Next useful step.

Pure helpers over startup-context inputs / ProjectState. No Decision Engine.
"""
from __future__ import annotations

from typing import Any

from jarvis.core.project_closure import (
    catalog_bound_motor_covers_power_w,
    catalog_bound_motor_lacks_nameplate_watts,
    catalog_gap_covered_by_declared_thrust,
)

_WATTS_RECOVERY_WHY = (
    "Inventar W usaría (Wh/W)×60 como si fuera vuelo. No hay "
    "autonomía de hover calculable con la evidencia actual."
)


def _watts_recovery_next_step(project_state: Any) -> tuple[str, str] | None:
    """Continuity next step when the bound SKU cannot feed L0 (no nameplate W)."""
    from jarvis.core.engineering_readiness import bound_motor_needs_watts_recovery
    from jarvis.core.motor_catalog_assist import build_nameplate_watts_motor_suggestions

    if project_state is None or not bound_motor_needs_watts_recovery(project_state):
        return None
    names = [s["name"] for s in build_nameplate_watts_motor_suggestions(project_state)]
    if names:
        listed = ", ".join(names[:5])
        step = (
            "Este motor de catálogo no declara vatios, por eso no hay autonomía. "
            f"Candidatos que sí declaran W: {listed}. Di 'ayúdame a elegir'. "
            "No inventes motor_power_w."
        )
    else:
        step = (
            "Este motor no declara vatios, por eso no hay autonomía. "
            "No hay otro motor en el catálogo con KV/hélice actuales que declare W. "
            "No inventes motor_power_w."
        )
    return step, _WATTS_RECOVERY_WHY


_AUTONOMY_RECALC_NEXT_STEP = (
    "El motor vinculado declara vatios de placa. Di 'calcular' y 'simular' para "
    "actualizar la autonomía. No declares motor_power_w a mano."
)
_AUTONOMY_RECALC_WHY = (
    "Los W ya están en el proyecto; el último cálculo es anterior al cambio de motor."
)


def _await_autonomy_recalc_next_step(
    project_state: Any,
    req: dict[str, Any],
    calc: dict[str, Any],
    sim: dict[str, Any],
) -> tuple[str, str] | None:
    """Continuity next step right after a watts-declaring pick: minutes are

    stale (or absent) but nameplate W and battery Wh are both already in the
    project — the honest next step is recalc, not "declare W/Wh" (that label
    would be a lie once the params are present) and not watts-recovery (that
    rank already required the SKU to lack W, so it never reaches here).
    """
    if req.get("autonomy_target_min") is None:
        return None
    stale = calc.get("autonomy_min") is None or sim.get("energy_status") == "missing_energy_parameters"
    if not stale:
        return None
    if catalog_bound_motor_lacks_nameplate_watts(getattr(project_state, "design_properties", None)):
        return None
    params = getattr(project_state, "current_parameters", None) or {}
    if params.get("motor_power_w") is None or params.get("battery_capacity_wh") is None:
        return None
    return _AUTONOMY_RECALC_NEXT_STEP, _AUTONOMY_RECALC_WHY


def _autonomy_objective_undemonstrated(
    req: dict[str, Any],
    calc: dict[str, Any],
    sim: dict[str, Any],
) -> bool:
    """True when an autonomy constraint exists and is not demonstrated.

    Parent CLI-feasibility IC: target set but minutes absent / energy params
    missing. Delta 2026-09-02: minutes present but below the target (or the
    simulator already emitted ``autonomy_below_restriction``).
    """
    target = req.get("autonomy_target_min")
    if target is None:
        return False
    if calc.get("autonomy_min") is None or sim.get("energy_status") == "missing_energy_parameters":
        return True
    if _autonomy_calculated_below_target(req, sim):
        return True
    return False


def _autonomy_calculated_below_target(req: dict[str, Any], sim: dict[str, Any]) -> bool:
    """True when autonomy was calculated and misses the user's target."""
    target = req.get("autonomy_target_min")
    if target is None:
        return False
    warnings = sim.get("warnings") or []
    if "autonomy_below_restriction" in warnings:
        return True
    cur = req.get("current_autonomy_min")
    if cur is not None and float(cur) < float(target):
        return True
    return False


_FRAME_SIZE_MISSING_WHY = (
    "Sin clase declarada no hay screening de compatibilidad de clase (nivel A) posible."
)
_FRAME_PROP_SIZE_WHY = (
    "Compatibilidad de clase nivel A: no establecida. No se demuestra interferencia geométrica."
)


def _frame_class_next_step(project_state: Any, readiness: Any | None) -> tuple[str, str] | None:
    """Structure A (implementation_contract_structure_a.md §2.2): locked
    Spanish copy for the two class-compatibility gaps. LEVEL A / CLASS-BASED
    screening only — never "cabe"/"no cabe", never VERIFIED, never a claim
    that thrust changed. Only fires when ``readiness`` carries one of the
    gaps; every existing caller that omits ``readiness`` is unaffected.
    """
    if readiness is None:
        return None
    gap_types = {g.gap_type for g in (readiness.gaps or [])}

    if "GAP-FRAME-PROP-SIZE" in gap_types:
        from jarvis.core.project_closure import propeller_diameter_in

        diameter_in = propeller_diameter_in(project_state)
        components = getattr(getattr(project_state, "design_properties", None), "components", None) or {}
        frame = components.get("frame")
        size_prop = getattr(frame, "properties", {}).get("size_class_inch") if frame is not None else None
        size_class_inch = size_prop.value if size_prop is not None else None
        step = (
            f"La hélice ({diameter_in:g} in) supera la clase de frame declarada "
            f"({size_class_inch:g} in). Compatibilidad de clase nivel A: no establecida. "
            "Declara un frame de clase mayor o una hélice menor. Esto no cambia el PASS "
            "de empuje ni demuestra interferencia geométrica."
        )
        return step, _FRAME_PROP_SIZE_WHY

    if "GAP-FRAME-SIZE-MISSING" in gap_types:
        from jarvis.core.project_closure import propeller_diameter_in

        diameter_in = propeller_diameter_in(project_state)
        step = (
            f"Hay una hélice de {diameter_in:g} in y el frame no declara clase en pulgadas. "
            "Declara el tamaño del chasis (ej. 'frame 5 pulgadas'). El empuje lo da la hélice, "
            "no el frame; sin clase no hay screening de compatibilidad de clase (nivel A)."
        )
        return step, _FRAME_SIZE_MISSING_WHY

    return None


_AUTONOMY_BELOW_NEXT_STEP = (
    "La autonomía calculada está por debajo del objetivo. "
    "Revisa energía (batería o consumo) o el requisito; el empuje ya es PASS."
)

# CLI fail-routing coherence (implementation_contract_cli_fail_routing_
# coherence.md §2.4): _AUTONOMY_BELOW_NEXT_STEP's "el empuje ya es PASS" is
# only true when thrust actually passed (sim.can_fly is True). These two
# sentences cover the same rank-2 ("sim not pass") branch when thrust also
# failed — never claim PASS, never name a SKU, never say "ayúdame a elegir"
# (that CTA belongs to a separate, not-yet-ratified catalog-honesty IC).
_THRUST_FAIL_AUTONOMY_BELOW_NEXT_STEP = (
    "La simulación no es PASS: el empuje no alcanza el requisito y la autonomía "
    "está por debajo del objetivo. Cambia entradas; repetir simular con los "
    "mismos datos no cierra el fallo."
)
_THRUST_FAIL_NEXT_STEP = (
    "La simulación no es PASS: el empuje disponible no cubre el requisito. "
    "Cambia motor, hélice o masa; repetir simular no cierra el fallo."
)

# Claim hygiene under ASSEMBLY READY IC §2.1: codes that make a PASS margin
# claim weak — never autonomy_below_restriction, which is owned by the
# autonomy-undemonstrated/below situation branches above.
_MARGIN_WEAK_WARNING_CODES = frozenset({
    "low_margin", "high_actuator_load", "low_force_to_weight_ratio",
})

_MARGIN_WEAK_SITUATION = (
    "Comprobación de empuje: PASS. Margen ajustado — el diseño no está "
    "validado con reserva cómoda."
)


def margin_claim_weak(sim: dict[str, Any]) -> bool:
    """True when a PASS claim would overstate margin comfort (IC §2.1)."""
    if (sim.get("quality") or "").lower() == "risky":
        return True
    warnings = sim.get("warnings") or []
    return bool(_MARGIN_WEAK_WARNING_CODES.intersection(warnings))


_FRAME_CLASS_GAP_TYPES = frozenset({"GAP-FRAME-SIZE-MISSING", "GAP-FRAME-PROP-SIZE"})

_FRAME_CLASS_GAP_SITUATION = (
    "Comprobación de empuje: PASS. Compatibilidad de clase (nivel A) pendiente."
)


def _frame_class_gap_live(readiness: Any | None) -> bool:
    """Structure Foundations IC §2.2: True when the Gap Registry already
    carries a live GAP-FRAME-SIZE-MISSING/GAP-FRAME-PROP-SIZE — never
    re-derives the LEVEL A screening itself (that stays Structure A's
    ``frame_class_compatibility_state``); this only reads what
    ``build_engineering_readiness`` already computed."""
    if readiness is None:
        return False
    return any(g.gap_type in _FRAME_CLASS_GAP_TYPES for g in (readiness.gaps or []))


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
    readiness: Any | None = None,
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

    ERF-1 Slice 4: ``readiness`` (an ``EngineeringReadinessResult``, optional
    kw-only) is the new Gap Registry authority (design_erf1_readiness_
    foundation.md ★2/★9). When provided, the catalog-gap ranking decision
    (rank 3 / the PASS-demoted branch) is sourced from
    ``readiness.top_gap``/``readiness.subsystems["catalog"]`` instead of
    re-deriving it locally — this is the one ranking Continuity previously
    owned ad-hoc that ERF-1's own investigation named directly (G9-B).
    Every other rank (blocking/warning/motor_power_w assisted flow/BOM/
    architecture/optimization/plain PASS) is untouched — those are not
    duplicated ranking logic ERF-1 models today, and FN-005's assisted-
    acquisition copy has no ERF-1 gap-type equivalent to derive from without
    losing its richer, catalog-suggestion-aware text (regression guard, see
    implementation report). When ``readiness`` is omitted (every existing
    direct caller/unit test), behavior is byte-identical to pre-ERF-1.
    """
    sim = (getattr(project_state, "latest_results", None) or {}).get("simulation") or {}
    calc = (getattr(project_state, "latest_results", None) or {}).get("calculations") or {}
    bom = component_bom or {}
    req = physical_requirements or {}

    incomplete = list(bom.get("incomplete") or [])
    missing = list(bom.get("missing") or [])
    sim_status = (sim.get("status") or "").lower()
    can_fly = sim.get("can_fly")

    if readiness is not None:
        _catalog_is_top = (
            readiness.top_gap is not None
            and readiness.top_gap.gap_type == "GAP-MOTOR-CATALOG-UNRESOLVED"
        )
        _catalog_subsystem = readiness.subsystems.get("catalog")
        _catalog_demoted = bool(
            _catalog_subsystem is not None
            and _catalog_subsystem.warning_type == "CATALOG-GAP-DEMOTED-POST-PASS"
        )
        # T1 (implementation_contract_cli_catalog_assist_t1.md §2.4): prefer
        # readiness.motor_catalog_gap_fact when readiness is passed — no
        # second resolve on the estado path.
        _underspec_live = bool(readiness.motor_catalog_gap_fact) and (
            readiness.motor_catalog_gap_fact.startswith("bound_sku_underspec:")
        )
    else:
        _catalog_is_top = bool(motor_catalog_gap)
        _catalog_demoted = catalog_gap_covered_by_declared_thrust(project_state, sim_status, req)
        # readiness omitted: the existing catalog_gap message already names
        # this exact shape (resolve_motor_catalog_surface's underspec
        # sentence) — match on it rather than re-resolving.
        _underspec_live = bool(motor_catalog_gap) and (
            "ya no cubre el hueco de diseño" in motor_catalog_gap
        )

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
    elif sim_status == "pass" and _autonomy_objective_undemonstrated(req, calc, sim):
        # CLI feasibility vs readiness semantics IC (§2.1) + autonomy-below
        # delta: thrust feasibility PASS is not the same claim as "the
        # autonomy objective is demonstrated" — missing minutes or minutes
        # below the target both keep "Diseño validado" off this branch.
        situation = (
            "Comprobación de empuje: PASS. Candidato inicial — la autonomía del "
            "objetivo no está demostrada."
        )
    elif sim_status == "pass" and margin_claim_weak(sim):
        # Claim hygiene under ASSEMBLY READY IC §2.1: PASS does not mean
        # "validado con reserva cómoda" when quality is risky or an active
        # margin/load warning is present — evidence bullet below already
        # names quality/margin; this line must agree with it.
        situation = _MARGIN_WEAK_SITUATION
    elif sim_status == "pass" and _frame_class_gap_live(readiness):
        # Structure Foundations IC §2.2: a live frame-class gap must not
        # coexist with "Diseño validado" — next_useful_step already names
        # the gap via _frame_class_next_step; this keeps the situation line
        # from contradicting it.
        situation = _FRAME_CLASS_GAP_SITUATION
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
        else:
            # §2.2: never a silent target — no calculated minute exists, say so.
            line += " — no calculada (sin evidencia de potencia de hover usable)"
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
        # T1 (implementation_contract_cli_catalog_assist_t1.md §2.4): rank 2
        # stays first and its generic copy stays the default — but when the
        # bound motor SKU has drifted underspec, name the catalog candidates
        # (or the honest empty search) instead of only "no es PASS". Never
        # claims sim PASS or block CERRADO — picking a candidate is not a
        # feasibility guarantee.
        if _underspec_live:
            thrust = req.get("thrust_per_motor_needed_n")
            thrust_bit = f"≥ {float(thrust):.1f}" if thrust is not None else "el actual"
            t1_names: list[str] = []
            relax_names: list[str] = []
            motors_comp = (
                getattr(getattr(project_state, "design_properties", None), "components", None)
                or {}
            ).get("motors")
            bound_sku = getattr(getattr(motors_comp, "catalog_ref", None), "sku", None)
            if bound_sku:
                from jarvis.core.motor_catalog_assist import build_underspec_motor_offer

                offer = build_underspec_motor_offer(project_state)
                t1_names = [s["name"] for s in offer if not s.get("relaxed")]
                relax_names = [s["name"] for s in offer if s.get("relaxed")]
            if not t1_names and motor_catalog_matches:
                t1_names = [
                    str(m.get("name"))
                    for m in motor_catalog_matches[:5]
                    if m.get("name")
                ]
            if relax_names:
                t1_bit = ", ".join(t1_names[:5]) if t1_names else "ninguno"
                relax_bit = ", ".join(relax_names[:5])
                next_step = (
                    f"El motor vinculado ya no cubre el empuje ({thrust_bit} N/motor). "
                    f"Candidatos (KV/hélice actuales): {t1_bit}. "
                    f"Filtros relajados (sin KV ni pulgadas heredados): {relax_bit}. "
                    "Di 'ayúdame a elegir'. Elegir no garantiza sim PASS. "
                    "Un candidato relajado puede exigir otra hélice."
                )
            elif t1_names:
                names = ", ".join(t1_names[:5])
                next_step = (
                    f"El motor vinculado ya no cubre el empuje ({thrust_bit} N/motor). "
                    f"Candidatos: {names}. Di 'ayúdame a elegir' para la lista numerada. "
                    "Elegir no garantiza sim PASS."
                )
            else:
                next_step = (
                    "El motor vinculado ya no cubre el empuje requerido. No hay otro motor "
                    "en el catálogo con KV/hélice actuales. Di 'ayúdame a elegir' — la lista "
                    "puede estar vacía."
                )
            next_why = motor_catalog_gap or "La última simulación no es PASS."
        elif _autonomy_calculated_below_target(req, sim) and sim.get("can_fly") is True:
            # Thrust genuinely passed (can_fly True) — the only state where
            # "el empuje ya es PASS" is an honest claim.
            next_step = _AUTONOMY_BELOW_NEXT_STEP
            next_why = "autonomy_below_restriction"
        elif _autonomy_calculated_below_target(req, sim):
            # Thrust did NOT pass here (can_fly is not True) — never claim PASS.
            next_step = _THRUST_FAIL_AUTONOMY_BELOW_NEXT_STEP
            next_why = "GAP-SIM-NOT-PASS"
        elif sim.get("can_fly") is not True:
            # Thrust fails and autonomy is not (yet) the blocker named.
            next_step = _THRUST_FAIL_NEXT_STEP
            next_why = "GAP-SIM-NOT-PASS"
        else:
            warn = (sim.get("warnings") or [None])[0] or status_reason
            # §2.4: never echo the architecture-complete non-action into the
            # generic sim-not-pass fallback — that CTA belongs to a state
            # where nothing is actively failing, which this branch isn't.
            _pq = proactive_question or ""
            if proactive_question and "puedes optimizar o simular" not in _pq:
                next_step = proactive_question
            else:
                next_step = "Corrige la causa del warning/fallo de simulación."
            next_why = str(warn) if warn else "La última simulación no es PASS."
    elif motor_catalog_gap and _catalog_is_top and not _catalog_demoted:
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
        not catalog_bound_motor_covers_power_w(getattr(project_state, "design_properties", None))
        and (
            any(e.get("key") == "motors" for e in incomplete)
            or "motors" in missing
            or motor_catalog_matches
        )
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
    elif (_fc := _frame_class_next_step(project_state, readiness)) is not None:
        next_step, next_why = _fc
    elif next_architecture_label:
        tag = " (en progreso)" if next_block_status == "in_progress" else ""
        next_step = proactive_question or f"Siguiente bloque: {next_architecture_label}{tag}."
        next_why = f"Arquitectura {architecture_progress or '?'} aún no cerrada."
    elif sim_status == "pass" and _autonomy_calculated_below_target(req, sim):
        next_step = _AUTONOMY_BELOW_NEXT_STEP
        next_why = "autonomy_below_restriction"
    elif (_wr := _watts_recovery_next_step(project_state)) is not None:
        next_step, next_why = _wr
    elif (_rc := _await_autonomy_recalc_next_step(project_state, req, calc, sim)) is not None:
        next_step, next_why = _rc
    elif suggested_action and sim_status == "pass" and not incomplete and not missing:
        next_step = suggested_action.get("label") or "Optimiza o itera el diseño."
        next_why = suggested_action.get("reason") or "Diseño cerrado; puedes explorar mejoras."
    elif sim_status == "pass" and motor_catalog_gap and _catalog_is_top and _catalog_demoted:
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
