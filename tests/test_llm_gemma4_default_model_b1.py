"""B1-llm-gemma4-default-model (CI-1): product default Ollama model.

Unit-level only — no live Ollama required (T3). Env-dependent checks run in a
subprocess so `jarvis.config` is never reloaded in-process (other modules hold
`from jarvis.config import ...` bindings).
"""

import os
import subprocess
import sys
from pathlib import Path

from jarvis import config
from jarvis.llm.ollama_client import OllamaClient

GEMMA_TAG = "hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _config_model_in_subprocess(env_override: str | None) -> str:
    env = dict(os.environ)
    env.pop("JARVIS_OLLAMA_MODEL", None)
    if env_override is not None:
        env["JARVIS_OLLAMA_MODEL"] = env_override
    code = (
        "from jarvis.config import OLLAMA_MODEL\n"
        "from jarvis.llm.ollama_client import OllamaClient\n"
        "assert OllamaClient().model == OLLAMA_MODEL\n"
        "print(OLLAMA_MODEL)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def test_t1_default_constant_is_locked_gemma_tag():
    assert config.DEFAULT_OLLAMA_MODEL == GEMMA_TAG


def test_t1_default_without_env_is_gemma_tag():
    assert _config_model_in_subprocess(None) == GEMMA_TAG


def test_t2_env_override_wins_for_config_and_client():
    assert _config_model_in_subprocess("other-tag") == "other-tag"


def test_t2_explicit_constructor_model_still_honoured():
    assert OllamaClient(model="explicit-test-model").model == "explicit-test-model"


def test_t4_product_docs_no_longer_claim_qwen_default():
    for rel in ("README.md", "src/jarvis/README.md"):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "qwen2.5:14b" not in text, rel
        assert GEMMA_TAG in text, rel
