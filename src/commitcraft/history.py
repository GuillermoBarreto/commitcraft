"""Local history of generated commit messages.

commitcraft keeps a small JSON-lines log of recent suggestions under
``~/.commitcraft/history.jsonl`` so ``--retry`` can ask for a *different*
message and users can look back at what was generated.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HISTORY_DIR_NAME = ".commitcraft"
HISTORY_FILE_NAME = "history.jsonl"
MAX_ENTRIES = 50


def history_path() -> Path:
    """Return the history file path, creating ``~/.commitcraft`` if needed."""
    directory = Path.home() / HISTORY_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory / HISTORY_FILE_NAME


def record_message(message: str, backend: str, model: str) -> None:
    """Append a generated message to the history log (newest last)."""
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "backend": backend,
        "model": model,
        "message": message,
    }
    path = history_path()
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines.append(json.dumps(entry))
    path.write_text("\n".join(lines[-MAX_ENTRIES:]) + "\n", encoding="utf-8")


def recent_messages(limit: int = 5) -> list[dict]:
    """Return up to ``limit`` history entries, newest first.

    Corrupted lines and valid-JSON-but-not-a-mapping lines (e.g. ``42``)
    are skipped: a single bad line in the log must not crash the CLI.
    """
    path = history_path()
    if not path.exists():
        return []
    if limit <= 0:
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        entries.append(entry)
    return entries[-limit:][::-1]
