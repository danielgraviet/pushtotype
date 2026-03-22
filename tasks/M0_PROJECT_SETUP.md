# Milestone 0: Project Setup

> **Goal:** A clean, installable Python project skeleton that anyone can clone, install, and run a smoke test on.

---

## Why This Phase Matters

Everything built in M1–M5 depends on having a solid project foundation. A well-structured `pyproject.toml`, consistent linting, and passing CI from day one means you never have to "go back and fix the plumbing." It also signals to contributors that this is a serious project.

---

## Learning Objectives

By completing this milestone you will understand:

- How to structure a modern Python package using `src/` layout
- How `pyproject.toml` replaces `setup.py` and `setup.cfg`
- How entry points create CLI commands from Python functions
- How GitHub Actions CI works for linting and testing
- How `ruff` handles both linting and formatting in one tool

---

## Tasks

### 0.1 — Create the GitHub repo
- [ ] Create a new public repo named `pushtotype` on GitHub
- [ ] Initialize with MIT `LICENSE` file
- [ ] Add a `.gitignore` for Python (use GitHub's Python template)

### 0.2 — Project directory structure
- [ ] Create the following structure:

```
pushtotype/
├── src/
│   └── pushtotype/
│       ├── __init__.py          # __version__ = "0.1.0"
│       └── __main__.py          # print("PushToType is not yet implemented")
├── tests/
│   └── test_smoke.py            # assert import works
├── assets/                      # empty for now, will hold audio feedback files
├── pyproject.toml
├── README.md
├── LICENSE
└── .github/
    └── workflows/
        └── ci.yml
```

### 0.3 — pyproject.toml
- [ ] Configure build system (`hatchling` or `setuptools`)
- [ ] Define project metadata (name, version, description, author, license, Python ≥3.10)
- [ ] Add placeholder dependencies (we'll fill these in during M1):

```toml
dependencies = [
    "click>=8.0",
]
```

- [ ] Add optional dependency groups:

```toml
[project.optional-dependencies]
dev = ["ruff", "pytest", "pytest-asyncio"]
```

- [ ] Define the CLI entry point:

```toml
[project.scripts]
pushtotype = "pushtotype.cli:main"
```

### 0.4 — Minimal CLI
- [ ] Create `src/pushtotype/cli.py` with a `click` group:
  - `pushtotype` (root) — prints version and help
  - `pushtotype test` — prints "Not yet implemented" placeholder
  - `pushtotype devices` — prints "Not yet implemented" placeholder
- [ ] Verify `pushtotype --help` works after install

### 0.5 — Linting and formatting
- [ ] Add `ruff` config to `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
```

- [ ] Run `ruff check .` and `ruff format .` — both should pass with zero issues

### 0.6 — Tests
- [ ] Write `tests/test_smoke.py`:
  - Test that `import pushtotype` works
  - Test that `pushtotype.__version__` is a string
- [ ] Run `pytest` — should pass

### 0.7 — GitHub Actions CI
- [ ] Create `.github/workflows/ci.yml` that runs on push and PR:
  - Install Python 3.10+
  - `pip install -e ".[dev]"`
  - `ruff check .`
  - `ruff format --check .`
  - `pytest`
- [ ] Push and verify the CI badge is green

### 0.8 — README (initial)
- [ ] Write a README.md with:
  - Project name and one-line description
  - "Work in progress" badge/notice
  - Vision statement (from PROJECT_PLAN.md)
  - Planned features list
  - Installation placeholder (`pip install pushtotype` — coming soon)
  - Contributing section pointing to CONTRIBUTING.md (can be a stub)
  - License

---

## Checkpoints

Use these to verify you're on track:

| # | Checkpoint | How to verify |
|---|---|---|
| 1 | Repo exists and is public | Visit `github.com/yourname/pushtotype` |
| 2 | Package installs locally | `pip install -e ".[dev]"` exits cleanly |
| 3 | CLI runs | `pushtotype --help` prints help text with version |
| 4 | Linting passes | `ruff check . && ruff format --check .` exits 0 |
| 5 | Tests pass | `pytest` shows 1+ tests passed |
| 6 | CI is green | GitHub Actions badge shows passing |

---

## Definition of Done

**You are ready to move to M1 when ALL of the following are true:**

- [ ] `git clone` → `pip install -e ".[dev]"` → `pushtotype --help` works on a fresh machine
- [ ] `pytest` passes with at least 1 smoke test
- [ ] GitHub Actions CI is green on `main`
- [ ] `ruff check` and `ruff format --check` produce zero warnings
- [ ] README exists with project description and vision
- [ ] Project is public on GitHub with MIT license

---

## What NOT to Do in This Phase

- Do NOT add `faster-whisper`, `sounddevice`, `evdev`, or any heavy dependencies yet
- Do NOT write any real application logic — stubs and placeholders only
- Do NOT set up Docker, pre-commit hooks, or other tooling that isn't essential
- Do NOT spend time on the README beyond basics — it'll evolve as features land

---

## Estimated Effort

**1–2 hours** if you're familiar with Python packaging.
**3–4 hours** if this is your first `pyproject.toml` + GitHub Actions setup (and that's fine — this is a learning objective).

---

## Files to Create

| File | Purpose |
|---|---|
| `src/pushtotype/__init__.py` | Package init, `__version__` |
| `src/pushtotype/__main__.py` | `python -m pushtotype` support |
| `src/pushtotype/cli.py` | Click CLI group with placeholder commands |
| `tests/test_smoke.py` | Import and version smoke test |
| `pyproject.toml` | Build config, deps, entry points |
| `.github/workflows/ci.yml` | CI pipeline |
| `README.md` | Project overview |
| `LICENSE` | MIT license |
| `.gitignore` | Python gitignore |
