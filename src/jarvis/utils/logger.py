from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DEFAULT_LLM_LOG_ROOT


class StructuredLogger:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or DEFAULT_LLM_LOG_ROOT

    def log_llm_event(self, payload: dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = self.root / f"{timestamp}.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return target
