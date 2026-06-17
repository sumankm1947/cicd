# CI/CD Practice Lab (GitHub Actions + Python)

A deliberately tiny Flask app + pytest suite. **The app is not the point — the
pipeline is.** You already know API & UI automation; here you learn to make a
CI/CD system *run* that automation automatically on every change.

## The app under test

| Path | What it is |
|------|------------|
| `app/calculator.py` | Pure functions — unit-test targets |
| `app/api.py` | Flask API (`/health`, `POST /calculate`) — API-test target |
| `tests/` | pytest unit + API tests |
| `.github/workflows/ci.yml` | The pipeline (Lab 1, fully commented) |

## Run it locally first (always debug locally before pushing)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

pytest                       # run all tests
pytest tests/test_api.py     # run one file
pytest -k divide             # run tests matching "divide"
pytest --cov=app             # with coverage
flake8 app tests             # lint

python -m app.api            # run the API at http://127.0.0.1:5000
```

---

## CI/CD core vocabulary (learn these 6 words)

- **Workflow** — one YAML file in `.github/workflows/`. Triggered by events.
- **Event / trigger** — `push`, `pull_request`, `schedule`, manual, etc. (`on:`)
- **Job** — runs on its own fresh VM (**runner**). Jobs run in parallel by default.
- **Step** — one action inside a job: either `uses:` (a prebuilt action) or `run:` (a shell command).
- **Action** — a reusable step from the Marketplace, e.g. `actions/checkout@v4`.
- **Artifact** — a file a job produces (report, build) that you download or pass on.

---

## The labs — do them in order

Each lab is a small change to `.github/workflows/`. Push, watch it run in the
GitHub **Actions** tab, read the logs. Break it on purpose to learn what red looks like.

**Lab 1 — Baseline (done for you).** Read `ci.yml` top to bottom. Push, open a PR,
watch lint + tests run and download the artifact. Make a test fail on purpose; see the PR go red.

**Lab 2 — Matrix builds.** Run the suite across versions in parallel:
```yaml
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```
Lesson: one job definition → many parallel runs. This is how you prove cross-version support.

**Lab 3 — Multiple jobs + `needs`.** Split `lint` and `test` into separate jobs;
make `test` wait with `needs: lint`. Lesson: dependencies, parallelism, the job graph.

**Lab 4 — Secrets.** Add a repo secret (Settings → Secrets → Actions), read it via
`${{ secrets.MY_TOKEN }}`, print masked. Lesson: never hard-code credentials in pipelines.

**Lab 5 — Caching, deeper.** Replace `cache: pip` with an explicit `actions/cache`
keyed on `requirements.txt` hash. Lesson: cache keys, hits vs misses, speed.

**Lab 6 — Scheduled & path-filtered runs.** Add a nightly `schedule: cron`, and a
workflow that only runs when `app/**` changes (`on: push: paths:`). Lesson: not everything runs every time.

**Lab 7 — Services / Docker.** Spin up a real dependency (e.g. a `postgres`
`services:` container) for integration tests; then add a `Dockerfile` and build the app image in CI.

**Lab 8 — Environments & deploy gates.** Define a `production` environment with a
required reviewer; add a `deploy` job that needs `test` and runs only on `main`. Lesson: CD + approvals.

**Lab 9 — Reusable & composite workflows.** Extract shared setup into a reusable
workflow (`workflow_call`). Lesson: DRY pipelines across repos.

**Lab 10 — Reporting & badges.** Publish JUnit results as a PR check, add HTML
coverage as an artifact, and put a build-status badge in this README.

### After GitHub Actions
Port Lab 1–3 to **Azure DevOps Pipelines** (`azure-pipelines.yml`) — same concepts,
different YAML. Doing this once makes you comfortable in either, which covers most SDET job listings.

---

## Getting it onto GitHub (required — Actions only run on GitHub)

```powershell
git init
git add .
git commit -m "Lab 1: baseline CI pipeline"
# create an EMPTY repo on github.com, then:
git remote add origin https://github.com/<you>/cicd-practice.git
git branch -M main
git push -u origin main
```
Make the repo **public** = unlimited free Actions minutes while you learn.
Open a PR for each lab so you see the pipeline act as a merge gate — that's the real SDET workflow.

