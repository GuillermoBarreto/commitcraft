"""Tests for commitcraft.gitutil using real throwaway git repos."""

import subprocess
from pathlib import Path

import pytest

from commitcraft.gitutil import GitError, repo_root, staged_diff


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("hello\n")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True
    )
    return tmp_path


def test_repo_root(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(git_repo)
    assert repo_root() == git_repo


def test_repo_root_not_a_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(GitError):
        repo_root()


def test_staged_diff(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (git_repo / "a.txt").write_text("hello world\n")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    monkeypatch.chdir(git_repo)
    assert "hello world" in staged_diff()


def test_staged_diff_empty_raises(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(git_repo)
    with pytest.raises(GitError, match="no staged changes"):
        staged_diff()


def test_staged_diff_truncates(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (git_repo / "a.txt").write_text("x" * 5000)
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    monkeypatch.chdir(git_repo)
    diff = staged_diff(max_chars=100)
    assert "[diff truncated]" in diff
    assert len(diff) < 5000
