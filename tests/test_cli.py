"""Tests for commitcraft.cli helpers."""

from commitcraft.cli import to_subject_only
from commitcraft.prompts import EMOJI_BY_TYPE, add_emoji


def test_to_subject_only_keeps_first_line():
    assert to_subject_only("feat: add thing\n\nBody goes here.") == "feat: add thing"


def test_to_subject_only_strips_surrounding_whitespace():
    assert to_subject_only("  fix: trim me  \n\nbody") == "fix: trim me"


def test_to_subject_only_empty_message():
    assert to_subject_only("   \n  ") == ""


def test_add_emoji_prefixes_known_types():
    assert add_emoji("fix(parser): guard empty lines") == "🐛 fix(parser): guard empty lines"
    assert add_emoji("feat: add retry flag").startswith("✨")


def test_add_emoji_leaves_unknown_types_alone():
    assert add_emoji("wip: something") == "wip: something"


def test_emoji_covers_all_prompt_types():
    for commit_type in ("feat", "fix", "docs", "style", "refactor", "perf",
                        "test", "build", "ci", "chore", "revert"):
        assert commit_type in EMOJI_BY_TYPE


def test_max_diff_chars_rejects_negative():
    import argparse

    from commitcraft.cli import build_parser

    parser = build_parser()
    try:
        parser.parse_args(["--max-diff-chars", "-5"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("negative --max-diff-chars should fail parsing")
