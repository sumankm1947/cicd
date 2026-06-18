# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> This file is also a **detailed learning log**. The owner is using it as raw
> material for documentation they will write later, so it intentionally records
> *what was done, why, and the concepts explained* — not just terse guidance.

---

## 1. Purpose

This is a **CI/CD learning lab**, not a product. The owner is practicing GitHub
Actions on the path to an **SDET** role. They already know **API and UI
automation**; the gap being filled here is **CI/CD**. The Flask app + pytest
suite exist only to give a pipeline something real to run. Optimize all work for
*teaching CI/CD concepts*, one lab at a time. Primary language: **Python**.
Plan after GitHub Actions: port the same pipeline to **Azure DevOps**.

Environment: Windows 11, Python 3.10, Docker + git installed, no `gh` CLI.

---

## 2. Commands

Always use the project venv (`venv/`) so this stays independent of the owner's
other project at `C:\E\Switch\pytest_api`.

```powershell
.\venv\Scripts\Activate.ps1          # activate venv (do this first)
pip install -r requirements.txt      # install deps

pytest                               # run all tests
pytest tests/test_api.py             # run one file
pytest -k divide                     # run tests whose name matches "divide"
pytest -n 4                          # run tests in parallel across 4 workers (pytest-xdist)
pytest -n auto                       # let xdist pick worker count = CPU cores
pytest --cov=app --cov-report=term-missing   # with coverage
flake8 app tests --max-line-length=100        # lint
python -m app.api                    # run the API at http://127.0.0.1:5000
```

If not activating the venv, call binaries directly: `.\venv\Scripts\pytest.exe`.

---

## 3. Architecture

```
app/calculator.py          pure functions (add/subtract/multiply/divide) — unit-test targets
app/api.py                 Flask API: GET /health, POST /calculate {op,a,b}
app/__init__.py            makes `app` an importable package
tests/test_calculator.py   unit tests (no Flask, no network)
tests/test_api.py          API tests via Flask's test client (no running server)
.github/workflows/ci.yml   the pipeline (Labs 1–7) — every line is commented; comments are the lesson
.github/workflows/app-only.yml   path-filtered workflow (Lab 6); fires only on app/** changes
Dockerfile                 packages the Flask app into an image (Lab 7)
.dockerignore              keeps venv/.git/etc out of the build context (Lab 7)
pytest.ini                 pytest config (see the pythonpath note below)
requirements.txt           flask, pytest, pytest-cov, pytest-xdist, flake8 (all pinned)
venv/                      local virtual environment
```

`app/api.py` imports the calculator via `from app import calculator`, so the
`app` package must remain importable from the project root.

Current status: **9 tests, all passing, ~91% coverage, flake8 clean.**

---

## 4. Key gotcha solved: `pythonpath` in pytest.ini

**Symptom:** `ModuleNotFoundError: No module named 'app'` when running the bare
`pytest` command (and it would have failed in CI too).

**Root cause:** `python -m pytest` adds the current directory to `sys.path`, so
`import app` works. The bare `pytest` console script (what the owner and the CI
workflow use) does **not** add the project root to the path.

**Fix:** added `pythonpath = .` to `pytest.ini` (a pytest 7+ feature). This puts
the project root on the import path regardless of how pytest is invoked.

**Lesson for the owner (SDET-relevant):** *how* a tool is invoked changes its
import/runtime behavior — the classic "passes on my machine, fails in CI" trap.
Pinning it in config is the durable fix. Requires pytest ≥ 7.0 (venv pins 8.2.2).

```ini
[pytest]
addopts = -v
testpaths = tests
pythonpath = .
```

---

## 5. CI/CD vocabulary (the 6 core words)

- **Workflow** — one YAML file in `.github/workflows/`, triggered by events.
- **Event / trigger** — what starts a run: `push`, `pull_request`, `schedule`, manual (`workflow_dispatch`). Declared under `on:`.
- **Job** — runs on its own fresh, isolated VM (a **runner**). Jobs run in parallel by default.
- **Step** — one ordered action inside a job: either `uses:` (a prebuilt action) or `run:` (shell commands).
- **Action** — a reusable step from the Marketplace, e.g. `actions/checkout@v4`.
- **Artifact** — a file a job produces (report, build) saved off the VM so you can download it or pass it on.

Hierarchy:
```
workflow (ci.yml)
└── jobs
    └── test (a JOB — own VM)
        └── steps (ordered commands)
            ├── Check out code
            ├── Set up Python
            └── ...
```

