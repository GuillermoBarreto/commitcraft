"""Tests for commitcraft.backends with a faked HTTP layer."""

import io
import json
import urllib.error

import pytest

from commitcraft import backends
from commitcraft.backends import (
    BACKENDS,
    DEFAULT_MODELS,
    BackendError,
    LocalBackend,
    OllamaBackend,
    OpenAICompatibleBackend,
)


class FakeResponse:
    """Minimal context-manager stand-in for urllib's response object."""

    def __init__(self, payload: dict) -> None:
        self._payload = json.dumps(payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def _patch_urlopen(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    def fake_urlopen(req, timeout=None):
        assert req.method == "POST"
        return FakeResponse(payload)

    monkeypatch.setattr(backends.urllib.request, "urlopen", fake_urlopen)


def test_backend_registry() -> None:
    assert set(BACKENDS) == {"openai", "ollama", "local"}
    assert set(DEFAULT_MODELS) == {"openai", "ollama", "local"}


def test_openai_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(BackendError, match="OPENAI_API_KEY"):
        OpenAICompatibleBackend()


def test_openai_generate_parses_chat_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _patch_urlopen(
        monkeypatch,
        {"choices": [{"message": {"content": "  feat: add thing  "}}]},
    )
    backend = OpenAICompatibleBackend()
    assert backend.generate("sys", "user", "gpt-4o-mini") == "feat: add thing"


def test_openai_generate_bad_shape_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _patch_urlopen(monkeypatch, {"unexpected": True})
    with pytest.raises(BackendError, match="unexpected response shape"):
        OpenAICompatibleBackend().generate("sys", "user", "gpt-4o-mini")


def test_ollama_generate_parses_chat_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_urlopen(
        monkeypatch,
        {"message": {"content": "fix: repair parser"}},
    )
    backend = OllamaBackend()
    assert backend.generate("sys", "user", "llama3.1") == "fix: repair parser"


def test_ollama_generate_bad_shape_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_urlopen(monkeypatch, {"nope": 1})
    with pytest.raises(BackendError, match="unexpected response shape"):
        OllamaBackend().generate("sys", "user", "llama3.1")


def test_http_error_becomes_backend_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 401, "Unauthorized", {}, io.BytesIO(b"bad key")
        )

    monkeypatch.setattr(backends.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(BackendError, match="HTTP 401"):
        OpenAICompatibleBackend().generate("sys", "user", "gpt-4o-mini")


def test_unreachable_host_becomes_backend_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(backends.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(BackendError, match="could not reach backend"):
        OllamaBackend().generate("sys", "user", "llama3.1")


def test_local_backend_composes_message(monkeypatch):
    answers = iter(["2", "parser", "guard against empty input lines", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    message = LocalBackend().generate("system", "user", "interactive")
    assert message == "fix(parser): guard against empty input lines"


def test_local_backend_without_scope_and_with_body(monkeypatch):
    answers = iter(["1", "", "add shiny thing", "It sparkles."])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    message = LocalBackend().generate("system", "user", "interactive")
    assert message == "feat: add shiny thing\n\nIt sparkles."


def test_local_backend_reprompts_on_bad_type(monkeypatch, capsys):
    answers = iter(["99", "nope", "3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    backend = LocalBackend()
    assert backend._pick_type() == "docs"
    assert "enter a number from the list" in capsys.readouterr().out


def test_local_backend_requires_subject(monkeypatch, capsys):
    answers = iter(["1", "cli", "", "  ", "real subject", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    message = LocalBackend().generate("system", "user", "interactive")
    assert message == "feat(cli): real subject"
    assert "subject cannot be empty" in capsys.readouterr().out


def test_local_backend_abort_on_eof(monkeypatch):
    def boom(prompt=""):
        raise EOFError
    monkeypatch.setattr("builtins.input", boom)
    with pytest.raises(BackendError, match="aborted"):
        LocalBackend().generate("system", "user", "interactive")
