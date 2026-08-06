from __future__ import annotations

import json
from urllib import error, request

from jarvis.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_PATH,
    OLLAMA_FORMAT,
    OLLAMA_MODEL,
    OLLAMA_STREAM,
    OLLAMA_TEMPERATURE,
    OLLAMA_TIMEOUT_SECONDS,
)


class OllamaClient:
    def __init__(
        self,
        *,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        chat_path: str = OLLAMA_CHAT_PATH,
        response_format: str = OLLAMA_FORMAT,
        stream: bool = OLLAMA_STREAM,
        temperature: float = OLLAMA_TEMPERATURE,
        timeout_seconds: float = OLLAMA_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.chat_path = chat_path
        self.response_format = response_format
        self.stream = stream
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds

    def complete(self, messages: list[dict[str, str]], json_mode: bool = True) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": self.stream,
            "options": {
                "temperature": self.temperature,
            },
        }
        if json_mode:
            payload["format"] = self.response_format
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url=f"{self.base_url}{self.chat_path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(
                f"No se pudo conectar con Ollama en {self.base_url}{self.chat_path}: {exc}"
            ) from exc

        content = response_payload.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama devolvió una respuesta sin `message.content` válido.")
        return content.strip()
