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
