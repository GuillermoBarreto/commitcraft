"""commitcraft CLI: draft a conventional commit message from the staged diff."""

from __future__ import annotations

import argparse
import subprocess
import sys

from .backends import BACKENDS, DEFAULT_MODELS, BackendError
from .gitutil import GitError, repo_root, staged_diff
from .history import record_message, recent_messages
from .prompts import SYSTEM_PROMPT, add_emoji, build_retry_user_prompt, build_user_prompt


def _non_negative_int(value: str) -> int:
    """argparse ``type`` that rejects negative ints.

    A negative ``--max-diff-chars`` would slice the diff as ``diff[:-N]``,
    silently dropping the tail without the "[diff truncated]" marker.
    """
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError(f"must be >= 0, got {value!r}")
    return ivalue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commitcraft",
        description=(
            "Draft a conventional commit message from your staged git diff "
            "using an LLM."
        ),
    )
    parser.add_argument(
        "--backend",
        choices=sorted(BACKENDS),
        default="openai",
        help="LLM backend to use (default: openai)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (defaults per backend)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit the staged changes with the suggested message",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt that would be sent, without calling the LLM",
    )
    parser.add_argument(
        "--max-diff-chars",
        type=_non_negative_int,
        default=12000,
        help="Truncate the staged diff past this many characters",
    )
    parser.add_argument(
        "--retry",
        action="store_true",
        help="Generate a fresh alternative different from the last suggestion",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show recently generated commit messages and exit",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=5,
        help="How many history entries --history shows (default: 5)",
    )
    parser.add_argument(
        "--oneline",
        action="store_true",
        help="Print only the subject line, without the body",
    )
    parser.add_argument(
        "--emoji",
        action="store_true",
        help="Prefix the commit type with its conventional emoji",
    )
    return parser


def draft_message(
    backend_name: str, model: str | None, max_diff_chars: int = 12000, retry: bool = False
) -> str:
    """Generate a commit message for the currently staged diff."""
    backend_cls = BACKENDS[backend_name]
    model = model or DEFAULT_MODELS[backend_name]
    diff = staged_diff(max_chars=max_diff_chars)
    user_prompt = build_user_prompt(diff)
    if retry:
        previous = recent_messages(limit=1)
        if previous:
            user_prompt = build_retry_user_prompt(diff, previous[0]["message"])
    backend = backend_cls()
    return backend.generate(SYSTEM_PROMPT, user_prompt, model)


def show_dry_run(
    backend_name: str, model: str | None, max_diff_chars: int = 12000, retry: bool = False
) -> int:
    """Print the prompt that would be sent, without calling the LLM."""
    try:
        diff = staged_diff(max_chars=max_diff_chars)
    except GitError as exc:
        print(f"commitcraft: error: {exc}", file=sys.stderr)
        return 1
    model = model or DEFAULT_MODELS[backend_name]
    user_prompt = build_user_prompt(diff)
    if retry:
        previous = recent_messages(limit=1)
        if previous:
            user_prompt = build_retry_user_prompt(diff, previous[0]["message"])
    print(f"backend: {backend_name}")
    print(f"model: {model}")
    print("--- system prompt ---")
    print(SYSTEM_PROMPT)
    print("--- user prompt ---")
    print(user_prompt)
    return 0


def to_subject_only(message: str) -> str:
    """Return just the subject line of a commit message (no body)."""
    stripped = message.strip()
    return stripped.splitlines()[0].strip() if stripped else ""


def show_history(limit: int = 5) -> int:
    """Print recent generated messages, newest first."""
    entries = recent_messages(limit=limit)
    if not entries:
        print("commitcraft: no history yet")
        return 0
    for entry in entries:
        print(f"[{entry['at']}] ({entry['backend']}/{entry['model']})")
        print(entry["message"])
        print()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.history:
        return show_history(args.history_limit)
    try:
        repo_root()
    except GitError as exc:
        print(f"commitcraft: error: {exc}", file=sys.stderr)
        return 1
    if args.dry_run:
        return show_dry_run(args.backend, args.model, args.max_diff_chars, args.retry)
    try:
        message = draft_message(args.backend, args.model, args.max_diff_chars, args.retry)
    except (GitError, BackendError) as exc:
        print(f"commitcraft: error: {exc}", file=sys.stderr)
        return 1
    if not message:
        print("commitcraft: error: backend returned an empty message", file=sys.stderr)
        return 1
    model = args.model or DEFAULT_MODELS[args.backend]
    record_message(message, args.backend, model)
    if args.oneline:
        message = to_subject_only(message)
    if args.emoji:
        message = add_emoji(message)
    print(message)
    if args.apply:
        try:
            confirm = input("Commit with this message? [y/N] ").strip().lower()
        except EOFError:
            confirm = "n"
        if confirm != "y":
            print("commitcraft: aborted", file=sys.stderr)
            return 1
        try:
            subprocess.run(["git", "commit", "-m", message], check=True)
        except subprocess.CalledProcessError:
            print("commitcraft: error: git commit failed", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
