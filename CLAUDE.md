# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a **CI/CD learning lab**, not a product. The owner is practicing GitHub
Actions for an SDET career path. The Flask app + pytest suite exist only to give
pipelines something real to run. Optimize explanations and changes for *teaching
CI/CD concepts*, not for app features. See `README.md` for the lab curriculum (Labs 1–10).

## Commands

Use the local venv interpreter (`venv/Scripts/python.exe` on Windows).

```powershell
.\venv\Scripts\Activate.ps1          # activate venv
pip install -r requirements.txt      # install deps
pytest                               # all tests
pytest tests/test_api.py             # one file
pytest -k divide                     # tests matching a name
pytest --cov=app --cov-report=term-missing   # with coverage
flake8 app tests --max-line-length=100        # lint
python -m app.api                    # run the API on :5000
```

## Architecture

- `app/calculator.py` — pure functions, no framework. Unit-test layer.
- `app/api.py` — thin Flask wrapper over calculator (`/health`, `POST /calculate`).
  Imports calculator via `from app import calculator`, so the package must stay importable.
- `tests/` — `test_calculator.py` (unit) and `test_api.py` (Flask test client; no server needed).
- `.github/workflows/ci.yml` — the pipeline. Heavily commented on purpose; comments
  are the lesson. Keep them when editing.

## Working conventions here

- When adding pipeline features, prefer one focused change per lab and explain the
  *why* in YAML comments — the user reads the workflow file to learn.
- Always verify changes locally (`pytest` + `flake8`) before suggesting a push;
  Actions only run after pushing to GitHub.
- Lint config: pyflakes/E9 errors fail CI; line length is 100 and non-blocking.
