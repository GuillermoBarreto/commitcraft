"""LLM backends over stdlib ``urllib`` — commitcraft has no runtime dependencies."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class BackendError(RuntimeError):
    """Raised when the LLM backend cannot produce a suggestion."""


def _post_json(
    url: str, payload: dict, headers: dict[str, str], timeout: int = 120
) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise BackendError(f"backend returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise BackendError(f"could not reach backend at {url}: {exc.reason}") from exc


class OpenAICompatibleBackend:
    """Any OpenAI-compatible chat-completions API.

    Configuration via environment:
        OPENAI_API_KEY   — required
        OPENAI_BASE_URL  — optional, defaults to https://api.openai.com/v1
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self, base_url: str | None = None, api_key: str | None = None
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL", self.DEFAULT_BASE_URL)
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise BackendError(
                "OPENAI_API_KEY is not set — export it before using the openai backend"
            )

    def generate(self, system_prompt: str, user_prompt: str, model: str) -> str:
        body = _post_json(
            f"{self.base_url}/chat/completions",
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            },
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise BackendError("unexpected response shape from chat API") from exc


class OllamaBackend:
    """Local models served by Ollama.

    Configuration via environment:
        OLLAMA_BASE_URL — optional, defaults to http://localhost:11434
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")

    def generate(self, system_prompt: str, user_prompt: str, model: str) -> str:
        body = _post_json(
            f"{self.base_url}/api/chat",
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
            },
            {"Content-Type": "application/json"},
        )
        try:
            return body["message"]["content"].strip()
        except (KeyError, AttributeError) as exc:
            raise BackendError("unexpected response shape from Ollama") from exc


BACKENDS = {
    "openai": OpenAICompatibleBackend,
    "ollama": OllamaBackend,
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "ollama": "llama3.1",
}
