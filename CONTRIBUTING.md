# Contributing to Operator

Thanks for your interest in contributing!

## Getting Started

1. Fork the repo and clone your fork
2. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Install in dev mode: `pip install -e ".[dev]"`
4. Create a branch: `git checkout -b my-feature`

## Before Submitting a PR

- Run linting: `ruff check src/ tests/`
- Run tests: `pytest`
- Make sure both pass cleanly

## Commit Messages

Use [conventional commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `refactor:` — code change that neither fixes a bug nor adds a feature
- `test:` — adding or updating tests
- `chore:` — maintenance (deps, CI, etc.)

## Workflow

1. Open an issue before starting large changes so we can discuss the approach
2. Keep PRs focused — one feature or fix per PR
3. Version bumps are done by maintainers at release time; don't change the version in your PR

## Code Style

- Python 3.11+
- Ruff for linting and formatting (config in `pyproject.toml`)
- Type hints everywhere
- Line length: 100 characters
