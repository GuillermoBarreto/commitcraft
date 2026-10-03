"""Prompts that teach the model the Conventional Commits style."""

SYSTEM_PROMPT = """\
You write git commit messages in the Conventional Commits style.

RULES
- Format: type(scope): subject
- type is one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- scope is a short noun naming the part of the codebase (file, module, feature). Omit it when it adds nothing.
- subject is a short imperative summary, lowercase, no trailing period, max 72 characters.
- Use feat for a new user-visible feature, fix for a bug fix, refactor when behavior is unchanged, docs for documentation only, test for tests only, chore for tooling and maintenance.
- After the subject line, leave a blank line and add a body (2-4 sentences) explaining WHY the change was made when it is not obvious from the diff.
- Describe what the code actually does. Never invent behavior that is not in the diff.
- Output ONLY the commit message. No explanations, no markdown fences, no quotes around the message.
"""

USER_PROMPT_TEMPLATE = """\
Write a conventional commit message for this staged git diff:

{diff}
"""


def build_user_prompt(diff: str) -> str:
    """Wrap the staged diff in the user prompt sent to the model.

    The diff is spliced in with ``str.replace`` rather than ``str.format``
    so braces in the diff (dict literals, f-strings, JSX, ...) can never be
    misread as template fields, whatever the template looks like.
    """
    return USER_PROMPT_TEMPLATE.replace("{diff}", diff)


def build_retry_user_prompt(diff: str, previous: str) -> str:
    """User prompt asking for an alternative message different from ``previous``."""
    return build_user_prompt(diff) + (
        "\nYour previous suggestion was:\n"
        f"{previous}\n"
        "Suggest a DIFFERENT commit message for the same diff."
    )


EMOJI_BY_TYPE = {
    "feat": "✨",
    "fix": "🐛",
    "docs": "📝",
    "style": "💄",
    "refactor": "♻️",
    "perf": "⚡️",
    "test": "✅",
    "build": "🏗️",
    "ci": "👷",
    "chore": "🔧",
    "revert": "⏪",
}


def add_emoji(message: str) -> str:
    """Prefix the conventional-commit type with its emoji (``🐛 fix(scope): ...``).

    Messages whose type is not recognized are returned unchanged.
    """
    stripped = message.lstrip()
    for commit_type, emoji in EMOJI_BY_TYPE.items():
        if stripped.startswith(commit_type + "(") or stripped.startswith(commit_type + ":"):
            return f"{emoji} {message}"
    return message
