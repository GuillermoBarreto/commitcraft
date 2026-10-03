"""Tests for commitcraft.history."""

from commitcraft import history


def test_record_and_recent_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "history_path", lambda: tmp_path / "history.jsonl")
    history.record_message("feat: add thing", "openai", "gpt-4o-mini")
    history.record_message("fix: repair bug", "ollama", "llama3.1")
    recent = history.recent_messages(limit=5)
    assert [e["message"] for e in recent] == ["fix: repair bug", "feat: add thing"]
    assert recent[0]["backend"] == "ollama"


def test_history_is_capped(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "history_path", lambda: tmp_path / "history.jsonl")
    monkeypatch.setattr(history, "MAX_ENTRIES", 3)
    for i in range(5):
        history.record_message(f"feat: thing {i}", "openai", "m")
    recent = history.recent_messages(limit=10)
    assert [e["message"] for e in recent] == ["feat: thing 4", "feat: thing 3", "feat: thing 2"]


def test_recent_messages_empty_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "history_path", lambda: tmp_path / "missing.jsonl")
    assert history.recent_messages() == []