---

## 6. The Lab 1 pipeline, step by step (`.github/workflows/ci.yml`)

`on:` triggers: `push` to main, every `pull_request` (the SDET merge gate), and
`workflow_dispatch` (manual "Run workflow" button).

One job, `test`, on `ubuntu-latest` (Linux = fastest/cheapest runner). Its steps:

1. **Check out code** — `actions/checkout@v4` pulls the repo onto the runner. Nearly every job starts here.
2. **Set up Python** — `actions/setup-python@v5` with `python-version: "3.10"` and `cache: pip` (caches downloaded packages between runs for speed — first taste of caching).
3. **Install dependencies** — `pip install -r requirements.txt`.
4. **Lint with flake8** — first pass (`--select=E9,F63,F7,F82`) fails the job on real errors; second pass (`--exit-zero`) reports style warnings without blocking.
5. **Run tests** — `pytest --cov=app --cov-report=term-missing --cov-report=xml --junitxml=report.xml`. Produces two machine-readable reports (see §8).
6. **Upload test & coverage reports** — saves the reports as an artifact (see §8).

---

## 7. Steps vs Jobs, and a multi-job example

All entries under one `steps:` belong to the **same job** and share the same VM
and files. **Multiple jobs** each get a **fresh, isolated VM**, run in **parallel
by default**, and can be chained with **`needs:`**.

Use more **steps** for sequential tasks that share setup. Use separate **jobs**
for parallelism, independent pass/fail signals, "run only if X passed" gating,
or a different OS/Python/environment.

Real-life SDET shape — fast checks → integration → deploy (main only):

```yaml
jobs:
  lint-and-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.10", cache: pip }
      - run: pip install -r requirements.txt
      - run: flake8 app tests
      - run: pytest tests/test_calculator.py

  integration:
    needs: lint-and-unit          # waits; won't start if lint-and-unit fails
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.10", cache: pip }
      - run: pip install -r requirements.txt
      - run: pytest tests/test_api.py

  deploy:
    needs: integration
    if: github.ref == 'refs/heads/main'   # skip on PRs
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying... (real deploy command here)"
```

Graph: `lint-and-unit ──▶ integration ──▶ deploy (main only)`.

**Gotcha:** because each job is a clean VM, to share a file between jobs you must
pass it via artifacts (`upload-artifact` → `download-artifact`). (Later lab.)

---

## 8. The "Upload test & coverage reports" step, in depth

```yaml
- name: Upload test & coverage reports
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: |
      report.xml
      coverage.xml
```

**Where the files come from** — the `pytest` step creates them:
- `--junitxml=report.xml` → `report.xml`: every test, pass/fail, duration, error, in standard **JUnit XML** (understood by nearly all CI tools).
- `--cov-report=xml` → `coverage.xml`: which lines of `app/` ran, in **Cobertura XML**.

**Why upload at all** — each job's VM is destroyed when the job ends, taking those
files with it. An **artifact** is a file explicitly saved off the VM so it survives
and can be downloaded from the run's page.

**Line meanings:**
- `uses: actions/upload-artifact@v4` — GitHub's prebuilt upload action (v4).
- `name: test-reports` — the downloadable bundle's name (`test-reports.zip`).
- `path: |` — a YAML multi-line block listing files; supports multiple paths and globs (e.g. `htmlcov/**`).
- `if: always()` — **most important.** By default a step is skipped if an earlier
  step failed. But you most want the report exactly *when tests fail*. `if: always()`
  forces the upload to run regardless of pass/fail. (Related: `success()` (default),
  `failure()`, `cancelled()`.)

**Retrieval:** Actions tab → the run → Artifacts section → download. Artifacts are
kept 90 days by default (tunable via `retention-days:`).

**Why an SDET cares:** the XML is raw material later turned into human-readable
output — PR test summaries, coverage gates (Codecov/SonarQube) that block a PR when
coverage drops, and clickable HTML coverage reports. This step is the foundation of
CI **test reporting**.

---

## 9. Lab roadmap & current progress

Full curriculum is in `README.md`. Status:

- **Lab 1 — Baseline pipeline:** DONE. Scaffolded, fixed the `pythonpath` issue,
  pushed to GitHub, pipeline ran **green**. The "break a test on purpose" sub-
  exercise was done as a throwaway practice branch (`break-a-case`) — it proved
  the red-CI merge-gate concept and was intentionally *not* merged. Branch
  protection was left as an optional follow-up.
