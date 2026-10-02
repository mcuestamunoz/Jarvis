"""Tests T1-T6 for `B1-capability-skills-runtime-software` (T21).

First Skill **runner** — software Skills only. Chat Task classify
unchanged; `run_skill` is an additional, separately-callable API.
"""

from __future__ import annotations

from pathlib import Path

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability
from jarvis.capabilities.skills_runtime import run_skill
from jarvis.core.orchestrator import JarvisOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[1]


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_explain_concept_cite_or_honest_miss():
    resolved = run_skill("skill.explain_concept", query="c-rate-de-bateria")
    assert resolved.outcome == "ok"
    assert resolved.message is not None
    assert "DEFINICION" in resolved.message
    assert "no inventa" in resolved.message

    missing_query = run_skill("skill.explain_concept")
    assert missing_query.outcome == "reject"
    assert missing_query.reason == "missing_query"

    honest_miss = run_skill("skill.explain_concept", query="this-alias-does-not-exist-anywhere")
    assert honest_miss.outcome == "ok"
    assert "No solid ontology note for" in honest_miss.message


def test_t2_project_status_with_and_without_project():
    without = run_skill("skill.project_status")
    assert without.outcome == "reject"
    assert without.reason == "no_project"

    with_project = run_skill(
        "skill.project_status",
        project_status_provider=lambda: {"has_project": True, "objective": "transporte"},
    )
    assert with_project.outcome == "ok"
    assert with_project.message is not None

    no_project_from_provider = run_skill(
        "skill.project_status",
        project_status_provider=lambda: {"has_project": False},
    )
    assert no_project_from_provider.outcome == "reject"
    assert no_project_from_provider.reason == "no_project"


def test_t2b_project_status_via_real_orchestrator_build_startup_context(tmp_path: Path):
    """Real end-to-end reuse check (DC §0 row 4: 'reuse Continuity status
    formatting used by defer fulfill') — not a fake stub. `tmp_path` keeps
    this isolated from any real project on disk (a bare `JarvisOrchestrator()`
    with no `workspace_root` would otherwise pick up the user's actual
    workspace)."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    result = run_skill(
        "skill.project_status",
        project_status_provider=lambda: orch.build_startup_context(),
    )
    assert result.outcome == "reject"
    assert result.reason == "no_project"


def test_t3_vehicle_and_ops_skills_stay_stub():
    """T21: vehicle/ops Skills were stub. T23/T24/T25/T26/T27/T28 flip
    HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW to available (shared
    vehicle gate). Remaining vehicle/ops stay stub."""
    for skill_id in (
        "skill.request_arm_policy",
        "skill.request_disarm_policy",
        "skill.request_patrol",
        "skill.request_charge",
    ):
        result = run_skill(skill_id)
        assert result.outcome == "reject"
        assert result.reason == "skill_stub", f"{skill_id} should still be stub"


def test_t3b_unknown_skill_id_honest_reject():
    result = run_skill("skill.does_not_exist")
    assert result.outcome == "reject"
    assert result.reason == "unknown_skill"


def test_t4_seed_exactly_two_available_rest_stub():
    """T21 shipped two available software Skills. T23/T24/T25/T26/T27/T28
    add HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW (shared vehicle gate)
    — membership widened, not a reopen of T21."""
    registry = CapabilityRegistry.load_default()
    available_ids = {s.id for s in registry.skills() if s.availability == CapabilityAvailability.AVAILABLE}
    assert available_ids == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
        "skill.request_return_home",
        "skill.request_follow",
    }

    stub_ids = {s.id for s in registry.skills() if s.availability == CapabilityAvailability.STUB}
    assert "skill.request_hold" not in stub_ids
    assert "skill.request_land" not in stub_ids
    assert "skill.request_charge" in stub_ids
    assert available_ids.isdisjoint(stub_ids)
    assert len(registry.skills()) == 12


def test_t5_chat_task_classify_still_emits_without_skill_lookup(tmp_path: Path):
    """T21 lock: Task *classify* still does not look Skills up before emit.
    T22 later wires *fulfill* through `run_skill` in `handle_explain_intent`
    — that import is expected now; classify body must still not call
    `registry.skills()` / Skill ids as a gate."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    result = orch.handle_user_text("explain c-rate-de-bateria", exploding)
    assert result["status"] == "ok"
    assert result["action"] == "global_command"

    classify_source = (
        REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"
    ).read_text(encoding="utf-8")
    # try_explain_concept_task body must not consult the Skills catalog
    assert "registry.skills(" not in classify_source
    assert "skill.explain_concept" not in classify_source.split("def handle_explain_intent")[0]
