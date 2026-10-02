"""commitcraft CLI: draft a conventional commit message from the staged diff."""

from __future__ import annotations

import argparse
import subprocess
import sys

from .backends import BACKENDS, DEFAULT_MODELS, BackendError
from .gitutil import GitError, repo_root, staged_diff
from .prompts import SYSTEM_PROMPT, build_user_prompt


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
        type=int,
        default=12000,
        help="Truncate the staged diff past this many characters",
    )
    return parser


def draft_message(
    backend_name: str, model: str | None, max_diff_chars: int = 12000
) -> str:
    """Generate a commit message for the currently staged diff."""
    backend_cls = BACKENDS[backend_name]
    model = model or DEFAULT_MODELS[backend_name]
    diff = staged_diff(max_chars=max_diff_chars)
    backend = backend_cls()
    return backend.generate(SYSTEM_PROMPT, build_user_prompt(diff), model)


def show_dry_run(
    backend_name: str, model: str | None, max_diff_chars: int = 12000
) -> int:
    """Print the prompt that would be sent, without calling the LLM."""
    try:
        diff = staged_diff(max_chars=max_diff_chars)
    except GitError as exc:
        print(f"commitcraft: error: {exc}", file=sys.stderr)
        return 1
    model = model or DEFAULT_MODELS[backend_name]
    print(f"backend: {backend_name}")
    print(f"model: {model}")
    print("--- system prompt ---")
    print(SYSTEM_PROMPT)
    print("--- user prompt ---")
    print(build_user_prompt(diff))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo_root()
    except GitError as exc:
        print(f"commitcraft: error: {exc}", file=sys.stderr)
        return 1
    if args.dry_run:
        return show_dry_run(args.backend, args.model, args.max_diff_chars)
    try:
        message = draft_message(args.backend, args.model, args.max_diff_chars)
    except (GitError, BackendError) as exc:
        print(f"commitcraft: error: {exc}", file=sys.stderr)
        return 1
    if not message:
        print("commitcraft: error: backend returned an empty message", file=sys.stderr)
        return 1
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