- **Lab 2 — Matrix builds:** DONE (config). Added `strategy.matrix` over Python
  3.9–3.12 with `fail-fast: false`, and made artifact names unique per version
  (`test-reports-${{ matrix.python-version }}`) to avoid the `upload-artifact@v4`
  409 name-collision. Merged via PR #2. (See §11 for the lesson.)
- **Lab 3 — Multiple jobs + `needs`:** DONE (config). Split the single job into
  `lint` (one run on 3.10) and `test` (matrix 3.9–3.12), chained with
  `needs: lint` so the test fan-out waits for lint. Each job carries its own
  checkout + setup-python + install (fresh-VM isolation). Pushed straight to
  `main` (skipped the PR this time). (See §12 for the lesson.)
- **Lab 4 — Secrets:** DONE (config). Added a step that reads `MY_TOKEN` via
  `env:` and echoes it, to watch GitHub mask the value to `***` in the logs.
  Pushed to `main`. (The repo secret `MY_TOKEN` must exist in Settings →
  Secrets → Actions, else the value is empty and there's nothing to mask.)
- **Lab 5 — Caching, deeper:** DONE (config). Removed the convenience
  `cache: pip` from `setup-python` and added an explicit `actions/cache@v4`
  step in both jobs, keyed on `hashFiles('requirements.txt')` with a
  `restore-keys` prefix fallback. (See §13 for the lesson.)
- **Lab 6 — Scheduled & path-filtered runs:** DONE (config). Added a daily
  `schedule: cron "0 3 * * *"` trigger to `ci.yml`, and a separate isolated
  workflow `app-only.yml` that fires only on `push` with `paths: app/**`.
  (See §14 for the lesson.)
- **Lab 7 — Services / Docker:** DONE. Part B (real): wrote a `Dockerfile`
  (python:3.10-slim, deps-before-code layer caching) + `.dockerignore`, built
  and ran the image locally, then added a `docker-build` CI job (`needs: test`)
  that builds the image and smoke-tests `/health` with `curl --fail`. Part A
  (mechanism demo): added an `integration-db` job with a `services: postgres`
  container, a `pg_isready` health check, and a `psql … SELECT version();` step
  to prove connectivity. Branch `lab-7-services-docker`, PR #3, merged green.
  (See §15 for the lesson.)
- **Labs 8–10:** environments & deploy gates, reusable workflows, reporting &
  badges. Then port Labs 1–3 to Azure DevOps (`azure-pipelines.yml`).

---

## 10. Working conventions in this repo

- Teach CI/CD one lab at a time; keep the **comments in workflow YAML** — they are
  the lesson, not clutter.
- Always verify locally (`pytest` + `flake8`) before suggesting a push; Actions only
  run after pushing to GitHub.
- Lint config: pyflakes/E9 errors fail CI; line length is 100 and non-blocking.
- Each lab should be its own branch + PR so the pipeline is experienced as a merge gate.
- The owner usually does the `git`/push steps themselves (building the muscle memory);
  don't push or `git init` unless explicitly asked. (For Lab 2 they asked Claude to
  branch/commit/push `lab-2-matrix`.) No `gh` CLI installed — open PRs from the link
  the `git push` prints.

---

## 11. Lab 2 — Matrix builds (the lesson)

**Goal:** prove the suite works across Python 3.9–3.12 without writing four jobs.

A **matrix** is a property of the **job**, not a step. It lives under `strategy:`
next to `runs-on`, and tells GitHub *"clone this whole job once per value."* Four
versions → four independent jobs (`test (3.9)` … `test (3.12)`), each on its own
fresh VM, all running **in parallel**. Each clone reads its value inside the steps
via `${{ matrix.python-version }}`.

```yaml
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false                                   # see gotcha 1
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}   # the per-clone value
          cache: pip
      # ... install / lint / test as before ...
      - name: Upload test & coverage reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-reports-${{ matrix.python-version }}  # see gotcha 2
          path: |
            report.xml
            coverage.xml
```

**Mental model:** `strategy.matrix` = job-level = "make N copies of this job".
`with:` = step-level = "inputs to THIS one action". The matrix lives where the
cloning happens; the steps just read from it.

**Gotcha 1 — `fail-fast`.** Default is `true`: the first matrix job to go red
**cancels its still-running siblings**. As an SDET you usually want the opposite —
see *every* version that breaks in one run — so set `fail-fast: false`.

