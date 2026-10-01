"""Git helpers: locate the repository root and read the staged diff."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git command fails or the repo state is unexpected."""


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise GitError("git executable not found on PATH") from exc
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"git exited with code {proc.returncode}"
        raise GitError(detail)
    return proc.stdout


def repo_root(cwd: Path | None = None) -> Path:
    """Return the top-level directory of the git repository at ``cwd``."""
    return Path(_run_git(["rev-parse", "--show-toplevel"], cwd=cwd).strip())


def staged_diff(cwd: Path | None = None, max_chars: int = 12000) -> str:
    """Return the staged diff, truncated so it fits a model context window."""
    diff = _run_git(["diff", "--cached"], cwd=cwd)
    if not diff.strip():
        raise GitError("no staged changes — stage files with 'git add' first")
    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n... [diff truncated] ..."
    return diff
