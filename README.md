# commitcraft

An AI-powered CLI that drafts [conventional commit](https://www.conventionalcommits.org/)
messages from your staged git diff. Stage your changes, run `commitcraft`,
get a clean `feat(scope): ...` message — optionally commit with it.

No runtime dependencies — the LLM calls are plain `urllib` over HTTPS.

## Install

Requires Python 3.10+.

```bash
git clone https://github.com/GuillermoBarreto/commitcraft
cd commitcraft
pip install -e .
```

For development (runs the test suite):

```bash
pip install -e ".[dev]"
pytest
```

## Usage

Stage some changes, then:

```bash
commitcraft
```

Example output:

```
fix(parser): guard against empty input lines

The tokenizer crashed on trailing newlines because it assumed every
line had at least one character. Skip blank lines before tokenizing.
```

Commit with the suggested message after a confirmation prompt:

```bash
commitcraft --apply
```

Choose the backend and model:

```bash
commitcraft --backend ollama --model codellama
commitcraft --backend openai --model gpt-4o-mini
```

## Configuration

commitcraft reads everything from environment variables. Never commit secrets —
set them in your shell profile instead.

| Variable          | Backend | Description                                              |
|-------------------|---------|----------------------------------------------------------|
| `OPENAI_API_KEY`  | openai  | **Required** for the default backend.                    |
| `OPENAI_BASE_URL` | openai  | Optional. Any OpenAI-compatible chat API (default: `https://api.openai.com/v1`). |
| `OLLAMA_BASE_URL` | ollama  | Optional (default: `http://localhost:11434`).            |

```bash
export OPENAI_API_KEY="..."            # keep this out of your shell history / repos
commitcraft --backend ollama           # or run fully local with Ollama
```

## How it works

1. `gitutil` reads `git diff --cached` and truncates it to a sane size.
2. `prompts` wraps the diff with a system prompt that teaches conventional commits.
3. `backends` sends the request — OpenAI-compatible chat API or local Ollama.
4. `cli` prints the suggestion, or commits it with `--apply`.

## Roadmap

- `--dry-run` showing the request that would be sent
- Message history / regeneration (`--retry`)
- Emoji conventional commits (`--emoji`)
- Commitizen-style interactive type picker fallback when offline