**Gotcha 2 — artifact name collisions (`upload-artifact@v4`).** All clones run the
same upload step. In v4, two artifacts in one workflow run **cannot share a name**;
the second to finish fails with a 409. Make the name unique per clone:
`test-reports-${{ matrix.python-version }}`. (v3 silently merged them — a real
behavior change worth knowing for interviews.)

**Common mistake (hit during this lab):** putting `matrix:` under the step's
`with:`. That's invalid — a matrix isn't a step input. It belongs at job level
under `strategy:`.

**Verifying locally:** you can't run a matrix off GitHub, but still confirm the
suite is green on your local interpreter (`pytest` + `flake8`) before pushing; a
matrix only multiplies *where* it runs, not *what* it runs.

---

## 12. Lab 3 — Multiple jobs + `needs` (the lesson)

**Goal:** split one job into two — `lint` and `test` — and make `test` wait for
`lint` to pass.

```yaml
jobs:
  lint:                         # JOB 1 — fast, cheap, runs once on 3.10
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.10", cache: pip }
      - run: pip install -r requirements.txt
      - run: flake8 app tests ...

  test:                         # JOB 2 — the matrix fan-out
    needs: lint                 # <-- the dependency edge
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4         # repeated on purpose (fresh VM)
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}", cache: pip }
      - run: pip install -r requirements.txt
      - run: pytest ...
      - uses: actions/upload-artifact@v4
        ...
```

**`needs:` is the whole point.** It draws a dependency edge in the job graph:
`lint → test (3.9/3.10/3.11/3.12)`. `lint` runs first; the four matrix jobs
**don't even start** until it's green. Drop `needs:` and all jobs run in parallel.
This is **fail-fast at the *job* level** — a style error blocks the PR before you
burn four test runners.

**Fresh-VM isolation (the recurring theme).** Each job is a brand-new machine, so
`lint` and `test` *each* repeat checkout + setup-python + install. Nothing carries
over between jobs. That repetition isn't waste to "fix" — it's the isolation that
makes jobs independent, and it's exactly why sharing a built file later needs the
**artifact handoff** (`upload-artifact` → `download-artifact`).

**Lint runs once, not in the matrix.** Linting is Python-version-independent, so
`lint` is a single job on 3.10. Only `test` carries the matrix. (Mistake hit
during this lab: the matrix landed on `lint` and the setup steps got dropped from
`test` — each job needs its *own* full setup.)

**See the gate for real:** introduce a lint error, push, and watch `lint` go red
while all four `test` jobs report **skipped** (they never run). Revert to restore.

---

## 13. Lab 5 — Caching, the explicit way (the lesson)

**Goal:** we've been caching since Lab 1 — `cache: pip` inside `setup-python` did
it invisibly. Lab 5 rips that convenience off and wires the cache **by hand**, so
the three things interviewers actually ask about are visible: the **key**, the
**hit vs miss**, and the **`restore-keys` fallback**.

**What a cache is.** A folder GitHub *saves* at the end of a job and *restores* at
the start of a future run, so we don't re-download the same packages every time.
For pip the folder worth caching is `~/.cache/pip` (downloaded wheels) — cache the
*downloads*, not installed `site-packages`.

**The two-part lifecycle (the part people miss).** One `actions/cache` step does
both ends:
- **Restore** happens *at the step* — when the runner reaches it, it looks for a
  matching cache and pulls it down.
- **Save** happens *automatically at the end of the job* (a hidden "post" step),
  and **only on a miss**. A hit doesn't re-save — nothing changed.

So you never write a separate save step. Place the cache step **before** install.

```yaml
  lint:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"      # note: NO `cache: pip` anymore
      - name: Cache pip downloads
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-3.10-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-3.10-
      - run: pip install -r requirements.txt   # HIT -> installs from cache, no net
```

**The key is the whole lesson.**
`key: ${{ runner.os }}-pip-3.10-${{ hashFiles('requirements.txt') }}`
- `hashFiles('requirements.txt')` is a fingerprint of the deps. **Edit
  `requirements.txt` → key changes → fresh cache built.** Same deps → same key →
  reused. This is what keeps the cache *correct* — you never restore stale deps.
- `runner.os` + the Python version in the key stop Linux/3.10 wheels from
  colliding with other combos.

