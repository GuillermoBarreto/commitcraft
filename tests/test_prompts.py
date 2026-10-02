"""Tests for commitcraft.prompts."""


from commitcraft.prompts import SYSTEM_PROMPT, build_user_prompt


def test_system_prompt_teaches_conventional_commits() -> None:
    assert "Conventional Commits" in SYSTEM_PROMPT


def test_system_prompt_lists_common_types() -> None:
    for commit_type in ("feat", "fix", "docs", "refactor", "test"):
        assert commit_type in SYSTEM_PROMPT


def test_system_prompt_constrains_output() -> None:
    assert "Output ONLY the commit message" in SYSTEM_PROMPT


def test_build_user_prompt_wraps_diff() -> None:
    diff = "diff --git a/a.txt b/a.txt\n+hello"
    prompt = build_user_prompt(diff)
    assert diff in prompt
    assert "commit message" in prompt.lower()


def test_build_user_prompt_inserts_diff_verbatim() -> None:
    # Diffs routinely contain braces (dict literals, f-strings, JSX, Go
    # structs, ...). Pin the contract that the diff is inserted verbatim,
    # whatever templating mechanism is used under the hood.
    diff = 'diff --git a/a.py b/a.py\n+config = {"key": f"{value}"}\n+if ok: print("{done}")'
    prompt = build_user_prompt(diff)
    assert diff in prompt
    assert prompt.count("{diff}") == 0
