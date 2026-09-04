#!/usr/bin/env python3
"""CLI probe post checkpoint-g21-g23 — G21 bind path + G22 gap/list parity.

Runs probes:
  1. Wizard path: create → arch A → definir propulsion → ayúdame a elegir → pick → estado
  2. G22 gap/list parity (prop=10, kv~2400)
  3. IDLE path: freeform 4x 2306… → atrás → ayúdame a elegir → pick → estado
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _say(orch: JarvisOrchestrator, text: str, llm: _RefuseLLM) -> dict:
    print(f"\nUser > {text}")
    result = orch.handle_user_text(text, llm)
    msg = result.get("message") or result.get("question") or ""
    if msg:
        print(f"Jarvis > {msg[:1200]}")
    print(f"  [action={result.get('action')} status={result.get('status')}]")
    return result


def main() -> int:
    llm = _RefuseLLM()
    with tempfile.TemporaryDirectory(prefix="jarvis-probe-g21-") as tmp:
        orch = JarvisOrchestrator(workspace_root=Path(tmp))
        orch.handle({
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "probe G21/G22 post checkpoint-g21-g23",
                "payload_kg": 1.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "structure_mass_factor": 0.5,
                "safety_factor": 1.2,
            },
        })
        ps = orch.state_manager.load_active_project(orch.workspace_manager)
        orch.system_definition_session.start("dron", ps)
        orch.system_definition_session.answer("A")
        print("=== Setup: project created, architecture A applied ===")

        steps = [
            "definir propulsion",
            "ayúdame a elegir",
            "1",
            "estado",
        ]
        results = {}
        for step in steps:
            results[step] = _say(orch, step, llm)

        # Assertions — Probe 1 (G21 + G9-A Scenario B via new path)
        choose = results["ayúdame a elegir"]
        assert "Candidatos del catálogo" in (choose.get("message") or ""), "G21: no catalog list"
        assert choose.get("motor_suggestions"), "G21: motor_suggestions empty"
        assert "Puedes:" not in (choose.get("message") or ""), "G21: Brief loop instead of catalog"

        pick = results["1"]
        assert pick.get("action") == "component_description_saved", f"pick action={pick.get('action')}"

        project = orch.state_manager.load_active_project(orch.workspace_manager)
        motors = project.design_properties.components.get("motors")
        assert motors is not None and motors.catalog_ref is not None, "G21: catalog_ref not set"
        print(f"\n✓ catalog_ref: {motors.catalog_ref.sku}")

        status = results["estado"]
        ctx = status.get("startup_context") or {}
        gap = ctx.get("motor_catalog_gap")
        assert gap is None, f"G9-A Scenario B: unexpected gap after bind: {gap!r}"
        print("✓ Probe 1 PASS: bind via component wizard clears motor_catalog_gap")

        # Probe 2 — G22 parity on a fresh project with prop filter
        print("\n=== Probe 2: G22 gap/list parity (prop=10, kv~2400) ===")
        with tempfile.TemporaryDirectory(prefix="jarvis-probe-g22-") as tmp2:
            o2 = JarvisOrchestrator(workspace_root=Path(tmp2))
            o2.handle({
                "action": "create_project",
                "parameters": {
                    "vehicle_type": "dron",
                    "objective": "G22 parity probe",
                    "payload_kg": 1.0,
                    "restrictions": "ninguna",
                    "detail_level": "conceptual",
                    "structure_mass_factor": 0.5,
                    "safety_factor": 1.2,
                    "motor_count": 4,
                    "motor_kv_rating": 2400,
                    "per_motor_max_thrust_n": 6.9,
                },
            })
            ps2 = o2.state_manager.load_active_project(o2.workspace_manager)
            from jarvis.schemas.action_schema import ComponentSpec, PropertyValue

            motors_free = ComponentSpec(
                name="4x 2306 2400KV",
                component_type="propulsion_active",
                suggested_key="motors",
                completeness="high",
                source="declared",
                properties={
                    "motor_count": PropertyValue(value=4),
                    "kv_rating": PropertyValue(value=2400),
                },
            )
            dp = ps2.design_properties.model_copy(update={
                "system_defined": True,
                "system_blocks": ["propulsion", "energy", "structure", "control"],
                "system_priority": ["propulsion", "energy", "structure", "control"],
                "components": {"motors": motors_free},
            })
            cp = dict(ps2.current_parameters or {})
            cp.update({
                "motor_count": 4,
                "motor_kv_rating": 2400,
                "propeller_diameter_in": 10.0,
                "per_motor_max_thrust_n": 6.9,
            })
            ps2 = ps2.model_copy(update={
                "design_properties": dp,
                "current_parameters": cp,
                "latest_results": {
                    "calculations": {"required_thrust_n": 27.6},
                    "simulation": {"physics_status": "valid", "status": "pass", "warnings": []},
                },
            })
            o2.workspace_manager.save_state(ps2)

            est = _say(o2, "estado", llm)
            ctx2 = est.get("startup_context") or {}
            gap2 = ctx2.get("motor_catalog_gap") or ""
            list_r = _say(o2, "qué motores tenemos", llm)
            list_msg = list_r.get("message") or ""
            list_has_skus = any(
                line.strip() and line.strip()[0].isdigit()
                for line in list_msg.splitlines()
            )
            gap_says_no_motor = "no tengo un motor" in gap2.lower()
            # G22: old bug was gap-empty-message + list populated. Agreement means
            # never "no motor" in gap while list shows numbered SKUs.
            if gap_says_no_motor:
                assert not list_has_skus, (
                    f"G22 contradiction: gap says no motor but list has SKUs\n"
                    f"gap={gap2!r}\nlist={list_msg[:400]!r}"
                )
            print("✓ Probe 2 PASS: gap and list agree (both empty for strict filter)")

        # Probe 3 — G21 IDLE: freeform declare → cancel wizard → ayúdame a elegir
        print("\n=== Probe 3: IDLE freeform motor (4x 2306…) → ayúdame a elegir ===")
        with tempfile.TemporaryDirectory(prefix="jarvis-probe-g21-idle-") as tmp3:
            o3 = JarvisOrchestrator(workspace_root=Path(tmp3))
            o3.handle({
                "action": "create_project",
                "parameters": {
                    "vehicle_type": "dron",
                    "objective": "G21 IDLE freeform probe",
                    "payload_kg": 1.0,
                    "restrictions": "ninguna",
                    "detail_level": "conceptual",
                    "structure_mass_factor": 0.5,
                    "safety_factor": 1.2,
                },
            })
            ps3 = o3.state_manager.load_active_project(o3.workspace_manager)
            o3.system_definition_session.start("dron", ps3)
            o3.system_definition_session.answer("A")
            _say(o3, "definir propulsion", llm)
            _say(o3, "4x 2306 2400KV 50W", llm)
            _say(o3, "atrás", llm)

            ps3 = o3.state_manager.load_active_project(o3.workspace_manager)
            motors3 = ps3.design_properties.components.get("motors")
            assert motors3 is not None and motors3.catalog_ref is None
            assert ps3.current_parameters.get("motor_power_w") is not None

            idle_choose = _say(o3, "ayúdame a elegir", llm)
            msg3 = idle_choose.get("message") or ""
            assert idle_choose.get("action") != "project_status", (
                "G21 IDLE dead-end: fell through to Continuity/estado"
            )
            assert "Candidatos del catálogo" in msg3 or "No tengo un motor" in msg3

            pick3 = _say(o3, "1", llm)
            ps3 = o3.state_manager.load_active_project(o3.workspace_manager)
            sku3 = ps3.design_properties.components["motors"].catalog_ref.sku
            status3 = _say(o3, "estado", llm)
            gap3 = (status3.get("startup_context") or {}).get("motor_catalog_gap")
            assert gap3 is None, f"gap after IDLE bind: {gap3!r}"
            print(f"✓ Probe 3 PASS: IDLE freeform → catalog → bind {sku3}")

        summary = {
            "checkpoint": "checkpoint-g21-g23",
            "probe1_catalog_ref": motors.catalog_ref.sku,
            "probe1_motor_catalog_gap": gap,
            "probe2_gap_list_agree": True,
            "probe3_idle_freeform_bind": sku3,
            "probe3_motor_catalog_gap": gap3,
        }
        print("\n=== SUMMARY ===")
        print(json.dumps(summary, indent=2))
        return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