**`restore-keys` = the fallback (miss only).** A list of key *prefixes*. If no
exact key match, GitHub grabs the newest cache whose name *starts with* the
prefix (your previous deps cache), so you still skip most downloads and pip only
fetches the one changed package. Without it, a single dep bump = full cold
download.

**Matrix twist (gotcha).** The `test` job is a matrix, so `matrix.python-version`
goes **in the key** — otherwise all four versions fight over one cache and you'd
restore 3.9 wheels into a 3.12 run:
`key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('requirements.txt') }}`.

**Mental model:** `cache: pip` = "cache, just handle it." `actions/cache` = "here
is exactly *what* to save, under *what* name, with *what* fallback." Same outcome;
the explicit form is what you reach for when the default doesn't fit (multiple
folders, custom keys, non-pip tools).

**See it work (the experiment):**
1. First push → log says **"Cache not found"** (miss); saved at job end.
2. No-op push → **"Cache restored from key …"** (hit); install visibly faster.
3. Bump a version in `requirements.txt` → **miss** again (key changed), but
   `restore-keys` gives a partial restore — only the changed package downloads.

Inspect stored caches at **Actions tab → Caches** (7-day idle eviction, 10 GB
repo cap).

**The one danger to internalize:** caching's failure mode is *staleness* —
restoring old deps that should have changed. The content fingerprint in the key
(`hashFiles(...)`) is what prevents it. A cache key with no content hash is a bug.

---

## 14. Lab 6 — Scheduled & path-filtered runs (the lesson)

**Goal:** two independent triggers, both under `on:`, both teaching the same
theme — *not everything should run on every event.*

### Part 1 — `schedule:` (a nightly cron), added to `ci.yml`

```yaml
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * *"      # every day at 03:00 UTC
```

**The 5 cron fields:** `minute hour day-of-month month day-of-week`. So
`0 3 * * *` = minute 0, hour 3, any day/month/weekday. Handy ones: `0 3 * * 1`
(Mondays 03:00), `*/15 * * * *` (every 15 min).

**Gotchas (interview-grade):**
- **Cron is always UTC** — no timezone field. Convert in your head.
- **`schedule` only runs on the default branch** (`main`), using the workflow as
  it exists *on main*. You can't schedule a feature branch.
- **Firing is best-effort, not punctual** — scheduled runs get delayed under load,
  worst on the hour. Offset away from `0` (e.g. `7 3 * * *`) if timing matters.
- **Auto-disabled after 60 days of repo inactivity** — GitHub pauses scheduled
  runs until the next push. Expected for a quiet learning repo.

**Why an SDET cares:** nightly regression suites, scheduled smoke tests against a
deployed env, dependency-freshness checks — work that shouldn't wait for a commit.

### Part 2 — path filters, in a *separate* workflow `app-only.yml`

```yaml
name: App-only check
on:
  push:
    paths:
      - "app/**"            # fires only when something under app/ changed
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - run: echo "app/ changed — this workflow fired."
```

- `paths:` / `paths-ignore:` attach to **`push` and `pull_request` only** — *not*
  to `schedule` or `workflow_dispatch` (no diff to filter on). Use one or the
  other per event, never both. Globs: `**` spans directories, `*.md` is one level,
  `**.md` is any depth.
- **Done as its own file on purpose.** Bolting `paths:` onto the main `ci.yml`
  push trigger would *stop the real test suite from running* on commits that don't
  touch `app/` (test-only or config changes included) — the wrong call for a gate.
  An isolated workflow gives a clean demo without weakening CI.

**The big trap — the "skipped required check" deadlock.** If a path-filtered
workflow is set as a **required status check** for merging, a PR that doesn't
touch those paths shows the check as **skipped**, and a required check that never
reports *passed* can **block the PR forever**. Know the failure mode; the fix is a
path-aware pattern or an always-green placeholder job.

**See it work:** commit a change to **only** `README.md` → `app-only.yml` stays
idle; commit a change to **`app/calculator.py`** → it fires. That contrast is the
lesson. (The `schedule` won't fire on demand — trigger `ci.yml` via
`workflow_dispatch` to confirm the file is valid, then check the Actions tab next
morning for the cron run.)

---

## 15. Lab 7 — Services / Docker (the lesson)

**Goal:** two unrelated mechanisms under one lab — **package the app as a Docker
image and build it in CI** (Part B, real for us), and **stand up a dependency
container with `services:`** (Part A, a mechanism demo since the calculator has
no DB).

### Core Docker vocabulary

- **Image** — the frozen, built package (the Dockerfile's *output*). Like a `.exe`
  on disk.
- **Container** — a *running instance* of an image. One image → many containers,
  like a class → many objects. A container only exists after `docker run`; a built
  image alone has zero containers.
- **Layer** — each Dockerfile line creates a cached layer. Images live in Docker's
  own content-addressed store (on Windows, inside the Docker Desktop WSL VM —
  *not* a file in the project folder). Identical base layers are stored once and
  shared between images.

### Part B — Dockerfile + build in CI (the real half)

```dockerfile
FROM python:3.10-slim       # minimal Linux that already has Python 3.10
WORKDIR /app                # all later commands run inside /app
COPY requirements.txt .     # copy deps list FIRST...
RUN pip install --no-cache-dir -r requirements.txt   # ...install (this layer caches)
COPY . .                    # then copy the app code
EXPOSE 5000                 # documents the port the app listens on
CMD ["python", "-m", "app.api"]   # what runs when a container starts
```

**The deps-before-code ordering is the key idea** — same "cache the deps, not the
app" lesson as Lab 5, one level up. Change app code and Docker reuses the cached
`pip install` layer instead of re-downloading everything.

**Prerequisite that bit us nowhere only because it was already right:** the app
must bind to `host="0.0.0.0"`, not `127.0.0.1` — otherwise it only listens
*inside* the container and nothing outside (your machine, a CI smoke test) can
reach it. `app/api.py` already did this.

**`.dockerignore` (gotcha).** `COPY . .` drags in `venv/`, `.git/`, caches, etc.
A `.dockerignore` excludes them (the `.gitignore` of the build context). **Trap
hit during this lab:** unlike `.gitignore`, `.dockerignore` does **not** support
*inline* comments — every non-`#` line is a pattern, so a trailing `# comment`
corrupts the pattern (Docker errored with `non-printable ASCII characters`).
Comments must be on their own line.

**Local-first loop:** `docker build -t cicd-lab .` → `docker run --rm -p 5000:5000
cicd-lab` → in another terminal `curl http://localhost:5000/health` →
`{"status":"ok"}`. Having run every command by hand means the CI job is
pre-tested.

**The CI job** (`docker-build`, `needs: test`): ubuntu runners have Docker
preinstalled, so it calls `docker build` directly, runs the container **detached**
(`-d`, since a CI step can't hang), then smoke-tests with `curl --fail` (exits
non-zero on an HTTP error → fails the job → catches "image builds but app is
broken"), and cleans up with `if: always()`. The `sleep 3` before the curl is a
known smell — a readiness race — fixable with a retry loop.

### Part A — `services:` containers (the mechanism demo)

```yaml
  integration-db:
    needs: test
    runs-on: ubuntu-latest
    services:                 # JOB-level key (sibling of runs-on / steps)
      postgres:               # service id = its network hostname
        image: postgres:16
        env: { POSTGRES_USER: testuser, POSTGRES_PASSWORD: testpass, POSTGRES_DB: testdb }
        ports: ["5432:5432"]  # container 5432 -> runner 5432
        options: >-           # GitHub waits for healthy BEFORE running steps
          --health-cmd pg_isready --health-interval 10s
          --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - name: Connect to Postgres and run a query
        env: { PGPASSWORD: testpass }
        run: psql -h localhost -U testuser -d testdb -c "SELECT version();"
```

**Three things that make `services:` click:**
1. **It's a job-level key** (sibling of `runs-on`/`steps`), not a step — same
   "lives at the job level" shape as `strategy.matrix`.
2. **The health check replaces guessing.** GitHub won't start your steps until
   `--health-cmd pg_isready` reports healthy — the *proper* fix for the `sleep`
   race in Part B. No sleeping, no flake.
3. **Addressing it:** because our **steps run directly on the runner VM** (not
   inside a container) and we mapped the port, we connect at `localhost:5432`. If
   the *job itself* ran inside a container, you'd use the service name `postgres`
   as the hostname instead — a classic interview distinction.

**`psql` is preinstalled on `ubuntu-latest`.** If a run ever says `psql: command
not found`, add `sudo apt-get install -y postgresql-client` before the connect
step.

**Why kept in its own job:** the calculator has no DB, so this job is honest about
being a *mechanism* demo — the skill (wire a service + connect to it) transfers to
any real app; the data is throwaway.
